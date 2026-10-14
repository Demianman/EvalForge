from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: str
    password: str = Field(min_length=6)


class UserOut(ORMModel):
    id: int
    email: str
    name: str


class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)


class ProjectOut(ProjectIn, ORMModel):
    id: int
    owner_id: int
    created_at: datetime


class DatasetIn(BaseModel):
    project_id: int
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)


class DatasetOut(DatasetIn, ORMModel):
    id: int
    created_at: datetime
    case_count: int = 0


class TestCaseIn(BaseModel):
    input: str = Field(min_length=1, max_length=20000)
    expected_output: dict[str, Any]
    tags: list[str] = []


class TestCaseOut(TestCaseIn, ORMModel):
    id: int
    dataset_id: int


class RunIn(BaseModel):
    dataset_id: int
    name: str = Field(min_length=2, max_length=160)
    provider: Literal["deterministic"] = "deterministic"
    model: Literal["rules-v1", "rules-v2"] = "rules-v1"
    prompt_version: str = Field(default="v1", max_length=80)
    prompt: str = Field(default="Extract medications as JSON", max_length=5000)
    baseline_run_id: int | None = None


class RunOut(ORMModel):
    id: int
    project_id: int
    dataset_id: int
    name: str
    provider: str
    model: str
    prompt_version: str
    status: str
    baseline_run_id: int | None
    status: str
    error: str | None
    progress_completed: int
    progress_total: int
    cancel_requested: bool
    created_at: datetime
    completed_at: datetime | None


class ReviewSummary(BaseModel):
    decision: Literal["accepted", "rejected"]
    comment: str


class MetricDetails(BaseModel):
    exact_match: bool
    schema_valid: bool
    precision: float
    recall: float
    f1: float


class ResultOut(BaseModel):
    id: int
    run_id: int
    test_case_id: int
    input: str
    expected_output: dict
    actual_output: dict
    passed: bool
    score: float
    metric_details: MetricDetails
    latency_ms: int
    cost_usd: float
    input_tokens: int
    output_tokens: int
    provider_request_id: str | None
    attempt_count: int
    review: ReviewSummary | None = None


class ReviewIn(BaseModel):
    decision: Literal["accepted", "rejected"]
    comment: str = Field(default="", max_length=2000)


class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class HealthOut(BaseModel):
    status: Literal["ok"]


class ImportOut(BaseModel):
    imported: int


class DatasetPage(BaseModel):
    items: list[DatasetOut]
    total: int
    page: int
    page_size: int


class TestCasePage(BaseModel):
    items: list[TestCaseOut]
    total: int
    page: int
    page_size: int


class ResultPage(BaseModel):
    items: list[ResultOut]
    total: int
    page: int
    page_size: int


class QualityCheck(BaseModel):
    name: str
    passed: bool


class QualityGate(BaseModel):
    passed: bool
    checks: list[QualityCheck]


class RunSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    mean_f1: float
    p50_latency_ms: int
    p95_latency_ms: int
    cost_usd: float
    input_tokens: int
    output_tokens: int
    quality_gate: QualityGate


class RunDetail(BaseModel):
    run: RunOut
    summary: RunSummary


class CompareRow(BaseModel):
    change: Literal["regression", "improvement", "unchanged"]
    input: str
    expected: dict[str, Any]
    old: dict[str, Any] | None
    new: dict[str, Any]
    result_id: int
    review: ReviewSummary | None


class CompareSummary(BaseModel):
    regressions: int
    improvements: int
    total: int


class CompareOut(BaseModel):
    items: list[CompareRow]
    summary: CompareSummary


class ReviewOut(ReviewSummary):
    id: int
    result_id: int
    updated_at: datetime


class DashboardMetrics(BaseModel):
    projects: int
    runs: int
    pass_rate: float
    regressions: int


class DashboardOut(BaseModel):
    projects: list[ProjectOut]
    recent_runs: list[RunOut]
    metrics: DashboardMetrics


class RagDocumentIn(BaseModel):
    project_id: int
    title: str = Field(min_length=2, max_length=240)
    source_uri: str = Field(default="", max_length=1000)
    content: str = Field(min_length=20, max_length=200000)
    chunk_size: int = Field(default=80, ge=20, le=500)
    chunk_overlap: int = Field(default=15, ge=0, le=100)


class RagDocumentOut(BaseModel):
    id: int
    project_id: int
    title: str
    source_uri: str
    content_sha256: str
    chunk_count: int
    created_at: datetime


class RagChunkOut(BaseModel):
    id: int
    document_id: int
    position: int
    content: str
    chunk_metadata: dict[str, Any]


class RagCitation(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    source_uri: str
    position: int
    content: str
    score: float


class RagRetrievalConfig(BaseModel):
    method: Literal["vector", "hybrid"]
    top_k: int = Field(default=3, ge=1, le=10)


class RagQuery(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    expected_chunk_ids: list[int] = Field(min_length=1)


class RagEvaluationIn(BaseModel):
    project_id: int
    name: str = Field(min_length=2, max_length=160)
    queries: list[RagQuery] = Field(min_length=1, max_length=100)
    baseline: RagRetrievalConfig = RagRetrievalConfig(method="vector", top_k=3)
    candidate: RagRetrievalConfig = RagRetrievalConfig(method="hybrid", top_k=3)


class RagMethodResult(BaseModel):
    answer: str
    citations: list[RagCitation]
    recall_at_k: float
    mrr: float


class RagQueryResult(BaseModel):
    question: str
    expected_chunk_ids: list[int]
    change: Literal["regression", "improvement", "unchanged"]
    baseline: RagMethodResult
    candidate: RagMethodResult


class RagEvaluationSummary(BaseModel):
    queries: int
    baseline_recall_at_k: float
    candidate_recall_at_k: float
    baseline_mrr: float
    candidate_mrr: float
    regressions: int
    improvements: int
    quality_gate_passed: bool


class RagEvaluationOut(ORMModel):
    id: int
    project_id: int
    name: str
    baseline_config: RagRetrievalConfig
    candidate_config: RagRetrievalConfig
    results: list[RagQueryResult]
    summary: RagEvaluationSummary
    created_at: datetime
