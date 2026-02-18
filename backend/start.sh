#!/bin/bash
set -e

echo "=== ScholarMind Backend Starting ==="

# Create data directories
mkdir -p data/chroma data/mlflow data/cache

# Start FastAPI on port 7860 (HF Spaces requirement)
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 7860 --workers 1
