# ==============================================================================
# Vector Service — Document Routes
# ==============================================================================

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.domain.DocumentProcessor import (
    ChunkingStrategy,
    DocumentProcessor,
    DocumentStatus,
)
from app.infrastructure import vectorstore, kafka

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Processor singleton ──────────────────────────────────────────────────────
_processor = DocumentProcessor(
    ai_service_url=settings.AI_SERVICE_URL,
    embedding_model=settings.EMBEDDING_MODEL,
    default_chunk_size=settings.DEFAULT_CHUNK_SIZE,
    default_chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
)

# ── In-memory document registry (production: DB) ────────────────────────────
_documents: dict[str, dict] = {}


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    chunk_size: int = Form(None),
    chunk_overlap: int = Form(None),
    chunking_strategy: str = Form("recursive"),
):
    """Upload and ingest a document into the vector store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Validate file size
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Save to disk
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    file_path = upload_dir / f"{file_id}{ext}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Process document
    try:
        strategy = ChunkingStrategy(chunking_strategy)
    except ValueError:
        strategy = ChunkingStrategy.RECURSIVE

    doc = await _processor.process_document(
        file_path=str(file_path),
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        collection=f"{settings.CHROMA_COLLECTION_PREFIX}{collection}",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=strategy,
    )

    # If processing succeeded, store chunks in ChromaDB
    if doc.status == DocumentStatus.INDEXED:
        chunks = doc.metadata.pop("_chunks", [])
        if chunks:
            vectorstore.add_documents(
                collection_name=f"{settings.CHROMA_COLLECTION_PREFIX}{collection}",
                ids=[c.chunk_id for c in chunks],
                documents=[c.content for c in chunks],
                embeddings=[c.embedding for c in chunks if c.embedding],
                metadatas=[c.metadata for c in chunks],
            )

        # Publish event
        await kafka.publish_event(
            topic="nemo.documents.uploaded",
            event_type="document.indexed",
            payload={
                "document_id": doc.document_id,
                "filename": doc.filename,
                "collection": collection,
                "chunk_count": doc.chunk_count,
            },
        )

    # Store document record
    _documents[doc.document_id] = {
        "document_id": doc.document_id,
        "filename": doc.filename,
        "collection": collection,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
        "file_size_bytes": doc.file_size_bytes,
        "mime_type": doc.mime_type,
        "content_hash": doc.content_hash,
        "error": doc.error,
        "created_at": doc.created_at.isoformat(),
    }

    return _documents[doc.document_id]


@router.get("/documents")
async def list_documents(collection: str | None = None, limit: int = 50):
    """List all ingested documents."""
    docs = list(_documents.values())
    if collection:
        docs = [d for d in docs if d["collection"] == collection]
    return {"documents": docs[:limit], "total": len(docs)}


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get document details."""
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks from the vector store."""
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}{doc['collection']}"

    # Delete chunks from ChromaDB
    try:
        chunk_ids = [f"{document_id}_{i}" for i in range(doc.get("chunk_count", 0))]
        if chunk_ids:
            vectorstore.delete_documents(collection_name, chunk_ids)
    except Exception as exc:
        logger.warning("Failed to delete chunks from ChromaDB: %s", exc)

    # Delete file from disk
    upload_dir = Path(settings.UPLOAD_DIR)
    for f in upload_dir.glob(f"{document_id}.*"):
        f.unlink(missing_ok=True)

    del _documents[document_id]

    return {"deleted": True, "document_id": document_id}
