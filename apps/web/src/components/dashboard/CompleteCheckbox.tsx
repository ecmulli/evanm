'use client';

import { useState } from 'react';
import { Check } from 'lucide-react';
import type { UnifiedTask, TaskDomain } from '@/server/dashboard/types';
import { denormalizeStatus } from '@/server/dashboard/types';

interface CompleteCheckboxProps {
  task: UnifiedTask;
  onStatusChange: (taskId: string, rawStatus: string, domain: TaskDomain) => void;
}

export function CompleteCheckbox({ task, onStatusChange }: CompleteCheckboxProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const isCompleted = task.status === 'done' || task.status === 'cancelled' || task.status === 'skipped';

  function handleToggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();

    if (isAnimating) return;

    const targetStatus = isCompleted ? 'todo' : 'done';
    const rawStatus = denormalizeStatus(task.domain, targetStatus);
    if (!rawStatus) return;

    setIsAnimating(true);
    onStatusChange(task.id, rawStatus, task.domain);

    // Reset animation after a brief delay
    setTimeout(() => setIsAnimating(false), 600);
  }

  return (
    <button
      onClick={handleToggle}
      className={`
        flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center
        transition-all duration-200 ease-out
        ${isCompleted
          ? 'bg-[#5B6B3B] border-[#5B6B3B] text-white'
          : 'border-[#D4CFC9] hover:border-[#5B6B3B] hover:bg-[#EFF2E8]'
        }
        ${isAnimating ? 'scale-110' : 'scale-100'}
      `}
      title={isCompleted ? 'Mark incomplete' : 'Mark complete'}
      aria-label={isCompleted ? 'Mark incomplete' : 'Mark complete'}
    >
      {isCompleted && <Check className="w-3 h-3" strokeWidth={3} />}
    </button>
  );
}
