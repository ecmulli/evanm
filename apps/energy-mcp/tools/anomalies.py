"""Anomaly detection and retrieval tools."""

from datetime import date, timedelta

import asyncpg


async def get_anomalies(
    pool: asyncpg.Pool,
    start_date: str | None = None,
    end_date: str | None = None,
    severity: str | None = None,
    unresolved_only: bool = True,
) -> dict:
    """Get detected energy usage anomalies."""
    today = date.today()
    end = date.fromisoformat(end_date) if end_date else today
    start = date.fromisoformat(start_date) if start_date else end - timedelta(days=30)

    conditions = ["date >= $1", "date <= $2"]
    params: list = [start, end]
    idx = 3

    if unresolved_only:
        conditions.append("resolved = FALSE")

    if severity:
        conditions.append(f"severity = ${idx}")
        params.append(severity)
        idx += 1

    where = " AND ".join(conditions)

    rows = await pool.fetch(
        f"""
        SELECT id, detected_at, anomaly_type, severity, date,
               metric_value, baseline_value, deviation_pct, description, resolved
        FROM energy_anomalies
        WHERE {where}
        ORDER BY date DESC, severity DESC
        """,
        *params,
    )

    return {
        "period": {"start": str(start), "end": str(end)},
        "filter": {"severity": severity, "unresolved_only": unresolved_only},
        "count": len(rows),
        "anomalies": [
            {
                "id": r["id"],
                "type": r["anomaly_type"],
                "severity": r["severity"],
                "date": str(r["date"]),
                "detected_at": r["detected_at"].isoformat(),
                "metric_value": float(r["metric_value"]) if r["metric_value"] else None,
                "baseline_value": float(r["baseline_value"]) if r["baseline_value"] else None,
                "deviation_pct": float(r["deviation_pct"]) if r["deviation_pct"] else None,
                "description": r["description"],
                "resolved": r["resolved"],
            }
            for r in rows
        ],
    }


async def run_anomaly_check(
    pool: asyncpg.Pool,
    timezone: str,
    target_date: str | None = None,
) -> dict:
    """
    Run anomaly detection for a specific date (on-demand).

    Checks:
    1. High baseline: nighttime min vs 30-day rolling average
    2. Consumption spikes: hourly consumption vs same-hour 30-day average
    3. Night usage: overnight total vs 30-day overnight average
    """
    check_date = date.fromisoformat(target_date) if target_date else date.today() - timedelta(days=1)
    anomalies = []

    # Check 1: High baseline
    row = await pool.fetchrow(
        """
        WITH stats AS (
            SELECT AVG(baseline_avg_night_wh) AS avg_night,
                   STDDEV(baseline_avg_night_wh) AS std_night
            FROM daily_energy_summary
            WHERE date >= ($1::date - 30) AND date < $1
              AND baseline_avg_night_wh IS NOT NULL
        ),
        today AS (
            SELECT baseline_avg_night_wh FROM daily_energy_summary WHERE date = $1
        )
        SELECT today.baseline_avg_night_wh AS value, stats.avg_night, stats.std_night,
               CASE WHEN stats.std_night > 0
                   THEN (today.baseline_avg_night_wh - stats.avg_night) / stats.std_night
                   ELSE 0 END AS z_score
        FROM today, stats
        """,
        check_date,
    )

    if row and row["value"] is not None:
        z = float(row["z_score"])
        if z >= 2.0:
            severity = "critical" if z >= 3.0 else "warning"
            anomalies.append({
                "check": "high_baseline",
                "severity": severity,
                "z_score": round(z, 2),
                "value_wh": float(row["value"]),
                "baseline_wh": round(float(row["avg_night"]), 1),
                "message": f"Nighttime baseline {float(row['value'])*4:.0f}W is {z:.1f} std devs above 30-day avg ({float(row['avg_night'])*4:.0f}W)",
            })

    # Check 2: Consumption spikes
    spike_rows = await pool.fetch(
        """
        WITH today_hourly AS (
            SELECT EXTRACT(HOUR FROM "timestamp" AT TIME ZONE $2)::int AS hour,
                   SUM(watt_hours) AS wh
            FROM energy_readings
            WHERE metric_type = 'consumption'
              AND ("timestamp" AT TIME ZONE $2)::date = $1
            GROUP BY 1
        ),
        baseline_hourly AS (
            SELECT hour, AVG(wh_sum) AS avg_wh FROM (
                SELECT ("timestamp" AT TIME ZONE $2)::date AS d,
                       EXTRACT(HOUR FROM "timestamp" AT TIME ZONE $2)::int AS hour,
                       SUM(watt_hours) AS wh_sum
                FROM energy_readings
                WHERE metric_type = 'consumption'
                  AND ("timestamp" AT TIME ZONE $2)::date >= ($1::date - 30)
                  AND ("timestamp" AT TIME ZONE $2)::date < $1
                GROUP BY 1, 2
            ) sub GROUP BY 1
        )
        SELECT t.hour, t.wh, b.avg_wh, t.wh / NULLIF(b.avg_wh, 0) AS mult
        FROM today_hourly t JOIN baseline_hourly b ON t.hour = b.hour
        WHERE b.avg_wh > 0 AND t.wh > b.avg_wh * 3
        ORDER BY mult DESC LIMIT 3
        """,
        check_date, timezone,
    )

    for r in spike_rows:
        mult = float(r["mult"])
        anomalies.append({
            "check": "consumption_spike",
            "severity": "warning" if mult >= 5 else "info",
            "hour": r["hour"],
            "value_wh": float(r["wh"]),
            "baseline_wh": round(float(r["avg_wh"]), 1),
            "multiplier": round(mult, 1),
            "message": f"Hour {r['hour']:02d}:00 usage {float(r['wh']):.0f}Wh is {mult:.1f}x normal ({float(r['avg_wh']):.0f}Wh)",
        })

    # Check 3: Night usage
    night_row = await pool.fetchrow(
        """
        WITH today_night AS (
            SELECT COALESCE(SUM(watt_hours), 0) AS total
            FROM energy_readings
            WHERE metric_type = 'consumption'
              AND ("timestamp" AT TIME ZONE $2)::date = $1
              AND EXTRACT(HOUR FROM "timestamp" AT TIME ZONE $2) IN (23,0,1,2,3,4)
        ),
        baseline AS (
            SELECT AVG(nt) AS avg_nt FROM (
                SELECT ("timestamp" AT TIME ZONE $2)::date AS d, SUM(watt_hours) AS nt
                FROM energy_readings
                WHERE metric_type = 'consumption'
                  AND ("timestamp" AT TIME ZONE $2)::date >= ($1::date - 30)
                  AND ("timestamp" AT TIME ZONE $2)::date < $1
                  AND EXTRACT(HOUR FROM "timestamp" AT TIME ZONE $2) IN (23,0,1,2,3,4)
                GROUP BY 1
            ) sub
        )
        SELECT today_night.total, baseline.avg_nt,
               today_night.total / NULLIF(baseline.avg_nt, 0) AS mult
        FROM today_night, baseline
        """,
        check_date, timezone,
    )

    if night_row and night_row["mult"] and float(night_row["mult"]) >= 1.5:
        mult = float(night_row["mult"])
        anomalies.append({
            "check": "night_usage_high",
            "severity": "warning",
            "value_wh": float(night_row["total"]),
            "baseline_wh": round(float(night_row["avg_nt"]), 1),
            "multiplier": round(mult, 1),
            "message": f"Overnight usage {float(night_row['total']):.0f}Wh is {mult:.1f}x normal ({float(night_row['avg_nt']):.0f}Wh)",
        })

    status = "clear" if not anomalies else max(a["severity"] for a in anomalies)

    return {
        "date": str(check_date),
        "status": status,
        "checks_run": ["high_baseline", "consumption_spikes", "night_usage"],
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
    }
