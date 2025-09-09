export function getEnvironmentInfo() {
  if (typeof window === 'undefined') {
    // Server-side - for display purposes only
    return {
      isStaging: false,
      isLocal: false,
      agentDomain: 'agent.evanm.xyz' // Default display
    };
  }
  
  // Client-side - determine display domain from hostname
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
  const isStaging = hostname.includes('staging');
  const isPR = hostname.includes('railway.app') && !isLocal;
  
  let displayDomain: string;
  if (isLocal) {
    displayDomain = 'localhost:8000';
  } else if (isStaging) {
    displayDomain = 'staging.agent.evanm.xyz';
  } else if (isPR) {
    displayDomain = 'agent (internal)';
  } else {
    displayDomain = 'agent.evanm.xyz';
  }
  
  return {
    isStaging,
    isLocal,
    agentDomain: displayDomain
  };
}