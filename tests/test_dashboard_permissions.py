"""Dashboard card API and registration guardrail tests."""

import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _decorators(function_name: str) -> set[str]:
    tree = ast.parse((ROOT / "custom_components/home_tasker/websocket.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name)
    return {ast.unparse(decorator) for decorator in function.decorator_list}


def test_dashboard_task_commands_allow_authenticated_users():
    for function_name in (
        "ws_list",
        "ws_task_create",
        "ws_task_update",
        "ws_task_delete",
        "ws_task_preview_next_due",
        "ws_task_complete",
        "ws_history_list",
        "ws_history_delete",
        "ws_attachment_delete",
    ):
        assert "websocket_api.require_admin" not in _decorators(function_name)


def test_upload_allows_authenticated_users():
    source=(ROOT / "custom_components/home_tasker/http.py").read_text(encoding="utf-8")
    assert 'request["hass_user"].is_admin' not in source
    assert '"signed_url": async_sign_path(' in source


def test_only_sidepanel_requires_admin():
    component = ROOT / "custom_components/home_tasker"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in component.rglob("*.py"))
    assert "websocket_api.require_admin" not in sources
    assert sources.count("require_admin=True") == 1


def test_dashboard_module_is_registered_and_removed_with_config_entry():
    source=(ROOT / "custom_components/home_tasker/__init__.py").read_text(encoding="utf-8")
    assert "frontend.add_extra_js_url(hass, CARD_JS_URL)" in source
    assert "frontend.remove_extra_js_url(hass, CARD_JS_URL)" in source


def test_nfc_listener_lifecycle_is_bound_to_config_entry():
    source=(ROOT / "custom_components/home_tasker/__init__.py").read_text(encoding="utf-8")
    assert "entry.async_on_unload(nfc.async_setup_listener(hass, store))" in source


def test_native_tag_integration_is_loaded_as_a_dependency():
    import json

    manifest = json.loads((ROOT / "custom_components/home_tasker/manifest.json").read_text(encoding="utf-8"))
    assert "tag" in manifest["dependencies"]


def test_frontend_and_consolidated_translations_are_registered_as_static_paths():
    source=(ROOT / "custom_components/home_tasker/__init__.py").read_text(encoding="utf-8")
    assert "StaticPathConfig(FRONTEND_URL, str(frontend_dir), False)" in source
    assert "StaticPathConfig(TRANSLATIONS_URL, str(translations_dir), False)" in source
    component=ROOT / "custom_components/home_tasker"
    assert list(component.rglob("de.json")) == [component / "translations/de.json"]
    assert list(component.rglob("en.json")) == [component / "translations/en.json"]
