# Gmail Proxy Skill

Build Gmail/Calendar integration via a REST proxy instead of implementing OAuth in your frontend.

## When to Use

- You need Gmail/Calendar access in a web app
- You want to avoid OAuth complexity in the frontend
- You need to support multiple Google accounts
- You want a clean API abstraction layer

## Architecture

```
Frontend (Vercel) → REST Proxy (Railway) → Gmail/Calendar API
```

**Why this pattern?**
- Proxy handles OAuth, token refresh, multiple accounts
- Frontend just makes simple REST calls with API key
- One source of truth for Google API access
- No token storage in frontend

## Implementation

### 1. Create the Proxy (Node.js/Express)

```javascript
const express = require('express');
const app = express();
app.use(express.json({ limit: '25mb' }));

// CORS for browser access
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, X-Api-Key');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

// API key auth
const API_KEY = process.env.API_KEY;
function auth(req, res, next) {
  const key = req.query.key || req.headers['x-api-key'];
  if (key !== API_KEY) return res.status(401).json({ error: 'Unauthorized' });
  next();
}

// Token management - load from env vars
const tokens = {};
for (const key of Object.keys(process.env)) {
  if (key.startsWith('TOKENS_')) {
    const account = key.replace('TOKENS_', '').toLowerCase();
    tokens[account] = JSON.parse(process.env[key]);
  }
}
```

### 2. Key Endpoints

```javascript
// List emails
app.get('/gmail/messages', auth, async (req, res) => {
  const { account, max = 10, q = '' } = req.query;
  // Call Gmail API with tokens[account]
});

// Send email (with optional 'from' for aliases)
app.post('/gmail/send', auth, async (req, res) => {
  const { account, to, subject, body, from } = req.body;
  const fromAddress = from || tokens[account].email;
  // Build MIME message and send
});

// Create draft
app.post('/gmail/drafts', auth, async (req, res) => {
  const { account, to, subject, body, threadId, replyToMessageId } = req.body;
  // Create draft, optionally as reply
});

// Calendar events
app.get('/calendar/events', auth, async (req, res) => {
  const { account, days = 7 } = req.query;
  // Fetch events for next N days
});
```

### 3. Deploy to Railway

```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "node index.js"
```

Environment variables needed:
- `API_KEY` - Your API key for auth
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret  
- `TOKENS_PERSONAL` - JSON tokens for personal account
- `TOKENS_WORK` - JSON tokens for work account

### 4. Frontend Usage

```typescript
const PROXY_URL = 'https://your-proxy.railway.app';
const API_KEY = process.env.NEXT_PUBLIC_PROXY_KEY;

// Fetch emails
const res = await fetch(
  `${PROXY_URL}/gmail/messages?account=personal&max=10&key=${API_KEY}`
);
const { messages } = await res.json();

// Send email
await fetch(`${PROXY_URL}/gmail/send?key=${API_KEY}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    account: 'work',
    to: 'someone@example.com',
    subject: 'Hello',
    body: 'Email body here'
  })
});
```

## OAuth Setup (One-time)

1. Create project in Google Cloud Console
2. Enable Gmail API and Calendar API
3. Create OAuth 2.0 credentials (Web application)
4. Run auth script locally to get tokens:

```javascript
// auth.js - run once per account
const { google } = require('googleapis');
const readline = require('readline');

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  'http://localhost:3000/callback'
);

const authUrl = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  scope: [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/calendar'
  ]
});

console.log('Visit:', authUrl);
// Exchange code for tokens, save to env var
```

## Best Practices

1. **Never expose tokens in frontend** - always go through proxy
2. **Use API key auth** - simple but effective for private APIs
3. **Enable CORS** - required for browser access
4. **Handle token refresh** - Google tokens expire, proxy should auto-refresh
5. **Support multiple accounts** - load tokens by account name
6. **Add 'from' parameter** - for sending as aliases

## Files

- `examples/proxy-server.js` - Full proxy implementation
- `examples/frontend-usage.ts` - TypeScript frontend examples
- `templates/railway.toml` - Railway config
