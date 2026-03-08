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
    <div className="flex items-center gap-2 flex-wrap">
      {/* View toggle */}
      <div className="flex items-center bg-white rounded-xl p-0.5 border border-[#E5E0DB] shadow-sm">
        {VIEW_BUTTONS.map(({ mode, icon: Icon, label }) => (
          <button
            key={mode}
            onClick={() => onViewChange(mode)}
            aria-label={label}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg transition-all ${
              viewMode === mode
                ? 'bg-[#1C2B4A] text-white shadow-sm'
                : 'text-[#6B6560] hover:text-[#1A1714] hover:bg-[#F7F6F4]'
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
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all border ${
                isActive
                  ? 'border-current shadow-sm'
                  : 'border-transparent text-[#6B6560] hover:bg-white hover:border-[#E5E0DB] hover:text-[#1A1714]'
              }`}
              style={
                isActive && config
                  ? {
                      backgroundColor: config.bgColor,
                      color: config.color,
                      borderColor: config.color + '40',
                    }
                  : isActive
                    ? { backgroundColor: '#F7F6F4', color: '#1A1714', borderColor: '#C8C2BC' }
                    : {}
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
            onChange={(e) => onShowCompletedChange(e.target.checked)}
            className="rounded border-[#C8C2BC] text-[#4A6B3A] focus:ring-[#4A6B3A] w-3.5 h-3.5"
          />
          <span className="hidden sm:inline">Done</span>
        </label>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-1.5 text-[#B5AFA9] hover:text-[#1A1714] hover:bg-white rounded-lg border border-transparent hover:border-[#E5E0DB] transition-all disabled:opacity-40"
          title="Refresh"
          aria-label="Refresh tasks"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
