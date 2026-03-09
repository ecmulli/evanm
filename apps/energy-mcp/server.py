#!/usr/bin/env python3
"""
Energy monitoring MCP server.

Provides tools for querying electricity usage, baseline analysis,
and anomaly detection from Enphase solar data stored in Postgres.
"""

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from config import Config
from db import create_pool
from tools.anomalies import get_anomalies, run_anomaly_check
from tools.baseline import get_baseline_analysis, get_baseline_trend
from tools.summary import get_daily_summary, get_system_overview, get_weekly_summary
from tools.usage import get_energy_usage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server("energy-monitor")
_pool = None
_config = None


def _json_result(data: dict) -> list[TextContent]:
    """Format a dict as JSON text content for MCP response."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_energy_usage",
            description=(
                "Get energy usage data for a date range. Returns consumption and/or "
                "production data at 15min, hourly, or daily granularity. "
                "Use for questions like 'how much electricity did I use yesterday?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD (defaults to today)"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD (defaults to start_date)"},
                    "metric": {
                        "type": "string",
                        "enum": ["consumption", "production", "both"],
                        "description": "Which metric to query (default: consumption)",
                    },
                    "granularity": {
                        "type": "string",
                        "enum": ["15min", "hourly", "daily"],
                        "description": "Data granularity (default: hourly)",
                    },
                },
            },
        ),
        Tool(
            name="get_baseline_analysis",
            description=(
                "Analyze baseline electricity consumption patterns. Shows the minimum "
                "power the house draws at any point (nighttime baseline). A healthy home "
                "should drop to 200-400W. If minimum is consistently 1000W+, something "
                "is drawing power that shouldn't be (e.g., stuck heater coils). "
                "Use for 'what is my baseline load?' or 'is something drawing power at night?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD (defaults to 30 days ago)"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD (defaults to today)"},
                },
            },
        ),
        Tool(
            name="get_baseline_trend",
            description=(
                "Show weekly baseline load trend over time. Shows whether baseline "
                "is trending up, down, or stable. A rising trend could indicate a "
                "new always-on appliance or malfunction. "
                "Use for 'is my baseline usage trending up?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "weeks": {"type": "integer", "description": "How many weeks to look back (default: 8)"},
                },
            },
        ),
        Tool(
            name="get_anomalies",
            description=(
                "Get detected energy usage anomalies. Returns anomalies flagged by "
                "the background detection job: high_baseline, consumption_spike, "
                "night_usage_high. Use for 'are there any energy anomalies?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD (defaults to 30 days ago)"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD (defaults to today)"},
                    "severity": {
                        "type": "string",
                        "enum": ["info", "warning", "critical"],
                        "description": "Filter by severity",
                    },
                    "unresolved_only": {"type": "boolean", "description": "Only show unresolved (default: true)"},
                },
            },
        ),
        Tool(
            name="run_anomaly_check",
            description=(
                "Run anomaly detection on-demand for a specific date. Checks baseline, "
                "consumption spikes, and night usage against 30-day rolling averages. "
                "Use for 'check yesterday for anomalies' or 'run anomaly detection for March 5'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD (defaults to yesterday)"},
                },
            },
        ),
        Tool(
            name="get_daily_summary",
            description=(
                "Get comprehensive summary for a single day: production, consumption, "
                "net, baseline, peaks, grid independence, and anomalies. "
                "Use for 'how did yesterday look?' or 'summarize March 5'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD (defaults to yesterday)"},
                },
            },
        ),
        Tool(
            name="get_weekly_summary",
            description=(
                "Get weekly energy summary with day-by-day breakdown, totals, "
                "averages, comparison to prior week, and anomalies. "
                "Use for 'how was this week?' or 'weekly energy report'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "week_of": {"type": "string", "description": "YYYY-MM-DD of any day in the week (defaults to current week)"},
                },
            },
        ),
        Tool(
            name="get_system_overview",
            description=(
                "Get high-level overview of the energy monitoring system: data range, "
                "total readings, current baseline, recent anomalies, last collection time. "
                "Use for 'what energy data do you have?' or 'is the monitoring system working?'"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    global _pool, _config

    if _pool is None:
        _config = Config.from_env()
        _pool = await create_pool(_config.database_url)

    tz = _config.timezone

    if name == "get_energy_usage":
        result = await get_energy_usage(
            _pool, tz,
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            metric=arguments.get("metric", "consumption"),
            granularity=arguments.get("granularity", "hourly"),
        )
    elif name == "get_baseline_analysis":
        result = await get_baseline_analysis(
            _pool, tz,
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
        )
    elif name == "get_baseline_trend":
        result = await get_baseline_trend(
            _pool, tz,
            weeks=arguments.get("weeks", 8),
        )
    elif name == "get_anomalies":
        result = await get_anomalies(
            _pool,
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            severity=arguments.get("severity"),
            unresolved_only=arguments.get("unresolved_only", True),
        )
    elif name == "run_anomaly_check":
        result = await run_anomaly_check(
            _pool, tz,
            target_date=arguments.get("date"),
        )
    elif name == "get_daily_summary":
        result = await get_daily_summary(
            _pool, tz,
            target_date=arguments.get("date"),
        )
    elif name == "get_weekly_summary":
        result = await get_weekly_summary(
            _pool, tz,
            week_of=arguments.get("week_of"),
        )
    elif name == "get_system_overview":
        result = await get_system_overview(_pool)
    else:
        result = {"error": f"Unknown tool: {name}"}

    return _json_result(result)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
