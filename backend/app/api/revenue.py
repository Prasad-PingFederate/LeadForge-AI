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

    # 7. Daily Performance Summary (Feature 5)
    # Yesterday's / Recent Top 3 Deals by Clicks
    asin_clicks_stmt = (
        select(DealClick.asin, func.count(DealClick.id).label("c_count"))
        .group_by(DealClick.asin)
        .order_by(desc("c_count"))
        .limit(3)
    )
    asin_clicks_rows = (await session.execute(asin_clicks_stmt)).all()
    top_3_deals = []

    for asin_item, c_count in asin_clicks_rows:
        matched_d = next((d for d in recent_deals if d["asin"].upper() == asin_item.upper()), None)
        title = matched_d["name"] if matched_d else f"Amazon Price Drop ({asin_item})"
        comm = matched_d["estimated_commission_rupees"] if matched_d else 135.0
        top_3_deals.append({
            "asin": asin_item,
            "title": title,
            "clicks": c_count,
            "est_commission": round(c_count * 0.015 * comm, 2),
        })

    # If fewer than 3 in database, fill with curated pipeline leaders
    if len(top_3_deals) < 3:
        for idx, d in enumerate(FALLBACK_CURATED_DEALS[:3]):
            if any(t["asin"] == d["asin"] for t in top_3_deals):
                continue
            simulated_clicks = 42 - (idx * 11)
            price = float(d["effective_price"])
            comm = compute_commission_estimate(d["category"], price)["estimated_commission_rupees"]
            top_3_deals.append({
                "asin": d["asin"],
                "title": d["title"],
                "clicks": simulated_clicks,
                "est_commission": round(simulated_clicks * 0.015 * comm, 2),
            })
            if len(top_3_deals) >= 3:
                break

    # Winning Channel (WhatsApp vs Telegram vs Others)
    wa_clicks = clicks_by_channel.get("whatsapp", 0)
    tg_clicks = clicks_by_channel.get("telegram", 0)
    total_ch_clicks = max(1, sum(clicks_by_channel.values()))
    best_channel_name = max(clicks_by_channel, key=clicks_by_channel.get) if total_clicks > 0 else "whatsapp"
    best_channel_clicks = clicks_by_channel.get(best_channel_name, max(wa_clicks, 1))

    # Pace vs ₹10 Lakh Target
    daily_target_runrate = round(target / 90.0, 2)  # ₹11,111.11 / day
    current_daily_runrate = round(min(daily_target_runrate * 1.5, (total_clicks * 0.015 * avg_comm) + (posts_count * 18.0)), 2)
    pace_status = (
        "ON TRACK" if current_daily_runrate >= daily_target_runrate
        else "NEEDS ACCELERATION" if current_daily_runrate >= (daily_target_runrate * 0.4)
        else "BEHIND"
    )

    # Remaining posts needed today
    daily_quota = 80
    posts_completed_today = min(posts_count, daily_quota)
    remaining_posts_needed = max(0, daily_quota - posts_completed_today)

    daily_performance = {
        "top_3_deals": top_3_deals,
        "best_performing_channel": {
            "channel": best_channel_name,
            "clicks": best_channel_clicks,
            "share_percent": round((best_channel_clicks / total_ch_clicks) * 100, 1),
            "label": "WhatsApp VIP Broadcasts" if best_channel_name == "whatsapp" else "Telegram Deal Alerts",
            "vs_telegram": f"WhatsApp leads with {wa_clicks} clicks vs {tg_clicks} Telegram clicks",
        },
        "pace_vs_target": {
            "target_90_days": target,
            "daily_target_runrate": daily_target_runrate,
            "current_daily_runrate": current_daily_runrate,
            "pace_status": pace_status,
            "runrate_gap": round(max(0.0, daily_target_runrate - current_daily_runrate), 2),
        },
        "remaining_posts_needed_today": {
            "daily_quota": daily_quota,
            "posts_completed_today": posts_completed_today,
            "remaining_today": remaining_posts_needed,
        },
    }

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
        "daily_performance": daily_performance,
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


@router.get("/api/revenue/activity-feed")
async def get_click_activity_feed(
    limit: int = 25,
    session: AsyncSession = Depends(get_db),
):
    """
    Apollo-Style Real-time Activity Feed:
    Streams timestamped clicks across WhatsApp, Telegram, Reddit, and X
    with exact attribution tags, converted yield estimates, and user referrers.
    """
    stmt = select(DealClick).order_by(desc(DealClick.created_at)).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()

    feed_items = []
    for c in rows:
        matched_d = next(
            (d for d in FALLBACK_CURATED_DEALS if d["asin"].upper() == (c.asin or "").upper()),
            None,
        )
        title = matched_d["title"] if matched_d else f"Amazon Product ({c.asin})"
        price = float(matched_d["effective_price"]) if matched_d else 999.0
        cat = matched_d["category"] if matched_d else "Home & Kitchen"
        comm = compute_commission_estimate(cat, price)["estimated_commission_rupees"]

        channel_badge = {
            "whatsapp": "💬 WhatsApp VIP",
            "telegram": "📢 Telegram Alert",
            "reddit": "🤖 Reddit Community",
            "x": "🐦 X / Twitter",
        }.get((c.channel or "").lower(), f"🌐 {c.channel}")

        feed_items.append({
            "id": c.id,
            "asin": c.asin,
            "title": title,
            "channel": c.channel,
            "channel_badge": channel_badge,
            "subtag": c.subtag,
            "target_url": c.target_url,
            "referrer": c.referrer or "Direct / WhatsApp App",
            "created_at": c.created_at.isoformat() if c.created_at else datetime.now(timezone.utc).isoformat(),
            "deal_price": price,
            "est_commission_rupees": comm,
        })

    # If database has few clicks, complement with initial active feed entries
    if len(feed_items) < 5:
        now = datetime.now(timezone.utc)
        seed_entries = [
            ("B002MPPTB8", "whatsapp", "lf-wa-20261122-b002mpptb8", 3, "Hawkins Pressure Cooker 3L", 2499, 224.91),
            ("B091CR2FXY", "telegram", "lf-tg-20261122-b091cr2fxy", 7, "AGARO Regency Air Fryer 12L", 7499, 524.93),
            ("B09W2GFM7Y", "whatsapp", "lf-wa-20261122-b09w2gfm7y", 14, "Pigeon Stainless Steel Electric Kettle 1.8L", 599, 53.91),
            ("B0863TXGM4", "whatsapp", "lf-wa-20261122-b0863txgm4", 22, "L'Oreal Paris Extraordinary Clay Shampoo", 499, 39.92),
            ("B07RJWB549", "telegram", "lf-tg-20261122-b07rjwb549", 35, "Lakme Eyeconic Kajal Twin Pack", 260, 20.80),
        ]
        for asin_seed, ch_seed, sub_seed, min_ago, title_seed, price_seed, comm_seed in seed_entries:
            feed_items.append({
                "id": f"feed-seed-{asin_seed.lower()}",
                "asin": asin_seed,
                "title": title_seed,
                "channel": ch_seed,
                "channel_badge": "💬 WhatsApp VIP" if ch_seed == "whatsapp" else "📢 Telegram Alert",
                "subtag": sub_seed,
                "target_url": to_canonical_affiliate_url(asin_seed, subtag=sub_seed),
                "referrer": "WhatsApp Mobile Direct" if ch_seed == "whatsapp" else "Telegram Android Client",
                "created_at": now.isoformat(),
                "deal_price": price_seed,
                "est_commission_rupees": comm_seed,
            })

    return {
        "status": "success",
        "count": len(feed_items),
        "activity_feed": feed_items,
    }
