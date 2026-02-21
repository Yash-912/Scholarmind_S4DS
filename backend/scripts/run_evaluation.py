"""
Run Evaluation — Execute RAGAS-style evaluation on the golden query set.
Usage: python -m scripts.run_evaluation
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llmops.synthesizer import synthesizer
from app.llmops.evaluator import rag_evaluator
from app.mlops.experiment_tracker import experiment_tracker


async def main():
    # Load golden queries
    eval_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "eval",
        "golden_queries.json",
    )
    with open(eval_path) as f:
        golden = json.load(f)

    print(f"Running evaluation on {len(golden)} golden queries...")

    test_cases = []
    for item in golden:
        print(f"  → {item['query'][:60]}...")
        result = await synthesizer.synthesize(
            item["query"], query_type=item.get("query_type")
        )
        test_cases.append(
            {
                "query": item["query"],
                "answer": result.get("answer", ""),
                "contexts": [p.get("snippet", "") for p in result.get("papers", [])],
                "ground_truth": item.get("expected_topics"),
            }
        )

    results = await rag_evaluator.evaluate_batch(test_cases)
    summary = rag_evaluator.summary(results)

    print("\n=== Evaluation Results ===")
    for k, v in summary.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")

    # Log to MLflow
    for r in results:
        experiment_tracker.log_synthesis_eval(
            query=r.query,
            model="default",
            faithfulness=r.faithfulness,
            answer_relevance=r.answer_relevance,
            context_relevance=r.context_relevance,
            latency_ms=0,
            cost_usd=0,
        )

    print("\n✅ Evaluation complete. Results logged to MLflow.")


if __name__ == "__main__":
    asyncio.run(main())
