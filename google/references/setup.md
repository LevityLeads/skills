# Google Cloud Project Setup

One-time setup to enable Gmail and Calendar APIs with OAuth.

## 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name it (e.g., "OpenClaw Integration") and create

## 2. Enable APIs

1. Go to **APIs & Services** → **Library**
2. Search and enable:
   - **Gmail API**
   - **Google Calendar API**

## 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (or Internal if using Google Workspace)
3. Fill in:
   - App name: "OpenClaw"
   - User support email: your email
   - Developer contact: your email
4. **Scopes**: Add these:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/calendar.events`
5. **Test users**: Add email addresses you'll authorize

## 4. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: "OpenClaw"
5. **Authorized redirect URIs**: Add `https://oauth.pstmn.io/v1/callback` (for manual flow)
6. Click **Create** and save the client ID and secret

## 5. Save Credentials

Create `/data/workspace/.secrets/google_credentials.json`:

```json
{
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "https://oauth.pstmn.io/v1/callback"
}
```

## 6. Authorize an Account

Run the auth script to get an OAuth URL:

```bash
python3 skills/google/scripts/auth.py url
```

1. Open the URL in a browser
2. Sign in and authorize
3. Copy the `code` parameter from the redirect URL
4. Exchange for tokens:

```bash
python3 skills/google/scripts/auth.py exchange "AUTHORIZATION_CODE"
```

The account is now ready to use.

## Notes

- **Refresh tokens**: Stored automatically, refreshed when expired
- **Multiple accounts**: Repeat step 6 for each account
- **Production**: Submit app for verification to remove "unverified app" warning
