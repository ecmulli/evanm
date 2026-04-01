'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import PixelIcon from './PixelIcons';
import { useOpenApp } from '@/hooks/useWindow';
import { DesktopIconConfig } from '@/types/window';

interface DesktopIconProps {
  config: DesktopIconConfig;
}

export default function DesktopIcon({ config }: DesktopIconProps) {
  const { openSimpleText, openStickies, openFolder } = useOpenApp();
  const router = useRouter();

  const handleClick = () => {
    if (config.href) {
      if (config.href.startsWith('http')) {
        window.open(config.href, '_blank');
      } else {
        router.push(config.href);
      }
      return;
    }

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
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          handleClick();
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
