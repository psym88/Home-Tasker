"""Full archive import and export tests."""

import ast
import asyncio
from pathlib import Path

import pytest

from custom_components.home_tasker.http import _build_archive, _parse_archive
from custom_components.home_tasker.store import HomeTaskerStore


class FakeHass:
    async def async_add_executor_job(self, function, *args):
        return function(*args)


class MemoryStore:
    async def async_save(self, data):
        self.data = data


def archive_task(task_id: str, task_name: str) -> dict:
    return {
        "task_id": task_id,
        "task_name": task_name,
        "task_description": None,
        "assignee_id": None,
        "label_ids": [],
        "nfc_tag_id": None,
        "task_due": "2026-07-24",
        "schedule_start_date": None,
        "schedule_anchor_date": "2026-07-24",
        "schedule_type": "sliding",
        "schedule_unit": "monthly",
        "schedule_interval": 1,
        "schedule_weekdays": [],
        "schedule_day": None,
        "schedule_month": None,
    }


def archive_store(tmp_path: Path) -> HomeTaskerStore:
    store = HomeTaskerStore.__new__(HomeTaskerStore)
    store._hass = FakeHass()
    store._store = MemoryStore()
    store._upload_dir = tmp_path / "uploads"
    store._lock = asyncio.Lock()
    store._data = {
        "tasks": [archive_task("task-1", "Bins")],
        "history": {"task-1": [{"history_entry_id": "history-1"}]},
        "attachments": [{"attachment_id": "file-1", "task_id": "task-1", "size": 7}],
    }
    store._upload_dir.mkdir(parents=True)
    (store._upload_dir / "file-1").write_bytes(b"content")
    return store


def test_export_and_import_preserve_existing_data_and_add_new_tasks(tmp_path):
    async def run():
        source = archive_store(tmp_path / "source")
        source._data["tasks"][0]["task_name"] = "Imported conflict"
        source._data["tasks"].append(archive_task("task-2", "New task"))
        source._data["history"]["task-2"] = [{"history_entry_id": "history-2"}]
        source._data["attachments"].append(
            {"attachment_id": "file-2", "task_id": "task-2", "size": 3}
        )
        source._data["attachments"].append(
            {"attachment_id": "file-3", "task_id": "task-2", "size": 5}
        )
        (source._upload_dir / "file-2").write_bytes(b"new")
        (source._upload_dir / "file-3").write_bytes(b"added")
        data, files = await source.async_export_archive()

        target = archive_store(tmp_path / "target")
        target._data["tasks"][0]["task_name"] = "Existing data"
        (target._upload_dir / "file-2").write_bytes(b"keep")
        (target._upload_dir / "obsolete").write_bytes(b"old")
        await target.async_import_archive(data, files)

        assert [
            (task["task_id"], task["task_name"]) for task in target._data["tasks"]
        ] == [
            ("task-1", "Existing data"),
            ("task-2", "New task"),
        ]
        assert target._data["tasks"][1] == source._data["tasks"][1]
        assert target._data["history"]["task-1"] == [
            {"history_entry_id": "history-1"}
        ]
        assert target._data["history"]["task-2"] == [
            {"history_entry_id": "history-2"}
        ]
        assert target._data["attachments"] == [
            {"attachment_id": "file-1", "task_id": "task-1", "size": 7},
            {"attachment_id": "file-3", "task_id": "task-2", "size": 5},
        ]
        assert target._store.data == target._data
        assert sorted(path.name for path in target._upload_dir.iterdir()) == [
            "file-1", "file-2", "file-3", "obsolete"
        ]
        assert (target._upload_dir / "file-1").read_bytes() == b"content"
        assert (target._upload_dir / "file-2").read_bytes() == b"keep"
        assert (target._upload_dir / "file-3").read_bytes() == b"added"

    asyncio.run(run())


def test_import_rejects_incomplete_or_inconsistent_archives(tmp_path):
    store = archive_store(tmp_path)
    data = store._data

    with pytest.raises(ValueError, match="invalid_archive_files"):
        store.validate_import(data, {})
    with pytest.raises(ValueError, match="invalid_archive_ids"):
        store.validate_import(
            {**data, "attachments": [{**data["attachments"][0], "attachment_id": "../file"}]},
            {"../file": b"content"},
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"task_due": "not-a-date"},
        {"schedule_interval": 0},
        {"schedule_type": "fixed", "schedule_unit": "weekly"},
        {"label_ids": [None]},
    ],
)
def test_import_rejects_invalid_task_records(patch):
    task = {**archive_task("task-1", "Bins"), **patch}

    with pytest.raises(ValueError, match="invalid_archive_task"):
        HomeTaskerStore.validate_import(
            {"tasks": [task], "history": {}, "attachments": []},
            {},
        )


def test_import_rejects_tasks_with_missing_runtime_fields():
    with pytest.raises(ValueError, match="invalid_archive_task"):
        HomeTaskerStore.validate_import(
            {"tasks": [{"task_id": "broken"}], "history": {}, "attachments": []},
            {},
        )


def test_archive_helpers_round_trip_and_views_offload_zip_work():
    data = {
        "tasks": [archive_task("task-1", "Bins")],
        "history": {},
        "attachments": [
            {"attachment_id": "file-1", "task_id": "task-1", "size": 7}
        ],
    }
    content = _build_archive(data, {"file-1": b"content"})

    assert _parse_archive(content) == (data, {"file-1": b"content"})

    source = Path("custom_components/home_tasker/http.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    archive_view = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ArchiveView"
    )
    methods = {
        node.name: ast.unparse(node)
        for node in archive_view.body
        if isinstance(node, ast.AsyncFunctionDef)
    }
    assert "async_add_executor_job(_build_archive" in methods["get"]
    assert "async_add_executor_job(_parse_archive" in methods["post"]
