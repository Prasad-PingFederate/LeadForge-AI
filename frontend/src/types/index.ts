export interface ICPData {
  product_name: string;
  category: string;
  value_proposition: string;
  target_roles: string[];
  target_industries: string[];
  company_size_range?: string;
  core_pain_points: string[];
  intent_search_queries: string[];
  negative_keywords?: string[];
  deal_metadata?: {
    asin?: string;
    title?: string;
    brand?: string;
    category?: string;
    canonical_affiliate_url?: string;
    commission_rate_percent?: number;
    estimated_commission_rupees?: number;
    effective_price?: number;
    mrp?: number;
    discount_pct?: number;
    savings_inr?: number;
    is_impulse_sweet_spot?: boolean;
    is_zero_roi?: boolean;
    rating?: number;
    review_count?: number;
    image_url?: string;
  };
}

export interface Competitor {
  id?: string;
  campaign_id?: string;
  name: string;
  domain: string;
  strengths: string[];
  weaknesses: string[];
  pricing_tier: string;
  displacement_angle: string;
  source_urls: string[];
}

export interface Strategy {
  id: string;
  campaign_id: string;
  title: string;
  channel: string;
  angle: string;
  target_queries: string[];
  conversion_weight: number;
}

export interface ScoreBreakdown {
  icp_fit: {
    score: number;
    max: number;
    role_match: number;
    industry_match: number;
    size_match: number;
  };
  intent_freshness: {
    score: number;
    max: number;
    platform: string;
    has_switching_keyword: boolean;
  };
  contact_verification: {
    score: number;
    max: number;
    email_status: string;
  };
  total: number;
}

export interface Lead {
  id: string;
  campaign_id: string;
  strategy_id?: string;
  company_name: string;
  domain: string;
  contact_name?: string;
  contact_role?: string;
  contact_email?: string;
  email_status: "verified" | "risky" | "invalid" | "unverified";
  linkedin_url?: string;
  intent_platform: string;
  intent_source_url: string;
  intent_snippet?: string;
  fit_score: number;
  intent_score: number;
  verif_score: number;
  overall_score: number;
  score_breakdown_json?: string;
  why_this_lead?: string;
  status: "new" | "approved" | "sent" | "replied" | "unsubscribed" | "bounced";
  created_at?: string;
}

export interface OutreachMessage {
  id: string;
  lead_id: string;
  channel: string;
  subject?: string;
  body_step1?: string;
  body_step2?: string;
  body_step3?: string;
  social_reply?: string;
  linkedin_dm?: string;
  whatsapp_message?: string;
  telegram_message?: string;
  deal_affiliate_url?: string;
  subtag?: string;
  clicks_count?: number;
  status: "draft" | "approved" | "sent" | "sent_dry_run" | "replied";
  reply_sentiment?: string;
  sent_at?: string;
  company_name?: string;
  domain?: string;
  contact_name?: string;
  contact_email?: string;
  email_status?: string;
  overall_score?: number;
  why_this_lead?: string;
  intent_platform?: string;
  intent_source_url?: string;
}

export interface Campaign {
  id: string;
  name: string;
  target_url: string;
  campaign_type: "b2b" | "b2c_deals";
  description?: string;
  status: "pending" | "profiling" | "competitor_analysis" | "hunting" | "enriching" | "completed" | "failed";
  deal_metadata_json?: string;
  created_at?: string;
}

export interface CampaignDetail extends Campaign {
  icp_data?: ICPData;
  competitors: Competitor[];
  strategies: Strategy[];
  total_leads?: number;
  verified_leads?: number;
  avg_score?: number;
}

export interface ProgressState {
  campaign_id: string;
  status: string;
  progress_percent: number;
  new_logs: string[];
  all_logs: string[];
  completed: boolean;
  error?: string | null;
}

export interface PostAttribution {
  id: string;
  channel: string;
  title: string;
  asin: string;
  subtag: string;
  short_url: string;
  clicks: number;
  deal_price: number;
  commission_rate_percent: number;
  commission_per_sale: number;
  est_commission_1pct: number;
  est_commission_1_5pct: number;
  created_at: string;
}

export interface RevenueSummary {
  target_commission_inr: number;
  target_days: number;
  total_posts_generated: number;
  total_clicks: number;
  clicks_by_channel: {
    whatsapp: number;
    telegram: number;
    reddit: number;
    x: number;
    other: number;
  };
  channel_learning_weights?: Record<string, number>;
  active_campaigns_count: number;
  estimated_commission_pool_inr: number;
  average_commission_per_sale_inr: number;
  total_sales_needed_for_10_lakh: number;
  recent_clicks: Array<{
    id: string;
    asin: string;
    channel: string;
    subtag: string;
    created_at: string;
  }>;
  recent_deals: Array<{
    campaign_id: string;
    name: string;
    asin: string;
    category: string;
    deal_price: number;
    mrp: number;
    discount_pct: number;
    commission_rate_percent: number;
    estimated_commission_rupees: number;
    sales_needed_for_10_lakh: number;
    subtag: string;
    created_at: string;
    quality_verdict?: {
      verdict: string;
      verdict_badge: string;
      reason: string;
      criteria_passed_count: number;
      composite_velocity_score?: number;
      pool_tier?: string;
      score_breakdown?: {
        commission_yield_pts: number;
        discount_depth_pts: number;
        social_proof_pts: number;
        impulse_fit_pts: number;
        total_score: number;
      };
      criteria: Record<string, boolean>;
    };
    where_to_post?: {
      whatsapp_groups: Array<{ type?: string; name: string; angle: string; badge?: string }>;
      telegram_channels: Array<string | { name: string; handle: string; desc?: string }>;
      subreddits: Array<string | { name: string; url?: string; desc?: string }>;
      hashtags: string[];
      best_posting_window: string;
    };
  }>;
  posts_attribution?: PostAttribution[];
  daily_performance?: DailyPerformanceSummary;
}

export interface DailyPerformanceSummary {
  top_3_deals: Array<{
    asin: string;
    title: string;
    clicks: number;
    est_commission: number;
  }>;
  best_performing_channel: {
    channel: string;
    clicks: number;
    share_percent: number;
    label: string;
    vs_telegram: string;
  };
  pace_vs_target: {
    target_90_days: number;
    daily_target_runrate: number;
    current_daily_runrate: number;
    pace_status: "ON TRACK" | "NEEDS ACCELERATION" | "BEHIND" | string;
    runrate_gap: number;
  };
  remaining_posts_needed_today: {
    daily_quota: number;
    posts_completed_today: number;
    remaining_today: number;
  };
}

export interface N8nExportItem {
  asin: string;
  title: string;
  price: number;
  mrp: number;
  discount: number;
  category: string;
  affiliate_url: string;
  whatsapp_message: string;
  telegram_message: string;
  unique_tag: string;
  quality_verdict: string;
  commission_rate_percent: number;
  estimated_commission_rupees: number;
  rating: number;
  review_count: number;
}

export interface ActivityFeedItem {
  id: string;
  asin: string;
  title: string;
  channel: string;
  channel_badge: string;
  subtag: string;
  target_url: string;
  referrer: string;
  created_at: string;
  deal_price: number;
  est_commission_rupees: number;
}
