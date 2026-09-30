import { gamesPool } from './db';

export const BOARDS = ['desktop', 'mobile'] as const;
export type Board = (typeof BOARDS)[number];
export const TOP_N = 10;
export const MAX_SCORE = 5_000_000;

export interface ScoreEntry {
  id: number;
  initials: string;
  score: number;
  level: number;
  wpm: number;
}

let ready: Promise<unknown> | null = null;

function ensureTable() {
  ready ??= gamesPool()
    .query(`
      CREATE TABLE IF NOT EXISTS keystroids_scores (
        id SERIAL PRIMARY KEY,
        board TEXT NOT NULL,
        initials CHAR(3) NOT NULL,
        score INTEGER NOT NULL,
        level INTEGER NOT NULL,
        wpm INTEGER NOT NULL,
        acc INTEGER NOT NULL,
        drill INTEGER NOT NULL,
        mode INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
      CREATE INDEX IF NOT EXISTS keystroids_scores_board_score_idx
        ON keystroids_scores (board, score DESC, created_at);
    `)
    .catch((err) => {
      ready = null;
      throw err;
    });
  return ready;
}

export async function topScores(board: Board): Promise<ScoreEntry[]> {
  await ensureTable();
  const { rows } = await gamesPool().query<ScoreEntry>(
    `SELECT id, initials, score, level, wpm FROM keystroids_scores
     WHERE board = $1 ORDER BY score DESC, created_at ASC LIMIT $2`,
    [board, TOP_N],
  );
  return rows;
}

export interface NewScore {
  board: Board;
  initials: string;
  score: number;
  level: number;
  wpm: number;
  acc: number;
  drill: number;
  mode: number;
}

export async function addScore(s: NewScore): Promise<number> {
  await ensureTable();
  const { rows } = await gamesPool().query<{ id: number }>(
    `INSERT INTO keystroids_scores (board, initials, score, level, wpm, acc, drill, mode)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id`,
    [s.board, s.initials, s.score, s.level, s.wpm, s.acc, s.drill, s.mode],
  );
  return rows[0].id;
}
