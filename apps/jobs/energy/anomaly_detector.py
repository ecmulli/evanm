"""
Energy anomaly detection.

Detects anomalous patterns in energy usage:
- High baseline load (e.g., stuck heater coils)
- Consumption spikes
- Elevated night usage
"""

import logging
from datetime import date, timedelta

from .db import Database

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in energy usage patterns."""

    # Flag if nighttime baseline > N standard deviations above 30-day average
    BASELINE_WARNING_Z = 2.0
    BASELINE_CRITICAL_Z = 3.0

    # Flag if any hour > Nx the same-hour 30-day average
    SPIKE_INFO_MULT = 3.0
    SPIKE_WARNING_MULT = 5.0

    # Flag if overnight total > Nx the 30-day average
    NIGHT_WARNING_MULT = 1.5

    def __init__(self, db: Database, timezone: str = "America/Chicago"):
        self.db = db
        self.timezone = timezone

    def check_date(self, target_date: date) -> list[dict]:
        """Run all anomaly checks for a given date."""
        anomalies = []
        anomalies += self._check_high_baseline(target_date)
        anomalies += self._check_consumption_spikes(target_date)
        anomalies += self._check_night_usage(target_date)
        self._store_anomalies(anomalies)
        return anomalies

    def _check_high_baseline(self, target_date: date) -> list[dict]:
        """Compare nighttime baseline to 30-day rolling average."""
        with self.db.cursor() as cur:
            cur.execute(
                """
                WITH stats AS (
                    SELECT
                        AVG(baseline_avg_night_wh) AS avg_night,
                        STDDEV(baseline_avg_night_wh) AS std_night
                    FROM daily_energy_summary
                    WHERE date >= (%s::date - INTERVAL '30 days')
                      AND date < %s
                      AND baseline_avg_night_wh IS NOT NULL
                ),
                today AS (
                    SELECT baseline_avg_night_wh
                    FROM daily_energy_summary
                    WHERE date = %s
                )
                SELECT
                    today.baseline_avg_night_wh AS value,
                    stats.avg_night AS baseline,
                    stats.std_night,
                    CASE WHEN stats.std_night > 0
                        THEN (today.baseline_avg_night_wh - stats.avg_night) / stats.std_night
                        ELSE 0 END AS z_score
                FROM today, stats
                """,
                (target_date, target_date, target_date),
            )
            row = cur.fetchone()

        if not row or row["value"] is None or row["baseline"] is None:
            return []

        z = float(row["z_score"])
        if z >= self.BASELINE_CRITICAL_Z:
            severity = "critical"
        elif z >= self.BASELINE_WARNING_Z:
            severity = "warning"
        else:
            return []

        value_w = int(row["value"]) * 4  # Convert 15-min Wh to estimated W
        baseline_w = int(float(row["baseline"])) * 4
        deviation = round((float(row["value"]) - float(row["baseline"])) / float(row["baseline"]) * 100, 1) if float(row["baseline"]) > 0 else 0

        return [{
            "anomaly_type": "high_baseline",
            "severity": severity,
            "date": target_date,
            "metric_value": float(row["value"]),
            "baseline_value": float(row["baseline"]),
            "deviation_pct": deviation,
            "description": (
                f"Nighttime baseline ~{value_w}W is {severity} "
                f"(z-score {z:.1f}, 30-day avg ~{baseline_w}W, "
                f"+{deviation}%). Possible always-on load."
            ),
        }]

    def _check_consumption_spikes(self, target_date: date) -> list[dict]:
        """Check if any hourly consumption is abnormally high vs same-hour average."""
        with self.db.cursor() as cur:
            # Get hourly consumption for the target date
            cur.execute(
                """
                WITH today_hourly AS (
                    SELECT
                        EXTRACT(HOUR FROM timestamp AT TIME ZONE %s)::int AS hour,
                        SUM(watt_hours) AS wh
                    FROM energy_readings
                    WHERE metric_type = 'consumption'
                      AND (timestamp AT TIME ZONE %s)::date = %s
                    GROUP BY 1
                ),
                baseline_hourly AS (
                    SELECT
                        EXTRACT(HOUR FROM timestamp AT TIME ZONE %s)::int AS hour,
                        AVG(watt_hours_sum) AS avg_wh
                    FROM (
                        SELECT
                            (timestamp AT TIME ZONE %s)::date AS d,
                            EXTRACT(HOUR FROM timestamp AT TIME ZONE %s)::int AS hour,
                            SUM(watt_hours) AS watt_hours_sum
                        FROM energy_readings
                        WHERE metric_type = 'consumption'
                          AND (timestamp AT TIME ZONE %s)::date >= (%s::date - INTERVAL '30 days')
                          AND (timestamp AT TIME ZONE %s)::date < %s
                        GROUP BY 1, 2
                    ) sub
                    GROUP BY 1
                )
                SELECT
                    t.hour, t.wh AS today_wh, b.avg_wh AS baseline_wh,
                    CASE WHEN b.avg_wh > 0 THEN t.wh / b.avg_wh ELSE 0 END AS multiplier
                FROM today_hourly t
                JOIN baseline_hourly b ON t.hour = b.hour
                WHERE b.avg_wh > 0 AND t.wh > b.avg_wh * %s
                ORDER BY multiplier DESC
                LIMIT 3
                """,
                (
                    self.timezone, self.timezone, target_date,
                    self.timezone, self.timezone, self.timezone,
                    self.timezone, target_date, self.timezone, target_date,
                    self.SPIKE_INFO_MULT,
                ),
            )
            rows = cur.fetchall()

        anomalies = []
        for row in rows:
            mult = float(row["multiplier"])
            severity = "warning" if mult >= self.SPIKE_WARNING_MULT else "info"
            anomalies.append({
                "anomaly_type": "consumption_spike",
                "severity": severity,
                "date": target_date,
                "metric_value": float(row["today_wh"]),
                "baseline_value": float(row["baseline_wh"]),
                "deviation_pct": round((mult - 1) * 100, 1),
                "description": (
                    f"Hour {int(row['hour']):02d}:00 consumption {float(row['today_wh']):.0f}Wh "
                    f"is {mult:.1f}x the 30-day average ({float(row['baseline_wh']):.0f}Wh)."
                ),
            })

        return anomalies

    def _check_night_usage(self, target_date: date) -> list[dict]:
        """Check if overnight usage (11pm-5am) is elevated."""
        with self.db.cursor() as cur:
            cur.execute(
                """
                WITH today_night AS (
                    SELECT COALESCE(SUM(watt_hours), 0) AS total_wh
                    FROM energy_readings
                    WHERE metric_type = 'consumption'
                      AND (timestamp AT TIME ZONE %s)::date = %s
                      AND EXTRACT(HOUR FROM timestamp AT TIME ZONE %s) IN (23, 0, 1, 2, 3, 4)
                ),
                baseline_night AS (
                    SELECT AVG(night_total) AS avg_wh
                    FROM (
                        SELECT
                            (timestamp AT TIME ZONE %s)::date AS d,
                            SUM(watt_hours) AS night_total
                        FROM energy_readings
                        WHERE metric_type = 'consumption'
                          AND (timestamp AT TIME ZONE %s)::date >= (%s::date - INTERVAL '30 days')
                          AND (timestamp AT TIME ZONE %s)::date < %s
                          AND EXTRACT(HOUR FROM timestamp AT TIME ZONE %s) IN (23, 0, 1, 2, 3, 4)
                        GROUP BY 1
                    ) sub
                )
                SELECT
                    today_night.total_wh,
                    baseline_night.avg_wh,
                    CASE WHEN baseline_night.avg_wh > 0
                        THEN today_night.total_wh / baseline_night.avg_wh
                        ELSE 0 END AS multiplier
                FROM today_night, baseline_night
                """,
                (
                    self.timezone, target_date, self.timezone,
                    self.timezone, self.timezone, target_date,
                    self.timezone, target_date, self.timezone,
                ),
            )
            row = cur.fetchone()

        if not row or row["avg_wh"] is None or float(row["multiplier"]) < self.NIGHT_WARNING_MULT:
            return []

        mult = float(row["multiplier"])
        return [{
            "anomaly_type": "night_usage_high",
            "severity": "warning",
            "date": target_date,
            "metric_value": float(row["total_wh"]),
            "baseline_value": float(row["avg_wh"]),
            "deviation_pct": round((mult - 1) * 100, 1),
            "description": (
                f"Overnight usage {float(row['total_wh']):.0f}Wh is {mult:.1f}x "
                f"the 30-day average ({float(row['avg_wh']):.0f}Wh)."
            ),
        }]

    def _store_anomalies(self, anomalies: list[dict]):
        """Persist detected anomalies to the database."""
        if not anomalies:
            return

        with self.db.cursor() as cur:
            for a in anomalies:
                cur.execute(
                    """
                    INSERT INTO energy_anomalies
                        (anomaly_type, severity, date, metric_value, baseline_value,
                         deviation_pct, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (anomaly_type, date) DO UPDATE SET
                        severity = EXCLUDED.severity,
                        metric_value = EXCLUDED.metric_value,
                        baseline_value = EXCLUDED.baseline_value,
                        deviation_pct = EXCLUDED.deviation_pct,
                        description = EXCLUDED.description,
                        detected_at = NOW()
                    """,
                    (
                        a["anomaly_type"], a["severity"], a["date"],
                        a["metric_value"], a["baseline_value"],
                        a["deviation_pct"], a["description"],
                    ),
                )

        logger.info(f"Stored {len(anomalies)} anomalies")
