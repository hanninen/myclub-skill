"""Tests for full event parsing from HTML."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestParseEventsFromHtml:
    def test_parses_events_from_data_events(self, data_events_html):
        events = fetch_myclub.parse_events_from_html(data_events_html, "2026-03-01", "2026-03-31")
        march_events = [e for e in events if e["month"] == "2026-03-01"]
        assert len(march_events) == 2
        assert march_events[0]["name"] == "Friendly match: Thunder vs. Storm"
        assert march_events[0]["type"] == "game"
        assert march_events[1]["name"] == "U11 skills training"
        assert march_events[1]["type"] == "training"

    def test_filters_by_date_range(self, data_events_html):
        events = fetch_myclub.parse_events_from_html(data_events_html, "2026-04-01", "2026-04-30")
        assert len(events) == 1
        assert events[0]["name"] == "Spring Cup"

    def test_merges_html_bar_data(self, data_events_html, event_bars_html):
        combined = data_events_html.replace("</body>", "") + event_bars_html.replace("<html><body>", "")
        events = fetch_myclub.parse_events_from_html(combined, "2026-03-01", "2026-03-31")
        game = next(e for e in events if e["id"] == 5001)
        assert game["day"] == "15.3."
        assert game["time"] == "12:35 - 14:30"
        assert game["registration_status"] == "Ilmoittautuminen päättynyt"

    def test_empty_html(self):
        events = fetch_myclub.parse_events_from_html("<html></html>", "2026-03-01", "2026-03-31")
        assert events == []

    def test_deduplicates_by_id(self, data_events_html):
        doubled = data_events_html.replace("</body>", data_events_html.split("<body>")[1])
        events = fetch_myclub.parse_events_from_html(doubled, "2026-03-01", "2026-03-31")
        ids = [e["id"] for e in events]
        assert len(ids) == len(set(ids))

    def test_sorts_by_day_and_time(self, data_events_html, event_bars_html):
        combined = data_events_html.replace("</body>", "") + event_bars_html.replace("<html><body>", "")
        events = fetch_myclub.parse_events_from_html(combined, "2026-03-01", "2026-03-31")
        days_with_values = [e for e in events if e.get("day")]
        for i in range(len(days_with_values) - 1):
            a = days_with_values[i]
            b = days_with_values[i + 1]
            a_day = int(a["day"].rstrip(".").split(".")[0])
            b_day = int(b["day"].rstrip(".").split(".")[0])
            assert a_day <= b_day
