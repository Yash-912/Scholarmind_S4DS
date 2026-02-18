"""
Hallucination Checker — Verifies LLM claims against retrieved source papers.
"""

import re
from typing import Optional
from app.llmops.gateway import llm_gateway


class HallucinationChecker:
    """
    Checks LLM-generated synthesis for hallucinations by
    verifying claims against source documents.
    """

    async def check(
        self,
        generated_text: str,
        source_papers: list[dict],
    ) -> dict:
        """
        Check generated text for faithfulness to source papers.

        Args:
            generated_text: LLM-generated synthesis
            source_papers: List of source paper dicts with 'text' key

        Returns:
            dict with faithfulness_score, flagged_claims, and details
        """
        if not source_papers or not generated_text:
            return {
                "faithfulness_score": 0.0,
                "flagged_claims": [],
                "verified_claims": [],
                "total_claims": 0,
            }

        # Extract citations from generated text
        citations = self._extract_citations(generated_text)

        # Build source context
        source_context = "\n\n".join([
            f"[Paper {i+1}] {p.get('title', 'Unknown')}\n{p.get('text', '')[:500]}"
            for i, p in enumerate(source_papers[:10])
        ])

        # Use LLM to verify faithfulness
        check_prompt = f"""You are a fact-checking assistant. Check if the following synthesis is faithful to the source papers.

SOURCE PAPERS:
{source_context}

SYNTHESIS TO CHECK:
{generated_text[:2000]}

For each major claim in the synthesis, determine if it is:
1. SUPPORTED — clearly stated or implied by the source papers
2. UNSUPPORTED — not found in the source papers (potential hallucination)
3. CONTRADICTED — directly contradicts the source papers

Respond in this JSON format:
{{
    "claims": [
        {{"claim": "...", "status": "SUPPORTED|UNSUPPORTED|CONTRADICTED", "source": "Paper N or N/A"}}
    ],
    "overall_faithfulness": 0.0-1.0
}}"""

        try:
            result = await llm_gateway.generate(
                prompt=check_prompt,
                model="llama-3.1-8b-instant",  # Use small model for checking
                temperature=0.1,
                max_tokens=2000,
            )

            # Parse the response
            response_text = result["text"]

            # Extract JSON from response
            import json
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                parsed = json.loads(json_match.group())
                claims = parsed.get("claims", [])
                overall = parsed.get("overall_faithfulness", 0.5)

                supported = [c for c in claims if c.get("status") == "SUPPORTED"]
                unsupported = [c for c in claims if c.get("status") == "UNSUPPORTED"]
                contradicted = [c for c in claims if c.get("status") == "CONTRADICTED"]

                return {
                    "faithfulness_score": overall,
                    "total_claims": len(claims),
                    "supported_count": len(supported),
                    "unsupported_count": len(unsupported),
                    "contradicted_count": len(contradicted),
                    "flagged_claims": unsupported + contradicted,
                    "verified_claims": supported,
                    "checker_cost_usd": result.get("cost_usd", 0),
                }

        except Exception as e:
            print(f"⚠️ Hallucination check failed: {e}")

        # Fallback: simple heuristic based on citations
        has_citations = len(citations) > 0
        return {
            "faithfulness_score": 0.7 if has_citations else 0.3,
            "total_claims": 0,
            "flagged_claims": [],
            "verified_claims": [],
            "note": "Heuristic fallback — LLM check failed",
        }

    def _extract_citations(self, text: str) -> list[str]:
        """Extract [Paper N] citations from text."""
        return re.findall(r'\[Paper \d+\]', text)


# Global singleton
hallucination_checker = HallucinationChecker()
