"""Native Home Assistant file upload tests."""

from types import SimpleNamespace
from uuid import uuid4

from homeassistant.components.file_upload import DOMAIN, FileUploadData

from custom_components.home_tasker.http import _build_archive
from custom_components.home_tasker.websocket import (
    _parse_uploaded_archive,
    _read_uploaded_file,
)


def test_native_upload_is_consumed_and_removed(tmp_path):
    file_id = uuid4().hex
    filename = "manual.pdf"
    upload_data = FileUploadData(tmp_path, {file_id: filename})
    upload_dir = upload_data.file_dir(file_id)
    upload_dir.mkdir()
    upload_data.file_path(file_id).write_bytes(b"document")
    hass = SimpleNamespace(data={DOMAIN: upload_data})

    assert _read_uploaded_file(hass, file_id) == (
        filename,
        "application/pdf",
        b"document",
    )
    assert file_id not in upload_data.files
    assert not upload_dir.exists()


def test_native_backup_upload_is_parsed_and_removed(tmp_path):
    file_id = uuid4().hex
    filename = "home-tasker.zip"
    upload_data = FileUploadData(tmp_path, {file_id: filename})
    upload_dir = upload_data.file_dir(file_id)
    upload_dir.mkdir()
    data = {"tasks": [], "history": {}, "attachments": []}
    upload_data.file_path(file_id).write_bytes(_build_archive(data, {}))
    hass = SimpleNamespace(data={DOMAIN: upload_data})

    assert _parse_uploaded_archive(hass, file_id) == (data, {})
    assert file_id not in upload_data.files
    assert not upload_dir.exists()
