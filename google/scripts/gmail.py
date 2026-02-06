#!/usr/bin/env python3
"""
Gmail API operations for OpenClaw.
"""

import argparse
import base64
import json
import sys
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import auth helper
import os
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_access_token

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"


def api_request(alias: str, endpoint: str, method: str = "GET", body: dict = None) -> dict:
    """Make authenticated Gmail API request."""
    token = get_access_token(alias)
    url = f"{GMAIL_API}{endpoint}"
    
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
        print(f"Gmail API error ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)


def list_messages(alias: str, max_results: int = 10, query: str = None):
    """List recent messages."""
    params = f"maxResults={max_results}"
    if query:
        params += f"&q={urllib.parse.quote(query)}"
    
    result = api_request(alias, f"/users/me/messages?{params}")
    messages = result.get("messages", [])
    
    if not messages:
        print("No messages found.")
        return
    
    print(f"Found {len(messages)} messages:\n")
    
    for msg in messages:
        # Get message details
        details = api_request(alias, f"/users/me/messages/{msg['id']}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date")
        
        headers = {h["name"]: h["value"] for h in details.get("payload", {}).get("headers", [])}
        
        subject = headers.get("Subject", "(no subject)")
        from_addr = headers.get("From", "unknown")
        date = headers.get("Date", "")
        snippet = details.get("snippet", "")[:100]
        
        print(f"ID: {msg['id']}")
        print(f"  From: {from_addr}")
        print(f"  Subject: {subject}")
        print(f"  Date: {date}")
        print(f"  Preview: {snippet}...")
        print()


def read_message(alias: str, message_id: str):
    """Read a specific message."""
    result = api_request(alias, f"/users/me/messages/{message_id}?format=full")
    
    headers = {h["name"]: h["value"] for h in result.get("payload", {}).get("headers", [])}
    
    print(f"From: {headers.get('From', 'unknown')}")
    print(f"To: {headers.get('To', 'unknown')}")
    print(f"Subject: {headers.get('Subject', '(no subject)')}")
    print(f"Date: {headers.get('Date', '')}")
    print("-" * 50)
    
    # Extract body
    payload = result.get("payload", {})
    body = extract_body(payload)
    print(body)


def extract_body(payload: dict) -> str:
    """Extract text body from message payload."""
    mime_type = payload.get("mimeType", "")
    
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    
    if mime_type.startswith("multipart/"):
        parts = payload.get("parts", [])
        for part in parts:
            # Prefer plain text
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        
        # Fallback to HTML
        for part in parts:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    # Basic HTML stripping
                    import re
                    text = re.sub(r'<[^>]+>', '', html)
                    text = re.sub(r'\s+', ' ', text)
                    return text.strip()
        
        # Recurse into nested parts
        for part in parts:
            result = extract_body(part)
            if result:
                return result
    
    return "(Could not extract message body)"


def send_message(alias: str, to: str, subject: str, body: str, html: bool = False):
    """Send an email message."""
    # Get sender email from profile
    profile = api_request(alias, "/users/me/profile")
    from_email = profile.get("emailAddress", "me")
    
    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "html"))
    else:
        msg = MIMEText(body)
    
    msg["To"] = to
    msg["From"] = from_email
    msg["Subject"] = subject
    
    # Encode message
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    
    result = api_request(alias, "/users/me/messages/send", method="POST", body={"raw": raw})
    
    print(f"✓ Message sent successfully")
    print(f"  To: {to}")
    print(f"  Subject: {subject}")
    print(f"  Message ID: {result.get('id')}")


def search_messages(alias: str, query: str, max_results: int = 10):
    """Search messages with Gmail query syntax."""
    list_messages(alias, max_results, query)


def main():
    parser = argparse.ArgumentParser(description="Gmail operations")
    parser.add_argument("--alias", required=True, help="Account alias")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent messages")
    list_parser.add_argument("--max", type=int, default=10, help="Max messages to return")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search messages")
    search_parser.add_argument("query", help="Gmail search query")
    search_parser.add_argument("--max", type=int, default=10, help="Max messages to return")
    
    # Read command
    read_parser = subparsers.add_parser("read", help="Read a message")
    read_parser.add_argument("message_id", help="Message ID")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send a message")
    send_parser.add_argument("--to", required=True, help="Recipient email")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--html", action="store_true", help="Send as HTML")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_messages(args.alias, args.max)
    elif args.command == "search":
        search_messages(args.alias, args.query, args.max)
    elif args.command == "read":
        read_message(args.alias, args.message_id)
    elif args.command == "send":
        send_message(args.alias, args.to, args.subject, args.body, args.html)


if __name__ == "__main__":
    main()
