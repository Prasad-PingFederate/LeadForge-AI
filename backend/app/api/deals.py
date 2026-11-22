import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

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
    limit: int = Query(15, ge=1, le=100),
    force_refresh: bool = Query(False, description="Bypass cache and re-fetch from upstream"),
):
    """Returns verified live deals from BharatBazaro with commission estimates."""
    if force_refresh:
        all_deals = await fetch_live_deals(force_refresh=True)
    else:
        all_deals = await fetch_live_deals()

    if query or category or max_price is not None or min_discount is not None:
        matched = await search_live_deals(
            query=query or "",
            category=category,
            max_price=max_price,
            min_discount=min_discount,
            limit=limit,
        )
    else:
        matched = all_deals[:limit]

    # Enrich with canonical affiliate link, commission info, and quality verdict
    enriched_deals = []
    for d in matched:
        asin = d.get("asin") or ""
        cat = d.get("category", "General")
        price = float(d.get("effective_price") or d.get("list_price") or 599.0)
        comm = compute_commission_estimate(cat, price)
        quality = evaluate_deal_quality(d)
        where_to_post = generate_where_to_post_recommendations(cat, price, d.get("title", ""))

        enriched_deals.append({
            **d,
            "canonical_affiliate_url": to_canonical_affiliate_url(asin, subtag="bb-api"),
            "commission_info": comm,
            "quality_verdict": quality,
            "where_to_post": where_to_post,
        })

    return {
        "count": len(enriched_deals),
        "total_available": len(all_deals),
        "source": settings.bharatbazaro_live_deals_url,
        "deals": enriched_deals,
    }


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

    return {
        **deal,
        "canonical_affiliate_url": to_canonical_affiliate_url(deal.get("asin", asin), subtag="bb-api-detail"),
        "commission_info": comm,
        "quality_verdict": quality,
        "where_to_post": where_to_post,
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
            "commission_rate_percent": comm["commission_rate_percent"],
            "estimated_commission_rupees": comm["estimated_commission_rupees"],
            "rating": rating,
            "review_count": reviews,
        })

        if len(exported) >= limit:
            break

    return {
        "status": "success",
        "count": len(exported),
        "target_affiliate_tag": settings.amazon_affiliate_tag,
        "deals": exported,
    }
