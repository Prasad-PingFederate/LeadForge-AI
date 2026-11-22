"use client";

import { useEffect, useState, use } from "react";
import CampaignNav from "@/components/CampaignNav";
import OutreachCard from "@/components/OutreachCard";
import { fetchCampaign, fetchOutreach } from "@/lib/api";
import { CampaignDetail, OutreachMessage } from "@/types";
import { Send, Loader2, Sparkles, Filter, CheckCircle2 } from "lucide-react";

export default function CampaignOutreachPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const campaignId = resolvedParams.id;

  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [messages, setMessages] = useState<OutreachMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const loadData = async () => {
    try {
      const [c, m] = await Promise.all([
        fetchCampaign(campaignId),
        fetchOutreach(campaignId),
      ]);
      setCampaign(c);
      setMessages(m);
    } catch (err: any) {
      setError(err.message || "Failed to load outreach sequences");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [campaignId]);

  const filteredMessages = messages.filter((m) => {
    if (statusFilter === "all") return true;
    return m.status === statusFilter;
  });

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="p-8 text-center text-rose-400">
        <p>{error || "Campaign not found"}</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <CampaignNav
        campaignId={campaign.id}
        campaignName={campaign.name}
        targetUrl={campaign.target_url}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Send className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Outreach Sequences & Human-Approval Queue
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Review signal-personalized 3-step emails, LinkedIn DMs, and social replies before safe dispatch.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Filter Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Sequences ({messages.length})</option>
              <option value="draft">Drafts</option>
              <option value="approved">Approved</option>
              <option value="sent">Sent (Live)</option>
              <option value="sent_dry_run">Dry-Run Sent</option>
            </select>
          </div>
        </div>

        {filteredMessages.length === 0 ? (
          <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-500 text-xs">
            No outreach drafts found matching this filter.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredMessages.map((msg) => (
              <OutreachCard key={msg.id} message={msg} onRefresh={loadData} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
