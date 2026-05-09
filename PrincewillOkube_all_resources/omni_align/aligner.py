"""
OmniAlign — Main Alignment Engine
Orchestrates all matching components to produce a complete alignment.

Pipeline:
  1. Load both ontologies
  2. Extract and preprocess entity labels
  3. TF-IDF blocking to generate candidate pairs
  4. For each candidate pair:
       a. Lexical similarity
       b. Structural similarity (hierarchy propagation)
       c. Embedding similarity
       d. LLM verification (optional, borderline pairs only)
       e. Ensemble fusion
  5. Filter by threshold and determine relation types
  6. Match properties separately
  7. Match instances (if any)
  8. Write alignment to Turtle file
"""

import logging
import time
import signal
from typing import Dict, List, Optional, Set, Tuple
from rdflib import URIRef

from omni_align.loader import OntologyLoader
from omni_align.preprocessor import EntityPreprocessor
from omni_align.lexical_matcher import LexicalMatcher, TFIDFBlocker
from omni_align.structural_matcher import StructuralMatcher
from omni_align.embedding_matcher import EmbeddingMatcher
from omni_align.llm_matcher import LLMMatcher
from omni_align.instance_matcher import InstanceMatcher
from omni_align.ensemble import EnsembleScorer
from omni_align.alignment_writer import AlignmentWriter

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutError("Alignment timed out.")


class OmniAligner:
    """
    Main alignment engine for OmniAlign.
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        matching = cfg.get("matching", {})
        scalability = cfg.get("scalability", {})
        llm_cfg = matching.get("llm_verification", {})

        self.threshold = matching.get("threshold", 0.50)
        self.blocking_threshold = matching.get("blocking_threshold", 0.10)
        self.max_candidates = matching.get("max_candidates", 50)
        self.embedding_model = matching.get("embedding_model", "all-MiniLM-L6-v2")
        self.structural_damping = matching.get("structural_damping", 0.5)
        self.timeout = scalability.get("timeout_seconds", 7200)

        weights = matching.get("weights", {})

        # Initialise components
        self.preprocessor = EntityPreprocessor(use_synonyms=True)
        self.lexical = LexicalMatcher()
        self.structural = StructuralMatcher(damping=self.structural_damping)
        self.embedding = EmbeddingMatcher(model_name=self.embedding_model)
        self.llm = LLMMatcher(
            model=llm_cfg.get("model", "gpt-4o-mini"),
            score_min=llm_cfg.get("score_min", 0.45),
            score_max=llm_cfg.get("score_max", 0.75),
            enabled=llm_cfg.get("enabled", False),
        )
        self.instance_matcher = InstanceMatcher(threshold=0.85)
        self.ensemble = EnsembleScorer(weights=weights, threshold=self.threshold)
        self.writer = AlignmentWriter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def align(
        self,
        source_path: str,
        target_path: str,
        output_path: str,
        timeout: Optional[int] = None,
    ) -> List[Tuple[URIRef, str, URIRef, float]]:
        """
        Align two ontologies and write the result to output_path.

        Returns the list of mappings: [(uri1, relation, uri2, score), ...]
        """
        t_start = time.time()
        effective_timeout = timeout or self.timeout

        # Set up timeout (Unix only)
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(effective_timeout)
            use_signal = True
        except (AttributeError, OSError):
            use_signal = False  # Windows doesn't support SIGALRM

        try:
            mappings = self._run_alignment(source_path, target_path, output_path)
        except TimeoutError:
            logger.warning(
                f"Alignment timed out after {effective_timeout}s. "
                f"Saving partial results to {output_path}."
            )
            mappings = []
        finally:
            if use_signal:
                signal.alarm(0)

        elapsed = time.time() - t_start
        logger.info(
            f"Alignment complete: {len(mappings)} mappings in {elapsed:.1f}s"
        )
        return mappings, elapsed

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _run_alignment(
        self,
        source_path: str,
        target_path: str,
        output_path: str,
    ) -> List[Tuple[URIRef, str, URIRef, float]]:

        # 1. Load ontologies
        logger.info("=== Step 1: Loading ontologies ===")
        loader1 = OntologyLoader(source_path)
        loader2 = OntologyLoader(target_path)
        logger.info(loader1.summary())
        logger.info(loader2.summary())

        # 2. Extract entities
        logger.info("=== Step 2: Extracting entities ===")
        classes1 = loader1.get_classes()
        classes2 = loader2.get_classes()
        props1 = loader1.get_all_properties()
        props2 = loader2.get_all_properties()
        inds1 = loader1.get_individuals()
        inds2 = loader2.get_individuals()

        logger.info(
            f"Source: {len(classes1)} classes, {len(props1)} props, {len(inds1)} individuals"
        )
        logger.info(
            f"Target: {len(classes2)} classes, {len(props2)} props, {len(inds2)} individuals"
        )

        # 3. Preprocess labels
        logger.info("=== Step 3: Preprocessing labels ===")
        labels1_cls = self._build_label_map(classes1, loader1)
        labels2_cls = self._build_label_map(classes2, loader2)
        labels1_prop = self._build_label_map(props1, loader1)
        labels2_prop = self._build_label_map(props2, loader2)
        labels1_ind = self._build_label_map(inds1, loader1)
        labels2_ind = self._build_label_map(inds2, loader2)

        all_mappings: List[Tuple[URIRef, str, URIRef, float]] = []

        # 4. Match classes
        logger.info("=== Step 4: Matching classes ===")
        class_mappings = self._match_entities(
            classes1, classes2,
            labels1_cls, labels2_cls,
            loader1, loader2,
            entity_type="class",
        )
        all_mappings.extend(class_mappings)
        logger.info(f"Class mappings: {len(class_mappings)}")

        # 5. Match properties
        logger.info("=== Step 5: Matching properties ===")
        prop_mappings = self._match_entities(
            props1, props2,
            labels1_prop, labels2_prop,
            loader1, loader2,
            entity_type="property",
        )
        all_mappings.extend(prop_mappings)
        logger.info(f"Property mappings: {len(prop_mappings)}")

        # 6. Match instances
        if inds1 and inds2:
            logger.info("=== Step 6: Matching instances ===")
            ind_mappings_raw = self.instance_matcher.match(
                inds1, inds2, loader1, loader2, labels1_ind, labels2_ind
            )
            ind_mappings = [(u1, r, u2, float(s)) for u1, r, u2, s in ind_mappings_raw]
            all_mappings.extend(ind_mappings)
            logger.info(f"Instance mappings: {len(ind_mappings)}")

        # 7. Filter: keep only valid (uri1, relation_str, uri2, score) tuples
        #    where relation_str is one of the 5 accepted alignment relations
        from omni_align.alignment_writer import RELATION_MAP
        valid_mappings = []
        seen_relations = set()
        for item in all_mappings:
            if len(item) != 4:
                continue
            uri1, rel, uri2, score = item
            rel_str = str(rel)
            seen_relations.add(rel_str)
            # Check if it's a valid alignment relation
            if rel_str not in RELATION_MAP:
                continue
            if not isinstance(uri1, URIRef) or not isinstance(uri2, URIRef):
                continue
            try:
                score = float(score)
            except (TypeError, ValueError):
                score = 0.0
            valid_mappings.append((uri1, rel_str, uri2, score))

        logger.info(f"Seen relation types: {seen_relations}")
        logger.info(f"Expected relations: {set(RELATION_MAP.keys())}")
        logger.info(f"Valid alignment mappings after filtering: {len(valid_mappings)}")
        logger.info(f"  Class mappings: {sum(1 for _, r, _, _ in valid_mappings if 'Class' in r)}")
        logger.info(f"  Property mappings: {sum(1 for _, r, _, _ in valid_mappings if 'Property' in r)}")
        logger.info(f"  Instance mappings: {sum(1 for _, r, _, _ in valid_mappings if 'sameAs' in r)}")

        # 8. Write output
        logger.info("=== Step 8: Writing alignment ===")
        self.writer.write(
            valid_mappings,
            output_path,
            source_ontology=source_path,
            target_ontology=target_path,
        )

        return valid_mappings

    def _build_label_map(
        self,
        entities: Set[URIRef],
        loader: OntologyLoader,
    ) -> Dict[URIRef, List[str]]:
        """Build {uri: [normalised_labels]} for a set of entities."""
        label_map = {}
        for uri in entities:
            raw = loader.get_labels(uri)
            processed = self.preprocessor.process(uri, raw)
            label_map[uri] = processed if processed else [str(uri).split("#")[-1].lower()]
        return label_map

    def _match_entities(
        self,
        entities1: Set[URIRef],
        entities2: Set[URIRef],
        labels1: Dict[URIRef, List[str]],
        labels2: Dict[URIRef, List[str]],
        loader1: OntologyLoader,
        loader2: OntologyLoader,
        entity_type: str = "class",
    ) -> List[Tuple[URIRef, str, URIRef, float]]:
        """
        Full matching pipeline for a set of entities.
        """
        if not entities1 or not entities2:
            return []

        # --- Blocking ---
        blocker = TFIDFBlocker(
            threshold=self.blocking_threshold,
            max_candidates=self.max_candidates,
        )
        blocker.fit(labels1, labels2)
        candidates = blocker.get_candidates()

        if not candidates:
            # Fallback: all pairs (for small ontologies)
            candidates = [(u1, u2, 0.5) for u1 in entities1 for u2 in entities2]

        # --- Structural maps ---
        if entity_type == "class":
            sup1, sub1 = self.structural.build_hierarchy_maps(entities1, loader1)
            sup2, sub2 = self.structural.build_hierarchy_maps(entities2, loader2)
        else:
            sup1 = sub1 = sup2 = sub2 = {}

        # --- Embedding ---
        self.embedding.fit(labels1, labels2)

        # --- Initial lexical scores ---
        initial_scores = {}
        for uri1, uri2, _ in candidates:
            if uri1 not in labels1 or uri2 not in labels2:
                continue
            lex = self.lexical.score(labels1[uri1], labels2[uri2])
            initial_scores[(uri1, uri2)] = lex

        # --- Structural propagation ---
        if entity_type == "class":
            propagated = self.structural.propagate(
                initial_scores, sup1, sup2, sub1, sub2
            )
        else:
            propagated = initial_scores

        # --- Ensemble scoring ---
        scored_candidates = []
        for uri1, uri2, tfidf_score in candidates:
            if uri1 not in labels1 or uri2 not in labels2:
                continue

            lex = initial_scores.get((uri1, uri2), 0.0)
            struct = propagated.get((uri1, uri2), lex)
            emb = self.embedding.score(uri1, uri2)

            # Quick pre-filter: skip very low scoring pairs
            if max(lex, emb, tfidf_score) < self.threshold * 0.5:
                continue

            ensemble_score = self.ensemble.fuse(lex, struct, emb, llm=0.5)

            # LLM verification for borderline cases
            llm_relation = "unknown"
            if self.llm.should_verify(ensemble_score):
                lbl1 = labels1[uri1][0] if labels1[uri1] else ""
                lbl2 = labels2[uri2][0] if labels2[uri2] else ""
                cmt1 = str(next(loader1.graph.objects(uri1, __import__('rdflib').RDFS.comment), ""))
                cmt2 = str(next(loader2.graph.objects(uri2, __import__('rdflib').RDFS.comment), ""))
                ensemble_score, llm_relation = self.llm.adjust_score(
                    ensemble_score, lbl1, cmt1, lbl2, cmt2
                )

            relation = self.ensemble.determine_relation(
                ensemble_score, lex, struct, emb,
                llm_relation=llm_relation,
                entity_type=entity_type,
            )

            scored_candidates.append((uri1, uri2, ensemble_score, relation))

        # --- Filter and rank ---
        final = self.ensemble.filter_and_rank(scored_candidates)
        # Convert from (uri1, uri2, score, relation) to (uri1, relation, uri2, score)
        final = [(u1, str(r), u2, s) for u1, u2, s, r in final]
        return final
