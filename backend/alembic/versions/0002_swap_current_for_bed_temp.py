"""Swap current_rms for bed_temp, rename temperature to nozzle_temp

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("fault_events", "temperature", new_column_name="nozzle_temp")
    op.add_column("fault_events", sa.Column("bed_temp", sa.Float(), nullable=False, server_default="0"))
    op.drop_column("fault_events", "current_rms")


def downgrade():
    op.alter_column("fault_events", "nozzle_temp", new_column_name="temperature")
    op.drop_column("fault_events", "bed_temp")
    op.add_column("fault_events", sa.Column("current_rms", sa.Float(), nullable=False, server_default="0"))
