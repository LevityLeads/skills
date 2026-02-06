# Vercel Deploy Skill

Deploy Next.js apps to Vercel with automatic preview deployments.

## When to Use

- Next.js applications
- Static sites
- Serverless functions
- Edge functions

## Quick Deploy

### 1. Connect GitHub

1. Go to vercel.com
2. Add New → Project
3. Import Git Repository
4. Select your repo
5. Vercel auto-detects Next.js

### 2. Environment Variables

Add in Vercel dashboard:
- Project Settings → Environment Variables

Or use `.env.local` for local dev (don't commit):
```
NEXT_PUBLIC_API_URL=https://api.example.com
DATABASE_URL=postgres://...
```

### 3. Deploy Hook (Optional)

For programmatic deploys:

1. Project Settings → Git → Deploy Hooks
2. Create hook, get URL
3. Trigger with:
```bash
curl -X POST "https://api.vercel.com/v1/integrations/deploy/..."
```

## vercel.json (Optional)

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/old-path",
      "destination": "/new-path",
      "permanent": true
    }
  ]
}
```

## Preview Deployments

Every PR gets a unique preview URL:
- `your-app-git-branch-name-username.vercel.app`

Great for:
- Testing changes before merge
- Sharing with stakeholders
- QA review

## Custom Domain

1. Project Settings → Domains
2. Add domain
3. Update DNS:
   - A record: `76.76.21.21`
   - Or CNAME: `cname.vercel-dns.com`

## Edge Functions

```typescript
// app/api/edge-example/route.ts
export const runtime = 'edge';

export async function GET(request: Request) {
  return new Response('Hello from the edge!');
}
```

## Serverless Function Limits

- 10 second timeout (Hobby)
- 60 second timeout (Pro)
- 50MB function size
- 4.5MB response size

## Best Practices

1. **Use environment variables** - never hardcode secrets
2. **Optimize images** - use next/image
3. **Enable caching** - use ISR or static generation where possible
4. **Monitor with Vercel Analytics** - built-in performance insights
5. **Use preview deployments** - test before production
