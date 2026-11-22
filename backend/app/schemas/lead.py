from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class LeadBase(BaseModel):
    company_name: str
    domain: str
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    contact_email: Optional[str] = None
    email_status: str = "unverified"
    linkedin_url: Optional[str] = None
    intent_platform: str
    intent_source_url: str
    intent_snippet: Optional[str] = None
    fit_score: int = 0
    intent_score: int = 0
    verif_score: int = 0
    overall_score: int = 0
    score_breakdown_json: Optional[str] = None
    why_this_lead: Optional[str] = None
    status: str = "new"


class LeadResponse(LeadBase):
    id: str
    campaign_id: str
    strategy_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadFilterParams(BaseModel):
    min_score: Optional[int] = None
    email_verified_only: Optional[bool] = False
    intent_platform: Optional[str] = None
    strategy_id: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    skip: int = 0
    limit: int = 50
