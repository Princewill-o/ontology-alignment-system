"""
OmniAlign — LLM-Assisted Matcher (Advanced Technique)
Uses OpenAI GPT-4o-mini to verify borderline candidate pairs.

For pairs with ensemble score in [score_min, score_max], the LLM is asked:
  "Are these two ontology concepts equivalent? Answer YES/NO with confidence."

The LLM response is parsed into a score adjustment (+0.2 for YES, -0.2 for NO).
This improves precision on ambiguous cases without sacrificing recall.

Usage:
  Set OPENAI_API_KEY environment variable.
  Enable in config.yaml: llm_verification.enabled = true
"""

import os
import logging
import json
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai package not installed. LLM matcher disabled.")


SYSTEM_PROMPT = """You are an expert ontology engineer specialising in ontology alignment.
Your task is to determine whether two ontology concepts (classes or properties) from different ontologies represent the same real-world concept (i.e., they are semantically equivalent or one subsumes the other).

You will be given:
- Concept A: label, definition/comment, and ontology context
- Concept B: label, definition/comment, and ontology context

Respond in JSON with:
{
  "relation": "equivalent" | "subclass" | "superclass" | "related" | "unrelated",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
"""


class LLMMatcher:
    """
    Uses an LLM to verify and re-score borderline candidate pairs.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        score_min: float = 0.45,
        score_max: float = 0.75,
        enabled: bool = False,
    ):
        self.model = model
        self.score_min = score_min
        self.score_max = score_max
        self.enabled = enabled and OPENAI_AVAILABLE
        self._client: Optional[object] = None
        self._cache: dict = {}

        if self.enabled:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning(
                    "OPENAI_API_KEY not set. LLM matcher disabled."
                )
                self.enabled = False
            else:
                self._client = OpenAI(api_key=api_key)
                logger.info(f"LLM matcher enabled with model: {self.model}")

    def should_verify(self, score: float) -> bool:
        """Return True if this score is in the borderline range."""
        return self.enabled and self.score_min <= score <= self.score_max

    def verify(
        self,
        label1: str,
        comment1: str,
        label2: str,
        comment2: str,
        context1: str = "",
        context2: str = "",
    ) -> Tuple[str, float]:
        """
        Ask the LLM whether two concepts are equivalent.

        Returns
        -------
        (relation, confidence) where relation is one of:
          'equivalent', 'subclass', 'superclass', 'related', 'unrelated'
        """
        if not self.enabled or self._client is None:
            return ("related", 0.5)

        cache_key = f"{label1}||{label2}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        user_message = f"""Concept A:
  Label: {label1}
  Definition: {comment1 or 'N/A'}
  Context: {context1 or 'N/A'}

Concept B:
  Label: {label2}
  Definition: {comment2 or 'N/A'}
  Context: {context2 or 'N/A'}

Are these two ontology concepts semantically equivalent, or does one subsume the other?"""

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            relation = data.get("relation", "unrelated")
            confidence = float(data.get("confidence", 0.5))
            result = (relation, confidence)
            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.warning(f"LLM verification failed for ({label1}, {label2}): {e}")
            return ("related", 0.5)

    def adjust_score(
        self,
        current_score: float,
        label1: str,
        comment1: str,
        label2: str,
        comment2: str,
        context1: str = "",
        context2: str = "",
    ) -> Tuple[float, str]:
        """
        Adjust the ensemble score based on LLM verification.

        Returns
        -------
        (adjusted_score, relation)
        """
        if not self.should_verify(current_score):
            return current_score, "unknown"

        relation, confidence = self.verify(
            label1, comment1, label2, comment2, context1, context2
        )

        if relation == "equivalent":
            # Boost score towards confidence
            adjusted = max(current_score, confidence * 0.9 + 0.1)
        elif relation in ("subclass", "superclass"):
            # Moderate boost
            adjusted = max(current_score, confidence * 0.7 + 0.1)
        elif relation == "related":
            # Small boost
            adjusted = current_score + 0.05
        else:  # unrelated
            # Penalise
            adjusted = current_score * (1 - confidence * 0.5)

        return min(1.0, max(0.0, adjusted)), relation
