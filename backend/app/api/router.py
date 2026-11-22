from fastapi import APIRouter

from app.api.campaigns import router as campaigns_router
from app.api.leads import router as leads_router
from app.api.outreach import router as outreach_router
from app.api.stream import router as stream_router
from app.api.unsubscribe import router as unsubscribe_router

api_router = APIRouter(prefix="/api")

api_router.include_router(campaigns_router)
api_router.include_router(leads_router)
api_router.include_router(outreach_router)
api_router.include_router(stream_router)
api_router.include_router(unsubscribe_router)
