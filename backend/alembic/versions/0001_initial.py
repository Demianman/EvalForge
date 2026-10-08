"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("email"))
    op.create_table("projects", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("datasets", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("test_cases", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id"), nullable=False), sa.Column("input", sa.Text(), nullable=False), sa.Column("expected_output", sa.JSON(), nullable=False), sa.Column("tags", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("experiment_runs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id"), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("provider", sa.String(80), nullable=False), sa.Column("model", sa.String(120), nullable=False), sa.Column("prompt_version", sa.String(80), nullable=False), sa.Column("prompt", sa.Text(), nullable=False), sa.Column("baseline_run_id", sa.Integer(), sa.ForeignKey("experiment_runs.id")), sa.Column("status", sa.String(30), nullable=False), sa.Column("error", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("completed_at", sa.DateTime()))
    op.create_table("evaluation_results", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("run_id", sa.Integer(), sa.ForeignKey("experiment_runs.id"), nullable=False), sa.Column("test_case_id", sa.Integer(), sa.ForeignKey("test_cases.id"), nullable=False), sa.Column("actual_output", sa.JSON(), nullable=False), sa.Column("passed", sa.Boolean(), nullable=False), sa.Column("score", sa.Float(), nullable=False), sa.Column("latency_ms", sa.Integer(), nullable=False), sa.Column("cost_usd", sa.Float(), nullable=False), sa.Column("error", sa.Text()), sa.UniqueConstraint("run_id", "test_case_id"))
    op.create_table("reviews", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("result_id", sa.Integer(), sa.ForeignKey("evaluation_results.id"), nullable=False, unique=True), sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("decision", sa.String(20), nullable=False), sa.Column("comment", sa.Text(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))


def downgrade():
    for table in ["reviews", "evaluation_results", "experiment_runs", "test_cases", "datasets", "projects", "users"]: op.drop_table(table)
