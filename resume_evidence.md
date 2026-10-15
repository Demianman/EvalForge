# EvalForge — Verified Resume Evidence

Last verified: 2026-10-14  
Repository: https://github.com/Demianman/EvalForge  
Verified benchmark source commit: `c13cdba7857ccd8011c958cdf62fc56511429d1d`
GitHub Actions: https://github.com/Demianman/EvalForge/actions/runs/38658703616

## Actual stack

- Next.js App Router, React, TypeScript, Tailwind, TanStack Query, Radix-based UI primitives
- FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL
- Redis, RQ worker, Docker Compose
- pytest, Vitest, React Testing Library, Playwright, GitHub Actions

## Implemented and verified features

- Session authentication and owner-scoped projects
- Dataset and test-case CRUD, validated CSV/JSON import, search, filtering, and pagination
- Deterministic provider abstraction and reproducible experiment runner
- Result tables, baseline/candidate comparison, regression/improvement filtering, quality gates, and side-by-side outputs
- Human accept/reject/comment review with optimistic updates and rollback
- FastAPI-derived OpenAPI contract and generated TypeScript types with CI drift detection
- Idempotent RAG document ingestion, versioned chunks, deterministic feature-hash embeddings, vector baseline, hybrid reciprocal-rank-fusion retrieval, citations, Recall@K, MRR, and no-regression gating
- Structured error envelopes and application logging
- Synthetic medication extraction and medication-safety fixtures only

## Verification evidence

- Backend: 14 pytest tests passed, including the deterministic benchmark regression test
- Frontend: 4 Vitest/React Testing Library tests passed
- ESLint, TypeScript typecheck, and Next.js production build passed
- Clean Alembic migration through `0004` passed
- Chromium E2E passed for sign-in, deterministic evaluation, results, RAG comparison, and citations
- Clean Linux Docker Compose build/start passed for PostgreSQL, Redis, FastAPI, RQ worker, and Next.js
- Compose smoke test submitted a queued evaluation and verified that the independent worker processed and persisted all 5 seeded cases before clean teardown
- Exact-source GitHub Actions run `38658703616` passed backend, frontend, E2E, API-contract, migration, benchmark-regression, and Compose jobs
- Production dependency audit reported 0 vulnerabilities at the verified milestone
- Reproducible 60-query synthetic benchmark measured Vector vs Hybrid RRF at equal Top-5: Hybrid Recall@5 was 95.00% vs 86.67% at 200-token chunks (+8.33 percentage points) and 91.67% vs 51.67% at 800-token chunks (+40.00 points)

## Architecture ownership demonstrated

- Defined the API, persistence, queue/worker, provider, retrieval, evaluation, and frontend state boundaries
- Used deterministic offline implementations so CI and demonstrations require no paid API key
- Kept FastAPI schemas as the source of truth for generated frontend contracts
- Added idempotency at document ingestion and evaluation-result creation boundaries
- Added release gates at both model-evaluation and CI levels

## Safe claims

- Built and verified a full-stack AI regression and RAG evaluation platform
- Implemented reproducible evaluation, retrieval comparison, human review, and automated quality gates
- Designed a PostgreSQL/Redis/RQ architecture and verified it through a clean Docker Compose workflow
- Implemented typed API contracts and multi-layer automated testing
- Used synthetic healthcare-themed fixtures with no patient or employer data

## Do not claim

- Real users, customers, production traffic, revenue, or business impact
- Clinical validation, diagnostic use, treatment recommendations, or medical-device status
- Employer ownership, employer data, patient data, or proprietary model integrations
- Production `pgvector`, learned reranking, LLM generation, OAuth/RBAC, or cloud deployment
- Performance or accuracy numbers not recorded in the repository's reproducible tests
- Generalize the synthetic identifier-heavy benchmark to clinical, production, or semantic-search accuracy

## Resume bullets

- Built EvalForge, a full-stack AI regression and RAG evaluation platform using Next.js, TypeScript, FastAPI, PostgreSQL, Redis/RQ, and Docker Compose, supporting versioned experiments, baseline comparisons, human review, and automated release gates.
- Implemented an offline RAG evaluation pipeline with idempotent ingestion, citations, Recall@K/MRR, and regression detection; a reproducible 60-query synthetic benchmark measured Hybrid Recall@5 of 95.00% vs 86.67% for Vector at 200-token chunks.
- Established typed OpenAPI-to-TypeScript contracts and GitHub Actions coverage across 13 backend tests, frontend tests, production builds, Chromium E2E, and a clean five-service Compose workflow that verifies queued worker execution and result persistence.
