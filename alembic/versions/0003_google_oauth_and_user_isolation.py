"""google_oauth_and_user_isolation

Revision ID: 0003_google_oauth_and_user_isolation
Revises: 0002_performance_indexes
Create Date: 2026-10-05 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_google_oauth_and_user_isolation"
down_revision: str | None = "0002_performance_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.add_column("users", sa.Column("google_id", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    op.add_column(
        "monitors",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_monitors_user_id_users",
        "monitors",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_monitors_user_id", "monitors", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_monitors_user_id", table_name="monitors")
    op.drop_constraint("fk_monitors_user_id_users", "monitors", type_="foreignkey")
    op.drop_column("monitors", "user_id")

    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "google_id")
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
