import logging
from typing import Dict, Any, Optional

from app.core.llm import llm_client
from app.core.deal_analyzer import (
    format_whatsapp_deal_post,
    format_telegram_deal_post,
    format_reddit_deal_post,
    format_x_deal_post,
    to_canonical_affiliate_url,
    generate_channel_subtag,
    generate_3step_sequence,
)

logger = logging.getLogger(__name__)

OUTREACH_SYSTEM_PROMPT = """
You are a master B2B Cold Outreach Copywriter known for ultra-concise, signal-based copy that converts at 18%+.
Rules:
- NEVER write fluffy or generic corporate jargon ("Hope this email finds you well", "I wanted to reach out").
- Email Step 1 must be under 90 words and reference the exact competitor gap or intent signal.
- Include a specific, low-friction call-to-action (e.g., "Worth a 5-min look this week?").
- Generate:
  1. subject
  2. body_step1 (The signal-personalized hook)
  3. body_step2 (Value proof & quick customer example)
  4. body_step3 (Short, respectful breakup)
  5. linkedin_dm (Conversational, under 45 words)
  6. social_reply (Helpful, non-salesy public reply for Reddit/HN/X)

Return a clean JSON object:
{
  "subject": "Quick question on your workflow",
  "body_step1": "Hi {name},\\n\\n...",
  "body_step2": "Hi {name},\\n\\n...",
  "body_step3": "Hi {name},\\n\\n...",
  "linkedin_dm": "Hey {name}, ...",
  "social_reply": "If you are looking for an alternative..."
}
"""


class OutreachAgent:
    """Generates signal-personalized multi-channel outreach sequences for every verified lead."""

    async def draft_outreach_for_lead(
        self,
        lead: Dict[str, Any],
        icp_data: Optional[Dict[str, Any]] = None,
        displacement_angle: Optional[str] = None,
        campaign_type: str = "b2b",
    ) -> Dict[str, Any]:
        contact_name = lead.get("contact_name") or "there"
        company_name = lead.get("company_name", "your team")
        contact_role = lead.get("contact_role", "team lead")
        intent_snippet = lead.get("intent_snippet", "")
        intent_platform = lead.get("intent_platform", "web")

        icp = icp_data or {}
        product_name = icp.get("product_name", "our solution")
        value_prop = icp.get("value_proposition", "modern developer-first workflow automation")
        is_deal_mode = campaign_type == "b2c_deals" or "deal_metadata" in icp

        prompt = (
            f"Target Contact: {contact_name} ({contact_role} at {company_name})\n"
            f"Intent Platform: {intent_platform}\n"
            f"Live Intent Signal / Query: \"{intent_snippet}\"\n"
            f"Our Product: {product_name}\n"
            f"Our Core Value Proposition: {value_prop}\n"
            f"Competitor Displacement Angle: {displacement_angle or 'Save 50% on seat costs with zero latency.'}\n"
            f"Mode: {'B2C E-Commerce Deal (BharatBazaro)' if is_deal_mode else 'B2B Enterprise Lead Gen'}\n"
        )

        draft = await llm_client.generate_json(OUTREACH_SYSTEM_PROMPT, prompt)

        # Fallback values if LLM skipped fields
        if not draft.get("subject"):
            draft["subject"] = f"🔥 Verified Price Drop: {product_name[:30]}" if is_deal_mode else "Quick question on your workflow"
        if not draft.get("body_step1"):
            draft["body_step1"] = f"Hi {contact_name},\n\nSaw your team discussion regarding {intent_snippet[:50]}..."
        if not draft.get("body_step2"):
            draft["body_step2"] = f"Hi {contact_name},\n\nFollowing up briefly with more details on {product_name}."
        if not draft.get("body_step3"):
            draft["body_step3"] = f"Hi {contact_name},\n\nAssuming this isn't a priority right now, so I'll stop following up."
        if not draft.get("linkedin_dm"):
            draft["linkedin_dm"] = f"Hey {contact_name}, noticed your focus on {product_name}. Worth a quick connection?"
        if not draft.get("social_reply"):
            draft["social_reply"] = f"If you're looking for an alternative, check out {product_name}."

        # Generate WhatsApp, Telegram, Reddit, and X deal distribution formats with unique ascsubtags
        deal_meta = icp.get("deal_metadata") or {}
        asin = deal_meta.get("asin") or "B09W2GFM7Y"
        deal_price = float(deal_meta.get("effective_price") or deal_meta.get("deal_price") or 599.0)
        mrp = float(deal_meta.get("mrp") or 1499.0)
        rating = float(deal_meta.get("rating") or 4.3)
        reviews_count = int(deal_meta.get("review_count") or 4500)
        campaign_id = lead.get("campaign_id") or icp.get("campaign_id")

        wa_subtag = generate_channel_subtag("whatsapp", campaign_id=campaign_id, asin=asin)
        tg_subtag = generate_channel_subtag("telegram", campaign_id=campaign_id, asin=asin)
        rd_subtag = generate_channel_subtag("reddit", campaign_id=campaign_id, asin=asin)
        x_subtag = generate_channel_subtag("x", campaign_id=campaign_id, asin=asin)

        # 3-Step Sequence Generation (Feature 3)
        seq = generate_3step_sequence({
            "title": product_name,
            "effective_price": deal_price,
            "mrp": mrp,
            "asin": asin,
            "rating": rating,
            "review_count": reviews_count,
        }, campaign_id=campaign_id)

        deal_url = to_canonical_affiliate_url(asin, subtag=wa_subtag)

        draft["deal_affiliate_url"] = deal_url
        draft["subtag"] = wa_subtag
        draft["whatsapp_message"] = seq["step1_morning"]["message"]
        draft["telegram_message"] = format_telegram_deal_post(
            title=product_name,
            deal_price=deal_price,
            mrp=mrp,
            asin=asin,
            subtag=tg_subtag,
            campaign_id=campaign_id,
        )

        if is_deal_mode:
            draft["body_step1"] = seq["step1_morning"]["message"]
            draft["body_step2"] = seq["step2_evening"]["message"]
            draft["body_step3"] = seq["step3_followup"]["message"]
            draft["subject"] = f"🔥 Price Drop Alert: {product_name[:40]} down to ₹{int(deal_price):,}"
            draft["social_reply"] = format_reddit_deal_post(
                title=product_name,
                deal_price=deal_price,
                mrp=mrp,
                asin=asin,
                subtag=rd_subtag,
                campaign_id=campaign_id,
            )
            draft["linkedin_dm"] = format_x_deal_post(
                title=product_name,
                deal_price=deal_price,
                mrp=mrp,
                asin=asin,
                subtag=x_subtag,
                campaign_id=campaign_id,
            )

        draft["channel"] = "whatsapp" if is_deal_mode else "email"
        return draft


outreach_agent = OutreachAgent()
