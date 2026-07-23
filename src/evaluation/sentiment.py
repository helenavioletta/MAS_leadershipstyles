"""
Sentiment Analysis: Post-experiment analysis of agent communication logs.

Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) to score
each agent message on a polarity scale from -1.0 (most negative) to
+1.0 (most positive). No LLM calls — fully deterministic and free.

VADER was chosen over TextBlob because:
- Better negation handling ("not good" → negative)
- Better intensifier support ("very good" > "good")
- More widely cited in academic research
- Purpose-built for sentiment analysis of short texts

Input: messages.jsonl from a completed experiment run.
Output: sentiment.json with per-message scores and aggregated metrics.

Aggregation slices (all derived from per-message scores):
- Per-run composite: overall team climate under this leadership style
- Per-agent: does Coder get frustrated? Does Boss stay positive?
- Per-phase: does sentiment drop during Revision?
- Boss vs workers: is Boss positive while workers are negative?
- Trajectory: does tone improve or worsen over the run?
"""

import json
import logging
from pathlib import Path
from typing import Any, Union

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


log = logging.getLogger(__name__)

# Agents whose messages are scored (system messages are excluded)
AGENT_NAMES = {"Boss", "Coder", "Writer", "Reviewer"}
WORKER_NAMES = {"Coder", "Writer", "Reviewer"}


def analyze_sentiment(
    output_dir: Union[str, Path],
) -> dict[str, Any]:
    """
    Run sentiment analysis on a completed experiment run.

    Reads messages.jsonl, scores each agent message with VADER,
    and computes aggregated metrics by agent, phase, and role.

    Args:
        output_dir: Path to the run's results directory
                    (e.g., results/coercive_short_run01/).

    Returns:
        Dict with per-message scores, aggregates, and metadata.
        Also saved to output_dir/sentiment.json.
    """
    output_dir = Path(output_dir)
    messages = _load_jsonl(output_dir / "messages.jsonl")

    if not messages:
        log.warning(f"Sentiment: no messages found in {output_dir}")
        return {"messages": [], "aggregates": {}, "valid": False}

    analyzer = SentimentIntensityAnalyzer()

    # Score each agent message
    scored_messages = []
    for msg in messages:
        sender = msg.get("sender", "")

        # Skip system messages — they're phase transitions, not agent communication
        if sender not in AGENT_NAMES:
            continue

        content = msg.get("content", "")
        if not content.strip():
            continue

        # VADER scores
        scores = analyzer.polarity_scores(content)

        scored_messages.append({
            "seq": msg.get("seq"),
            "sender": sender,
            "phase": msg.get("phase"),
            "compound": round(scores["compound"], 4),
            "positive": round(scores["pos"], 4),
            "negative": round(scores["neg"], 4),
            "neutral": round(scores["neu"], 4),
        })

    if not scored_messages:
        log.warning(f"Sentiment: no agent messages to score in {output_dir}")
        return {"messages": [], "aggregates": {}, "valid": False}

    # Compute aggregates
    aggregates = _compute_aggregates(scored_messages)

    results = {
        "messages": scored_messages,
        "aggregates": aggregates,
        "message_count": len(scored_messages),
        "valid": True,
    }

    # Save results
    results_path = output_dir / "sentiment.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(
        f"Sentiment: scored {len(scored_messages)} messages. "
        f"Run mean = {aggregates['run']['mean_compound']:.3f}. "
        f"Saved to {results_path}"
    )

    return results


def _compute_aggregates(
    scored_messages: list[dict],
) -> dict[str, Any]:
    """
    Compute aggregated sentiment metrics from per-message scores.

    Slices:
    - run: overall composite score for the entire run
    - per_agent: mean compound per agent (Boss, Coder, Writer, Reviewer)
    - per_phase: mean compound per workflow phase (1-7)
    - boss_vs_workers: Boss mean vs worker mean + gap
    - trajectory: list of compound scores in message order (for plotting)
    """
    compounds = [m["compound"] for m in scored_messages]

    # ── Run-level ──
    run_agg = {
        "mean_compound": round(_mean(compounds), 4),
        "median_compound": round(_median(compounds), 4),
        "min_compound": round(min(compounds), 4),
        "max_compound": round(max(compounds), 4),
        "std_compound": round(_std(compounds), 4),
        "positive_ratio": round(
            sum(1 for c in compounds if c > 0.05) / len(compounds), 4
        ),
        "negative_ratio": round(
            sum(1 for c in compounds if c < -0.05) / len(compounds), 4
        ),
        "neutral_ratio": round(
            sum(1 for c in compounds if -0.05 <= c <= 0.05) / len(compounds), 4
        ),
    }

    # ── Per-agent ──
    per_agent = {}
    for agent in AGENT_NAMES:
        agent_scores = [
            m["compound"] for m in scored_messages if m["sender"] == agent
        ]
        if agent_scores:
            per_agent[agent] = {
                "mean_compound": round(_mean(agent_scores), 4),
                "message_count": len(agent_scores),
                "positive_ratio": round(
                    sum(1 for c in agent_scores if c > 0.05) / len(agent_scores), 4
                ),
                "negative_ratio": round(
                    sum(1 for c in agent_scores if c < -0.05) / len(agent_scores), 4
                ),
            }

    # ── Per-phase ──
    per_phase = {}
    phases = sorted(set(m["phase"] for m in scored_messages if m["phase"]))
    for phase in phases:
        phase_scores = [
            m["compound"] for m in scored_messages if m["phase"] == phase
        ]
        if phase_scores:
            per_phase[str(phase)] = {
                "mean_compound": round(_mean(phase_scores), 4),
                "message_count": len(phase_scores),
            }

    # ── Boss vs workers ──
    boss_scores = [
        m["compound"] for m in scored_messages if m["sender"] == "Boss"
    ]
    worker_scores = [
        m["compound"] for m in scored_messages if m["sender"] in WORKER_NAMES
    ]

    boss_vs_workers = {}
    if boss_scores:
        boss_vs_workers["boss_mean"] = round(_mean(boss_scores), 4)
    if worker_scores:
        boss_vs_workers["worker_mean"] = round(_mean(worker_scores), 4)
    if boss_scores and worker_scores:
        boss_vs_workers["gap"] = round(
            _mean(boss_scores) - _mean(worker_scores), 4
        )

    # ── Trajectory (for time-series plotting) ──
    trajectory = [
        {"seq": m["seq"], "sender": m["sender"], "compound": m["compound"]}
        for m in scored_messages
    ]

    return {
        "run": run_agg,
        "per_agent": per_agent,
        "per_phase": per_phase,
        "boss_vs_workers": boss_vs_workers,
        "trajectory": trajectory,
    }


# ─────────────────────────────────────────────
# Stats helpers (avoid numpy dependency)
# ─────────────────────────────────────────────

def _mean(values: list[float]) -> float:
    """Arithmetic mean."""
    return sum(values) / len(values) if values else 0.0


def _median(values: list[float]) -> float:
    """Median value."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _std(values: list[float]) -> float:
    """Standard deviation (population)."""
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return variance ** 0.5


# ─────────────────────────────────────────────
# File loader
# ─────────────────────────────────────────────

def _load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file. Returns empty list if file doesn't exist."""
    if not path.exists():
        log.warning(f"Sentiment: file not found: {path}")
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries
