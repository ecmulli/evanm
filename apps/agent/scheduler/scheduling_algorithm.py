#!/usr/bin/env python3
"""
Scheduling Algorithm

Core scheduling logic for assigning tasks to time slots based on priority ranking.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from notion_client import Client
from .time_slots import TimeSlotManager


class TaskScheduler:
    """Handles task scheduling logic."""

    def __init__(
        self,
        notion_client: Client,
        database_id: str,
        time_slot_manager: TimeSlotManager,
        dry_run: bool = False,
    ):
        self.notion_client = notion_client
        self.database_id = database_id
        self.time_slot_manager = time_slot_manager
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

    def fetch_schedulable_tasks(self) -> List[Dict[str, Any]]:
        """
        Fetch all tasks that should be scheduled.

        Criteria:
        - Status NOT IN (Completed, Canceled, Backlog)
        - Auto Schedule = true (or missing/unchecked = default true)
        - Sorted by Rank (ASC) - lower rank = higher priority (scheduled first)

        Returns:
            List of Notion page objects sorted by rank (ascending)
        """
        # Build filter for schedulable tasks
        filter_query = {
            "and": [
                {"property": "Status", "status": {"does_not_equal": "Completed"}},
                {"property": "Status", "status": {"does_not_equal": "Canceled"}},
                {"property": "Status", "status": {"does_not_equal": "Backlog"}},
            ]
        }

        # Query the database
        try:
            response = self.notion_client.databases.query(
                database_id=self.database_id,
                filter=filter_query,
                sorts=[{"property": "Rank", "direction": "ascending"}],
            )

            tasks = response.get("results", [])

            # Filter out tasks where Auto Schedule is explicitly false
            schedulable_tasks = []
            for task in tasks:
                auto_schedule = self._get_checkbox_value(
                    task.get("properties", {}).get("Auto Schedule")
                )

                # If Auto Schedule checkbox doesn't exist or is checked, include it
                # Only exclude if explicitly unchecked
                if auto_schedule is None or auto_schedule is True:
                    schedulable_tasks.append(task)

            self.logger.info(
                f"Fetched {len(schedulable_tasks)} schedulable tasks "
                f"(out of {len(tasks)} active tasks)"
            )

            return schedulable_tasks

        except Exception as e:
            self.logger.error(f"Error fetching tasks: {e}")
            return []

    def extract_task_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant data from a Notion task page."""
        props = task.get("properties", {})

        task_name = self._get_title_text(props.get("Task name"))
        rank = self._get_number_value(props.get("Rank"))
        duration_hrs = self._get_number_value(props.get("Est Duration Hrs")) or 1.0
        due_date = self._get_date_value(props.get("Due date"))
        scheduled_date = self._get_date_value(props.get("Scheduled Date"))
        status = self._get_status_value(props.get("Status"))

        return {
            "id": task.get("id"),
            "task_name": task_name,
            "rank": rank,
            "duration_hrs": duration_hrs,
            "due_date": due_date,
            "scheduled_date": scheduled_date,
            "status": status,
            "url": task.get("url"),
        }

    def schedule_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Schedule all tasks into available time slots.

        Args:
            tasks: List of Notion task pages (already sorted by rank)

        Returns:
            Statistics dict with counts of scheduled, rescheduled, skipped tasks
        """
        stats = {"scheduled": 0, "rescheduled": 0, "skipped": 0, "errors": 0}

        # Clear any previously occupied slots
        self.time_slot_manager.clear_occupied_slots()

        # Generate all available time slots
        all_slots = self.time_slot_manager.generate_work_slots()
        self.logger.info(f"Generated {len(all_slots)} total work hour slots")

        # Process each task in rank order (highest rank first)
        for task in tasks:
            try:
                task_data = self.extract_task_data(task)

                # Skip if no duration (can't schedule)
                if not task_data["duration_hrs"]:
                    self.logger.warning(
                        f"Skipping task '{task_data['task_name']}' - no duration set"
                    )
                    stats["skipped"] += 1
                    continue

                # Check if task needs rescheduling
                needs_scheduling = self._needs_scheduling(task_data)

                if not needs_scheduling:
                    # Task is already scheduled and doesn't need rescheduling
                    # Mark its slots as occupied
                    if task_data["scheduled_date"]:
                        self.time_slot_manager.mark_slots_occupied(
                            task_data["scheduled_date"]["start"],
                            task_data["scheduled_date"]["end"],
                            task_data["id"],
                        )
                    stats["skipped"] += 1
                    continue

                # Find available slots for this task
                available_slots = self.time_slot_manager.get_available_slots(all_slots)

                # Parse due date if present (soft constraint)
                prefer_before = None
                if task_data["due_date"]:
                    # Handle both single datetime and date range dict
                    if isinstance(task_data["due_date"], dict):
                        # If it's a date range, use the start date
                        prefer_before = task_data["due_date"]["start"]
                    else:
                        # If it's a single datetime, use it directly
                        prefer_before = task_data["due_date"]

                # Find a suitable time slot range
                slot_range = self.time_slot_manager.find_available_slot_range(
                    available_slots, task_data["duration_hrs"], prefer_before
                )

                if slot_range:
                    start_time, end_time = slot_range

                    # Determine if this is a new schedule or reschedule
                    is_reschedule = task_data["scheduled_date"] is not None

                    # Update Notion with the scheduled time
                    if self._update_scheduled_date(
                        task_data["id"], start_time, end_time, task_data["task_name"]
                    ):
                        # Mark slots as occupied
                        self.time_slot_manager.mark_slots_occupied(
                            start_time, end_time, task_data["id"]
                        )

                        if is_reschedule:
                            stats["rescheduled"] += 1
                        else:
                            stats["scheduled"] += 1
                    else:
                        stats["errors"] += 1
                else:
                    self.logger.warning(
                        f"No available slots for task '{task_data['task_name']}' "
                        f"({task_data['duration_hrs']}h)"
                    )
                    stats["skipped"] += 1

            except Exception as e:
                self.logger.error(f"Error scheduling task: {e}")
                stats["errors"] += 1

        return stats

    def _needs_scheduling(self, task_data: Dict[str, Any]) -> bool:
        """
        Determine if a task needs (re)scheduling.

        A task needs scheduling if:
        1. It has no scheduled date yet
        2. Its scheduled time has passed but it's not completed
        """
        # No scheduled date = needs scheduling
        if not task_data["scheduled_date"]:
            return True

        # Scheduled time has passed but task isn't completed = needs rescheduling
        now = datetime.now().astimezone()
        scheduled_start = task_data["scheduled_date"]["start"]

        if scheduled_start < now and task_data["status"] != "Completed":
            self.logger.info(
                f"Task '{task_data['task_name']}' passed its scheduled time "
                f"({scheduled_start.strftime('%Y-%m-%d %H:%M')}) - needs rescheduling"
            )
            return True

        # Task is scheduled in the future = no need to reschedule
        return False

    def _update_scheduled_date(
        self, task_id: str, start_time: datetime, end_time: datetime, task_name: str
    ) -> bool:
        """
        Update the Scheduled Date property in Notion with a date range.

        Args:
            task_id: Notion page ID
            start_time: Scheduled start datetime
            end_time: Scheduled end datetime
            task_name: Task name for logging

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would schedule '{task_name}' "
                f"from {start_time.strftime('%Y-%m-%d %H:%M')} "
                f"to {end_time.strftime('%H:%M')}"
            )
            return True

        try:
            # Format datetimes for Notion API
            # Notion expects ISO 8601 format with timezone
            start_iso = start_time.isoformat()
            end_iso = end_time.isoformat()

            # Update the task with scheduled date range
            self.notion_client.pages.update(
                page_id=task_id,
                properties={
                    "Scheduled Date": {"date": {"start": start_iso, "end": end_iso}},
                    "Last Scheduled": {
                        "date": {"start": datetime.now().astimezone().isoformat()}
                    },
                },
            )

            self.logger.info(
                f"✅ Scheduled '{task_name}' "
                f"from {start_time.strftime('%Y-%m-%d %H:%M')} "
                f"to {end_time.strftime('%H:%M')}"
            )

            return True

        except Exception as e:
            self.logger.error(
                f"❌ Failed to update scheduled date for '{task_name}': {e}"
            )
            return False

    # Helper methods for extracting Notion property values

    def _get_title_text(self, prop: Optional[Dict]) -> str:
        """Extract text from title property."""
        if not prop or prop.get("type") != "title":
            return ""
        title_items = prop.get("title", [])
        return title_items[0].get("plain_text", "") if title_items else ""

    def _get_number_value(self, prop: Optional[Dict]) -> Optional[float]:
        """Extract number value."""
        if not prop or prop.get("type") != "number":
            return None
        return prop.get("number")

    def _get_date_value(self, prop: Optional[Dict]) -> Optional[Any]:
        """Extract date value and parse to datetime if present."""
        if not prop or prop.get("type") != "date":
            return None

        date_data = prop.get("date")
        if not date_data:
            return None

        start_str = date_data.get("start")
        end_str = date_data.get("end")

        if start_str:
            try:
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

                # If there's an end date, return both
                if end_str:
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    return {"start": start_dt, "end": end_dt}
                else:
                    # Just a single date
                    return start_dt
            except Exception as e:
                self.logger.warning(f"Error parsing date '{start_str}': {e}")
                return None

        return None

    def _get_status_value(self, prop: Optional[Dict]) -> Optional[str]:
        """Extract status value."""
        if not prop or prop.get("type") != "status":
            return None
        status_data = prop.get("status")
        return status_data.get("name") if status_data else None

    def _get_checkbox_value(self, prop: Optional[Dict]) -> Optional[bool]:
        """Extract checkbox value."""
        if not prop or prop.get("type") != "checkbox":
            return None
        return prop.get("checkbox")
