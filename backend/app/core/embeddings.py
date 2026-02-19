"""
Embedding Service — 100% PyTorch-free using ONNX Runtime.
Downloads an ONNX model from HuggingFace and runs inference
using only onnxruntime + tokenizers. No torch import anywhere.
"""

import numpy as np
import time
import os
from pathlib import Path


class EmbeddingService:
    """Manages embeddings using ONNX Runtime — no PyTorch needed."""

    def __init__(self, model_name: str = None, dimension: int = None):
        from app.config import settings
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIM
        self._session = None
        self._tokenizer = None
        self._loaded = False
        self._backend = "none"

    def load(self):
        """Load the ONNX model and tokenizer."""
        if self._loaded:
            return

        print(f"🔄 Loading embedding model: {self.model_name} (ONNX backend)")
        start = time.time()

        try:
            self._load_onnx()
            self._backend = "onnx"
            elapsed = time.time() - start
            print(f"✅ ONNX embedding model loaded in {elapsed:.1f}s (dim={self.dimension})")
        except Exception as e:
            print(f"⚠️ ONNX load failed: {e}")
            print("⚠️ Using random embeddings for demo mode")
            self._backend = "random"

        self._loaded = True

    def _load_onnx(self):
        """Download and load ONNX model + tokenizer."""
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        repo_id = self.model_name
        cache_dir = os.path.join("data", "models")
        os.makedirs(cache_dir, exist_ok=True)

        # Download ONNX model
        onnx_path = hf_hub_download(
            repo_id=repo_id,
            filename="onnx/model.onnx",
            cache_dir=cache_dir,
        )

        # Download tokenizer
        tokenizer_path = hf_hub_download(
            repo_id=repo_id,
            filename="tokenizer.json",
            cache_dir=cache_dir,
        )

        # Load ONNX Runtime session
        import onnxruntime as ort
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.inter_op_num_threads = 2
        sess_options.intra_op_num_threads = 4
        self._session = ort.InferenceSession(onnx_path, sess_options, providers=["CPUExecutionProvider"])

        # Load tokenizer
        self._tokenizer = Tokenizer.from_file(tokenizer_path)
        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        self._tokenizer.enable_truncation(max_length=512)

    def _encode_onnx(self, texts: list[str], normalize: bool = True) -> np.ndarray:
        """Encode texts using pure ONNX Runtime."""
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)

        # Tokenize
        encoded = self._tokenizer.encode_batch(texts)

        # Build numpy arrays
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

        # Run ONNX inference
        feeds = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        }

        # Only pass inputs that the model expects
        model_inputs = {inp.name for inp in self._session.get_inputs()}
        feeds = {k: v for k, v in feeds.items() if k in model_inputs}

        outputs = self._session.run(None, feeds)
        token_embeddings = outputs[0]  # (batch, seq_len, dim)

        # Mean pooling
        mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.clip(norms, a_min=1e-9, a_max=None)
            embeddings = embeddings / norms

        return embeddings.astype(np.float32)

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

        if self._backend == "onnx":
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                emb = self._encode_onnx(batch)
                all_embeddings.append(emb)
            embeddings = np.vstack(all_embeddings) if all_embeddings else np.zeros((0, self.dimension))
        else:
            # Random fallback for demo
            embeddings = np.random.randn(len(texts), self.dimension).astype(np.float32)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms

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

        if self._backend == "onnx":
            return self._encode_onnx([query])[0]
        else:
            vec = np.random.randn(self.dimension).astype(np.float32)
            return vec / np.linalg.norm(vec)

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
            "backend": self._backend,
        }


# Global singleton
embedding_service = EmbeddingService()
