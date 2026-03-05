# ==============================================================================
# Vector Service — Collection Routes
# ==============================================================================

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.infrastructure import vectorstore

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateCollectionRequest(BaseModel):
    name: str
    metadata: dict | None = None


@router.get("/collections")
async def list_collections():
    """List all vector collections."""
    try:
        collections = vectorstore.list_collections()
        # Strip prefix for display
        prefix = settings.CHROMA_COLLECTION_PREFIX
        for c in collections:
            if c["name"].startswith(prefix):
                c["display_name"] = c["name"][len(prefix):]
            else:
                c["display_name"] = c["name"]
        return {"collections": collections}
    except Exception as exc:
        logger.error("Failed to list collections: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list collections")


@router.post("/collections")
async def create_collection(body: CreateCollectionRequest):
    """Create a new vector collection."""
    collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}{body.name}"
    try:
        vectorstore.get_or_create_collection(collection_name, body.metadata)
        return {"name": body.name, "full_name": collection_name, "created": True}
    except Exception as exc:
        logger.error("Failed to create collection: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """Delete a vector collection and all its data."""
    collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}{name}"
    try:
        vectorstore.delete_collection(collection_name)
        return {"deleted": True, "name": name}
    except Exception as exc:
        logger.error("Failed to delete collection: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
