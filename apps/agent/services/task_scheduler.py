"""
Task Scheduler Service

Manages automatic scheduling of Notion tasks into calendar time slots.
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from zoneinfo import ZoneInfo

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
        timezone: Optional[str] = None,
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
            timezone: Timezone name (optional - will auto-detect from Notion if not provided)
        """
        self.notion_client = Client(auth=notion_api_key)
        self.database_id = database_id

        # Auto-detect timezone from Notion tasks if not explicitly provided
        if timezone is None:
            timezone = self._detect_timezone_from_notion()

        self.timezone = ZoneInfo(timezone)

        # Initialize time slot manager
        self.time_slot_manager = TimeSlotManager(
            work_start_hour=work_start_hour,
            work_end_hour=work_end_hour,
            slot_duration_minutes=slot_duration_minutes,
            schedule_days_ahead=schedule_days_ahead,
            timezone=timezone,
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

        logger.info("Task Scheduler Service initialized")
        logger.info(
            f"Work hours: {work_start_hour}:00-{work_end_hour}:00, Slot: {slot_duration_minutes}min, Days ahead: {schedule_days_ahead}, TZ: {timezone}"
        )

    def _detect_timezone_from_notion(self) -> str:
        """
        Auto-detect timezone from existing Notion tasks.

        Queries recent tasks and extracts timezone from any date property with time.
        Falls back to UTC if no timezone can be detected.

        Returns:
            Timezone name (IANA format) or "UTC" if detection fails
        """
        try:
            # Query database for any recent tasks
            response = self.notion_client.databases.query(
                database_id=self.database_id, page_size=10
            )

            tasks = response.get("results", [])

            # Try to extract timezone from any date property
            for task in tasks:
                props = task.get("properties", {})

                # Check common date properties
                for prop_name in [
                    "Scheduled Date",
                    "Due date",
                    "Due Date",
                    "Created time",
                    "Last edited time",
                ]:
                    prop_data = props.get(prop_name)
                    if not prop_data:
                        continue

                    # Get date value
                    date_str = None
                    if prop_data.get("type") == "date":
                        date_data = prop_data.get("date")
                        if date_data:
                            date_str = date_data.get("start")
                    elif prop_data.get("type") in ["created_time", "last_edited_time"]:
                        date_str = prop_data.get(prop_data["type"])

                    if not date_str:
                        continue

                    # Parse the datetime and extract timezone
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        if dt.tzinfo:
                            # Convert tzinfo to IANA timezone name
                            tz_name = self._tzinfo_to_name(dt.tzinfo)
                            if tz_name:
                                logger.info(
                                    f"Auto-detected timezone from Notion: {tz_name}"
                                )
                                return tz_name
                    except Exception:
                        continue

            # Check page metadata for timezone
            for task in tasks:
                # created_time and last_edited_time are at the root level
                for time_field in ["created_time", "last_edited_time"]:
                    date_str = task.get(time_field)
                    if date_str:
                        try:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            if dt.tzinfo:
                                tz_name = self._tzinfo_to_name(dt.tzinfo)
                                if tz_name:
                                    logger.info(
                                        f"Auto-detected timezone from Notion metadata: {tz_name}"
                                    )
                                    return tz_name
                        except Exception:
                            continue

            logger.warning(
                "Could not auto-detect timezone from Notion tasks, defaulting to UTC"
            )
            return "UTC"

        except Exception as e:
            logger.warning(f"Error auto-detecting timezone: {e}, defaulting to UTC")
            return "UTC"

    def _tzinfo_to_name(self, tzinfo) -> Optional[str]:
        """
        Convert a tzinfo object to IANA timezone name.

        Args:
            tzinfo: Timezone info from datetime object

        Returns:
            IANA timezone name or None if not convertible
        """
        # If it's already a ZoneInfo, get the key
        if hasattr(tzinfo, "key"):
            return tzinfo.key

        # If it's a fixed offset (like UTC-04:00), try to map to common zones
        if hasattr(tzinfo, "utcoffset"):
            offset = tzinfo.utcoffset(None)
            if offset:
                # Map common offsets to likely timezones
                hours = offset.total_seconds() / 3600
                offset_map = {
                    -8.0: "America/Los_Angeles",
                    -7.0: "America/Denver",
                    -6.0: "America/Chicago",
                    -5.0: "America/New_York",
                    -4.0: "America/New_York",  # EDT
                    0.0: "UTC",
                    1.0: "Europe/London",
                }

                mapped = offset_map.get(hours)
                if mapped:
                    logger.info(f"Mapped UTC offset {hours} to timezone {mapped}")
                    return mapped

        return None

    def run_scheduling_cycle(self) -> Dict[str, int]:
        """
        Run a single scheduling cycle.

        Returns:
            Statistics dictionary with scheduling results
        """
        logger.info("Starting scheduling cycle")
        cycle_start = datetime.now(self.timezone)

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
            cycle_duration = (datetime.now(self.timezone) - cycle_start).total_seconds()

            logger.info(
                f"Cycle complete: scheduled={stats['scheduled']}, "
                f"rescheduled={stats['rescheduled']}, skipped={stats['skipped']}, "
                f"errors={stats['errors']}, duration={cycle_duration:.1f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Error during scheduling cycle: {e}", exc_info=True)
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
