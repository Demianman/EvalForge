"""add queued run progress and cancellation"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"


def upgrade():
    op.add_column("experiment_runs", sa.Column("progress_completed", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("experiment_runs", sa.Column("progress_total", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("experiment_runs", sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column("experiment_runs", "cancel_requested")
    op.drop_column("experiment_runs", "progress_total")
    op.drop_column("experiment_runs", "progress_completed")
