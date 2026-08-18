"""
Survey Summary Generator

Reads survey_results.json from each experiment run and writes a human-readable
survey_results.md with team mean, question-by-question scores, and per-worker
reflections.

Can be run standalone:
    python src/utils/survey_summary.py
    python src/utils/survey_summary.py results/coercive_short_run01
    python src/utils/survey_summary.py --all
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning an empty dict if missing."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _clean_reflection(text: str) -> str:
    """Strip trailing score/json markers from reflection text."""
    if not text:
        return ""
    text = text.strip()
    # Remove trailing Step 2 / Scores headers (case-insensitive)
    text = re.sub(r"\n+\s*#{1,2}\s*Step\s*2.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n+\s*\*\*Scores?:?\*\*.*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _sort_keys(items: dict) -> list:
    """Return question keys in q1..q6 order if possible."""
    def _key(k: str):
        if len(k) > 1 and k[1:].isdigit():
            return int(k[1:])
        return 0
    return sorted(items.keys(), key=_key)


def generate_survey_summary(run_dir: Union[str, Path]) -> Optional[Path]:
    """Generate survey_results.md for a single run directory."""
    run_dir = Path(run_dir)
    survey_path = run_dir / "survey_results.json"

    if not survey_path.exists():
        print(f"Skipping {run_dir.name}: survey_results.json not found.")
        return None

    data = _load_json(survey_path)
    workers = data.get("workers", {})
    items = data.get("items", {})
    team_mean = data.get("team_mean", None)

    out = []
    out.append(f"# Post-Task Satisfaction Survey — {run_dir.name}")
    out.append("")

    # ── Team summary ───────────────────────────────────────────────
    out.append("## Team Summary")
    out.append("")
    out.append("| Worker | Valid | Composite |")
    out.append("|--------|-------|-----------|")

    for worker_name in ("Coder", "Writer", "Reviewer"):
        w = workers.get(worker_name, {})
        valid = w.get("valid", False)
        composite = w.get("composite_score", "N/A")
        out.append(f"| {worker_name} | {'Yes' if valid else 'No'} | {composite} |")

    out.append("")
    if team_mean is not None:
        out.append(f"**Team mean (composite):** {team_mean}")
        out.append("")

    # ── Scores by question ─────────────────────────────────────────
    out.append("## Scores by Question")
    out.append("")

    for q_key in _sort_keys(items):
        question_text = items[q_key]
        out.append(f"### {q_key.upper()} — {question_text}")
        out.append("")
        out.append("| Worker | Raw | Adjusted |")
        out.append("|--------|-----|----------|")

        raw_vals = []
        adj_vals = []
        for worker_name in ("Coder", "Writer", "Reviewer"):
            w = workers.get(worker_name, {})
            raw = w.get("raw_scores", {}).get(q_key, "N/A")
            adj = w.get("adjusted_scores", {}).get(q_key, "N/A")
            out.append(f"| {worker_name} | {raw} | {adj} |")

            if isinstance(raw, (int, float)):
                raw_vals.append(raw)
            if isinstance(adj, (int, float)):
                adj_vals.append(adj)

        if raw_vals and adj_vals:
            raw_mean = round(sum(raw_vals) / len(raw_vals), 3)
            adj_mean = round(sum(adj_vals) / len(adj_vals), 3)
            out.append("")
            out.append(f"*Question mean — raw: {raw_mean}, adjusted: {adj_mean}*")

        out.append("")

    # ── Reflections ────────────────────────────────────────────────
    out.append("## Reflections")
    out.append("")

    for worker_name in ("Coder", "Writer", "Reviewer"):
        w = workers.get(worker_name, {})
        reflection = _clean_reflection(w.get("reflection", ""))
        out.append(f"### {worker_name}")
        out.append("")
        if reflection:
            out.append(reflection)
        else:
            out.append("*No reflection available.*")
        out.append("")

    out_path = run_dir / "survey_results.md"
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Generated: {out_path}")
    return out_path


def generate_all():
    """Generate survey_results.md for all run directories in results/."""
    if not RESULTS_DIR.exists():
        print("No results directory found.")
        return

    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if run_dir.is_dir() and not run_dir.name.startswith("."):
            generate_survey_summary(run_dir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--all":
            generate_all()
        else:
            generate_survey_summary(arg)
    else:
        generate_all()
