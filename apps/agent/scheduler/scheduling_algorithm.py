#!/usr/bin/env python3
"""
Scheduling Algorithm

Core scheduling logic for assigning tasks to time slots based on priority ranking.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

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
        user_id: Optional[str] = None,
    ):
        self.notion_client = notion_client
        self.database_id = database_id
        self.time_slot_manager = time_slot_manager
        self.dry_run = dry_run
        self.user_id = user_id
        self.timezone = time_slot_manager.timezone
        self.logger = logging.getLogger(__name__)

    def fetch_schedulable_tasks(self) -> List[Dict[str, Any]]:
        """
        Fetch all tasks that should be scheduled.

        Criteria:
        - Status NOT IN (Completed, Canceled, Backlog)
        - Auto Schedule = true (or missing/unchecked = default true)
        - Assigned to user (if user_id is provided)
        - Sorted by Rank (ASC) - lower rank = higher priority (scheduled first)

        Returns:
            List of Notion page objects sorted by rank (ascending)
        """
        # Build filter for schedulable tasks
        filter_conditions = [
            {"property": "Status", "status": {"does_not_equal": "Completed"}},
            {"property": "Status", "status": {"does_not_equal": "Canceled"}},
            {"property": "Status", "status": {"does_not_equal": "Backlog"}},
        ]

        # Add assignee filter if user_id is provided
        if self.user_id:
            filter_conditions.append(
                {"property": "Assignee", "people": {"contains": self.user_id}}
            )
            self.logger.info(f"Filtering tasks assigned to user: {self.user_id}")

        filter_query = {"and": filter_conditions}

        # Query the database
        try:
            response = self.notion_client.databases.query(
                database_id=self.database_id,
                filter=filter_query,
                sorts=[{"property": "Rank", "direction": "ascending"}],
            )

            tasks = response.get("results", [])

            # Filter out tasks where Auto Schedule is explicitly false
            # Also verify assignee filter if user_id is set
            schedulable_tasks = []
            for task in tasks:
                auto_schedule = self._get_checkbox_value(
                    task.get("properties", {}).get("Auto Schedule")
                )

                # If Auto Schedule checkbox doesn't exist or is checked, include it
                # Only exclude if explicitly unchecked
                if auto_schedule is None or auto_schedule is True:
                    # Double-check assignee if user_id is configured
                    if self.user_id:
                        assignees = self._get_people_value(
                            task.get("properties", {}).get("Assignee")
                        )
                        if not assignees or self.user_id not in assignees:
                            task_name = self._get_title_text(
                                task.get("properties", {}).get("Task name")
                            )
                            self.logger.info(
                                f"Skipping task '{task_name}' - not assigned to user (assignees: {assignees})"
                            )
                            continue

                    schedulable_tasks.append(task)

            self.logger.info(
                f"Found {len(schedulable_tasks)} schedulable tasks (of {len(tasks)} active)"
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
        # Extract "Blocked by" relation - try both possible property names
        blocked_by = self._get_relation_value(props.get("Blocked by")) or self._get_relation_value(props.get("Blocked By"))

        return {
            "id": task.get("id"),
            "task_name": task_name,
            "rank": rank,
            "duration_hrs": duration_hrs,
            "due_date": due_date,
            "scheduled_date": scheduled_date,
            "status": status,
            "blocking_task_ids": blocked_by,
            "url": task.get("url"),
        }

    def _build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]]]:
        """
        Build a dependency graph mapping task IDs to their blocking task IDs.
        
        Args:
            tasks: List of Notion task pages
            
        Returns:
            Tuple of (dependency_graph, task_id_to_data) where:
            - dependency_graph: Dictionary mapping task_id -> list of blocking task IDs
            - task_id_to_data: Dictionary mapping task_id -> extracted task data
        """
        dependency_graph = {}
        task_id_to_data = {}
        
        # First pass: extract all task data and build initial graph
        for task in tasks:
            task_data = self.extract_task_data(task)
            task_id = task_data["id"]
            task_id_to_data[task_id] = task_data
            dependency_graph[task_id] = task_data.get("blocking_task_ids", [])
        
        return dependency_graph, task_id_to_data
    
    def _resolve_all_blocking_tasks(
        self, task_id: str, dependency_graph: Dict[str, List[str]], visited: Optional[set] = None
    ) -> List[str]:
        """
        Resolve all blocking tasks for a given task, including transitive dependencies.
        
        Args:
            task_id: The task ID to resolve dependencies for
            dependency_graph: Dictionary mapping task_id -> list of blocking task IDs
            visited: Set of visited task IDs (to detect cycles)
            
        Returns:
            List of all blocking task IDs (including transitive)
        """
        if visited is None:
            visited = set()
        
        # Detect circular dependencies
        if task_id in visited:
            self.logger.warning(
                f"Circular dependency detected involving task {task_id}. "
                "Scheduling will proceed but dependencies may not be fully respected."
            )
            return []
        
        visited.add(task_id)
        
        blocking_tasks = dependency_graph.get(task_id, [])
        all_blocking = set(blocking_tasks)
        
        # Recursively resolve transitive dependencies
        for blocking_id in blocking_tasks:
            transitive_blocking = self._resolve_all_blocking_tasks(
                blocking_id, dependency_graph, visited.copy()
            )
            all_blocking.update(transitive_blocking)
        
        return list(all_blocking)

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
        self.logger.info(f"Generated {len(all_slots)} work slots")

        # Build dependency graph and task data mapping
        dependency_graph, task_id_to_data = self._build_dependency_graph(tasks)
        
        # Track scheduled tasks by ID for dependency checking
        scheduled_tasks = {}  # task_id -> (start_time, end_time)

        # Process each task in rank order (highest rank first)
        for task in tasks:
            try:
                task_data = self.extract_task_data(task)
                task_id = task_data["id"]

                # Skip if no duration (can't schedule)
                if not task_data["duration_hrs"]:
                    self.logger.warning(
                        f"Skipping task '{task_data['task_name']}' - no duration set"
                    )
                    stats["skipped"] += 1
                    continue

                # Check for blocking tasks
                blocking_task_ids = self._resolve_all_blocking_tasks(
                    task_id, dependency_graph
                )
                
                minimum_start_time = None
                if blocking_task_ids:
                    # Find the latest scheduled end time among blocking tasks
                    blocking_end_times = []
                    unscheduled_blockers = []
                    non_schedulable_blockers = []
                    
                    for blocking_id in blocking_task_ids:
                        if blocking_id in scheduled_tasks:
                            _, blocking_end_time = scheduled_tasks[blocking_id]
                            blocking_end_times.append(blocking_end_time)
                        elif blocking_id in task_id_to_data:
                            # Blocking task exists but hasn't been scheduled yet
                            # We need to schedule blocking tasks first
                            unscheduled_blockers.append(blocking_id)
                        else:
                            # Blocking task is not in the schedulable tasks list
                            # (might be completed, canceled, or not assigned)
                            non_schedulable_blockers.append(blocking_id)
                    
                    # If there are non-schedulable blockers, skip this task
                    if non_schedulable_blockers:
                        blocker_info = []
                        for bid in non_schedulable_blockers:
                            # Try to fetch blocking task info from Notion if possible
                            blocker_info.append(f"task {bid}")
                        self.logger.warning(
                            f"Task '{task_data['task_name']}' is blocked by tasks not in "
                            f"schedulable list: {', '.join(blocker_info)}. Skipping scheduling."
                        )
                        stats["skipped"] += 1
                        continue
                    
                    # If there are unscheduled blockers in the current batch, skip this task for now
                    # It will be rescheduled in a later cycle after blockers are scheduled
                    if unscheduled_blockers:
                        blocker_names = [
                            task_id_to_data.get(bid, {}).get("task_name", bid)
                            for bid in unscheduled_blockers
                        ]
                        self.logger.info(
                            f"Skipping '{task_data['task_name']}' - waiting for blocking tasks "
                            f"to be scheduled first: {', '.join(blocker_names)}"
                        )
                        stats["skipped"] += 1
                        continue
                    
                    # If we have scheduled blocking tasks, use the latest end time
                    if blocking_end_times:
                        minimum_start_time = max(blocking_end_times)
                        self.logger.info(
                            f"Task '{task_data['task_name']}' must start after blocking tasks "
                            f"complete at {minimum_start_time.strftime('%Y-%m-%d %H:%M')}"
                        )

                # Always reschedule based on current priority order
                # This ensures tasks are optimally scheduled when priorities/due dates change

                # Determine if this is a new schedule or reschedule
                is_reschedule = task_data["scheduled_date"] is not None

                if is_reschedule:
                    old_start = task_data["scheduled_date"]["start"]
                    self.logger.info(
                        f"Rescheduling: {task_data['task_name']} "
                        f"(was {old_start.strftime('%m/%d %H:%M')})"
                    )
                else:
                    self.logger.info(f"Scheduling: {task_data['task_name']}")

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
                    available_slots, 
                    task_data["duration_hrs"], 
                    prefer_before,
                    minimum_start_time
                )

                if slot_range:
                    start_time, end_time = slot_range

                    # Update Notion with the scheduled time
                    if self._update_scheduled_date(
                        task_data["id"], start_time, end_time, task_data["task_name"]
                    ):
                        # Mark slots as occupied
                        self.time_slot_manager.mark_slots_occupied(
                            start_time, end_time, task_data["id"]
                        )
                        
                        # Track scheduled task for dependency checking
                        scheduled_tasks[task_id] = (start_time, end_time)

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
                    if minimum_start_time:
                        self.logger.warning(
                            f"  Note: Task requires start time after "
                            f"{minimum_start_time.strftime('%Y-%m-%d %H:%M')} "
                            f"due to blocking tasks"
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
        now = datetime.now(self.timezone)
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
                        "date": {"start": datetime.now(self.timezone).isoformat()}
                    },
                },
            )

            self.logger.info(
                f"Scheduled: {task_name} -> {start_time.strftime('%m/%d %H:%M')}-{end_time.strftime('%H:%M')}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to update scheduled date for '{task_name}': {e}")
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

    def _get_people_value(self, prop: Optional[Dict]) -> List[str]:
        """Extract list of user IDs from people property."""
        if not prop or prop.get("type") != "people":
            return []
        people_list = prop.get("people", [])
        return [person.get("id") for person in people_list if person.get("id")]

    def _get_relation_value(self, prop: Optional[Dict]) -> List[str]:
        """Extract list of page IDs from relation property."""
        if not prop or prop.get("type") != "relation":
            return []
        relation_list = prop.get("relation", [])
        return [relation.get("id") for relation in relation_list if relation.get("id")]
