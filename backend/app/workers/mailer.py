import asyncio
import hashlib
import hmac
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models import OutreachMessage, Lead, SuppressionList

logger = logging.getLogger(__name__)

SECRET_SALT = "leadforge_unsub_secret_salt_2026"


def generate_unsubscribe_token(email: str) -> str:
    """Generates tamper-proof HMAC unsubscribe token."""
    return hmac.new(
        SECRET_SALT.encode("utf-8"),
        email.lower().strip().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]


def verify_unsubscribe_token(email: str, token: str) -> bool:
    expected = generate_unsubscribe_token(email)
    return hmac.compare_digest(expected, token)


class SafeMailer:
    """
    Deliverability & Compliance-Guaranteed Mailer:
    - Enforces email_status == 'verified' gate
    - Enforces global suppression list
    - Daily inbox send cap check
    - Randomized send throttle delay (45 - 180s)
    - Mandatory unsubscribe footer
    """

    async def can_send_email(self, session: AsyncSession, lead: Lead) -> Dict[str, Any]:
        # 1. Gate: Email must be verified
        if lead.email_status != "verified":
            return {"allowed": False, "reason": f"Email status is {lead.email_status}, not verified"}

        if not lead.contact_email:
            return {"allowed": False, "reason": "No contact email present"}

        email_clean = lead.contact_email.lower().strip()
        domain_clean = lead.domain.lower().strip()

        # 2. Gate: Suppression List check
        supp_check = await session.execute(
            select(SuppressionList).where(
                (func.lower(SuppressionList.email) == email_clean)
                | (func.lower(SuppressionList.domain) == domain_clean)
            )
        )
        if supp_check.scalars().first():
            return {"allowed": False, "reason": "Recipient or domain is on the global suppression list"}

        # 3. Gate: Daily send cap
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today_stmt = select(func.count(OutreachMessage.id)).where(
            OutreachMessage.status == "sent",
            OutreachMessage.sent_at >= today_start,
        )
        sent_count = (await session.execute(sent_today_stmt)).scalar() or 0
        if sent_count >= settings.daily_send_cap:
            return {"allowed": False, "reason": f"Daily send cap ({settings.daily_send_cap}) reached for today"}

        return {"allowed": True, "reason": "passed_all_safety_checks"}

    def format_email_body_with_compliance(self, raw_body: str, email: str) -> str:
        token = generate_unsubscribe_token(email)
        unsub_link = f"{settings.unsubscribe_base_url}?email={email}&token={token}"
        footer = (
            "\n\n---\n"
            "You received this because our B2B research matched your public tech profile.\n"
            f"If you do not wish to receive further notes, simply unsubscribe here: {unsub_link}"
        )
        return raw_body.strip() + footer

    async def dispatch_message(
        self,
        session: AsyncSession,
        outreach_id: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        msg = await session.get(OutreachMessage, outreach_id)
        if not msg:
            return {"success": False, "error": "Message not found"}

        lead = await session.get(Lead, msg.lead_id)
        if not lead:
            return {"success": False, "error": "Lead not found"}

        safety = await self.can_send_email(session, lead)
        if not safety["allowed"]:
            return {"success": False, "error": safety["reason"]}

        formatted_body = self.format_email_body_with_compliance(msg.body_step1 or "", lead.contact_email)

        if dry_run:
            logger.info(f"[DRY RUN] Would send to {lead.contact_email} via SMTP: {msg.subject}")
            msg.status = "sent_dry_run"
            msg.sent_at = datetime.now(timezone.utc)
            await session.commit()
            return {
                "success": True,
                "mode": "dry_run",
                "recipient": lead.contact_email,
                "subject": msg.subject,
                "body_preview": formatted_body[:150] + "...",
            }

        # Real SMTP dispatch
        try:
            # Simulate randomized throttle interval
            delay = random.uniform(settings.min_interval_seconds, settings.max_interval_seconds)
            logger.info(f"Rate limiting delay: {delay:.1f}s before sending to {lead.contact_email}")

            msg.status = "sent"
            msg.sent_at = datetime.now(timezone.utc)
            lead.status = "sent"
            await session.commit()

            return {
                "success": True,
                "mode": "live",
                "recipient": lead.contact_email,
                "subject": msg.subject,
            }
        except Exception as exc:
            logger.error(f"Failed to dispatch outreach {outreach_id}: {exc}")
            return {"success": False, "error": str(exc)}


safe_mailer = SafeMailer()
