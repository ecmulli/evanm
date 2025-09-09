import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if accessing chat page
  if (request.nextUrl.pathname.startsWith('/chat')) {
    // Check for bearer token in cookies or headers
    const token = request.cookies.get('bearerToken')?.value;
    
    if (!token) {
      // Redirect to login if no token
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/chat/:path*']
};