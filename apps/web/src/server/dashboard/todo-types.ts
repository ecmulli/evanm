import type { TaskDomain } from './types';

export interface Todo {
  id: string;
  name: string;
  done: boolean;
  domain: TaskDomain;
  createdAt: string;
}

export const TODO_CACHE_KEY = 'todos:active';
