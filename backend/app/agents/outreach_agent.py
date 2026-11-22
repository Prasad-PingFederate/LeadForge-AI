import logging
from typing import Dict, Any, Optional

from app.core.llm import llm_client

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
        displacement_angle: Optional[str] = None
    ) -> Dict[str, Any]:
        contact_name = lead.get("contact_name") or "there"
        company_name = lead.get("company_name", "your team")
        contact_role = lead.get("contact_role", "team lead")
        intent_snippet = lead.get("intent_snippet", "")
        intent_platform = lead.get("intent_platform", "web")

        icp = icp_data or {}
        product_name = icp.get("product_name", "our solution")
        value_prop = icp.get("value_proposition", "modern developer-first workflow automation")

        prompt = (
            f"Target Contact: {contact_name} ({contact_role} at {company_name})\n"
            f"Intent Platform: {intent_platform}\n"
            f"Live Intent Signal / Query: \"{intent_snippet}\"\n"
            f"Our Product: {product_name}\n"
            f"Our Core Value Proposition: {value_prop}\n"
            f"Competitor Displacement Angle: {displacement_angle or 'Save 50% on seat costs with zero latency.'}\n"
        )

        result = await llm_client.generate_json(OUTREACH_SYSTEM_PROMPT, prompt)

        # Ensure placeholders are formatted
        formatted_result = {
            "channel": "email",
            "subject": result.get("subject", f"Quick question regarding {company_name}'s stack").replace("{name}", contact_name),
            "body_step1": (result.get("body_step1") or (
                f"Hi {contact_name},\n\n"
                f"Saw your recent team discussion regarding scaling constraints with your current tool. "
                f"We built {product_name} to provide a modern, high-speed alternative with zero per-seat markups.\n\n"
                f"Would you be open to a 5-min look this week?\n\n"
                f"Best,\nAlex"
            )).replace("{name}", contact_name).replace("{contact_name}", contact_name),
            "body_step2": (result.get("body_step2") or (
                f"Hi {contact_name},\n\n"
                f"Following up briefly—teams like Acme switched over last quarter and cut overhead by 45%. "
                f"Happy to share a 2-min demo if relevant to {company_name}'s roadmap."
            )).replace("{name}", contact_name).replace("{contact_name}", contact_name),
            "body_step3": (result.get("body_step3") or (
                f"Hi {contact_name},\n\n"
                f"Assuming this isn't a priority right now, so I'll stop following up. "
                f"If you ever hit scaling roadblocks down the line, feel free to reach out anytime."
            )).replace("{name}", contact_name).replace("{contact_name}", contact_name),
            "linkedin_dm": (result.get("linkedin_dm") or (
                f"Hey {contact_name}, noticed your focus on scaling productivity at {company_name}. "
                f"We built a modern alternative with zero seat minimums. Worth a quick connection?"
            )).replace("{name}", contact_name).replace("{contact_name}", contact_name),
            "social_reply": (result.get("social_reply") or (
                f"If you're still looking for an alternative that avoids per-seat penalties, "
                f"check out {product_name}. Happy to answer any technical questions!"
            )),
            "status": "draft",
        }

        return formatted_result


outreach_agent = OutreachAgent()
