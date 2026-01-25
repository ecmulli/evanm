'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface ViewSettings {
  showStars: boolean;
  showGrid: boolean;
  showMountains: boolean;
  showSun: boolean;
}

interface ViewContextType {
  settings: ViewSettings;
  toggleStars: () => void;
  toggleGrid: () => void;
  toggleMountains: () => void;
  toggleSun: () => void;
  resetView: () => void;
}

const defaultSettings: ViewSettings = {
  showStars: true,
  showGrid: true,
  showMountains: true,
  showSun: true,
};

const ViewContext = createContext<ViewContextType | undefined>(undefined);

interface ViewProviderProps {
  children: ReactNode;
}

export function ViewProvider({ children }: ViewProviderProps) {
  const [settings, setSettings] = useState<ViewSettings>(defaultSettings);

  const toggleStars = useCallback(() => {
    setSettings(prev => ({ ...prev, showStars: !prev.showStars }));
  }, []);

  const toggleGrid = useCallback(() => {
    setSettings(prev => ({ ...prev, showGrid: !prev.showGrid }));
  }, []);

  const toggleMountains = useCallback(() => {
    setSettings(prev => ({ ...prev, showMountains: !prev.showMountains }));
  }, []);

  const toggleSun = useCallback(() => {
    setSettings(prev => ({ ...prev, showSun: !prev.showSun }));
  }, []);

  const resetView = useCallback(() => {
    setSettings(defaultSettings);
  }, []);

  const value: ViewContextType = {
    settings,
    toggleStars,
    toggleGrid,
    toggleMountains,
    toggleSun,
    resetView,
  };

  return (
    <ViewContext.Provider value={value}>
      {children}
    </ViewContext.Provider>
  );
}

export function useView(): ViewContextType {
  const context = useContext(ViewContext);
  if (context === undefined) {
    throw new Error('useView must be used within a ViewProvider');
  }
  return context;
}

export { ViewContext };
