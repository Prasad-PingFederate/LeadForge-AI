"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Target,
  Zap,
  Globe,
  ShoppingBag,
  Briefcase,
  ExternalLink,
  Flame,
  MessageCircle,
} from "lucide-react";
import { createCampaign, fetchLiveDeals } from "@/lib/api";

export default function Launchpad() {
  const router = useRouter();
  const [mode, setMode] = useState<"b2b" | "b2c_deals">("b2c_deals");
  const [targetUrl, setTargetUrl] = useState("");
  const [description, setDescription] = useState("");
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [liveDeals, setLiveDeals] = useState<any[]>([]);

  useEffect(() => {
    if (mode === "b2c_deals" && liveDeals.length === 0) {
      fetchLiveDeals({ limit: 4 })
        .then((res) => {
          if (res.deals && res.deals.length > 0) {
            setLiveDeals(res.deals);
          }
        })
        .catch(() => {});
    }
  }, [mode, liveDeals.length]);

  const setPresetDeal = (url: string, presetName: string, desc: string) => {
    setMode("b2c_deals");
    setTargetUrl(url);
    setName(presetName);
    setDescription(desc);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUrl.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const camp = await createCampaign({
        target_url: targetUrl.trim(),
        name: name.trim() || undefined,
        campaign_type: mode,
        description: description.trim() || undefined,
      });

      router.push(`/campaigns/${camp.id}/strategy`);
    } catch (err: any) {
      setError(err.message || "Failed to initialize pipeline");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-center px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-3xl mx-auto w-full">
        {/* Hero Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-xs font-semibold text-emerald-400 mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Multi-Agent Sales & Deal Promotion Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-black text-slate-100 tracking-tight leading-tight">
            Autonomous Pipeline for <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              {mode === "b2c_deals" ? "High-Converting B2C Deals" : "Verified B2B Sales Leads"}
            </span>
          </h1>

          <p className="mt-3 text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
            {mode === "b2c_deals"
              ? "Promote Amazon India & BharatBazaro deals. Discovers deal intent on Reddit & Telegram and drafts 1-click WhatsApp broadcasts with tag=dammaiprasad-21."
              : "Autonomous ICP profiling, real competitor gap extraction, zero-hallucination lead discovery, live DNS MX verification, and safe multi-step outreach."}
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex p-1 rounded-xl bg-slate-900 border border-slate-800">
            <button
              type="button"
              onClick={() => {
                setMode("b2c_deals");
                if (!targetUrl || targetUrl.includes("leadforge")) {
                  setTargetUrl("https://www.amazon.in/dp/B09W2GFM7Y");
                  setName("Pigeon 1.8L Electric Kettle Drop");
                  setDescription("Home & Kitchen impulse deal under ₹599 (60% off, high 9% commission)");
                }
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                mode === "b2c_deals"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Flame className="w-4 h-4 text-amber-300" />
              <span>B2C Deals Mode (BharatBazaro & Amazon)</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setMode("b2b");
                if (targetUrl.includes("amazon") || targetUrl.includes("bharatbazaro")) {
                  setTargetUrl("https://resend.com");
                  setName("Resend Developer Outreach");
                  setDescription("Modern developer email API vs SendGrid legacy bloat");
                }
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                mode === "b2b"
                  ? "bg-blue-600 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Briefcase className="w-4 h-4" />
              <span>B2B Enterprise Lead Gen</span>
            </button>
          </div>
        </div>

        {/* Launchpad Form Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative">
          {mode === "b2c_deals" && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/50 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <ShoppingBag className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-200 font-medium">Affiliate Tag:</span>
                <span className="font-mono font-bold text-emerald-400 bg-slate-950 px-2 py-0.5 rounded border border-emerald-800/40">
                  dammaiprasad-21
                </span>
              </div>
              <span className="text-[11px] text-slate-400">
                Prioritizes 7%–9% Home & Kitchen, Appliances & Beauty steals
              </span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-1.5 flex items-center justify-between">
                <span>{mode === "b2c_deals" ? "Amazon India / BharatBazaro Deal URL" : "Product Website URL"}</span>
                <span className="text-slate-500 font-mono text-[11px] normal-case">
                  {mode === "b2c_deals" ? "e.g. amazon.in/dp/B09W2GFM7Y" : "e.g. resend.com or stripe.com"}
                </span>
              </label>
              <div className="relative">
                <Globe className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
                <input
                  type="text"
                  required
                  placeholder={mode === "b2c_deals" ? "https://www.amazon.in/dp/B09W2GFM7Y" : "https://yourproduct.com"}
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-1.5">
                  Campaign Title
                </label>
                <input
                  type="text"
                  placeholder={mode === "b2c_deals" ? "e.g. Electric Kettle Price Drop Under ₹599" : "e.g. Q4 Competitor Displacement"}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-1.5">
                  Category / Focus Notes
                </label>
                <input
                  type="text"
                  placeholder={mode === "b2c_deals" ? "e.g. Home & Kitchen impulse steal, 60% off" : "e.g. Developer tools, eliminate per-seat costs"}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Quick 1-Click Preset Deals (B2C Mode) */}
            {mode === "b2c_deals" && (
              <div className="pt-2">
                <span className="text-[11px] font-semibold text-slate-400 block mb-1.5 uppercase tracking-wider">
                  {liveDeals.length > 0 ? "Live Deals from BharatBazaro Feed:" : "Quick High-Commission Preset Deals:"}
                </span>
                <div className="flex flex-wrap gap-2 text-xs">
                  {liveDeals.length > 0 ? (
                    liveDeals.map((deal) => (
                      <button
                        key={deal.asin}
                        type="button"
                        onClick={() =>
                          setPresetDeal(
                            `https://www.amazon.in/dp/${deal.asin}`,
                            deal.title.slice(0, 40),
                            `${deal.category} deal at ₹${deal.effective_price} (${deal.discount_pct}% off, ${deal.commission_info?.commission_rate_percent || 9}% comm)`
                          )
                        }
                        className="px-2.5 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-200 border border-emerald-800/60 transition-colors flex items-center gap-1.5"
                      >
                        <span className="text-emerald-400 font-bold">₹{deal.effective_price}</span>
                        <span className="text-slate-300 truncate max-w-[140px]">{deal.title.split(" ")[0]} {deal.title.split(" ")[1]}</span>
                        <span className="text-[10px] bg-emerald-950 text-emerald-300 px-1 py-0.5 rounded border border-emerald-800/40">
                          {deal.discount_pct}% OFF
                        </span>
                      </button>
                    ))
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() =>
                          setPresetDeal(
                            "https://www.amazon.in/dp/B09W2GFM7Y",
                            "Pigeon 1.8L Electric Kettle Drop",
                            "Home & Kitchen 9% commission, deal price ₹599 (60% off)"
                          )
                        }
                        className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
                      >
                        🫖 Electric Kettle (₹599)
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          setPresetDeal(
                            "https://www.amazon.in/dp/B07VXYZ123",
                            "Philips Digital Air Fryer 4.1L Drop",
                            "Small Appliances 7% commission, ₹4,999 deal"
                          )
                        }
                        className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
                      >
                        🍟 Air Fryer (₹4,999)
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          setPresetDeal(
                            "https://bharatbazaro.com",
                            "BharatBazaro Live Impulse Steals",
                            "Top-converting Home & Kitchen verified price drops"
                          )
                        }
                        className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
                      >
                        🇮🇳 BharatBazaro Live Feed
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-xs text-rose-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !targetUrl.trim()}
              className="w-full mt-3 py-3.5 px-6 rounded-xl font-bold text-sm bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition-all cursor-pointer"
            >
              {isLoading ? (
                <span>Spawning Autonomous Agent Pipeline...</span>
              ) : (
                <>
                  <span>
                    {mode === "b2c_deals"
                      ? "Launch Deal Promotion & WhatsApp/Telegram Pipeline"
                      : "Launch Autonomous Lead Generation"}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800/40 flex items-center justify-center text-emerald-400 shrink-0">
              <MessageCircle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200">WhatsApp-First Copy</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                Direct WhatsApp VIP Broadcasts with bold emoji headings, rupee savings calculations, and tag=dammaiprasad-21.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-950/60 border border-blue-800/40 flex items-center justify-center text-blue-400 shrink-0">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200">Indian Intent Communities</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                Hunts real buyer discussions across r/dealsforindia, r/IndianGaming, and public Telegram loot channels.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-800/40 flex items-center justify-center text-purple-400 shrink-0">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200">Zero-Key / Free LLM Path</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                Works out-of-the-box with Gemini free tier, Groq, or offline heuristic engine without requiring paid credits.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
