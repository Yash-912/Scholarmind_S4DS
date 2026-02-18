"""
MLOps Routes — Model registry, drift detection, experiments.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.mlops.registry import model_registry
from app.mlops.drift_detector import drift_detector
from app.db import crud

router = APIRouter(prefix="/mlops", tags=["MLOps"])


@router.get("/models")
async def list_models():
    """List all registered model versions."""
    models = await model_registry.list_models()
    return {"models": models}


@router.post("/models/register")
async def register_model(body: dict):
    """Register a new model version."""
    result = await model_registry.register_model(
        name=body.get("name", ""),
        version=body.get("version", ""),
        model_type=body.get("model_type", ""),
        metrics=body.get("metrics"),
        parameters=body.get("parameters"),
    )
    return result


@router.get("/models/{name}/active")
async def get_active_model(name: str):
    """Get the active version of a model."""
    model = await model_registry.get_active(name)
    if model:
        return model
    return {"error": f"No active model found for '{name}'"}


@router.get("/drift")
async def drift_history():
    """Get drift detection history."""
    records = await drift_detector.get_drift_history()
    return {"records": records}


@router.get("/experiments")
async def list_experiments():
    """List MLflow experiments."""
    experiments = model_registry.get_mlflow_experiments()
    return {"experiments": experiments}


@router.get("/query-analytics")
async def query_analytics(db: AsyncSession = Depends(get_db)):
    """Get query analytics — costs by model, stats."""
    stats = await crud.get_query_stats(db, hours=24)
    costs = await crud.get_cost_by_model(db, hours=24)
    return {
        "stats": stats,
        "cost_by_model": costs,
    }


@router.get("/prompt-analytics")
async def prompt_analytics(
    prompt_name: str = "synthesis",
    db: AsyncSession = Depends(get_db),
):
    """Get prompt version performance analytics."""
    stats = await crud.get_prompt_stats(db, prompt_name)
    return {"prompt_name": prompt_name, "versions": stats}
