"""
main.py — FastAPI application entry point.

Mounts all routers, configures CORS, and creates DB tables on startup.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.facts import router as facts_router
from app.api.health import router as health_router
from app.api.investigations import router as investigations_router
from app.api.jobs import router as jobs_router
from app.api.ledger import router as ledger_router
from app.api.verify import router as verify_router
from app.config import get_settings
from app.db import Base, engine
import app.models.models  # ensure models are registered with Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables (no-op if they already exist) on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Graceful teardown (close engine connection pool).
    await engine.dispose()


app = FastAPI(
    title="ContradictIQ",
    description="Financial claim verification engine — LLM proposes, code disposes.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(investigations_router, prefix="/api/investigations", tags=["investigations"])
app.include_router(documents_router, prefix="/api", tags=["documents"])
app.include_router(facts_router, prefix="/api", tags=["facts"])
app.include_router(claims_router, prefix="/api", tags=["claims"])
app.include_router(verify_router, prefix="/api", tags=["verify"])
app.include_router(ledger_router, prefix="/api", tags=["ledger"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(jobs_router, prefix="/api", tags=["jobs"])
