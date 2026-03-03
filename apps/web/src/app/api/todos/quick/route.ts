import { NextRequest, NextResponse } from 'next/server';
import { taskCache } from '@/server/dashboard/cache';
import { createTodoInNotion } from '@/server/dashboard/todo-queries';
import { TODO_CACHE_KEY } from '@/server/dashboard/todo-types';
import type { TaskDomain } from '@/server/dashboard/types';

// POST /api/todos/quick — simplified endpoint for Apple Shortcuts
// Auth: Bearer token only (no cookie fallback)
// Body: { text: string, domain?: "work" | "career" | "personal" }
export async function POST(request: NextRequest) {
  const bearerToken = process.env.BEARER_TOKEN;
  if (bearerToken) {
    const authHeader = request.headers.get('Authorization');
    if (
      !authHeader?.startsWith('Bearer ') ||
      authHeader.slice(7) !== bearerToken
    ) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
  }

  try {
    const body = await request.json();
    const text = body.text?.trim();

    if (!text) {
      return NextResponse.json({ error: 'text is required' }, { status: 400 });
    }

    const validDomains: TaskDomain[] = ['work', 'career', 'personal'];
    const domain: TaskDomain = validDomains.includes(body.domain)
      ? body.domain
      : 'personal';

    await createTodoInNotion(text, domain);

    taskCache.invalidate(TODO_CACHE_KEY);
    taskCache.invalidate(`${TODO_CACHE_KEY}:completed`);

    return NextResponse.json({ success: true, name: text });
  } catch (error) {
    console.error('Failed to create quick todo:', error);
    return NextResponse.json(
      { error: 'Failed to create todo', details: String(error) },
      { status: 500 },
    );
  }
}
