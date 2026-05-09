"""
Scoring and filtering for ontology alignments
Combines multiple similarity signals and filters results
"""

import logging
from typing import Dict, List, Tuple
from rdflib import URIRef

logger = logging.getLogger(__name__)


# ==============================================================================
# Ensemble Scoring
# ==============================================================================

class EnsembleScorer:
    """Combines multiple similarity scores into final score"""
    
    def __init__(self, weights=None, threshold=0.50):
        """
        weights: dict with 'lexical', 'structural', 'embedding' keys
        threshold: minimum score to accept a mapping
        """
        if weights is None:
            weights = {
                'lexical': 0.30,
                'structural': 0.15,
                'embedding': 0.40,
                'llm': 0.15  # Not used but kept for compatibility
            }
        
        self.weights = weights
        self.threshold = threshold
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in weights.items()}
    
    def compute_score(self, lexical, structural, embedding):
        """
        Compute weighted ensemble score
        Returns float in [0, 1]
        """
        w = self.weights
        
        # Simple weighted average
        score = (
            w.get('lexical', 0) * lexical +
            w.get('structural', 0) * structural +
            w.get('embedding', 0) * embedding
        )
        
        return max(0.0, min(1.0, score))
    
    def determine_relation(self, score, entity_type='class'):
        """
        Determine what type of relation this mapping should be
        
        Args:
            score: similarity score
            entity_type: 'class', 'property', or 'instance'
        
        Returns:
            relation string like 'owl:equivalentClass'
        """
        if entity_type == 'instance':
            return 'owl:sameAs'
        
        if entity_type == 'property':
            # High score = equivalent, lower = subproperty
            if score >= 0.75:
                return 'owl:equivalentProperty'
            else:
                return 'rdfs:subPropertyOf'
        
        # For classes
        if score >= 0.75:
            return 'owl:equivalentClass'
        else:
            # Could be subclass but equivalence is safer
            return 'owl:equivalentClass'
    
    def filter_mappings(self, candidates):
        """
        Filter candidates by threshold and remove duplicates
        
        Args:
            candidates: list of (uri1, uri2, score, relation) tuples
        
        Returns:
            filtered list sorted by score descending
        """
        # Filter by threshold
        filtered = [(u1, u2, s, r) for u1, u2, s, r in candidates 
                   if s >= self.threshold]
        
        # Sort by score
        filtered.sort(key=lambda x: x[2], reverse=True)
        
        return filtered


# ==============================================================================
# Simple Confidence Filtering
# ==============================================================================

def filter_low_confidence(mappings, min_confidence=0.60):
    """
    Remove mappings where the score is suspiciously low compared to others
    
    This is a simple heuristic - just removes the bottom X% of scores
    """
    if len(mappings) < 10:
        return mappings  # Too few to filter
    
    scores = [score for _, _, _, score in mappings]
    avg_score = sum(scores) / len(scores)
    
    # Keep mappings above some fraction of average
    threshold = avg_score * 0.7  # Keep if score > 70% of average
    
    filtered = [(u1, r, u2, s) for u1, r, u2, s in mappings 
               if s >= threshold]
    
    if len(filtered) < len(mappings):
        logger.info(f"Confidence filter: kept {len(filtered)}/{len(mappings)} mappings")
    
    return filtered


def remove_many_to_many(mappings, max_per_entity=5):
    """
    If an entity has too many mappings, keep only the top ones
    This helps avoid noise in large ontologies
    """
    from collections import defaultdict
    
    # Count mappings per entity
    source_counts = defaultdict(list)
    target_counts = defaultdict(list)
    
    for uri1, rel, uri2, score in mappings:
        source_counts[uri1].append((uri2, rel, score))
        target_counts[uri2].append((uri1, rel, score))
    
    # Filter
    filtered = []
    for uri1, rel, uri2, score in mappings:
        # Check if this is in top N for source
        source_mappings = source_counts[uri1]
        if len(source_mappings) > max_per_entity:
            top_scores = sorted([s for _, _, s in source_mappings], reverse=True)
            if score not in top_scores[:max_per_entity]:
                continue
        
        # Check if this is in top N for target
        target_mappings = target_counts[uri2]
        if len(target_mappings) > max_per_entity:
            top_scores = sorted([s for _, _, s in target_mappings], reverse=True)
            if score not in top_scores[:max_per_entity]:
                continue
        
        filtered.append((uri1, rel, uri2, score))
    
    if len(filtered) < len(mappings):
        logger.info(f"Many-to-many filter: kept {len(filtered)}/{len(mappings)}")
    
    return filtered
