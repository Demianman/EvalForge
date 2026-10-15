import random

from benchmarks.rag_retrieval import SEED, evaluate, exact_mcnemar, paired_bootstrap_ci


def test_retrieval_benchmark_is_deterministic():
    expected = {
        (200, "vector"): (0.8667, 0.6633),
        (200, "hybrid"): (0.95, 0.8992),
        (800, "vector"): (0.5167, 0.3256),
        (800, "hybrid"): (0.9167, 0.7069),
    }

    for configuration, scores in expected.items():
        result, _, _ = evaluate(*configuration)
        assert (result.recall_at_5, result.mrr) == scores


def test_paired_retrieval_statistics_are_regression_protected():
    _, vector_200, _ = evaluate(200, "vector")
    _, hybrid_200, _ = evaluate(200, "hybrid")
    _, vector_800, _ = evaluate(800, "vector")
    _, hybrid_800, _ = evaluate(800, "hybrid")

    assert exact_mcnemar(vector_200, hybrid_200) == {
        "vector_only": 0,
        "hybrid_only": 5,
        "two_sided_p": 0.0625,
    }
    assert exact_mcnemar(vector_800, hybrid_800) == {
        "vector_only": 0,
        "hybrid_only": 24,
        "two_sided_p": 1.1920928955078125e-07,
    }
    assert paired_bootstrap_ci(vector_800, hybrid_800, random.Random(SEED + 900)) == [0.2833, 0.5167]
