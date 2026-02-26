'use client';

import { List, LayoutGrid, Calendar, RefreshCw } from 'lucide-react';
import type { TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';

export type ViewMode = 'list' | 'board' | 'calendar';

interface FilterBarProps {
  viewMode: ViewMode;
  onViewChange: (mode: ViewMode) => void;
  domainFilter: TaskDomain | null;
  onDomainChange: (domain: TaskDomain | null) => void;
  showCompleted: boolean;
  onShowCompletedChange: (show: boolean) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  taskCount: number;
}

const VIEW_BUTTONS: { mode: ViewMode; icon: typeof List; label: string }[] = [
  { mode: 'list', icon: List, label: 'List' },
  { mode: 'board', icon: LayoutGrid, label: 'Board' },
  { mode: 'calendar', icon: Calendar, label: 'Calendar' },
];

const DOMAIN_FILTERS: { value: TaskDomain | null; label: string }[] = [
  { value: null, label: 'All' },
  { value: 'work', label: 'Work' },
  { value: 'career', label: 'Career' },
  { value: 'personal', label: 'Personal' },
];

export function FilterBar({
  viewMode,
  onViewChange,
  domainFilter,
  onDomainChange,
  showCompleted,
  onShowCompletedChange,
  onRefresh,
  isRefreshing,
}: FilterBarProps) {
  return (
    <div className="space-y-2 sm:space-y-0 sm:flex sm:items-center sm:gap-3 pb-3 sm:pb-4 border-b border-[#E8E4E0]">
      {/* Top row on mobile: view toggle + actions */}
      <div className="flex items-center gap-2">
        {/* View toggle */}
        <div className="flex items-center bg-white rounded-lg p-0.5 border border-[#E8E4E0] shadow-sm">
          {VIEW_BUTTONS.map(({ mode, icon: Icon, label }) => (
            <button
              key={mode}
              onClick={() => onViewChange(mode)}
              className={`flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                viewMode === mode
                  ? 'bg-[#152A54] text-white shadow-sm'
                  : 'text-[#6B6560] hover:text-[#2A2520] hover:bg-[#F5F2EE]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* Domain filter pills */}
        <div className="flex items-center gap-1">
          {DOMAIN_FILTERS.map(({ value, label }) => {
            const isActive = domainFilter === value;
            const config = value ? DOMAIN_CONFIG[value] : null;
            return (
              <button
                key={label}
                onClick={() => onDomainChange(value)}
                className={`px-2 sm:px-3 py-1 text-xs font-medium rounded-full transition-all border ${
                  isActive
                    ? 'border-current shadow-sm'
                    : 'border-transparent hover:bg-white hover:border-[#E8E4E0]'
                }`}
                style={
                  isActive && config
                    ? { backgroundColor: config.bgColor, color: config.color, borderColor: config.color }
                    : isActive
                      ? { backgroundColor: '#FDFCFA', color: '#2A2520', borderColor: '#6B6560' }
                      : { color: '#6B6560' }
                }
              >
                {label}
              </button>
            );
          })}
        </div>

        {/* Right section */}
        <div className="flex items-center gap-2 ml-auto">
          <label className="flex items-center gap-1.5 text-xs text-[#6B6560] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showCompleted}
              onChange={e => onShowCompletedChange(e.target.checked)}
              className="rounded border-[#BEA09A] text-[#A0584A] focus:ring-[#A0584A] w-3.5 h-3.5"
            />
            <span className="hidden sm:inline">Done</span>
          </label>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1 sm:p-1.5 text-[#6B6560] hover:text-[#A0584A] transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  );
}
