import pytest
from unittest.mock import AsyncMock, patch
from app.core.crawler import crawl_url
from app.agents.profiler_agent import profiler_agent


@pytest.mark.asyncio
async def test_crawl_url_success():
    mock_html = """
    <html>
        <head>
            <title>Acme AI - Next-Gen CRM</title>
            <meta name="description" content="AI-powered sales platform for B2B enterprises." />
        </head>
        <body>
            <h1>Automate Your Outbound Sales</h1>
            <h2>Close More Deals Faster</h2>
            <p>Acme AI replaces slow manual prospecting with multi-agent intelligence.</p>
        </body>
    </html>
    """
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        res = await crawl_url("https://acmeai.io")
        assert res["success"] is True
        assert res["domain"] == "acmeai.io"
        assert res["title"] == "Acme AI - Next-Gen CRM"
        assert res["meta_description"] == "AI-powered sales platform for B2B enterprises."
        assert "Automate Your Outbound Sales" in res["headings"]
        assert "Close More Deals Faster" in res["headings"]
        assert "replaces slow manual prospecting" in res["content_text"]


@pytest.mark.asyncio
async def test_crawl_url_error_handling():
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
        res = await crawl_url("https://invalid-non-existent-domain-12345.xyz")
        assert res["success"] is False
        assert res["error"] is not None
        assert res["domain"] == "invalid-non-existent-domain-12345.xyz"


@pytest.mark.asyncio
async def test_profiler_agent_structured_icp():
    with patch("app.agents.profiler_agent.crawl_url") as mock_crawl:
        mock_crawl.return_value = {
            "url": "https://leadforge.ai",
            "domain": "leadforge.ai",
            "title": "LeadForge AI - Autonomous B2B Sales Platform",
            "meta_description": "Find real intent leads and automate hyper-personalized outreach.",
            "headings": ["Autonomous Prospecting", "Competitor Intelligence"],
            "content_text": "LeadForge AI crawls competitor gaps and extracts verified prospects.",
            "status_code": 200,
            "success": True,
        }

        icp = await profiler_agent.profile_product(
            url="https://leadforge.ai",
            user_description="Autonomous B2B Sales Agent platform"
        )

        assert "product_name" in icp
        assert "category" in icp
        assert "value_proposition" in icp
        assert isinstance(icp["target_roles"], list)
        assert len(icp["target_roles"]) > 0
        assert isinstance(icp["target_industries"], list)
        assert len(icp["target_industries"]) > 0
        assert isinstance(icp["intent_search_queries"], list)
