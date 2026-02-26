'use client';

import useSWR from 'swr';
import { useCallback } from 'react';
import type { TaskDomain, TaskStatus, UnifiedTask } from '@/server/dashboard/types';
import { STATUS_MAP } from '@/server/dashboard/types';

interface UseTasksOptions {
  domain?: TaskDomain;
  status?: TaskStatus;
  includeCompleted?: boolean;
}

interface TasksResponse {
  tasks: UnifiedTask[];
  count: number;
}

const fetcher = (url: string) => fetch(url).then(res => {
  if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
  return res.json();
});

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

  const { data, error, isLoading, mutate } = useSWR<TasksResponse>(url, fetcher, {
    revalidateOnFocus: false,
    refreshInterval: 3 * 60 * 1000, // 3 minutes — match server cache TTL
    dedupingInterval: 5000,
  });

  const updateTaskStatus = useCallback(
    async (taskId: string, rawStatus: string, domain: TaskDomain) => {
      // Optimistic update
      if (data) {
        const normalizedStatus = STATUS_MAP[domain]?.[rawStatus] || 'todo';
        const optimisticTasks = data.tasks.map(t =>
          t.id === taskId ? { ...t, status: normalizedStatus, rawStatus } : t,
        );
        mutate({ tasks: optimisticTasks, count: optimisticTasks.length }, false);
      }

      const res = await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: rawStatus, domain }),
      });

      if (!res.ok) {
        // Revert optimistic update on error
        mutate();
        throw new Error(`Failed to update: ${res.status}`);
      }

      // Revalidate after successful write
      mutate();
    },
    [data, mutate],
  );

  const refreshTasks = useCallback(async () => {
    const res = await fetch('/api/tasks', { method: 'POST' });
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
    refreshTasks,
    mutate,
  };
}
