import argparse
import json
from .database import SessionLocal
from .models import ExperimentRun
from .runner import evaluate_quality_gate, percentile


def gate_for_run(run: ExperimentRun) -> dict:
    total = len(run.results); passed = sum(result.passed for result in run.results)
    pass_rate = passed / total if total else 0
    mean_f1 = sum(float(result.metric_details.get("f1", result.score)) for result in run.results) / total if total else 0
    p95 = percentile([result.latency_ms for result in run.results], .95)
    return {"run_id": run.id, "status": run.status, "metrics": {"pass_rate": pass_rate, "mean_f1": mean_f1, "p95_latency_ms": p95}, "quality_gate": evaluate_quality_gate(pass_rate=pass_rate, mean_f1=mean_f1, p95_latency_ms=p95)}


def main() -> int:
    parser = argparse.ArgumentParser(prog="evalforge", description="EvalForge CI quality gate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    gate = subparsers.add_parser("gate", help="Exit non-zero when a completed run fails its quality gate")
    gate.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        run = db.get(ExperimentRun, args.run_id)
        if not run:
            print(json.dumps({"error": "run_not_found", "run_id": args.run_id})); return 2
        report = gate_for_run(run); print(json.dumps(report, indent=2))
        return 0 if run.status == "completed" and report["quality_gate"]["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
