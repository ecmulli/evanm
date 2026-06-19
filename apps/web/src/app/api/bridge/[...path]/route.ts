import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';

// Server-side proxy to the local claude-bridge. Keeps BRIDGE_TOKEN off the client.
// Forwards CRUD (JSON) and /chat (SSE) transparently by streaming the upstream body.
const BRIDGE_URL = process.env.BRIDGE_URL ?? 'http://127.0.0.1:8787';
const BRIDGE_TOKEN = process.env.BRIDGE_TOKEN ?? '';

async function proxy(req: NextRequest, path: string[]) {
  if (!validateApiAuth(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const target = `${BRIDGE_URL}/${path.join('/')}${req.nextUrl.search}`;
  const isBodyless = req.method === 'GET' || req.method === 'HEAD';

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers: {
        Authorization: `Bearer ${BRIDGE_TOKEN}`,
        'content-type': req.headers.get('content-type') ?? 'application/json',
      },
      body: isBodyless ? undefined : await req.text(),
      // @ts-expect-error - Node fetch needs duplex for request bodies
      duplex: 'half',
    });
  } catch {
    return NextResponse.json(
      { error: 'bridge unreachable', hint: 'Is claude-bridge running / Funnel up?' },
      { status: 502 },
    );
  }

  // Stream the upstream body straight through (works for JSON and text/event-stream).
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'content-type': upstream.headers.get('content-type') ?? 'application/json',
      'cache-control': 'no-cache',
    },
  });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, (await ctx.params).path);
}
export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, (await ctx.params).path);
}
export async function DELETE(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, (await ctx.params).path);
}
