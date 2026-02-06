# Railway Deploy Skill

Deploy Node.js services to Railway with auto-deploy from GitHub.

## When to Use

- Always-on backend services
- APIs and proxies
- Cron jobs and workers
- Anything that needs to run 24/7

## Quick Deploy

### 1. Create railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "node index.js"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### 2. Set Up package.json

```json
{
  "name": "my-service",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
```

### 3. Add Health Check

```javascript
app.get('/', (req, res) => {
  res.json({ status: 'ok', version: '1.0.0' });
});
```

### 4. Connect GitHub

1. Go to railway.app
2. New Project → Deploy from GitHub
3. Select repo
4. Railway auto-detects Node.js and deploys

## Environment Variables

Set in Railway dashboard or CLI:

```bash
railway variables set API_KEY=xxx
railway variables set DATABASE_URL=xxx
```

Access in code:
```javascript
const API_KEY = process.env.API_KEY;
```

## Custom Domain

1. Go to Settings → Domains
2. Add custom domain
3. Update DNS with provided CNAME

## Auto-Deploy

Railway auto-deploys on every push to the connected branch (usually `main`).

To deploy manually:
```bash
railway up
```

## Logs

View in dashboard or:
```bash
railway logs
```

## Pricing

- $5/month gives 500 hours + $5 usage
- Hobby tier is usually enough for small services
- Pay for what you use (CPU/RAM/bandwidth)

## Best Practices

1. **Always add health check** - Railway uses it for deployments
2. **Use environment variables** - never commit secrets
3. **Add error handling** - unhandled errors = crash = restart
4. **Log important events** - helps with debugging
5. **Set restart policy** - auto-recover from crashes
