"use client";

import { useEffect, useState, use } from "react";
import CampaignNav from "@/components/CampaignNav";
import LeadTable from "@/components/LeadTable";
import { fetchCampaign, fetchLeads } from "@/lib/api";
import { CampaignDetail, Lead } from "@/types";
import { Loader2, Users } from "lucide-react";

export default function CampaignLeadsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const campaignId = resolvedParams.id;

  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const [c, l] = await Promise.all([
          fetchCampaign(campaignId),
          fetchLeads(campaignId),
        ]);
        setCampaign(c);
        setLeads(l);
      } catch (err: any) {
        setError(err.message || "Failed to load leads");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [campaignId]);

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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Clay-Style Verified Lead Intelligence Grid
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Every lead includes live intent proof, transparent 0-100 scoring, and waterfall email verification.
            </p>
          </div>
        </div>

        <LeadTable campaignId={campaign.id} initialLeads={leads} />
      </div>
    </div>
  );
}
