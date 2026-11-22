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
  description?: string;
  status: "pending" | "profiling" | "competitor_analysis" | "hunting" | "enriching" | "completed" | "failed";
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
