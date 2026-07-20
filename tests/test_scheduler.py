"""Scheduler unit tests."""

from datetime import date

from custom_components.home_tasker.scheduler import add_interval


def test_days_and_weeks():
    assert add_interval(date(2026, 7, 20), 2, "day") == date(2026, 7, 22)
    assert add_interval(date(2026, 7, 20), 2, "week") == date(2026, 8, 3)


def test_month_anchor_returns_after_clamp():
    february = add_interval(date(2026, 1, 31), 1, "month", 31)
    assert february == date(2026, 2, 28)
    assert add_interval(february, 1, "month", 31) == date(2026, 3, 31)


def test_leap_year_anchor():
    assert add_interval(date(2024, 2, 29), 1, "year", 29) == date(2025, 2, 28)

