"""Tests for club parsing and formatting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "myclub" / "scripts"))
import fetch_myclub


class TestParseClubsFromHtml:
    def test_parses_clubs(self, home_page_html):
        clubs = fetch_myclub.parse_clubs_from_html(home_page_html)
        assert "Mika" in clubs
        assert clubs["Mika"]["subdomain"] == "thunderfc"
        assert clubs["Mika"]["full_name"] == "Mika Virtanen"

    def test_deduplicates_same_account_subdomain(self, home_page_html):
        clubs = fetch_myclub.parse_clubs_from_html(home_page_html)
        mika_keys = [k for k in clubs if k.startswith("Mika")]
        assert len(mika_keys) == 1

    def test_handles_multiple_clubs_per_account(self, home_page_html):
        clubs = fetch_myclub.parse_clubs_from_html(home_page_html)
        liisa_keys = [k for k in clubs if k.startswith("Liisa")]
        assert len(liisa_keys) == 2

    def test_skips_navigation_links(self, home_page_html):
        clubs = fetch_myclub.parse_clubs_from_html(home_page_html)
        for info in clubs.values():
            assert "id.myclub.fi" not in info["url"]

    def test_handles_nested_html_in_links(self, home_page_html_nested):
        clubs = fetch_myclub.parse_clubs_from_html(home_page_html_nested)
        assert "Mika" in clubs
        assert clubs["Mika"]["full_name"] == "Mika Virtanen"

    def test_returns_empty_for_no_links(self):
        clubs = fetch_myclub.parse_clubs_from_html("<html><body>No links</body></html>")
        assert clubs == {}


class TestFormatClubName:
    def test_short_subdomain_uppercased(self):
        assert fetch_myclub.format_club_name("ajax") == "AJAX"
        assert fetch_myclub.format_club_name("nifs") == "NIFS"

    def test_six_chars_still_uppercased(self):
        assert fetch_myclub.format_club_name("abcdef") == "ABCDEF"

    def test_long_subdomain_capitalized(self):
        assert fetch_myclub.format_club_name("thunderfc") == "Thunderfc"

    def test_hyphenated_subdomain(self):
        assert fetch_myclub.format_club_name("my-club-name") == "My Club Name"
