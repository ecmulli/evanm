#!/usr/bin/env python3
"""
AI Task Creation Agent

Synthesizes information from various sources (text, quotes, screenshots)
and creates well-structured Notion tasks using AI.

Usage:
    python agent/task_creator.py --input "text description" --workspace Personal
    python agent/task_creator.py --file input.txt --screenshots img1.png,img2.png

Environment Variables Required:
    OPENAI_API_KEY - OpenAI API token for ChatGPT
    PERSONAL_NOTION_API_KEY - Notion Personal Hub API token
    PERSONAL_NOTION_DB_ID - Personal hub database ID

Author: AI Task Creation Agent
"""

import argparse
import base64
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
import openai
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.dev"))


class TaskCreationAgent:
    """AI-powered agent that creates Notion tasks from synthesized information."""

    def __init__(self, dry_run: bool = False):
        """Initialize the agent with API clients."""
        self.dry_run = dry_run
        self.logger = self._setup_logging()

        # Initialize OpenAI
        self.openai_client = self._init_openai()

        # Initialize Notion
        self.notion_client = self._init_notion()

        # Workspace mapping
        self.workspace_db_mapping = {
            "Personal": os.getenv("PERSONAL_NOTION_DB_ID"),
            "Livepeer": os.getenv("LIVEPEER_NOTION_DB_ID"),
            "Vanquish": os.getenv("VANQUISH_NOTION_DB_ID"),
        }

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logger = logging.getLogger(__name__)

        if self.dry_run:
            logger.info("🧪 Running in DRY RUN mode - no tasks will be created")

        return logger

    def _init_openai(self) -> openai.OpenAI:
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return openai.OpenAI(api_key=api_key)

    def _init_notion(self) -> Client:
        """Initialize Notion client."""
        api_key = os.getenv("PERSONAL_NOTION_API_KEY")
        if not api_key:
            raise ValueError("PERSONAL_NOTION_API_KEY environment variable is required")

        return Client(auth=api_key)

    def read_file(self, file_path: str) -> str:
        """Read text content from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return ""

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from an image using OpenAI Vision API."""
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            # Get file extension for MIME type
            file_ext = Path(image_path).suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(file_ext, "image/png")

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text content from this image. Include any UI text, error messages, user feedback, or other readable content. Be thorough and accurate.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )

            extracted_text = response.choices[0].message.content
            self.logger.info(f"📸 Extracted text from {image_path}")
            return extracted_text

        except Exception as e:
            self.logger.error(f"Error extracting text from {image_path}: {e}")
            return f"[Error extracting text from {image_path}]"

    def synthesize_task_info(
        self,
        text_inputs: List[str],
        image_texts: List[str],
        suggested_workspace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Use AI to synthesize information into a structured task."""

        # Combine all inputs
        combined_input = "\n\n".join(
            [
                "=== TEXT INPUTS ===",
                *text_inputs,
                "=== SCREENSHOT/IMAGE CONTENT ===",
                *image_texts,
            ]
        )

        workspace_guidance = ""
        if suggested_workspace:
            workspace_guidance = (
                f"\nThe user has suggested workspace: {suggested_workspace}"
            )

        system_prompt = f"""You are an expert task creation assistant. Your job is to analyze the provided information and create a well-structured task definition.

AVAILABLE WORKSPACES:
- Personal: Personal projects and tasks (DEFAULT)
- Livepeer: Livepeer/streaming technology company work  
- Vanquish: Vanquish/marketing agency client work{workspace_guidance}

RESPONSE FORMAT (JSON):
{{
    "task_name": "Clear, actionable task title (max 100 chars)",
    "workspace": "Personal|Livepeer|Vanquish",
    "priority": "Low|Medium|High|ASAP", 
    "estimated_hours": <number between 0.25 and 40>,
    "description": "Detailed description of what needs to be done",
    "acceptance_criteria": "Clear, testable criteria for completion"
}}

INTELLIGENT PARSING RULES:
1. WORKSPACE DETECTION (look for these clues):
   - "Livepeer", "streaming", "video", "analytics dashboard" → Livepeer
   - "Vanquish", "client", "marketing", "campaign", "ads" → Vanquish  
   - Default to "Personal" if no clear workspace clues

2. PRIORITY DETECTION (look for these clues):
   - "urgent", "ASAP", "blocking", "critical", "emergency" → ASAP
   - "high priority", "important", "soon", "deadline" → High
   - "low priority", "nice to have", "eventually", "when time" → Low
   - Default to "Medium" if no clear priority clues

3. DURATION ESTIMATION (look for these clues):
   - "quick", "15 min", "15 minutes" → 0.25 hours
   - "30 min", "30 minutes", "half hour" → 0.5 hours  
   - "1 hour", "1hr", "hour task" → 1 hour
   - "2 hours", "2hrs", "couple hours" → 2 hours
   - "half day", "4 hours" → 4 hours
   - "full day", "8 hours", "day task" → 8 hours
   - "week", "40 hours" → 40 hours
   - Default to 1 hour if no clear duration clues

GUIDELINES:
- Task name should be specific and actionable
- Parse the input text carefully for workspace/priority/duration clues
- Description should be comprehensive but concise
- Acceptance criteria should be specific, measurable, and formatted as a markdown checklist
- Use the intelligent parsing rules above, but apply common sense

ACCEPTANCE CRITERIA FORMAT:
Format acceptance criteria as a markdown checklist using this pattern:
- [ ] First specific, testable criterion
- [ ] Second specific, testable criterion  
- [ ] Third specific, testable criterion
- [ ] Final verification step

Example: "- [ ] Dashboard loads in under 3 seconds\n- [ ] All charts display correct data\n- [ ] No console errors present\n- [ ] Performance metrics improved by 50%"

Analyze the input and respond with ONLY the JSON object:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": combined_input},
                ],
                temperature=0.3,  # Lower temperature for more consistent outputs
                max_tokens=1000,
            )

            response_text = response.choices[0].message.content.strip()

            # Parse JSON response
            if response_text.startswith("```json"):
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            task_info = json.loads(response_text)

            # Apply sensible defaults if AI didn't provide them
            task_info["workspace"] = task_info.get("workspace", "Personal")
            task_info["priority"] = task_info.get("priority", "Medium")
            task_info["estimated_hours"] = task_info.get("estimated_hours", 1.0)

            # Validate workspace
            if task_info["workspace"] not in ["Personal", "Livepeer", "Vanquish"]:
                self.logger.warning(
                    f"Invalid workspace '{task_info['workspace']}', defaulting to Personal"
                )
                task_info["workspace"] = "Personal"

            # Validate priority
            if task_info["priority"] not in ["Low", "Medium", "High", "ASAP"]:
                self.logger.warning(
                    f"Invalid priority '{task_info['priority']}', defaulting to Medium"
                )
                task_info["priority"] = "Medium"

            # Validate duration
            if (
                not isinstance(task_info["estimated_hours"], (int, float))
                or task_info["estimated_hours"] <= 0
            ):
                self.logger.warning(
                    f"Invalid duration '{task_info['estimated_hours']}', defaulting to 1 hour"
                )
                task_info["estimated_hours"] = 1.0

            self.logger.info("🤖 AI successfully synthesized task information")
            self.logger.info(f"📋 Task: {task_info.get('task_name', 'Unknown')}")
            self.logger.info(f"🏢 Workspace: {task_info.get('workspace', 'Unknown')}")
            self.logger.info(f"⚡ Priority: {task_info.get('priority', 'Unknown')}")
            self.logger.info(
                f"⏱️  Duration: {task_info.get('estimated_hours', 'Unknown')} hours"
            )
            self.logger.info(
                f"📝 Description: {task_info.get('description', 'No description')}"
            )
            self.logger.info(
                f"✅ Acceptance Criteria: {task_info.get('acceptance_criteria', 'No criteria')}"
            )

            return task_info

        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing AI response as JSON: {e}")
            self.logger.error(f"Raw response: {response_text}")
            raise
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            raise

    def create_notion_task(self, task_info: Dict[str, Any]) -> Optional[str]:
        """Create a task in the appropriate Notion database."""

        workspace = task_info["workspace"]
        database_id = self.workspace_db_mapping.get(workspace)

        if not database_id:
            raise ValueError(f"No database ID configured for workspace: {workspace}")

        # Build description content (rich text blocks)
        description_blocks = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": task_info["description"]}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Acceptance Criteria"}}
                    ]
                },
            }
        ]
        
        # Parse acceptance criteria and create checklist items
        acceptance_criteria = task_info["acceptance_criteria"]
        if acceptance_criteria:
            # Split by newlines and create checklist items
            criteria_lines = [line.strip() for line in acceptance_criteria.split('\n') if line.strip()]
            
            for line in criteria_lines:
                # Remove markdown checkbox syntax and create proper Notion to-do blocks
                clean_text = line.replace('- [ ]', '').replace('- [x]', '').replace('- [ ] ', '').replace('- [x] ', '').strip()
                if clean_text:
                    description_blocks.append({
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [
                                {"type": "text", "text": {"content": clean_text}}
                            ],
                            "checked": False
                        }
                    })
        else:
            # Fallback if no acceptance criteria
            description_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "No acceptance criteria specified"}}
                    ]
                },
            })

        # Create page properties
        properties = {
            "Task name": {
                "title": [{"type": "text", "text": {"content": task_info["task_name"]}}]
            },
            "Workspace": {"select": {"name": workspace}},
            "Priority": {"select": {"name": task_info["priority"]}},
            "Est Duration Hrs": {"number": task_info["estimated_hours"]},
            "Status": {"status": {"name": "Not started"}},
        }

        if self.dry_run:
            self.logger.info(f"🧪 DRY RUN: Would create task in {workspace} database")
            return None

        try:
            # Create the page
            response = self.notion_client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=description_blocks,
            )

            page_id = response["id"]
            page_url = response["url"]

            self.logger.info(
                f"✅ Created task '{task_info['task_name']}' in {workspace}"
            )
            self.logger.info(f"📝 Notion URL: {page_url}")

            return page_id

        except Exception as e:
            self.logger.error(f"Error creating Notion task: {e}")
            raise

    def create_task_from_inputs(
        self,
        text_inputs: List[str],
        image_paths: List[str] = None,
        suggested_workspace: Optional[str] = None,
    ) -> Optional[str]:
        """Main method to create a task from various inputs."""

        self.logger.info("🚀 Starting AI task creation")

        # Process images if provided
        image_texts = []
        if image_paths:
            for image_path in image_paths:
                if os.path.exists(image_path):
                    extracted_text = self.extract_text_from_image(image_path)
                    image_texts.append(f"--- From {image_path} ---\n{extracted_text}")
                else:
                    self.logger.warning(f"Image file not found: {image_path}")

        # Synthesize task information
        task_info = self.synthesize_task_info(
            text_inputs, image_texts, suggested_workspace
        )

        # Create the task
        page_id = self.create_notion_task(task_info)

        return page_id


def main():
    """CLI interface for the task creation agent."""
    parser = argparse.ArgumentParser(description="AI Task Creation Agent")
    parser.add_argument("--input", "-i", type=str, help="Direct text input")
    parser.add_argument("--file", "-f", type=str, help="Path to text file")
    parser.add_argument(
        "--screenshots", "-s", type=str, help="Comma-separated image paths"
    )
    parser.add_argument(
        "--workspace",
        "-w",
        type=str,
        choices=["Personal", "Livepeer", "Vanquish"],
        help="Suggested workspace",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no task creation)"
    )

    args = parser.parse_args()

    if not args.input and not args.file and not args.screenshots:
        parser.error("Must provide at least one of: --input, --file, or --screenshots")

    # Initialize agent
    agent = TaskCreationAgent(dry_run=args.dry_run)

    # Collect text inputs
    text_inputs = []

    if args.input:
        text_inputs.append(args.input)

    if args.file:
        file_content = agent.read_file(args.file)
        if file_content:
            text_inputs.append(file_content)

    # Process screenshots
    image_paths = []
    if args.screenshots:
        image_paths = [path.strip() for path in args.screenshots.split(",")]

    try:
        page_id = agent.create_task_from_inputs(
            text_inputs=text_inputs,
            image_paths=image_paths,
            suggested_workspace=args.workspace,
        )

        if page_id:
            print(f"\n🎉 Task created successfully!")
            print(f"📋 Page ID: {page_id}")
        elif args.dry_run:
            print(f"\n🧪 Dry run completed - no task created")
        else:
            print(f"\n❌ Task creation failed")

    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
