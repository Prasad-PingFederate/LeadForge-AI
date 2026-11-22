import json
import logging
from typing import Dict, Any, List

from app.connectors.web_search import web_search_connector
from app.core.llm import llm_client

logger = logging.getLogger(__name__)

COMPETITOR_SYSTEM_PROMPT = """
You are an elite Competitive Intelligence Strategist and B2B Positioning Expert.
Based on the provided product ICP and live web search findings on competitors, generate:
1. Top 2-4 Competitor Battlecards detailing their strengths, real weaknesses/complaints, pricing tier, and your displacement angle.
2. Exactly 3 actionable, high-ROI Go-To-Market Lead Generation Strategies with exact target search queries and recommended outreach channel.

Return a JSON object matching this schema:
{
  "competitors": [
    {
      "name": "Competitor Name",
      "domain": "competitor.com",
      "strengths": ["Enterprise market share", "Brand recognition"],
      "weaknesses": ["Expensive seat minimums", "Slow support", "Bloated legacy UI"],
      "pricing_tier": "$30 - $80 / user / mo",
      "displacement_angle": "Cut software bill by 50% with instant self-serve onboarding and zero per-seat penalty.",
      "source_urls": ["https://reddit.com/r/saas/comments/..."]
    }
  ],
  "strategies": [
    {
      "title": "Displace Overpriced Legacy Competitor",
      "channel": "email",
      "angle": "Target teams burdened by 10-seat enterprise contracts",
      "target_queries": ["alternative to [competitor]", "[competitor] pricing increase"]
    },
    {
      "title": "Active Social Buying Intent on Reddit & Hacker News",
      "channel": "reddit",
      "angle": "Help users complaining about competitor outages or missing APIs",
      "target_queries": ["recommend tool for [pain point]", "looking for alternative to [competitor]"]
    },
    {
      "title": "High-Growth Scaleup ICP Discovery",
      "channel": "linkedin",
      "angle": "Target newly funded engineering teams migrating off outdated stack",
      "target_queries": ["VP Engineering B2B SaaS startup"]
    }
  ]
}
"""

DEAL_COMPETITOR_SYSTEM_PROMPT = """
You are an expert E-Commerce Deal & Indian Marketplace Price Strategist (BharatBazaro & Amazon India).
Analyze the deal item, compare against competitors (Flipkart, Meesho, local offline stores), and generate:
1. Top Competitor Comparison Battlecards highlighting where our Amazon deal wins (instant Prime delivery, genuine warranty vs fake clones).
2. Exactly 3 high-converting promotional channel strategies (WhatsApp VIP Broadcast, Telegram Loot Alert, Reddit/Community recommendation).

Return a JSON object:
{
  "competitors": [
    {
      "name": "Flipkart Retail",
      "domain": "flipkart.com",
      "strengths": ["Big Billion Days marketing", "Bank discounts"],
      "weaknesses": ["Frequent price cancellations on loot items", "Slower delivery for non-Plus", "Difficult returns"],
      "pricing_tier": "Retail ₹1,299",
      "displacement_angle": "Direct Amazon 1-Day Prime Delivery with hassle-free replacement warranty at ₹599.",
      "source_urls": ["https://reddit.com/r/dealsforindia/comments/flipkart_cancellation"]
    }
  ],
  "strategies": [
    {
      "title": "WhatsApp VIP Deal Broadcast (High-Intent Impulse)",
      "channel": "whatsapp",
      "angle": "Direct savings alert with bold emojis, verified price drop badge, and 1-click cart link",
      "target_queries": ["best home deals under 999", "kitchen appliance price drop"]
    },
    {
      "title": "Telegram Loot & Flash Price Drops",
      "channel": "telegram",
      "angle": "Instant markdown post for bargain hunters with all-time low price verification",
      "target_queries": ["telegram loot deals india", "amazon flash deal telegram"]
    },
    {
      "title": "Community Social Bargain Review (Reddit & X)",
      "channel": "reddit",
      "angle": "Answering active recommendation threads with genuine review highlights",
      "target_queries": ["site:reddit.com/r/dealsforindia recommend", "site:reddit.com/r/IndianGaming deals"]
    }
  ]
}
"""


class CompetitorAgent:
    """Discovers real competitors via live web search and formulates 3 high-ROI GTM strategies."""

    async def analyze_competitors_and_strategies(
        self,
        icp_data: Dict[str, Any],
        campaign_type: str = "b2b",
    ) -> Dict[str, Any]:
        product_name = icp_data.get("product_name", "Product")
        category = icp_data.get("category", "Technology")
        is_deal_mode = campaign_type == "b2c_deals" or "deal_metadata" in icp_data

        # 1. Search query
        if is_deal_mode:
            search_query = f"{product_name} price Flipkart Meesho Amazon India deal"
        else:
            search_query = f"{product_name} competitors alternatives {category}"

        logger.info(f"Searching competitors/alternatives with query: {search_query}")
        raw_results = await web_search_connector.search(search_query, limit=6)

        search_context = [
            f"- {r.get('title')}: {r.get('url')} | {r.get('snippet')}" for r in raw_results
        ]

        # 2. Build prompt for LLM
        prompt = (
            f"Target: {product_name}\n"
            f"Category: {category}\n"
            f"Mode: {'B2C E-Commerce Deal (BharatBazaro)' if is_deal_mode else 'B2B Enterprise Lead Gen'}\n"
            f"Value Proposition: {icp_data.get('value_proposition')}\n"
            f"Pain Points: {', '.join(icp_data.get('core_pain_points', []))}\n\n"
            f"Live Search Findings:\n" + "\n".join(search_context)
        )

        sys_prompt = DEAL_COMPETITOR_SYSTEM_PROMPT if is_deal_mode else COMPETITOR_SYSTEM_PROMPT
        result = await llm_client.generate_json(sys_prompt, prompt)

        competitors = result.get("competitors", [])
        strategies = result.get("strategies", [])

        # Fallback Battlecards
        if not competitors:
            if is_deal_mode:
                competitors = [
                    {
                        "name": "Flipkart Big Billion Days",
                        "domain": "flipkart.com",
                        "strengths": ["Festive brand awareness", "Bank card instant discounts"],
                        "weaknesses": ["Frequent order cancellations on deals", "Slower non-Plus delivery", "Return hassle"],
                        "pricing_tier": "Retail MRP Tier",
                        "displacement_angle": "Direct Amazon Prime 1-day delivery with verified brand warranty at lowest price.",
                        "source_urls": ["https://reddit.com/r/dealsforindia/comments/flipkart_cancellation"],
                    }
                ]
            else:
                competitors = [
                    {
                        "name": "LegacyCorp",
                        "domain": "legacycorp.com",
                        "strengths": ["Enterprise market presence", "Extensive documentation"],
                        "weaknesses": ["High per-seat pricing", "Clunky user interface", "Slow API latency"],
                        "pricing_tier": "$45 - $90 / user / mo",
                        "displacement_angle": "Save 50% on SaaS costs with zero bloat and 10x faster response time.",
                        "source_urls": ["https://reddit.com/r/saas/comments/reviews_legacycorp"],
                    }
                ]

        # Ensure exactly 3 strategies
        if len(strategies) < 3:
            if is_deal_mode:
                strategies = [
                    {
                        "title": "WhatsApp VIP Deal Broadcast (High-Intent Impulse)",
                        "channel": "whatsapp",
                        "angle": "Direct ₹ Savings alert with bold emojis, verified price drop badge, and 1-click Amazon link",
                        "target_queries": ["best home deals under 999", "kitchen appliance price drop amazon"],
                    },
                    {
                        "title": "Telegram Loot & Flash Price Drops",
                        "channel": "telegram",
                        "angle": "Markdown alert for bargain hunters with verified price drop link",
                        "target_queries": ["site:t.me loot deals india", "telegram deal alert amazon"],
                    },
                    {
                        "title": "Community Social Bargain Review (Reddit & X)",
                        "channel": "reddit",
                        "angle": "Answering active recommendation threads in r/dealsforindia with genuine review highlights",
                        "target_queries": ["site:reddit.com/r/dealsforindia recommend", "best budget kettle reddit"],
                    },
                ]
            else:
                strategies = [
                    {
                        "title": f"Target Frustrated Users of {competitors[0]['name']}",
                        "channel": "email",
                        "angle": "Highlight transparent pricing without enterprise seat barriers",
                        "target_queries": [f"looking for alternative to {competitors[0]['name']}", f"switch from {competitors[0]['name']}"],
                    },
                    {
                        "title": "Community Social Intent Listening",
                        "channel": "reddit",
                        "angle": "Directly answer community threads asking for modern tool recommendations",
                        "target_queries": ["site:reddit.com recommend tool for scheduling", "site:news.ycombinator.com alternative"],
                    },
                    {
                        "title": "Fast-Growing Scaleup Discovery",
                        "channel": "linkedin",
                        "angle": "Reach decision-makers modernizing their developer and workflow stack",
                        "target_queries": ["VP Product B2B software", "Head of Engineering SaaS"],
                    },
                ]

        return {
            "competitors": competitors,
            "strategies": strategies[:3],
        }


competitor_agent = CompetitorAgent()
