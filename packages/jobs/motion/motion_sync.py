#!/usr/bin/env python3
"""
Motion ↔ Notion Task Synchronization Script

Bidirectional sync between Motion AI and Notion task databases.
Handles task creation, updates, and field mapping between systems.

Usage:
    python motion_sync.py --mode [full|test|test-real]

Environment Variables Required:
    MOTION_API_KEY - Motion AI API token
    PERSONAL_NOTION_API_KEY - Notion Personal Hub API token
    LIVEPEER_NOTION_API_KEY - Notion Livepeer API token
    VANQUISH_NOTION_API_KEY - Notion Vanquish API token
    PERSONAL_NOTION_DB_ID - Personal hub database ID
    LIVEPEER_NOTION_DB_ID - Livepeer database ID
    VANQUISH_NOTION_DB_ID - Vanquish database ID
    PERSONAL_NOTION_USER_ID - Personal hub user ID
    LIVEPEER_NOTION_USER_ID - Livepeer user ID
    VANQUISH_NOTION_USER_ID - Vanquish user ID
    MOTION_PERSONAL_WORKSPACE_ID - Motion Personal workspace ID
    MOTION_LIVEPEER_WORKSPACE_ID - Motion Livepeer workspace ID
    MOTION_VANQUISH_WORKSPACE_ID - Motion Vanquish workspace ID
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from notion_client import Client


class MotionNotionSync:
    """Handles syncing tasks between Motion AI and Notion databases."""

    def __init__(self, dry_run: bool = False):
        """Initialize the sync client with API credentials."""
        self.dry_run = dry_run
        self.logger = self._setup_logging()

        # Load environment variables
        load_dotenv(".env.dev", override=True)
        load_dotenv(".env", override=False)

        # Initialize API clients
        self._init_motion_client()
        self._init_notion_clients()

        # Motion workspace mappings
        self.motion_workspaces = {
            "Personal": os.getenv("MOTION_PERSONAL_WORKSPACE_ID"),
            "Livepeer": os.getenv("MOTION_LIVEPEER_WORKSPACE_ID"),
            "Vanquish": os.getenv("MOTION_VANQUISH_WORKSPACE_ID"),
        }

        # Motion custom field IDs (tied to specific workspaces)
        self.motion_custom_fields = {
            "Personal": {
                "notion_id": "cfi_4G15DQNV797KHaNzQqsxt3",
                "notion_url": "cfi_RBFEnK3uN2Ho2o8XQXdWfv",
                "notion_last_sync": "cfi_U1o2VDha6sjs3UFwFH8xC1",  # text type
            },
            "Livepeer": {
                "notion_id": "cfi_rLcNg95UQ1Cggz2YAnYjsL",
                "notion_url": "cfi_g85FVuj115igtCPLVCo34t",
                "notion_last_sync": "cfi_1S1Fi4oP3adjT9Ab88U2Ja",  # date type
            },
            "Vanquish": {
                "notion_id": "cfi_vS8mS9agZUaCDMX88usZXq",
                "notion_url": "cfi_eoBPfnbbCWfS3CnbbYCbD4",
                "notion_last_sync": "cfi_r8AYnDjHMH7XCV5GsK7A8c",  # date type
            },
        }

        if self.dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no changes will be made")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        log_level = os.getenv("SYNC_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, log_level, logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def _init_motion_client(self):
        """Initialize Motion API client."""
        self.motion_api_key = os.getenv("MOTION_API_KEY")
        if not self.motion_api_key:
            raise ValueError("MOTION_API_KEY environment variable is required")

        self.motion_base_url = "https://api.usemotion.com/v1"
        self.motion_headers = {
            "X-API-Key": self.motion_api_key,
            "Content-Type": "application/json",
        }

    def _init_notion_clients(self):
        """Initialize Notion API clients for each workspace."""
        # Personal Hub client (main client)
        personal_key = os.getenv("PERSONAL_NOTION_API_KEY")
        if not personal_key:
            raise ValueError("PERSONAL_NOTION_API_KEY is required")
        self.personal_client = Client(auth=personal_key)

        # Workspace-specific clients
        self.workspace_clients = {
            "Personal": self.personal_client,
            "Livepeer": Client(auth=os.getenv("LIVEPEER_NOTION_API_KEY")),
            "Vanquish": Client(auth=os.getenv("VANQUISH_NOTION_API_KEY")),
        }

        # Database IDs
        self.notion_databases = {
            "Personal": os.getenv("PERSONAL_NOTION_DB_ID"),
            "Livepeer": os.getenv("LIVEPEER_NOTION_DB_ID"),
            "Vanquish": os.getenv("VANQUISH_NOTION_DB_ID"),
        }

        # User IDs for filtering
        self.notion_user_ids = {
            "Personal": os.getenv("PERSONAL_NOTION_USER_ID"),
            "Livepeer": os.getenv("LIVEPEER_NOTION_USER_ID"),
            "Vanquish": os.getenv("VANQUISH_NOTION_USER_ID"),
        }

        # Validate required environment variables
        missing_vars = []
        for workspace, db_id in self.notion_databases.items():
            if not db_id:
                missing_vars.append(f"{workspace.upper()}_NOTION_DB_ID")
        for workspace, user_id in self.notion_user_ids.items():
            if not user_id:
                missing_vars.append(f"{workspace.upper()}_NOTION_USER_ID")

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

    # === FIELD MAPPING HELPERS ===

    def get_priority_mapping(self) -> Dict[str, str]:
        """Map priority values between Notion and Motion."""
        return {
            # Notion → Motion
            "Low": "LOW",
            "Medium": "MEDIUM",
            "High": "HIGH",
            "ASAP": "ASAP",
            # Motion → Notion
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "ASAP": "ASAP",
        }

    def get_status_mapping(self) -> Dict[str, str]:
        """Map status values between Notion and Motion."""
        return {
            # Notion → Motion (using actual Notion database status values)
            "Todo": "TODO",
            "Backlog": "TODO",
            "In Progress": "IN_PROGRESS",
            "Completed": "COMPLETED",
            # Motion → Notion (using actual Motion status values)
            "Todo": "Todo",  # Motion uses "Todo", keep as-is for Notion
            "TODO": "Todo",  # Also handle uppercase version
            "IN_PROGRESS": "In Progress",
            "COMPLETED": "Completed",
            "CANCELLED": "Canceled",  # Map cancelled to completed since no direct equivalent
        }

    def convert_hours_to_minutes(self, hours: float) -> int:
        """Convert hours to minutes for Motion duration field."""
        if hours is None or hours == 0:
            return 60  # Default to 60 minutes
        return int(hours * 60)

    def convert_minutes_to_hours(self, minutes: int) -> float:
        """Convert minutes to hours for Notion duration field."""
        if minutes is None or minutes == 0:
            return 1.0  # Default to 1 hour
        return round(minutes / 60, 1)

    def extract_due_date_start(self, notion_date: Dict[str, Any]) -> Optional[str]:
        """Extract start date from Notion date field."""
        if not notion_date:
            return None

        # Notion date can be a range or single date
        start_date = notion_date.get("start")
        if start_date:
            # Convert to ISO format that Motion expects
            return start_date
        return None

    def blocks_to_description(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert Notion blocks to plain text description for Motion."""
        description_parts = []

        for block in blocks:
            block_type = block.get("type", "")

            if block_type == "paragraph":
                text = self._extract_rich_text(
                    block.get("paragraph", {}).get("rich_text", [])
                )
                if text.strip():
                    description_parts.append(text)

            elif block_type == "heading_1":
                text = self._extract_rich_text(
                    block.get("heading_1", {}).get("rich_text", [])
                )
                if text.strip():
                    description_parts.append(f"# {text}")

            elif block_type == "heading_2":
                text = self._extract_rich_text(
                    block.get("heading_2", {}).get("rich_text", [])
                )
                if text.strip():
                    description_parts.append(f"## {text}")

            elif block_type == "heading_3":
                text = self._extract_rich_text(
                    block.get("heading_3", {}).get("rich_text", [])
                )
                if text.strip():
                    description_parts.append(f"### {text}")

            elif block_type == "bulleted_list_item":
                text = self._extract_rich_text(
                    block.get("bulleted_list_item", {}).get("rich_text", [])
                )
                if text.strip():
                    description_parts.append(f"• {text}")

            elif block_type == "numbered_list_item":
                text = self._extract_rich_text(
                    block.get("numbered_list_item", {}).get("rich_text", [])
                )
                if text.strip():
                    description_parts.append(f"1. {text}")

        return "\n\n".join(description_parts) if description_parts else ""

    def _extract_rich_text(self, rich_text_array: List[Dict[str, Any]]) -> str:
        """Extract plain text from Notion rich text array."""
        text_parts = []
        for item in rich_text_array:
            text_parts.append(item.get("plain_text", ""))
        return "".join(text_parts)

    # === MOTION API METHODS ===

    def motion_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Make authenticated request to Motion API with retry logic."""
        # Handle beta endpoints that use different base URL
        if endpoint.startswith("/beta/") or endpoint.startswith("beta/"):
            url = f"https://api.usemotion.com/{endpoint.lstrip('/')}"
        else:
            url = f"{self.motion_base_url}/{endpoint.lstrip('/')}"

        for attempt in range(max_retries + 1):
            try:
                # Log the Motion API call
                self.logger.info(
                    f"🔗 Motion API: {method.upper()} {endpoint} (attempt {attempt + 1})"
                )

                if method.upper() == "GET":
                    response = requests.get(url, headers=self.motion_headers)
                elif method.upper() == "POST":
                    response = requests.post(
                        url, headers=self.motion_headers, json=data
                    )
                elif method.upper() == "PATCH":
                    response = requests.patch(
                        url, headers=self.motion_headers, json=data
                    )
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=self.motion_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()

                # Log successful response
                self.logger.info(
                    f"✅ Motion API: {method.upper()} {endpoint} → {response.status_code}"
                )

                # Small delay between successful requests to be respectful
                if attempt == 0:  # Only delay on first attempt (not retries)
                    time.sleep(0.1)  # 100ms - just enough to avoid hammering

                return response.json() if response.content else {}

            except requests.exceptions.RequestException as e:
                if (
                    hasattr(e, "response")
                    and e.response is not None
                    and e.response.status_code == 429
                ):
                    # Rate limit hit - implement exponential backoff
                    if attempt < max_retries:
                        wait_time = 2**attempt * 10  # 10s, 20s, 40s
                        self.logger.warning(
                            f"⚠️ Motion API Rate limit hit on {method.upper()} {endpoint} (attempt {attempt + 1}/{max_retries + 1}), waiting {wait_time}s before retry..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(
                            f"Rate limit exceeded after {max_retries + 1} attempts"
                        )
                        raise
                elif (
                    hasattr(e, "response")
                    and e.response is not None
                    and e.response.status_code in [502, 503, 504]
                ):
                    # Server errors - retry with shorter backoff
                    if attempt < max_retries:
                        wait_time = 2**attempt * 2  # 2s, 4s, 8s
                        self.logger.warning(
                            f"Server error {e.response.status_code} (attempt {attempt + 1}/{max_retries + 1}), waiting {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(
                            f"Server error after {max_retries + 1} attempts"
                        )
                        raise
                else:
                    # Other errors - don't retry
                    self.logger.error(f"Motion API request failed: {e}")
                    if hasattr(e, "response") and e.response is not None:
                        self.logger.error(f"Response: {e.response.text}")
                    raise

    def get_motion_tasks(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all tasks from Motion workspace, including completed ones."""
        try:
            # Use includeAllStatuses=true to get tasks across all statuses, including completed
            response = self.motion_request(
                "GET", f"tasks?workspaceId={workspace_id}&includeAllStatuses=true"
            )
            return response.get("tasks", [])
        except Exception as e:
            self.logger.error(
                f"Failed to get Motion tasks for workspace {workspace_id}: {e}"
            )
            return []

    def get_motion_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a single Motion task by ID."""
        try:
            return self.motion_request("GET", f"tasks/{task_id}")
        except Exception as e:
            self.logger.warning(f"Failed to get Motion task {task_id}: {e}")
            return None

    def create_motion_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new task in Motion."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would create Motion task: {task_data.get('name', 'Unknown')}"
            )
            return "dry-run-motion-id"

        try:
            response = self.motion_request("POST", "tasks", task_data)
            task_id = response.get("id")
            self.logger.info(
                f"✅ Created Motion task: {task_data.get('name', 'Unknown')} (ID: {task_id})"
            )
            return task_id
        except Exception as e:
            self.logger.error(f"Failed to create Motion task: {e}")
            return None

    def update_motion_task(
        self, task_id: str, updates: Dict[str, Any], workspace: str = None
    ) -> bool:
        """Update an existing Motion task."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would update Motion task {task_id} with: {list(updates.keys())}"
            )
            return True

        try:
            self.motion_request("PATCH", f"tasks/{task_id}", updates)
            self.logger.info(f"✅ Updated Motion task {task_id}")

            # Note: Using property-based change detection instead of timestamps

            return True
        except requests.exceptions.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                # Task not found - let the caller handle recreation
                raise
            else:
                self.logger.error(f"Failed to update Motion task {task_id}: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to update Motion task {task_id}: {e}")
            return False

    def set_motion_custom_fields(
        self, task_id: str, workspace: str, notion_id: str, notion_url: str
    ) -> bool:
        """Set custom field values for a Motion task."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would set custom fields for Motion task {task_id}"
            )
            return True

        try:
            custom_fields = self.motion_custom_fields[workspace]

            # Set Notion ID custom field
            notion_id_data = {
                "customFieldInstanceId": custom_fields["notion_id"],
                "value": {"type": "text", "value": notion_id},
            }
            self.motion_request(
                "POST", f"/beta/custom-field-values/task/{task_id}", notion_id_data
            )

            # Set Notion URL custom field
            notion_url_data = {
                "customFieldInstanceId": custom_fields["notion_url"],
                "value": {"type": "url", "value": notion_url},
            }
            self.motion_request(
                "POST", f"/beta/custom-field-values/task/{task_id}", notion_url_data
            )

            self.logger.info(f"✅ Set custom fields for Motion task {task_id}")
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to set custom fields for Motion task {task_id}: {e}"
            )
            return False

    def set_motion_notion_sync_time(
        self, task_id: str, sync_time: str, workspace: str
    ) -> bool:
        """Set Motion custom field for Notion Last Sync timestamp."""
        if self.dry_run:
            return True  # Skip in dry run

        try:
            # Check if we have the custom field ID for this workspace
            custom_fields = self.motion_custom_fields.get(workspace, {})
            notion_sync_field_id = custom_fields.get("notion_last_sync")

            if not notion_sync_field_id:
                self.logger.debug(
                    f"Notion Last Sync custom field not configured for {workspace} workspace"
                )
                return True  # Skip if field not configured

            # Use POST approach to set custom field value
            # Handle both text and date types (Personal is text, others are date)
            if workspace == "Personal":
                # Text type - just pass the ISO string
                value_data = {"type": "text", "value": sync_time}
            else:
                # Date type - Motion expects date format
                value_data = {"type": "date", "value": sync_time}

            sync_data = {
                "customFieldInstanceId": notion_sync_field_id,
                "value": value_data,
            }

            # Debug: Log what we're sending to Motion
            self.logger.info(f"🔍 DEBUG - Setting custom field: {sync_data}")

            self.motion_request(
                "POST", f"/beta/custom-field-values/task/{task_id}", sync_data
            )
            self.logger.info(
                f"✅ Set Notion Last Sync time for Motion task {task_id} to {sync_time}"
            )
            return True
        except Exception as e:
            # Don't fail the whole sync if we can't set sync time - just log and continue
            self.logger.debug(
                f"Could not set Notion Last Sync time for Motion task {task_id}: {e}"
            )
            return True  # Return True so sync continues

    # === NOTION API METHODS ===

    def get_notion_tasks(self, workspace: str) -> List[Dict[str, Any]]:
        """Get all tasks from Notion database for a workspace."""
        client = self.workspace_clients[workspace]
        database_id = self.notion_databases[workspace]
        user_id = self.notion_user_ids[workspace]

        # For Personal hub, skip assignee filtering since all tasks are implicitly yours
        if workspace == "Personal":
            filter_conditions = {
                "and": [
                    {"property": "Status", "status": {"does_not_equal": "Backlog"}},
                    {
                        "property": "Status",
                        "status": {"does_not_equal": "Completed"},
                    },
                    {
                        "property": "Status",
                        "status": {"does_not_equal": "Canceled"},
                    },
                ]
            }
        else:
            # For external workspaces, filter by assignee
            filter_conditions = {
                "and": [
                    {
                        "property": "Assignee",
                        "people": {"contains": user_id},
                    },
                    {
                        "and": [
                            {
                                "property": "Status",
                                "status": {"does_not_equal": "Backlog"},
                            },
                            {
                                "property": "Status",
                                "status": {"does_not_equal": "Completed"},
                            },
                            {
                                "property": "Status",
                                "status": {"does_not_equal": "Canceled"},
                            },
                        ]
                    },
                ]
            }

        try:
            response = client.databases.query(
                database_id=database_id, filter=filter_conditions
            )
            return response.get("results", [])
        except Exception as e:
            self.logger.error(f"Failed to get Notion tasks for {workspace}: {e}")
            return []

    def extract_notion_task_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract task data from Notion page."""
        props = page.get("properties", {})

        # Helper functions for property extraction
        def get_title(prop):
            if not prop:
                return ""
            title_items = prop.get("title", [])
            return title_items[0].get("plain_text", "") if title_items else ""

        def get_text(prop):
            if not prop:
                return ""
            rich_text = prop.get("rich_text", [])
            return rich_text[0].get("plain_text", "") if rich_text else ""

        def get_select(prop):
            if not prop:
                return ""
            select = prop.get("select")
            return select.get("name", "").strip() if select else ""

        def get_status(prop):
            if not prop:
                return ""
            status = prop.get("status")
            return status.get("name", "").strip() if status else ""

        def get_number(prop):
            if not prop:
                return None
            return prop.get("number")

        def get_date(prop):
            if not prop:
                return None
            return prop.get("date")

        return {
            "id": page.get("id"),
            "task_name": get_title(props.get("Task name")),
            "status": get_status(
                props.get("Status")
            ),  # Use get_status for Status property
            "workspace": get_select(props.get("Workspace")),
            "est_duration_hrs": get_number(props.get("Est Duration Hrs")),
            "actual_duration_hrs": get_number(props.get("Actual Duration")),
            "due_date": get_date(props.get("Due date")),
            "priority": get_select(props.get("Priority")),
            "description": get_text(props.get("Description")),
            "motion_id": get_text(props.get("Motion ID")),
            "updated_at": page.get("last_edited_time"),
            "url": page.get("url"),
        }

    # === SYNC LOGIC ===

    def sync_motion_to_notion(
        self,
        workspace: str,
        max_tasks: Optional[int] = None,
        cached_motion_tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, int]:
        """Sync ONLY completed tasks from Motion to Notion (simplified architecture)."""
        stats = {"updated": 0, "skipped": 0, "errors": 0}

        motion_workspace_id = self.motion_workspaces[workspace]
        if not motion_workspace_id:
            self.logger.error(f"No Motion workspace ID configured for {workspace}")
            return stats

        # Use cached Motion tasks if provided, otherwise fetch them
        if cached_motion_tasks is not None:
            motion_tasks = cached_motion_tasks
            self.logger.info(
                f"📊 Using cached Motion tasks ({len(motion_tasks)} total)"
            )
        else:
            motion_tasks = self.get_motion_tasks(motion_workspace_id)

        # DEBUG: Print all Motion tasks
        self.logger.info(f"🔍 DEBUG: Total Motion tasks returned: {len(motion_tasks)}")
        for i, task in enumerate(motion_tasks[:10]):  # Show first 10 tasks
            task_name = task.get("name", "Unknown")
            task_status = task.get("status", {})
            status_name = (
                task_status.get("name", "No Status")
                if isinstance(task_status, dict)
                else task_status
            )
            notion_id = (
                task.get("customFieldValues", {})
                .get("Notion ID", {})
                .get("value", "No Notion ID")
            )
            self.logger.info(
                f"🔍 DEBUG: Task {i+1}: '{task_name}' | Status: '{status_name}' | Notion ID: {notion_id}"
            )

        # Filter to only COMPLETED tasks that have Notion ID custom field
        completed_tasks = []
        custom_fields = self.motion_custom_fields[workspace]

        for task in motion_tasks:
            custom_field_values = task.get("customFieldValues", {})
            notion_id_field = custom_field_values.get("Notion ID")

            # DEBUG: Log all tasks with Notion IDs and their statuses
            if notion_id_field and notion_id_field.get("value"):
                task_name = task.get("name", "Unknown")
                task_status = task.get("status", {})
                status_name = (
                    task_status.get("name", "No Status")
                    if isinstance(task_status, dict)
                    else task_status
                )
                self.logger.info(
                    f"🔍 DEBUG: Task '{task_name}' has status '{status_name}'"
                )

            # Only process tasks that are completed AND have Notion ID
            task_status = task.get("status", {})
            if (
                notion_id_field
                and notion_id_field.get("value")
                and isinstance(task_status, dict)
                and task_status.get("name", "").lower() == "completed"
            ):
                completed_tasks.append(task)

        # Apply task limit for test mode
        if max_tasks is not None:
            original_count = len(completed_tasks)
            # Sort by Notion ID for consistent ordering across sync directions
            completed_tasks = sorted(
                completed_tasks,
                key=lambda t: t["customFieldValues"]["Notion ID"]["value"],
            )
            completed_tasks = completed_tasks[:max_tasks]
            self.logger.info(
                f"📊 Found {original_count} completed Motion tasks in {workspace}, limiting to {len(completed_tasks)} for testing"
            )
        else:
            self.logger.info(
                f"📊 Found {len(completed_tasks)} completed Motion tasks in {workspace}"
            )

        processed_notion_ids = []
        for motion_task in completed_tasks:
            try:
                notion_id = motion_task["customFieldValues"]["Notion ID"]["value"]
                processed_notion_ids.append(notion_id)

                # Get current Notion task
                try:
                    notion_page = self.workspace_clients[workspace].pages.retrieve(
                        page_id=notion_id
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Notion task {notion_id} not found, skipping completed Motion task {motion_task['id']}"
                    )
                    stats["skipped"] += 1
                    continue

                # Update Notion with completion status and actual duration
                if self._update_notion_from_completed_motion(
                    motion_task, notion_id, workspace
                ):
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1

            except Exception as e:
                self.logger.error(
                    f"Error processing completed Motion task {motion_task.get('id', 'unknown')}: {e}"
                )
                stats["errors"] += 1

        # Track first processed task for test mode coordination
        if processed_notion_ids:
            stats["processed_notion_id"] = processed_notion_ids[0]
        stats["processed_notion_ids"] = processed_notion_ids

        # Check for deleted Motion tasks and mark as canceled in Notion
        self._handle_deleted_motion_tasks(
            workspace, processed_notion_ids, cached_motion_tasks
        )

        self.logger.info(f"📊 {workspace} Motion → Notion sync complete: {stats}")
        return stats

    def _handle_deleted_motion_tasks(
        self,
        workspace: str,
        processed_notion_ids: List[str],
        cached_motion_tasks: Optional[List[Dict[str, Any]]] = None,
    ):
        """Mark Notion tasks as 'Canceled' if their Motion tasks have been deleted."""
        try:
            # Create lookup set of Motion IDs from cached tasks for fast existence checking
            if cached_motion_tasks:
                existing_motion_ids = {
                    task.get("id") for task in cached_motion_tasks if task.get("id")
                }
            else:
                existing_motion_ids = set()

            # Get all Notion tasks with Motion IDs
            notion_tasks = self.get_notion_tasks(workspace)

            for notion_task in notion_tasks:
                notion_data = self.extract_notion_task_data(notion_task)
                motion_id = notion_data.get("motion_id")
                notion_id = notion_data.get("id")

                # Skip if no Motion ID or already processed (means Motion task exists)
                if not motion_id or notion_id in processed_notion_ids:
                    continue

                # Check if Motion task still exists using cached data
                if motion_id not in existing_motion_ids:
                    # Motion task was deleted, mark as canceled in Notion
                    try:
                        update_data = {
                            "Status": {"status": {"name": "Canceled"}},
                            "Motion ID": {"rich_text": []},  # Clear the Motion ID
                        }

                        self.workspace_clients[workspace].pages.update(
                            page_id=notion_id, properties=update_data
                        )

                        self.logger.info(
                            f"🗑️ Marked as CANCELED - Motion task deleted: {notion_data['task_name']}"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to mark task as canceled: {e}")

        except Exception as e:
            self.logger.error(f"Error checking for deleted Motion tasks: {e}")

    def _update_notion_from_completed_motion(
        self, motion_task: Dict[str, Any], notion_id: str, workspace: str
    ) -> bool:
        """Update Notion task with ONLY status=Completed and actual duration from Motion."""
        try:
            # Extract actual duration from Motion (in minutes)
            motion_duration_minutes = motion_task.get("duration", 60)  # Default 60 min
            actual_duration_hours = motion_duration_minutes / 60.0

            # Get current Notion status to check if already completed
            notion_page = self.workspace_clients[workspace].pages.retrieve(
                page_id=notion_id
            )
            notion_data = self.extract_notion_task_data(notion_page)
            current_status = notion_data.get("status", "")

            # Skip if already completed in Notion
            if current_status == "Completed":
                self.logger.info(
                    f"✅ SKIPPING - Already completed in Notion: {notion_data['task_name']}"
                )
                return False

            # Update Notion with completion status and actual duration
            update_data = {
                "Status": {"status": {"name": "Completed"}},
                "Actual Duration": {"number": actual_duration_hours},
            }

            self.workspace_clients[workspace].pages.update(
                page_id=notion_id, properties=update_data
            )

            self.logger.info(
                f"✅ Marked as completed in Notion: {notion_data['task_name']} (actual: {actual_duration_hours}h)"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to update Notion from completed Motion task: {e}"
            )
            return False

    def _update_notion_from_motion(
        self, motion_task: Dict[str, Any], notion_id: str, workspace: str
    ) -> bool:
        """Update Notion task with Motion task data."""
        try:
            # Compare Motion's updatedTime vs Notion's motion_last_sync_time (avoid infinite loops)
            motion_updated = motion_task.get("updatedTime")

            if motion_updated:
                try:
                    motion_dt = datetime.fromisoformat(
                        motion_updated.replace("Z", "+00:00")
                    )

                    # Get the Notion task to check motion_last_sync_time
                    client = self.workspace_clients[workspace]
                    notion_page = client.pages.retrieve(page_id=notion_id)

                    # Get motion_last_sync_time from Notion properties
                    field_mapping = self.get_workspace_field_mapping(workspace)
                    motion_sync_field = field_mapping.get(
                        "Motion Last Sync", "Motion Last Sync"
                    )
                    motion_sync_prop = notion_page["properties"].get(
                        motion_sync_field, {}
                    )

                    # Check if there are actual content differences worth syncing
                    if not self.has_meaningful_changes(
                        motion_task, notion_page, workspace
                    ):
                        self.logger.info(
                            f"✅ SKIPPING - No meaningful changes in Motion task: {motion_task['name']}"
                        )
                        return True  # Not an error, just no update needed

                    self.logger.info(
                        f"🔄 UPDATING - Found meaningful changes in Motion task: {motion_task['name']}"
                    )
                except Exception as e:
                    self.logger.debug(
                        f"Error comparing sync timestamps, proceeding with update: {e}"
                    )

            # Map Motion fields back to Notion
            priority_map = self.get_priority_mapping()
            status_map = self.get_status_mapping()

            # Build Notion updates
            updates = {}

            # Update status if changed
            motion_status = motion_task.get("status", {}).get("name", "")
            notion_status = status_map.get(motion_status, motion_status)
            if notion_status:
                updates["Status"] = {"status": {"name": notion_status}}

            # Update priority if changed
            motion_priority = motion_task.get("priority", "")
            notion_priority = priority_map.get(motion_priority, motion_priority)
            if notion_priority:
                updates["Priority"] = {"select": {"name": notion_priority}}

            # Update duration (convert minutes back to hours)
            motion_duration = motion_task.get("duration", 0)
            notion_duration = self.convert_minutes_to_hours(motion_duration)
            updates["Est Duration Hrs"] = {"number": notion_duration}

            # Update due date if present
            motion_due_date = motion_task.get("dueDate")
            if motion_due_date:
                updates["Due date"] = {"date": {"start": motion_due_date}}

            if self.dry_run:
                self.logger.info(
                    f"🧪 DRY RUN: Would update Notion task '{motion_task['name']}' with Motion changes: {list(updates.keys())}"
                )
                return True

            if updates:
                # Apply field mapping for workspace-specific property names
                field_mapping = self.get_workspace_field_mapping(workspace)
                mapped_updates = {}
                for notion_field, value in updates.items():
                    mapped_field = field_mapping.get(notion_field, notion_field)
                    mapped_updates[mapped_field] = value

                self.workspace_clients[workspace].pages.update(
                    page_id=notion_id, properties=mapped_updates
                )
                self.logger.info(
                    f"✅ Updated Notion task from Motion: {motion_task['name']}"
                )

                # Set "Motion Last Sync" timestamp to track when we last synced from Motion
                current_time = datetime.now(timezone.utc).isoformat()
                self.set_notion_motion_sync_time(notion_id, current_time, workspace)

                return True
            else:
                self.logger.info(
                    f"📝 No changes needed for Notion task: {motion_task['name']}"
                )
                return True

        except Exception as e:
            self.logger.error(
                f"Failed to update Notion task {notion_id} from Motion: {e}"
            )
            return False

    def get_workspace_field_mapping(self, workspace: str) -> Dict[str, str]:
        """Get field name mappings for different workspaces."""
        # Map standard field names to workspace-specific names
        if workspace == "Livepeer":
            return {
                "Est Duration Hrs": "Est Duration Hrs",
                "Due date": "Due date",
                "Priority": "Priority",
                "Status": "Status",
                "Motion Last Sync": "Motion Last Sync",
            }
        elif workspace == "Vanquish":
            return {
                "Est Duration Hrs": "Est. Duration Hrs",
                "Due date": "Due date",  # Personal hub uses "Due date" (lowercase 'd')
                "Priority": "Priority",
                "Status": "Status",
                "Motion Last Sync": "Motion Last Sync",
            }
        else:  # Personal
            return {
                "Est Duration Hrs": "Est Duration Hrs",
                "Due date": "Due date",  # Personal hub uses "Due date" (lowercase 'd')
                "Priority": "Priority",
                "Status": "Status",
                "Motion Last Sync": "Motion Last Sync",
            }

    def sync_notion_to_motion(
        self,
        workspace: str,
        max_tasks: Optional[int] = None,
        skip_notion_ids: Optional[List[str]] = None,
        cached_motion_tasks_by_id: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, int]:
        """Sync tasks from Notion to Motion."""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        notion_tasks = self.get_notion_tasks(workspace)
        motion_workspace_id = self.motion_workspaces[workspace]

        if not motion_workspace_id:
            self.logger.error(f"No Motion workspace ID configured for {workspace}")
            return stats

        # Limit tasks for testing if specified
        if max_tasks is not None:
            # Sort by Notion ID for consistent ordering across sync directions
            notion_tasks = sorted(notion_tasks, key=lambda t: t["id"])
            notion_tasks = notion_tasks[:max_tasks]
            self.logger.info(
                f"📊 Found {len(self.get_notion_tasks(workspace))} Notion tasks in {workspace}, limiting to {len(notion_tasks)} for testing"
            )
        else:
            self.logger.info(
                f"📊 Found {len(notion_tasks)} Notion tasks in {workspace}"
            )

        for notion_task in notion_tasks:
            notion_data = self.extract_notion_task_data(notion_task)
            notion_id = notion_data.get("id")
            motion_id = notion_data.get("motion_id")

            # Skip tasks that were just processed by Motion → Notion sync
            if skip_notion_ids and notion_id in skip_notion_ids:
                self.logger.info(
                    f"⏭️ SKIPPING - Task already processed by Motion → Notion: {notion_data['task_name']}"
                )
                stats["skipped"] += 1
                continue

            if motion_id:
                # Update existing Motion task
                update_result = self._update_motion_from_notion(
                    motion_id, notion_data, workspace, cached_motion_tasks_by_id
                )
                if update_result is True:
                    stats["updated"] += 1
                elif update_result is False:
                    stats["skipped"] += 1
                else:
                    stats["errors"] += 1
            else:
                # Create new Motion task
                if self._create_motion_from_notion(notion_data, workspace):
                    stats["created"] += 1
                else:
                    stats["errors"] += 1

        self.logger.info(f"📊 {workspace} → Motion sync complete: {stats}")
        return stats

    def sync_specific_notion_task(
        self,
        workspace: str,
        notion_id: str,
        cached_motion_tasks_by_id: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, int]:
        """Sync a specific Notion task to Motion (used in test mode for coordination)."""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        try:
            # Get the specific Notion task
            notion_page = self.workspace_clients[workspace].pages.retrieve(
                page_id=notion_id
            )
            notion_data = self.extract_notion_task_data(notion_page)
            motion_id = notion_data.get("motion_id")

            self.logger.info(
                f"📊 Processing specific Notion task: {notion_data['task_name']}"
            )

            if motion_id:
                # Update existing Motion task
                update_result = self._update_motion_from_notion(
                    motion_id, notion_data, workspace, cached_motion_tasks_by_id
                )
                if update_result is True:
                    stats["updated"] += 1
                elif update_result is False:
                    stats["skipped"] += 1
                else:
                    stats["errors"] += 1
            else:
                # Create new Motion task
                if self._create_motion_from_notion(notion_data, workspace):
                    stats["created"] += 1
                else:
                    stats["errors"] += 1

        except Exception as e:
            self.logger.error(f"Error processing specific Notion task {notion_id}: {e}")
            stats["errors"] += 1

        self.logger.info(f"📊 {workspace} → Motion specific sync complete: {stats}")
        return stats

    def _create_motion_from_notion(
        self, notion_data: Dict[str, Any], workspace: str
    ) -> bool:
        """Create a new Motion task from Notion data."""
        try:
            # Get Notion blocks for description
            blocks = []
            if notion_data["id"]:
                blocks_response = self.workspace_clients[
                    workspace
                ].blocks.children.list(block_id=notion_data["id"])
                blocks = blocks_response.get("results", [])

            # Build Motion task data
            priority_map = self.get_priority_mapping()
            status_map = self.get_status_mapping()

            motion_task_data = {
                "workspaceId": self.motion_workspaces[workspace],
                "name": notion_data["task_name"],
                "description": self.blocks_to_description(blocks),
                "priority": priority_map.get(notion_data["priority"], "MEDIUM"),
                "status": status_map.get(notion_data["status"], "TODO"),
                "duration": self.convert_hours_to_minutes(
                    notion_data["est_duration_hrs"]
                ),
            }

            # Add due date (required for auto-scheduled tasks)
            if notion_data["due_date"]:
                due_date = self.extract_due_date_start(notion_data["due_date"])
                if due_date:
                    motion_task_data["dueDate"] = due_date
                else:
                    # Default due date if none provided but auto-scheduling is enabled
                    default_due = (datetime.now() + timedelta(days=7)).strftime(
                        "%Y-%m-%d"
                    )
                    motion_task_data["dueDate"] = default_due
            else:
                # Default due date for auto-scheduled tasks
                default_due = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                motion_task_data["dueDate"] = default_due

            # Custom fields will be set after task creation via separate API call

            # Set auto-scheduling for work hours
            motion_task_data["autoScheduled"] = {"schedule": "Work Hours"}

            # Create Motion task
            motion_id = self.create_motion_task(motion_task_data)

            if motion_id:
                # Set custom fields for back-reference to Notion
                if self.set_motion_custom_fields(
                    motion_id, workspace, notion_data["id"], notion_data["url"]
                ):
                    # Update Notion with Motion ID
                    if not self.dry_run:
                        self._update_notion_motion_id(
                            notion_data["id"], motion_id, workspace
                        )
                    return True
                else:
                    return False

            return False

        except Exception as e:
            self.logger.error(f"Failed to create Motion task from Notion: {e}")
            return False

    def _update_motion_from_notion(
        self,
        motion_id: str,
        notion_data: Dict[str, Any],
        workspace: str,
        cached_motion_tasks_by_id: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> bool:
        """Update Motion task with Notion data (Notion owns all fields except status)."""
        try:
            # Use cached Motion task data when available to avoid unnecessary API calls
            if cached_motion_tasks_by_id and motion_id in cached_motion_tasks_by_id:
                motion_task = cached_motion_tasks_by_id[motion_id]
                self.logger.debug(f"Using cached Motion task data for {motion_id}")
            else:
                # Fallback to API call if not in cache
                motion_task = self.get_motion_task(motion_id)
                self.logger.debug(
                    f"Fetched Motion task data via API for {motion_id} (cache miss)"
                )

            if not motion_task:
                self.logger.warning(f"Motion task {motion_id} not found")
                return False

            # Compare actual task properties to detect changes instead of timestamps
            def normalize_for_comparison(value):
                """Normalize values for comparison."""
                if value is None:
                    return ""
                if isinstance(value, str):
                    return value.strip()
                return str(value)

            def normalize_priority(priority):
                """Normalize priority values for comparison."""
                if priority is None:
                    return "NONE"
                return str(priority).upper()

            def normalize_due_date(due_date):
                """Normalize due date for comparison - extract just YYYY-MM-DD."""
                if due_date is None:
                    return None
                # If it's a dict with 'start', extract the start date
                if isinstance(due_date, dict) and "start" in due_date:
                    due_date = due_date["start"]
                # Extract just the date part (YYYY-MM-DD)
                due_date_str = str(due_date)
                if "T" in due_date_str:
                    return due_date_str.split("T")[0]
                return due_date_str

            # Get current Motion task properties
            motion_name = normalize_for_comparison(motion_task.get("name", ""))
            motion_priority = normalize_priority(motion_task.get("priority", "NONE"))
            motion_duration = motion_task.get("duration", 30)
            motion_due_date = normalize_due_date(motion_task.get("dueDate"))
            # Get Notion properties for comparison
            notion_name = normalize_for_comparison(notion_data.get("task_name", ""))
            notion_priority = normalize_priority(notion_data.get("priority", "NONE"))
            # Convert Notion hours to minutes to match Motion's format
            notion_duration_hours = notion_data.get("est_duration_hrs", 1.0) or 1.0
            notion_duration = int(notion_duration_hours * 60)  # Convert to minutes
            notion_due_date = normalize_due_date(notion_data.get("due_date"))

            # Debug: Log values for comparison
            self.logger.info(f"🔍 DEBUG comparison for {notion_data['task_name']}:")
            self.logger.info(
                f"  due_date: Motion='{motion_due_date}' vs Notion='{notion_due_date}'"
            )
            self.logger.info(
                f"  duration: Motion={motion_duration}min vs Notion={notion_duration}min ({notion_duration_hours}hrs)"
            )

            # Check for differences (excluding description to avoid formatting noise)
            changes = []
            if motion_name != notion_name:
                changes.append(f"name ('{motion_name}' → '{notion_name}')")
            if motion_priority != notion_priority:
                changes.append(f"priority ('{motion_priority}' → '{notion_priority}')")
            if motion_duration != notion_duration:
                changes.append(f"duration ({motion_duration} → {notion_duration})")
            if motion_due_date != notion_due_date:
                changes.append(f"due_date ('{motion_due_date}' → '{notion_due_date}')")

            if not changes:
                self.logger.info(
                    f"⏭️ SKIPPING - No changes detected for: {notion_data['task_name']}"
                )
                return False
            else:
                self.logger.info(
                    f"🔄 Motion task needs update: {notion_data['task_name']}"
                )
                for change in changes:
                    self.logger.info(f"  📝 {change}")

            # Get Notion blocks for description (expensive operation)
            blocks = []
            if notion_data["id"]:
                blocks_response = self.workspace_clients[
                    workspace
                ].blocks.children.list(block_id=notion_data["id"])
                blocks = blocks_response.get("results", [])

            # Build update data - Notion always overwrites Motion fields
            priority_map = self.get_priority_mapping()
            status_map = self.get_status_mapping()

            # Always use Notion's status UNLESS Motion is completed
            motion_status_obj = motion_task.get("status", {})
            motion_status = (
                motion_status_obj.get("name", "")
                if isinstance(motion_status_obj, dict)
                else motion_status_obj
            )
            if motion_status.lower() == "completed":
                # Preserve Motion's completed status
                final_status = "Completed"
                self.logger.info(
                    f"🔒 PRESERVING Motion completed status for: {notion_data['task_name']}"
                )
            else:
                # Use Notion's status for all other cases
                final_status = status_map.get(notion_data["status"], "TODO")

            updates = {
                "name": notion_data["task_name"],
                "description": self.blocks_to_description(blocks),
                "priority": priority_map.get(notion_data["priority"], "MEDIUM"),
                "status": final_status,
                "duration": self.convert_hours_to_minutes(
                    notion_data["est_duration_hrs"]
                ),
            }

            # Add due date if present
            if notion_data["due_date"]:
                due_date = self.extract_due_date_start(notion_data["due_date"])
                if due_date:
                    updates["dueDate"] = due_date

            # Set auto-scheduling for work hours
            updates["autoScheduled"] = {"schedule": "Work Hours"}

            self.logger.info(
                f"🔄 OVERWRITING Motion task from Notion: {notion_data['task_name']}"
            )
            return self.update_motion_task(motion_id, updates, workspace)

        except requests.exceptions.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                self.logger.warning(
                    f"Motion task {motion_id} not found - creating new task to replace orphaned reference"
                )
                # Create a new Motion task since the old one doesn't exist
                return self._create_motion_from_notion(notion_data, workspace)
            else:
                self.logger.error(f"Failed to update Motion task {motion_id}: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to update Motion task {motion_id}: {e}")
            return False

    def _update_notion_motion_id(self, notion_id: str, motion_id: str, workspace: str):
        """Update Notion task with Motion ID - always in Personal hub."""
        try:
            # Motion IDs should only be stored in the Personal hub
            personal_client = self.workspace_clients["Personal"]
            personal_client.pages.update(
                page_id=notion_id,
                properties={
                    "Motion ID": {"rich_text": [{"text": {"content": motion_id}}]}
                },
            )
            self.logger.info(
                f"✅ Updated Personal hub task {notion_id} with Motion ID {motion_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to update Notion task with Motion ID: {e}")

    def has_meaningful_changes(
        self, motion_task: Dict[str, Any], notion_page: Dict[str, Any], workspace: str
    ) -> bool:
        """Check if Motion task has meaningful differences compared to Notion page."""
        try:
            # Get field mapping for this workspace
            field_mapping = self.get_workspace_field_mapping(workspace)

            # Get Motion values
            motion_status = motion_task.get("status", {}).get("name", "")
            motion_priority = motion_task.get("priority", "")
            motion_duration = motion_task.get("duration", 0)  # in minutes
            motion_due_date = motion_task.get("dueDate")

            # Get Notion values
            notion_props = notion_page["properties"]

            # Status comparison
            status_field = field_mapping.get("Status", "Status")
            notion_status_prop = notion_props.get(status_field, {})
            notion_status = ""
            if notion_status_prop.get("status") and notion_status_prop["status"].get(
                "name"
            ):
                notion_status = notion_status_prop["status"]["name"]

            # Priority comparison
            priority_field = field_mapping.get("Priority", "Priority")
            notion_priority_prop = notion_props.get(priority_field, {})
            notion_priority = ""
            if notion_priority_prop.get("select") and notion_priority_prop[
                "select"
            ].get("name"):
                notion_priority = notion_priority_prop["select"]["name"]

            # Duration comparison (convert Motion minutes to Notion hours)
            duration_field = field_mapping.get("Est Duration Hrs", "Est Duration Hrs")
            notion_duration_prop = notion_props.get(duration_field, {})
            notion_duration_hours = notion_duration_prop.get("number", 0) or 0
            motion_duration_hours = self.convert_minutes_to_hours(motion_duration)

            # Due date comparison (normalize timezone formats)
            due_date_field = field_mapping.get("Due date", "Due date")
            notion_due_prop = notion_props.get(due_date_field, {})
            notion_due_date = None
            if notion_due_prop.get("date") and notion_due_prop["date"].get("start"):
                notion_due_date = notion_due_prop["date"]["start"]
                # Normalize timezone format: convert +00:00 to Z for comparison
                if notion_due_date and notion_due_date.endswith("+00:00"):
                    notion_due_date = notion_due_date.replace("+00:00", "Z")

            # Map Motion values to Notion format for comparison
            priority_map = self.get_priority_mapping()
            status_map = self.get_status_mapping()

            mapped_motion_status = status_map.get(motion_status, motion_status)
            mapped_motion_priority = priority_map.get(motion_priority, motion_priority)

            # Check for differences
            status_changed = mapped_motion_status != notion_status
            priority_changed = mapped_motion_priority != notion_priority

            duration_changed = (
                abs(motion_duration_hours - notion_duration_hours) > 0.01
            )  # Small tolerance
            due_date_changed = motion_due_date != notion_due_date

            if (
                status_changed
                or priority_changed
                or duration_changed
                or due_date_changed
            ):
                self.logger.info(f"📋 Changes detected in {motion_task['name']}:")
                if status_changed:
                    self.logger.info(
                        f"   Status: '{notion_status}' → '{mapped_motion_status}'"
                    )
                if priority_changed:
                    self.logger.info(
                        f"   Priority: '{notion_priority}' → '{mapped_motion_priority}'"
                    )
                if duration_changed:
                    self.logger.info(
                        f"   Duration: {notion_duration_hours}h → {motion_duration_hours}h"
                    )
                if due_date_changed:
                    self.logger.info(
                        f"   Due date: '{notion_due_date}' → '{motion_due_date}'"
                    )
                return True
            else:
                self.logger.debug(f"No meaningful changes in {motion_task['name']}")
                return False

        except Exception as e:
            self.logger.warning(
                f"Error comparing task content, proceeding with update: {e}"
            )
            return True  # When in doubt, update

    def has_notion_to_motion_changes(
        self, notion_data: Dict[str, Any], motion_task: Dict[str, Any], workspace: str
    ) -> bool:
        """Check if Notion task has meaningful differences compared to Motion task."""
        try:

            # Get Notion values
            notion_status = notion_data.get("status", "")
            notion_priority = notion_data.get("priority", "")
            notion_duration_hours = notion_data.get("est_duration_hrs", 1.0)
            notion_due_date = notion_data.get("due_date")

            if isinstance(notion_due_date, dict) and notion_due_date.get("start"):
                notion_due_date = notion_due_date["start"]
                # Normalize timezone format
                if notion_due_date and notion_due_date.endswith("+00:00"):
                    notion_due_date = notion_due_date.replace("+00:00", "Z")
            notion_description = notion_data.get("description", "")

            # Get Motion values (with debug logging)
            motion_status = motion_task.get("status", {}).get("name", "")
            motion_priority = motion_task.get("priority", "")
            motion_duration_minutes = motion_task.get("duration", 0)
            motion_due_date = motion_task.get("dueDate")
            motion_description = motion_task.get("description", "")

            # Convert Motion minutes to hours for comparison
            motion_duration_hours = self.convert_minutes_to_hours(
                motion_duration_minutes
            )

            # Normalize both values to a common format for comparison
            # Motion → Common format
            motion_status_normalized = motion_status.upper() if motion_status else ""
            motion_priority_normalized = (
                motion_priority.upper() if motion_priority else ""
            )

            # Notion → Common format
            notion_status_map = {
                "Todo": "TODO",
                "Backlog": "TODO",
                "In Progress": "IN_PROGRESS",
                "Completed": "COMPLETED",
            }
            notion_priority_map = {
                "Low": "LOW",
                "Medium": "MEDIUM",
                "High": "HIGH",
                "ASAP": "ASAP",
            }

            notion_status_normalized = notion_status_map.get(
                notion_status, notion_status.upper() if notion_status else ""
            )
            notion_priority_normalized = notion_priority_map.get(
                notion_priority, notion_priority.upper() if notion_priority else ""
            )

            # Check for differences using normalized values (excluding description)
            status_changed = notion_status_normalized != motion_status_normalized
            priority_changed = notion_priority_normalized != motion_priority_normalized
            duration_changed = abs(notion_duration_hours - motion_duration_hours) > 0.01
            due_date_changed = notion_due_date != motion_due_date

            # Debug: Always log the raw values being compared
            self.logger.debug(
                f"🔍 Notion→Motion comparison for {notion_data['task_name']}:"
            )
            self.logger.debug(
                f"   Motion status: '{motion_status}' → normalized: '{motion_status_normalized}'"
            )
            self.logger.debug(
                f"   Notion status: '{notion_status}' → normalized: '{notion_status_normalized}'"
            )
            self.logger.debug(
                f"   Motion duration: {motion_duration_minutes} min ({motion_duration_hours}h)"
            )
            self.logger.debug(f"   Notion duration: {notion_duration_hours}h")
            self.logger.debug(
                f"   Changes: status={status_changed}, priority={priority_changed}, duration={duration_changed}"
            )

            if (
                status_changed
                or priority_changed
                or duration_changed
                or due_date_changed
            ):
                self.logger.info(f"📋 Changes detected in {notion_data['task_name']}:")
                if status_changed:
                    self.logger.info(
                        f"   Status: '{motion_status}' ({motion_status_normalized}) → '{notion_status}' ({notion_status_normalized})"
                    )
                if priority_changed:
                    self.logger.info(
                        f"   Priority: '{motion_priority}' ({motion_priority_normalized}) → '{notion_priority}' ({notion_priority_normalized})"
                    )
                if duration_changed:
                    self.logger.info(
                        f"   Duration: {motion_duration_hours}h → {notion_duration_hours}h"
                    )
                if due_date_changed:
                    self.logger.info(
                        f"   Due date: '{motion_due_date}' → '{notion_due_date}'"
                    )
                return True
            else:
                self.logger.debug(
                    f"No meaningful changes in {notion_data['task_name']}"
                )
                return False

        except Exception as e:
            self.logger.warning(
                f"Error comparing Notion→Motion content, proceeding with update: {e}"
            )
            return True  # When in doubt, update

    def set_notion_motion_sync_time(
        self, notion_id: str, sync_time: str, workspace: str
    ) -> bool:
        """Set Notion 'Motion Last Sync' field to track when we last synced from Motion."""
        if self.dry_run:
            return True  # Skip in dry run

        try:
            # Update the Motion Last Sync field in the specified workspace
            client = self.workspace_clients[workspace]

            # Get the field mapping for this workspace
            field_mapping = self.get_workspace_field_mapping(workspace)
            motion_sync_field = field_mapping.get(
                "Motion Last Sync", "Motion Last Sync"
            )

            client.pages.update(
                page_id=notion_id,
                properties={motion_sync_field: {"date": {"start": sync_time}}},
            )
            self.logger.debug(
                f"✅ Set Motion Last Sync time for Notion task {notion_id}"
            )
            return True
        except Exception as e:
            # Don't fail the whole sync if we can't set sync time - just log and continue
            self.logger.debug(
                f"Could not set Motion Last Sync time for Notion task {notion_id}: {e}"
            )
            return True  # Return True so sync continues

    def sync_full(self, test_mode: bool = False) -> Dict[str, Any]:
        """Perform full sync of all tasks."""
        mode_label = "TEST (1 task limit)" if test_mode else "FULL"
        self.logger.info(f"🚀 Starting {mode_label} Motion ↔ Notion sync")
        results = {"workspaces": {}}

        # Motion sync only works with Personal hub (Motion IDs are stored there)
        workspace = "Personal"
        self.logger.info(f"🔄 Syncing Motion ↔ {workspace} Hub")

        # Get Motion tasks once and cache them for both sync directions
        motion_workspace_id = self.motion_workspaces[workspace]
        if not motion_workspace_id:
            self.logger.error(f"No Motion workspace ID configured for {workspace}")
            return results

        motion_tasks = self.get_motion_tasks(motion_workspace_id)
        self.logger.info(f"📊 Cached {len(motion_tasks)} Motion tasks for sync")

        # Create lookup dictionary by Motion ID for fast access
        motion_tasks_by_id = {
            task.get("id"): task for task in motion_tasks if task.get("id")
        }

        workspace_results = {}

        # Motion → Notion sync first (to capture user changes from Motion)
        max_tasks = 1 if test_mode else None
        workspace_results["motion_to_notion"] = self.sync_motion_to_notion(
            workspace, max_tasks=max_tasks, cached_motion_tasks=motion_tasks
        )

        # Get list of Notion IDs that were just processed by Motion → Notion
        processed_notion_ids = workspace_results["motion_to_notion"].get(
            "processed_notion_ids", []
        )

        # Notion → Motion second (after Motion changes are synced to Notion)
        # In test mode, limit to same task that was processed by Motion → Notion
        if test_mode and workspace_results["motion_to_notion"].get(
            "processed_notion_id"
        ):
            # Process only the same Notion task that Motion → Notion just processed
            processed_id = workspace_results["motion_to_notion"]["processed_notion_id"]
            workspace_results["notion_to_motion"] = self.sync_specific_notion_task(
                workspace, processed_id, cached_motion_tasks_by_id=motion_tasks_by_id
            )
        else:
            # Skip tasks that were just processed by Motion → Notion to avoid overwriting changes
            workspace_results["notion_to_motion"] = self.sync_notion_to_motion(
                workspace,
                max_tasks=max_tasks,
                skip_notion_ids=processed_notion_ids,
                cached_motion_tasks_by_id=motion_tasks_by_id,
            )

        results["workspaces"] = {workspace: workspace_results}

        self.logger.info(f"✅ {mode_label} Motion ↔ Notion sync completed")
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Sync tasks between Motion AI and Notion"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "test", "test-real"],
        required=True,
        help="Sync mode: full (all tasks), test (dry run), test-real (1 task real update)",
    )

    args = parser.parse_args()

    try:
        # Initialize sync client
        dry_run = args.mode == "test"
        sync_client = MotionNotionSync(dry_run=dry_run)

        # Run sync based on mode
        if args.mode == "full":
            results = sync_client.sync_full()
        elif args.mode == "test":
            results = sync_client.sync_full(test_mode=True)
        elif args.mode == "test-real":
            results = sync_client.sync_full(test_mode=True)
        else:
            results = sync_client.sync_full()

        # Print summary
        print("\n" + "=" * 50)
        print("MOTION ↔ NOTION SYNC SUMMARY")
        print("=" * 50)

        total_errors = 0
        for workspace, workspace_results in results.get("workspaces", {}).items():
            print(f"\n{workspace}:")
            notion_to_motion = workspace_results.get("notion_to_motion", {})
            motion_to_notion = workspace_results.get("motion_to_notion", {})

            print(
                f"  Notion → Motion: {notion_to_motion.get('created', 0)} created, {notion_to_motion.get('updated', 0)} updated"
            )
            print(f"  Motion → Notion: {motion_to_notion.get('updated', 0)} updated")

            workspace_errors = notion_to_motion.get("errors", 0) + motion_to_notion.get(
                "errors", 0
            )
            total_errors += workspace_errors

            if workspace_errors > 0:
                print(f"  ⚠️  Errors: {workspace_errors}")

        if total_errors > 0:
            print(f"\n❌ Sync completed with {total_errors} errors")
            sys.exit(1)
        else:
            print(
                f"\n{'🧪 DRY RUN - No changes made' if dry_run else '✅ Sync completed successfully'}"
            )

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
