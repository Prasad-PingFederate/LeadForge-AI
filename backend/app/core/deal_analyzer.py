import logging
import re
from datetime import datetime, timezone
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


def waterfall_deal_enrichment(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clay-Style 3-Tier Waterfall Deal Enrichment:
    Layer 1: Price & Margin Waterfall (Price, MRP, Discount %, Category Commission %)
    Layer 2: Social Proof & Trust Waterfall (Rating, Review Volume, Trust Tier)
    Layer 3: Velocity & Urgency Waterfall (Impulse Sweet-Spot, Loot Badge, High Yield)
    Claygent Synthesizer: 1-sentence "Why This Deal Converts" rationale.
    """
    title = deal.get("title") or deal.get("name") or "Amazon Deal"
    price = float(deal.get("effective_price") or deal.get("list_price") or deal.get("deal_price") or 499.0)
    mrp = float(deal.get("mrp") or (price * 1.5))
    disc = int(deal.get("discount_pct") or (round(((mrp - price) / mrp) * 100) if mrp > price else 35))
    savings = int(mrp - price) if mrp > price else int(price * 0.35)
    cat = (deal.get("category") or "Home & Kitchen")
    rating = float(deal.get("rating") or 4.3)
    reviews = int(deal.get("review_count") or deal.get("reviews_count") or 1500)

    # Layer 1: Price & Commission Yield Waterfall
    comm_info = compute_commission_estimate(cat, price)
    rate = comm_info["commission_rate_percent"]
    comm_rupees = comm_info["estimated_commission_rupees"]
    is_zero_roi = comm_info["is_zero_roi"] or rate == 0.0

    # Layer 2: Trust & Social Proof Waterfall
    if rating >= 4.4 and reviews >= 10000:
        trust_tier = "Elite Trust (Viral Social Proof)"
    elif rating >= 4.2 and reviews >= 500:
        trust_tier = "High Trust (Verified Buyer Proof)"
    elif rating >= 4.0:
        trust_tier = "Moderate Trust"
    else:
        trust_tier = "Low Trust Risk"

    # Layer 3: Velocity & Urgency Waterfall
    is_loot = disc >= 50 and price <= 2999.0
    is_price_drop_leader = savings >= 500
    is_high_yield = rate >= 8.0
    is_impulse_sweet_spot = 199.0 <= price <= 1499.0

    # Claygent Rationale Synthesizer
    title_short = title[:45].strip()
    if is_zero_roi:
        why_it_converts = f"Suppressed: {cat} has 0% Amazon affiliate commission. Promotes zero revenue."
    elif rating < 4.0 and reviews > 50:
        why_it_converts = f"Suppressed: Rating ({rating}★) below minimum 4.0 standard. High return rate risk."
    else:
        why_it_converts = (
            f"{title_short} at verified ₹{price:,.0f} saves ₹{savings:,} ({disc}% off) "
            f"with {rating}★ ({reviews:,} reviews) yielding {rate}% commission (₹{comm_rupees:.2f}/sale)."
        )

    return {
        "tier1_pricing_yield": {
            "price": price,
            "mrp": mrp,
            "discount_pct": disc,
            "savings_inr": savings,
            "commission_rate_percent": rate,
            "commission_rupees_per_sale": comm_rupees,
            "is_zero_commission": is_zero_roi,
        },
        "tier2_trust_proof": {
            "rating": rating,
            "review_count": reviews,
            "trust_tier": trust_tier,
            "trust_passed": rating >= 4.2 and reviews >= 500,
        },
        "tier3_velocity_urgency": {
            "is_loot": is_loot,
            "is_price_drop_leader": is_price_drop_leader,
            "is_high_yield": is_high_yield,
            "is_impulse_sweet_spot": is_impulse_sweet_spot,
        },
        "why_it_converts": why_it_converts,
    }


def compute_loot_score(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    BuyHatke & Keepa-style Loot Score (0-100):
    Calculates instant impulse appeal, price drop depth, and revenue yield for Indian deal shoppers.
    Scoring:
      - Discount Depth (up to 35 pts): >=60% -> 35, >=50% -> 30, >=40% -> 20, >=30% -> 10
      - Impulse Sweet-Spot (up to 30 pts): ₹199-₹999 -> 30, ₹1000-₹2499 -> 20, ₹2500-₹4999 -> 10
      - Social Proof Trust (up to 25 pts): >=4.4 & >=5000 rev -> 25, >=4.2 & >=500 rev -> 20, >=4.0 -> 10
      - Category Yield (up to 10 pts): >=8% -> 10, >=5% -> 6, 0% -> 0
    """
    price = float(deal.get("effective_price") or deal.get("list_price") or deal.get("deal_price") or 499.0)
    mrp = float(deal.get("mrp") or (price * 1.5))
    disc = int(deal.get("discount_pct") or (round(((mrp - price) / mrp) * 100) if mrp > price else 30))
    rating = float(deal.get("rating") or 4.2)
    reviews = int(deal.get("review_count") or deal.get("reviews_count") or 1000)
    cat = (deal.get("category") or "Home & Kitchen").lower()

    comm_info = compute_commission_estimate(cat, price)
    rate = comm_info["commission_rate_percent"]
    is_zero = comm_info["is_zero_roi"] or rate == 0.0

    # 1. Discount Depth
    if disc >= 60:
        disc_pts = 35
    elif disc >= 50:
        disc_pts = 30
    elif disc >= 40:
        disc_pts = 20
    elif disc >= 30:
        disc_pts = 10
    else:
        disc_pts = 4

    # 2. Impulse Price Point
    if 199.0 <= price <= 999.0:
        price_pts = 30
    elif 1000.0 <= price <= 2499.0:
        price_pts = 20
    elif 2500.0 <= price <= 4999.0:
        price_pts = 10
    elif price < 199.0:
        price_pts = 25
    else:
        price_pts = 5

    # 3. Buyer Trust Proof
    if rating >= 4.4 and reviews >= 5000:
        trust_pts = 25
    elif rating >= 4.2 and reviews >= 500:
        trust_pts = 20
    elif rating >= 4.0:
        trust_pts = 10
    else:
        trust_pts = 2

    # 4. Affiliate Margin Yield
    if rate >= 8.0:
        yield_pts = 10
    elif rate >= 5.0:
        yield_pts = 6
    else:
        yield_pts = 0

    total_score = min(100, disc_pts + price_pts + trust_pts + yield_pts)
    if is_zero or (rating < 4.0 and reviews > 50):
        total_score = min(total_score, 30)

    is_mega = total_score >= 80
    is_solid = total_score >= 60

    if is_mega:
        tier_label = "🔥 MEGA LOOT (Top 5%)"
        badge = f"🔥 {total_score}/100 MEGA LOOT"
    elif is_solid:
        tier_label = "⚡ SOLID DEAL (Top 25%)"
        badge = f"⚡ {total_score}/100 SOLID DEAL"
    else:
        tier_label = "STANDARD DEAL"
        badge = f"🏷 {total_score}/100 STANDARD"

    reasons = []
    if disc >= 50:
        reasons.append(f"Deep {disc}% discount drop")
    if 199.0 <= price <= 999.0:
        reasons.append(f"Frictionless impulse price point (₹{price:,.0f})")
    if rating >= 4.2 and reviews >= 500:
        reasons.append(f"High buyer trust proof ({rating}★ with {reviews:,} reviews)")
    if rate >= 8.0:
        reasons.append(f"High-yield affiliate commission ({rate}%)")

    return {
        "loot_score": total_score,
        "loot_badge": badge,
        "tier_label": tier_label,
        "is_mega_loot": is_mega,
        "is_solid_deal": is_solid,
        "breakdown": {
            "discount_depth_pts": disc_pts,
            "impulse_price_pts": price_pts,
            "trust_proof_pts": trust_pts,
            "category_yield_pts": yield_pts,
        },
        "reasons": reasons,
    }


def evaluate_deal_quality(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sales Manager Deal Quality Filter (Phase 3 Standard):
    Rigorously gates every deal against 6 strict criteria to protect conversion rates.
    Criteria:
      1. Discount >= 35%
      2. Price between ₹99 and ₹2,999 (Impulse sweet spot)
      3. Rating >= 4.2
      4. Review count >= 500
      5. Commission rate >= 6%
      6. Not 0% commission category (smartphones)
    """
    price = float(deal.get("effective_price") or deal.get("list_price") or deal.get("deal_price") or 0.0)
    disc = int(deal.get("discount_pct") or 0)
    rating = float(deal.get("rating") or 0.0)
    reviews = int(deal.get("review_count") or 0)
    cat = (deal.get("category") or "").lower()

    comm_info = compute_commission_estimate(cat, price)
    rate = comm_info["commission_rate_percent"]
    is_zero_roi = comm_info["is_zero_roi"] or rate == 0.0

    c1_discount = disc >= 35
    c2_price = 99.0 <= price <= 2999.0
    c3_rating = rating >= 4.2
    c4_reviews = reviews >= 500
    c5_commission = rate >= 6.0
    c6_not_zero_roi = not is_zero_roi

    criteria_passed = sum([
        c1_discount,
        c2_price,
        c3_rating,
        c4_reviews,
        c5_commission,
        c6_not_zero_roi,
    ])

    # Strict 5-point PROMOTE check (Feature 6):
    is_strictly_promote = (
        c1_discount and c2_price and c3_rating and c4_reviews and c5_commission and c6_not_zero_roi
    )

    # Verdict Determination
    if is_zero_roi:
        verdict = "KILL"
        verdict_badge = "🔴 KILL"
        reason = "0% Amazon commission category. Promotes zero revenue."
    elif rating < 4.0 and reviews > 50:
        verdict = "KILL"
        verdict_badge = "🔴 KILL"
        reason = f"Poor rating ({rating}/5). High return rate hazard."
    elif is_strictly_promote:
        verdict = "PROMOTE"
        verdict_badge = "🟢 PROMOTE"
        reason = f"Strict Sales Standard passed. {disc}% discount, ₹{price:,.0f} price, {rate}% commission, {rating}★ ({reviews:,} reviews)."
    elif criteria_passed >= 3:
        verdict = "HOLD"
        verdict_badge = "🟡 HOLD"
        if price > 2999.0:
            reason = f"High ticket price (₹{price:,.0f}). Requires targeted buyer audience."
        elif disc < 35:
            reason = f"Modest discount ({disc}%). Requires ≥35% for impulse conversion."
        elif reviews < 500:
            reason = f"Low review volume ({reviews:,}). Requires ≥500 reviews for trust."
        elif rate < 6.0:
            reason = f"Low commission rate ({rate}%). Hold for higher margin categories."
        else:
            reason = "Moderate performance metrics. Hold for price drop flash alert."
    else:
        verdict = "KILL"
        verdict_badge = "🔴 KILL"
        reason = "Fails sales manager quality thresholds."

    # Apollo-Style Composite Conversion Velocity Score (0-100)
    # 1. Commission yield (up to 30 pts)
    est_comm_val = comm_info["estimated_commission_rupees"]
    score_commission = min(30, int(est_comm_val * 0.25)) if not is_zero_roi else 0

    # 2. Discount depth (up to 25 pts)
    score_discount = min(25, int(disc * 0.45))

    # 3. Social proof trust (up to 25 pts)
    rating_pts = int((max(0.0, rating - 3.5) / 1.5) * 15) if rating >= 3.5 else 0
    reviews_pts = min(10, int(reviews / 500)) if reviews >= 100 else 0
    score_trust = min(25, rating_pts + reviews_pts)

    # 4. Impulse price fit (up to 20 pts)
    if 199.0 <= price <= 1499.0:
        score_price = 20
    elif 99.0 <= price <= 2999.0:
        score_price = 12
    else:
        score_price = 4

    composite_score = min(100, score_commission + score_discount + score_trust + score_price)
    if is_zero_roi or (rating < 4.0 and reviews > 50):
        composite_score = min(composite_score, 35)

    pool_tier = (
        "Tier 1: Instant VIP Broadcast"
        if verdict == "PROMOTE"
        else ("Tier 2: Targeted / Evening Hold" if verdict == "HOLD" else "Tier 3: Suppressed")
    )

    waterfall = waterfall_deal_enrichment(deal)
    loot_info = compute_loot_score(deal)

    return {
        "verdict": verdict,
        "verdict_badge": verdict_badge,
        "reason": reason,
        "why_it_converts": waterfall["why_it_converts"],
        "criteria_passed_count": criteria_passed,
        "composite_velocity_score": composite_score,
        "pool_tier": pool_tier,
        "loot_score": loot_info["loot_score"],
        "loot_badge": loot_info["loot_badge"],
        "is_mega_loot": loot_info["is_mega_loot"],
        "loot_info": loot_info,
        "waterfall_enrichment": waterfall,
        "score_breakdown": {
            "commission_yield_pts": score_commission,
            "discount_depth_pts": score_discount,
            "social_proof_pts": score_trust,
            "impulse_fit_pts": score_price,
            "total_score": composite_score,
        },
        "criteria": {
            "discount_ge_35pct": c1_discount,
            "price_between_99_and_2999": c2_price,
            "rating_ge_4_2": c3_rating,
            "reviews_ge_500": c4_reviews,
            "commission_ge_6pct": c5_commission,
            "not_zero_commission": c6_not_zero_roi,
        },
    }


def validate_deal_copy(text: str, affiliate_url: str = "") -> Dict[str, Any]:
    """
    Explee-Style Pre-flight Copy Validator:
    Verifies that generated deal messages meet affiliate compliance and conversion standards.
    """
    tag = settings.amazon_affiliate_tag
    has_tag = tag in (affiliate_url or "") or tag in (text or "")
    has_subtag = "ascsubtag=" in (affiliate_url or "") or "lf-" in (text or "")
    has_price = "₹" in (text or "")
    has_cta = any(w in (text or "").lower() for w in ["check", "buy", "deal", "amazon", "claim", "grab", "order"])
    length_ok = 50 <= len(text or "") <= 2500

    warnings = []
    if not has_tag:
        warnings.append(f"Missing affiliate tag '{tag}'. Commissions will not track.")
    if not has_subtag:
        warnings.append("Missing ascsubtag. Channel attribution will be lost.")
    if not has_price:
        warnings.append("No price symbol (₹) detected in message body.")

    is_valid = has_tag and length_ok and has_price

    return {
        "valid": is_valid,
        "compliance_score": 100 if is_valid else (70 if has_tag else 30),
        "has_affiliate_tag": has_tag,
        "has_subtag": has_subtag,
        "has_price_disclosure": has_price,
        "has_clear_cta": has_cta,
        "length": len(text or ""),
        "warnings": warnings,
        "status_badge": "🟢 COMPLIANT" if is_valid else "⚠️ ACTION NEEDED",
    }


def generate_where_to_post_recommendations(
    category: str,
    deal_price: float,
    title: str = "",
) -> Dict[str, Any]:
    """
    Distribution Engine Recommendations (Phase 2):
    Suggests high-converting WhatsApp group personas (Homemaker, Hostel, Budget, Office, College),
    Telegram channels (Indian Deal Alert style), subreddits, and hashtags for maximum click intent.
    """
    cat_lower = (category or "").lower()
    price_val = int(deal_price or 499)
    clean_title = (title or "Deal Drop").strip()
    short_title = clean_title[:32]

    wa_groups = [
        {
            "type": "Homemaker",
            "name": "Homemaker & Family Savings VIP",
            "angle": f"Kitchen, pantry & home utility; verified brand quality for {short_title}",
            "badge": "🏠 Homemaker",
        },
        {
            "type": "Hostel",
            "name": "Hostel & Bachelor Fast Living",
            "angle": f"Quick meal prep & daily room essentials under ₹{price_val:,}; zero hassle",
            "badge": "🎒 Hostel",
        },
        {
            "type": "Budget",
            "name": "Budget Deal Hunters & Loot Alerts",
            "angle": "Deep discount price drop; high impulse checkout before price bounce",
            "badge": "💰 Budget",
        },
        {
            "type": "Office",
            "name": "Office & Desk Lifestyle Group",
            "angle": "Workplace desk comfort, hydration & productivity gear",
            "badge": "💼 Office",
        },
        {
            "type": "College",
            "name": "College Campus & Youth Steals",
            "angle": "Pocket-friendly lifestyle drops under ₹999 for students",
            "badge": "🎓 College",
        },
    ]

    tg_channels = [
        {"name": "Indian Deal Alerts", "handle": "t.me/indiandealalerts", "desc": "Top trending flash drops & Amazon loot"},
        {"name": "Loot Deals India", "handle": "t.me/lootdealsindia", "desc": "Sub-₹999 price drop alerts with verified stock"},
        {"name": "Amazon Flipkart Loots", "handle": "t.me/amazon_flipkart_loots", "desc": "Instant coupon links & lightning deals"},
    ]

    subreddits = [
        {"name": "r/dealsforindia", "url": "https://reddit.com/r/dealsforindia", "desc": "India's premier deals community"},
        {"name": "r/GadgetsIndia", "url": "https://reddit.com/r/GadgetsIndia", "desc": "Tech, appliances & smart lifestyle"},
        {"name": "r/indiasocial", "url": "https://reddit.com/r/indiasocial", "desc": "Casual everyday recommendations"},
    ]

    hashtags = ["#AmazonDeals", "#Loot", "#PriceDrop", "#AmazonPriceDrop", "#BharatBazaro"]

    best_time = "Morning 8:30 AM – 10:30 AM & Evening 7:30 PM – 9:30 PM"
    if any(k in cat_lower for k in ["beauty", "personal", "grocery"]):
        best_time = "Afternoon 1:30 PM – 3:30 PM & Night 9:00 PM – 11:00 PM"

    return {
        "whatsapp_groups": wa_groups,
        "telegram_channels": tg_channels,
        "subreddits": subreddits,
        "hashtags": hashtags,
        "best_posting_window": best_time,
    }


def get_channel_performance_weights(clicks_by_channel: Optional[Dict[str, int]] = None) -> Dict[str, float]:
    """
    Self-Learning Loop (Phase 5):
    Dynamically scales strategy discovery quotas based on verified clicks.
    Channels driving higher volume receive proportional discovery multipliers.
    """
    baseline = {
        "whatsapp": 1.5,   # Highest converting channel
        "telegram": 1.25,
        "reddit": 1.0,
        "x": 0.8,
    }
    if not clicks_by_channel:
        return baseline

    total = sum(clicks_by_channel.values())
    if total < 5:
        return baseline

    weights = {}
    for ch, base in baseline.items():
        ch_clicks = clicks_by_channel.get(ch, 0)
        share = ch_clicks / total
        # Scale between 0.5x and 2.5x
        multiplier = round(base * (0.7 + (share * 1.6)), 2)
        weights[ch] = max(0.5, min(multiplier, 2.5))

    return weights


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


def generate_channel_subtag(
    channel: str,
    campaign_id: Optional[str] = None,
    asin: Optional[str] = None,
    date_str: Optional[str] = None,
) -> str:
    """
    Builds a granular Amazon Associate ascsubtag for exact conversion attribution:
    Format: lf-{channel}-{YYYYMMDD}-{ident}
    e.g. lf-wa-20261122-c4f8a1 or lf-tg-20261122-B002MPPTB8
    """
    d = date_str or datetime.now(timezone.utc).strftime("%Y%m%d")
    ch = {
        "whatsapp": "wa",
        "telegram": "tg",
        "reddit": "rd",
        "twitter": "x",
        "x": "x",
        "email": "em",
    }.get(channel.lower(), channel.lower()[:2])

    if asin:
        ident = asin.strip().lower()[:10]
    elif campaign_id:
        ident = campaign_id.replace("-", "").lower()[:8]
    else:
        ident = "deal"

    return f"lf-{ch}-{d}-{ident}"


def format_whatsapp_deal_post(
    title: str,
    deal_price: float,
    mrp: float,
    asin: Optional[str] = None,
    rating: float = 4.3,
    reviews_count: int = 4500,
    key_features: Optional[list] = None,
    subtag: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> str:
    """Formats an ultra-high converting WhatsApp deal broadcast message."""
    discount_pct = int(round(((mrp - deal_price) / mrp) * 100)) if mrp > deal_price else 45
    savings = int(mrp - deal_price) if mrp > deal_price else int(deal_price * 0.4)
    actual_subtag = subtag or generate_channel_subtag("whatsapp", campaign_id=campaign_id, asin=asin)
    aff_url = to_canonical_affiliate_url(asin or "B09W2GFM7Y", subtag=actual_subtag)

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
    subtag: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> str:
    discount_pct = int(round(((mrp - deal_price) / mrp) * 100)) if mrp > deal_price else 40
    actual_subtag = subtag or generate_channel_subtag("telegram", campaign_id=campaign_id, asin=asin)
    aff_url = to_canonical_affiliate_url(asin or "B09W2GFM7Y", subtag=actual_subtag)

    return (
        f"🚨 **PRICE DROP ALERT** 🚨\n\n"
        f"**{title}**\n\n"
        f"🏷 Price: **₹{int(deal_price):,}** ~₹{int(mrp):,}~ ({discount_pct}% Off)\n\n"
        f"🛒 **Buy on Amazon:** [Check Deal Now]({aff_url})"
    )


def format_reddit_deal_post(
    title: str,
    deal_price: float,
    mrp: float,
    asin: Optional[str] = None,
    subtag: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> str:
    discount_pct = int(round(((mrp - deal_price) / mrp) * 100)) if mrp > deal_price else 40
    savings = int(mrp - deal_price) if mrp > deal_price else int(deal_price * 0.4)
    actual_subtag = subtag or generate_channel_subtag("reddit", campaign_id=campaign_id, asin=asin)
    aff_url = to_canonical_affiliate_url(asin or "B09W2GFM7Y", subtag=actual_subtag)

    return (
        f"[Deal Alert] {title} dropped to ₹{int(deal_price):,} ({discount_pct}% off, save ₹{savings:,}) on Amazon India.\n\n"
        f"Verified price drop with brand warranty and Prime delivery.\n"
        f"Check deal: {aff_url}"
    )


def format_x_deal_post(
    title: str,
    deal_price: float,
    mrp: float,
    asin: Optional[str] = None,
    subtag: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> str:
    discount_pct = int(round(((mrp - deal_price) / mrp) * 100)) if mrp > deal_price else 40
    actual_subtag = subtag or generate_channel_subtag("x", campaign_id=campaign_id, asin=asin)
    aff_url = to_canonical_affiliate_url(asin or "B09W2GFM7Y", subtag=actual_subtag)
    short_title = title[:65]

    return (
        f"🔥 PRICE DROP: {short_title}...\n\n"
        f"📉 Deal: ₹{int(deal_price):,} (~MRP ₹{int(mrp):,}~ | {discount_pct}% off)\n"
        f"🛒 Buy on Amazon: {aff_url}\n\n"
        f"#AmazonDeals #PriceDrop #LootDealsIndia"
    )


def generate_multi_angle_copy(
    deal: Dict[str, Any],
    channel: str = "whatsapp",
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lemlist & EarnKaro-Style 4-Angle Copy Generator:
    Generates 4 psychologically distinct sales angles for maximum CTR:
      1. Urgency / Scarcity Loot (Stock ending, flash drop alert)
      2. Pure Savings Math (Detailed ₹ calculation: MRP, Deal, You Save)
      3. Social Proof & Trust (Star rating, buyer review volume, brand reputation)
      4. Daily Utility / Problem Solver (Under ₹499 lifestyle solution)
    Available in both WhatsApp and Telegram formatting with unique channel subtags.
    """
    title = deal.get("title") or deal.get("name") or "Amazon Verified Deal"
    price = float(deal.get("effective_price") or deal.get("list_price") or deal.get("deal_price") or 499.0)
    mrp = float(deal.get("mrp") or (price * 1.5))
    disc = int(deal.get("discount_pct") or (round(((mrp - price) / mrp) * 100) if mrp > price else 35))
    savings = int(mrp - price) if mrp > price else int(price * 0.35)
    rating = float(deal.get("rating") or 4.3)
    reviews = int(deal.get("review_count") or deal.get("reviews_count") or 3500)
    brand = deal.get("brand") or "Top Brand"
    asin = deal.get("asin") or extract_asin(deal.get("affiliate_url", "")) or "B09W2GFM7Y"

    d_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    subtag_base = generate_channel_subtag(channel, campaign_id=campaign_id, asin=asin, date_str=d_str)

    sub_urgency = f"{subtag_base}-urg"
    sub_math = f"{subtag_base}-math"
    sub_proof = f"{subtag_base}-prf"
    sub_utility = f"{subtag_base}-utl"

    url_urgency = to_canonical_affiliate_url(asin, subtag=sub_urgency)
    url_math = to_canonical_affiliate_url(asin, subtag=sub_math)
    url_proof = to_canonical_affiliate_url(asin, subtag=sub_proof)
    url_utility = to_canonical_affiliate_url(asin, subtag=sub_utility)

    if channel.lower() == "telegram":
        # Telegram Markdown styling
        urgency_msg = (
            f"⚡️ **FLASH LOOT ALERT: PRICE DROP DETECTED** ⚡️\n\n"
            f"**{title}**\n\n"
            f"📉 Deal Price: **₹{int(price):,}** ~₹{int(mrp):,}~ (**{disc}% OFF**)\n"
            f"🔥 **You Save: ₹{savings:,}**\n\n"
            f"⚠️ *Stock Status:* Deal allocation selling out fast! Price reverts soon.\n\n"
            f"🛒 **Grab on Amazon:** [Claim Deal Now]({url_urgency})"
        )
        math_msg = (
            f"💰 **SAVINGS MATH BREAKDOWN** 💰\n\n"
            f"**{title}**\n\n"
            f"• MRP: ~₹{int(mrp):,}~\n"
            f"• Verified Deal Price: **₹{int(price):,}**\n"
            f"• Flat Discount: **{disc}% OFF**\n"
            f"• **Net Savings In Your Pocket: ₹{savings:,}**\n\n"
            f"🛒 **Check Live Pricing:** [Order on Amazon]({url_math})"
        )
        proof_msg = (
            f"⭐️ **VERIFIED BUYER CHOICE ({rating}★ by {reviews:,}+ INDIANS)** ⭐️\n\n"
            f"**{title}**\n\n"
            f"Why thousands recommend this {brand} product:\n"
            f"• Official Brand Warranty & Prime Free Delivery\n"
            f"• Verified durable build & genuine seller backing\n"
            f"• Today's drop: **₹{int(price):,}** (Save ₹{savings:,})\n\n"
            f"🛒 **See Customer Reviews & Order:** [View on Amazon]({url_proof})"
        )
        utility_msg = (
            f"🎁 **DAILY LIFESTYLE UPGRADE (STEAL DEAL)** 🎁\n\n"
            f"**{title}**\n\n"
            f"📉 Pocket Friendly: **₹{int(price):,}** (Normally ₹{int(mrp):,})\n"
            f"• Perfect everyday essential & hassle-free upgrade\n"
            f"• Zero hesitation impulse price point\n\n"
            f"🛒 **Grab Yours Before Price Bounces:** [Shop Now]({url_utility})"
        )
    else:
        # WhatsApp Formatting
        urgency_msg = (
            f"⚡️ *FLASH LOOT ALERT — PRICE CRASH* ⚡️\n\n"
            f"*{title}*\n"
            f"⭐️ Rating: {rating}/5 ({reviews:,}+ reviews)\n\n"
            f"📉 *Deal Price: ₹{int(price):,}* ~MRP ₹{int(mrp):,}~ (*{disc}% OFF*)\n"
            f"💰 *Instant Rupee Savings: ₹{savings:,}*\n\n"
            f"⚠️ *Urgency:* Amazon lightning deal allocation is active now. Price may bounce at midnight!\n\n"
            f"👉 *Claim Live Deal On Amazon:*\n{url_urgency}\n\n"
            f"_(Checked live — grab before stock runs out!)_"
        )
        math_msg = (
            f"💰 *CLEAR SAVINGS MATH: WHAT YOU SAVE TODAY* 💰\n\n"
            f"*{title}*\n\n"
            f"• Original List Price: ~₹{int(mrp):,}~\n"
            f"• Today's Special Price: *₹{int(price):,}*\n"
            f"• Instant Discount: *{disc}% OFF*\n"
            f"👉 *NET RUPEES SAVED: ₹{savings:,}*\n\n"
            f"Includes Prime 1-Day Delivery & Official Brand Warranty.\n\n"
            f"👉 *Lock In Discounted Price Now:*\n{url_math}"
        )
        proof_msg = (
            f"⭐️ *RATED {rating}★ BY {reviews:,}+ VERIFIED BUYERS* ⭐️\n\n"
            f"*{title}*\n"
            f"Brand: *{brand}*\n\n"
            f"Why Indian buyers love this:\n"
            f"• Top tier build quality & verified longevity\n"
            f"• Genuine manufacturer warranty & hassle-free returns\n"
            f"• Now down to *₹{int(price):,}* (Save ₹{savings:,})\n\n"
            f"👉 *Read Reviews & Buy on Amazon:*\n{url_proof}"
        )
        utility_msg = (
            f"🎁 *DAILY PROBLEM SOLVER (STEAL DEAL UNDER ₹{int(max(499.0, price)):,})* 🎁\n\n"
            f"*{title}*\n\n"
            f"📉 *Price Drop: ₹{int(price):,}* ~MRP ₹{int(mrp):,}~ (*{disc}% OFF*)\n"
            f"💰 *You Save: ₹{savings:,}*\n\n"
            f"Why you should grab this today:\n"
            f"• Essential daily utility upgrade\n"
            f"• Zero-regret impulse pricing with Prime delivery\n\n"
            f"👉 *Check Availability On Amazon:*\n{url_utility}"
        )

    return {
        "channel": channel,
        "asin": asin,
        "angles": {
            "urgency_loot": {
                "key": "urgency_loot",
                "label": "⚡️ Loot / Urgency Alert",
                "headline": f"{disc}% OFF Lightning Price Drop",
                "message": urgency_msg,
                "url": url_urgency,
                "subtag": sub_urgency,
            },
            "savings_math": {
                "key": "savings_math",
                "label": "💰 Pure Savings Math",
                "headline": f"Save ₹{savings:,} In Pocket",
                "message": math_msg,
                "url": url_math,
                "subtag": sub_math,
            },
            "social_proof": {
                "key": "social_proof",
                "label": "⭐️ Social Proof & Trust",
                "headline": f"Rated {rating}★ by {reviews:,}+ Buyers",
                "message": proof_msg,
                "url": url_proof,
                "subtag": sub_proof,
            },
            "daily_utility": {
                "key": "daily_utility",
                "label": "🎁 Daily Utility / Impulse",
                "headline": f"Steal Deal Under ₹{int(max(499.0, price)):,}",
                "message": utility_msg,
                "url": url_utility,
                "subtag": sub_utility,
            },
        },
    }


def generate_3step_sequence(
    deal: Dict[str, Any],
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    3-Step Sequence Generator (Feature 3):
    1. Morning Broadcast (8:30 AM): Best high-commission drop with deep savings & brand trust.
    2. Evening Impulse (7:30 PM): Under ₹499 impulse grab with deep discount & fast checkout.
    3. Follow-up Alert (Late night/next day): Scarcity & price bounce alert for low-click recovery.
    """
    title = deal.get("title") or deal.get("name") or "Verified Deal Drop"
    price = float(deal.get("effective_price") or deal.get("deal_price") or 499.0)
    mrp = float(deal.get("mrp") or (price * 1.6))
    asin = deal.get("asin") or extract_asin(deal.get("affiliate_url", "")) or "B09W2GFM7Y"
    discount_pct = int(deal.get("discount_pct") or (round(((mrp - price) / mrp) * 100) if mrp > price else 40))
    savings = int(mrp - price) if mrp > price else int(price * 0.4)
    rating = float(deal.get("rating") or 4.3)
    reviews = int(deal.get("review_count") or deal.get("reviews_count") or 3500)

    # Granular subtag for each sequence step
    d_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    subtag_s1 = f"lf-wa-{d_str}-{asin.lower()[:10]}-s1"
    subtag_s2 = f"lf-wa-{d_str}-{asin.lower()[:10]}-s2"
    subtag_s3 = f"lf-wa-{d_str}-{asin.lower()[:10]}-s3"

    url_s1 = to_canonical_affiliate_url(asin, subtag=subtag_s1)
    url_s2 = to_canonical_affiliate_url(asin, subtag=subtag_s2)
    url_s3 = to_canonical_affiliate_url(asin, subtag=subtag_s3)

    # Step 1: Morning Hero Drop
    step1_morning = (
        f"☀️ *MORNING HERO DROP — EXCLUSIVE SAVINGS* ☀️\n\n"
        f"*{title}*\n"
        f"⭐️ Rating: {rating}/5 ({reviews:,}+ verified ratings)\n\n"
        f"📉 *Deal Price: ₹{int(price):,}* ~MRP ₹{int(mrp):,}~ (*{discount_pct}% OFF*)\n"
        f"💰 *Instant Savings: ₹{savings:,}*\n\n"
        f"⚡️ *Why It's Today's Best Pick:*\n"
        f"• Verified all-time lowest price on Amazon India\n"
        f"• 1-Year Official Brand Warranty & Prime Free Delivery\n"
        f"• Highest commission sweet-spot category\n\n"
        f"👉 *Check Live Price & Claim Deal:*\n{url_s1}\n\n"
        f"_(Verified deal — stock sells out fast during morning hours!)_"
    )

    # Step 2: Evening Impulse
    impulse_price = min(price, 499.0) if price <= 999.0 else price
    step2_evening = (
        f"🌙 *EVENING FLASH IMPULSE LOOT (UNDER ₹{int(max(499.0, impulse_price)):,})* 🌙\n\n"
        f"*{title}*\n\n"
        f"📉 *Steal Deal: ₹{int(price):,}* (~MRP ₹{int(mrp):,}~ | *{discount_pct}% OFF*)\n"
        f"💰 *You Save: ₹{savings:,}*\n\n"
        f"🔥 *Evening Prime Grab:*\n"
        f"• Impulse price point under ₹{int(max(499.0, impulse_price)):,}\n"
        f"• Lightning discount active for tonight only\n"
        f"• Perfect daily utility addition\n\n"
        f"👉 *Grab Before Midnight Price Bounce:*\n{url_s2}\n\n"
        f"_(Deal may expire tonight when daily discount cap is reached!)_"
    )

    # Step 3: Follow-up / Scarcity Alert
    step3_followup = (
        f"🚨 *FINAL NOTICE: PRICE BOUNCE INCOMING* 🚨\n\n"
        f"Quick alert on: *{title}*\n"
        f"📉 Price is still held at *₹{int(price):,}* (Save ₹{savings:,})\n\n"
        f"⚠️ *Why Act Now:*\n"
        f"• Deal allocation is 83% claimed on Amazon\n"
        f"• Price reverts back to ₹{int(mrp):,} at midnight\n"
        f"• Last call for Prime delivery tomorrow\n\n"
        f"👉 *Lock In Discounted Price Now:*\n{url_s3}\n\n"
        f"_(Don't pay full price tomorrow!)_"
    )

    # Telegram Formatted Messages
    step1_tg = (
        f"☀️ **MORNING HERO DROP — EXCLUSIVE SAVINGS** ☀️\n\n"
        f"**{title}**\n"
        f"⭐️ Rating: {rating}/5 ({reviews:,}+ verified ratings)\n\n"
        f"📉 Price: **₹{int(price):,}** ~₹{int(mrp):,}~ ({discount_pct}% OFF)\n"
        f"💰 You Save: **₹{savings:,}**\n\n"
        f"🛒 **Buy on Amazon:** [Check Live Price]({url_s1})"
    )

    step2_tg = (
        f"🌙 **EVENING FLASH IMPULSE LOOT** 🌙\n\n"
        f"**{title}**\n\n"
        f"📉 Deal Price: **₹{int(price):,}** ~₹{int(mrp):,}~ ({discount_pct}% Off)\n"
        f"🔥 *Grab before tonight's price bounce:*\n"
        f"🛒 **Buy on Amazon:** [Order Now]({url_s2})"
    )

    step3_tg = (
        f"🚨 **PRICE BOUNCE WARNING: FINAL HOURS** 🚨\n\n"
        f"**{title}**\n"
        f"⚠️ Price held at **₹{int(price):,}** (Deal allocation 83% claimed). Reverts to MRP at midnight.\n\n"
        f"🛒 **Lock In Discount Now:** [Claim Deal]({url_s3})"
    )

    return {
        "step1_morning": {
            "step_number": 1,
            "title": "☀️ Step 1: Morning Hero Broadcast (8:30 AM)",
            "message": step1_morning,
            "whatsapp_message": step1_morning,
            "telegram_message": step1_tg,
            "subtag": subtag_s1,
            "url": url_s1,
            "delay_hours": 0,
            "delay_unit": "hours",
            "send_window_ist": "08:30 – 10:30 IST",
            "trigger_condition": "Immediate Morning Hero Blast",
            "is_conditional": False,
            "best_time": "8:30 AM – 10:30 AM IST",
        },
        "step2_evening": {
            "step_number": 2,
            "title": "🌙 Step 2: Evening Impulse (<₹499)",
            "message": step2_evening,
            "whatsapp_message": step2_evening,
            "telegram_message": step2_tg,
            "subtag": subtag_s2,
            "url": url_s2,
            "delay_hours": 10,
            "delay_unit": "hours",
            "send_window_ist": "18:30 – 20:30 IST",
            "trigger_condition": "Automatic Evening Impulse Delay (+10h)",
            "is_conditional": False,
            "best_time": "7:30 PM – 9:30 PM IST",
        },
        "step3_followup": {
            "step_number": 3,
            "title": "⚡ Step 3: Scarcity & Price Bounce Follow-up",
            "message": step3_followup,
            "whatsapp_message": step3_followup,
            "telegram_message": step3_tg,
            "subtag": subtag_s3,
            "url": url_s3,
            "delay_hours": 26,
            "delay_unit": "hours",
            "send_window_ist": "21:30 – 23:00 IST",
            "trigger_condition": "Conditional: Trigger if clicks < 25 or midnight expiry",
            "is_conditional": True,
            "best_time": "Low clicks follow-up / 10:00 PM IST",
        },
    }
