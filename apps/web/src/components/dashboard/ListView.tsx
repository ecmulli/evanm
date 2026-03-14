'use client';

import { useState, useMemo } from 'react';
import { parseISO } from 'date-fns';
import { ExternalLink } from 'lucide-react';
import { useIsMobile } from '@/hooks/useIsMobile';
import type { UnifiedTask, TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';
import { TaskCard } from './TaskCard';
import { StatusDropdown } from './StatusDropdown';
import { CompleteCheckbox } from './CompleteCheckbox';

type SortKey = 'title' | 'status' | 'startTime' | 'durationHours' | 'dueDate';
type SortDir = 'asc' | 'desc';

interface ListViewProps {
  tasks: UnifiedTask[];
  onStatusChange: (taskId: string, rawStatus: string, domain: TaskDomain) => void;
  selectedTaskId?: string | null;
  onSelectTask?: (task: UnifiedTask) => void;
}

function compareTasks(a: UnifiedTask, b: UnifiedTask, key: SortKey, dir: SortDir): number {
  let cmp = 0;
  switch (key) {
    case 'title':
      cmp = a.title.localeCompare(b.title);
      break;
    case 'status':
      cmp = a.status.localeCompare(b.status);
      break;
    case 'startTime': {
      // Sort by time string — null sorts last
      const ta = a.startTime ?? '\xFF';
      const tb = b.startTime ?? '\xFF';
      cmp = ta.localeCompare(tb);
      break;
    }
    case 'durationHours': {
      const da = a.durationHours ?? Infinity;
      const db = b.durationHours ?? Infinity;
      cmp = da - db;
      break;
    }
    case 'dueDate': {
      const da = a.dueDate ? parseISO(a.dueDate).getTime() : Infinity;
      const db = b.dueDate ? parseISO(b.dueDate).getTime() : Infinity;
      cmp = da - db;
      break;
    }
  }
  return dir === 'desc' ? -cmp : cmp;
}

function DueDateCell({ dueDate }: { dueDate: string | null }) {
  if (!dueDate) return <span className="text-[#B5AFA9]">&mdash;</span>;
  const date = parseISO(dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const isOverdue = date < today;
  const isDueToday = date.toDateString() === today.toDateString();
  const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return (
    <span className={`text-xs font-medium ${isOverdue ? 'text-[#B34438]' : isDueToday ? 'text-[#B45309]' : 'text-[#6B6560]'}`}>
      {formatted}
      {isOverdue && <span className="ml-1">overdue</span>}
      {isDueToday && <span className="ml-1">today</span>}
    </span>
  );
}

function StartTimeCell({ startTime }: { startTime: string | null }) {
  if (!startTime) return <span className="text-[#B5AFA9]">&mdash;</span>;
  return <span className="text-xs font-medium text-[#6B6560]">{startTime}</span>;
}

function DurationCell({ hours }: { hours: number | null }) {
  if (hours == null) return <span className="text-[#B5AFA9]">&mdash;</span>;
  const label = hours === Math.floor(hours) ? `${hours}h` : `${hours}h`;
  return <span className="text-xs font-medium text-[#6B6560]">{label}</span>;
}

export function ListView({ tasks, onStatusChange, selectedTaskId, onSelectTask }: ListViewProps) {
  const isMobile = useIsMobile();
  const [sortKey, setSortKey] = useState<SortKey>('dueDate');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const sorted = useMemo(() => {
    return [...tasks].sort((a, b) => compareTasks(a, b, sortKey, sortDir));
  }, [tasks, sortKey, sortDir]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  function handleRowClick(task: UnifiedTask, e: React.MouseEvent) {
    const target = e.target as HTMLElement;
    if (target.closest('button, select, [role="listbox"], a')) return;
    onSelectTask?.(task);
  }

  function SortHeader({ label, sortKeyName }: { label: string; sortKeyName: SortKey }) {
    const active = sortKey === sortKeyName;
    return (
      <button
        onClick={() => handleSort(sortKeyName)}
        className={`text-xs font-medium uppercase tracking-wider text-left flex items-center gap-1 ${
          active ? 'text-[#1C2B4A]' : 'text-[#6B6560] hover:text-[#1A1714]'
        }`}
      >
        {label}
        {active && (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d={sortDir === 'asc' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'}
            />
          </svg>
        )}
      </button>
    );
  }

  // Mobile: stacked cards
  if (isMobile) {
    return (
      <div className="space-y-2">
        {sorted.map(task => (
          <TaskCard key={task.id} task={task} onStatusChange={onStatusChange} />
        ))}
        {sorted.length === 0 && (
          <p className="text-center text-[#BEA09A] py-8 text-sm">No tasks found</p>
        )}
      </div>
    );
  }

  // Desktop: table with domain-colored rows
  return (
    <div className="bg-white rounded-2xl border border-[#E5E0DB] overflow-hidden shadow-sm">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[#E5E0DB] bg-[#F7F6F4]">
            <th className="pl-4 pr-1 py-2.5 w-10"></th>
            <th className="px-3 py-2.5"><SortHeader label="Title" sortKeyName="title" /></th>
            <th className="px-3 py-2.5 w-32"><SortHeader label="Status" sortKeyName="status" /></th>
            <th className="px-3 py-2.5 w-20"><SortHeader label="Start" sortKeyName="startTime" /></th>
            <th className="px-3 py-2.5 w-16"><SortHeader label="Dur" sortKeyName="durationHours" /></th>
            <th className="px-3 py-2.5 w-28"><SortHeader label="Due" sortKeyName="dueDate" /></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(task => {
            const isCompleted = task.status === 'done' || task.status === 'cancelled' || task.status === 'skipped';
            const isSelected = selectedTaskId === task.id;
            const domainColor = DOMAIN_CONFIG[task.domain].color;
            const domainBgColor = DOMAIN_CONFIG[task.domain].bgColor;

            return (
              <tr
                key={task.id}
                onClick={(e) => handleRowClick(task, e)}
                className={`border-b border-[#F7F6F4]/60 transition-colors ${
                  isCompleted ? 'opacity-50' : ''
                } ${onSelectTask ? 'cursor-pointer' : ''}`}
                style={{
                  backgroundColor: isSelected ? `${domainColor}18` : domainBgColor,
                  borderLeft: `3px solid ${isSelected ? domainColor : `${domainColor}50`}`,
                }}
              >
                <td className="pl-4 pr-1 py-3">
                  <CompleteCheckbox task={task} onStatusChange={onStatusChange} />
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-sm font-medium text-[#1A1714] ${isCompleted ? 'line-through text-[#B5AFA9]' : ''}`}
                    >
                      {task.title}
                    </span>
                    <a
                      href={task.notionUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-shrink-0 text-[#B5AFA9] hover:text-[#A05040] transition-colors"
                      title="Open in Notion"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <StatusDropdown
                    domain={task.domain}
                    currentRawStatus={task.rawStatus}
                    onStatusChange={rawStatus => onStatusChange(task.id, rawStatus, task.domain)}
                  />
                </td>
                <td className="px-3 py-3"><StartTimeCell startTime={task.startTime} /></td>
                <td className="px-3 py-3"><DurationCell hours={task.durationHours} /></td>
                <td className="px-3 py-3 text-sm"><DueDateCell dueDate={task.dueDate} /></td>
              </tr>
            );
          })}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center text-[#B5AFA9] py-10 text-sm">No tasks found</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
