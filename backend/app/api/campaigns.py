import asyncio
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db, AsyncSessionLocal
from app.db.models import Campaign, Competitor, Strategy, Lead, OutreachMessage
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignDetailResponse
from app.schemas.competitor import CompetitorResponse
from app.schemas.strategy import StrategyResponse
from app.workflows.leadforge_graph import leadforge_graph
from app.workflows.state import LeadForgeState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# In-memory progress tracking for SSE streaming
ACTIVE_CAMPAIGN_PROGRESS: dict = {}


async def run_campaign_workflow(campaign_id: str, target_url: str, description: str, campaign_type: str = "b2b"):
    """Executes the full multi-agent LangGraph pipeline and persists results into PostgreSQL/SQLite."""
    logger.info(f"Starting LangGraph workflow for campaign {campaign_id} (mode: {campaign_type})")
    ACTIVE_CAMPAIGN_PROGRESS[campaign_id] = {
        "status": "profiling",
        "progress_percent": 10,
        "logs": [f"🚀 Initialized Autonomous Agent pipeline for {target_url} (mode: {campaign_type})"],
        "completed": False,
        "error": None,
    }

    initial_state: LeadForgeState = {
        "campaign_id": campaign_id,
        "target_url": target_url,
        "campaign_type": campaign_type,
        "description": description or "",
        "deal_data": None,
        "icp_data": {},
        "competitors": [],
        "strategies": [],
        "raw_leads": [],
        "enriched_leads": [],
        "outreach_drafts": [],
        "current_step": "started",
        "progress_percent": 10,
        "logs": [f"🚀 Initialized Autonomous Agent pipeline for {target_url} ({campaign_type})"],
        "error": None,
    }

    try:
        final_state = await leadforge_graph.ainvoke(initial_state)

        # Update progress stream
        ACTIVE_CAMPAIGN_PROGRESS[campaign_id] = {
            "status": "completed",
            "progress_percent": 100,
            "logs": final_state.get("logs", []),
            "completed": True,
            "error": None,
        }

        # Persist results to DB
        async with AsyncSessionLocal() as session:
            campaign = await session.get(Campaign, campaign_id)
            if not campaign:
                return

            icp_result = final_state.get("icp_data", {})
            campaign.status = "completed"
            campaign.icp_json = json.dumps(icp_result)
            if "deal_metadata" in icp_result:
                campaign.deal_metadata_json = json.dumps(icp_result["deal_metadata"])

            # Save Competitors
            for comp in final_state.get("competitors", []):
                c_model = Competitor(
                    campaign_id=campaign_id,
                    name=comp.get("name", "Competitor"),
                    domain=comp.get("domain", ""),
                    strengths=json.dumps(comp.get("strengths", [])),
                    weaknesses=json.dumps(comp.get("weaknesses", [])),
                    pricing_tier=comp.get("pricing_tier", ""),
                    displacement_angle=comp.get("displacement_angle", ""),
                    source_urls_json=json.dumps(comp.get("source_urls", [])),
                )
                session.add(c_model)

            # Save Strategies
            strategy_models = {}
            for strat in final_state.get("strategies", []):
                s_model = Strategy(
                    campaign_id=campaign_id,
                    title=strat.get("title", "GTM Strategy"),
                    channel=strat.get("channel", "email"),
                    angle=strat.get("angle", ""),
                    target_queries_json=json.dumps(strat.get("target_queries", [])),
                    conversion_weight=1.0,
                )
                session.add(s_model)
                await session.flush()
                strategy_models[s_model.title] = s_model.id

            # Save Enriched Leads & Outreach Drafts
            lead_models = []
            for enriched in final_state.get("enriched_leads", []):
                strat_title = enriched.get("strategy_title")
                s_id = strategy_models.get(strat_title)

                lead_m = Lead(
                    campaign_id=campaign_id,
                    strategy_id=s_id,
                    company_name=enriched.get("company_name", ""),
                    domain=enriched.get("domain", ""),
                    contact_name=enriched.get("contact_name"),
                    contact_role=enriched.get("contact_role"),
                    contact_email=enriched.get("contact_email"),
                    email_status=enriched.get("email_status", "unverified"),
                    linkedin_url=enriched.get("linkedin_url"),
                    intent_platform=enriched.get("intent_platform", "b2b_search"),
                    intent_source_url=enriched.get("intent_source_url", ""),
                    intent_snippet=enriched.get("intent_snippet", ""),
                    fit_score=enriched.get("fit_score", 0),
                    intent_score=enriched.get("intent_score", 0),
                    verif_score=enriched.get("verif_score", 0),
                    overall_score=enriched.get("overall_score", 0),
                    score_breakdown_json=enriched.get("score_breakdown_json"),
                    why_this_lead=enriched.get("why_this_lead"),
                    status="new",
                )
                session.add(lead_m)
                lead_models.append(lead_m)

            await session.flush()

            # Save Outreach Messages matching leads
            for draft in final_state.get("outreach_drafts", []):
                match_lead = next((l for l in lead_models if l.domain == draft.get("lead_domain")), None)
                if match_lead:
                    msg = OutreachMessage(
                        lead_id=match_lead.id,
                        channel=draft.get("channel", "email"),
                        subject=draft.get("subject"),
                        body_step1=draft.get("body_step1"),
                        body_step2=draft.get("body_step2"),
                        body_step3=draft.get("body_step3"),
                        social_reply=draft.get("social_reply"),
                        linkedin_dm=draft.get("linkedin_dm"),
                        whatsapp_message=draft.get("whatsapp_message"),
                        telegram_message=draft.get("telegram_message"),
                        deal_affiliate_url=draft.get("deal_affiliate_url"),
                        status="draft",
                    )
                    session.add(msg)

            await session.commit()
            logger.info(f"Successfully saved campaign {campaign_id} results to DB")

    except Exception as exc:
        logger.error(f"Workflow failed for campaign {campaign_id}: {exc}", exc_info=True)
        ACTIVE_CAMPAIGN_PROGRESS[campaign_id] = {
            "status": "error",
            "progress_percent": 100,
            "logs": [f"❌ Error: {str(exc)}"],
            "completed": True,
            "error": str(exc),
        }
        async with AsyncSessionLocal() as session:
            campaign = await session.get(Campaign, campaign_id)
            if campaign:
                campaign.status = "error"
                campaign.error_message = str(exc)
                await session.commit()


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    url = payload.target_url.strip()
    name = payload.name or url.replace("https://", "").replace("http://", "").split("/")[0]

    campaign = Campaign(
        name=name,
        target_url=url,
        campaign_type=payload.campaign_type,
        description=payload.description or "",
        status="profiling",
    )
    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)

    # Launch background workflow
    background_tasks.add_task(
        run_campaign_workflow,
        campaign.id,
        campaign.target_url,
        campaign.description or "",
        campaign.campaign_type,
    )

    return campaign


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(session: AsyncSession = Depends(get_db)):
    stmt = select(Campaign).order_by(desc(Campaign.created_at))
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{id}", response_model=CampaignDetailResponse)
async def get_campaign_detail(id: str, session: AsyncSession = Depends(get_db)):
    campaign = await session.get(Campaign, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    comp_count = await session.scalar(select(func.count(Competitor.id)).where(Competitor.campaign_id == id)) or 0
    strat_count = await session.scalar(select(func.count(Strategy.id)).where(Strategy.campaign_id == id)) or 0
    lead_count = await session.scalar(select(func.count(Lead.id)).where(Lead.campaign_id == id)) or 0
    verif_count = await session.scalar(
        select(func.count(Lead.id)).where(Lead.campaign_id == id, Lead.email_status == "verified")
    ) or 0

    detail = CampaignDetailResponse.from_orm(campaign)
    detail.competitors_count = comp_count
    detail.strategies_count = strat_count
    detail.leads_count = lead_count
    detail.verified_leads_count = verif_count
    return detail


@router.get("/{id}/competitors", response_model=List[CompetitorResponse])
async def get_campaign_competitors(id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(Competitor).where(Competitor.campaign_id == id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{id}/strategies", response_model=List[StrategyResponse])
async def get_campaign_strategies(id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(Strategy).where(Strategy.campaign_id == id)
    result = await session.execute(stmt)
    return result.scalars().all()
