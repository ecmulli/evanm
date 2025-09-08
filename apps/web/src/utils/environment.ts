export function getEnvironmentInfo() {
  if (typeof window === 'undefined') {
    // Server-side
    return {
      isStaging: false,
      agentDomain: 'agent.evanm.xyz'
    };
  }
  
  // Client-side
  const hostname = window.location.hostname;
  const isStaging = hostname.includes('staging');
  
  return {
    isStaging,
    agentDomain: isStaging ? 'staging.agent.evanm.xyz' : 'agent.evanm.xyz'
  };
}