"""Tests for event-bar HTML parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestParseEventBars:
    def test_parses_day_time_registration(self, event_bars_html):
        bars = fetch_myclub._parse_event_bars(event_bars_html)
        assert len(bars) == 3

        bar = bars[5001]
        assert bar["day"] == "15.3."
        assert bar["time"] == "12:35 - 14:30"
        assert bar["registration_status"] == "Ilmoittautuminen päättynyt"

    def test_strips_weekday_from_day(self, event_bars_html):
        bars = fetch_myclub._parse_event_bars(event_bars_html)
        assert bars[5002]["day"] == "17.3."  # "ma 17.3." → "17.3."

    def test_defaults_registration_to_unknown(self, event_bars_html):
        bars = fetch_myclub._parse_event_bars(event_bars_html)
        assert bars[9999]["registration_status"] == "unknown"

    def test_returns_empty_for_no_bars(self):
        assert fetch_myclub._parse_event_bars("<html><body></body></html>") == {}
