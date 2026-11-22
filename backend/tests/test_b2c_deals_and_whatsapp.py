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
    compute_loot_score,
    parse_subtag_metadata,
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
async def test_revenue_clicks_by_step_summary(async_client):
    resp = await async_client.get("/api/revenue/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "clicks_by_step" in data
    assert "step1_morning" in data["clicks_by_step"]
    assert "step2_evening" in data["clicks_by_step"]


@pytest.mark.asyncio
async def test_buyhatke_loot_score_calculation():
    from app.core.deal_analyzer import compute_loot_score, evaluate_deal_quality

    # High impulse, deep discount loot deal
    deal = {
        "title": "Pigeon 1.8L Stainless Steel Electric Kettle",
        "category": "Home & Kitchen",
        "effective_price": 599.0,
        "mrp": 1499.0,
        "discount_pct": 60,
        "rating": 4.4,
        "review_count": 18200,
    }
    loot = compute_loot_score(deal)
    assert loot["loot_score"] >= 80
    assert loot["is_mega_loot"] is True
    assert "MEGA LOOT" in loot["loot_badge"]
    assert "reasons" in loot
    assert len(loot["reasons"]) >= 3

    # Gated quality check includes loot score
    quality = evaluate_deal_quality(deal)
    assert "loot_score" in quality
    assert "loot_badge" in quality
    assert quality["is_mega_loot"] is True


@pytest.mark.asyncio
async def test_lemlist_multi_angle_copy_generation():
    from app.core.deal_analyzer import generate_multi_angle_copy

    deal = {
        "asin": "B002MPPTB8",
        "title": "Hawkins Futura Hard Anodised Pressure Cooker 3L",
        "brand": "Hawkins",
        "category": "Home & Kitchen",
        "effective_price": 2499.0,
        "mrp": 3350.0,
        "discount_pct": 25,
        "rating": 4.4,
        "review_count": 28400,
    }
    res_wa = generate_multi_angle_copy(deal, channel="whatsapp")
    assert "angles" in res_wa
    angles = res_wa["angles"]
    assert "urgency_loot" in angles
    assert "savings_math" in angles
    assert "social_proof" in angles
    assert "daily_utility" in angles

    assert "FLASH LOOT" in angles["urgency_loot"]["message"]
    assert "SAVINGS MATH" in angles["savings_math"]["message"]
    assert "VERIFIED BUYER" in angles["social_proof"]["message"]
    assert "STEAL DEAL" in angles["daily_utility"]["message"]

    # Test Telegram format
    res_tg = generate_multi_angle_copy(deal, channel="telegram")
    assert "**" in res_tg["angles"]["urgency_loot"]["message"]


@pytest.mark.asyncio
async def test_deals_angles_and_dispatch_endpoints(async_client):
    # 1. Angles endpoint
    resp_angles = await async_client.get("/api/deals/B002MPPTB8/angles?channel=whatsapp")
    assert resp_angles.status_code == 200
    data_a = resp_angles.json()
    assert data_a["status"] == "success"
    assert "angles" in data_a
    assert "urgency_loot" in data_a["angles"]

    # 2. Dispatch simulated Telegram alert
    resp_disp = await async_client.post("/api/deals/dispatch-telegram", json={
        "asin": "B002MPPTB8",
        "step_number": 1,
        "channel_id": "@dealsforindia"
    })
    assert resp_disp.status_code == 200
    data_d = resp_disp.json()
    assert data_d["status"] == "dispatched_simulated"
    assert "n8n_curl_example" in data_d

    # 3. Daily deals outbox
    resp_outbox = await async_client.get("/api/deals/outbox/daily")
    assert resp_outbox.status_code == 200
    data_o = resp_outbox.json()
    assert "cadence" in data_o
    assert "morning_hero" in data_o["cadence"]
    assert "evening_impulse" in data_o["cadence"]
    assert "scarcity_closer" in data_o["cadence"]


@pytest.mark.asyncio
async def test_device_and_app_telemetry_summary(async_client):
    resp = await async_client.get("/api/revenue/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "clicks_by_device" in data
    assert "mobile_android" in data["clicks_by_device"]
    assert "clicks_by_app" in data
    assert "whatsapp" in data["clicks_by_app"]
    assert "goal_progress" in data
    assert data["goal_progress"]["target_commission_inr"] == 1000000.0
    assert "step3_scarcity" in data["clicks_by_step"]


@pytest.mark.asyncio
async def test_generate_audience_copy_and_variants():
    from app.core.deal_analyzer import generate_audience_copy, generate_all_audience_variants

    deal = {
        "asin": "B002MPPTB8",
        "title": "Hawkins Futura Hard Anodised Pressure Cooker 3L",
        "brand": "Hawkins",
        "category": "Home & Kitchen",
        "effective_price": 2499.0,
        "mrp": 3350.0,
        "discount_pct": 25,
        "rating": 4.4,
        "review_count": 28400,
    }

    # Test Homemaker variant
    c_home = generate_audience_copy(deal, audience="homemaker", channel="whatsapp")
    msg_home = c_home["message"]
    assert "Kitchen Upgrade" in msg_home or "Pantry" in msg_home or "Family" in msg_home or "Hawkins" in msg_home
    assert "₹2,499" in msg_home or "2499" in msg_home

    # Test Hostel variant
    c_hostel = generate_audience_copy(deal, audience="hostel", channel="whatsapp")
    msg_hostel = c_hostel["message"]
    assert "Hostel" in msg_hostel or "Jugaad" in msg_hostel or "Roommates" in msg_hostel or "Pocket Money" in msg_hostel

    # Test Office variant
    c_office = generate_audience_copy(deal, audience="office", channel="whatsapp")
    msg_office = c_office["message"]
    assert "Desk" in msg_office or "Commute" in msg_office or "Office" in msg_office or "Working" in msg_office

    # Test Budget variant
    c_budget = generate_audience_copy(deal, audience="budget", channel="whatsapp")
    msg_budget = c_budget["message"]
    assert "PRICE CRASH" in msg_budget or "LOOT" in msg_budget or "DISCOUNT" in msg_budget

    # Test generate_all_audience_variants
    all_vars = generate_all_audience_variants(deal, channel="whatsapp")
    assert len(all_vars["variants"]) == 4
    aud_keys = list(all_vars["variants"].keys())
    assert "homemaker" in aud_keys
    assert "hostel_college" in aud_keys
    assert "office_pro" in aud_keys
    assert "budget_impulse" in aud_keys


@pytest.mark.asyncio
async def test_dispatch_whatsapp_and_n8n_workflow_template(async_client):
    # 1. WhatsApp Evolution API payload generator
    resp_wa = await async_client.post("/api/deals/dispatch-whatsapp", json={
        "asin": "B002MPPTB8",
        "step_number": 1,
        "audience": "homemaker",
        "group_jid": "120363024849204829@g.us",
        "instance_name": "BharatBazaro_Main"
    })
    assert resp_wa.status_code == 200
    data_wa = resp_wa.json()
    assert data_wa["status"] == "prepared"
    assert "evolution_api_payload" in data_wa
    assert data_wa["evolution_api_payload"]["number"] == "120363024849204829@g.us"
    assert "baileys_payload" in data_wa
    assert "curl_command" in data_wa
    assert "anti_ban_warnings" in data_wa
    assert len(data_wa["anti_ban_warnings"]) >= 3

    # 2. n8n Workflow Template JSON
    resp_n8n = await async_client.get("/api/deals/n8n-workflow-template")
    assert resp_n8n.status_code == 200
    data_n8n = resp_n8n.json()
    assert "workflow" in data_n8n
    assert data_n8n["workflow"]["name"] == "BharatBazaro Deal Alert Telegram Bot"
    assert "nodes" in data_n8n["workflow"]
    node_names = [n["name"] for n in data_n8n["workflow"]["nodes"]]
    assert "Deal Webhook Trigger" in node_names
    assert "Telegram Bot Broadcast" in node_names


@pytest.mark.asyncio
async def test_dispatch_queue_and_mark_sent(async_client):
    # 1. Fetch dispatch queue
    resp_q = await async_client.get("/api/deals/dispatch-queue")
    assert resp_q.status_code == 200
    data_q = resp_q.json()
    assert "date" in data_q
    assert "slots" in data_q
    assert len(data_q["slots"]) == 3
    slot1 = data_q["slots"][0]
    assert slot1["slot_id"] == "s1_morning"
    assert "audience_variants_whatsapp" in slot1
    assert "audience_variants_telegram" in slot1

    # 2. Mark slot as sent
    resp_mark = await async_client.post("/api/deals/mark-sent", json={
        "slot_id": "s1_morning",
        "asin": slot1["asin"],
        "channel": "whatsapp",
        "audience": "homemaker",
        "subtag": slot1["unique_subtag"]
    })
    assert resp_mark.status_code == 200
    data_mark = resp_mark.json()
    assert data_mark["success"] is True
    assert data_mark["subtag"] == slot1["unique_subtag"]
    assert data_mark["channel"] == "whatsapp"

    # 3. Fetch dispatch queue again and verify marked sent
    resp_q2 = await async_client.get("/api/deals/dispatch-queue")
    data_q2 = resp_q2.json()
    assert data_q2["slots"][0]["is_sent"] is True


@pytest.mark.asyncio
async def test_historical_clicks_feedback_loop():
    from app.core.deal_analyzer import compute_loot_score

    deal = {
        "title": "AGARO Regency Air Fryer 12L",
        "category": "Home & Kitchen",
        "effective_price": 7499.0,
        "mrp": 15999.0,
        "discount_pct": 53,
        "rating": 4.5,
        "review_count": 12800,
    }

    base = compute_loot_score(deal)
    base_score = base["loot_score"]

    # 1. High clicks boost (+15 pts)
    boosted = compute_loot_score(deal, historical_clicks=30)
    assert boosted["loot_score"] == min(100, base_score + 15)
    assert any("High-Velocity Leader" in r for r in boosted["reasons"])

    # 2. Moderate clicks boost (+8 pts)
    mod_boost = compute_loot_score(deal, historical_clicks=15)
    assert mod_boost["loot_score"] == min(100, base_score + 8)
    assert any("Consistent Click Performer" in r for r in mod_boost["reasons"])

    # 3. Low clicks penalty on previously dispatched deal (-10 pts)
    penalized = compute_loot_score(deal, historical_clicks=0, is_previously_dispatched=True)
    assert penalized["loot_score"] == max(0, base_score - 10)
    assert any("Low Velocity Penalty" in r for r in penalized["reasons"])


@pytest.mark.asyncio
async def test_deal_freshness_and_safety_checks():
    from app.core.deal_analyzer import check_deal_freshness_and_safety, validate_deal_copy

    # 1. Stale deal (>24h)
    stale_deal = {
        "effective_price": 999.0,
        "discount_pct": 40,
        "category": "Home & Kitchen",
        "deal_age_hours": 36.0,
    }
    res_stale = check_deal_freshness_and_safety(stale_deal)
    assert res_stale["is_stale"] is True
    assert res_stale["price_bounce_risk"] is True
    assert any("exceeds 24 hours" in w for w in res_stale["warnings"])

    # 2. High-ticket deal (>₹2,999)
    high_ticket_deal = {
        "effective_price": 8499.0,
        "discount_pct": 40,
        "category": "Home & Kitchen",
        "deal_age_hours": 2.0,
    }
    res_ht = check_deal_freshness_and_safety(high_ticket_deal)
    assert res_ht["in_impulse_range"] is False
    assert res_ht["price_status"] == "TOO_HIGH"
    assert any("High ticket price" in w for w in res_ht["warnings"])

    # 3. Optimal impulse deal (₹199 - ₹1,499)
    optimal_deal = {
        "effective_price": 599.0,
        "discount_pct": 50,
        "category": "Home & Kitchen",
        "deal_age_hours": 4.0,
    }
    res_opt = check_deal_freshness_and_safety(optimal_deal)
    assert res_opt["is_safe_to_broadcast"] is True
    assert res_opt["price_status"] == "OPTIMAL_IMPULSE"

    # 4. Integrated in validate_deal_copy
    val_res = validate_deal_copy(
        text="🔥 Special Deal: ₹599 https://www.amazon.in/dp/B002MPPTB8?tag=dammaiprasad-21&ascsubtag=lf-wa-test",
        affiliate_url="https://www.amazon.in/dp/B002MPPTB8?tag=dammaiprasad-21&ascsubtag=lf-wa-test",
        deal=optimal_deal,
    )
    assert val_res["valid"] is True
    assert "freshness_safety" in val_res


@pytest.mark.asyncio
async def test_revenue_channel_performance_and_next_post_suggestion(async_client):
    resp = await async_client.get("/api/revenue/summary")
    assert resp.status_code == 200
    data = resp.json()

    # Phase 3: Channel performance comparison
    assert "channel_performance" in data
    cp = data["channel_performance"]
    assert "whatsapp" in cp
    assert "telegram" in cp
    assert "clicks" in cp["whatsapp"]
    assert "cvr_estimate" in cp["whatsapp"]
    assert "recommended_channel" in cp

    # Phase 3: AI Recommended next post
    assert "recommended_next_post" in data
    rnp = data["recommended_next_post"]
    assert "time_slot" in rnp
    assert "channel" in rnp
    assert "audience" in rnp
    assert "rationale" in rnp

    # Phase 4: Daily pace indicator
    assert "daily_pace_indicator" in data
    dpi = data["daily_pace_indicator"]
    assert "target_commission_today_inr" in dpi
    assert dpi["target_commission_today_inr"] > 10000
    assert "target_sales_today" in dpi
    assert dpi["target_sales_today"] == 120
    assert "remaining_sales_needed_today" in dpi
    assert "pace_percentage" in dpi

    # Phase 5: Daily checklist
    assert "daily_checklist" in data
    checklist = data["daily_checklist"]
    assert len(checklist) == 5
    task_ids = [c["id"] for c in checklist]
    assert "step_morning_hero" in task_ids
    assert "step_evening_impulse" in task_ids
    assert "step_night_scarcity" in task_ids


@pytest.mark.asyncio
async def test_order_based_learning_api_and_csv_import(async_client):
    # 1. Manual order logging
    order_payload = {
        "subtag": "lf-wa-homemaker-20261122-b002mpptb8",
        "asin": "B002MPPTB8",
        "order_id": "402-9988771-1234567",
        "items_count": 2,
        "revenue_inr": 4998.0,
        "commission_inr": 399.84,
        "channel": "whatsapp",
        "audience": "homemaker",
        "notes": "Verified Prime Order from WhatsApp Homemaker VIP",
    }
    resp = await async_client.post("/api/deals/orders/log", json=order_payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["order"]["asin"] == "B002MPPTB8"
    assert res_data["order"]["items_count"] == 2
    assert res_data["order"]["commission_inr"] == 399.84

    # 2. Bulk CSV upload
    csv_text = """subtag,asin,items_count,revenue_inr,commission_inr
lf-wa-hostel-20261122-b08v5q4x1c,B08V5Q4X1C,3,1197.0,95.76
lf-tg-20261122-b091cr2fxy-bi,B091CR2FXY,1,349.0,27.92"""
    csv_resp = await async_client.post("/api/deals/orders/upload-csv", json={"csv_text": csv_text})
    assert csv_resp.status_code == 200
    csv_data = csv_resp.json()
    assert csv_data["success"] is True
    assert csv_data["orders_imported_count"] == 2
    assert csv_data["total_commission_inr"] > 100

    # 3. List orders
    list_resp = await async_client.get("/api/deals/orders")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total_confirmed_orders"] >= 3
    assert list_data["total_confirmed_commission_inr"] >= 400.0
    assert len(list_data["orders"]) >= 3


def test_loot_score_order_learning_feedback():
    sample_deal = {
        "effective_price": 599.0,
        "mrp": 1299.0,
        "discount_pct": 54,
        "rating": 4.3,
        "review_count": 2500,
        "category": "Home & Kitchen",
    }
    # Base score without order data
    base = compute_loot_score(sample_deal)
    base_score = base["loot_score"]

    # 1. Boost for proven high converter (>=5 orders) -> +25 pts
    high_conv = compute_loot_score(sample_deal, historical_orders=6, conversion_rate=5.2)
    assert high_conv["feedback_adjustment"] == 25
    assert high_conv["loot_score"] >= min(100, base_score + 25)
    assert any("Proven High Converter" in r for r in high_conv["reasons"])

    # 2. Boost for proven converter (>=1 order) -> +15 pts
    conv = compute_loot_score(sample_deal, historical_orders=2, conversion_rate=3.5)
    assert conv["feedback_adjustment"] == 15
    assert conv["loot_score"] >= min(100, base_score + 15)

    # 3. Penalty for zero conversion on 50+ clicks -> -20 pts
    zero_conv = compute_loot_score(sample_deal, historical_clicks=60, historical_orders=0)
    assert zero_conv["feedback_adjustment"] == -20
    assert zero_conv["loot_score"] == max(0, base_score - 20)
    assert any("Zero Conversion Alert" in r for r in zero_conv["reasons"])


@pytest.mark.asyncio
async def test_zero_conversion_alerts_and_root_cause_diagnosis(async_client):
    # Simulate high clicks on a high ticket deal without orders
    subtag = "lf-wa-20261122-b09w2gfm7y-hm"
    for _ in range(55):
        await async_client.post("/api/deals/click", json={
            "asin": "B09W2GFM7Y",
            "channel": "whatsapp",
            "subtag": subtag,
        })

    resp = await async_client.get("/api/deals/zero-conversion-alerts?threshold_clicks=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["alerts_count"] >= 1
    alert = next((a for a in data["alerts"] if a["subtag"] == subtag), data["alerts"][0])
    assert alert["clicks"] >= 50
    assert alert["orders"] == 0
    assert "root_cause_diagnosis" in alert
    assert "recommended_action" in alert


@pytest.mark.asyncio
async def test_audience_subtag_parsing_and_revenue_summary(async_client):
    # 1. Parse subtag metadata
    hm = parse_subtag_metadata("lf-wa-homemaker-20261122-b002mpptb8")
    assert hm["channel"] == "whatsapp"
    assert hm["audience"] == "homemaker"
    assert hm["asin"] == "B002MPPTB8"

    hc = parse_subtag_metadata("lf-wa-hostel-b08v5q4x1c")
    assert hc["audience"] == "hostel_college"

    op = parse_subtag_metadata("lf-tg-20261122-b091cr2fxy-op")
    assert op["channel"] == "telegram"
    assert op["audience"] == "office_pro"

    bi = parse_subtag_metadata("lf-wa-20261122-b002mpptb8-bi")
    assert bi["audience"] == "budget_impulse"

    # 2. Revenue summary check
    resp = await async_client.get("/api/revenue/summary")
    assert resp.status_code == 200
    rev = resp.json()
    assert "actual_confirmed_orders" in rev
    assert "actual_confirmed_commission_inr" in rev
    assert "actual_conversion_rate_pct" in rev
    assert "zero_conversion_alerts" in rev
    assert "audience_performance" in rev
    assert len(rev["audience_performance"]) >= 4
    audiences = [a["audience"] for a in rev["audience_performance"]]
    assert "homemaker" in audiences
    assert "budget_impulse" in audiences



