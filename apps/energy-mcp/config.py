"""Configuration for the energy MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the same directory as this config file
load_dotenv(Path(__file__).parent / ".env")


@dataclass
class Config:
    database_url: str
    timezone: str

    @classmethod
    def from_env(cls) -> "Config":
        url = os.getenv("ENERGY_DATABASE_URL", os.getenv("DATABASE_URL", ""))
        if not url:
            raise ValueError("ENERGY_DATABASE_URL or DATABASE_URL must be set")
        return cls(
            database_url=url,
            timezone=os.getenv("ENERGY_TIMEZONE", "America/Chicago"),
        )
