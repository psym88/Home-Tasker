"""Authenticated file upload and download."""

from datetime import timedelta
from io import BytesIO
import json
import zipfile

from aiohttp import web
from homeassistant.components.http import KEY_HASS_USER, HomeAssistantView
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import Context, HomeAssistant

from .const import ARCHIVE_URL, DOWNLOAD_URL, UPLOAD_URL
from .events import async_fire_home_tasker_event
from .helpers import get_store

MAX_ARCHIVE_SIZE = 100 * 1024 * 1024
ARCHIVE_FORMAT = 1


def _build_archive(data: dict, files: dict[str, bytes]) -> bytes:
    """Build an archive outside the Home Assistant event loop."""
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "home-tasker.json",
            json.dumps({"format": ARCHIVE_FORMAT, "data": data}, ensure_ascii=False),
        )
        for file_id, content in files.items():
            archive.writestr(f"attachments/{file_id}", content)
    return output.getvalue()


def _parse_archive(content: bytes) -> tuple[dict, dict[str, bytes]]:
    """Parse and decompress an archive outside the Home Assistant event loop."""
    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or "home-tasker.json" not in names or any(
            name != "home-tasker.json" and not name.startswith("attachments/")
            for name in names
        ):
            raise ValueError("invalid_archive")
        if sum(item.file_size for item in archive.infolist()) > MAX_ARCHIVE_SIZE:
            raise ValueError("archive_too_large")
        manifest = json.loads(archive.read("home-tasker.json"))
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"format", "data"}
            or manifest["format"] != ARCHIVE_FORMAT
        ):
            raise ValueError("unsupported_archive_format")
        files = {
            name.removeprefix("attachments/"): archive.read(name)
            for name in names
            if name.startswith("attachments/") and not name.endswith("/")
        }
    return manifest["data"], files


def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(UploadView)
    hass.http.register_view(DownloadView)
    hass.http.register_view(ArchiveView)


class UploadView(HomeAssistantView):
    url = UPLOAD_URL
    name = "api:home_tasker:upload"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        store = get_store(request.app["hass"])
        if store is None:
            raise web.HTTPServiceUnavailable()
        reader = await request.multipart()
        task_id = None
        uploaded = None
        async for part in reader:
            if part.name == "task_id": task_id = (await part.text()).strip()
            elif part.name == "file": uploaded = (part.filename or "upload", part.headers.get("Content-Type", "application/octet-stream"), await part.read())
        if not task_id or uploaded is None:
            raise web.HTTPBadRequest(text="task_id and file are required")
        try:
            record = await store.async_add_attachment(task_id, *uploaded)
        except ValueError as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        async_fire_home_tasker_event(
            request.app["hass"],
            "created",
            "attachment",
            record["attachment_id"],
            context=Context(user_id=request[KEY_HASS_USER].id),
            task_id=task_id,
        )
        return web.json_response({
            **record,
            "signed_url": async_sign_path(
                request.app["hass"],
                f"{DOWNLOAD_URL}/{record['attachment_id']}",
                timedelta(hours=1),
            ),
        })


class DownloadView(HomeAssistantView):
    url = f"{DOWNLOAD_URL}/{{attachment_id}}"
    name = "api:home_tasker:download"
    requires_auth = True

    async def get(self, request: web.Request, attachment_id: str) -> web.StreamResponse:
        store = get_store(request.app["hass"])
        record = store.attachment(attachment_id) if store else None
        if record is None or not store.file_path(attachment_id).exists():
            raise web.HTTPNotFound()
        return web.FileResponse(store.file_path(attachment_id), headers={"Content-Type": record["content_type"], "Content-Disposition": f'inline; filename="{record["filename"]}"'})


class ArchiveView(HomeAssistantView):
    url = ARCHIVE_URL
    name = "api:home_tasker:archive"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        store = get_store(request.app["hass"])
        if store is None:
            raise web.HTTPServiceUnavailable()
        data, files = await store.async_export_archive()
        body = await request.app["hass"].async_add_executor_job(
            _build_archive, data, files
        )
        return web.Response(
            body=body,
            content_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="home-tasker-backup.zip"'},
        )

    async def post(self, request: web.Request) -> web.Response:
        if request.content_length is not None and request.content_length > MAX_ARCHIVE_SIZE:
            raise web.HTTPRequestEntityTooLarge(
                max_size=MAX_ARCHIVE_SIZE, actual_size=request.content_length
            )
        content = await request.read()
        try:
            data, files = await request.app["hass"].async_add_executor_job(
                _parse_archive, content
            )
        except (ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        store = get_store(request.app["hass"])
        if store is None:
            raise web.HTTPServiceUnavailable()
        try:
            await store.async_import_archive(data, files)
        except ValueError as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        async_fire_home_tasker_event(
            request.app["hass"],
            "imported",
            "archive",
            context=Context(user_id=request[KEY_HASS_USER].id),
        )
        return web.json_response({"imported": True})
