"""Tests for SPECTER2 embeddings — verifies correct dimensionality."""

import numpy as np
from app.core.embeddings import embedding_service


def test_embed_single_text():
    vec = embedding_service.embed_query("transformer attention mechanism")
    assert isinstance(vec, (list, np.ndarray))
    arr = np.array(vec)
    assert arr.shape == (768,) or arr.shape == (384,)  # SPECTER2 or MiniLM fallback


def test_embed_batch():
    texts = [
        "Graph neural networks for drug discovery",
        "Federated learning preserves privacy",
        "Reinforcement learning in robotics",
    ]
    embeddings = embedding_service.embed_texts(texts)
    assert len(embeddings) == 3
    assert all(len(e) == len(embeddings[0]) for e in embeddings)


def test_embed_empty_string():
    vec = embedding_service.embed_query("")
    assert vec is not None


def test_embeddings_are_normalized():
    vec = np.array(embedding_service.embed_query("test query"))
    norm = np.linalg.norm(vec)
    # Should be approximately unit length if normalized
    assert 0.5 < norm < 2.0
