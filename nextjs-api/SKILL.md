# Next.js API Skill

Patterns for building API routes in Next.js App Router.

## When to Use

- Building REST APIs in Next.js
- Backend logic for your frontend
- Proxy APIs to external services

## Route Structure

```
app/
├── api/
│   ├── items/
│   │   ├── route.ts           # GET /api/items, POST /api/items
│   │   └── [id]/
│   │       ├── route.ts       # GET/PUT/DELETE /api/items/:id
│   │       └── action/
│   │           └── route.ts   # POST /api/items/:id/action
│   └── health/
│       └── route.ts           # GET /api/health
```

## Basic CRUD

```typescript
// app/api/items/route.ts
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get('limit') || '10');
  
  const items = await db.items.findMany({ take: limit });
  return NextResponse.json({ items });
}

export async function POST(request: Request) {
  const body = await request.json();
  
  // Validate
  if (!body.title) {
    return NextResponse.json(
      { error: 'title required' }, 
      { status: 400 }
    );
  }
  
  const item = await db.items.create({ data: body });
  return NextResponse.json({ item }, { status: 201 });
}
```

```typescript
// app/api/items/[id]/route.ts
import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const item = await db.items.findUnique({ where: { id: params.id } });
  
  if (!item) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }
  
  return NextResponse.json({ item });
}

export async function PUT(
  request: Request,
  { params }: { params: { id: string } }
) {
  const body = await request.json();
  const item = await db.items.update({
    where: { id: params.id },
    data: body,
  });
  return NextResponse.json({ item });
}

export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  await db.items.delete({ where: { id: params.id } });
  return NextResponse.json({ success: true });
}
```

## API Key Authentication

```typescript
// lib/auth.ts
export function validateApiKey(request: Request): boolean {
  const apiKey = request.headers.get('x-api-key') 
    || new URL(request.url).searchParams.get('key');
  return apiKey === process.env.API_KEY;
}

// Middleware wrapper
export function withAuth(handler: Function) {
  return async (request: Request, context: any) => {
    if (!validateApiKey(request)) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return handler(request, context);
  };
}

// Usage
export const GET = withAuth(async (request: Request) => {
  // Protected logic
});
```

## Error Handling

```typescript
// lib/api-utils.ts
export function apiError(message: string, status: number = 400) {
  return NextResponse.json({ error: message }, { status });
}

export function apiSuccess<T>(data: T, status: number = 200) {
  return NextResponse.json(data, { status });
}

export async function withErrorHandling(
  handler: () => Promise<NextResponse>
) {
  try {
    return await handler();
  } catch (error) {
    console.error('API Error:', error);
    return apiError('Internal server error', 500);
  }
}

// Usage
export async function POST(request: Request) {
  return withErrorHandling(async () => {
    const body = await request.json();
    const item = await db.items.create({ data: body });
    return apiSuccess({ item }, 201);
  });
}
```

## Validation with Zod

```typescript
import { z } from 'zod';

const createItemSchema = z.object({
  title: z.string().min(1).max(200),
  type: z.enum(['note', 'link', 'image']),
  content: z.string().optional(),
  url: z.string().url().optional(),
});

export async function POST(request: Request) {
  const body = await request.json();
  
  const result = createItemSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json(
      { error: 'Validation failed', details: result.error.issues },
      { status: 400 }
    );
  }
  
  const item = await db.items.create({ data: result.data });
  return NextResponse.json({ item }, { status: 201 });
}
```

## CORS Headers

```typescript
// For APIs called from other origins
export async function GET(request: Request) {
  const response = NextResponse.json({ data: 'hello' });
  
  response.headers.set('Access-Control-Allow-Origin', '*');
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, X-Api-Key');
  
  return response;
}

// Handle preflight
export async function OPTIONS(request: Request) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key',
    },
  });
}
```

## Rate Limiting

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'), // 10 requests per 10 seconds
});

export async function POST(request: Request) {
  const ip = request.headers.get('x-forwarded-for') || 'anonymous';
  const { success, limit, remaining } = await ratelimit.limit(ip);
  
  if (!success) {
    return NextResponse.json(
      { error: 'Rate limit exceeded' },
      { 
        status: 429,
        headers: {
          'X-RateLimit-Limit': limit.toString(),
          'X-RateLimit-Remaining': remaining.toString(),
        }
      }
    );
  }
  
  // Process request...
}
```

## Best Practices

1. **Always validate input** - use Zod or similar
2. **Return consistent response shapes** - `{ data }` or `{ error }`
3. **Use proper HTTP status codes** - 201 for created, 404 for not found, etc.
4. **Add rate limiting** - protect against abuse
5. **Log errors server-side** - don't expose details to clients
6. **Use middleware for auth** - DRY principle
