import pytest
from app.core.deal_analyzer import (
    extract_asin,
    to_canonical_affiliate_url,
    compute_commission_estimate,
    format_whatsapp_deal_post,
    format_telegram_deal_post,
)
from app.core.cache import TTLCache
from app.agents.profiler_agent import profiler_agent
from app.agents.competitor_agent import competitor_agent


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
