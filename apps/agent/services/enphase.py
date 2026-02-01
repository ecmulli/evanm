#!/usr/bin/env python3
"""
Enphase Solar API Service

Handles OAuth 2.0 authentication and API calls to the Enphase v4 API.
Provides methods for fetching production, consumption, and system summary data.
"""

import base64
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
from models.enphase_models import (
    EnphaseConsumptionResponse,
    EnphaseProductionResponse,
    EnphaseSystemSummary,
    EnphaseTokenResponse,
    EnphaseTokenStore,
    NetEnergyData,
    SolarConsumptionData,
    SolarProductionData,
    SystemStatusData,
)

logger = logging.getLogger(__name__)


class EnphaseService:
    """
    Service for interacting with the Enphase Solar API.

    Handles:
    - OAuth 2.0 token management (authorization, refresh)
    - Production data fetching
    - Consumption data fetching
    - System summary/status
    - Net energy calculations
    """

    # Enphase API endpoints
    BASE_URL = "https://api.enphaseenergy.com"
    AUTH_URL = "https://api.enphaseenergy.com/oauth/authorize"
    TOKEN_URL = "https://api.enphaseenergy.com/oauth/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_key: Optional[str] = None,
        system_id: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        redirect_uri: str = "https://api.enphaseenergy.com/oauth/redirect_uri",
        timezone: str = "America/Chicago",
    ):
        """
        Initialize the Enphase service.

        Args:
            client_id: Enphase OAuth client ID
            client_secret: Enphase OAuth client secret
            api_key: Enphase API key
            system_id: Enphase system ID
            access_token: Current OAuth access token (optional, will refresh if expired)
            refresh_token: OAuth refresh token for getting new access tokens
            redirect_uri: OAuth redirect URI (must match app registration)
            timezone: Timezone for date calculations
        """
        # Load from environment if not provided
        self.client_id = client_id or os.getenv("ENPHASE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("ENPHASE_CLIENT_SECRET", "")
        self.api_key = api_key or os.getenv("ENPHASE_API_KEY", "")
        self.system_id = system_id or os.getenv("ENPHASE_SYSTEM_ID", "")
        self.redirect_uri = redirect_uri or os.getenv(
            "ENPHASE_REDIRECT_URI", "https://api.enphaseenergy.com/oauth/redirect_uri"
        )
        self.timezone = ZoneInfo(timezone)

        # Token management
        self._access_token = access_token or os.getenv("ENPHASE_ACCESS_TOKEN", "")
        self._refresh_token = refresh_token or os.getenv("ENPHASE_REFRESH_TOKEN", "")
        self._token_expires_at: Optional[datetime] = None

        # Token file for persistence (optional)
        self._token_file = Path(os.getenv("ENPHASE_TOKEN_FILE", ""))

        # Load persisted tokens if available
        self._load_persisted_tokens()

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        missing = []
        if not self.client_id:
            missing.append("ENPHASE_CLIENT_ID")
        if not self.client_secret:
            missing.append("ENPHASE_CLIENT_SECRET")
        if not self.api_key:
            missing.append("ENPHASE_API_KEY")

        if missing:
            logger.warning(
                f"Enphase configuration incomplete. Missing: {', '.join(missing)}. "
                "Some features may not work."
            )
        else:
            logger.info("Enphase service initialized with valid configuration")

        if not self.system_id:
            logger.warning(
                "ENPHASE_SYSTEM_ID not set. You'll need to provide it for data queries."
            )

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.client_id and self.client_secret and self.api_key)

    def has_valid_tokens(self) -> bool:
        """Check if we have valid tokens for API calls."""
        return bool(self._access_token and self._refresh_token)

    def _load_persisted_tokens(self) -> None:
        """Load tokens from persistent storage if available."""
        if self._token_file and self._token_file.exists():
            try:
                with open(self._token_file, "r") as f:
                    data = json.load(f)
                    self._access_token = data.get("access_token", self._access_token)
                    self._refresh_token = data.get("refresh_token", self._refresh_token)
                    if data.get("expires_at"):
                        self._token_expires_at = datetime.fromisoformat(
                            data["expires_at"]
                        )
                    logger.info("Loaded persisted Enphase tokens")
            except Exception as e:
                logger.warning(f"Failed to load persisted tokens: {e}")

    def _persist_tokens(self) -> None:
        """Persist tokens to storage if configured."""
        if self._token_file:
            try:
                self._token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._token_file, "w") as f:
                    json.dump(
                        {
                            "access_token": self._access_token,
                            "refresh_token": self._refresh_token,
                            "expires_at": (
                                self._token_expires_at.isoformat()
                                if self._token_expires_at
                                else None
                            ),
                        },
                        f,
                    )
                logger.info("Persisted Enphase tokens")
            except Exception as e:
                logger.warning(f"Failed to persist tokens: {e}")

    def _get_basic_auth_header(self) -> str:
        """Get Basic Auth header for token requests."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Get the OAuth authorization URL for user consent.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Tuple of (authorization_url, state)
        """
        if not state:
            state = base64.urlsafe_b64encode(os.urandom(16)).decode()

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{self.AUTH_URL}?{query_string}"

        return auth_url, state

    def exchange_code_for_tokens(self, code: str) -> EnphaseTokenResponse:
        """
        Exchange an authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token response with access and refresh tokens
        """
        logger.info("Exchanging authorization code for tokens")

        response = requests.post(
            self.TOKEN_URL,
            headers={
                "Authorization": self._get_basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": code,
            },
        )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} {response.text}")
            raise Exception(f"Token exchange failed: {response.text}")

        token_data = response.json()
        token_response = EnphaseTokenResponse(**token_data)

        # Store tokens
        self._access_token = token_response.access_token
        self._refresh_token = token_response.refresh_token
        self._token_expires_at = datetime.now(self.timezone) + timedelta(
            seconds=token_response.expires_in - 60  # 1 minute buffer
        )

        self._persist_tokens()

        logger.info("Successfully obtained Enphase tokens")
        return token_response

    def refresh_access_token(self) -> EnphaseTokenResponse:
        """
        Refresh the access token using the refresh token.

        Returns:
            New token response
        """
        if not self._refresh_token:
            raise ValueError("No refresh token available. Please re-authorize.")

        logger.info("Refreshing Enphase access token")

        response = requests.post(
            self.TOKEN_URL,
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

        # Store new tokens
        self._access_token = token_response.access_token
        self._refresh_token = token_response.refresh_token
        self._token_expires_at = datetime.now(self.timezone) + timedelta(
            seconds=token_response.expires_in - 60
        )

        self._persist_tokens()

        logger.info("Successfully refreshed Enphase tokens")
        return token_response

    def _ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token, refreshing if necessary.

        Returns:
            Valid access token
        """
        if not self._access_token:
            raise ValueError("No access token. Please authorize first.")

        # Check if token is expired or will expire soon
        if self._token_expires_at:
            if datetime.now(self.timezone) >= self._token_expires_at:
                logger.info("Access token expired, refreshing...")
                self.refresh_access_token()

        return self._access_token

    def _make_api_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True,
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request to Enphase.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            retry_on_401: Whether to retry with refreshed token on 401

        Returns:
            JSON response data
        """
        token = self._ensure_valid_token()

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "key": self.api_key,
        }

        logger.debug(f"Making API request to {endpoint}")

        response = requests.get(url, headers=headers, params=params)

        # Handle token expiration
        if response.status_code == 401 and retry_on_401:
            logger.info("Received 401, attempting token refresh...")
            self.refresh_access_token()
            return self._make_api_request(endpoint, params, retry_on_401=False)

        if response.status_code != 200:
            logger.error(
                f"API request failed: {response.status_code} {response.text}"
            )
            raise Exception(f"API request failed: {response.status_code} {response.text}")

        return response.json()

    # =========================================================================
    # Production Data
    # =========================================================================

    def get_production_telemetry(
        self,
        start_at: Optional[int] = None,
        end_at: Optional[int] = None,
        granularity: str = "day",
        system_id: Optional[str] = None,
    ) -> EnphaseProductionResponse:
        """
        Get production telemetry data.

        Args:
            start_at: Start timestamp (Unix). Defaults to 7 days ago.
            end_at: End timestamp (Unix). Defaults to now.
            granularity: Data granularity (15mins, day, week, lifetime)
            system_id: System ID (uses default if not provided)

        Returns:
            Production telemetry response
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("System ID is required")

        # Default to last 7 days
        now = int(time.time())
        if not start_at:
            start_at = now - (7 * 24 * 60 * 60)
        if not end_at:
            end_at = now

        endpoint = f"/api/v4/systems/{sys_id}/telemetry/production_micro"
        params = {
            "start_at": start_at,
            "end_at": end_at,
            "granularity": granularity,
        }

        data = self._make_api_request(endpoint, params)
        return EnphaseProductionResponse(**data)

    def get_production(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: str = "day",
        system_id: Optional[str] = None,
    ) -> SolarProductionData:
        """
        Get processed production data for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
            end_date: End date (YYYY-MM-DD). Defaults to today.
            granularity: Data granularity
            system_id: System ID

        Returns:
            Processed production data
        """
        # Parse dates
        now = datetime.now(self.timezone)
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=self.timezone
            )
        else:
            end_dt = now
            end_date = now.strftime("%Y-%m-%d")

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=self.timezone
            )
        else:
            start_dt = end_dt - timedelta(days=7)
            start_date = start_dt.strftime("%Y-%m-%d")

        # Convert to timestamps
        start_at = int(start_dt.timestamp())
        end_at = int(end_dt.replace(hour=23, minute=59, second=59).timestamp())

        # Fetch data
        response = self.get_production_telemetry(
            start_at=start_at,
            end_at=end_at,
            granularity=granularity,
            system_id=system_id,
        )

        # Calculate totals
        total_wh = sum(
            interval.wh_del or 0 for interval in response.intervals
        )
        total_kwh = total_wh / 1000

        # Calculate average daily production
        days = (end_dt - start_dt).days + 1
        average_daily_kwh = total_kwh / days if days > 0 else None

        return SolarProductionData(
            start_date=start_date,
            end_date=end_date,
            total_wh=total_wh,
            total_kwh=round(total_kwh, 2),
            intervals=len(response.intervals),
            average_daily_kwh=round(average_daily_kwh, 2) if average_daily_kwh else None,
        )

    # =========================================================================
    # Consumption Data
    # =========================================================================

    def get_consumption_telemetry(
        self,
        start_at: Optional[int] = None,
        end_at: Optional[int] = None,
        granularity: str = "day",
        system_id: Optional[str] = None,
    ) -> EnphaseConsumptionResponse:
        """
        Get consumption telemetry data.

        Args:
            start_at: Start timestamp (Unix). Defaults to 7 days ago.
            end_at: End timestamp (Unix). Defaults to now.
            granularity: Data granularity
            system_id: System ID

        Returns:
            Consumption telemetry response
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("System ID is required")

        now = int(time.time())
        if not start_at:
            start_at = now - (7 * 24 * 60 * 60)
        if not end_at:
            end_at = now

        endpoint = f"/api/v4/systems/{sys_id}/telemetry/consumption"
        params = {
            "start_at": start_at,
            "end_at": end_at,
            "granularity": granularity,
        }

        data = self._make_api_request(endpoint, params)
        return EnphaseConsumptionResponse(**data)

    def get_consumption(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: str = "day",
        system_id: Optional[str] = None,
    ) -> SolarConsumptionData:
        """
        Get processed consumption data for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: Data granularity
            system_id: System ID

        Returns:
            Processed consumption data
        """
        now = datetime.now(self.timezone)
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=self.timezone
            )
        else:
            end_dt = now
            end_date = now.strftime("%Y-%m-%d")

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=self.timezone
            )
        else:
            start_dt = end_dt - timedelta(days=7)
            start_date = start_dt.strftime("%Y-%m-%d")

        start_at = int(start_dt.timestamp())
        end_at = int(end_dt.replace(hour=23, minute=59, second=59).timestamp())

        response = self.get_consumption_telemetry(
            start_at=start_at,
            end_at=end_at,
            granularity=granularity,
            system_id=system_id,
        )

        total_wh = sum(
            interval.enwh or 0 for interval in response.intervals
        )
        total_kwh = total_wh / 1000

        days = (end_dt - start_dt).days + 1
        average_daily_kwh = total_kwh / days if days > 0 else None

        return SolarConsumptionData(
            start_date=start_date,
            end_date=end_date,
            total_wh=total_wh,
            total_kwh=round(total_kwh, 2),
            intervals=len(response.intervals),
            average_daily_kwh=round(average_daily_kwh, 2) if average_daily_kwh else None,
        )

    # =========================================================================
    # System Summary
    # =========================================================================

    def get_system_summary_raw(
        self, system_id: Optional[str] = None
    ) -> EnphaseSystemSummary:
        """
        Get raw system summary from Enphase API.

        Args:
            system_id: System ID

        Returns:
            Raw system summary response
        """
        sys_id = system_id or self.system_id
        if not sys_id:
            raise ValueError("System ID is required")

        endpoint = f"/api/v4/systems/{sys_id}/summary"
        data = self._make_api_request(endpoint)
        return EnphaseSystemSummary(**data)

    def get_system_status(self, system_id: Optional[str] = None) -> SystemStatusData:
        """
        Get processed system status.

        Args:
            system_id: System ID

        Returns:
            Processed system status
        """
        summary = self.get_system_summary_raw(system_id)

        return SystemStatusData(
            system_id=summary.system_id,
            current_power_w=summary.current_power,
            current_power_kw=round(summary.current_power / 1000, 2),
            energy_today_kwh=round(summary.energy_today / 1000, 2),
            energy_lifetime_mwh=round(summary.energy_lifetime / 1_000_000, 2),
            system_size_kw=round(summary.size_w / 1000, 2),
            num_panels=summary.modules,
            status=summary.status,
            last_report=datetime.fromtimestamp(
                summary.last_report_at, tz=self.timezone
            ).isoformat(),
            is_producing=summary.current_power > 0,
        )

    # =========================================================================
    # Net Energy Calculation
    # =========================================================================

    def get_net_energy(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: str = "day",
        system_id: Optional[str] = None,
    ) -> NetEnergyData:
        """
        Calculate net energy usage (production - consumption).

        Positive net = exported to grid
        Negative net = imported from grid

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: Data granularity
            system_id: System ID

        Returns:
            Net energy data with production, consumption, and calculations
        """
        # Get both production and consumption
        production = self.get_production(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            system_id=system_id,
        )
        consumption = self.get_consumption(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            system_id=system_id,
        )

        # Calculate net
        net_kwh = production.total_kwh - consumption.total_kwh

        # Calculate percentages
        self_consumption_pct = None
        grid_independence_pct = None

        if production.total_kwh > 0:
            # How much of production was used on-site
            used_onsite = min(production.total_kwh, consumption.total_kwh)
            self_consumption_pct = round((used_onsite / production.total_kwh) * 100, 1)

        if consumption.total_kwh > 0:
            # How much of consumption came from solar
            from_solar = min(production.total_kwh, consumption.total_kwh)
            grid_independence_pct = round(
                (from_solar / consumption.total_kwh) * 100, 1
            )

        return NetEnergyData(
            start_date=production.start_date,
            end_date=production.end_date,
            production_kwh=production.total_kwh,
            consumption_kwh=consumption.total_kwh,
            net_kwh=round(net_kwh, 2),
            self_consumption_pct=self_consumption_pct,
            grid_independence_pct=grid_independence_pct,
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_systems(self) -> list:
        """
        Get list of systems accessible to this account.

        Returns:
            List of system info dictionaries
        """
        endpoint = "/api/v4/systems"
        data = self._make_api_request(endpoint)
        return data.get("systems", [])
