"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, ShieldCheck, Target, Zap, Globe, Compass, Users } from "lucide-react";
import { createCampaign } from "@/lib/api";

export default function Launchpad() {
  const router = useRouter();
  const [targetUrl, setTargetUrl] = useState("");
  const [description, setDescription] = useState("");
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUrl.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const camp = await createCampaign({
        target_url: targetUrl.trim(),
        name: name.trim() || undefined,
        description: description.trim() || undefined,
      });

      router.push(`/campaigns/${camp.id}/strategy`);
    } catch (err: any) {
      setError(err.message || "Failed to initialize pipeline");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-center px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-3xl mx-auto w-full">
        {/* Hero Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-xs font-semibold text-emerald-400 mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Multi-Agent B2B Sales & Intelligence Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-black text-slate-100 tracking-tight leading-tight">
            Turn Any Product URL Into <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              Verified High-Intent Leads
            </span>
          </h1>

          <p className="mt-4 text-sm sm:text-base text-slate-400 max-w-xl mx-auto">
            Autonomous ICP profiling, real competitor gap extraction, zero-hallucination lead discovery, live DNS MX verification, and signal-personalized outreach sequences.
          </p>
        </div>

        {/* Launchpad Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-1.5 flex items-center justify-between">
                <span>Product Website URL</span>
                <span className="text-slate-500 font-mono text-[11px] normal-case">e.g. resend.com or stripe.com</span>
              </label>
              <div className="relative">
                <Globe className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
                <input
                  type="text"
                  required
                  placeholder="https://yourproduct.com"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-1.5">
                  Campaign Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Q4 Competitor Displacement"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-1.5">
                  Extra Context / Focus (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Developer tools, eliminate per-seat costs"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-xs text-rose-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !targetUrl.trim()}
              className="w-full mt-2 py-3.5 px-6 rounded-xl font-bold text-sm bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition-all cursor-pointer"
            >
              {isLoading ? (
                <span>Spawning Autonomous Agent Pipeline...</span>
              ) : (
                <>
                  <span>Launch Autonomous Lead Generation</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800/40 flex items-center justify-center text-emerald-400 shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200">Zero Hallucinations</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                Every lead links to real public intent proof on Hacker News, Reddit, or verified business domains.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-950/60 border border-blue-800/40 flex items-center justify-center text-blue-400 shrink-0">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200">Battlecards & 3 GTM Angles</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                Autonomous competitor weakness extraction formulated into 3 targeted outreach angles.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-800/40 flex items-center justify-center text-purple-400 shrink-0">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200">Safe Deliverability Mailer</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                DNS MX validation, suppression list gating, HMAC unsubscribe tokens, and daily inbox caps.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
