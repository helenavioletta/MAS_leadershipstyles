"""
Sentiment Analysis: Post-experiment analysis of agent communication logs.

Scores each agent message on a polarity scale from -1.0 (most negative) to
+1.0 (most positive). No LLM calls — fully deterministic and free, so the
whole step can be recomputed from messages.jsonl at any time.

Two analyzers are supported, and both are run on the same messages so their
results are directly comparable:

- "vader"   — VADER (Valence Aware Dictionary and sEntiment Reasoner), a
              rule-based lexicon. Fast, deterministic, no model download.
              Chosen over TextBlob for negation handling ("not good"),
              intensifier support ("very good" > "good"), and because it is
              widely cited. Weakness: it is a social-media lexicon, and it
              scores most formal agent messages as strongly positive, which
              compresses the differences between conditions.
- "roberta" — cardiffnlp/twitter-roberta-base-sentiment-latest, a fine-tuned
              Transformer that reads sentence structure and context instead
              of counting keywords. Agent messages are longer than the
              model's 512-token window, so each message is split into
              consecutive 510-token chunks that together cover the whole
              message; every chunk is scored and the probabilities are
              averaged weighted by chunk token count.

Input:  messages.jsonl from a completed experiment run (the only raw artifact).
Output: sentiment_<analyzer>.json — per-message scores, aggregated metrics,
        and a provenance block recording exactly how the scores were produced
        (analyzer, model, pinned revision, library versions, and a SHA-256 of
        the messages.jsonl they were derived from).

Because the provenance block records the hash of the source file, the output
file doubles as its own cache: re-scoring skips runs that are already up to
date and automatically recomputes runs whose messages or analyzer changed.

Aggregation slices (all derived from per-message scores):
- Per-run composite: overall team climate under this leadership style
- Per-agent: does Coder get frustrated? Does Boss stay positive?
- Per-phase: does sentiment drop during Revision?
- Boss vs workers: is Boss positive while workers are negative?
- Trajectory: does tone improve or worsen over the run?
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional, Union


log = logging.getLogger(__name__)

# Agents whose messages are scored (system messages are excluded)
AGENT_NAMES = {"Boss", "Coder", "Writer", "Reviewer"}
WORKER_NAMES = {"Coder", "Writer", "Reviewer"}


# ─────────────────────────────────────────────
# Scorers
#
# A scorer turns a list of message texts into a list of
# {"neg", "neu", "pos", "compound"} dicts, and describes itself via .meta so
# that every output file states how it was produced.
# ─────────────────────────────────────────────

class VaderScorer:
    """Rule-based VADER lexicon scorer."""

    name = "vader"

    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        self._analyzer = SentimentIntensityAnalyzer()

    @property
    def meta(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": "lexicon",
            "model": "vaderSentiment.SentimentIntensityAnalyzer",
            "compound_definition": "vader_compound",
            "versions": {"vaderSentiment": _version("vaderSentiment")},
        }

    def score(self, texts: list[str]) -> list[dict[str, float]]:
        out = []
        for text in texts:
            s = self._analyzer.polarity_scores(text)
            out.append({
                "neg": s["neg"],
                "neu": s["neu"],
                "pos": s["pos"],
                "compound": s["compound"],
            })
        return out


class RobertaScorer:
    """
    Fine-tuned Transformer scorer with chunked scoring for long messages.

    The model revision is pinned so that re-running this months later
    reproduces the exact same numbers, even if the `-latest` tag moves.
    """

    name = "roberta"

    MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    REVISION = "3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7"
    MAX_TOKENS = 512               # model context window
    CHUNK_TOKENS = MAX_TOKENS - 2  # room for the <s> / </s> special tokens
    BATCH_SIZE = 16
    POOLING = "length_weighted_mean"

    def __init__(self):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.MODEL, revision=self.REVISION
        )
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.MODEL, revision=self.REVISION
        )
        self._model.eval()
        self._bos = self._tokenizer.bos_token_id
        self._eos = self._tokenizer.eos_token_id
        self._pad = self._tokenizer.pad_token_id

    @property
    def meta(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": "transformer",
            "model": self.MODEL,
            "revision": self.REVISION,
            "compound_definition": "positive_minus_negative",
            "chunking": {
                "max_tokens": self.MAX_TOKENS,
                "chunk_tokens": self.CHUNK_TOKENS,
                "pooling": self.POOLING,
            },
            "versions": {
                "transformers": _version("transformers"),
                "torch": _version("torch"),
            },
        }

    def _chunk(self, text: str) -> list[list[int]]:
        """Split text into consecutive <=CHUNK_TOKENS chunks covering all of it."""
        ids = self._tokenizer(text, add_special_tokens=False)["input_ids"]
        step = self.CHUNK_TOKENS
        return [ids[i:i + step] for i in range(0, len(ids), step)]

    def _score_chunks(self, chunks: list[list[int]]) -> list[tuple[float, float, float]]:
        """Score token-id chunks. Returns (neg, neu, pos) per chunk."""
        torch = self._torch
        out = []
        for i in range(0, len(chunks), self.BATCH_SIZE):
            batch = chunks[i:i + self.BATCH_SIZE]
            seqs = [[self._bos] + c + [self._eos] for c in batch]
            width = max(len(s) for s in seqs)
            input_ids = torch.tensor(
                [s + [self._pad] * (width - len(s)) for s in seqs]
            )
            attention_mask = torch.tensor(
                [[1] * len(s) + [0] * (width - len(s)) for s in seqs]
            )
            with torch.no_grad():
                logits = self._model(
                    input_ids=input_ids, attention_mask=attention_mask
                ).logits
            probs = torch.nn.functional.softmax(logits, dim=-1).tolist()
            # Label order for this checkpoint: [negative, neutral, positive]
            out.extend(tuple(p) for p in probs)
        return out

    def score(self, texts: list[str]) -> list[dict[str, float]]:
        out = []
        for text in texts:
            chunks = self._chunk(text)
            if not chunks:
                out.append({"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0})
                continue
            probs = self._score_chunks(chunks)
            weights = [len(c) for c in chunks]
            total = sum(weights)
            neg = sum(p[0] * w for p, w in zip(probs, weights)) / total
            neu = sum(p[1] * w for p, w in zip(probs, weights)) / total
            pos = sum(p[2] * w for p, w in zip(probs, weights)) / total
            out.append({
                "neg": neg,
                "neu": neu,
                "pos": pos,
                "compound": pos - neg,
            })
        return out


SCORERS = {
    VaderScorer.name: VaderScorer,
    RobertaScorer.name: RobertaScorer,
}

ANALYZERS = list(SCORERS.keys())


def get_scorer(analyzer: str):
    """Instantiate a scorer by name ('vader' or 'roberta')."""
    if analyzer not in SCORERS:
        raise ValueError(
            f"Unknown analyzer {analyzer!r}. Available: {', '.join(ANALYZERS)}"
        )
    return SCORERS[analyzer]()


def sentiment_path(output_dir: Union[str, Path], analyzer: str) -> Path:
    """Path of the sentiment artifact for one run and one analyzer."""
    return Path(output_dir) / f"sentiment_{analyzer}.json"


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def analyze_sentiment(
    output_dir: Union[str, Path],
    analyzer: str = "vader",
    scorer: Optional[Any] = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Run sentiment analysis on a completed experiment run.

    Reads messages.jsonl, scores each agent message with the chosen analyzer,
    and computes aggregated metrics by agent, phase, and role.

    Args:
        output_dir: Path to the run's results directory
                    (e.g., results/coercive_short_run01/).
        analyzer:   "vader" or "roberta".
        scorer:     Optional pre-built scorer (avoids reloading a Transformer
                    once per run when scoring many runs in a batch).
        force:      Re-score even if an up-to-date artifact already exists.

    Returns:
        Dict with per-message scores, aggregates, provenance, and metadata.
        Also saved to output_dir/sentiment_<analyzer>.json.
    """
    output_dir = Path(output_dir)
    messages_file = output_dir / "messages.jsonl"
    messages = _load_jsonl(messages_file)

    if not messages:
        log.warning(f"Sentiment: no messages found in {output_dir}")
        return {"messages": [], "aggregates": {}, "valid": False}

    if scorer is None:
        scorer = get_scorer(analyzer)
    analyzer = scorer.name
    analyzer_meta = scorer.meta

    source_meta = {
        "file": messages_file.name,
        "sha256": _sha256(messages_file),
    }

    results_path = sentiment_path(output_dir, analyzer)
    if not force:
        cached = _load_if_current(results_path, analyzer_meta, source_meta)
        if cached is not None:
            log.info(f"Sentiment ({analyzer}): up to date, skipping {output_dir.name}")
            return cached

    # Keep only real agent messages — system messages are phase transitions
    kept = [
        msg for msg in messages
        if msg.get("sender", "") in AGENT_NAMES
        and str(msg.get("content", "")).strip()
    ]

    if not kept:
        log.warning(f"Sentiment: no agent messages to score in {output_dir}")
        return {"messages": [], "aggregates": {}, "valid": False}

    scores = scorer.score([str(msg.get("content", "")) for msg in kept])

    scored_messages = [
        {
            "seq": msg.get("seq"),
            "sender": msg.get("sender"),
            "phase": msg.get("phase"),
            "compound": round(s["compound"], 4),
            "positive": round(s["pos"], 4),
            "negative": round(s["neg"], 4),
            "neutral": round(s["neu"], 4),
        }
        for msg, s in zip(kept, scores)
    ]

    # Compute aggregates
    aggregates = _compute_aggregates(scored_messages)

    results = {
        "analyzer": analyzer_meta,
        "source": {**source_meta, "n_messages": len(scored_messages)},
        "messages": scored_messages,
        "aggregates": aggregates,
        "message_count": len(scored_messages),
        "valid": True,
    }

    # Save results
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(
        f"Sentiment ({analyzer}): scored {len(scored_messages)} messages. "
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
# Provenance helpers
# ─────────────────────────────────────────────

def _version(package: str) -> Optional[str]:
    """Installed version of a package, or None if it cannot be determined."""
    try:
        from importlib.metadata import version

        return version(package)
    except Exception:
        return None


def _sha256(path: Path) -> str:
    """SHA-256 of a file, used to detect whether scores are still current."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _load_if_current(
    results_path: Path,
    analyzer_meta: dict,
    source_meta: dict,
) -> Optional[dict]:
    """
    Return the existing artifact if it was produced from the same messages by
    the same analyzer configuration, otherwise None (meaning: re-score).
    """
    if not results_path.exists():
        return None
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not existing.get("valid"):
        return None
    if existing.get("analyzer") != analyzer_meta:
        return None
    existing_source = existing.get("source", {})
    if existing_source.get("sha256") != source_meta["sha256"]:
        return None
    return existing


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
