from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OutreachMessageBase(BaseModel):
    channel: str = "email"
    subject: Optional[str] = None
    body_step1: Optional[str] = None
    body_step2: Optional[str] = None
    body_step3: Optional[str] = None
    social_reply: Optional[str] = None
    linkedin_dm: Optional[str] = None
    status: str = "draft"


class OutreachUpdate(BaseModel):
    subject: Optional[str] = None
    body_step1: Optional[str] = None
    body_step2: Optional[str] = None
    body_step3: Optional[str] = None
    social_reply: Optional[str] = None
    linkedin_dm: Optional[str] = None
    status: Optional[str] = None


class OutreachResponse(OutreachMessageBase):
    id: str
    lead_id: str
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    reply_sentiment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
