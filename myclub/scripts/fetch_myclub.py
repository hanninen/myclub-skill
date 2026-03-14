#!/usr/bin/env python3
"""
Fetch myclub.fi schedules for accounts using Playwright.

Usage:
    python3 fetch_myclub.py setup --username USER --password PASS
    python3 fetch_myclub.py discover
    python3 fetch_myclub.py fetch --account Kaarlo --period "this week"
"""

import json
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

CONFIG_FILE = Path.home() / ".myclub-config.json"

def load_config():
    """Load credentials from config."""
    if not CONFIG_FILE.exists():
        print("Error: No .myclub-config.json found. Run 'setup' first.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(username: str, password: str):
    """Save credentials (accounts/clubs auto-discovered)."""
    config = {"username": username, "password": password}
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    CONFIG_FILE.chmod(0o600)  # Owner read/write only
    print(f"✓ Credentials saved to {CONFIG_FILE}")
    print("✓ Run 'discover' to see available accounts and clubs")

def _find_visible(page, selectors: list[str]) -> str | None:
    """Return the first selector that matches a visible element, or None."""
    for sel in selectors:
        try:
            if page.locator(sel).first.is_visible():
                return sel
        except Exception:
            pass
    return None

def _dump_inputs(page, file=sys.stderr):
    """Print all input elements on the page for debugging."""
    inputs = page.locator("input").all()
    for i, inp in enumerate(inputs):
        attrs = {
            "type": inp.get_attribute("type") or "text",
            "id": inp.get_attribute("id") or "",
            "name": inp.get_attribute("name") or "",
            "placeholder": inp.get_attribute("placeholder") or "",
            "visible": inp.is_visible(),
        }
        print(f"    [{i}] {attrs}", file=file)

def login_to_myclub(page, username: str, password: str, debug: bool = False) -> bool:
    """Log in to myclub.fi. The login page is server-rendered with static fields."""
    print("🔓 Logging in to myclub.fi...")

    page.goto("https://id.myclub.fi/flow/login", wait_until="networkidle")
    print("  ✓ Login page loaded")

    if debug:
        page.screenshot(path="/tmp/myclub-login-debug.png")
        print("  📸 Screenshot saved to /tmp/myclub-login-debug.png")

    # Find and fill email
    email_selector = _find_visible(page, [
        "#user_session_email",
        "input[name='user_session[email]']",
        "input[type='email']",
    ])
    if not email_selector:
        print("  ✗ Email field not found!", file=sys.stderr)
        if debug:
            _dump_inputs(page)
        return False

    page.fill(email_selector, username)

    # Find and fill password
    password_selector = _find_visible(page, [
        "#user_session_password",
        "input[name='user_session[password]']",
        "input[type='password']",
    ])
    if not password_selector:
        print("  ✗ Password field not found!", file=sys.stderr)
        if debug:
            page.screenshot(path="/tmp/myclub-password-debug.png")
            print("  📸 Screenshot saved to /tmp/myclub-password-debug.png", file=sys.stderr)
            _dump_inputs(page)
        return False

    page.fill(password_selector, password)

    # Submit
    button_selector = _find_visible(page, [
        "button[type='submit']",
        "button.btn-primary",
    ])
    if not button_selector:
        print("  ✗ Login button not found!", file=sys.stderr)
        return False

    page.click(button_selector)

    # Wait for post-login navigation
    try:
        page.wait_for_url("**/id.myclub.fi**", timeout=15000)
    except Exception:
        print("  ⚠️  Navigation didn't match expected URL, continuing...", file=sys.stderr)

    page.wait_for_load_state("networkidle")
    print("  ✓ Login successful")

    return True

def discover_clubs(username: str, password: str, debug: bool = False) -> dict:
    """
    Discover all accounts and their clubs.

    Returns:
    {
        "Kaarlo": {"name": "FC Kasiysi", "url": "https://..."},
        "Helmi": {"name": "Gymnast Club A", "url": "https://..."}
    }
    """
    print("🔍 Discovering accounts and clubs...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Set default timeout for operations (5 seconds)
        page.set_default_timeout(5000)
        
        try:
            if not login_to_myclub(page, username, password, debug=debug):
                print("Error: Login failed", file=sys.stderr)
                return {}

            # We should be at id.myclub.fi/flow/home
            print("📋 Reading clubs list...")
            page.wait_for_load_state("networkidle")
            
            # Parse clubs from the page
            clubs = parse_clubs_from_page(page)
            
        finally:
            browser.close()
    
    return clubs

def parse_clubs_from_page(page) -> dict:
    """
    Parse accounts and clubs from home page.

    Link format:
    - text: "Kaarlo Hänninen" (account's full name)
    - href: "https://fckasiysi.myclub.fi/flow/select_account?id=889307"
    - club name: extracted from subdomain (fckasiysi → FC Kasiysi)
    """
    clubs = {}
    
    # Find all links to club subdomains
    links = page.locator("a[href*='myclub.fi']").all()
    
    print(f"  Found {len(links)} club links")
    
    if not links:
        return clubs
    
    # Parse links: each should have an account name and club URL
    seen_combos = set()  # Track (account_name, subdomain) to avoid duplicates
    
    for link in links:
        href = link.get_attribute("href")
        text = link.text_content().strip()
        
        # Skip empty or short text
        if not href or not text or len(text) < 2:
            continue
        
        # Skip navigation links and links without select_account
        if href.endswith("/flow/") or "select_account" not in href:
            continue
        
        # Extract club subdomain from URL
        # e.g., "https://fckasiysi.myclub.fi/..." → "fckasiysi"
        url_match = re.search(r'https?://([a-z0-9-]+)\.myclub\.fi', href)
        if not url_match:
            continue
        
        club_subdomain = url_match.group(1)
        
        # Extract account name from text
        # Text is usually "Firstname Lastname" or just first name
        name_parts = text.split()
        if not name_parts:
            continue

        account_name = name_parts[0].strip()

        # Skip duplicate (account, subdomain) combinations
        combo = (account_name, club_subdomain)
        if combo in seen_combos:
            continue
        seen_combos.add(combo)

        # Human-readable club name from subdomain
        club_display_name = format_club_name(club_subdomain)

        # Use first name as key; if account has multiple clubs, add subdomain to key
        if account_name in clubs:
            # Account has multiple clubs - add subdomain to key for uniqueness
            key = f"{account_name} ({club_subdomain})"
        else:
            # First club for this account
            key = account_name
        
        clubs[key] = {
            "name": club_display_name,
            "url": href,
            "subdomain": club_subdomain,
            "full_name": text
        }
    
    if clubs:
        print(f"  ✓ Discovered {len(clubs)} account/club combinations", file=sys.stderr)
        return clubs

    print("  ⚠️  No valid account/club links found", file=sys.stderr)
    return {}

def format_club_name(subdomain: str) -> str:
    """
    Format club subdomain to readable name.
    
    Examples:
    - fckasiysi → FC Kasiysi
    - esjt → ESJT
    - htkd → HTKD
    """
    # If it's all lowercase and looks like an acronym, uppercase it
    if subdomain.islower() and len(subdomain) <= 6:
        return subdomain.upper()
    
    # Otherwise capitalize first letter of each word
    return " ".join(word.capitalize() for word in subdomain.split("-"))

def infer_event_type(category: str, name: str) -> str:
    """Infer event type from category or event name."""
    cat = category.strip().lower()
    if cat == "ottelu":
        return "game"
    if cat == "turnaus":
        return "tournament"
    if cat == "harjoitus":
        return "training"
    if cat == "muu":
        return "other"

    name_lower = name.lower()
    if any(w in name_lower for w in ["harjoituspeli", "ottelu", "peli", "match", "vs"]):
        return "game"
    if any(w in name_lower for w in ["turnaus", "tournament", "cup", "liiga"]):
        return "tournament"
    if "harjoitus" in name_lower:
        return "training"
    if any(w in name_lower for w in ["info", "kokous", "palaver", "vanhempainfo"]):
        return "meeting"
    return "training"

def fetch_schedule(username: str, password: str, account_name: str, start_date: str, end_date: str, debug: bool = False) -> dict:
    """
    Fetch schedule from myclub.fi.
    """
    print(f"📅 Fetching schedule for {account_name}...")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Set default timeout for operations (5 seconds)
        page.set_default_timeout(5000)

        try:
            if not login_to_myclub(page, username, password, debug=debug):
                print("Error: Login failed", file=sys.stderr)
                return {"account": account_name, "club": "", "events": []}

            # Discover clubs
            print(f"🏟️  Looking for {account_name}'s club...")
            page.wait_for_load_state("networkidle")

            clubs = parse_clubs_from_page(page)

            if account_name not in clubs:
                print(f"Error: '{account_name}' not found", file=sys.stderr)
                print(f"Available: {', '.join(clubs.keys())}", file=sys.stderr)
                return {"account": account_name, "club": "", "events": []}

            club_info = clubs[account_name]
            club_name = club_info["name"]
            club_url = club_info["url"]

            print(f"  ✓ Found {account_name} → {club_name}")
            print(f"  ✓ Navigating to {club_url}...")

            # Navigate to club page
            page.goto(club_url, wait_until="networkidle")

            print("📅 Parsing events...")
            page.wait_for_load_state("networkidle")

            # Parse events from schedule page
            events = parse_events_from_page(page, start_date, end_date)

            return {
                "account": account_name,
                "club": club_name,
                "start_date": start_date,
                "end_date": end_date,
                "events": events
            }
            
        finally:
            browser.close()

def parse_events_from_page(page, start_date: str, end_date: str) -> list:
    """
    Parse events from schedule page using embedded JSON data + HTML day/time info.
    
    The page contains: 
    1. <div data-events='[{"id":..,"name":"..","group":"..","venue":"..","month":"YYYY-MM-DD","event_category":".."}]'>
    2. HTML structure with actual day/time:
       <div class="event-container">
         <div class="event-bar" href="#event-content-ID">
           <span class="day">pe 13.3.</span>
           <span class="time">17:00 - 19:00</span>
    
    JSON Structure (month level only):
    {
        "id": integer,
        "name": string (event name),
        "group": string (team/group name),
        "venue": string (location),
        "month": string (YYYY-MM-DD, first day of month),
        "event_category": string (Muu, Harjoitus, Ottelu, Turnaus)
    }
    
    HTML Structure (actual day + time):
    <div class="event-bar" data-toggle="collapse" href="#event-content-ID">
      <span class="day">pe 13.3.</span>
      <span class="time">17:00 - 19:00</span>
    </div>
    """
    events = []
    html_event_data = {}  # Will map event ID to {day, time, name, venue, group}
    
    print("  📋 Looking for data-events JSON...")
    
    try:
        # Step 1: Parse HTML to get day/time info for each event ID
        print("  🔍 Extracting day and time from HTML...")
        html_event_data = parse_event_times_from_html(page)
        print(f"  ✓ Found {len(html_event_data)} events with day/time in HTML")
        
        # Step 2: Find the div with data-events attribute (may not have id="events")
        if page.locator("[data-events]").count() == 0:
            print("  ⚠️  No data-events JSON found, using HTML data only")
            events_data = []
        else:
            # Get the data-events attribute
            data_events_str = page.locator("[data-events]").first.get_attribute("data-events")
            if not data_events_str:
                print("  ⚠️  No data-events attribute found, using HTML data only")
                events_data = []
            else:
                print(f"  ✓ Found data-events (length: {len(data_events_str)} chars)")
                
                # Parse JSON
                try:
                    events_data = json.loads(data_events_str)
                    
                    if not isinstance(events_data, list):
                        events_data = [events_data]
                    
                    print(f"  ✓ Parsed {len(events_data)} events from JSON")
                except json.JSONDecodeError as e:
                    print(f"  ✗ Failed to parse JSON: {str(e)[:60]}")
                    events_data = []
        
        # Extract relevant fields from JSON events
        json_event_ids = set()
        for event_data in events_data:
            try:
                # Get basic info
                name = event_data.get("name", "").strip()
                if not name:
                    continue
                
                event_id = event_data.get("id")
                if event_id:
                    json_event_ids.add(event_id)
                
                # Parse month (format: YYYY-MM-DD, first day of month)
                month_str = event_data.get("month", "").strip()
                if not month_str:
                    continue
                
                # Extract year and month from "YYYY-MM-DD"
                try:
                    month_parts = month_str.split('-')
                    year = int(month_parts[0])
                    month = int(month_parts[1])
                except (ValueError, IndexError):
                    print(f"  ⚠️  Could not parse month: {month_str}")
                    continue
                
                # Check if month is in range (use first day of month for comparison)
                month_date = datetime(year, month, 1).date()
                month_end_dt = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                month_end = month_end_dt.date()
                
                if not is_month_in_range(month_date, month_end, start_date, end_date):
                    continue
                
                # Get location
                venue = event_data.get("venue", "").strip()
                
                # Get group/team info
                group = event_data.get("group", "").strip()
                
                event_type = infer_event_type(event_data.get("event_category", ""), name)
                
                # Step 3: Merge with HTML day/time data if available
                day = None
                time = None
                if event_id and event_id in html_event_data:
                    day = html_event_data[event_id].get("day")
                    time = html_event_data[event_id].get("time")
                
                event = {
                    "id": event_id,
                    "name": name,
                    "group": group,
                    "venue": venue,
                    "month": month_str,
                    "day": day,  # Actual day from HTML (e.g., "pe 13.3.")
                    "time": time,  # Actual time from HTML (e.g., "17:00 - 19:00")
                    "event_category": event_data.get("event_category", ""),
                    "type": event_type,
                    "registration_status": "unknown"
                }
                
                events.append(event)
            
            except Exception as e:
                print(f"  ⚠️  Error parsing event: {str(e)[:50]}")
                continue
        
        # Step 4: Add HTML-only events (not in JSON data)
        # These are events that only appear in HTML but not in data-events JSON
        if html_event_data:
            print("  📋 Processing HTML-only events...")
            for event_id, html_data in html_event_data.items():
                # Skip if already in JSON
                if event_id in json_event_ids:
                    continue
                
                day = html_data.get("day")
                time = html_data.get("time")
                
                # Check if day is in requested range
                if day and not is_date_in_range_finnish(day, start_date, end_date):
                    continue
                
                # Create minimal event from HTML data
                name = html_data.get("name", f"Event {event_id}")
                venue = html_data.get("venue", "")
                group = html_data.get("group", "")
                
                event_type = infer_event_type("", name)
                
                event = {
                    "id": event_id,
                    "name": name,
                    "group": group,
                    "venue": venue,
                    "month": None,  # Unknown from HTML
                    "day": day,
                    "time": time,
                    "event_category": None,
                    "type": event_type,
                    "registration_status": "unknown"
                }
                
                events.append(event)
                print(f"    ✓ Added HTML-only event: {name} ({day})")
    
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:60]}")
        return []
    
    # Remove duplicates (same id or same name+venue+day)
    seen = set()
    unique_events = []
    for e in events:
        # Use event ID if available, otherwise use name+venue+day
        key = e.get("id") or (e["name"], e.get("venue"), e.get("day"))
        if key not in seen:
            seen.add(key)
            unique_events.append(e)
    
    # Sort by day/time if available, otherwise by month and name
    def sort_key(e):
        if e.get("day"):
            # Parse day like "13.3." to sort properly
            try:
                day_str = e["day"].rstrip('.')  # Remove trailing dot: "13.3" 
                day_parts = day_str.split('.')
                day_num = int(day_parts[0])
                month_num = int(day_parts[1]) if len(day_parts) > 1 else 1
                time_val = e.get("time", "00:00")
                return (month_num, day_num, time_val)
            except:
                pass
        
        # Fallback: parse month from e["month"] (YYYY-MM-DD format)
        try:
            month_str = e.get("month", "")
            if month_str:
                month_parts = month_str.split('-')
                year = int(month_parts[0])
                month = int(month_parts[1])
                return (month, 1, e.get("name", ""))
        except:
            pass
        
        return (99, 99, "")
    
    unique_events.sort(key=sort_key)
    
    print(f"  ✓ Extracted {len(unique_events)} unique events total")
    
    return unique_events


def parse_event_times_from_html(page) -> dict:
    """
    Parse HTML to extract actual day and time for each event.
    
    Structure:
    <div class="event-bar" data-toggle="collapse" href="#event-content-ID">
      <span class="day">pe 13.3.</span>
      <span class="time">17:00 - 19:00</span>
    </div>
    
    Returns: {event_id: {"day": "13.3.", "time": "17:00 - 19:00"}, ...}
    Note: Strips Finnish weekday abbreviation (pe, ma, ti, ke, to, la, su)
    """
    event_times = {}
    
    try:
        # Set shorter timeout for HTML parsing
        page.set_default_timeout(2000)
        
        # Find all event-bar elements with shorter timeout
        try:
            event_bars = page.locator(".event-bar").all()
        except Exception as e:
            print(f"  ⚠️  Could not find event bars: {str(e)[:40]}")
            return event_times
        
        if not event_bars:
            print("  ⚠️  No event bars found in HTML")
            return event_times
        
        for bar in event_bars:
            try:
                # Get the href attribute to extract event ID
                # href format: "#event-content-ID" (e.g., "#event-content-10375030")
                href = None
                try:
                    href = bar.get_attribute("href")
                except:
                    try:
                        href = bar.get_attribute("data-toggle")
                    except:
                        pass
                
                if not href:
                    continue
                
                # Extract event ID from href
                event_id = None
                if "event-content-" in href:
                    try:
                        event_id = int(href.split("event-content-")[-1])
                    except ValueError:
                        continue
                
                # Extract day from <span class="day">
                day = None
                try:
                    day_span = bar.locator("span.day").first
                    day_text = day_span.text_content().strip()
                    # Strip weekday abbreviation (format: "pe 13.3.")
                    # Split by whitespace and take the last part (the date)
                    parts = day_text.split()
                    if parts:
                        # Last part should be the date (e.g., "13.3.")
                        date_part = parts[-1]
                        day = date_part
                except Exception:
                    # Don't fail if day parsing fails
                    pass
                
                # Extract time from <span class="time">
                time = None
                try:
                    time_span = bar.locator("span.time").first
                    time = time_span.text_content().strip()
                except Exception:
                    # Don't fail if time parsing fails
                    pass
                
                # Store if we have ID and at least day or time
                if event_id and (day or time):
                    event_times[event_id] = {
                        "day": day,
                        "time": time
                    }
            
            except Exception:
                # Skip individual events that fail
                continue
        
        # Restore default timeout
        page.set_default_timeout(5000)
    
    except Exception as e:
        print(f"  ⚠️  Error parsing HTML event times: {str(e)[:50]}")
        # Restore default timeout on error
        try:
            page.set_default_timeout(5000)
        except:
            pass
    
    return event_times

def is_date_in_range(date_str: str, start_date: str, end_date: str) -> bool:
    """Check if date (DD.MM) is within range."""
    try:
        day, month = map(int, date_str.split('.'))
        current_year = datetime.now().year
        date_obj = datetime(current_year, month, day).date()
        
        start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        return start_obj <= date_obj <= end_obj
    except (ValueError, AttributeError):
        return True

def is_date_in_range_finnish(date_str: str, start_date: str, end_date: str) -> bool:
    """
    Check if Finnish date string (e.g., "15.3." or "15.3") is within range.
    
    Handles format: DD.M. or DD.M or DD.MM. or DD.MM
    """
    try:
        # Clean up the date string
        date_clean = date_str.strip().rstrip('.')
        
        # Split by dot
        parts = date_clean.split('.')
        if len(parts) < 2:
            return True
        
        day = int(parts[0])
        month = int(parts[1])
        
        current_year = datetime.now().year
        date_obj = datetime(current_year, month, day).date()
        
        start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        return start_obj <= date_obj <= end_obj
    except (ValueError, AttributeError, IndexError):
        return True

def is_month_in_range(month_start: object, month_end: object, start_date: str, end_date: str) -> bool:
    """Check if a month (start and end dates) overlaps with the requested range."""
    try:
        start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Month overlaps if it doesn't end before start or start after end
        return not (month_end < start_obj or month_start > end_obj)
    except (ValueError, AttributeError):
        return True

def parse_period(period_str: str) -> tuple:
    """Convert period string to (start_date, end_date)."""
    today = datetime.now().date()
    
    next_month_first = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    period_map = {
        "this week": (today - timedelta(days=today.weekday()), today + timedelta(days=6-today.weekday())),
        "next week": (today + timedelta(days=7-today.weekday()), today + timedelta(days=13-today.weekday())),
        "this month": (today.replace(day=1), (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)),
        "next month": (next_month_first, (next_month_first + timedelta(days=32)).replace(day=1) - timedelta(days=1)),
    }
    
    if period_str.lower() in period_map:
        start, end = period_map[period_str.lower()]
        return str(start), str(end)
    
    # Default to this week
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return str(start), str(end)

def format_output(schedule: dict) -> str:
    """Format schedule as human-readable text."""
    account = schedule["account"]
    club = schedule["club"]
    events = schedule["events"]

    if not events:
        return f"No events found for {account} ({club}) in the requested period."

    output = f"📅 {account}'s Schedule ({club})\n"
    output += f"   {schedule['start_date']} to {schedule['end_date']}\n\n"
    
    for event in events:
        emoji = {
            "training": "🏃",
            "game": "⚽",
            "tournament": "🏆",
            "meeting": "👥",
            "other": "📌"
        }.get(event["type"], "📌")
        
        # Display day/time if available (from HTML), otherwise month
        if event.get("day"):
            output += f"{emoji} {event['day']}"
            if event.get("time"):
                output += f"  {event['time']}"
            output += "\n"
        else:
            output += f"{emoji} {event['month']}\n"
        
        output += f"   {event['name']}\n"
        
        if event.get("group"):
            output += f"   👥 Group: {event['group']}\n"
        
        if event.get("venue"):
            output += f"   📍 {event['venue']}\n"
        
        if event.get("event_category"):
            output += f"   📂 {event['event_category']}\n"
        
        output += "\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(
        description="Fetch myclub.fi schedules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 fetch_myclub.py setup --username user@example.com --password pass
  python3 fetch_myclub.py discover
  python3 fetch_myclub.py fetch --account Kaarlo --period "this week"
        """
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output (screenshots, input dumps)")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Setup command
    setup = subparsers.add_parser("setup", help="Store credentials")
    setup.add_argument("--username", required=True, help="myclub.fi email")
    setup.add_argument("--password", required=True, help="myclub.fi password")
    
    # Discover command
    discover = subparsers.add_parser("discover", help="List accounts and clubs")
    
    # Fetch command
    fetch = subparsers.add_parser("fetch", help="Fetch schedule")
    fetch.add_argument("--account", required=True, help="Account name")
    fetch.add_argument("--period", default="this week", help="Period")
    fetch.add_argument("--start", help="Start date (YYYY-MM-DD)")
    fetch.add_argument("--end", help="End date (YYYY-MM-DD)")
    fetch.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        save_config(args.username, args.password)
    
    elif args.command == "discover":
        config = load_config()
        clubs = discover_clubs(config["username"], config["password"], debug=args.debug)
        
        if not clubs:
            print("No clubs found", file=sys.stderr)
            sys.exit(1)
        
        print("\n📚 Available accounts and clubs:\n")
        for account, info in clubs.items():
            print(f"  {account}:")
            print(f"    Club: {info['name']}")
            print(f"    URL: {info['url']}")
            print()
    
    elif args.command == "fetch":
        config = load_config()
        start_date, end_date = (args.start, args.end) if args.start and args.end else parse_period(args.period)
        
        schedule = fetch_schedule(
            config["username"],
            config["password"],
            args.account,
            start_date,
            end_date,
            debug=args.debug
        )
        
        if args.json:
            print(json.dumps(schedule, indent=2))
        else:
            print(format_output(schedule))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
