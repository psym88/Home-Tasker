"""Versioned persistence for Home Tasker."""

from __future__ import annotations

import asyncio
import contextlib
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import shutil
import tempfile
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import STORAGE_KEY, STORAGE_VERSION
from .due import (
    normalize_task_due,
    parse_task_due,
    task_due_date,
    task_due_datetime,
    task_due_with_date,
)
from .scheduler import initial_due, next_due, validate_schedule


_IMPORTED_TASK_FIELDS = {
    "task_id",
    "task_name",
    "task_description",
    "assignee_id",
    "label_ids",
    "nfc_tag_id",
    "task_due",
    "schedule_start_date",
    "schedule_anchor_date",
    "schedule_type",
    "schedule_unit",
    "schedule_interval",
    "schedule_weekdays",
    "schedule_day",
    "schedule_month",
}

_SCHEDULE_FIELDS = (
    "schedule_start_date",
    "schedule_type",
    "schedule_unit",
    "schedule_interval",
    "schedule_weekdays",
    "schedule_day",
    "schedule_month",
)


def _now() -> str:
    return dt_util.utcnow().isoformat()


def _schedule_signature(task: dict[str, Any]) -> tuple[Any, ...]:
    """Return only values that affect the active recurrence rule."""
    mode = task.get("schedule_type")
    schedule_unit = task.get("schedule_unit")
    values: list[Any] = [task.get("schedule_start_date") or None, mode, schedule_unit, int(task.get("schedule_interval") or 1)]
    if mode == "fixed" and schedule_unit == "weekly":
        values.append(tuple(sorted(int(day) for day in task.get("schedule_weekdays") or [])))
    elif mode == "fixed" and schedule_unit == "monthly":
        values.append(task.get("schedule_day"))
    elif mode == "fixed" and schedule_unit == "yearly":
        values.extend((task.get("schedule_month"), task.get("schedule_day")))
    return tuple(values)


def _normalize_schedule(task: dict[str, Any]) -> dict[str, Any]:
    """Clear recurrence values that do not belong to the active rule."""
    normalized = dict(task)
    normalized["schedule_weekdays"] = (
        list(task.get("schedule_weekdays") or [])
        if task.get("schedule_type") == "fixed"
        and task.get("schedule_unit") == "weekly"
        else []
    )
    normalized["schedule_day"] = (
        task.get("schedule_day")
        if task.get("schedule_type") == "fixed"
        and task.get("schedule_unit") in {"monthly", "yearly"}
        else None
    )
    normalized["schedule_month"] = (
        task.get("schedule_month")
        if task.get("schedule_type") == "fixed"
        and task.get("schedule_unit") == "yearly"
        else None
    )
    return normalized


def _validate_imported_task(task: Any) -> None:
    """Reject task records that cannot be consumed by runtime components."""
    if not isinstance(task, dict) or not _IMPORTED_TASK_FIELDS <= task.keys():
        raise ValueError("invalid_archive_task")
    if not isinstance(task["task_name"], str) or not task["task_name"].strip():
        raise ValueError("invalid_archive_task")
    if task["schedule_type"] not in {"fixed", "sliding"}:
        raise ValueError("invalid_archive_task")
    if task["schedule_unit"] not in {"daily", "weekly", "monthly", "yearly"}:
        raise ValueError("invalid_archive_task")
    if (
        isinstance(task["schedule_interval"], bool)
        or not isinstance(task["schedule_interval"], int)
        or task["schedule_interval"] < 1
    ):
        raise ValueError("invalid_archive_task")
    if not isinstance(task["schedule_weekdays"], list) or any(
        isinstance(day, bool) or not isinstance(day, int) or not 0 <= day <= 6
        for day in task["schedule_weekdays"]
    ):
        raise ValueError("invalid_archive_task")
    if not isinstance(task["label_ids"], list) or any(
        not isinstance(label_id, str) for label_id in task["label_ids"]
    ):
        raise ValueError("invalid_archive_task")
    if any(
        value is not None and not isinstance(value, str)
        for value in (
            task["task_description"],
            task["assignee_id"],
            task["nfc_tag_id"],
        )
    ):
        raise ValueError("invalid_archive_task")
    if task["schedule_day"] != "last" and task["schedule_day"] is not None and (
        isinstance(task["schedule_day"], bool)
        or not isinstance(task["schedule_day"], int)
        or not 1 <= task["schedule_day"] <= 31
    ):
        raise ValueError("invalid_archive_task")
    if task["schedule_month"] is not None and (
        isinstance(task["schedule_month"], bool)
        or not isinstance(task["schedule_month"], int)
        or not 1 <= task["schedule_month"] <= 12
    ):
        raise ValueError("invalid_archive_task")
    try:
        normalize_task_due(task["task_due"])
        date.fromisoformat(task["schedule_anchor_date"])
        if task["schedule_start_date"] is not None:
            date.fromisoformat(task["schedule_start_date"])
        validate_schedule(task)
    except (KeyError, TypeError, ValueError, OverflowError) as err:
        raise ValueError("invalid_archive_task") from err


class HomeTaskerStore:
    """Serialize mutations and persist one compact snapshot."""

    def __init__(self, hass: HomeAssistant, upload_dir: Path) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._upload_dir = upload_dir
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = {
            "tasks": [], "history": {}, "attachments": []
        }

    async def async_load(self) -> None:
        if stored := await self._store.async_load():
            self._data = {key: stored.get(key, default) for key, default in self._data.items()}

    def snapshot(self) -> dict[str, Any]:
        return {key: list(self._data[key]) for key in ("tasks", "attachments")}

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
            item["attachment_id"]: self.file_path(item["attachment_id"]).read_bytes()
            for item in attachments
        }

    @staticmethod
    def validate_import(data: Any, files: dict[str, bytes]) -> dict[str, Any]:
        """Validate the current archive schema without legacy compatibility."""
        if not isinstance(data, dict) or set(data) != {
            "tasks", "history", "attachments"
        }:
            raise ValueError("invalid_archive_data")
        if not all(isinstance(data[key], expected) for key, expected in (
            ("tasks", list), ("history", dict),
            ("attachments", list),
        )):
            raise ValueError("invalid_archive_data")
        for task in data["tasks"]:
            _validate_imported_task(task)
        tasks = {item.get("task_id") for item in data["tasks"] if isinstance(item, dict)}
        attachments = {
            item.get("attachment_id"): item for item in data["attachments"]
            if isinstance(item, dict)
        }
        if (len(tasks) != len(data["tasks"]) or None in tasks
                or len(attachments) != len(data["attachments"]) or None in attachments):
            raise ValueError("invalid_archive_ids")
        all_ids = tasks | set(attachments)
        if any(not isinstance(item_id, str) or not item_id or "/" in item_id
               or "\\" in item_id or item_id in {".", ".."} for item_id in all_ids):
            raise ValueError("invalid_archive_ids")
        nfc_tag_ids = [
            task["nfc_tag_id"] for task in data["tasks"] if task["nfc_tag_id"]
        ]
        if len(nfc_tag_ids) != len(set(nfc_tag_ids)):
            raise ValueError("invalid_archive_task")
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
        """Add new archive records without overwriting existing data."""
        imported = self.validate_import(data, files)
        async with self._lock:
            old_data = self._data
            existing_task_ids = {task["task_id"] for task in old_data["tasks"]}
            existing_attachment_ids = {
                attachment["attachment_id"] for attachment in old_data["attachments"]
            }
            new_tasks = [
                task for task in imported["tasks"]
                if task["task_id"] not in existing_task_ids
            ]
            new_task_ids = {task["task_id"] for task in new_tasks}
            new_attachments = [
                attachment for attachment in imported["attachments"]
                if attachment["task_id"] in new_task_ids
                and attachment["attachment_id"] not in existing_attachment_ids
                and not self.file_path(attachment["attachment_id"]).exists()
            ]
            new_attachment_ids = {
                attachment["attachment_id"] for attachment in new_attachments
            }
            merged = deepcopy(old_data)
            merged["tasks"].extend(new_tasks)
            merged["attachments"].extend(new_attachments)
            merged["history"].update({
                task_id: entries
                for task_id, entries in imported["history"].items()
                if task_id in new_task_ids
            })
            backup = await self._hass.async_add_executor_job(
                self._merge_attachment_files,
                {
                    file_id: content for file_id, content in files.items()
                    if file_id in new_attachment_ids
                },
            )
            self._data = merged
            try:
                await self._save()
            except Exception:
                self._data = old_data
                await self._hass.async_add_executor_job(
                    self._restore_attachment_files, backup
                )
                raise
            await self._hass.async_add_executor_job(self._discard_backup, backup)

    def _merge_attachment_files(self, files: dict[str, bytes]) -> Path | None:
        parent = self._upload_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="home_tasker_import_", dir=parent))
        backup = None
        try:
            if self._upload_dir.exists():
                shutil.copytree(self._upload_dir, staging, dirs_exist_ok=True)
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
    def tasks(self) -> list[dict[str, Any]]:
        return list(self._data["tasks"])

    def _find(self, kind: str, item_id: str) -> dict[str, Any]:
        id_key = {"tasks": "task_id", "attachments": "attachment_id"}[kind]
        item = next((x for x in self._data[kind] if x[id_key] == item_id), None)
        if item is None:
            raise ValueError(f"unknown_{kind[:-1]}")
        return item

    @staticmethod
    def _required_name(value: Any) -> str:
        name = str(value or "").strip()
        if not name:
            raise ValueError("name_required")
        return name

    def _normalize_nfc_tag_id(
        self, value: Any, exclude_task_id: str | None = None
    ) -> str | None:
        tag_id = str(value or "").strip() or None
        if tag_id and any(
            task["task_id"] != exclude_task_id and task.get("nfc_tag_id") == tag_id
            for task in self._data["tasks"]
        ):
            raise ValueError("nfc_tag_already_assigned")
        return tag_id

    def task(self, task_id: str) -> dict[str, Any]:
        """Return one task for validation by the API layer."""
        return dict(self._find("tasks", task_id))

    async def _save(self) -> None:
        await self._store.async_save(self._data)

    async def async_add_task(self, payload: dict[str, Any], today: date | None = None) -> dict[str, Any]:
        due = initial_due(payload, today or dt_util.now().date())
        task_due = normalize_task_due(str(payload.get("task_due") or due.isoformat()))
        parsed_due = parse_task_due(task_due)
        due_date = (
            dt_util.as_local(parsed_due).date()
            if isinstance(parsed_due, datetime)
            else parsed_due
        )
        async with self._lock:
            name = self._required_name(payload.get("task_name"))
            nfc_tag_id = self._normalize_nfc_tag_id(payload.get("nfc_tag_id"))
            task = _normalize_schedule({
                "task_id": uuid4().hex,
                **{k: payload.get(k) for k in ("task_name", "task_description", "assignee_id", *_SCHEDULE_FIELDS)},
                "task_name": name,
                "label_ids": list(dict.fromkeys(payload.get("label_ids") or [])),
                "nfc_tag_id": nfc_tag_id,
                "task_due": task_due,
                "schedule_anchor_date": due_date.isoformat(),
            })
            self._data["tasks"].append(task)
            await self._save()
            return task

    async def async_update_task(self, task_id: str, payload: dict[str, Any], today: date | None = None) -> dict[str, Any]:
        async with self._lock:
            task = self._find("tasks", task_id)
            if "task_name" in payload:
                payload = {**payload, "task_name": self._required_name(payload["task_name"])}
            if "nfc_tag_id" in payload:
                payload = {
                    **payload,
                    "nfc_tag_id": self._normalize_nfc_tag_id(
                        payload["nfc_tag_id"], task_id
                    ),
                }
            old_schedule = _schedule_signature(task)
            schedule_update = any(key in payload for key in _SCHEDULE_FIELDS)
            normalized_schedule = None
            if schedule_update:
                merged_schedule = {
                    **task,
                    **{key: payload[key] for key in _SCHEDULE_FIELDS if key in payload},
                }
                validate_schedule(merged_schedule)
                normalized_schedule = _normalize_schedule(merged_schedule)
            if "label_ids" in payload:
                task["label_ids"] = list(dict.fromkeys(payload["label_ids"]))
            for key in ("task_name", "task_description", "assignee_id", "nfc_tag_id", "task_due"):
                if key in payload:
                    task[key] = payload[key]
            if normalized_schedule is not None:
                for key in _SCHEDULE_FIELDS:
                    task[key] = normalized_schedule[key]
            schedule_changed = _schedule_signature(task) != old_schedule
            if schedule_changed:
                due = initial_due(task, today or dt_util.now().date())
                task["task_due"] = task_due_with_date(task, due)
                task["schedule_anchor_date"] = due.isoformat()
            elif "task_due" in payload:
                task["task_due"] = normalize_task_due(str(payload["task_due"]))
                due = task_due_date(task)
                task["schedule_start_date"] = due.isoformat()
                task["schedule_anchor_date"] = due.isoformat()
            await self._save()
            return task

    async def async_delete_task(self, task_id: str) -> None:
        async with self._lock:
            self._find("tasks", task_id)
            file_ids = [a["attachment_id"] for a in self._data["attachments"] if a["task_id"] == task_id]
            self._data["tasks"] = [t for t in self._data["tasks"] if t["task_id"] != task_id]
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
            task_due_before = task["task_due"]
            next_date = next_due(task, date.fromisoformat(completion_date))
            task_due_after = task_due_with_date(task, next_date)
            record = {
                "history_entry_id": uuid4().hex,
                "completion_date": completion_date,
                "recorded_at": _now(),
                "user_id": user_id,
                "user_name": user_name,
                "notes": str(notes or "").strip() or None,
                "task_due_before": task_due_before,
                "task_due_after": task_due_after,
            }
            task["task_due"] = task_due_after
            self._data["history"].setdefault(task_id, []).append(record)
            await self._save()
            return task

    def history(self, task_id: str) -> list[dict[str, Any]]:
        self._find("tasks", task_id)
        return sorted(self._data["history"].get(task_id, []), key=lambda x: x["recorded_at"], reverse=True)

    async def async_delete_history(self, task_id: str, history_entry_id: str) -> dict[str, Any]:
        async with self._lock:
            task = self._find("tasks", task_id)
            entries = self._data["history"].get(task_id, [])
            removed = next((x for x in entries if x["history_entry_id"] == history_entry_id), None)
            if removed is None:
                raise ValueError("unknown_history_entry")
            chronological = sorted(entries, key=lambda entry: entry["recorded_at"])
            original_due = chronological[0]["task_due_before"]
            remaining = [entry for entry in chronological if entry["history_entry_id"] != history_entry_id]
            replay_task = {**task, "task_due": original_due}
            for entry in remaining:
                entry["task_due_before"] = replay_task["task_due"]
                entry["task_due_after"] = task_due_with_date(
                    replay_task,
                    next_due(replay_task, date.fromisoformat(entry["completion_date"])),
                )
                replay_task["task_due"] = entry["task_due_after"]
            self._data["history"][task_id] = remaining
            task["task_due"] = replay_task["task_due"]
            await self._save()
            return task

    def attachment(self, attachment_id: str) -> dict[str, Any] | None:
        return next((x for x in self._data["attachments"] if x["attachment_id"] == attachment_id), None)

    async def async_add_attachment(self, task_id: str, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        async with self._lock:
            self._find("tasks", task_id)
            attachment = {"attachment_id": uuid4().hex, "task_id": task_id, "filename": filename, "content_type": content_type, "size": len(data), "uploaded_at": _now()}
            await self._hass.async_add_executor_job(self._write, attachment["attachment_id"], data)
            self._data["attachments"].append(attachment)
            await self._save()
            return attachment

    async def async_delete_attachment(self, attachment_id: str) -> None:
        async with self._lock:
            if self.attachment(attachment_id) is None:
                raise ValueError("unknown_attachment")
            self._data["attachments"] = [x for x in self._data["attachments"] if x["attachment_id"] != attachment_id]
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
    def is_due(task: dict[str, Any], now: datetime) -> bool:
        return task_due_datetime(task) <= now
