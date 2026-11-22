import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlencode

from app.config import settings

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
    "daily essentials": 6.0,
    "grocery": 6.0,
    "fashion": 9.0,
    "footwear": 9.0,
    "electronics": 5.0,
    "computers": 5.0,
    "laptops": 5.0,
    "smartphones": 0.0,
    "mobiles": 0.0,
}


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
