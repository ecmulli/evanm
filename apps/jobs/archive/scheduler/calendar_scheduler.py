#!/usr/bin/env python3
"""
Notion Calendar Auto-Scheduler

Main scheduling service that continuously schedules and reschedules tasks
into Notion Calendar based on priority ranking.

Usage:
    python calendar_scheduler.py --mode [continuous|once|test]

Modes:
    continuous - Run continuously with scheduled intervals (default 10 min)
    once - Run scheduling once and exit
    test - Dry run mode (no Notion updates)
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from notion_client import Client
from scheduling_algorithm import TaskScheduler
from time_slots import TimeSlotManager


class CalendarSchedulerService:
    """Main service for automated task scheduling."""

    def __init__(self, dry_run: bool = False):
        """Initialize the scheduler service."""
        self.dry_run = dry_run
        self.logger = self._setup_logging()

        # Load environment variables
        load_dotenv(".env.dev", override=True)
        load_dotenv(".env", override=False)

        # Load configuration
        self._load_config()

        # Initialize Notion client
        self._init_notion_client()

        # Initialize time slot manager
        self.time_slot_manager = TimeSlotManager(
            work_start_hour=self.work_start_hour,
            work_end_hour=self.work_end_hour,
            slot_duration_minutes=self.slot_duration_minutes,
            schedule_days_ahead=self.schedule_days_ahead,
        )

        # Initialize task scheduler
        self.task_scheduler = TaskScheduler(
            notion_client=self.notion_client,
            database_id=self.database_id,
            time_slot_manager=self.time_slot_manager,
            dry_run=self.dry_run,
        )

        if self.dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no changes will be made")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        log_level = os.getenv("SCHEDULER_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, log_level, logging.INFO)

        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

        return logging.getLogger(__name__)

    def _load_config(self):
        """Load configuration from environment variables."""
        # Notion configuration
        self.notion_api_key = os.getenv("LIVEPEER_NOTION_API_KEY")
        self.database_id = os.getenv("LIVEPEER_NOTION_DB_ID")

        if not self.notion_api_key or not self.database_id:
            raise ValueError(
                "Missing required environment variables: "
                "LIVEPEER_NOTION_API_KEY and LIVEPEER_NOTION_DB_ID must be set"
            )

        # Scheduler configuration with defaults
        self.scheduler_interval_minutes = int(
            os.getenv("SCHEDULER_INTERVAL_MINUTES", "10")
        )
        self.work_start_hour = int(os.getenv("WORK_START_HOUR", "9"))
        self.work_end_hour = int(os.getenv("WORK_END_HOUR", "17"))
        self.slot_duration_minutes = int(os.getenv("SLOT_DURATION_MINUTES", "15"))
        self.schedule_days_ahead = int(os.getenv("SCHEDULE_DAYS_AHEAD", "7"))

        self.logger.info("📋 Configuration loaded:")
        self.logger.info(
            f"  Work hours: {self.work_start_hour}:00 - {self.work_end_hour}:00"
        )
        self.logger.info(f"  Slot duration: {self.slot_duration_minutes} minutes")
        self.logger.info(
            f"  Scheduling interval: {self.scheduler_interval_minutes} minutes"
        )
        self.logger.info(f"  Days ahead: {self.schedule_days_ahead}")

    def _init_notion_client(self):
        """Initialize Notion API client."""
        try:
            self.notion_client = Client(auth=self.notion_api_key)
            self.logger.info("✅ Notion client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Notion client: {e}")
            raise

    def run_scheduling_cycle(self) -> dict:
        """
        Run a single scheduling cycle.

        Returns:
            Statistics dictionary with scheduling results
        """
        self.logger.info("🔄 Starting scheduling cycle...")
        cycle_start = datetime.now().astimezone()

        try:
            # Fetch all schedulable tasks
            tasks = self.task_scheduler.fetch_schedulable_tasks()

            if not tasks:
                self.logger.info("No tasks to schedule")
                return {"scheduled": 0, "rescheduled": 0, "skipped": 0, "errors": 0}

            # Schedule/reschedule tasks
            stats = self.task_scheduler.schedule_tasks(tasks)

            # Log results
            cycle_duration = (datetime.now().astimezone() - cycle_start).total_seconds()

            self.logger.info("📊 Scheduling cycle complete:")
            self.logger.info(f"  ✅ Scheduled: {stats['scheduled']}")
            self.logger.info(f"  🔄 Rescheduled: {stats['rescheduled']}")
            self.logger.info(f"  ⏭️  Skipped: {stats['skipped']}")
            if stats["errors"] > 0:
                self.logger.warning(f"  ❌ Errors: {stats['errors']}")
            self.logger.info(f"  ⏱️  Duration: {cycle_duration:.2f}s")

            return stats

        except Exception as e:
            self.logger.error(f"❌ Error during scheduling cycle: {e}", exc_info=True)
            return {"scheduled": 0, "rescheduled": 0, "skipped": 0, "errors": 1}

    def run_continuous(self):
        """Run the scheduler continuously with periodic intervals."""
        self.logger.info(
            f"🚀 Starting continuous scheduler (interval: {self.scheduler_interval_minutes} min)"
        )

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                self.logger.info(f"\n{'=' * 60}")
                self.logger.info(f"Scheduling Cycle #{cycle_count}")
                self.logger.info(f"{'=' * 60}")

                # Run scheduling cycle
                self.run_scheduling_cycle()

                # Wait for next cycle
                self.logger.info(
                    f"\n⏸️  Waiting {self.scheduler_interval_minutes} minutes "
                    f"until next cycle..."
                )
                time.sleep(self.scheduler_interval_minutes * 60)

        except KeyboardInterrupt:
            self.logger.info("\n\n🛑 Scheduler stopped by user")
            self.logger.info(f"Total cycles completed: {cycle_count}")
        except Exception as e:
            self.logger.error(f"❌ Scheduler crashed: {e}", exc_info=True)
            sys.exit(1)

    def run_once(self):
        """Run the scheduler once and exit."""
        self.logger.info("🚀 Running scheduler once...")
        stats = self.run_scheduling_cycle()

        # Exit with error code if there were errors
        if stats.get("errors", 0) > 0:
            sys.exit(1)
        else:
            self.logger.info("✅ Scheduling complete")
            sys.exit(0)


def main():
    """Main entry point for the calendar scheduler."""
    parser = argparse.ArgumentParser(
        description="Notion Calendar Auto-Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run continuously (every 10 minutes)
  python calendar_scheduler.py --mode continuous
  
  # Run once and exit
  python calendar_scheduler.py --mode once
  
  # Test mode (dry run, no Notion updates)
  python calendar_scheduler.py --mode test
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["continuous", "once", "test"],
        default="continuous",
        help="Scheduling mode (default: continuous)",
    )

    args = parser.parse_args()

    # Determine if dry run
    dry_run = args.mode == "test"

    try:
        # Initialize service
        service = CalendarSchedulerService(dry_run=dry_run)

        # Run based on mode
        if args.mode == "continuous":
            service.run_continuous()
        elif args.mode == "once":
            service.run_once()
        elif args.mode == "test":
            service.run_once()  # Test mode runs once in dry-run

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure you have set the required environment variables:")
        print("  - LIVEPEER_NOTION_API_KEY")
        print("  - LIVEPEER_NOTION_DB_ID")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
