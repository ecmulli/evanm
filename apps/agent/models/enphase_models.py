#!/usr/bin/env python3
"""
Pydantic models for Enphase Solar API integration.

These models represent the data structures returned by the Enphase v4 API
and the responses from our agent endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enphase API Response Models
# =============================================================================


class EnphaseInterval(BaseModel):
    """A single time interval of telemetry data."""

    end_at: int = Field(..., description="Unix timestamp for end of interval")
    wh_del: Optional[int] = Field(
        None, description="Watt-hours delivered (production)"
    )
    powr: Optional[int] = Field(None, description="Power in watts at interval end")
    enwh: Optional[int] = Field(None, description="Energy in watt-hours (consumption)")


class EnphaseProductionResponse(BaseModel):
    """Response from Enphase production telemetry endpoint."""

    system_id: int
    granularity: str
    total_devices: int
    start_at: int
    end_at: int
    intervals: List[EnphaseInterval]


class EnphaseConsumptionResponse(BaseModel):
    """Response from Enphase consumption telemetry endpoint."""

    system_id: int
    granularity: str
    start_at: int
    end_at: int
    intervals: List[EnphaseInterval]


class EnphaseSystemSummary(BaseModel):
    """Response from Enphase system summary endpoint."""

    system_id: int
    current_power: int = Field(..., description="Current power production in watts")
    energy_today: int = Field(..., description="Energy produced today in watt-hours")
    energy_lifetime: int = Field(
        ..., description="Total lifetime energy in watt-hours"
    )
    modules: int = Field(..., description="Number of modules/panels")
    size_w: int = Field(..., description="System size in watts")
    status: str = Field(..., description="System status (normal, micro, etc.)")
    operational_at: int = Field(..., description="Unix timestamp when system went live")
    last_report_at: int = Field(..., description="Unix timestamp of last report")
    last_interval_end_at: Optional[int] = Field(
        None, description="End of last telemetry interval"
    )


# =============================================================================
# OAuth Token Models
# =============================================================================


class EnphaseTokenResponse(BaseModel):
    """OAuth token response from Enphase."""

    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str


class EnphaseTokenStore(BaseModel):
    """Stored token data with expiration tracking."""

    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"


# =============================================================================
# Agent Response Models
# =============================================================================


class SolarProductionData(BaseModel):
    """Processed solar production data for agent responses."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    total_wh: int = Field(..., description="Total watt-hours produced")
    total_kwh: float = Field(..., description="Total kilowatt-hours produced")
    intervals: int = Field(..., description="Number of data intervals")
    average_daily_kwh: Optional[float] = Field(
        None, description="Average daily production in kWh"
    )


class SolarConsumptionData(BaseModel):
    """Processed solar consumption data for agent responses."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    total_wh: int = Field(..., description="Total watt-hours consumed")
    total_kwh: float = Field(..., description="Total kilowatt-hours consumed")
    intervals: int = Field(..., description="Number of data intervals")
    average_daily_kwh: Optional[float] = Field(
        None, description="Average daily consumption in kWh"
    )


class NetEnergyData(BaseModel):
    """Net energy usage (production - consumption)."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    production_kwh: float = Field(..., description="Total production in kWh")
    consumption_kwh: float = Field(..., description="Total consumption in kWh")
    net_kwh: float = Field(
        ..., description="Net energy (positive = exported, negative = imported)"
    )
    self_consumption_pct: Optional[float] = Field(
        None, description="Percentage of production consumed on-site"
    )
    grid_independence_pct: Optional[float] = Field(
        None, description="Percentage of consumption from solar"
    )


class SystemStatusData(BaseModel):
    """Current system status summary."""

    system_id: int
    current_power_w: int = Field(..., description="Current power in watts")
    current_power_kw: float = Field(..., description="Current power in kilowatts")
    energy_today_kwh: float = Field(..., description="Energy today in kWh")
    energy_lifetime_mwh: float = Field(..., description="Lifetime energy in MWh")
    system_size_kw: float = Field(..., description="System size in kW")
    num_panels: int = Field(..., description="Number of panels")
    status: str = Field(..., description="System status")
    last_report: str = Field(..., description="Last report timestamp (ISO format)")
    is_producing: bool = Field(..., description="Whether system is currently producing")


# =============================================================================
# Agent API Request/Response Models
# =============================================================================


class AgentMessage(BaseModel):
    """A single message in the agent conversation."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class AgentRequest(BaseModel):
    """Request to the unified agent endpoint."""

    message: str = Field(..., description="User message")
    conversation_history: Optional[List[AgentMessage]] = Field(
        default=None, description="Previous conversation messages for context"
    )
    include_solar_context: bool = Field(
        default=True, description="Whether to include solar tools in available actions"
    )
    include_task_context: bool = Field(
        default=True, description="Whether to include task tools in available actions"
    )


class ToolCall(BaseModel):
    """Record of a tool that was called during processing."""

    tool_name: str
    arguments: dict
    result: Optional[dict] = None


class AgentResponse(BaseModel):
    """Response from the unified agent endpoint."""

    success: bool
    message: str = Field(..., description="Natural language response to user")
    tool_calls: List[ToolCall] = Field(
        default_factory=list, description="Tools that were called"
    )
    solar_data: Optional[dict] = Field(
        None, description="Structured solar data if relevant"
    )
    task_data: Optional[dict] = Field(
        None, description="Task creation data if relevant"
    )


# =============================================================================
# OAuth Flow Models
# =============================================================================


class OAuthInitResponse(BaseModel):
    """Response when initiating OAuth flow."""

    auth_url: str = Field(..., description="URL to redirect user for authorization")
    state: str = Field(..., description="State parameter for CSRF protection")


class OAuthCallbackRequest(BaseModel):
    """Request from OAuth callback."""

    code: str = Field(..., description="Authorization code from Enphase")
    state: str = Field(..., description="State parameter to verify")


class OAuthCallbackResponse(BaseModel):
    """Response after successful OAuth callback."""

    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
