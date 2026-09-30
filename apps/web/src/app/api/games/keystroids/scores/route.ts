import { NextRequest, NextResponse } from 'next/server';
import { BOARDS, MAX_SCORE, addScore, topScores } from '@/server/games/keystroids-scores';
import type { Board, NewScore } from '@/server/games/keystroids-scores';

export const dynamic = 'force-dynamic';

const lastPost = new Map<string, number>();
const POST_GAP_MS = 5_000;

function parseBoard(value: unknown): Board | null {
  return BOARDS.includes(value as Board) ? (value as Board) : null;
}

function intIn(value: unknown, min: number, max: number): number | null {
  return Number.isInteger(value) && (value as number) >= min && (value as number) <= max ? (value as number) : null;
}

export async function GET(request: NextRequest) {
  const board = parseBoard(request.nextUrl.searchParams.get('board'));
  if (!board) return NextResponse.json({ error: 'Unknown board' }, { status: 400 });
  try {
    return NextResponse.json({ scores: await topScores(board) });
  } catch (error) {
    console.error('Failed to read keystroids scores:', error);
    return NextResponse.json({ error: 'Scores unavailable' }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0].trim() || 'unknown';
  const now = Date.now();
  if (now - (lastPost.get(ip) ?? 0) < POST_GAP_MS) {
    return NextResponse.json({ error: 'Too many submissions' }, { status: 429 });
  }

  const body = await request.json().catch(() => null);
  const initials = typeof body?.initials === 'string' ? body.initials.toUpperCase() : '';
  const entry = {
    board: parseBoard(body?.board),
    initials: /^[A-Z0-9]{3}$/.test(initials) ? initials : null,
    score: intIn(body?.score, 1, MAX_SCORE),
    level: intIn(body?.level, 1, 99),
    wpm: intIn(body?.wpm, 0, 400),
    acc: intIn(body?.acc, 0, 100),
    drill: intIn(body?.drill, 0, 99),
    mode: intIn(body?.mode, 0, 9),
  };
  if (Object.values(entry).some((v) => v === null)) {
    return NextResponse.json({ error: 'Invalid score' }, { status: 400 });
  }

  lastPost.set(ip, now);
  try {
    const id = await addScore(entry as NewScore);
    return NextResponse.json({ id, scores: await topScores(entry.board as Board) });
  } catch (error) {
    console.error('Failed to save keystroids score:', error);
    return NextResponse.json({ error: 'Scores unavailable' }, { status: 503 });
  }
}
