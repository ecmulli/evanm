'use client';

import React, { useEffect } from 'react';
import MenuBar from './MenuBar';
import DesktopIcon from './DesktopIcon';
import WindowFrame from './WindowFrame';
import SimpleText from './apps/SimpleText';
import Stickies from './apps/Stickies';
import Folder from './apps/Folder';
import { useWindow } from '@/hooks/useWindow';
import { useView } from '@/context/ViewContext';
import { desktopIcons } from '@/data/content';
import { WindowState } from '@/types/window';

function WindowContent({ window }: { window: WindowState }) {
  switch (window.appType) {
    case 'simpletext':
      return <SimpleText contentId={window.contentId || ''} />;
    case 'stickies':
      return <Stickies />;
    case 'folder':
      return <Folder contentId={window.contentId || ''} />;
    default:
      return <div className="p-4">Unknown app type</div>;
  }
}

function getWindowDimensions(appType: string): { width: number; height: number } {
  switch (appType) {
    case 'simpletext':
      return { width: 450, height: 350 };
    case 'stickies':
      return { width: 320, height: 450 };
    case 'folder':
      return { width: 400, height: 300 };
    default:
      return { width: 400, height: 300 };
  }
}

export default function Desktop() {
  const { visibleWindows, closeWindow, openWindow } = useWindow();
  const { settings } = useView();

  // Open "About Me.txt" window centered on page load
  useEffect(() => {
    // Only open if no windows are currently open (first load)
    if (visibleWindows.length === 0) {
      const windowWidth = 450;
      const windowHeight = 350;
      const menuBarHeight = 32;
      
      // Calculate center position relative to the desktop container
      // Desktop container height is calc(100vh - 32px), width is 100vw
      const desktopWidth = typeof window !== 'undefined' ? window.innerWidth : 1200;
      const desktopHeight = typeof window !== 'undefined' ? window.innerHeight - menuBarHeight : 800 - menuBarHeight;
      
      const centerX = (desktopWidth - windowWidth) / 2;
      const centerY = (desktopHeight - windowHeight) / 2;
      
      openWindow({
        appType: 'simpletext',
        title: 'About Me.txt',
        contentId: 'about-me',
        position: { x: centerX, y: centerY },
      });
    }
  }, []); // Empty dependency array - only run on mount

  return (
    <div className="desktop-environment">
      {/* Menu Bar */}
      <MenuBar />

      {/* Desktop Area (below menu bar) with pixel art background */}
      <div 
        className="pixel-desktop relative w-full overflow-hidden"
        style={{ 
          height: 'calc(100vh - 32px)',
          marginTop: '32px',
        }}
      >
        {/* Stars layer */}
        {settings.showStars && <div className="stars" />}

        {/* Sun */}
        {settings.showSun && <div className="pixel-sun" />}

        {/* Mountains */}
        {settings.showMountains && (
          <div className="pixel-mountains">
            <div className="mountain mountain-1" />
            <div className="mountain mountain-2" />
            <div className="mountain mountain-3" />
            <div className="mountain mountain-4" />
          </div>
        )}

        {/* Grid overlay */}
        {settings.showGrid && <div className="pixel-grid" />}

        {/* Desktop Icons */}
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
          {desktopIcons.map((icon) => (
            <DesktopIcon key={icon.id} config={icon} />
          ))}
        </div>

        {/* Open Windows */}
        {visibleWindows.map((window) => {
          const dimensions = getWindowDimensions(window.appType);
          return (
            <WindowFrame
              key={window.id}
              id={window.id}
              title={window.title}
              initialPosition={window.position}
              zIndex={window.zIndex}
              width={dimensions.width}
              height={dimensions.height}
              onClose={() => closeWindow(window.id)}
            >
              <WindowContent window={window} />
            </WindowFrame>
          );
        })}
      </div>
    </div>
  );
}
