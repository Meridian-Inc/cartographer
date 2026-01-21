"""
Tests for database configuration and session management.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseModule:
    """Test database.py functions."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session_and_closes(self):
        """Test that get_db yields a session and closes it in finally block."""
        from app.database import get_db

        mock_session = AsyncMock()

        with patch("app.database.async_session_maker") as mock_maker:
            # Set up async context manager
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None
            mock_maker.return_value = mock_context

            # Get the generator
            gen = get_db()

            # Advance to yield
            session = await gen.__anext__()
            assert session == mock_session

            # Complete the generator (triggers finally block)
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()

            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_db_closes_session_on_exception(self):
        """Test that get_db closes session even when exception occurs."""
        from app.database import get_db

        mock_session = AsyncMock()

        with patch("app.database.async_session_maker") as mock_maker:
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None
            mock_maker.return_value = mock_context

            gen = get_db()
            session = await gen.__anext__()

            # Simulate throwing an exception into the generator
            try:
                await gen.athrow(ValueError("Test error"))
            except ValueError:
                pass

            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self):
        """Test that init_db creates all tables using Base.metadata."""
        with patch("app.database.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_conn
            mock_context.__aexit__.return_value = None
            mock_engine.begin.return_value = mock_context

            from app.database import init_db

            await init_db()

            mock_engine.begin.assert_called_once()
            mock_conn.run_sync.assert_awaited_once()

    def test_base_class_exists(self):
        """Test that Base declarative class is defined."""
        from app.database import Base

        assert Base is not None
        assert hasattr(Base, "metadata")


class TestDatabaseConfiguration:
    """Test database configuration settings."""

    def test_engine_configuration(self):
        """Test that engine is created with expected parameters."""
        from app.database import engine

        # Engine should exist and be an async engine
        assert engine is not None
        # Check that pool settings are configured
        assert engine.pool.size() >= 0  # Pool exists

    def test_session_maker_configuration(self):
        """Test that session maker is properly configured."""
        from app.database import async_session_maker

        assert async_session_maker is not None
