import os
import re

BASE = r"d:\MLOps S4DS\backend\app"

def regex_update_file(filepath, pattern, new):
    path = os.path.join(BASE, filepath)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    content, count = re.subn(pattern, new, content, flags=re.DOTALL)
    if count == 0:
        print(f"WARN: Regex not matched in {filepath}")
        
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {filepath}")

# 1. Gateway: Add HF Inference API fallback and metrics wiring
regex_update_file(r"llmops\gateway.py",
r'            # Calculate cost',
r'''            # Prometheus metric
            from app.aiops.metrics_collector import llm_calls_total
            llm_calls_total.labels(model=model, provider="groq", status="success").inc()

            # Calculate cost''')

regex_update_file(r"llmops\gateway.py",
r'        except Exception as e:.*?raise',
r'''        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ LLM generation failed ({model}): {e}")

            from app.aiops.metrics_collector import llm_calls_total
            llm_calls_total.labels(model=model, provider="groq", status="error").inc()

            # HuggingFace Serverless Inference Fallback
            if settings.HF_TOKEN:
                print("♻️ Failing over to HuggingFace Inference API")
                import httpx
                hf_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
                headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "temperature": temperature}}
                try:
                    async with httpx.AsyncClient() as client:
                        hf_resp = await client.post(hf_url, headers=headers, json=payload, timeout=15.0)
                        hf_resp.raise_for_status()
                        hf_data = hf_resp.json()
                        text = hf_data[0].get("generated_text", "")
                        if text.startswith(prompt):
                            text = text[len(prompt):].strip()
                        
                        llm_calls_total.labels(model="Meta-Llama-3-8B-Instruct", provider="hf", status="success").inc()
                        return {
                            "text": text, "model": "Meta-Llama-3-8B-Instruct", "provider": "huggingface",
                            "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": elapsed
                        }
                except Exception as hf_err:
                    llm_calls_total.labels(model="Meta-Llama-3-8B-Instruct", provider="hf", status="error").inc()
                    print(f"❌ HuggingFace fallback also failed. {hf_err}")

            raise''')

# 2. Main.py: APScheduler for proactive health monitoring and Prometheus metrics
regex_update_file(r"main.py",
r'async def track_latency\(request: Request, call_next\):.*?return response',
r'''async def track_latency(request: Request, call_next):
    import time
    from app.aiops.health_monitor import health_monitor
    from app.aiops.metrics_collector import query_latency_seconds
    from app.aiops.anomaly_detector import anomaly_detector
    
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    
    # Record stage-level tracking
    health_monitor.record_latency(request.url.path, elapsed)
    
    # Wire Prometheus Metrics & Anomaly Detector
    query_latency_seconds.labels(endpoint=request.url.path).observe(elapsed / 1000.0)
    anomaly_detector.record(f"latency_{request.url.path.replace('/', '_')}", elapsed)
    
    response.headers["X-Response-Time"] = f"{elapsed:.0f}ms"
    return response

# Connect scheduler to proactively poll health check
from apscheduler.schedulers.asyncio import AsyncIOScheduler
proactive_scheduler = AsyncIOScheduler()
@proactive_scheduler.scheduled_job("interval", minutes=1)
async def scheduled_health_check():
    from app.aiops.health_monitor import health_monitor
    await health_monitor.collect_metrics()
    
@app.on_event("startup")
async def start_proactive_monitoring():
    proactive_scheduler.start()

@app.on_event("shutdown")
async def stop_proactive_monitoring():
    proactive_scheduler.shutdown()
''')

# 3. Drift Detector: Use actual baseline samples instead of PCA/L2 gaussian
regex_update_file(r"mlops\drift_detector.py",
r'    def set_baseline\(self, embeddings: np.ndarray\):.*?def compute_psi',
r'''    def set_baseline(self, embeddings: np.ndarray):
        """Set baseline embedding statistics for drift comparison."""
        self._baseline_mean = np.mean(embeddings, axis=0)
        self._baseline_std = np.std(embeddings, axis=0)
        # Store actual embeddings for true distribution testing
        np.random.seed(42)
        indices = np.random.choice(len(embeddings), min(300, len(embeddings)), replace=False)
        self._baseline_sample = embeddings[indices]
        self._baseline_set = True
        print(f"✅ Drift baseline set from {len(embeddings)} embeddings")

    def compute_psi''')

regex_update_file(r"mlops\drift_detector.py",
r'        baseline_norms = np.linalg.norm\(.*?axis=1,\n        \)',
r'''        # Compute Euclidean distance (L2 norm) using the actual baseline sample, not gaussian randoms
        if hasattr(self, '_baseline_sample'):
            baseline_norms = np.linalg.norm(self._baseline_sample, axis=1)
        else:
            baseline_norms = np.linalg.norm(
                np.random.randn(max(len(new_embeddings), 50), new_embeddings.shape[1])
                * self._baseline_std + self._baseline_mean, axis=1)
''')

# 4. Ingestion.py: Automatically call drift detector
regex_update_file(r"api\routes\ingestion.py",
r'    # Return stats.*?return \{',
r'''    # Automatically run MLops drift detector on new papers
    if new_embeddings:
        from app.mlops.drift_detector import drift_detector
        import numpy as np
        await drift_detector.check_drift(np.array(new_embeddings))
    
    # Return stats
    return {''')

# 5. Arxiv Scraper: Wire Prometheus ingestion metric
regex_update_file(r"ingestion\arxiv_scraper.py",
r'        print\(f"Found {len\(results\)} papers on arXiv"\)\n        return results',
r'''        print(f"Found {len(results)} papers on arXiv")
        from app.aiops.metrics_collector import papers_ingested_total
        papers_ingested_total.labels(source="arxiv").inc(len(results))
        return results''')

print("Applied Fixer 2: AIOps/MLOps.")
