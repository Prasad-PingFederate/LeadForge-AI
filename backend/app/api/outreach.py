import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import OutreachMessage, Lead, Strategy, SuppressionList
from app.schemas.outreach import OutreachResponse, OutreachUpdate
from app.workers.mailer import safe_mailer
from app.agents.learning_agent import learning_agent

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Outreach"])


class ReplyPayload(BaseModel):
    reply_text: str


class SendPayload(BaseModel):
    dry_run: bool = True


@router.get("/campaigns/{campaign_id}/outreach", response_model=List[dict])
async def list_campaign_outreach(
    campaign_id: str,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(OutreachMessage)
        .join(Lead)
        .where(Lead.campaign_id == campaign_id)
        .options(selectinload(OutreachMessage.lead))
    )
    if status:
        stmt = stmt.where(OutreachMessage.status == status)

    stmt = stmt.order_by(desc(OutreachMessage.created_at))
    result = await session.execute(stmt)
    messages = result.scalars().all()

    output = []
    for m in messages:
        output.append({
            "id": m.id,
            "lead_id": m.lead_id,
            "company_name": m.lead.company_name if m.lead else "",
            "domain": m.lead.domain if m.lead else "",
            "contact_name": m.lead.contact_name if m.lead else "",
            "contact_email": m.lead.contact_email if m.lead else "",
            "email_status": m.lead.email_status if m.lead else "unverified",
            "overall_score": m.lead.overall_score if m.lead else 0,
            "why_this_lead": m.lead.why_this_lead if m.lead else "",
            "intent_platform": m.lead.intent_platform if m.lead else "",
            "channel": m.channel,
            "subject": m.subject,
            "body_step1": m.body_step1,
            "body_step2": m.body_step2,
            "body_step3": m.body_step3,
            "social_reply": m.social_reply,
            "linkedin_dm": m.linkedin_dm,
            "whatsapp_message": m.whatsapp_message,
            "telegram_message": m.telegram_message,
            "deal_affiliate_url": m.deal_affiliate_url,
            "status": m.status,
            "approved_at": m.approved_at,
            "sent_at": m.sent_at,
            "reply_sentiment": m.reply_sentiment,
            "created_at": m.created_at,
        })
    return output


@router.put("/outreach/{id}", response_model=OutreachResponse)
async def update_outreach_message(
    id: str,
    payload: OutreachUpdate,
    session: AsyncSession = Depends(get_db),
):
    msg = await session.get(OutreachMessage, id)
    if not msg:
        raise HTTPException(status_code=404, detail="Outreach message not found")

    if payload.subject is not None:
        msg.subject = payload.subject
    if payload.body_step1 is not None:
        msg.body_step1 = payload.body_step1
    if payload.body_step2 is not None:
        msg.body_step2 = payload.body_step2
    if payload.body_step3 is not None:
        msg.body_step3 = payload.body_step3
    if payload.social_reply is not None:
        msg.social_reply = payload.social_reply
    if payload.linkedin_dm is not None:
        msg.linkedin_dm = payload.linkedin_dm
    if payload.whatsapp_message is not None:
        msg.whatsapp_message = payload.whatsapp_message
    if payload.telegram_message is not None:
        msg.telegram_message = payload.telegram_message
    if payload.deal_affiliate_url is not None:
        msg.deal_affiliate_url = payload.deal_affiliate_url
    if payload.status is not None:
        msg.status = payload.status
        if payload.status == "approved" and not msg.approved_at:
            msg.approved_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(msg)
    return msg


@router.post("/outreach/{id}/send")
async def send_outreach_message(
    id: str,
    payload: SendPayload = Body(default=SendPayload(dry_run=True)),
    session: AsyncSession = Depends(get_db),
):
    result = await safe_mailer.dispatch_message(session, id, dry_run=payload.dry_run)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/outreach/{id}/reply")
async def record_prospect_reply(
    id: str,
    payload: ReplyPayload,
    session: AsyncSession = Depends(get_db),
):
    msg = await session.get(OutreachMessage, id)
    if not msg:
        raise HTTPException(status_code=404, detail="Outreach message not found")

    lead = await session.get(Lead, msg.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Classify reply with learning agent
    classification = await learning_agent.classify_reply(payload.reply_text)
    sentiment = classification.get("category", "objection")
    msg.reply_sentiment = sentiment
    msg.status = "replied"
    lead.status = "replied"

    # If prospect unsubscribed, add to suppression list
    if sentiment == "unsubscribe":
        lead.status = "unsubscribed"
        supp = SuppressionList(
            domain=lead.domain,
            email=lead.contact_email,
            reason="prospect_unsubscribe_reply",
        )
        session.add(supp)

    new_weight = None
    # Re-weight strategy conversion score
    if lead.strategy_id:
        strat = await session.get(Strategy, lead.strategy_id)
        if strat:
            new_weight = learning_agent.compute_weight_adjustment(strat.conversion_weight, sentiment)
            strat.conversion_weight = new_weight
            logger.info(f"Strategy '{strat.title}' conversion_weight adjusted to {new_weight}")

    await session.commit()

    return {
        "success": True,
        "sentiment": sentiment,
        "classification_summary": classification.get("summary"),
        "lead_status": lead.status,
        "new_strategy_weight": new_weight,
    }
