import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.campaigns import ACTIVE_CAMPAIGN_PROGRESS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Stream"])


async def event_generator(campaign_id: str) -> AsyncGenerator[str, None]:
    last_log_count = 0
    poll_iterations = 0

    while True:
        poll_iterations += 1
        progress = ACTIVE_CAMPAIGN_PROGRESS.get(campaign_id, {
            "status": "profiling",
            "progress_percent": 10,
            "logs": ["Connecting to LeadForge Multi-Agent Pipeline..."],
            "completed": False,
            "error": None,
        })

        logs = progress.get("logs", [])
        new_logs = logs[last_log_count:]
        last_log_count = len(logs)

        event_payload = {
            "campaign_id": campaign_id,
            "status": progress.get("status", "running"),
            "progress_percent": progress.get("progress_percent", 0),
            "new_logs": new_logs,
            "all_logs": logs,
            "completed": progress.get("completed", False),
            "error": progress.get("error"),
        }

        yield f"data: {json.dumps(event_payload)}\n\n"

        if progress.get("completed", False) or progress.get("status") in ["completed", "error"]:
            yield f"event: done\ndata: {json.dumps({'message': 'Workflow finished'})}\n\n"
            break

        # Max polling safety limit (6 minutes)
        if poll_iterations > 360:
            yield f"event: timeout\ndata: {json.dumps({'message': 'Stream timeout'})}\n\n"
            break

        await asyncio.sleep(1.0)


@router.get("/campaigns/{id}/stream")
async def stream_campaign_progress(id: str):
    """
    Streams LangGraph step events, node executions, and logs in real-time
    via Server-Sent Events (SSE) to the frontend progress bar.
    """
    return StreamingResponse(
        event_generator(id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
