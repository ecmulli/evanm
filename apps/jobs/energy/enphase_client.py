"""
Simplified Enphase API client for data collection.

Ported from the cursor/enphase-solar-mcp-6c99 branch's
apps/agent/services/enphase.py, stripped down to just
the API client + OAuth token management needed for collection.
"""

import base64
import collections
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests

from .config import Config
from .db import Database
from .models import (
    EnphaseLifetimeResponse,
    EnphaseProductionResponse,
    EnphaseRgmStatsResponse,
    EnphaseTokenResponse,
)

logger = logging.getLogger(__name__)

# Enphase API base
BASE_URL = "https://api.enphaseenergy.com"
TOKEN_URL = "https://api.enphaseenergy.com/oauth/token"


class EnphaseClient:
    """Enphase API client with OAuth token management backed by Postgres."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.timezone = ZoneInfo(config.timezone)

        # Load tokens: DB first (refreshed tokens), then env fallback
        self._access_token = db.get_token("enphase_access_token") or ""
        self._refresh_token = (
            db.get_token("enphase_refresh_token")
            or config.enphase_client_secret  # Initial bootstrap from env
            and ""  # Will be set by oauth_bootstrap
        )
        # If DB had no tokens, check for env-provided refresh token
        if not self._refresh_token:
            import os
            self._refresh_token = os.getenv("ENPHASE_REFRESH_TOKEN", "")

        self._token_expires_at: Optional[datetime] = None

        # Rate limiter: track timestamps of recent API requests
        # Enphase Watt (free) plan: 10 requests/minute
        self._request_timestamps: collections.deque = collections.deque()
        self._rate_limit = 10
        self._rate_window = 60  # seconds

    def _get_basic_auth_header(self) -> str:
        credentials = f"{self.config.enphase_client_id}:{self.config.enphase_client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def refresh_access_token(self) -> EnphaseTokenResponse:
        """Refresh the access token and persist new tokens to DB."""
        if not self._refresh_token:
            raise ValueError("No refresh token available. Run oauth_bootstrap.py first.")

        logger.info("Refreshing Enphase access token")

        response = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": self._get_basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )

        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.status_code} {response.text}")
            raise Exception(f"Token refresh failed: {response.text}")

        token_data = response.json()
        token_response = EnphaseTokenResponse(**token_data)

        # Persist to DB so next GitHub Actions run picks them up
        self._access_token = token_response.access_token
        self._refresh_token = token_response.refresh_token
        self._token_expires_at = datetime.now(self.timezone) + timedelta(
            seconds=token_response.expires_in - 60
        )

        self.db.set_token("enphase_access_token", self._access_token)
        self.db.set_token("enphase_refresh_token", self._refresh_token)

        logger.info("Refreshed and persisted Enphase tokens")
        return token_response

    def _ensure_valid_token(self) -> str:
        if not self._access_token:
            # No access token — try refreshing
            self.refresh_access_token()
            return self._access_token

        if self._token_expires_at and datetime.now(self.timezone) >= self._token_expires_at:
            self.refresh_access_token()

        return self._access_token

    def _wait_for_rate_limit(self) -> None:
        """Sleep if needed to stay within the rate limit window."""
        now = time.monotonic()

        # Purge timestamps older than the window
        while self._request_timestamps and now - self._request_timestamps[0] >= self._rate_window:
            self._request_timestamps.popleft()

        if len(self._request_timestamps) >= self._rate_limit:
            # Wait until the oldest request falls outside the window
            wait = self._rate_window - (now - self._request_timestamps[0]) + 0.5
            if wait > 0:
                logger.info(f"Rate limit: {len(self._request_timestamps)} requests in window, waiting {wait:.1f}s")
                time.sleep(wait)
                # Purge again after sleeping
                now = time.monotonic()
                while self._request_timestamps and now - self._request_timestamps[0] >= self._rate_window:
                    self._request_timestamps.popleft()

        self._request_timestamps.append(time.monotonic())

    def _make_api_request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        retry_on_401: bool = True,
        _rate_retries: int = 0,
    ) -> dict[str, Any]:
        token = self._ensure_valid_token()

        url = f"{BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
        }

        # API key must be a query parameter, not a header
        if params is None:
            params = {}
        params["key"] = self.config.enphase_api_key

        # Proactive rate limiting
        self._wait_for_rate_limit()

        logger.debug(f"API request: {endpoint}")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401 and retry_on_401:
            logger.info("Got 401, refreshing token and retrying...")
            self.refresh_access_token()
            return self._make_api_request(endpoint, params, retry_on_401=False)

        # Handle 429 rate limit response: back off and retry (max 3 times)
        if response.status_code == 429:
            if _rate_retries >= 3:
                raise Exception(f"Enphase API rate limit exceeded after {_rate_retries} retries")
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited (429). Waiting {retry_after}s before retry ({_rate_retries + 1}/3)...")
            time.sleep(retry_after)
            return self._make_api_request(endpoint, params, retry_on_401=retry_on_401, _rate_retries=_rate_retries + 1)

        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} {response.text}")
            raise Exception(f"Enphase API error: {response.status_code} {response.text}")

        return response.json()

    def get_production_intervals(
        self, start_at: int, end_at: int
    ) -> EnphaseProductionResponse:
        """Fetch 15-min production intervals for a time range."""
        endpoint = f"/api/v4/systems/{self.config.enphase_system_id}/telemetry/production_micro"
        data = self._make_api_request(
            endpoint,
            params={"start_at": start_at, "end_at": end_at, "granularity": "15mins"},
        )
        return EnphaseProductionResponse(**data)

    def get_consumption_intervals(
        self, start_at: int, end_at: int
    ) -> EnphaseRgmStatsResponse:
        """Fetch 15-min consumption intervals via rgm_stats endpoint.

        The telemetry/consumption endpoint requires a paid plan.
        rgm_stats returns meter_intervals with channels:
          - Channel 1: Production
          - Channel 2: Consumption (net)
        """
        endpoint = f"/api/v4/systems/{self.config.enphase_system_id}/rgm_stats"
        data = self._make_api_request(
            endpoint,
            params={"start_at": start_at, "end_at": end_at, "granularity": "15mins"},
        )
        return EnphaseRgmStatsResponse(**data)

    def get_production_lifetime(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> EnphaseLifetimeResponse:
        """Fetch daily production Wh totals for a date range (or all history).

        Much more efficient than telemetry for backfills — no date range limit.
        Returns {system_id, start_date, production: [wh_day1, wh_day2, ...]}.
        1 API call for any range.
        """
        endpoint = f"/api/v4/systems/{self.config.enphase_system_id}/energy_lifetime"
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        data = self._make_api_request(endpoint, params=params)
        return EnphaseLifetimeResponse(**data)

    def get_consumption_lifetime(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> EnphaseLifetimeResponse:
        """Fetch daily consumption Wh totals for a date range (or all history).

        May return 405 on free Watt plan — caller should handle gracefully.
        """
        endpoint = f"/api/v4/systems/{self.config.enphase_system_id}/consumption_lifetime"
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        data = self._make_api_request(endpoint, params=params)
        return EnphaseLifetimeResponse(**data)
