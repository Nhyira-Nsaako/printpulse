"""Initial schema — users and fault_events tables

Revision ID: 0001
Revises:
Create Date: 2025-07-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # fault_class enum
    op.execute("CREATE TYPE fault_class_enum AS ENUM ('NORMAL','NOZZLE_CLOG','MOTOR_FAULT','THERMAL_RUNAWAY')")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_email", sa.String(255), nullable=True),
        sa.Column("alert_phone", sa.String(30), nullable=True),
        sa.Column("alerts_enabled", sa.Boolean(), default=True, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "fault_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fault_class", sa.Enum("NORMAL", "NOZZLE_CLOG", "MOTOR_FAULT", "THERMAL_RUNAWAY",
                                          name="fault_class_enum"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("accel_rms_z", sa.Float(), nullable=True),
        sa.Column("current_rms", sa.Float(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("esp32_timestamp", sa.Integer(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_sent", sa.Boolean(), default=False, nullable=False),
        sa.Column("acknowledged", sa.Boolean(), default=False, nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_fault_events_fault_class", "fault_events", ["fault_class"])
    op.create_index("ix_fault_events_received_at", "fault_events", ["received_at"])


def downgrade() -> None:
    op.drop_table("fault_events")
    op.drop_table("users")
    op.execute("DROP TYPE fault_class_enum")
