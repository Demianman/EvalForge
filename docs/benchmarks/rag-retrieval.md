# RAG retrieval benchmark

Last verified: 2026-10-14

This reproducible benchmark compares EvalForge's deterministic vector baseline
with its hybrid vector + lexical reciprocal-rank-fusion (RRF) retriever. It
uses the production chunking, embedding, retrieval, and metric functions.

## Results

All configurations use the same 60 synthetic queries and `top_k=5`.

| Chunk size | Method | Recall@5 | 95% bootstrap CI | MRR | 95% bootstrap CI |
|---:|---|---:|---:|---:|---:|
| 200 | Vector | 86.67% | 78.33–95.00% | 0.6633 | 0.5605–0.7611 |
| 200 | Hybrid RRF | 95.00% | 88.33–100.00% | 0.8992 | 0.8242–0.9625 |
| 800 | Vector | 51.67% | 40.00–65.00% | 0.3256 | 0.2311–0.4317 |
| 800 | Hybrid RRF | 91.67% | 83.33–98.33% | 0.7069 | 0.6181–0.7917 |

At chunk size 200, Hybrid improves Recall@5 by **8.33 percentage points**
and MRR by **0.2358** over Vector. At chunk size 800, Hybrid improves
Recall@5 by **40.00 percentage points** and MRR by **0.3814**.

Increasing chunk size from 200 to 800 lowers Vector Recall@5 by **35.00
percentage points** and Hybrid Recall@5 by **3.33 percentage points** in this
benchmark. Larger chunks dilute the identifier-level evidence used by these
deterministic feature-hash embeddings; hybrid lexical ranking is more robust
to that dilution.

## Methodology

- Fixed seed: `20271014`
- 60 fictional protocol documents and 60 pre-generated questions
- One unique protocol identifier and one labelled evidence chunk per question
- 10% chunk overlap at both chunk sizes
- Same `top_k=5` for Vector and Hybrid
- Deterministic 96-dimensional feature-hash embeddings
- Hybrid candidate combines vector and lexical ranks using RRF
- Query-level bootstrap with 2,000 fixed-seed resamples for 95% confidence intervals
- Exact expected values are protected by an automated regression test

Run from `backend`:

```bash
python -m benchmarks.rag_retrieval
```

The machine-readable result is committed at
[`rag-retrieval.json`](rag-retrieval.json).

## Scope and limitations

This is an intentionally synthetic, identifier-heavy retrieval benchmark. It
demonstrates controlled evaluation, regression protection, and the behavior of
EvalForge's offline retrievers. It does **not** estimate clinical accuracy,
production performance, general semantic-search quality, or user impact.

The experiment does not use Chroma, `pgvector`, a learned reranker, a commercial
embedding model, or an LLM generator. Comparisons with reports using those
systems require their exact corpus, ground truth, embedding model, distance
metric, and retrieval configuration.
