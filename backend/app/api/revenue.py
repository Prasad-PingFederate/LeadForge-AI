import json
import logging
import math
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Campaign, OutreachMessage, Lead, DealClick
from app.core.deal_analyzer import (
    to_canonical_affiliate_url,
    compute_commission_estimate,
    extract_asin,
    FALLBACK_CURATED_DEALS,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Revenue & Tracking"])


class ClickEventPayload(BaseModel):
    asin: str
    channel: str = "whatsapp"
    subtag: Optional[str] = None
    campaign_id: Optional[str] = None
    outreach_id: Optional[str] = None
    referrer: Optional[str] = None


@router.get("/api/revenue/summary")
async def get_revenue_summary(session: AsyncSession = Depends(get_db)):
    """
    Sales Manager revenue dashboard:
    Tracks progress towards ₹10 Lakh in commissions, posts generated,
    and granular channel clicks.
    """
    # 1. Total posts generated
    posts_count = await session.scalar(
        select(func.count(OutreachMessage.id)).where(
            (OutreachMessage.whatsapp_message.isnot(None))
            | (OutreachMessage.telegram_message.isnot(None))
        )
    ) or 0

    # 2. Total clicks recorded
    total_clicks = await session.scalar(select(func.count(DealClick.id))) or 0

    # 3. Clicks by channel
    channel_stmt = select(DealClick.channel, func.count(DealClick.id)).group_by(DealClick.channel)
    channel_rows = (await session.execute(channel_stmt)).all()
    clicks_by_channel = {
        "whatsapp": 0,
        "telegram": 0,
        "reddit": 0,
        "x": 0,
        "other": 0,
    }
    for ch, count in channel_rows:
        ch_key = ch.lower() if ch else "other"
        if ch_key in clicks_by_channel:
            clicks_by_channel[ch_key] += count
        else:
            clicks_by_channel["other"] += count

    # 4. Recent clicks
    clicks_stmt = select(DealClick).order_by(desc(DealClick.created_at)).limit(15)
    recent_clicks_rows = (await session.execute(clicks_stmt)).scalars().all()
    recent_clicks = [
        {
            "id": c.id,
            "asin": c.asin,
            "channel": c.channel,
            "subtag": c.subtag,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recent_clicks_rows
    ]

    # 5. Active B2C Deal Campaigns & Commission Pool
    camp_stmt = (
        select(Campaign)
        .where(Campaign.campaign_type == "b2c_deals")
        .order_by(desc(Campaign.created_at))
        .limit(20)
    )
    campaigns = (await session.execute(camp_stmt)).scalars().all()

    total_est_commission_pool = 0.0
    recent_deals = []

    for camp in campaigns:
        meta = {}
        if camp.deal_metadata_json:
            try:
                meta = json.loads(camp.deal_metadata_json)
            except Exception:
                meta = {}

        price = float(meta.get("effective_price") or 599.0)
        cat = meta.get("category", "Home & Kitchen")
        comm_info = compute_commission_estimate(cat, price)
        comm_rupees = comm_info["estimated_commission_rupees"]
        total_est_commission_pool += (comm_rupees * 100)  # assume 100 conversions baseline

        sales_needed_10l = math.ceil(1000000.0 / comm_rupees) if comm_rupees > 0 else 999999

        recent_deals.append({
            "campaign_id": camp.id,
            "name": camp.name,
            "asin": meta.get("asin", "B09W2GFM7Y"),
            "category": cat,
            "deal_price": price,
            "mrp": float(meta.get("mrp") or (price * 1.5)),
            "discount_pct": int(meta.get("discount_pct") or 40),
            "commission_rate_percent": comm_info["commission_rate_percent"],
            "estimated_commission_rupees": comm_rupees,
            "sales_needed_for_10_lakh": sales_needed_10l,
            "subtag": f"lf-wa-{camp.id[:6]}",
            "created_at": camp.created_at.isoformat(),
        })

    # If no campaigns run yet, show curated pipeline deals
    if not recent_deals:
        for d in FALLBACK_CURATED_DEALS:
            price = float(d["effective_price"])
            comm_info = compute_commission_estimate(d["category"], price)
            comm_rupees = comm_info["estimated_commission_rupees"]
            sales_needed_10l = math.ceil(1000000.0 / comm_rupees) if comm_rupees > 0 else 999999
            recent_deals.append({
                "campaign_id": "seed",
                "name": d["title"],
                "asin": d["asin"],
                "category": d["category"],
                "deal_price": price,
                "mrp": float(d["mrp"]),
                "discount_pct": int(d["discount_pct"]),
                "commission_rate_percent": comm_info["commission_rate_percent"],
                "estimated_commission_rupees": comm_rupees,
                "sales_needed_for_10_lakh": sales_needed_10l,
                "subtag": f"lf-wa-{d['asin'][:6]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    target = 1000000.0
    avg_comm = (
        round(sum(d["estimated_commission_rupees"] for d in recent_deals) / len(recent_deals), 2)
        if recent_deals
        else 150.0
    )
    sales_needed_total = math.ceil(target / avg_comm)

    return {
        "target_commission_inr": target,
        "target_days": 90,
        "total_posts_generated": posts_count,
        "total_clicks": total_clicks,
        "clicks_by_channel": clicks_by_channel,
        "active_campaigns_count": len(campaigns),
        "estimated_commission_pool_inr": round(total_est_commission_pool, 2),
        "average_commission_per_sale_inr": avg_comm,
        "total_sales_needed_for_10_lakh": sales_needed_total,
        "recent_clicks": recent_clicks,
        "recent_deals": recent_deals[:10],
    }


@router.post("/api/deals/click", status_code=status.HTTP_201_CREATED)
async def track_deal_click(
    payload: ClickEventPayload,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Logs an affiliate link click or share action from the distribution engine."""
    asin = extract_asin(payload.asin) or payload.asin.strip().upper()
    subtag = payload.subtag or f"lf-{payload.channel[:2]}-{asin[:6]}"
    target_url = to_canonical_affiliate_url(asin, subtag=subtag)

    click = DealClick(
        campaign_id=payload.campaign_id,
        outreach_id=payload.outreach_id,
        asin=asin,
        channel=payload.channel.lower(),
        subtag=subtag,
        target_url=target_url,
        referrer=payload.referrer or request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
    )
    session.add(click)

    # Increment click count on outreach message if matched
    if payload.outreach_id:
        outreach = await session.get(OutreachMessage, payload.outreach_id)
        if outreach:
            outreach.clicks_count = (outreach.clicks_count or 0) + 1

    await session.commit()
    logger.info(f"Recorded affiliate click: asin={asin} channel={payload.channel} subtag={subtag}")

    return {
        "success": True,
        "click_id": click.id,
        "asin": asin,
        "subtag": subtag,
        "canonical_affiliate_url": target_url,
    }


@router.get("/r/{subtag}")
@router.get("/api/r/{subtag}")
async def redirect_short_link(
    subtag: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    HTTP 302 Short Link Redirector:
    Logs click server-side and redirects directly to Amazon India with tag=dammaiprasad-21.
    """
    clean_subtag = subtag.strip()
    parts = clean_subtag.split("-")
    # Subtag format: lf-{channel}-{YYYYMMDD}-{ident}
    channel = "whatsapp"
    asin = "B002MPPTB8"

    if len(parts) >= 2:
        ch_code = parts[1].lower()
        channel = {"wa": "whatsapp", "tg": "telegram", "rd": "reddit", "x": "x"}.get(ch_code, "whatsapp")

    if len(parts) >= 4:
        ident = parts[3].upper()
        if len(ident) == 10 and ident.isalnum():
            asin = ident

    target_url = to_canonical_affiliate_url(asin, subtag=clean_subtag)

    # Log click
    click = DealClick(
        asin=asin,
        channel=channel,
        subtag=clean_subtag,
        target_url=target_url,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
    )
    session.add(click)
    await session.commit()

    return RedirectResponse(url=target_url, status_code=302)
