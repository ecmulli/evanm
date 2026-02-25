// ===== Domain Types =====

export type TaskDomain = 'work' | 'career' | 'personal';
export type TaskStatus = 'todo' | 'in_progress' | 'done' | 'blocked' | 'skipped' | 'cancelled';
export type TaskPriority = 'urgent' | 'high' | 'medium' | 'low' | 'none';

export interface UnifiedTask {
  id: string;
  title: string;
  notionUrl: string;
  domain: TaskDomain;
  status: TaskStatus;
  rawStatus: string;
  priority: TaskPriority | null;
  dueDate: string | null; // ISO date string
  metadata: {
    labels?: string[];
    estimatedHours?: number;
    phase?: string;
    category?: string;
    cadence?: string;
    timeEstimate?: string;
    description?: string;
    personalCategory?: string;
  };
  createdAt: string;
  updatedAt: string;
}

// ===== Status Mapping =====

export const STATUS_MAP: Record<TaskDomain, Record<string, TaskStatus>> = {
  work: {
    'Backlog': 'todo',
    'Todo': 'todo',
    'In progress': 'in_progress',
    'Blocked': 'blocked',
    'Completed': 'done',
    'Cancelled': 'cancelled',
  },
  career: {
    'To Do': 'todo',
    'In Progress': 'in_progress',
    'Done': 'done',
    'Skipped': 'skipped',
  },
  personal: {
    'To Do': 'todo',
    'In Progress': 'in_progress',
    'Done': 'done',
  },
};

// Reverse mapping: for each domain + normalized status, what raw status to write back
// Uses the first matching raw status for the normalized value
export function denormalizeStatus(domain: TaskDomain, normalized: TaskStatus): string | null {
  const domainMap = STATUS_MAP[domain];
  // For write-back, prefer specific raw values
  const preferredMap: Record<TaskDomain, Partial<Record<TaskStatus, string>>> = {
    work: {
      todo: 'Todo',
      in_progress: 'In progress',
      blocked: 'Blocked',
      done: 'Completed',
      cancelled: 'Cancelled',
    },
    career: {
      todo: 'To Do',
      in_progress: 'In Progress',
      done: 'Done',
      skipped: 'Skipped',
    },
    personal: {
      todo: 'To Do',
      in_progress: 'In Progress',
      done: 'Done',
    },
  };

  return preferredMap[domain]?.[normalized] ?? null;
}

// Available raw status options per domain (for the UI dropdown)
export const DOMAIN_STATUSES: Record<TaskDomain, string[]> = {
  work: ['Backlog', 'Todo', 'In progress', 'Blocked', 'Completed', 'Cancelled'],
  career: ['To Do', 'In Progress', 'Done', 'Skipped'],
  personal: ['To Do', 'In Progress', 'Done'],
};

// ===== Priority Mapping =====

export const PRIORITY_MAP: Record<TaskDomain, Record<string, TaskPriority>> = {
  work: {
    'ASAP': 'urgent',
    'High': 'high',
    'Medium': 'medium',
    'Low': 'low',
    'Needs Review': 'none',
    'None': 'none',
  },
  career: {
    'High': 'high',
    'Medium': 'medium',
    'Low': 'low',
  },
  personal: {
    'High': 'high',
    'Medium': 'medium',
    'Low': 'low',
  },
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
  blocked: { label: 'Blocked', color: '#DC2626', bgColor: '#FEF2F2' },
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
export const BOARD_COLUMNS: TaskStatus[] = ['todo', 'in_progress', 'blocked', 'done'];
