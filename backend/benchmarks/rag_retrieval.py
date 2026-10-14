"""Reproducible synthetic benchmark for EvalForge retrieval strategies.

This benchmark intentionally uses production chunking, embedding, retrieval,
and metric functions. The corpus is synthetic and contains no clinical advice
or patient data. Run from ``backend`` with:

    python -m benchmarks.rag_retrieval
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from app.rag import chunk_text, embed, metrics, retrieve, tokenize


QUERY_COUNT = 60
TOP_K = 5
CHUNK_SIZES = (200, 800)
BOOTSTRAP_SAMPLES = 2_000
SEED = 20271014
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "docs" / "benchmarks" / "rag-retrieval.json"

FILLER = (
    "review workflow documentation monitoring training validation governance "
    "quality safety operations checklist evidence approval escalation reporting "
    "audit schedule assessment coordination standard process record control"
).split()
MARKERS = (
    "amber cobalt delta ember fuchsia granite harbor indigo juniper keystone "
    "lilac mercury nickel ochre pearl quartz russet silver topaz ultramarine "
    "violet willow xenon yellow zircon"
).split()


@dataclass(frozen=True)
class Result:
    chunk_size: int
    method: str
    queries: int
    top_k: int
    recall_at_5: float
    mrr: float
    recall_ci_95: list[float]
    mrr_ci_95: list[float]


def synthetic_documents() -> list[tuple[str, str, str]]:
    """Return (protocol code, expected marker, document text) records."""
    records = []
    for index in range(QUERY_COUNT):
        code = f"hcx-{index:04d}"
        marker = MARKERS[index % len(MARKERS)] + f"-{index:04d}"
        prefix = [FILLER[(index + offset * 7) % len(FILLER)] for offset in range(470)]
        suffix = [FILLER[(index * 3 + offset * 11) % len(FILLER)] for offset in range(470)]
        evidence = (
            f"Protocol {code} uses evidence marker {marker} for its synthetic "
            "escalation checkpoint. This benchmark statement is fictional."
        ).split()
        records.append((code, marker, " ".join(prefix + evidence + suffix)))
    return records


def build_chunks(chunk_size: int):
    chunks = []
    expected_by_code: dict[str, int] = {}
    next_id = 1
    for document_id, (code, marker, text) in enumerate(synthetic_documents(), 1):
        for position, content in enumerate(chunk_text(text, chunk_size, chunk_size // 10)):
            chunk = SimpleNamespace(
                id=next_id,
                document_id=document_id,
                position=position,
                content=content,
                token_set=sorted(set(tokenize(content))),
                embedding=embed(content),
            )
            chunks.append(chunk)
            if code in content and marker in content:
                expected_by_code[code] = next_id
            next_id += 1
    assert len(expected_by_code) == QUERY_COUNT
    return chunks, expected_by_code


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * quantile)]


def bootstrap_ci(values: list[float], rng: random.Random) -> list[float]:
    means = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    return [round(percentile(means, 0.025), 4), round(percentile(means, 0.975), 4)]


def evaluate(chunk_size: int, method: str) -> tuple[Result, list[float], list[float]]:
    chunks, expected_by_code = build_chunks(chunk_size)
    recalls, reciprocal_ranks = [], []
    for code, marker, _ in synthetic_documents():
        query = f"Which evidence marker controls the escalation checkpoint for protocol {code}?"
        ranked = retrieve(chunks, query, method, TOP_K)
        score = metrics([item.chunk.id for item in ranked], [expected_by_code[code]])
        recalls.append(score["recall_at_k"])
        reciprocal_ranks.append(score["mrr"])
    rng = random.Random(SEED + chunk_size + (1 if method == "hybrid" else 0))
    result = Result(
        chunk_size=chunk_size,
        method=method,
        queries=QUERY_COUNT,
        top_k=TOP_K,
        recall_at_5=round(sum(recalls) / len(recalls), 4),
        mrr=round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4),
        recall_ci_95=bootstrap_ci(recalls, rng),
        mrr_ci_95=bootstrap_ci(reciprocal_ranks, rng),
    )
    return result, recalls, reciprocal_ranks


def main() -> None:
    results = []
    raw: dict[tuple[int, str], tuple[list[float], list[float]]] = {}
    for chunk_size in CHUNK_SIZES:
        for method in ("vector", "hybrid"):
            result, recalls, reciprocal_ranks = evaluate(chunk_size, method)
            results.append(result)
            raw[(chunk_size, method)] = (recalls, reciprocal_ranks)

    comparisons = []
    for chunk_size in CHUNK_SIZES:
        vector_recall, vector_mrr = raw[(chunk_size, "vector")]
        hybrid_recall, hybrid_mrr = raw[(chunk_size, "hybrid")]
        comparisons.append(
            {
                "chunk_size": chunk_size,
                "hybrid_recall_absolute_lift": round(sum(h - v for h, v in zip(hybrid_recall, vector_recall, strict=True)) / QUERY_COUNT, 4),
                "hybrid_mrr_absolute_lift": round(sum(h - v for h, v in zip(hybrid_mrr, vector_mrr, strict=True)) / QUERY_COUNT, 4),
            }
        )

    report = {
        "benchmark": "synthetic protocol evidence retrieval",
        "seed": SEED,
        "queries": QUERY_COUNT,
        "top_k": TOP_K,
        "chunk_overlap": "10%",
        "embedding": "deterministic 96-dimensional feature hashing",
        "results": [asdict(result) for result in results],
        "comparisons": comparisons,
        "limitations": [
            "Synthetic identifier-heavy corpus; results do not estimate clinical or production performance.",
            "No semantic embedding model, Chroma, pgvector, reranker, or LLM generator is used.",
        ],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
