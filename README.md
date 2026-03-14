# AI Skill for myClub (myclub.fi)

An AI skill that fetches sports schedules from [myclub.fi](https://myclub.fi), including practice times, game dates, locations, and registration status.

This is an independent Open Source project for helping everyone using myClub to manage their schedules with AI assistants and is not affiliated with myClub.

Uses only Python standard library (`urllib.request`, `http.cookiejar`, `re`) — no external runtime dependencies.

## Prerequisites

- Python 3.10+

## Installation

Copy the `myclub` directory to your AI agents `skills` directory:

- Openclaw: `.openclaw/skills/myclub`
- Claude: `.claude/skills/myclub`
- Cursor: `.cursor/skills/myclub`
- General agents directory `.agents/skills/myclub`

## Usage

### Setup credentials

```bash
python3 myclub/scripts/fetch_myclub.py setup --username "your-email" --password "your-password"
```

Credentials are stored in `~/.myclub-config.json` with owner-only permissions (`600`).

### Discover accounts and clubs

```bash
python3 myclub/scripts/fetch_myclub.py discover [--json]
```

### Fetch schedule

```bash
python3 myclub/scripts/fetch_myclub.py fetch --account "Account Name" [--period PERIOD | --start DATE --end DATE] [--json]
```

- `--period`: `this week` (default), `next week`, `this month`, `next month`
- `--start` / `--end`: Custom date range in `YYYY-MM-DD` format (overrides `--period`)
- `--json`: Output JSON instead of formatted text
- `--debug`: Dump HTML pages and cookies to `/tmp/` for troubleshooting

## Development

Requires [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

### Running tests

```bash
uv run pytest
```

With coverage summary:

```bash
uv run pytest --cov=myclub/scripts --cov-report=term-missing
```

With HTML coverage report:

```bash
uv run pytest --cov=myclub/scripts --cov-report=html
```

The report is generated in `htmlcov/`. Open `htmlcov/index.html` in a browser to view it.

### Linting

```bash
uv run ruff check
```
