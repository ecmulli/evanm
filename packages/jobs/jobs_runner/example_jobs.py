"""
Example job implementations.
"""

from typing import Any, Dict, Optional

import requests

from .base_job import BaseJob


class HelloWorldJob(BaseJob):
    """
    Simple example job that prints a hello message.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("hello_world", config)

    def run(self) -> bool:
        """Print a hello message."""
        message = self.config.get("message", "Hello, World!")

        if not self.config.get("enabled", True):
            self.logger.info("Job is disabled, skipping")
            return True

        self.logger.info(f"Message: {message}")
        print(f"[{self.name}] {message}")

        return True


class StatusCheckJob(BaseJob):
    """
    Example job that checks the status of a URL.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("status_check", config)

    def run(self) -> bool:
        """Check the status of a URL."""
        if not self.config.get("enabled", True):
            self.logger.info("Job is disabled, skipping")
            return True

        url = self.config.get("url", "https://httpbin.org/status/200")
        timeout = self.config.get("timeout", 10)

        try:
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                self.logger.info(
                    f"URL {url} is healthy (status: {response.status_code})"
                )
                return True
            else:
                self.logger.warning(
                    f"URL {url} returned status: {response.status_code}"
                )
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to check URL {url}: {e}")
            return False


class FileCleanupJob(BaseJob):
    """
    Example job that cleans up old files from a directory.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("file_cleanup", config)

    def run(self) -> bool:
        """Clean up old files from specified directories."""
        if not self.config.get("enabled", True):
            self.logger.info("Job is disabled, skipping")
            return True

        directories = self.config.get("directories", [])
        max_age_days = self.config.get("max_age_days", 30)

        if not directories:
            self.logger.warning("No directories specified for cleanup")
            return True

        # Implementation would go here
        # This is just a placeholder
        self.logger.info(
            f"Would clean files older than {max_age_days} days from {directories}"
        )

        return True
