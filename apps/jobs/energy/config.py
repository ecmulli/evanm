"""Configuration for energy data collection."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # Enphase API
    enphase_client_id: str = ""
    enphase_client_secret: str = ""
    enphase_api_key: str = ""
    enphase_system_id: str = ""
    enphase_redirect_uri: str = "https://api.enphaseenergy.com/oauth/redirect_uri"

    # Database
    database_url: str = ""

    # Timezone for date calculations
    timezone: str = "America/Chicago"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            enphase_client_id=os.getenv("ENPHASE_CLIENT_ID", ""),
            enphase_client_secret=os.getenv("ENPHASE_CLIENT_SECRET", ""),
            enphase_api_key=os.getenv("ENPHASE_API_KEY", ""),
            enphase_system_id=os.getenv("ENPHASE_SYSTEM_ID", ""),
            enphase_redirect_uri=os.getenv(
                "ENPHASE_REDIRECT_URI",
                "https://api.enphaseenergy.com/oauth/redirect_uri",
            ),
            database_url=os.getenv("DATABASE_URL", os.getenv("ENERGY_DATABASE_URL", "")),
            timezone=os.getenv("ENERGY_TIMEZONE", "America/Chicago"),
        )
