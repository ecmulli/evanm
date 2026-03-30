import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { getNotionClient, PROPS } from '@/server/dashboard/notion-client';
import { normalizeTask } from '@/server/dashboard/notion-normalizer';
import { promoteTodoToTask } from '@/server/dashboard/todo-queries';
import { TODO_CACHE_KEY } from '@/server/dashboard/todo-types';
import type { TaskDomain } from '@/server/dashboard/types';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const { id } = await params;

    // Fetch the existing to-do to get its name and domain
    const notion = getNotionClient();
    const page = await notion.pages.retrieve({ page_id: id });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const props = (page as any).properties;
    const titleProp = props[PROPS.title];
    const todoName =
      titleProp?.title?.[0]?.plain_text || titleProp?.title?.[0]?.text?.content || '';

    if (!todoName) {
      return NextResponse.json({ error: 'Could not read todo name' }, { status: 400 });
    }

    const rawDomain = props[PROPS.domain]?.select?.name?.toLowerCase() || 'personal';
    const domain: TaskDomain =
      rawDomain === 'work' || rawDomain === 'career' || rawDomain === 'personal'
        ? rawDomain
        : 'personal';

    // Promote the to-do to a task
    await promoteTodoToTask(id, todoName, domain);

    // Invalidate both todo and task caches
    taskCache.invalidate(TODO_CACHE_KEY);
    taskCache.invalidate(`${TODO_CACHE_KEY}:completed`);
    taskCache.invalidateAll();

    // Re-fetch and return the updated page as a task
    const updatedPage = await notion.pages.retrieve({ page_id: id });
    const task = normalizeTask(updatedPage);

    return NextResponse.json({
      success: true,
      task,
    });
  } catch (error) {
    console.error('Failed to promote todo:', error);
    return NextResponse.json(
      {
        error: 'Failed to promote todo to task',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}
