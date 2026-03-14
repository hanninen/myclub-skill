"""Tests for event type inference."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestInferEventType:
    def test_category_ottelu(self):
        assert fetch_myclub.infer_event_type("Ottelu", "anything") == "game"

    def test_category_harjoitus(self):
        assert fetch_myclub.infer_event_type("Harjoitus", "anything") == "training"

    def test_category_turnaus(self):
        assert fetch_myclub.infer_event_type("Turnaus", "anything") == "tournament"

    def test_category_muu(self):
        assert fetch_myclub.infer_event_type("Muu", "anything") == "other"

    def test_category_case_insensitive(self):
        assert fetch_myclub.infer_event_type("OTTELU", "anything") == "game"
        assert fetch_myclub.infer_event_type("  harjoitus  ", "anything") == "training"

    def test_name_fallback_game(self):
        assert fetch_myclub.infer_event_type("", "Harjoituspeli: Black vs. Nups") == "game"
        assert fetch_myclub.infer_event_type("", "Team A vs Team B") == "game"

    def test_name_fallback_tournament(self):
        assert fetch_myclub.infer_event_type("", "Kevät Cup 2026") == "tournament"
        assert fetch_myclub.infer_event_type("", "Turnaus Helsinki") == "tournament"

    def test_name_fallback_training(self):
        assert fetch_myclub.infer_event_type("", "Harjoitus ma") == "training"

    def test_name_fallback_meeting(self):
        assert fetch_myclub.infer_event_type("", "Vanhempaininfo kevät") == "meeting"
        assert fetch_myclub.infer_event_type("", "Joukkueen kokous") == "meeting"

    def test_unknown_defaults_to_training(self):
        assert fetch_myclub.infer_event_type("", "Something random") == "training"
