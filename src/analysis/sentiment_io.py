"""
Loading of sentiment artifacts for analysis notebooks.

Reads the per-run, per-analyzer artifacts written by
`src/evaluation/sentiment.py` (results/<run>/sentiment_<analyzer>.json) and
returns tidy DataFrames.

Both sentiment notebooks use this single loader, so the VADER and RoBERTa
analyses are guaranteed to be built from identically filtered and identically
aggregated data — the analyzer is the only thing that differs between them.

Typical use in a notebook:

    from src.analysis.sentiment_io import load_sentiment

    df_msg_sent, df_run_sent = load_sentiment(
        RESULTS_DIR, analyzer='roberta', style_order=STYLE_ORDER
    )
"""

import json
from pathlib import Path
from typing import Optional, Union

import pandas as pd


def find_run_dirs(results_dir: Union[str, Path]) -> list[Path]:
    """Every experiment run directory in results/, sorted by name."""
    results_dir = Path(results_dir)
    return sorted(
        d for d in results_dir.iterdir() if d.is_dir() and "_run" in d.name
    )


def load_sentiment(
    results_dir: Union[str, Path],
    analyzer: str,
    style_order: Optional[list[str]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load message-level and run-level sentiment for one analyzer.

    Args:
        results_dir: Path to the results/ directory.
        analyzer:    'vader' or 'roberta' — selects sentiment_<analyzer>.json.
        style_order: Optional leadership-style order; when given, the `style`
                     column becomes an ordered Categorical.

    Returns:
        (df_msg_sent, df_run_sent)

        df_msg_sent: one row per scored agent message with columns
            seq, sender, phase, compound, positive, negative, neutral,
            style, task, run_id, run_dir
        df_run_sent: one row per run with columns
            style, task, run_id, run_dir, run_mean_compound,
            boss_mean_compound, worker_mean_compound, boss_worker_gap

    Raises:
        FileNotFoundError: if no artifact for this analyzer exists, which means
            the scoring step has not been run yet:
                python experiments/score_sentiment.py --analyzer <analyzer>
    """
    all_messages: list[dict] = []
    all_runs: list[dict] = []
    missing: list[str] = []

    for run_dir in find_run_dirs(results_dir):
        path = run_dir / f"sentiment_{analyzer}.json"
        if not path.exists():
            missing.append(run_dir.name)
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("valid", False):
            continue

        parts = run_dir.name.split("_")
        if len(parts) < 3:
            continue
        style, task, run_id = parts[0], parts[1], parts[2].replace("run", "")

        agg = data.get("aggregates", {})
        run_agg = agg.get("run", {})
        per_agent = agg.get("per_agent", {})
        boss_vs = agg.get("boss_vs_workers", {})

        for msg in data.get("messages", []):
            all_messages.append({
                "seq": msg.get("seq"),
                "sender": msg.get("sender"),
                "phase": msg.get("phase"),
                "compound": msg.get("compound"),
                "positive": msg.get("positive"),
                "negative": msg.get("negative"),
                "neutral": msg.get("neutral"),
                "style": style,
                "task": task,
                "run_id": run_id,
                "run_dir": run_dir.name,
            })

        all_runs.append({
            "style": style,
            "task": task,
            "run_id": run_id,
            "run_dir": run_dir.name,
            "run_mean_compound": run_agg.get("mean_compound"),
            "boss_mean_compound": per_agent.get("Boss", {}).get("mean_compound"),
            "worker_mean_compound": boss_vs.get("worker_mean"),
            "boss_worker_gap": boss_vs.get("gap"),
        })

    if not all_runs:
        raise FileNotFoundError(
            f"No sentiment_{analyzer}.json artifacts found in {results_dir}. "
            f"Run: python experiments/score_sentiment.py --analyzer {analyzer}"
        )
    if missing:
        print(
            f"WARNING: {len(missing)} run(s) have no sentiment_{analyzer}.json "
            f"and were skipped: {', '.join(missing[:5])}"
            f"{' ...' if len(missing) > 5 else ''}"
        )

    df_msg_sent = pd.DataFrame(all_messages)
    df_run_sent = pd.DataFrame(all_runs)

    df_msg_sent["phase"] = pd.to_numeric(df_msg_sent["phase"], errors="coerce")
    if style_order is not None:
        df_msg_sent["style"] = pd.Categorical(
            df_msg_sent["style"], categories=style_order, ordered=True
        )
        df_run_sent["style"] = pd.Categorical(
            df_run_sent["style"], categories=style_order, ordered=True
        )

    return df_msg_sent, df_run_sent


def load_analyzer_meta(results_dir: Union[str, Path], analyzer: str) -> dict:
    """
    Provenance block of the artifacts (analyzer, model, revision, versions).

    Read from the first available run; the scoring step guarantees that all
    runs of one analyzer share the same configuration, because a change to it
    invalidates every artifact.
    """
    for run_dir in find_run_dirs(results_dir):
        path = run_dir / f"sentiment_{analyzer}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("analyzer", {})
    return {}
