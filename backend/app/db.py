"""
db.py — SQLAlchemy engine, session factory, and declarative base.

Usage:
    from app.db import get_session, Base

    # In routers:
    async def endpoint(session: AsyncSession = Depends(get_session)): ...

    # In scripts / startup:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# Convert plain sqlite:/// URL to the async sqlite+aiosqlite:/// variant.
_db_url = settings.database_url
if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite+aiosqlite"):
    _db_url = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

# Ensure the data directory exists (SQLite needs the parent dir).
_db_path = _db_url.replace("sqlite+aiosqlite:///", "")
if _db_path and not _db_path.startswith(":"):
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_session() -> AsyncSession:  # type: ignore[return]
    """Yield an AsyncSession; roll back on error, close on exit."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
