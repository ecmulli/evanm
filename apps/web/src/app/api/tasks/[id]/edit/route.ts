import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { parseEditWithAI, updateTaskInNotionFull } from '@/server/dashboard/task-update';
import type { TaskContext } from '@/server/dashboard/task-update';
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
    const body = await request.json();
    const { instruction, task, domain } = body as {
      instruction: string;
      task: TaskContext;
      domain: TaskDomain;
    };

    if (!instruction?.trim()) {
      return NextResponse.json({ error: 'instruction is required' }, { status: 400 });
    }

    if (!task || !domain) {
      return NextResponse.json({ error: 'task and domain are required' }, { status: 400 });
    }

    // Step 1: AI parses the edit instruction
    const parsed = await parseEditWithAI(instruction, task, domain);

    // Step 2: Apply the updates to Notion
    await updateTaskInNotionFull(id, domain, parsed.propertyUpdates, parsed.pageBodyUpdate);

    // Invalidate caches so task lists refresh
    taskCache.invalidateAll();

    return NextResponse.json({
      success: true,
      updates: {
        propertyUpdates: parsed.propertyUpdates,
        pageBodyUpdate: parsed.pageBodyUpdate,
        summary: parsed.summary,
      },
    });
  } catch (error) {
    console.error('Failed to edit task:', error);
    return NextResponse.json(
      {
        error: 'Failed to edit task',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}
