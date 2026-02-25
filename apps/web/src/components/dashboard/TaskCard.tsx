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
        isOverdue ? 'text-red-600 font-medium' : isDueToday ? 'text-amber-600 font-medium' : 'text-gray-500'
      }`}
    >
      {formatted}
      {isOverdue && <span className="ml-1 text-red-500">overdue</span>}
      {isDueToday && <span className="ml-1">today</span>}
    </span>
  );
}

export function TaskCard({ task, onStatusChange, compact, disabled }: TaskCardProps) {
  const isCompleted = task.status === 'done' || task.status === 'cancelled' || task.status === 'skipped';

  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 p-3 hover:shadow-sm transition-shadow ${
        isCompleted ? 'opacity-60' : ''
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
          </div>
          <a
            href={task.notionUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-sm font-medium text-gray-900 hover:text-blue-600 hover:underline block truncate ${
              isCompleted ? 'line-through' : ''
            }`}
            title={task.title}
          >
            {task.title}
          </a>
          {!compact && (
            <div className="flex items-center gap-2 mt-1">
              <DueDateLabel dueDate={task.dueDate} />
              {task.metadata.estimatedHours && (
                <span className="text-xs text-gray-400">{task.metadata.estimatedHours}h</span>
              )}
              {task.metadata.labels && task.metadata.labels.length > 0 && (
                <div className="flex gap-1">
                  {task.metadata.labels.map(label => (
                    <span key={label} className="text-xs text-gray-400 bg-gray-100 px-1 rounded">
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
