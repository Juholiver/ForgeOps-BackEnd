"""add_performance_indexes

Revision ID: 0002_performance_indexes
Revises: 0001_initial_schema
Create Date: 2026-09-28 17:30:00.000000

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002_performance_indexes"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_monitors_active", "monitors", ["active"])
    op.create_index(
        "ix_check_results_monitor_id_checked_at",
        "check_results",
        ["monitor_id", "checked_at"],
    )
    op.create_index(
        "ix_incidents_monitor_id_status",
        "incidents",
        ["monitor_id", "status"],
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_monitors_active", table_name="monitors")
    op.drop_index(
        "ix_check_results_monitor_id_checked_at", table_name="check_results"
    )
    op.drop_index("ix_incidents_monitor_id_status", table_name="incidents")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
