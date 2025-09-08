import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 
      (process.env.NODE_ENV === 'production' 
        ? 'https://agent.evanm.xyz'
        : 'http://localhost:8000');
        
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
