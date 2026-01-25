'use client';

import React from 'react';

// Brand colors
const BRAND = {
  terracotta: '#A0584A',
  navy: '#152A54',
  olive: '#6B6B41',
  rose: '#BEA09A',
  moss: '#5B6B3B',
  silver: '#ACACAC',
  cream: '#FDFCFA',
  warmWhite: '#F5EFE6',
};

// Pixel art style icons using CSS/SVG
export function PixelFileIcon({ color = BRAND.navy }: { color?: string }) {
  return (
    <svg width="48" height="48" viewBox="0 0 16 16" style={{ imageRendering: 'pixelated' }}>
      {/* Document body */}
      <rect x="2" y="1" width="10" height="14" fill={BRAND.cream} />
      <rect x="2" y="1" width="10" height="14" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Folded corner */}
      <polygon points="9,1 12,1 12,4 9,4" fill={BRAND.rose} />
      <polyline points="9,1 9,4 12,4" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Text lines */}
      <rect x="4" y="6" width="6" height="1" fill={color} />
      <rect x="4" y="8" width="5" height="1" fill={color} />
      <rect x="4" y="10" width="6" height="1" fill={color} />
      <rect x="4" y="12" width="3" height="1" fill={color} />
    </svg>
  );
}

export function PixelFolderIcon({ color = BRAND.olive }: { color?: string }) {
  return (
    <svg width="48" height="48" viewBox="0 0 16 16" style={{ imageRendering: 'pixelated' }}>
      {/* Folder back */}
      <rect x="1" y="4" width="14" height="11" fill={color} />
      <rect x="1" y="4" width="14" height="11" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Folder tab */}
      <polygon points="1,4 1,2 6,2 7,4" fill={color} />
      <polyline points="1,4 1,2 6,2 7,4" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Folder front (lighter) */}
      <rect x="1" y="6" width="14" height="9" fill={BRAND.warmWhite} />
      <rect x="1" y="6" width="14" height="9" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Highlight */}
      <rect x="2" y="7" width="12" height="1" fill="rgba(255,255,255,0.5)" />
    </svg>
  );
}

export function PixelStickyIcon({ color = BRAND.terracotta }: { color?: string }) {
  return (
    <svg width="48" height="48" viewBox="0 0 16 16" style={{ imageRendering: 'pixelated' }}>
      {/* Sticky note body */}
      <rect x="1" y="2" width="14" height="12" fill={BRAND.warmWhite} />
      <rect x="1" y="2" width="14" height="12" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Folded corner */}
      <polygon points="11,14 15,14 15,10" fill={BRAND.rose} />
      <polygon points="11,14 15,10 11,10" fill={BRAND.silver} />
      <polyline points="11,14 11,10 15,10" fill="none" stroke="#3A3530" strokeWidth="1" />
      
      {/* Heart decoration */}
      <path 
        d="M8,6 C8,5 7,4 6,4 C5,4 4,5 4,6 C4,8 8,11 8,11 C8,11 12,8 12,6 C12,5 11,4 10,4 C9,4 8,5 8,6" 
        fill={color}
        stroke="#3A3530"
        strokeWidth="0.5"
      />
    </svg>
  );
}

export function PixelAppleIcon() {
  // Using brand terracotta for the apple
  return (
    <svg width="14" height="14" viewBox="0 0 8 8" style={{ imageRendering: 'pixelated' }}>
      {/* Stem */}
      <rect x="4" y="0" width="1" height="2" fill={BRAND.moss} />
      {/* Apple body */}
      <rect x="2" y="2" width="4" height="1" fill={BRAND.terracotta} />
      <rect x="1" y="3" width="6" height="3" fill={BRAND.terracotta} />
      <rect x="2" y="6" width="4" height="1" fill={BRAND.terracotta} />
      {/* Highlight */}
      <rect x="2" y="3" width="1" height="1" fill={BRAND.rose} />
    </svg>
  );
}

// Brand logo icon (diagonal lines in circle)
export function BrandLogoIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" style={{ imageRendering: 'auto' }}>
      <circle cx="12" cy="12" r="10" fill="none" stroke={BRAND.terracotta} strokeWidth="1.5" />
      <line x1="6" y1="6" x2="18" y2="18" stroke={BRAND.terracotta} strokeWidth="1.5" />
      <line x1="8" y1="4" x2="20" y2="16" stroke={BRAND.terracotta} strokeWidth="1.5" />
      <line x1="4" y1="8" x2="16" y2="20" stroke={BRAND.terracotta} strokeWidth="1.5" />
      <line x1="10" y1="4" x2="20" y2="14" stroke={BRAND.terracotta} strokeWidth="1.5" />
      <line x1="4" y1="10" x2="14" y2="20" stroke={BRAND.terracotta} strokeWidth="1.5" />
    </svg>
  );
}

interface PixelIconProps {
  type: 'file' | 'folder' | 'app';
  color?: string;
}

export default function PixelIcon({ type, color }: PixelIconProps) {
  switch (type) {
    case 'file':
      return <PixelFileIcon color={color || BRAND.navy} />;
    case 'folder':
      return <PixelFolderIcon color={color || BRAND.olive} />;
    case 'app':
      return <PixelStickyIcon color={color || BRAND.terracotta} />;
    default:
      return <PixelFileIcon color={color} />;
  }
}
