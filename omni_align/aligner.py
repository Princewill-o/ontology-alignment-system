"""
Main alignment engine
Coordinates the matching process between two ontologies
"""

import logging
import time
from typing import Dict, List, Set, Tuple
from rdflib import URIRef, RDFS

from omni_align.ontology_utils import OntologyLoader, LabelProcessor
from omni_align.matchers import (
    CandidateGenerator, EmbeddingMatcher, compare_labels,
    propagate_similarity, build_hierarchy_info, match_instances
)
from omni_align.scoring import EnsembleScorer
from omni_align.alignment_writer import AlignmentWriter

logger = logging.getLogger(__name__)


class OmniAligner:
    """
    Main class for aligning two ontologies
    """
    
    def __init__(self, config=None):
        cfg = config or {}
        matching = cfg.get('matching', {})
        
        self.threshold = matching.get('threshold', 0.50)
        self.blocking_threshold = matching.get('blocking_threshold', 0.10)
        self.max_candidates = matching.get('max_candidates', 50)
        self.embedding_model = matching.get('embedding_model', 'all-MiniLM-L6-v2')
        self.damping = matching.get('structural_damping', 0.5)
        
        weights = matching.get('weights', {})
        
        # Initialize components
        self.label_processor = LabelProcessor(use_synonyms=True)
        self.embedding_matcher = EmbeddingMatcher(model_name=self.embedding_model)
        self.scorer = EnsembleScorer(weights=weights, threshold=self.threshold)
        self.writer = AlignmentWriter()
    
    def align(self, source_path, target_path, output_path, timeout=None):
        """
        Align two ontologies and save results
        
        Returns:
            (mappings, elapsed_time)
        """
        start_time = time.time()
        
        logger.info("Starting alignment...")
        
        # Load ontologies
        logger.info("Loading ontologies...")
        loader1 = OntologyLoader(source_path)
        loader2 = OntologyLoader(target_path)
        
        # Extract entities
        logger.info("Extracting entities...")
        classes1 = loader1.get_classes()
        classes2 = loader2.get_classes()
        props1 = loader1.get_all_properties()
        props2 = loader2.get_all_properties()
        inds1 = loader1.get_individuals()
        inds2 = loader2.get_individuals()
        
        logger.info(f"Source: {len(classes1)} classes, {len(props1)} properties, {len(inds1)} individuals")
        logger.info(f"Target: {len(classes2)} classes, {len(props2)} properties, {len(inds2)} individuals")
        
        # Process labels
        logger.info("Processing labels...")
        labels1_cls = self._get_labels(classes1, loader1)
        labels2_cls = self._get_labels(classes2, loader2)
        labels1_prop = self._get_labels(props1, loader1)
        labels2_prop = self._get_labels(props2, loader2)
        labels1_ind = self._get_labels(inds1, loader1)
        labels2_ind = self._get_labels(inds2, loader2)
        
        all_mappings = []
        
        # Match classes
        logger.info("Matching classes...")
        class_mappings = self._match_entities(
            classes1, classes2,
            labels1_cls, labels2_cls,
            loader1, loader2,
            entity_type='class'
        )
        all_mappings.extend(class_mappings)
        logger.info(f"Found {len(class_mappings)} class mappings")
        
        # Match properties
        logger.info("Matching properties...")
        prop_mappings = self._match_entities(
            props1, props2,
            labels1_prop, labels2_prop,
            loader1, loader2,
            entity_type='property'
        )
        all_mappings.extend(prop_mappings)
        logger.info(f"Found {len(prop_mappings)} property mappings")
        
        # Match instances
        if inds1 and inds2:
            logger.info("Matching instances...")
            ind_mappings = match_instances(
                inds1, inds2,
                loader1, loader2,
                labels1_ind, labels2_ind,
                threshold=0.85
            )
            all_mappings.extend(ind_mappings)
            logger.info(f"Found {len(ind_mappings)} instance mappings")
        
        # Write output
        logger.info("Writing alignment...")
        self.writer.write(
            all_mappings,
            output_path,
            source_ontology=source_path,
            target_ontology=target_path
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Alignment complete: {len(all_mappings)} mappings in {elapsed:.1f}s")
        
        return all_mappings, elapsed
    
    def _get_labels(self, entities, loader):
        """Build label map for entities"""
        label_map = {}
        for uri in entities:
            raw_labels = loader.get_labels(uri)
            processed = self.label_processor.process(uri, raw_labels)
            if not processed:
                # Fallback to local name
                local = str(uri).split('#')[-1].lower()
                processed = [local]
            label_map[uri] = processed
        return label_map
    
    def _match_entities(self, entities1, entities2, labels1, labels2,
                       loader1, loader2, entity_type='class'):
        """
        Match entities using multiple strategies
        """
        if not entities1 or not entities2:
            return []
        
        # Generate candidate pairs using TF-IDF blocking
        logger.info("Generating candidate pairs...")
        candidate_gen = CandidateGenerator(
            min_score=self.blocking_threshold,
            max_candidates=self.max_candidates
        )
        candidate_gen.build_index(labels1, labels2)
        candidates = candidate_gen.get_candidates()
        
        if not candidates:
            # Fallback for small ontologies - compare all pairs
            candidates = [(u1, u2, 0.5) for u1 in entities1 for u2 in entities2]
        
        logger.info(f"Evaluating {len(candidates)} candidate pairs...")
        
        # Compute embeddings
        self.embedding_matcher.encode_entities(labels1, labels2)
        
        # Compute initial lexical scores
        initial_scores = {}
        for uri1, uri2, tfidf_score in candidates:
            if uri1 not in labels1 or uri2 not in labels2:
                continue
            
            lex_score = compare_labels(labels1[uri1], labels2[uri2])
            initial_scores[(uri1, uri2)] = lex_score
        
        # Structural propagation for classes
        if entity_type == 'class':
            logger.info("Propagating through class hierarchy...")
            parents1, children1 = build_hierarchy_info(entities1, loader1)
            parents2, children2 = build_hierarchy_info(entities2, loader2)
            
            structural_scores = propagate_similarity(
                initial_scores,
                parents1, parents2,
                children1, children2,
                damping=self.damping,
                iterations=2
            )
        else:
            structural_scores = initial_scores
        
        # Ensemble scoring
        logger.info("Computing ensemble scores...")
        scored_candidates = []
        
        for uri1, uri2, tfidf_score in candidates:
            if uri1 not in labels1 or uri2 not in labels2:
                continue
            
            # Get individual scores
            lex = initial_scores.get((uri1, uri2), 0.0)
            struct = structural_scores.get((uri1, uri2), lex)
            emb = self.embedding_matcher.get_similarity(uri1, uri2)
            
            # Quick filter - skip very low scores
            if max(lex, emb, tfidf_score) < self.threshold * 0.5:
                continue
            
            # Compute ensemble score
            final_score = self.scorer.compute_score(lex, struct, emb)
            
            # Determine relation type
            relation = self.scorer.determine_relation(final_score, entity_type)
            
            scored_candidates.append((uri1, uri2, final_score, relation))
        
        # Filter by threshold
        final_mappings = self.scorer.filter_mappings(scored_candidates)
        
        # Convert to standard format: (uri1, relation, uri2, score)
        result = [(u1, r, u2, s) for u1, u2, s, r in final_mappings]
        
        return result
