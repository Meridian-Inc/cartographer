"""Create user_limits table for network limits feature.

Revision ID: 006_create_user_limits
Revises: 005_backfill_user_timestamps
Create Date: 2026-02-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_create_user_limits"
down_revision: Union[str, None] = "005_backfill_user_timestamps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_limits table."""
    op.create_table(
        "user_limits",
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("network_limit", sa.Integer(), nullable=True),
        sa.Column("is_role_exempt", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Drop user_limits table."""
    op.drop_table("user_limits")
