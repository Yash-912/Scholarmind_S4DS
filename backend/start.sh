#!/bin/bash
set -e

echo "=== ScholarMind Backend Starting ==="

# Create data directories
mkdir -p data/chroma data/mlflow data/cache data/models

# Seed database on first boot (if no papers exist yet)
echo "Running database initialization and seeding..."
python -m app.seed_papers || echo "⚠️ Seeding skipped or failed (may already have data)"

# Start FastAPI on port 7860 (HF Spaces requirement)
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 7860 --workers 1
