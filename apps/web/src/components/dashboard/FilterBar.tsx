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
  taskCount,
}: FilterBarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3 pb-4 border-b border-gray-200">
      {/* View toggle */}
      <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
        {VIEW_BUTTONS.map(({ mode, icon: Icon, label }) => (
          <button
            key={mode}
            onClick={() => onViewChange(mode)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              viewMode === mode
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      {/* Domain filter pills */}
      <div className="flex items-center gap-1.5">
        {DOMAIN_FILTERS.map(({ value, label }) => {
          const isActive = domainFilter === value;
          const config = value ? DOMAIN_CONFIG[value] : null;
          return (
            <button
              key={label}
              onClick={() => onDomainChange(value)}
              className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors border ${
                isActive
                  ? 'border-current'
                  : 'border-transparent hover:bg-gray-100'
              }`}
              style={
                isActive && config
                  ? { backgroundColor: config.bgColor, color: config.color, borderColor: config.color }
                  : isActive
                    ? { backgroundColor: '#F3F4F6', color: '#374151', borderColor: '#9CA3AF' }
                    : undefined
              }
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Right section: completed toggle + refresh + count */}
      <div className="flex items-center gap-3 sm:ml-auto">
        <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer">
          <input
            type="checkbox"
            checked={showCompleted}
            onChange={e => onShowCompletedChange(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
          />
          Done
        </label>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          title="Refresh"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>

        <span className="text-xs text-gray-400">
          {taskCount} task{taskCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
