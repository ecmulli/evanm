"""
Task Scheduler API Routes

Endpoints for managing automatic task scheduling.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


# Global scheduler instance (will be set by app.py)
scheduler_service = None


def set_scheduler_service(service):
    """Set the global scheduler service instance."""
    global scheduler_service
    scheduler_service = service


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""

    last_run: str | None
    last_stats: dict
    work_hours: str
    slot_duration_minutes: int
    schedule_days_ahead: int


class SchedulingResultResponse(BaseModel):
    """Response model for scheduling operation."""

    success: bool
    message: str
    stats: dict


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """
    Get current scheduler status.

    Returns scheduler configuration and last run information.
    """
    if not scheduler_service:
        raise HTTPException(status_code=503, detail="Scheduler service not initialized")

    try:
        status = scheduler_service.get_status()
        return SchedulerStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=SchedulingResultResponse)
async def trigger_scheduling():
    """
    Manually trigger a scheduling cycle.

    This will immediately schedule/reschedule all tasks based on current priorities.
    """
    if not scheduler_service:
        raise HTTPException(status_code=503, detail="Scheduler service not initialized")

    try:
        logger.info("📅 Manual scheduling cycle triggered via API")
        stats = scheduler_service.run_scheduling_cycle()

        return SchedulingResultResponse(
            success=True,
            message="Scheduling cycle completed successfully",
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Error during manual scheduling: {e}")
        return SchedulingResultResponse(
            success=False, message=f"Scheduling failed: {str(e)}", stats={}
        )


@router.get("/health")
async def scheduler_health_check():
    """
    Health check endpoint for the scheduler.

    Returns scheduler operational status.
    """
    if not scheduler_service:
        return {"status": "not_initialized", "healthy": False}

    try:
        status = scheduler_service.get_status()
        return {
            "status": "operational",
            "healthy": True,
            "last_run": status["last_run"],
            "last_stats": status["last_stats"],
        }
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        return {"status": "error", "healthy": False, "error": str(e)}

