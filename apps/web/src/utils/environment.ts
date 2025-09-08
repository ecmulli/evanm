export function getEnvironmentInfo() {
  if (typeof window === 'undefined') {
    // Server-side - assume production
    return {
      isStaging: false,
      isLocal: false,
      agentDomain: 'agent.evanm.xyz'
    };
  }
  
  // Client-side
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('localhost');
  const isStaging = hostname.includes('staging');
  
  return {
    isStaging,
    isLocal,
    agentDomain: isLocal ? 'localhost:8000' : (isStaging ? 'staging.agent.evanm.xyz' : 'agent.evanm.xyz')
  };
}