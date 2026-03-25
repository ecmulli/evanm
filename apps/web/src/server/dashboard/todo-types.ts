import type { TaskDomain } from './types';

export interface Todo {
  id: string;
  name: string;
  done: boolean;
  domain: TaskDomain;
  dueDate: string | null;
  startTime: string | null;
  createdAt: string;
}

export const TODO_CACHE_KEY = 'todos:active';
