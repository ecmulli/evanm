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
  dueDate: string | null;
  startTime: string | null;
  createdAt: string;
}

interface TodosResponse {
  todos: Todo[];
  count: number;
}

interface EditResult {
  success: boolean;
  updates: {
    summary: string;
  };
}

export function useTodos(includeCompleted = false, disabled = false) {
  const url = `/api/todos${includeCompleted ? '?includeCompleted=true' : ''}`;

  const { data, error, isLoading, mutate } = useSWR<TodosResponse>(
    disabled ? null : url,
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
        dueDate: null,
        startTime: null,
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

  const editTodo = useCallback(
    async (instruction: string, todo: Todo): Promise<EditResult> => {
      const res = await fetch(`/api/todos/${todo.id}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instruction,
          todo: {
            title: todo.name,
            status: todo.done ? 'Done' : 'To Do',
            priority: null,
            dueDate: todo.dueDate,
            startTime: todo.startTime,
            durationHours: null,
            domain: todo.domain,
            metadata: {},
          },
        }),
      });

      checkAuth(res);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.details || body.error || `Failed: ${res.status}`);
      }

      const result = await res.json();

      // Revalidate
      setTimeout(() => mutate(), 2000);
      mutate();

      return result;
    },
    [mutate],
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
    editTodo,
    createSmartTask,
    mutate,
  };
}
