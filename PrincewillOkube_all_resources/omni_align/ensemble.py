"""
OmniAlign — Ensemble Scorer
Combines lexical, structural, embedding, and LLM scores into a final
similarity score using configurable weights.

Also handles:
  - Relation type determination (equivalentClass vs subClassOf)
  - Threshold filtering
  - One-to-one mapping enforcement (optional)
"""

import logging
from typing import Dict, List, Optional, Tuple
from rdflib import URIRef

logger = logging.getLogger(__name__)


class EnsembleScorer:
    """
    Fuses multiple similarity signals into a final alignment decision.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.50,
        one_to_one: bool = False,
    ):
        """
        weights: dict with keys 'lexical', 'structural', 'embedding', 'llm'
        threshold: minimum score to accept a mapping
        one_to_one: if True, enforce injective mappings (best match only)
        """
        default_weights = {
            "lexical": 0.30,
            "structural": 0.15,
            "embedding": 0.40,
            "llm": 0.15,
        }
        self.weights = weights or default_weights
        self._normalise_weights()
        self.threshold = threshold
        self.one_to_one = one_to_one

    def _normalise_weights(self):
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def fuse(
        self,
        lexical: float,
        structural: float,
        embedding: float,
        llm: float = 0.5,
        llm_weight_override: Optional[float] = None,
    ) -> float:
        """
        Compute weighted ensemble score.

        If llm_weight_override is provided, it replaces the configured LLM weight.
        """
        w = self.weights
        llm_w = llm_weight_override if llm_weight_override is not None else w.get("llm", 0.0)

        # If LLM score is the default 0.5 (not verified), reduce its weight
        if llm == 0.5 and llm_w > 0:
            # Redistribute LLM weight to other components
            remaining = 1.0 - llm_w
            if remaining > 0:
                scale = 1.0 / remaining
                score = (
                    w.get("lexical", 0) * scale * lexical
                    + w.get("structural", 0) * scale * structural
                    + w.get("embedding", 0) * scale * embedding
                )
            else:
                score = lexical
        else:
            score = (
                w.get("lexical", 0) * lexical
                + w.get("structural", 0) * structural
                + w.get("embedding", 0) * embedding
                + llm_w * llm
            )

        return min(1.0, max(0.0, score))

    def determine_relation(
        self,
        score: float,
        lexical: float,
        structural: float,
        embedding: float,
        llm_relation: str = "unknown",
        entity_type: str = "class",
    ) -> str:
        """
        Determine the alignment relation type based on scores and LLM hint.

        Returns one of:
          'owl:equivalentClass', 'rdfs:subClassOf',
          'owl:equivalentProperty', 'rdfs:subPropertyOf',
          'owl:sameAs'
        """
        if entity_type == "instance":
            return "owl:sameAs"

        if entity_type == "property":
            equiv_prop = "owl:equivalentProperty"
            sub_prop = "rdfs:subPropertyOf"
            if score >= 0.75:
                return equiv_prop
            elif score >= self.threshold:
                if llm_relation in ("subclass", "superclass"):
                    return sub_prop
                return equiv_prop if score >= 0.65 else sub_prop
            return equiv_prop

        # Class mappings
        equiv_class = "owl:equivalentClass"
        sub_class = "rdfs:subClassOf"

        if score >= 0.80:
            return equiv_class
        elif score >= self.threshold:
            if llm_relation in ("subclass", "superclass"):
                return sub_class
            # High lexical + high embedding → likely equivalent
            if lexical >= 0.70 and embedding >= 0.70:
                return equiv_class
            # Moderate scores → subclass is safer
            return equiv_class if score >= 0.65 else sub_class
        return equiv_class

    def filter_and_rank(
        self,
        candidates: List[Tuple[URIRef, URIRef, float, str]],
    ) -> List[Tuple[URIRef, URIRef, float, str]]:
        """
        Filter candidates below threshold and optionally enforce one-to-one.

        Input: [(uri1, uri2, score, relation), ...]
        Output: filtered and sorted list
        """
        # Filter by threshold
        filtered = [(u1, u2, s, r) for u1, u2, s, r in candidates if s >= self.threshold]

        # Sort by score descending
        filtered.sort(key=lambda x: x[2], reverse=True)

        if not self.one_to_one:
            return filtered

        # Enforce one-to-one: greedy assignment
        used1 = set()
        used2 = set()
        result = []
        for u1, u2, s, r in filtered:
            if u1 not in used1 and u2 not in used2:
                result.append((u1, u2, s, r))
                used1.add(u1)
                used2.add(u2)

        return result
