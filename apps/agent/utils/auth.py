#!/usr/bin/env python3
"""
Authentication utilities for the Agent server.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from utils.config import config

security = HTTPBearer(auto_error=False)


async def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> bool:
    """
    Verify the bearer token from the Authorization header.

    Args:
        credentials: HTTP authorization credentials from FastAPI security

    Returns:
        True if token is valid

    Raises:
        HTTPException: If token is missing or invalid
    """
    # If no bearer token is configured, skip auth (for local development)
    if not config.BEARER_TOKEN:
        return True

    # Check if credentials were provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the token
    if credentials.credentials != config.BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
