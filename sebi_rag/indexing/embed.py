from functools import lru_cache

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from api.config import settings


class BGEEmbedder:
    MODEL_NAME = "BAAI/bge-large-en-v1.5"
    DIM = 1024

    def __init__(self):
        logger.info(f"Loading embedding model: {self.MODEL_NAME}")
        self.model = SentenceTransformer(self.MODEL_NAME)
        # Warm up the model with a dummy forward pass
        self.model.encode(["warmup"], normalize_embeddings=True)
        logger.info("Embedding model loaded and warmed up")

    def embed_documents(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed_query_cached(text)

    @lru_cache(maxsize=256)
    def _embed_query_cached(self, text: str) -> np.ndarray:
        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        return self.model.encode([prefixed], normalize_embeddings=True)[0]


_embedder: BGEEmbedder | None = None


def get_embedder() -> BGEEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = BGEEmbedder()
    return _embedder
