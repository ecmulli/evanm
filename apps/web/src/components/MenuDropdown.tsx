'use client';

import React, { useRef, useEffect } from 'react';

interface MenuItem {
  label: string;
  action?: () => void;
  shortcut?: string;
  disabled?: boolean;
  separator?: boolean;
  checked?: boolean;
}

interface MenuDropdownProps {
  label: string;
  items: MenuItem[];
  bold?: boolean;
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  isAnyMenuOpen: boolean;
}

export default function MenuDropdown({ 
  label, 
  items, 
  bold, 
  isOpen, 
  onOpen, 
  onClose,
  isAnyMenuOpen 
}: MenuDropdownProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Close menu on escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  const handleItemClick = (item: MenuItem) => {
    if (item.disabled) return;
    if (item.action) {
      item.action();
    }
    onClose();
  };

  const handleMouseEnter = () => {
    // If any menu is already open, switch to this one on hover
    if (isAnyMenuOpen && !isOpen) {
      onOpen();
    }
  };

  const handleClick = () => {
    if (isOpen) {
      onClose();
    } else {
      onOpen();
    }
  };

  return (
    <div ref={menuRef} className="relative">
      <button
        className={`retro-menu-item ${bold ? 'font-bold' : ''} ${isOpen ? 'bg-[#3A3530] text-[#F5F0EB]' : ''}`}
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
      >
        {label}
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-0 min-w-[180px] bg-[#F5F0EB] border-2 border-[#3A3530] shadow-[2px_2px_0_#3A3530] z-[10000]">
          {items.map((item, index) => (
            item.separator ? (
              <div key={index} className="border-t border-[#3A3530] my-1" />
            ) : (
              <button
                key={index}
                className={`w-full text-left px-3 py-1 text-xs flex items-center justify-between ${
                  item.disabled 
                    ? 'text-gray-400 cursor-not-allowed' 
                    : 'hover:bg-[#3A3530] hover:text-[#F5F0EB]'
                }`}
                onClick={() => handleItemClick(item)}
                disabled={item.disabled}
              >
                <span className="flex items-center gap-2">
                  {item.checked !== undefined && (
                    <span className="w-3">{item.checked ? '✓' : ''}</span>
                  )}
                  {item.label}
                </span>
                {item.shortcut && (
                  <span className="text-[10px] opacity-60">{item.shortcut}</span>
                )}
              </button>
            )
          ))}
        </div>
      )}
    </div>
  );
}
