'use client';

import { isAfter, isSameDay, parseISO } from 'date-fns';
import type { UnifiedTask } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';
import { StatusDropdown } from './StatusDropdown';
import { CompleteCheckbox } from './CompleteCheckbox';

interface TaskCardProps {
  task: UnifiedTask;
  onStatusChange: (taskId: string, rawStatus: string) => void;
  compact?: boolean;
  disabled?: boolean;
  selected?: boolean;
  onSelect?: (task: UnifiedTask) => void;
}

function DueDateLabel({ dueDate }: { dueDate: string | null }) {
  if (!dueDate) return null;

  const date = parseISO(dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const isOverdue = isAfter(today, date) && !isSameDay(today, date);
  const isDueToday = isSameDay(today, date);

  const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  return (
    <span
      className={`text-xs whitespace-nowrap font-medium ${
        isOverdue
          ? 'text-[#B34438]'
          : isDueToday
            ? 'text-[#B45309]'
            : 'text-[#6B6560]'
      }`}
    >
      {formatted}
      {isOverdue && <span className="ml-1">overdue</span>}
      {isDueToday && <span className="ml-1">today</span>}
    </span>
  );
}

export function TaskCard({ task, onStatusChange, compact, disabled, selected, onSelect }: TaskCardProps) {
  const isCompleted =
    task.status === 'done' || task.status === 'cancelled' || task.status === 'skipped';
  const domainConfig = DOMAIN_CONFIG[task.domain];

  function handleCardClick(e: React.MouseEvent) {
    const target = e.target as HTMLElement;
    if (target.closest('button, select, [role="listbox"], a')) return;
    onSelect?.(task);
  }

  return (
    <div
      onClick={handleCardClick}
      className={`rounded-2xl border px-4 py-3.5 hover:border-[#C8C2BC] hover:shadow-sm transition-all ${
        isCompleted ? 'opacity-50' : ''
      } ${selected ? 'border-[#C8C2BC] shadow-sm' : 'border-[#E5E0DB]'} ${onSelect ? 'cursor-pointer' : ''}`}
      style={{
        borderLeft: `3px solid ${domainConfig.color}`,
        backgroundColor: selected ? `${domainConfig.color}08` : 'white',
        boxShadow: selected ? `0 0 0 2px ${domainConfig.color}40` : undefined,
      }}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <div className="mt-0.5 flex-shrink-0">
          <CompleteCheckbox task={task} onStatusChange={onStatusChange} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Tags row */}
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
            <StatusDropdown
              currentRawStatus={task.rawStatus}
              onStatusChange={(rawStatus) =>
                onStatusChange(task.id, rawStatus)
              }
              disabled={disabled}
            />
            {compact && <DueDateLabel dueDate={task.dueDate} />}
          </div>

          {/* Title */}
          <a
            href={task.notionUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-[15px] font-medium leading-snug text-[#1A1714] hover:text-[#A05040] transition-colors block ${
              compact ? 'line-clamp-2' : ''
            } ${isCompleted ? 'line-through text-[#B5AFA9]' : ''}`}
            title={task.title}
          >
            {task.title}
          </a>

          {/* Metadata */}
          {!compact && (
            <div className="flex items-center gap-2.5 mt-1.5 flex-wrap">
              <DueDateLabel dueDate={task.dueDate} />
              {task.startTime && (
                <span className="text-xs text-[#6B6560]">{task.startTime}</span>
              )}
              {task.durationHours != null && (
                <span className="text-xs text-[#B5AFA9]">
                  {task.durationHours}h
                </span>
              )}
              {task.metadata.category && (
                <span className="text-xs text-[#6B6560] bg-[#F7F6F4] border border-[#E5E0DB] px-2 py-0.5 rounded-full">
                  {task.metadata.category}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
