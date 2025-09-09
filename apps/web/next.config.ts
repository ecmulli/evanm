import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  
  env: {
    NEXT_PUBLIC_RAILWAY_DOMAIN: process.env.RAILWAY_PUBLIC_DOMAIN,
  },
  
  async rewrites() {
    // Determine backend URL based on environment
    let backendUrl = process.env.BACKEND_URL;
    
    const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN || '';
    const nodeEnv = process.env.NODE_ENV;
    
    console.log('🔧 NEXT.CONFIG Environment Check:', {
      BACKEND_URL: backendUrl,
      NODE_ENV: nodeEnv,
      RAILWAY_PUBLIC_DOMAIN: railwayDomain,
      VERCEL_URL: process.env.VERCEL_URL,
      allRailwayVars: Object.keys(process.env).filter(key => key.includes('RAILWAY')).reduce((obj, key) => {
        obj[key] = process.env[key];
        return obj;
      }, {} as Record<string, string | undefined>)
    });
    
    if (!backendUrl) {
      if (nodeEnv === 'production') {
        // Check if we're on staging domain
        const isStaging = railwayDomain.includes('staging') || 
                         railwayDomain.includes('-pr-') ||
                         process.env.VERCEL_URL?.includes('staging');
        backendUrl = isStaging 
          ? 'https://staging.agent.evanm.xyz'
          : 'https://agent.evanm.xyz';
          
        console.log('🎯 Backend URL Decision:', { isStaging, backendUrl });
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
