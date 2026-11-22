import pytest
from unittest.mock import AsyncMock, patch
from app.workflows.leadforge_graph import leadforge_graph
from app.workflows.state import LeadForgeState


@pytest.mark.asyncio
async def test_full_leadforge_langgraph_workflow():
    initial_state: LeadForgeState = {
        "campaign_id": "test-graph-camp-1",
        "target_url": "https://leadforge.ai",
        "description": "Autonomous B2B Sales & Competitor Intelligence Agent",
        "icp_data": {},
        "competitors": [],
        "strategies": [],
        "raw_leads": [],
        "enriched_leads": [],
        "outreach_drafts": [],
        "current_step": "started",
        "progress_percent": 10,
        "logs": ["Initial test trigger"],
        "error": None,
    }

    dummy_raw_leads = [
        {
            "company_name": "CloudScale",
            "domain": "cloudscale.io",
            "contact_name": "Elena Rostova",
            "contact_role": "VP Engineering",
            "contact_email": "elena@cloudscale.io",
            "intent_platform": "hackernews",
            "intent_source_url": "https://news.ycombinator.com/item?id=3819201",
            "intent_snippet": "Looking for modern workflow tools without per-seat penalty",
            "strategy_title": "Displace Overpriced Legacy Seat Minimums",
        }
    ]

    with patch("app.agents.profiler_agent.crawl_url") as mock_crawl, \
         patch("app.agents.hunter_agent.hunter_agent.hunt_leads_for_strategies", new_callable=AsyncMock) as mock_hunt, \
         patch("app.core.email_verifier.dns.resolver.resolve") as mock_dns:

        mock_hunt.return_value = dummy_raw_leads
        mock_dns.return_value = []
        mock_crawl.return_value = {
            "url": "https://leadforge.ai",
            "domain": "leadforge.ai",
            "title": "LeadForge AI - Autonomous Sales Intelligence",
            "meta_description": "Find real intent leads and automate hyper-personalized outreach.",
            "headings": ["Autonomous Prospecting", "Competitor Intelligence"],
            "content_text": "LeadForge AI extracts verified prospects and competitor gaps.",
            "status_code": 200,
            "success": True,
        }

        final_state = await leadforge_graph.ainvoke(initial_state)

        assert final_state["current_step"] == "completed"
        assert final_state["progress_percent"] == 100

        # 1. Profiler output
        assert "product_name" in final_state["icp_data"]

        # 2. Competitor output
        assert len(final_state["competitors"]) >= 1
        assert len(final_state["strategies"]) == 3

        # 3. Hunter & Enricher output
        assert isinstance(final_state["raw_leads"], list)
        assert isinstance(final_state["enriched_leads"], list)
        for lead in final_state["enriched_leads"]:
            assert "overall_score" in lead
            assert "why_this_lead" in lead
            assert 0 <= lead["overall_score"] <= 100

        # 4. Outreach output
        assert isinstance(final_state["outreach_drafts"], list)
        if final_state["outreach_drafts"]:
            draft = final_state["outreach_drafts"][0]
            assert "subject" in draft
            assert "body_step1" in draft

        # 5. Logs verification
        assert len(final_state["logs"]) >= 5
