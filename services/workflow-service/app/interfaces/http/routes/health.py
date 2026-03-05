# ==============================================================================
# Workflow Service — Health Routes
# ==============================================================================

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "workflow-service"}


@router.get("/ready")
async def ready():
    return {"status": "ready", "service": "workflow-service"}
