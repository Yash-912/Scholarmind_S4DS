FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories (for ChromaDB and MLflow local storage)
RUN mkdir -p data/chroma data/mlflow data/cache data/models

# Expose HF Spaces port (must be 7860)
EXPOSE 7860

# Health check for HF Spaces
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Start script
RUN chmod +x start.sh
CMD ["./start.sh"]
