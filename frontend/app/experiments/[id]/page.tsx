"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, CircleX, Gauge } from "lucide-react";
import { api } from "@/lib/api";
import type { Page,Result,Run,RunDetail } from "@/lib/types";
import { ErrorBox,Json,Pager,Status } from "@/components/ui";

export default function Experiment(){
  const {id}=useParams<{id:string}>(); const [status,setStatus]=useState("all"); const [page,setPage]=useState(1); const qc=useQueryClient();
  const detail=useQuery({queryKey:["run",id],queryFn:()=>api<RunDetail>(`/experiments/${id}`),refetchInterval:q=>["pending","running"].includes(q.state.data?.run.status??"")?1000:false});
  const results=useQuery({queryKey:["results",id,status,page],queryFn:()=>api<Page<Result>>(`/experiments/${id}/results?status=${status}&page=${page}`),refetchInterval:detail.data&&["pending","running"].includes(detail.data.run.status)?1000:false});
  const cancel=useMutation({mutationFn:()=>api<Run>(`/experiments/${id}/cancel`,{method:"POST"}),onSuccess:()=>qc.invalidateQueries({queryKey:["run",id]})});
  if(detail.error)return <ErrorBox error={detail.error}/>; if(!detail.data)return <p>Loading experiment…</p>;
  const {run,summary}=detail.data;
  return <div className="space-y-5">
    <header className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-sm font-medium text-teal">Experiment #{run.id}</p><h1 className="text-3xl font-bold">{run.name}</h1><p className="mt-1 text-sm capitalize text-slate-500">{run.model} · {run.prompt_version} · {run.status}</p></div><div className="flex gap-2">{["pending","running"].includes(run.status)&&<button className="btn-secondary text-red-600" onClick={()=>cancel.mutate()} disabled={cancel.isPending}>Cancel run</button>}{run.baseline_run_id&&<Link href={`/experiments/${id}/compare?baseline=${run.baseline_run_id}`} className="btn">Compare with baseline</Link>}</div></header>
    {["pending","running"].includes(run.status)&&<section className="card p-5"><div className="mb-2 flex justify-between text-sm"><span>Evaluation in progress</span><span>{run.progress_completed} / {run.progress_total}</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-teal transition-all" style={{width:`${run.progress_total?run.progress_completed/run.progress_total*100:0}%`}}/></div></section>}
    {run.error&&<ErrorBox error={new Error(run.error)}/>}
    {run.status==="completed"&&<section className={`card flex flex-wrap items-center justify-between gap-4 border-l-4 p-5 ${summary.quality_gate.passed?"border-l-emerald-500":"border-l-red-500"}`}><div className="flex items-center gap-3">{summary.quality_gate.passed?<CheckCircle2 className="text-emerald-600"/>:<CircleX className="text-red-600"/>}<div><p className="font-semibold">Release quality gate: {summary.quality_gate.passed?"Passed":"Blocked"}</p><p className="text-sm text-slate-500">Candidate evaluated against explicit quality and latency thresholds.</p></div></div><div className="flex flex-wrap gap-2">{summary.quality_gate.checks.map(check=><span key={check.name} className={`rounded-full px-2.5 py-1 text-xs font-medium ${check.passed?"bg-emerald-50 text-emerald-700":"bg-red-50 text-red-700"}`}>{check.passed?"✓":"×"} {check.name}</span>)}</div></section>}
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">{[["Pass rate",`${Math.round(summary.pass_rate*100)}%`],["Mean F1",summary.mean_f1.toFixed(2)],["p50 latency",`${summary.p50_latency_ms} ms`],["p95 latency",`${summary.p95_latency_ms} ms`],["Tokens",(summary.input_tokens+summary.output_tokens).toLocaleString()]].map(([k,v])=><div className="card p-4" key={k}><p className="text-xs text-slate-500">{k}</p><p className="mt-1 text-2xl font-semibold">{v}</p></div>)}</section>
    <div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-line p-3"><h2 className="flex items-center gap-2 font-semibold"><Gauge size={17}/> Case results</h2><select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}><option value="all">All outcomes</option><option value="passed">Passed</option><option value="failed">Failed</option></select></div><div className="overflow-x-auto"><table><thead><tr><th>Case</th><th>Output</th><th>Status</th><th>Precision</th><th>Recall</th><th>F1</th><th>Latency</th></tr></thead><tbody>{results.data?.items.map(r=><tr key={r.id}><td className="max-w-xs"><Link className="font-medium text-teal hover:underline" href={`/review/${r.id}`}>{r.input}</Link><p className="mt-1 font-mono text-[10px] text-slate-400">{r.provider_request_id}</p></td><td><Json value={r.actual_output}/></td><td><Status passed={r.passed}/></td><td>{r.metric_details.precision.toFixed(2)}</td><td>{r.metric_details.recall.toFixed(2)}</td><td className="font-semibold">{r.metric_details.f1.toFixed(2)}</td><td>{r.latency_ms} ms</td></tr>)}</tbody></table></div>{results.data&&<Pager page={page} total={results.data.total} pageSize={results.data.page_size} onChange={setPage}/>}</div>
  </div>
}
