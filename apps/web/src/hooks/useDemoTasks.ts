'use client';

import { useState, useCallback, useEffect } from 'react';
import type { TaskDomain, TaskStatus, UnifiedTask } from '@/server/dashboard/types';
import { STATUS_MAP } from '@/server/dashboard/types';

const now = new Date().toISOString();
const today = new Date().toISOString().split('T')[0];
const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

const DEMO_TASKS: UnifiedTask[] = [
  {
    id: 'demo-task-1',
    title: 'Review Q4 project proposal',
    notionUrl: '#',
    type: 'task',
    domain: 'work',
    status: 'in_progress',
    rawStatus: 'In Progress',
    priority: 'high',
    dueDate: today,
    startTime: '2:00 PM',
    durationHours: 1.5,
    metadata: { category: 'Planning' },
    createdAt: now,
    updatedAt: now,
  },
  {
    id: 'demo-task-2',
    title: 'Update portfolio with recent projects',
    notionUrl: '#',
    type: 'task',
    domain: 'career',
    status: 'todo',
    rawStatus: 'To Do',
    priority: 'medium',
    dueDate: tomorrow,
    startTime: null,
    durationHours: 2,
    metadata: {},
    createdAt: now,
    updatedAt: now,
  },
  {
    id: 'demo-task-3',
    title: 'Schedule dentist appointment',
    notionUrl: '#',
    type: 'task',
    domain: 'personal',
    status: 'todo',
    rawStatus: 'To Do',
    priority: 'low',
    dueDate: tomorrow,
    startTime: null,
    durationHours: null,
    metadata: {},
    createdAt: now,
    updatedAt: now,
  },
  {
    id: 'demo-task-4',
    title: 'Prepare team standup notes',
    notionUrl: '#',
    type: 'task',
    domain: 'work',
    status: 'todo',
    rawStatus: 'To Do',
    priority: 'medium',
    dueDate: today,
    startTime: '9:00 AM',
    durationHours: 0.5,
    metadata: {},
    createdAt: now,
    updatedAt: now,
  },
  {
    id: 'demo-task-5',
    title: 'Draft blog post on TypeScript patterns',
    notionUrl: '#',
    type: 'task',
    domain: 'career',
    status: 'in_progress',
    rawStatus: 'In Progress',
    priority: 'medium',
    dueDate: null,
    startTime: null,
    durationHours: null,
    metadata: {},
    createdAt: now,
    updatedAt: now,
  },
];

interface UseDemoTasksOptions {
  domain?: TaskDomain;
  status?: TaskStatus;
  includeCompleted?: boolean;
}

export function useDemoTasks(options: UseDemoTasksOptions = {}) {
  const [tasks, setTasks] = useState<UnifiedTask[]>(DEMO_TASKS);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 300);
    return () => clearTimeout(timer);
  }, []);

  const filteredTasks = tasks.filter((t) => {
    if (options.domain && t.domain !== options.domain) return false;
    if (options.status && t.status !== options.status) return false;
    if (!options.includeCompleted && (t.status === 'done' || t.status === 'cancelled' || t.status === 'skipped')) return false;
    return true;
  });

  const updateTaskStatus = useCallback(
    async (taskId: string, rawStatus: string) => {
      const normalizedStatus = STATUS_MAP[rawStatus] || 'todo';
      setTasks((prev) =>
        prev.map((t) =>
          t.id === taskId ? { ...t, status: normalizedStatus, rawStatus } : t,
        ),
      );
    },
    [],
  );

  const editTask = useCallback(
    async () => {
      throw new Error('Editing is not available in demo mode. Log in to use this feature.');
    },
    [],
  );

  const refreshTasks = useCallback(async () => {
    // No-op in demo
  }, []);

  const mutate = useCallback(() => {}, []);

  return {
    tasks: filteredTasks,
    count: filteredTasks.length,
    isLoading,
    error: null as Error | null,
    updateTaskStatus,
    editTask,
    refreshTasks,
    mutate,
  };
}
