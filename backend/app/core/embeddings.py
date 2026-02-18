"""
Embedding Service — SPECTER2 model for scientific paper embeddings.
Loads the model once and provides batch embedding generation.
"""

import numpy as np
from typing import Optional
import time
import os


class EmbeddingService:
    """Manages the SPECTER2 embedding model."""

    def __init__(self, model_name: str = "allenai/specter2", dimension: int = 768):
        self.model_name = model_name
        self.dimension = dimension
        self.model = None
        self._loaded = False

    def load(self):
        """Load the embedding model into memory."""
        if self._loaded:
            return

        print(f"🔄 Loading embedding model: {self.model_name}")
        start = time.time()

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self._loaded = True
            elapsed = time.time() - start
            print(f"✅ Embedding model loaded in {elapsed:.1f}s")
        except Exception as e:
            print(f"⚠️ Failed to load {self.model_name}, falling back to all-MiniLM-L6-v2: {e}")
            from sentence_transformers import SentenceTransformer
            self.model_name = "all-MiniLM-L6-v2"
            self.dimension = 384
            self.model = SentenceTransformer(self.model_name)
            self._loaded = True
            print(f"✅ Fallback model loaded")

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings (titles + abstracts)
            batch_size: Batch size for encoding

        Returns:
            numpy array of shape (len(texts), dimension)
        """
        if not self._loaded:
            self.load()

        if not texts:
            return np.zeros((0, self.dimension))

        start = time.time()
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        elapsed = time.time() - start

        print(f"📊 Embedded {len(texts)} texts in {elapsed:.2f}s ({len(texts)/max(elapsed,0.001):.0f} texts/s)")
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.

        Returns:
            numpy array of shape (dimension,)
        """
        if not self._loaded:
            self.load()

        embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
        )
        return embedding[0]

    def format_paper_text(self, title: str, abstract: str) -> str:
        """Format paper for embedding: title [SEP] abstract."""
        return f"{title} [SEP] {abstract}"

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def info(self) -> dict:
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "loaded": self._loaded,
        }


# Global singleton
embedding_service = EmbeddingService()
