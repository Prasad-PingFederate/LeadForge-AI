import logging
from typing import Dict, Any, Tuple

from app.core.llm import llm_client

logger = logging.getLogger(__name__)

REPLY_CLASSIFICATION_PROMPT = """
You are a Sales Reply Sentiment Classifier.
Analyze the incoming prospect email/message reply.
Classify it into EXACTLY ONE of the following categories:
- "positive" (interested in a demo, call, more info, pricing)
- "objection" (interested but has concerns, pricing questions, feature questions)
- "not_now" (busy, check back in Q3/Q4, wrong timing)
- "unsubscribe" (not interested, remove me, stop emailing, unsubscribe)

Return a clean JSON object:
{
  "category": "positive" | "objection" | "not_now" | "unsubscribe",
  "confidence": 0.95,
  "summary": "Prospect requested a 15-min call next Tuesday"
}
"""


class LearningAgent:
    """
    Self-learning feedback loop:
    1. Classifies prospect replies
    2. Dynamically re-weights strategy conversion scores
    3. Triggers automated suppression on unsubscribe
    """

    async def classify_reply(self, reply_text: str) -> Dict[str, Any]:
        text_low = reply_text.lower().strip()

        # Heuristic fast-path
        if any(w in text_low for w in ["unsubscribe", "remove me", "stop emailing", "do not contact", "spam"]):
            return {"category": "unsubscribe", "confidence": 0.99, "summary": "Prospect requested removal"}
        if any(w in text_low for w in ["sounds good", "let's talk", "book time", "send a demo", "call", "schedule", "pricing"]):
            return {"category": "positive", "confidence": 0.92, "summary": "Prospect expressed buying interest"}
        if any(w in text_low for w in ["not right now", "next quarter", "circle back", "busy"]):
            return {"category": "not_now", "confidence": 0.88, "summary": "Timing objection / revisit later"}

        try:
            res = await llm_client.generate_json(REPLY_CLASSIFICATION_PROMPT, reply_text)
            if isinstance(res, dict) and res.get("category"):
                return res
        except Exception:
            pass
        return {"category": "objection", "confidence": 0.70, "summary": "General inquiry / objection"}

    def compute_weight_adjustment(self, current_weight: float, category: str) -> float:
        """
        Dynamically adjusts strategy weight so future lead-hunting runs
        allocate more search queries to top-converting angles.
        """
        if category == "positive":
            return round(current_weight + 0.35, 2)
        elif category == "objection":
            return round(current_weight + 0.05, 2)
        elif category == "not_now":
            return round(current_weight, 2)
        elif category == "unsubscribe":
            return round(max(0.2, current_weight - 0.25), 2)
        return current_weight


learning_agent = LearningAgent()
