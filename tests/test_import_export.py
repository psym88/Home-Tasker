"""Full archive import and export tests."""

import asyncio
from pathlib import Path

import pytest

from custom_components.home_tasker.store import HomeTaskerStore


class FakeHass:
    async def async_add_executor_job(self, function, *args):
        return function(*args)


class MemoryStore:
    async def async_save(self, data):
        self.data = data


def archive_store(tmp_path: Path) -> HomeTaskerStore:
    store = HomeTaskerStore.__new__(HomeTaskerStore)
    store._hass = FakeHass()
    store._store = MemoryStore()
    store._upload_dir = tmp_path / "uploads"
    store._lock = asyncio.Lock()
    store._data = {
        "tasks": [{"task_id": "task-1", "task_name": "Bins"}],
        "history": {"task-1": [{"history_entry_id": "history-1"}]},
        "attachments": [{"attachment_id": "file-1", "task_id": "task-1", "size": 7}],
    }
    store._upload_dir.mkdir(parents=True)
    (store._upload_dir / "file-1").write_bytes(b"content")
    return store


def test_export_and_import_replace_all_data_and_files(tmp_path):
    async def run():
        source = archive_store(tmp_path / "source")
        data, files = await source.async_export_archive()

        target = archive_store(tmp_path / "target")
        target._data["tasks"][0]["task_name"] = "Old data"
        (target._upload_dir / "obsolete").write_bytes(b"old")
        await target.async_import_archive(data, files)

        assert target._data == source._data
        assert target._store.data == source._data
        assert sorted(path.name for path in target._upload_dir.iterdir()) == ["file-1"]
        assert (target._upload_dir / "file-1").read_bytes() == b"content"

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
