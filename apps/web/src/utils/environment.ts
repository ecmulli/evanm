export function getEnvironmentInfo() {
  if (typeof window === 'undefined') {
    // Server-side - check Railway environment
    const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN || '';
    const isStaging = railwayDomain.includes('staging') || railwayDomain.includes('-pr-');
    
    console.log('🖥️ SERVER Environment Detection:', {
      railwayDomain,
      isStaging,
      NODE_ENV: process.env.NODE_ENV,
      allRailwayVars: Object.keys(process.env).filter(key => key.includes('RAILWAY')).reduce((obj, key) => {
        obj[key] = process.env[key];
        return obj;
      }, {} as Record<string, string | undefined>)
    });
    
    return {
      isStaging,
      isLocal: false,
      agentDomain: isStaging ? 'staging.agent.evanm.xyz' : 'agent.evanm.xyz'
    };
  }
  
  // Client-side
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('localhost');
  
  // Check for staging using Railway's public domain variable or hostname patterns
  const railwayDomain = process.env.NEXT_PUBLIC_RAILWAY_DOMAIN || '';
  const isStaging = hostname.includes('staging') || 
                   railwayDomain.includes('staging') ||
                   railwayDomain.includes('-pr-');
  
  console.log('🌐 CLIENT Environment Detection:', {
    hostname,
    railwayDomain,
    isLocal,
    isStaging,
    allPublicVars: Object.keys(process.env).filter(key => key.startsWith('NEXT_PUBLIC')).reduce((obj, key) => {
      obj[key] = process.env[key];
      return obj;
    }, {} as Record<string, string | undefined>)
  });
  
  return {
    isStaging,
    isLocal,
    agentDomain: isLocal ? 'localhost:8000' : (isStaging ? 'staging.agent.evanm.xyz' : 'agent.evanm.xyz')
  };
}