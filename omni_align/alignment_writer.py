"""
OmniAlign — Alignment Writer
Serialises computed alignments as RDF triples in Turtle format.

Output format (as required by the assignment):
  <uri1> owl:equivalentClass <uri2> .
  <uri1> rdfs:subClassOf <uri2> .
  <uri1> owl:equivalentProperty <uri2> .
  <uri1> rdfs:subPropertyOf <uri2> .
  <uri1> owl:sameAs <uri2> .
"""

import os
import logging
from typing import List, Tuple
from rdflib import Graph, URIRef, OWL, RDFS, RDF, Namespace
from rdflib.namespace import XSD

logger = logging.getLogger(__name__)

# Relation URI mapping
RELATION_MAP = {
    "owl:equivalentClass": OWL.equivalentClass,
    "rdfs:subClassOf": RDFS.subClassOf,
    "owl:equivalentProperty": OWL.equivalentProperty,
    "rdfs:subPropertyOf": RDFS.subPropertyOf,
    "owl:sameAs": OWL.sameAs,
}


class AlignmentWriter:
    """
    Writes alignment mappings to a Turtle file.
    """

    def write(
        self,
        mappings: List[Tuple[URIRef, str, URIRef, float]],
        output_path: str,
        source_ontology: str = "",
        target_ontology: str = "",
        system_name: str = "OmniAlign",
    ):
        """
        Write mappings to a Turtle file.

        Parameters
        ----------
        mappings : list of (uri1, relation_str, uri2, score)
        output_path : path to output .ttl file
        source_ontology : path/name of source ontology (for comment)
        target_ontology : path/name of target ontology (for comment)
        system_name : name of the alignment system
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        g = Graph()
        g.bind("owl", OWL)
        g.bind("rdfs", RDFS)
        g.bind("rdf", RDF)

        for item in mappings:
            # Support both (uri1, relation_str, uri2, score) and (uri1, relation_str, uri2)
            if len(item) == 4:
                uri1, relation_str, uri2, score = item
            else:
                uri1, relation_str, uri2 = item
            predicate = RELATION_MAP.get(str(relation_str))
            if predicate is None:
                logger.debug(f"Unknown relation: {relation_str}, skipping.")
                continue
            if not isinstance(uri1, URIRef) or not isinstance(uri2, URIRef):
                continue
            g.add((uri1, predicate, uri2))

        # Serialise to Turtle
        turtle_str = g.serialize(format="turtle")

        # Prepend a header comment
        header = self._build_header(
            len(mappings), source_ontology, target_ontology, system_name
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(turtle_str)

        logger.info(f"Wrote {len(mappings)} mappings to {output_path}")

    @staticmethod
    def _build_header(
        n_mappings: int,
        source: str,
        target: str,
        system: str,
    ) -> str:
        return (
            f"# Alignment produced by {system}\n"
            f"# Source ontology: {source}\n"
            f"# Target ontology: {target}\n"
            f"# Total mappings: {n_mappings}\n"
            f"#\n"
        )

    @staticmethod
    def load_reference(ref_path: str) -> List[Tuple[URIRef, str, URIRef]]:
        """
        Load a reference alignment from a Turtle file.
        Returns list of (uri1, relation_str, uri2).
        """
        g = Graph()
        try:
            g.parse(ref_path, format="turtle")
        except Exception as e:
            logger.error(f"Could not parse reference alignment {ref_path}: {e}")
            return []

        mappings = []
        for s, p, o in g:
            if not isinstance(s, URIRef) or not isinstance(o, URIRef):
                continue
            rel = None
            for rel_str, rel_uri in RELATION_MAP.items():
                if p == rel_uri:
                    rel = rel_str
                    break
            if rel:
                mappings.append((s, rel, o))

        return mappings
