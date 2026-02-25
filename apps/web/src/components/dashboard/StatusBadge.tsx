'use client';

import type { TaskStatus } from '@/server/dashboard/types';
import { STATUS_CONFIG } from '@/server/dashboard/types';

export function StatusBadge({ status }: { status: TaskStatus }) {
  const config = STATUS_CONFIG[status];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${
        status === 'cancelled' ? 'line-through' : ''
      }`}
      style={{ backgroundColor: config.bgColor, color: config.color }}
    >
      {config.label}
    </span>
  );
}
