"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Project, RagChunk, RagDocument, RagEvaluation } from "@/lib/types";
import { Empty, ErrorBox } from "@/components/ui";

const DEMO_CONTENT = "Metformin is commonly used to manage type 2 diabetes. Renal function should be reviewed when evaluating medication safety. Lisinopril may be used for blood pressure management, with potassium and kidney function monitoring. This entirely synthetic educational guide is not medical advice and must not be used for clinical decisions.";

export default function RagPage() {
  const queryClient = useQueryClient();
  const [projectId, setProjectId] = useState<number>();
  const [documentId, setDocumentId] = useState<number>();
  const [question, setQuestion] = useState("What medication is used to manage type 2 diabetes?");
  const [expectedChunkId, setExpectedChunkId] = useState<number>();
  const [evaluation, setEvaluation] = useState<RagEvaluation>();
  const projects = useQuery({ queryKey: ["projects"], queryFn: () => api<Project[]>("/projects") });
  const selectedProjectId = projectId ?? projects.data?.[0]?.id;
  const documents = useQuery({ queryKey: ["rag-documents", selectedProjectId], queryFn: () => api<RagDocument[]>(`/rag/documents?project_id=${selectedProjectId}`), enabled: !!selectedProjectId });
  const selectedDocumentId = documentId && documents.data?.some(item => item.id === documentId) ? documentId : documents.data?.[0]?.id;
  const chunks = useQuery({ queryKey: ["rag-chunks", selectedDocumentId], queryFn: () => api<RagChunk[]>(`/rag/documents/${selectedDocumentId}/chunks`), enabled: !!selectedDocumentId });
  const selectedExpectedChunkId = expectedChunkId && chunks.data?.some(item => item.id === expectedChunkId) ? expectedChunkId : chunks.data?.[0]?.id;
  const ingest = useMutation({ mutationFn: (body: unknown) => api<RagDocument>("/rag/documents", { method: "POST", body: JSON.stringify(body) }), onSuccess: document => { queryClient.invalidateQueries({ queryKey: ["rag-documents", selectedProjectId] }); setDocumentId(document.id); } });
  const run = useMutation({ mutationFn: (body: unknown) => api<RagEvaluation>("/rag/evaluations", { method: "POST", body: JSON.stringify(body) }), onSuccess: setEvaluation });
  const result = evaluation?.results[0];

  return <div className="space-y-6">
    <header><p className="text-sm font-medium text-teal">Grounded retrieval evaluation</p><h1 className="text-3xl font-bold">RAG Lab</h1><p className="mt-1 max-w-3xl text-sm text-slate-500">Compare a vector baseline with hybrid retrieval using expected evidence, Recall@K, MRR, citations, and a no-regression quality gate.</p></header>
    {(ingest.error || run.error) && <ErrorBox error={ingest.error || run.error}/>}
    <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <section className="space-y-4">
        <form className="card space-y-3 p-5" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); ingest.mutate({ project_id: Number(form.get("project_id")), title: form.get("title"), source_uri: form.get("source_uri"), content: form.get("content"), chunk_size: 24, chunk_overlap: 6 }); }}>
          <div><p className="font-semibold">1. Index a knowledge document</p><p className="mt-1 text-xs text-slate-500">Content is chunked, hashed for idempotency, and embedded locally.</p></div>
          <select name="project_id" value={selectedProjectId ?? ""} onChange={event => { setProjectId(Number(event.target.value)); setDocumentId(undefined); setExpectedChunkId(undefined); }} className="w-full" required><option value="">Select project</option>{projects.data?.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}</select>
          <input name="title" className="w-full" defaultValue="Synthetic medication safety guide" required/>
          <input name="source_uri" className="w-full" defaultValue="fixture://synthetic-medication-guide" aria-label="Source URI"/>
          <textarea name="content" className="min-h-44 w-full" defaultValue={DEMO_CONTENT} required/>
          <button className="btn w-full" disabled={ingest.isPending || !selectedProjectId}>{ingest.isPending ? "Indexing…" : "Index document"}</button>
        </form>
        <div className="card overflow-hidden"><div className="border-b border-line p-4"><h2 className="font-semibold">Knowledge base</h2></div>{documents.data?.length ? documents.data.map(document => <button key={document.id} onClick={() => { setDocumentId(document.id); setExpectedChunkId(undefined); }} className={`w-full border-b border-line p-4 text-left ${selectedDocumentId === document.id ? "bg-emerald-50" : "hover:bg-slate-50"}`}><p className="font-medium">{document.title}</p><p className="mt-1 text-xs text-slate-500">{document.chunk_count} chunks · {document.source_uri || "No source URI"}</p></button>) : <div className="p-5 text-sm text-slate-500">No indexed documents yet.</div>}</div>
      </section>
      <section className="space-y-4">
        {!selectedDocumentId ? <Empty title="Index or select a document" body="A RAG evaluation needs a versioned knowledge source and expected evidence."/> : <>
          <form className="card space-y-4 p-5" onSubmit={event => { event.preventDefault(); if (!selectedProjectId || !selectedExpectedChunkId) return; run.mutate({ project_id: selectedProjectId, name: "Vector vs hybrid retrieval", queries: [{ question, expected_chunk_ids: [selectedExpectedChunkId] }], baseline: { method: "vector", top_k: 1 }, candidate: { method: "hybrid", top_k: 3 } }); }}>
            <div><p className="font-semibold">2. Define expected evidence</p><p className="mt-1 text-xs text-slate-500">The selected chunk is the ground-truth evidence for this question.</p></div>
            <textarea className="w-full" value={question} onChange={event => setQuestion(event.target.value)} aria-label="Evaluation question"/>
            <select className="w-full" value={selectedExpectedChunkId ?? ""} onChange={event => setExpectedChunkId(Number(event.target.value))} aria-label="Expected evidence chunk" required>{chunks.data?.map(chunk => <option key={chunk.id} value={chunk.id}>Chunk {chunk.position + 1}: {chunk.content.slice(0, 90)}…</option>)}</select>
            <div className="grid gap-3 sm:grid-cols-2"><div className="rounded-md border border-line p-3"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Baseline</p><p className="mt-1 font-medium">Vector · top 1</p></div><div className="rounded-md border border-teal bg-emerald-50 p-3"><p className="text-xs font-semibold uppercase tracking-wide text-teal">Candidate</p><p className="mt-1 font-medium">Hybrid RRF · top 3</p></div></div>
            <button className="btn w-full" disabled={run.isPending || !selectedExpectedChunkId}>{run.isPending ? "Evaluating…" : "Run RAG comparison"}</button>
          </form>
          {evaluation && result && <div className="space-y-4"><section className={`card border-l-4 p-5 ${evaluation.summary.quality_gate_passed ? "border-l-emerald-500" : "border-l-red-500"}`}><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold">No-regression gate: {evaluation.summary.quality_gate_passed ? "Passed" : "Blocked"}</p><p className="text-sm text-slate-500">{evaluation.summary.improvements} improvements · {evaluation.summary.regressions} regressions</p></div><div className="text-right text-sm"><p>Recall@K {evaluation.summary.baseline_recall_at_k.toFixed(2)} → <strong>{evaluation.summary.candidate_recall_at_k.toFixed(2)}</strong></p><p>MRR {evaluation.summary.baseline_mrr.toFixed(2)} → <strong>{evaluation.summary.candidate_mrr.toFixed(2)}</strong></p></div></div></section><div className="grid gap-4 lg:grid-cols-2"><ResultCard label="Vector baseline" result={result.baseline}/><ResultCard label={`Hybrid candidate · ${result.change}`} result={result.candidate}/></div></div>}
        </>}
      </section>
    </div>
  </div>;
}

function ResultCard({ label, result }: { label: string; result: RagEvaluation["results"][number]["baseline"] }) {
  return <article className="card p-5"><p className="text-xs font-semibold uppercase tracking-wide text-teal">{label}</p><p className="mt-2 text-sm">{result.answer}</p><div className="mt-3 flex gap-2 text-xs"><span className="rounded bg-slate-100 px-2 py-1">Recall@K {result.recall_at_k.toFixed(2)}</span><span className="rounded bg-slate-100 px-2 py-1">MRR {result.mrr.toFixed(2)}</span></div><div className="mt-4 space-y-2">{result.citations.map(citation => <div key={citation.chunk_id} className="rounded-md border border-line bg-slate-50 p-3"><p className="text-xs font-semibold">[{citation.chunk_id}] {citation.document_title} · score {citation.score.toFixed(4)}</p><p className="mt-1 text-xs text-slate-600">{citation.content}</p></div>)}</div></article>;
}
