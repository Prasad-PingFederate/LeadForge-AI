import json
import logging
from typing import Dict, Any

from app.core.crawler import crawl_url
from app.core.llm import llm_client
from app.schemas.campaign import ICPData

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


class ProfilerAgent:
    """Crawls user URL, understands product value proposition, and builds structured ICP."""

    async def profile_product(self, url: str, user_description: str = "") -> Dict[str, Any]:
        logger.info(f"Profiling product from URL: {url}")
        
        # 1. Crawl the landing page
        crawl_data = await crawl_url(url)

        # 2. Prepare context for LLM
        prompt = (
            f"Target URL: {url}\n"
            f"User Description/Context: {user_description}\n\n"
            f"Website Title: {crawl_data.get('title')}\n"
            f"Meta Description: {crawl_data.get('meta_description')}\n"
            f"Headings: {', '.join(crawl_data.get('headings', []))}\n\n"
            f"Page Content Snippet:\n{crawl_data.get('content_text', '')[:2500]}"
        )

        # 3. Generate structured ICP
        icp_dict = await llm_client.generate_json(PROFILER_SYSTEM_PROMPT, prompt)

        # Ensure required fields exist with fallbacks
        if not icp_dict.get("product_name"):
            domain = crawl_data.get("domain", "SaaS Platform")
            icp_dict["product_name"] = domain.split(".")[0].capitalize()
        if not icp_dict.get("target_roles"):
            icp_dict["target_roles"] = ["Head of Product", "VP of Engineering", "CTO", "Founder"]
        if not icp_dict.get("target_industries"):
            icp_dict["target_industries"] = ["B2B SaaS", "Tech", "Fintech", "Operations"]
        if not icp_dict.get("intent_search_queries"):
            icp_dict["intent_search_queries"] = [
                f"alternative to {icp_dict['product_name'].lower()} competitors",
                "recommend modern workflow tool",
                "frustrated with legacy pricing",
            ]

        return icp_dict


profiler_agent = ProfilerAgent()
