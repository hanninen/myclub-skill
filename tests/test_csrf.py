"""Tests for CSRF token extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestExtractCsrfToken:
    def test_extracts_from_hidden_input(self, csrf_html_input):
        token = fetch_myclub._extract_csrf_token(csrf_html_input)
        assert token == "form-token-456"

    def test_extracts_from_meta_tag(self, csrf_html_meta_only):
        token = fetch_myclub._extract_csrf_token(csrf_html_meta_only)
        assert token == "meta-token-789"

    def test_extracts_from_meta_reversed_attrs(self, csrf_html_meta_reversed):
        token = fetch_myclub._extract_csrf_token(csrf_html_meta_reversed)
        assert token == "reversed-token-abc"

    def test_prefers_hidden_input_over_meta(self, csrf_html_input):
        token = fetch_myclub._extract_csrf_token(csrf_html_input)
        assert token == "form-token-456"  # not meta-token-123

    def test_returns_none_for_no_token(self):
        assert fetch_myclub._extract_csrf_token("<html><body></body></html>") is None
