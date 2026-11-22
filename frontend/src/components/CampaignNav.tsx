"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Users, Send, Settings as SettingsIcon, ExternalLink } from "lucide-react";

interface CampaignNavProps {
  campaignId: string;
  campaignName?: string;
  targetUrl?: string;
}

export default function CampaignNav({ campaignId, campaignName, targetUrl }: CampaignNavProps) {
  const pathname = usePathname();

  const tabs = [
    {
      name: "Strategy & Intel",
      href: `/campaigns/${campaignId}/strategy`,
      icon: Compass,
      match: pathname.endsWith("/strategy"),
    },
    {
      name: "Verified Leads Grid",
      href: `/campaigns/${campaignId}/leads`,
      icon: Users,
      match: pathname.endsWith("/leads"),
    },
    {
      name: "Outreach Approval Queue",
      href: `/campaigns/${campaignId}/outreach`,
      icon: Send,
      match: pathname.endsWith("/outreach"),
    },
    {
      name: "Compliance & Safety",
      href: `/campaigns/${campaignId}/settings`,
      icon: SettingsIcon,
      match: pathname.endsWith("/settings"),
    },
  ];

  return (
    <div className="border-b border-slate-800 bg-slate-900/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-100">{campaignName || "Campaign"}</h1>
            {targetUrl && (
              <a
                href={targetUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-emerald-400 transition-colors mt-0.5"
              >
                <span>{targetUrl}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        <nav className="flex space-x-1 sm:space-x-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = tab.match;
            return (
              <Link
                key={tab.name}
                href={tab.href}
                className={`flex items-center gap-2 py-3 px-3 border-b-2 text-sm font-medium transition-all ${
                  active
                    ? "border-emerald-500 text-emerald-400 bg-emerald-950/20"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? "text-emerald-400" : "text-slate-400"}`} />
                <span>{tab.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
