# ==============================================================================
# Plugin Service — Health Routes
# ==============================================================================

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "plugin-service"}


@router.get("/ready")
async def ready():
    return {"status": "ready", "service": "plugin-service"}
