"""
main.py — FastAPI application entry point.

Mounts all routers, configures CORS, and creates DB tables on startup.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.api.health import router as health_router

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
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health_router, prefix="/api")

# Future routers (added as phases complete):
# from app.api import auth, investigations, documents, claims, verify, ledger, reports, eval, share, jobs
# app.include_router(auth.router,            prefix="/api/auth",             tags=["auth"])
# app.include_router(investigations.router,  prefix="/api/investigations",   tags=["investigations"])
# app.include_router(documents.router,       prefix="/api",                  tags=["documents"])
# app.include_router(claims.router,          prefix="/api",                  tags=["claims"])
# app.include_router(verify.router,          prefix="/api",                  tags=["verify"])
# app.include_router(ledger.router,          prefix="/api",                  tags=["ledger"])
# app.include_router(reports.router,         prefix="/api",                  tags=["reports"])
# app.include_router(eval.router,            prefix="/api/eval",             tags=["eval"])
# app.include_router(share.router,           prefix="/api",                  tags=["share"])
# app.include_router(jobs.router,            prefix="/api/jobs",             tags=["jobs"])
