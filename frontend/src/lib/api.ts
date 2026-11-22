import { Campaign, CampaignDetail, Lead, OutreachMessage, ProgressState, RevenueSummary } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function createCampaign(data: {
  target_url: string;
  name?: string;
  campaign_type?: "b2b" | "b2c_deals";
  description?: string;
}): Promise<Campaign> {
  const res = await fetch(`${API_BASE}/campaigns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create campaign");
  }
  return res.json();
}

export async function fetchCampaign(id: string): Promise<CampaignDetail> {
  const res = await fetch(`${API_BASE}/campaigns/${id}`);
  if (!res.ok) {
    throw new Error("Failed to fetch campaign");
  }
  return res.json();
}

export async function fetchLeads(
  campaignId: string,
  filters: {
    min_score?: number;
    email_verified_only?: boolean;
    intent_platform?: string;
    search?: string;
    status?: string;
  } = {}
): Promise<Lead[]> {
  const params = new URLSearchParams();
  if (filters.min_score !== undefined) params.set("min_score", String(filters.min_score));
  if (filters.email_verified_only) params.set("email_verified_only", "true");
  if (filters.intent_platform) params.set("intent_platform", filters.intent_platform);
  if (filters.search) params.set("search", filters.search);
  if (filters.status) params.set("status", filters.status);

  const res = await fetch(`${API_BASE}/campaigns/${campaignId}/leads?${params.toString()}`);
  if (!res.ok) {
    throw new Error("Failed to fetch leads");
  }
  return res.json();
}

export function getExportCsvUrl(campaignId: string, minScore?: number, emailVerifiedOnly?: boolean): string {
  const params = new URLSearchParams();
  if (minScore !== undefined) params.set("min_score", String(minScore));
  if (emailVerifiedOnly) params.set("email_verified_only", "true");
  return `${API_BASE}/campaigns/${campaignId}/leads/export?${params.toString()}`;
}

export async function pushWebhook(
  campaignId: string,
  webhookUrl: string,
  minScore: number = 50
): Promise<{ success: boolean; pushed_count: number; message: string }> {
  const res = await fetch(`${API_BASE}/campaigns/${campaignId}/leads/webhook`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ webhook_url: webhookUrl, min_score: minScore }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to push webhook");
  }
  return res.json();
}

export async function fetchOutreach(campaignId: string, status?: string): Promise<OutreachMessage[]> {
  const params = status ? `?status=${status}` : "";
  const res = await fetch(`${API_BASE}/campaigns/${campaignId}/outreach${params}`);
  if (!res.ok) {
    throw new Error("Failed to fetch outreach sequences");
  }
  return res.json();
}

export async function updateOutreach(
  messageId: string,
  payload: {
    subject?: string;
    body_step1?: string;
    body_step2?: string;
    body_step3?: string;
    linkedin_dm?: string;
    social_reply?: string;
    whatsapp_message?: string;
    telegram_message?: string;
    deal_affiliate_url?: string;
    status?: string;
  }
): Promise<void> {
  const res = await fetch(`${API_BASE}/outreach/${messageId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error("Failed to update outreach message");
  }
}

export async function dispatchOutreach(
  messageId: string,
  dryRun: boolean = true
): Promise<{ success: boolean; mode: string; recipient?: string; error?: string }> {
  const res = await fetch(`${API_BASE}/outreach/${messageId}/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dry_run: dryRun }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to send message");
  }
  return res.json();
}

export async function postReplyFeedback(
  messageId: string,
  replyText: string
): Promise<{ sentiment: string; new_strategy_weight?: number; lead_status: string }> {
  const res = await fetch(`${API_BASE}/outreach/${messageId}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reply_text: replyText }),
  });
  if (!res.ok) {
    throw new Error("Failed to post reply classification");
  }
  return res.json();
}

export async function fetchSuppression(): Promise<Array<{ id: string; domain?: string; email?: string; reason: string }>> {
  const res = await fetch(`${API_BASE}/compliance/suppression`);
  if (!res.ok) return [];
  return res.json();
}

export async function addSuppression(data: { domain?: string; email?: string; reason?: string }): Promise<void> {
  await fetch(`${API_BASE}/compliance/suppression`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchLiveDeals(params: {
  category?: string;
  max_price?: number;
  limit?: number;
  query?: string;
} = {}): Promise<{ deals: any[]; count: number; total_available: number }> {
  const q = new URLSearchParams();
  if (params.category) q.set("category", params.category);
  if (params.max_price) q.set("max_price", String(params.max_price));
  if (params.limit) q.set("limit", String(params.limit));
  if (params.query) q.set("query", params.query);

  const res = await fetch(`${API_BASE}/deals/live?${q.toString()}`);
  if (!res.ok) {
    return { deals: [], count: 0, total_available: 0 };
  }
  return res.json();
}

export async function fetchRevenueSummary(): Promise<RevenueSummary> {
  const res = await fetch(`${API_BASE}/revenue/summary`);
  if (!res.ok) {
    throw new Error("Failed to fetch revenue summary");
  }
  return res.json();
}

export async function trackDealClick(payload: {
  asin: string;
  channel: string;
  subtag?: string;
  campaign_id?: string;
  outreach_id?: string;
}): Promise<void> {
  await fetch(`${API_BASE}/deals/click`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).catch(() => {});
}
