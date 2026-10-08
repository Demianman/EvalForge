"""add detailed evaluation metrics"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"


def upgrade():
    op.add_column("evaluation_results", sa.Column("metric_details", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("evaluation_results", sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("evaluation_results", sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("evaluation_results", sa.Column("provider_request_id", sa.String(160), nullable=True))
    op.add_column("evaluation_results", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    for column in ["attempt_count", "provider_request_id", "output_tokens", "input_tokens", "metric_details"]:
        op.drop_column("evaluation_results", column)
