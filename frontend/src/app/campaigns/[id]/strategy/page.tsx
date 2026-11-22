"use client";

import { useEffect, useState, use } from "react";
import CampaignNav from "@/components/CampaignNav";
import BattlecardCard from "@/components/BattlecardCard";
import StrategyCard from "@/components/StrategyCard";
import ProgressStream from "@/components/ProgressStream";
import { fetchCampaign } from "@/lib/api";
import { CampaignDetail } from "@/types";
import { Swords, Compass, Briefcase, Target, Loader2, Sparkles } from "lucide-react";

export default function CampaignStrategyPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const campaignId = resolvedParams.id;

  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const data = await fetchCampaign(campaignId);
      setCampaign(data);
    } catch (err: any) {
      setError(err.message || "Failed to load campaign data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
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

  const icp = campaign.icp_data;

  return (
    <div className="flex-1 flex flex-col">
      <CampaignNav
        campaignId={campaign.id}
        campaignName={campaign.name}
        targetUrl={campaign.target_url}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">
        {/* Live SSE Stream Widget */}
        <ProgressStream campaignId={campaign.id} onCompleted={loadData} />

        {/* B2C Deal Mode Highlight Box */}
        {(campaign.campaign_type === "b2c_deals" || icp?.deal_metadata) && (
          <div className="bg-gradient-to-r from-emerald-950/60 via-slate-900 to-slate-900 border border-emerald-800/60 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950 px-2.5 py-0.5 rounded-full border border-emerald-800/80">
                  🔥 BharatBazaro Deal Campaign Active
                </span>
                <span className="font-mono text-xs text-amber-300 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
                  tag=dammaiprasad-21
                </span>
              </div>
              <h3 className="font-bold text-slate-100 text-base mt-1">{icp?.product_name || "Live Deal Item"}</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Targeting high-intent Indian buyer communities on WhatsApp VIP, Telegram & r/dealsforindia.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4 bg-slate-950/80 p-3 rounded-xl border border-slate-800 font-mono text-xs">
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">Comm. Rate</span>
                <span className="font-bold text-emerald-400 text-sm">
                  {icp?.deal_metadata?.commission_rate_percent || 9.0}%
                </span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">Est. Comm. / Sale</span>
                <span className="font-bold text-emerald-300 text-sm">
                  ₹{icp?.deal_metadata?.estimated_commission_rupees?.toFixed(2) || (icp?.deal_metadata?.effective_price ? ((icp.deal_metadata.effective_price * (icp.deal_metadata.commission_rate_percent || 9)) / 100).toFixed(2) : "53.91")}
                </span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">Sales to ₹10L</span>
                <span className="font-bold text-amber-300 text-sm">
                  {Math.ceil(1000000 / (icp?.deal_metadata?.estimated_commission_rupees || 53.91)).toLocaleString("en-IN")}
                </span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">Target ASIN</span>
                <span className="font-bold text-slate-200 text-sm">
                  {icp?.deal_metadata?.asin || "B09W2GFM7Y"}
                </span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">Sales Standard</span>
                <span className="font-bold text-emerald-400 text-xs px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 inline-block mt-0.5">
                  🟢 PROMOTE
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Structured ICP Profile Section */}
        {icp && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Ideal Customer Profile (ICP) Analysis
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold block mb-1">
                  Product & Category
                </span>
                <p className="text-sm font-semibold text-slate-200">{icp.product_name}</p>
                <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                  {icp.category}
                </span>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  {icp.value_proposition}
                </p>
              </div>

              <div>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold block mb-1">
                  Target Decision-Maker Roles
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {icp.target_roles?.map((role, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/50"
                    >
                      {role}
                    </span>
                  ))}
                </div>

                <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold block mt-4 mb-1">
                  Target Industries
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {icp.target_industries?.map((ind, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700"
                    >
                      {ind}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold block mb-1">
                  Core Solved Pain Points
                </span>
                <ul className="text-xs text-slate-300 space-y-1.5 mt-1">
                  {icp.core_pain_points?.map((pt, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Competitor Battlecards */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Swords className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Competitor Intelligence & Battlecards
              </h2>
            </div>
            <span className="text-xs text-slate-400">
              {campaign.competitors?.length || 0} competitors analyzed
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {campaign.competitors && campaign.competitors.length > 0 ? (
              campaign.competitors.map((comp) => (
                <BattlecardCard key={comp.id || comp.name} competitor={comp} />
              ))
            ) : (
              <div className="col-span-full p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-500 text-xs">
                Competitor intelligence pipeline is executing...
              </div>
            )}
          </div>
        </div>

        {/* 3 Actionable GTM Strategies */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Compass className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-slate-100">
                3 Actionable Go-To-Market Lead-Gen Strategies
              </h2>
            </div>
            <span className="text-xs text-slate-400">
              Allocated dynamically across Social Intent, Competitor Displacement & Scaleup ICP
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {campaign.strategies && campaign.strategies.length > 0 ? (
              campaign.strategies.map((strat, idx) => (
                <StrategyCard key={strat.id || idx} strategy={strat} index={idx} />
              ))
            ) : (
              <div className="col-span-full p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-500 text-xs">
                Formulating GTM strategies...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
