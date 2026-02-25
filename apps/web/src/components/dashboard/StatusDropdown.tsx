'use client';

import { useState, useRef, useEffect } from 'react';
import type { TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_STATUSES, STATUS_MAP, STATUS_CONFIG } from '@/server/dashboard/types';

interface StatusDropdownProps {
  domain: TaskDomain;
  currentRawStatus: string;
  onStatusChange: (rawStatus: string) => void;
  disabled?: boolean;
}

export function StatusDropdown({ domain, currentRawStatus, onStatusChange, disabled }: StatusDropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const statuses = DOMAIN_STATUSES[domain];
  const normalizedCurrent = STATUS_MAP[domain]?.[currentRawStatus] || 'todo';
  const currentConfig = STATUS_CONFIG[normalizedCurrent];

  return (
    <div ref={ref} className="relative inline-block">
      <button
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium cursor-pointer hover:opacity-80 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed ${
          normalizedCurrent === 'cancelled' ? 'line-through' : ''
        }`}
        style={{ backgroundColor: currentConfig.bgColor, color: currentConfig.color }}
      >
        {currentRawStatus}
        <svg className="ml-1 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 mt-1 py-1 bg-white rounded-lg shadow-lg border border-gray-200 min-w-[140px] left-0">
          {statuses.map(rawStatus => {
            const normalized = STATUS_MAP[domain]?.[rawStatus] || 'todo';
            const config = STATUS_CONFIG[normalized];
            const isActive = rawStatus === currentRawStatus;
            return (
              <button
                key={rawStatus}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 flex items-center gap-2 ${
                  isActive ? 'font-semibold' : ''
                }`}
                onClick={() => {
                  if (rawStatus !== currentRawStatus) {
                    onStatusChange(rawStatus);
                  }
                  setOpen(false);
                }}
              >
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: config.color }}
                />
                {rawStatus}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
