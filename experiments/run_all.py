"""
Batch runner: Execute all experiment conditions as subprocesses.

Runs 7 styles × 2 tasks × 3 repetitions = 42 experiments.
Smoke test (test task) is NEVER included — use run_experiments.py --smoke for that.

Usage:
    python experiments/run_all.py

Features:
    - Resume support: skips runs that already have a completed results/ folder
    - Retry once on failure, then log and continue
    - Prints progress and final summary table
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml


# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
RESULTS_DIR = PROJECT_ROOT / "results"
RUN_SCRIPT = PROJECT_ROOT / "experiments" / "run_experiments.py"


# ─────────────────────────────────────────────
# Config loading
# ─────────────────────────────────────────────

def load_config() -> dict:
    """Load experiment_config.yaml."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────
# Run completion check
# ─────────────────────────────────────────────

def is_run_complete(style: str, task: str, run_id: int) -> bool:
    """
    Check if a run has already been completed successfully.

    A run is considered complete if its results folder exists AND
    contains a metadata.json file (written at the very end of a run).
    """
    folder_name = f"{style}_{task}_run{run_id:02d}"
    run_dir = RESULTS_DIR / folder_name
    metadata_path = run_dir / "metadata.json"
    return metadata_path.exists()


# ─────────────────────────────────────────────
# Single run execution (subprocess)
# ─────────────────────────────────────────────

def execute_run(style: str, task: str, run_id: int) -> dict:
    """
    Execute a single experiment run as a subprocess.

    Args:
        style: Leadership style short name.
        task: Task type ("short" or "long").
        run_id: Repetition number.

    Returns:
        Dict with keys: success, style, task, run_id, duration, error
    """
    cmd = [
        sys.executable,
        str(RUN_SCRIPT),
        "--style", style,
        "--task", task,
        "--run", str(run_id),
    ]

    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=1800,  # 30 minute timeout per run
        )
        duration = time.time() - start

        if result.returncode == 0:
            return {
                "success": True,
                "style": style,
                "task": task,
                "run_id": run_id,
                "duration": round(duration, 1),
                "error": None,
            }
        else:
            # Extract last few lines of stderr for error context
            stderr_tail = "\n".join(result.stderr.strip().split("\n")[-5:])
            return {
                "success": False,
                "style": style,
                "task": task,
                "run_id": run_id,
                "duration": round(duration, 1),
                "error": stderr_tail or f"Exit code {result.returncode}",
            }

    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return {
            "success": False,
            "style": style,
            "task": task,
            "run_id": run_id,
            "duration": round(duration, 1),
            "error": "Timeout (30 minutes exceeded)",
        }

    except Exception as e:
        duration = time.time() - start
        return {
            "success": False,
            "style": style,
            "task": task,
            "run_id": run_id,
            "duration": round(duration, 1),
            "error": str(e),
        }


# ─────────────────────────────────────────────
# Main batch runner
# ─────────────────────────────────────────────

def main():
    """Run all experiment conditions."""
    config = load_config()

    styles = config["styles"]
    tasks = config["experiment_tasks"]
    repetitions = config["repetitions"]

    # Build full list of conditions
    conditions = []
    for style in styles:
        for task in tasks:
            for run_id in range(1, repetitions + 1):
                conditions.append((style, task, run_id))

    total = len(conditions)
    print("=" * 70)
    print("MAS Leadership Experiment — Batch Runner")
    print("=" * 70)
    print(f"  Styles:      {', '.join(styles)}")
    print(f"  Tasks:       {', '.join(tasks)}")
    print(f"  Repetitions: {repetitions}")
    print(f"  Total runs:  {total}")
    print(f"  Started:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Check which runs are already complete
    skipped = []
    to_run = []
    for style, task, run_id in conditions:
        if is_run_complete(style, task, run_id):
            skipped.append((style, task, run_id))
        else:
            to_run.append((style, task, run_id))

    if skipped:
        print(f"\n  Skipping {len(skipped)} already-completed run(s).")
    print(f"  Runs to execute: {len(to_run)}")
    print()

    # Execute runs
    results = []
    batch_start = time.time()

    for i, (style, task, run_id) in enumerate(to_run, 1):
        label = f"{style}_{task}_run{run_id:02d}"
        print(f"[{i}/{len(to_run)}] Running {label}...", end=" ", flush=True)

        result = execute_run(style, task, run_id)

        if result["success"]:
            print(f"OK ({result['duration']:.0f}s)")
            results.append(result)
        else:
            print(f"FAILED ({result['duration']:.0f}s)")
            print(f"         Error: {result['error']}")

            # Retry once
            print(f"         Retrying {label}...", end=" ", flush=True)
            retry_result = execute_run(style, task, run_id)

            if retry_result["success"]:
                print(f"OK ({retry_result['duration']:.0f}s)")
                results.append(retry_result)
            else:
                print(f"FAILED again ({retry_result['duration']:.0f}s)")
                print(f"         Error: {retry_result['error']}")
                results.append(retry_result)

    batch_duration = time.time() - batch_start

    # ── Summary ──
    passed = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print()
    print("=" * 70)
    print("BATCH SUMMARY")
    print("=" * 70)
    print(f"  Total conditions:  {total}")
    print(f"  Skipped (existed): {len(skipped)}")
    print(f"  Executed:          {len(results)}")
    print(f"  Passed:            {len(passed)}")
    print(f"  Failed:            {len(failed)}")
    print(f"  Batch duration:    {batch_duration:.0f}s ({batch_duration/60:.1f} min)")
    print(f"  Finished:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if failed:
        print()
        print("FAILED RUNS:")
        print("-" * 70)
        for r in failed:
            label = f"{r['style']}_{r['task']}_run{r['run_id']:02d}"
            print(f"  {label}: {r['error']}")

    print("=" * 70)

    # Exit with error code if any runs failed
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
