import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import DealClick, DispatchLog
from app.core.deal_analyzer import (
    fetch_live_deals,
    get_deal_by_asin,
    search_live_deals,
    get_top_converting_deals,
    compute_commission_estimate,
    to_canonical_affiliate_url,
    evaluate_deal_quality,
    generate_where_to_post_recommendations,
    format_whatsapp_deal_post,
    format_telegram_deal_post,
    extract_asin,
    validate_deal_copy,
    generate_3step_sequence,
    compute_loot_score,
    generate_multi_angle_copy,
    generate_audience_copy,
    generate_all_audience_variants,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deals", tags=["B2C Deals"])


@router.get("/live")
async def list_live_deals(
    query: Optional[str] = Query(None, description="Search term in title, brand, or category"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Home & Kitchen, Personal Care)"),
    max_price: Optional[float] = Query(None, description="Max effective price in INR"),
    min_discount: Optional[int] = Query(None, description="Minimum discount percentage"),
    verdict: Optional[str] = Query(None, description="Filter deals by pool ladder verdict (PROMOTE, HOLD, KILL)"),
    limit: int = Query(15, ge=1, le=100),
    force_refresh: bool = Query(False, description="Bypass cache and re-fetch from upstream"),
):
    """Returns verified live deals from BharatBazaro with commission estimates and pool ladder tiering."""
    if force_refresh:
        all_deals = await fetch_live_deals(force_refresh=True)
    else:
        all_deals = await fetch_live_deals()

    # Calculate overall pool ladder counts across entire catalog
    pool_counts = {"promote": 0, "hold": 0, "kill": 0, "total": len(all_deals)}
    for d in all_deals:
        v = evaluate_deal_quality(d).get("verdict", "KILL")
        if v == "PROMOTE":
            pool_counts["promote"] += 1
        elif v == "HOLD":
            pool_counts["hold"] += 1
        else:
            pool_counts["kill"] += 1

    if query or category or max_price is not None or min_discount is not None:
        matched = await search_live_deals(
            query=query or "",
            category=category,
            max_price=max_price,
            min_discount=min_discount,
            limit=limit * 2 if verdict else limit,
        )
    else:
        matched = all_deals

    # Enrich with canonical affiliate link, commission info, and quality verdict
    enriched_deals = []
    for d in matched:
        asin = d.get("asin") or ""
        cat = d.get("category", "General")
        price = float(d.get("effective_price") or d.get("list_price") or 599.0)
        comm = compute_commission_estimate(cat, price)
        quality = evaluate_deal_quality(d)
        where_to_post = generate_where_to_post_recommendations(cat, price, d.get("title", ""))
        loot_info = quality.get("loot_info") or compute_loot_score(d)

        if verdict and quality.get("verdict", "").upper() != verdict.strip().upper():
            continue

        enriched_deals.append({
            **d,
            "canonical_affiliate_url": to_canonical_affiliate_url(asin, subtag="bb-api"),
            "commission_info": comm,
            "quality_verdict": quality,
            "where_to_post": where_to_post,
            "loot_score": loot_info["loot_score"],
            "loot_badge": loot_info["loot_badge"],
            "is_mega_loot": loot_info["is_mega_loot"],
        })
        if len(enriched_deals) >= limit:
            break

    return {
        "count": len(enriched_deals),
        "total_available": len(all_deals),
        "pool_ladder": pool_counts,
        "source": settings.bharatbazaro_live_deals_url,
        "deals": enriched_deals,
    }


class CopyValidationRequest(BaseModel):
    message: str
    affiliate_url: Optional[str] = ""


@router.post("/validate-copy")
async def validate_copy_endpoint(payload: CopyValidationRequest):
    """
    Explee-Style Pre-flight Copy Validator Endpoint:
    Checks compliance of generated WhatsApp/Telegram deal text before broadcasting.
    """
    res = validate_deal_copy(payload.message, payload.affiliate_url or "")
    return res


@router.get("/live/{asin}")
async def get_live_deal_by_asin(asin: str):
    """Fetches a single verified deal by 10-char Amazon ASIN."""
    deal = await get_deal_by_asin(asin)
    if not deal:
        raise HTTPException(status_code=404, detail=f"Deal with ASIN {asin} not found in live feed")

    cat = deal.get("category", "General")
    price = float(deal.get("effective_price") or deal.get("list_price") or 599.0)
    comm = compute_commission_estimate(cat, price)
    quality = evaluate_deal_quality(deal)
    where_to_post = generate_where_to_post_recommendations(cat, price, deal.get("title", ""))
    loot_info = quality.get("loot_info") or compute_loot_score(deal)
    angles = generate_multi_angle_copy(deal, channel="whatsapp")

    return {
        **deal,
        "canonical_affiliate_url": to_canonical_affiliate_url(deal.get("asin", asin), subtag="bb-api-detail"),
        "commission_info": comm,
        "quality_verdict": quality,
        "where_to_post": where_to_post,
        "loot_score": loot_info["loot_score"],
        "loot_badge": loot_info["loot_badge"],
        "is_mega_loot": loot_info["is_mega_loot"],
        "angles": angles["angles"],
        "sequence": generate_3step_sequence(deal),
    }


@router.get("/top-converting")
async def list_top_converting_deals(limit: int = Query(10, ge=1, le=50)):
    """Returns top high-margin impulse deals (₹99-₹2999 sweet spot) from BharatBazaro."""
    top_deals = await get_top_converting_deals(limit=limit)
    enriched = []
    for d in top_deals:
        asin = d.get("asin") or ""
        cat = d.get("category", "General")
        price = float(d.get("effective_price") or d.get("list_price") or 599.0)
        comm = compute_commission_estimate(cat, price)
        quality = evaluate_deal_quality(d)
        where_to_post = generate_where_to_post_recommendations(cat, price, d.get("title", ""))

        enriched.append({
            **d,
            "canonical_affiliate_url": to_canonical_affiliate_url(asin, subtag="bb-top"),
            "commission_info": comm,
            "quality_verdict": quality,
            "where_to_post": where_to_post,
        })

    return {
        "count": len(enriched),
        "deals": enriched,
    }


@router.post("/export-n8n")
@router.get("/export-n8n")
async def export_deals_for_n8n(
    limit: int = Query(25, ge=1, le=100),
    only_promote: bool = Query(True, description="Only export deals passing strict PROMOTE gate"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    min_discount: Optional[int] = Query(30, description="Minimum discount percentage"),
):
    """
    n8n-Ready Webhook Export (Feature 4):
    Returns approved/curated deals in clean JSON format:
    { asin, title, price, mrp, discount, affiliate_url, whatsapp_message, telegram_message, unique_tag }
    Allows automated n8n workflows to immediately push deals to Telegram channels or WhatsApp broadcasts.
    """
    deals = await fetch_live_deals()
    d_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    exported = []

    for d in deals:
        if d.get("expired"):
            continue

        price = float(d.get("effective_price") or d.get("list_price") or 599.0)
        disc = int(d.get("discount_pct") or 0)
        cat = d.get("category") or "Home & Kitchen"
        title = d.get("title") or "Amazon Price Drop"
        asin = d.get("asin") or extract_asin(d.get("affiliate_url", "")) or "B09W2GFM7Y"

        if min_discount and disc < min_discount:
            continue
        if category and category.lower() not in cat.lower():
            continue

        quality = evaluate_deal_quality(d)
        if only_promote and quality.get("verdict") != "PROMOTE":
            continue

        unique_tag = f"lf-n8n-{d_str}-{asin.lower()[:10]}"
        aff_url = to_canonical_affiliate_url(asin, subtag=unique_tag)
        mrp = float(d.get("mrp") or (price * 1.5))
        rating = float(d.get("rating") or 4.3)
        reviews = int(d.get("review_count") or 3500)
        comm = compute_commission_estimate(cat, price)

        wa_msg = format_whatsapp_deal_post(
            title=title,
            deal_price=price,
            mrp=mrp,
            asin=asin,
            rating=rating,
            reviews_count=reviews,
            subtag=unique_tag,
        )
        tg_msg = format_telegram_deal_post(
            title=title,
            deal_price=price,
            mrp=mrp,
            asin=asin,
            subtag=unique_tag,
        )

        exported.append({
            "asin": asin,
            "title": title,
            "price": price,
            "mrp": mrp,
            "discount": disc,
            "category": cat,
            "affiliate_url": aff_url,
            "whatsapp_message": wa_msg,
            "telegram_message": tg_msg,
            "unique_tag": unique_tag,
            "quality_verdict": quality.get("verdict", "PROMOTE"),
            "why_it_converts": quality.get("why_it_converts", ""),
            "commission_rate_percent": comm["commission_rate_percent"],
            "estimated_commission_rupees": comm["estimated_commission_rupees"],
            "rating": rating,
            "review_count": reviews,
            "sequence": generate_3step_sequence(d),
        })

        if len(exported) >= limit:
            break

    return {
        "status": "success",
        "count": len(exported),
        "target_affiliate_tag": settings.amazon_affiliate_tag,
        "deals": exported,
    }


@router.get("/{asin}/angles")
async def get_deal_copy_angles(
    asin: str,
    channel: str = Query("whatsapp", description="Target channel: whatsapp | telegram | reddit | x"),
):
    """
    Lemlist & EarnKaro-Style 4-Angle Copy Engine:
    Returns 4 distinct psychological copy angles (Urgency Loot, Savings Math, Social Proof, Daily Utility)
    for the selected deal, formatted for the requested channel.
    """
    deal = await get_deal_by_asin(asin)
    if not deal:
        raise HTTPException(status_code=404, detail=f"Deal with ASIN {asin} not found")

    angles_data = generate_multi_angle_copy(deal, channel=channel)
    loot = compute_loot_score(deal)
    return {
        "status": "success",
        "asin": asin.upper(),
        "channel": channel,
        "loot_badge": loot["loot_badge"],
        "loot_score": loot["loot_score"],
        "angles": angles_data["angles"],
    }


@router.get("/{asin}/audience-copy")
async def get_deal_audience_copy(
    asin: str,
    channel: str = Query("whatsapp", description="Target channel: whatsapp | telegram"),
):
    """
    Phase 2 Audience Segmentation Copy Endpoint:
    Returns 4 audience-specific message variants (Homemaker, Hostel/College, Office Pro, Budget/Impulse).
    """
    deal = await get_deal_by_asin(asin)
    if not deal:
        raise HTTPException(status_code=404, detail=f"Deal with ASIN {asin} not found")

    variants = generate_all_audience_variants(deal, channel=channel)
    loot = compute_loot_score(deal)
    return {
        "status": "success",
        "asin": asin.upper(),
        "channel": channel,
        "loot_badge": loot["loot_badge"],
        "loot_score": loot["loot_score"],
        "audiences": variants["variants"],
    }


class WhatsAppDispatchRequest(BaseModel):
    asin: str
    audience: str = "homemaker"
    group_jid: str = "120363028392819283@g.us"
    instance_name: str = "bharatbazaro-vip"
    custom_message: Optional[str] = None
    step_number: int = 1


@router.post("/dispatch-whatsapp")
async def dispatch_whatsapp_payload(payload: WhatsAppDispatchRequest):
    """
    Phase 1 WhatsApp Evolution API / Baileys Automation Path:
    Generates production-ready Evolution API / Baileys webhook payloads,
    cURL commands, and anti-ban rate limiting safeguards.
    """
    deal = await get_deal_by_asin(payload.asin)
    if not deal:
        raise HTTPException(status_code=404, detail=f"Deal with ASIN {payload.asin} not found")

    aud_copy = generate_audience_copy(deal, audience=payload.audience, channel="whatsapp")
    msg_text = payload.custom_message or aud_copy["message"]
    subtag = aud_copy["subtag"]

    evolution_payload = {
        "number": payload.group_jid,
        "text": msg_text,
        "options": {
            "delay": 1500,
            "presence": "composing",
            "linkPreview": True,
        },
    }

    baileys_payload = {
        "jid": payload.group_jid,
        "message": {
            "text": msg_text,
        },
    }

    curl_cmd = (
        f"curl -s -X POST 'http://localhost:8080/message/sendText/{payload.instance_name}' \\\n"
        f"  -H 'Content-Type: application/json' \\\n"
        f"  -H 'apikey: <EVOLUTION_API_KEY>' \\\n"
        f"  -d '{json.dumps(evolution_payload)}'"
    )

    anti_ban_warnings = [
        "⚠️ ANTI-BAN WARNING: Maintain minimum 45–60 seconds delay between group broadcasts.",
        "⚠️ HUMAN EMULATION: Keep typing delay enabled (presence: 'composing', 1200ms–2500ms).",
        "⚠️ DAILY VOLUME CAP: Max 50 group broadcasts / day per WhatsApp instance to prevent Meta spam detection.",
        "⚠️ TEMPLATE ROTATION: Rotate audience profiles (Homemaker vs Hostel vs Budget) across different groups.",
    ]

    return {
        "status": "prepared",
        "channel": "whatsapp",
        "audience": payload.audience,
        "asin": payload.asin.upper(),
        "subtag": subtag,
        "message_length": len(msg_text),
        "whatsapp_message": msg_text,
        "evolution_api_payload": evolution_payload,
        "baileys_payload": baileys_payload,
        "curl_command": curl_cmd,
        "anti_ban_warnings": anti_ban_warnings,
        "ready_for_production": True,
    }


N8N_WORKFLOW_TEMPLATE = {
    "name": "BharatBazaro Deal Alert Telegram Bot",
    "nodes": [
        {
            "parameters": {
                "httpMethod": "POST",
                "path": "bharatbazaro-deal-alert",
                "responseMode": "lastNode",
                "options": {}
            },
            "id": "node-webhook-1",
            "name": "Deal Webhook Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [220, 300]
        },
        {
            "parameters": {
                "assignments": {
                    "assignments": [
                        {"id": "c1", "name": "chat_id", "value": "={{ $json.body.chat_id || '@dealsforindia' }}", "type": "string"},
                        {"id": "c2", "name": "text", "value": "={{ $json.body.telegram_message }}", "type": "string"},
                        {"id": "c3", "name": "parse_mode", "value": "Markdown", "type": "string"}
                    ]
                }
            },
            "id": "node-set-2",
            "name": "Prepare Message",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [440, 300]
        },
        {
            "parameters": {
                "operation": "sendMessage",
                "chatId": "={{ $json.chat_id }}",
                "text": "={{ $json.text }}",
                "additionalFields": {
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False
                }
            },
            "id": "node-telegram-3",
            "name": "Telegram Bot Broadcast",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [660, 300]
        }
    ],
    "connections": {
        "Deal Webhook Trigger": {
            "main": [
                [
                    {
                        "node": "Prepare Message",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        "Prepare Message": {
            "main": [
                [
                    {
                        "node": "Telegram Bot Broadcast",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
    },
    "settings": {
        "executionOrder": "v1"
    }
}


@router.get("/n8n-workflow-template")
async def get_n8n_workflow_template():
    """Returns a complete, production-ready n8n workflow JSON schema for Telegram deal alert bots."""
    return {
        "status": "success",
        "description": "Standard importable n8n workflow for automated Telegram bot deal broadcasting",
        "workflow": N8N_WORKFLOW_TEMPLATE,
    }


class TelegramDispatchRequest(BaseModel):
    asin: str
    step_number: int = 1
    channel_id: Optional[str] = None
    custom_message: Optional[str] = None


@router.post("/dispatch-telegram")
async def dispatch_telegram_alert(payload: TelegramDispatchRequest):
    """
    Autonomous Telegram Bot Dispatcher:
    Validates and outputs production-ready webhook payloads, curl command,
    and n8n trigger format for Telegram deal channels.
    """
    deal = await get_deal_by_asin(payload.asin)
    if not deal:
        raise HTTPException(status_code=404, detail=f"Deal with ASIN {payload.asin} not found")

    seq = generate_3step_sequence(deal)
    step_key = (
        "step1_morning" if payload.step_number == 1
        else ("step2_evening" if payload.step_number == 2 else "step3_followup")
    )
    step_data = seq.get(step_key, seq["step1_morning"])
    msg_text = payload.custom_message or step_data["telegram_message"]

    target_chat = payload.channel_id or "@dealsforindia"
    curl_cmd = (
        f"curl -s -X POST 'https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage' \\\n"
        f"  -d 'chat_id={target_chat}' \\\n"
        f"  -d 'parse_mode=Markdown' \\\n"
        f"  --data-urlencode 'text={msg_text}'"
    )

    n8n_webhook_payload = {
        "chat_id": target_chat,
        "telegram_message": msg_text,
        "asin": payload.asin.upper(),
        "subtag": step_data.get("subtag"),
        "step_number": payload.step_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "status": "dispatched_simulated",
        "channel": "telegram",
        "step_number": payload.step_number,
        "asin": payload.asin.upper(),
        "message_length": len(msg_text),
        "telegram_message": msg_text,
        "subtag": step_data.get("subtag"),
        "target_chat": target_chat,
        "n8n_webhook_payload": n8n_webhook_payload,
        "n8n_curl_example": curl_cmd,
        "ready_for_production": True,
    }


class MarkSentRequest(BaseModel):
    slot_id: str
    asin: str
    channel: str = "whatsapp"
    audience: str = "homemaker"
    subtag: Optional[str] = None


@router.post("/mark-sent")
async def mark_deal_sent(payload: MarkSentRequest, session: AsyncSession = Depends(get_db)):
    """
    Phase 1 Dispatch Queue Execution:
    Marks a deal slot as sent, records persistent DispatchLog,
    and logs a DealClick event so attribution dashboard is updated in real time.
    """
    d_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    clean_asin = payload.asin.upper()
    subtag = payload.subtag or f"lf-{payload.channel[:2]}-{d_str}-{clean_asin.lower()[:10]}-{payload.slot_id[:2]}"
    target_url = to_canonical_affiliate_url(clean_asin, subtag=subtag)

    # 1. Insert DispatchLog
    disp_log = DispatchLog(
        slot_id=payload.slot_id,
        asin=clean_asin,
        channel=payload.channel,
        audience=payload.audience,
        subtag=subtag,
        status="sent",
    )
    session.add(disp_log)

    # 2. Log DealClick so click counter and activity feed update immediately
    click = DealClick(
        asin=clean_asin,
        channel=payload.channel,
        subtag=subtag,
        target_url=target_url,
        referrer=f"{payload.channel}_auto_dispatch",
        user_agent=f"[mobile_android:{payload.channel}] LeadForge Dispatch Queue Auto-Log",
    )
    session.add(click)

    await session.commit()
    logger.info(f"Marked deal slot {payload.slot_id} sent for {clean_asin} on {payload.channel} (subtag={subtag})")

    return {
        "success": True,
        "slot_id": payload.slot_id,
        "asin": clean_asin,
        "channel": payload.channel,
        "audience": payload.audience,
        "subtag": subtag,
        "target_url": target_url,
        "dispatched_at": disp_log.dispatched_at.isoformat(),
    }


@router.get("/dispatch-queue")
async def get_dispatch_queue(session: AsyncSession = Depends(get_db)):
    """
    Phase 1 & Phase 2 Distribution Queue:
    Returns today's 3 scheduled deals (Morning Hero, Evening Impulse, Scarcity Nudge)
    with 4 audience copy variants, Evolution API / Telegram payloads, and persistent sent status.
    """
    all_deals = await fetch_live_deals()
    promoted = [d for d in all_deals if evaluate_deal_quality(d).get("verdict") == "PROMOTE"]
    if not promoted:
        promoted = all_deals[:5]

    morning_deal = max(promoted, key=lambda d: float(d.get("effective_price") or 0)) if promoted else all_deals[0]
    impulse_candidates = [d for d in promoted if float(d.get("effective_price") or 9999) <= 999] or promoted
    evening_deal = min(impulse_candidates, key=lambda d: float(d.get("effective_price") or 9999))
    scarcity_deal = max(promoted, key=lambda d: int(d.get("discount_pct") or 0))

    d_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    # Check today's dispatch logs
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    dispatch_stmt = select(DispatchLog).where(DispatchLog.dispatched_at >= today_start)
    logged_dispatches = (await session.execute(dispatch_stmt)).scalars().all()
    sent_slots = {log.slot_id: log for log in logged_dispatches}

    # Fetch historical clicks by ASIN for loot feedback loop
    clicks_stmt = select(DealClick.asin, func.count(DealClick.id)).group_by(DealClick.asin)
    asin_clicks_map = dict((await session.execute(clicks_stmt)).all())

    def build_slot_data(slot_id: str, slot_name: str, timing: str, delay_info: str, deal: Dict[str, Any]):
        asin = deal.get("asin") or extract_asin(deal.get("affiliate_url", "")) or "B09W2GFM7Y"
        log_item = sent_slots.get(slot_id)
        is_sent = log_item is not None
        hist_clicks = asin_clicks_map.get(asin.upper(), 0)

        loot = compute_loot_score(deal, historical_clicks=hist_clicks, is_previously_dispatched=is_sent)
        quality = evaluate_deal_quality(deal)
        freshness = quality.get("freshness_safety")
        price = float(deal.get("effective_price") or deal.get("list_price") or 499.0)
        mrp = float(deal.get("mrp") or (price * 1.5))
        disc = int(deal.get("discount_pct") or 40)
        comm = compute_commission_estimate(deal.get("category", "General"), price)

        aud_wa = generate_all_audience_variants(deal, channel="whatsapp")
        aud_tg = generate_all_audience_variants(deal, channel="telegram")

        log_item = sent_slots.get(slot_id)
        is_sent = log_item is not None

        subtag = f"lf-wa-{d_str}-{asin.lower()[:10]}-{slot_id[:2]}"

        evo_payload = {
            "number": "120363028392819283@g.us",
            "text": aud_wa["variants"]["homemaker"]["message"],
            "options": {"delay": 1500, "presence": "composing", "linkPreview": True},
        }

        tg_payload = {
            "chat_id": "@dealsforindia",
            "text": aud_tg["variants"]["budget_impulse"]["message"],
            "parse_mode": "Markdown",
        }

        return {
            "slot_id": slot_id,
            "slot_name": slot_name,
            "timing_ist": timing,
            "delay_info": delay_info,
            "asin": asin,
            "title": deal.get("title") or "Amazon Deal",
            "category": deal.get("category", "Home & Kitchen"),
            "deal_price": price,
            "mrp": mrp,
            "discount_pct": disc,
            "rating": float(deal.get("rating") or 4.3),
            "review_count": int(deal.get("review_count") or 3500),
            "commission_rate_percent": comm["commission_rate_percent"],
            "estimated_commission_rupees": comm["estimated_commission_rupees"],
            "loot_score": loot["loot_score"],
            "loot_badge": loot["loot_badge"],
            "is_mega_loot": loot["is_mega_loot"],
            "loot_info": loot,
            "historical_clicks": hist_clicks,
            "quality_verdict": quality.get("verdict", "PROMOTE"),
            "why_it_converts": quality.get("why_it_converts", ""),
            "freshness_safety": freshness,
            "unique_subtag": subtag,
            "canonical_affiliate_url": to_canonical_affiliate_url(asin, subtag=subtag),
            "audience_variants_whatsapp": aud_wa["variants"],
            "audience_variants_telegram": aud_tg["variants"],
            "evolution_api_payload": evo_payload,
            "telegram_payload": tg_payload,
            "is_sent": is_sent,
            "dispatched_at": log_item.dispatched_at.isoformat() if log_item and log_item.dispatched_at else None,
            "sent_channel": log_item.channel if log_item else None,
            "sent_audience": log_item.audience if log_item else None,
        }

    slots = [
        build_slot_data("s1_morning", "☀️ Slot 1: Morning Hero Drop", "08:30 – 10:30 IST", "Immediate blast (0h delay)", morning_deal),
        build_slot_data("s2_evening", "🌙 Slot 2: Evening Impulse (<₹499)", "18:30 – 20:30 IST", "+10h delay", evening_deal),
        build_slot_data("s3_scarcity", "⚡ Slot 3: Scarcity Closer", "21:30 – 23:00 IST", "Conditional (+26h delay)", scarcity_deal),
    ]

    return {
        "status": "success",
        "date": d_str,
        "queue_count": len(slots),
        "slots": slots,
    }


@router.get("/outbox/daily")
async def get_daily_deals_outbox():
    """
    Instantly-Style Daily Cadence Outbox:
    Returns today's 3-slot deal lineup ready for 1-click execution:
      - Slot 1: Morning Hero Drop (08:30 IST)
      - Slot 2: Evening Impulse Under ₹499 (18:30 IST)
      - Slot 3: Scarcity & Price Bounce Closer (21:30 IST)
    """
    all_deals = await fetch_live_deals()
    promoted = [d for d in all_deals if evaluate_deal_quality(d).get("verdict") == "PROMOTE"]
    if not promoted:
        promoted = all_deals[:5]

    morning_deal = max(promoted, key=lambda d: float(d.get("effective_price") or 0)) if promoted else all_deals[0]
    impulse_candidates = [d for d in promoted if float(d.get("effective_price") or 9999) <= 999] or promoted
    evening_deal = min(impulse_candidates, key=lambda d: float(d.get("effective_price") or 9999))
    scarcity_deal = max(promoted, key=lambda d: int(d.get("discount_pct") or 0))

    return {
        "status": "success",
        "schedule_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "cadence": {
            "morning_hero": {
                "slot": "08:30 – 10:30 IST",
                "deal_title": morning_deal.get("title"),
                "asin": morning_deal.get("asin"),
                "deal": morning_deal,
                "step": generate_3step_sequence(morning_deal)["step1_morning"],
            },
            "evening_impulse": {
                "slot": "18:30 – 20:30 IST",
                "deal_title": evening_deal.get("title"),
                "asin": evening_deal.get("asin"),
                "deal": evening_deal,
                "step": generate_3step_sequence(evening_deal)["step2_evening"],
            },
            "scarcity_closer": {
                "slot": "21:30 – 23:00 IST",
                "deal_title": scarcity_deal.get("title"),
                "asin": scarcity_deal.get("asin"),
                "deal": scarcity_deal,
                "step": generate_3step_sequence(scarcity_deal)["step3_followup"],
            },
        },
    }
