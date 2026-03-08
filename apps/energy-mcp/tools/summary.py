"""Summary and overview tools."""

from datetime import date, timedelta

import asyncpg


async def get_daily_summary(
    pool: asyncpg.Pool,
    timezone: str,
    target_date: str | None = None,
) -> dict:
    """Get comprehensive summary for a single day."""
    d = date.fromisoformat(target_date) if target_date else date.today() - timedelta(days=1)

    # Daily summary
    summary = await pool.fetchrow(
        "SELECT * FROM daily_energy_summary WHERE date = $1", d
    )

    # Anomalies for the day
    anomalies = await pool.fetch(
        "SELECT anomaly_type, severity, description FROM energy_anomalies WHERE date = $1",
        d,
    )

    # Hourly breakdown
    hourly = await pool.fetch(
        """
        SELECT
            EXTRACT(HOUR FROM timestamp AT TIME ZONE $2)::int AS hour,
            metric_type,
            SUM(watt_hours) AS wh,
            MAX(watts) AS peak_w,
            MIN(watts) AS min_w
        FROM energy_readings
        WHERE (timestamp AT TIME ZONE $2)::date = $1
        GROUP BY 1, 2
        ORDER BY 1
        """,
        d, timezone,
    )

    if not summary:
        return {"date": str(d), "status": "no_data", "message": f"No data available for {d}"}

    # Build hourly consumption profile
    cons_by_hour = {}
    prod_by_hour = {}
    for r in hourly:
        entry = {"wh": r["wh"], "peak_w": r["peak_w"], "min_w": r["min_w"]}
        if r["metric_type"] == "consumption":
            cons_by_hour[r["hour"]] = entry
        else:
            prod_by_hour[r["hour"]] = entry

    return {
        "date": str(d),
        "production": {
            "total_kwh": round(summary["production_wh"] / 1000, 2),
            "peak_w": summary["production_peak_w"],
        },
        "consumption": {
            "total_kwh": round(summary["consumption_wh"] / 1000, 2),
            "peak_w": summary["consumption_peak_w"],
            "min_w": summary["consumption_min_w"],
        },
        "net_kwh": round(summary["net_wh"] / 1000, 2) if summary["net_wh"] else None,
        "self_consumption_pct": float(summary["self_consumption_pct"]) if summary["self_consumption_pct"] else None,
        "grid_independence_pct": float(summary["grid_independence_pct"]) if summary["grid_independence_pct"] else None,
        "baseline": {
            "min_interval_wh": summary["baseline_min_wh"],
            "avg_night_wh": summary["baseline_avg_night_wh"],
            "avg_night_w": summary["baseline_avg_night_wh"] * 4 if summary["baseline_avg_night_wh"] else None,
        },
        "anomalies": [
            {"type": a["anomaly_type"], "severity": a["severity"], "description": a["description"]}
            for a in anomalies
        ],
        "hourly_consumption": cons_by_hour,
        "hourly_production": prod_by_hour,
    }


async def get_weekly_summary(
    pool: asyncpg.Pool,
    timezone: str,
    week_of: str | None = None,
) -> dict:
    """Get weekly energy summary with day-by-day breakdown."""
    ref = date.fromisoformat(week_of) if week_of else date.today()
    # Start of week (Monday)
    start = ref - timedelta(days=ref.weekday())
    end = start + timedelta(days=6)

    rows = await pool.fetch(
        """
        SELECT * FROM daily_energy_summary
        WHERE date >= $1 AND date <= $2
        ORDER BY date
        """,
        start, end,
    )

    # Prior week for comparison
    prev_start = start - timedelta(days=7)
    prev_end = start - timedelta(days=1)
    prev_rows = await pool.fetch(
        """
        SELECT
            SUM(consumption_wh) AS cons, SUM(production_wh) AS prod,
            AVG(baseline_avg_night_wh) AS avg_baseline
        FROM daily_energy_summary WHERE date >= $1 AND date <= $2
        """,
        prev_start, prev_end,
    )

    # Anomalies for the week
    anomalies = await pool.fetch(
        """
        SELECT anomaly_type, severity, date, description
        FROM energy_anomalies WHERE date >= $1 AND date <= $2
        ORDER BY date
        """,
        start, end,
    )

    total_cons = sum(r["consumption_wh"] or 0 for r in rows)
    total_prod = sum(r["production_wh"] or 0 for r in rows)

    prev = prev_rows[0] if prev_rows else None
    prev_cons = int(prev["cons"]) if prev and prev["cons"] else None
    prev_prod = int(prev["prod"]) if prev and prev["prod"] else None

    return {
        "week": {"start": str(start), "end": str(end)},
        "totals": {
            "consumption_kwh": round(total_cons / 1000, 2),
            "production_kwh": round(total_prod / 1000, 2),
            "net_kwh": round((total_prod - total_cons) / 1000, 2),
        },
        "averages": {
            "daily_consumption_kwh": round(total_cons / max(len(rows), 1) / 1000, 2),
            "daily_production_kwh": round(total_prod / max(len(rows), 1) / 1000, 2),
        },
        "vs_prior_week": {
            "consumption_change_pct": round((total_cons - prev_cons) / prev_cons * 100, 1) if prev_cons else None,
            "production_change_pct": round((total_prod - prev_prod) / prev_prod * 100, 1) if prev_prod else None,
        },
        "days": [
            {
                "date": str(r["date"]),
                "consumption_kwh": round(r["consumption_wh"] / 1000, 2) if r["consumption_wh"] else 0,
                "production_kwh": round(r["production_wh"] / 1000, 2) if r["production_wh"] else 0,
                "baseline_night_w": r["baseline_avg_night_wh"] * 4 if r["baseline_avg_night_wh"] else None,
            }
            for r in rows
        ],
        "anomalies": [
            {"type": a["anomaly_type"], "severity": a["severity"],
             "date": str(a["date"]), "description": a["description"]}
            for a in anomalies
        ],
        "days_with_data": len(rows),
    }


async def get_system_overview(pool: asyncpg.Pool) -> dict:
    """Get high-level overview of the energy monitoring system."""
    # Data range
    data_range = await pool.fetchrow(
        """
        SELECT
            MIN(timestamp)::date AS first_date,
            MAX(timestamp)::date AS last_date,
            COUNT(*) AS total_readings,
            COUNT(DISTINCT (timestamp::date)) AS days_with_data
        FROM energy_readings
        """
    )

    # Recent anomalies
    anomaly_counts = await pool.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE NOT resolved) AS unresolved,
            COUNT(*) FILTER (WHERE NOT resolved AND severity = 'critical') AS critical,
            COUNT(*) FILTER (WHERE NOT resolved AND severity = 'warning') AS warnings,
            COUNT(*) FILTER (WHERE date >= CURRENT_DATE - 7) AS last_7_days
        FROM energy_anomalies
        """
    )

    # Current baseline
    baseline = await pool.fetchrow(
        """
        SELECT AVG(baseline_avg_night_wh) * 4 AS avg_night_w
        FROM daily_energy_summary
        WHERE date >= CURRENT_DATE - 7 AND baseline_avg_night_wh IS NOT NULL
        """
    )

    # Last collection timestamp
    last_collection = await pool.fetchval(
        "SELECT MAX(created_at) FROM energy_readings"
    )

    has_data = data_range and data_range["total_readings"] and data_range["total_readings"] > 0

    return {
        "status": "active" if has_data else "no_data",
        "data_range": {
            "first_date": str(data_range["first_date"]) if has_data else None,
            "last_date": str(data_range["last_date"]) if has_data else None,
            "total_readings": data_range["total_readings"] if has_data else 0,
            "days_with_data": data_range["days_with_data"] if has_data else 0,
        },
        "last_collection": last_collection.isoformat() if last_collection else None,
        "current_baseline_w": int(float(baseline["avg_night_w"])) if baseline and baseline["avg_night_w"] else None,
        "anomalies": {
            "unresolved": anomaly_counts["unresolved"] if anomaly_counts else 0,
            "critical": anomaly_counts["critical"] if anomaly_counts else 0,
            "warnings": anomaly_counts["warnings"] if anomaly_counts else 0,
            "last_7_days": anomaly_counts["last_7_days"] if anomaly_counts else 0,
        },
    }
