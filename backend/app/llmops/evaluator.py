"""
Evaluator — RAGAS-style evaluation for RAG quality.
Measures faithfulness, answer relevance, and context relevance.
"""

import json
import asyncio
from dataclasses import dataclass, field
from app.llmops.gateway import llm_gateway


@dataclass
class EvalResult:
    query: str
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    context_relevance: float = 0.0
    overall: float = 0.0
    details: dict = field(default_factory=dict)


class RAGEvaluator:
    """RAGAS-inspired evaluation of RAG pipeline quality."""

    async def evaluate_single(
        self,
        query: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> EvalResult:
        """Evaluate a single RAG response."""
        faithfulness, answer_rel, context_rel = await asyncio.gather(
            self._score_faithfulness(answer, contexts),
            self._score_answer_relevance(query, answer),
            self._score_context_relevance(query, contexts),
        )

        overall = (faithfulness + answer_rel + context_rel) / 3

        return EvalResult(
            query=query,
            faithfulness=faithfulness,
            answer_relevance=answer_rel,
            context_relevance=context_rel,
            overall=overall,
        )

    async def evaluate_batch(
        self,
        test_cases: list[dict],
    ) -> list[EvalResult]:
        """Run evaluation on a batch of test cases."""
        tasks = [
            self.evaluate_single(
                query=tc["query"],
                answer=tc["answer"],
                contexts=tc.get("contexts", []),
                ground_truth=tc.get("ground_truth"),
            )
            for tc in test_cases
        ]
        return await asyncio.gather(*tasks)

    async def _score_faithfulness(self, answer: str, contexts: list[str]) -> float:
        """Score how faithful the answer is to the provided contexts."""
        if not contexts:
            return 0.0

        context_str = "\n---\n".join(contexts[:5])
        prompt = f"""Score how faithfully this answer is supported by the source contexts.
Return ONLY a JSON object: {{"score": 0.0-1.0, "reasoning": "..."}}

Contexts:
{context_str}

Answer:
{answer}"""

        for _ in range(3):
            try:
                resp = await llm_gateway.generate(prompt, model="llama-3.1-8b-instant")
                # regex to extract json if wrapped in markdown
                import re
                txt = resp["text"]
                match = re.search(r'\{.*\}', txt, re.DOTALL)
                if match: txt = match.group(0)
                data = json.loads(txt.strip())
                return float(data.get("score", 0.5))
            except Exception:
                continue
        return 0.5

    async def _score_answer_relevance(self, query: str, answer: str) -> float:
        """Score how relevant the answer is to the query."""
        prompt = f"""Score how relevant this answer is to the question asked.
Return ONLY a JSON object: {{"score": 0.0-1.0, "reasoning": "..."}}

Question: {query}

Answer: {answer}"""

        for _ in range(3):
            try:
                resp = await llm_gateway.generate(prompt, model="llama-3.1-8b-instant")
                # regex to extract json if wrapped in markdown
                import re
                txt = resp["text"]
                match = re.search(r'\{.*\}', txt, re.DOTALL)
                if match: txt = match.group(0)
                data = json.loads(txt.strip())
                return float(data.get("score", 0.5))
            except Exception:
                continue
        return 0.5

    async def _score_context_relevance(self, query: str, contexts: list[str]) -> float:
        """Score how relevant the retrieved contexts are to the query."""
        if not contexts:
            return 0.0

        context_str = "\n---\n".join(contexts[:5])
        prompt = f"""Score how relevant these retrieved contexts are to the question.
Return ONLY a JSON object: {{"score": 0.0-1.0, "reasoning": "..."}}

Question: {query}

Retrieved Contexts:
{context_str}"""

        for _ in range(3):
            try:
                resp = await llm_gateway.generate(prompt, model="llama-3.1-8b-instant")
                # regex to extract json if wrapped in markdown
                import re
                txt = resp["text"]
                match = re.search(r'\{.*\}', txt, re.DOTALL)
                if match: txt = match.group(0)
                data = json.loads(txt.strip())
                return float(data.get("score", 0.5))
            except Exception:
                continue
        return 0.5

    def summary(self, results: list[EvalResult]) -> dict:
        """Aggregate evaluation results."""
        if not results:
            return {"count": 0}
        n = len(results)
        return {
            "count": n,
            "avg_faithfulness": sum(r.faithfulness for r in results) / n,
            "avg_answer_relevance": sum(r.answer_relevance for r in results) / n,
            "avg_context_relevance": sum(r.context_relevance for r in results) / n,
            "avg_overall": sum(r.overall for r in results) / n,
        }


rag_evaluator = RAGEvaluator()
