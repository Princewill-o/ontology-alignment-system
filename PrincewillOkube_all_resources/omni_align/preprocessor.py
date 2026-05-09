"""
OmniAlign — Label Preprocessor
Normalises entity labels for matching: lowercasing, camelCase splitting,
punctuation removal, stopword filtering, and synonym expansion via WordNet.
"""

import re
import logging
from typing import List, Set, Dict
from rdflib import URIRef

logger = logging.getLogger(__name__)

# Attempt to load NLTK WordNet; gracefully degrade if unavailable
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk.corpus import stopwords as sw

    # Download required NLTK data silently
    for resource in ["wordnet", "stopwords", "omw-1.4"]:
        try:
            nltk.data.find(f"corpora/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)

    ENGLISH_STOPWORDS: Set[str] = set(sw.words("english"))
    WORDNET_AVAILABLE = True
    logger.info("WordNet loaded successfully.")
except Exception as e:
    ENGLISH_STOPWORDS = {
        "a", "an", "the", "of", "in", "on", "at", "to", "for",
        "with", "by", "from", "and", "or", "is", "are", "was",
        "be", "has", "have", "that", "this", "it", "its",
    }
    WORDNET_AVAILABLE = False
    logger.warning(f"WordNet not available: {e}. Synonym expansion disabled.")


def split_camel_case(name: str) -> List[str]:
    """Split a camelCase or PascalCase string into tokens."""
    # Insert space before uppercase letters that follow lowercase letters
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    # Insert space before sequences of uppercase followed by lowercase
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return s.split()


def normalise_label(label: str) -> str:
    """
    Normalise a label string:
    1. Split camelCase
    2. Replace underscores/hyphens with spaces
    3. Lowercase
    4. Remove non-alphanumeric characters
    5. Strip extra whitespace
    """
    # Split camelCase first
    tokens = split_camel_case(label)
    text = " ".join(tokens)
    # Replace separators
    text = re.sub(r"[_\-]", " ", text)
    # Lowercase
    text = text.lower()
    # Remove non-alphanumeric (keep spaces)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenise(label: str) -> List[str]:
    """Normalise and tokenise a label, removing stopwords."""
    normalised = normalise_label(label)
    tokens = normalised.split()
    return [t for t in tokens if t not in ENGLISH_STOPWORDS and len(t) > 1]


def get_synonyms(word: str, max_synonyms: int = 5) -> List[str]:
    """
    Return WordNet synonyms for a word.
    Returns empty list if WordNet is unavailable.
    """
    if not WORDNET_AVAILABLE:
        return []
    synonyms = set()
    for synset in wn.synsets(word, lang="eng"):
        for lemma in synset.lemmas():
            syn = lemma.name().replace("_", " ").lower()
            if syn != word:
                synonyms.add(syn)
        if len(synonyms) >= max_synonyms:
            break
    return list(synonyms)[:max_synonyms]


def expand_with_synonyms(tokens: List[str], max_per_token: int = 3) -> List[str]:
    """Expand a token list with WordNet synonyms."""
    expanded = list(tokens)
    for token in tokens:
        syns = get_synonyms(token, max_per_token)
        expanded.extend(syns)
    return list(set(expanded))


class EntityPreprocessor:
    """
    Preprocesses ontology entities by extracting and normalising their labels.
    Builds a lookup: URI -> list of normalised label strings (with synonyms).
    """

    def __init__(self, use_synonyms: bool = True):
        self.use_synonyms = use_synonyms and WORDNET_AVAILABLE
        self._cache: Dict[str, List[str]] = {}

    def process(self, uri: URIRef, raw_labels: List[str]) -> List[str]:
        """
        Given a URI and its raw labels, return a deduplicated list of
        normalised label strings (including synonym expansions).
        """
        key = str(uri)
        if key in self._cache:
            return self._cache[key]

        processed = set()
        for label in raw_labels:
            norm = normalise_label(label)
            if norm:
                processed.add(norm)
            tokens = tokenise(label)
            if tokens:
                processed.add(" ".join(tokens))
            if self.use_synonyms:
                expanded = expand_with_synonyms(tokens)
                for t in expanded:
                    if t:
                        processed.add(t)

        result = sorted(processed)
        self._cache[key] = result
        return result

    def get_primary_label(self, uri: URIRef, raw_labels: List[str]) -> str:
        """Return the single best normalised label for an entity."""
        processed = self.process(uri, raw_labels)
        if processed:
            # Prefer the longest label as it's usually most descriptive
            return max(processed, key=len)
        # Fallback to local name
        s = str(uri)
        local = s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]
        return normalise_label(local)
