"""
Daily energy aggregator.

Computes daily_energy_summary rows from raw 15-minute interval data.
"""

import logging
from datetime import date, timedelta

from .db import Database

logger = logging.getLogger(__name__)


class Aggregator:
    """Computes daily summary statistics from raw interval data."""

    def __init__(self, db: Database, timezone: str = "America/Chicago"):
        self.db = db
        self.timezone = timezone

    def aggregate_date(self, target_date: date):
        """Compute or update the daily summary for a single date."""
        logger.info(f"Aggregating daily summary for {target_date}")

        with self.db.cursor() as cur:
            # Compute stats from raw readings
            cur.execute(
                """
                WITH prod AS (
                    SELECT
                        COALESCE(SUM(watt_hours), 0) AS total_wh,
                        MAX(watts) AS peak_w
                    FROM energy_readings
                    WHERE metric_type = 'production'
                      AND (timestamp AT TIME ZONE %s)::date = %s
                ),
                cons AS (
                    SELECT
                        COALESCE(SUM(watt_hours), 0) AS total_wh,
                        MAX(watts) AS peak_w,
                        MIN(watts) AS min_w,
                        MIN(watt_hours) AS min_wh
                    FROM energy_readings
                    WHERE metric_type = 'consumption'
                      AND (timestamp AT TIME ZONE %s)::date = %s
                ),
                night AS (
                    SELECT AVG(watt_hours)::integer AS avg_night_wh
                    FROM energy_readings
                    WHERE metric_type = 'consumption'
                      AND (timestamp AT TIME ZONE %s)::date = %s
                      AND EXTRACT(HOUR FROM timestamp AT TIME ZONE %s) IN (23, 0, 1, 2, 3, 4)
                )
                SELECT
                    prod.total_wh AS prod_wh,
                    prod.peak_w AS prod_peak_w,
                    cons.total_wh AS cons_wh,
                    cons.peak_w AS cons_peak_w,
                    cons.min_w AS cons_min_w,
                    cons.min_wh AS baseline_min_wh,
                    night.avg_night_wh,
                    -- Self-consumption: min(production, consumption) / production
                    CASE WHEN prod.total_wh > 0
                        THEN ROUND(LEAST(prod.total_wh, cons.total_wh)::numeric / prod.total_wh * 100, 2)
                        ELSE NULL END AS self_consumption_pct,
                    -- Grid independence: min(production, consumption) / consumption
                    CASE WHEN cons.total_wh > 0
                        THEN ROUND(LEAST(prod.total_wh, cons.total_wh)::numeric / cons.total_wh * 100, 2)
                        ELSE NULL END AS grid_independence_pct
                FROM prod, cons, night
                """,
                (
                    self.timezone, target_date,
                    self.timezone, target_date,
                    self.timezone, target_date, self.timezone,
                ),
            )
            row = cur.fetchone()

            if row is None or (row["prod_wh"] == 0 and row["cons_wh"] == 0):
                logger.info(f"No data for {target_date}, skipping aggregation")
                return

            # Upsert daily summary
            cur.execute(
                """
                INSERT INTO daily_energy_summary (
                    date, production_wh, production_peak_w,
                    consumption_wh, consumption_peak_w, consumption_min_w,
                    self_consumption_pct, grid_independence_pct,
                    baseline_min_wh, baseline_avg_night_wh
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    production_wh = EXCLUDED.production_wh,
                    production_peak_w = EXCLUDED.production_peak_w,
                    consumption_wh = EXCLUDED.consumption_wh,
                    consumption_peak_w = EXCLUDED.consumption_peak_w,
                    consumption_min_w = EXCLUDED.consumption_min_w,
                    self_consumption_pct = EXCLUDED.self_consumption_pct,
                    grid_independence_pct = EXCLUDED.grid_independence_pct,
                    baseline_min_wh = EXCLUDED.baseline_min_wh,
                    baseline_avg_night_wh = EXCLUDED.baseline_avg_night_wh,
                    updated_at = NOW()
                """,
                (
                    target_date,
                    row["prod_wh"], row["prod_peak_w"],
                    row["cons_wh"], row["cons_peak_w"], row["cons_min_w"],
                    row["self_consumption_pct"], row["grid_independence_pct"],
                    row["baseline_min_wh"], row["avg_night_wh"],
                ),
            )

            logger.info(
                f"Aggregated {target_date}: "
                f"prod={row['prod_wh']}Wh, cons={row['cons_wh']}Wh, "
                f"baseline_night={row['avg_night_wh']}Wh"
            )

    def aggregate_recent(self, days: int = 2):
        """Aggregate the last N days (covers data from overlapping collection windows)."""
        today = date.today()
        for i in range(days):
            self.aggregate_date(today - timedelta(days=i))
