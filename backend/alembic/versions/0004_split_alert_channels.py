"""Split alerts_enabled into email_alerts_enabled and sms_alerts_enabled

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "alerts_enabled", new_column_name="email_alerts_enabled")
    op.add_column("users", sa.Column("sms_alerts_enabled", sa.Boolean(), nullable=False, server_default="true"))


def downgrade():
    op.drop_column("users", "sms_alerts_enabled")
    op.alter_column("users", "email_alerts_enabled", new_column_name="alerts_enabled")
