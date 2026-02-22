import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith('/chat') || pathname.startsWith('/claw') || pathname.startsWith('/gateway')) {
    const token = request.cookies.get('bearerToken')?.value;
    
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/chat/:path*', '/claw/:path*', '/gateway', '/gateway/:path*']
};