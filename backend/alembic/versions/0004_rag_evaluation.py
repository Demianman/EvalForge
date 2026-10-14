"""add RAG documents, chunks, and evaluations

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("rag_documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("title", sa.String(240), nullable=False), sa.Column("source_uri", sa.String(1000), nullable=False, server_default=""), sa.Column("content_sha256", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_rag_documents_project_id", "rag_documents", ["project_id"])
    op.create_index("ix_rag_documents_content_sha256", "rag_documents", ["content_sha256"])
    op.create_table("rag_chunks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("document_id", sa.Integer(), sa.ForeignKey("rag_documents.id"), nullable=False), sa.Column("position", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("token_set", sa.JSON(), nullable=False), sa.Column("embedding", sa.JSON(), nullable=False), sa.Column("chunk_metadata", sa.JSON(), nullable=False), sa.UniqueConstraint("document_id", "position"))
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    op.create_table("rag_evaluations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("queries", sa.JSON(), nullable=False), sa.Column("baseline_config", sa.JSON(), nullable=False), sa.Column("candidate_config", sa.JSON(), nullable=False), sa.Column("results", sa.JSON(), nullable=False), sa.Column("summary", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_rag_evaluations_project_id", "rag_evaluations", ["project_id"])


def downgrade():
    op.drop_table("rag_evaluations")
    op.drop_table("rag_chunks")
    op.drop_table("rag_documents")
