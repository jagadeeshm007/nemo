# ==============================================================================
# AI Service — Database (PostgreSQL with SQLAlchemy Async)
# ==============================================================================

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class Database:
    """Async PostgreSQL connection manager."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = create_async_engine(
            settings.database_url,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=settings.nemo_env == "development",
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def connect(self) -> None:
        """Verify database connectivity."""
        async with self._engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Database connected")

    async def disconnect(self) -> None:
        """Close all connections."""
        await self._engine.dispose()
        logger.info("Database disconnected")

    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self._session_factory()

    @property
    def engine(self):
        return self._engine
