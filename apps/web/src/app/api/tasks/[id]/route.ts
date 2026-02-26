import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { updateTaskInNotion } from '@/server/dashboard/notion-queries';
import { DOMAIN_STATUSES, type TaskDomain } from '@/server/dashboard/types';

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
    const { status, domain } = body as { status: string; domain: TaskDomain };

    if (!status || !domain) {
      return NextResponse.json({ error: 'Missing status or domain' }, { status: 400 });
    }

    // Validate the raw status is valid for this domain
    const validStatuses = DOMAIN_STATUSES[domain];
    if (!validStatuses?.includes(status)) {
      return NextResponse.json(
        { error: `Invalid status "${status}" for domain "${domain}". Valid: ${validStatuses?.join(', ')}` },
        { status: 400 },
      );
    }

    await updateTaskInNotion(id, domain, status);

    // Invalidate cache so next fetch gets fresh data
    taskCache.invalidateAll();

    return NextResponse.json({ success: true, id, status, domain });
  } catch (error) {
    console.error('Error updating task:', error);
    return NextResponse.json(
      { error: 'Failed to update task', detail: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    );
  }
}
