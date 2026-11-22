"use client";

import { useState, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from "@tanstack/react-table";
import { Lead } from "@/types";
import {
  Search,
  Download,
  Send,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Eye,
  SlidersHorizontal,
  ChevronDown,
  ArrowUpDown,
} from "lucide-react";
import LeadDetailDrawer from "./LeadDetailDrawer";
import { getExportCsvUrl, pushWebhook } from "@/lib/api";

interface LeadTableProps {
  campaignId: string;
  initialLeads: Lead[];
}

export default function LeadTable({ campaignId, initialLeads }: LeadTableProps) {
  const [data, setData] = useState<Lead[]>(initialLeads);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "overall_score", desc: true },
  ]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(false);
  const [minScore, setMinScore] = useState<number>(0);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // Webhook Push modal state
  const [isWebhookModalOpen, setIsWebhookModalOpen] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookMinScore, setWebhookMinScore] = useState(60);
  const [webhookSubmitting, setWebhookSubmitting] = useState(false);
  const [webhookMsg, setWebhookMsg] = useState<string | null>(null);

  // Filtered dataset
  const filteredData = useMemo(() => {
    return data.filter((lead) => {
      if (verifiedOnly && lead.email_status !== "verified") return false;
      if (minScore > 0 && lead.overall_score < minScore) return false;
      if (platformFilter !== "all" && lead.intent_platform !== platformFilter) return false;
      return true;
    });
  }, [data, verifiedOnly, minScore, platformFilter]);

  const columns = useMemo<ColumnDef<Lead>[]>(
    () => [
      {
        accessorKey: "overall_score",
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-xs text-slate-400 hover:text-slate-200"
          >
            <span>Score</span>
            <ArrowUpDown className="w-3 h-3" />
          </button>
        ),
        cell: ({ getValue }) => {
          const score = Number(getValue());
          const badgeClass =
            score >= 80
              ? "text-emerald-400 bg-emerald-950/60 border-emerald-800/60"
              : score >= 60
              ? "text-amber-400 bg-amber-950/60 border-amber-800/60"
              : "text-slate-400 bg-slate-900 border-slate-800";
          return (
            <span className={`inline-flex items-center justify-center font-mono font-bold px-2 py-0.5 text-xs rounded border ${badgeClass}`}>
              {score}
            </span>
          );
        },
      },
      {
        accessorKey: "company_name",
        header: "Company & Domain",
        cell: ({ row }) => (
          <div>
            <div className="font-semibold text-slate-200 text-xs">{row.original.company_name}</div>
            <span className="text-[11px] font-mono text-slate-500">{row.original.domain}</span>
          </div>
        ),
      },
      {
        accessorKey: "contact_name",
        header: "Contact",
        cell: ({ row }) => (
          <div>
            <div className="font-medium text-slate-200 text-xs">
              {row.original.contact_name || "Decision Maker"}
            </div>
            {row.original.contact_role && (
              <span className="text-[11px] text-slate-400 block truncate max-w-[180px]">
                {row.original.contact_role}
              </span>
            )}
          </div>
        ),
      },
      {
        accessorKey: "contact_email",
        header: "Email & Verification",
        cell: ({ row }) => {
          const isVerified = row.original.email_status === "verified";
          return (
            <div>
              <span className="font-mono text-xs text-slate-300 block truncate max-w-[190px]">
                {row.original.contact_email || "Not found"}
              </span>
              <span
                className={`inline-flex items-center gap-1 text-[10px] font-semibold mt-0.5 ${
                  isVerified ? "text-emerald-400" : "text-amber-400"
                }`}
              >
                <ShieldCheck className="w-3 h-3" />
                <span className="capitalize">{row.original.email_status}</span>
              </span>
            </div>
          );
        },
      },
      {
        accessorKey: "intent_platform",
        header: "Intent Platform",
        cell: ({ getValue }) => (
          <span className="inline-flex px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800/80 text-slate-300 border border-slate-700/60 capitalize">
            {String(getValue())}
          </span>
        ),
      },
      {
        accessorKey: "why_this_lead",
        header: "Why This Lead",
        cell: ({ getValue }) => (
          <p className="text-xs text-slate-300 line-clamp-2 max-w-[260px] leading-relaxed">
            {String(getValue() || "Discovered via high-fit strategy search")}
          </p>
        ),
      },
      {
        id: "actions",
        header: "Proof / Detail",
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedLead(row.original)}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-emerald-400 transition-colors"
              title="Inspect Evidence & Score Breakdown"
            >
              <Eye className="w-4 h-4" />
            </button>
            <a
              href={row.original.intent_source_url}
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-emerald-400 transition-colors"
              title="View Original Proof Source"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        ),
      },
    ],
    []
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const handlePushWebhook = async () => {
    if (!webhookUrl) return;
    setWebhookSubmitting(true);
    setWebhookMsg(null);
    try {
      const res = await pushWebhook(campaignId, webhookUrl, webhookMinScore);
      setWebhookMsg(`✓ Successfully pushed ${res.pushed_count} leads to webhook!`);
      setTimeout(() => {
        setIsWebhookModalOpen(false);
        setWebhookMsg(null);
      }, 2000);
    } catch (e: any) {
      setWebhookMsg(`Error: ${e.message}`);
    } finally {
      setWebhookSubmitting(false);
    }
  };

  return (
    <div>
      {/* Action Controls & Filters Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search company, contact, or domain..."
            value={globalFilter ?? ""}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Platform selector */}
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500 capitalize"
          >
            <option value="all">All Intent Sources</option>
            <option value="hackernews">Hacker News</option>
            <option value="reddit">Reddit</option>
            <option value="b2b_search">B2B Search</option>
            <option value="website_auditor">Website Audit</option>
          </select>

          {/* Verified email toggle */}
          <button
            onClick={() => setVerifiedOnly(!verifiedOnly)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              verifiedOnly
                ? "bg-emerald-950/60 text-emerald-400 border-emerald-600/60"
                : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verified Email Only</span>
          </button>

          {/* Min Score Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Min Score:</span>
            <input
              type="number"
              min="0"
              max="100"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-14 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Export CSV Button */}
          <a
            href={getExportCsvUrl(campaignId, minScore > 0 ? minScore : undefined, verifiedOnly)}
            download
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>

          {/* Push Webhook Button */}
          <button
            onClick={() => setIsWebhookModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Push Webhook</span>
          </button>
        </div>
      </div>

      {/* Clay-style Data Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 border-b border-slate-800 uppercase text-[11px] font-semibold text-slate-400 tracking-wider">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="px-4 py-3">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-500">
                    No leads matching criteria found.
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="hover:bg-slate-850/50 transition-colors cursor-pointer"
                    onClick={() => setSelectedLead(row.original)}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3" onClick={(e) => {
                        // Avoid triggering row click if clicking direct action button
                        if ((e.target as HTMLElement).closest("button, a")) {
                          e.stopPropagation();
                        }
                      }}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer */}
        <div className="px-4 py-2.5 bg-slate-950/40 border-t border-slate-800 text-xs text-slate-500 flex justify-between items-center">
          <span>Showing {filteredData.length} leads</span>
          <span className="font-mono text-[11px]">Zero-Hallucination Verified</span>
        </div>
      </div>

      {/* Slide-out detail drawer */}
      <LeadDetailDrawer lead={selectedLead} onClose={() => setSelectedLead(null)} />

      {/* Webhook Modal */}
      {isWebhookModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="font-bold text-slate-100 text-base mb-1">Push Leads to Webhook / CRM</h3>
            <p className="text-xs text-slate-400 mb-4">
              Instantly push verified leads to Make, Zapier, n8n, or your internal API endpoint.
            </p>

            <div className="space-y-3 mb-5">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Webhook URL</label>
                <input
                  type="url"
                  placeholder="https://hooks.zapier.com/hooks/catch/..."
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Minimum Score Gate</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={webhookMinScore}
                  onChange={(e) => setWebhookMinScore(Number(e.target.value))}
                  className="w-24 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>

              {webhookMsg && (
                <div className={`p-2.5 rounded text-xs font-medium ${
                  webhookMsg.startsWith("✓") ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-rose-950 text-rose-400 border border-rose-800"
                }`}>
                  {webhookMsg}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setIsWebhookModalOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={webhookSubmitting || !webhookUrl}
                onClick={handlePushWebhook}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white transition-colors"
              >
                {webhookSubmitting ? "Pushing..." : "Dispatch Leads"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
