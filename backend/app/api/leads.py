import csv
import io
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
import httpx
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Lead, Campaign
from app.schemas.lead import LeadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/campaigns/{campaign_id}/leads", tags=["Leads"])


class WebhookPayload(BaseModel):
    webhook_url: str
    min_score: int = 50


@router.get("", response_model=List[LeadResponse])
async def list_campaign_leads(
    campaign_id: str,
    min_score: Optional[int] = Query(None, description="Minimum lead score (0-100)"),
    email_verified_only: bool = Query(False, description="Filter for email_status == 'verified' only"),
    intent_platform: Optional[str] = Query(None, description="Filter by source platform: reddit, hackernews, etc."),
    strategy_id: Optional[str] = Query(None, description="Filter by strategy"),
    status: Optional[str] = Query(None, description="Filter by status: new, approved, sent, etc."),
    search: Optional[str] = Query(None, description="Search company, contact name or domain"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Lead).where(Lead.campaign_id == campaign_id)

    if min_score is not None:
        stmt = stmt.where(Lead.overall_score >= min_score)
    if email_verified_only:
        stmt = stmt.where(Lead.email_status == "verified")
    if intent_platform:
        stmt = stmt.where(Lead.intent_platform == intent_platform)
    if strategy_id:
        stmt = stmt.where(Lead.strategy_id == strategy_id)
    if status:
        stmt = stmt.where(Lead.status == status)
    if search:
        search_pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Lead.company_name).like(search_pattern)
            | func.lower(Lead.domain).like(search_pattern)
            | func.lower(Lead.contact_name).like(search_pattern)
        )

    stmt = stmt.order_by(desc(Lead.overall_score)).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/export")
async def export_leads_csv(
    campaign_id: str,
    min_score: Optional[int] = Query(None),
    email_verified_only: bool = Query(False),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Lead).where(Lead.campaign_id == campaign_id)
    if min_score is not None:
        stmt = stmt.where(Lead.overall_score >= min_score)
    if email_verified_only:
        stmt = stmt.where(Lead.email_status == "verified")

    stmt = stmt.order_by(desc(Lead.overall_score))
    result = await session.execute(stmt)
    leads = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Company Name",
        "Domain",
        "Contact Name",
        "Contact Role",
        "Contact Email",
        "Email Verification Status",
        "Lead Score",
        "Intent Platform",
        "Intent Proof URL",
        "Intent Snippet",
        "Why This Lead",
        "Created At",
    ])

    for l in leads:
        writer.writerow([
            l.company_name,
            l.domain,
            l.contact_name or "",
            l.contact_role or "",
            l.contact_email or "",
            l.email_status,
            l.overall_score,
            l.intent_platform,
            l.intent_source_url,
            l.intent_snippet or "",
            l.why_this_lead or "",
            l.created_at.isoformat() if l.created_at else "",
        ])

    csv_data = output.getvalue()
    filename = f"leadforge_leads_{campaign_id[:8]}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/webhook")
async def trigger_webhook_push(
    campaign_id: str,
    payload: WebhookPayload,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Lead).where(
        Lead.campaign_id == campaign_id,
        Lead.overall_score >= payload.min_score,
    ).order_by(desc(Lead.overall_score))
    result = await session.execute(stmt)
    leads = result.scalars().all()

    items = []
    for l in leads:
        items.append({
            "id": l.id,
            "company_name": l.company_name,
            "domain": l.domain,
            "contact_name": l.contact_name,
            "contact_email": l.contact_email,
            "email_status": l.email_status,
            "overall_score": l.overall_score,
            "intent_platform": l.intent_platform,
            "intent_source_url": l.intent_source_url,
            "intent_snippet": l.intent_snippet,
            "why_this_lead": l.why_this_lead,
        })

    webhook_data = {
        "event": "leadforge.leads.synced",
        "campaign_id": campaign_id,
        "count": len(items),
        "leads": items,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(payload.webhook_url, json=webhook_data)
            return {
                "success": True,
                "status_code": resp.status_code,
                "leads_pushed": len(items),
            }
    except Exception as exc:
        logger.error(f"Webhook push failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "leads_count": len(items),
        }
