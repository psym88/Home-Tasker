"""Tests for the Home Tasker config flow."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.data_entry_flow import AbortFlow, FlowResultType

from custom_components.home_tasker.config_flow import HomeTaskerConfigFlow
from custom_components.home_tasker.const import DOMAIN


def test_user_flow_shows_form_and_creates_entry() -> None:
    """Test the complete user-initiated setup flow."""
    flow = HomeTaskerConfigFlow()

    with (
        patch.object(flow, "async_set_unique_id", AsyncMock()) as set_unique_id,
        patch.object(flow, "_abort_if_unique_id_configured") as abort_if_configured,
    ):
        result = asyncio.run(flow.async_step_user())

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = asyncio.run(flow.async_step_user({}))

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home Tasker"
    assert result["data"] == {}
    assert set_unique_id.await_count == 2
    set_unique_id.assert_awaited_with(DOMAIN)
    assert abort_if_configured.call_count == 2


def test_user_flow_aborts_when_already_configured() -> None:
    """Test that a second Home Tasker entry is rejected."""
    flow = HomeTaskerConfigFlow()

    with (
        patch.object(flow, "async_set_unique_id", AsyncMock()),
        patch.object(
            flow,
            "_abort_if_unique_id_configured",
            Mock(side_effect=AbortFlow("already_configured")),
        ),
        pytest.raises(AbortFlow, match="already_configured"),
    ):
        asyncio.run(flow.async_step_user())
