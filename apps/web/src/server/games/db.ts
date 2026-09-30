import { Pool } from 'pg';

const globalForPg = globalThis as unknown as { gamesPool?: Pool };

export function gamesPool(): Pool {
  if (!globalForPg.gamesPool) {
    const connectionString = process.env.DATABASE_URL;
    if (!connectionString) throw new Error('DATABASE_URL is not set');
    globalForPg.gamesPool = new Pool({ connectionString, max: 3 });
  }
  return globalForPg.gamesPool;
}
