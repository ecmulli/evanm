import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  
  async rewrites() {
    // Simple backend URL determination
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    console.log('🔧 Backend URL:', {
      BACKEND_URL: process.env.BACKEND_URL,
      resolvedUrl: backendUrl,
      NODE_ENV: process.env.NODE_ENV
    });
        
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
  // Enable if you want to serve this on a subpath like /chat
  // basePath: process.env.NODE_ENV === 'production' ? '/chat' : '',
  // assetPrefix: process.env.NODE_ENV === 'production' ? '/chat' : '',
};

export default nextConfig;
