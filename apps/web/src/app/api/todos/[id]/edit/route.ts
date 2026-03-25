import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { getNotionClient } from '@/server/dashboard/notion-client';
import { parseEditWithAI, updateTaskInNotionFull } from '@/server/dashboard/task-update';
import type { TaskContext } from '@/server/dashboard/task-update';
import { TODO_CACHE_KEY } from '@/server/dashboard/todo-types';

// POST /api/todos/:id/edit — AI-powered Quick To-Do editing
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const { id } = await params;
    const body = await request.json();
    const { instruction, todo } = body as {
      instruction: string;
      todo: TaskContext;
    };

    if (!instruction?.trim()) {
      return NextResponse.json({ error: 'instruction is required' }, { status: 400 });
    }

    if (!todo) {
      return NextResponse.json({ error: 'todo context is required' }, { status: 400 });
    }

    // AI parses the edit instruction
    const parsed = await parseEditWithAI(instruction, todo);

    // Apply updates to Notion (same unified DB)
    await updateTaskInNotionFull(id, parsed.propertyUpdates, parsed.pageBodyUpdate);

    // Invalidate all caches
    taskCache.invalidateAll();
    taskCache.invalidate(TODO_CACHE_KEY);
    taskCache.invalidate(`${TODO_CACHE_KEY}:completed`);

    // Re-fetch updated page for response
    const notion = getNotionClient();
    const updatedPage = await notion.pages.retrieve({ page_id: id });
    const props = (updatedPage as { properties: Record<string, unknown> }).properties;
    const titleProp = props['Name'] as { title?: Array<{ plain_text: string }> } | undefined;
    const name = titleProp?.title?.[0]?.plain_text || '';

    return NextResponse.json({
      success: true,
      todo: { id, name },
      updates: {
        propertyUpdates: parsed.propertyUpdates,
        pageBodyUpdate: parsed.pageBodyUpdate,
        summary: parsed.summary,
      },
    });
  } catch (error) {
    console.error('Failed to edit todo:', error);
    return NextResponse.json(
      {
        error: 'Failed to edit todo',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}
