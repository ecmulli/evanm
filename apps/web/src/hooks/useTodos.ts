'use client';

import useSWR from 'swr';
import { useCallback } from 'react';
import type { TaskDomain } from '@/server/dashboard/types';
import { authedFetcher, checkAuth } from '@/hooks/fetcher';

export interface Todo {
  id: string;
  name: string;
  done: boolean;
  domain: TaskDomain;
  createdAt: string;
}

interface TodosResponse {
  todos: Todo[];
  count: number;
}

export function useTodos(includeCompleted = false) {
  const url = `/api/todos${includeCompleted ? '?includeCompleted=true' : ''}`;

  const { data, error, isLoading, mutate } = useSWR<TodosResponse>(
    url,
    authedFetcher,
    {
      revalidateOnFocus: false,
      refreshInterval: 3 * 60 * 1000,
      dedupingInterval: 5000,
    },
  );

  const addTodo = useCallback(
    async (name: string, domain: TaskDomain) => {
      // Optimistic: prepend temp item
      const tempTodo: Todo = {
        id: `temp-${Date.now()}`,
        name,
        done: false,
        domain,
        createdAt: new Date().toISOString(),
      };
      if (data) {
        mutate(
          { todos: [tempTodo, ...data.todos], count: data.count + 1 },
          false,
        );
      }

      const res = await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, domain }),
      });

      checkAuth(res);
      if (!res.ok) {
        mutate();
        throw new Error(`Failed to add todo: ${res.status}`);
      }

      mutate();
    },
    [data, mutate],
  );

  const toggleTodo = useCallback(
    async (id: string, done: boolean) => {
      // Optimistic toggle
      if (data) {
        const updated = data.todos.map((t) =>
          t.id === id ? { ...t, done } : t,
        );
        mutate({ todos: updated, count: data.count }, false);
      }

      const res = await fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ done }),
      });

      checkAuth(res);
      if (!res.ok) {
        mutate();
        throw new Error(`Failed to toggle todo: ${res.status}`);
      }

      mutate();
    },
    [data, mutate],
  );

  const deleteTodo = useCallback(
    async (id: string) => {
      // Optimistic remove
      if (data) {
        const filtered = data.todos.filter((t) => t.id !== id);
        mutate({ todos: filtered, count: filtered.length }, false);
      }

      const res = await fetch(`/api/todos/${id}`, { method: 'DELETE' });

      checkAuth(res);
      if (!res.ok) {
        mutate();
        throw new Error(`Failed to delete todo: ${res.status}`);
      }

      mutate();
    },
    [data, mutate],
  );

  const createSmartTask = useCallback(
    async (text: string, domainHint: TaskDomain) => {
      const res = await fetch('/api/tasks/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, domain: domainHint }),
      });

      checkAuth(res);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(err.details || err.error || `Failed: ${res.status}`);
      }

      // Refresh todos in case AI routed to quick_todo
      mutate();
      return res.json();
    },
    [mutate],
  );

  return {
    todos: data?.todos ?? [],
    count: data?.count ?? 0,
    isLoading,
    error,
    addTodo,
    toggleTodo,
    deleteTodo,
    createSmartTask,
    mutate,
  };
}
