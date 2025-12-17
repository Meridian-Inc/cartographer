"""Database connection and session management for assistant service."""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert postgres:// to postgresql+asyncpg:// for async support
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Only create engine if DATABASE_URL is set
engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def init_db():
    """Initialize database and create tables."""
    if engine is None:
        print("[Database] DATABASE_URL not configured, skipping database initialization")
        return
    
    from . import db_models  # Import models to register them
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("[Database] Tables created successfully")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session() -> AsyncSession | None:
    """Get a database session directly (not as a dependency).
    
    Returns None if database is not configured.
    """
    if AsyncSessionLocal is None:
        return None
    
    return AsyncSessionLocal()

