"""
OmniAlign — Lexical Matcher
Computes string-based similarity between entity label sets using:
  - Exact match
  - Levenshtein edit distance (via rapidfuzz)
  - Token set ratio (handles word-order variation)
  - Jaccard similarity on token sets
  - TF-IDF cosine similarity for blocking (candidate generation)
"""

import logging
from typing import Dict, List, Set, Tuple
from rdflib import URIRef

try:
    from rapidfuzz import fuzz, distance
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("rapidfuzz not available; falling back to basic string matching.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available; TF-IDF blocking disabled.")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level similarity functions
# ---------------------------------------------------------------------------

def exact_match(labels1: List[str], labels2: List[str]) -> float:
    """Return 1.0 if any label from set1 exactly matches any label from set2."""
    set1 = {l.lower().strip() for l in labels1}
    set2 = {l.lower().strip() for l in labels2}
    return 1.0 if set1 & set2 else 0.0


def levenshtein_sim(s1: str, s2: str) -> float:
    """Normalised Levenshtein similarity in [0, 1]."""
    if not s1 or not s2:
        return 0.0
    if RAPIDFUZZ_AVAILABLE:
        return fuzz.ratio(s1, s2) / 100.0
    # Fallback: simple character overlap
    longer = max(len(s1), len(s2))
    if longer == 0:
        return 1.0
    common = sum(c1 == c2 for c1, c2 in zip(s1, s2))
    return common / longer


def token_set_ratio(s1: str, s2: str) -> float:
    """Token-set ratio: handles word-order differences."""
    if not s1 or not s2:
        return 0.0
    if RAPIDFUZZ_AVAILABLE:
        return fuzz.token_set_ratio(s1, s2) / 100.0
    # Fallback: Jaccard on tokens
    t1 = set(s1.lower().split())
    t2 = set(s2.lower().split())
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / len(t1 | t2)


def jaccard_tokens(s1: str, s2: str) -> float:
    """Jaccard similarity on token sets."""
    t1 = set(s1.lower().split())
    t2 = set(s2.lower().split())
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / len(t1 | t2)


def best_label_pair_sim(labels1: List[str], labels2: List[str]) -> float:
    """
    Compute the maximum pairwise similarity across all label combinations.
    Uses a combination of Levenshtein and token-set ratio.
    """
    if not labels1 or not labels2:
        return 0.0

    # Quick exact match check
    if exact_match(labels1, labels2) == 1.0:
        return 1.0

    best = 0.0
    for l1 in labels1:
        for l2 in labels2:
            lev = levenshtein_sim(l1, l2)
            tsr = token_set_ratio(l1, l2)
            jac = jaccard_tokens(l1, l2)
            sim = max(lev, tsr, jac)
            if sim > best:
                best = sim
    return best


# ---------------------------------------------------------------------------
# TF-IDF Blocking
# ---------------------------------------------------------------------------

class TFIDFBlocker:
    """
    Builds TF-IDF vectors over entity labels and uses cosine similarity
    to generate candidate pairs efficiently (blocking step).
    """

    def __init__(self, threshold: float = 0.10, max_candidates: int = 50):
        self.threshold = threshold
        self.max_candidates = max_candidates
        self._vectorizer = None
        self._matrix1 = None
        self._matrix2 = None
        self._uris1: List[URIRef] = []
        self._uris2: List[URIRef] = []

    def fit(
        self,
        entities1: Dict[URIRef, List[str]],
        entities2: Dict[URIRef, List[str]],
    ):
        """
        Fit TF-IDF on the union of all labels from both ontologies.
        entities1/2: {uri: [normalised_label, ...]}
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available; TF-IDF blocking skipped.")
            return

        self._uris1 = list(entities1.keys())
        self._uris2 = list(entities2.keys())

        docs1 = [" ".join(entities1[u]) for u in self._uris1]
        docs2 = [" ".join(entities2[u]) for u in self._uris2]

        all_docs = docs1 + docs2
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self._vectorizer.fit(all_docs)
        self._matrix1 = self._vectorizer.transform(docs1)
        self._matrix2 = self._vectorizer.transform(docs2)
        logger.info(
            f"TF-IDF blocking: {len(self._uris1)} x {len(self._uris2)} entities, "
            f"vocab size={len(self._vectorizer.vocabulary_)}"
        )

    def get_candidates(self) -> List[Tuple[URIRef, URIRef, float]]:
        """
        Return candidate pairs (uri1, uri2, tfidf_score) above threshold.
        """
        if not SKLEARN_AVAILABLE or self._matrix1 is None:
            # No blocking: return all pairs
            candidates = []
            for u1 in self._uris1:
                for u2 in self._uris2:
                    candidates.append((u1, u2, 0.5))
            return candidates

        candidates = []
        # Compute cosine similarity in batches
        batch_size = 500
        for i in range(0, len(self._uris1), batch_size):
            batch = self._matrix1[i : i + batch_size]
            sims = cosine_similarity(batch, self._matrix2)  # shape: (batch, n2)
            for bi, row in enumerate(sims):
                uri1 = self._uris1[i + bi]
                # Get top-k indices above threshold
                above = np.where(row >= self.threshold)[0]
                if len(above) == 0:
                    continue
                # Sort by score descending, take top max_candidates
                top_idx = above[np.argsort(row[above])[::-1][: self.max_candidates]]
                for j in top_idx:
                    candidates.append((uri1, self._uris2[j], float(row[j])))

        logger.info(f"TF-IDF blocking produced {len(candidates)} candidate pairs.")
        return candidates


# ---------------------------------------------------------------------------
# Main Lexical Matcher
# ---------------------------------------------------------------------------

class LexicalMatcher:
    """
    Computes lexical similarity scores for candidate entity pairs.
    """

    def score(
        self,
        labels1: List[str],
        labels2: List[str],
    ) -> float:
        """
        Return a lexical similarity score in [0, 1] for two label sets.
        """
        return best_label_pair_sim(labels1, labels2)
