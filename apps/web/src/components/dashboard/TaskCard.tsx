'use client';

import { isAfter, isSameDay, parseISO } from 'date-fns';
import type { UnifiedTask } from '@/server/dashboard/types';
import { DomainBadge } from './DomainBadge';
import { PriorityIndicator } from './PriorityIndicator';
import { StatusDropdown } from './StatusDropdown';

interface TaskCardProps {
  task: UnifiedTask;
  onStatusChange: (taskId: string, rawStatus: string, domain: UnifiedTask['domain']) => void;
  compact?: boolean;
  disabled?: boolean;
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
      className={`text-xs whitespace-nowrap ${
        isOverdue ? 'text-[#A0584A] font-medium' : isDueToday ? 'text-[#CA8A04] font-medium' : 'text-[#6B6560]'
      }`}
    >
      {formatted}
      {isOverdue && <span className="ml-1 text-[#A0584A]">overdue</span>}
      {isDueToday && <span className="ml-1">today</span>}
    </span>
  );
}

export function TaskCard({ task, onStatusChange, compact, disabled }: TaskCardProps) {
  const isCompleted = task.status === 'done' || task.status === 'cancelled' || task.status === 'skipped';

  return (
    <div
      className={`bg-[#FDFCFA] rounded-lg border border-[#E8E4E0] p-2.5 sm:p-3 hover:shadow-md hover:border-[#BEA09A] transition-all ${
        isCompleted ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-start gap-2">
        <PriorityIndicator priority={task.priority} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1 flex-wrap">
            <DomainBadge domain={task.domain} />
            <StatusDropdown
              domain={task.domain}
              currentRawStatus={task.rawStatus}
              onStatusChange={rawStatus => onStatusChange(task.id, rawStatus, task.domain)}
              disabled={disabled}
            />
            {compact && <DueDateLabel dueDate={task.dueDate} />}
          </div>
          <a
            href={task.notionUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-sm font-medium text-[#2A2520] hover:text-[#A0584A] hover:underline block ${
              compact ? 'line-clamp-2' : ''
            } ${isCompleted ? 'line-through' : ''}`}
            title={task.title}
          >
            {task.title}
          </a>
          {!compact && (
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <DueDateLabel dueDate={task.dueDate} />
              {task.metadata.estimatedHours && (
                <span className="text-xs text-[#BEA09A]">{task.metadata.estimatedHours}h</span>
              )}
              {task.metadata.labels && task.metadata.labels.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {task.metadata.labels.map(label => (
                    <span key={label} className="text-xs text-[#6B6560] bg-[#F5F2EE] px-1.5 py-0.5 rounded">
                      {label}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
