'use client';

import useSWR from 'swr';
import { useCallback } from 'react';
import type { TaskDomain, TaskStatus, UnifiedTask } from '@/server/dashboard/types';
import { STATUS_MAP } from '@/server/dashboard/types';
import { authedFetcher, checkAuth } from '@/hooks/fetcher';

interface UseTasksOptions {
  domain?: TaskDomain;
  status?: TaskStatus;
  includeCompleted?: boolean;
}

interface TasksResponse {
  tasks: UnifiedTask[];
  count: number;
}

function buildUrl(options: UseTasksOptions): string {
  const params = new URLSearchParams();
  if (options.domain) params.set('domain', options.domain);
  if (options.status) params.set('status', options.status);
  if (options.includeCompleted) params.set('includeCompleted', 'true');
  const qs = params.toString();
  return `/api/tasks${qs ? `?${qs}` : ''}`;
}

export function useTasks(options: UseTasksOptions = {}) {
  const url = buildUrl(options);

  const { data, error, isLoading, mutate } = useSWR<TasksResponse>(url, authedFetcher, {
    revalidateOnFocus: false,
    refreshInterval: 3 * 60 * 1000,
    dedupingInterval: 5000,
  });

  const updateTaskStatus = useCallback(
    async (taskId: string, rawStatus: string) => {
      // Optimistic update
      if (data) {
        const normalizedStatus = STATUS_MAP[rawStatus] || 'todo';
        const optimisticTasks = data.tasks.map(t =>
          t.id === taskId ? { ...t, status: normalizedStatus, rawStatus } : t,
        );
        mutate({ tasks: optimisticTasks, count: optimisticTasks.length }, false);
      }

      const res = await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: rawStatus }),
      });

      checkAuth(res);
      if (!res.ok) {
        mutate();
        throw new Error(`Failed to update: ${res.status}`);
      }

      mutate();
    },
    [data, mutate],
  );

  const editTask = useCallback(
    async (instruction: string, task: UnifiedTask) => {
      const res = await fetch(`/api/tasks/${task.id}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instruction,
          task: {
            title: task.title,
            status: task.rawStatus,
            priority: task.priority,
            dueDate: task.dueDate,
            startTime: task.startTime,
            durationHours: task.durationHours,
            domain: task.domain,
            metadata: task.metadata,
          },
        }),
      });

      checkAuth(res);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.details || body.error || `Failed: ${res.status}`);
      }

      const result = await res.json();

      if (result.task && data) {
        const updatedTasks = data.tasks.map(t =>
          t.id === task.id ? result.task : t,
        );
        mutate({ tasks: updatedTasks, count: updatedTasks.length }, false);
      }

      setTimeout(() => mutate(), 2000);

      return result;
    },
    [data, mutate],
  );

  const refreshTasks = useCallback(async () => {
    const res = await fetch('/api/tasks', { method: 'POST' });
    checkAuth(res);
    if (!res.ok) throw new Error(`Failed to refresh: ${res.status}`);
    const freshData = await res.json();
    mutate(freshData, false);
  }, [mutate]);

  return {
    tasks: data?.tasks ?? [],
    count: data?.count ?? 0,
    isLoading,
    error,
    updateTaskStatus,
    editTask,
    refreshTasks,
    mutate,
  };
}
