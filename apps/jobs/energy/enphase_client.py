"""
Simplified Enphase API client for data collection.

Ported from the cursor/enphase-solar-mcp-6c99 branch's
apps/agent/services/enphase.py, stripped down to just
the API client + OAuth token management needed for collection.
"""

import base64
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests

from .config import Config
from .db import Database
from .models import (
    EnphaseConsumptionResponse,
    EnphaseProductionResponse,
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

    def _make_api_request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        retry_on_401: bool = True,
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

        logger.debug(f"API request: {endpoint}")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401 and retry_on_401:
            logger.info("Got 401, refreshing token and retrying...")
            self.refresh_access_token()
            return self._make_api_request(endpoint, params, retry_on_401=False)

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
    ) -> EnphaseConsumptionResponse:
        """Fetch 15-min consumption intervals for a time range."""
        endpoint = f"/api/v4/systems/{self.config.enphase_system_id}/telemetry/consumption"
        data = self._make_api_request(
            endpoint,
            params={"start_at": start_at, "end_at": end_at, "granularity": "15mins"},
        )
        return EnphaseConsumptionResponse(**data)
