import json
import logging
from typing import Dict, Any, List

from langgraph.graph import StateGraph, END

from app.workflows.state import LeadForgeState
from app.agents.profiler_agent import profiler_agent
from app.agents.competitor_agent import competitor_agent
from app.agents.hunter_agent import hunter_agent
from app.agents.enrichment_agent import enrichment_agent
from app.agents.outreach_agent import outreach_agent

logger = logging.getLogger(__name__)


async def profiler_node(state: LeadForgeState) -> Dict[str, Any]:
    """Node 1: Crawl target URL and extract structured Ideal Customer Profile (ICP)."""
    url = state["target_url"]
    desc = state.get("description", "")
    logger.info(f"[Profiler Node] Analyzing {url}")

    icp_data = await profiler_agent.profile_product(url, desc)
    logs = list(state.get("logs", []))
    logs.append(f"✓ Crawled {url} and extracted ICP for {icp_data.get('product_name')}")

    return {
        "icp_data": icp_data,
        "current_step": "profiling_completed",
        "progress_percent": 25,
        "logs": logs,
    }


async def competitor_node(state: LeadForgeState) -> Dict[str, Any]:
    """Node 2: Real web search for competitors, battlecards & 3 GTM strategies."""
    icp_data = state["icp_data"]
    logger.info("[Competitor Node] Researching competitors and generating battlecards")

    intel = await competitor_agent.analyze_competitors_and_strategies(icp_data)
    competitors = intel.get("competitors", [])
    strategies = intel.get("strategies", [])

    logs = list(state.get("logs", []))
    comp_names = ", ".join(c.get("name", "") for c in competitors[:3])
    logs.append(f"✓ Analyzed competitors: {comp_names}")
    logs.append(f"✓ Formulated {len(strategies)} actionable GTM lead-gen strategies")

    return {
        "competitors": competitors,
        "strategies": strategies,
        "current_step": "competitor_analysis_completed",
        "progress_percent": 50,
        "logs": logs,
    }


async def hunter_node(state: LeadForgeState) -> Dict[str, Any]:
    """Node 3: Hunt real leads across Reddit, HN, and B2B web queries."""
    strategies = state.get("strategies", [])
    logger.info(f"[Hunter Node] Executing {len(strategies)} hunting strategies")

    raw_leads = await hunter_agent.hunt_leads_for_strategies(strategies, limit_per_strategy=4)
    logs = list(state.get("logs", []))
    logs.append(f"✓ Discovered {len(raw_leads)} real intent prospects across social and B2B channels")

    return {
        "raw_leads": raw_leads,
        "current_step": "lead_hunting_completed",
        "progress_percent": 75,
        "logs": logs,
    }


async def enricher_node(state: LeadForgeState) -> Dict[str, Any]:
    """Node 4: Deduplicate, waterfall audit, live DNS MX email verify, 0-100 scoring."""
    raw_leads = state.get("raw_leads", [])
    icp_data = state.get("icp_data", {})
    logger.info(f"[Enricher Node] Enriching and verifying {len(raw_leads)} leads")

    enriched = await enrichment_agent.enrich_and_score_leads(raw_leads, icp_data=icp_data)
    verified_count = sum(1 for l in enriched if l.get("email_status") == "verified")

    logs = list(state.get("logs", []))
    logs.append(f"✓ Enriched {len(enriched)} deduplicated leads ({verified_count} verified via DNS MX)")

    return {
        "enriched_leads": enriched,
        "current_step": "enrichment_completed",
        "progress_percent": 90,
        "logs": logs,
    }


async def outreach_node(state: LeadForgeState) -> Dict[str, Any]:
    """Node 5: Draft signal-personalized 3-step cold emails, LinkedIn DMs, social replies."""
    enriched_leads = state.get("enriched_leads", [])
    icp_data = state.get("icp_data", {})
    competitors = state.get("competitors", [])
    displacement_angle = competitors[0].get("displacement_angle") if competitors else None

    logger.info(f"[Outreach Node] Generating hyper-personalized outreach sequences")
    drafts = []

    # Generate outreach drafts for top verified leads
    for lead in enriched_leads[:10]:
        draft = await outreach_agent.draft_outreach_for_lead(
            lead=lead,
            icp_data=icp_data,
            displacement_angle=displacement_angle,
        )
        draft["lead_domain"] = lead.get("domain")
        draft["company_name"] = lead.get("company_name")
        draft["contact_email"] = lead.get("contact_email")
        drafts.append(draft)

    logs = list(state.get("logs", []))
    logs.append(f"✓ Generated {len(drafts)} personalized multi-step sequences in Human-Approval queue")

    return {
        "outreach_drafts": drafts,
        "current_step": "completed",
        "progress_percent": 100,
        "logs": logs,
    }


def build_leadforge_workflow():
    """Compiles the LangGraph StateGraph workflow."""
    workflow = StateGraph(LeadForgeState)

    workflow.add_node("profiler", profiler_node)
    workflow.add_node("competitor", competitor_node)
    workflow.add_node("hunter", hunter_node)
    workflow.add_node("enricher", enricher_node)
    workflow.add_node("outreach", outreach_node)

    workflow.set_entry_point("profiler")
    workflow.add_edge("profiler", "competitor")
    workflow.add_edge("competitor", "hunter")
    workflow.add_edge("hunter", "enricher")
    workflow.add_edge("enricher", "outreach")
    workflow.add_edge("outreach", END)

    return workflow.compile()


leadforge_graph = build_leadforge_workflow()
