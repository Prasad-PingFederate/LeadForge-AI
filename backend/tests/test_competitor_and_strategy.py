import pytest
from unittest.mock import AsyncMock, patch
from app.agents.competitor_agent import competitor_agent


@pytest.mark.asyncio
async def test_competitor_agent_analysis():
    mock_search_results = [
        {
            "title": "Top 5 Alternatives to LegacySaaS in 2026",
            "url": "https://reddit.com/r/saas/comments/legacysaas_alternatives",
            "snippet": "Users are complaining about LegacySaaS pricing doubling and clunky UI.",
        },
        {
            "title": "Why we migrated away from OldCRM",
            "url": "https://news.ycombinator.com/item?id=3829102",
            "snippet": "We cut our bill from $80/user to $15 by finding a lightweight alternative.",
        }
    ]

    with patch("app.connectors.web_search.web_search_connector.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_search_results

        icp_data = {
            "product_name": "SwiftFlow",
            "category": "Workflow Automation",
            "value_proposition": "Automate sales workflows with zero per-seat fees.",
            "core_pain_points": ["Expensive seat fees", "Clunky UI"],
        }

        intel = await competitor_agent.analyze_competitors_and_strategies(icp_data)

        assert "competitors" in intel
        assert "strategies" in intel
        assert len(intel["competitors"]) >= 1
        assert len(intel["strategies"]) == 3

        # Validate Battlecard structure
        comp = intel["competitors"][0]
        assert "name" in comp
        assert "strengths" in comp
        assert "weaknesses" in comp
        assert "displacement_angle" in comp
        assert isinstance(comp["strengths"], list)
        assert isinstance(comp["weaknesses"], list)

        # Validate 3 Strategies structure
        for strat in intel["strategies"]:
            assert "title" in strat
            assert "channel" in strat
            assert "angle" in strat
            assert "target_queries" in strat
            assert isinstance(strat["target_queries"], list)


@pytest.mark.asyncio
async def test_competitor_agent_fallback_on_empty():
    with patch("app.connectors.web_search.web_search_connector.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []

        with patch("app.core.llm.llm_client.generate_json", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {"competitors": [], "strategies": []}

            intel = await competitor_agent.analyze_competitors_and_strategies({"product_name": "TestTool"})
            assert len(intel["competitors"]) >= 1
            assert len(intel["strategies"]) == 3
            assert intel["strategies"][0]["title"] is not None
