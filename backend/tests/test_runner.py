import pytest
from app.runner import DeterministicProvider, evaluate_quality_gate, get_provider, percentile, score_entity_extraction


def test_field_level_metrics_capture_partial_match():
    metrics = score_entity_extraction({"medications": ["metformin", "aspirin"]}, {"medications": ["metformin", "lisinopril"]})
    assert metrics == {"exact_match": False, "schema_valid": True, "precision": .5, "recall": .5, "f1": .5}


def test_empty_outputs_are_perfect_match():
    assert score_entity_extraction({"medications": []}, {"medications": []})["f1"] == 1


def test_provider_is_reproducible():
    provider = DeterministicProvider(); first = provider.evaluate("Start metformin", "rules-v1", "extract")
    assert first == provider.evaluate("Start metformin", "rules-v1", "extract")
    assert first.request_id.startswith("local_")


def test_unknown_provider_fails_closed():
    with pytest.raises(ValueError, match="Unsupported provider"): get_provider("unknown")


def test_percentiles_and_quality_gate():
    assert percentile([10, 20, 30, 90], .95) == 90
    assert evaluate_quality_gate(pass_rate=.9, mean_f1=.95, p95_latency_ms=90)["passed"] is True
    assert evaluate_quality_gate(pass_rate=.7, mean_f1=.95, p95_latency_ms=90)["passed"] is False
