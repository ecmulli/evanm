import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production' 
          ? 'https://agent-evanm.railway.app/api/:path*'  // Replace with your actual Railway backend URL
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
  // Enable if you want to serve this on a subpath like /chat
  // basePath: process.env.NODE_ENV === 'production' ? '/chat' : '',
  // assetPrefix: process.env.NODE_ENV === 'production' ? '/chat' : '',
};

export default nextConfig;
