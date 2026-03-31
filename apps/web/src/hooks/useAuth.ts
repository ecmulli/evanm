'use client';

import { useState, useEffect } from 'react';

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const cookieToken = getCookie('bearerToken');
    const localToken = localStorage.getItem('bearerToken');
    setIsAuthenticated(!!(cookieToken || localToken));
  }, []);

  return { isAuthenticated };
}
