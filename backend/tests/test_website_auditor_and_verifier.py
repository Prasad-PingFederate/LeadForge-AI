import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.email_verifier import verify_email_address
from app.connectors.website_auditor import WebsiteAuditorConnector


@pytest.mark.asyncio
async def test_email_verifier_empty():
    res = await verify_email_address(None)
    assert res["status"] == "invalid"
    assert res["score_contribution"] == 0

    res = await verify_email_address("")
    assert res["status"] == "invalid"
    assert res["score_contribution"] == 0


@pytest.mark.asyncio
async def test_email_verifier_invalid_syntax():
    res = await verify_email_address("invalid-email-address")
    assert res["status"] == "invalid"
    assert res["reason"] == "invalid_syntax"
    assert res["score_contribution"] == 0


@pytest.mark.asyncio
async def test_email_verifier_disposable_domain():
    res = await verify_email_address("hacker@mailinator.com")
    assert res["status"] == "invalid"
    assert res["is_disposable"] is True
    assert res["score_contribution"] == 0


@pytest.mark.asyncio
async def test_email_verifier_valid_with_mock_mx():
    mock_rdata = MagicMock()
    mock_rdata.exchange = "aspmx.l.google.com."

    with patch("dns.resolver.resolve", return_value=[mock_rdata]):
        res = await verify_email_address("founder@stripe.com")
        assert res["status"] == "verified"
        assert res["score_contribution"] == 25
        assert "Google Workspace" in res["provider"]
        assert "aspmx.l.google.com" in res["mx_records"]


@pytest.mark.asyncio
async def test_email_verifier_no_mx():
    with patch("dns.resolver.resolve", side_effect=Exception("NXDOMAIN")):
        res = await verify_email_address("someone@non-existent-domain-4982749.org")
        assert res["status"] == "invalid"
        assert res["reason"] == "no_mx_records_found"
        assert res["score_contribution"] == 0
        assert res["mx_records"] == []


@pytest.mark.asyncio
async def test_website_auditor_extracts_contact_info():
    auditor = WebsiteAuditorConnector()
    sample_html = """
    <html>
        <body>
            <p>Reach us at contact@fastscale.io or sales@fastscale.io</p>
            <a href="https://www.linkedin.com/company/fastscale-inc">Follow us on LinkedIn</a>
            <img src="logo.png" />
        </body>
    </html>
    """

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_html
        mock_get.return_value = mock_resp

        audit = await auditor.audit_company_domain("fastscale.io")
        assert "fastscale.io" in audit["domain"]
        assert "contact@fastscale.io" in audit["emails"]
        assert "https://www.linkedin.com/company/fastscale-inc" in audit["linkedin_urls"]
