from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    rag_documents: Mapped[list["RagDocument"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    rag_evaluations: Mapped[list["RagEvaluation"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    project: Mapped[Project] = relationship(back_populates="datasets")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    input: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[dict] = mapped_column(JSON)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dataset: Mapped[Dataset] = relationship(back_populates="test_cases")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    provider: Mapped[str] = mapped_column(String(80), default="deterministic")
    model: Mapped[str] = mapped_column(String(120), default="rules-v1")
    prompt_version: Mapped[str] = mapped_column(String(80), default="v1")
    prompt: Mapped[str] = mapped_column(Text, default="")
    baseline_run_id: Mapped[int | None] = mapped_column(ForeignKey("experiment_runs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=RunStatus.pending.value)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_completed: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    results: Mapped[list["EvaluationResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (UniqueConstraint("run_id", "test_case_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("experiment_runs.id"), index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), index=True)
    actual_output: Mapped[dict] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float)
    metric_details: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    provider_request_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    run: Mapped[ExperimentRun] = relationship(back_populates="results")
    test_case: Mapped[TestCase] = relationship()
    review: Mapped["Review | None"] = relationship(back_populates="result", cascade="all, delete-orphan", uselist=False)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("evaluation_results.id"), unique=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    result: Mapped[EvaluationResult] = relationship(back_populates="review")


class RagDocument(Base):
    __tablename__ = "rag_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    source_uri: Mapped[str] = mapped_column(String(1000), default="")
    content_sha256: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    project: Mapped[Project] = relationship(back_populates="rag_documents")
    chunks: Mapped[list["RagChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class RagChunk(Base):
    __tablename__ = "rag_chunks"
    __table_args__ = (UniqueConstraint("document_id", "position"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("rag_documents.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_set: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list] = mapped_column(JSON, default=list)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    document: Mapped[RagDocument] = relationship(back_populates="chunks")


class RagEvaluation(Base):
    __tablename__ = "rag_evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    queries: Mapped[list] = mapped_column(JSON)
    baseline_config: Mapped[dict] = mapped_column(JSON)
    candidate_config: Mapped[dict] = mapped_column(JSON)
    results: Mapped[list] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    project: Mapped[Project] = relationship(back_populates="rag_evaluations")
