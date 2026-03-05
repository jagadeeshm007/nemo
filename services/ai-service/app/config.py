# ==============================================================================
# AI Service — Configuration (Pydantic Settings)
# ==============================================================================

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # General
    nemo_env: str = "development"
    log_level: str = "info"
    log_format: str = "json"
    config_path: Path = Path("/app/configs")

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "nemo"
    postgres_password: str = "nemo_secret_change_me"
    postgres_db: str = "nemo"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # Kafka
    kafka_brokers: str = "localhost:9092"
    kafka_group_id: str = "nemo-ai-service"

    @property
    def kafka_broker_list(self) -> list[str]:
        return self.kafka_brokers.split(",")

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # gRPC downstream services
    plugin_service_grpc: str = "localhost:50052"
    workflow_service_grpc: str = "localhost:50053"
    vector_service_grpc: str = "localhost:50054"

    # Service ports
    http_port: int = 8001
    grpc_port: int = 50051

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
