#!/usr/bin/env python3
"""
CLI script for running ontology alignment
Takes two ontology files and produces alignment output

Usage:
  python run_alignment.py \\
    --source data/conference/ontologies/cmt.owl \\
    --target data/conference/ontologies/conference.owl \\
    --output alignments/omni_align-cmt-conference.ttl

Optional args:
  --config config.yaml      
  --timeout 7200            
  --threshold 0.50          
  --no-embeddings           
"""

import argparse
import logging
import os
import sys
import yaml

# setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

from omni_align.aligner import OmniAligner


def parse_args():
    parser = argparse.ArgumentParser(description="Ontology Alignment Tool")
    parser.add_argument("--source", required=True, help="source ontology path")
    parser.add_argument("--target", required=True, help="target ontology path")
    parser.add_argument("--output", required=True, help="output file (.ttl)")
    parser.add_argument("--config", default="config.yaml", help="config file")
    parser.add_argument("--timeout", type=int, default=None, help="timeout seconds")
    parser.add_argument("--threshold", type=float, default=None, help="threshold")
    parser.add_argument("--no-embeddings", action="store_true", 
                       help="skip embeddings for speed")
    return parser.parse_args()


def load_config(path: str) -> dict:
    # check if config exists
    if os.path.exists(path):
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)
            return cfg if cfg else {}
    return {}


def main():
    args = parse_args()
    cfg = load_config(args.config)

    # override config with CLI args
    if args.threshold is not None:
        if "matching" not in cfg:
            cfg["matching"] = {}
        cfg["matching"]["threshold"] = args.threshold
    
    if args.no_embeddings:
        if "matching" not in cfg:
            cfg["matching"] = {}
        cfg["matching"]["weights"] = {
            "lexical": 0.55,
            "structural": 0.30,
            "embedding": 0.00,
            "llm": 0.15
        }

    aligner = OmniAligner(config=cfg)

    # print header
    print(f"\n{'='*60}")
    print(f"  Ontology Alignment System")
    print(f"{'='*60}")
    print(f"  Source:  {args.source}")
    print(f"  Target:  {args.target}")
    print(f"  Output:  {args.output}")
    print(f"{'='*60}\n")

    # run alignment
    mappings, elapsed = aligner.align(
        source_path=args.source,
        target_path=args.target,
        output_path=args.output,
        timeout=args.timeout
    )

    print(f"\n{'='*60}")
    print(f"  Done! {len(mappings)} mappings in {elapsed:.1f}s")
    print(f"  Output: {args.output}")
    print(f"{'='*60}\n")

    # show summary
    from collections import Counter
    rel_counts = Counter(r for _, r, _, _ in mappings)
    for rel, count in sorted(rel_counts.items()):
        print(f"  {rel}: {count}")


if __name__ == "__main__":
    main()
