"""Tests for output formatting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestFormatOutput:
    def test_empty_events(self):
        schedule = {"account": "Mika", "club": "Thunder FC", "events": [], "start_date": "2026-03-10", "end_date": "2026-03-16"}
        output = fetch_myclub.format_output(schedule)
        assert "No events found" in output
        assert "Mika" in output

    def test_formats_event_with_day_and_time(self):
        schedule = {
            "account": "Mika", "club": "Thunder FC",
            "start_date": "2026-03-10", "end_date": "2026-03-16",
            "events": [{
                "id": 1, "name": "Training", "group": "U11 Blue", "venue": "Aurora Sports Hall",
                "month": "2026-03-01", "day": "15.3.", "time": "17:00 - 18:00",
                "event_category": "Harjoitus", "type": "training", "registration_status": "unknown",
            }],
        }
        output = fetch_myclub.format_output(schedule)
        assert "15.3." in output
        assert "17:00 - 18:00" in output
        assert "Training" in output
        assert "Aurora Sports Hall" in output
        assert "U11 Blue" in output

    def test_formats_event_with_month_only(self):
        schedule = {
            "account": "Mika", "club": "Thunder FC",
            "start_date": "2026-03-01", "end_date": "2026-03-31",
            "events": [{
                "id": 1, "name": "Game", "group": "", "venue": "",
                "month": "2026-03-01", "day": None, "time": None,
                "event_category": "Ottelu", "type": "game", "registration_status": "unknown",
            }],
        }
        output = fetch_myclub.format_output(schedule)
        assert "2026-03-01" in output
        assert "Game" in output

    def test_emoji_per_type(self):
        types_emojis = [
            ("training", "🏃"), ("game", "⚽"), ("tournament", "🏆"),
            ("meeting", "👥"), ("other", "📌"),
        ]
        for event_type, emoji in types_emojis:
            schedule = {
                "account": "X", "club": "C", "start_date": "2026-03-01", "end_date": "2026-03-31",
                "events": [{
                    "id": 1, "name": "E", "group": "", "venue": "",
                    "month": "2026-03-01", "day": None, "time": None,
                    "event_category": "", "type": event_type, "registration_status": "unknown",
                }],
            }
            output = fetch_myclub.format_output(schedule)
            assert emoji in output, f"Expected {emoji} for type {event_type}"
