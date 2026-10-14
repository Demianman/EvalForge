from benchmarks.rag_retrieval import evaluate


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
