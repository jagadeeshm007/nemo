# ==============================================================================
# AI Service — Health Routes
# ==============================================================================

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-service"}


@router.get("/ready")
async def ready(request: Request):
    checks = {}

    # Check database
    try:
        db = request.app.state.db
        async with db.engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["postgres"] = "healthy"
    except Exception as e:
        checks["postgres"] = f"unhealthy: {e}"

    # Check Redis
    try:
        redis = request.app.state.redis
        await redis.client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    all_healthy = all("healthy" == v for v in checks.values())
    return {
        "status": "ready" if all_healthy else "not ready",
        "checks": checks,
    }
