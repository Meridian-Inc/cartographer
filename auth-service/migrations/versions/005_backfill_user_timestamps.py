"""Backfill user timestamps and enforce defaults.

Revision ID: 005_backfill_user_timestamps
Revises: 004_create_provider_links
Create Date: 2026-02-03
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_backfill_user_timestamps"
down_revision: str | None = "004_create_provider_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Backfill missing values first to avoid NOT NULL/default issues on legacy schemas.
    op.execute(
        sa.text(
            """
            UPDATE users
            SET created_at = COALESCE(created_at, NOW()),
                updated_at = COALESCE(updated_at, created_at, NOW())
            WHERE created_at IS NULL OR updated_at IS NULL
            """
        )
    )

    # Ensure inserts always get timestamps even on older databases.
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN created_at SET DEFAULT NOW()"))
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT NOW()"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN created_at DROP DEFAULT"))
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN updated_at DROP DEFAULT"))
