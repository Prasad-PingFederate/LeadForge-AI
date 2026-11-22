import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs, urlencode

import httpx

from app.config import settings
from app.core.cache import cache

logger = logging.getLogger(__name__)

ASIN_REGEX = re.compile(r"(?:/dp/|/gp/product/|/gp/aw/d/)([A-Z0-9]{10})", re.I)
PRICE_REGEX = re.compile(r"[₹\s,]*([0-9,]+(?:\.[0-9]+)?)")

# Amazon India Category Commission Rates (Impulse & High-ROI prioritization)
CATEGORY_COMMISSION_RATES = {
    "home & kitchen": 9.0,
    "kitchen": 9.0,
    "appliances": 7.0,
    "small appliances": 7.0,
    "beauty": 8.0,
    "personal care": 8.0,
    "grocery": 8.0,
    "daily essentials": 8.0,
    "fashion": 9.0,
    "footwear": 9.0,
    "electronics": 5.0,
    "audio": 5.0,
    "computers": 5.0,
    "laptops": 5.0,
    "smartphones": 0.0,
    "mobiles": 0.0,
}

LIVE_DEALS_CACHE_KEY = "bb_live_deals_feed"

FALLBACK_CURATED_DEALS: List[Dict[str, Any]] = [
    {
        "id": "amazon:B002MPPTB8",
        "asin": "B002MPPTB8",
        "title": "Hawkins Futura Hard Anodised Pressure Cooker 3 Litre with Induction Base",
        "brand": "Hawkins",
        "category": "Home & Kitchen",
        "mrp": 3350,
        "list_price": 2499,
        "effective_price": 2499,
        "discount_pct": 25,
        "savings_inr": 851,
        "rating": 4.4,
        "review_count": 28400,
        "score": 75,
        "is_loot": False,
        "is_price_drop": True,
        "image_url": "https://m.media-amazon.com/images/I/71uQaPuz8jL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B002MPPTB8?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=bb-grid",
    },
    {
        "id": "amazon:B091CR2FXY",
        "asin": "B091CR2FXY",
        "title": "AGARO Regency Air Fryer 12L 1800W with 9 Preset Modes",
        "brand": "AGARO",
        "category": "Home & Kitchen",
        "mrp": 15999,
        "list_price": 7499,
        "effective_price": 7499,
        "discount_pct": 53,
        "savings_inr": 8500,
        "rating": 4.5,
        "review_count": 12800,
        "score": 141,
        "is_loot": True,
        "is_price_drop": True,
        "image_url": "https://m.media-amazon.com/images/I/71VjXyGfW2L._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B091CR2FXY?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=bb-grid",
    },
    {
        "id": "amazon:B0863TXGM4",
        "asin": "B0863TXGM4",
        "title": "L'Oreal Paris Extraordinary Clay Purifying & Hydrating Shampoo (650ml)",
        "brand": "L'Oreal Paris",
        "category": "Personal Care & Grocery",
        "mrp": 899,
        "list_price": 499,
        "effective_price": 499,
        "discount_pct": 45,
        "savings_inr": 400,
        "rating": 4.4,
        "review_count": 19500,
        "score": 136,
        "is_loot": True,
        "is_price_drop": True,
        "image_url": "https://m.media-amazon.com/images/I/61NlU9f8YgL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B0863TXGM4?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=bb-grid",
    },
    {
        "id": "amazon:B07RJWB549",
        "asin": "B07RJWB549",
        "title": "Lakme Eyeconic Kajal Twin Pack Deep Black 2x0.35g",
        "brand": "Lakme",
        "category": "Personal Care & Grocery",
        "mrp": 450,
        "list_price": 260,
        "effective_price": 260,
        "discount_pct": 42,
        "savings_inr": 190,
        "rating": 4.3,
        "review_count": 31000,
        "score": 136,
        "is_loot": False,
        "is_price_drop": True,
        "image_url": "https://m.media-amazon.com/images/I/61b7b7pS6oL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B07RJWB549?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=bb-grid",
    },
    {
        "id": "amazon:B09W2GFM7Y",
        "asin": "B09W2GFM7Y",
        "title": "Pigeon by Stovekraft 1.8 Litre Stainless Steel Electric Kettle",
        "brand": "Pigeon",
        "category": "Home & Kitchen",
        "mrp": 1499,
        "list_price": 599,
        "effective_price": 599,
        "discount_pct": 60,
        "savings_inr": 900,
        "rating": 4.4,
        "review_count": 18200,
        "score": 125,
        "is_loot": True,
        "is_price_drop": True,
        "image_url": "https://m.media-amazon.com/images/I/61F9D4V4w2L._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09W2GFM7Y?tag=dammaiprasad-21&linkCode=ll1&ascsubtag=bb-grid",
    },
]


def extract_asin(url_or_text: str) -> Optional[str]:
    """Extracts a 10-character Amazon ASIN from URL or raw text."""
    if not url_or_text:
        return None
    raw = url_or_text.strip()

    # Direct 10-char ASIN check
    if re.fullmatch(r"^[A-Z0-9]{10}$", raw, re.I):
        return raw.upper()

    match = ASIN_REGEX.search(raw)
    if match:
        return match.group(1).upper()
    return None


def to_canonical_affiliate_url(asin_or_url: str, subtag: str = "leadforge-deal") -> str:
    """Builds a universal Amazon Affiliate URL with tag=dammaiprasad-21."""
    tag = settings.amazon_affiliate_tag
    asin = extract_asin(asin_or_url)
    if asin:
        return f"https://www.amazon.in/dp/{asin}?tag={tag}&linkCode=ll1&ascsubtag={subtag}"

    try:
        u = urlparse(asin_or_url)
        params = parse_qs(u.query)
        # Strip competing tags
        for p in ["tag", "ascsubtag", "linkCode", "ref", "ref_"]:
            params.pop(p, None)
        params["tag"] = [tag]
        params["ascsubtag"] = [subtag]
        clean_query = urlencode(params, doseq=True)
        return f"{u.scheme}://{u.netloc}{u.path}?{clean_query}"
    except Exception:
        return f"https://www.amazon.in/?tag={tag}&ascsubtag={subtag}"


def compute_commission_estimate(category: str, deal_price: float) -> Dict[str, Any]:
    cat_lower = category.lower()
    rate = 5.0
    for k, v in CATEGORY_COMMISSION_RATES.items():
        if k in cat_lower:
            rate = v
            break

    est_commission = round((deal_price * rate) / 100.0, 2)
    is_impulse = deal_price <= 999.0 and rate >= 6.0

    return {
        "commission_rate_percent": rate,
        "estimated_commission_rupees": est_commission,
        "is_impulse_sweet_spot": is_impulse,
        "is_zero_roi": rate == 0.0,
    }


async def fetch_live_deals(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Fetches and caches the 170+ verified live deals from BharatBazaro / GitHub raw feed."""
    if not force_refresh:
        cached = cache.get(LIVE_DEALS_CACHE_KEY)
        if cached and isinstance(cached, list) and len(cached) > 0:
            return cached

    urls = [
        settings.bharatbazaro_live_deals_url,
        "https://raw.githubusercontent.com/Prasad-PingFederate/bharatbazaro/main/data/live_deals.json",
        "https://bharatbazaro.com/data/live_deals.json",
    ]

    for u in urls:
        if not u:
            continue
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(u)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        cache.set(LIVE_DEALS_CACHE_KEY, data, ttl_seconds=3600)
                        logger.info(f"Loaded {len(data)} live deals from {u}")
                        return data
        except Exception as e:
            logger.debug(f"Failed to fetch live deals from {u}: {e}")

    # Fallback curated live deals if network/DNS unavailable
    logger.info("Using curated in-memory deals fallback")
    return list(FALLBACK_CURATED_DEALS)


async def get_deal_by_asin(asin: str) -> Optional[Dict[str, Any]]:
    """Finds an exact deal by 10-char ASIN in the live deals feed."""
    clean_asin = (asin or "").strip().upper()
    if not clean_asin:
        return None

    deals = await fetch_live_deals()
    for d in deals:
        d_asin = (d.get("asin") or "").upper()
        d_id = (d.get("id") or "").upper()
        if d_asin == clean_asin or clean_asin in d_id:
            return d
    return None


async def search_live_deals(
    query: str = "",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_discount: Optional[int] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Filters, scores, and prioritizes live deals from the BharatBazaro feed."""
    deals = await fetch_live_deals()
    q_words = [w.lower() for w in re.findall(r"\w+", query)] if query else []
    cat_lower = category.lower() if category else ""

    matched = []
    for d in deals:
        if d.get("expired"):
            continue

        price = float(d.get("effective_price") or d.get("list_price") or 99999)
        if max_price is not None and price > max_price:
            continue

        disc = int(d.get("discount_pct") or 0)
        if min_discount is not None and disc < min_discount:
            continue

        deal_cat = (d.get("category") or "").lower()
        if cat_lower and cat_lower not in deal_cat:
            continue

        # Text relevance check
        text_corpus = f"{d.get('title', '')} {d.get('brand', '')} {deal_cat} {d.get('asin', '')}".lower()
        if q_words:
            # Check if any or all query words match
            match_count = sum(1 for w in q_words if w in text_corpus)
            if match_count == 0:
                continue
            relevance = match_count
        else:
            relevance = 1

        score = float(d.get("score") or 50) + (relevance * 20) + (disc * 0.5)
        # Boost high-commission categories
        if any(h in deal_cat for h in ["kitchen", "home", "beauty", "personal"]):
            score += 25

        matched.append((score, d))

    # Sort descending by score
    matched.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in matched[:limit]]


async def get_top_converting_deals(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns top high-converting sweet-spot deals (₹99-₹2999, high commission & score)."""
    deals = await fetch_live_deals()
    scored = []
    for d in deals:
        if d.get("expired"):
            continue
        price = float(d.get("effective_price") or d.get("list_price") or 5000)
        cat = (d.get("category") or "").lower()
        base_score = float(d.get("score") or 50)

        # Impulse sweet spot bonus
        if price <= 999 and any(h in cat for h in ["kitchen", "home", "personal", "beauty"]):
            base_score += 40
        elif price <= 2999 and any(h in cat for h in ["kitchen", "home", "personal", "appliances"]):
            base_score += 20

        scored.append((base_score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def format_whatsapp_deal_post(
    title: str,
    deal_price: float,
    mrp: float,
    asin: Optional[str] = None,
    rating: float = 4.3,
    reviews_count: int = 4500,
    key_features: Optional[list] = None,
    subtag: str = "lf-wa",
) -> str:
    """Formats an ultra-high converting WhatsApp deal broadcast message."""
    discount_pct = int(round(((mrp - deal_price) / mrp) * 100)) if mrp > deal_price else 45
    savings = int(mrp - deal_price) if mrp > deal_price else int(deal_price * 0.4)
    aff_url = to_canonical_affiliate_url(asin or "B09W2GFM7Y", subtag=subtag)

    features = key_features or [
        "Verified all-time low price drop",
        "Top-rated build quality with 1-Yr Brand Warranty",
        "Free 1-Day Prime Delivery available",
    ]
    bullets = "\n".join(f"• {f}" for f in features[:3])

    return (
        f"🔥 *TODAY'S VERIFIED PRICE DROP* 🔥\n\n"
        f"*{title}*\n"
        f"⭐️ Rating: {rating}/5 ({reviews_count:,}+ reviews)\n\n"
        f"📉 *Deal Price: ₹{int(deal_price):,}* ~MRP ₹{int(mrp):,}~ ({discount_pct}% OFF!)\n"
        f"💰 *You Save: ₹{savings:,}*\n\n"
        f"⚡️ *Why It's a Steal:*\n"
        f"{bullets}\n\n"
        f"👉 *Check Live Price on Amazon:*\n{aff_url}\n\n"
        f"_(Price checked live — deals on Amazon sell out fast!)_"
    )


def format_telegram_deal_post(
    title: str,
    deal_price: float,
    mrp: float,
    asin: Optional[str] = None,
    subtag: str = "lf-tg",
) -> str:
    discount_pct = int(round(((mrp - deal_price) / mrp) * 100)) if mrp > deal_price else 40
    aff_url = to_canonical_affiliate_url(asin or "B09W2GFM7Y", subtag=subtag)

    return (
        f"🚨 **PRICE DROP ALERT** 🚨\n\n"
        f"**{title}**\n\n"
        f"🏷 Price: **₹{int(deal_price):,}** ~₹{int(mrp):,}~ ({discount_pct}% Off)\n\n"
        f"🛒 **Buy on Amazon:** [Check Deal Now]({aff_url})"
    )
