import json
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.learning_agent import learning_agent
from app.db.models import Campaign, Strategy, Lead, OutreachMessage
from app.api.campaigns import ACTIVE_CAMPAIGN_PROGRESS


@pytest.mark.asyncio
async def test_learning_agent_reply_classification():
    # Positive intent
    res_pos = await learning_agent.classify_reply("Sounds great, let's schedule a call next Tuesday.")
    assert res_pos["category"] == "positive"

    # Objection intent
    res_obj = await learning_agent.classify_reply("Does your tool support multi-tenant SSO?")
    assert res_obj["category"] in ["objection", "positive"]

    # Unsubscribe intent
    res_unsub = await learning_agent.classify_reply("Unsubscribe. Stop emailing me.")
    assert res_unsub["category"] == "unsubscribe"

    # Weight adjustments
    assert learning_agent.compute_weight_adjustment(1.0, "positive") == 1.35
    assert learning_agent.compute_weight_adjustment(1.0, "not_now") == 1.0
    assert learning_agent.compute_weight_adjustment(1.0, "unsubscribe") == 0.75


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "daily_send_cap" in data


@pytest.mark.asyncio
async def test_campaign_create_and_read(async_client: AsyncClient):
    payload = {
        "target_url": "https://leadforge.ai",
        "description": "Autonomous B2B Sales & Intelligence Platform",
        "name": "LeadForge Launch Campaign",
    }
    with patch("app.api.campaigns.run_campaign_workflow", new_callable=AsyncMock):
        resp = await async_client.post("/api/campaigns", json=payload)
        assert resp.status_code == 201
        camp = resp.json()
        assert camp["id"] is not None
        assert camp["target_url"] == "https://leadforge.ai"

        # Read back campaign
        get_resp = await async_client.get(f"/api/campaigns/{camp['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "LeadForge Launch Campaign"


@pytest.mark.asyncio
async def test_leads_list_and_csv_export(async_client: AsyncClient, db_session: AsyncSession):
    # Setup test campaign with leads
    camp = Campaign(id="camp-test-leads", name="Leads Test", target_url="https://leadforge.ai")
    db_session.add(camp)

    lead1 = Lead(
        id="lead-1",
        campaign_id="camp-test-leads",
        company_name="CloudScale",
        domain="cloudscale.io",
        contact_name="Sarah Connor",
        contact_role="CTO",
        contact_email="sarah@cloudscale.io",
        email_status="verified",
        overall_score=92,
        intent_platform="hackernews",
        intent_source_url="https://news.ycombinator.com/item?id=123",
        intent_snippet="Looking for alternatives to Datadog",
        why_this_lead="CTO at CloudScale actively asked about alternatives on Hacker News",
    )
    lead2 = Lead(
        id="lead-2",
        campaign_id="camp-test-leads",
        company_name="LowFit Inc",
        domain="lowfit.com",
        contact_name="Bob",
        contact_role="Intern",
        contact_email="bob@lowfit.com",
        email_status="unverified",
        overall_score=35,
        intent_platform="b2b_search",
        intent_source_url="https://lowfit.com",
        why_this_lead="Low confidence match",
    )
    db_session.add(lead1)
    db_session.add(lead2)
    await db_session.commit()

    # List all leads
    resp = await async_client.get("/api/campaigns/camp-test-leads/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) == 2

    # Filter with min_score=80
    resp_filtered = await async_client.get("/api/campaigns/camp-test-leads/leads?min_score=80")
    assert resp_filtered.status_code == 200
    filtered = resp_filtered.json()
    assert len(filtered) == 1
    assert filtered[0]["company_name"] == "CloudScale"

    # Export CSV
    resp_csv = await async_client.get("/api/campaigns/camp-test-leads/leads/export")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    csv_text = resp_csv.text
    assert "Company Name,Domain" in csv_text
    assert "CloudScale" in csv_text
    assert "sarah@cloudscale.io" in csv_text


@pytest.mark.asyncio
async def test_reply_classification_endpoint(async_client: AsyncClient, db_session: AsyncSession):
    camp = Campaign(id="camp-reply-test", name="Reply Test", target_url="https://leadforge.ai")
    db_session.add(camp)

    strat = Strategy(
        id="strat-1",
        campaign_id="camp-reply-test",
        title="Displace Expensive Competitor",
        conversion_weight=1.0,
    )
    db_session.add(strat)

    lead = Lead(
        id="lead-reply-1",
        campaign_id="camp-reply-test",
        strategy_id="strat-1",
        company_name="Target Corp",
        domain="targetcorp.com",
        contact_email="target@targetcorp.com",
        email_status="verified",
        intent_platform="b2b_search",
        intent_source_url="https://targetcorp.com",
    )
    db_session.add(lead)

    msg = OutreachMessage(
        id="msg-reply-1",
        lead_id="lead-reply-1",
        channel="email",
        status="sent",
    )
    db_session.add(msg)
    await db_session.commit()

    # Post positive reply
    reply_payload = {"reply_text": "Sounds very interesting! Can you send pricing and schedule a quick demo?"}
    resp = await async_client.post("/api/outreach/msg-reply-1/reply", json=reply_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sentiment"] == "positive"
    assert data["new_strategy_weight"] > 1.0


@pytest.mark.asyncio
async def test_stream_progress_endpoint(async_client: AsyncClient):
    camp_id = "camp-sse-test"
    ACTIVE_CAMPAIGN_PROGRESS[camp_id] = {
        "status": "completed",
        "progress_percent": 100,
        "logs": ["Step 1 done", "Step 2 done"],
        "completed": True,
        "error": None,
    }

    resp = await async_client.get(f"/api/campaigns/{camp_id}/stream")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "data:" in resp.text
