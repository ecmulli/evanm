# Web App (Next.js)

Located in `apps/web/`. Provides a minimal UI for login and an AI-assisted chat interface to create tasks via the Agent API.

## Pages

### `/` Home
File: `src/app/page.tsx`
- Shows CTA to open Chat if authenticated, else Login
- Displays connected backend domain via `getEnvironmentInfo()`

Example navigation:
```tsx
import Link from 'next/link';
<Link href={isAuthenticated ? '/chat' : '/login'}>Open</Link>
```

### `/login`
File: `src/app/login/page.tsx`
- Accepts a bearer token and validates it via `GET /api/v1/auth/validate`
- On success, writes token to both `localStorage` and a `bearerToken` cookie, then redirects to `/chat`

Usage notes:
- Token format validation: expects a long hexadecimal string
- Cookie is used by middleware for route protection

### `/chat`
File: `src/app/chat/page.tsx`
- Chat UI that performs a dry-run call to `/api/v1/task_creator` for preview
- After confirmation, performs actual creation call
- Supports optional image uploads (converted to data URLs for OCR demo)

Request sample (client-side):
```ts
await fetch('/api/v1/task_creator', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ text_inputs: [input], dry_run })
});
```

## Middleware

File: `src/middleware.ts`
- Protects `/chat` routes; redirects to `/login` if `bearerToken` cookie is missing

```ts
export const config = { matcher: ['/chat/:path*'] };
```

## Utilities

### `getEnvironmentInfo()`
File: `src/utils/environment.ts`
- Server: returns default display domain
- Client: derives display domain from `window.location.hostname` and identifies local/staging/PR contexts

Return shape:
```ts
{ isStaging: boolean, isLocal: boolean, agentDomain: string }
```

## Authentication Flow
1. User enters token on `/login`
2. App calls `GET /api/v1/auth/validate` with `Authorization: Bearer <token>`
3. On 200 OK, token persisted to localStorage and cookie; redirect to `/chat`
4. Middleware enforces presence of cookie for `/chat`

## Styling & Icons
- Tailwind CSS utility classes for layout and styling
- Icons from `lucide-react` used in chat UI