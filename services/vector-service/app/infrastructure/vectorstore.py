# ==============================================================================
# Vector Service — ChromaDB Vector Store
# ==============================================================================

from __future__ import annotations

import logging
import time
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

_client: chromadb.HttpClient | None = None

MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 2.0


def init_vectorstore(host: str, port: int) -> None:
    global _client
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # Verify connection
            heartbeat = _client.heartbeat()
            logger.info("ChromaDB connected (heartbeat=%s)", heartbeat)
            return
        except Exception as exc:
            logger.warning(
                "ChromaDB connection attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_DELAY_SECONDS * attempt)


def get_client() -> chromadb.HttpClient:
    assert _client is not None, "ChromaDB not initialized"
    return _client


def get_or_create_collection(
    name: str,
    metadata: dict[str, Any] | None = None,
) -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata=metadata or {"hnsw:space": "cosine"},
    )


def list_collections() -> list[dict]:
    """List all collections with metadata."""
    client = get_client()
    collections = client.list_collections()
    return [
        {
            "name": c.name,
            "metadata": c.metadata,
            "count": c.count(),
        }
        for c in collections
    ]


def delete_collection(name: str) -> None:
    client = get_client()
    client.delete_collection(name)
    logger.info("Deleted collection: %s", name)


def add_documents(
    collection_name: str,
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict] | None = None,
) -> None:
    """Add documents with pre-computed embeddings to a collection."""
    collection = get_or_create_collection(collection_name)
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info("Added %d documents to collection '%s'", len(ids), collection_name)


def query_collection(
    collection_name: str,
    query_embeddings: list[list[float]],
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    """Query a collection using embedding vectors."""
    collection = get_or_create_collection(collection_name)
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return results


def delete_documents(collection_name: str, ids: list[str]) -> None:
    """Delete documents by ID from a collection."""
    collection = get_or_create_collection(collection_name)
    collection.delete(ids=ids)
    logger.info("Deleted %d documents from collection '%s'", len(ids), collection_name)
