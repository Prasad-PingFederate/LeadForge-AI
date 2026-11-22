import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.outreach_agent import outreach_agent
from app.workers.mailer import (
    safe_mailer,
    generate_unsubscribe_token,
    verify_unsubscribe_token,
)
from app.db.models import Lead, OutreachMessage, SuppressionList, Campaign


@pytest.mark.asyncio
async def test_outreach_agent_drafts():
    lead = {
        "contact_name": "Elena Rostova",
        "contact_role": "VP of Engineering",
        "company_name": "HyperScale AI",
        "domain": "hyperscale.ai",
        "intent_platform": "hackernews",
        "intent_snippet": "Looking for a cost-effective alternative to Salesforce",
    }
    icp_data = {
        "product_name": "LeadForge AI",
        "value_proposition": "Autonomous sales intelligence platform",
    }

    draft = await outreach_agent.draft_outreach_for_lead(lead, icp_data)

    assert "subject" in draft
    assert "body_step1" in draft
    assert "body_step2" in draft
    assert "body_step3" in draft
    assert "linkedin_dm" in draft
    assert "social_reply" in draft
    assert len(draft["body_step1"]) > 10


def test_unsubscribe_hmac_token():
    email = "prospect@acmecorp.com"
    token = generate_unsubscribe_token(email)
    assert len(token) == 16
    assert verify_unsubscribe_token(email, token) is True
    assert verify_unsubscribe_token("different@acmecorp.com", token) is False
    assert verify_unsubscribe_token(email, "invalidtoken1234") is False


@pytest.mark.asyncio
async def test_safe_mailer_gates(db_session: AsyncSession):
    # 1. Test unverified email blocked
    lead_unverified = Lead(
        campaign_id="test-camp-1",
        company_name="Unverified Corp",
        domain="unverified.com",
        contact_email="test@unverified.com",
        email_status="unverified",
        intent_platform="b2b_search",
        intent_source_url="https://unverified.com",
    )
    db_session.add(lead_unverified)
    await db_session.commit()

    check1 = await safe_mailer.can_send_email(db_session, lead_unverified)
    assert check1["allowed"] is False
    assert "not verified" in check1["reason"]

    # 2. Test verified email allowed
    lead_verified = Lead(
        campaign_id="test-camp-1",
        company_name="Verified Corp",
        domain="verified.com",
        contact_email="test@verified.com",
        email_status="verified",
        intent_platform="b2b_search",
        intent_source_url="https://verified.com",
    )
    db_session.add(lead_verified)
    await db_session.commit()

    check2 = await safe_mailer.can_send_email(db_session, lead_verified)
    assert check2["allowed"] is True

    # 3. Test suppressed email blocked
    supp = SuppressionList(
        email="test@verified.com",
        domain="verified.com",
        reason="manual_optout",
    )
    db_session.add(supp)
    await db_session.commit()

    check3 = await safe_mailer.can_send_email(db_session, lead_verified)
    assert check3["allowed"] is False
    assert "suppression" in check3["reason"]


@pytest.mark.asyncio
async def test_safe_mailer_dry_run_dispatch(db_session: AsyncSession):
    camp = Campaign(id="camp-dry-run", name="Test Camp", target_url="https://leadforge.ai")
    db_session.add(camp)

    lead = Lead(
        id="lead-dry-1",
        campaign_id="camp-dry-run",
        company_name="DryRun Corp",
        domain="dryrun.com",
        contact_email="dispatch@dryrun.com",
        email_status="verified",
        intent_platform="b2b_search",
        intent_source_url="https://dryrun.com",
    )
    db_session.add(lead)
    await db_session.flush()

    msg = OutreachMessage(
        id="msg-dry-1",
        lead_id="lead-dry-1",
        channel="email",
        subject="Quick question",
        body_step1="Hi Elena, saw your post regarding Salesforce.",
        status="draft",
    )
    db_session.add(msg)
    await db_session.commit()

    dispatch_res = await safe_mailer.dispatch_message(db_session, "msg-dry-1", dry_run=True)
    assert dispatch_res["success"] is True
    assert dispatch_res["mode"] == "dry_run"
    assert "dispatch@dryrun.com" in dispatch_res["recipient"]

    # Verify message status updated in DB
    refreshed_msg = await db_session.get(OutreachMessage, "msg-dry-1")
    assert refreshed_msg.status == "sent_dry_run"
    assert refreshed_msg.sent_at is not None
