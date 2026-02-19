"""
Experiment Tracker — MLflow experiment logging wrapper.
"""

import mlflow
import time
from typing import Any, Optional
from app.config import settings


class ExperimentTracker:
    """Wraps MLflow experiment tracking for all ScholarMind experiments."""

    EXPERIMENTS = [
        "ingestion_pipeline",
        "retrieval_evaluation",
        "synthesis_evaluation",
        "topic_modeling",
        "drift_detection",
    ]

    def __init__(self):
        self._initialized = False

    def initialize(self):
        """Set up MLflow tracking and create experiments."""
        if self._initialized:
            return
        try:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            for exp_name in self.EXPERIMENTS:
                try:
                    mlflow.create_experiment(exp_name)
                except Exception:
                    pass  # Already exists
            self._initialized = True
        except Exception as e:
            print(f"[ExperimentTracker] Init warning: {e}")

    def log_ingestion_run(
        self,
        source: str,
        papers_scraped: int,
        papers_new: int,
        papers_duplicate: int,
        duration_seconds: float,
        errors: int = 0,
    ):
        """Log an ingestion pipeline run."""
        self._safe_log(
            experiment="ingestion_pipeline",
            run_name=f"ingest_{source}_{int(time.time())}",
            params={"source": source},
            metrics={
                "papers_scraped": papers_scraped,
                "papers_new": papers_new,
                "papers_duplicate": papers_duplicate,
                "duration_seconds": duration_seconds,
                "errors": errors,
            },
        )

    def log_retrieval_eval(
        self,
        query: str,
        top_k: int,
        recall: float,
        precision: float,
        mrr: float,
        latency_ms: float,
        reranked: bool = False,
    ):
        """Log a retrieval evaluation."""
        self._safe_log(
            experiment="retrieval_evaluation",
            run_name=f"retrieval_{int(time.time())}",
            params={"query": query[:100], "top_k": top_k, "reranked": reranked},
            metrics={
                "recall": recall,
                "precision": precision,
                "mrr": mrr,
                "latency_ms": latency_ms,
            },
        )

    def log_synthesis_eval(
        self,
        query: str,
        model: str,
        faithfulness: float,
        answer_relevance: float,
        context_relevance: float,
        latency_ms: float,
        cost_usd: float,
    ):
        """Log a synthesis evaluation."""
        self._safe_log(
            experiment="synthesis_evaluation",
            run_name=f"synthesis_{int(time.time())}",
            params={"query": query[:100], "model": model},
            metrics={
                "faithfulness": faithfulness,
                "answer_relevance": answer_relevance,
                "context_relevance": context_relevance,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
            },
        )

    def log_topic_modeling(
        self,
        num_topics: int,
        num_documents: int,
        coherence_score: float,
        duration_seconds: float,
    ):
        """Log a topic model training run."""
        self._safe_log(
            experiment="topic_modeling",
            run_name=f"topics_{int(time.time())}",
            params={"num_documents": num_documents},
            metrics={
                "num_topics": num_topics,
                "coherence_score": coherence_score,
                "duration_seconds": duration_seconds,
            },
        )

    def log_drift(self, drift_type: str, psi: float, threshold: float, drifted: bool):
        """Log a drift detection run."""
        self._safe_log(
            experiment="drift_detection",
            run_name=f"drift_{drift_type}_{int(time.time())}",
            params={"drift_type": drift_type, "threshold": threshold},
            metrics={"psi": psi, "drifted": 1.0 if drifted else 0.0},
        )

    def _safe_log(
        self,
        experiment: str,
        run_name: str,
        params: dict[str, Any],
        metrics: dict[str, Any],
    ):
        """Log to MLflow safely (no crash if MLflow unavailable)."""
        try:
            mlflow.set_experiment(experiment)
            with mlflow.start_run(run_name=run_name):
                for k, v in params.items():
                    mlflow.log_param(k, v)
                for k, v in metrics.items():
                    mlflow.log_metric(k, float(v))
        except Exception as e:
            print(f"[ExperimentTracker] Log warning: {e}")


experiment_tracker = ExperimentTracker()
