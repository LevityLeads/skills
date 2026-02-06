#!/usr/bin/env python3
"""
Google OAuth2 authentication for OpenClaw.
Uses localhost callback flow for Desktop apps.
"""

import argparse
import json
import os
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import urllib.request
import urllib.error

# OAuth endpoints
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Scopes for Gmail + Calendar + Contacts (full access)
SCOPES = [
    # Gmail - full control
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",     # Filters, IMAP/POP
    "https://www.googleapis.com/auth/gmail.settings.sharing",   # Delegates, send-as
    # Calendar - full control
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    # Contacts - read + write
    "https://www.googleapis.com/auth/contacts",
    # Tasks
    "https://www.googleapis.com/auth/tasks",
]

# Default port for localhost callback
CALLBACK_PORT = 8085


def get_config_dir():
    """Get config directory for storing tokens."""
    # Prefer XDG config dir
    xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = os.path.join(xdg_config, "openclaw-google")
    
    # Fallback to skill directory
    if not os.path.exists(os.path.dirname(config_dir)):
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tokens")
    
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_token_path(alias: str) -> str:
    """Get path to token file for an alias."""
    return os.path.join(get_config_dir(), f"{alias}.json")


def get_credentials():
    """Get OAuth credentials from env or raise error."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set", file=sys.stderr)
        print("\nSet them in your environment or OpenClaw config:", file=sys.stderr)
        print('  export GOOGLE_CLIENT_ID="your-client-id"', file=sys.stderr)
        print('  export GOOGLE_CLIENT_SECRET="your-client-secret"', file=sys.stderr)
        sys.exit(1)
    
    return client_id, client_secret


def load_tokens(alias: str) -> dict | None:
    """Load tokens for an alias."""
    path = get_token_path(alias)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_tokens(alias: str, tokens: dict):
    """Save tokens for an alias."""
    path = get_token_path(alias)
    with open(path, "w") as f:
        json.dump(tokens, f, indent=2)
    print(f"Tokens saved to {path}")


def refresh_access_token(alias: str) -> str | None:
    """Refresh access token if expired. Returns valid access token or None."""
    tokens = load_tokens(alias)
    if not tokens:
        return None
    
    # Check if token is expired (with 5 min buffer)
    import time
    expires_at = tokens.get("expires_at", 0)
    if time.time() < expires_at - 300:
        return tokens["access_token"]
    
    # Need to refresh
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print(f"No refresh token for {alias}, need to re-authenticate", file=sys.stderr)
        return None
    
    client_id, client_secret = get_credentials()
    
    data = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            
            # Update tokens
            tokens["access_token"] = result["access_token"]
            if "refresh_token" in result:
                tokens["refresh_token"] = result["refresh_token"]
            if "expires_in" in result:
                import time
                tokens["expires_at"] = time.time() + result["expires_in"]
            
            save_tokens(alias, tokens)
            return tokens["access_token"]
    except urllib.error.HTTPError as e:
        print(f"Failed to refresh token: {e.read().decode()}", file=sys.stderr)
        return None


def get_access_token(alias: str) -> str:
    """Get valid access token for alias, refreshing if needed."""
    token = refresh_access_token(alias)
    if not token:
        print(f"No valid token for alias '{alias}'. Run: python3 scripts/auth.py --alias {alias}", file=sys.stderr)
        sys.exit(1)
    return token


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback on localhost."""
    
    auth_code = None
    error = None
    
    def do_GET(self):
        """Handle GET request with auth code."""
        query = parse_qs(urlparse(self.path).query)
        
        if "code" in query:
            OAuthCallbackHandler.auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family: system-ui; text-align: center; padding: 50px;">
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        elif "error" in query:
            OAuthCallbackHandler.error = query.get("error_description", query["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"""
                <html><body style="font-family: system-ui; text-align: center; padding: 50px;">
                <h1>Authentication Failed</h1>
                <p>{OAuthCallbackHandler.error}</p>
                </body></html>
            """.encode())
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def authenticate(alias: str, port: int = CALLBACK_PORT):
    """Run OAuth flow and save tokens."""
    client_id, client_secret = get_credentials()
    
    redirect_uri = f"http://localhost:{port}"
    
    # Build auth URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",  # Force consent to get refresh token
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    
    print(f"Opening browser for authentication...")
    print(f"If browser doesn't open, visit:\n{auth_url}\n")
    
    # Start local server
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.timeout = 120  # 2 minute timeout
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback
    print(f"Waiting for authentication on http://localhost:{port}...")
    while OAuthCallbackHandler.auth_code is None and OAuthCallbackHandler.error is None:
        server.handle_request()
    
    server.server_close()
    
    if OAuthCallbackHandler.error:
        print(f"Authentication failed: {OAuthCallbackHandler.error}", file=sys.stderr)
        sys.exit(1)
    
    code = OAuthCallbackHandler.auth_code
    
    # Exchange code for tokens
    print("Exchanging code for tokens...")
    data = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code": code,
    }).encode()
    
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            
            import time
            tokens = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "expires_at": time.time() + result.get("expires_in", 3600),
                "scope": result.get("scope"),
            }
            
            save_tokens(alias, tokens)
            print(f"\n✓ Successfully authenticated as '{alias}'")
            
    except urllib.error.HTTPError as e:
        print(f"Failed to exchange code: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def list_accounts():
    """List all configured accounts."""
    config_dir = get_config_dir()
    print(f"Token directory: {config_dir}\n")
    
    if not os.path.exists(config_dir):
        print("No accounts configured.")
        return
    
    accounts = []
    for f in os.listdir(config_dir):
        if f.endswith(".json"):
            alias = f[:-5]
            tokens = load_tokens(alias)
            if tokens:
                # Check if token is valid
                import time
                expires_at = tokens.get("expires_at", 0)
                status = "valid" if time.time() < expires_at else "expired (will auto-refresh)"
                accounts.append((alias, status))
    
    if accounts:
        print("Configured accounts:")
        for alias, status in accounts:
            print(f"  - {alias}: {status}")
    else:
        print("No accounts configured.")


def main():
    parser = argparse.ArgumentParser(description="Google OAuth2 authentication")
    parser.add_argument("--alias", help="Account alias (e.g., 'work', 'personal')")
    parser.add_argument("--port", type=int, default=CALLBACK_PORT, help=f"Callback port (default: {CALLBACK_PORT})")
    parser.add_argument("action", nargs="?", choices=["auth", "list"], default="auth", help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_accounts()
    else:
        if not args.alias:
            print("Error: --alias required for authentication", file=sys.stderr)
            print("Example: python3 scripts/auth.py --alias work", file=sys.stderr)
            sys.exit(1)
        authenticate(args.alias, args.port)


if __name__ == "__main__":
    main()
