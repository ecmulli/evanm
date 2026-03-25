// ===== Domain Types =====

export type TaskDomain = 'work' | 'career' | 'personal';
export type TaskType = 'task' | 'quick_todo';
export type TaskStatus = 'todo' | 'in_progress' | 'done' | 'skipped' | 'cancelled';
export type TaskPriority = 'urgent' | 'high' | 'medium' | 'low' | 'none';

export interface UnifiedTask {
  id: string;
  title: string;
  notionUrl: string;
  type: TaskType;
  domain: TaskDomain;
  status: TaskStatus;
  rawStatus: string;
  priority: TaskPriority | null;
  dueDate: string | null; // ISO date string
  startTime: string | null; // e.g., "1:00 PM" — time portion of due date start
  durationHours: number | null; // decimal hours (e.g., 1.5)
  metadata: {
    category?: string;
    timeEstimate?: string;
  };
  createdAt: string;
  updatedAt: string;
}

// ===== Status Mapping (unified across all domains) =====

export const STATUS_MAP: Record<string, TaskStatus> = {
  'To Do': 'todo',
  'In Progress': 'in_progress',
  'Done': 'done',
  'Skipped': 'skipped',
  'Cancelled': 'cancelled',
};

export function denormalizeStatus(normalized: TaskStatus): string | null {
  const map: Record<TaskStatus, string> = {
    todo: 'To Do',
    in_progress: 'In Progress',
    done: 'Done',
    skipped: 'Skipped',
    cancelled: 'Cancelled',
  };
  return map[normalized] ?? null;
}

// Available raw status options (same for all domains)
export const RAW_STATUSES: string[] = ['To Do', 'In Progress', 'Done', 'Skipped', 'Cancelled'];

// ===== Priority Mapping (unified) =====

export const PRIORITY_MAP: Record<string, TaskPriority> = {
  'Urgent': 'urgent',
  'High': 'high',
  'Medium': 'medium',
  'Low': 'low',
  'None': 'none',
};

// ===== Domain UI Config =====

export const DOMAIN_CONFIG: Record<TaskDomain, { label: string; color: string; bgColor: string }> = {
  work: { label: 'Work', color: '#152A54', bgColor: '#E8EDF5' },
  career: { label: 'Career', color: '#5B6B3B', bgColor: '#EFF2E8' },
  personal: { label: 'Personal', color: '#A0584A', bgColor: '#F5EDEB' },
};

export const STATUS_CONFIG: Record<TaskStatus, { label: string; color: string; bgColor: string }> = {
  todo: { label: 'To Do', color: '#6B7280', bgColor: '#F3F4F6' },
  in_progress: { label: 'In Progress', color: '#2563EB', bgColor: '#EFF6FF' },
  done: { label: 'Done', color: '#16A34A', bgColor: '#F0FDF4' },
  skipped: { label: 'Skipped', color: '#CA8A04', bgColor: '#FEFCE8' },
  cancelled: { label: 'Cancelled', color: '#9CA3AF', bgColor: '#F9FAFB' },
};

export const PRIORITY_CONFIG: Record<TaskPriority, { label: string; color: string }> = {
  urgent: { label: 'Urgent', color: '#DC2626' },
  high: { label: 'High', color: '#EA580C' },
  medium: { label: 'Medium', color: '#CA8A04' },
  low: { label: 'Low', color: '#2563EB' },
  none: { label: 'None', color: '#9CA3AF' },
};

// Board view column ordering
export const BOARD_COLUMNS: TaskStatus[] = ['todo', 'in_progress', 'done'];
