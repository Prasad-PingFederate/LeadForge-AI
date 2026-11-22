import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import SuppressionList, Lead
from app.workers.mailer import verify_unsubscribe_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Compliance"])


class SuppressionCreate(BaseModel):
    domain: Optional[str] = None
    email: Optional[str] = None
    reason: str = "manual_block"


@router.get("/unsubscribe")
async def unsubscribe_endpoint(
    email: str = Query(..., description="Email address to unsubscribe"),
    token: Optional[str] = Query(None, description="HMAC verification token"),
    session: AsyncSession = Depends(get_db),
):
    clean_email = email.strip().lower()
    domain = clean_email.split("@")[1] if "@" in clean_email else ""

    # Check token if provided
    if token and not verify_unsubscribe_token(clean_email, token):
        logger.warning(f"Unsubscribe token mismatch for {clean_email}")

    # Add to suppression list if not already present
    existing = await session.execute(
        select(SuppressionList).where(SuppressionList.email == clean_email)
    )
    if not existing.scalars().first():
        supp = SuppressionList(
            domain=domain,
            email=clean_email,
            reason="user_unsubscribed",
        )
        session.add(supp)

    # Update any existing leads
    leads = await session.execute(
        select(Lead).where(Lead.contact_email == clean_email)
    )
    for lead in leads.scalars().all():
        lead.status = "unsubscribed"

    await session.commit()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unsubscribed — LeadForge AI</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #09090b; color: #f4f4f5; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .box {{ background: #18181b; border: 1px solid #27272a; padding: 40px; border-radius: 12px; max-width: 480px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ font-size: 1.5rem; margin-bottom: 12px; color: #10b981; }}
            p {{ font-size: 0.95rem; color: #a1a1aa; line-height: 1.5; }}
            .email-badge {{ background: #27272a; color: #e4e4e7; padding: 4px 10px; border-radius: 6px; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>✓ Successfully Unsubscribed</h1>
            <p>You will no longer receive outreach messages at <span class="email-badge">{clean_email}</span>.</p>
            <p style="font-size: 0.8rem; margin-top: 24px; color: #71717a;">LeadForge AI Compliance Guard • Global Suppression Enforced</p>
        </div>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")


@router.get("/suppression")
async def list_suppression_list(session: AsyncSession = Depends(get_db)):
    stmt = select(SuppressionList).order_by(desc(SuppressionList.created_at)).limit(100)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/suppression")
async def add_to_suppression_list(
    payload: SuppressionCreate,
    session: AsyncSession = Depends(get_db),
):
    if not payload.domain and not payload.email:
        raise HTTPException(status_code=400, detail="Must provide at least domain or email")

    supp = SuppressionList(
        domain=payload.domain.strip().lower() if payload.domain else None,
        email=payload.email.strip().lower() if payload.email else None,
        reason=payload.reason,
    )
    session.add(supp)
    await session.commit()
    await session.refresh(supp)
    return supp
