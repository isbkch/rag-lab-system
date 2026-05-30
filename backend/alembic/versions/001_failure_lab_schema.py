"""failure lab schema

Revision ID: 001_failure_lab_schema
Revises:
Create Date: 2026-05-30 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "001_failure_lab_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scenario_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scenario_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scenario_runs_scenario_id", "scenario_runs", ["scenario_id"]
    )
    op.create_index("ix_scenario_runs_status", "scenario_runs", ["status"])

    op.create_table(
        "lab_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("component", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["scenario_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lab_events_component", "lab_events", ["component"])
    op.create_index("ix_lab_events_created_at", "lab_events", ["created_at"])
    op.create_index("ix_lab_events_severity", "lab_events", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_lab_events_severity", table_name="lab_events")
    op.drop_index("ix_lab_events_created_at", table_name="lab_events")
    op.drop_index("ix_lab_events_component", table_name="lab_events")
    op.drop_table("lab_events")
    op.drop_index("ix_scenario_runs_status", table_name="scenario_runs")
    op.drop_index("ix_scenario_runs_scenario_id", table_name="scenario_runs")
    op.drop_table("scenario_runs")
