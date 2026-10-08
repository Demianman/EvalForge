"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, Database, FlaskConical, LogOut, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
const nav = [{href:"/dashboard",label:"Dashboard",icon:BarChart3},{href:"/datasets",label:"Datasets",icon:Database},{href:"/experiments/new",label:"New experiment",icon:FlaskConical}];
export function Shell({children}:{children:React.ReactNode}) {
  const path=usePathname();
  const router=useRouter();
  if(path==="/login") return <>{children}</>;
  return <div className="min-h-screen md:grid md:grid-cols-[230px_1fr]">
    <aside className="border-b border-line bg-[#132521] p-5 text-white md:min-h-screen md:border-b-0">
      <Link href="/dashboard" className="mb-8 flex items-center gap-2 text-lg font-bold"><ShieldCheck className="text-emerald-400"/> EvalForge</Link>
      <nav className="flex gap-2 md:flex-col">{nav.map(({href,label,icon:Icon})=><Link key={href} href={href} className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${path.startsWith(href)?"bg-white/15 text-white":"text-slate-300 hover:bg-white/10"}`}><Icon size={17}/>{label}</Link>)}</nav>
      <button className="mt-8 flex items-center gap-2 text-xs text-slate-400" onClick={async()=>{await api("/auth/logout",{method:"POST"});router.push("/login")}}><LogOut size={14}/> Sign out</button>
    </aside>
    <main className="min-w-0 p-5 md:p-8">{children}</main>
  </div>;
}
