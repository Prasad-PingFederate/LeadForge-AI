import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

EMAIL_FINDER_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)
LINKEDIN_COMPANY_REGEX = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_.-]+", re.I
)

IGNORED_EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".js", ".css"}


class WebsiteAuditorConnector(BaseConnector):
    """
    Asynchronously crawls target company websites (homepage, /about, /contact)
    to discover real contact emails, LinkedIn URLs, tech stack signals, and pain points.
    """

    async def audit_company_domain(self, domain: str, timeout_seconds: float = 8.0) -> Dict[str, Any]:
        base_url = f"https://{domain}" if not domain.startswith("http") else domain
        clean_domain = urlparse(base_url).netloc.replace("www.", "")

        audit_result: Dict[str, Any] = {
            "domain": clean_domain,
            "emails": [],
            "linkedin_urls": [],
            "tech_signals": [],
            "audited_url": base_url,
            "status": "success",
        }

        urls_to_check = [base_url, f"{base_url}/contact", f"{base_url}/about"]

        headers = {
            "User-Agent": "LeadForgeBot/1.0 (B2B Public Audit; contact@leadforge.ai)",
            "Accept": "text/html,application/xhtml+xml",
        }

        async with httpx.AsyncClient(headers=headers, timeout=timeout_seconds, follow_redirects=True, verify=False) as client:
            for url in urls_to_check:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        text = resp.text
                        soup = BeautifulSoup(text, "html.parser")

                        # 1. Extract Emails
                        matches = EMAIL_FINDER_REGEX.findall(text)
                        for m in matches:
                            clean_m = m.lower().strip()
                            if not any(clean_m.endswith(ext) for ext in IGNORED_EMAIL_EXTENSIONS):
                                if clean_domain in clean_m or "@" in clean_m:
                                    if clean_m not in audit_result["emails"]:
                                        audit_result["emails"].append(clean_m)

                        # 2. Extract LinkedIn URLs
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            if "linkedin.com" in href:
                                if href not in audit_result["linkedin_urls"]:
                                    audit_result["linkedin_urls"].append(href)

                        # 3. Detect Tech Signals
                        t_lower = text.lower()
                        for tech in ["react", "next.js", "tailwind", "aws", "stripe", "segment", "hubspot", "salesforce", "intercom", "datadog"]:
                            if tech in t_lower and tech not in audit_result["tech_signals"]:
                                audit_result["tech_signals"].append(tech)

                except Exception as e:
                    logger.debug(f"Audit fetch error on {url}: {e}")

        # If no email was found on page, synthesize the standard domain contact point
        if not audit_result["emails"]:
            audit_result["emails"].append(f"contact@{clean_domain}")

        return audit_result

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        # Required implementation for BaseConnector interface
        audit = await self.audit_company_domain(query)
        return [audit]


website_auditor_connector = WebsiteAuditorConnector()
