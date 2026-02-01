#!/usr/bin/env python3
"""
Task creation tool definitions for OpenAI function calling.

These tools allow the agent to create tasks based on user requests.
"""

from typing import Any, Dict

# Tool definitions for OpenAI
TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": (
                "Create a new task in Notion. Use this when the user wants to create "
                "a task, add something to their to-do list, or schedule work to be done. "
                "The task description should include all relevant details from the conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": (
                            "Full description of the task including context, requirements, "
                            "and any relevant information from the conversation."
                        ),
                    },
                    "suggested_workspace": {
                        "type": "string",
                        "enum": ["Personal", "Livepeer", "Vanquish"],
                        "description": "Suggested workspace for the task.",
                    },
                },
                "required": ["description"],
            },
        },
    },
]


def execute_task_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    task_service: Any,
) -> Dict[str, Any]:
    """
    Execute a task tool and return results.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        task_service: Initialized TaskCreationService instance

    Returns:
        Tool execution result as a dictionary
    """
    try:
        if tool_name == "create_task":
            # Use the task creation service
            result = task_service.create_task_from_inputs(
                text_inputs=[arguments.get("description", "")],
                image_urls=None,
                suggested_workspace=arguments.get("suggested_workspace"),
            )

            task_info = result["task_info"]
            return {
                "success": True,
                "data": {
                    "task_name": task_info.get("task_name"),
                    "workspace": task_info.get("workspace"),
                    "priority": task_info.get("priority"),
                    "estimated_hours": task_info.get("estimated_hours"),
                    "due_date": task_info.get("due_date"),
                    "task_id": result.get("page_id"),
                    "task_url": result.get("page_url"),
                },
                "summary": (
                    f"Created task '{task_info.get('task_name')}' "
                    f"in {task_info.get('workspace')} workspace."
                ),
            }

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
