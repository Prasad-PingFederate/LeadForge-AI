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
    generate_channel_subtag,
    evaluate_deal_quality,
    generate_where_to_post_recommendations,
    get_channel_performance_weights,
    generate_3step_sequence,
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


def test_unique_channel_subtags():
    sub_wa = generate_channel_subtag("whatsapp", asin="b002mpptb8")
    assert sub_wa.startswith("lf-wa-")
    assert "b002mpptb8" in sub_wa

    sub_tg = generate_channel_subtag("telegram", asin="b091cr2fxy")
    assert sub_tg.startswith("lf-tg-")
    assert "b091cr2fxy" in sub_tg

    sub_camp = generate_channel_subtag("whatsapp", campaign_id="camp12345")
    assert sub_camp.startswith("lf-wa-")
    assert "camp1234" in sub_camp

    sub_rd = generate_channel_subtag("reddit")
    assert sub_rd.startswith("lf-rd-")


@pytest.mark.asyncio
async def test_revenue_and_click_tracking(async_client: AsyncClient):
    # 1. Post click
    click_payload = {
        "asin": "B002MPPTB8",
        "channel": "whatsapp",
        "subtag": "lf-wa-20261122-b002mpptb8",
    }
    resp_click = await async_client.post("/api/deals/click", json=click_payload)
    assert resp_click.status_code == 201
    assert resp_click.json()["success"] is True

    # 2. Get Revenue Summary with Posts Attribution (Feature 1)
    resp_rev = await async_client.get("/api/revenue/summary")
    assert resp_rev.status_code == 200
    rev_data = resp_rev.json()
    assert rev_data["target_commission_inr"] == 1000000.0
    assert rev_data["total_clicks"] >= 1
    assert "clicks_by_channel" in rev_data
    assert rev_data["clicks_by_channel"]["whatsapp"] >= 1
    assert len(rev_data["recent_deals"]) > 0
    assert "posts_attribution" in rev_data
    assert len(rev_data["posts_attribution"]) > 0
    first_post = rev_data["posts_attribution"][0]
    assert "short_url" in first_post
    assert "est_commission_1pct" in first_post
    assert "est_commission_1_5pct" in first_post

    # 3. Test HTTP 302 Short link redirects (/r/, /go/, /a/)
    resp_redir_r = await async_client.get("/r/lf-wa-20261122-b002mpptb8", follow_redirects=False)
    assert resp_redir_r.status_code == 302
    assert "amazon.in" in resp_redir_r.headers["location"]
    assert "dammaiprasad-21" in resp_redir_r.headers["location"]

    resp_redir_go = await async_client.get("/go/lf-wa-20261122-b002mpptb8", follow_redirects=False)
    assert resp_redir_go.status_code == 302
    assert "amazon.in" in resp_redir_go.headers["location"]

    resp_redir_a = await async_client.get("/a/B002MPPTB8", follow_redirects=False)
    assert resp_redir_a.status_code == 302
    assert "amazon.in" in resp_redir_a.headers["location"]
    assert "B002MPPTB8" in resp_redir_a.headers["location"]


def test_deal_quality_filter():
    # Good impulse deal -> PROMOTE
    good_deal = {
        "title": "Pigeon Electric Kettle",
        "category": "Home & Kitchen",
        "effective_price": 599.0,
        "discount_pct": 60,
        "rating": 4.4,
        "review_count": 18200,
    }
    res_good = evaluate_deal_quality(good_deal)
    assert res_good["verdict"] == "PROMOTE"
    assert "🟢" in res_good["verdict_badge"]

    # 0% commission mobile -> KILL
    mobile_deal = {
        "title": "OnePlus 12 5G",
        "category": "Smartphones",
        "effective_price": 64999.0,
        "discount_pct": 10,
        "rating": 4.5,
        "review_count": 2200,
    }
    res_mobile = evaluate_deal_quality(mobile_deal)
    assert res_mobile["verdict"] == "KILL"
    assert "0%" in res_mobile["reason"]

    # Expensive kitchen item (>3000) with good discount -> HOLD
    high_ticket = {
        "title": "Bosch 12 Place Dishwasher",
        "category": "Home & Kitchen",
        "effective_price": 38999.0,
        "discount_pct": 40,
        "rating": 4.5,
        "review_count": 3200,
    }
    res_high = evaluate_deal_quality(high_ticket)
    assert res_high["verdict"] in ["HOLD", "PROMOTE"]


def test_where_to_post_recommendations():
    recs = generate_where_to_post_recommendations("Home & Kitchen", 599.0, "Kettle")
    # All 5 WhatsApp group personas required by Phase 2
    wa_types = [g["type"] for g in recs["whatsapp_groups"]]
    assert "Homemaker" in wa_types
    assert "Hostel" in wa_types
    assert "Budget" in wa_types
    assert "Office" in wa_types
    assert "College" in wa_types

    # Telegram Indian Deal Alerts
    assert any("indiandealalerts" in ch["handle"] or "lootdeals" in ch["handle"] for ch in recs["telegram_channels"])

    # Subreddits
    sub_names = [s["name"] for s in recs["subreddits"]]
    assert "r/dealsforindia" in sub_names
    assert "r/GadgetsIndia" in sub_names

    # X Hashtags
    assert "#AmazonDeals" in recs["hashtags"]
    assert "#Loot" in recs["hashtags"]
    assert "#PriceDrop" in recs["hashtags"]
    assert "best_posting_window" in recs


def test_channel_performance_learning_weights():
    # High WhatsApp clicks -> higher WhatsApp discovery multiplier
    weights = get_channel_performance_weights({"whatsapp": 85, "telegram": 15, "reddit": 5, "x": 2})
    assert weights["whatsapp"] > weights["x"]
    assert weights["whatsapp"] >= 1.5


def test_3step_sequence_generator():
    deal = {
        "title": "Pigeon 1.8L Electric Kettle",
        "effective_price": 599.0,
        "mrp": 1499.0,
        "asin": "B09W2GFM7Y",
        "rating": 4.4,
        "review_count": 18200,
        "category": "Home & Kitchen",
    }
    seq = generate_3step_sequence(deal)
    assert "step1_morning" in seq
    assert "step2_evening" in seq
    assert "step3_followup" in seq

    # Step 1 Morning
    assert "☀️" in seq["step1_morning"]["title"]
    assert "599" in seq["step1_morning"]["message"]
    assert "-s1" in seq["step1_morning"]["subtag"]

    # Step 2 Evening Impulse (<₹499 / flash)
    assert "🌙" in seq["step2_evening"]["title"]
    assert "-s2" in seq["step2_evening"]["subtag"]

    # Step 3 Follow-up / Scarcity
    assert "🚨" in seq["step3_followup"]["message"]
    assert "-s3" in seq["step3_followup"]["subtag"]


@pytest.mark.asyncio
async def test_n8n_export_endpoint(async_client: AsyncClient):
    # Test POST /api/deals/export-n8n
    resp_post = await async_client.post("/api/deals/export-n8n?limit=10")
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["status"] == "success"
    assert data_post["count"] > 0
    first = data_post["deals"][0]
    for field in ["asin", "title", "price", "mrp", "discount", "affiliate_url", "whatsapp_message", "telegram_message", "unique_tag"]:
        assert field in first
        assert first[field] is not None
    assert "dammaiprasad-21" in first["affiliate_url"]

    # Test GET /api/deals/export-n8n
    resp_get = await async_client.get("/api/deals/export-n8n?limit=5")
    assert resp_get.status_code == 200
    assert resp_get.json()["count"] > 0


@pytest.mark.asyncio
async def test_daily_performance_summary(async_client: AsyncClient):
    resp = await async_client.get("/api/revenue/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "daily_performance" in data
    dp = data["daily_performance"]

    # 1. Top 3 deals
    assert "top_3_deals" in dp
    assert len(dp["top_3_deals"]) == 3

    # 2. Best performing channel
    assert "best_performing_channel" in dp
    assert "whatsapp" in dp["best_performing_channel"]["channel"].lower()

    # 3. Pace vs target
    assert "pace_vs_target" in dp
    assert dp["pace_vs_target"]["daily_target_runrate"] > 0

    # 4. Remaining posts needed today
    assert "remaining_posts_needed_today" in dp
    assert dp["remaining_posts_needed_today"]["daily_quota"] == 80


def test_strict_promote_gate_criteria():
    # Deal missing review threshold (<500) -> CANNOT BE PROMOTE
    deal_low_reviews = {
        "title": "New Brand Blender",
        "category": "Home & Kitchen",
        "effective_price": 799.0,
        "discount_pct": 50,
        "rating": 4.5,
        "review_count": 120,  # Below 500
    }
    res_low = evaluate_deal_quality(deal_low_reviews)
    assert res_low["verdict"] != "PROMOTE"
    assert res_low["verdict"] == "HOLD"

    # Deal missing discount (<35%) -> CANNOT BE PROMOTE
    deal_low_disc = {
        "title": "Premium Cooker",
        "category": "Home & Kitchen",
        "effective_price": 1299.0,
        "discount_pct": 20,  # Below 35%
        "rating": 4.5,
        "review_count": 4500,
    }
    res_disc = evaluate_deal_quality(deal_low_disc)
    assert res_disc["verdict"] != "PROMOTE"

    # Deal passing all 5 criteria -> STRICTLY PROMOTE
    deal_perfect = {
        "title": "Pigeon Kettle",
        "category": "Home & Kitchen",
        "effective_price": 599.0,
        "discount_pct": 60,
        "rating": 4.4,
        "review_count": 18200,
    }
    res_perf = evaluate_deal_quality(deal_perfect)
    assert res_perf["verdict"] == "PROMOTE"
    assert "Strict Sales Standard passed" in res_perf["reason"]


@pytest.mark.asyncio
async def test_composite_velocity_score_and_pool_tier():
    from app.core.deal_analyzer import evaluate_deal_quality

    deal_high = {
        "title": "Pigeon Kettle",
        "category": "Home & Kitchen",
        "effective_price": 599.0,
        "discount_pct": 60,
        "rating": 4.4,
        "review_count": 18200,
    }
    res = evaluate_deal_quality(deal_high)
    assert "composite_velocity_score" in res
    assert res["composite_velocity_score"] >= 70
    assert "Tier 1" in res["pool_tier"]
    assert "score_breakdown" in res
    assert res["score_breakdown"]["total_score"] == res["composite_velocity_score"]


@pytest.mark.asyncio
async def test_validate_deal_copy_engine():
    from app.core.deal_analyzer import validate_deal_copy
    from app.config import settings

    valid_text = (
        f"🔥 *TODAY'S VERIFIED PRICE DROP* 🔥\n\n"
        f"Pigeon Kettle 1.8L\n"
        f"📉 Deal Price: ₹599 ~MRP ₹1,499~ (60% OFF!)\n"
        f"👉 Check Deal on Amazon: https://www.amazon.in/dp/B09W2GFM7Y?tag={settings.amazon_affiliate_tag}&ascsubtag=lf-wa-20261122-b09w2gfm7y"
    )
    res_valid = validate_deal_copy(valid_text, f"https://www.amazon.in/dp/B09W2GFM7Y?tag={settings.amazon_affiliate_tag}&ascsubtag=lf-wa")
    assert res_valid["valid"] is True
    assert res_valid["compliance_score"] == 100
    assert res_valid["has_affiliate_tag"] is True
    assert res_valid["has_price_disclosure"] is True

    # Invalid text missing affiliate tag
    invalid_text = "Check out this product on some website without tags."
    res_invalid = validate_deal_copy(invalid_text, "https://example.com")
    assert res_invalid["valid"] is False
    assert len(res_invalid["warnings"]) > 0


@pytest.mark.asyncio
async def test_pool_ladder_live_deals_filtering():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/deals/live?verdict=PROMOTE")
        assert resp.status_code == 200
        data = resp.json()
        assert "pool_ladder" in data
        assert "promote" in data["pool_ladder"]
        assert "hold" in data["pool_ladder"]
        assert "kill" in data["pool_ladder"]
        for d in data["deals"]:
            assert d["quality_verdict"]["verdict"] == "PROMOTE"


@pytest.mark.asyncio
async def test_activity_feed_endpoint():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/revenue/activity-feed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["activity_feed"]) > 0
        first_item = data["activity_feed"][0]
        assert "channel" in first_item
        assert "subtag" in first_item
        assert "est_commission_rupees" in first_item
        assert "step_label" in first_item


@pytest.mark.asyncio
async def test_clay_waterfall_enrichment():
    from app.core.deal_analyzer import waterfall_deal_enrichment, evaluate_deal_quality

    deal = {
        "title": "Hawkins Futura Hard Anodised Pressure Cooker 3L",
        "category": "Home & Kitchen",
        "effective_price": 2499.0,
        "mrp": 3350.0,
        "discount_pct": 25,
        "rating": 4.4,
        "review_count": 28400,
    }
    wf = waterfall_deal_enrichment(deal)
    assert "tier1_pricing_yield" in wf
    assert "tier2_trust_proof" in wf
    assert "tier3_velocity_urgency" in wf
    assert "why_it_converts" in wf
    assert "Hawkins" in wf["why_it_converts"]
    assert "9.0% commission" in wf["why_it_converts"] or "9% commission" in wf["why_it_converts"]

    # Verify integrated in evaluate_deal_quality
    eq = evaluate_deal_quality(deal)
    assert "waterfall_enrichment" in eq
    assert "why_it_converts" in eq
    assert eq["why_it_converts"] == wf["why_it_converts"]


@pytest.mark.asyncio
async def test_instantly_3step_sequence_delays_and_conditions():
    from app.core.deal_analyzer import generate_3step_sequence

    deal = {
        "title": "AGARO Regency Air Fryer 12L",
        "asin": "B091CR2FXY",
        "category": "Home & Kitchen",
        "effective_price": 7499.0,
        "mrp": 15999.0,
        "discount_pct": 53,
        "rating": 4.5,
        "review_count": 12800,
    }
    seq = generate_3step_sequence(deal)
    s1 = seq["step1_morning"]
    s2 = seq["step2_evening"]
    s3 = seq["step3_followup"]

    assert s1["step_number"] == 1
    assert s1["delay_hours"] == 0
    assert "08:30" in s1["send_window_ist"]
    assert s1["is_conditional"] is False
    assert "telegram_message" in s1

    assert s2["step_number"] == 2
    assert s2["delay_hours"] == 10
    assert "18:30" in s2["send_window_ist"]
    assert s2["is_conditional"] is False
    assert "telegram_message" in s2

    assert s3["step_number"] == 3
    assert s3["delay_hours"] == 26
    assert s3["is_conditional"] is True
    assert "telegram_message" in s3


@pytest.mark.asyncio
async def test_revenue_clicks_by_step_summary():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/revenue/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "clicks_by_step" in data
        assert "step1_morning" in data["clicks_by_step"]
        assert "step2_evening" in data["clicks_by_step"]
        assert "step3_scarcity" in data["clicks_by_step"]
