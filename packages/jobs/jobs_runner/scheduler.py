"""
Job scheduler for managing and running scheduled jobs.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import schedule

from .base_job import BaseJob


class JobScheduler:
    """
    Manages and runs scheduled jobs.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.jobs: Dict[str, BaseJob] = {}
        self.scheduled_jobs: List[schedule.Job] = []
        self.logger = logging.getLogger("jobs.scheduler")

        # Configure logging
        self._setup_logging()

        # Register available jobs
        self._register_jobs()

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        log_level = self.config.get("log_level", "INFO")
        log_format = self.config.get(
            "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                # Add file handler if log_file is specified
                *(
                    [logging.FileHandler(self.config["log_file"])]
                    if "log_file" in self.config
                    else []
                ),
            ],
        )

    def _register_jobs(self) -> None:
        """Register all available jobs."""
        # Import and register example jobs
        from .example_jobs import HelloWorldJob, StatusCheckJob

        # Register jobs
        hello_job = HelloWorldJob(self.config.get("hello_job", {}))
        status_job = StatusCheckJob(self.config.get("status_job", {}))

        self.register_job(hello_job)
        self.register_job(status_job)

        # Schedule jobs based on configuration
        self._schedule_jobs()

    def register_job(self, job: BaseJob) -> None:
        """
        Register a job with the scheduler.

        Args:
            job: The job instance to register
        """
        self.jobs[job.name] = job
        self.logger.info(f"Registered job: {job.name}")

    def _schedule_jobs(self) -> None:
        """Schedule registered jobs based on configuration."""
        schedules = self.config.get(
            "schedules",
            {"hello_world": "every(10).seconds", "status_check": "every(1).minutes"},
        )

        for job_name, schedule_str in schedules.items():
            if job_name in self.jobs:
                try:
                    # Parse and create schedule
                    # This is a simple parser - you might want to use a more robust one
                    scheduled_job = self._parse_schedule(schedule_str, job_name)
                    if scheduled_job:
                        self.scheduled_jobs.append(scheduled_job)
                        self.logger.info(f"Scheduled {job_name}: {schedule_str}")
                except Exception as e:
                    self.logger.error(f"Failed to schedule {job_name}: {e}")

    def _parse_schedule(
        self, schedule_str: str, job_name: str
    ) -> Optional[schedule.Job]:
        """
        Parse a schedule string and create a scheduled job.

        Args:
            schedule_str: Schedule string like "every(10).seconds"
            job_name: Name of the job to schedule

        Returns:
            Scheduled job or None if parsing failed
        """
        try:
            # Simple parser for basic schedule formats
            if schedule_str.startswith("every(") and ")." in schedule_str:
                interval_part, unit_part = schedule_str.split(").", 1)
                interval = int(interval_part.replace("every(", ""))

                job = getattr(schedule.every(interval), unit_part)
                return job.do(self._run_job_wrapper, job_name)

        except Exception as e:
            self.logger.error(f"Failed to parse schedule '{schedule_str}': {e}")

        return None

    def _run_job_wrapper(self, job_name: str) -> None:
        """
        Wrapper to run a job by name.

        Args:
            job_name: Name of the job to run
        """
        if job_name in self.jobs:
            self.jobs[job_name].execute()
        else:
            self.logger.error(f"Job not found: {job_name}")

    def run_job(self, job_name: str) -> bool:
        """
        Run a specific job by name.

        Args:
            job_name: Name of the job to run

        Returns:
            True if successful, False otherwise
        """
        if job_name not in self.jobs:
            self.logger.error(f"Job not found: {job_name}")
            return False

        return self.jobs[job_name].execute()

    def run_all(self) -> None:
        """
        Run the scheduler continuously.
        """
        self.logger.info("Starting job scheduler...")
        self.logger.info(f"Registered {len(self.jobs)} jobs")
        self.logger.info(f"Scheduled {len(self.scheduled_jobs)} jobs")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")

    def run_once(self) -> Dict[str, bool]:
        """
        Run all enabled jobs once and exit.

        Returns:
            Dict mapping job names to their success status
        """
        self.logger.info("Running all jobs once...")
        results = {}

        for job_name, job in self.jobs.items():
            if job.config.get("enabled", True):
                self.logger.info(f"Running job: {job_name}")
                results[job_name] = job.execute()
            else:
                self.logger.info(f"Skipping disabled job: {job_name}")
                results[job_name] = None

        return results

    def run_for_duration(self, duration_seconds: int) -> None:
        """
        Run the scheduler for a specific duration then exit.

        Args:
            duration_seconds: How long to run the scheduler
        """
        import time

        start_time = time.time()
        end_time = start_time + duration_seconds

        self.logger.info(f"Running scheduler for {duration_seconds} seconds...")

        try:
            while time.time() < end_time:
                schedule.run_pending()
                time.sleep(1)
            self.logger.info("Scheduler duration completed")
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")

    def list_jobs(self) -> None:
        """List all registered jobs and their status."""
        print(f"\nRegistered Jobs ({len(self.jobs)}):")
        print("-" * 50)

        for job_name, job in self.jobs.items():
            status = job.get_status()
            print(f"• {job_name}")
            print(f"  Last run: {status['last_run'] or 'Never'}")
            print(f"  Last result: {status['last_result'] or 'N/A'}")
            print()

        print(f"Scheduled Jobs ({len(self.scheduled_jobs)}):")
        print("-" * 50)
        for scheduled_job in self.scheduled_jobs:
            print(f"• {scheduled_job}")
        print()
