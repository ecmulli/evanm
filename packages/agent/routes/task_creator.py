#!/usr/bin/env python3
"""
Task creator route handler.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from models.task_models import (
    ErrorResponse,
    ParsedTaskData,
    TaskCreationRequest,
    TaskCreationResponse,
)
from services.task_creation import TaskCreationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["task_creator"])


@router.post("/task_creator", response_model=TaskCreationResponse)
async def create_task(request: TaskCreationRequest) -> TaskCreationResponse:
    """
    Create a new task using AI-powered synthesis.

    This endpoint takes text inputs (and optionally image URLs) and uses AI to:
    1. Parse and understand the requirements
    2. Extract workspace, priority, duration, and due date information
    3. Generate a comprehensive task description and acceptance criteria
    4. Create the task in the appropriate Notion database

    Args:
        request: TaskCreationRequest with text inputs and optional parameters

    Returns:
        TaskCreationResponse with task details and creation results

    Raises:
        HTTPException: If task creation fails
    """
    try:
        logger.info(f"🚀 Received task creation request")
        logger.info(f"📝 Text inputs: {len(request.text_inputs)} items")
        logger.info(
            f"🖼️  Image URLs: {len(request.image_urls) if request.image_urls else 0} items"
        )
        logger.info(f"🏢 Suggested workspace: {request.suggested_workspace}")
        logger.info(f"🧪 Dry run: {request.dry_run}")

        # Initialize the task creation service
        service = TaskCreationService(dry_run=request.dry_run)

        # Create the task
        result = service.create_task_from_inputs(
            text_inputs=request.text_inputs,
            image_urls=request.image_urls,
            suggested_workspace=request.suggested_workspace,
        )

        # Extract results
        task_info = result["task_info"]
        page_id = result["page_id"]
        page_url = result["page_url"]

        # Build parsed data response
        parsed_data = ParsedTaskData(
            task_name=task_info["task_name"],
            workspace=task_info["workspace"],
            priority=task_info["priority"],
            estimated_hours=task_info["estimated_hours"],
            due_date=task_info["due_date"],
            description=task_info["description"],
            acceptance_criteria=task_info["acceptance_criteria"],
        )

        # Build success response
        if request.dry_run:
            message = "Task parsed and validated successfully (dry run)"
        else:
            message = f"Task '{task_info['task_name']}' created successfully in {task_info['workspace']}"

        response = TaskCreationResponse(
            success=True,
            message=message,
            task_id=page_id,
            task_url=page_url,
            parsed_data=parsed_data,
            dry_run=request.dry_run,
        )

        logger.info(f"✅ Task creation completed successfully")
        return response

    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "Validation Error", "details": str(e)},
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error during task creation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal Server Error",
                "details": str(e),
            },
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "agent"}
