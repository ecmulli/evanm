#!/usr/bin/env python3
"""
Pydantic models for task creation API.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TaskCreationRequest(BaseModel):
    """Request model for task creation."""

    text_inputs: List[str] = Field(
        ..., description="List of text inputs to synthesize into a task", min_items=1
    )
    image_urls: Optional[List[str]] = Field(
        default=None, description="Optional list of image URLs to extract text from"
    )
    suggested_workspace: Optional[str] = Field(
        default=None,
        description="Optional suggested workspace (Personal, Livepeer, Vanquish)",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, parse and validate but don't create the task",
    )


class ParsedTaskData(BaseModel):
    """Parsed task data model."""

    task_name: str
    workspace: str
    priority: str
    estimated_hours: float
    due_date: str
    description: str
    acceptance_criteria: str


class TaskCreationResponse(BaseModel):
    """Response model for task creation."""

    success: bool
    message: str
    task_id: Optional[str] = None
    task_url: Optional[str] = None
    parsed_data: ParsedTaskData
    dry_run: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    details: Optional[str] = None
