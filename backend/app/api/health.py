"""
api/health.py — Health-check route.

GET /api/health → {"status": "ok", "version": "<app version>"}
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])

_VERSION = "0.1.0"


@router.get("/health")
async def health() -> JSONResponse:
    """
    Lightweight liveness probe.

    Returns HTTP 200 with ``{"status": "ok"}`` when the backend is running.
    No DB query is made here so it stays fast even under load.
    """
    return JSONResponse({"status": "ok", "version": _VERSION})
