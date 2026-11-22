import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.connectors.intent_social import IntentSocialConnector
from app.connectors.b2b_discovery import B2BDiscoveryConnector


@pytest.mark.asyncio
async def test_intent_social_hn_algolia_parsing():
    connector = IntentSocialConnector()
    mock_hn_payload = {
        "hits": [
            {
                "objectID": "12345678",
                "title": "Ask HN: What is your favorite alternative to Salesforce?",
                "author": "devfounder",
                "story_text": "Looking for a modern, lightweight CRM without per-user licensing.",
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_hn_payload

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        results = await connector._search_hackernews("Salesforce alternative", limit=2)
        assert len(results) == 1
        item = results[0]
        assert item["intent_platform"] == "hackernews"
        assert item["intent_source_url"] == "https://news.ycombinator.com/item?id=12345678"
        assert "devfounder" in item["contact_name"]
        assert "CRM" in item["intent_snippet"]
        assert "Salesforce" in item["raw_title"]


@pytest.mark.asyncio
async def test_intent_social_reddit_parsing():
    connector = IntentSocialConnector()
    mock_reddit_payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc1234",
                        "title": "Frustrated with Zendesk pricing",
                        "selftext": "Anyone migrated off Zendesk to an open source or modern tool?",
                        "author": "tech_lead_99",
                        "permalink": "/r/SaaS/comments/abc1234/frustrated_with_zendesk_pricing/",
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_reddit_payload

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        results = await connector._search_reddit("Zendesk alternative", limit=2)
        assert len(results) == 1
        item = results[0]
        assert item["intent_platform"] == "reddit"
        assert item["intent_source_url"] == "https://reddit.com/r/SaaS/comments/abc1234/frustrated_with_zendesk_pricing/"
        assert "tech_lead_99" in item["contact_name"]


@pytest.mark.asyncio
async def test_b2b_discovery_connector():
    connector = B2BDiscoveryConnector()
    mock_search_results = [
        {"title": "Google Search", "domain": "google.com", "url": "https://google.com"},
        {"title": "Acme Logix - B2B Supply Chain", "domain": "acmelogix.com", "url": "https://acmelogix.com", "snippet": "Leading supply chain software."},
        {"title": "CloudScale Systems", "domain": "cloudscale.io", "url": "https://cloudscale.io", "snippet": "Cloud infrastructure optimization."},
    ]

    with patch("app.connectors.web_search.web_search_connector.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_search_results

        leads = await connector.search("supply chain software", limit=5)
        # Google should be filtered out
        domains = [l["domain"] for l in leads]
        assert "google.com" not in domains
        assert "acmelogix.com" in domains
        assert "cloudscale.io" in domains
        assert all(l["intent_platform"] == "b2b_search" for l in leads)
        assert all(l["intent_source_url"].startswith("http") for l in leads)
