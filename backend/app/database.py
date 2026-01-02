"""
Database configuration and session management.
Matches cartographer-cloud's database setup for compatibility.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings

settings = get_settings()

# Create async engine with optimized connection pool
# Backend is the main gateway - needs largest pool to handle proxy traffic
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=40,  # Increased from 5 - main gateway handles all traffic
    max_overflow=60,  # Increased from 10 - allow burst capacity
    pool_timeout=30,  # Seconds to wait for connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
