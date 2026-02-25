import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { fetchAllTasks } from '@/server/dashboard/notion-queries';
import type { TaskDomain, TaskStatus, UnifiedTask } from '@/server/dashboard/types';

const CACHE_KEY = 'tasks:all';
const CACHE_KEY_COMPLETED = 'tasks:all:completed';

async function getTasks(includeCompleted: boolean): Promise<UnifiedTask[]> {
  const cacheKey = includeCompleted ? CACHE_KEY_COMPLETED : CACHE_KEY;
  const cached = taskCache.get<UnifiedTask[]>(cacheKey);
  if (cached) return cached;

  const tasks = await fetchAllTasks({ includeCompleted });
  taskCache.set(cacheKey, tasks);
  return tasks;
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

    let tasks = await getTasks(includeCompleted);

    if (domainFilter) {
      tasks = tasks.filter(t => t.domain === domainFilter);
    }
    if (statusFilter) {
      tasks = tasks.filter(t => t.status === statusFilter);
    }

    return NextResponse.json({ tasks, count: tasks.length });
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
    const tasks = await fetchAllTasks({ includeCompleted: false });
    taskCache.set(CACHE_KEY, tasks);
    return NextResponse.json({ tasks, count: tasks.length, refreshed: true });
  } catch (error) {
    console.error('Error refreshing tasks:', error);
    return NextResponse.json(
      { error: 'Failed to refresh tasks', detail: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    );
  }
}
