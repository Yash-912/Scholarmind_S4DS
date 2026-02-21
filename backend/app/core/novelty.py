"""
Novelty Detection — Identify genuinely novel papers using embedding distance.
"""

import numpy as np
from app.core.vector_store import vector_store
from app.core.embeddings import embedding_service


class NoveltyDetector:
    """
    Detects novel papers using:
    1. Embedding distance from cluster centroids
    2. Cross-domain bridge detection (connects distant clusters)
    3. Citation velocity (if available)
    """

    def score_novelty(
        self,
        title: str,
        abstract: str,
        categories: list[str] = None,
    ) -> dict:
        """
        Compute novelty score for a paper.

        Returns:
            dict with novelty_score (0-1), novelty_type, reasoning
        """
        text = embedding_service.format_paper_text(title, abstract)
        embedding = embedding_service.embed_query(text)

        # Get nearest neighbors from vector store
        results = vector_store.search(embedding, top_k=20)

        if not results or not results["ids"] or not results["ids"][0]:
            return {
                "novelty_score": 0.5,
                "novelty_type": "unknown",
                "reasoning": "Not enough papers in the database for comparison.",
            }

        distances = results["distances"][0]

        # Calculate novelty metrics
        avg_distance = np.mean(distances)
        min_distance = np.min(distances)
        _ = np.std(distances)  # reserved for future use

        # Novelty score: based on how far this paper is from its neighbors
        # Higher avg_distance = more novel (in cosine distance, 0=identical, 2=opposite)
        # Typical values: 0.1-0.3 for similar, 0.4-0.8 for somewhat novel, 0.8+ for very novel
        novelty_score = min(1.0, avg_distance / 0.8)  # Normalize to 0-1

        # Determine novelty type
        novelty_type = "incremental"  # default

        if novelty_score > 0.7:
            # Check if it bridges different categories
            neighbor_categories = set()
            for meta in results.get("metadatas", [[]])[0]:
                if meta and "categories" in meta:
                    for cat in meta["categories"].split(","):
                        neighbor_categories.add(cat.strip())

            paper_cats = set(categories or [])
            overlap = paper_cats & neighbor_categories

            if len(overlap) < len(paper_cats) * 0.3:
                novelty_type = "cross_domain"
            else:
                novelty_type = "methodological"

        elif novelty_score > 0.4:
            novelty_type = "application"

        reasoning = self._generate_reasoning(
            novelty_score, novelty_type, avg_distance, min_distance, len(distances)
        )

        return {
            "novelty_score": round(novelty_score, 3),
            "novelty_type": novelty_type,
            "reasoning": reasoning,
            "avg_distance": round(avg_distance, 4),
            "min_distance": round(min_distance, 4),
            "neighbors_checked": len(distances),
        }

    def _generate_reasoning(
        self,
        score: float,
        ntype: str,
        avg_dist: float,
        min_dist: float,
        n_neighbors: int,
    ) -> str:
        """Generate human-readable novelty reasoning."""
        if score > 0.7:
            level = "**Highly novel**"
        elif score > 0.4:
            level = "**Moderately novel**"
        else:
            level = "**Incremental contribution**"

        type_desc = {
            "cross_domain": "bridges multiple research domains",
            "methodological": "introduces a new method or approach",
            "application": "applies existing methods to a new domain",
            "incremental": "extends existing work incrementally",
            "unknown": "insufficient data for comparison",
        }

        return (
            f"{level} (score: {score:.2f}). "
            f"This paper {type_desc.get(ntype, '')}. "
            f"Average distance from {n_neighbors} nearest papers: {avg_dist:.3f}."
        )

    def batch_score(
        self,
        papers: list[dict],
    ) -> list[dict]:
        """Score novelty for multiple papers."""
        results = []
        for paper in papers:
            score = self.score_novelty(
                title=paper.get("title", ""),
                abstract=paper.get("abstract", ""),
                categories=paper.get("categories", []),
            )
            results.append(score)
        return results


# Global singleton
novelty_detector = NoveltyDetector()
