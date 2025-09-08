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

    # Server config
    HOST: str = os.getenv("HOST", "0.0.0.0")
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

    VANQUISH_NOTION_API_KEY: str = os.getenv("VANQUISH_NOTION_API_KEY", "")
    VANQUISH_NOTION_DB_ID: str = os.getenv("VANQUISH_NOTION_DB_ID", "")

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

        if cls.VANQUISH_NOTION_API_KEY and cls.VANQUISH_NOTION_DB_ID:
            logger.info("✅ Vanquish workspace configuration found")
        else:
            logger.info("ℹ️  Vanquish workspace not configured (optional)")


config = Config()
