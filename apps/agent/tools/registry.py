#!/usr/bin/env python3
"""
Tool registry for the agent.

Centralizes all available tools and provides dispatch logic.
"""

from typing import Any, Callable, Dict, List, Optional

from tools.enphase_tools import ENPHASE_TOOLS, execute_enphase_tool
from tools.task_tools import TASK_TOOLS, execute_task_tool


# Registry mapping tool names to their definitions and handlers
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Register Enphase tools
for tool in ENPHASE_TOOLS:
    tool_name = tool["function"]["name"]
    TOOL_REGISTRY[tool_name] = {
        "definition": tool,
        "category": "enphase",
        "handler": "enphase",
    }

# Register Task tools
for tool in TASK_TOOLS:
    tool_name = tool["function"]["name"]
    TOOL_REGISTRY[tool_name] = {
        "definition": tool,
        "category": "task",
        "handler": "task",
    }


def get_all_tools(
    include_enphase: bool = True,
    include_tasks: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get all available tool definitions for OpenAI.

    Args:
        include_enphase: Whether to include Enphase solar tools
        include_tasks: Whether to include task creation tools

    Returns:
        List of tool definitions in OpenAI format
    """
    tools = []

    if include_enphase:
        tools.extend(ENPHASE_TOOLS)

    if include_tasks:
        tools.extend(TASK_TOOLS)

    return tools


def get_tool_handler(tool_name: str) -> Optional[str]:
    """
    Get the handler type for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Handler type string ("enphase", "task") or None if not found
    """
    if tool_name in TOOL_REGISTRY:
        return TOOL_REGISTRY[tool_name]["handler"]
    return None


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    enphase_service: Optional[Any] = None,
    task_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Execute a tool by name.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        enphase_service: EnphaseService instance (required for enphase tools)
        task_service: TaskCreationService instance (required for task tools)

    Returns:
        Tool execution result
    """
    handler = get_tool_handler(tool_name)

    if handler == "enphase":
        if not enphase_service:
            return {
                "success": False,
                "error": "Enphase service not configured",
            }
        return execute_enphase_tool(tool_name, arguments, enphase_service)

    elif handler == "task":
        if not task_service:
            return {
                "success": False,
                "error": "Task service not configured",
            }
        return execute_task_tool(tool_name, arguments, task_service)

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }


def get_tool_categories() -> Dict[str, List[str]]:
    """
    Get tools organized by category.

    Returns:
        Dictionary mapping category names to lists of tool names
    """
    categories: Dict[str, List[str]] = {}

    for tool_name, info in TOOL_REGISTRY.items():
        category = info["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(tool_name)

    return categories
