"""Regression tests for Bronze quality-scale artifacts."""

import json
from pathlib import Path

from PIL import Image


INTEGRATION_DIR = Path("custom_components/home_tasker")


def test_brand_icons_match_home_assistant_requirements() -> None:
    """Brand icons are transparent PNGs in both required resolutions."""
    for filename, size in (("icon.png", (256, 256)), ("icon@2x.png", (512, 512))):
        with Image.open(INTEGRATION_DIR / "brand" / filename) as image:
            assert image.format == "PNG"
            assert image.mode == "RGBA"
            assert image.size == size
            assert image.getpixel((0, 0))[3] == 0


def test_versions_stay_aligned() -> None:
    """Backend and frontend cache versions match the manifest release."""
    version = json.loads((INTEGRATION_DIR / "manifest.json").read_text())["version"]
    assert f'PANEL_VERSION = "{version}"' in (INTEGRATION_DIR / "const.py").read_text()
    assert f'VERSION = "{version}"' in (
        INTEGRATION_DIR / "frontend/panel.js"
    ).read_text()
