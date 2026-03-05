# ==============================================================================
# Vector Service — Document Processor (Domain Core)
# ==============================================================================
#
# Handles the full document ingestion pipeline:
#   1. File upload & storage
#   2. Text extraction (plain text, markdown, PDF — extensible)
#   3. Text chunking with configurable strategies
#   4. Embedding generation via AI Service
#   5. Storage in ChromaDB vector store
# ==============================================================================

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import httpx
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)

logger = logging.getLogger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────


class ChunkingStrategy(StrEnum):
    RECURSIVE = "recursive"
    TOKEN = "token"
    SENTENCE = "sentence"
    FIXED = "fixed"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class DocumentChunk:
    """A single chunk of a document with its embedding."""

    chunk_id: str
    document_id: str
    content: str
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    chunk_index: int = 0


@dataclass
class DocumentRecord:
    """Metadata record for an ingested document."""

    document_id: str
    filename: str
    content_hash: str
    collection: str
    status: DocumentStatus = DocumentStatus.PENDING
    chunk_count: int = 0
    file_size_bytes: int = 0
    mime_type: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None


# ── Document Processor ───────────────────────────────────────────────────────


class DocumentProcessor:
    """Core document processing pipeline."""

    def __init__(
        self,
        ai_service_url: str,
        embedding_model: str = "text-embedding-3-small",
        default_chunk_size: int = 512,
        default_chunk_overlap: int = 50,
    ) -> None:
        self._ai_service_url = ai_service_url
        self._embedding_model = embedding_model
        self._default_chunk_size = default_chunk_size
        self._default_chunk_overlap = default_chunk_overlap

    # ── Text Extraction ──────────────────────────────────────────────────

    def extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract plain text from a file based on MIME type."""
        path = Path(file_path)

        if mime_type in ("text/plain", "text/markdown", "text/csv"):
            return path.read_text(encoding="utf-8")

        if mime_type == "application/json":
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(data, indent=2)

        # Fallback — try reading as text
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Cannot extract text from %s (mime=%s)", file_path, mime_type)
            raise ValueError(f"Unsupported file type: {mime_type}") from None

    # ── Chunking ─────────────────────────────────────────────────────────

    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[str]:
        """Split text into chunks using the specified strategy."""
        size = chunk_size or self._default_chunk_size
        overlap = chunk_overlap or self._default_chunk_overlap

        match strategy:
            case ChunkingStrategy.RECURSIVE:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=size,
                    chunk_overlap=overlap,
                    separators=["\n\n", "\n", ". ", " ", ""],
                )
            case ChunkingStrategy.TOKEN:
                splitter = TokenTextSplitter(
                    chunk_size=size,
                    chunk_overlap=overlap,
                )
            case _:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=size,
                    chunk_overlap=overlap,
                )

        return splitter.split_text(text)

    # ── Embedding Generation ─────────────────────────────────────────────

    async def generate_embeddings(
        self, texts: list[str], model: str | None = None
    ) -> list[list[float]]:
        """Generate embeddings for a list of text chunks via the AI Service."""
        model = model or self._embedding_model

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self._ai_service_url}/api/v1/models/embed",
                json={"texts": texts, "model": model},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embeddings", [])

    # ── Full Pipeline ────────────────────────────────────────────────────

    async def process_document(
        self,
        file_path: str,
        filename: str,
        mime_type: str,
        collection: str,
        metadata: dict | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    ) -> DocumentRecord:
        """
        Full ingestion pipeline:
          file → text → chunks → embeddings → DocumentRecord + DocumentChunks
        """
        path = Path(file_path)
        file_size = path.stat().st_size
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()

        doc = DocumentRecord(
            document_id=str(uuid.uuid4()),
            filename=filename,
            content_hash=content_hash,
            collection=collection,
            file_size_bytes=file_size,
            mime_type=mime_type,
            metadata=metadata or {},
        )

        doc.status = DocumentStatus.PROCESSING

        try:
            # 1. Extract text
            text = self.extract_text(file_path, mime_type)

            # 2. Chunk
            chunks_text = self.chunk_text(
                text,
                strategy=chunking_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            if not chunks_text:
                raise ValueError("No text chunks generated from document")

            # 3. Generate embeddings
            embeddings = await self.generate_embeddings(chunks_text)

            # 4. Build chunk objects
            chunks = []
            for i, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings, strict=False)):
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{doc.document_id}_{i}",
                        document_id=doc.document_id,
                        content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "filename": filename,
                            "chunk_index": i,
                            "total_chunks": len(chunks_text),
                        },
                        embedding=embedding,
                        chunk_index=i,
                    )
                )

            doc.chunk_count = len(chunks)
            doc.status = DocumentStatus.INDEXED

            # Store chunks in the document record for the caller to persist
            doc.metadata["_chunks"] = chunks

            logger.info(
                "Processed document %s: %d chunks generated",
                doc.document_id,
                doc.chunk_count,
            )

        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error = str(exc)
            logger.error("Failed to process document %s: %s", filename, exc)

        return doc

    @staticmethod
    def compute_content_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
