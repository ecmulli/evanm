'use client';

import { useState, useEffect } from 'react';

export function useIsMobile(breakpoint: number = 640): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < breakpoint);
    };

    // Check on mount
    checkMobile();

    // Listen for resize
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [breakpoint]);

  return isMobile;
}

export function useIsTouchDevice(): boolean {
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  return isTouch;
}

// Rows of compact icons that fit beside the window on a short landscape screen (a sideways phone). 0 = not that layout.
export function useLandscapeDockRows(maxHeight: number = 500): number {
  const [rows, setRows] = useState(0);

  useEffect(() => {
    const check = () => {
      const { innerWidth: w, innerHeight: h } = window;
      setRows(w > h && h < maxHeight ? Math.max(1, Math.floor((h - 60) / 86)) : 0);
    };
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, [maxHeight]);

  return rows;
}
