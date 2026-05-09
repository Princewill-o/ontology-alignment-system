#!/usr/bin/env python3
"""
OmniAlign — CLI Entry Point
Aligns two ontologies and writes the result to a Turtle file.

Usage:
  python run_alignment.py \\
    --source data/conference/ontologies/cmt.owl \\
    --target data/conference/ontologies/conference.owl \\
    --output alignments/omni_align-cmt-conference.ttl

Optional:
  --config config.yaml      (default: config.yaml)
  --timeout 7200            (seconds, default from config)
  --threshold 0.50          (override config threshold)
  --no-embeddings           (disable sentence-transformer for speed)
"""

import argparse
import logging
import os
import sys
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from omni_align.aligner import OmniAligner


def parse_args():
    parser = argparse.ArgumentParser(
        description="OmniAlign — Ontology Alignment System"
    )
    parser.add_argument("--source", required=True, help="Path to source ontology")
    parser.add_argument("--target", required=True, help="Path to target ontology")
    parser.add_argument("--output", required=True, help="Path to output alignment (.ttl)")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    parser.add_argument("--threshold", type=float, default=None, help="Similarity threshold")
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Disable sentence-transformer embeddings (faster but less accurate)",
    )
    return parser.parse_args()


def load_config(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    args = parse_args()
    config = load_config(args.config)

    # Apply CLI overrides
    if args.threshold is not None:
        config.setdefault("matching", {})["threshold"] = args.threshold
    if args.no_embeddings:
        config.setdefault("matching", {})["weights"] = {
            "lexical": 0.55,
            "structural": 0.30,
            "embedding": 0.00,
            "llm": 0.15,
        }

    aligner = OmniAligner(config=config)

    print(f"\n{'='*60}")
    print(f"  OmniAlign — Ontology Alignment System")
    print(f"{'='*60}")
    print(f"  Source:  {args.source}")
    print(f"  Target:  {args.target}")
    print(f"  Output:  {args.output}")
    print(f"{'='*60}\n")

    mappings, elapsed = aligner.align(
        source_path=args.source,
        target_path=args.target,
        output_path=args.output,
        timeout=args.timeout,
    )

    print(f"\n{'='*60}")
    print(f"  Done! {len(mappings)} mappings in {elapsed:.1f}s")
    print(f"  Output: {args.output}")
    print(f"{'='*60}\n")

    # Print summary by relation type
    from collections import Counter
    rel_counts = Counter(r for _, r, _, _ in mappings)
    for rel, count in sorted(rel_counts.items()):
        print(f"  {rel}: {count}")


if __name__ == "__main__":
    main()
