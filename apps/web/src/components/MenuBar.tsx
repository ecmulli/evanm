'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import MenuDropdown from './MenuDropdown';
import { useWindowContext } from '@/context/WindowContext';
import { useView } from '@/context/ViewContext';

export default function MenuBar() {
  const [time, setTime] = useState<string>('');
  const [showAboutMac, setShowAboutMac] = useState(false);
  const [showSleep, setShowSleep] = useState(false);
  const [showRestart, setShowRestart] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState(false);

  const { 
    windows, 
    openWindow, 
    closeTopWindow, 
    closeAllWindows,
    arrangeWindows 
  } = useWindowContext();
  
  const { 
    settings, 
    toggleStars, 
    toggleGrid, 
    toggleMountains, 
    toggleSun,
    resetView 
  } = useView();

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 || 12;
      const displayMinutes = minutes.toString().padStart(2, '0');
      setTime(`${displayHours}:${displayMinutes} ${ampm}`);
    };

    updateTime();
    const interval = setInterval(updateTime, 60000);
    return () => clearInterval(interval);
  }, []);

  // Handle sleep effect
  useEffect(() => {
    if (showSleep) {
      const timer = setTimeout(() => setShowSleep(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [showSleep]);

  // Handle restart effect
  useEffect(() => {
    if (showRestart) {
      const timer = setTimeout(() => {
        window.location.reload();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [showRestart]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopyFeedback(true);
    setTimeout(() => setCopyFeedback(false), 2000);
  };

  const handleOpenAboutMe = () => {
    openWindow({
      appType: 'simpletext',
      title: 'About Me.md',
      contentId: 'about-me',
    });
  };

  const handleNewNote = () => {
    openWindow({
      appType: 'stickies',
      title: 'Guestbook',
    });
  };

  const fileMenuItems = [
    { label: 'New Note', action: handleNewNote, shortcut: '⌘N' },
    { label: 'Open About Me', action: handleOpenAboutMe, shortcut: '⌘O' },
    { separator: true, label: '' },
    { label: 'Close Window', action: closeTopWindow, shortcut: '⌘W', disabled: windows.length === 0 },
    { label: 'Close All', action: closeAllWindows, disabled: windows.length === 0 },
  ];

  const editMenuItems = [
    { label: copyFeedback ? 'Copied!' : 'Copy Link', action: handleCopyLink, shortcut: '⌘C' },
    { separator: true, label: '' },
    { label: 'Preferences...', action: () => setShowAboutMac(true), disabled: true },
  ];

  const viewMenuItems = [
    { label: 'Show Stars', action: toggleStars, checked: settings.showStars },
    { label: 'Show Grid', action: toggleGrid, checked: settings.showGrid },
    { label: 'Show Mountains', action: toggleMountains, checked: settings.showMountains },
    { label: 'Show Sun', action: toggleSun, checked: settings.showSun },
    { separator: true, label: '' },
    { label: 'Reset View', action: resetView },
    { separator: true, label: '' },
    { label: 'Cascade Windows', action: () => arrangeWindows('cascade'), disabled: windows.length < 2 },
    { label: 'Tile Windows', action: () => arrangeWindows('tile'), disabled: windows.length < 2 },
  ];

  const specialMenuItems = [
    { label: 'About This Mac', action: () => setShowAboutMac(true) },
    { separator: true, label: '' },
    { label: 'Sleep', action: () => setShowSleep(true) },
    { label: 'Restart...', action: () => setShowRestart(true) },
    { separator: true, label: '' },
    { label: 'Empty Trash', action: () => alert('🗑️ The Trash is already empty!') },
    { separator: true, label: '' },
    { label: 'View Source', action: () => window.open('https://github.com/ecmulli/evanm', '_blank') },
    { label: 'Contact', action: () => window.open('mailto:hello@evanm.xyz', '_blank') },
  ];

  return (
    <>
      <div className="retro-menubar fixed top-0 left-0 right-0 z-[9999]">
        {/* Left side - Apple logo and menus */}
        <div className="flex items-center">
          {/* Brand Logo */}
          <div className="retro-menu-item flex items-center">
            <Image 
              src="/full_logo.svg" 
              alt="Brand Logo" 
              width={60} 
              height={16}
              className="h-4 w-auto"
              style={{ imageRendering: 'auto' }}
            />
          </div>

          {/* File Menu */}
          <MenuDropdown label="File" items={fileMenuItems} bold />
          
          {/* Edit Menu */}
          <MenuDropdown label="Edit" items={editMenuItems} />
          
          {/* View Menu */}
          <MenuDropdown label="View" items={viewMenuItems} />
          
          {/* Special Menu */}
          <MenuDropdown label="Special" items={specialMenuItems} />
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right side - Clock */}
        <div className="flex items-center">
          <span className="px-4 text-xs font-bold">
            {time}
          </span>
        </div>
      </div>

      {/* About This Mac Modal */}
      {showAboutMac && (
        <div 
          className="fixed inset-0 bg-black/50 z-[10001] flex items-center justify-center"
          onClick={() => setShowAboutMac(false)}
        >
          <div 
            className="bg-[#F5F0EB] border-2 border-[#3A3530] shadow-[4px_4px_0_#3A3530] p-6 max-w-sm"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center gap-4 mb-4">
              <Image 
                src="/pfp.svg" 
                alt="Logo" 
                width={64} 
                height={64}
                className="border-2 border-[#3A3530]"
              />
              <div>
                <h2 className="text-lg font-bold">evanm.xyz</h2>
                <p className="text-xs text-gray-600">Version 1.0.0</p>
              </div>
            </div>
            
            <div className="text-xs space-y-2 border-t border-[#3A3530] pt-4">
              <p><strong>Processor:</strong> Brain v29.0</p>
              <p><strong>Memory:</strong> Too many browser tabs</p>
              <p><strong>Storage:</strong> Unlimited ideas</p>
              <p><strong>Display:</strong> Retro-tinted glasses</p>
              <p><strong>Built with:</strong> Next.js, Tailwind, & nostalgia</p>
            </div>
            
            <div className="mt-4 pt-4 border-t border-[#3A3530] text-center">
              <p className="text-[10px] text-gray-500">© 2026 Evan Mullins</p>
              <button 
                className="mt-2 px-4 py-1 bg-[#3A3530] text-[#F5F0EB] text-xs hover:bg-[#A0584A]"
                onClick={() => setShowAboutMac(false)}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sleep Overlay */}
      {showSleep && (
        <div 
          className="fixed inset-0 bg-black z-[10002] flex items-center justify-center cursor-pointer animate-pulse"
          onClick={() => setShowSleep(false)}
        >
          <p className="text-white text-xs opacity-50">Click anywhere to wake...</p>
        </div>
      )}

      {/* Restart Overlay */}
      {showRestart && (
        <div className="fixed inset-0 bg-[#3A3530] z-[10002] flex flex-col items-center justify-center">
          <Image 
            src="/pfp.svg" 
            alt="Logo" 
            width={80} 
            height={80}
            className="mb-4 animate-pulse"
          />
          <p className="text-[#F5F0EB] text-sm">Restarting...</p>
          <div className="mt-4 w-48 h-2 bg-[#F5F0EB]/20 rounded overflow-hidden">
            <div className="h-full bg-[#A0584A] animate-[loading_1.5s_ease-in-out]" 
                 style={{ animation: 'loading 1.5s ease-in-out forwards' }} />
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes loading {
          from { width: 0%; }
          to { width: 100%; }
        }
      `}</style>
    </>
  );
}
