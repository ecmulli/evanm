#!/usr/bin/env python3
"""
Agent Server - AI-powered task creation and management API.

This server provides intelligent task creation capabilities using OpenAI and Notion integration.
Future features will include content generation, task analysis, and meeting summarization.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from routes.agent import router as agent_router
from routes.scheduler import router as scheduler_router
from routes.scheduler import set_scheduler_service
from routes.task_creator import router as task_creator_router
from services.task_scheduler import TaskSchedulerService
from utils.config import config

# Set up logging - simplified format, output to stdout
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

# Global scheduler service instance
scheduler_service = None
scheduler_task = None


async def run_scheduler_loop():
    """Background task that runs the scheduler every 10 minutes."""
    global scheduler_service

    # Get scheduler interval from env (default 10 minutes)
    interval_minutes = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "10"))
    interval_seconds = interval_minutes * 60

    logger.info(f"Scheduler loop started (interval: {interval_minutes} min)")

    while True:
        try:
            if scheduler_service:
                logger.info("Running scheduling cycle...")
                # Run the synchronous method in a thread pool to avoid blocking
                await asyncio.to_thread(scheduler_service.run_scheduling_cycle)
            else:
                logger.warning("Scheduler service not initialized")
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)

        # Wait for next cycle
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global scheduler_service, scheduler_task

    # Startup
    logger.info("Starting Agent Server")

    try:
        # Validate required environment variables
        config.validate_required_env_vars()
        logger.info("Environment variables validated")
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise

    logger.info(f"Server configured for port: {config.PORT}")
    logger.info(f"Debug mode: {config.DEBUG}")

    # Initialize task scheduler if Livepeer credentials are available
    livepeer_api_key = os.getenv("LIVEPEER_NOTION_API_KEY")
    livepeer_db_id = os.getenv("LIVEPEER_NOTION_DB_ID")

    if livepeer_api_key and livepeer_db_id:
        try:
            logger.info("Initializing Task Scheduler Service...")
            # Get user name for filtering tasks by assignee (required)
            # Can be a name like "evan" or a Notion user ID
            livepeer_user_id = os.getenv("LIVEPEER_NOTION_USER_ID", "evan")
            logger.info(
                f"Scheduler will only schedule tasks assigned to: {livepeer_user_id}"
            )
            logger.info(
                f"Using Livepeer database ID: {livepeer_db_id[:8]}...{livepeer_db_id[-8:]}"
            )
            logger.info(
                f"Using Livepeer API key: {livepeer_api_key[:10]}...{livepeer_api_key[-4:]}"
            )

            scheduler_service = TaskSchedulerService(
                notion_api_key=livepeer_api_key,
                database_id=livepeer_db_id,
                work_start_hour=int(os.getenv("WORK_START_HOUR", "9")),
                work_end_hour=int(os.getenv("WORK_END_HOUR", "17")),
                slot_duration_minutes=int(os.getenv("SLOT_DURATION_MINUTES", "15")),
                schedule_days_ahead=int(os.getenv("SCHEDULE_DAYS_AHEAD", "7")),
                timezone=os.getenv("TIMEZONE", "America/Chicago"),
                user_id=livepeer_user_id,
            )
            # Set the service in the routes module
            set_scheduler_service(scheduler_service)

            # Start background scheduler task
            scheduler_task = asyncio.create_task(run_scheduler_loop())
            logger.info("Task Scheduler Service started")
        except Exception as e:
            logger.error(f"Failed to initialize Task Scheduler: {e}")
            # Don't fail startup if scheduler fails
    else:
        logger.info(
            "Task Scheduler not configured (LIVEPEER_NOTION_API_KEY/DB_ID not set)"
        )

    yield

    # Shutdown
    logger.info("Shutting down Agent Server")

    # Cancel scheduler task if running
    if scheduler_task and not scheduler_task.done():
        logger.info("Stopping scheduler background task...")
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Scheduler task stopped")


# Create FastAPI application
app = FastAPI(
    title="Agent Server",
    description="AI-powered task creation and management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(task_creator_router)
app.include_router(scheduler_router)
app.include_router(agent_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "details": "An unexpected error occurred",
        },
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agent Server is running",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": "1.0.0",
    }


@app.get("/api/v1")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Agent API",
        "version": "v1",
        "endpoints": {
            "task_creator": "/api/v1/task_creator",
            "scheduler": "/api/v1/scheduler",
            "scheduler_status": "/api/v1/scheduler/status",
            "scheduler_run": "/api/v1/scheduler/run",
            "agent": "/api/v1/agent",
            "enphase_status": "/api/v1/enphase/status",
            "enphase_production": "/api/v1/enphase/production",
            "enphase_consumption": "/api/v1/enphase/consumption",
            "enphase_net": "/api/v1/enphase/net",
            "enphase_system": "/api/v1/enphase/system",
            "enphase_oauth_init": "/api/v1/enphase/oauth/init",
            "enphase_oauth_callback": "/api/v1/enphase/oauth/callback",
            "health": "/api/v1/health",
        },
        "future_endpoints": [
            "task_analyzer",
            "content_generator",
            "meeting_summarizer",
        ],
    }


def main():
    """Run the server with Hypercorn for dual-stack binding."""
    # Create Hypercorn config
    hypercorn_config = HypercornConfig()

    # IPv6 binding that accepts both IPv4 and IPv6 connections
    hypercorn_config.bind = [f"[::]:{config.PORT}"]

    hypercorn_config.loglevel = "info"

    # Log configuration
    logger.info(f"Hypercorn IPv6 binding: [::]:{config.PORT}")
    logger.info(f"Debug mode: {config.DEBUG}")

    # Run server
    asyncio.run(serve(app, hypercorn_config))


if __name__ == "__main__":
    main()
