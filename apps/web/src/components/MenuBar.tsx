'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';

export default function MenuBar() {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    // Update time immediately
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
    
    // Update every minute
    const interval = setInterval(updateTime, 60000);
    
    return () => clearInterval(interval);
  }, []);

  return (
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
        <span className="retro-menu-item font-bold">File</span>
        
        {/* Edit Menu */}
        <span className="retro-menu-item">Edit</span>
        
        {/* View Menu */}
        <span className="retro-menu-item">View</span>
        
        {/* Special Menu */}
        <span className="retro-menu-item">Special</span>
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
  );
}
