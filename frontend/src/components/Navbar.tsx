"use client";

import Link from "next/link";
import { Sparkles, ShieldCheck, Target, ArrowUpRight } from "lucide-react";

export default function Navbar() {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:border-emerald-500 transition-colors">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-lg text-slate-100 tracking-tight flex items-center gap-1.5">
              LeadForge <span className="text-emerald-400 font-mono text-sm px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40">AI</span>
            </span>
          </div>
        </Link>

        <div className="flex items-center gap-6 text-sm">
          <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-3 py-1.5 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Zero Hallucination Guaranteed</span>
          </div>

          <a
            href="https://github.com/Prasad-PingFederate/LeadForge-AI"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-slate-400 hover:text-slate-100 transition-colors"
          >
            <span>GitHub</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </header>
  );
}
