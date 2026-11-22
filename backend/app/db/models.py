import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icp_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    competitors: Mapped[List["Competitor"]] = relationship(
        "Competitor", back_populates="campaign", cascade="all, delete-orphan", lazy="selectin"
    )
    strategies: Mapped[List["Strategy"]] = relationship(
        "Strategy", back_populates="campaign", cascade="all, delete-orphan", lazy="selectin"
    )
    leads: Mapped[List["Lead"]] = relationship(
        "Lead", back_populates="campaign", cascade="all, delete-orphan", lazy="selectin"
    )


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pricing_tier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    displacement_angle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_urls_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="competitors")

    __table_args__ = (
        Index("ix_competitor_campaign_id", "campaign_id"),
    )


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="email", nullable=False)
    angle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_queries_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversion_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="strategies")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="strategy", lazy="selectin")

    __table_args__ = (
        Index("ix_strategy_campaign_id", "campaign_id"),
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    strategy_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_status: Mapped[str] = mapped_column(String(50), default="unverified", nullable=False)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Proof of Intent (CRITICAL ZERO-HALLUCINATION INVARIANT)
    intent_platform: Mapped[str] = mapped_column(String(50), nullable=False)
    intent_source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    intent_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Transparent Scoring Engine (0-100)
    fit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)       # 0 - 40
    intent_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)    # 0 - 35
    verif_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)     # 0 - 25
    overall_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)   # 0 - 100
    score_breakdown_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    why_this_lead: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="leads")
    strategy: Mapped[Optional["Strategy"]] = relationship("Strategy", back_populates="leads")
    outreach_messages: Mapped[List["OutreachMessage"]] = relationship(
        "OutreachMessage", back_populates="lead", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_lead_campaign_id", "campaign_id"),
        Index("ix_lead_domain", "domain"),
        Index("ix_lead_contact_email", "contact_email"),
        Index("ix_lead_overall_score", "overall_score"),
    )


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="email", nullable=False)

    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_step1: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_step2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_step3: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    social_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_dm: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reply_sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="outreach_messages")

    __table_args__ = (
        Index("ix_outreach_lead_id", "lead_id"),
        Index("ix_outreach_status", "status"),
    )


class SuppressionList(Base):
    __tablename__ = "suppression_list"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(String(100), default="unsubscribed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_suppression_domain", "domain"),
        Index("ix_suppression_email", "email"),
    )
