import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const zeroclawUrl = process.env.ZEROCLAW_URL || 'http://localhost:3000';
    
    console.log('🔧 Backend URL:', {
      BACKEND_URL: process.env.BACKEND_URL,
      resolvedUrl: backendUrl,
      NODE_ENV: process.env.NODE_ENV
    });
    console.log('🦀 ZeroClaw URL:', zeroclawUrl);
        
    return [
      {
        source: '/claw/api/:path*',
        destination: `${zeroclawUrl}/v1/:path*`,
      },
      // ZeroClaw dashboard assets (served at /_app/*)
      {
        source: '/_app/:path*',
        destination: `${zeroclawUrl}/_app/:path*`,
      },
      {
        source: '/gateway/:path*',
        destination: `${zeroclawUrl}/:path*`,
      },
      {
        source: '/gateway',
        destination: `${zeroclawUrl}/`,
      },
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
