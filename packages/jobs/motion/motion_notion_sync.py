#!/usr/bin/env python3
"""
Motion ↔ Notion Task Synchronization Script

Bidirectional sync between Motion AI and Notion task databases.
Handles task creation, updates, and field mapping between systems.

Usage:
    python motion_notion_sync.py --mode [full|incremental|test]
    
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
from datetime import datetime, timezone
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
            "Vanquish": os.getenv("MOTION_VANQUISH_WORKSPACE_ID")
        }
        
        # Motion custom field IDs (tied to specific workspaces)
        self.motion_custom_fields = {
            "Personal": {
                "notion_id": "cfi_4G15DQNV797KHaNzQqsxt3",
                "notion_url": "cfi_RBFEnK3uN2Ho2o8XQXdWfv"
            },
            "Livepeer": {
                "notion_id": "cfi_rLcNg95UQ1Cggz2YAnYjsL", 
                "notion_url": "cfi_g85FVuj115igtCPLVCo34t"
            },
            "Vanquish": {
                "notion_id": "cfi_vS8mS9agZUaCDMX88usZXq",
                "notion_url": "cfi_eoBPfnbbCWfS3CnbbYCbD4"
            }
        }
        
        if self.dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no changes will be made")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
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
            "Content-Type": "application/json"
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
            "Vanquish": Client(auth=os.getenv("VANQUISH_NOTION_API_KEY"))
        }
        
        # Database IDs
        self.notion_databases = {
            "Personal": os.getenv("PERSONAL_NOTION_DB_ID"),
            "Livepeer": os.getenv("LIVEPEER_NOTION_DB_ID"),
            "Vanquish": os.getenv("VANQUISH_NOTION_DB_ID")
        }
        
        # User IDs for filtering
        self.notion_user_ids = {
            "Personal": os.getenv("PERSONAL_NOTION_USER_ID"),
            "Livepeer": os.getenv("LIVEPEER_NOTION_USER_ID"),
            "Vanquish": os.getenv("VANQUISH_NOTION_USER_ID")
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
            "ASAP": "URGENT",
            # Motion → Notion
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High", 
            "URGENT": "ASAP"
        }

    def get_status_mapping(self) -> Dict[str, str]:
        """Map status values between Notion and Motion."""
        return {
            # Notion → Motion (adjust based on actual Motion status values)
            "Not started": "TODO",
            "In progress": "IN_PROGRESS", 
            "Completed": "COMPLETED",
            "Canceled": "CANCELLED",
            # Motion → Notion (adjust based on actual Motion status values)
            "TODO": "Not started",
            "IN_PROGRESS": "In progress",
            "COMPLETED": "Completed", 
            "CANCELLED": "Canceled"
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
                text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
                if text.strip():
                    description_parts.append(text)
            
            elif block_type == "heading_1":
                text = self._extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
                if text.strip():
                    description_parts.append(f"# {text}")
            
            elif block_type == "heading_2":
                text = self._extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
                if text.strip():
                    description_parts.append(f"## {text}")
            
            elif block_type == "heading_3":
                text = self._extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
                if text.strip():
                    description_parts.append(f"### {text}")
            
            elif block_type == "bulleted_list_item":
                text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
                if text.strip():
                    description_parts.append(f"• {text}")
            
            elif block_type == "numbered_list_item":
                text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
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
    
    def motion_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Motion API."""
        # Handle beta endpoints that use different base URL
        if endpoint.startswith('/beta/') or endpoint.startswith('beta/'):
            url = f"https://api.usemotion.com/{endpoint.lstrip('/')}"
        else:
            url = f"{self.motion_base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.motion_headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.motion_headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.motion_headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.motion_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Add delay to respect rate limits
            time.sleep(0.2)  # 200ms delay between requests
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Motion API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response: {e.response.text}")
            
            # Handle rate limiting with exponential backoff
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                self.logger.warning("Rate limit hit, waiting 30 seconds before retry...")
                time.sleep(30)
                # Don't retry automatically to avoid infinite loops
            
            raise

    def get_motion_tasks(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all tasks from Motion workspace."""
        try:
            response = self.motion_request("GET", f"tasks?workspaceId={workspace_id}")
            return response.get("tasks", [])
        except Exception as e:
            self.logger.error(f"Failed to get Motion tasks for workspace {workspace_id}: {e}")
            return []

    def create_motion_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new task in Motion."""
        if self.dry_run:
            self.logger.info(f"🧪 DRY RUN: Would create Motion task: {task_data.get('name', 'Unknown')}")
            return "dry-run-motion-id"
        
        try:
            response = self.motion_request("POST", "tasks", task_data)
            task_id = response.get("id")
            self.logger.info(f"✅ Created Motion task: {task_data.get('name', 'Unknown')} (ID: {task_id})")
            return task_id
        except Exception as e:
            self.logger.error(f"Failed to create Motion task: {e}")
            return None

    def update_motion_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing Motion task."""
        if self.dry_run:
            self.logger.info(f"🧪 DRY RUN: Would update Motion task {task_id} with: {list(updates.keys())}")
            return True
        
        try:
            self.motion_request("PATCH", f"tasks/{task_id}", updates)
            self.logger.info(f"✅ Updated Motion task {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update Motion task {task_id}: {e}")
            return False

    def set_motion_custom_fields(self, task_id: str, workspace: str, notion_id: str, notion_url: str) -> bool:
        """Set custom field values for a Motion task."""
        if self.dry_run:
            self.logger.info(f"🧪 DRY RUN: Would set custom fields for Motion task {task_id}")
            return True
        
        try:
            custom_fields = self.motion_custom_fields[workspace]
            
            # Set Notion ID custom field
            notion_id_data = {
                "customFieldInstanceId": custom_fields["notion_id"],
                "value": {
                    "type": "text",
                    "value": notion_id
                }
            }
            self.motion_request("POST", f"/beta/custom-field-values/task/{task_id}", notion_id_data)
            
            # Set Notion URL custom field  
            notion_url_data = {
                "customFieldInstanceId": custom_fields["notion_url"],
                "value": {
                    "type": "url",
                    "value": notion_url
                }
            }
            self.motion_request("POST", f"/beta/custom-field-values/task/{task_id}", notion_url_data)
            
            self.logger.info(f"✅ Set custom fields for Motion task {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set custom fields for Motion task {task_id}: {e}")
            return False

    # === NOTION API METHODS ===
    
    def get_notion_tasks(self, workspace: str) -> List[Dict[str, Any]]:
        """Get all tasks from Notion database for a workspace."""
        client = self.workspace_clients[workspace]
        database_id = self.notion_databases[workspace]
        user_id = self.notion_user_ids[workspace]
        
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
        
        try:
            response = client.databases.query(
                database_id=database_id,
                filter=filter_conditions
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
            "status": get_select(props.get("Status")),
            "workspace": get_select(props.get("Workspace")),
            "est_duration_hrs": get_number(props.get("Est Duration Hrs")),
            "due_date": get_date(props.get("Due date")),
            "priority": get_select(props.get("Priority")),
            "description": get_text(props.get("Description")),
            "motion_id": get_text(props.get("Motion ID")),
            "updated_at": page.get("last_edited_time"),
            "url": page.get("url"),
        }

    # === SYNC LOGIC ===
    
    def sync_notion_to_motion(self, workspace: str, max_tasks: Optional[int] = None) -> Dict[str, int]:
        """Sync tasks from Notion to Motion."""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        notion_tasks = self.get_notion_tasks(workspace)
        motion_workspace_id = self.motion_workspaces[workspace]
        
        if not motion_workspace_id:
            self.logger.error(f"No Motion workspace ID configured for {workspace}")
            return stats
        
        # Limit tasks for testing if specified
        if max_tasks is not None:
            notion_tasks = notion_tasks[:max_tasks]
            self.logger.info(f"📊 Found {len(self.get_notion_tasks(workspace))} Notion tasks in {workspace}, limiting to {len(notion_tasks)} for testing")
        else:
            self.logger.info(f"📊 Found {len(notion_tasks)} Notion tasks in {workspace}")
        
        for notion_task in notion_tasks:
            notion_data = self.extract_notion_task_data(notion_task)
            motion_id = notion_data.get("motion_id")
            
            if motion_id:
                # Update existing Motion task
                if self._update_motion_from_notion(motion_id, notion_data, workspace):
                    stats["updated"] += 1
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

    def _create_motion_from_notion(self, notion_data: Dict[str, Any], workspace: str) -> bool:
        """Create a new Motion task from Notion data."""
        try:
            # Get Notion blocks for description
            blocks = []
            if notion_data["id"]:
                blocks_response = self.workspace_clients[workspace].blocks.children.list(
                    block_id=notion_data["id"]
                )
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
                "duration": self.convert_hours_to_minutes(notion_data["est_duration_hrs"]),
            }
            
            # Add due date if present
            if notion_data["due_date"]:
                due_date = self.extract_due_date_start(notion_data["due_date"])
                if due_date:
                    motion_task_data["dueDate"] = due_date
            
            # Custom fields will be set after task creation via separate API call
            
            # Set auto-scheduling for work hours
            motion_task_data["autoScheduled"] = {
                "schedule": "Work Hours"
            }
            
            # Create Motion task
            motion_id = self.create_motion_task(motion_task_data)
            
            if motion_id:
                # Set custom fields for back-reference to Notion
                if self.set_motion_custom_fields(motion_id, workspace, notion_data["id"], notion_data["url"]):
                    # Update Notion with Motion ID
                    if not self.dry_run:
                        self._update_notion_motion_id(notion_data["id"], motion_id, workspace)
                    return True
                else:
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create Motion task from Notion: {e}")
            return False

    def _update_motion_from_notion(self, motion_id: str, notion_data: Dict[str, Any], workspace: str) -> bool:
        """Update existing Motion task with Notion data."""
        try:
            # Get Notion blocks for description
            blocks = []
            if notion_data["id"]:
                blocks_response = self.workspace_clients[workspace].blocks.children.list(
                    block_id=notion_data["id"]
                )
                blocks = blocks_response.get("results", [])
            
            # Build update data
            priority_map = self.get_priority_mapping()
            status_map = self.get_status_mapping()
            
            updates = {
                "name": notion_data["task_name"],
                "description": self.blocks_to_description(blocks),
                "priority": priority_map.get(notion_data["priority"], "MEDIUM"),
                "status": status_map.get(notion_data["status"], "TODO"),
                "duration": self.convert_hours_to_minutes(notion_data["est_duration_hrs"]),
            }
            
            # Add due date if present
            if notion_data["due_date"]:
                due_date = self.extract_due_date_start(notion_data["due_date"])
                if due_date:
                    updates["dueDate"] = due_date
            
            # Set auto-scheduling for work hours
            updates["autoScheduled"] = {
                "schedule": "Work Hours"
            }
            
            return self.update_motion_task(motion_id, updates)
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                self.logger.warning(f"Motion task {motion_id} not found - may have been deleted. Clearing Motion ID from Notion.")
                # Clear the Motion ID from Notion since the task no longer exists
                try:
                    if not self.dry_run:
                        self.workspace_clients[workspace].pages.update(
                            page_id=notion_data["id"],
                            properties={"Motion ID": {"rich_text": []}}
                        )
                        self.logger.info(f"✅ Cleared orphaned Motion ID {motion_id} from Notion task")
                except Exception as clear_error:
                    self.logger.error(f"Failed to clear Motion ID from Notion: {clear_error}")
                return False
            else:
                self.logger.error(f"Failed to update Motion task {motion_id}: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to update Motion task {motion_id}: {e}")
            return False

    def _update_notion_motion_id(self, notion_id: str, motion_id: str, workspace: str):
        """Update Notion task with Motion ID."""
        try:
            client = self.workspace_clients[workspace]
            client.pages.update(
                page_id=notion_id,
                properties={
                    "Motion ID": {
                        "rich_text": [{"text": {"content": motion_id}}]
                    }
                }
            )
            self.logger.info(f"✅ Updated Notion task {notion_id} with Motion ID {motion_id}")
        except Exception as e:
            self.logger.error(f"Failed to update Notion task with Motion ID: {e}")

    def sync_full(self, test_mode: bool = False) -> Dict[str, Any]:
        """Perform full sync of all tasks."""
        mode_label = "TEST (1 task limit)" if test_mode else "FULL"
        self.logger.info(f"🚀 Starting {mode_label} Motion ↔ Notion sync")
        results = {"workspaces": {}}
        
        for workspace in ["Personal", "Livepeer", "Vanquish"]:
            self.logger.info(f"🔄 Syncing {workspace}")
            
            workspace_results = {}
            
            # Notion → Motion (limit to 1 task in test mode)
            max_tasks = 1 if test_mode else None
            workspace_results["notion_to_motion"] = self.sync_notion_to_motion(workspace, max_tasks=max_tasks)
            
            # TODO: Motion → Notion sync
            # workspace_results["motion_to_notion"] = self.sync_motion_to_notion(workspace)
            
            results["workspaces"][workspace] = workspace_results
        
        self.logger.info(f"✅ {mode_label} Motion ↔ Notion sync completed")
        return results


def main():
    parser = argparse.ArgumentParser(description="Sync tasks between Motion AI and Notion")
    parser.add_argument(
        "--mode",
        choices=["full", "incremental", "test", "test-real"],
        required=True,
        help="Sync mode: full (all tasks), incremental (last 24h), test (dry run), test-real (1 task real update)",
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
        elif args.mode == "incremental":
            # TODO: Implement incremental sync
            results = sync_client.sync_full()  # Fallback to full for now
        
        # Print summary
        print("\n" + "=" * 50)
        print("MOTION ↔ NOTION SYNC SUMMARY")
        print("=" * 50)
        
        total_errors = 0
        for workspace, workspace_results in results.get("workspaces", {}).items():
            print(f"\n{workspace}:")
            notion_to_motion = workspace_results.get("notion_to_motion", {})
            
            print(
                f"  Notion → Motion: {notion_to_motion.get('created', 0)} created, {notion_to_motion.get('updated', 0)} updated"
            )
            
            workspace_errors = notion_to_motion.get("errors", 0)
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
