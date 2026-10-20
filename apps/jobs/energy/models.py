"""Pydantic models for Enphase API responses."""

from typing import List, Optional

from pydantic import BaseModel, Field


class EnphaseInterval(BaseModel):
    """A single time interval of telemetry data."""

    end_at: int = Field(..., description="Unix timestamp for end of interval")
    wh_del: Optional[float] = Field(None, description="Watt-hours delivered")
    powr: Optional[int] = Field(None, description="Power in watts at interval end")
    enwh: Optional[int] = Field(None, description="Energy in watt-hours (consumption)")


class EnphaseProductionResponse(BaseModel):
    """Response from an Enphase telemetry endpoint (production_micro, production_meter, consumption_meter)."""

    system_id: int
    granularity: str
    total_devices: int
    start_at: int
    end_at: int
    intervals: List[EnphaseInterval] = Field(default_factory=list)


class EnphaseLifetimeResponse(BaseModel):
    """Response from energy_lifetime or consumption_lifetime endpoint.

    Returns daily Wh totals as an array starting from start_date.
    """

    system_id: int
    start_date: str = Field(..., description="YYYY-MM-DD of first element")
    production: List[int] = Field(default_factory=list, description="Daily Wh values")
    meta: Optional[dict] = None


class EnphaseTokenResponse(BaseModel):
    """OAuth token response from Enphase."""

    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
