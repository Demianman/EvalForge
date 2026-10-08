import csv
import io
import json
import logging
from datetime import datetime
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from itsdangerous import BadSignature, URLSafeSerializer
from .config import settings
from .database import get_db
from .models import Dataset, EvaluationResult, ExperimentRun, Project, Review, TestCase, User
from .runner import evaluate_quality_gate, percentile
from .jobs import enqueue_run, execute_run
from .schemas import (
    CompareOut,
    DashboardOut,
    DatasetIn,
    DatasetOut,
    DatasetPage,
    HealthOut,
    ImportOut,
    LoginIn,
    ProjectIn,
    ProjectOut,
    ResultOut,
    ResultPage,
    ReviewIn,
    ReviewOut,
    RunDetail,
    RunIn,
    RunOut,
    TestCaseIn,
    TestCaseOut,
    TestCasePage,
    UserOut,
)

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
log = logging.getLogger("evalforge")
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
session_signer = URLSafeSerializer(settings.session_secret, salt="evalforge-session")
app = FastAPI(title="EvalForge API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    return Response(content=json.dumps({"error": {"code": f"http_{exc.status_code}", "message": exc.detail}}), status_code=exc.status_code, media_type="application/json")


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return Response(
        content=json.dumps(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": details,
                }
            }
        ),
        status_code=422,
        media_type="application/json",
    )


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("evalforge_session")
    try:
        user_id = session_signer.loads(token) if token else None
    except BadSignature:
        user_id = None
    user = db.get(User, int(user_id)) if user_id else None
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


@app.get("/health", response_model=HealthOut)
def health(): return {"status": "ok"}


@app.post("/api/auth/login", response_model=UserOut)
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not pwd.verify(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    response.set_cookie("evalforge_session", session_signer.dumps(user.id), httponly=True, samesite="lax", max_age=86400)
    return {"id": user.id, "email": user.email, "name": user.name}


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response): response.delete_cookie("evalforge_session")


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)): return {"id": user.id, "email": user.email, "name": user.name}


@app.get("/api/projects", response_model=list[ProjectOut])
def projects(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())).all()


@app.post("/api/projects", status_code=201, response_model=ProjectOut)
def create_project(data: ProjectIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = Project(**data.model_dump(), owner_id=user.id); db.add(item); db.commit(); db.refresh(item); return item


@app.get("/api/datasets", response_model=DatasetPage)
def datasets(project_id: int | None = None, q: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    stmt = select(Dataset).join(Project).where(Project.owner_id == user.id)
    if project_id: stmt = stmt.where(Dataset.project_id == project_id)
    if q: stmt = stmt.where(or_(Dataset.name.ilike(f"%{q}%"), Dataset.description.ilike(f"%{q}%")))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(Dataset.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {"items": [{"id": d.id, "project_id": d.project_id, "name": d.name, "description": d.description, "created_at": d.created_at, "case_count": len(d.test_cases)} for d in items], "total": total, "page": page, "page_size": page_size}


@app.post("/api/datasets", status_code=201, response_model=DatasetOut)
def create_dataset(data: DatasetIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = db.get(Project, data.project_id)
    if not project or project.owner_id != user.id: raise HTTPException(404, "Project not found")
    item = Dataset(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@app.put("/api/datasets/{dataset_id}", response_model=DatasetOut)
def update_dataset(dataset_id: int, data: DatasetIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(Dataset, dataset_id)
    if not item or item.project.owner_id != user.id: raise HTTPException(404, "Dataset not found")
    for k, v in data.model_dump().items(): setattr(item, k, v)
    db.commit(); db.refresh(item); return item


@app.delete("/api/datasets/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(Dataset, dataset_id)
    if not item or item.project.owner_id != user.id: raise HTTPException(404, "Dataset not found")
    db.delete(item); db.commit()


@app.get("/api/datasets/{dataset_id}/cases", response_model=TestCasePage)
def cases(dataset_id: int, q: str = "", tag: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset or dataset.project.owner_id != user.id: raise HTTPException(404, "Dataset not found")
    stmt = select(TestCase).where(TestCase.dataset_id == dataset_id)
    if q: stmt = stmt.where(TestCase.input.ilike(f"%{q}%"))
    items = db.scalars(stmt.order_by(TestCase.id).offset((page-1)*page_size).limit(page_size)).all()
    if tag: items = [x for x in items if tag in x.tags]
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.post("/api/datasets/{dataset_id}/cases", status_code=201, response_model=TestCaseOut)
def create_case(dataset_id: int, data: TestCaseIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset or dataset.project.owner_id != user.id: raise HTTPException(404, "Dataset not found")
    item = TestCase(dataset_id=dataset_id, **data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@app.put("/api/cases/{case_id}", response_model=TestCaseOut)
def update_case(case_id: int, data: TestCaseIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(TestCase, case_id)
    if not item or item.dataset.project.owner_id != user.id: raise HTTPException(404, "Test case not found")
    for k, v in data.model_dump().items(): setattr(item, k, v)
    db.commit(); return item


@app.delete("/api/cases/{case_id}", status_code=204)
def delete_case(case_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(TestCase, case_id)
    if not item or item.dataset.project.owner_id != user.id: raise HTTPException(404, "Test case not found")
    db.delete(item); db.commit()


@app.post("/api/datasets/{dataset_id}/import", response_model=ImportOut)
async def import_cases(dataset_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset or dataset.project.owner_id != user.id: raise HTTPException(404, "Dataset not found")
    raw = (await file.read()).decode("utf-8")
    try:
        rows = json.loads(raw) if file.filename and file.filename.endswith(".json") else list(csv.DictReader(io.StringIO(raw)))
        if not isinstance(rows, list): raise ValueError("Expected a JSON array")
        valid = []
        for index, row in enumerate(rows):
            expected = row.get("expected_output") or row.get("expected")
            if isinstance(expected, str): expected = json.loads(expected)
            valid.append(TestCaseIn(input=row["input"], expected_output=expected, tags=row.get("tags", []) if isinstance(row.get("tags", []), list) else row.get("tags", "").split("|")))
    except Exception as exc:
        raise HTTPException(422, f"Invalid import: {exc}")
    db.add_all([TestCase(dataset_id=dataset_id, **row.model_dump()) for row in valid]); db.commit()
    return {"imported": len(valid)}


@app.post("/api/experiments", status_code=201, response_model=RunOut)
def run_experiment(data: RunIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    dataset = db.get(Dataset, data.dataset_id)
    if not dataset or dataset.project.owner_id != user.id: raise HTTPException(404, "Dataset not found")
    run = ExperimentRun(**data.model_dump(), project_id=dataset.project_id, status="pending", progress_total=len(dataset.test_cases)); db.add(run); db.commit(); db.refresh(run)
    try:
        if settings.job_mode == "sync": execute_run(run.id)
        else: enqueue_run(run.id)
        db.refresh(run)
        return run
    except Exception as exc:
        run.status = "failed"; run.error = str(exc); db.commit(); log.exception("experiment_enqueue_failed"); raise HTTPException(503, f"Could not queue evaluation: {exc}")


@app.post("/api/experiments/{run_id}/cancel", status_code=202, response_model=RunOut)
def cancel_experiment(run_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    run = db.get(ExperimentRun, run_id)
    if not run or db.get(Project, run.project_id).owner_id != user.id: raise HTTPException(404, "Experiment not found")
    if run.status not in {"pending", "running"}: raise HTTPException(409, "Only pending or running experiments can be cancelled")
    run.cancel_requested = True
    if run.status == "pending": run.status = "cancelled"; run.completed_at = datetime.utcnow()
    db.commit(); db.refresh(run); return run


@app.get("/api/experiments", response_model=list[RunOut])
def runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(ExperimentRun).join(Project).where(Project.owner_id == user.id).order_by(ExperimentRun.created_at.desc()).limit(limit)).all()


@app.get("/api/experiments/{run_id}", response_model=RunDetail)
def run_detail(run_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    run = db.get(ExperimentRun, run_id)
    if not run or db.get(Project, run.project_id).owner_id != user.id: raise HTTPException(404, "Experiment not found")
    total = len(run.results); passed = sum(r.passed for r in run.results); pass_rate = passed / total if total else 0
    mean_f1 = sum(float(r.metric_details.get("f1", r.score)) for r in run.results) / total if total else 0
    latencies = [r.latency_ms for r in run.results]; p50, p95 = percentile(latencies, .5), percentile(latencies, .95)
    return {"run": run, "summary": {"total": total, "passed": passed, "failed": total-passed, "pass_rate": pass_rate, "mean_f1": mean_f1, "p50_latency_ms": p50, "p95_latency_ms": p95, "cost_usd": sum(r.cost_usd for r in run.results), "input_tokens": sum(r.input_tokens for r in run.results), "output_tokens": sum(r.output_tokens for r in run.results), "quality_gate": evaluate_quality_gate(pass_rate=pass_rate, mean_f1=mean_f1, p95_latency_ms=p95)}}


@app.get("/api/experiments/{run_id}/results", response_model=ResultPage)
def results(run_id: int, status: str = "all", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    run = db.get(ExperimentRun, run_id)
    if not run or db.get(Project, run.project_id).owner_id != user.id: raise HTTPException(404, "Experiment not found")
    stmt = select(EvaluationResult).where(EvaluationResult.run_id == run_id)
    if status == "passed": stmt = stmt.where(EvaluationResult.passed.is_(True))
    if status == "failed": stmt = stmt.where(EvaluationResult.passed.is_(False))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(EvaluationResult.id).offset((page-1)*page_size).limit(page_size)).all()
    return {"items": [serialize_result(r) for r in rows], "total": total, "page": page, "page_size": page_size}


def serialize_result(r: EvaluationResult):
    return {"id": r.id, "run_id": r.run_id, "test_case_id": r.test_case_id, "input": r.test_case.input, "expected_output": r.test_case.expected_output, "actual_output": r.actual_output, "passed": r.passed, "score": r.score, "metric_details": r.metric_details, "latency_ms": r.latency_ms, "cost_usd": r.cost_usd, "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "provider_request_id": r.provider_request_id, "attempt_count": r.attempt_count, "review": ({"decision": r.review.decision, "comment": r.review.comment} if r.review else None)}


@app.get("/api/experiments/{run_id}/compare", response_model=CompareOut)
def compare(run_id: int, baseline_id: int, change: str = "all", db: Session = Depends(get_db), user: User = Depends(current_user)):
    current, baseline = db.get(ExperimentRun, run_id), db.get(ExperimentRun, baseline_id)
    if not current or not baseline or current.dataset_id != baseline.dataset_id or db.get(Project, current.project_id).owner_id != user.id: raise HTTPException(404, "Comparable experiments not found")
    old = {r.test_case_id: r for r in baseline.results}; rows = []
    for new in current.results:
        previous = old.get(new.test_case_id)
        kind = "regression" if previous and previous.passed and not new.passed else "improvement" if previous and not previous.passed and new.passed else "unchanged"
        if change != "all" and kind != change: continue
        rows.append({"change": kind, "input": new.test_case.input, "expected": new.test_case.expected_output, "old": previous.actual_output if previous else None, "new": new.actual_output, "result_id": new.id, "review": ({"decision": new.review.decision, "comment": new.review.comment} if new.review else None)})
    return {"items": rows, "summary": {"regressions": sum(x["change"] == "regression" for x in rows), "improvements": sum(x["change"] == "improvement" for x in rows), "total": len(rows)}}


@app.get("/api/results/{result_id}", response_model=ResultOut)
def result_detail(result_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    result = db.get(EvaluationResult, result_id)
    if not result or db.get(Project, result.run.project_id).owner_id != user.id: raise HTTPException(404, "Result not found")
    return serialize_result(result)


@app.put("/api/results/{result_id}/review", response_model=ReviewOut)
def review(result_id: int, data: ReviewIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    result = db.get(EvaluationResult, result_id)
    if not result or db.get(Project, result.run.project_id).owner_id != user.id: raise HTTPException(404, "Result not found")
    item = result.review or Review(result_id=result_id, reviewer_id=user.id)
    item.decision, item.comment = data.decision, data.comment
    db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "result_id": item.result_id, "decision": item.decision, "comment": item.comment, "updated_at": item.updated_at}


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    projects = db.scalars(select(Project).where(Project.owner_id == user.id)).all()
    project_ids = [p.id for p in projects]
    runs = db.scalars(select(ExperimentRun).where(ExperimentRun.project_id.in_(project_ids)).order_by(ExperimentRun.created_at.desc()).limit(8)).all() if project_ids else []
    result_rows = [r for run in runs for r in run.results]; total = len(result_rows); passed = sum(r.passed for r in result_rows)
    return {"projects": projects, "recent_runs": runs, "metrics": {"projects": len(projects), "runs": len(runs), "pass_rate": passed/total if total else 0, "regressions": sum(not r.passed for r in result_rows)}}
