"""Tests for MyclubSession."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestMyclubSession:
    def test_initial_state(self):
        session = fetch_myclub.MyclubSession()
        assert session.last_url is None
        assert session.last_html is None
        assert session.cookies_as_list() == []
