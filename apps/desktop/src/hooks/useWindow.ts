'use client';

import { useWindowContext } from '@/context/WindowContext';
import { OpenWindowConfig, WindowState } from '@/types/window';

export function useWindow() {
  const { windows, topZIndex, openWindow, closeWindow, focusWindow, minimizeWindow } = useWindowContext();

  // Get only visible (non-minimized) windows
  const visibleWindows = windows.filter(w => !w.isMinimized);

  // Get minimized windows (for potential dock/taskbar)
  const minimizedWindows = windows.filter(w => w.isMinimized);

  // Check if a specific window is focused (has the highest z-index)
  const isWindowFocused = (id: string): boolean => {
    const window = windows.find(w => w.id === id);
    return window ? window.zIndex === topZIndex : false;
  };

  // Get a specific window by ID
  const getWindow = (id: string): WindowState | undefined => {
    return windows.find(w => w.id === id);
  };

  // Restore a minimized window
  const restoreWindow = (id: string) => {
    focusWindow(id);
    // The focusWindow already handles bringing to front
    // We need to also un-minimize it
  };

  return {
    windows,
    visibleWindows,
    minimizedWindows,
    topZIndex,
    openWindow,
    closeWindow,
    focusWindow,
    minimizeWindow,
    isWindowFocused,
    getWindow,
    restoreWindow,
  };
}

// Convenience hook for opening specific app types
export function useOpenApp() {
  const { openWindow } = useWindowContext();

  const openSimpleText = (title: string, contentId: string) => {
    openWindow({
      appType: 'simpletext',
      title,
      contentId,
    });
  };

  const openStickies = () => {
    openWindow({
      appType: 'stickies',
      title: 'Guestbook',
    });
  };

  const openFolder = (title: string, contentId: string) => {
    openWindow({
      appType: 'folder',
      title,
      contentId,
    });
  };

  return {
    openSimpleText,
    openStickies,
    openFolder,
    openWindow,
  };
}
