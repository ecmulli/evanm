"""
Base job class for all scheduled jobs.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class BaseJob(ABC):
    """
    Abstract base class for all jobs.

    All jobs should inherit from this class and implement the run() method.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"jobs.{name}")
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[str] = None

    @abstractmethod
    def run(self) -> bool:
        """
        Execute the job.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    def pre_run(self) -> bool:
        """
        Hook called before run().

        Returns:
            bool: True to continue with run(), False to skip
        """
        self.logger.info(f"Starting job: {self.name}")
        return True

    def post_run(self, success: bool, error: Optional[Exception] = None) -> None:
        """
        Hook called after run().

        Args:
            success: Whether the job completed successfully
            error: Exception if one occurred
        """
        self.last_run = datetime.now()

        if success:
            self.logger.info(f"Job completed successfully: {self.name}")
            self.last_result = "success"
        else:
            self.logger.error(f"Job failed: {self.name}")
            if error:
                self.logger.error(f"Error: {error}")
            self.last_result = "failed"

    def execute(self) -> bool:
        """
        Execute the complete job lifecycle.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.pre_run():
                return False

            success = self.run()
            self.post_run(success)
            return success

        except Exception as e:
            self.post_run(False, e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get job status information.

        Returns:
            Dict containing job status information
        """
        return {
            "name": self.name,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
            "config": self.config,
        }
