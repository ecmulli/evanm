'use client';

import { useRef, useCallback } from 'react';

export function useRateLimit(maxActions: number, windowMs: number) {
  const timestamps = useRef<number[]>([]);

  const checkLimit = useCallback(() => {
    const now = Date.now();
    timestamps.current = timestamps.current.filter((t) => now - t < windowMs);

    if (timestamps.current.length >= maxActions) {
      return false;
    }

    timestamps.current.push(now);
    return true;
  }, [maxActions, windowMs]);

  const remaining = () => {
    const now = Date.now();
    const recent = timestamps.current.filter((t) => now - t < windowMs);
    return Math.max(0, maxActions - recent.length);
  };

  return { checkLimit, remaining };
}
