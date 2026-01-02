"""Add performance indexes for notification service

Revision ID: 003_performance_indexes
Revises: 002_discord_link_context
Create Date: 2026-01-02

Performance optimization migration to support 200+ concurrent users.
Adds indexes for frequently queried columns in notification tables.

Impact: +10-15 concurrent users expected
Risk: Low (uses CONCURRENTLY to avoid table locks)

Note: This migration runs outside of a transaction because
CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "003_performance_indexes"
down_revision = "002_discord_link_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes.
    
    Note: We use connection.execute() with AUTOCOMMIT isolation level
    because CREATE INDEX CONCURRENTLY cannot run in a transaction.
    """
    
    connection = op.get_bind()
    
    # Set autocommit mode (no transaction)
    connection.execute(text("COMMIT"))
    
    # User network preferences lookup (most frequent query)
    connection.execute(
        text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_network_prefs_user_network
        ON user_network_notification_prefs(user_id, network_id)
        """)
    )
    
    # Global user preferences lookup
    connection.execute(
        text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_global_prefs_user
        ON user_global_notification_prefs(user_id)
        """)
    )
    
    # Discord user link lookups (by user_id)
    connection.execute(
        text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_discord_links_user
        ON discord_user_links(user_id)
        """)
    )
    
    # Discord user link lookups (by discord_user_id)
    connection.execute(
        text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_discord_links_discord_user
        ON discord_user_links(discord_user_id)
        """)
    )


def downgrade() -> None:
    """Remove performance indexes.
    
    Note: DROP INDEX CONCURRENTLY also requires autocommit mode.
    """
    
    connection = op.get_bind()
    
    # Set autocommit mode (no transaction)
    connection.execute(text("COMMIT"))
    
    connection.execute(text("DROP INDEX CONCURRENTLY IF EXISTS idx_user_network_prefs_user_network"))
    connection.execute(text("DROP INDEX CONCURRENTLY IF EXISTS idx_user_global_prefs_user"))
    connection.execute(text("DROP INDEX CONCURRENTLY IF EXISTS idx_discord_links_user"))
    connection.execute(text("DROP INDEX CONCURRENTLY IF EXISTS idx_discord_links_discord_user"))

