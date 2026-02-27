import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { fetchTodos, createTodoInNotion } from '@/server/dashboard/todo-queries';
import { TODO_CACHE_KEY } from '@/server/dashboard/todo-types';
import type { Todo } from '@/server/dashboard/todo-types';
import type { TaskDomain } from '@/server/dashboard/types';

export async function GET(request: NextRequest) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const includeCompleted =
      request.nextUrl.searchParams.get('includeCompleted') === 'true';
    const cacheKey = includeCompleted
      ? `${TODO_CACHE_KEY}:completed`
      : TODO_CACHE_KEY;

    let todos = taskCache.get<Todo[]>(cacheKey);
    if (!todos) {
      todos = await fetchTodos(includeCompleted);
      taskCache.set(cacheKey, todos);
    }

    return NextResponse.json({ todos, count: todos.length });
  } catch (error) {
    console.error('Failed to fetch todos:', error);
    return NextResponse.json(
      { error: 'Failed to fetch todos', details: String(error) },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const name = body.name?.trim();

    if (!name) {
      return NextResponse.json({ error: 'name is required' }, { status: 400 });
    }

    const validDomains: TaskDomain[] = ['work', 'career', 'personal'];
    const domain: TaskDomain = validDomains.includes(body.domain)
      ? body.domain
      : 'personal';

    const todo = await createTodoInNotion(name, domain);

    // Invalidate cache
    taskCache.invalidate(TODO_CACHE_KEY);
    taskCache.invalidate(`${TODO_CACHE_KEY}:completed`);

    return NextResponse.json({ success: true, todo });
  } catch (error) {
    console.error('Failed to create todo:', error);
    return NextResponse.json(
      { error: 'Failed to create todo', details: String(error) },
      { status: 500 },
    );
  }
}
