"""saved monthly dashboard snapshots"""
from alembic import op
import sqlalchemy as sa

revision = "0003_dashboard_months"
down_revision = "0002_business"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dashboard_months",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("month", sa.String(7), nullable=False, unique=True),
        sa.Column("details", sa.JSON, nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_dashboard_months_month", "dashboard_months", ["month"])


def downgrade():
    op.drop_index("ix_dashboard_months_month", table_name="dashboard_months")
    op.drop_table("dashboard_months")
