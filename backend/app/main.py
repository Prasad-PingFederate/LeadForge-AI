import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.router import api_router
from app.api.revenue import router as revenue_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("leadforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    logger.info("Initializing LeadForge AI database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
    yield
    await engine.dispose()


app = FastAPI(
    title="LeadForge AI — Autonomous B2B Sales & Intelligence Platform",
    description="Autonomous ICP profiling, competitor battlecards, multi-source high-intent lead generation, and personalized outreach.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API
app.include_router(api_router)
app.include_router(revenue_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "LeadForge AI",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Autonomous B2B Sales, Competitor Intelligence & Lead-Generation Platform",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "db": "connected",
        "llm_provider": settings.llm_provider,
        "daily_send_cap": settings.daily_send_cap,
    }
