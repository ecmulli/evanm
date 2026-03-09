"""Pydantic models for Enphase API responses."""

from typing import List, Optional

from pydantic import BaseModel, Field


class EnphaseInterval(BaseModel):
    """A single time interval of telemetry data."""

    end_at: int = Field(..., description="Unix timestamp for end of interval")
    wh_del: Optional[float] = Field(None, description="Watt-hours delivered")
    powr: Optional[int] = Field(None, description="Power in watts at interval end")
    enwh: Optional[int] = Field(None, description="Energy in watt-hours (consumption)")


class EnphaseRgmInterval(BaseModel):
    """A single interval from the rgm_stats meter_intervals response."""

    channel: int = Field(..., description="Meter channel (1=production, 2=consumption)")
    end_at: int = Field(..., description="Unix timestamp for end of interval")
    wh_del: Optional[float] = Field(None, description="Watt-hours delivered")
    curr_w: Optional[int] = Field(None, description="Current power in watts")


class EnphaseProductionResponse(BaseModel):
    """Response from Enphase production telemetry endpoint."""

    system_id: int
    granularity: str
    total_devices: int
    start_at: int
    end_at: int
    intervals: List[EnphaseInterval]


class EnphaseMeterIntervalGroup(BaseModel):
    """A group of meter intervals from rgm_stats."""

    envoy_serial_number: Optional[str] = None
    channel: Optional[int] = None
    intervals: List[EnphaseRgmInterval]


class EnphaseRgmStatsResponse(BaseModel):
    """Response from Enphase rgm_stats endpoint."""

    system_id: int
    total_devices: int
    intervals: List[dict] = Field(default_factory=list)
    meter_intervals: List[EnphaseMeterIntervalGroup] = Field(default_factory=list)


class EnphaseTokenResponse(BaseModel):
    """OAuth token response from Enphase."""

    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
