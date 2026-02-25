'use client';

import type { TaskPriority } from '@/server/dashboard/types';
import { PRIORITY_CONFIG } from '@/server/dashboard/types';

export function PriorityIndicator({ priority }: { priority: TaskPriority | null }) {
  if (!priority) return null;
  const config = PRIORITY_CONFIG[priority];
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ backgroundColor: config.color }}
      title={config.label}
    />
  );
}
