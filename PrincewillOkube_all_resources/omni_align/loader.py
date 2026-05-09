"""
OmniAlign — Ontology Loader
Loads OWL ontologies using rdflib and extracts entities with their labels.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import SKOS, DC, DCTERMS

logger = logging.getLogger(__name__)

# Common annotation properties used for labels
LABEL_PROPERTIES = [
    RDFS.label,
    SKOS.prefLabel,
    SKOS.altLabel,
    SKOS.hiddenLabel,
    URIRef("http://purl.org/dc/elements/1.1/title"),
    URIRef("http://purl.org/dc/terms/title"),
    URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"),
    URIRef("http://www.w3.org/2004/02/skos/core#altLabel"),
]


class OntologyLoader:
    """
    Loads an OWL ontology from a file and provides access to its entities.
    Supports .owl (RDF/XML), .ttl (Turtle), .n3, .nt formats.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.graph = Graph()
        self._load()

    def _load(self):
        """Parse the ontology file into an rdflib Graph."""
        logger.info(f"Loading ontology from: {self.filepath}")
        try:
            self.graph.parse(self.filepath)
        except Exception as e:
            # Try common formats explicitly
            for fmt in ["xml", "turtle", "n3", "nt", "json-ld"]:
                try:
                    self.graph = Graph()
                    self.graph.parse(self.filepath, format=fmt)
                    logger.info(f"Loaded with format: {fmt}")
                    return
                except Exception:
                    continue
            raise RuntimeError(f"Could not parse ontology: {self.filepath}") from e
        logger.info(f"Loaded {len(self.graph)} triples from {self.filepath}")

    # ------------------------------------------------------------------
    # Entity extraction helpers
    # ------------------------------------------------------------------

    def get_classes(self) -> Set[URIRef]:
        """Return all OWL classes defined in the ontology."""
        classes = set()
        for s in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(s, URIRef):
                classes.add(s)
        for s in self.graph.subjects(RDF.type, RDFS.Class):
            if isinstance(s, URIRef):
                classes.add(s)
        # Also pick up classes used as domain/range
        for p in [RDFS.domain, RDFS.range, RDFS.subClassOf]:
            for s, o in self.graph.subject_objects(p):
                if isinstance(s, URIRef):
                    classes.add(s)
                if isinstance(o, URIRef):
                    classes.add(o)
        # Remove blank nodes and OWL built-ins
        builtins = {OWL.Thing, OWL.Nothing}
        return {c for c in classes if c not in builtins}

    def get_object_properties(self) -> Set[URIRef]:
        """Return all OWL object properties."""
        props = set()
        for s in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(s, URIRef):
                props.add(s)
        return props

    def get_datatype_properties(self) -> Set[URIRef]:
        """Return all OWL datatype properties."""
        props = set()
        for s in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(s, URIRef):
                props.add(s)
        return props

    def get_all_properties(self) -> Set[URIRef]:
        """Return all properties (object + datatype + rdf:Property)."""
        props = self.get_object_properties() | self.get_datatype_properties()
        for s in self.graph.subjects(RDF.type, RDF.Property):
            if isinstance(s, URIRef):
                props.add(s)
        return props

    def get_individuals(self) -> Set[URIRef]:
        """Return all named individuals."""
        individuals = set()
        for s in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            if isinstance(s, URIRef):
                individuals.add(s)
        return individuals

    def get_labels(self, uri: URIRef) -> List[str]:
        """
        Return all string labels for a URI, including local name fallback.
        """
        labels = []
        for prop in LABEL_PROPERTIES:
            for obj in self.graph.objects(uri, prop):
                if isinstance(obj, Literal):
                    labels.append(str(obj))
        # Fallback: extract local name from URI
        local = self._local_name(uri)
        if local and local not in labels:
            labels.append(local)
        return labels

    @staticmethod
    def _local_name(uri: URIRef) -> str:
        """Extract the local name (fragment or last path segment) from a URI."""
        s = str(uri)
        if "#" in s:
            return s.split("#")[-1]
        return s.rstrip("/").split("/")[-1]

    def get_superclasses(self, uri: URIRef) -> Set[URIRef]:
        """Return direct superclasses of a class."""
        parents = set()
        for o in self.graph.objects(uri, RDFS.subClassOf):
            if isinstance(o, URIRef):
                parents.add(o)
        return parents

    def get_subclasses(self, uri: URIRef) -> Set[URIRef]:
        """Return direct subclasses of a class."""
        children = set()
        for s in self.graph.subjects(RDFS.subClassOf, uri):
            if isinstance(s, URIRef):
                children.add(s)
        return children

    def get_domain(self, prop: URIRef) -> Set[URIRef]:
        """Return domain classes of a property."""
        return {o for o in self.graph.objects(prop, RDFS.domain) if isinstance(o, URIRef)}

    def get_range(self, prop: URIRef) -> Set[URIRef]:
        """Return range classes of a property."""
        return {o for o in self.graph.objects(prop, RDFS.range) if isinstance(o, URIRef)}

    def get_property_values(self, individual: URIRef) -> Dict[URIRef, List]:
        """Return all property-value pairs for an individual."""
        values: Dict[URIRef, List] = {}
        for p, o in self.graph.predicate_objects(individual):
            if p not in (RDF.type,):
                values.setdefault(p, []).append(o)
        return values

    def summary(self) -> str:
        classes = self.get_classes()
        obj_props = self.get_object_properties()
        dt_props = self.get_datatype_properties()
        individuals = self.get_individuals()
        return (
            f"Ontology: {self.filepath}\n"
            f"  Triples:    {len(self.graph)}\n"
            f"  Classes:    {len(classes)}\n"
            f"  Obj Props:  {len(obj_props)}\n"
            f"  Data Props: {len(dt_props)}\n"
            f"  Individuals:{len(individuals)}"
        )
