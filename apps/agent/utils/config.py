#!/usr/bin/env python3
"""
Configuration management for the Agent server.
"""

import os

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

    # Notion config (optional — only needed for task creation service)
    HUB_NOTION_API_KEY: str = os.getenv("HUB_NOTION_API_KEY") or os.getenv(
        "PERSONAL_NOTION_API_KEY", ""
    )
    HUB_NOTION_DB_ID: str = os.getenv("HUB_NOTION_DB_ID") or os.getenv(
        "PERSONAL_NOTION_DB_ID", ""
    )

    @classmethod
    def validate_required_env_vars(cls) -> None:
        """Validate that all required environment variables are set."""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
        ]

        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )


config = Config()
