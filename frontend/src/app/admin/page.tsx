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
} from "lucide-react";
import { fetchRevenueSummary, trackDealClick } from "@/lib/api";
import { RevenueSummary } from "@/types";

export default function RevenueDashboard() {
  const [data, setData] = useState<RevenueSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchRevenueSummary();
      setData(res);
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
              Focusing 100% on high-intent WhatsApp broadcasts and verified price drops.
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

      {/* Channel Performance Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Share2 className="w-4 h-4 text-emerald-400" />
          <span>Clicks by High-Intent Distribution Channel</span>
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-emerald-900/40">
            <div className="flex items-center gap-2 mb-1">
              <MessageCircle className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-bold text-slate-200">WhatsApp VIP</span>
            </div>
            <div className="text-xl font-bold font-mono text-emerald-400">
              {data?.clicks_by_channel.whatsapp || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400">#1 Highest Converting Channel</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-sky-900/40">
            <div className="flex items-center gap-2 mb-1">
              <Send className="w-4 h-4 text-sky-400" />
              <span className="text-xs font-bold text-slate-200">Telegram Deals</span>
            </div>
            <div className="text-xl font-bold font-mono text-sky-400">
              {data?.clicks_by_channel.telegram || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400">Flash Price Drop Alerts</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-orange-900/40">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-orange-400">r/</span>
              <span className="text-xs font-bold text-slate-200">Reddit Communities</span>
            </div>
            <div className="text-xl font-bold font-mono text-orange-400">
              {data?.clicks_by_channel.reddit || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400">r/dealsforindia, r/GadgetsIndia</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-slate-400">𝕏</span>
              <span className="text-xs font-bold text-slate-200">X / Twitter</span>
            </div>
            <div className="text-xl font-bold font-mono text-slate-300">
              {data?.clicks_by_channel.x || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400">Price drop tweets</span>
          </div>
        </div>
      </div>

      {/* Active Deal Inventory & Estimated Commission per Sale */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              <span>Deal Revenue & Commission Economics (Sales Manager View)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Clear estimated commission (₹) and exact sales needed to reach ₹10 Lakh per deal.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Deal Title / ASIN</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Deal Price / MRP</th>
                <th className="py-3 px-4">Comm. Rate</th>
                <th className="py-3 px-4 text-emerald-400 font-bold">Est. Commission / Sale</th>
                <th className="py-3 px-4 text-amber-300">Sales to ₹10L</th>
                <th className="py-3 px-4">Subtag</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {data?.recent_deals && data.recent_deals.length > 0 ? (
                data.recent_deals.map((deal, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
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
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {deal.subtag}
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
                        <span>Check Deal</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </td>
                  </tr>
                ))
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
