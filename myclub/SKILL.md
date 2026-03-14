---
name: myclub
description: Fetch accounts' sports schedules, practices, games, and events from myclub.fi. Auto-discovers accounts and clubs from your myclub.fi account. Use for checking practice times and locations, finding upcoming games and matches, viewing club events, or getting schedule summaries. Requires myclub.fi credentials (stored locally).
---

# myclub Skill

Fetch sports schedules from myclub.fi, including practice times, game dates, locations, and registration status.

## Setup (one-time)

```bash
python3 scripts/fetch_myclub.py setup --username your_email@example.com --password your_password
```

Credentials are stored in `~/.myclub-config.json` with owner-only permissions (`600`).

## Commands

### discover

List all available accounts and their clubs.

```bash
python3 scripts/fetch_myclub.py discover
```

### fetch

```bash
python3 scripts/fetch_myclub.py fetch --account "Account Name" [--period PERIOD | --start DATE [--end DATE]] [--json]
```

**`--period`** values: `this week` (default), `next week`, `this month`, `next month`
**`--start` / `--end`**: Custom date range in `YYYY-MM-DD` format (overrides `--period`)
**`--json`**: Output JSON instead of formatted text

## Event Fields

| Field | Description |
|-------|-------------|
| `id` | Unique event identifier |
| `name` | Event description |
| `group` | Team or group (e.g., "P2015 Black") |
| `venue` | Location |
| `month` | First day of event's month (YYYY-MM-DD) |
| `event_category` | `Harjoitus` (training), `Ottelu` (game), `Turnaus` (tournament), `Muu` (other) |
| `type` | Inferred: `training`, `game`, `tournament`, `meeting`, `other` |

**Note:** Data has month-level granularity only — exact times require visiting myclub.fi directly.

## Troubleshooting

- **"No .myclub-config.json found"** — Run `setup` first
- **"Unknown account 'Name'"** — Run `discover` to check exact spelling (case-sensitive)
- **Timeout / auth errors** — Verify credentials with `discover`; check internet connection
- **JSON parsing fails** — myclub.fi page structure may have changed; check for `data-events` attribute on the calendar page

## Requirements

Python 3.8+ with Playwright:

```bash
pip install playwright && playwright install
```
