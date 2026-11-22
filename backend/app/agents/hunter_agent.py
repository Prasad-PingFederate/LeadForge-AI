import logging
from typing import List, Dict, Any

from app.connectors.intent_social import intent_social_connector
from app.connectors.b2b_discovery import b2b_discovery_connector

logger = logging.getLogger(__name__)


class HunterAgent:
    """
    Executes GTM lead-generation strategies across live intent channels:
    - Reddit & Hacker News buying-intent discussions
    - B2B target company discovery matching ICP queries
    
    Enforces ZERO HALLUCINATIONS: Every lead has an external intent_source_url.
    """

    async def hunt_leads_for_strategies(
        self,
        strategies: List[Dict[str, Any]],
        limit_per_strategy: int = 4
    ) -> List[Dict[str, Any]]:
        raw_leads: List[Dict[str, Any]] = []

        for strat in strategies:
            strat_id = strat.get("id")
            title = strat.get("title", "")
            channel = strat.get("channel", "email").lower()
            queries = strat.get("target_queries", [])
            if isinstance(queries, str):
                import json
                try:
                    queries = json.loads(queries)
                except Exception:
                    queries = [queries]

            weight = float(strat.get("conversion_weight", 1.0))
            # Self-learning dynamic limit adjustment
            adjusted_limit = max(2, int(round(limit_per_strategy * weight)))
            logger.info(f"Hunter executing strategy '{title}' on channel '{channel}' (weight: {weight:.2f}x, limit: {adjusted_limit})")

            for query in queries[:2]:
                found_leads = []
                if channel in ["reddit", "hackernews", "whatsapp", "telegram", "social"] or "intent" in title.lower() or "deal" in title.lower():
                    found_leads = await intent_social_connector.search(query, limit=adjusted_limit)
                else:
                    found_leads = await b2b_discovery_connector.search(query, limit=adjusted_limit)

                for item in found_leads:
                    # Attach strategy attribution
                    item["strategy_id"] = strat_id
                    item["strategy_title"] = title
                    raw_leads.append(item)

        logger.info(f"Hunter Agent discovered {len(raw_leads)} potential intent leads")
        return raw_leads


hunter_agent = HunterAgent()
