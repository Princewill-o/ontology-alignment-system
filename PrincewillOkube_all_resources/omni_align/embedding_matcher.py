"""
OmniAlign — Embedding Matcher
Uses sentence-transformers to encode entity labels into dense vectors
and computes cosine similarity in embedding space.

This captures semantic relatedness beyond surface-form similarity,
e.g. "VideoGame" ≈ "ComputerGame", "Developer" ≈ "GameStudio".
"""

import logging
from typing import Dict, List, Tuple, Optional
from rdflib import URIRef

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logger.warning(
        "sentence-transformers not installed. "
        "Run: pip install sentence-transformers\n"
        "Embedding matcher will return 0.0 for all pairs."
    )


class EmbeddingMatcher:
    """
    Encodes entity labels with a sentence-transformer model and
    computes cosine similarity between embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Optional[object] = None
        self._embeddings1: Optional[np.ndarray] = None
        self._embeddings2: Optional[np.ndarray] = None
        self._uris1: List[URIRef] = []
        self._uris2: List[URIRef] = []
        self._uri_to_idx1: Dict[URIRef, int] = {}
        self._uri_to_idx2: Dict[URIRef, int] = {}

    def _load_model(self):
        if not SBERT_AVAILABLE:
            return
        if self._model is None:
            logger.info(f"Loading sentence-transformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Model loaded.")

    def _labels_to_sentence(self, labels: List[str]) -> str:
        """Concatenate labels into a single sentence for encoding."""
        # Use the longest label as primary, append others
        if not labels:
            return ""
        primary = max(labels, key=len)
        others = [l for l in labels if l != primary]
        if others:
            return primary + ". Also known as: " + ", ".join(others[:3])
        return primary

    def fit(
        self,
        entities1: Dict[URIRef, List[str]],
        entities2: Dict[URIRef, List[str]],
    ):
        """
        Pre-compute embeddings for all entities in both ontologies.
        entities1/2: {uri: [normalised_label, ...]}
        """
        self._load_model()
        if not SBERT_AVAILABLE or self._model is None:
            return

        self._uris1 = list(entities1.keys())
        self._uris2 = list(entities2.keys())
        self._uri_to_idx1 = {u: i for i, u in enumerate(self._uris1)}
        self._uri_to_idx2 = {u: i for i, u in enumerate(self._uris2)}

        sentences1 = [self._labels_to_sentence(entities1[u]) for u in self._uris1]
        sentences2 = [self._labels_to_sentence(entities2[u]) for u in self._uris2]

        logger.info(
            f"Encoding {len(sentences1)} + {len(sentences2)} entities with {self.model_name}..."
        )
        self._embeddings1 = self._model.encode(
            sentences1, batch_size=64, show_progress_bar=False, normalize_embeddings=True
        )
        self._embeddings2 = self._model.encode(
            sentences2, batch_size=64, show_progress_bar=False, normalize_embeddings=True
        )
        logger.info("Embeddings computed.")

    def score(self, uri1: URIRef, uri2: URIRef) -> float:
        """
        Return cosine similarity between embeddings of uri1 and uri2.
        Returns 0.0 if embeddings are not available.
        """
        if (
            not SBERT_AVAILABLE
            or self._embeddings1 is None
            or self._embeddings2 is None
        ):
            return 0.0

        idx1 = self._uri_to_idx1.get(uri1)
        idx2 = self._uri_to_idx2.get(uri2)
        if idx1 is None or idx2 is None:
            return 0.0

        # Embeddings are L2-normalised, so dot product = cosine similarity
        sim = float(np.dot(self._embeddings1[idx1], self._embeddings2[idx2]))
        # Clamp to [0, 1] (cosine can be negative for dissimilar items)
        return max(0.0, sim)

    def get_top_candidates(
        self,
        uri1: URIRef,
        top_k: int = 10,
    ) -> List[Tuple[URIRef, float]]:
        """
        Return the top-k most similar entities from ontology 2 for a given uri1.
        """
        if (
            not SBERT_AVAILABLE
            or self._embeddings1 is None
            or self._embeddings2 is None
        ):
            return []

        idx1 = self._uri_to_idx1.get(uri1)
        if idx1 is None:
            return []

        sims = np.dot(self._embeddings2, self._embeddings1[idx1])
        top_indices = np.argsort(sims)[::-1][:top_k]
        return [(self._uris2[i], float(sims[i])) for i in top_indices]
