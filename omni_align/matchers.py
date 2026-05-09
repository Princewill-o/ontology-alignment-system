"""
Matching functions for ontology alignment
Combines lexical, structural, and embedding-based matching
"""

import logging
from typing import Dict, List, Set, Tuple
from rdflib import URIRef, OWL
import numpy as np

logger = logging.getLogger(__name__)

# Try importing optional dependencies
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    logger.warning("rapidfuzz not available, using basic string matching")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False
    logger.warning("sentence-transformers not available, embedding matching disabled")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ==============================================================================
# String Similarity Functions
# ==============================================================================

def string_similarity(s1, s2):
    """Basic string similarity using rapidfuzz or fallback"""
    if not s1 or not s2:
        return 0.0
    
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    
    if s1 == s2:
        return 1.0
    
    if HAS_RAPIDFUZZ:
        # Use token set ratio - handles word order differences
        return fuzz.token_set_ratio(s1, s2) / 100.0
    else:
        # Simple fallback - jaccard on tokens
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0


def compare_labels(labels1, labels2):
    """
    Compare two lists of labels and return best similarity score
    """
    if not labels1 or not labels2:
        return 0.0
    
    # Check for exact matches first
    set1 = {l.lower().strip() for l in labels1}
    set2 = {l.lower().strip() for l in labels2}
    if set1 & set2:
        return 1.0
    
    # Find best pairwise match
    best = 0.0
    for l1 in labels1:
        for l2 in labels2:
            sim = string_similarity(l1, l2)
            if sim > best:
                best = sim
    return best


# ==============================================================================
# TF-IDF Candidate Generation (Blocking)
# ==============================================================================

class CandidateGenerator:
    """
    Uses TF-IDF to find candidate pairs instead of comparing all pairs
    This speeds things up for large ontologies
    """
    
    def __init__(self, min_score=0.1, max_candidates=50):
        self.min_score = min_score
        self.max_candidates = max_candidates
        self.vectorizer = None
        self.matrix1 = None
        self.matrix2 = None
        self.uris1 = []
        self.uris2 = []
    
    def build_index(self, entities1, entities2):
        """
        Build TF-IDF index for both ontologies
        entities1/2: dict of {uri: [label1, label2, ...]}
        """
        if not HAS_SKLEARN:
            # No sklearn - just return all pairs
            logger.info("sklearn not available, using all pairs")
            self.uris1 = list(entities1.keys())
            self.uris2 = list(entities2.keys())
            return
        
        self.uris1 = list(entities1.keys())
        self.uris2 = list(entities2.keys())
        
        # Combine labels into documents
        docs1 = [" ".join(entities1[u]) for u in self.uris1]
        docs2 = [" ".join(entities2[u]) for u in self.uris2]
        
        # Fit vectorizer on all documents
        all_docs = docs1 + docs2
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),
            min_df=1
        )
        self.vectorizer.fit(all_docs)
        
        # Transform each ontology
        self.matrix1 = self.vectorizer.transform(docs1)
        self.matrix2 = self.vectorizer.transform(docs2)
        
        logger.info(f"Built TF-IDF index: {len(self.uris1)} x {len(self.uris2)} entities")
    
    def get_candidates(self):
        """Return list of (uri1, uri2, tfidf_score) candidate pairs"""
        if not HAS_SKLEARN or self.matrix1 is None:
            # Return all pairs with dummy score
            candidates = []
            for u1 in self.uris1:
                for u2 in self.uris2:
                    candidates.append((u1, u2, 0.5))
            return candidates
        
        candidates = []
        
        # Compute similarities in batches
        batch_size = 500
        for i in range(0, len(self.uris1), batch_size):
            batch = self.matrix1[i:i+batch_size]
            sims = cosine_similarity(batch, self.matrix2)
            
            for bi, row in enumerate(sims):
                uri1 = self.uris1[i + bi]
                # Get indices above threshold
                above_thresh = np.where(row >= self.min_score)[0]
                if len(above_thresh) == 0:
                    continue
                
                # Sort and take top candidates
                sorted_idx = above_thresh[np.argsort(row[above_thresh])[::-1]]
                top_idx = sorted_idx[:self.max_candidates]
                
                for j in top_idx:
                    candidates.append((uri1, self.uris2[j], float(row[j])))
        
        logger.info(f"Generated {len(candidates)} candidate pairs")
        return candidates


# ==============================================================================
# Embedding-based Matching
# ==============================================================================

class EmbeddingMatcher:
    """
    Uses sentence transformers to encode labels and compute semantic similarity
    Good for catching synonyms and related concepts
    """
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embeddings1 = None
        self.embeddings2 = None
        self.uris1 = []
        self.uris2 = []
        self.uri_to_idx1 = {}
        self.uri_to_idx2 = {}
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if not HAS_SBERT:
            return
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
    
    def encode_entities(self, entities1, entities2):
        """
        Pre-compute embeddings for all entities
        entities1/2: dict of {uri: [label1, label2, ...]}
        """
        self._load_model()
        if not HAS_SBERT or self.model is None:
            return
        
        self.uris1 = list(entities1.keys())
        self.uris2 = list(entities2.keys())
        self.uri_to_idx1 = {u: i for i, u in enumerate(self.uris1)}
        self.uri_to_idx2 = {u: i for i, u in enumerate(self.uris2)}
        
        # Create sentences from labels
        sentences1 = []
        for u in self.uris1:
            labels = entities1[u]
            # Use longest label as main text
            if labels:
                main = max(labels, key=len)
                sentences1.append(main)
            else:
                sentences1.append("")
        
        sentences2 = []
        for u in self.uris2:
            labels = entities2[u]
            if labels:
                main = max(labels, key=len)
                sentences2.append(main)
            else:
                sentences2.append("")
        
        logger.info(f"Encoding {len(sentences1)} + {len(sentences2)} entities...")
        self.embeddings1 = self.model.encode(
            sentences1,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        self.embeddings2 = self.model.encode(
            sentences2,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        logger.info("Embeddings computed")
    
    def get_similarity(self, uri1, uri2):
        """Get embedding similarity between two entities"""
        if not HAS_SBERT or self.embeddings1 is None:
            return 0.0
        
        idx1 = self.uri_to_idx1.get(uri1)
        idx2 = self.uri_to_idx2.get(uri2)
        
        if idx1 is None or idx2 is None:
            return 0.0
        
        # Cosine similarity (embeddings are normalized)
        sim = float(np.dot(self.embeddings1[idx1], self.embeddings2[idx2]))
        return max(0.0, sim)  # Clamp to [0, 1]


# ==============================================================================
# Structural Matching (Hierarchy Propagation)
# ==============================================================================

def propagate_similarity(initial_scores, parents1, parents2, children1, children2, 
                        damping=0.5, iterations=2):
    """
    Propagate similarity scores through class hierarchy
    If two classes are similar, their parents/children should also be similar
    
    Args:
        initial_scores: dict of {(uri1, uri2): score}
        parents1/2: dict of {uri: set of parent uris}
        children1/2: dict of {uri: set of child uris}
        damping: how much score to propagate (0-1)
        iterations: number of propagation rounds
    """
    scores = dict(initial_scores)
    
    for iteration in range(iterations):
        updates = {}
        
        for (c1, c2), score in scores.items():
            if score <= 0:
                continue
            
            boost = damping * score
            
            # Propagate to parents
            for p1 in parents1.get(c1, set()):
                for p2 in parents2.get(c2, set()):
                    key = (p1, p2)
                    updates[key] = max(updates.get(key, 0.0), boost)
            
            # Propagate to children
            for ch1 in children1.get(c1, set()):
                for ch2 in children2.get(c2, set()):
                    key = (ch1, ch2)
                    updates[key] = max(updates.get(key, 0.0), boost)
        
        # Merge updates
        for key, val in updates.items():
            scores[key] = max(scores.get(key, 0.0), val)
    
    return scores


def build_hierarchy_info(entities, loader):
    """
    Extract parent/child relationships for a set of entities
    Returns (parents_dict, children_dict)
    """
    parents = {}
    children = {}
    
    for uri in entities:
        p = loader.get_superclasses(uri) & entities
        c = loader.get_subclasses(uri) & entities
        if p:
            parents[uri] = p
        if c:
            children[uri] = c
    
    return parents, children


# ==============================================================================
# Instance Matching
# ==============================================================================

def match_instances(individuals1, individuals2, loader1, loader2, 
                   labels1, labels2, threshold=0.85):
    """
    Match named individuals across ontologies
    Uses label similarity and property values
    """
    mappings = []
    
    if not individuals1 or not individuals2:
        return mappings
    
    logger.info(f"Matching {len(individuals1)} x {len(individuals2)} instances")
    
    # Check existing owl:sameAs links
    for uri1 in individuals1:
        for obj in loader1.graph.objects(uri1, OWL.sameAs):
            if isinstance(obj, URIRef) and obj in individuals2:
                mappings.append((uri1, "owl:sameAs", obj, 1.0))
    
    matched1 = {m[0] for m in mappings}
    matched2 = {m[2] for m in mappings}
    
    # Match remaining by label similarity
    remaining1 = individuals1 - matched1
    remaining2 = individuals2 - matched2
    
    for uri1 in remaining1:
        lbls1 = labels1.get(uri1, [])
        best_score = 0.0
        best_match = None
        
        for uri2 in remaining2:
            lbls2 = labels2.get(uri2, [])
            score = compare_labels(lbls1, lbls2)
            if score > best_score:
                best_score = score
                best_match = uri2
        
        if best_match and best_score >= threshold:
            mappings.append((uri1, "owl:sameAs", best_match, best_score))
    
    logger.info(f"Found {len(mappings)} instance mappings")
    return mappings
