from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class CampaignCreate(BaseModel):
    name: Optional[str] = None
    target_url: str = Field(..., description="Target product website URL, Amazon link, or BharatBazaro URL")
    campaign_type: str = Field("b2b", description="'b2b' for B2B enterprise sales, 'b2c_deals' for BharatBazaro/Amazon affiliate deal promotion")
    description: Optional[str] = Field(None, description="Optional description of product, ICP hints, or deal category")


class ICPData(BaseModel):
    product_name: str
    category: str
    value_proposition: str
    target_roles: List[str]
    target_industries: List[str]
    company_size_range: str
    core_pain_points: List[str]
    intent_search_queries: List[str]
    negative_keywords: List[str]


class CampaignResponse(BaseModel):
    id: str
    name: str
    target_url: str
    campaign_type: str = "b2b"
    description: Optional[str] = None
    icp_json: Optional[str] = None
    deal_metadata_json: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignDetailResponse(CampaignResponse):
    competitors_count: int = 0
    strategies_count: int = 0
    leads_count: int = 0
    verified_leads_count: int = 0
