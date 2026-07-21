"""Dashboard card API and registration guardrail tests."""

import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _decorators(function_name: str) -> set[str]:
    tree = ast.parse((ROOT / "custom_components/home_tasker/websocket.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name)
    return {ast.unparse(decorator) for decorator in function.decorator_list}


def test_dashboard_read_and_completion_commands_allow_authenticated_users():
    for function_name in ("ws_list", "ws_task_complete", "ws_history_list", "ws_attachment_sign_all"):
        assert "websocket_api.require_admin" not in _decorators(function_name)


def test_structural_and_history_mutations_remain_admin_only():
    for function_name in (
        "ws_group_create",
        "ws_group_update",
        "ws_group_delete",
        "ws_task_create",
        "ws_task_update",
        "ws_task_delete",
        "ws_history_delete",
        "ws_attachment_delete",
    ):
        assert "websocket_api.require_admin" in _decorators(function_name)


def test_dashboard_module_is_registered_and_removed_with_config_entry():
    source=(ROOT / "custom_components/home_tasker/__init__.py").read_text(encoding="utf-8")
    assert "frontend.add_extra_js_url(hass, CARD_JS_URL)" in source
    assert "frontend.remove_extra_js_url(hass, CARD_JS_URL)" in source
