# ==============================================================================
# Workflow Service — FastAPI Application
# ==============================================================================

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.config import settings
from app.infrastructure.logging import setup_logging
from app.infrastructure.database import init_db, close_db
from app.infrastructure.cache import init_cache, close_cache
from app.infrastructure.kafka import init_kafka, close_kafka
from app.interfaces.http.routes import health, workflows

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle."""
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Starting %s v%s", settings.SERVICE_NAME, settings.SERVICE_VERSION
    )

    await init_db(settings.database_url)
    await init_cache(settings.redis_url)
    await init_kafka(settings.kafka_broker_list)

    # Load workflow definitions from YAML on startup
    from app.domain.WorkflowEngine import workflow_engine
    workflow_engine.load_definitions(settings.WORKFLOW_CONFIG_PATH)
    application.state.workflow_engine = workflow_engine

    yield

    await close_kafka()
    await close_cache()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Nemo Workflow Service",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# ── Prometheus metrics ───────────────────────────────────────────────────────
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
