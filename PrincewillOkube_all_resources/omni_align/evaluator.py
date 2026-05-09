"""
OmniAlign — Evaluator
Computes Precision, Recall, and F-score for a computed alignment
against a reference alignment.

Metrics:
  Precision = |MS ∩ MRA| / |MS|
  Recall    = |MS ∩ MRA| / |MRA|
  F-score   = 2 * Pr * Re / (Pr + Re)
"""

import logging
from typing import List, Set, Tuple, Dict
from rdflib import URIRef

logger = logging.getLogger(__name__)


def _normalise_mapping(uri1: URIRef, relation: str, uri2: URIRef) -> Tuple:
    """
    Normalise a mapping for comparison.
    Symmetric relations (equivalentClass, equivalentProperty, sameAs)
    are stored in canonical order (smaller URI first).
    """
    symmetric = {
        "owl:equivalentClass",
        "owl:equivalentProperty",
        "owl:sameAs",
    }
    if relation in symmetric and str(uri1) > str(uri2):
        return (uri2, relation, uri1)
    return (uri1, relation, uri2)


def compute_metrics(
    system_mappings: List[Tuple[URIRef, str, URIRef]],
    reference_mappings: List[Tuple[URIRef, str, URIRef]],
    ignore_relation: bool = True,
) -> Dict[str, float]:
    """
    Compute Precision, Recall, and F-score.

    Parameters
    ----------
    system_mappings : list of (uri1, relation, uri2) from the system
    reference_mappings : list of (uri1, relation, uri2) from the reference
    ignore_relation : if True, only compare (uri1, uri2) pairs regardless of relation type

    Returns
    -------
    dict with keys: precision, recall, f_score, n_system, n_reference, n_correct
    """
    if ignore_relation:
        # Compare only entity pairs, ignoring relation type
        sys_set: Set = {
            (min(str(u1), str(u2)), max(str(u1), str(u2)))
            for u1, _, u2 in system_mappings
        }
        ref_set: Set = {
            (min(str(u1), str(u2)), max(str(u1), str(u2)))
            for u1, _, u2 in reference_mappings
        }
    else:
        sys_set = {_normalise_mapping(u1, r, u2) for u1, r, u2 in system_mappings}
        ref_set = {_normalise_mapping(u1, r, u2) for u1, r, u2 in reference_mappings}

    n_system = len(sys_set)
    n_reference = len(ref_set)
    n_correct = len(sys_set & ref_set)

    precision = n_correct / n_system if n_system > 0 else 0.0
    recall = n_correct / n_reference if n_reference > 0 else 0.0
    f_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f_score": round(f_score, 4),
        "n_system": n_system,
        "n_reference": n_reference,
        "n_correct": n_correct,
    }


def print_metrics(metrics: Dict[str, float], task_name: str = ""):
    """Pretty-print evaluation metrics."""
    prefix = f"[{task_name}] " if task_name else ""
    print(
        f"{prefix}Precision={metrics['precision']:.4f}  "
        f"Recall={metrics['recall']:.4f}  "
        f"F-score={metrics['f_score']:.4f}  "
        f"(System={metrics['n_system']}, "
        f"Reference={metrics['n_reference']}, "
        f"Correct={metrics['n_correct']})"
    )
