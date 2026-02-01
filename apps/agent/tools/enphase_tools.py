#!/usr/bin/env python3
"""
Enphase Solar tool definitions for OpenAI function calling.

These tools allow the agent to query solar production, consumption,
and system status data from the Enphase API.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

# Tool definitions for OpenAI
ENPHASE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_solar_production",
            "description": (
                "Get solar panel production data for a specified date range. "
                "Returns total kWh produced and daily averages. "
                "Use this when the user asks about solar production, energy generated, "
                "or how much power their panels made."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": (
                            "Start date in YYYY-MM-DD format. "
                            "Defaults to 7 days ago if not provided."
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "End date in YYYY-MM-DD format. "
                            "Defaults to today if not provided."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_energy_consumption",
            "description": (
                "Get home energy consumption data for a specified date range. "
                "Returns total kWh consumed and daily averages. "
                "Use this when the user asks about energy usage, consumption, "
                "or how much power their home used."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_net_energy_usage",
            "description": (
                "Calculate net energy usage (production minus consumption). "
                "Positive values mean energy was exported to the grid. "
                "Negative values mean energy was imported from the grid. "
                "Also provides self-consumption percentage and grid independence metrics. "
                "Use this when the user asks about net usage, grid import/export, "
                "or energy balance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": (
                "Get current solar system status and summary. "
                "Returns current power production, today's energy, lifetime energy, "
                "system size, number of panels, and whether the system is currently producing. "
                "Use this when the user asks about current status, real-time production, "
                "or system health."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def parse_date_with_context(
    date_str: Optional[str], default_offset_days: int = 0, timezone: str = "America/Chicago"
) -> str:
    """
    Parse a date string or return a default based on offset.

    Args:
        date_str: Date string in YYYY-MM-DD format, or None
        default_offset_days: Days from today for default (negative for past)
        timezone: Timezone for date calculation

    Returns:
        Date string in YYYY-MM-DD format
    """
    tz = ZoneInfo(timezone)
    if date_str:
        return date_str
    return (datetime.now(tz) + timedelta(days=default_offset_days)).strftime("%Y-%m-%d")


def execute_enphase_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    enphase_service: Any,
) -> Dict[str, Any]:
    """
    Execute an Enphase tool and return results.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        enphase_service: Initialized EnphaseService instance

    Returns:
        Tool execution result as a dictionary
    """
    try:
        if tool_name == "get_solar_production":
            result = enphase_service.get_production(
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
            )
            return {
                "success": True,
                "data": result.model_dump(),
                "summary": (
                    f"Solar production from {result.start_date} to {result.end_date}: "
                    f"{result.total_kwh} kWh total"
                    + (
                        f" ({result.average_daily_kwh} kWh/day average)"
                        if result.average_daily_kwh
                        else ""
                    )
                ),
            }

        elif tool_name == "get_energy_consumption":
            result = enphase_service.get_consumption(
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
            )
            return {
                "success": True,
                "data": result.model_dump(),
                "summary": (
                    f"Energy consumption from {result.start_date} to {result.end_date}: "
                    f"{result.total_kwh} kWh total"
                    + (
                        f" ({result.average_daily_kwh} kWh/day average)"
                        if result.average_daily_kwh
                        else ""
                    )
                ),
            }

        elif tool_name == "get_net_energy_usage":
            result = enphase_service.get_net_energy(
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
            )
            net_direction = "exported to grid" if result.net_kwh >= 0 else "imported from grid"
            return {
                "success": True,
                "data": result.model_dump(),
                "summary": (
                    f"Net energy from {result.start_date} to {result.end_date}: "
                    f"{abs(result.net_kwh)} kWh {net_direction}. "
                    f"Production: {result.production_kwh} kWh, "
                    f"Consumption: {result.consumption_kwh} kWh."
                    + (
                        f" Grid independence: {result.grid_independence_pct}%."
                        if result.grid_independence_pct is not None
                        else ""
                    )
                ),
            }

        elif tool_name == "get_system_status":
            result = enphase_service.get_system_status()
            status_msg = "currently producing" if result.is_producing else "not producing"
            return {
                "success": True,
                "data": result.model_dump(),
                "summary": (
                    f"System status: {status_msg} at {result.current_power_kw} kW. "
                    f"Today: {result.energy_today_kwh} kWh. "
                    f"Lifetime: {result.energy_lifetime_mwh} MWh. "
                    f"System: {result.system_size_kw} kW with {result.num_panels} panels."
                ),
            }

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
