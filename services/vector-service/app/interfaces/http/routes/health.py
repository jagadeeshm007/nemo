# ==============================================================================
# Vector Service — Health Routes
# ==============================================================================

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "vector-service"}


@router.get("/ready")
async def ready():
    # Check ChromaDB connectivity
    try:
        from app.infrastructure.vectorstore import get_client

        get_client().heartbeat()
        chroma_ok = True
    except Exception:
        chroma_ok = False

    return {
        "status": "ready" if chroma_ok else "degraded",
        "service": "vector-service",
        "dependencies": {"chromadb": chroma_ok},
    }
