"""Async database connection pool for the MCP server."""

import asyncpg


async def create_pool(database_url: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=database_url,
        min_size=1,
        max_size=3,
        ssl="require",
    )
