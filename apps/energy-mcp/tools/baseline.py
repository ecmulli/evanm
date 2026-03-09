"""Baseline load analysis tools."""

from datetime import date, timedelta

import asyncpg


async def get_baseline_analysis(
    pool: asyncpg.Pool,
    timezone: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Analyze baseline electricity consumption patterns.

    Examines minimum consumption intervals to determine the "floor" load.
    A healthy home should have periods near 200-400W. If the minimum is
    consistently 1000W+, something is drawing power that shouldn't be.
    """
    today = date.today()
    end = date.fromisoformat(end_date) if end_date else today
    start = date.fromisoformat(start_date) if start_date else end - timedelta(days=30)

    # Absolute minimum across the period
    abs_min = await pool.fetchrow(
        """
        SELECT timestamp AT TIME ZONE $3 AS ts, watt_hours, watt_hours * 4 AS estimated_watts
        FROM energy_readings
        WHERE metric_type = 'consumption'
          AND (timestamp AT TIME ZONE $3)::date >= $1
          AND (timestamp AT TIME ZONE $3)::date <= $2
        ORDER BY watt_hours ASC
        LIMIT 1
        """,
        start, end, timezone,
    )

    # Daily nighttime minimums (11pm-5am)
    daily_mins = await pool.fetch(
        """
        SELECT
            (timestamp AT TIME ZONE $3)::date AS date,
            MIN(watt_hours) AS min_wh,
            MIN(watt_hours) * 4 AS min_estimated_w,
            (array_agg(timestamp AT TIME ZONE $3 ORDER BY watt_hours ASC))[1]::time AS min_time
        FROM energy_readings
        WHERE metric_type = 'consumption'
          AND (timestamp AT TIME ZONE $3)::date >= $1
          AND (timestamp AT TIME ZONE $3)::date <= $2
          AND EXTRACT(HOUR FROM timestamp AT TIME ZONE $3) IN (23, 0, 1, 2, 3, 4)
        GROUP BY 1
        ORDER BY 1 DESC
        """,
        start, end, timezone,
    )

    # Average nighttime baseline stats
    stats = await pool.fetchrow(
        """
        SELECT
            AVG(baseline_avg_night_wh) AS avg_night_wh,
            AVG(baseline_avg_night_wh) * 4 AS avg_night_w,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY baseline_avg_night_wh) AS median_night_wh
        FROM daily_energy_summary
        WHERE date >= $1 AND date <= $2 AND baseline_avg_night_wh IS NOT NULL
        """,
        start, end,
    )

    # Current week vs prior month
    week_ago = today - timedelta(days=7)
    trend = await pool.fetchrow(
        """
        SELECT
            (SELECT AVG(baseline_avg_night_wh)
             FROM daily_energy_summary WHERE date >= $1 AND date <= $2
             AND baseline_avg_night_wh IS NOT NULL) AS current_week,
            (SELECT AVG(baseline_avg_night_wh)
             FROM daily_energy_summary WHERE date >= $3 AND date < $1
             AND baseline_avg_night_wh IS NOT NULL) AS prior_period
        """,
        week_ago, end, start,
    )

    # Build assessment
    avg_w = int(float(stats["avg_night_w"])) if stats and stats["avg_night_w"] else None
    assessment = _build_assessment(abs_min, avg_w, trend)

    return {
        "period": {"start": str(start), "end": str(end)},
        "baseline_stats": {
            "absolute_min_wh": abs_min["watt_hours"] if abs_min else None,
            "absolute_min_w": abs_min["estimated_watts"] if abs_min else None,
            "absolute_min_timestamp": abs_min["ts"].isoformat() if abs_min else None,
            "avg_night_wh": round(float(stats["avg_night_wh"]), 1) if stats and stats["avg_night_wh"] else None,
            "avg_night_w": avg_w,
            "median_night_wh": round(float(stats["median_night_wh"]), 1) if stats and stats["median_night_wh"] else None,
            "current_week_avg_night_wh": round(float(trend["current_week"]), 1) if trend and trend["current_week"] else None,
            "prior_period_avg_night_wh": round(float(trend["prior_period"]), 1) if trend and trend["prior_period"] else None,
        },
        "daily_minimums": [
            {
                "date": str(r["date"]),
                "min_wh": r["min_wh"],
                "min_w": r["min_estimated_w"],
                "min_time": str(r["min_time"]) if r["min_time"] else None,
            }
            for r in daily_mins[:14]  # Last 2 weeks
        ],
        "assessment": assessment,
    }


def _build_assessment(abs_min, avg_night_w, trend) -> str:
    parts = []

    if avg_night_w:
        if avg_night_w > 1000:
            parts.append(
                f"Your baseline load is ~{avg_night_w}W average overnight. "
                "This is elevated — typical homes are 300-500W. "
                "Something may be drawing significant power continuously."
            )
        elif avg_night_w > 500:
            parts.append(
                f"Your baseline load is ~{avg_night_w}W average overnight. "
                "This is slightly above typical (300-500W) but may be normal "
                "depending on your appliances."
            )
        else:
            parts.append(
                f"Your baseline load is ~{avg_night_w}W average overnight. "
                "This is within normal range."
            )

    if abs_min and abs_min["estimated_watts"]:
        parts.append(
            f"Absolute minimum observed: {abs_min['estimated_watts']}W "
            f"on {abs_min['ts'].strftime('%b %d at %I:%M %p')}."
        )

    if trend and trend["current_week"] and trend["prior_period"]:
        curr = float(trend["current_week"])
        prior = float(trend["prior_period"])
        if prior > 0:
            change = (curr - prior) / prior * 100
            if change > 20:
                parts.append(
                    f"Trending UP: current week avg {curr:.0f}Wh vs "
                    f"prior period {prior:.0f}Wh (+{change:.0f}%). "
                    "Something may have changed recently."
                )
            elif change < -20:
                parts.append(
                    f"Trending DOWN: current week avg {curr:.0f}Wh vs "
                    f"prior period {prior:.0f}Wh ({change:.0f}%). Improving."
                )

    return " ".join(parts) if parts else "Insufficient data for assessment."


async def get_baseline_trend(
    pool: asyncpg.Pool,
    timezone: str,
    weeks: int = 8,
) -> dict:
    """Show weekly baseline load trend over time."""
    rows = await pool.fetch(
        """
        SELECT
            DATE_TRUNC('week', date)::date AS week_start,
            AVG(baseline_avg_night_wh) AS avg_night_wh,
            AVG(baseline_avg_night_wh) * 4 AS avg_night_w,
            MIN(baseline_min_wh) AS min_wh,
            MIN(baseline_min_wh) * 4 AS min_w,
            COUNT(*) AS days_with_data
        FROM daily_energy_summary
        WHERE date >= CURRENT_DATE - ($1 * 7)
          AND baseline_avg_night_wh IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """,
        weeks,
    )

    weeks_data = [
        {
            "week_start": str(r["week_start"]),
            "avg_night_wh": round(float(r["avg_night_wh"]), 1) if r["avg_night_wh"] else None,
            "avg_night_w": int(float(r["avg_night_w"])) if r["avg_night_w"] else None,
            "min_wh": r["min_wh"],
            "min_w": r["min_w"],
            "days_with_data": r["days_with_data"],
        }
        for r in rows
    ]

    # Determine trend direction
    trend = "insufficient_data"
    if len(weeks_data) >= 3:
        first_half = [w["avg_night_w"] for w in weeks_data[:len(weeks_data)//2] if w["avg_night_w"]]
        second_half = [w["avg_night_w"] for w in weeks_data[len(weeks_data)//2:] if w["avg_night_w"]]
        if first_half and second_half:
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            change = (avg_second - avg_first) / avg_first * 100 if avg_first > 0 else 0
            if change > 10:
                trend = "increasing"
            elif change < -10:
                trend = "decreasing"
            else:
                trend = "stable"

    return {
        "weeks": weeks_data,
        "trend": trend,
        "period": f"Last {weeks} weeks",
    }
