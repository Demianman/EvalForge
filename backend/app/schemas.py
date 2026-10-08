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
