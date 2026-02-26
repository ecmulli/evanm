import { NextRequest } from 'next/server';

export function validateApiAuth(request: NextRequest): boolean {
  const bearerToken = process.env.BEARER_TOKEN;

  // No token configured → allow all (local dev)
  if (!bearerToken) return true;

  // Check Authorization header first
  const authHeader = request.headers.get('Authorization');
  if (authHeader?.startsWith('Bearer ')) {
    const token = authHeader.slice(7);
    if (token === bearerToken) return true;
  }

  // Fall back to cookie
  const cookieToken = request.cookies.get('bearerToken')?.value;
  if (cookieToken === bearerToken) return true;

  return false;
}
