"""
Run a single MAS leadership experiment.

Usage:
    # Run one experiment condition
    python experiments/run_experiments.py --style coercive --task short --run 1

    # Smoke test (pipeline validation only)
    python experiments/run_experiments.py --smoke --style baseline

    # Smoke test with evaluation forced
    python experiments/run_experiments.py --smoke --style baseline --eval

    # Skip evaluation on a regular experiment
    python experiments/run_experiments.py --style coercive --task short --run 1 --skip-eval
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path so we can import src.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from src.agents.boss import BossAgent
from src.agents.coder import CoderAgent
from src.agents.writer import WriterAgent
from src.agents.reviewer import ReviewerAgent
from src.orchestrator import Orchestrator
from src.message_bus import MessageBus
from src.shared_state import SharedState
from src.sandbox import Sandbox
from src.utils.api_client import APIClient
from src.utils.logger import ExperimentLogger
from src.evaluation.control_agent import evaluate_run
from src.evaluation.satisfaction_survey import administer_survey
from src.evaluation.sentiment import analyze_sentiment
from src.agents.base_agent import load_prompt


# ─────────────────────────────────────────────
# Style Mapping: CLI name → prompt filename (without .md)
# ─────────────────────────────────────────────

STYLE_MAP = {
    "baseline": "2_baseline",
    "coercive": "3_coercive",
    "authoritative": "4_authoritative",
    "affiliative": "5_affiliative",
    "democratic": "6_democratic",
    "pacesetting": "7_pacesetting",
    "coaching": "8_coaching",
}

VALID_STYLES = list(STYLE_MAP.keys())
VALID_TASKS = ["short", "long"]


# ─────────────────────────────────────────────
# Config loading
# ─────────────────────────────────────────────

def load_config() -> dict:
    """Load experiment_config.yaml from the config/ directory."""
    config_path = PROJECT_ROOT / "config" / "experiment_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_task_text(task_type: str) -> str:
    """Load task description from config/tasks/{task_type}_task.md."""
    task_path = PROJECT_ROOT / "config" / "tasks" / f"{task_type}_task.md"
    if not task_path.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")
    return task_path.read_text(encoding="utf-8").strip()


# ─────────────────────────────────────────────
# Main run function
# ─────────────────────────────────────────────

def run_single(
    style: str,
    task_type: str,
    run_id: int,
    skip_eval: bool = False,
) -> dict:
    """
    Execute a single experiment run end-to-end.

    Args:
        style: Leadership style short name (e.g., "coercive").
        task_type: Task type ("test", "short", or "long").
        run_id: Repetition number (1, 2, 3, ...).
        skip_eval: If True, skip post-experiment evaluation.

    Returns:
        Dict with run summary (success, duration, tokens, etc.).
    """
    config = load_config()
    style_prompt_name = STYLE_MAP[style]
    task_text = load_task_text(task_type)
    dataset_path = str(PROJECT_ROOT / config["dataset_path"])

    # Models and parameters from config
    boss_model = config["models"]["boss"]
    worker_model = config["models"]["worker"]
    max_tokens_per_response = config["max_tokens_per_response"]
    coder_max_tokens = config.get("coder_max_tokens_per_response", max_tokens_per_response)
    max_revision_rounds = config["max_revision_rounds"]
    max_coding_extensions = config.get("max_coding_extensions", 2)

    # Check if run already completed successfully
    folder_name = f"{style}_{task_type}_run{run_id:02d}"
    run_dir_check = PROJECT_ROOT / "results" / folder_name
    if (run_dir_check / "metadata.json").exists():
        logging.info(f"Skipping run {folder_name}: already complete (metadata.json exists).")
        return {
            "success": True,
            "skipped": True,
            "run_dir": str(run_dir_check),
            "style": style,
            "task_type": task_type,
            "run_id": run_id,
            "duration_seconds": 0,
            "total_tokens": 0,
            "revision_rounds": 0,
            "token_usage_by_agent": {},
        }

    # Build the Boss system prompt (for metadata logging)
    base_role = load_prompt("boss/1_base_role.md")
    style_prompt = load_prompt(f"boss/{style_prompt_name}.md")
    boss_system_prompt = f"{base_role}\n\n{style_prompt}"

    # ── Create ExperimentLogger (creates results folder) ──
    exp_logger = ExperimentLogger(
        style=style,
        task_type=task_type,
        run_id=run_id,
        boss_system_prompt=boss_system_prompt,
        task_wording=task_text,
        boss_model=boss_model,
        worker_model=worker_model,
        max_revision_rounds=max_revision_rounds,
    )
    run_dir = exp_logger.run_dir

    logging.info(f"Run directory: {run_dir}")

    # ── Create infrastructure ──
    api_client = APIClient(output_dir=run_dir)
    message_bus = MessageBus(output_dir=run_dir)
    shared_state = SharedState(
        task_spec=task_text,
        dataset_path=dataset_path,
        task_type=task_type,
        output_dir=run_dir,
    )
    sandbox = Sandbox(
        output_dir=run_dir,
        working_dir=run_dir / "outputs",
    )

    # ── Create agents ──
    boss = BossAgent(
        style=style_prompt_name,
        model=boss_model,
        api_client=api_client,
        message_bus=message_bus,
        shared_state=shared_state,
        max_tokens=max_tokens_per_response,
    )

    coder = CoderAgent(
        model=worker_model,
        api_client=api_client,
        message_bus=message_bus,
        shared_state=shared_state,
        sandbox=sandbox,
        max_tokens=coder_max_tokens,
    )

    writer = WriterAgent(
        model=worker_model,
        api_client=api_client,
        message_bus=message_bus,
        shared_state=shared_state,
        max_tokens=max_tokens_per_response,
    )

    reviewer = ReviewerAgent(
        model=worker_model,
        api_client=api_client,
        message_bus=message_bus,
        shared_state=shared_state,
        max_tokens=max_tokens_per_response,
    )

    # ── Run the orchestrator ──
    orchestrator = Orchestrator(
        boss=boss,
        coder=coder,
        writer=writer,
        reviewer=reviewer,
        message_bus=message_bus,
        shared_state=shared_state,
        max_revision_rounds=max_revision_rounds,
        max_coding_extensions=max_coding_extensions,
    )

    logging.info(f"Starting run: style={style}, task={task_type}, run={run_id}")
    summary = orchestrator.run()
    logging.info(f"Orchestrator finished in {summary['duration_seconds']:.1f}s")

    # ── Save shared state snapshot ──
    shared_state.save_snapshot()

    # ── Post-experiment evaluation ──
    if not skip_eval:
        logging.info("Running post-experiment evaluation...")

        # 1. Control Agent (LLM-as-judge)
        if task_type in ("short", "long"):
            logging.info("  Running control agent evaluation...")
            evaluate_run(
                output_dir=run_dir,
                api_client=api_client,
                model=boss_model,
            )

        # 2. Satisfaction Survey
        logging.info("  Running satisfaction survey...")
        workers = {
            "Coder": {"system_prompt": coder.system_prompt},
            "Writer": {"system_prompt": writer.system_prompt},
            "Reviewer": {"system_prompt": reviewer.system_prompt},
        }
        administer_survey(
            workers=workers,
            message_bus=message_bus,
            api_client=api_client,
            output_dir=run_dir,
            model=worker_model,
        )

        # 3. Sentiment Analysis (no LLM calls — just VADER)
        logging.info("  Running sentiment analysis...")
        analyze_sentiment(output_dir=run_dir)
    else:
        logging.info("Evaluation skipped (--skip-eval or smoke test default)")

    # ── Save metadata (before transcript so transcript generator can read it) ──
    exp_logger.save_metadata(
        total_tokens=api_client.total_tokens,
        total_input_tokens=api_client.total_input_tokens,
        total_output_tokens=api_client.total_output_tokens,
        total_messages=message_bus.message_count,
        total_api_calls=api_client.total_api_calls,
        total_code_executions=sandbox.total_executions,
        extra={
            "revision_rounds": summary["revision_rounds"],
            "token_usage_by_agent": summary["token_usage_by_agent"],
            "evaluation_run": not skip_eval,
            "worker_prompts": {
                "Coder": coder.system_prompt,
                "Writer": writer.system_prompt,
                "Reviewer": reviewer.system_prompt,
            },
        },
    )

    # ── Generate Markdown transcript (after metadata so it can read run config) ──
    message_bus.save_transcript()

    logging.info(f"Run complete. Results saved to: {run_dir}")
    logging.info(
        f"  Total tokens: {api_client.total_tokens:,} "
        f"(input: {api_client.total_input_tokens:,}, "
        f"output: {api_client.total_output_tokens:,})"
    )
    logging.info(f"  API calls: {api_client.total_api_calls}")
    logging.info(f"  Messages: {message_bus.message_count}")

    return {
        "success": True,
        "run_dir": str(run_dir),
        "style": style,
        "task_type": task_type,
        "run_id": run_id,
        **summary,
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a single MAS leadership experiment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--style",
        type=str,
        required=True,
        choices=VALID_STYLES,
        help=f"Leadership style. Options: {', '.join(VALID_STYLES)}",
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=VALID_TASKS,
        default=None,
        help="Task type: 'short' or 'long'. Required unless --smoke is used.",
    )
    parser.add_argument(
        "--run",
        type=int,
        default=1,
        help="Repetition number (default: 1).",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run smoke test (uses test_task.md, skips evaluation by default).",
    )
    parser.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip post-experiment evaluation (control agent, survey, sentiment).",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Force evaluation even on smoke test.",
    )

    args = parser.parse_args()

    # Validation
    if args.smoke:
        if args.task is not None:
            parser.error("--task cannot be used with --smoke (smoke test always uses test_task.md).")
        args.task = "test"
    else:
        if args.task is None:
            parser.error("--task is required when not using --smoke.")

    # Determine whether to skip evaluation
    if args.smoke and not args.eval:
        args.skip_eval = True

    return args


def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()

    logging.info("=" * 60)
    logging.info("MAS Leadership Experiment — Single Run")
    logging.info("=" * 60)
    logging.info(f"  Style:    {args.style}")
    logging.info(f"  Task:     {args.task}")
    logging.info(f"  Run ID:   {args.run}")
    logging.info(f"  Smoke:    {args.smoke}")
    logging.info(f"  Eval:     {'skip' if args.skip_eval else 'run'}")
    logging.info("=" * 60)

    start = time.time()

    try:
        result = run_single(
            style=args.style,
            task_type=args.task,
            run_id=args.run,
            skip_eval=args.skip_eval,
        )
        elapsed = time.time() - start
        logging.info(f"SUCCESS — completed in {elapsed:.1f}s")
        sys.exit(0)

    except KeyboardInterrupt:
        logging.warning("Run interrupted by user.")
        sys.exit(130)

    except Exception as e:
        elapsed = time.time() - start
        logging.error(f"FAILED after {elapsed:.1f}s: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
