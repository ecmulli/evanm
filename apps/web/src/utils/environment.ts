export function getEnvironmentInfo() {
  if (typeof window === 'undefined') {
    // Server-side - check environment variable
    const isStaging = process.env.ENVIRONMENT === 'staging';
    
    console.log('🖥️ SERVER Environment Detection:', {
      ENVIRONMENT: process.env.ENVIRONMENT,
      isStaging,
      NODE_ENV: process.env.NODE_ENV
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
  
  // Check for staging using environment variable or hostname patterns
  const environment = process.env.NEXT_PUBLIC_ENVIRONMENT || '';
  const isStaging = hostname.includes('staging') || environment === 'staging';
  
  console.log('🌐 CLIENT Environment Detection:', {
    hostname,
    environment,
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