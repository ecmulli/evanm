'use client';

import React from 'react';
import PixelIcon from './PixelIcons';
import { useOpenApp } from '@/hooks/useWindow';
import { DesktopIconConfig } from '@/types/window';

interface DesktopIconProps {
  config: DesktopIconConfig;
}

export default function DesktopIcon({ config }: DesktopIconProps) {
  const { openSimpleText, openStickies, openFolder } = useOpenApp();

  const handleDoubleClick = () => {
    switch (config.appType) {
      case 'simpletext':
        openSimpleText(config.label, config.contentId || config.id);
        break;
      case 'stickies':
        openStickies();
        break;
      case 'folder':
        openFolder(config.label, config.contentId || config.id);
        break;
    }
  };

  return (
    <div
      className="desktop-icon"
      onDoubleClick={handleDoubleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          handleDoubleClick();
        }
      }}
    >
      <div className="desktop-icon-image">
        <PixelIcon type={config.iconType} />
      </div>
      <span className="desktop-icon-label">
        {config.label}
      </span>
    </div>
  );
}
