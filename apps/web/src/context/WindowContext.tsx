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

// Default window positions with slight offset for cascading effect
const getDefaultPosition = (windowCount: number) => ({
  x: 100 + (windowCount * 30) % 200,
  y: 100 + (windowCount * 30) % 150,
});

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
        const windowWidth = Math.floor((window.innerWidth - 100) / cols);
        const windowHeight = Math.floor((window.innerHeight - 132) / Math.ceil(prev.length / cols));
        
        return prev.map((w, i) => ({
          ...w,
          position: { 
            x: 50 + (i % cols) * windowWidth, 
            y: 50 + Math.floor(i / cols) * windowHeight 
          },
          zIndex: 100 + i,
        }));
      }
    });
  }, []);

  const openWindow = useCallback((config: OpenWindowConfig) => {
    // Check if a window with the same contentId is already open
    setWindows(prev => {
      const existingWindow = prev.find(w => 
        w.contentId === config.contentId && w.appType === config.appType
      );
      
      if (existingWindow) {
        // Focus existing window by bringing it to top
        const newTopZ = topZIndex + 1;
        setTopZIndex(newTopZ);
        return prev.map(w =>
          w.id === existingWindow.id ? { ...w, zIndex: newTopZ } : w
        );
      }

      const newWindow: WindowState = {
        id: generateWindowId(),
        appType: config.appType,
        title: config.title,
        position: config.position || getDefaultPosition(prev.length),
        zIndex: topZIndex + 1,
        isMinimized: false,
        contentId: config.contentId,
      };

      setTopZIndex(p => p + 1);
      return [...prev, newWindow];
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
