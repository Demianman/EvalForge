from app.cli import gate_for_run
from app.models import EvaluationResult, ExperimentRun


def test_cli_gate_report_for_passing_run():
    run = ExperimentRun(id=7, project_id=1, dataset_id=1, name="candidate", status="completed")
    run.results = [EvaluationResult(test_case_id=1, actual_output={}, passed=True, score=1, metric_details={"f1": 1}, latency_ms=40, cost_usd=0)]
    report = gate_for_run(run)
    assert report["run_id"] == 7
    assert report["quality_gate"]["passed"] is True
