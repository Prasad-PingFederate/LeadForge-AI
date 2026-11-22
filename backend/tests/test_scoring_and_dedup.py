import json
import pytest
from unittest.mock import AsyncMock, patch
from app.core.scoring import compute_lead_score
from app.agents.enrichment_agent import EnrichmentAgent


def test_compute_lead_score_high_intent():
    icp_data = {
        "target_roles": ["VP of Engineering", "Head of Product", "CTO"],
        "target_industries": ["B2B SaaS", "DevTools"],
    }

    score_result = compute_lead_score(
        contact_role="VP of Engineering",
        company_name="CloudStack Labs",
        domain="cloudstack.io",
        intent_platform="hackernews",
        intent_snippet="Looking for a modern alternative to legacy expensive tools",
        email_status="verified",
        icp_data=icp_data,
    )

    assert score_result["fit_score"] == 40
    assert score_result["intent_score"] == 35
    assert score_result["verif_score"] == 25
    assert score_result["overall_score"] == 100
    assert "CloudStack Labs" in score_result["why_this_lead"]

    breakdown = json.loads(score_result["score_breakdown_json"])
    assert breakdown["icp_fit"]["score"] == 40
    assert breakdown["intent_freshness"]["score"] == 35
    assert breakdown["contact_verification"]["score"] == 25


def test_compute_lead_score_unverified_lead():
    score_result = compute_lead_score(
        contact_role=None,
        company_name="Generic Shop",
        domain="genericshop.com",
        intent_platform="b2b_search",
        intent_snippet=None,
        email_status="unverified",
        icp_data={},
    )

    assert 0 <= score_result["overall_score"] <= 60
    assert score_result["verif_score"] == 0
    assert "Generic Shop" in score_result["why_this_lead"]


@pytest.mark.asyncio
async def test_enrichment_agent_dedup_and_suppression():
    agent = EnrichmentAgent()

    raw_leads = [
        {
            "company_name": "DupeCorp",
            "domain": "https://www.dupecorp.com/about",
            "intent_platform": "b2b_search",
            "intent_source_url": "https://dupecorp.com",
            "contact_email": "alex@dupecorp.com",
        },
        {
            "company_name": "DupeCorp Secondary",
            "domain": "dupecorp.com",
            "intent_platform": "reddit",
            "intent_source_url": "https://reddit.com/r/saas/comments/123",
            "contact_email": "alex@dupecorp.com",
        },
        {
            "company_name": "BlockedCorp",
            "domain": "blockedcorp.com",
            "intent_platform": "b2b_search",
            "intent_source_url": "https://blockedcorp.com",
            "contact_email": "lead@blockedcorp.com",
        },
        {
            "company_name": "GoodCorp",
            "domain": "goodcorp.io",
            "intent_platform": "hackernews",
            "intent_source_url": "https://news.ycombinator.com/item?id=456",
            "contact_email": "team@goodcorp.io",
        },
    ]

    with patch("app.agents.enrichment_agent.verify_email_address") as mock_verify:
        mock_verify.return_value = {
            "email": "team@goodcorp.io",
            "status": "verified",
            "score_contribution": 25,
            "provider": "Google Workspace",
        }

        enriched = await agent.enrich_and_score_leads(
            raw_leads,
            suppressed_domains={"blockedcorp.com"},
            suppressed_emails=set(),
        )

        domains = [e["domain"] for e in enriched]
        assert "blockedcorp.com" not in domains
        # dupecorp should appear exactly once
        assert domains.count("dupecorp.com") == 1
        assert "goodcorp.io" in domains
        assert all("why_this_lead" in e for e in enriched)
        assert all("overall_score" in e for e in enriched)
