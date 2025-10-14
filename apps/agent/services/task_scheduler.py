"""
Task Scheduler Service

Manages automatic scheduling of Notion tasks into calendar time slots.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from notion_client import Client
from scheduler.scheduling_algorithm import TaskScheduler
from scheduler.time_slots import TimeSlotManager

logger = logging.getLogger(__name__)


class TaskSchedulerService:
    """Service for managing task scheduling."""

    def __init__(
        self,
        notion_api_key: str,
        database_id: str,
        work_start_hour: int = 9,
        work_end_hour: int = 17,
        slot_duration_minutes: int = 15,
        schedule_days_ahead: int = 7,
    ):
        """
        Initialize the task scheduler service.

        Args:
            notion_api_key: Notion API key
            database_id: Notion database ID
            work_start_hour: Work day start hour (default: 9)
            work_end_hour: Work day end hour (default: 17)
            slot_duration_minutes: Time slot duration in minutes (default: 15)
            schedule_days_ahead: How many days ahead to schedule (default: 7)
        """
        self.notion_client = Client(auth=notion_api_key)
        self.database_id = database_id

        # Initialize time slot manager
        self.time_slot_manager = TimeSlotManager(
            work_start_hour=work_start_hour,
            work_end_hour=work_end_hour,
            slot_duration_minutes=slot_duration_minutes,
            schedule_days_ahead=schedule_days_ahead,
        )

        # Initialize task scheduler
        self.task_scheduler = TaskScheduler(
            notion_client=self.notion_client,
            database_id=self.database_id,
            time_slot_manager=self.time_slot_manager,
            dry_run=False,
        )

        self.last_run: Optional[datetime] = None
        self.last_stats: Optional[Dict] = None

        logger.info("✅ Task Scheduler Service initialized")
        logger.info(f"  Work hours: {work_start_hour}:00 - {work_end_hour}:00")
        logger.info(f"  Slot duration: {slot_duration_minutes} minutes")
        logger.info(f"  Days ahead: {schedule_days_ahead}")

    def run_scheduling_cycle(self) -> Dict[str, int]:
        """
        Run a single scheduling cycle.

        Returns:
            Statistics dictionary with scheduling results
        """
        logger.info("🔄 Starting scheduling cycle...")
        cycle_start = datetime.now().astimezone()

        try:
            # Fetch all schedulable tasks
            tasks = self.task_scheduler.fetch_schedulable_tasks()

            if not tasks:
                logger.info("No tasks to schedule")
                return {"scheduled": 0, "rescheduled": 0, "skipped": 0, "errors": 0}

            # Schedule/reschedule tasks
            stats = self.task_scheduler.schedule_tasks(tasks)

            # Update last run info
            self.last_run = cycle_start
            self.last_stats = stats

            # Log results
            cycle_duration = (datetime.now().astimezone() - cycle_start).total_seconds()

            logger.info("📊 Scheduling cycle complete:")
            logger.info(f"  ✅ Scheduled: {stats['scheduled']}")
            logger.info(f"  🔄 Rescheduled: {stats['rescheduled']}")
            logger.info(f"  ⏭️  Skipped: {stats['skipped']}")
            if stats["errors"] > 0:
                logger.warning(f"  ❌ Errors: {stats['errors']}")
            logger.info(f"  ⏱️  Duration: {cycle_duration:.2f}s")

            return stats

        except Exception as e:
            logger.error(f"❌ Error during scheduling cycle: {e}", exc_info=True)
            return {"scheduled": 0, "rescheduled": 0, "skipped": 0, "errors": 1}

    def get_status(self) -> Dict:
        """Get scheduler status information."""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_stats": self.last_stats or {},
            "work_hours": f"{self.time_slot_manager.work_start_hour}:00 - {self.time_slot_manager.work_end_hour}:00",
            "slot_duration_minutes": self.time_slot_manager.slot_duration_minutes,
            "schedule_days_ahead": self.time_slot_manager.schedule_days_ahead,
        }
