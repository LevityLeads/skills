---
name: google
description: Gmail and Google Calendar integration via OAuth. Use for reading/sending emails, managing calendar events, checking availability. Supports multiple Google accounts with automatic token refresh.
---

# Google Integration

Gmail + Calendar API access via OAuth2. Supports multiple accounts (work, personal, etc).

## Setup

Run auth script to add an account:

```bash
python3 scripts/auth.py --alias work
```

Opens browser for OAuth consent → stores tokens locally.

## Usage

### Gmail

```bash
# List recent emails
python3 scripts/gmail.py --alias work list --max 10

# Search emails
python3 scripts/gmail.py --alias work search "from:important@example.com"

# Read specific email (by ID from list/search)
python3 scripts/gmail.py --alias work read MESSAGE_ID

# Send email
python3 scripts/gmail.py --alias work send --to "someone@example.com" --subject "Hello" --body "Message body"
```

### Calendar

```bash
# List upcoming events (next 7 days default)
python3 scripts/calendar.py --alias work list

# List events for specific range
python3 scripts/calendar.py --alias work list --days 14

# Create event
python3 scripts/calendar.py --alias work create \
  --title "Meeting" \
  --start "2026-02-04 10:00" \
  --end "2026-02-04 11:00" \
  --description "Optional description"

# Check free/busy
python3 scripts/calendar.py --alias work freebusy --date "2026-02-04"
```

## Accounts

List configured accounts:
```bash
python3 scripts/auth.py list
```

Tokens stored in `~/.config/openclaw-google/` (or skill directory `tokens/` as fallback).

## Environment

Requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables, OR pass directly:
```bash
python3 scripts/auth.py --alias work --client-id "..." --client-secret "..."
```
