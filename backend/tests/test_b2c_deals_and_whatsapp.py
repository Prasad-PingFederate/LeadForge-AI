import pytest
from app.core.deal_analyzer import (
    extract_asin,
    to_canonical_affiliate_url,
    compute_commission_estimate,
    format_whatsapp_deal_post,
    format_telegram_deal_post,
    fetch_live_deals,
    get_deal_by_asin,
    search_live_deals,
    get_top_converting_deals,
)
from app.core.cache import TTLCache
from app.agents.profiler_agent import profiler_agent
from app.agents.competitor_agent import competitor_agent
from httpx import AsyncClient


def test_extract_asin():
    assert extract_asin("B09W2GFM7Y") == "B09W2GFM7Y"
    assert extract_asin("https://www.amazon.in/dp/B09W2GFM7Y/ref=deal") == "B09W2GFM7Y"
    assert extract_asin("https://www.amazon.in/gp/product/B08N5WRWNW") == "B08N5WRWNW"
    assert extract_asin("https://bharatbazaro.com") is None


def test_canonical_affiliate_url():
    url = to_canonical_affiliate_url("B09W2GFM7Y", subtag="test-sub")
    assert "tag=dammaiprasad-21" in url
    assert "ascsubtag=test-sub" in url
    assert "amazon.in/dp/B09W2GFM7Y" in url


def test_commission_estimation():
    home = compute_commission_estimate("Home & Kitchen", 799.0)
    assert home["commission_rate_percent"] == 9.0
    assert home["is_impulse_sweet_spot"] is True
    assert home["is_zero_roi"] is False

    mobile = compute_commission_estimate("Smartphones", 45000.0)
    assert mobile["commission_rate_percent"] == 0.0
    assert mobile["is_zero_roi"] is True


def test_whatsapp_deal_post_formatting():
    post = format_whatsapp_deal_post(
        title="Pigeon 1.8L Electric Kettle",
        deal_price=599.0,
        mrp=1499.0,
        asin="B09W2GFM7Y",
        rating=4.4,
        reviews_count=12500,
    )

    assert "*TODAY'S VERIFIED PRICE DROP*" in post
    assert "Pigeon 1.8L Electric Kettle" in post
    assert "Deal Price: ₹599" in post
    assert "MRP ₹1,499" in post
    assert "60% OFF" in post
    assert "You Save: ₹900" in post
    assert "tag=dammaiprasad-21" in post


def test_telegram_deal_post_formatting():
    post = format_telegram_deal_post(
        title="Philips Air Fryer 4.1L",
        deal_price=4999.0,
        mrp=9999.0,
        asin="B07VXYZ123",
    )

    assert "PRICE DROP ALERT" in post
    assert "Philips Air Fryer" in post
    assert "₹4,999" in post
    assert "tag=dammaiprasad-21" in post


def test_ttl_cache():
    cache = TTLCache(default_ttl_seconds=10)
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar"
    assert cache.get("non-existent") is None


@pytest.mark.asyncio
async def test_profiler_agent_b2c_deals_mode():
    res = await profiler_agent.profile_product(
        url="https://www.amazon.in/dp/B09W2GFM7Y",
        user_description="Electric Kettle deal drop on Amazon",
        campaign_type="b2c_deals",
    )

    assert "product_name" in res
    assert "deal_metadata" in res
    assert res["deal_metadata"]["asin"] == "B09W2GFM7Y"
    assert "dammaiprasad-21" in res["deal_metadata"]["canonical_affiliate_url"]


@pytest.mark.asyncio
async def test_competitor_agent_b2c_deals_mode():
    icp_data = {
        "product_name": "Rapid-Boil Electric Kettle",
        "category": "Home & Kitchen",
        "deal_metadata": {"asin": "B09W2GFM7Y"},
    }

    intel = await competitor_agent.analyze_competitors_and_strategies(
        icp_data, campaign_type="b2c_deals"
    )

    assert len(intel["competitors"]) >= 1
    assert len(intel["strategies"]) == 3
    channels = [s["channel"].lower() for s in intel["strategies"]]
    assert "whatsapp" in channels or "telegram" in channels


@pytest.mark.asyncio
async def test_fetch_live_deals_feed():
    deals = await fetch_live_deals()
    assert isinstance(deals, list)
    assert len(deals) >= 5
    first = deals[0]
    assert "asin" in first
    assert "effective_price" in first
    assert "title" in first


@pytest.mark.asyncio
async def test_get_deal_by_asin():
    # Test lookup of known item
    deal = await get_deal_by_asin("B002MPPTB8")
    assert deal is not None
    assert deal["asin"] == "B002MPPTB8"
    assert "Hawkins" in deal.get("title", "") or "Hawkins" in deal.get("brand", "")

    # Non-existent ASIN
    bad_deal = await get_deal_by_asin("NONEXIST01")
    assert bad_deal is None


@pytest.mark.asyncio
async def test_search_and_top_live_deals():
    kettle_deals = await search_live_deals(query="kettle", limit=5)
    assert isinstance(kettle_deals, list)

    top_deals = await get_top_converting_deals(limit=5)
    assert len(top_deals) >= 1
    assert "effective_price" in top_deals[0]


@pytest.mark.asyncio
async def test_deals_api_endpoints(async_client: AsyncClient):
    # GET /api/deals/live
    resp = await async_client.get("/api/deals/live?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] <= 5
    assert "deals" in data
    assert len(data["deals"]) > 0
    first = data["deals"][0]
    assert "dammaiprasad-21" in first["canonical_affiliate_url"]
    assert "commission_info" in first

    # GET /api/deals/top-converting
    resp_top = await async_client.get("/api/deals/top-converting?limit=3")
    assert resp_top.status_code == 200
    assert len(resp_top.json()["deals"]) > 0

    # GET /api/deals/live/{asin}
    test_asin = first["asin"]
    resp_detail = await async_client.get(f"/api/deals/live/{test_asin}")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["asin"] == test_asin
