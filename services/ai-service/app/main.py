# ==============================================================================
# AI Service — FastAPI Application Entry Point
# ==============================================================================

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.config import get_settings
from app.infrastructure.database import Database
from app.infrastructure.cache import RedisCache
from app.infrastructure.kafka import KafkaEventBus
from app.infrastructure.logging import setup_logging, get_logger
from app.interfaces.http.routes import chat, models, health, agent
from app.domain.llm.LLMFactory import LLMFactory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — startup and shutdown."""
    settings = get_settings()
    logger = get_logger("ai-service")

    logger.info("Starting AI Service", extra={"service": "ai-service"})

    # Initialize infrastructure
    db = Database(settings)
    await db.connect()
    app.state.db = db

    redis = RedisCache(settings)
    await redis.connect()
    app.state.redis = redis

    kafka = KafkaEventBus(settings)
    await kafka.connect()
    app.state.kafka = kafka

    # Initialize LLM Factory
    llm_factory = LLMFactory(settings.config_path / "models.yaml")
    app.state.llm_factory = llm_factory
    logger.info(
        "LLM Factory initialized",
        extra={"providers": llm_factory.list_providers()},
    )

    yield

    # Shutdown
    logger.info("Shutting down AI Service")
    await kafka.disconnect()
    await redis.disconnect()
    await db.disconnect()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title="Nemo AI Service",
        description="LLM orchestration, agent reasoning, and tool execution",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
    app.include_router(models.router, prefix="/api/v1", tags=["models"])

    return app


app = create_app()
