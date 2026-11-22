from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CompetitorBase(BaseModel):
    name: str
    domain: str
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    pricing_tier: Optional[str] = None
    displacement_angle: Optional[str] = None
    source_urls_json: Optional[str] = None


class CompetitorResponse(CompetitorBase):
    id: str
    campaign_id: str
    created_at: datetime

    class Config:
        from_attributes = True
