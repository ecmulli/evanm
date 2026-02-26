import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { fetchAllTasks, type FetchResult } from '@/server/dashboard/notion-queries';
import type { TaskDomain, TaskStatus } from '@/server/dashboard/types';

const CACHE_KEY = 'tasks:all';
const CACHE_KEY_COMPLETED = 'tasks:all:completed';

async function getTasks(includeCompleted: boolean): Promise<FetchResult> {
  const cacheKey = includeCompleted ? CACHE_KEY_COMPLETED : CACHE_KEY;
  const cached = taskCache.get<FetchResult>(cacheKey);
  if (cached) return cached;

  const result = await fetchAllTasks({ includeCompleted });
  taskCache.set(cacheKey, result);
  return result;
}

// GET /api/tasks — returns normalized tasks with optional filters
export async function GET(request: NextRequest) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const { searchParams } = request.nextUrl;
    const domainFilter = searchParams.get('domain') as TaskDomain | null;
    const statusFilter = searchParams.get('status') as TaskStatus | null;
    const includeCompleted = searchParams.get('includeCompleted') === 'true';

    const result = await getTasks(includeCompleted);
    let { tasks } = result;

    if (domainFilter) {
      tasks = tasks.filter(t => t.domain === domainFilter);
    }
    if (statusFilter) {
      tasks = tasks.filter(t => t.status === statusFilter);
    }

    const response: Record<string, unknown> = { tasks, count: tasks.length };
    if (Object.keys(result.errors).length > 0) {
      response.errors = result.errors;
    }
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error fetching tasks:', error);
    return NextResponse.json(
      { error: 'Failed to fetch tasks', detail: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    );
  }
}

// POST /api/tasks — force refresh cache
export async function POST(request: NextRequest) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    taskCache.invalidateAll();
    const result = await fetchAllTasks({ includeCompleted: false });
    taskCache.set(CACHE_KEY, result);
    const response: Record<string, unknown> = { tasks: result.tasks, count: result.tasks.length, refreshed: true };
    if (Object.keys(result.errors).length > 0) {
      response.errors = result.errors;
    }
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error refreshing tasks:', error);
    return NextResponse.json(
      { error: 'Failed to refresh tasks', detail: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    );
  }
}
