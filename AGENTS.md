# Agents

## Development

Use `uv` to manage the project. `uv` is for development purposes only — when the skill is installed, `python3` is used directly.

## SKILL.md

SKILL.md documents the skill's usage from the end-user perspective. Commands in SKILL.md should use `python3 scripts/fetch_myclub.py`, not `uv run`.

## Debugging parse failures

If the script fails due to changed HTML structure on myclub.fi, fetch the current HTML from the live site and compare it against the test fixtures in `tests/fixtures/`. Update the parsing logic and fixtures to match the new structure.
