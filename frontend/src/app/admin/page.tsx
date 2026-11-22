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
import { fetchRevenueSummary, trackDealClick, fetchActivityFeed } from "@/lib/api";
import { RevenueSummary, PostAttribution, ActivityFeedItem } from "@/types";

export default function RevenueDashboard() {
  const [data, setData] = useState<RevenueSummary | null>(null);
  const [activityFeed, setActivityFeed] = useState<ActivityFeedItem[]>([]);
  const [verdictFilter, setVerdictFilter] = useState<"ALL" | "PROMOTE" | "HOLD" | "KILL">("ALL");
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

  // Phase 5: Daily Operational Checklist State
  const [checklistCompleted, setChecklistCompleted] = useState<Record<string, boolean>>({});

  useEffect(() => {
    try {
      const saved = localStorage.getItem("bb_daily_checklist_v1");
      if (saved) {
        setChecklistCompleted(JSON.parse(saved));
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const toggleChecklistItem = (id: string) => {
    setChecklistCompleted((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      try {
        localStorage.setItem("bb_daily_checklist_v1", JSON.stringify(next));
      } catch (e) {}
      return next;
    });
  };

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

  const [copiedN8nUrl, setCopiedN8nUrl] = useState(false);
  const handleCopyN8nUrl = () => {
    const url = "http://127.0.0.1:8000/api/deals/export-n8n";
    navigator.clipboard.writeText(url);
    setCopiedN8nUrl(true);
    setTimeout(() => setCopiedN8nUrl(false), 2000);
  };

  const handleOneClickWhatsApp = (deal: any) => {
    const subtag = deal.subtag || `lf-wa-manual-${deal.asin.toLowerCase()}`;
    const affUrl = `https://www.amazon.in/dp/${deal.asin}?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=${subtag}`;
    const savings = Math.max(0, deal.mrp - deal.deal_price);
    const msg = `🔥 *VERIFIED PRICE DROP: ${deal.name}*\n\n` +
      `📉 *Deal Price: ₹${deal.deal_price.toLocaleString("en-IN")}* ~MRP ₹${deal.mrp.toLocaleString("en-IN")}~ (${deal.discount_pct}% OFF)\n` +
      `💰 *You Save: ₹${savings.toLocaleString("en-IN")}*\n\n` +
      `👉 *Order on Amazon (Free Prime Delivery):*\n${affUrl}\n\n` +
      `_(Deal live now on Amazon India — grab before stock sells out!)_`;

    trackDealClick({
      asin: deal.asin,
      channel: "whatsapp",
      subtag: subtag,
      campaign_id: deal.campaign_id,
    });
    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`, "_blank");
  };

  const handleOneClickTelegram = (deal: any) => {
    const subtag = deal.subtag || `lf-tg-manual-${deal.asin.toLowerCase()}`;
    const affUrl = `https://www.amazon.in/dp/${deal.asin}?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=${subtag}`;
    const msg = `🚨 **PRICE DROP ALERT** 🚨\n\n` +
      `**${deal.name}**\n\n` +
      `🏷 Price: **₹${deal.deal_price.toLocaleString("en-IN")}** ~₹${deal.mrp.toLocaleString("en-IN")}~ (${deal.discount_pct}% Off)\n\n` +
      `🛒 **Buy on Amazon:** [Check Deal Now](${affUrl})`;

    trackDealClick({
      asin: deal.asin,
      channel: "telegram",
      subtag: subtag,
      campaign_id: deal.campaign_id,
    });
    window.open(`https://t.me/share/url?url=${encodeURIComponent(affUrl)}&text=${encodeURIComponent(msg)}`, "_blank");
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchRevenueSummary();
      setData(res);
      if (res.average_commission_per_sale_inr) {
        setCalcAvgPrice(Math.round(res.average_commission_per_sale_inr / 0.08));
      }
      const feedRes = await fetchActivityFeed(25);
      if (feedRes && feedRes.activity_feed) {
        setActivityFeed(feedRes.activity_feed);
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
    const interval = setInterval(async () => {
      const feedRes = await fetchActivityFeed(25);
      if (feedRes && feedRes.activity_feed) {
        setActivityFeed(feedRes.activity_feed);
      }
    }, 12000);
    return () => clearInterval(interval);
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

          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              href="/dispatch"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-sky-950 hover:bg-sky-900 border border-sky-700/80 text-xs font-bold text-sky-300 transition-colors shadow-sm"
            >
              <span>🚀</span>
              <span>Open Dispatch Queue</span>
            </Link>
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

      {/* Phase 4 & 5: Daily Pace Indicator & Operational Execution Playbook */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Pace Indicator Card */}
        <div className="lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-950 border border-emerald-800/60 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-[10px] font-bold text-emerald-400 font-mono">
                Phase 4: Pace
              </span>
              <h2 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                Daily Pace Indicator
              </h2>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
              data?.daily_pace_indicator?.pace_status === "ON TRACK"
                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                : "bg-amber-950 text-amber-300 border border-amber-800"
            }`}>
              {data?.daily_pace_indicator?.pace_status || "NEEDS PUSH"}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between items-baseline mb-1">
                <span className="text-xs text-slate-400">Today's Target Pace</span>
                <span className="text-xs font-mono font-bold text-slate-200">
                  ₹{data?.daily_pace_indicator?.target_commission_today_inr?.toLocaleString("en-IN") || "11,111"}
                </span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-950 border border-slate-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-400 rounded-full transition-all"
                  style={{ width: `${Math.min(100, data?.daily_pace_indicator?.pace_percentage || 12)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
                <span>{data?.daily_pace_indicator?.pace_percentage || 12}% achieved today</span>
                <span>₹{data?.daily_pace_indicator?.achieved_commission_today_inr?.toLocaleString("en-IN") || "1,349"} est.</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block font-sans">Target Sales / Day</span>
                <span className="text-base font-bold text-slate-100">
                  {data?.daily_pace_indicator?.target_sales_today || 120}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950 border border-amber-900/40 text-center">
                <span className="text-[10px] text-amber-300 block font-sans">Sales Needed Today</span>
                <span className="text-base font-bold text-amber-400">
                  {data?.daily_pace_indicator?.remaining_sales_needed_today ?? 116}
                </span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
              {data?.daily_pace_indicator?.summary_message ||
                "Need 116 more sales today to maintain the ₹10 Lakh in 90 days runrate."}
            </p>
          </div>
        </div>

        {/* Daily Operational Checklist Card (Phase 5) */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-[10px] font-bold text-sky-300 font-mono">
                Phase 5: Playbook
              </span>
              <h2 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Daily Operational Checklist (₹11,111 / Day Rhythm)</span>
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/dispatch"
                className="text-[11px] font-semibold text-sky-400 hover:text-sky-300 underline font-mono"
              >
                Go to Dispatch Queue →
              </Link>
            </div>
          </div>

          <div className="space-y-2">
            {(data?.daily_checklist || [
              { id: "step_morning_hero", time: "08:30 IST", task: "Post Morning Hero deal to WhatsApp (Homemaker & Family)", completed: false, slot_id: "s1_morning" },
              { id: "step_midday_telemetry", time: "13:30 IST", task: "Review In-App Telemetry & Click Attribution on /admin", completed: false, slot_id: null },
              { id: "step_evening_impulse", time: "18:30 IST", task: "Post Evening Impulse deal (<₹499) to WhatsApp & Telegram", completed: false, slot_id: "s2_evening" },
              { id: "step_night_scarcity", time: "21:30 IST", task: "Post Scarcity Follow-up ('Price reverts at midnight') if clicks < 25", completed: false, slot_id: "s3_scarcity" },
              { id: "step_night_audit", time: "23:00 IST", task: "Verify daily clicks vs 2,500 click target & check ₹11,111 pace", completed: false, slot_id: null },
            ]).map((item) => {
              const isChecked = checklistCompleted[item.id] ?? item.completed;
              return (
                <div
                  key={item.id}
                  onClick={() => toggleChecklistItem(item.id)}
                  className={`flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer ${
                    isChecked
                      ? "bg-emerald-950/30 border-emerald-800/60 text-slate-200"
                      : "bg-slate-950/80 border-slate-800/80 hover:border-slate-700 text-slate-300"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {}} // handled by parent div onClick
                      className="w-4 h-4 rounded border-slate-700 text-emerald-500 accent-emerald-500 cursor-pointer"
                    />
                    <div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 mr-2 font-bold">
                        {item.time}
                      </span>
                      <span className={`text-xs font-medium ${isChecked ? "line-through text-slate-400" : "text-slate-100"}`}>
                        {item.task}
                      </span>
                    </div>
                  </div>
                  {item.slot_id && (
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                      Syncs with /dispatch
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Phase 3: Channel Performance & Recommended Next Post */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Channel Performance Card */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-[10px] font-bold text-emerald-400 font-mono">
                Phase 3 Feedback
              </span>
              <h2 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span>Channel Conversion Performance: WhatsApp vs Telegram</span>
              </h2>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              {data?.channel_performance?.summary || "WhatsApp yields higher net commission volume"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* WhatsApp Metrics */}
            <div className="p-4 rounded-xl bg-slate-950 border border-emerald-900/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                  <MessageCircle className="w-4 h-4 text-emerald-400" />
                  <span>WhatsApp VIP Broadcasts</span>
                </span>
                <span className="text-[10px] font-bold font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                  {data?.channel_performance?.whatsapp?.share_percent ?? 72}% share
                </span>
              </div>
              <div className="space-y-1.5 pt-1 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Clicks:</span>
                  <span className="text-slate-100 font-bold">{data?.channel_performance?.whatsapp?.clicks ?? 36} clicks</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Est. CVR:</span>
                  <span className="text-emerald-400 font-bold">{data?.channel_performance?.whatsapp?.cvr_estimate || "3.8% – 4.5%"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Est. Conversions:</span>
                  <span className="text-slate-200">{data?.channel_performance?.whatsapp?.est_conversions ?? 1.4} orders</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-slate-900">
                  <span className="text-slate-400 font-bold">Est. Net Commission:</span>
                  <span className="text-emerald-400 font-black">₹{data?.channel_performance?.whatsapp?.est_commission?.toLocaleString("en-IN") || "216"}</span>
                </div>
              </div>
            </div>

            {/* Telegram Metrics */}
            <div className="p-4 rounded-xl bg-slate-950 border border-sky-900/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                  <Send className="w-4 h-4 text-sky-400" />
                  <span>Telegram Deal Alerts</span>
                </span>
                <span className="text-[10px] font-bold font-mono text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800">
                  {data?.channel_performance?.telegram?.share_percent ?? 28}% share
                </span>
              </div>
              <div className="space-y-1.5 pt-1 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Clicks:</span>
                  <span className="text-slate-100 font-bold">{data?.channel_performance?.telegram?.clicks ?? 14} clicks</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Est. CVR:</span>
                  <span className="text-sky-400 font-bold">{data?.channel_performance?.telegram?.cvr_estimate || "2.0% – 2.8%"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Est. Conversions:</span>
                  <span className="text-slate-200">{data?.channel_performance?.telegram?.est_conversions ?? 0.4} orders</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-slate-900">
                  <span className="text-slate-400 font-bold">Est. Net Commission:</span>
                  <span className="text-sky-400 font-black">₹{data?.channel_performance?.telegram?.est_commission?.toLocaleString("en-IN") || "54"}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Recommended Next Post Combination */}
        <div className="lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-950 border border-purple-900/60 rounded-2xl p-6 shadow-xl space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="px-2 py-0.5 rounded bg-purple-950 border border-purple-800 text-[10px] font-bold text-purple-300 font-mono">
                🎯 Next Post Suggestion
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                IST Hour: {data?.recommended_next_post?.current_ist_hour ?? 19}:00
              </span>
            </div>

            <h3 className="text-sm font-black text-purple-300">
              {data?.recommended_next_post?.time_slot || "Evening Impulse Drop (18:30 IST)"}
            </h3>

            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-xs font-bold text-emerald-300 font-mono">
                {data?.recommended_next_post?.channel === "whatsapp" ? "WhatsApp VIP" : "Telegram"}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-xs font-bold text-slate-200 font-mono">
                {data?.recommended_next_post?.audience === "homemaker" ? "🏠 Homemaker" : data?.recommended_next_post?.audience === "office" ? "💼 Office Pro" : "⚡ Budget/Hostel"}
              </span>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
              {data?.recommended_next_post?.rationale ||
                "Sub-₹499 impulse deals convert at 4.8% among Hostel and Budget Deal Hunter groups post-commute."}
            </p>
          </div>

          <Link
            href="/dispatch"
            className="w-full inline-flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white transition-colors shadow-md mt-2"
          >
            <span>🚀 Open in Dispatch Queue</span>
          </Link>
        </div>
      </div>

      {/* Feature 5: Daily Performance Summary Command Center */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-[10px] font-bold text-emerald-400 uppercase tracking-widest font-mono">
              Feature 5: Daily Performance
            </span>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Daily Performance Command Center</span>
            </h2>
          </div>
          <span className="text-xs text-slate-400 font-mono">Updated in real-time from verified Associate clicks</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Card 1: Yesterday's Top 3 Deals by Clicks */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <span className="text-emerald-400">🔥 Top 3 Deals (By Clicks)</span>
              <span className="font-mono text-slate-500">24H Window</span>
            </div>
            <div className="space-y-1.5 pt-1">
              {data?.daily_performance?.top_3_deals && data.daily_performance.top_3_deals.length > 0 ? (
                data.daily_performance.top_3_deals.map((t, idx) => (
                  <div key={idx} className="flex items-center justify-between p-1.5 rounded bg-slate-900 border border-slate-800/80">
                    <div className="truncate max-w-[145px]">
                      <span className="font-semibold text-slate-200 block truncate text-[11px]" title={t.title}>
                        #{idx + 1} {t.title}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">{t.asin}</span>
                    </div>
                    <div className="text-right font-mono">
                      <span className="text-cyan-300 font-bold block">{t.clicks} clicks</span>
                      <span className="text-[10px] text-emerald-400">+₹{t.est_commission.toFixed(0)}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-[11px]">Collecting click trends...</p>
              )}
            </div>
          </div>

          {/* Card 2: Winning Channel (WhatsApp vs Telegram) */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <span className="text-sky-400">🏆 Best Performing Channel</span>
              <span className="font-mono text-emerald-400">{data?.daily_performance?.best_performing_channel?.share_percent || 75}% share</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-emerald-900/60 space-y-1 text-center">
              <span className="text-base font-black text-emerald-300 font-mono block">
                {data?.daily_performance?.best_performing_channel?.label || "WhatsApp VIP Broadcasts"}
              </span>
              <p className="text-[11px] text-slate-400">
                {data?.daily_performance?.best_performing_channel?.vs_telegram || "WhatsApp leads with higher conversion intent"}
              </p>
            </div>
          </div>

          {/* Card 3: Current Pace vs ₹10 Lakh Target */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <span className="text-amber-400">⚡ Pace vs ₹10L Target</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                data?.daily_performance?.pace_vs_target?.pace_status === "ON TRACK"
                  ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                  : "bg-amber-950 text-amber-300 border border-amber-800"
              }`}>
                {data?.daily_performance?.pace_vs_target?.pace_status || "NEEDS ACCELERATION"}
              </span>
            </div>
            <div className="space-y-1 pt-1">
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-slate-400">Daily Target:</span>
                <span className="text-slate-200 font-bold">₹{data?.daily_performance?.pace_vs_target?.daily_target_runrate?.toLocaleString("en-IN") || "11,111"}/day</span>
              </div>
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-slate-400">Est. Daily Run-rate:</span>
                <span className="text-emerald-400 font-bold">₹{data?.daily_performance?.pace_vs_target?.current_daily_runrate?.toLocaleString("en-IN") || "1,349"}/day</span>
              </div>
              <div className="flex justify-between font-mono text-[11px] pt-1 border-t border-slate-900">
                <span className="text-slate-400">Run-rate Gap:</span>
                <span className="text-rose-400 font-bold">₹{data?.daily_performance?.pace_vs_target?.runrate_gap?.toLocaleString("en-IN") || "9,762"}/day</span>
              </div>
            </div>
          </div>

          {/* Card 4: Remaining Posts Needed Today */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <span className="text-teal-400">📋 Remaining Posts Today</span>
              <span className="font-mono text-slate-400">Quota: 80/day</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-teal-900/60 text-center space-y-1">
              <div className="text-3xl font-black text-teal-300 font-mono">
                {data?.daily_performance?.remaining_posts_needed_today?.remaining_today ?? 74}
              </div>
              <p className="text-[10px] text-slate-400">
                {data?.daily_performance?.remaining_posts_needed_today?.posts_completed_today || 6} broadcasted · {data?.daily_performance?.remaining_posts_needed_today?.remaining_today ?? 74} remaining to hit daily clicks target
              </p>
            </div>
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

      {/* Dub.co Server-Side Device & In-App Browser Telemetry Grid */}
      <div className="bg-slate-900 border border-cyan-900/40 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <MousePointerClick className="w-4 h-4 text-cyan-400" />
              <span>Dub.co-Style Server-Side Device & In-App Browser Telemetry</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Zero ad-block attribution tracking devices and native in-app shoppers for Amazon app deeplinking.
            </p>
          </div>
          <span className="text-xs text-cyan-400 font-mono">100% Server-Side HTTP 302/307</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 font-sans block mb-1">📱 Mobile Android</span>
            <div className="text-xl font-bold text-emerald-400">
              {data?.clicks_by_device?.mobile_android ?? 34} clicks
            </div>
            <span className="text-[10px] text-slate-500 font-sans mt-1 block">Amazon App Deeplink #1</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 font-sans block mb-1">🍏 Mobile iOS / iPhone</span>
            <div className="text-xl font-bold text-sky-400">
              {data?.clicks_by_device?.mobile_ios ?? 12} clicks
            </div>
            <span className="text-[10px] text-slate-500 font-sans mt-1 block">High AOV Shoppers</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 font-sans block mb-1">💻 Desktop (Win/Mac)</span>
            <div className="text-xl font-bold text-amber-400">
              {((data?.clicks_by_device?.desktop_windows ?? 5) + (data?.clicks_by_device?.desktop_mac ?? 2))} clicks
            </div>
            <span className="text-[10px] text-slate-500 font-sans mt-1 block">Office & Work Browsing</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 font-sans block mb-1">💬 In-App WhatsApp/Telegram</span>
            <div className="text-xl font-bold text-purple-400">
              {((data?.clicks_by_app?.whatsapp ?? 36) + (data?.clicks_by_app?.telegram ?? 14))} clicks
            </div>
            <span className="text-[10px] text-slate-500 font-sans mt-1 block">Direct In-App Webview</span>
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

      {/* Feature 4: n8n-Ready Webhook Export Card */}
      <div className="bg-slate-900 border border-purple-900/40 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-purple-950 border border-purple-800 text-[10px] font-bold text-purple-300 uppercase tracking-widest font-mono">
              Feature 4: Automation Webhook
            </span>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" />
              <span>n8n-Ready Webhook & Pipeline Export</span>
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyN8nUrl}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-950 hover:bg-purple-900 border border-purple-700 text-xs font-semibold text-purple-200 transition-colors"
            >
              {copiedN8nUrl ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedN8nUrl ? "Webhook URL Copied!" : "Copy n8n Webhook URL"}</span>
            </button>
            <a
              href="http://127.0.0.1:8000/api/deals/export-n8n?limit=15"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
            >
              <span>Preview Live JSON ↗</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="md:col-span-2 p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-sans font-bold">Endpoint:</span>
            <code className="text-purple-300 select-all block">POST http://127.0.0.1:8000/api/deals/export-n8n</code>
            <p className="text-[10px] text-slate-400 font-sans mt-2">
              Returns strictly approved <code className="text-emerald-400">🟢 PROMOTE</code> deals with pre-formatted WhatsApp & Telegram messages, unique tags, and tag=dammaiprasad-21 Amazon links for automatic n8n broadcast bots.
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[10px] text-slate-400 overflow-x-auto">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-sans font-bold mb-1">Payload Schema:</span>
            <pre className="text-slate-300">
{`{
  "asin": "B002MPPTB8",
  "title": "Hawkins Futura Cooker",
  "price": 2499,
  "discount": 25,
  "affiliate_url": "...",
  "whatsapp_message": "...",
  "telegram_message": "...",
  "unique_tag": "lf-n8n-..."
}`}
            </pre>
          </div>
        </div>
      </div>

      {/* Phase 3: Deal Quality Filter & Pool Ladder Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-[10px] font-bold text-emerald-400 uppercase tracking-widest font-mono">
                Pool Ladder Engine
              </span>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span>Phase 3 Quality Gated Deals (Apollo & Explee Pool Ladder)</span>
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Deals scored by conversion velocity (0–100) factoring in commission yield, discount depth, trust rating, and impulse price sweet spot.
            </p>
          </div>

          {/* Pool Ladder Filter Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setVerdictFilter("ALL")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                verdictFilter === "ALL"
                  ? "bg-slate-700 text-white"
                  : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              All Deals ({data?.recent_deals?.length || 0})
            </button>
            <button
              onClick={() => setVerdictFilter("PROMOTE")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                verdictFilter === "PROMOTE"
                  ? "bg-emerald-950 text-emerald-300 border border-emerald-700"
                  : "bg-slate-950 text-emerald-400/80 hover:text-emerald-300 border border-slate-800"
              }`}
            >
              🟢 PROMOTE (
              {data?.recent_deals?.filter((d) => (d.quality_verdict?.verdict || "HOLD") === "PROMOTE").length || 0}
              )
            </button>
            <button
              onClick={() => setVerdictFilter("HOLD")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                verdictFilter === "HOLD"
                  ? "bg-amber-950 text-amber-300 border border-amber-700"
                  : "bg-slate-950 text-amber-400/80 hover:text-amber-300 border border-slate-800"
              }`}
            >
              🟡 HOLD (
              {data?.recent_deals?.filter((d) => (d.quality_verdict?.verdict || "HOLD") === "HOLD").length || 0}
              )
            </button>
            <button
              onClick={() => setVerdictFilter("KILL")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                verdictFilter === "KILL"
                  ? "bg-rose-950 text-rose-300 border border-rose-700"
                  : "bg-slate-950 text-rose-400/80 hover:text-rose-300 border border-slate-800"
              }`}
            >
              🔴 KILL ({data?.recent_deals?.filter((d) => d.quality_verdict?.verdict === "KILL").length || 0})
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Pool Verdict & Velocity</th>
                <th className="py-3 px-4">Deal Title / ASIN</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Deal Price / MRP</th>
                <th className="py-3 px-4">Comm. Rate</th>
                <th className="py-3 px-4 text-emerald-400 font-bold">Est. Comm. / Sale</th>
                <th className="py-3 px-4 text-amber-300">Sales to ₹10L</th>
                <th className="py-3 px-4 text-right">Instant Launch</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {data?.recent_deals && data.recent_deals.length > 0 ? (
                data.recent_deals
                  .filter((deal) => {
                    const verdict =
                      deal.quality_verdict?.verdict ||
                      (deal.commission_rate_percent >= 6 && deal.discount_pct >= 35 ? "PROMOTE" : "HOLD");
                    if (verdictFilter === "ALL") return true;
                    return verdict === verdictFilter;
                  })
                  .map((deal, idx) => {
                    const verdict =
                      deal.quality_verdict?.verdict ||
                      (deal.commission_rate_percent >= 6 && deal.discount_pct >= 35 ? "PROMOTE" : "HOLD");
                    const score =
                      deal.quality_verdict?.composite_velocity_score ??
                      (verdict === "PROMOTE" ? 85 : verdict === "HOLD" ? 60 : 35);
                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4">
                          <span
                            className={`px-2.5 py-1 rounded-full text-[11px] font-bold font-mono inline-flex items-center gap-1 ${
                              verdict === "PROMOTE"
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : verdict === "HOLD"
                                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                                  : "bg-rose-950 text-rose-300 border border-rose-800"
                            }`}
                          >
                            {verdict === "PROMOTE" ? "🟢 PROMOTE" : verdict === "HOLD" ? "🟡 HOLD" : "🔴 KILL"}
                          </span>
                          <div className="text-[10px] text-slate-400 font-mono mt-1">
                            Velocity: <span className="font-bold text-emerald-400">{score}/100</span>
                          </div>
                          {(deal.loot_badge || deal.quality_verdict?.loot_badge) && (
                            <div className="text-[10px] font-bold text-amber-300 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800/80 mt-1 inline-block">
                              {deal.loot_badge || deal.quality_verdict?.loot_badge}
                            </div>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-100 max-w-xs truncate" title={deal.name}>
                            {deal.name}
                          </div>
                          <div className="font-mono text-[11px] text-slate-500">ASIN: {deal.asin}</div>
                          {deal.quality_verdict?.why_it_converts && (
                            <div className="text-[10px] text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/60 mt-1 max-w-sm line-clamp-2" title={deal.quality_verdict.why_it_converts}>
                              💡 <span className="font-semibold text-emerald-300">Claygent:</span> {deal.quality_verdict.why_it_converts}
                            </div>
                          )}
                          {(deal.quality_verdict as any)?.freshness_safety?.safety_badge && (
                            <div className="text-[10px] font-mono font-bold text-slate-300 mt-1">
                              <span>{(deal.quality_verdict as any).freshness_safety.safety_badge}</span>
                            </div>
                          )}
                          {(deal.quality_verdict as any)?.freshness_safety?.warnings?.length > 0 && (
                            <div className="text-[10px] text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-900/60 mt-0.5 max-w-sm">
                              {(deal.quality_verdict as any).freshness_safety.warnings[0]}
                            </div>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-medium">
                            {deal.category}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono">
                          <div className="text-slate-100 font-bold">₹{deal.deal_price.toLocaleString("en-IN")}</div>
                          <div className="text-slate-500 text-[11px] line-through">
                            ₹{deal.mrp.toLocaleString("en-IN")} ({deal.discount_pct}% off)
                          </div>
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
                          <div className="inline-flex items-center gap-1.5 justify-end">
                            <button
                              type="button"
                              onClick={() => handleOneClickWhatsApp(deal)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-950 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-[11px] font-semibold transition-colors"
                              title="Format and open directly in WhatsApp Web"
                            >
                              <MessageCircle className="w-3 h-3" />
                              <span>WhatsApp</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleOneClickTelegram(deal)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-950 hover:bg-sky-900 border border-sky-800 text-sky-300 text-[11px] font-semibold transition-colors"
                              title="Format and open directly in Telegram"
                            >
                              <Send className="w-3 h-3" />
                              <span>Telegram</span>
                            </button>
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
                              className="inline-flex items-center gap-1 p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition-colors"
                              title="Open on Amazon"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          </div>
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

      {/* Apollo & Instantly-Style Real-time Live Click Activity Feed */}
      <div className="bg-slate-900 border border-cyan-900/40 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <MousePointerClick className="w-4 h-4 text-cyan-400" />
                <span>Instantly & Apollo-Style Activity Stream & Sequence Attribution</span>
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Live click stream with sequence touchpoint attribution (S1 Morning, S2 Evening, S3 Scarcity), unique <code className="text-cyan-300 font-mono">ascsubtag</code>, and realized commission yield.
            </p>
          </div>
          <button
            onClick={loadData}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh Feed</span>
          </button>
        </div>

        {/* Instantly-Style 3-Step Sequence Attribution Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-amber-900/50">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-amber-300 flex items-center gap-1.5">
                ☀️ S1: Morning Hero
              </span>
              <span className="font-mono text-[10px] bg-amber-950 text-amber-200 px-1.5 py-0.5 rounded border border-amber-800 font-semibold">
                08:30 IST (0h delay)
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-amber-400 mt-1.5">
              {data?.clicks_by_step?.step1_morning || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-0.5">Top-commission utility drop</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-sky-900/50">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-sky-300 flex items-center gap-1.5">
                🌙 S2: Evening Impulse
              </span>
              <span className="font-mono text-[10px] bg-sky-950 text-sky-200 px-1.5 py-0.5 rounded border border-sky-800 font-semibold">
                18:30 IST (+10h delay)
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-sky-400 mt-1.5">
              {data?.clicks_by_step?.step2_evening || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-0.5">Sub-₹499 lightning checkout</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-rose-900/50">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-rose-300 flex items-center gap-1.5">
                ⚡ S3: Scarcity Nudge
              </span>
              <span className="font-mono text-[10px] bg-rose-950 text-rose-200 px-1.5 py-0.5 rounded border border-rose-800 font-semibold">
                Conditional (+26h)
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-rose-400 mt-1.5">
              {data?.clicks_by_step?.step3_scarcity || 0} clicks
            </div>
            <span className="text-[10px] text-slate-400 block mt-0.5">Midnight price bounce recovery</span>
          </div>
        </div>

        {activityFeed && activityFeed.length > 0 ? (
          <div className="divide-y divide-slate-800 overflow-x-auto pt-2">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Channel</th>
                  <th className="py-2.5 px-3">Sequence Touch</th>
                  <th className="py-2.5 px-3">Product / ASIN</th>
                  <th className="py-2.5 px-3">Attribution Subtag</th>
                  <th className="py-2.5 px-3">Referrer</th>
                  <th className="py-2.5 px-3 text-right text-emerald-400">Est. Yield / Sale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300 font-mono text-[11px]">
                {activityFeed.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 px-3 text-slate-400">
                      {new Date(item.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          item.channel === "whatsapp"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : item.channel === "telegram"
                              ? "bg-sky-950 text-sky-300 border border-sky-800"
                              : item.channel === "reddit"
                                ? "bg-orange-950 text-orange-300 border border-orange-800"
                                : "bg-slate-950 text-slate-300 border border-slate-800"
                        }`}
                      >
                        {item.channel_badge || item.channel}
                      </span>
                      {item.device_badge && (
                        <span className="ml-1.5 px-1.5 py-0.5 rounded text-[10px] bg-slate-950 text-slate-300 border border-slate-800 font-sans">
                          {item.device_badge}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300">
                        {item.step_label || "🔥 Direct Drop"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-200 max-w-xs truncate" title={item.title}>
                      {item.title} <span className="text-[10px] text-slate-500 font-mono">({item.asin})</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <code className="text-cyan-300 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/60 text-[10px]">
                        {item.subtag}
                      </code>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans text-[11px]">
                      {item.referrer || "Direct"}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                      +₹{item.est_commission_rupees.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-slate-500 text-xs py-4 text-center">
            No live clicks recorded yet. Share deal broadcasts to begin real-time attribution.
          </p>
        )}
      </div>
    </div>
  );
}
