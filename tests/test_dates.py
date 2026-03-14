"""Tests for date helpers and period parsing."""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestIsDateInRangeFinnish:
    def test_date_in_range(self):
        assert fetch_myclub.is_date_in_range_finnish("15.3.", "2026-03-10", "2026-03-20") is True

    def test_date_out_of_range(self):
        assert fetch_myclub.is_date_in_range_finnish("15.3.", "2026-03-16", "2026-03-20") is False

    def test_date_on_boundary(self):
        assert fetch_myclub.is_date_in_range_finnish("10.3.", "2026-03-10", "2026-03-20") is True
        assert fetch_myclub.is_date_in_range_finnish("20.3.", "2026-03-10", "2026-03-20") is True

    def test_handles_no_trailing_dot(self):
        assert fetch_myclub.is_date_in_range_finnish("15.3", "2026-03-10", "2026-03-20") is True

    def test_returns_true_for_unparseable(self):
        assert fetch_myclub.is_date_in_range_finnish("invalid", "2026-03-10", "2026-03-20") is True


class TestIsMonthInRange:
    def test_overlapping(self):
        month_start = date(2026, 3, 1)
        month_end = date(2026, 3, 31)
        assert fetch_myclub.is_month_in_range(month_start, month_end, "2026-03-10", "2026-03-20") is True

    def test_month_before_range(self):
        month_start = date(2026, 1, 1)
        month_end = date(2026, 1, 31)
        assert fetch_myclub.is_month_in_range(month_start, month_end, "2026-03-01", "2026-03-31") is False

    def test_month_after_range(self):
        month_start = date(2026, 5, 1)
        month_end = date(2026, 5, 31)
        assert fetch_myclub.is_month_in_range(month_start, month_end, "2026-03-01", "2026-03-31") is False

    def test_partial_overlap(self):
        month_start = date(2026, 3, 1)
        month_end = date(2026, 3, 31)
        assert fetch_myclub.is_month_in_range(month_start, month_end, "2026-03-15", "2026-04-15") is True


class TestParsePeriod:
    def test_this_week(self):
        start, end = fetch_myclub.parse_period("this week")
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        end_d = datetime.strptime(end, "%Y-%m-%d").date()
        assert start_d.weekday() == 0  # Monday
        assert end_d.weekday() == 6    # Sunday
        assert (end_d - start_d).days == 6

    def test_next_week(self):
        start, end = fetch_myclub.parse_period("next week")
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        end_d = datetime.strptime(end, "%Y-%m-%d").date()
        today = datetime.now().date()
        assert start_d > today
        assert start_d.weekday() == 0
        assert (end_d - start_d).days == 6

    def test_this_month(self):
        start, end = fetch_myclub.parse_period("this month")
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        end_d = datetime.strptime(end, "%Y-%m-%d").date()
        assert start_d.day == 1
        assert (end_d + timedelta(days=1)).day == 1

    def test_next_month(self):
        start, end = fetch_myclub.parse_period("next month")
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        end_d = datetime.strptime(end, "%Y-%m-%d").date()
        today = datetime.now().date()
        assert start_d.day == 1
        assert start_d.month != today.month or start_d.year != today.year
        assert (end_d + timedelta(days=1)).day == 1

    def test_case_insensitive(self):
        s1, e1 = fetch_myclub.parse_period("This Week")
        s2, e2 = fetch_myclub.parse_period("this week")
        assert s1 == s2
        assert e1 == e2

    def test_unknown_defaults_to_this_week(self):
        start, end = fetch_myclub.parse_period("unknown")
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        assert start_d.weekday() == 0
        expected_start, expected_end = fetch_myclub.parse_period("this week")
        assert start == expected_start
        assert end == expected_end
