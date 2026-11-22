import logging
from typing import List, Dict, Any
from urllib.parse import urlparse

from app.connectors.base import BaseConnector
from app.connectors.web_search import web_search_connector

logger = logging.getLogger(__name__)


class B2BDiscoveryConnector(BaseConnector):
    """
    Discovers real target companies and buyer organizations matching
    ICP target roles, industries, and strategic angles.
    """

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Execute search across web & business directories
        search_results = await web_search_connector.search(query, limit=limit)
        
        leads = []
        seen_domains = set()

        for item in search_results:
            domain = item.get("domain", "").lower().strip()
            # Ignore search engines or social aggregators
            if not domain or any(blocked in domain for blocked in ["google.", "bing.", "youtube.", "wikipedia.", "duckduckgo."]):
                continue
            if domain in seen_domains:
                continue
            seen_domains.add(domain)

            name = item.get("title", "").split("-")[0].split("|")[0].strip()
            if not name or len(name) < 2:
                name = domain.split(".")[0].capitalize()

            leads.append({
                "company_name": name,
                "domain": domain,
                "contact_name": None,
                "contact_role": "Decision Maker",
                "contact_email": None,
                "intent_platform": "b2b_search",
                "intent_source_url": item.get("url", f"https://{domain}"),
                "intent_snippet": item.get("snippet", f"Discovered via ICP query: {query}"),
            })

        return leads[:limit]


b2b_discovery_connector = B2BDiscoveryConnector()
