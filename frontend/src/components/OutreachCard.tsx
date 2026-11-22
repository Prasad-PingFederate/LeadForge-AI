"use client";

import { useState } from "react";
import { OutreachMessage } from "@/types";
import {
  Mail,
  Linkedin,
  MessageSquare,
  ShieldCheck,
  CheckCircle,
  Send,
  Play,
  RotateCcw,
  Sparkles,
  ExternalLink,
  MessageCircle,
  Copy,
  Check,
  Share2,
} from "lucide-react";
import { updateOutreach, dispatchOutreach, postReplyFeedback } from "@/lib/api";

interface OutreachCardProps {
  message: OutreachMessage;
  onRefresh?: () => void;
}

export default function OutreachCard({ message, onRefresh }: OutreachCardProps) {
  const [activeTab, setActiveTab] = useState<
    "whatsapp" | "telegram" | "step1" | "step2" | "step3" | "linkedin" | "social"
  >(message.whatsapp_message ? "whatsapp" : "step1");

  const [subject, setSubject] = useState(message.subject || "");
  const [step1, setStep1] = useState(message.body_step1 || "");
  const [step2, setStep2] = useState(message.body_step2 || "");
  const [step3, setStep3] = useState(message.body_step3 || "");
  const [linkedinDm, setLinkedinDm] = useState(message.linkedin_dm || "");
  const [socialReply, setSocialReply] = useState(message.social_reply || "");
  const [whatsappMsg, setWhatsappMsg] = useState(message.whatsapp_message || "");
  const [telegramMsg, setTelegramMsg] = useState(message.telegram_message || "");
  const [status, setStatus] = useState<string>(message.status || "draft");

  const [copied, setCopied] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sendResult, setSendResult] = useState<string | null>(null);

  // Simulated reply test modal
  const [isReplyModalOpen, setIsReplyModalOpen] = useState(false);
  const [simulatedReply, setSimulatedReply] = useState("");
  const [replyResult, setReplyResult] = useState<any>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenWhatsApp = () => {
    const textToShare = whatsappMsg || step1;
    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(textToShare)}`;
    window.open(url, "_blank");
  };

  const handleOpenTelegram = () => {
    const textToShare = telegramMsg || step1;
    const affUrl = message.deal_affiliate_url || "";
    const url = `https://t.me/share/url?url=${encodeURIComponent(affUrl)}&text=${encodeURIComponent(textToShare)}`;
    window.open(url, "_blank");
  };

  const handleSave = async () => {
    try {
      await updateOutreach(message.id, {
        subject,
        body_step1: step1,
        body_step2: step2,
        body_step3: step3,
        linkedin_dm: linkedinDm,
        social_reply: socialReply,
        whatsapp_message: whatsappMsg,
        telegram_message: telegramMsg,
      });
      setSendResult("✓ Sequence edits saved!");
      setTimeout(() => setSendResult(null), 3000);
    } catch (e: any) {
      setSendResult(`Error: ${e.message}`);
    }
  };

  const handleApprove = async () => {
    try {
      await updateOutreach(message.id, { status: "approved" });
      setStatus("approved");
      setSendResult("✓ Approved for autonomous delivery");
      setTimeout(() => setSendResult(null), 3000);
    } catch (e: any) {
      setSendResult(`Error: ${e.message}`);
    }
  };

  const handleDispatch = async (dryRun: boolean) => {
    setIsSending(true);
    setSendResult(null);
    try {
      const res = await dispatchOutreach(message.id, dryRun);
      if (res.success) {
        setStatus(dryRun ? "sent_dry_run" : "sent");
        setSendResult(
          dryRun
            ? `✓ [Dry-Run Safe Dispatch] Validated gates & generated unsubscribe token for ${res.recipient}`
            : `✓ Live SMTP Dispatch completed for ${res.recipient}`
        );
        if (onRefresh) onRefresh();
      } else {
        setSendResult(`Delivery Blocked: ${res.error}`);
      }
    } catch (e: any) {
      setSendResult(`Error: ${e.message}`);
    } finally {
      setIsSending(false);
    }
  };

  const handleSimulateReply = async () => {
    if (!simulatedReply) return;
    try {
      const res = await postReplyFeedback(message.id, simulatedReply);
      setReplyResult(res);
      setStatus(res.lead_status);
      if (onRefresh) onRefresh();
    } catch (e: any) {
      setReplyResult({ error: e.message });
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg transition-all hover:border-slate-700">
      {/* Header */}
      <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-100 text-sm">{message.company_name}</h3>
            {message.overall_score !== undefined && (
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                {message.overall_score}/100 Fit
              </span>
            )}
            {message.deal_affiliate_url && (
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/40">
                tag=dammaiprasad-21
              </span>
            )}
          </div>
          <span className="text-xs text-slate-400 font-mono mt-0.5 block">
            {message.contact_name || "Community Member"} &lt;{message.contact_email || "verified prospect"}&gt;
          </span>
        </div>

        {/* Status pill & Proof */}
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wider ${
              status === "sent"
                ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                : status === "sent_dry_run"
                ? "bg-blue-950 text-blue-400 border border-blue-800"
                : status === "approved"
                ? "bg-amber-950 text-amber-400 border border-amber-800"
                : "bg-slate-800 text-slate-400 border border-slate-700"
            }`}
          >
            {status.replace("_", " ")}
          </span>

          {message.intent_source_url && (
            <a
              href={message.intent_source_url}
              target="_blank"
              rel="noreferrer"
              className="p-1 rounded text-slate-500 hover:text-emerald-400 transition-colors"
              title="Inspect intent proof URL"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-950/30 text-xs font-medium px-4 overflow-x-auto">
        {/* WhatsApp Tab */}
        <button
          onClick={() => setActiveTab("whatsapp")}
          className={`py-2.5 px-3 border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "whatsapp"
              ? "border-emerald-500 text-emerald-400 font-bold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <MessageCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>WhatsApp Broadcast (VIP)</span>
        </button>

        {/* Telegram Tab */}
        <button
          onClick={() => setActiveTab("telegram")}
          className={`py-2.5 px-3 border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "telegram"
              ? "border-sky-500 text-sky-400 font-bold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Send className="w-3.5 h-3.5 text-sky-400" />
          <span>Telegram Alert</span>
        </button>

        {/* Email Tabs */}
        <button
          onClick={() => setActiveTab("step1")}
          className={`py-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "step1" ? "border-blue-500 text-blue-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Email 1: Hook
        </button>
        <button
          onClick={() => setActiveTab("step2")}
          className={`py-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "step2" ? "border-blue-500 text-blue-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Email 2: Value Proof
        </button>
        <button
          onClick={() => setActiveTab("step3")}
          className={`py-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "step3" ? "border-blue-500 text-blue-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Email 3: Breakup
        </button>
        <button
          onClick={() => setActiveTab("linkedin")}
          className={`py-2.5 px-3 border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "linkedin" ? "border-sky-500 text-sky-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Linkedin className="w-3.5 h-3.5" />
          <span>LinkedIn DM</span>
        </button>
        <button
          onClick={() => setActiveTab("social")}
          className={`py-2.5 px-3 border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "social" ? "border-orange-500 text-orange-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Social Reply</span>
        </button>
      </div>

      {/* Editor Body */}
      <div className="p-4 space-y-3">
        {activeTab.startsWith("step") && (
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Subject Line
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              {activeTab === "whatsapp"
                ? "WhatsApp VIP Broadcast (Bold formatting, Rupee savings & Universal affiliate tag)"
                : activeTab === "telegram"
                ? "Telegram Loot Deal Alert (Markdown formatted with Instant Buy link)"
                : activeTab === "step1"
                ? "Cold Email Step 1 (Hook & CTA)"
                : activeTab === "step2"
                ? "Cold Email Step 2 (Customer Proof)"
                : activeTab === "step3"
                ? "Cold Email Step 3 (Breakup)"
                : activeTab === "linkedin"
                ? "LinkedIn Connection Note / DM"
                : "Helpful Community Reply"}
            </label>

            {/* Quick 1-Click Copy / Share for WhatsApp & Telegram */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  const content =
                    activeTab === "whatsapp"
                      ? whatsappMsg
                      : activeTab === "telegram"
                      ? telegramMsg
                      : activeTab === "step1"
                      ? step1
                      : activeTab === "step2"
                      ? step2
                      : activeTab === "step3"
                      ? step3
                      : activeTab === "linkedin"
                      ? linkedinDm
                      : socialReply;
                  handleCopy(content);
                }}
                className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied!" : "Copy Post"}</span>
              </button>

              {activeTab === "whatsapp" && (
                <button
                  type="button"
                  onClick={handleOpenWhatsApp}
                  className="inline-flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>Send in WhatsApp Web ↗</span>
                </button>
              )}

              {activeTab === "telegram" && (
                <button
                  type="button"
                  onClick={handleOpenTelegram}
                  className="inline-flex items-center gap-1 text-[11px] text-sky-400 hover:text-sky-300 font-semibold transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>Post to Telegram ↗</span>
                </button>
              )}
            </div>
          </div>

          <textarea
            rows={7}
            value={
              activeTab === "whatsapp"
                ? whatsappMsg
                : activeTab === "telegram"
                ? telegramMsg
                : activeTab === "step1"
                ? step1
                : activeTab === "step2"
                ? step2
                : activeTab === "step3"
                ? step3
                : activeTab === "linkedin"
                ? linkedinDm
                : socialReply
            }
            onChange={(e) => {
              const val = e.target.value;
              if (activeTab === "whatsapp") setWhatsappMsg(val);
              else if (activeTab === "telegram") setTelegramMsg(val);
              else if (activeTab === "step1") setStep1(val);
              else if (activeTab === "step2") setStep2(val);
              else if (activeTab === "step3") setStep3(val);
              else if (activeTab === "linkedin") setLinkedinDm(val);
              else setSocialReply(val);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 font-sans leading-relaxed focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>

        {/* Feedback alert banner */}
        {sendResult && (
          <div
            className={`p-2.5 rounded-lg text-xs font-medium ${
              sendResult.startsWith("✓")
                ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/60"
                : "bg-rose-950/70 text-rose-400 border border-rose-800/60"
            }`}
          >
            {sendResult}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="p-4 bg-slate-950/60 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Save Edits
          </button>
          <button
            onClick={handleApprove}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-950 hover:bg-emerald-900 text-emerald-400 border border-emerald-800 transition-colors"
          >
            Approve Sequence
          </button>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick WhatsApp broadcast trigger */}
          <button
            onClick={handleOpenWhatsApp}
            className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-slate-950 transition-colors flex items-center gap-1.5"
          >
            <MessageCircle className="w-3.5 h-3.5" />
            <span>Broadcast to WhatsApp</span>
          </button>

          {/* Simulate reply test */}
          <button
            onClick={() => setIsReplyModalOpen(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors flex items-center gap-1.5"
            title="Simulate inbound prospect reply to test self-learning loop"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Test Feedback Loop</span>
          </button>

          {/* Dry-run dispatch */}
          <button
            disabled={isSending}
            onClick={() => handleDispatch(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-900/60 hover:bg-blue-800/80 text-blue-300 border border-blue-700/60 transition-colors flex items-center gap-1.5"
          >
            <Play className="w-3 h-3" />
            <span>Send (Dry-Run)</span>
          </button>

          {/* Live dispatch */}
          <button
            disabled={isSending}
            onClick={() => handleDispatch(false)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <Send className="w-3 h-3" />
            <span>Send Live</span>
          </button>
        </div>
      </div>

      {/* Reply test modal */}
      {isReplyModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="font-bold text-slate-100 text-sm mb-1">
              Simulate Inbound Prospect Reply
            </h3>
            <p className="text-xs text-slate-400 mb-3">
              Tests the sentiment classifier and dynamic strategy weight adjustment.
            </p>

            <textarea
              rows={3}
              placeholder="e.g. 'Sounds interesting, can you send over pricing or a demo?' or 'Unsubscribe please'"
              value={simulatedReply}
              onChange={(e) => setSimulatedReply(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 mb-3 focus:outline-none focus:border-emerald-500"
            />

            {replyResult && (
              <div className="mb-3 p-3 rounded bg-slate-950 border border-slate-800 text-xs space-y-1">
                <div>
                  <span className="text-slate-500">Sentiment: </span>
                  <span className="font-bold uppercase text-emerald-400">{replyResult.sentiment}</span>
                </div>
                {replyResult.new_strategy_weight && (
                  <div>
                    <span className="text-slate-500">New Strategy Weight: </span>
                    <span className="font-mono text-emerald-400 font-bold">{replyResult.new_strategy_weight}x</span>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setIsReplyModalOpen(false);
                  setReplyResult(null);
                }}
                className="px-3 py-1.5 rounded text-xs text-slate-400 hover:bg-slate-800"
              >
                Close
              </button>
              <button
                onClick={handleSimulateReply}
                className="px-3.5 py-1.5 rounded text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                Classify & Re-weight
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
