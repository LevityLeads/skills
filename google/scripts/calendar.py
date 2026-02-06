#!/usr/bin/env python3
"""
Google Calendar API operations for OpenClaw.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import urllib.parse

# Import auth helper
import os
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_access_token

CALENDAR_API = "https://www.googleapis.com/calendar/v3"


def api_request(alias: str, endpoint: str, method: str = "GET", body: dict = None) -> dict:
    """Make authenticated Calendar API request."""
    token = get_access_token(alias)
    url = f"{CALENDAR_API}{endpoint}"
    
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return {}
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Calendar API error ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)


def list_calendars(alias: str):
    """List all calendars."""
    result = api_request(alias, "/users/me/calendarList")
    calendars = result.get("items", [])
    
    print("Calendars:")
    for cal in calendars:
        primary = " (primary)" if cal.get("primary") else ""
        print(f"  - {cal.get('summary', 'Untitled')}{primary}")
        print(f"    ID: {cal['id']}")
    return calendars


def list_events(alias: str, days: int = 7, calendar_id: str = "primary"):
    """List upcoming events."""
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days)).isoformat() + "Z"
    
    params = urllib.parse.urlencode({
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 50,
    })
    
    result = api_request(alias, f"/calendars/{urllib.parse.quote(calendar_id)}/events?{params}")
    events = result.get("items", [])
    
    if not events:
        print(f"No events in the next {days} days.")
        return
    
    print(f"Upcoming events (next {days} days):\n")
    
    current_date = None
    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})
        
        # Handle all-day vs timed events
        if "dateTime" in start:
            start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
            time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
            date_str = start_dt.strftime("%A, %B %d")
        else:
            date_str = start.get("date", "")
            time_str = "All day"
            start_dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_str = start_dt.strftime("%A, %B %d")
        
        # Print date header if changed
        if date_str != current_date:
            if current_date is not None:
                print()
            print(f"📅 {date_str}")
            current_date = date_str
        
        summary = event.get("summary", "(No title)")
        location = event.get("location", "")
        
        print(f"  {time_str}: {summary}")
        if location:
            print(f"    📍 {location}")
        
        # Show attendees if present
        attendees = event.get("attendees", [])
        if attendees:
            attending = [a.get("email") for a in attendees if a.get("responseStatus") == "accepted"]
            if attending:
                print(f"    👥 {', '.join(attending[:3])}" + ("..." if len(attending) > 3 else ""))


def create_event(alias: str, title: str, start: str, end: str, description: str = None, 
                 location: str = None, calendar_id: str = "primary", attendees: list = None):
    """Create a calendar event."""
    # Parse datetime strings
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            # All-day event
            event_body = {
                "summary": title,
                "start": {"date": start_dt.strftime("%Y-%m-%d")},
                "end": {"date": end_dt.strftime("%Y-%m-%d")},
            }
        except ValueError:
            print(f"Invalid date format. Use 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'", file=sys.stderr)
            sys.exit(1)
    else:
        event_body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
        }
    
    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location
    if attendees:
        event_body["attendees"] = [{"email": a} for a in attendees]
    
    result = api_request(alias, f"/calendars/{urllib.parse.quote(calendar_id)}/events", 
                         method="POST", body=event_body)
    
    print(f"✓ Event created successfully")
    print(f"  Title: {title}")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    print(f"  Event ID: {result.get('id')}")
    if result.get("htmlLink"):
        print(f"  Link: {result['htmlLink']}")


def get_freebusy(alias: str, date: str, calendar_id: str = "primary"):
    """Check free/busy for a specific date."""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date format. Use 'YYYY-MM-DD'", file=sys.stderr)
        sys.exit(1)
    
    time_min = target_date.replace(hour=0, minute=0).isoformat() + "Z"
    time_max = target_date.replace(hour=23, minute=59).isoformat() + "Z"
    
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": calendar_id}],
    }
    
    result = api_request(alias, "/freeBusy", method="POST", body=body)
    
    calendars = result.get("calendars", {})
    busy_times = calendars.get(calendar_id, {}).get("busy", [])
    
    print(f"Free/Busy for {target_date.strftime('%A, %B %d, %Y')}:\n")
    
    if not busy_times:
        print("✓ Completely free all day!")
        return
    
    print("Busy times:")
    for slot in busy_times:
        start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
        print(f"  🔴 {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
    
    # Calculate free slots
    print("\nFree slots:")
    work_start = target_date.replace(hour=9, minute=0)
    work_end = target_date.replace(hour=18, minute=0)
    
    busy_sorted = sorted(busy_times, key=lambda x: x["start"])
    current = work_start
    
    for slot in busy_sorted:
        slot_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00")).replace(tzinfo=None)
        slot_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00")).replace(tzinfo=None)
        
        if slot_start > current and slot_start <= work_end:
            end_time = min(slot_start, work_end)
            if end_time > current:
                print(f"  🟢 {current.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
        
        current = max(current, slot_end)
    
    if current < work_end:
        print(f"  🟢 {current.strftime('%H:%M')} - {work_end.strftime('%H:%M')}")


def main():
    parser = argparse.ArgumentParser(description="Google Calendar operations")
    parser.add_argument("--alias", required=True, help="Account alias")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # List calendars
    subparsers.add_parser("calendars", help="List all calendars")
    
    # List events
    list_parser = subparsers.add_parser("list", help="List upcoming events")
    list_parser.add_argument("--days", type=int, default=7, help="Days to look ahead")
    list_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    
    # Create event
    create_parser = subparsers.add_parser("create", help="Create an event")
    create_parser.add_argument("--title", required=True, help="Event title")
    create_parser.add_argument("--start", required=True, help="Start time (YYYY-MM-DD HH:MM)")
    create_parser.add_argument("--end", required=True, help="End time (YYYY-MM-DD HH:MM)")
    create_parser.add_argument("--description", help="Event description")
    create_parser.add_argument("--location", help="Event location")
    create_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    create_parser.add_argument("--attendee", action="append", help="Attendee email (can repeat)")
    
    # Free/busy
    freebusy_parser = subparsers.add_parser("freebusy", help="Check free/busy")
    freebusy_parser.add_argument("--date", required=True, help="Date to check (YYYY-MM-DD)")
    freebusy_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    
    args = parser.parse_args()
    
    if args.command == "calendars":
        list_calendars(args.alias)
    elif args.command == "list":
        list_events(args.alias, args.days, args.calendar)
    elif args.command == "create":
        create_event(args.alias, args.title, args.start, args.end, 
                     args.description, args.location, args.calendar, args.attendee)
    elif args.command == "freebusy":
        get_freebusy(args.alias, args.date, args.calendar)


if __name__ == "__main__":
    main()
