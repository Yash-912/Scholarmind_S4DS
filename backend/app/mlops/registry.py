"""
Model Registry — Track, version, and manage ML models.
Wraps MLflow for experiment tracking.
"""

import mlflow
import os
import time
from typing import Optional
from app.config import settings
from app.db.database import async_session
from app.db import crud


class ModelRegistry:
    """
    ML model registry that:
    1. Registers model versions with metrics
    2. Tracks active/staged/archived models
    3. Integrates with MLflow for experiment logging
    """

    def __init__(self):
        self._initialized = False

    def initialize(self):
        """Set up MLflow tracking."""
        if self._initialized:
            return

        os.makedirs(settings.MLFLOW_TRACKING_URI, exist_ok=True)
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        self._initialized = True
        print(f"✅ MLflow initialized at {settings.MLFLOW_TRACKING_URI}")

    async def register_model(
        self,
        name: str,
        version: str,
        model_type: str,
        metrics: dict = None,
        parameters: dict = None,
        artifact_path: str = None,
    ) -> dict:
        """
        Register a new model version.

        Args:
            name: Model name (e.g., "specter2", "bertopic")
            version: Version string (e.g., "1.0.0")
            model_type: Type (e.g., "embedding", "topic", "reranker")
            metrics: Evaluation metrics
            parameters: Hyperparameters
            artifact_path: Path to model artifacts

        Returns:
            Registered model version info
        """
        if not self._initialized:
            self.initialize()

        # Log to MLflow
        try:
            mlflow.set_experiment(f"scholarmind_{name}")
            with mlflow.start_run(run_name=f"{name}_v{version}"):
                if parameters:
                    mlflow.log_params(parameters)
                if metrics:
                    mlflow.log_metrics(metrics)
                mlflow.set_tag("model_type", model_type)
                mlflow.set_tag("version", version)
        except Exception as e:
            print(f"⚠️ MLflow logging failed: {e}")

        # Save to DB
        async with async_session() as db:
            model_version = await crud.register_model_version(
                db,
                name=name,
                version=version,
                model_type=model_type,
                metrics=metrics or {},
                parameters=parameters or {},
                artifact_path=artifact_path,
                is_active=True,
            )
            await db.commit()

            return {
                "id": model_version.id,
                "name": name,
                "version": version,
                "model_type": model_type,
                "metrics": metrics,
                "is_active": True,
            }

    async def list_models(self) -> list[dict]:
        """List all registered model versions."""
        async with async_session() as db:
            models = await crud.list_model_versions(db)
            return [
                {
                    "id": m.id,
                    "name": m.name,
                    "version": m.version,
                    "model_type": m.model_type,
                    "metrics": m.metrics,
                    "is_active": m.is_active,
                    "registered_at": m.registered_at.isoformat(),
                }
                for m in models
            ]

    async def get_active(self, name: str) -> Optional[dict]:
        """Get the active version of a named model."""
        async with async_session() as db:
            model = await crud.get_active_model(db, name)
            if model:
                return {
                    "name": model.name,
                    "version": model.version,
                    "metrics": model.metrics,
                    "parameters": model.parameters,
                }
            return None

    def get_mlflow_experiments(self) -> list[dict]:
        """List MLflow experiments."""
        if not self._initialized:
            self.initialize()

        try:
            experiments = mlflow.search_experiments()
            return [
                {
                    "name": exp.name,
                    "experiment_id": exp.experiment_id,
                    "lifecycle_stage": exp.lifecycle_stage,
                }
                for exp in experiments
            ]
        except Exception:
            return []


# Global singleton
model_registry = ModelRegistry()
