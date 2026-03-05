# ==============================================================================
# Vector Service — Database (PostgreSQL + SQLAlchemy Async)
# ==============================================================================

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logger = logging.getLogger(__name__)

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(database_url, pool_size=10, max_overflow=5, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Database connection pool initialized")


async def close_db() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Database connection pool closed")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    assert _session_factory is not None, "Database not initialized"
    return _session_factory
