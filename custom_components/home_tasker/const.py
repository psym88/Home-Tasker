"""Constants for Home Tasker."""

DOMAIN = "home_tasker"
PLATFORMS = ["binary_sensor", "calendar"]
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1
SIGNAL_UPDATED = f"{DOMAIN}_updated"
PANEL_URL = "/home-tasker"
PANEL_TITLE = "Home Tasker"
PANEL_VERSION = "0.3.3"
FALLBACK_GROUP_NAME = "Tasks"
FRONTEND_URL = f"/{DOMAIN}_frontend"
TRANSLATIONS_URL = f"/{DOMAIN}_translations"
PANEL_JS_URL = f"{FRONTEND_URL}/panel.js?v={PANEL_VERSION}"
CARD_JS_URL = f"{FRONTEND_URL}/dashboard-card.js?v={PANEL_VERSION}"
UPLOAD_URL = f"/api/{DOMAIN}/upload"
DOWNLOAD_URL = f"/api/{DOMAIN}/download"
ARCHIVE_URL = f"/api/{DOMAIN}/archive"
