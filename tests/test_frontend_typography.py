"""Regression tests for Home Assistant-aligned frontend typography."""

from pathlib import Path


PANEL = Path(__file__).parents[1] / "custom_components/home_tasker/frontend/panel.js"


def panel_source() -> str:
    return PANEL.read_text(encoding="utf-8")


def test_due_date_preview_uses_normal_body_typography() -> None:
    source = panel_source()

    assert "var(--ha-font-size-s,13px)" not in source
    assert ".schedule-summary{" in source
    assert 'summary.style.cssText="margin:2px 0 0;color:var(--primary-text-color);font-size:var(--ha-font-size-m,14px)' in source


def test_due_dates_use_aligned_dynamic_columns_below_rule() -> None:
    source = panel_source()

    assert 'role="table" aria-label="Fälligkeiten"' in source
    assert "grid-template-columns:max-content max-content;column-gap:12px" in source
    assert 'style="display:grid;justify-content:start;margin-top:8px"' in source
    assert "editorScheduleHtml(task,result.due_dates)" in source


def test_group_name_is_larger_than_normal_weight_task_name() -> None:
    source = panel_source()

    assert ".group-head strong{color:var(--primary-text-color);font-size:var(--ha-font-size-l,20px)" in source
    assert ".task strong{color:var(--primary-text-color);font-size:var(--ha-font-size-m,14px);font-weight:var(--ha-font-weight-normal,400)}" in source


def test_supporting_text_uses_normal_body_typography() -> None:
    source = panel_source()

    assert "p,small,label,.pill,.schedule-options,.schedule-summary,.version,header p" in source
    assert ".history-entry{font-size:var(--ha-font-size-m,14px)" in source


def test_optional_start_date_matches_planning_subtitle_hierarchy() -> None:
    source = panel_source()

    assert 'class="start-date-title"' in source
    assert "color:var(--secondary-text-color);font-size:var(--ha-font-size-m,14px);font-weight:var(--ha-font-weight-medium,500)" in source
    assert 'class="start-date-actions" style="display:flex;align-items:center;gap:4px"' in source
    assert 'min-height:32px;color:var(--error-color)' in source
