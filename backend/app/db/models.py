"""
SQLAlchemy ORM Models for ScholarMind.
Covers papers, topics, users, bookmarks, query logs, alerts, model versions, and prompt usage.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, JSON,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base


class Paper(Base):
    """Research paper metadata and references."""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1000), nullable=False, index=True)
    abstract = Column(Text, nullable=False)
    authors = Column(JSON, nullable=False, default=list)  # ["Author 1", "Author 2"]
    source = Column(String(50), nullable=False)  # "arxiv", "pubmed", "semantic_scholar"
    source_id = Column(String(200), nullable=False, unique=True, index=True)  # arxiv_id, pmid
    doi = Column(String(200), nullable=True, index=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    categories = Column(JSON, nullable=False, default=list)  # ["cs.AI", "cs.LG"]
    references = Column(JSON, nullable=False, default=list)  # [source_id1, source_id2]
    citation_count = Column(Integer, default=0)
    pdf_url = Column(String(500), nullable=True)
    embedding_id = Column(String(200), nullable=True)  # ChromaDB document ID
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    novelty_score = Column(Float, default=0.0)
    novelty_type = Column(String(50), nullable=True)  # "methodological", "application", etc.
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    topic = relationship("Topic", back_populates="papers")
    bookmarks = relationship("Bookmark", back_populates="paper", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_papers_published", "published_date"),
        Index("ix_papers_source", "source"),
    )


class Topic(Base):
    """Discovered research topics from BERTopic clustering."""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, nullable=False, unique=True)  # BERTopic topic ID
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=False, default=list)  # Top keywords
    paper_count = Column(Integer, default=0)
    trend_direction = Column(String(20), default="stable")  # "rising", "stable", "declining"
    parent_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    representative_papers = Column(JSON, default=list)  # [paper_id1, paper_id2]
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    papers = relationship("Paper", back_populates="topic")
    parent = relationship("Topic", remote_side=[id])


class User(Base):
    """User profiles for personalized recommendations."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=True)
    username = Column(String(100), unique=True, nullable=False)
    interests = Column(JSON, default=list)  # ["federated learning", "NLP"]
    profile_embedding = Column(JSON, nullable=True)  # Serialized embedding vector
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")


class Bookmark(Base):
    """User bookmarks for papers (implicit feedback signal)."""
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    paper = relationship("Paper", back_populates="bookmarks")

    __table_args__ = (
        Index("ix_bookmark_user_paper", "user_id", "paper_id", unique=True),
    )


class QueryLog(Base):
    """Log of all user queries for analytics and evaluation."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)  # "synthesis", "comparison", "search", etc.
    model_used = Column(String(100), nullable=True)
    provider = Column(String(50), nullable=True)  # "groq", "hf", "openai"
    prompt_version = Column(String(50), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    cache_hit = Column(Boolean, default=False)
    faithfulness_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    user_rating = Column(Integer, nullable=True)  # 1-5 stars or thumbs up/down
    num_papers_retrieved = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_query_timestamp", "timestamp"),
    )


class Alert(Base):
    """System alerts from AIOps monitoring."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)  # "info", "warning", "critical"
    message = Column(Text, nullable=False)
    metric_name = Column(String(100), nullable=True)
    metric_value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    remediation_action = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_alert_severity", "severity"),
        Index("ix_alert_created", "created_at"),
    )


class ModelVersion(Base):
    """ML model registry entries."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # "specter2", "bertopic", "reranker"
    version = Column(String(50), nullable=False)
    model_type = Column(String(100), nullable=False)  # "embedding", "topic", "reranker"
    metrics = Column(JSON, default=dict)  # {"recall@10": 0.85, "ndcg": 0.72}
    parameters = Column(JSON, default=dict)  # Hyperparameters
    artifact_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_model_name_version", "name", "version", unique=True),
    )


class PromptUsage(Base):
    """Track prompt template usage and quality metrics."""
    __tablename__ = "prompt_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String(200), nullable=False)
    prompt_version = Column(String(50), nullable=False)
    faithfulness = Column(Float, nullable=True)
    relevance = Column(Float, nullable=True)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IngestionRun(Base):
    """Track ingestion pipeline runs."""
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # "arxiv", "pubmed", "all"
    status = Column(String(20), nullable=False)  # "running", "completed", "failed"
    papers_found = Column(Integer, default=0)
    papers_new = Column(Integer, default=0)
    papers_duplicate = Column(Integer, default=0)
    papers_failed = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class DriftRecord(Base):
    """Data drift detection records."""
    __tablename__ = "drift_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drift_type = Column(String(50), nullable=False)  # "data_drift", "concept_drift"
    metric_name = Column(String(100), nullable=False)  # "psi", "unclustered_ratio"
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    is_drifted = Column(Boolean, default=False)
    details = Column(JSON, default=dict)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
