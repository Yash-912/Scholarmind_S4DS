"""
Topic Model — BERTopic-based topic discovery and clustering.
"""

import numpy as np
import time


class TopicModeler:
    """
    Discovers research topics using BERTopic.
    Uses pre-computed SPECTER2 embeddings.
    """

    def __init__(self):
        self.model = None
        self._fitted = False
        self._topic_names = {}
        self._topic_keywords = {}

    def fit(self, texts: list[str], embeddings: np.ndarray) -> dict:
        """
        Fit topic model on paper texts using pre-computed embeddings.

        Args:
            texts: Paper texts (title + abstract)
            embeddings: Pre-computed embedding vectors

        Returns:
            dict with topic_count, topics, and cluster assignments
        """
        if len(texts) < 10:
            print("⚠️ Too few papers for topic modeling (need at least 10)")
            return {"topic_count": 0, "topics": [], "assignments": []}

        start = time.time()
        print(f"🔄 Fitting BERTopic on {len(texts)} papers...")

        try:
            from bertopic import BERTopic
            from umap import UMAP
            from hdbscan import HDBSCAN

            # Configure UMAP for dimensionality reduction
            umap_model = UMAP(
                n_neighbors=15,
                n_components=5,
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            )

            # Configure HDBSCAN for clustering
            hdbscan_model = HDBSCAN(
                min_cluster_size=5,
                min_samples=3,
                metric="euclidean",
                prediction_data=True,
            )

            # Create BERTopic model (using pre-computed embeddings)
            self.model = BERTopic(
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                calculate_probabilities=True,
                verbose=False,
            )

            # Fit the model
            topics, probs = self.model.fit_transform(texts, embeddings)

            # Extract topic info
            topic_info = self.model.get_topic_info()

            # Build topic data
            topic_data = []
            for _, row in topic_info.iterrows():
                tid = row["Topic"]
                if tid == -1:
                    continue  # Skip outlier topic

                # Get keywords
                topic_words = self.model.get_topic(tid)
                keywords = [word for word, _ in topic_words[:10]]

                # Generate readable name from top keywords
                name = ", ".join(keywords[:3]).title()

                self._topic_names[tid] = name
                self._topic_keywords[tid] = keywords

                topic_data.append(
                    {
                        "topic_id": tid,
                        "name": name,
                        "keywords": keywords,
                        "paper_count": row["Count"],
                    }
                )

            self._fitted = True
            elapsed = time.time() - start

            print(f"✅ BERTopic: {len(topic_data)} topics discovered in {elapsed:.1f}s")

            return {
                "topic_count": len(topic_data),
                "topics": topic_data,
                "assignments": topics,  # Topic assignment per paper
                "outlier_count": sum(1 for t in topics if t == -1),
            }

        except Exception as e:
            print(f"❌ Topic modeling failed: {e}")
            return {"topic_count": 0, "topics": [], "assignments": [], "error": str(e)}

    def predict(self, texts: list[str], embeddings: np.ndarray) -> list[int]:
        """Predict topics for new papers."""
        if not self._fitted or self.model is None:
            return [-1] * len(texts)

        try:
            topics, _ = self.model.transform(texts, embeddings)
            return topics
        except Exception:
            return [-1] * len(texts)

    def get_topic_hierarchy(self) -> list[dict]:
        """Get hierarchical topic representation."""
        if not self._fitted or self.model is None:
            return []

        try:
            hierarchy = self.model.get_topic_tree(
                self.model.hierarchical_topics(self.model._get_topic_model_data())
            )
            return hierarchy
        except Exception:
            return []

    def get_topics(self) -> list[dict]:
        """Return discovered topics (empty list if model not fitted)."""
        if not self._fitted or self.model is None:
            return []

        try:
            topics = []
            for tid, name in self._topic_names.items():
                topics.append(
                    {
                        "topic_id": tid,
                        "name": name,
                        "keywords": self._topic_keywords.get(tid, []),
                    }
                )
            return topics
        except Exception:
            return []

    def get_trending(self) -> list[dict]:
        """Return trending topics (empty list if model not fitted)."""
        if not self._fitted or self.model is None:
            return []

        try:
            # Trending = topics sorted by recency/count
            topics = self.get_topics()
            return topics[:10]  # Top 10 as "trending"
        except Exception:
            return []

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def get_stats(self) -> dict:
        return {
            "fitted": self._fitted,
            "topic_count": len(self._topic_names),
            "topics": list(self._topic_names.values()),
        }


# Global singleton
topic_modeler = TopicModeler()
