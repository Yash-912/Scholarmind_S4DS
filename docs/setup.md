# ScholarMind — Local Development Setup

## Prerequisites

- Python 3.12+
- Node.js 20+
- Git

## 1. Clone & Environment

```bash
git clone https://github.com/YOUR_USERNAME/scholarmind.git
cd scholarmind

# Copy environment template
cp .env.example .env
# Edit .env with your API keys (GROQ_API_KEY, HF_TOKEN)
```

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Mac/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed initial papers from arXiv
python -m app.seed_papers

# Start the backend server
uvicorn app.main:app --port 7860 --reload
```

The API will be running at `http://localhost:7860` with docs at `http://localhost:7860/docs`.

## 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:7860" > .env.local

# Start dev server
npm run dev
```

The frontend will be running at `http://localhost:3000`.

## 4. Running Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
```

## 5. Running Scripts

```bash
cd backend

# Seed papers
python -m app.seed_papers

# Benchmark retrieval
python -m scripts.benchmark_retrieval

# Run RAGAS evaluation
python -m scripts.run_evaluation

# Generate topic model
python -m scripts.generate_topics
```

## 6. Project Structure

```
scholarmind/
├── backend/           # FastAPI + ML pipeline
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # ML: embeddings, retrieval, topics
│   │   ├── ingestion/ # Data pipeline: scrapers, dedup
│   │   ├── llmops/    # LLM: gateway, cache, prompts
│   │   ├── mlops/     # MLflow, drift, quality gate
│   │   ├── aiops/     # Monitoring, anomalies, alerts
│   │   └── db/        # Database models & CRUD
│   ├── tests/         # Test suite
│   ├── scripts/       # Utility scripts
│   └── eval/          # Evaluation data
├── frontend/          # Next.js UI
│   └── src/
│       ├── app/       # Pages
│       ├── components/# Reusable components
│       └── lib/       # API client, hooks, types
├── docs/              # Documentation
└── .github/           # CI/CD workflows
```

## Troubleshooting

**ChromaDB build error on Windows:** Install pre-built wheel first:
```bash
pip install chroma-hnswlib --only-binary :all:
pip install -r requirements.txt
```

**PyTorch DLL error:** Use a virtual environment to avoid Anaconda conflicts:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
