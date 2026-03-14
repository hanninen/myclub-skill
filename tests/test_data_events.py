"""Tests for data-events extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestExtractDataEvents:
    def test_extracts_events_json(self, data_events_html):
        events = fetch_myclub._extract_data_events(data_events_html)
        assert len(events) == 4
        assert events[0]["id"] == 5001
        assert events[0]["name"] == "Friendly match: Thunder vs. Storm"
        assert events[0]["event_category"] == "Ottelu"

    def test_returns_empty_for_no_attribute(self):
        assert fetch_myclub._extract_data_events("<html><body></body></html>") == []

    def test_returns_empty_for_invalid_json(self):
        html = '<div data-events="not json"></div>'
        assert fetch_myclub._extract_data_events(html) == []

    def test_wraps_single_object_in_list(self):
        html = '<div data-events="{&quot;id&quot;:1,&quot;name&quot;:&quot;Test&quot;}"></div>'
        events = fetch_myclub._extract_data_events(html)
        assert len(events) == 1
        assert events[0]["id"] == 1
