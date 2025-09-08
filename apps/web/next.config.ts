import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  
  async rewrites() {
    // Determine backend URL based on environment
    let backendUrl = process.env.BACKEND_URL;
    
    if (!backendUrl) {
      if (process.env.NODE_ENV === 'production') {
        // Check if we're on staging domain
        const isStaging = process.env.RAILWAY_PUBLIC_DOMAIN?.includes('staging') || 
                         process.env.VERCEL_URL?.includes('staging');
        backendUrl = isStaging 
          ? 'https://staging.agent.evanm.xyz'
          : 'https://agent.evanm.xyz';
      } else {
        backendUrl = 'http://localhost:8000';
      }
    }
        
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
