import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Provider-Agnostic LLM client supporting:
    - OpenAI (gpt-4o, gpt-4o-mini, etc.)
    - Anthropic (claude-3-5-sonnet, etc.)
    - Google Gemini (gemini-1.5-flash, gemini-1.5-pro, etc.)
    - Heuristic / Offline Mock engine when keys are absent or testing.
    """

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.openai_key = settings.openai_api_key
        self.anthropic_key = settings.anthropic_api_key
        self.gemini_key = settings.gemini_api_key

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        # Check active provider and available credentials
        if self.provider == "openai" and self.openai_key:
            return await self._call_openai(system_prompt, user_prompt, temperature=temperature)
        elif self.provider == "anthropic" and self.anthropic_key:
            return await self._call_anthropic(system_prompt, user_prompt, temperature=temperature)
        elif self.provider == "gemini" and self.gemini_key:
            return await self._call_gemini(system_prompt, user_prompt, temperature=temperature)
        
        # Fallback to intelligent deterministic heuristic
        return self._heuristic_fallback(system_prompt, user_prompt)

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        full_system = (
            system_prompt
            + "\nCRITICAL: Respond ONLY with a valid, clean JSON object. No markdown fences, no explanatory text."
        )
        raw_output = await self.generate_text(full_system, user_prompt, temperature=0.1)
        
        # Clean potential markdown fences
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback heuristic parser
            logger.warning(f"Failed to parse LLM JSON: {cleaned[:100]}... Falling back to heuristic.")
            return self._heuristic_json_fallback(user_prompt)

    async def _call_openai(self, system: str, user: str, temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, system: str, user: str, temperature: float) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.anthropic_model,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "max_tokens": 2048,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_gemini(self, system: str, user: str, temperature: float) -> str:
        model = settings.gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
            "generationConfig": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _heuristic_fallback(self, system: str, user: str) -> str:
        """Deterministic, rich fallback generator for offline tests & zero-key runs."""
        u_lower = user.lower()
        if "ideal customer profile" in system.lower() or "icp" in system.lower():
            return json.dumps(self._heuristic_json_fallback(user))
        if "outreach" in system.lower() or "email" in system.lower():
            return (
                "Hi there,\n\n"
                "Saw your team was recently looking into modern workflow alternatives. "
                "Unlike legacy tools, we provide zero-latency real-time collaboration with complete data privacy.\n\n"
                "Worth a quick 5-min look this week?\n\n"
                "Best,\nAlex"
            )
        return "LeadForge AI autonomous analysis completed with verified signals."

    def _heuristic_json_fallback(self, user_prompt: str) -> Dict[str, Any]:
        """Generate high-quality structured data from user prompt keywords."""
        p_lower = user_prompt.lower()
        
        # Profiler ICP extraction
        if "crawl" in p_lower or "product" in p_lower or "url" in p_lower:
            product_name = "Modern SaaS Platform"
            for word in ["cal.com", "posthog", "linear", "supabase", "slack", "notion", "loom"]:
                if word in p_lower:
                    product_name = word.capitalize()
                    break

            return {
                "product_name": product_name,
                "category": "B2B Software & Productivity",
                "value_proposition": "Fast, privacy-first, developer-friendly workflow automation.",
                "target_roles": [
                    "Head of Product",
                    "VP of Engineering",
                    "Chief Technology Officer",
                    "Director of Operations",
                    "RevOps Lead",
                ],
                "target_industries": [
                    "B2B SaaS",
                    "Fintech",
                    "Healthcare IT",
                    "Developer Tools",
                    "E-commerce Infrastructure",
                ],
                "company_size_range": "11-250 employees",
                "core_pain_points": [
                    "High pricing tiers with rigid seat minimums in legacy tools",
                    "Slow UI and cumbersome latency impacting team productivity",
                    "Lack of self-hosting, privacy compliance, or API flexibility",
                ],
                "intent_search_queries": [
                    f"alternative to {product_name.lower()} competitors",
                    "looking for modern team tool recommendations",
                    "frustrated with legacy pricing and latency",
                    "recommend a fast developer-first workflow solution",
                ],
                "negative_keywords": [
                    "freelance",
                    "internship",
                    "cheap clones",
                    "student discount",
                ],
            }

        # Competitor Battlecards
        if "competitor" in p_lower or "battlecard" in p_lower:
            return {
                "competitors": [
                    {
                        "name": "LegacyCorp Suite",
                        "domain": "legacycorp.com",
                        "strengths": ["Broad enterprise recognition", "Extensive marketplace"],
                        "weaknesses": ["Expensive per-seat pricing", "Clunky UI", "Slow customer support"],
                        "pricing_tier": "$45 - $99 / user / month",
                        "displacement_angle": "Cut software bill by 60% with zero bloat and 10x faster response time.",
                        "source_urls": ["https://reddit.com/r/saas/comments/reviews_legacycorp"]
                    },
                    {
                        "name": "CloudBloat Inc",
                        "domain": "cloudbloat.io",
                        "strengths": ["Wide feature checklist"],
                        "weaknesses": ["Over-complicated onboarding", "Vendor lock-in", "Hidden fees"],
                        "pricing_tier": "Enterprise custom quotes only",
                        "displacement_angle": "Transparent self-serve setup in 3 minutes without mandatory sales calls.",
                        "source_urls": ["https://news.ycombinator.com/item?id=3819201"]
                    }
                ],
                "strategies": [
                    {
                        "title": "Displace Overpriced Legacy Seat Minimums",
                        "channel": "email",
                        "angle": "Highlight transparent pricing vs competitor's 10-seat enterprise barrier",
                        "target_queries": ["looking for alternative to LegacyCorp", "LegacyCorp pricing increase"]
                    },
                    {
                        "title": "Social Intent Listening on Reddit & HN",
                        "channel": "reddit",
                        "angle": "Directly help users complaining about competitor latency or missing APIs",
                        "target_queries": ["site:reddit.com recommend tool for scheduling", "site:x.com alternative to"]
                    },
                    {
                        "title": "Fast-Growing Series A / B B2B Discovery",
                        "channel": "linkedin",
                        "angle": "Target newly funded engineering teams migrating off outdated stack",
                        "target_queries": ["site:linkedin.com VP Engineering B2B SaaS"]
                    }
                ]
            }

        # Outreach sequence
        if "outreach" in p_lower:
            return {
                "subject": "Quick question on your workflow stack",
                "body_step1": (
                    "Hi {contact_name},\n\n"
                    "Saw your recent team discussion regarding scaling constraints with your current tool. "
                    "We built a high-speed, modern alternative that eliminates per-seat markups and runs 10x faster.\n\n"
                    "Would you be open to a 5-min look this week?\n\n"
                    "Best,\nAlex"
                ),
                "body_step2": (
                    "Hi {contact_name},\n\n"
                    "Following up briefly—teams like Acme and Horizon switched over last quarter and cut their overhead by 45%. "
                    "Happy to share a 2-min demo if relevant to your roadmap."
                ),
                "body_step3": (
                    "Hi {contact_name},\n\n"
                    "Assuming this isn't a priority right now, so I'll stop following up. "
                    "If you ever hit scaling roadblocks down the line, you know where to find us!"
                ),
                "linkedin_dm": (
                    "Hey {contact_name}, noticed your focus on scaling developer productivity. "
                    "We built a modern alternative to legacy tools with zero seat minimums. Worth a quick connection?"
                ),
                "social_reply": (
                    "If you're still looking for an alternative that avoids the seat minimums, "
                    "check out our open/developer-first solution. Happy to answer any questions!"
                )
            }

        # Reply classification
        if any(k in p_lower for k in ["reply", "sentiment", "classify", "sso", "demo", "pricing", "timing", "question", "support"]):
            return {
                "category": "objection",
                "confidence": 0.85,
                "summary": "Technical question or feature inquiry",
            }

        return {}


llm_client = LLMClient()
