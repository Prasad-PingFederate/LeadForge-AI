"use client";

import { Strategy } from "@/types";
import { Compass, Mail, MessageSquare, Linkedin, CheckCircle2 } from "lucide-react";

export default function StrategyCard({ strategy, index }: { strategy: Strategy; index: number }) {
  const getChannelBadge = (ch: string) => {
    switch (ch.toLowerCase()) {
      case "email":
        return { label: "Cold Email", icon: Mail, color: "text-blue-400 bg-blue-950/40 border-blue-800/60" };
      case "reddit":
      case "social":
        return { label: "Social Intent", icon: MessageSquare, color: "text-orange-400 bg-orange-950/40 border-orange-800/60" };
      case "linkedin":
        return { label: "LinkedIn DM", icon: Linkedin, color: "text-sky-400 bg-sky-950/40 border-sky-800/60" };
      default:
        return { label: ch, icon: Compass, color: "text-emerald-400 bg-emerald-950/40 border-emerald-800/60" };
    }
  };

  const channelInfo = getChannelBadge(strategy.channel || "email");
  const ChannelIcon = channelInfo.icon;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-xs font-mono font-bold text-slate-500 uppercase">Strategy {index + 1}</span>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${channelInfo.color}`}>
            <ChannelIcon className="w-3 h-3" />
            <span>{channelInfo.label}</span>
          </span>
        </div>

        <h3 className="font-bold text-slate-100 text-base mb-2">{strategy.title}</h3>
        <p className="text-xs text-slate-300 leading-relaxed mb-4">{strategy.angle}</p>
      </div>

      <div>
        <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800 mb-3">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
            Autonomous Search Queries
          </span>
          <div className="space-y-1">
            {strategy.target_queries && strategy.target_queries.map((q, i) => (
              <div key={i} className="text-xs font-mono text-emerald-300 bg-slate-900 px-2 py-1 rounded border border-slate-800 truncate">
                {q}
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
          <span className="text-slate-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Self-Learning Weight</span>
          </span>
          <span className="font-mono font-bold text-emerald-400">
            {Number(strategy.conversion_weight || 1.0).toFixed(2)}x
          </span>
        </div>
      </div>
    </div>
  );
}
