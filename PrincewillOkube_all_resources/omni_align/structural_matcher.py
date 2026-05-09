"""
OmniAlign — Structural Matcher
Propagates similarity scores through the class hierarchy.
If two classes are similar, their parents/children should also receive
a boosted similarity score (with a damping factor).

Algorithm:
  1. Start with initial lexical similarity scores S0.
  2. For each pair (c1, c2) with score s:
       - For each parent p1 of c1 and parent p2 of c2:
           S[p1, p2] += damping * s
       - For each child ch1 of c1 and child ch2 of c2:
           S[ch1, ch2] += damping * s
  3. Normalise scores to [0, 1].
  4. Combine with initial scores: final = max(S0, S_propagated).
"""

import logging
from typing import Dict, Set, Tuple
from rdflib import URIRef

logger = logging.getLogger(__name__)


class StructuralMatcher:
    """
    Propagates similarity through the ontology hierarchy.
    """

    def __init__(self, damping: float = 0.5, iterations: int = 2):
        """
        damping: fraction of score propagated to neighbours (0 < damping < 1)
        iterations: number of propagation rounds
        """
        self.damping = damping
        self.iterations = iterations

    def propagate(
        self,
        initial_scores: Dict[Tuple[URIRef, URIRef], float],
        superclasses1: Dict[URIRef, Set[URIRef]],
        superclasses2: Dict[URIRef, Set[URIRef]],
        subclasses1: Dict[URIRef, Set[URIRef]],
        subclasses2: Dict[URIRef, Set[URIRef]],
    ) -> Dict[Tuple[URIRef, URIRef], float]:
        """
        Run structural propagation and return updated scores.

        Parameters
        ----------
        initial_scores : {(uri1, uri2): score}
        superclasses1/2 : {uri: set of parent URIs} for each ontology
        subclasses1/2   : {uri: set of child URIs} for each ontology
        """
        scores = dict(initial_scores)

        for _ in range(self.iterations):
            additions: Dict[Tuple[URIRef, URIRef], float] = {}

            for (c1, c2), s in scores.items():
                if s <= 0:
                    continue
                boost = self.damping * s

                # Propagate to parents
                for p1 in superclasses1.get(c1, set()):
                    for p2 in superclasses2.get(c2, set()):
                        key = (p1, p2)
                        additions[key] = max(additions.get(key, 0.0), boost)

                # Propagate to children
                for ch1 in subclasses1.get(c1, set()):
                    for ch2 in subclasses2.get(c2, set()):
                        key = (ch1, ch2)
                        additions[key] = max(additions.get(key, 0.0), boost)

            # Merge additions into scores
            for key, val in additions.items():
                scores[key] = max(scores.get(key, 0.0), val)

        return scores

    def build_hierarchy_maps(
        self,
        entities: Set[URIRef],
        loader,
    ) -> Tuple[Dict[URIRef, Set[URIRef]], Dict[URIRef, Set[URIRef]]]:
        """
        Build superclass and subclass maps for a set of entities.

        Returns
        -------
        (superclasses, subclasses) where each is {uri: set_of_uris}
        """
        superclasses: Dict[URIRef, Set[URIRef]] = {}
        subclasses: Dict[URIRef, Set[URIRef]] = {}

        for uri in entities:
            parents = loader.get_superclasses(uri) & entities
            children = loader.get_subclasses(uri) & entities
            if parents:
                superclasses[uri] = parents
            if children:
                subclasses[uri] = children

        return superclasses, subclasses
