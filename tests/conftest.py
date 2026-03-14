"""Shared pytest fixtures for myclub tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


@pytest.fixture
def csrf_html_input():
    return _load("csrf_with_input.html")


@pytest.fixture
def csrf_html_meta_only():
    return _load("csrf_meta_only.html")


@pytest.fixture
def csrf_html_meta_reversed():
    return _load("csrf_meta_reversed.html")


@pytest.fixture
def home_page_html():
    return _load("home_page.html")


@pytest.fixture
def home_page_html_nested():
    return _load("home_page_nested.html")


@pytest.fixture
def data_events_html():
    return _load("data_events.html")


@pytest.fixture
def event_bars_html():
    return _load("event_bars.html")
