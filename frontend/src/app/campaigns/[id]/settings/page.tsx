"use client";

import { useEffect, useState, use } from "react";
import CampaignNav from "@/components/CampaignNav";
import { fetchCampaign, fetchSuppression, addSuppression } from "@/lib/api";
import { CampaignDetail } from "@/types";
import { ShieldCheck, Ban, Plus, Loader2, CheckCircle2, Lock } from "lucide-react";

export default function CampaignSettingsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const campaignId = resolvedParams.id;

  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [suppressionList, setSuppressionList] = useState<Array<{ id: string; domain?: string; email?: string; reason: string }>>([]);
  const [loading, setLoading] = useState(true);

  // Add suppression form state
  const [blockDomain, setBlockDomain] = useState("");
  const [blockEmail, setBlockEmail] = useState("");
  const [blockReason, setBlockReason] = useState("manual_optout");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [c, s] = await Promise.all([
        fetchCampaign(campaignId),
        fetchSuppression(),
      ]);
      setCampaign(c);
      setSuppressionList(s);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [campaignId]);

  const handleAddSuppression = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!blockDomain && !blockEmail) return;

    setSubmitting(true);
    setMsg(null);
    try {
      await addSuppression({
        domain: blockDomain.trim() || undefined,
        email: blockEmail.trim() || undefined,
        reason: blockReason,
      });
      setMsg("✓ Successfully added to global suppression list!");
      setBlockDomain("");
      setBlockEmail("");
      loadData();
      setTimeout(() => setMsg(null), 3000);
    } catch (err: any) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <CampaignNav
        campaignId={campaign?.id || campaignId}
        campaignName={campaign?.name}
        targetUrl={campaign?.target_url}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-slate-100">
              Deliverability, Compliance & Safety Gates
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure global suppression lists, daily inbox send quotas, and automated spam compliance.
          </p>
        </div>

        {/* Global Compliance Quotas */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Daily Send Quota Cap
            </span>
            <span className="font-mono text-2xl font-bold text-slate-100">50 emails / day</span>
            <p className="text-xs text-slate-400 mt-2">
              Protects domain reputation and prevents blacklisting with automatic hard-stop.
            </p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Randomized Send Throttle
            </span>
            <span className="font-mono text-2xl font-bold text-emerald-400">45s – 180s</span>
            <p className="text-xs text-slate-400 mt-2">
              Human-like randomized delivery intervals between outgoing dispatches.
            </p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Tamper-Proof Unsubscribe
            </span>
            <span className="inline-flex items-center gap-1.5 font-mono text-base font-bold text-emerald-400 mt-1">
              <Lock className="w-4 h-4" />
              <span>HMAC-SHA256 Token</span>
            </span>
            <p className="text-xs text-slate-400 mt-2">
              Appended to every cold email with automatic 1-click suppression update.
            </p>
          </div>
        </div>

        {/* Suppression Management Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Add to suppression list form */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Ban className="w-4 h-4 text-rose-400" />
              <h3 className="font-bold text-slate-100 text-sm">Add Domain or Email to Blocklist</h3>
            </div>

            <form onSubmit={handleAddSuppression} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Company Domain</label>
                <input
                  type="text"
                  placeholder="e.g. competitorcorp.com"
                  value={blockDomain}
                  onChange={(e) => setBlockDomain(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. optout@company.com"
                  value={blockEmail}
                  onChange={(e) => setBlockEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Reason</label>
                <select
                  value={blockReason}
                  onChange={(e) => setBlockReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="manual_optout">Manual Opt-Out</option>
                  <option value="competitor_firm">Competitor Firm</option>
                  <option value="existing_customer">Existing Customer</option>
                  <option value="do_not_contact">Do Not Contact</option>
                </select>
              </div>

              {msg && (
                <div
                  className={`p-2.5 rounded-lg text-xs font-medium ${
                    msg.startsWith("✓")
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      : "bg-rose-950 text-rose-400 border border-rose-800"
                  }`}
                >
                  {msg}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting || (!blockDomain && !blockEmail)}
                className="w-full py-2.5 rounded-lg text-xs font-bold bg-rose-900/60 hover:bg-rose-800/80 disabled:opacity-50 text-rose-200 border border-rose-700/60 transition-colors flex items-center justify-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add to Global Blocklist</span>
              </button>
            </form>
          </div>

          {/* Current suppression entries */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-slate-100 text-sm">Active Suppressed Entities</h3>
                <span className="text-xs text-slate-500 font-mono">{suppressionList.length} blocked</span>
              </div>

              {suppressionList.length === 0 ? (
                <div className="p-8 text-center bg-slate-950/60 border border-slate-800/60 rounded-lg text-slate-500 text-xs">
                  No active suppressions yet.
                </div>
              ) : (
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {suppressionList.map((item) => (
                    <div
                      key={item.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-mono text-slate-200 block">
                          {item.email || item.domain}
                        </span>
                        <span className="text-[10px] text-slate-500 capitalize">
                          {item.reason.replace("_", " ")}
                        </span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-900">
                        Suppressed
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-800/80 mt-4 text-[11px] text-slate-500">
              <span>Automatic hard-block prevents accidental outreach to these domains/emails.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
