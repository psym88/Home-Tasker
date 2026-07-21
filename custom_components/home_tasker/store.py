"""Versioned persistence for Home Tasker."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import FALLBACK_GROUP_NAME, STORAGE_KEY, STORAGE_VERSION
from .scheduler import next_due


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HomeTaskerStore:
    """Serialize mutations and persist one compact snapshot."""

    def __init__(self, hass: HomeAssistant, upload_dir: Path) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._upload_dir = upload_dir
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = {
            "groups": [], "tasks": [], "history": {}, "attachments": []
        }

    async def async_load(self) -> None:
        if stored := await self._store.async_load():
            self._data = {key: stored.get(key, default) for key, default in self._data.items()}

    def snapshot(self) -> dict[str, Any]:
        return {key: list(self._data[key]) for key in ("groups", "tasks", "attachments")}

    @property
    def groups(self) -> list[dict[str, Any]]:
        return list(self._data["groups"])

    @property
    def tasks(self) -> list[dict[str, Any]]:
        return list(self._data["tasks"])

    def _find(self, kind: str, item_id: str) -> dict[str, Any]:
        item = next((x for x in self._data[kind] if x["id"] == item_id), None)
        if item is None:
            raise ValueError(f"unknown_{kind[:-1]}")
        return item

    @staticmethod
    def _required_name(value: Any) -> str:
        name = str(value or "").strip()
        if not name:
            raise ValueError("name_required")
        return name

    def _group_name_exists(self, name: str, exclude_id: str | None = None) -> bool:
        normalized = name.casefold()
        return any(
            group["id"] != exclude_id
            and group.get("name", "").strip().casefold() == normalized
            for group in self._data["groups"]
        )

    def task(self, task_id: str) -> dict[str, Any]:
        """Return one task for validation by the API layer."""
        return dict(self._find("tasks", task_id))

    async def _save(self) -> None:
        await self._store.async_save(self._data)

    def _resolve_task_group(
        self, group_id: str | None, group_name: str | None, now: str
    ) -> str:
        """Resolve an existing group or create one inside the mutation lock."""
        if group_id:
            return self._find("groups", group_id)["id"]

        name = (group_name or "").strip()
        fallback = not name
        if fallback:
            name = FALLBACK_GROUP_NAME
            group = next(
                (item for item in self._data["groups"] if item.get("is_fallback")),
                None,
            )
        else:
            group = None

        if group is None:
            normalized = name.casefold()
            group = next(
                (
                    item
                    for item in self._data["groups"]
                    if item.get("name", "").strip().casefold() == normalized
                ),
                None,
            )
        if group is None:
            group = {
                "id": uuid4().hex,
                "name": name,
                "manufacturer": None,
                "model": None,
                "icon": None,
                "description": None,
                "created_at": now,
                "updated_at": now,
            }
            self._data["groups"].append(group)
        if fallback or name.casefold() == FALLBACK_GROUP_NAME.casefold():
            group["is_fallback"] = True
        return group["id"]

    async def async_add_group(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            now = _now()
            name = self._required_name(payload.get("name"))
            if self._group_name_exists(name):
                raise ValueError("group_name_exists")
            group = {"id": uuid4().hex, **{k: payload.get(k) for k in (
                "name", "manufacturer", "model", "icon", "description"
            )}, "name": name, "created_at": now, "updated_at": now}
            self._data["groups"].append(group)
            await self._save()
            return group

    async def async_update_group(self, group_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            group = self._find("groups", group_id)
            if "name" in payload:
                name = self._required_name(payload["name"])
                if self._group_name_exists(name, group_id):
                    raise ValueError("group_name_exists")
                payload = {**payload, "name": name}
            for key in ("name", "manufacturer", "model", "icon", "description"):
                if key in payload:
                    group[key] = payload[key]
            group["updated_at"] = _now()
            await self._save()
            return group

    async def async_delete_group(self, group_id: str) -> None:
        async with self._lock:
            self._find("groups", group_id)
            task_ids = {t["id"] for t in self._data["tasks"] if t["group_id"] == group_id}
            file_ids = [a["id"] for a in self._data["attachments"] if a["task_id"] in task_ids]
            self._data["groups"] = [g for g in self._data["groups"] if g["id"] != group_id]
            self._data["tasks"] = [t for t in self._data["tasks"] if t["id"] not in task_ids]
            self._data["attachments"] = [a for a in self._data["attachments"] if a["task_id"] not in task_ids]
            for task_id in task_ids:
                self._data["history"].pop(task_id, None)
            for file_id in file_ids:
                await self._unlink(file_id)
            await self._save()

    async def async_add_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        due = date.fromisoformat(payload["due_date"])
        async with self._lock:
            now = _now()
            name = self._required_name(payload.get("name"))
            group_id = self._resolve_task_group(
                payload.get("group_id"), payload.get("group_name"), now
            )
            task = {
                "id": uuid4().hex,
                **{k: payload.get(k) for k in ("name", "description", "assignee_user_id", "due_date", "recurrence_mode", "frequency", "interval", "weekdays", "day_of_month")},
                "name": name,
                "group_id": group_id,
                "anchor_day": due.day,
                "schedule_anchor": payload["due_date"],
                "created_at": now,
                "updated_at": now,
            }
            self._data["tasks"].append(task)
            await self._save()
            return task

    async def async_update_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            task = self._find("tasks", task_id)
            if "name" in payload:
                payload = {**payload, "name": self._required_name(payload["name"])}
            if "group_id" in payload or "group_name" in payload:
                task["group_id"] = self._resolve_task_group(
                    payload.get("group_id"), payload.get("group_name"), _now()
                )
            for key in ("name", "description", "assignee_user_id", "due_date", "recurrence_mode", "frequency", "interval", "weekdays", "day_of_month"):
                if key in payload:
                    task[key] = payload[key]
            if "due_date" in payload:
                task["anchor_day"] = date.fromisoformat(payload["due_date"]).day
                task["schedule_anchor"] = payload["due_date"]
            task["updated_at"] = _now()
            await self._save()
            return task

    async def async_delete_task(self, task_id: str) -> None:
        async with self._lock:
            self._find("tasks", task_id)
            file_ids = [a["id"] for a in self._data["attachments"] if a["task_id"] == task_id]
            self._data["tasks"] = [t for t in self._data["tasks"] if t["id"] != task_id]
            self._data["attachments"] = [a for a in self._data["attachments"] if a["task_id"] != task_id]
            self._data["history"].pop(task_id, None)
            for file_id in file_ids:
                await self._unlink(file_id)
            await self._save()

    async def async_complete_task(
        self,
        task_id: str,
        completion_date: str,
        user_id: str | None,
        user_name: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            task = self._find("tasks", task_id)
            due_before = task["due_date"]
            due_after = next_due(task, date.fromisoformat(completion_date)).isoformat()
            record = {
                "id": uuid4().hex,
                "completion_date": completion_date,
                "recorded_at": _now(),
                "user_id": user_id,
                "user_name": user_name,
                "notes": str(notes or "").strip() or None,
                "due_before": due_before,
                "due_after": due_after,
            }
            task["due_date"] = due_after
            task["updated_at"] = record["recorded_at"]
            self._data["history"].setdefault(task_id, []).append(record)
            await self._save()
            return task

    def history(self, task_id: str) -> list[dict[str, Any]]:
        self._find("tasks", task_id)
        return sorted(self._data["history"].get(task_id, []), key=lambda x: x["recorded_at"], reverse=True)

    async def async_delete_history(self, task_id: str, entry_id: str) -> dict[str, Any]:
        async with self._lock:
            task = self._find("tasks", task_id)
            entries = self._data["history"].get(task_id, [])
            removed = next((x for x in entries if x["id"] == entry_id), None)
            if removed is None:
                raise ValueError("unknown_history_entry")
            remaining = [x for x in entries if x["id"] != entry_id]
            self._data["history"][task_id] = remaining
            task["due_date"] = (max(remaining, key=lambda x: x["recorded_at"])["due_after"] if remaining else removed["due_before"])
            task["updated_at"] = _now()
            await self._save()
            return task

    def attachment(self, attachment_id: str) -> dict[str, Any] | None:
        return next((x for x in self._data["attachments"] if x["id"] == attachment_id), None)

    async def async_add_attachment(self, task_id: str, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        async with self._lock:
            self._find("tasks", task_id)
            attachment = {"id": uuid4().hex, "task_id": task_id, "filename": filename, "content_type": content_type, "size": len(data), "uploaded_at": _now()}
            await self._hass.async_add_executor_job(self._write, attachment["id"], data)
            self._data["attachments"].append(attachment)
            await self._save()
            return attachment

    async def async_delete_attachment(self, attachment_id: str) -> None:
        async with self._lock:
            if self.attachment(attachment_id) is None:
                raise ValueError("unknown_attachment")
            self._data["attachments"] = [x for x in self._data["attachments"] if x["id"] != attachment_id]
            await self._unlink(attachment_id)
            await self._save()

    def _write(self, file_id: str, data: bytes) -> None:
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        (self._upload_dir / file_id).write_bytes(data)

    async def _unlink(self, file_id: str) -> None:
        await self._hass.async_add_executor_job(self._unlink_sync, file_id)

    def _unlink_sync(self, file_id: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            (self._upload_dir / file_id).unlink()

    def file_path(self, file_id: str) -> Path:
        return self._upload_dir / file_id

    @staticmethod
    def is_due(task: dict[str, Any], today: date) -> bool:
        return today >= date.fromisoformat(task["due_date"])
