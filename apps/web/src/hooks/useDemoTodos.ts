'use client';

import { useState, useCallback, useEffect } from 'react';
import type { TaskDomain } from '@/server/dashboard/types';
import type { Todo } from '@/hooks/useTodos';
import { useRateLimit } from '@/hooks/useRateLimit';

const now = new Date().toISOString();
const today = new Date().toISOString().split('T')[0];

const DEMO_TODOS: Todo[] = [
  {
    id: 'demo-todo-1',
    name: 'Pick up dry cleaning',
    done: false,
    domain: 'personal',
    dueDate: today,
    startTime: '5:00 PM',
    createdAt: now,
  },
  {
    id: 'demo-todo-2',
    name: 'Reply to Sarah about coffee meetup',
    done: false,
    domain: 'personal',
    dueDate: null,
    startTime: null,
    createdAt: now,
  },
  {
    id: 'demo-todo-3',
    name: 'Submit expense report',
    done: false,
    domain: 'work',
    dueDate: today,
    startTime: null,
    createdAt: now,
  },
  {
    id: 'demo-todo-4',
    name: 'Read chapter 3 of System Design book',
    done: true,
    domain: 'career',
    dueDate: null,
    startTime: null,
    createdAt: now,
  },
];

export function useDemoTodos(includeCompleted = false) {
  const [todos, setTodos] = useState<Todo[]>(DEMO_TODOS);
  const [isLoading, setIsLoading] = useState(true);
  const { checkLimit } = useRateLimit(3, 60_000);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 300);
    return () => clearTimeout(timer);
  }, []);

  const filtered = includeCompleted ? todos : todos.filter((t) => !t.done);

  const addTodo = useCallback(
    async (name: string, domain: TaskDomain) => {
      if (!checkLimit()) {
        throw new Error('Demo rate limit: 3 actions per minute. Log in for unlimited access.');
      }
      const newTodo: Todo = {
        id: `demo-${Date.now()}`,
        name,
        done: false,
        domain,
        dueDate: null,
        startTime: null,
        createdAt: new Date().toISOString(),
      };
      setTodos((prev) => [newTodo, ...prev]);
    },
    [checkLimit],
  );

  const toggleTodo = useCallback(
    async (id: string, done: boolean) => {
      setTodos((prev) => prev.map((t) => (t.id === id ? { ...t, done } : t)));
    },
    [],
  );

  const deleteTodo = useCallback(
    async (id: string) => {
      setTodos((prev) => prev.filter((t) => t.id !== id));
    },
    [],
  );

  const editTodo = useCallback(
    async () => {
      throw new Error('Editing is not available in demo mode. Log in to use this feature.');
    },
    [],
  );

  const createSmartTask = useCallback(
    async () => {
      throw new Error('Smart task creation is not available in demo mode. Log in to use this feature.');
    },
    [],
  );

  const mutate = useCallback(() => {}, []);

  return {
    todos: filtered,
    count: filtered.length,
    isLoading,
    error: null as Error | null,
    addTodo,
    toggleTodo,
    deleteTodo,
    editTodo,
    createSmartTask,
    mutate,
  };
}
