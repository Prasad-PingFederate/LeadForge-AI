"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Send,
  MessageCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  Share2,
  Copy,
  Check,
  ExternalLink,
  ShieldAlert,
  RefreshCw,
  Flame,
  Target,
  Zap,
  Download,
  AlertTriangle,
  Info,
  Calendar,
} from "lucide-react";
import { fetchDispatchQueue, markDealSent, fetchN8nWorkflowTemplate } from "@/lib/api";
import { DispatchQueueSlot } from "@/types";

export default function DispatchQueuePage() {
  const [slots, setSlots] = useState<DispatchQueueSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Per-slot audience and channel selections
  const [selectedAudience, setSelectedAudience] = useState<Record<string, string>>({});
  const [selectedChannel, setSelectedChannel] = useState<Record<string, "whatsapp" | "telegram">>({});

  // Action states
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [n8nModalOpen, setN8nModalOpen] = useState(false);
  const [n8nTemplateJson, setN8nTemplateJson] = useState<any>(null);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const res = await fetchDispatchQueue();
      if (res && res.slots) {
        setSlots(res.slots);
        // Default audiences per slot if not already set
        const defaultAud: Record<string, string> = {};
        const defaultCh: Record<string, "whatsapp" | "telegram"> = {};
        res.slots.forEach((s) => {
          defaultAud[s.slot_id] = selectedAudience[s.slot_id] || (s.slot_id === "s1_morning" ? "homemaker" : (s.slot_id === "s2_evening" ? "hostel_college" : "budget_impulse"));
          defaultCh[s.slot_id] = selectedChannel[s.slot_id] || "whatsapp";
        });
        setSelectedAudience((prev) => ({ ...defaultAud, ...prev }));
        setSelectedChannel((prev) => ({ ...defaultCh, ...prev }));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load dispatch queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
    // Auto-refresh queue every 20 seconds
    const interval = setInterval(loadQueue, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkSent = async (slot: DispatchQueueSlot) => {
    const aud = selectedAudience[slot.slot_id] || "homemaker";
    const ch = selectedChannel[slot.slot_id] || "whatsapp";
    const variants = ch === "telegram" ? slot.audience_variants_telegram : slot.audience_variants_whatsapp;
    const subtag = variants[aud]?.subtag || slot.unique_subtag;

    try {
      setMarkingId(slot.slot_id);
      await markDealSent({
        slot_id: slot.slot_id,
        asin: slot.asin,
        channel: ch,
        audience: aud,
        subtag: subtag,
      });

      // Update local state immediately
      setSlots((prev) =>
        prev.map((s) =>
          s.slot_id === slot.slot_id
            ? { ...s, is_sent: true, sent_channel: ch, sent_audience: aud, dispatched_at: new Date().toISOString() }
            : s
        )
      );
    } catch (err) {
      console.error("Failed to mark as sent:", err);
    } finally {
      setMarkingId(null);
    }
  };

  const handleCopyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleLaunchWhatsApp = (slot: DispatchQueueSlot) => {
    const aud = selectedAudience[slot.slot_id] || "homemaker";
    const msg = slot.audience_variants_whatsapp[aud]?.message || slot.title;
    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`, "_blank");
  };

  const handleLaunchTelegram = (slot: DispatchQueueSlot) => {
    const aud = selectedAudience[slot.slot_id] || "budget_impulse";
    const item = slot.audience_variants_telegram[aud];
    const affUrl = item?.affiliate_url || slot.canonical_affiliate_url;
    const msg = item?.message || slot.title;
    window.open(`https://t.me/share/url?url=${encodeURIComponent(affUrl)}&text=${encodeURIComponent(msg)}`, "_blank");
  };

  const handleOpenN8nModal = async () => {
    setN8nModalOpen(true);
    if (!n8nTemplateJson) {
      try {
        const res = await fetchN8nWorkflowTemplate();
        setN8nTemplateJson(res.workflow);
      } catch (e) {
        console.error("Failed to fetch n8n template", e);
      }
    }
  };

  const handleDownloadN8n = () => {
    if (!n8nTemplateJson) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(n8nTemplateJson, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "bharatbazaro_telegram_n8n_workflow.json");
    dlAnchorElem.click();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-950/80 via-slate-900 to-slate-900 border border-sky-800/50 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-xs font-bold text-sky-400 mb-2">
              <Clock className="w-3.5 h-3.5" />
              <span>Real Distribution Automation (Phase 1 & 2)</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
              High-Velocity Deal Dispatch Queue
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-2xl">
              Today’s 3 strategic waves (Morning Hero, Evening Impulse, Scarcity Nudge) calibrated for WhatsApp VIP groups and Telegram alerts with audience-specific psychological copy.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={handleOpenN8nModal}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-950 hover:bg-purple-900 border border-purple-700/80 text-xs font-bold text-purple-200 transition-colors shadow-sm"
            >
              <Zap className="w-3.5 h-3.5 text-purple-400" />
              <span>n8n Workflow JSON</span>
            </button>
            <button
              onClick={loadQueue}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
              <span>Refresh Queue</span>
            </button>
            <Link
              href="/admin"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white transition-colors shadow-lg shadow-emerald-950/50"
            >
              <span>💰 Revenue Tracker</span>
            </Link>
          </div>
        </div>
      </div>

      {/* WhatsApp Anti-Ban Safeguards & Pacing Warning Box */}
      <div className="bg-amber-950/30 border border-amber-800/60 rounded-xl p-4 sm:p-5 text-xs text-amber-200/90 space-y-2">
        <div className="flex items-center gap-2 font-bold text-amber-300 text-sm">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>Evolution API & Baileys Anti-Ban Guardrails</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1 text-[11px]">
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-amber-900/40">
            <span className="font-bold text-amber-300 block mb-0.5">⏱ 45–60s Delay</span>
            <span className="text-slate-400">Pacing between group broadcasts to prevent automated spam flags.</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-amber-900/40">
            <span className="font-bold text-amber-300 block mb-0.5">✍️ Typing Presence</span>
            <span className="text-slate-400">Keep 1500ms composing presence simulated before message dispatch.</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-amber-900/40">
            <span className="font-bold text-amber-300 block mb-0.5">🔒 50 Groups / Day Cap</span>
            <span className="text-slate-400">Strict maximum daily broadcast limit per WhatsApp number/instance.</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-amber-900/40">
            <span className="font-bold text-amber-300 block mb-0.5">🔄 Persona Rotation</span>
            <span className="text-slate-400">Rotate copy (Homemaker vs Hostel vs Budget) across group categories.</span>
          </div>
        </div>
      </div>

      {/* Today's 3 Slots Timeline */}
      {loading && slots.length === 0 ? (
        <div className="text-center py-16">
          <RefreshCw className="w-8 h-8 text-sky-400 animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading today’s high-yield dispatch lineup...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {slots.map((slot, idx) => {
            const currentAud = selectedAudience[slot.slot_id] || (slot.slot_id === "s1_morning" ? "homemaker" : (slot.slot_id === "s2_evening" ? "hostel_college" : "budget_impulse"));
            const currentCh = selectedChannel[slot.slot_id] || "whatsapp";
            const variants = currentCh === "telegram" ? slot.audience_variants_telegram : slot.audience_variants_whatsapp;
            const currentVariant = variants[currentAud] || Object.values(variants)[0];

            return (
              <div
                key={slot.slot_id}
                className={`bg-slate-900 border rounded-2xl p-5 sm:p-6 shadow-xl space-y-5 transition-all ${
                  slot.is_sent ? "border-emerald-800/80 bg-slate-900/90" : "border-slate-800"
                }`}
              >
                {/* Slot Top Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-sm text-sky-400">
                      0{idx + 1}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base sm:text-lg font-bold text-slate-100">{slot.slot_name}</h2>
                        {slot.loot_badge && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800 font-mono">
                            {slot.loot_badge}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                        <span className="font-mono text-emerald-400 font-semibold">{slot.timing_ist}</span>
                        <span>•</span>
                        <span>{slot.delay_info}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Indicator & Mark as Sent Button */}
                  <div className="flex items-center gap-3 self-start sm:self-auto">
                    {slot.is_sent ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950 border border-emerald-700 text-xs font-bold text-emerald-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span>Sent via {slot.sent_channel === "telegram" ? "Telegram" : "WhatsApp"} ({slot.sent_audience})</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleMarkSent(slot)}
                        disabled={markingId === slot.slot_id}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white transition-all shadow-md shadow-emerald-950/50 disabled:opacity-50"
                      >
                        {markingId === slot.slot_id ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        <span>Mark as Sent</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Deal Context Strip */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 font-sans block uppercase">Product / ASIN</span>
                    <span className="font-semibold text-slate-200 block truncate" title={slot.title}>
                      {slot.title}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">{slot.asin}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-sans block uppercase">Deal Price / MRP</span>
                    <span className="text-slate-100 font-bold">₹{slot.deal_price.toLocaleString("en-IN")}</span>
                    <span className="text-[10px] text-slate-500 line-through ml-1">₹{slot.mrp.toLocaleString("en-IN")}</span>
                    <span className="text-emerald-400 text-[10px] ml-1">({slot.discount_pct}% off)</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-sans block uppercase">Commission Yield</span>
                    <span className="text-emerald-400 font-bold block">+₹{slot.estimated_commission_rupees.toFixed(2)} / sale</span>
                    <span className="text-[10px] text-slate-400">{slot.commission_rate_percent}% category rate</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-sans block uppercase">Attribution Subtag</span>
                    <code className="text-cyan-300 text-[10px] bg-cyan-950/60 px-1 py-0.5 rounded border border-cyan-800/50">
                      {currentVariant?.subtag || slot.unique_subtag}
                    </code>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-sans block uppercase">Buyer Trust</span>
                    <span className="text-amber-300 font-bold block">⭐️ {slot.rating}/5</span>
                    <span className="text-[10px] text-slate-400 font-sans">{slot.review_count.toLocaleString("en-IN")} reviews</span>
                  </div>
                </div>

                {/* Claygent Rationale & Freshness/Safety Strip */}
                <div className="space-y-2">
                  {slot.why_it_converts && (
                    <div className="text-xs text-emerald-400 bg-emerald-950/30 px-3 py-1.5 rounded-lg border border-emerald-900/50 flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-300 shrink-0" />
                      <span><strong className="text-emerald-300 font-semibold">Claygent Rationale:</strong> {slot.why_it_converts}</span>
                    </div>
                  )}

                  {slot.freshness_safety && (
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="font-mono font-bold text-[11px] px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300">
                        {slot.freshness_safety.safety_badge}
                      </span>
                      {slot.historical_clicks !== undefined && slot.historical_clicks > 0 && (
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 font-bold">
                          ⚡ {slot.historical_clicks} verified clicks in feed
                        </span>
                      )}
                      {slot.freshness_safety.warnings?.length > 0 && (
                        <span className="text-[11px] text-amber-300 font-medium">
                          {slot.freshness_safety.warnings[0]}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Audience Segmentation & Channel Toggle Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">
                      Audience Persona:
                    </span>
                    <button
                      onClick={() => setSelectedAudience((prev) => ({ ...prev, [slot.slot_id]: "homemaker" }))}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                        currentAud === "homemaker"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-700 shadow-sm"
                          : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                      }`}
                    >
                      🏠 Homemaker & Family
                    </button>
                    <button
                      onClick={() => setSelectedAudience((prev) => ({ ...prev, [slot.slot_id]: "hostel_college" }))}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                        currentAud === "hostel_college"
                          ? "bg-sky-950 text-sky-300 border border-sky-700 shadow-sm"
                          : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                      }`}
                    >
                      🎒 Hostel & College
                    </button>
                    <button
                      onClick={() => setSelectedAudience((prev) => ({ ...prev, [slot.slot_id]: "office_pro" }))}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                        currentAud === "office_pro"
                          ? "bg-purple-950 text-purple-300 border border-purple-700 shadow-sm"
                          : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                      }`}
                    >
                      💼 Office Pro
                    </button>
                    <button
                      onClick={() => setSelectedAudience((prev) => ({ ...prev, [slot.slot_id]: "budget_impulse" }))}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                        currentAud === "budget_impulse"
                          ? "bg-amber-950 text-amber-300 border border-amber-700 shadow-sm"
                          : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                      }`}
                    >
                      ⚡ Budget Impulse
                    </button>
                  </div>

                  {/* Channel Switch */}
                  <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 self-start sm:self-auto">
                    <button
                      onClick={() => setSelectedChannel((prev) => ({ ...prev, [slot.slot_id]: "whatsapp" }))}
                      className={`px-2.5 py-1 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                        currentCh === "whatsapp"
                          ? "bg-emerald-600 text-white"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <MessageCircle className="w-3 h-3" />
                      <span>WhatsApp</span>
                    </button>
                    <button
                      onClick={() => setSelectedChannel((prev) => ({ ...prev, [slot.slot_id]: "telegram" }))}
                      className={`px-2.5 py-1 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                        currentCh === "telegram"
                          ? "bg-sky-600 text-white"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Send className="w-3 h-3" />
                      <span>Telegram</span>
                    </button>
                  </div>
                </div>

                {/* Formatted Message Box */}
                <div className="relative rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-slate-200">
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80 text-[11px] text-slate-400 font-sans">
                    <span className="flex items-center gap-2">
                      <span className="font-semibold text-slate-300">Live Formatted Preview:</span>
                      <span className="text-cyan-400 font-mono text-[10px]">
                        {currentVariant?.badge || "Deal Alert"}
                      </span>
                    </span>
                    <span>{currentVariant?.message?.length || 0} characters</span>
                  </div>

                  <pre className="whitespace-pre-wrap font-sans text-xs sm:text-sm text-slate-200 leading-relaxed max-h-56 overflow-y-auto">
                    {currentVariant?.message || "Generating audience message..."}
                  </pre>
                </div>

                {/* Action Buttons Toolbar */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => handleCopyText(currentVariant?.message || "", `msg-${slot.slot_id}`)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
                    >
                      {copiedKey === `msg-${slot.slot_id}` ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                      <span>{copiedKey === `msg-${slot.slot_id}` ? "Message Copied!" : "Copy Message"}</span>
                    </button>

                    <button
                      onClick={() =>
                        handleCopyText(
                          JSON.stringify(
                            {
                              number: "120363028392819283@g.us",
                              text: currentVariant?.message,
                              options: { delay: 1500, presence: "composing", linkPreview: true },
                            },
                            null,
                            2
                          ),
                          `evo-${slot.slot_id}`
                        )
                      }
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
                      title="Evolution API / Baileys JSON payload"
                    >
                      {copiedKey === `evo-${slot.slot_id}` ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Zap className="w-3.5 h-3.5 text-amber-400" />
                      )}
                      <span>Evolution API Payload</span>
                    </button>

                    <button
                      onClick={() =>
                        handleCopyText(
                          JSON.stringify(
                            {
                              chat_id: "@dealsforindia",
                              telegram_message: currentVariant?.message,
                              asin: slot.asin,
                              subtag: currentVariant?.subtag,
                            },
                            null,
                            2
                          ),
                          `n8n-${slot.slot_id}`
                        )
                      }
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
                      title="n8n webhook JSON payload"
                    >
                      {copiedKey === `n8n-${slot.slot_id}` ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Send className="w-3.5 h-3.5 text-purple-400" />
                      )}
                      <span>n8n Payload</span>
                    </button>
                  </div>

                  {/* Instant 1-Click Launchers */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleLaunchWhatsApp(slot)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 border border-emerald-800 text-xs font-bold text-emerald-300 transition-colors"
                    >
                      <MessageCircle className="w-3.5 h-3.5" />
                      <span>WhatsApp Web</span>
                    </button>
                    <button
                      onClick={() => handleLaunchTelegram(slot)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-950 hover:bg-sky-900 border border-sky-800 text-xs font-bold text-sky-300 transition-colors"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Telegram</span>
                    </button>
                    <a
                      href={currentVariant?.affiliate_url || slot.canonical_affiliate_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                      title="Test live affiliate link"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* n8n Workflow Modal */}
      {n8nModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-purple-800/60 rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-purple-400" />
                <h3 className="font-bold text-slate-100 text-base">Production n8n Workflow Template</h3>
              </div>
              <button
                onClick={() => setN8nModalOpen(false)}
                className="text-slate-400 hover:text-slate-100 text-sm px-2 py-1 rounded bg-slate-800"
              >
                ✕ Close
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Import this JSON directly into n8n (<code className="text-purple-300">Import from Clipboard</code>). It triggers on webhook, formats the deal markdown, and dispatches via your Telegram bot credentials to @dealsforindia.
            </p>

            <div className="overflow-y-auto flex-1 bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300">
              <pre className="whitespace-pre-wrap">{JSON.stringify(n8nTemplateJson, null, 2)}</pre>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => handleCopyText(JSON.stringify(n8nTemplateJson, null, 2), "modal-n8n")}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-950 hover:bg-purple-900 border border-purple-700 text-xs font-bold text-purple-200 transition-colors"
              >
                {copiedKey === "modal-n8n" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey === "modal-n8n" ? "Workflow JSON Copied!" : "Copy JSON to Clipboard"}</span>
              </button>
              <button
                onClick={handleDownloadN8n}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download .json File</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
