"""Database connection management for energy jobs."""

import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._conn = None

    def connect(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.database_url)
            self._conn.autocommit = False
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    @contextmanager
    def cursor(self):
        conn = self.connect()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def upsert_readings(self, readings: list[dict]):
        """Batch upsert energy readings. Skips duplicates."""
        if not readings:
            return 0

        conn = self.connect()
        cur = conn.cursor()
        try:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO energy_readings ("timestamp", metric_type, watt_hours, watts)
                VALUES %s
                ON CONFLICT ("timestamp", metric_type) DO NOTHING
                """,
                [
                    (r["timestamp"], r["metric_type"], r["watt_hours"], r.get("watts"))
                    for r in readings
                ],
            )
            inserted = cur.rowcount
            conn.commit()
            logger.info(f"Upserted {inserted} readings (skipped {len(readings) - inserted} duplicates)")
            return inserted
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def get_token(self, key: str) -> str | None:
        """Get a value from key_value_store."""
        with self.cursor() as cur:
            cur.execute("SELECT value FROM key_value_store WHERE key = %s", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_token(self, key: str, value: str):
        """Upsert a value in key_value_store."""
        with self.cursor() as cur:
            cur.execute(
                """
                INSERT INTO key_value_store (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                """,
                (key, value),
            )
