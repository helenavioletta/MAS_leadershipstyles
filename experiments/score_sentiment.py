"""
Standalone sentiment scoring over existing experiment results.

Sentiment is a *derived* artifact: it is computed from messages.jsonl, needs no
API calls, and can therefore be recomputed at any time without re-running the
experiments. This script does exactly that for every run in results/.

Each run gets one artifact per analyzer:

    results/<run>/sentiment_vader.json
    results/<run>/sentiment_roberta.json

Every artifact records the analyzer, the pinned model revision, library
versions, and a SHA-256 of the messages.jsonl it was derived from. That makes
the artifact its own cache: runs that are already up to date are skipped, and
runs whose messages or analyzer configuration changed are re-scored
automatically.

Usage:
    python experiments/score_sentiment.py                        # both analyzers, all runs
    python experiments/score_sentiment.py --analyzer roberta     # one analyzer
    python experiments/score_sentiment.py --run coercive_short_run01
    python experiments/score_sentiment.py --force                # ignore the up-to-date check
    python experiments/score_sentiment.py --dry-run              # list what would be scored
"""

import argparse
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.sentiment import (  # noqa: E402
    ANALYZERS,
    analyze_sentiment,
    get_scorer,
    sentiment_path,
)


RESULTS_DIR = PROJECT_ROOT / "results"


def find_runs(results_dir: Path, only: list[str] | None = None) -> list[Path]:
    """Every run directory that has a messages.jsonl to score."""
    runs = sorted(
        d for d in results_dir.iterdir()
        if d.is_dir() and "_run" in d.name and (d / "messages.jsonl").exists()
    )
    if only:
        wanted = set(only)
        runs = [d for d in runs if d.name in wanted]
        missing = wanted - {d.name for d in runs}
        for name in sorted(missing):
            logging.warning(f"Run not found or has no messages.jsonl: {name}")
    return runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score agent communication sentiment for existing runs."
    )
    parser.add_argument(
        "--analyzer",
        default="all",
        choices=[*ANALYZERS, "all"],
        help="Which analyzer to run (default: all).",
    )
    parser.add_argument(
        "--run",
        action="append",
        metavar="RUN_NAME",
        help="Score only this run (repeatable). Default: every run in results/.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help=f"Results directory (default: {RESULTS_DIR}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-score even when the existing artifact is already up to date.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be scored without writing anything.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    args = parse_args()

    if not args.results_dir.is_dir():
        logging.error(f"Results directory not found: {args.results_dir}")
        return 1

    runs = find_runs(args.results_dir, args.run)
    if not runs:
        logging.error("No runs with messages.jsonl found — nothing to do.")
        return 1

    analyzers = ANALYZERS if args.analyzer == "all" else [args.analyzer]

    logging.info("=" * 60)
    logging.info("Sentiment scoring")
    logging.info("=" * 60)
    logging.info(f"  Runs:      {len(runs)}")
    logging.info(f"  Analyzers: {', '.join(analyzers)}")
    logging.info(f"  Force:     {args.force}")

    if args.dry_run:
        for analyzer in analyzers:
            todo = [
                d.name for d in runs
                if args.force or not sentiment_path(d, analyzer).exists()
            ]
            logging.info(
                f"  [dry-run] {analyzer}: {len(todo)} of {len(runs)} runs missing "
                f"an artifact{' (--force: all would be re-scored)' if args.force else ''}"
            )
        return 0

    exit_code = 0
    for analyzer in analyzers:
        # Build the scorer once per analyzer, not once per run: loading a
        # Transformer 70 times would dominate the runtime.
        logging.info(f"Loading scorer: {analyzer}")
        scorer = get_scorer(analyzer)

        scored = skipped = failed = 0
        started = time.time()
        for i, run_dir in enumerate(runs, start=1):
            path = sentiment_path(run_dir, analyzer)
            before = path.stat().st_mtime if path.exists() else None
            try:
                analyze_sentiment(
                    output_dir=run_dir,
                    scorer=scorer,
                    force=args.force,
                )
            except Exception as e:
                logging.error(f"  [{i}/{len(runs)}] {run_dir.name}: FAILED — {e}")
                failed += 1
                exit_code = 1
                continue
            # The artifact is its own cache, so "was it rewritten?" tells us
            # whether this run actually had to be re-scored.
            after = path.stat().st_mtime if path.exists() else None
            if after is not None and after != before:
                scored += 1
            else:
                skipped += 1

        elapsed = time.time() - started
        logging.info(
            f"{analyzer}: {scored} scored, {skipped} already present, "
            f"{failed} failed in {elapsed:.1f}s"
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
