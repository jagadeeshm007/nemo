# ==============================================================================
# Vector Service — FastAPI Application
# ==============================================================================

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.config import settings
from app.infrastructure.cache import close_cache, init_cache
from app.infrastructure.database import close_db, init_db
from app.infrastructure.kafka import close_kafka, init_kafka
from app.infrastructure.logging import setup_logging
from app.infrastructure.vectorstore import init_vectorstore
from app.interfaces.http.routes import collections, documents, health, search

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle."""
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting %s v%s", settings.SERVICE_NAME, settings.SERVICE_VERSION)

    await init_db(settings.database_url)
    await init_cache(settings.redis_url)
    await init_kafka(settings.kafka_broker_list)
    init_vectorstore(settings.CHROMA_HOST, settings.CHROMA_PORT)

    yield

    await close_kafka()
    await close_cache()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Nemo Vector Service",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# ── Prometheus metrics ───────────────────────────────────────────────────────
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(collections.router, prefix="/api/v1", tags=["collections"])
