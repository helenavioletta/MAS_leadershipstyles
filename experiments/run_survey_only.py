"""
Re-run only the post-task satisfaction survey for existing experiment runs.

This does NOT re-run the orchestrator. It loads the existing `messages.jsonl`
and `metadata.json` for each target run, asks each worker for a fresh
reflection + scores, and saves `survey_results.json`.

Usage:
    # Re-run the survey for one specific run
    python experiments/run_survey_only.py --style coercive --task short --run 1

    # Re-run the survey for all 70 runs
    python experiments/run_survey_only.py --all

    # Overwrite already-rescored runs as well
    python experiments/run_survey_only.py --all --force

    # Preview what would be run without making API calls
    python experiments/run_survey_only.py --all --dry-run
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Add project root to path so we can import src.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.satisfaction_survey import administer_survey
from src.message_bus import MessageBus
from src.utils.api_client import APIClient


# ─────────────────────────────────────────────
# Run target selection
# ─────────────────────────────────────────────

VALID_STYLES = [
    "baseline",
    "coercive",
    "authoritative",
    "affiliative",
    "democratic",
    "pacesetting",
    "coaching",
]
VALID_TASKS = ["short", "long"]


def iter_target_runs(
    style: Optional[str],
    task: Optional[str],
    run_id: Optional[int],
    all_runs: bool,
) -> List[Tuple[str, str, int]]:
    """Return the list of (style, task, run_id) tuples to re-survey."""
    if all_runs:
        return [
            (s, t, r)
            for s in VALID_STYLES
            for t in VALID_TASKS
            for r in range(1, 6)
        ]

    if style is None or task is None or run_id is None:
        raise ValueError(
            "You must either pass --all or specify --style, --task, and --run."
        )
    return [(style, task, run_id)]


def resurvey_run(style: str, task: str, run_id: int, force: bool = False) -> bool:
    """Re-run the satisfaction survey for a single existing run."""
    folder_name = f"{style}_{task}_run{run_id:02d}"
    run_dir = PROJECT_ROOT / "results" / folder_name

    if not run_dir.exists():
        logging.warning(f"Run directory not found, skipping: {run_dir}")
        return False

    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        logging.warning(f"No metadata.json found, skipping: {run_dir}")
        return False

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if not force and (run_dir / "survey_results.json").exists():
        logging.info(f"Skipping {folder_name}: survey_results.json already exists (use --force to override)")
        return False

    worker_prompts = metadata.get("worker_prompts")
    if not worker_prompts or any(role not in worker_prompts for role in ("Coder", "Writer", "Reviewer")):
        logging.warning(f"Missing worker_prompts in metadata, skipping: {folder_name}")
        return False

    worker_model = metadata.get("worker_model")
    if not worker_model:
        logging.warning(f"Missing worker_model in metadata, skipping: {folder_name}")
        return False

    logging.info(f"Re-surveying {folder_name}...")
    message_bus = MessageBus.load_log(run_dir)
    api_client = APIClient(output_dir=run_dir)

    workers = {
        "Coder": {"system_prompt": worker_prompts["Coder"]},
        "Writer": {"system_prompt": worker_prompts["Writer"]},
        "Reviewer": {"system_prompt": worker_prompts["Reviewer"]},
    }

    administer_survey(
        workers=workers,
        message_bus=message_bus,
        api_client=api_client,
        output_dir=run_dir,
        model=worker_model,
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-run only the satisfaction survey for existing experiment runs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=VALID_STYLES,
        default=None,
        help="Leadership style to re-survey.",
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=VALID_TASKS,
        default=None,
        help="Task type to re-survey.",
    )
    parser.add_argument(
        "--run",
        type=int,
        default=None,
        help="Repetition number to re-survey (1-5).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Re-survey all 70 existing runs (7 styles x 2 tasks x 5 reps).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing survey_results.json files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List which runs would be re-surveyed without making API calls.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    targets = iter_target_runs(args.style, args.task, args.run, args.all)

    if args.dry_run:
        logging.info(f"Dry run: would re-survey {len(targets)} runs")
        for style, task, run_id in targets:
            folder_name = f"{style}_{task}_run{run_id:02d}"
            logging.info(f"  - {folder_name}")
        return

    success_count = 0
    for style, task, run_id in targets:
        if resurvey_run(style, task, run_id, force=args.force):
            success_count += 1

    logging.info(f"Re-survey complete. Successful runs: {success_count}/{len(targets)}")


if __name__ == "__main__":
    main()
