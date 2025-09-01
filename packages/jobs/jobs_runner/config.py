"""
Configuration management for jobs package.
"""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


def load_config(dev_mode: bool = False) -> Dict[str, Any]:
    """
    Load configuration from environment variables and config files.

    Args:
        dev_mode: Whether to load development configuration

    Returns:
        Configuration dictionary
    """
    # Load environment variables
    env_file = ".env.dev" if dev_mode else ".env"
    env_path = Path(__file__).parent.parent / env_file

    if env_path.exists():
        load_dotenv(env_path)

    config = {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_file": os.getenv("LOG_FILE"),
        "dev_mode": dev_mode,
        # Job-specific configurations
        "hello_job": {
            "message": os.getenv("HELLO_MESSAGE", "Hello, World!"),
            "enabled": os.getenv("HELLO_JOB_ENABLED", "true").lower() == "true",
        },
        "status_job": {
            "url": os.getenv("STATUS_CHECK_URL", "https://httpbin.org/status/200"),
            "timeout": int(os.getenv("STATUS_CHECK_TIMEOUT", "10")),
            "enabled": os.getenv("STATUS_JOB_ENABLED", "true").lower() == "true",
        },
        # Scheduling configuration
        "schedules": {
            "hello_world": os.getenv("HELLO_SCHEDULE", "every(30).seconds"),
            "status_check": os.getenv("STATUS_SCHEDULE", "every(2).minutes"),
        },
    }

    # Development mode overrides
    if dev_mode:
        config["log_level"] = "DEBUG"
        config["schedules"] = {
            "hello_world": "every(5).seconds",
            "status_check": "every(30).seconds",
        }

    return config
