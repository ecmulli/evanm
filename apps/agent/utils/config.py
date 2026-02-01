#!/usr/bin/env python3
"""
Configuration management for the Agent server.
"""

import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the Agent server."""

    # Server config - Hypercorn handles dual-stack binding
    # HOST not needed with Hypercorn's explicit bind configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Authentication
    BEARER_TOKEN: str = os.getenv("BEARER_TOKEN", "")

    # OpenAI config
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Notion config
    HUB_NOTION_API_KEY: str = os.getenv("HUB_NOTION_API_KEY") or os.getenv(
        "PERSONAL_NOTION_API_KEY", ""
    )
    HUB_NOTION_DB_ID: str = os.getenv("HUB_NOTION_DB_ID") or os.getenv(
        "PERSONAL_NOTION_DB_ID", ""
    )

    # Optional external workspace configs
    LIVEPEER_NOTION_API_KEY: str = os.getenv("LIVEPEER_NOTION_API_KEY", "")
    LIVEPEER_NOTION_DB_ID: str = os.getenv("LIVEPEER_NOTION_DB_ID", "")
    LIVEPEER_NOTION_USER_ID: str = os.getenv("LIVEPEER_NOTION_USER_ID", "")

    VANQUISH_NOTION_API_KEY: str = os.getenv("VANQUISH_NOTION_API_KEY", "")
    VANQUISH_NOTION_DB_ID: str = os.getenv("VANQUISH_NOTION_DB_ID", "")

    # Enphase Solar API config
    ENPHASE_CLIENT_ID: str = os.getenv("ENPHASE_CLIENT_ID", "")
    ENPHASE_CLIENT_SECRET: str = os.getenv("ENPHASE_CLIENT_SECRET", "")
    ENPHASE_API_KEY: str = os.getenv("ENPHASE_API_KEY", "")
    ENPHASE_SYSTEM_ID: str = os.getenv("ENPHASE_SYSTEM_ID", "")
    ENPHASE_ACCESS_TOKEN: str = os.getenv("ENPHASE_ACCESS_TOKEN", "")
    ENPHASE_REFRESH_TOKEN: str = os.getenv("ENPHASE_REFRESH_TOKEN", "")
    # Default redirect URI - should be set to your site's callback URL
    # e.g., https://evanm.xyz/settings/enphase/callback
    ENPHASE_REDIRECT_URI: str = os.getenv(
        "ENPHASE_REDIRECT_URI", "https://evanm.xyz/settings/enphase/callback"
    )
    ENPHASE_TOKEN_FILE: str = os.getenv("ENPHASE_TOKEN_FILE", "")
    ENPHASE_TIMEZONE: str = os.getenv("ENPHASE_TIMEZONE", "America/Chicago")

    @classmethod
    def validate_required_env_vars(cls) -> None:
        """Validate that all required environment variables are set."""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("HUB_NOTION_API_KEY", cls.HUB_NOTION_API_KEY),
            ("HUB_NOTION_DB_ID", cls.HUB_NOTION_DB_ID),
        ]

        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Log optional workspace configurations
        import logging

        logger = logging.getLogger(__name__)

        if cls.LIVEPEER_NOTION_API_KEY and cls.LIVEPEER_NOTION_DB_ID:
            logger.info("✅ Livepeer workspace configuration found")
        else:
            logger.info("ℹ️  Livepeer workspace not configured (optional)")

        # Vanquish configuration ignored for now

        # Log Enphase configuration status
        if cls.ENPHASE_CLIENT_ID and cls.ENPHASE_CLIENT_SECRET and cls.ENPHASE_API_KEY:
            logger.info("✅ Enphase Solar API configuration found")
            if cls.ENPHASE_SYSTEM_ID:
                logger.info(f"   System ID: {cls.ENPHASE_SYSTEM_ID}")
            if cls.ENPHASE_ACCESS_TOKEN:
                logger.info("   Access token: configured")
            else:
                logger.info("   Access token: not set (OAuth required)")
        else:
            logger.info("ℹ️  Enphase Solar API not configured (optional)")

    @classmethod
    def is_enphase_configured(cls) -> bool:
        """Check if Enphase API is configured."""
        return bool(
            cls.ENPHASE_CLIENT_ID
            and cls.ENPHASE_CLIENT_SECRET
            and cls.ENPHASE_API_KEY
        )

    @classmethod
    def has_enphase_tokens(cls) -> bool:
        """Check if Enphase OAuth tokens are available."""
        return bool(cls.ENPHASE_ACCESS_TOKEN and cls.ENPHASE_REFRESH_TOKEN)


config = Config()
