"""Versioned persistence for Home Tasker."""

from __future__ import annotations

import asyncio
import contextlib
from copy import deepcopy
from datetime import date
from pathlib import Path
import shutil
import tempfile
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import FALLBACK_GROUP_NAME, STORAGE_KEY, STORAGE_VERSION
from .scheduler import initial_due, next_due


def _now() -> str:
    return dt_util.utcnow().isoformat()


def _schedule_signature(task: dict[str, Any]) -> tuple[Any, ...]:
    """Return only values that affect the active recurrence rule."""
    mode = task.get("recurrence_mode")
    frequency = task.get("frequency")
    values: list[Any] = [task.get("start_date") or None, mode, frequency, int(task.get("interval") or 1)]
    if mode == "fixed" and frequency == "weekly":
        values.append(tuple(sorted(int(day) for day in task.get("weekdays") or [])))
    elif mode == "fixed" and frequency == "monthly":
        values.append(task.get("day_of_month"))
    elif mode == "fixed" and frequency == "yearly":
        values.extend((task.get("month_of_year"), task.get("day_of_month")))
    return tuple(values)


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

    async def async_export_archive(self) -> tuple[dict[str, Any], dict[str, bytes]]:
        """Return a consistent copy of all persisted data and attachment content."""
        async with self._lock:
            data = deepcopy(self._data)
            files = await self._hass.async_add_executor_job(
                self._read_attachment_files, data["attachments"]
            )
            return data, files

    def _read_attachment_files(
        self, attachments: list[dict[str, Any]]
    ) -> dict[str, bytes]:
        return {
            item["id"]: self.file_path(item["id"]).read_bytes()
            for item in attachments
        }

    @staticmethod
    def validate_import(data: Any, files: dict[str, bytes]) -> dict[str, Any]:
        """Validate the current archive schema without legacy compatibility."""
        if not isinstance(data, dict) or set(data) != {
            "groups", "tasks", "history", "attachments"
        }:
            raise ValueError("invalid_archive_data")
        if not all(isinstance(data[key], expected) for key, expected in (
            ("groups", list), ("tasks", list), ("history", dict),
            ("attachments", list),
        )):
            raise ValueError("invalid_archive_data")
        groups = {item.get("id") for item in data["groups"] if isinstance(item, dict)}
        tasks = {item.get("id") for item in data["tasks"] if isinstance(item, dict)}
        attachments = {
            item.get("id"): item for item in data["attachments"]
            if isinstance(item, dict)
        }
        if (len(groups) != len(data["groups"]) or None in groups
                or len(tasks) != len(data["tasks"]) or None in tasks
                or len(attachments) != len(data["attachments"]) or None in attachments):
            raise ValueError("invalid_archive_ids")
        all_ids = groups | tasks | set(attachments)
        if any(not isinstance(item_id, str) or not item_id or "/" in item_id
               or "\\" in item_id or item_id in {".", ".."} for item_id in all_ids):
            raise ValueError("invalid_archive_ids")
        if any(item.get("group_id") not in groups for item in data["tasks"]):
            raise ValueError("invalid_archive_group")
        if any(item.get("task_id") not in tasks for item in data["attachments"]):
            raise ValueError("invalid_archive_attachment")
        if set(data["history"]) - tasks or set(files) != set(attachments):
            raise ValueError("invalid_archive_files")
        if any(not isinstance(entries, list)
               or any(not isinstance(entry, dict) for entry in entries)
               for entries in data["history"].values()):
            raise ValueError("invalid_archive_history")
        if any(len(files[file_id]) != int(item.get("size", -1)) for file_id, item in attachments.items()):
            raise ValueError("invalid_archive_file_size")
        return deepcopy(data)

    async def async_import_archive(
        self, data: Any, files: dict[str, bytes]
    ) -> None:
        """Clear the current store and replace it with one validated archive."""
        imported = self.validate_import(data, files)
        async with self._lock:
            old_data = self._data
            backup = await self._hass.async_add_executor_job(
                self._replace_attachment_files, files
            )
            self._data = imported
            try:
                await self._save()
            except Exception:
                self._data = old_data
                await self._hass.async_add_executor_job(
                    self._restore_attachment_files, backup
                )
                raise
            await self._hass.async_add_executor_job(self._discard_backup, backup)

    def _replace_attachment_files(self, files: dict[str, bytes]) -> Path | None:
        parent = self._upload_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="home_tasker_import_", dir=parent))
        backup = None
        try:
            for file_id, content in files.items():
                (staging / file_id).write_bytes(content)
            if self._upload_dir.exists():
                backup = Path(tempfile.mkdtemp(prefix="home_tasker_backup_", dir=parent))
                backup.rmdir()
                self._upload_dir.replace(backup)
            staging.replace(self._upload_dir)
            return backup
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            if backup and backup.exists() and not self._upload_dir.exists():
                backup.replace(self._upload_dir)
            raise

    def _restore_attachment_files(self, backup: Path | None) -> None:
        shutil.rmtree(self._upload_dir, ignore_errors=True)
        if backup and backup.exists():
            backup.replace(self._upload_dir)

    @staticmethod
    def _discard_backup(backup: Path | None) -> None:
        if backup:
            shutil.rmtree(backup, ignore_errors=True)

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

    def _normalize_nfc_tag_id(
        self, value: Any, exclude_task_id: str | None = None
    ) -> str | None:
        tag_id = str(value or "").strip() or None
        if tag_id and any(
            task["id"] != exclude_task_id and task.get("nfc_tag_id") == tag_id
            for task in self._data["tasks"]
        ):
            raise ValueError("nfc_tag_already_assigned")
        return tag_id

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

    async def async_add_task(self, payload: dict[str, Any], today: date | None = None) -> dict[str, Any]:
        due = initial_due(payload, today or dt_util.now().date())
        async with self._lock:
            now = _now()
            name = self._required_name(payload.get("name"))
            nfc_tag_id = self._normalize_nfc_tag_id(payload.get("nfc_tag_id"))
            group_id = self._resolve_task_group(
                payload.get("group_id"), payload.get("group_name"), now
            )
            task = {
                "id": uuid4().hex,
                **{k: payload.get(k) for k in ("name", "description", "assignee_user_id", "start_date", "recurrence_mode", "frequency", "interval", "weekdays", "day_of_month", "month_of_year")},
                "name": name,
                "nfc_tag_id": nfc_tag_id,
                "group_id": group_id,
                "anchor_day": due.day,
                "due_date": due.isoformat(),
                "schedule_anchor": due.isoformat(),
                "created_at": now,
                "updated_at": now,
            }
            self._data["tasks"].append(task)
            await self._save()
            return task

    async def async_update_task(self, task_id: str, payload: dict[str, Any], today: date | None = None) -> dict[str, Any]:
        async with self._lock:
            task = self._find("tasks", task_id)
            if "name" in payload:
                payload = {**payload, "name": self._required_name(payload["name"])}
            if "nfc_tag_id" in payload:
                payload = {
                    **payload,
                    "nfc_tag_id": self._normalize_nfc_tag_id(
                        payload["nfc_tag_id"], task_id
                    ),
                }
            if "group_id" in payload or "group_name" in payload:
                task["group_id"] = self._resolve_task_group(
                    payload.get("group_id"), payload.get("group_name"), _now()
                )
            schedule_keys = ("start_date", "recurrence_mode", "frequency", "interval", "weekdays", "day_of_month", "month_of_year")
            old_schedule = _schedule_signature(task)
            for key in ("name", "description", "assignee_user_id", "nfc_tag_id", *schedule_keys):
                if key in payload:
                    task[key] = payload[key]
            schedule_changed = _schedule_signature(task) != old_schedule
            if schedule_changed:
                due = initial_due(task, today or dt_util.now().date())
                task["due_date"] = due.isoformat()
                task["anchor_day"] = due.day
                task["schedule_anchor"] = due.isoformat()
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
            chronological = sorted(entries, key=lambda entry: entry["recorded_at"])
            original_due = chronological[0]["due_before"]
            remaining = [entry for entry in chronological if entry["id"] != entry_id]
            replay_task = {**task, "due_date": original_due}
            for entry in remaining:
                entry["due_before"] = replay_task["due_date"]
                entry["due_after"] = next_due(
                    replay_task, date.fromisoformat(entry["completion_date"])
                ).isoformat()
                replay_task["due_date"] = entry["due_after"]
            self._data["history"][task_id] = remaining
            task["due_date"] = replay_task["due_date"]
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
