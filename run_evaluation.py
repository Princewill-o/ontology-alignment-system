#!/usr/bin/env python3
"""
Batch OAEI Evaluation Script (Subtask OA.4)

Evaluates alignment system on all OAEI tasks in dataset directory
Computes Precision, Recall, F-score, and computation time for each task
Saves results to CSV file

Expected dataset structure:
  data/
    conference/
      ontologies/
        cmt.owl
        conference.owl
        ...
      cmt-conference.ttl          (reference alignment)
      cmt-confof.ttl
      ...
    anatomy/
      ontologies/
        mouse.owl
        human.owl
      mouse-human.ttl
    ...

Usage:
  python run_evaluation.py --dataset data/ --output results/evaluation_results.csv
"""

import argparse
import csv
import logging
import os
import time
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

from omni_align.aligner import OmniAligner
from omni_align.alignment_writer import AlignmentWriter
from omni_align.evaluator import compute_metrics, print_metrics


TRACKS = [
    "conference",
    "digital-humanities",
    "circular-economy",
    "anatomy",
    "bio-ml",
    "knowledge-graph"
]

# timeout per track (seconds)
TRACK_TIMEOUTS = {
    "conference": 300,
    "digital_humanities": 300,
    "circular_economy": 300,
    "anatomy": 3600,
    "bio-ml": 7200,
    "knowledge_graph": 7200
}


def find_reference_alignments(track_dir: Path) -> List[Tuple[str, str, str, Path]]:
    """
    Discover all reference alignment files in track directory
    Returns list of (onto1_name, onto2_name, onto1_path, onto2_path, ref_path)
    """
    tasks = []
    onto_dir = track_dir / "ontologies"

    if not onto_dir.exists():
        # try flat structure
        onto_dir = track_dir

    # find all .ttl reference files in track directory (not in ontologies/)
    for ref_file in sorted(track_dir.glob("*.ttl")):
        # parse filename: onto1-onto2.ttl
        stem = ref_file.stem
        parts = stem.split("-")
        if len(parts) < 2:
            continue

        onto1_name = parts[0]
        onto2_name = "-".join(parts[1:])

        # find ontology files
        onto1_path = _find_ontology(onto_dir, onto1_name)
        onto2_path = _find_ontology(onto_dir, onto2_name)

        if onto1_path and onto2_path:
            tasks.append((onto1_name, onto2_name, str(onto1_path), str(onto2_path), ref_file))
        else:
            logger.warning(
                f"Could not find ontologies for {stem}: "
                f"onto1={onto1_path}, onto2={onto2_path}"
            )

    return tasks


def _find_ontology(onto_dir: Path, name: str) -> Optional[Path]:
    """Find ontology file by name (tries .owl, .ttl, .rdf, .n3)"""
    for ext in [".owl", ".ttl", ".rdf", ".n3", ".xml"]:
        p = onto_dir / (name + ext)
        if p.exists():
            return p
    # try case-insensitive
    for f in onto_dir.iterdir():
        if f.stem.lower() == name.lower():
            return f
    return None


def run_evaluation(dataset_dir: str, output_csv: str, alignment_dir: str = "alignments",
                   config_path: str = "config.yaml"):
    """Run full OAEI evaluation"""
    dataset_path = Path(dataset_dir)
    os.makedirs(alignment_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else ".", exist_ok=True)

    # load config
    config = {}
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    writer = AlignmentWriter()
    results = []

    for track_name in TRACKS:
        track_dir = dataset_path / track_name
        if not track_dir.exists():
            # try alternative names
            for alt in [track_name.replace("_", "-"), track_name.replace("-", "_")]:
                alt_dir = dataset_path / alt
                if alt_dir.exists():
                    track_dir = alt_dir
                    break
            else:
                logger.info(f"Track directory not found: {track_dir}, skipping")
                continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Track: {track_name}")
        logger.info(f"{'='*60}")

        tasks = find_reference_alignments(track_dir)
        if not tasks:
            logger.warning(f"No tasks found in {track_dir}")
            continue

        track_timeout = TRACK_TIMEOUTS.get(track_name, 7200)
        # override config timeout for this track
        track_config = dict(config)
        if "scalability" not in track_config:
            track_config["scalability"] = {}
        track_config["scalability"]["timeout_seconds"] = track_timeout

        aligner = OmniAligner(config=track_config)

        for onto1_name, onto2_name, onto1_path, onto2_path, ref_path in tasks:
            task_name = f"{onto1_name}-{onto2_name}"
            output_path = os.path.join(
                alignment_dir, f"omni_align-{onto1_name}-{onto2_name}.ttl"
            )

            logger.info(f"\nTask: {task_name}")
            logger.info(f"  Source: {onto1_path}")
            logger.info(f"  Target: {onto2_path}")
            logger.info(f"  Reference: {ref_path}")

            t_start = time.time()
            timed_out = False

            try:
                mappings, elapsed = aligner.align(
                    source_path=onto1_path,
                    target_path=onto2_path,
                    output_path=output_path,
                    timeout=track_timeout,
                )
            except Exception as e:
                logger.error(f"Error aligning {task_name}: {e}")
                elapsed = time.time() - t_start
                mappings = []
                timed_out = True

            # Load reference alignment
            ref_mappings = writer.load_reference(str(ref_path))

            # Compute metrics
            if mappings and ref_mappings:
                system_triples = [(u1, r, u2) for u1, r, u2, _ in mappings]
                metrics = compute_metrics(system_triples, ref_mappings)
            else:
                metrics = {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f_score": 0.0,
                    "n_system": len(mappings),
                    "n_reference": len(ref_mappings) if ref_mappings else 0,
                    "n_correct": 0,
                }

            print_metrics(metrics, task_name)

            results.append({
                "track": track_name,
                "task": task_name,
                "onto1": onto1_name,
                "onto2": onto2_name,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f_score": metrics["f_score"],
                "n_system": metrics["n_system"],
                "n_reference": metrics["n_reference"],
                "n_correct": metrics["n_correct"],
                "time_seconds": round(elapsed, 2),
                "timed_out": timed_out,
                "output_file": output_path,
            })

    # Write CSV
    _write_csv(results, output_csv)
    logger.info(f"\nResults saved to: {output_csv}")

    # Print summary
    _print_summary(results)


def _write_csv(results: List[Dict], output_path: str):
    """Write evaluation results to CSV."""
    if not results:
        logger.warning("No results to write.")
        return

    fieldnames = [
        "track", "task", "onto1", "onto2",
        "precision", "recall", "f_score",
        "n_system", "n_reference", "n_correct",
        "time_seconds", "timed_out", "output_file",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def _print_summary(results: List[Dict]):
    """Print per-track summary statistics."""
    from collections import defaultdict

    track_results = defaultdict(list)
    for r in results:
        track_results[r["track"]].append(r)

    print(f"\n{'='*70}")
    print(f"{'EVALUATION SUMMARY':^70}")
    print(f"{'='*70}")
    print(f"{'Track':<20} {'Tasks':>5} {'Avg Pr':>8} {'Avg Re':>8} {'Avg F':>8} {'Avg Time':>10}")
    print(f"{'-'*70}")

    for track, track_res in sorted(track_results.items()):
        n = len(track_res)
        avg_pr = sum(r["precision"] for r in track_res) / n
        avg_re = sum(r["recall"] for r in track_res) / n
        avg_f = sum(r["f_score"] for r in track_res) / n
        avg_t = sum(r["time_seconds"] for r in track_res) / n
        timed = sum(1 for r in track_res if r["timed_out"])
        timed_str = f" ({timed} TLE)" if timed else ""
        print(
            f"{track:<20} {n:>5} {avg_pr:>8.4f} {avg_re:>8.4f} {avg_f:>8.4f} "
            f"{avg_t:>8.1f}s{timed_str}"
        )

    print(f"{'='*70}")


def parse_args():
    parser = argparse.ArgumentParser(description="OmniAlign OAEI Evaluation")
    parser.add_argument(
        "--dataset", default="data/", help="Path to OAEI dataset directory"
    )
    parser.add_argument(
        "--output",
        default="results/evaluation_results.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--alignment-dir",
        default="alignments",
        help="Directory to save alignment files",
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_evaluation(
        dataset_dir=args.dataset,
        output_csv=args.output,
        alignment_dir=args.alignment_dir,
        config_path=args.config,
    )
