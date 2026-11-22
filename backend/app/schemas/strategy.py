from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class StrategyBase(BaseModel):
    title: str
    channel: str = "email"
    angle: Optional[str] = None
    target_queries_json: Optional[str] = None
    conversion_weight: float = 1.0


class StrategyResponse(StrategyBase):
    id: str
    campaign_id: str
    created_at: datetime

    class Config:
        from_attributes = True
