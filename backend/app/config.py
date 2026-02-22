"""
ScholarMind Configuration — Single source of truth for all settings.
Uses Pydantic Settings with environment variable loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # === App ===
    APP_NAME: str = "ScholarMind"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # === LLM Providers ===
    GROQ_API_KEY: str = ""
    HF_TOKEN: str = ""
    OPENAI_API_KEY: Optional[str] = None

    # === Database ===
    SQLITE_URL: str = "sqlite+aiosqlite:///./data/scholarmind.db"
    DATABASE_URL: Optional[str] = (
        None  # Neon PostgreSQL — takes priority over SQLITE_URL
    )

    @property
    def db_url(self) -> str:
        """Return Neon PostgreSQL URL if set, otherwise SQLite."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Convert postgres:// to postgresql+asyncpg:// for SQLAlchemy async
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            # Strip query params that asyncpg doesn't support
            # (sslmode, channel_binding — handled via connect_args instead)
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params.pop("sslmode", None)
            params.pop("channel_binding", None)
            clean_query = urlencode({k: v[0] for k, v in params.items()})
            url = urlunparse(parsed._replace(query=clean_query))
            return url
        return self.SQLITE_URL

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.DATABASE_URL is not None

    # === Vector Store ===
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # === MLflow ===
    MLFLOW_TRACKING_URI: str = "./data/mlflow"

    # === Embedding Model ===
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_DIM: int = 768

    # === Reranker ===
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_ENABLED: bool = True

    # === Ingestion ===
    SCRAPE_INTERVAL_HOURS: int = 6
    ARXIV_CATEGORIES: str = "cs.AI,cs.LG,cs.CL,cs.CV,stat.ML"
    ARXIV_MAX_RESULTS: int = 100
    PUBMED_QUERY: str = "machine learning healthcare"
    PUBMED_MAX_RESULTS: int = 50

    # === LLMOps ===
    CACHE_SIMILARITY_THRESHOLD: float = 0.95
    LLM_COST_ALERT_PER_HOUR: float = 5.0
    DEFAULT_SYNTHESIS_MODEL: str = "mixtral-8x7b-32768"
    MAX_RETRIEVAL_RESULTS: int = 15
    MAX_CONTEXT_CHUNKS: int = 10

    # === Redis Cache (Upstash/Cloud) ===
    REDIS_URL: Optional[str] = None  # e.g. redis://default:xxx@xxx.upstash.io:6379

    # === AIOps ===
    HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    ANOMALY_DETECTION_WINDOW_HOURS: int = 1
    ALERT_COOLDOWN_MINUTES: int = 15

    # === CORS ===
    CORS_ORIGINS: str = "http://localhost:3000,https://scholarmind.vercel.app"

    model_config = SettingsConfigDict(
        env_file=(
            ".env"
            if os.path.exists(".env")
            else os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                ".env",
            )
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def arxiv_categories_list(self) -> list[str]:
        return [c.strip() for c in self.ARXIV_CATEGORIES.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
