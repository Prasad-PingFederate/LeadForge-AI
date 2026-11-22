"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  DollarSign,
  Target,
  MousePointerClick,
  Share2,
  ExternalLink,
  Flame,
  CheckCircle2,
  RefreshCw,
  ShoppingBag,
  MessageCircle,
  Send,
  Zap,
  Calculator,
  Sliders,
  Check,
  XCircle,
  AlertTriangle,
  Copy,
  Plus,
} from "lucide-react";
import { fetchRevenueSummary, trackDealClick } from "@/lib/api";
import { RevenueSummary, PostAttribution } from "@/types";

export default function RevenueDashboard() {
  const [data, setData] = useState<RevenueSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedSubtag, setCopiedSubtag] = useState<string | null>(null);
  const [loggingClickId, setLoggingClickId] = useState<string | null>(null);

  // Phase 4: Interactive ₹10 Lakh Math Calculator State
  const [calcTarget, setCalcTarget] = useState<number>(1000000);
  const [calcDays, setCalcDays] = useState<number>(90);
  const [calcAvgPrice, setCalcAvgPrice] = useState<number>(1499);
  const [calcCommRate, setCalcCommRate] = useState<number>(8.0);
  const [calcConvRate, setCalcConvRate] = useState<number>(1.5); // %
  const [calcClicksPerPost, setCalcClicksPerPost] = useState<number>(75);

  const handleManualLogClick = async (post: PostAttribution) => {
    try {
      setLoggingClickId(post.id);
      await trackDealClick({
        asin: post.asin,
        channel: post.channel,
        subtag: post.subtag,
        outreach_id: post.id.startsWith("post-") ? undefined : post.id,
      });
      await loadData();
    } catch (err) {
      console.error("Failed to log click manually:", err);
    } finally {
      setLoggingClickId(null);
    }
  };

  const handleCopyShortLink = (subtag: string) => {
    const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const url = `${origin}/go/${subtag}`;
    navigator.clipboard.writeText(url);
    setCopiedSubtag(subtag);
    setTimeout(() => setCopiedSubtag(null), 2000);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchRevenueSummary();
      setData(res);
      if (res.average_commission_per_sale_inr) {
        setCalcAvgPrice(Math.round(res.average_commission_per_sale_inr / 0.08));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load revenue metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-sm">Loading Sales Manager Revenue Dashboard...</p>
      </div>
    );
  }

  const target = data?.target_commission_inr || 1000000;
  const estPool = data?.estimated_commission_pool_inr || 0;
  const progressPct = Math.min(100, Math.round((estPool / target) * 100));

  // Phase 4 Math Calculations
  const calcCommPerSale = Math.max(1, (calcAvgPrice * calcCommRate) / 100);
  const calcTotalSalesNeeded = Math.ceil(calcTarget / calcCommPerSale);
  const calcDailySalesNeeded = Math.ceil(calcTotalSalesNeeded / calcDays);
  const calcTotalClicksNeeded = Math.ceil(calcTotalSalesNeeded / (calcConvRate / 100));
  const calcDailyClicksNeeded = Math.ceil(calcTotalClicksNeeded / calcDays);
  const calcDailyPostsNeeded = Math.ceil(calcDailyClicksNeeded / calcClicksPerPost);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-950/80 via-slate-900 to-slate-900 border border-emerald-800/50 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-bold text-emerald-400 mb-2">
              <Target className="w-3.5 h-3.5" />
              <span>Target: ₹10,00,000 Commission in 90 Days</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
              BharatBazaro ₹10 Lakh Revenue Command Center
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-2xl">
              Ruthless conversion tracking for tag <code className="font-mono text-emerald-300 bg-slate-950 px-1.5 py-0.5 rounded border border-emerald-800/40">dammaiprasad-21</code>.
              Focusing 100% on high-intent WhatsApp broadcasts, Telegram loot alerts, and verified price drops.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh Metrics</span>
            </button>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white transition-colors shadow-lg shadow-emerald-950/50"
            >
              <Flame className="w-3.5 h-3.5 text-amber-300" />
              <span>Launch New Deal</span>
            </Link>
          </div>
        </div>

        {/* ₹10 Lakh Progress Bar */}
        <div className="mt-6 pt-6 border-t border-slate-800/80 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-300">
              Pipeline Commission Potential: <span className="text-emerald-400 font-bold font-mono">₹{estPool.toLocaleString("en-IN")}</span>
            </span>
            <span className="text-slate-400 font-mono">
              Target: <span className="text-slate-200 font-bold">₹10,00,000</span> ({progressPct}%)
            </span>
          </div>
          <div className="w-full h-3 rounded-full bg-slate-950 border border-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
              style={{ width: `${Math.max(4, progressPct)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Posts Generated</span>
            <Share2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-slate-100 font-mono">
            {data?.total_posts_generated || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Ready for WhatsApp & Telegram distribution</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Total Tracked Clicks</span>
            <MousePointerClick className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-slate-100 font-mono">
            {data?.total_clicks || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Via unique granular <code className="text-cyan-300">ascsubtag</code></p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Avg Commission / Sale</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            ₹{data?.average_commission_per_sale_inr || 150}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Weighted across 7%–9% Home & Appliances</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Sales to Hit ₹10 Lakh</span>
            <Target className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-300 font-mono">
            {data?.total_sales_needed_for_10_lakh?.toLocaleString("en-IN") || "6,667"}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">~{Math.ceil((data?.total_sales_needed_for_10_lakh || 6667) / 90)} orders/day needed over 90 days</p>
        </div>
      </div>

      {/* Phase 4: ₹10 Lakh Interactive Math Calculator */}
      <div className="bg-slate-900 border border-emerald-800/50 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-emerald-400" />
              <span>₹10 Lakh Sales Math & Daily Posting Quota Calculator</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Adjust conversion variables to compute the exact daily operational rhythm required to hit ₹10 Lakh in commissions.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono text-xs font-bold self-start sm:self-auto">
            Phase 4 Standard
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Controls Column */}
          <div className="space-y-4 md:col-span-1 bg-slate-950/80 p-5 rounded-xl border border-slate-800">
            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1 flex justify-between">
                <span>Target Commission</span>
                <span className="text-emerald-400 font-mono">₹{calcTarget.toLocaleString("en-IN")}</span>
              </label>
              <input
                type="number"
                value={calcTarget}
                onChange={(e) => setCalcTarget(Number(e.target.value) || 1000000)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1 flex justify-between">
                <span>Avg. Deal Price (₹)</span>
                <span className="text-emerald-400 font-mono">₹{calcAvgPrice}</span>
              </label>
              <input
                type="range"
                min="299"
                max="4999"
                step="50"
                value={calcAvgPrice}
                onChange={(e) => setCalcAvgPrice(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1 flex justify-between">
                <span>Avg. Commission Rate</span>
                <span className="text-emerald-400 font-mono">{calcCommRate}%</span>
              </label>
              <input
                type="range"
                min="5"
                max="9"
                step="0.5"
                value={calcCommRate}
                onChange={(e) => setCalcCommRate(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1 flex justify-between">
                <span>WhatsApp Conversion Rate</span>
                <span className="text-cyan-400 font-mono">{calcConvRate}%</span>
              </label>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={calcConvRate}
                onChange={(e) => setCalcConvRate(Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500">Benchmark: 1.0%–2.0% for WhatsApp VIP loot broadcasts</span>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1 flex justify-between">
                <span>Avg Clicks per Broadcast</span>
                <span className="text-amber-400 font-mono">{calcClicksPerPost} clicks</span>
              </label>
              <input
                type="range"
                min="20"
                max="250"
                step="5"
                value={calcClicksPerPost}
                onChange={(e) => setCalcClicksPerPost(Number(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>
          </div>

          {/* Results Display Columns */}
          <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 block mb-1">
                  Commission per Sale
                </span>
                <div className="text-3xl font-black font-mono text-emerald-400">
                  ₹{calcCommPerSale.toFixed(2)}
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  At ₹{calcAvgPrice.toLocaleString("en-IN")} deal price with {calcCommRate}% Amazon India category commission.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs font-mono text-slate-300">
                1 sale = <span className="text-emerald-400 font-bold">₹{calcCommPerSale.toFixed(0)}</span> in pocket
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-950 border border-amber-900/40 flex flex-col justify-between">
              <div>
                <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 block mb-1">
                  Total Orders Required
                </span>
                <div className="text-3xl font-black font-mono text-amber-300">
                  {calcTotalSalesNeeded.toLocaleString("en-IN")} sales
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Need <span className="font-bold text-amber-300 font-mono">{calcDailySalesNeeded} orders / day</span> across 90 days.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs font-mono text-slate-300">
                Daily Revenue Pace: <span className="text-amber-300 font-bold">₹{Math.ceil(calcTarget / calcDays).toLocaleString("en-IN")} / day</span>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-950 border border-cyan-900/40 flex flex-col justify-between">
              <div>
                <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 block mb-1">
                  Total Clicks Required
                </span>
                <div className="text-3xl font-black font-mono text-cyan-400">
                  {calcTotalClicksNeeded.toLocaleString("en-IN")}
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Target: <span className="font-bold text-cyan-300 font-mono">{calcDailyClicksNeeded.toLocaleString("en-IN")} clicks / day</span> (at {calcConvRate}% CVR).
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs font-mono text-slate-300">
                Tracked via <span className="text-cyan-400 font-bold">lf-wa-*</span> tags
              </div>
            </div>

            <div className="p-5 rounded-xl bg-gradient-to-br from-emerald-950/60 to-slate-950 border border-emerald-800 flex flex-col justify-between">
              <div>
                <span className="text-[11px] uppercase tracking-wider font-bold text-emerald-300 block mb-1">
                  Daily WhatsApp Broadcast Quota
                </span>
                <div className="text-3xl font-black font-mono text-white">
                  {calcDailyPostsNeeded} posts / day
                </div>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  Post <span className="font-bold text-emerald-400">{calcDailyPostsNeeded} verified drops</span> daily across Homemaker, Hostel & Budget WhatsApp groups.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-emerald-800/60 text-xs font-semibold text-emerald-300">
                👉 Direct path to hitting ₹10,00,000!
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Phase 5: Self-Learning Adaptive Multipliers & Channel Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Share2 className="w-4 h-4 text-emerald-400" />
            <span>Phase 5 Self-Learning Loop: Dynamic Channel Quotas</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Auto-weights strategies by real click velocity
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-emerald-900/60">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <MessageCircle className="w-3.5 h-3.5 text-emerald-400" />
                WhatsApp VIP
              </span>
              <span className="text-[10px] font-bold font-mono bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800/60">
                {data?.channel_learning_weights?.whatsapp || 1.5}x Boost
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-2">
              {data?.clicks_by_channel.whatsapp || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">#1 Highest Converting Channel</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-sky-900/60">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <Send className="w-3.5 h-3.5 text-sky-400" />
                Telegram Deals
              </span>
              <span className="text-[10px] font-bold font-mono bg-sky-950 text-sky-300 px-1.5 py-0.5 rounded border border-sky-800/60">
                {data?.channel_learning_weights?.telegram || 1.25}x Boost
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-sky-400 mt-2">
              {data?.clicks_by_channel.telegram || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">Instant price drop alerts</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-orange-900/60">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <span className="text-orange-400 font-bold">r/</span>
                Reddit Forums
              </span>
              <span className="text-[10px] font-bold font-mono bg-orange-950 text-orange-300 px-1.5 py-0.5 rounded border border-orange-800/60">
                {data?.channel_learning_weights?.reddit || 1.0}x
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-orange-400 mt-2">
              {data?.clicks_by_channel.reddit || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">r/dealsforindia recommendations</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <span className="text-slate-400 font-bold">𝕏</span>
                Twitter / X
              </span>
              <span className="text-[10px] font-bold font-mono bg-slate-900 text-slate-300 px-1.5 py-0.5 rounded border border-slate-800">
                {data?.channel_learning_weights?.x || 0.8}x
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-slate-300 mt-2">
              {data?.clicks_by_channel.x || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">Price drop hashtags</span>
          </div>
        </div>
      </div>

      {/* Feature 1: Full Click Attribution Dashboard (Highest Priority) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4 bg-slate-950/40">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-[10px] font-bold text-emerald-400 uppercase tracking-widest font-mono">
                Feature 1: Attribution Engine
              </span>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <MousePointerClick className="w-4 h-4 text-emerald-400" />
                <span>Full Click & Conversion Attribution Dashboard</span>
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Every broadcast post tracked via unique <code className="text-emerald-300 font-mono">ascsubtag</code>. Logs real-time clicks from <code className="text-cyan-300">/go/:subtag</code> and manual log actions, calculating projected commission at 1.0%–1.5% conversion rates.
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Total Tracked Posts: <span className="font-bold text-emerald-400">{data?.posts_attribution?.length || 0}</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Post Subtag / Short URL</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4">Deal Title / ASIN</th>
                <th className="py-3 px-4 text-center">Tracked Clicks</th>
                <th className="py-3 px-4 text-center">Est. Conversions (1%–1.5%)</th>
                <th className="py-3 px-4 text-emerald-400 font-bold">Est. Comm. Potential (1%–1.5%)</th>
                <th className="py-3 px-4 text-right">Quick Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {data?.posts_attribution && data.posts_attribution.length > 0 ? (
                data.posts_attribution.map((post) => {
                  const estConvLow = (post.clicks * 0.01).toFixed(1);
                  const estConvHigh = (post.clicks * 0.015).toFixed(1);
                  return (
                    <tr key={post.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <code className="text-[11px] font-mono text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/60 font-semibold">
                            {post.subtag}
                          </code>
                          <button
                            type="button"
                            onClick={() => handleCopyShortLink(post.subtag)}
                            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                            title="Copy short redirect link"
                          >
                            {copiedSubtag === post.subtag ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
                          /go/{post.subtag}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                            post.channel === "whatsapp"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : post.channel === "telegram"
                                ? "bg-sky-950 text-sky-300 border border-sky-800"
                                : post.channel === "reddit"
                                  ? "bg-orange-950 text-orange-300 border border-orange-800"
                                  : "bg-slate-950 text-slate-300 border border-slate-800"
                          }`}
                        >
                          {post.channel}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-100 max-w-xs truncate" title={post.title}>
                          {post.title}
                        </div>
                        <div className="font-mono text-[10px] text-slate-500">
                          ASIN: {post.asin} · ₹{post.deal_price.toLocaleString("en-IN")} · Comm {post.commission_rate_percent}% (₹{post.commission_per_sale.toFixed(0)}/sale)
                        </div>
                      </td>

                      <td className="py-3 px-4 text-center font-mono">
                        <div className="inline-flex items-center gap-2">
                          <span className="text-sm font-bold text-slate-100 bg-slate-950 px-2.5 py-0.5 rounded border border-slate-800">
                            {post.clicks}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleManualLogClick(post)}
                            disabled={loggingClickId === post.id}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-emerald-400 hover:text-emerald-300 text-[10px] font-semibold transition-colors disabled:opacity-50"
                            title="Manually log a click for this post"
                          >
                            <Plus className="w-2.5 h-2.5" />
                            <span>Log Click</span>
                          </button>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-center font-mono text-slate-300">
                        <span className="bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800/80 text-[11px]">
                          {estConvLow} – {estConvHigh} sales
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono font-bold text-sm text-emerald-400 bg-emerald-950/10">
                        ₹{post.est_commission_1pct.toFixed(2)} – ₹{post.est_commission_1_5pct.toFixed(2)}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <a
                            href={`http://127.0.0.1:8000/go/${post.subtag}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-medium transition-colors"
                            title="Test short link HTTP 302 redirect to Amazon with affiliate tag"
                          >
                            <span>Test Redirect</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500">
                    No tracked posts yet. Generate deals to view click attribution and commission potential.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Phase 3: Deal Quality Filter & Economics Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              <span>Phase 3 Quality Gated Deals (Promote / Hold / Kill Verdicts)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Only deals passing the 6 sales manager criteria (≥35% discount, ₹99–₹2,999, ≥4.2 rating, ≥500 reviews, ≥6% commission) earn the 🟢 PROMOTE verdict.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Quality Verdict</th>
                <th className="py-3 px-4">Deal Title / ASIN</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Deal Price / MRP</th>
                <th className="py-3 px-4">Comm. Rate</th>
                <th className="py-3 px-4 text-emerald-400 font-bold">Est. Comm. / Sale</th>
                <th className="py-3 px-4 text-amber-300">Sales to ₹10L</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {data?.recent_deals && data.recent_deals.length > 0 ? (
                data.recent_deals.map((deal, idx) => {
                  const verdict = deal.quality_verdict?.verdict || (deal.commission_rate_percent >= 6 && deal.discount_pct >= 35 ? "PROMOTE" : "HOLD");
                  return (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold font-mono inline-flex items-center gap-1 ${
                          verdict === "PROMOTE" ? "bg-emerald-950 text-emerald-300 border border-emerald-800" :
                          verdict === "HOLD" ? "bg-amber-950 text-amber-300 border border-amber-800" :
                          "bg-rose-950 text-rose-300 border border-rose-800"
                        }`}>
                          {verdict === "PROMOTE" ? "🟢 PROMOTE" : verdict === "HOLD" ? "🟡 HOLD" : "🔴 KILL"}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-100 max-w-xs truncate" title={deal.name}>
                          {deal.name}
                        </div>
                        <div className="font-mono text-[11px] text-slate-500">ASIN: {deal.asin}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-medium">
                          {deal.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <div className="text-slate-100 font-bold">₹{deal.deal_price.toLocaleString("en-IN")}</div>
                        <div className="text-slate-500 text-[11px] line-through">₹{deal.mrp.toLocaleString("en-IN")} ({deal.discount_pct}% off)</div>
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-200">
                        {deal.commission_rate_percent}%
                      </td>
                      <td className="py-3 px-4 font-mono font-black text-sm text-emerald-400 bg-emerald-950/20">
                        +₹{deal.estimated_commission_rupees.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-mono text-amber-300 font-semibold">
                        {deal.sales_needed_for_10_lakh.toLocaleString("en-IN")}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <a
                          href={`https://www.amazon.in/dp/${deal.asin}?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=${deal.subtag}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={() =>
                            trackDealClick({
                              asin: deal.asin,
                              channel: "admin",
                              subtag: deal.subtag,
                              campaign_id: deal.campaign_id,
                            })
                          }
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition-colors"
                        >
                          <span>Open Deal</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-slate-500">
                    No active deal campaigns found. Launch a deal to start tracking commissions.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Real-time Clicks Activity Audit Log */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
          <MousePointerClick className="w-4 h-4 text-cyan-400" />
          <span>Real-Time Click Attribution Log (Amazon Associates Subtags)</span>
        </h2>
        {data?.recent_clicks && data.recent_clicks.length > 0 ? (
          <div className="divide-y divide-slate-800">
            {data.recent_clicks.map((clk) => (
              <div key={clk.id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                    clk.channel === "whatsapp" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                    clk.channel === "telegram" ? "bg-sky-950 text-sky-400 border border-sky-800" :
                    clk.channel === "reddit" ? "bg-orange-950 text-orange-400 border border-orange-800" :
                    "bg-slate-950 text-slate-300 border border-slate-800"
                  }`}>
                    {clk.channel}
                  </span>
                  <span className="font-mono text-slate-200">ASIN: {clk.asin}</span>
                  <span className="font-mono text-slate-500 text-[11px]">{clk.subtag}</span>
                </div>
                <div className="font-mono text-slate-500 text-[11px]">
                  {new Date(clk.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-xs">No clicks recorded yet. Share deal broadcasts to begin real-time attribution.</p>
        )}
      </div>
    </div>
  );
}
