"""Local multilingual embeddings via sentence-transformers (bge-m3 by default).

The model is loaded lazily and cached, so importing this module is cheap.
"""
from __future__ import annotations

from functools import lru_cache

from .config import config


@lru_cache(maxsize=1)
def _model():
    # Imported lazily: torch/transformers are heavy and not needed for, e.g.,
    # database-only operations.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.embed_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Normalised so cosine distance is meaningful."""
    vectors = _model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 32,
    )
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
