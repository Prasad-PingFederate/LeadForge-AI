import json
from typing import Dict, Any, Optional


def compute_lead_score(
    contact_role: Optional[str],
    company_name: str,
    domain: str,
    intent_platform: str,
    intent_snippet: Optional[str],
    email_status: str,
    icp_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Transparent Lead Scoring Engine (0 - 100):
    - ICP Fit (0 - 40 pts)
    - Live Intent Freshness (0 - 35 pts)
    - Contact Verification (0 - 25 pts)
    """
    icp = icp_data or {}
    target_roles = [r.lower() for r in icp.get("target_roles", [])]
    target_industries = [i.lower() for i in icp.get("target_industries", [])]

    # ── 1. ICP FIT SCORE (0 - 40) ──────────────────────────────────────────────
    fit_score = 0
    role_pts = 0
    industry_pts = 0
    size_pts = 8  # Baseline target size

    role_str = (contact_role or "").lower()
    high_value_roles = [
        "vp", "head of", "director", "cto", "cio", "cpo", "founder", "ceo",
        "chief", "lead", "architect", "manager", "operations"
    ]
    if any(r in role_str for r in target_roles) or any(h in role_str for h in high_value_roles):
        role_pts = 20
    elif contact_role:
        role_pts = 12
    else:
        role_pts = 6

    # Industry / Company fit
    comp_str = f"{company_name} {domain}".lower()
    if any(ind in comp_str for ind in target_industries) or any(term in comp_str for term in ["tech", "soft", "ai", "cloud", "data", "app", "dev", "io", "labs"]):
        industry_pts = 12
    else:
        industry_pts = 8

    fit_score = min(40, role_pts + industry_pts + size_pts)

    # ── 2. LIVE INTENT FRESHNESS SCORE (0 - 35) ────────────────────────────────
    intent_score = 0
    platform = (intent_platform or "").lower()
    snippet = (intent_snippet or "").lower()

    if platform in ["reddit", "hackernews", "telegram"]:
        # Active buyer publicly seeking alternatives or asking for recommendations
        intent_score = 35
    elif platform in ["web_audit", "website_auditor"]:
        intent_score = 25
    elif platform in ["b2b_search", "google_places"]:
        intent_score = 22
    else:
        intent_score = 18

    # Bonus for competitor switching keywords or deal intent
    if any(k in snippet for k in ["alternative", "switch", "replace", "cancel", "expensive", "slow", "frustrated", "recommend", "deal", "price drop", "discount"]):
        intent_score = min(35, intent_score + 5)

    # ── 3. CONTACT VERIFICATION SCORE (0 - 25) ─────────────────────────────────
    verif_score = 0
    if email_status == "verified":
        verif_score = 25
    elif email_status == "risky":
        verif_score = 15
    else:
        verif_score = 0

    overall_score = min(100, fit_score + intent_score + verif_score)

    breakdown = {
        "icp_fit": {
            "score": fit_score,
            "max": 40,
            "role_match": role_pts,
            "industry_match": industry_pts,
            "size_match": size_pts,
        },
        "intent_freshness": {
            "score": intent_score,
            "max": 35,
            "platform": intent_platform,
            "has_switching_keyword": any(k in snippet for k in ["alternative", "switch", "replace"]),
        },
        "contact_verification": {
            "score": verif_score,
            "max": 25,
            "email_status": email_status,
        },
        "total": overall_score,
    }

    # ── 4. 1-SENTENCE "WHY THIS LEAD" EVIDENCE STRING ──────────────────────────
    role_desc = contact_role if contact_role else "Decision-maker"
    if platform in ["reddit", "hackernews", "telegram"]:
        why_this_lead = (
            f"{role_desc} at {company_name} actively asked about workflow alternatives on {intent_platform.capitalize()} "
            f"with verified business domain and {email_status} contact."
        )
    elif platform == "website_auditor":
        why_this_lead = (
            f"{company_name} matches your target ICP profile with audited tech gaps and {email_status} direct email."
        )
    else:
        why_this_lead = (
            f"{company_name} was discovered via active search matching your GTM strategy with {overall_score}/100 confidence."
        )

    return {
        "fit_score": fit_score,
        "intent_score": intent_score,
        "verif_score": verif_score,
        "overall_score": overall_score,
        "score_breakdown_json": json.dumps(breakdown),
        "why_this_lead": why_this_lead,
    }
