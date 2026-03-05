# ==============================================================================
# Vector Service — Search Routes
# ==============================================================================

from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.domain.DocumentProcessor import DocumentProcessor
from app.infrastructure import vectorstore, cache

logger = logging.getLogger(__name__)
router = APIRouter()

_processor = DocumentProcessor(
    ai_service_url=settings.AI_SERVICE_URL,
    embedding_model=settings.EMBEDDING_MODEL,
)


class SearchRequest(BaseModel):
    query: str
    collection: str = "default"
    top_k: int = 5
    filter: dict | None = None


class HybridSearchRequest(BaseModel):
    query: str
    collection: str = "default"
    top_k: int = 5
    filter: dict | None = None
    rerank: bool = False


@router.post("/search")
async def semantic_search(body: SearchRequest):
    """Perform semantic search across a collection."""
    collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}{body.collection}"

    # Check cache
    cache_key = hashlib.md5(
        f"{body.query}:{body.collection}:{body.top_k}".encode()
    ).hexdigest()
    cached = await cache.get_cached_search(cache_key)
    if cached:
        return {"results": cached, "cached": True}

    # Generate query embedding
    try:
        embeddings = await _processor.generate_embeddings([body.query])
    except Exception as exc:
        logger.error("Failed to generate query embedding: %s", exc)
        raise HTTPException(status_code=502, detail="Embedding generation failed")

    if not embeddings:
        raise HTTPException(status_code=500, detail="No embedding returned")

    # Query ChromaDB
    try:
        results = vectorstore.query_collection(
            collection_name=collection_name,
            query_embeddings=embeddings,
            n_results=body.top_k,
            where=body.filter,
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Vector search failed")

    # Format results
    formatted = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            formatted.append({
                "rank": i + 1,
                "content": doc,
                "metadata": meta,
                "score": 1.0 - dist,  # cosine distance → similarity
            })

    # Cache results
    await cache.cache_search_results(cache_key, formatted, ttl=300)

    return {
        "results": formatted,
        "total": len(formatted),
        "collection": body.collection,
        "cached": False,
    }


@router.post("/search/multi")
async def multi_collection_search(body: HybridSearchRequest):
    """Search across multiple collections."""
    # For now, search the specified collection
    # In production, this would fan out across collections
    collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}{body.collection}"

    try:
        embeddings = await _processor.generate_embeddings([body.query])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    results = vectorstore.query_collection(
        collection_name=collection_name,
        query_embeddings=embeddings,
        n_results=body.top_k,
        where=body.filter,
    )

    formatted = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            formatted.append({
                "rank": i + 1,
                "content": doc,
                "metadata": meta,
                "score": 1.0 - dist,
                "collection": body.collection,
            })

    return {"results": formatted, "total": len(formatted)}
