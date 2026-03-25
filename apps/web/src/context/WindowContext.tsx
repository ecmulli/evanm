'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { WindowState, WindowContextType, OpenWindowConfig } from '@/types/window';

const WindowContext = createContext<WindowContextType | undefined>(undefined);

// Generate unique window IDs
let windowIdCounter = 0;
const generateWindowId = (): string => {
  windowIdCounter += 1;
  return `window-${windowIdCounter}-${Date.now()}`;
};

// Center the window (80% width capped at 750px, 80% height)
const MAX_WINDOW_WIDTH = 750;
const getDefaultPosition = () => {
  const vw = typeof window !== 'undefined' ? window.innerWidth : 1200;
  const vh = typeof window !== 'undefined' ? window.innerHeight - 32 : 768;
  const winWidth = Math.min(vw * 0.8, MAX_WINDOW_WIDTH);
  const winHeight = vh * 0.8;
  return { x: (vw - winWidth) / 2, y: (vh - winHeight) / 2 };
};

interface WindowProviderProps {
  children: ReactNode;
}

export function WindowProvider({ children }: WindowProviderProps) {
  const [windows, setWindows] = useState<WindowState[]>([]);
  const [topZIndex, setTopZIndex] = useState(100);

  const closeWindow = useCallback((id: string) => {
    setWindows(prev => prev.filter(w => w.id !== id));
  }, []);

  const closeTopWindow = useCallback(() => {
    setWindows(prev => {
      if (prev.length === 0) return prev;
      // Find the window with the highest zIndex
      const topWindow = prev.reduce((top, w) => 
        w.zIndex > top.zIndex ? w : top
      , prev[0]);
      return prev.filter(w => w.id !== topWindow.id);
    });
  }, []);

  const closeAllWindows = useCallback(() => {
    setWindows([]);
  }, []);

  const focusWindow = useCallback((id: string) => {
    setWindows(prev => {
      const window = prev.find(w => w.id === id);
      if (!window || window.zIndex === topZIndex) {
        return prev; // Already on top or doesn't exist
      }

      const newTopZ = topZIndex + 1;
      setTopZIndex(newTopZ);

      return prev.map(w =>
        w.id === id ? { ...w, zIndex: newTopZ } : w
      );
    });
  }, [topZIndex]);

  const minimizeWindow = useCallback((id: string) => {
    setWindows(prev =>
      prev.map(w =>
        w.id === id ? { ...w, isMinimized: true } : w
      )
    );
  }, []);

  const arrangeWindows = useCallback((mode: 'cascade' | 'tile') => {
    setWindows(prev => {
      if (prev.length === 0) return prev;
      
      if (mode === 'cascade') {
        return prev.map((w, i) => ({
          ...w,
          position: { x: 50 + i * 30, y: 50 + i * 30 },
          zIndex: 100 + i,
        }));
      } else {
        // Tile mode - arrange in grid
        const cols = Math.ceil(Math.sqrt(prev.length));
        const screenWidth = typeof globalThis.window !== 'undefined' ? globalThis.window.innerWidth : 1200;
        const screenHeight = typeof globalThis.window !== 'undefined' ? globalThis.window.innerHeight : 800;
        const tileWidth = Math.floor((screenWidth - 100) / cols);
        const tileHeight = Math.floor((screenHeight - 132) / Math.ceil(prev.length / cols));
        
        return prev.map((w, i) => ({
          ...w,
          position: { 
            x: 50 + (i % cols) * tileWidth, 
            y: 50 + Math.floor(i / cols) * tileHeight 
          },
          zIndex: 100 + i,
        }));
      }
    });
  }, []);

  const updateWindowPosition = useCallback((id: string, position: { x: number; y: number }) => {
    setWindows(prev =>
      prev.map(w =>
        w.id === id ? { ...w, position } : w
      )
    );
  }, []);

  const openWindow = useCallback((config: OpenWindowConfig) => {
    setWindows(prev => {
      // Check if this exact window is already open
      const existingWindow = prev.find(w =>
        w.contentId === config.contentId && w.appType === config.appType
      );
      if (existingWindow) {
        return prev; // Already showing this content
      }

      // Single-window mode: replace all existing windows
      const newWindow: WindowState = {
        id: generateWindowId(),
        appType: config.appType,
        title: config.title,
        position: config.position || getDefaultPosition(),
        zIndex: topZIndex + 1,
        isMinimized: false,
        contentId: config.contentId,
      };

      setTopZIndex(p => p + 1);
      return [newWindow];
    });
  }, [topZIndex]);

  const value: WindowContextType = {
    windows,
    topZIndex,
    openWindow,
    closeWindow,
    closeTopWindow,
    closeAllWindows,
    focusWindow,
    minimizeWindow,
    arrangeWindows,
    updateWindowPosition,
  };

  return (
    <WindowContext.Provider value={value}>
      {children}
    </WindowContext.Provider>
  );
}

export function useWindowContext(): WindowContextType {
  const context = useContext(WindowContext);
  if (context === undefined) {
    throw new Error('useWindowContext must be used within a WindowProvider');
  }
  return context;
}

export { WindowContext };
