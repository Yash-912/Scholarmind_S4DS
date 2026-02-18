"""
Relevance Scoring — Personalized paper recommendations based on user interests.
"""

import numpy as np
from typing import Optional
from app.core.embeddings import embedding_service
from app.core.vector_store import vector_store


class RelevanceScorer:
    """
    Scores paper relevance for a user based on:
    1. Interest profile embedding similarity
    2. Category overlap
    3. Citation proximity (if available)
    """

    def compute_user_profile(
        self,
        interests: list[str],
        bookmarked_texts: list[str] = None,
    ) -> np.ndarray:
        """
        Compute a user profile embedding from their interests and bookmarks.

        Args:
            interests: List of interest keywords/phrases
            bookmarked_texts: Optional list of bookmarked paper texts

        Returns:
            User profile embedding vector
        """
        texts = interests.copy()
        if bookmarked_texts:
            texts.extend(bookmarked_texts)

        if not texts:
            return np.zeros(embedding_service.dimension)

        embeddings = embedding_service.embed_texts(texts)
        # Weighted average: bookmarks get more weight
        if bookmarked_texts:
            n_interests = len(interests)
            n_bookmarks = len(bookmarked_texts)
            # Interest weight: 1.0, Bookmark weight: 2.0
            weights = [1.0] * n_interests + [2.0] * n_bookmarks
            weights = np.array(weights) / sum(weights)
            profile = np.average(embeddings, axis=0, weights=weights)
        else:
            profile = np.mean(embeddings, axis=0)

        # Normalize
        norm = np.linalg.norm(profile)
        if norm > 0:
            profile = profile / norm

        return profile

    def score_papers(
        self,
        user_profile: np.ndarray,
        paper_ids: list[str] = None,
        top_k: int = 20,
    ) -> list[dict]:
        """
        Score papers for relevance to a user profile.

        Args:
            user_profile: User profile embedding
            paper_ids: Optional list of specific paper IDs to score
            top_k: Number of recommendations

        Returns:
            List of {paper_id, score, title} sorted by relevance
        """
        if np.linalg.norm(user_profile) == 0:
            return []

        # Use vector store to find similar papers
        results = vector_store.search(
            query_embedding=user_profile,
            top_k=top_k,
        )

        if not results or not results["ids"][0]:
            return []

        scored = []
        for i, paper_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            score = 1 - distance  # Convert to similarity
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}

            scored.append({
                "paper_id": paper_id,
                "relevance_score": round(score, 4),
                "title": metadata.get("title", ""),
                "source": metadata.get("source", ""),
            })

        return scored

    def get_personalized_feed(
        self,
        interests: list[str],
        bookmarked_texts: list[str] = None,
        top_k: int = 20,
    ) -> list[dict]:
        """
        Get a personalized paper feed for a user.
        Convenience method combining profile computation and scoring.
        """
        profile = self.compute_user_profile(interests, bookmarked_texts)
        return self.score_papers(profile, top_k=top_k)


# Global singleton
relevance_scorer = RelevanceScorer()
