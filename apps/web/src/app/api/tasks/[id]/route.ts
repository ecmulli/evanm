import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { updateTaskInNotion } from '@/server/dashboard/notion-queries';
import { RAW_STATUSES } from '@/server/dashboard/types';

// PATCH /api/tasks/:id — update a task's status
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const { id } = await params;
    const body = await request.json();
    const { status } = body as { status: string };

    if (!status) {
      return NextResponse.json({ error: 'Missing status' }, { status: 400 });
    }

    if (!RAW_STATUSES.includes(status)) {
      return NextResponse.json(
        { error: `Invalid status "${status}". Valid: ${RAW_STATUSES.join(', ')}` },
        { status: 400 },
      );
    }

    await updateTaskInNotion(id, status);

    taskCache.invalidateAll();

    return NextResponse.json({ success: true, id, status });
  } catch (error) {
    console.error('Error updating task:', error);
    return NextResponse.json(
      { error: 'Failed to update task', detail: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    );
  }
}
