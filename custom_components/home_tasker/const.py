"""Constants for Home Tasker."""

DOMAIN = "home_tasker"
PLATFORMS = ["calendar", "sensor", "todo"]
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1
EVENT_HOME_TASKER = f"{DOMAIN}_event"
PANEL_URL = "/home-tasker"
PANEL_TITLE = "Home Tasker"
PANEL_VERSION = "0.5.2"
FRONTEND_URL = f"/{DOMAIN}_frontend"
TRANSLATIONS_URL = f"/{DOMAIN}_translations"
PANEL_JS_URL = f"{FRONTEND_URL}/panel.js?v={PANEL_VERSION}"
CARD_JS_URL = f"{FRONTEND_URL}/dashboard-card.js?v={PANEL_VERSION}"
UPLOAD_URL = f"/api/{DOMAIN}/upload"
DOWNLOAD_URL = f"/api/{DOMAIN}/download"
ARCHIVE_URL = f"/api/{DOMAIN}/archive"
