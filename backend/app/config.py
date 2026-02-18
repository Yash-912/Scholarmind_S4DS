"""
ScholarMind Configuration — Single source of truth for all settings.
Uses Pydantic Settings with environment variable loading.
"""

from pydantic_settings import BaseSettings
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

    # === Vector Store ===
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # === MLflow ===
    MLFLOW_TRACKING_URI: str = "./data/mlflow"

    # === Embedding Model ===
    EMBEDDING_MODEL: str = "allenai/specter2"
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

    # === AIOps ===
    HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    ANOMALY_DETECTION_WINDOW_HOURS: int = 1
    ALERT_COOLDOWN_MINUTES: int = 15

    # === CORS ===
    CORS_ORIGINS: str = "http://localhost:3000,https://scholarmind.vercel.app"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def arxiv_categories_list(self) -> list[str]:
        return [c.strip() for c in self.ARXIV_CATEGORIES.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
