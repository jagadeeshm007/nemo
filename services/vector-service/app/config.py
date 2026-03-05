# ==============================================================================
# Vector Service — Config
# ==============================================================================

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Service ──────────────────────────────────────────────────────────
    SERVICE_NAME: str = "vector-service"
    SERVICE_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── HTTP / gRPC ──────────────────────────────────────────────────────
    HTTP_PORT: int = 8004
    GRPC_PORT: int = 50054

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
    REDIS_DB: int = 4

    # ── Kafka ────────────────────────────────────────────────────────────
    KAFKA_BROKERS: str = "localhost:9092"

    # ── ChromaDB ─────────────────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    CHROMA_COLLECTION_PREFIX: str = "nemo_"

    # ── AI Service (for embeddings) ──────────────────────────────────────
    AI_SERVICE_URL: str = "http://localhost:8001"

    # ── Document Processing ──────────────────────────────────────────────
    UPLOAD_DIR: str = "/data/uploads"
    MAX_FILE_SIZE_MB: int = 50
    DEFAULT_CHUNK_SIZE: int = 512
    DEFAULT_CHUNK_OVERLAP: int = 50
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

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
