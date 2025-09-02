#!/usr/bin/env python3
"""
Task creation service - extracted from the original task_creator.py
"""

import base64
import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import openai
import requests
from notion_client import Client as NotionClient
from utils.config import config


class TaskCreationService:
    """Service for creating tasks using AI and Notion integration."""

    def __init__(self, dry_run: bool = False):
        """Initialize the task creation service."""
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

        # Initialize OpenAI client
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

        # Initialize Notion client for personal hub
        if not config.PERSONAL_NOTION_API_KEY:
            raise ValueError("PERSONAL_NOTION_API_KEY environment variable is required")
        self.notion_client = NotionClient(auth=config.PERSONAL_NOTION_API_KEY)

    def extract_urls_from_text(self, text: str) -> List[str]:
        """Extract URLs from text using regex."""
        # Regular expression to match URLs
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        urls = re.findall(url_pattern, text)
        return urls

    def extract_all_urls_from_inputs(self, text_inputs: List[str]) -> List[str]:
        """Extract all URLs from the provided text inputs."""
        all_urls = []
        for text in text_inputs:
            urls = self.extract_urls_from_text(text)
            all_urls.extend(urls)
        return list(set(all_urls))  # Remove duplicates

    def convert_markdown_to_notion_rich_text(self, text: str) -> List[Dict]:
        """Convert markdown text (including URLs) to Notion rich text format."""
        rich_text = []

        # Pattern to match markdown links: [text](url)
        markdown_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        # Pattern to match plain URLs
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

        # Split text by markdown links first
        parts = re.split(markdown_link_pattern, text)

        i = 0
        while i < len(parts):
            part = parts[i]

            # If this is a text part (not a link), check for plain URLs
            if i % 3 == 0:  # Text parts are at indices 0, 3, 6, etc.
                # Split by plain URLs
                url_parts = re.split(f"({url_pattern})", part)
                for j, url_part in enumerate(url_parts):
                    if url_part:
                        if re.match(url_pattern, url_part):
                            # This is a plain URL
                            rich_text.append(
                                {
                                    "type": "text",
                                    "text": {
                                        "content": url_part,
                                        "link": {"url": url_part},
                                    },
                                }
                            )
                        else:
                            # This is regular text
                            rich_text.append(
                                {"type": "text", "text": {"content": url_part}}
                            )
            elif i % 3 == 1:  # Link text parts
                link_text = part
                link_url = parts[i + 1] if i + 1 < len(parts) else ""
                if link_url:
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": link_text, "link": {"url": link_url}},
                        }
                    )
                i += 1  # Skip the URL part since we've processed it

            i += 1

        return rich_text

    def extract_text_from_image_url(self, image_url: str) -> str:
        """Extract text from an image URL using OpenAI Vision API."""
        try:
            self.logger.info(f"📸 Extracting text from image: {image_url}")

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text content from this image. Include any visible text, labels, captions, or written content. Return only the extracted text without additional commentary.",
                            },
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                max_tokens=1000,
            )

            extracted_text = response.choices[0].message.content
            self.logger.info(
                f"✅ Extracted {len(extracted_text)} characters from image"
            )
            return extracted_text

        except Exception as e:
            self.logger.error(f"Error extracting text from image {image_url}: {e}")
            return f"[Error extracting text from image: {e}]"

    def synthesize_task_info(
        self,
        text_inputs: List[str],
        image_texts: List[str] = None,
        suggested_workspace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesize task information from inputs using AI."""

        if image_texts is None:
            image_texts = []

        # Prepare workspace guidance
        workspace_guidance = ""
        if suggested_workspace:
            workspace_guidance = (
                f"\nThe user has suggested workspace: {suggested_workspace}"
            )

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")

        system_prompt = f"""You are an expert task creation assistant. Your job is to analyze the provided information and create a well-structured task definition.

CURRENT DATE CONTEXT:
- Today is {current_date} ({current_day})
- Use this to calculate relative dates like 'tomorrow', 'next Friday', etc.

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
    "due_date": "YYYY-MM-DD format (e.g., 2025-01-15)",
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

4. DUE DATE DETECTION (look for these clues):
   - "today", "by end of day" → today's date
   - "tomorrow", "by tomorrow" → tomorrow's date
   - "by Friday", "this Friday" → next Friday
   - "next week", "by next week" → 7 days from now
   - "end of week", "by EOW" → next Friday
   - "next Monday", "by Monday" → next Monday
   - "in 2 days", "2 days from now" → 2 days from now
   - "by [specific date]" → parse the specific date
   - Default to 7 days from now if no clear due date clues

GUIDELINES:
- Task name should be specific and actionable
- Parse the input text carefully for workspace/priority/duration clues
- Description should be comprehensive but concise
- Acceptance criteria should be specific, measurable, and formatted as a markdown checklist
- PRESERVE ALL URLs: Include any URLs found in the input text in the description or acceptance criteria as clickable links

URL HANDLING:
- If URLs are found in the input, include them in the description as supporting materials
- Format URLs as markdown links when possible: [Link Text](URL)
- If the URL context is unclear, label it as "Supporting Material: [URL]"
- URLs should be preserved exactly as provided

ACCEPTANCE CRITERIA FORMAT:
Format acceptance criteria as a markdown checklist like:
- [ ] First acceptance criterion
- [ ] Second acceptance criterion  
- [ ] Third acceptance criterion"""

        # Extract URLs from text inputs
        extracted_urls = self.extract_all_urls_from_inputs(text_inputs)
        if extracted_urls:
            self.logger.info(
                f"🔗 Found {len(extracted_urls)} URL(s) in text inputs: {extracted_urls}"
            )

        # Combine all inputs
        all_inputs = text_inputs + image_texts
        combined_input = "\n\n".join(all_inputs)

        # Add URL information to prompt if URLs were found
        url_instruction = ""
        if extracted_urls:
            url_list = "\n".join([f"- {url}" for url in extracted_urls])
            url_instruction = f"""

IMPORTANT: The following URLs were found in the input and MUST be preserved in the task:
{url_list}

Please include these URLs in the description or acceptance criteria as supporting materials."""

        user_prompt = f"""Please analyze the following information and create a structured task definition:

{combined_input}{url_instruction}

Return only the JSON response with the task information."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            response_text = response.choices[0].message.content.strip()

            # Clean up response text (remove markdown code blocks if present)
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            task_info = json.loads(response_text)

            # Apply sensible defaults if AI didn't provide them
            task_info["workspace"] = task_info.get("workspace", "Personal")
            task_info["priority"] = task_info.get("priority", "Medium")
            task_info["estimated_hours"] = task_info.get("estimated_hours", 1.0)

            # Default due date to 7 days from now if not provided
            if not task_info.get("due_date"):
                default_due_date = (datetime.now() + timedelta(days=7)).strftime(
                    "%Y-%m-%d"
                )
                task_info["due_date"] = default_due_date

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

            # Validate estimated hours
            if (
                not isinstance(task_info["estimated_hours"], (int, float))
                or task_info["estimated_hours"] <= 0
            ):
                self.logger.warning(
                    f"Invalid estimated_hours '{task_info['estimated_hours']}', defaulting to 1.0"
                )
                task_info["estimated_hours"] = 1.0

            self.logger.info("🤖 AI successfully synthesized task information")
            self.logger.info(f"📋 Task: {task_info.get('task_name', 'Unknown')}")
            self.logger.info(f"🏢 Workspace: {task_info.get('workspace', 'Unknown')}")
            self.logger.info(f"⚡ Priority: {task_info.get('priority', 'Unknown')}")
            self.logger.info(
                f"⏱️  Duration: {task_info.get('estimated_hours', 'Unknown')} hours"
            )
            self.logger.info(f"📅 Due Date: {task_info.get('due_date', 'Unknown')}")
            self.logger.info(
                f"📝 Description: {task_info.get('description', 'No description')}"
            )
            self.logger.info(
                f"✅ Acceptance Criteria: {task_info.get('acceptance_criteria', 'No criteria')}"
            )

            return task_info

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            self.logger.error(f"Raw response: {response_text}")
            raise ValueError(f"Invalid JSON response from AI: {e}")
        except Exception as e:
            self.logger.error(f"Error synthesizing task info: {e}")
            raise

    def create_notion_task(self, task_info: Dict[str, Any]) -> Optional[str]:
        """Create a task in Notion and return the page ID."""

        workspace = task_info["workspace"]
        # Always create in personal database - sync jobs will handle distribution
        database_id = config.PERSONAL_NOTION_DB_ID

        if not database_id:
            raise ValueError("PERSONAL_NOTION_DB_ID environment variable is required")

        # Build description content (rich text blocks)
        description_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Description"}}]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": self.convert_markdown_to_notion_rich_text(
                        task_info["description"]
                    )
                },
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Acceptance Criteria"}}
                    ]
                },
            },
        ]

        # Parse acceptance criteria and create checklist items
        acceptance_criteria = task_info["acceptance_criteria"]
        if acceptance_criteria:
            # Split by newlines and create checklist items
            criteria_lines = [
                line.strip() for line in acceptance_criteria.split("\n") if line.strip()
            ]

            for line in criteria_lines:
                # Remove markdown checkbox syntax and create proper Notion to-do blocks
                clean_text = (
                    line.replace("- [ ]", "")
                    .replace("- [x]", "")
                    .replace("- [ ] ", "")
                    .replace("- [x] ", "")
                    .strip()
                )
                if clean_text:
                    description_blocks.append(
                        {
                            "object": "block",
                            "type": "to_do",
                            "to_do": {
                                "rich_text": self.convert_markdown_to_notion_rich_text(
                                    clean_text
                                ),
                                "checked": False,
                            },
                        }
                    )
        else:
            # Fallback if no acceptance criteria
            description_blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "No acceptance criteria specified"},
                            }
                        ]
                    },
                }
            )

            # Create page properties (matching the existing Notion sync field names)
        properties = {
            "Task name": {
                "title": [{"type": "text", "text": {"content": task_info["task_name"]}}]
            },
            "Workspace": {"select": {"name": workspace}},
            "Priority": {"select": {"name": task_info["priority"]}},
            "Est Duration Hrs": {"number": task_info["estimated_hours"]},
            "Due date": {"date": {"start": task_info["due_date"]}},
            "Status": {"status": {"name": "Todo"}},
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
        image_urls: List[str] = None,
        suggested_workspace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main method to create a task from various inputs."""

        self.logger.info("🚀 Starting AI task creation")

        # Process images if provided
        image_texts = []
        if image_urls:
            for image_url in image_urls:
                extracted_text = self.extract_text_from_image_url(image_url)
                image_texts.append(f"--- From {image_url} ---\n{extracted_text}")

        # Synthesize task information
        task_info = self.synthesize_task_info(
            text_inputs, image_texts, suggested_workspace
        )

        # Create the task
        page_id = self.create_notion_task(task_info)

        return {
            "task_info": task_info,
            "page_id": page_id,
            "page_url": (
                f"https://www.notion.so/{page_id.replace('-', '')}" if page_id else None
            ),
        }
