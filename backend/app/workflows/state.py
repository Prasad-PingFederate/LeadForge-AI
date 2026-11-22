from typing import TypedDict, List, Dict, Any, Optional


class LeadForgeState(TypedDict):
    campaign_id: str
    target_url: str
    description: str
    icp_data: Dict[str, Any]
    competitors: List[Dict[str, Any]]
    strategies: List[Dict[str, Any]]
    raw_leads: List[Dict[str, Any]]
    enriched_leads: List[Dict[str, Any]]
    outreach_drafts: List[Dict[str, Any]]
    current_step: str
    progress_percent: int
    logs: List[str]
    error: Optional[str]
