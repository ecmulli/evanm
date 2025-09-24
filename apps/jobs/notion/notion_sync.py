#!/usr/bin/env python3
"""
Notion Task Sync Script

Syncs tasks between personal task hub and external workspace databases (Livepeer, Vanquish).

Usage:
    python notion_sync.py --mode full
    python notion_sync.py --mode incremental
    python notion_sync.py --mode test  # dry run

Environment Variables Required:
    HUB_NOTION_API_KEY - Hub workspace Notion API token
    HUB_NOTION_DB_ID - Hub task database ID
    HUB_NOTION_USER_ID - Your user ID in the hub workspace

    Dynamic workspaces (auto-discovered from pattern):
    <WORKSPACE>_NOTION_API_KEY - External workspace Notion API token
    <WORKSPACE>_NOTION_DB_ID - External workspace database ID
    <WORKSPACE>_NOTION_USER_ID - Your user ID in the external workspace

    Examples:
    LIVEPEER_NOTION_API_KEY, LIVEPEER_NOTION_DB_ID, LIVEPEER_NOTION_USER_ID
    VANQUISH_NOTION_API_KEY, VANQUISH_NOTION_DB_ID, VANQUISH_NOTION_USER_ID
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv
from notion_client import Client


class NotionTaskSync:
    """Handles syncing tasks between personal hub and workspace databases."""

    def get_block_content(self, page_id: str, client=None) -> List[Dict[str, Any]]:
        """Get all blocks (content) from a page."""
        if not client:
            client = self.hub_client

        blocks = []
        cursor = None

        while True:
            response = client.blocks.children.list(
                block_id=page_id,
                start_cursor=cursor,
            )
            blocks.extend(response.get("results", []))

            if not response.get("has_more"):
                break

            cursor = response.get("next_cursor")

        return blocks

    def normalize_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a block for comparison by removing volatile fields."""
        normalized = block.copy()

        # Remove fields that change between copies
        for field in [
            "id",
            "created_time",
            "last_edited_time",
            "created_by",
            "last_edited_by",
        ]:
            normalized.pop(field, None)

        # Recursively normalize child blocks
        if block.get("has_children"):
            child_blocks = self.get_block_content(block["id"])
            normalized["children"] = [
                self.normalize_block(child) for child in child_blocks
            ]

        return normalized

    def blocks_are_equal(
        self, blocks1: List[Dict[str, Any]], blocks2: List[Dict[str, Any]]
    ) -> bool:
        """Compare two lists of blocks for equality."""
        if len(blocks1) != len(blocks2):
            return False

        normalized1 = [self.normalize_block(b) for b in blocks1]
        normalized2 = [self.normalize_block(b) for b in blocks2]

        return normalized1 == normalized2

    def sync_blocks(
        self,
        source_page_id: str,
        target_page_id: str,
        source_client=None,
        target_client=None,
    ) -> bool:
        """Sync blocks from source page to target page."""
        if not source_client:
            source_client = self.hub_client
        if not target_client:
            target_client = self.hub_client

        # Get source and target blocks
        source_blocks = self.get_block_content(source_page_id, source_client)
        target_blocks = self.get_block_content(target_page_id, target_client)

        # Check if sync is needed
        if self.blocks_are_equal(source_blocks, target_blocks):
            self.logger.debug(f"📝 Blocks already in sync for {target_page_id}")
            return False

        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would sync {len(source_blocks)} blocks to {target_page_id}"
            )
            return True

        # Delete existing blocks
        for block in target_blocks:
            target_client.blocks.delete(block["id"])

        # Create new blocks with validation
        children = []
        for i, block in enumerate(source_blocks):
            try:
                # Deep copy to avoid modifying the original
                block_copy = block.copy()

                # Remove fields that can't be sent in creation
                for field in [
                    "id",
                    "created_time",
                    "last_edited_time",
                    "created_by",
                    "last_edited_by",
                    "archived",
                    "has_children",
                ]:
                    block_copy.pop(field, None)

                # Validate block has a proper type
                block_type = block_copy.get("type")
                if not block_type:
                    self.logger.warning(f"⚠️ Skipping block {i}: missing 'type' field")
                    continue

                # Check if the block content for the type exists
                if block_type not in block_copy or not block_copy[block_type]:
                    self.logger.warning(
                        f"⚠️ Skipping block {i}: empty or invalid '{block_type}' content"
                    )
                    continue

                children.append(block_copy)

            except Exception as e:
                self.logger.warning(f"⚠️ Skipping invalid block {i}: {e}")
                continue

        if not children:
            self.logger.info(f"📝 No valid blocks to sync to {target_page_id}")
            return True

        # Append all blocks at once (more efficient)
        target_client.blocks.children.append(
            block_id=target_page_id,
            children=children,
        )

        self.logger.info(f"✅ Synced {len(source_blocks)} blocks to {target_page_id}")
        return True

    def __init__(self, dry_run: bool = False):
        # Setup logging first
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

        # Try to load .env.dev first, then fall back to .env
        load_dotenv(".env.dev")
        load_dotenv(".env")
        self.dry_run = dry_run

        # Initialize hub workspace
        self._init_hub_workspace()

        # Discover and initialize external workspaces dynamically
        self._discover_workspaces()

        # Validate all required environment variables
        self._validate_workspace_config()

        if dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no changes will be made")

    def _init_hub_workspace(self):
        """Initialize the hub workspace (main task database)."""
        # Hub workspace (backwards compatibility: check both HUB and PERSONAL)
        self.hub_token = os.getenv("HUB_NOTION_API_KEY") or os.getenv(
            "PERSONAL_NOTION_API_KEY"
        )
        self.hub_db_id = os.getenv("HUB_NOTION_DB_ID") or os.getenv(
            "PERSONAL_NOTION_DB_ID"
        )
        self.hub_user_id = os.getenv("HUB_NOTION_USER_ID") or os.getenv(
            "PERSONAL_NOTION_USER_ID"
        )

        if not all([self.hub_token, self.hub_db_id, self.hub_user_id]):
            raise ValueError(
                "Hub workspace requires HUB_NOTION_API_KEY, HUB_NOTION_DB_ID, and HUB_NOTION_USER_ID"
            )

        # Initialize hub client
        self.hub_client = Client(auth=self.hub_token)

    def _discover_workspaces(self):
        """Auto-discover external workspaces from environment variables."""
        self.workspaces = {}
        self.workspace_clients = {"Hub": self.hub_client}
        self.workspace_databases = {"Hub": self.hub_db_id}
        self.workspace_user_ids = {"Hub": self.hub_user_id}

        # Find all *_NOTION_DB_ID patterns
        for key, value in os.environ.items():
            if key.endswith("_NOTION_DB_ID") and value:
                workspace_name = key.replace("_NOTION_DB_ID", "")

                # Skip HUB and PERSONAL (hub workspace, handled separately)
                if workspace_name in ["HUB", "PERSONAL"]:
                    continue

                # Check if this workspace has all required vars
                api_key = os.getenv(f"{workspace_name}_NOTION_API_KEY")
                user_id = os.getenv(f"{workspace_name}_NOTION_USER_ID")

                if api_key and user_id:
                    # Store workspace configuration
                    self.workspaces[workspace_name] = {
                        "api_key": api_key,
                        "db_id": value,
                        "user_id": user_id,
                    }

                    # Initialize client and store references
                    self.workspace_clients[workspace_name] = Client(auth=api_key)
                    self.workspace_databases[workspace_name] = value
                    self.workspace_user_ids[workspace_name] = user_id

                    self.logger.info(f"📊 Discovered workspace: {workspace_name}")
                else:
                    missing_vars = []
                    if not api_key:
                        missing_vars.append(f"{workspace_name}_NOTION_API_KEY")
                    if not user_id:
                        missing_vars.append(f"{workspace_name}_NOTION_USER_ID")
                    self.logger.warning(
                        f"⚠️ Incomplete workspace config for {workspace_name}, missing: {missing_vars}"
                    )

    def _validate_workspace_config(self):
        """Validate that we have at least the hub workspace configured."""
        if not self.workspace_clients.get("Hub"):
            raise ValueError("Hub workspace must be configured")

        workspace_count = len(self.workspaces)
        self.logger.info(
            f"✅ Initialized {workspace_count} external workspaces: {list(self.workspaces.keys())}"
        )

    def get_workspace_databases(self) -> Dict[str, str]:
        """Return mapping of workspace names to database IDs (excluding Hub)."""
        return {name: self.workspace_databases[name] for name in self.workspaces.keys()}

    def get_workspace_client(self, workspace: str) -> Client:
        """Return the appropriate Notion client for a workspace."""
        # Handle backwards compatibility and aliases
        if workspace in ["Personal", "Hub"]:
            return self.workspace_clients["Hub"]
        return self.workspace_clients.get(workspace, self.workspace_clients["Hub"])

    def get_workspace_user_id(self, workspace: str) -> str:
        """Return the appropriate User ID for a workspace."""
        # Handle backwards compatibility and aliases
        if workspace in ["Personal", "Hub"]:
            return self.workspace_user_ids["Hub"]
        return self.workspace_user_ids.get(workspace, self.workspace_user_ids["Hub"])

    def get_workspace_field_mapping(self, workspace: str) -> Dict[str, str]:
        """Return field name mappings for each workspace."""
        if workspace == "Vanquish":
            return {
                "est_duration_hrs": "Est. Duration Hrs",  # Note the period
                "due_date": "Due Date",  # Note the capital D
                "task_name": "Task name",
                "status": "Status",
                "priority": "Priority",
                "external_notion_id": "External Notion ID",
                "labels": "Labels",
                "team": "Team",
            }
        else:
            return {
                "est_duration_hrs": "Est Duration Hrs",
                "due_date": "Due date",
                "task_name": "Task name",
                "status": "Status",
                "priority": "Priority",
                "external_notion_id": "External Notion ID",
                "labels": "Labels",
                "team": "Team",
            }

    def query_assigned_tasks(
        self, database_id: str, workspace: str, since_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Query tasks assigned to user from a database.

        Args:
            database_id: Notion database ID
            workspace: Workspace name to determine which client to use
            since_date: Only get tasks updated since this date (for incremental sync)
        """
        return self.query_workspace_tasks(database_id, workspace, assigned_only=True, since_date=since_date)

    def query_workspace_tasks(
        self, database_id: str, workspace: str, assigned_only: bool = True, since_date: Optional[datetime] = None, include_completed: bool = False
    ) -> List[Dict]:
        """
        Query tasks from a database, optionally filtered by assignment.

        Args:
            database_id: Notion database ID
            workspace: Workspace name to determine which client to use
            assigned_only: If True, only get tasks assigned to user. If False, get all tasks.
            since_date: Only get tasks updated since this date (for incremental sync)
            include_completed: If True, include completed/backlog/canceled tasks. If False, exclude them.
        """
        user_id = self.get_workspace_user_id(workspace)
        filter_conditions = {"and": []}
        
        # Add assignment filter if requested
        if assigned_only:
            filter_conditions["and"].append({
                "property": "Assignee", 
                "people": {"contains": user_id}
            })
        
        # Exclude completed statuses unless explicitly requested
        if not include_completed:
            filter_conditions["and"].append({
                "and": [
                    {"property": "Status", "status": {"does_not_equal": "Backlog"}},
                    {"property": "Status", "status": {"does_not_equal": "Completed"}},
                    {"property": "Status", "status": {"does_not_equal": "Canceled"}},
                ]
            })

        # Note: since_date filtering is not implemented due to Notion API limitations
        # The "Last edited time" property cannot be used in database queries
        if since_date:
            self.logger.debug(f"Date filtering skipped (since_date: {since_date})")

        try:
            client = self.get_workspace_client(workspace)

            if self.dry_run:
                self.logger.info(f"🔍 Filter for {workspace}: {filter_conditions}")
                self.logger.info(f"🔍 Using User ID: {user_id}")

            response = client.databases.query(
                database_id=database_id, filter=filter_conditions
            )
            results = response.get("results", [])

            if self.dry_run:
                self.logger.info(
                    f"🔍 Raw query returned {len(results)} results from {workspace}"
                )

                # Test query without filters to see all tasks
                if len(results) == 0:
                    self.logger.info(
                        f"🔍 Testing query without filters for {workspace}..."
                    )
                    test_response = client.databases.query(database_id=database_id)
                    test_results = test_response.get("results", [])
                    self.logger.info(
                        f"🔍 Query without filters returned {len(test_results)} total tasks"
                    )

                    if len(test_results) > 0:
                        # Show properties of first task for debugging
                        first_task = test_results[0]
                        props = first_task.get("properties", {})
                        self.logger.info(
                            f"🔍 Available properties in {workspace}: {list(props.keys())}"
                        )

                        # Check assignee field specifically
                        assignee_prop = props.get("Assignee")
                        if assignee_prop:
                            self.logger.info(
                                f"🔍 Assignee property type: {assignee_prop.get('type')}"
                            )
                            if assignee_prop.get("type") == "people":
                                people_list = assignee_prop.get("people", [])
                                self.logger.info(
                                    f"🔍 Assignee contains {len(people_list)} people"
                                )
                                for person in people_list:
                                    self.logger.info(
                                        f"🔍 Person ID: {person.get('id')}"
                                    )
                        else:
                            self.logger.warning(
                                f"⚠️ No 'Assignee' property found in {workspace}"
                            )

            return results
        except Exception as e:
            self.logger.error(f"Error querying database {database_id}: {e}")
            return []

    def query_hub_tasks(
        self, workspace: str = None, since_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Query tasks from hub, optionally filtered by workspace.

        Args:
            workspace: Filter by workspace (external workspace name, or None for all)
            since_date: Only get tasks updated since this date
        """
        filter_conditions = {"and": []}

        # Filter by workspace if specified
        if workspace:
            # Use case-insensitive matching for workspace names
            filter_conditions["and"].append(
                {"property": "Workspace", "select": {"equals": workspace.title()}}
            )

        # Note: since_date filtering is not implemented due to Notion API limitations
        # The "Last edited time" property cannot be used in database queries
        if since_date:
            self.logger.debug(f"Date filtering skipped (since_date: {since_date})")

        # If no conditions, query all
        query_filter = filter_conditions if filter_conditions["and"] else None

        try:
            response = self.hub_client.databases.query(
                database_id=self.hub_db_id, filter=query_filter
            )
            return response.get("results", [])
        except Exception as e:
            self.logger.error(f"Error querying hub: {e}")
            return []

    def extract_task_data(self, page: Dict) -> Dict[str, Any]:
        """Extract standardized task data from a Notion page."""
        props = page.get("properties", {})

        # Debug: Log available properties
        if self.dry_run:
            self.logger.debug(f"🔍 Available properties: {list(props.keys())}")

        def get_text(prop_data):
            if not prop_data:
                return ""
            try:
                if prop_data.get("type") == "title":
                    title_list = prop_data.get("title", [])
                    return "".join([t.get("plain_text", "") for t in title_list if t])
                elif prop_data.get("type") == "rich_text":
                    rich_text_list = prop_data.get("rich_text", [])
                    return "".join(
                        [t.get("plain_text", "") for t in rich_text_list if t]
                    )
                return ""
            except (AttributeError, TypeError) as e:
                self.logger.warning(f"⚠️ Error extracting text from property: {e}")
                return ""

        def get_select(prop_data):
            if not prop_data or prop_data.get("type") != "select":
                return None
            select_data = prop_data.get("select")
            value = select_data.get("name") if select_data else None
            return value.strip() if value else None  # Strip whitespace

        def get_status(prop_data):
            if not prop_data or prop_data.get("type") != "status":
                return None
            status_data = prop_data.get("status")
            return status_data.get("name") if status_data else None

        def get_number(prop_data):
            if not prop_data or prop_data.get("type") != "number":
                return None
            return prop_data.get("number")

        def get_date(prop_data):
            if not prop_data or prop_data.get("type") != "date":
                return None
            date_data = prop_data.get("date")
            return date_data.get("start") if date_data else None

        def get_multi_select(prop_data):
            if not prop_data or prop_data.get("type") != "multi_select":
                return []
            multi_select_data = prop_data.get("multi_select", [])
            return [item.get("name") for item in multi_select_data if item.get("name")]

        return {
            "id": page.get("id"),
            "task_name": get_text(props.get("Task name")),
            "status": get_status(props.get("Status")),
            "workspace": get_select(props.get("Workspace")),
            "est_duration_hrs": get_number(props.get("Est Duration Hrs")),
            "due_date": get_date(props.get("Due date")),
            "priority": get_select(props.get("Priority")),
            "external_notion_id": get_text(props.get("External Notion ID")),
            "labels": get_multi_select(props.get("Labels")),
            "team": get_select(props.get("Team")),
            "updated_at": page.get("last_edited_time"),
            "url": page.get("url"),
        }

    def create_task_in_hub(
        self, task_data: Dict, workspace: str, external_id: str, sync_content: bool = True
    ) -> Optional[str]:
        """Create a new task in the hub."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would create task '{task_data['task_name']}' in hub"
            )
            if sync_content:
                self.logger.info(
                    f"🧪 DRY RUN: Would also sync content blocks from {external_id}"
                )
            return "dry_run_id"

        properties = {
            "Task name": {"title": [{"text": {"content": task_data["task_name"]}}]},
            "Workspace": {"select": {"name": workspace}},
            "External Notion ID": {"rich_text": [{"text": {"content": external_id}}]},
        }

        # Add optional properties
        if task_data.get("status"):
            properties["Status"] = {"status": {"name": task_data["status"]}}
        if task_data.get("est_duration_hrs") is not None:
            properties["Est Duration Hrs"] = {"number": task_data["est_duration_hrs"]}
        if task_data.get("due_date"):
            properties["Due date"] = {"date": {"start": task_data["due_date"]}}
        if task_data.get("priority"):
            properties["Priority"] = {"select": {"name": task_data["priority"]}}
        if task_data.get("labels"):
            properties["Labels"] = {
                "multi_select": [{"name": label} for label in task_data["labels"]]
            }
        if task_data.get("team"):
            properties["Team"] = {"select": {"name": task_data["team"]}}

        try:
            response = self.hub_client.pages.create(
                parent={"database_id": self.hub_db_id}, properties=properties
            )
            new_task_id = response.get("id")
            self.logger.info(f"✅ Created task '{task_data['task_name']}' in hub")
            
            # Sync content blocks from external workspace to hub
            if sync_content and new_task_id:
                try:
                    external_client = self.get_workspace_client(workspace)
                    blocks_synced = self.sync_blocks(
                        source_page_id=external_id,
                        target_page_id=new_task_id,
                        source_client=external_client,
                        target_client=self.hub_client,
                    )
                    if blocks_synced:
                        self.logger.info(f"📝 Synced content blocks from {workspace} to hub")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to sync content blocks: {e}")
            
            return new_task_id
        except Exception as e:
            self.logger.error(f"❌ Error creating task in hub: {e}")
            return None

    def update_task_properties(
        self,
        page_id: str,
        updates: Dict[str, Any],
        workspace: str = "Hub",
        sync_content: bool = False,
        source_page_id: str = None,
        source_workspace: str = None,
    ) -> bool:
        """Update properties of an existing task."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would update task {page_id} with {list(updates.keys())}"
            )
            if sync_content and source_page_id:
                self.logger.info(
                    f"🧪 DRY RUN: Would also sync content from {source_page_id}"
                )
            return True

        # Get field mapping for this workspace
        field_mapping = self.get_workspace_field_mapping(workspace)
        properties = {}

        for field, value in updates.items():
            if field == "task_name" and value:
                field_name = field_mapping.get("task_name", "Task name")
                properties[field_name] = {"title": [{"text": {"content": value}}]}
            elif field == "status" and value:
                field_name = field_mapping.get("status", "Status")
                properties[field_name] = {"status": {"name": value}}
            elif field == "workspace" and value:
                properties["Workspace"] = {
                    "select": {"name": value}
                }  # Only in personal hub
            elif field == "est_duration_hrs" and value is not None:
                field_name = field_mapping.get("est_duration_hrs", "Est Duration Hrs")
                properties[field_name] = {"number": value}
            elif field == "due_date" and value:
                field_name = field_mapping.get("due_date", "Due date")
                properties[field_name] = {"date": {"start": value}}
            elif field == "priority" and value:
                field_name = field_mapping.get("priority", "Priority")
                properties[field_name] = {"select": {"name": value}}
            elif field == "external_notion_id" and value:
                field_name = field_mapping.get(
                    "external_notion_id", "External Notion ID"
                )
                properties[field_name] = {"rich_text": [{"text": {"content": value}}]}
            elif field == "labels" and value:
                field_name = field_mapping.get("labels", "Labels")
                properties[field_name] = {
                    "multi_select": [{"name": label} for label in value]
                }
            elif field == "team" and value:
                field_name = field_mapping.get("team", "Team")
                properties[field_name] = {"select": {"name": value}}

        if not properties:
            return True

        try:
            client = self.get_workspace_client(workspace)
            client.pages.update(page_id=page_id, properties=properties)
            self.logger.info(f"✅ Updated task {page_id}")

            # Sync content if requested
            if sync_content and source_page_id:
                # Determine the correct source client
                if source_workspace:
                    source_client = self.get_workspace_client(source_workspace)
                else:
                    # Default: if no source_workspace specified, assume source is from the workspace we're syncing
                    source_client = self.get_workspace_client(workspace)

                self.sync_blocks(
                    source_page_id=source_page_id,
                    target_page_id=page_id,
                    source_client=source_client,
                    target_client=client,
                )

            return True
        except Exception as e:
            self.logger.error(f"❌ Error updating task {page_id}: {e}")
            return False

    def create_task_in_external_workspace(
        self, task_data: Dict, workspace: str, database_id: str
    ) -> Optional[str]:
        """Create a new task in external workspace database."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would create task '{task_data['task_name']}' in {workspace}"
            )
            return "dry_run_external_id"

        try:
            client = self.get_workspace_client(workspace)
            field_mapping = self.get_workspace_field_mapping(workspace)

            # Build properties for external workspace
            properties = {
                "Task name": {"title": [{"text": {"content": task_data["task_name"]}}]},
            }

            # Add optional properties using field mapping
            if task_data.get("status"):
                field_name = field_mapping.get("status", "Status")
                properties[field_name] = {"status": {"name": task_data["status"]}}
            if task_data.get("est_duration_hrs") is not None:
                field_name = field_mapping.get("est_duration_hrs", "Est Duration Hrs")
                properties[field_name] = {"number": task_data["est_duration_hrs"]}
            if task_data.get("due_date"):
                field_name = field_mapping.get("due_date", "Due date")
                properties[field_name] = {"date": {"start": task_data["due_date"]}}
            if task_data.get("priority"):
                field_name = field_mapping.get("priority", "Priority")
                properties[field_name] = {"select": {"name": task_data["priority"]}}
            if task_data.get("labels"):
                field_name = field_mapping.get("labels", "Labels")
                properties[field_name] = {
                    "multi_select": [{"name": label} for label in task_data["labels"]]
                }
            if task_data.get("team"):
                field_name = field_mapping.get("team", "Team")
                properties[field_name] = {"select": {"name": task_data["team"]}}

            # Create the page
            response = client.pages.create(
                parent={"database_id": database_id}, properties=properties
            )

            return response["id"]

        except Exception as e:
            self.logger.error(f"Error creating task in {workspace}: {e}")
            return None

    def sync_external_to_hub(
        self,
        workspace: str,
        since_date: Optional[datetime] = None,
        sync_content: bool = False,
    ) -> Dict[str, int]:
        """Sync tasks from external workspace to hub."""
        self.logger.info(f"🔄 Syncing {workspace} → Hub")

        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        workspace_db_id = self.get_workspace_databases()[workspace]

        # Get tasks from external workspace
        external_tasks = self.query_assigned_tasks(
            workspace_db_id, workspace, since_date
        )

        # Get existing hub tasks for this workspace
        hub_tasks = self.query_hub_tasks(workspace, since_date)
        external_id_map = {}

        for task in hub_tasks:
            try:
                # Safely extract External Notion ID
                props = task.get("properties", {})
                external_id_prop = props.get("External Notion ID", {})
                rich_text = external_id_prop.get("rich_text", [])

                if rich_text and len(rich_text) > 0:
                    text_obj = rich_text[0].get("text", {})
                    external_id = text_obj.get("content", "")
                    if external_id:
                        external_id_map[external_id] = task
                else:
                    # Task doesn't have External Notion ID - that's fine for personal tasks
                    pass

            except Exception as e:
                task_name = (
                    task.get("properties", {}).get("Task name", {}).get("title", [{}])
                )
                task_title = (
                    task_name[0].get("plain_text", "Unknown")
                    if task_name
                    else "Unknown"
                )
                self.logger.warning(
                    f"⚠️ Could not extract External ID from task '{task_title}': {e}"
                )

        self.logger.info(
            f"📊 Found {len(external_tasks)} external tasks in {workspace}"
        )
        self.logger.info(f"📊 Found {len(hub_tasks)} hub tasks for {workspace}")

        for external_task in external_tasks:
            try:
                external_data = self.extract_task_data(external_task)
                external_id = external_data["id"]
                self.logger.debug(
                    f"🔍 Processing external task: {external_data.get('task_name', 'Unknown')}"
                )
            except Exception as e:
                self.logger.error(f"❌ Error extracting data from external task: {e}")
                stats["errors"] += 1
                continue

            # Check if task already exists in personal hub
            existing_personal_task = external_id_map.get(external_id)

            if existing_personal_task:
                # SKIP existing tasks - External workspaces should NEVER update existing tasks
                # The Hub is the single source of truth for all task data
                hub_data = self.extract_task_data(existing_personal_task)
                if self.dry_run:
                    self.logger.info(
                        f"🚫 DRY RUN: SKIPPING existing hub task '{hub_data['task_name']}' (External should not update existing tasks)"
                    )
                else:
                    self.logger.info(
                        f"🚫 SKIPPING existing hub task '{hub_data['task_name']}' (External should not update existing tasks)"
                    )
                stats["skipped"] += 1
            else:
                # Create new task in hub
                new_task_id = self.create_task_in_hub(
                    external_data, workspace, external_id, sync_content
                )
                if new_task_id:
                    stats["created"] += 1
                else:
                    stats["errors"] += 1

        self.logger.info(f"📊 {workspace} sync complete: {stats}")
        return stats

    def sync_hub_to_external(
        self,
        workspace: str,
        since_date: Optional[datetime] = None,
        sync_content: bool = False,
    ) -> Dict[str, int]:
        """Sync tasks from hub back to external workspace."""
        self.logger.info(f"🔄 Syncing Hub → {workspace}")

        stats = {"updated": 0, "skipped": 0, "errors": 0}
        workspace_db_id = self.get_workspace_databases()[workspace]

        # Get hub tasks for this workspace
        hub_tasks = self.query_hub_tasks(workspace, since_date)
        
        # OPTIMIZATION: Bulk fetch all external tasks upfront to avoid individual API calls
        # Include completed tasks to handle hub→external status syncing (e.g. completed tasks)
        self.logger.info(f"📦 Bulk fetching external tasks from {workspace} (including completed)...")
        all_external_tasks = self.query_workspace_tasks(workspace_db_id, workspace, assigned_only=False, since_date=since_date, include_completed=True)
        
        # Create mapping of external_id -> external_task_data for fast lookup
        external_tasks_map = {}
        for ext_task in all_external_tasks:
            external_tasks_map[ext_task["id"]] = self.extract_task_data(ext_task)
        
        self.logger.info(f"📦 Cached {len(external_tasks_map)} external tasks from {workspace}")

        for hub_task in hub_tasks:
            hub_data = self.extract_task_data(hub_task)
            external_id = hub_data["external_notion_id"]

            if not external_id:
                # Task has no External Notion ID - create it in external workspace
                self.logger.info(
                    f"🆕 Creating new task in {workspace}: {hub_data['task_name']}"
                )
                try:
                    new_external_id = self.create_task_in_external_workspace(
                        hub_data, workspace, workspace_db_id
                    )
                    if new_external_id:
                        # Update hub task with the new External Notion ID
                        self.update_task_properties(
                            hub_task["id"],
                            {"external_notion_id": new_external_id},
                            "Hub",
                        )
                        stats["updated"] += 1
                        self.logger.info(
                            f"✅ Created and linked task: {hub_data['task_name']}"
                        )
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    self.logger.error(f"Error creating external task: {e}")
                    stats["errors"] += 1
                continue

            # Get the external task from our pre-fetched mapping (no API call needed!)
            try:
                external_data = external_tasks_map.get(external_id)
                if not external_data:
                    self.logger.warning(f"⚠️ External task {external_id} not found in {workspace} (may have been deleted)")
                    stats["errors"] += 1
                    continue

                # Check if sync is needed based on updated_at timestamp
                hub_updated = hub_data.get("updated_at")
                external_updated = external_data.get("updated_at")

                needs_sync = False
                if hub_updated and external_updated:
                    # Compare timestamps - if hub is newer, sync is needed
                    try:
                        if isinstance(hub_updated, str):
                            hub_dt = datetime.fromisoformat(
                                hub_updated.replace("Z", "+00:00")
                            )
                        else:
                            hub_dt = hub_updated
                        if isinstance(external_updated, str):
                            external_dt = datetime.fromisoformat(
                                external_updated.replace("Z", "+00:00")
                            )
                        else:
                            external_dt = external_updated
                        needs_sync = hub_dt > external_dt
                    except Exception as e:
                        self.logger.debug(f"Error comparing timestamps: {e}")
                        needs_sync = True  # Fallback to full sync
                else:
                    needs_sync = True  # Missing timestamps, do full sync

                if needs_sync:
                    updates = {}

                    # Compare fields and build updates (exclude workspace-specific fields)
                    if hub_data["task_name"] != external_data["task_name"]:
                        updates["task_name"] = hub_data["task_name"]
                    if hub_data["status"] != external_data["status"]:
                        updates["status"] = hub_data["status"]
                    if (
                        hub_data["est_duration_hrs"]
                        != external_data["est_duration_hrs"]
                    ):
                        updates["est_duration_hrs"] = hub_data["est_duration_hrs"]
                    if hub_data["due_date"] != external_data["due_date"]:
                        updates["due_date"] = hub_data["due_date"]
                    if hub_data["priority"] != external_data["priority"]:
                        updates["priority"] = hub_data["priority"]
                    if hub_data["labels"] != external_data["labels"]:
                        updates["labels"] = hub_data["labels"]
                    if hub_data["team"] != external_data["team"]:
                        updates["team"] = hub_data["team"]

                    if updates:
                        # There are actual property changes to sync
                        if self.dry_run:
                            self.logger.info(
                                f"🧪 DRY RUN: Would update {workspace} task '{hub_data['task_name']}' (hub newer: {hub_updated} > {external_updated}):"
                            )
                            for field, value in updates.items():
                                old_value = external_data.get(field, "None")
                                self.logger.info(
                                    f"  - {field}: '{old_value}' → '{value}'"
                                )
                            if sync_content:
                                self.logger.info(
                                    f"🧪 DRY RUN: Would also sync content from hub"
                                )
                            stats["updated"] += 1
                        else:
                            if self.update_task_properties(
                                external_id,
                                updates,
                                workspace,
                                sync_content=True,  # Always sync content from hub to external
                                source_page_id=hub_task["id"],
                                source_workspace="Hub",
                            ):
                                stats["updated"] += 1
                            else:
                                stats["errors"] += 1
                    else:  # Always sync content from hub to external
                        # No property changes, but always sync content from hub - check if content differs
                        if self.dry_run:
                            self.logger.info(
                                f"🧪 DRY RUN: {workspace} task '{hub_data['task_name']}' - checking content only"
                            )
                            stats[
                                "skipped"
                            ] += 1  # Don't count as update in dry run for content-only
                        else:
                            # Only sync content if there are actual block differences
                            hub_blocks = self.get_block_content(
                                hub_task["id"], self.hub_client
                            )
                            external_blocks = self.get_block_content(
                                external_id, self.get_workspace_client(workspace)
                            )

                            if not self.blocks_are_equal(hub_blocks, external_blocks):
                                if self.update_task_properties(
                                    external_id,
                                    {},
                                    workspace,
                                    sync_content=True,
                                    source_page_id=hub_task["id"],
                                    source_workspace="Hub",
                                ):
                                    stats["updated"] += 1
                                else:
                                    stats["errors"] += 1
                            else:
                                stats["skipped"] += 1
                else:
                    if self.dry_run:
                        self.logger.info(
                            f"🧪 DRY RUN: {workspace} task '{hub_data['task_name']}' up to date (hub: {hub_updated}, external: {external_updated})"
                        )
                    stats["skipped"] += 1

            except Exception as e:
                self.logger.error(
                    f"❌ Error accessing external task {external_id}: {e}"
                )
                stats["errors"] += 1

        self.logger.info(f"📊 {workspace} reverse sync complete: {stats}")
        return stats

    def sync_full(self, sync_content: bool = False) -> Dict[str, Any]:
        """Perform full sync of all tasks."""
        self.logger.info("🚀 Starting FULL sync")
        results = {"workspaces": {}}

        for workspace in self.get_workspace_databases().keys():
            workspace_results = {}

            # External → Hub
            workspace_results["external_to_hub"] = self.sync_external_to_hub(
                workspace, sync_content=sync_content
            )

            # Hub → External
            workspace_results["hub_to_external"] = self.sync_hub_to_external(
                workspace, sync_content=sync_content
            )

            results["workspaces"][workspace] = workspace_results

        self.logger.info("✅ Full sync completed")
        return results

    def sync_incremental(self, sync_content: bool = False) -> Dict[str, Any]:
        """Perform incremental sync - currently same as full sync due to Notion API limitations."""
        self.logger.info("🚀 Starting INCREMENTAL sync (falling back to full sync)")
        self.logger.warning(
            "⚠️  Note: Incremental sync requires custom timestamp fields. Using full sync for now."
        )

        # Fallback to full sync since Notion's last_edited_time isn't filterable
        return self.sync_full(sync_content=sync_content)


def main():
    parser = argparse.ArgumentParser(description="Sync Notion tasks between workspaces")
    parser.add_argument(
        "--mode",
        choices=["full", "incremental", "test"],
        required=True,
        help="Sync mode: full (all tasks), incremental (last 24h), test (dry run)",
    )
    parser.add_argument(
        "--sync-content",
        action="store_true",
        help="Also sync page content (blocks) - slower but more complete",
    )

    args = parser.parse_args()
    sync_content = args.sync_content

    try:
        # Initialize sync client
        dry_run = args.mode == "test"
        sync_client = NotionTaskSync(dry_run=dry_run)

        # Run sync based on mode
        if args.mode == "full" or args.mode == "test":
            results = sync_client.sync_full(sync_content=sync_content)
        elif args.mode == "incremental":
            results = sync_client.sync_incremental(sync_content=sync_content)

        # Print summary
        print("\n" + "=" * 50)
        print("SYNC SUMMARY")
        print("=" * 50)

        total_errors = 0
        for workspace, workspace_results in results.get("workspaces", {}).items():
            print(f"\n{workspace}:")
            ext_to_hub = workspace_results.get("external_to_hub", {})
            hub_to_ext = workspace_results.get("hub_to_external", {})

            print(
                f"  External → Hub: {ext_to_hub.get('created', 0)} created, {ext_to_hub.get('updated', 0)} updated"
            )
            print(f"  Hub → External: {hub_to_ext.get('updated', 0)} updated")

            workspace_errors = ext_to_hub.get("errors", 0) + hub_to_ext.get("errors", 0)
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
