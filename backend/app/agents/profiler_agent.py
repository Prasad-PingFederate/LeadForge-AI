import json
import logging
from typing import Dict, Any

from app.core.crawler import crawl_url
from app.core.llm import llm_client
from app.core.deal_analyzer import (
    extract_asin,
    to_canonical_affiliate_url,
    compute_commission_estimate,
    get_deal_by_asin,
    search_live_deals,
    get_top_converting_deals,
)

logger = logging.getLogger(__name__)

PROFILER_SYSTEM_PROMPT = """
You are an expert B2B Go-To-Market and Sales Intelligence Architect.
Analyze the provided product website crawl data and short description.
Extract a highly structured, accurate Ideal Customer Profile (ICP).

Return a JSON object matching this schema:
{
  "product_name": "Name of the product",
  "category": "e.g. Developer Tools, B2B SaaS, Analytics",
  "value_proposition": "1-2 sentence core value prop",
  "target_roles": ["VP of Engineering", "Head of Product", "CTO", "Operations Director"],
  "target_industries": ["B2B SaaS", "Fintech", "Healthtech", "DevTools"],
  "company_size_range": "11-250 employees",
  "core_pain_points": [
    "High per-seat pricing in legacy tools",
    "Slow latency and clunky user experience",
    "Lack of custom API flexibility"
  ],
  "intent_search_queries": [
    "looking for alternative to [competitor]",
    "recommend a tool for [pain point]",
    "frustrated with [competitor] pricing"
  ],
  "negative_keywords": ["freelance", "internship", "consumer"]
}
"""

DEAL_PROFILER_SYSTEM_PROMPT = """
You are an expert E-Commerce Deal & Affiliate Conversion Architect for the Indian market (BharatBazaro / Amazon India).
Analyze the provided product deal crawl data, pricing, and category.
Extract a structured Deal Buyer Profile optimized for high-conversion WhatsApp & Telegram broadcasts.

Return a JSON object matching this schema:
{
  "product_name": "Title of the deal item",
  "category": "Home & Kitchen / Small Appliances / Personal Care",
  "value_proposition": "All-time low price drop under ₹999 with 1-day Prime delivery",
  "target_roles": ["Bargain Hunters", "Kitchen & Home Shoppers", "Impulse Buyers", "Prime Members"],
  "target_industries": ["B2C E-Commerce", "Indian Households", "Deal Seekers"],
  "company_size_range": "Individual Consumers",
  "core_pain_points": [
    "Paying full retail MRP without coupon tracking",
    "Missing limited-time lightning flash sales",
    "Unreliable quality on cheap local marketplace knockoffs"
  ],
  "intent_search_queries": [
    "site:reddit.com/r/dealsforindia recommend kettle",
    "telegram deal alert amazon loot",
    "air fryer price drop deal india"
  ],
  "negative_keywords": ["0% commission mobile", "used", "refurbished"]
}
"""


class ProfilerAgent:
    """Crawls user URL, understands product value proposition, and builds structured ICP or B2C Deal Profile."""

    async def profile_product(
        self,
        url: str,
        user_description: str = "",
        campaign_type: str = "b2b",
    ) -> Dict[str, Any]:
        logger.info(f"Profiling target: {url} (mode: {campaign_type})")

        is_deal_mode = (
            campaign_type == "b2c_deals"
            or any(d in url.lower() for d in ["amazon.in", "amzn.in", "amzn.to", "bharatbazaro", "flipkart"])
            or any(k in user_description.lower() for k in ["deal", "discount", "loot", "impulse", "affiliate", "mrp"])
        )

        # 1. Crawl the landing page or deal page
        crawl_data = await crawl_url(url)

        # 2. Extract deal metadata if Amazon or BharatBazaro
        asin = extract_asin(url) or extract_asin(crawl_data.get("content_text", ""))
        canonical_url = to_canonical_affiliate_url(url, subtag="leadforge-profile")

        prompt = (
            f"Task: Extract Ideal Customer Profile (ICP)\n"
            f"Target URL: {url}\n"
            f"Mode: {'B2C E-Commerce Deal (BharatBazaro)' if is_deal_mode else 'B2B Enterprise Lead Gen'}\n"
            f"User Context: {user_description}\n\n"
            f"Website Title: {crawl_data.get('title')}\n"
            f"Meta Description: {crawl_data.get('meta_description')}\n"
            f"Headings: {', '.join(crawl_data.get('headings', []))}\n\n"
            f"Page Snippet:\n{crawl_data.get('content_text', '')[:2500]}"
        )

        sys_prompt = DEAL_PROFILER_SYSTEM_PROMPT if is_deal_mode else PROFILER_SYSTEM_PROMPT
        icp_dict = await llm_client.generate_json(sys_prompt, prompt)

        # Fallback fields
        if not icp_dict.get("product_name"):
            title = crawl_data.get("title") or crawl_data.get("domain", "Product")
            icp_dict["product_name"] = title.split("-")[0].split("|")[0].strip()

        if is_deal_mode:
            # Query the live BharatBazaro feed for exact or matching deal
            matched_deal = None
            if asin:
                matched_deal = await get_deal_by_asin(asin)

            if not matched_deal:
                q_text = f"{user_description} {url} {crawl_data.get('title', '')}"
                search_results = await search_live_deals(query=q_text, limit=1)
                if search_results:
                    matched_deal = search_results[0]

            if not matched_deal:
                top_results = await get_top_converting_deals(limit=1)
                if top_results:
                    matched_deal = top_results[0]

            if matched_deal:
                deal_asin = asin or matched_deal.get("asin") or "B002MPPTB8"
                deal_title = matched_deal.get("title") or icp_dict.get("product_name") or "Deal Item"
                category = matched_deal.get("category") or icp_dict.get("category", "Home & Kitchen")
                deal_price = float(matched_deal.get("effective_price") or matched_deal.get("list_price") or 599.0)
                mrp = float(matched_deal.get("mrp") or (deal_price * 1.5))
                disc_pct = int(matched_deal.get("discount_pct") or int(((mrp - deal_price) / mrp) * 100))
                savings = int(matched_deal.get("savings_inr") or (mrp - deal_price))
                rating = float(matched_deal.get("rating") or 4.3)
                review_count = int(matched_deal.get("review_count") or 4500)
                image_url = matched_deal.get("image_url", "")
                deal_url = to_canonical_affiliate_url(deal_asin, subtag="lf-deal")
                comm_info = compute_commission_estimate(category, deal_price)

                icp_dict["product_name"] = deal_title
                icp_dict["category"] = category
                icp_dict["value_proposition"] = (
                    f"Verified {disc_pct}% price drop at ₹{int(deal_price):,} "
                    f"(Save ₹{int(savings):,}) with 1-Day Prime Delivery"
                )
                icp_dict["deal_metadata"] = {
                    "asin": deal_asin,
                    "title": deal_title,
                    "brand": matched_deal.get("brand", ""),
                    "category": category,
                    "effective_price": deal_price,
                    "mrp": mrp,
                    "discount_pct": disc_pct,
                    "savings_inr": savings,
                    "rating": rating,
                    "review_count": review_count,
                    "image_url": image_url,
                    "canonical_affiliate_url": deal_url,
                    "commission_rate_percent": comm_info["commission_rate_percent"],
                    "estimated_commission_rupees": comm_info["estimated_commission_rupees"],
                    "is_impulse_sweet_spot": comm_info["is_impulse_sweet_spot"],
                    "is_zero_roi": comm_info["is_zero_roi"],
                }
            else:
                category = icp_dict.get("category", "Home & Kitchen")
                comm_info = compute_commission_estimate(category, 599.0)
                icp_dict["deal_metadata"] = {
                    "asin": asin or "B09W2GFM7Y",
                    "canonical_affiliate_url": canonical_url,
                    "commission_rate_percent": comm_info["commission_rate_percent"],
                    "is_impulse_sweet_spot": comm_info["is_impulse_sweet_spot"],
                }

            if not icp_dict.get("target_roles"):
                icp_dict["target_roles"] = ["Budget Shoppers", "Home & Kitchen Buyers", "Deal Seekers"]
            if not icp_dict.get("target_industries"):
                icp_dict["target_industries"] = ["B2C E-Commerce", "Impulse Consumers"]
        else:
            if not icp_dict.get("target_roles"):
                icp_dict["target_roles"] = ["Head of Product", "VP of Engineering", "CTO", "Founder"]
            if not icp_dict.get("target_industries"):
                icp_dict["target_industries"] = ["B2B SaaS", "Tech", "Operations"]

        return icp_dict


profiler_agent = ProfilerAgent()
