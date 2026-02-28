import { NextRequest, NextResponse } from 'next/server';

// Local auth validation endpoint — validates bearer token without
// needing the agent backend to be running.
export async function GET(request: NextRequest) {
  const bearerToken = process.env.BEARER_TOKEN;

  // No token configured → allow all (local dev)
  if (!bearerToken) {
    return NextResponse.json({ valid: true });
  }

  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Missing bearer token' }, { status: 401 });
  }

  const token = authHeader.slice(7);
  if (token !== bearerToken) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
  }

  return NextResponse.json({ valid: true });
}
