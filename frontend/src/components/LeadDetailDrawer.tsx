"use client";

import { Lead, ScoreBreakdown } from "@/types";
import { X, ExternalLink, ShieldCheck, AlertCircle, CheckCircle2, Building, Mail, Linkedin } from "lucide-react";

interface LeadDetailDrawerProps {
  lead: Lead | null;
  onClose: () => void;
}

export default function LeadDetailDrawer({ lead, onClose }: LeadDetailDrawerProps) {
  if (!lead) return null;

  let breakdown: ScoreBreakdown | null = null;
  if (lead.score_breakdown_json) {
    try {
      breakdown = JSON.parse(lead.score_breakdown_json);
    } catch (e) {
      // ignore
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400 border-emerald-500/40 bg-emerald-950/40";
    if (score >= 60) return "text-amber-400 border-amber-500/40 bg-amber-950/40";
    return "text-slate-400 border-slate-700 bg-slate-900";
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto flex flex-col justify-between p-6 shadow-2xl">
        <div>
          {/* Header */}
          <div className="flex items-start justify-between pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <Building className="w-4 h-4 text-emerald-400" />
                <h2 className="text-xl font-bold text-slate-100">{lead.company_name}</h2>
              </div>
              <span className="text-xs font-mono text-slate-400 mt-0.5 block">{lead.domain}</span>
            </div>

            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Lead Score Card */}
          <div className="my-5 p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-0.5">
                Lead Conversion Score
              </span>
              <span className="text-xs text-slate-500">
                Calculated across ICP Fit, Live Buying Intent, and DNS MX Verification
              </span>
            </div>
            <div className={`px-4 py-2 rounded-xl border font-mono font-bold text-2xl ${getScoreColor(lead.overall_score)}`}>
              {lead.overall_score}<span className="text-xs font-normal opacity-60">/100</span>
            </div>
          </div>

          {/* Evidence String: "Why this lead" */}
          {lead.why_this_lead && (
            <div className="mb-5 p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Verifiable Evidence ("Why This Lead")</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {lead.why_this_lead}
              </p>
            </div>
          )}

          {/* Score Breakdown Bars */}
          {breakdown && (
            <div className="mb-5 space-y-3 p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Transparent Score Breakdown
              </h3>

              {/* ICP Fit */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>ICP Fit (Role + Industry Match)</span>
                  <span className="font-mono font-bold text-emerald-400">{breakdown.icp_fit.score} / 40 pts</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full"
                    style={{ width: `${(breakdown.icp_fit.score / 40) * 100}%` }}
                  />
                </div>
              </div>

              {/* Intent Freshness */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Live Intent Freshness ({breakdown.intent_freshness.platform})</span>
                  <span className="font-mono font-bold text-blue-400">{breakdown.intent_freshness.score} / 35 pts</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-500 h-full rounded-full"
                    style={{ width: `${(breakdown.intent_freshness.score / 35) * 100}%` }}
                  />
                </div>
              </div>

              {/* Contact Verification */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Email Verification ({breakdown.contact_verification.email_status})</span>
                  <span className="font-mono font-bold text-amber-400">{breakdown.contact_verification.score} / 25 pts</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full"
                    style={{ width: `${(breakdown.contact_verification.score / 25) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Contact Details & Verification */}
          <div className="mb-5 p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Discovered Contact & Channel
            </h3>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block mb-0.5">Contact Name & Role</span>
                <span className="font-medium text-slate-200">
                  {lead.contact_name || "Decision Maker"} {lead.contact_role ? `(${lead.contact_role})` : ""}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block mb-0.5">Email Address</span>
                <span className="font-mono text-slate-200 truncate block">
                  {lead.contact_email || "Not discovered"}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block mb-0.5">Verification Status</span>
                <span className={`inline-flex items-center gap-1 font-semibold ${
                  lead.email_status === "verified" ? "text-emerald-400" : "text-amber-400"
                }`}>
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span className="capitalize">{lead.email_status}</span>
                </span>
              </div>

              <div>
                <span className="text-slate-500 block mb-0.5">Discovered Intent Source</span>
                <span className="capitalize font-medium text-slate-200">
                  {lead.intent_platform}
                </span>
              </div>
            </div>
          </div>

          {/* Proof URL / Source Snippet */}
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Verifiable Proof Source
              </span>
              <a
                href={lead.intent_source_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors font-medium"
              >
                <span>View Original Proof</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {lead.intent_snippet && (
              <p className="text-xs text-slate-400 bg-slate-900 p-3 rounded-lg border border-slate-800 italic">
                "{lead.intent_snippet}"
              </p>
            )}
          </div>
        </div>

        {/* Footer actions */}
        <div className="pt-6 border-t border-slate-800 mt-6 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
