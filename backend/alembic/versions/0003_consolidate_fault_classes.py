"""Consolidate fault classes: merge NOZZLE_CLOG + MOTOR_FAULT into MECHANICAL_FAULT, rename THERMAL_RUNAWAY to THERMAL_ANOMALY

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create the new enum type
    op.execute("CREATE TYPE fault_class_enum_new AS ENUM ('NORMAL', 'MECHANICAL_FAULT', 'THERMAL_ANOMALY')")

    # 2. Cast the column across, mapping old values to new ones
    op.execute("""
        ALTER TABLE fault_events
        ALTER COLUMN fault_class TYPE fault_class_enum_new
        USING (
            CASE fault_class::text
                WHEN 'NOZZLE_CLOG' THEN 'MECHANICAL_FAULT'
                WHEN 'MOTOR_FAULT' THEN 'MECHANICAL_FAULT'
                WHEN 'THERMAL_RUNAWAY' THEN 'THERMAL_ANOMALY'
                ELSE fault_class::text
            END
        )::fault_class_enum_new
    """)

    # 3. Drop the old type, rename the new one into its place
    op.execute("DROP TYPE fault_class_enum")
    op.execute("ALTER TYPE fault_class_enum_new RENAME TO fault_class_enum")


def downgrade():
    op.execute("CREATE TYPE fault_class_enum_old AS ENUM ('NORMAL', 'NOZZLE_CLOG', 'MOTOR_FAULT', 'THERMAL_RUNAWAY')")
    op.execute("""
        ALTER TABLE fault_events
        ALTER COLUMN fault_class TYPE fault_class_enum_old
        USING (
            CASE fault_class::text
                WHEN 'MECHANICAL_FAULT' THEN 'MOTOR_FAULT'
                WHEN 'THERMAL_ANOMALY' THEN 'THERMAL_RUNAWAY'
                ELSE fault_class::text
            END
        )::fault_class_enum_old
    """)
    op.execute("DROP TYPE fault_class_enum")
    op.execute("ALTER TYPE fault_class_enum_old RENAME TO fault_class_enum")
