import json
import logging
import math
import re
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
    evaluate_deal_quality,
    generate_where_to_post_recommendations,
    get_channel_performance_weights,
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
        quality = evaluate_deal_quality({"effective_price": price, "discount_pct": meta.get("discount_pct", 40), "rating": meta.get("rating", 4.3), "review_count": meta.get("review_count", 4500), "category": cat})
        where_to_post = generate_where_to_post_recommendations(cat, price, camp.name)

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
            "quality_verdict": quality,
            "where_to_post": where_to_post,
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
            quality = evaluate_deal_quality(d)
            where_to_post = generate_where_to_post_recommendations(d["category"], price, d["title"])
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
                "quality_verdict": quality,
                "where_to_post": where_to_post,
                "subtag": f"lf-wa-{d['asin'][:6]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    # 6. Post-Level Click & Commission Attribution (Feature 1)
    posts_stmt = (
        select(OutreachMessage, Lead, Campaign)
        .join(Lead, OutreachMessage.lead_id == Lead.id)
        .join(Campaign, Lead.campaign_id == Campaign.id)
        .order_by(desc(OutreachMessage.created_at))
        .limit(30)
    )
    post_rows = (await session.execute(posts_stmt)).all()
    posts_attribution = []

    for msg, lead, camp in post_rows:
        meta = {}
        if camp.deal_metadata_json:
            try:
                meta = json.loads(camp.deal_metadata_json)
            except Exception:
                meta = {}

        deal_title = meta.get("title") or camp.name
        asin = meta.get("asin") or extract_asin(msg.deal_affiliate_url or "") or "B09W2GFM7Y"
        cat = meta.get("category", "Home & Kitchen")
        price = float(meta.get("effective_price") or 599.0)
        comm_info = compute_commission_estimate(cat, price)
        comm_rupees = comm_info["estimated_commission_rupees"]

        clicks = msg.clicks_count or 0
        est_comm_1pct = round(clicks * 0.01 * comm_rupees, 2)
        est_comm_1_5pct = round(clicks * 0.015 * comm_rupees, 2)
        sub = msg.subtag or f"lf-wa-{asin.lower()[:10]}"

        posts_attribution.append({
            "id": msg.id,
            "channel": msg.channel,
            "title": deal_title,
            "asin": asin,
            "subtag": sub,
            "short_url": f"/go/{sub}",
            "clicks": clicks,
            "deal_price": price,
            "commission_rate_percent": comm_info["commission_rate_percent"],
            "commission_per_sale": comm_rupees,
            "est_commission_1pct": est_comm_1pct,
            "est_commission_1_5pct": est_comm_1_5pct,
            "created_at": msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat(),
        })

    # If no stored messages yet, seed high-intent post attribution rows
    if not posts_attribution:
        for idx, d in enumerate(FALLBACK_CURATED_DEALS):
            price = float(d["effective_price"])
            comm_info = compute_commission_estimate(d["category"], price)
            comm_rupees = comm_info["estimated_commission_rupees"]
            sub = f"lf-{'wa' if idx % 2 == 0 else 'tg'}-20261122-{d['asin'].lower()}"
            clicks = 24 - (idx * 5) if idx < 4 else 3
            posts_attribution.append({
                "id": f"post-{d['asin'].lower()}",
                "channel": "whatsapp" if idx % 2 == 0 else "telegram",
                "title": d["title"],
                "asin": d["asin"],
                "subtag": sub,
                "short_url": f"/go/{sub}",
                "clicks": clicks,
                "deal_price": price,
                "commission_rate_percent": comm_info["commission_rate_percent"],
                "commission_per_sale": comm_rupees,
                "est_commission_1pct": round(clicks * 0.01 * comm_rupees, 2),
                "est_commission_1_5pct": round(clicks * 0.015 * comm_rupees, 2),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    target = 1000000.0
    avg_comm = (
        round(sum(d["estimated_commission_rupees"] for d in recent_deals) / len(recent_deals), 2)
        if recent_deals
        else 150.0
    )
    sales_needed_total = math.ceil(target / avg_comm)
    channel_learning_weights = get_channel_performance_weights(clicks_by_channel)

    return {
        "target_commission_inr": target,
        "target_days": 90,
        "total_posts_generated": max(posts_count, len(posts_attribution)),
        "total_clicks": total_clicks,
        "clicks_by_channel": clicks_by_channel,
        "channel_learning_weights": channel_learning_weights,
        "active_campaigns_count": len(campaigns),
        "estimated_commission_pool_inr": round(total_est_commission_pool, 2),
        "average_commission_per_sale_inr": avg_comm,
        "total_sales_needed_for_10_lakh": sales_needed_total,
        "recent_clicks": recent_clicks,
        "recent_deals": recent_deals[:10],
        "posts_attribution": posts_attribution,
    }


@router.post("/api/deals/click", status_code=status.HTTP_201_CREATED)
async def track_deal_click(
    payload: ClickEventPayload,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Logs an affiliate link click or share action from the distribution engine."""
    asin = extract_asin(payload.asin) or payload.asin.strip().upper()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    subtag = payload.subtag or f"lf-{payload.channel[:2]}-{date_str}-{asin.lower()[:10]}"
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
    elif payload.subtag:
        outreach_stmt = select(OutreachMessage).where(OutreachMessage.subtag == payload.subtag).limit(1)
        outreach = (await session.execute(outreach_stmt)).scalar_one_or_none()
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


async def _execute_short_redirect(identifier: str, request: Request, session: AsyncSession) -> RedirectResponse:
    clean_id = identifier.strip()
    channel = "whatsapp"
    asin = "B002MPPTB8"
    subtag = clean_id

    # Check if identifier is a pure 10-char ASIN (e.g. /a/B002MPPTB8)
    if re.fullmatch(r"^[A-Za-z0-9]{10}$", clean_id):
        asin = clean_id.upper()
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        subtag = f"lf-a-{date_str}-{asin.lower()}"
    else:
        # It is an ascsubtag: lf-{ch}-{date}-{asin/camp}
        parts = clean_id.split("-")
        if len(parts) >= 2:
            ch_code = parts[1].lower()
            channel = {"wa": "whatsapp", "tg": "telegram", "rd": "reddit", "x": "x", "em": "email"}.get(ch_code, "whatsapp")
        if len(parts) >= 4:
            ident = parts[3].upper()
            if len(ident) == 10 and ident.isalnum():
                asin = ident

    # If matching OutreachMessage exists, increment clicks_count and fetch campaign deal ASIN
    outreach_stmt = select(OutreachMessage).where(OutreachMessage.subtag == clean_id).limit(1)
    outreach = (await session.execute(outreach_stmt)).scalar_one_or_none()
    if outreach:
        outreach.clicks_count = (outreach.clicks_count or 0) + 1
        lead = await session.get(Lead, outreach.lead_id)
        if lead and lead.campaign_id:
            camp = await session.get(Campaign, lead.campaign_id)
            if camp and camp.deal_metadata_json:
                try:
                    meta = json.loads(camp.deal_metadata_json)
                    if meta.get("asin"):
                        asin = meta["asin"].upper()
                except Exception:
                    pass

    target_url = to_canonical_affiliate_url(asin, subtag=subtag)

    # Log click server-side
    click = DealClick(
        asin=asin,
        channel=channel,
        subtag=subtag,
        target_url=target_url,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
    )
    session.add(click)
    await session.commit()
    logger.info(f"Short link redirect: {clean_id} -> {target_url} [asin={asin}, channel={channel}]")

    return RedirectResponse(url=target_url, status_code=302)


@router.get("/r/{subtag}")
@router.get("/api/r/{subtag}")
@router.get("/go/{subtag}")
@router.get("/api/go/{subtag}")
async def redirect_short_link(
    subtag: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    HTTP 302 Short Link Redirector (/r/ and /go/):
    Logs click server-side and redirects directly to Amazon India with tag=dammaiprasad-21.
    """
    return await _execute_short_redirect(subtag, request, session)


@router.get("/a/{path_param}")
@router.get("/api/a/{path_param}")
async def redirect_short_asin(
    path_param: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    HTTP 302 ASIN Short Link Redirector (/a/:asin):
    Matches BharatBazaro /a/ASIN path, logs click, and redirects cleanly to Amazon India.
    """
    return await _execute_short_redirect(path_param, request, session)
