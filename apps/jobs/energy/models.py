"""Pydantic models for Enphase API responses."""

from typing import List, Optional

from pydantic import BaseModel, Field


class EnphaseInterval(BaseModel):
    """A single time interval of telemetry data."""

    end_at: int = Field(..., description="Unix timestamp for end of interval")
    wh_del: Optional[int] = Field(None, description="Watt-hours delivered (production)")
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


class EnphaseTokenResponse(BaseModel):
    """OAuth token response from Enphase."""

    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
