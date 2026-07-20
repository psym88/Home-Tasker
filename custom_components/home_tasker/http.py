"""Authenticated file upload and download."""

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOWNLOAD_URL, UPLOAD_URL
from .helpers import get_store


def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(UploadView)
    hass.http.register_view(DownloadView)


class UploadView(HomeAssistantView):
    url = UPLOAD_URL
    name = "api:home_tasker:upload"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        if not request["hass_user"].is_admin:
            raise web.HTTPUnauthorized()
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
        return web.json_response(record)


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
