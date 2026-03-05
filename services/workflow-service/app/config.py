# ==============================================================================
# Workflow Service — Config
# ==============================================================================

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Service ──────────────────────────────────────────────────────────
    SERVICE_NAME: str = "workflow-service"
    SERVICE_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── HTTP / gRPC ──────────────────────────────────────────────────────
    HTTP_PORT: int = 8003
    GRPC_PORT: int = 50053

    # ── PostgreSQL ───────────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "nemo"
    POSTGRES_PASSWORD: str = "nemo_secret"
    POSTGRES_DB: str = "nemo"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 3

    # ── Kafka ────────────────────────────────────────────────────────────
    KAFKA_BROKERS: str = "localhost:9092"

    # ── AI Service ───────────────────────────────────────────────────────
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_GRPC: str = "localhost:50051"

    # ── Plugin Service ───────────────────────────────────────────────────
    PLUGIN_SERVICE_URL: str = "http://localhost:8002"
    PLUGIN_SERVICE_GRPC: str = "localhost:50052"

    # ── Vector Service ───────────────────────────────────────────────────
    VECTOR_SERVICE_URL: str = "http://localhost:8004"
    VECTOR_SERVICE_GRPC: str = "localhost:50054"

    # ── Workflow Defaults ────────────────────────────────────────────────
    MAX_CONCURRENT_WORKFLOWS: int = 20
    STEP_TIMEOUT_SECONDS: int = 120
    WORKFLOW_CONFIG_PATH: str = "/app/configs/workflows.yaml"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def kafka_broker_list(self) -> list[str]:
        return [b.strip() for b in self.KAFKA_BROKERS.split(",")]

    class Config:
        env_prefix = ""
        case_sensitive = True


settings = Settings()
