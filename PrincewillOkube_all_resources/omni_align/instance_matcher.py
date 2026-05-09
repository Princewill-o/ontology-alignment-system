"""
OmniAlign — Instance Matcher
Matches named individuals (owl:NamedIndividual) across ontologies using:
  1. Existing owl:sameAs links
  2. Shared property values (functional properties)
  3. Label similarity (same pipeline as class matching)
"""

import logging
from typing import Dict, List, Set, Tuple
from rdflib import URIRef, OWL, RDF, Literal

from omni_align.lexical_matcher import best_label_pair_sim

logger = logging.getLogger(__name__)


class InstanceMatcher:
    """
    Matches individuals across two ontologies.
    """

    def __init__(self, threshold: float = 0.85):
        """
        threshold: minimum similarity to accept an instance mapping.
        Instance matching uses a higher threshold than class matching
        to avoid false positives.
        """
        self.threshold = threshold

    def match(
        self,
        individuals1: Set[URIRef],
        individuals2: Set[URIRef],
        loader1,
        loader2,
        labels1: Dict[URIRef, List[str]],
        labels2: Dict[URIRef, List[str]],
    ) -> List[Tuple[URIRef, str, URIRef, float]]:
        # Filter out blank nodes and non-individual URIs
        individuals1 = {u for u in individuals1 if isinstance(u, URIRef)}
        individuals2 = {u for u in individuals2 if isinstance(u, URIRef)}
        """
        Return a list of (uri1, relation, uri2, score) instance mappings.
        relation is always 'owl:sameAs' for instances.
        """
        mappings = []

        if not individuals1 or not individuals2:
            logger.info("No individuals to match.")
            return mappings

        logger.info(
            f"Matching {len(individuals1)} x {len(individuals2)} individuals..."
        )

        # Step 1: Check existing owl:sameAs links
        existing = self._find_existing_same_as(individuals1, individuals2, loader1)
        for uri1, uri2 in existing:
            mappings.append((uri1, "owl:sameAs", uri2, 1.0))
            logger.debug(f"Existing sameAs: {uri1} = {uri2}")

        matched1 = {m[0] for m in mappings}
        matched2 = {m[2] for m in mappings}

        # Step 2: Property-value matching
        prop_matches = self._property_value_match(
            individuals1 - matched1,
            individuals2 - matched2,
            loader1,
            loader2,
        )
        for uri1, uri2, score in prop_matches:
            if score >= self.threshold:
                mappings.append((uri1, "owl:sameAs", uri2, score))
                matched1.add(uri1)
                matched2.add(uri2)

        # Step 3: Label similarity for remaining individuals
        remaining1 = individuals1 - matched1
        remaining2 = individuals2 - matched2
        for uri1 in remaining1:
            lbls1 = labels1.get(uri1, [])
            best_score = 0.0
            best_uri2 = None
            for uri2 in remaining2:
                lbls2 = labels2.get(uri2, [])
                score = best_label_pair_sim(lbls1, lbls2)
                if score > best_score:
                    best_score = score
                    best_uri2 = uri2
            if best_uri2 is not None and best_score >= self.threshold:
                mappings.append((uri1, "owl:sameAs", best_uri2, best_score))

        logger.info(f"Instance matching found {len(mappings)} mappings.")
        return mappings

    def _find_existing_same_as(
        self,
        individuals1: Set[URIRef],
        individuals2: Set[URIRef],
        loader1,
    ) -> List[Tuple[URIRef, URIRef]]:
        """Find pairs already linked by owl:sameAs in ontology 1."""
        pairs = []
        for uri1 in individuals1:
            for obj in loader1.graph.objects(uri1, OWL.sameAs):
                if isinstance(obj, URIRef) and obj in individuals2:
                    pairs.append((uri1, obj))
        return pairs

    def _property_value_match(
        self,
        individuals1: Set[URIRef],
        individuals2: Set[URIRef],
        loader1,
        loader2,
    ) -> List[Tuple[URIRef, URIRef, float]]:
        """
        Match individuals by comparing their property values.
        Two individuals are similar if they share many property values.
        """
        matches = []
        pv1 = {u: loader1.get_property_values(u) for u in individuals1}
        pv2 = {u: loader2.get_property_values(u) for u in individuals2}

        for uri1, props1 in pv1.items():
            best_score = 0.0
            best_uri2 = None
            for uri2, props2 in pv2.items():
                score = self._pv_similarity(props1, props2)
                if score > best_score:
                    best_score = score
                    best_uri2 = uri2
            if best_uri2 is not None and best_score > 0:
                matches.append((uri1, best_uri2, best_score))

        return matches

    @staticmethod
    def _pv_similarity(
        pv1: Dict[URIRef, List],
        pv2: Dict[URIRef, List],
    ) -> float:
        """Compute similarity between two property-value dictionaries."""
        if not pv1 or not pv2:
            return 0.0

        shared_props = set(pv1.keys()) & set(pv2.keys())
        if not shared_props:
            return 0.0

        matches = 0
        total = 0
        for prop in shared_props:
            vals1 = {str(v).lower() for v in pv1[prop]}
            vals2 = {str(v).lower() for v in pv2[prop]}
            total += max(len(vals1), len(vals2))
            matches += len(vals1 & vals2)

        if total == 0:
            return 0.0
        return matches / total
