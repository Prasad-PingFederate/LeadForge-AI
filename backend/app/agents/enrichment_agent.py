import logging
from typing import List, Dict, Any, Set, Optional

from app.connectors.website_auditor import website_auditor_connector
from app.core.email_verifier import verify_email_address
from app.core.scoring import compute_lead_score

logger = logging.getLogger(__name__)


class EnrichmentAgent:
    """
    Enriches, deduplicates, verifies, and scores all discovered leads:
    1. Deduplication by normalized domain / email
    2. Waterfall website audit for public contact & tech signals
    3. Live DNS MX Email Verification
    4. Transparent 0-100 Lead Scoring + "Why this lead" evidence string
    """

    async def enrich_and_score_leads(
        self,
        raw_leads: List[Dict[str, Any]],
        icp_data: Optional[Dict[str, Any]] = None,
        suppressed_domains: Optional[Set[str]] = None,
        suppressed_emails: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        supp_doms = {d.lower() for d in (suppressed_domains or set())}
        supp_emails = {e.lower() for e in (suppressed_emails or set())}

        seen_domains: Set[str] = set()
        seen_emails: Set[str] = set()
        enriched_leads: List[Dict[str, Any]] = []

        for lead in raw_leads:
            raw_domain = lead.get("domain", "").strip().lower()
            # Clean domain
            domain = raw_domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            if not domain:
                continue

            # Check suppression list
            if domain in supp_doms:
                logger.info(f"Skipping suppressed domain: {domain}")
                continue

            # Deduplication by domain
            if domain in seen_domains:
                continue
            seen_domains.add(domain)

            company_name = lead.get("company_name") or domain.split(".")[0].capitalize()
            contact_name = lead.get("contact_name")
            contact_role = lead.get("contact_role")
            contact_email = lead.get("contact_email")
            linkedin_url = lead.get("linkedin_url")

            # Waterfall Enrichment: If email or details are missing, audit company site
            if not contact_email or not linkedin_url:
                try:
                    audit = await website_auditor_connector.audit_company_domain(domain)
                    if not contact_email and audit.get("emails"):
                        contact_email = audit["emails"][0]
                    if not linkedin_url and audit.get("linkedin_urls"):
                        linkedin_url = audit["linkedin_urls"][0]
                except Exception as exc:
                    logger.debug(f"Audit failed for {domain}: {exc}")

            # Check email suppression
            if contact_email and contact_email.lower() in supp_emails:
                logger.info(f"Skipping suppressed email: {contact_email}")
                continue

            # Email deduplication
            if contact_email:
                c_email = contact_email.lower().strip()
                if c_email in seen_emails:
                    contact_email = None
                else:
                    seen_emails.add(c_email)

            # Email verification (DNS MX + format check)
            verif_result = await verify_email_address(contact_email)
            email_status = verif_result["status"]
            verified_email = verif_result["email"] if email_status in ["verified", "risky"] else contact_email

            # Compute transparent 0-100 lead score
            scoring = compute_lead_score(
                contact_role=contact_role,
                company_name=company_name,
                domain=domain,
                intent_platform=lead.get("intent_platform", "b2b_search"),
                intent_snippet=lead.get("intent_snippet", ""),
                email_status=email_status,
                icp_data=icp_data,
            )

            enriched_lead = {
                "strategy_id": lead.get("strategy_id"),
                "company_name": company_name,
                "domain": domain,
                "contact_name": contact_name,
                "contact_role": contact_role,
                "contact_email": verified_email,
                "email_status": email_status,
                "linkedin_url": linkedin_url,
                "intent_platform": lead.get("intent_platform", "b2b_search"),
                "intent_source_url": lead.get("intent_source_url", f"https://{domain}"),
                "intent_snippet": lead.get("intent_snippet", ""),
                "fit_score": scoring["fit_score"],
                "intent_score": scoring["intent_score"],
                "verif_score": scoring["verif_score"],
                "overall_score": scoring["overall_score"],
                "score_breakdown_json": scoring["score_breakdown_json"],
                "why_this_lead": scoring["why_this_lead"],
                "status": "new",
            }

            enriched_leads.append(enriched_lead)

        # Sort leads by overall_score descending
        enriched_leads.sort(key=lambda x: x["overall_score"], reverse=True)
        return enriched_leads


enrichment_agent = EnrichmentAgent()
