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

Because both methods run the same 60 queries, method comparisons are paired.
At chunk size 200, Hybrid improves Recall@5 by **8.33 percentage points**
(paired bootstrap 95% CI **+1.67 to +16.67 pp**) and MRR by **0.2358**.
The five discordant queries are all Hybrid-only, but the two-sided exact
McNemar result is **p=0.0625**; this small, boundary-case comparison is not the
benchmark's primary claim.

At chunk size 800, Hybrid improves Recall@5 by **40.00 percentage points**
(paired 95% CI **+28.33 to +51.67 pp**) and MRR by **0.3814**. The 24
discordant queries are all Hybrid-only and exact McNemar **p=1.19e-7**.

Increasing chunk size from 200 to 800 lowers Vector Recall@5 by **35.00
percentage points** (paired 95% CI **-48.33 to -21.67 pp**) and Hybrid
Recall@5 by **3.33 percentage points** (paired 95% CI **-8.33 to 0 pp**) in
this benchmark. The paired difference-in-differences shows a **+31.67 pp**
Hybrid robustness advantage (95% CI **+18.33 to +45.00 pp**). Larger chunks
dilute the identifier-level evidence used by these deterministic feature-hash
embeddings; the Jaccard lexical rank fused through RRF is more robust to that
dilution.

The direction is consistent with Chroma's published observation that a
200-token recursive splitter performs reliably while 800-token settings have
weaker retrieval-efficiency tradeoffs. This is **not a reproduction** of that
report: Chroma evaluates five corpora with token-level relevance and
`text-embedding-3-large`, whereas EvalForge uses a synthetic identifier-heavy
corpus and deterministic feature hashing. See Chroma's
[original technical report](https://www.trychroma.com/research/evaluating-chunking).

## Methodology

- Fixed seed: `20271014`
- 60 fictional protocol documents and 60 pre-generated questions
- One unique protocol identifier and one labelled evidence chunk per question
- 10% chunk overlap at both chunk sizes
- Same `top_k=5` for Vector and Hybrid
- Deterministic 96-dimensional feature-hash embeddings
- Hybrid candidate combines vector and lexical ranks using RRF
- Query-level paired bootstrap with 2,000 fixed-seed resamples for difference confidence intervals
- Exact two-sided McNemar tests for paired binary Recall@5 outcomes
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

The lexical component is Jaccard overlap ranking, not BM25. The experiment does
not use Chroma, `pgvector`, a learned reranker, a commercial
embedding model, or an LLM generator. Comparisons with reports using those
systems require their exact corpus, ground truth, embedding model, distance
metric, and retrieval configuration.
