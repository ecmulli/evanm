"""Energy usage query tools."""

import json
from datetime import date, timedelta

import asyncpg


async def get_energy_usage(
    pool: asyncpg.Pool,
    timezone: str,
    start_date: str | None = None,
    end_date: str | None = None,
    metric: str = "consumption",
    granularity: str = "hourly",
) -> dict:
    """
    Get energy usage data for a date range.

    Args:
        start_date: YYYY-MM-DD (defaults to today)
        end_date: YYYY-MM-DD (defaults to start_date)
        metric: "consumption", "production", or "both"
        granularity: "15min", "hourly", or "daily"
    """
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = date.fromisoformat(end_date) if end_date else start
    end_exclusive = end + timedelta(days=1)

    metrics = ["consumption", "production"] if metric == "both" else [metric]
    result = {"start_date": str(start), "end_date": str(end), "metric": metric, "granularity": granularity}

    for m in metrics:
        if granularity == "daily":
            rows = await pool.fetch(
                """
                SELECT date, consumption_wh, production_wh, net_wh,
                       consumption_peak_w, consumption_min_w, baseline_min_wh
                FROM daily_energy_summary
                WHERE date >= $1 AND date <= $2
                ORDER BY date
                """,
                start, end,
            )
            key = "daily" if metric == "both" else "intervals"
            result[key] = [dict(r) for r in rows]
            if m == "consumption":
                result["total_kwh"] = sum(r["consumption_wh"] or 0 for r in rows) / 1000
            else:
                result["total_kwh"] = sum(r["production_wh"] or 0 for r in rows) / 1000

        elif granularity == "hourly":
            rows = await pool.fetch(
                """
                SELECT
                    date_trunc('hour', "timestamp" AT TIME ZONE $3) AS hour,
                    SUM(watt_hours) AS wh,
                    ROUND(SUM(watt_hours) / 1000.0, 3) AS kwh,
                    MAX(watts) AS peak_w,
                    MIN(watts) AS min_w
                FROM energy_readings
                WHERE metric_type = $1
                  AND ("timestamp" AT TIME ZONE $3)::date >= $2
                  AND ("timestamp" AT TIME ZONE $3)::date < $4
                GROUP BY 1
                ORDER BY 1
                """,
                m, start, timezone, end_exclusive,
            )
            key = f"{m}_intervals" if metric == "both" else "intervals"
            result[key] = [
                {"hour": r["hour"].isoformat(), "wh": r["wh"], "kwh": float(r["kwh"]),
                 "peak_w": r["peak_w"], "min_w": r["min_w"]}
                for r in rows
            ]
            total = sum(r["wh"] or 0 for r in rows)
            if metric != "both":
                result["total_kwh"] = round(total / 1000, 3)
            else:
                result[f"{m}_total_kwh"] = round(total / 1000, 3)

        else:  # 15min
            rows = await pool.fetch(
                """
                SELECT "timestamp" AT TIME ZONE $3 AS ts, watt_hours, watts
                FROM energy_readings
                WHERE metric_type = $1
                  AND ("timestamp" AT TIME ZONE $3)::date >= $2
                  AND ("timestamp" AT TIME ZONE $3)::date < $4
                ORDER BY "timestamp"
                """,
                m, start, timezone, end_exclusive,
            )
            key = f"{m}_intervals" if metric == "both" else "intervals"
            result[key] = [
                {"timestamp": r["ts"].isoformat(), "wh": r["watt_hours"], "watts": r["watts"]}
                for r in rows
            ]
            total = sum(r["watt_hours"] or 0 for r in rows)
            if metric != "both":
                result["total_kwh"] = round(total / 1000, 3)
            else:
                result[f"{m}_total_kwh"] = round(total / 1000, 3)

    return result
