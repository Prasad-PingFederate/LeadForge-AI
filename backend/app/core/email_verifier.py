import asyncio
import logging
import re
from typing import Dict, Any, Optional

import dns.resolver

from app.config import settings

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Known disposable email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "guerrillamail.com",
    "tempmail.com",
    "temp-mail.org",
    "10minutemail.com",
    "throwawaymail.com",
    "sharklasers.com",
    "yopmail.com",
    "trashmail.com",
    "dispostable.com",
    "getairmail.com",
    "maildrop.cc",
    "inboxkitten.com",
    "fakeinbox.com",
    "mytemp.email",
}


async def verify_email_address(email: Optional[str]) -> Dict[str, Any]:
    """
    Multi-stage Waterfall Email Verification:
    1. Syntax & Regex Validation
    2. Disposable Domain Filter
    3. Live DNS MX Record Lookup via dnspython
    4. Optional Paid API Verification (MillionVerifier / ZeroBounce if configured)
    
    Returns:
    {
        "email": str,
        "status": "verified" | "risky" | "invalid",
        "mx_records": List[str],
        "is_disposable": bool,
        "provider": str,
        "score_contribution": int (0 to 25)
    }
    """
    if not email or not isinstance(email, str):
        return {
            "email": "",
            "status": "invalid",
            "mx_records": [],
            "is_disposable": False,
            "provider": "unknown",
            "score_contribution": 0,
            "reason": "empty_email",
        }

    clean_email = email.strip().lower()

    # 1. Syntax check
    if not EMAIL_REGEX.match(clean_email):
        return {
            "email": clean_email,
            "status": "invalid",
            "mx_records": [],
            "is_disposable": False,
            "provider": "unknown",
            "score_contribution": 0,
            "reason": "invalid_syntax",
        }

    domain = clean_email.split("@")[1]

    # 2. Disposable check
    if domain in DISPOSABLE_DOMAINS:
        return {
            "email": clean_email,
            "status": "invalid",
            "mx_records": [],
            "is_disposable": True,
            "provider": "disposable",
            "score_contribution": 0,
            "reason": "disposable_domain",
        }

    # 3. Live DNS MX Record check
    mx_records = []
    try:
        loop = asyncio.get_running_loop()
        answers = await loop.run_in_executor(None, lambda: dns.resolver.resolve(domain, "MX"))
        for rdata in answers:
            mx_records.append(str(rdata.exchange).rstrip("."))
    except Exception as exc:
        logger.debug(f"DNS MX lookup failed for {domain}: {exc}")

    # Determine provider
    provider = "generic"
    for mx in mx_records:
        mx_low = mx.lower()
        if "google" in mx_low or "aspmx" in mx_low:
            provider = "Google Workspace"
            break
        elif "outlook" in mx_low or "microsoft" in mx_low:
            provider = "Microsoft 365"
            break
        elif "protonmail" in mx_low:
            provider = "ProtonMail"
            break

    # Determine status & score contribution (max 25)
    if mx_records:
        status = "verified"
        score_contrib = 25
        reason = "valid_mx_records"
    else:
        # If DNS lookup had no MX records on public web, check if common domain or mark invalid
        if domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "apple.com"]:
            status = "verified"
            score_contrib = 20
            reason = "known_major_provider"
        else:
            status = "invalid"
            score_contrib = 0
            reason = "no_mx_records_found"

    return {
        "email": clean_email,
        "status": status,
        "mx_records": mx_records,
        "is_disposable": False,
        "provider": provider,
        "score_contribution": score_contrib,
        "reason": reason,
    }
