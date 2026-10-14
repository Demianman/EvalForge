from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from .models import RagChunk

EMBEDDING_DIMENSIONS = 96


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def embed(text: str) -> list[float]:
    """Deterministic feature-hash embedding for offline, reproducible RAG tests."""
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in tokenize(text):
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        vector[index] += 1.0 if digest[4] % 2 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = size - overlap
    return [" ".join(words[start : start + size]) for start in range(0, len(words), step) if words[start : start + size]]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def lexical_score(query_tokens: set[str], chunk_tokens: set[str]) -> float:
    return len(query_tokens & chunk_tokens) / len(query_tokens | chunk_tokens) if query_tokens | chunk_tokens else 0.0


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: RagChunk
    score: float


def retrieve(chunks: list[RagChunk], query: str, method: str, top_k: int) -> list[RetrievedChunk]:
    query_embedding = embed(query)
    query_tokens = set(tokenize(query))
    vector_scores = {chunk.id: cosine(query_embedding, chunk.embedding) for chunk in chunks}
    lexical_scores = {chunk.id: lexical_score(query_tokens, set(chunk.token_set)) for chunk in chunks}

    if method == "vector":
        scores = vector_scores
    else:
        vector_rank = {chunk_id: rank for rank, (chunk_id, _) in enumerate(sorted(vector_scores.items(), key=lambda item: (-item[1], item[0])), 1)}
        lexical_rank = {chunk_id: rank for rank, (chunk_id, _) in enumerate(sorted(lexical_scores.items(), key=lambda item: (-item[1], item[0])), 1)}
        scores = {
            chunk.id: 1 / (60 + vector_rank[chunk.id]) + 1 / (60 + lexical_rank[chunk.id])
            for chunk in chunks
        }
    ranked = sorted(chunks, key=lambda chunk: (-scores[chunk.id], chunk.id))[:top_k]
    return [RetrievedChunk(chunk=chunk, score=round(scores[chunk.id], 6)) for chunk in ranked]


def metrics(retrieved_ids: list[int], expected_ids: list[int]) -> dict[str, float]:
    expected = set(expected_ids)
    if not expected:
        return {"recall_at_k": 1.0, "mrr": 1.0}
    hits = expected.intersection(retrieved_ids)
    first_rank = next((index for index, chunk_id in enumerate(retrieved_ids, 1) if chunk_id in expected), None)
    return {
        "recall_at_k": round(len(hits) / len(expected), 4),
        "mrr": round(1 / first_rank, 4) if first_rank else 0.0,
    }


def grounded_answer(items: list[RetrievedChunk]) -> str:
    if not items:
        return "Insufficient evidence in the indexed knowledge base."
    excerpts = [item.chunk.content.strip() for item in items[:2]]
    return " ".join(excerpts)
