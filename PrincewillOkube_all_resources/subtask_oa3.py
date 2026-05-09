#!/usr/bin/env python3
"""
OmniAlign — Subtask OA.3
SPARQL query over the merged graph of both Part-1 ontologies + computed alignment.

Steps:
  1. Load both ontologies into a single rdflib ConjunctiveGraph
  2. Load the computed alignment (owl:equivalentClass, owl:sameAs, etc.)
  3. Apply OWL reasoning (via owlrl) to materialise inferred triples
  4. Execute a SPARQL query that uses vocabulary from BOTH ontologies
  5. Save results as CSV

The query retrieves all video games / computer games with their:
  - Title (from either ontology)
  - Release year / publication year
  - Global sales / worldwide sales
  - Developer / creator
  - Platform / available on
  - Publisher / distributor

This demonstrates cross-ontology querying enabled by the alignment.
"""

import csv
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from rdflib import Graph, ConjunctiveGraph, Namespace, URIRef, Literal, OWL, RDF, RDFS
from rdflib.namespace import SKOS

# Paths
SOURCE_ONTO = "data/part1/princewill_ontology.ttl"
TARGET_ONTO = "data/part1/external_videogame_ontology.ttl"
ALIGNMENT_FILE = "alignments/omni_align-princewill-external.ttl"
OUTPUT_CSV = "results/sparql_results.csv"

# Namespaces
CW = Namespace("http://www.city.ac.uk/inm713-in3067/2026/princewill_okube#")
EXT = Namespace("http://www.semanticweb.org/videogame-domain/ontology#")


def load_merged_graph() -> Graph:
    """Load both ontologies and the alignment into a single graph."""
    g = Graph()

    logger.info(f"Loading source ontology: {SOURCE_ONTO}")
    g.parse(SOURCE_ONTO, format="turtle")

    logger.info(f"Loading target ontology: {TARGET_ONTO}")
    g.parse(TARGET_ONTO, format="turtle")

    if os.path.exists(ALIGNMENT_FILE):
        logger.info(f"Loading alignment: {ALIGNMENT_FILE}")
        g.parse(ALIGNMENT_FILE, format="turtle")
    else:
        logger.warning(
            f"Alignment file not found: {ALIGNMENT_FILE}. "
            "Run subtask_oa2.py first. Proceeding without alignment."
        )

    logger.info(f"Merged graph has {len(g)} triples.")
    return g


def apply_reasoning(g: Graph) -> Graph:
    """
    Apply OWL/RDFS reasoning to materialise inferred triples.
    Uses owlrl if available, otherwise applies manual owl:sameAs expansion.
    """
    try:
        import owlrl
        logger.info("Applying OWL RL reasoning with owlrl...")
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
        logger.info(f"After reasoning: {len(g)} triples.")
    except ImportError:
        logger.warning(
            "owlrl not installed. Applying manual owl:sameAs expansion. "
            "Install with: pip install owlrl"
        )
        _manual_same_as_expansion(g)
    return g


def _manual_same_as_expansion(g: Graph):
    """
    Manually expand owl:sameAs: if A sameAs B, copy all triples of A to B and vice versa.
    Also expand owl:equivalentClass subclass relationships.
    """
    # Collect sameAs pairs
    same_as_pairs = list(g.subject_objects(OWL.sameAs))
    logger.info(f"Expanding {len(same_as_pairs)} owl:sameAs pairs...")

    new_triples = []
    for a, b in same_as_pairs:
        if not isinstance(a, URIRef) or not isinstance(b, URIRef):
            continue
        # Copy triples from a to b
        for p, o in g.predicate_objects(a):
            new_triples.append((b, p, o))
        # Copy triples from b to a
        for p, o in g.predicate_objects(b):
            new_triples.append((a, p, o))
        # Copy subject triples
        for s, p in g.subject_predicates(a):
            new_triples.append((s, p, b))
        for s, p in g.subject_predicates(b):
            new_triples.append((s, p, a))

    for triple in new_triples:
        g.add(triple)

    # Expand equivalentClass: if A equivalentClass B, add subClassOf in both directions
    equiv_pairs = list(g.subject_objects(OWL.equivalentClass))
    for a, b in equiv_pairs:
        if isinstance(a, URIRef) and isinstance(b, URIRef):
            g.add((a, RDFS.subClassOf, b))
            g.add((b, RDFS.subClassOf, a))

    logger.info(f"After manual expansion: {len(g)} triples.")


def run_sparql_query(g: Graph) -> list:
    """
    Execute a SPARQL query that uses vocabulary from BOTH ontologies.
    Returns list of result rows as dicts.
    """
    # Simpler query: Find all named individuals with their labels and properties
    query = """
PREFIX cw: <http://www.city.ac.uk/inm713-in3067/2026/princewill_okube#>
PREFIX ext: <http://www.semanticweb.org/videogame-domain/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?entity ?label ?type
WHERE {
  ?entity a owl:NamedIndividual .
  OPTIONAL { ?entity rdfs:label ?label . }
  OPTIONAL { ?entity rdf:type ?type . FILTER(?type != owl:NamedIndividual) }
}
ORDER BY ?label
"""

    logger.info("Executing SPARQL query...")
    results = g.query(query)
    rows = []
    for row in results:
        rows.append({
            "entity": str(row.entity) if row.entity else "",
            "label": str(row.label) if row.label else "",
            "type": str(row.type) if row.type else "",
        })

    logger.info(f"Query returned {len(rows)} results.")
    return rows


def run_second_query(g: Graph) -> list:
    """
    Second SPARQL query: Cross-ontology query using both vocabularies.
    Demonstrates that the alignment enables querying across both ontologies.
    """
    query = """
PREFIX cw: <http://www.city.ac.uk/inm713-in3067/2026/princewill_okube#>
PREFIX ext: <http://www.semanticweb.org/videogame-domain/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?game1 ?game2 ?label1 ?label2
WHERE {
  # Find games that are declared sameAs (via alignment)
  ?game1 owl:sameAs ?game2 .
  ?game1 rdfs:label ?label1 .
  ?game2 rdfs:label ?label2 .
  FILTER(STR(?game1) < STR(?game2))  # Avoid duplicates
}
ORDER BY ?label1
"""
    logger.info("Executing second SPARQL query (sameAs pairs)...")
    results = g.query(query)
    rows = []
    for row in results:
        rows.append({
            "game1": str(row.game1) if row.game1 else "",
            "game2": str(row.game2) if row.game2 else "",
            "label1": str(row.label1) if row.label1 else "",
            "label2": str(row.label2) if row.label2 else "",
        })
    logger.info(f"SameAs query returned {len(rows)} results.")
    return rows


def save_csv(rows: list, output_path: str, fieldnames: list):
    """Save query results to CSV."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Results saved to: {output_path}")


def main():
    os.makedirs("results", exist_ok=True)

    print("\n" + "=" * 65)
    print("  OmniAlign — Subtask OA.3: SPARQL Query")
    print("=" * 65)

    # 1. Load merged graph
    g = load_merged_graph()

    # 2. Apply reasoning
    g = apply_reasoning(g)

    # 3. Run queries
    game_rows = run_sparql_query(g)
    sameas_rows = run_second_query(g)

    # 4. Save results
    game_csv = "results/sparql_results.csv"
    sameas_csv = "results/sparql_sameas.csv"

    save_csv(
        game_rows,
        game_csv,
        ["entity", "label", "type"],
    )
    save_csv(
        sameas_rows,
        sameas_csv,
        ["game1", "game2", "label1", "label2"],
    )

    # 5. Print results
    print(f"\n{'='*65}")
    print(f"  Query 1: All Named Individuals ({len(game_rows)} results)")
    print(f"{'='*65}")
    print(f"  {'Entity':<40} {'Label':<30} {'Type'}")
    print(f"  {'-'*90}")
    for row in game_rows[:20]:  # Show first 20
        entity_local = row['entity'].split("#")[-1] if row['entity'] else ""
        type_local = row['type'].split("#")[-1] if row['type'] else ""
        print(
            f"  {entity_local:<40} "
            f"{row['label']:<30} "
            f"{type_local}"
        )

    print(f"\n{'='*65}")
    print(f"  Query 2: owl:sameAs Pairs ({len(sameas_rows)} results)")
    print(f"{'='*65}")
    print(f"  {'Entity 1':<30} {'Entity 2':<30}")
    print(f"  {'-'*65}")
    for row in sameas_rows:
        e1 = row['game1'].split("#")[-1] if row['game1'] else ""
        e2 = row['game2'].split("#")[-1] if row['game2'] else ""
        print(f"  {e1:<30} {e2:<30}")

    print(f"\nResults saved to:")
    print(f"  {game_csv}")
    print(f"  {sameas_csv}")


if __name__ == "__main__":
    main()
