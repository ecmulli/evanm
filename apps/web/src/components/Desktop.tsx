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
import { useIsMobile } from '@/hooks/useIsMobile';
import { useDesktopIcons, useTextContent } from '@/context/ContentContext';
import { WindowState } from '@/types/window';

const KNOWN_FOLDERS = ['thoughts', 'projects'];

function contentIdToPath(contentId: string): string {
  for (const folder of KNOWN_FOLDERS) {
    if (contentId.startsWith(`${folder}-`)) {
      const slug = contentId.slice(folder.length + 1);
      return `/${folder}/${slug}`;
    }
  }
  return `/${contentId}`;
}

interface DesktopProps {
  initialContentId?: string;
}

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

function getWindowDimensions(appType: string): { width: number | string; height: number | string } {
  switch (appType) {
    case 'simpletext':
      return { width: '80%', height: '80%' };
    case 'stickies':
      return { width: 320, height: 450 };
    case 'folder':
      return { width: '60%', height: '60%' };
    default:
      return { width: '80%', height: '80%' };
  }
}

export default function Desktop({ initialContentId }: DesktopProps) {
  const { visibleWindows, closeWindow, openWindow, updateWindowPosition } = useWindow();
  const { settings } = useView();
  const isMobile = useIsMobile();
  const desktopIcons = useDesktopIcons();
  const initialContent = useTextContent(initialContentId || 'about-me');

  // Open initial content window centered on page load
  useEffect(() => {
    if (visibleWindows.length === 0) {
      const contentId = initialContentId || 'about-me';
      const title = initialContent?.title || 'About Me.txt';

      openWindow({
        appType: 'simpletext',
        title,
        contentId,
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // URL sync: update browser URL to match the current window's content
  useEffect(() => {
    const current = visibleWindows[0];
    if (current?.appType === 'simpletext' && current.contentId) {
      const path = contentIdToPath(current.contentId);
      if (window.location.pathname !== path) {
        window.history.replaceState(null, '', path);
      }
    } else if (current?.appType === 'folder') {
      // Folder open — keep URL as-is (or set to /)
    } else if (window.location.pathname !== '/') {
      window.history.replaceState(null, '', '/');
    }
  }, [visibleWindows]);

  return (
    <div className="desktop-environment">
      {/* Menu Bar */}
      <MenuBar />

      {/* Desktop Area (below menu bar) with pixel art background */}
      <div 
        className="pixel-desktop relative w-full overflow-hidden"
        style={{ 
          height: isMobile ? 'calc(100vh - 44px)' : 'calc(100vh - 32px)',
          marginTop: isMobile ? '44px' : '32px',
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

        {/* Desktop Icons - bottom dock on mobile, top-right on desktop */}
        <div className={
          isMobile 
            ? "absolute bottom-2 left-0 right-0 flex justify-center gap-2 z-10"
            : "absolute top-4 right-4 flex flex-col gap-1 z-10"
        }>
          {desktopIcons.map((icon) => (
            <DesktopIcon key={icon.id} config={icon} />
          ))}
        </div>

        {/* Open Windows */}
        {visibleWindows.map((win) => {
          const dimensions = getWindowDimensions(win.appType);
          return (
            <WindowFrame
              key={win.id}
              id={win.id}
              title={win.title}
              position={win.position}
              zIndex={win.zIndex}
              width={dimensions.width}
              height={dimensions.height}
              onClose={() => closeWindow(win.id)}
              onPositionChange={(pos) => updateWindowPosition(win.id, pos)}
            >
              <WindowContent window={win} />
            </WindowFrame>
          );
        })}
      </div>
    </div>
  );
}
