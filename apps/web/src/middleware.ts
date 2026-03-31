import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Dashboard is accessible to everyone (demo mode for unauthenticated users)
  // Auth state is handled client-side in the dashboard page
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*']
};