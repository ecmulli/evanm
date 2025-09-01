#!/usr/bin/env python3
"""
Notion Task Sync Script

Syncs tasks between personal task hub and external workspace databases (Livepeer, Vanquish).

Usage:
    python notion_motion_sync.py --mode full
    python notion_motion_sync.py --mode incremental
    python notion_motion_sync.py --mode test  # dry run

Environment Variables Required:
    PERSONAL_NOTION_API_KEY - Personal workspace Notion API token
    LIVEPEER_NOTION_API_KEY - Livepeer workspace Notion API token
    VANQUISH_NOTION_API_KEY - Vanquish workspace Notion API token
    PERSONAL_NOTION_DB_ID - Personal task hub database ID
    LIVEPEER_NOTION_DB_ID - Livepeer workspace database ID
    VANQUISH_NOTION_DB_ID - Vanquish workspace database ID
    PERSONAL_NOTION_USER_ID - Your user ID in the personal workspace
    LIVEPEER_NOTION_USER_ID - Your user ID in the Livepeer workspace
    VANQUISH_NOTION_USER_ID - Your user ID in the Vanquish workspace
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

    def __init__(self, dry_run: bool = False):
        # Try to load .env.dev first, then fall back to .env
        load_dotenv(".env.dev")
        load_dotenv(".env")
        self.dry_run = dry_run

        # API tokens for each workspace
        self.personal_token = os.getenv("PERSONAL_NOTION_API_KEY")
        self.livepeer_token = os.getenv("LIVEPEER_NOTION_API_KEY")
        self.vanquish_token = os.getenv("VANQUISH_NOTION_API_KEY")

        # Initialize Notion clients for each workspace
        self.personal_client = Client(auth=self.personal_token)
        self.livepeer_client = Client(auth=self.livepeer_token)
        self.vanquish_client = Client(auth=self.vanquish_token)

        # Database IDs
        self.personal_hub_id = os.getenv("PERSONAL_NOTION_DB_ID")
        self.livepeer_db_id = os.getenv("LIVEPEER_NOTION_DB_ID")
        self.vanquish_db_id = os.getenv("VANQUISH_NOTION_DB_ID")

        # User IDs for each workspace
        self.personal_user_id = os.getenv("PERSONAL_NOTION_USER_ID")
        self.livepeer_user_id = os.getenv("LIVEPEER_NOTION_USER_ID")
        self.vanquish_user_id = os.getenv("VANQUISH_NOTION_USER_ID")

        # Validate required environment variables
        required_vars = [
            "PERSONAL_NOTION_API_KEY",
            "LIVEPEER_NOTION_API_KEY",
            "VANQUISH_NOTION_API_KEY",
            "PERSONAL_NOTION_DB_ID",
            "LIVEPEER_NOTION_DB_ID",
            "VANQUISH_NOTION_DB_ID",
            "PERSONAL_NOTION_USER_ID",
            "LIVEPEER_NOTION_USER_ID",
            "VANQUISH_NOTION_USER_ID",
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

        if dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no changes will be made")

    def get_workspace_databases(self) -> Dict[str, str]:
        """Return mapping of workspace names to database IDs."""
        return {"Livepeer": self.livepeer_db_id, "Vanquish": self.vanquish_db_id}

    def get_workspace_client(self, workspace: str) -> Client:
        """Return the appropriate Notion client for a workspace."""
        if workspace == "Livepeer":
            return self.livepeer_client
        elif workspace == "Vanquish":
            return self.vanquish_client
        else:
            return self.personal_client

    def get_workspace_user_id(self, workspace: str) -> str:
        """Return the appropriate User ID for a workspace."""
        if workspace == "Livepeer":
            return self.livepeer_user_id
        elif workspace == "Vanquish":
            return self.vanquish_user_id
        else:
            return self.personal_user_id

    def get_workspace_field_mapping(self, workspace: str) -> Dict[str, str]:
        """Return field name mappings for each workspace."""
        if workspace == "Vanquish":
            return {
                "est_duration_hrs": "Est. Duration Hrs",  # Note the period
                "due_date": "Due Date",  # Note the capital D
                "task_name": "Task name",
                "status": "Status",
                "priority": "Priority",
                "description": "Description",
                "external_notion_id": "External Notion ID"
            }
        else:
            return {
                "est_duration_hrs": "Est Duration Hrs",
                "due_date": "Due date",
                "task_name": "Task name",
                "status": "Status",
                "priority": "Priority",
                "description": "Description",
                "external_notion_id": "External Notion ID"
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
        user_id = self.get_workspace_user_id(workspace)
        filter_conditions = {
            "and": [
                {
                    "property": "Assignee",
                    "people": {"contains": user_id},
                },
                {
                    "and": [
                        {"property": "Status", "status": {"does_not_equal": "Backlog"}},
                        {"property": "Status", "status": {"does_not_equal": "Completed"}},
                        {"property": "Status", "status": {"does_not_equal": "Canceled"}},
                    ]
                },
            ]
        }

        # Add date filter for incremental sync
        if since_date:
            filter_conditions["and"].append(
                {
                    "property": "Updated At",
                    "last_edited_time": {"on_or_after": since_date.isoformat()},
                }
            )

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

    def query_personal_hub_tasks(
        self, workspace: str = None, since_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Query tasks from personal hub, optionally filtered by workspace.

        Args:
            workspace: Filter by workspace (Livepeer, Vanquish, or None for all)
            since_date: Only get tasks updated since this date
        """
        filter_conditions = {"and": []}

        # Filter by workspace if specified
        if workspace:
            filter_conditions["and"].append(
                {"property": "Workspace", "select": {"equals": workspace}}
            )

        # Add date filter for incremental sync
        if since_date:
            filter_conditions["and"].append(
                {
                    "property": "Updated At",
                    "last_edited_time": {"on_or_after": since_date.isoformat()},
                }
            )

        # If no conditions, query all
        query_filter = filter_conditions if filter_conditions["and"] else None

        try:
            response = self.personal_client.databases.query(
                database_id=self.personal_hub_id, filter=query_filter
            )
            return response.get("results", [])
        except Exception as e:
            self.logger.error(f"Error querying personal hub: {e}")
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

        return {
            "id": page.get("id"),
            "task_name": get_text(props.get("Task name")),
            "status": get_status(props.get("Status")),
            "workspace": get_select(props.get("Workspace")),
            "est_duration_hrs": get_number(props.get("Est Duration Hrs")),
            "due_date": get_date(props.get("Due date")),
            "priority": get_select(props.get("Priority")),
            "description": get_text(props.get("Description")),
            "external_notion_id": get_text(props.get("External Notion ID")),
            "updated_at": page.get("last_edited_time"),
            "url": page.get("url"),
        }

    def create_task_in_personal_hub(
        self, task_data: Dict, workspace: str, external_id: str
    ) -> Optional[str]:
        """Create a new task in the personal hub."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would create task '{task_data['task_name']}' in personal hub"
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
        if task_data.get("description"):
            properties["Description"] = {
                "rich_text": [{"text": {"content": task_data["description"]}}]
            }

        try:
            response = self.personal_client.pages.create(
                parent={"database_id": self.personal_hub_id}, properties=properties
            )
            self.logger.info(
                f"✅ Created task '{task_data['task_name']}' in personal hub"
            )
            return response.get("id")
        except Exception as e:
            self.logger.error(f"❌ Error creating task in personal hub: {e}")
            return None

    def update_task_properties(
        self, page_id: str, updates: Dict[str, Any], workspace: str = "Personal"
    ) -> bool:
        """Update properties of an existing task."""
        if self.dry_run:
            self.logger.info(
                f"🧪 DRY RUN: Would update task {page_id} with {list(updates.keys())}"
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
                properties["Workspace"] = {"select": {"name": value}}  # Only in personal hub
            elif field == "est_duration_hrs" and value is not None:
                field_name = field_mapping.get("est_duration_hrs", "Est Duration Hrs")
                properties[field_name] = {"number": value}
            elif field == "due_date" and value:
                field_name = field_mapping.get("due_date", "Due date")
                properties[field_name] = {"date": {"start": value}}
            elif field == "priority" and value:
                field_name = field_mapping.get("priority", "Priority")
                properties[field_name] = {"select": {"name": value}}
            elif field == "description" and value:
                field_name = field_mapping.get("description", "Description")
                properties[field_name] = {
                    "rich_text": [{"text": {"content": value}}]
                }
            elif field == "external_notion_id" and value:
                field_name = field_mapping.get("external_notion_id", "External Notion ID")
                properties[field_name] = {
                    "rich_text": [{"text": {"content": value}}]
                }

        if not properties:
            return True

        try:
            client = self.get_workspace_client(workspace)
            client.pages.update(page_id=page_id, properties=properties)
            self.logger.info(f"✅ Updated task {page_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error updating task {page_id}: {e}")
            return False

    def sync_external_to_personal(
        self, workspace: str, since_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync tasks from external workspace to personal hub."""
        self.logger.info(f"🔄 Syncing {workspace} → Personal Hub")

        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        workspace_db_id = self.get_workspace_databases()[workspace]

        # Get tasks from external workspace
        external_tasks = self.query_assigned_tasks(
            workspace_db_id, workspace, since_date
        )

        # Get existing personal hub tasks for this workspace
        personal_tasks = self.query_personal_hub_tasks(workspace, since_date)
        external_id_map = {}

        for task in personal_tasks:
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
        self.logger.info(
            f"📊 Found {len(personal_tasks)} personal hub tasks for {workspace}"
        )

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
                # Update existing task
                personal_data = self.extract_task_data(existing_personal_task)
                updates = {}

                # Compare fields and build updates
                if external_data["task_name"] != personal_data["task_name"]:
                    updates["task_name"] = external_data["task_name"]
                if external_data["status"] != personal_data["status"]:
                    updates["status"] = external_data["status"]
                if (
                    external_data["est_duration_hrs"]
                    != personal_data["est_duration_hrs"]
                ):
                    updates["est_duration_hrs"] = external_data["est_duration_hrs"]
                if external_data["due_date"] != personal_data["due_date"]:
                    updates["due_date"] = external_data["due_date"]
                if external_data["priority"] != personal_data["priority"]:
                    updates["priority"] = external_data["priority"]
                if external_data["description"] != personal_data["description"]:
                    updates["description"] = external_data["description"]

                if updates:
                    if self.dry_run:
                        self.logger.info(
                            f"🧪 DRY RUN: Would update personal hub task '{personal_data['task_name']}':"
                        )
                        for field, value in updates.items():
                            old_value = personal_data.get(field, "None")
                            self.logger.info(f"  - {field}: '{old_value}' → '{value}'")
                        stats["updated"] += 1
                    else:
                        if self.update_task_properties(
                            personal_data["id"], updates, "Personal"
                        ):
                            stats["updated"] += 1
                        else:
                            stats["errors"] += 1
                else:
                    if self.dry_run:
                        self.logger.info(
                            f"🧪 DRY RUN: Personal hub task '{personal_data['task_name']}' already up to date"
                        )
                    stats["skipped"] += 1
            else:
                # Create new task in personal hub
                new_task_id = self.create_task_in_personal_hub(
                    external_data, workspace, external_id
                )
                if new_task_id:
                    stats["created"] += 1
                else:
                    stats["errors"] += 1

        self.logger.info(f"📊 {workspace} sync complete: {stats}")
        return stats

    def sync_personal_to_external(
        self, workspace: str, since_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync tasks from personal hub back to external workspace."""
        self.logger.info(f"🔄 Syncing Personal Hub → {workspace}")

        stats = {"updated": 0, "skipped": 0, "errors": 0}
        workspace_db_id = self.get_workspace_databases()[workspace]

        # Get personal hub tasks for this workspace
        personal_tasks = self.query_personal_hub_tasks(workspace, since_date)

        for personal_task in personal_tasks:
            personal_data = self.extract_task_data(personal_task)
            external_id = personal_data["external_notion_id"]

            if not external_id:
                stats["skipped"] += 1
                continue

            # Get the external task
            try:
                client = self.get_workspace_client(workspace)
                external_task = client.pages.retrieve(external_id)
                external_data = self.extract_task_data(external_task)

                updates = {}

                # Compare fields and build updates (exclude workspace-specific fields)
                if personal_data["task_name"] != external_data["task_name"]:
                    updates["task_name"] = personal_data["task_name"]
                if personal_data["status"] != external_data["status"]:
                    updates["status"] = personal_data["status"]
                if (
                    personal_data["est_duration_hrs"]
                    != external_data["est_duration_hrs"]
                ):
                    updates["est_duration_hrs"] = personal_data["est_duration_hrs"]
                if personal_data["due_date"] != external_data["due_date"]:
                    updates["due_date"] = personal_data["due_date"]
                if personal_data["priority"] != external_data["priority"]:
                    updates["priority"] = personal_data["priority"]
                if personal_data["description"] != external_data["description"]:
                    updates["description"] = personal_data["description"]

                if updates:
                    if self.dry_run:
                        self.logger.info(
                            f"🧪 DRY RUN: Would update {workspace} task '{personal_data['task_name']}':"
                        )
                        for field, value in updates.items():
                            old_value = external_data.get(field, "None")
                            self.logger.info(f"  - {field}: '{old_value}' → '{value}'")
                        stats["updated"] += 1
                    else:
                        if self.update_task_properties(external_id, updates, workspace):
                            stats["updated"] += 1
                        else:
                            stats["errors"] += 1
                else:
                    if self.dry_run:
                        self.logger.info(
                            f"🧪 DRY RUN: {workspace} task '{personal_data['task_name']}' already up to date"
                        )
                    stats["skipped"] += 1

            except Exception as e:
                self.logger.error(
                    f"❌ Error accessing external task {external_id}: {e}"
                )
                stats["errors"] += 1

        self.logger.info(f"📊 {workspace} reverse sync complete: {stats}")
        return stats

    def sync_full(self) -> Dict[str, Any]:
        """Perform full sync of all tasks."""
        self.logger.info("🚀 Starting FULL sync")
        results = {"workspaces": {}}

        for workspace in self.get_workspace_databases().keys():
            workspace_results = {}

            # External → Personal
            workspace_results["external_to_personal"] = self.sync_external_to_personal(
                workspace
            )

            # Personal → External
            workspace_results["personal_to_external"] = self.sync_personal_to_external(
                workspace
            )

            results["workspaces"][workspace] = workspace_results

        self.logger.info("✅ Full sync completed")
        return results

    def sync_incremental(self) -> Dict[str, Any]:
        """Perform incremental sync of tasks updated in last 24 hours."""
        since_date = datetime.now(timezone.utc) - timedelta(hours=24)
        self.logger.info(
            f"🚀 Starting INCREMENTAL sync (since {since_date.isoformat()})"
        )

        results = {"workspaces": {}, "since_date": since_date.isoformat()}

        for workspace in self.get_workspace_databases().keys():
            workspace_results = {}

            # External → Personal
            workspace_results["external_to_personal"] = self.sync_external_to_personal(
                workspace, since_date
            )

            # Personal → External
            workspace_results["personal_to_external"] = self.sync_personal_to_external(
                workspace, since_date
            )

            results["workspaces"][workspace] = workspace_results

        self.logger.info("✅ Incremental sync completed")
        return results


def main():
    parser = argparse.ArgumentParser(description="Sync Notion tasks between workspaces")
    parser.add_argument(
        "--mode",
        choices=["full", "incremental", "test"],
        required=True,
        help="Sync mode: full (all tasks), incremental (last 24h), test (dry run)",
    )

    args = parser.parse_args()

    try:
        # Initialize sync client
        dry_run = args.mode == "test"
        sync_client = NotionTaskSync(dry_run=dry_run)

        # Run sync based on mode
        if args.mode == "full" or args.mode == "test":
            results = sync_client.sync_full()
        elif args.mode == "incremental":
            results = sync_client.sync_incremental()

        # Print summary
        print("\n" + "=" * 50)
        print("SYNC SUMMARY")
        print("=" * 50)

        for workspace, workspace_results in results.get("workspaces", {}).items():
            print(f"\n{workspace}:")
            ext_to_personal = workspace_results.get("external_to_personal", {})
            personal_to_ext = workspace_results.get("personal_to_external", {})

            print(
                f"  External → Personal: {ext_to_personal.get('created', 0)} created, {ext_to_personal.get('updated', 0)} updated"
            )
            print(f"  Personal → External: {personal_to_ext.get('updated', 0)} updated")

            if ext_to_personal.get("errors", 0) + personal_to_ext.get("errors", 0) > 0:
                print(
                    f"  ⚠️  Errors: {ext_to_personal.get('errors', 0) + personal_to_ext.get('errors', 0)}"
                )

        print(
            f"\n{'🧪 DRY RUN - No changes made' if dry_run else '✅ Sync completed successfully'}"
        )

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
