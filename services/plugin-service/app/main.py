# ==============================================================================
# Plugin Service — FastAPI Application
# ==============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.interfaces.http.routes import plugins, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Initialize DB, Redis, Kafka, load plugin configs
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nemo Plugin Service",
        description="Plugin lifecycle management and execution",
        version="1.0.0",
        lifespan=lifespan,
    )

    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    app.include_router(health.router, tags=["health"])
    app.include_router(plugins.router, prefix="/api/v1", tags=["plugins"])

    return app


app = create_app()
