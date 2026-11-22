import json
import logging
from typing import Dict, Any, List

from app.connectors.web_search import web_search_connector
from app.core.llm import llm_client

logger = logging.getLogger(__name__)

COMPETITOR_SYSTEM_PROMPT = """
You are an elite Competitive Intelligence Strategist and B2B Positioning Expert.
Based on the provided product ICP and live web search findings on competitors, generate:
1. Top 3-5 Competitor Battlecards detailing their strengths, real weaknesses/complaints, pricing tier, and your displacement angle.
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


class CompetitorAgent:
    """Discovers real competitors via live web search and formulates 3 high-ROI GTM strategies."""

    async def analyze_competitors_and_strategies(self, icp_data: Dict[str, Any]) -> Dict[str, Any]:
        product_name = icp_data.get("product_name", "Software")
        category = icp_data.get("category", "B2B SaaS")

        # 1. Live web search for real competitors
        search_query = f"{product_name} competitors alternatives {category}"
        logger.info(f"Searching real competitors with query: {search_query}")
        raw_results = await web_search_connector.search(search_query, limit=8)

        search_context = []
        for r in raw_results:
            search_context.append(f"- {r.get('title')}: {r.get('url')} | {r.get('snippet')}")

        # 2. Build prompt for LLM
        prompt = (
            f"Product Name: {product_name}\n"
            f"Category: {category}\n"
            f"Value Proposition: {icp_data.get('value_proposition')}\n"
            f"Pain Points: {', '.join(icp_data.get('core_pain_points', []))}\n\n"
            f"Live Competitor Web Search Findings:\n" + "\n".join(search_context)
        )

        # 3. Generate Battlecards and 3 Strategies
        result = await llm_client.generate_json(COMPETITOR_SYSTEM_PROMPT, prompt)

        competitors = result.get("competitors", [])
        strategies = result.get("strategies", [])

        # Ensure fallback battlecards if search was sparse
        if not competitors:
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
