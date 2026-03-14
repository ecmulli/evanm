import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import { parseTaskWithAI, createTaskInNotion } from '@/server/dashboard/task-creation';
import type { TaskDomain } from '@/server/dashboard/types';

export async function POST(request: NextRequest) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const text = body.text?.trim();

    if (!text) {
      return NextResponse.json({ error: 'text is required' }, { status: 400 });
    }

    const validDomains: TaskDomain[] = ['work', 'career', 'personal'];
    if (!body.domain || !validDomains.includes(body.domain)) {
      return NextResponse.json({ error: 'domain is required (work, career, or personal)' }, { status: 400 });
    }
    const domain: TaskDomain = body.domain;

    // Step 1: AI parses the free-form text
    const parsed = await parseTaskWithAI(text, domain);

    // Step 2: Create the task in Notion
    const result = await createTaskInNotion(parsed);

    // Invalidate all caches so task lists refresh
    taskCache.invalidateAll();

    return NextResponse.json({
      success: true,
      task: result,
    });
  } catch (error) {
    console.error('Failed to create task:', error);
    return NextResponse.json(
      {
        error: 'Failed to create task',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}
