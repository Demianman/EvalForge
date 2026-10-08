import logging
from datetime import datetime
from redis import Redis
from rq import Queue, Retry
from .config import settings
from .database import SessionLocal
from .models import Dataset, EvaluationResult, ExperimentRun
from .runner import get_provider, score_entity_extraction

log = logging.getLogger("evalforge.worker")


def enqueue_run(run_id: int) -> str:
    queue = Queue("evaluations", connection=Redis.from_url(settings.redis_url))
    job = queue.enqueue(execute_run, run_id, job_timeout=1800, retry=Retry(max=3, interval=[10, 30, 60]))
    return job.id


def execute_run(run_id: int) -> None:
    """Idempotent worker entrypoint. Each result is committed independently."""
    with SessionLocal() as db:
        run = db.get(ExperimentRun, run_id)
        if not run or run.status == "completed":
            return
        run.status = "running"; run.error = None; db.commit()
        provider = get_provider(run.provider)
        dataset = db.get(Dataset, run.dataset_id)
        if not dataset:
            run.status = "failed"; run.error = "Dataset not found"; db.commit(); return
        cases = list(dataset.test_cases)
        run.progress_total = len(cases); db.commit()
        try:
            for index, case in enumerate(cases, start=1):
                db.refresh(run)
                if run.cancel_requested:
                    run.status = "cancelled"; run.completed_at = datetime.utcnow(); db.commit(); return
                existing = next((r for r in run.results if r.test_case_id == case.id), None)
                if not existing:
                    outcome = provider.evaluate(case.input, run.model, run.prompt)
                    metrics = score_entity_extraction(outcome.output, case.expected_output)
                    db.add(EvaluationResult(run_id=run.id, test_case_id=case.id, actual_output=outcome.output, passed=bool(metrics["exact_match"]), score=float(metrics["f1"]), metric_details=metrics, latency_ms=outcome.latency_ms, cost_usd=outcome.cost_usd, input_tokens=outcome.input_tokens, output_tokens=outcome.output_tokens, provider_request_id=outcome.request_id))
                run.progress_completed = index; db.commit()
            run.status = "completed"; run.completed_at = datetime.utcnow(); db.commit()
            log.info("evaluation_completed run_id=%s cases=%s", run.id, len(cases))
        except Exception as exc:
            run.status = "failed"; run.error = str(exc); db.commit(); log.exception("evaluation_failed run_id=%s", run_id); raise
