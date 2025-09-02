#!/usr/bin/env python3
"""
Agent Server - AI-powered task creation and management API.

This server provides intelligent task creation capabilities using OpenAI and Notion integration.
Future features will include content generation, task analysis, and meeting summarization.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.task_creator import router as task_creator_router
from utils.config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Agent Server")

    try:
        # Validate required environment variables
        config.validate_required_env_vars()
        logger.info("✅ Environment variables validated")
    except ValueError as e:
        logger.error(f"❌ Environment validation failed: {e}")
        raise

    logger.info(f"🌐 Server configured for host: {config.HOST}:{config.PORT}")
    logger.info(f"🔧 Debug mode: {config.DEBUG}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Agent Server")


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
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
            "health": "/api/v1/health",
        },
        "future_endpoints": [
            "task_analyzer",
            "content_generator",
            "meeting_summarizer",
        ],
    }


def main():
    """Run the server."""
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
