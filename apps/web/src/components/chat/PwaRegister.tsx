'use client';

import { useEffect } from 'react';

// Registers the service worker so the chat is installable + can receive push.
export function PwaRegister() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, []);
  return null;
}
