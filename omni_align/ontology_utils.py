"""
Ontology loading and label preprocessing utilities
"""

import re
import logging
from typing import Dict, List, Set
from rdflib import Graph, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import SKOS

logger = logging.getLogger(__name__)

# Try to load NLTK for synonym expansion
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk.corpus import stopwords
    
    # Download data if needed
    for resource in ["wordnet", "stopwords", "omw-1.4"]:
        try:
            nltk.data.find(f"corpora/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)
    
    STOPWORDS = set(stopwords.words("english"))
    HAS_WORDNET = True
except Exception as e:
    # Fallback stopwords
    STOPWORDS = {"a", "an", "the", "of", "in", "on", "at", "to", "for", 
                 "with", "by", "from", "and", "or", "is", "are", "was"}
    HAS_WORDNET = False
    logger.warning(f"WordNet not available: {e}")


# Label properties to check
LABEL_PROPS = [
    RDFS.label,
    SKOS.prefLabel,
    SKOS.altLabel,
    SKOS.hiddenLabel,
    URIRef("http://purl.org/dc/elements/1.1/title"),
    URIRef("http://purl.org/dc/terms/title"),
]


# ==============================================================================
# Ontology Loader
# ==============================================================================

class OntologyLoader:
    """Loads and parses OWL ontologies"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.graph = Graph()
        self._load()
    
    def _load(self):
        """Parse the ontology file"""
        logger.info(f"Loading: {self.filepath}")
        try:
            self.graph.parse(self.filepath)
        except Exception:
            # Try different formats
            for fmt in ["xml", "turtle", "n3", "nt"]:
                try:
                    self.graph = Graph()
                    self.graph.parse(self.filepath, format=fmt)
                    logger.info(f"Loaded with format: {fmt}")
                    return
                except Exception:
                    continue
            raise RuntimeError(f"Could not parse: {self.filepath}")
        
        logger.info(f"Loaded {len(self.graph)} triples")
    
    def get_classes(self):
        """Get all OWL classes"""
        classes = set()
        
        # Classes explicitly typed
        for s in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(s, URIRef):
                classes.add(s)
        for s in self.graph.subjects(RDF.type, RDFS.Class):
            if isinstance(s, URIRef):
                classes.add(s)
        
        # Classes used in domain/range/subClassOf
        for p in [RDFS.domain, RDFS.range, RDFS.subClassOf]:
            for s, o in self.graph.subject_objects(p):
                if isinstance(s, URIRef):
                    classes.add(s)
                if isinstance(o, URIRef):
                    classes.add(o)
        
        # Remove OWL built-ins
        classes.discard(OWL.Thing)
        classes.discard(OWL.Nothing)
        
        return classes
    
    def get_object_properties(self):
        """Get all object properties"""
        props = set()
        for s in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(s, URIRef):
                props.add(s)
        return props
    
    def get_datatype_properties(self):
        """Get all datatype properties"""
        props = set()
        for s in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(s, URIRef):
                props.add(s)
        return props
    
    def get_all_properties(self):
        """Get all properties"""
        props = self.get_object_properties() | self.get_datatype_properties()
        for s in self.graph.subjects(RDF.type, RDF.Property):
            if isinstance(s, URIRef):
                props.add(s)
        return props
    
    def get_individuals(self):
        """Get all named individuals"""
        individuals = set()
        for s in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            if isinstance(s, URIRef):
                individuals.add(s)
        return individuals
    
    def get_labels(self, uri):
        """Get all labels for a URI"""
        labels = []
        for prop in LABEL_PROPS:
            for obj in self.graph.objects(uri, prop):
                if isinstance(obj, Literal):
                    labels.append(str(obj))
        
        # Fallback to local name
        local = self._get_local_name(uri)
        if local and local not in labels:
            labels.append(local)
        
        return labels
    
    def _get_local_name(self, uri):
        """Extract local name from URI"""
        s = str(uri)
        if "#" in s:
            return s.split("#")[-1]
        return s.rstrip("/").split("/")[-1]
    
    def get_superclasses(self, uri):
        """Get direct superclasses"""
        parents = set()
        for o in self.graph.objects(uri, RDFS.subClassOf):
            if isinstance(o, URIRef):
                parents.add(o)
        return parents
    
    def get_subclasses(self, uri):
        """Get direct subclasses"""
        children = set()
        for s in self.graph.subjects(RDFS.subClassOf, uri):
            if isinstance(s, URIRef):
                children.add(s)
        return children
    
    def get_domain(self, prop):
        """Get property domain"""
        return {o for o in self.graph.objects(prop, RDFS.domain) 
                if isinstance(o, URIRef)}
    
    def get_range(self, prop):
        """Get property range"""
        return {o for o in self.graph.objects(prop, RDFS.range) 
                if isinstance(o, URIRef)}
    
    def get_property_values(self, individual):
        """Get all property values for an individual"""
        values = {}
        for p, o in self.graph.predicate_objects(individual):
            if p != RDF.type:
                values.setdefault(p, []).append(o)
        return values


# ==============================================================================
# Label Preprocessing
# ==============================================================================

def split_camel_case(text):
    """Split camelCase into separate words"""
    # Insert space before uppercase letters
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return s.split()


def normalize_label(label):
    """
    Normalize a label string:
    - Split camelCase
    - Replace underscores/hyphens
    - Lowercase
    - Remove punctuation
    """
    # Split camelCase
    tokens = split_camel_case(label)
    text = " ".join(tokens)
    
    # Replace separators
    text = re.sub(r"[_\-]", " ", text)
    
    # Lowercase
    text = text.lower()
    
    # Remove non-alphanumeric
    text = re.sub(r"[^a-z0-9\s]", "", text)
    
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def tokenize(label):
    """Tokenize and remove stopwords"""
    norm = normalize_label(label)
    tokens = norm.split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def get_synonyms(word, max_syns=3):
    """Get WordNet synonyms for a word"""
    if not HAS_WORDNET:
        return []
    
    syns = set()
    for synset in wn.synsets(word, lang="eng"):
        for lemma in synset.lemmas():
            syn = lemma.name().replace("_", " ").lower()
            if syn != word:
                syns.add(syn)
        if len(syns) >= max_syns:
            break
    
    return list(syns)[:max_syns]


class LabelProcessor:
    """Processes and normalizes entity labels"""
    
    def __init__(self, use_synonyms=True):
        self.use_synonyms = use_synonyms and HAS_WORDNET
        self.cache = {}
    
    def process(self, uri, raw_labels):
        """
        Process raw labels into normalized forms
        Returns list of normalized label strings
        """
        key = str(uri)
        if key in self.cache:
            return self.cache[key]
        
        processed = set()
        
        for label in raw_labels:
            # Add normalized version
            norm = normalize_label(label)
            if norm:
                processed.add(norm)
            
            # Add tokenized version
            tokens = tokenize(label)
            if tokens:
                processed.add(" ".join(tokens))
            
            # Add synonyms
            if self.use_synonyms:
                for token in tokens:
                    syns = get_synonyms(token)
                    for syn in syns:
                        processed.add(syn)
        
        result = sorted(processed)
        self.cache[key] = result
        return result
    
    def get_primary_label(self, uri, raw_labels):
        """Get the best single label for an entity"""
        processed = self.process(uri, raw_labels)
        if processed:
            # Return longest (usually most descriptive)
            return max(processed, key=len)
        
        # Fallback to local name
        s = str(uri)
        local = s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]
        return normalize_label(local)
