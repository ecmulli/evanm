import { NextRequest, NextResponse } from 'next/server';
import { validateApiAuth } from '@/server/dashboard/auth';
import { taskCache } from '@/server/dashboard/cache';
import {
  toggleTodoInNotion,
  deleteTodoInNotion,
} from '@/server/dashboard/todo-queries';
import { TODO_CACHE_KEY } from '@/server/dashboard/todo-types';

function invalidateTodoCache() {
  taskCache.invalidate(TODO_CACHE_KEY);
  taskCache.invalidate(`${TODO_CACHE_KEY}:completed`);
}

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

    if (typeof body.done !== 'boolean') {
      return NextResponse.json(
        { error: 'done must be a boolean' },
        { status: 400 },
      );
    }

    await toggleTodoInNotion(id, body.done);
    invalidateTodoCache();

    return NextResponse.json({ success: true, id, done: body.done });
  } catch (error) {
    console.error('Failed to toggle todo:', error);
    return NextResponse.json(
      { error: 'Failed to toggle todo', details: String(error) },
      { status: 500 },
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!validateApiAuth(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const { id } = await params;
    await deleteTodoInNotion(id);
    invalidateTodoCache();

    return NextResponse.json({ success: true, id });
  } catch (error) {
    console.error('Failed to delete todo:', error);
    return NextResponse.json(
      { error: 'Failed to delete todo', details: String(error) },
      { status: 500 },
    );
  }
}
