"use client";

import { Competitor } from "@/types";
import { Swords, ThumbsUp, AlertTriangle, Zap, ExternalLink } from "lucide-react";

export default function BattlecardCard({ competitor }: { competitor: Competitor }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <Swords className="w-4 h-4 text-amber-400" />
              <h3 className="font-bold text-slate-100 text-base">{competitor.name}</h3>
            </div>
            {competitor.domain && (
              <span className="text-xs text-slate-400 font-mono mt-0.5 block">{competitor.domain}</span>
            )}
          </div>
          {competitor.pricing_tier && (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700 whitespace-nowrap">
              {competitor.pricing_tier}
            </span>
          )}
        </div>

        {/* Strengths */}
        {competitor.strengths && competitor.strengths.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1.5">
              <ThumbsUp className="w-3 h-3" />
              <span>Competitor Moat</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1">
              {competitor.strengths.map((str, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-500 font-bold">•</span>
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Weaknesses / Complaints */}
        {competitor.weaknesses && competitor.weaknesses.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1.5">
              <AlertTriangle className="w-3 h-3" />
              <span>Real Vulnerabilities & Complaints</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1">
              {competitor.weaknesses.map((weak, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-rose-500 font-bold">•</span>
                  <span>{weak}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Displacement Angle */}
      <div className="pt-3 border-t border-slate-800/80 bg-slate-950/40 -mx-5 -mb-5 p-5 rounded-b-xl">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
          <Zap className="w-3 h-3" />
          <span>Our Displacement Angle</span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed font-medium">
          {competitor.displacement_angle || "Highlight self-serve agility and transparent usage without seat minimums."}
        </p>

        {/* Proof URLs */}
        {competitor.source_urls && competitor.source_urls.length > 0 && (
          <div className="mt-2.5 flex items-center gap-2">
            <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Proof:</span>
            {competitor.source_urls.slice(0, 2).map((url, i) => (
              <a
                key={i}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                <span>Source {i + 1}</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
