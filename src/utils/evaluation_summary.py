"""
Evaluation Summary Generator

Reads the control agent's evaluation.json, the final shared state, and the last
successful code execution for each run, then writes an easy-to-read
evaluation_summary.md in the result folder.

Can be run standalone:
    python src/utils/evaluation_summary.py
    python src/utils/evaluation_summary.py results/coercive_short_run01
    python src/utils/evaluation_summary.py --all
"""

import json
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


def _load_jsonl(path: Path) -> list:
    """Load a JSONL file, returning an empty list if missing."""
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _last_successful_code_execution(code_executions: list) -> Optional[dict]:
    """Return the last successful code execution, or None."""
    for exe in reversed(code_executions):
        if exe.get("success", False):
            return exe
    return None


def _format_scores(scores: dict) -> list:
    """Format the quality score table."""
    order = ["accuracy", "completeness", "cohesion", "quality"]
    out = []
    out.append("| Dimension | Score | Justification |")
    out.append("|-----------|-------|---------------|")
    for dim in order:
        s = scores.get(dim, {})
        score = s.get("score", "N/A")
        just = s.get("justification", "")
        # Replace pipe chars to avoid breaking markdown table
        just = str(just).replace("|", "\\|")
        out.append(f"| {dim.title()} | {score} | {just} |")
    return out


def _format_traps(traps: dict) -> list:
    """Format the trap detection table."""
    out = []
    out.append("| Trap | Status | Evidence |")
    out.append("|------|--------|----------|")
    for trap_id, info in sorted(traps.items()):
        status = info.get("status", "N/A")
        evidence = str(info.get("evidence", "")).replace("|", "\\|")
        out.append(f"| {trap_id} | {status} | {evidence} |")
    return out


def _file_outputs(code_outputs: dict) -> list:
    """Return list of actual saved files (excluding console-output artifacts)."""
    files = []
    for name, info in code_outputs.items():
        if name.startswith("console_output_"):
            continue
        file_path = info.get("file_path")
        if file_path:
            files.append(file_path)
    return files


def generate_evaluation_summary(run_dir: Union[str, Path]) -> Optional[Path]:
    """Generate evaluation_summary.md for a single run directory."""
    run_dir = Path(run_dir)
    eval_path = run_dir / "evaluation.json"
    state_path = run_dir / "shared_state_final.json"
    exec_path = run_dir / "code_executions.jsonl"

    if not eval_path.exists():
        print(f"Skipping {run_dir.name}: evaluation.json not found.")
        return None

    evaluation = _load_json(eval_path)
    state = _load_json(state_path)
    code_executions = _load_jsonl(exec_path)

    task_type = state.get("task_type") or evaluation.get("task_type", "unknown")
    task_spec = state.get("task_spec", "")
    report_draft = state.get("report_draft", "")
    code_outputs = state.get("code_outputs", {})

    last_exec = _last_successful_code_execution(code_executions)
    code_text = ""
    stdout = ""
    if last_exec:
        code_text = last_exec.get("code", "").strip()
        stdout = last_exec.get("stdout", "").strip()

    out = []
    out.append(f"# Control Agent Evaluation — {run_dir.name}")
    out.append("")

    # ── Task specification ─────────────────────────────────────────
    out.append("## Task Specification")
    out.append("")
    if task_spec:
        # task_spec usually starts with '>' blockquote prompts
        out.append(task_spec)
    else:
        out.append(f"Task type: **{task_type}**")
    out.append("")

    # ── Console output (what the judge saw) ────────────────────────
    out.append("## Console Output (from last successful code execution)")
    out.append("")
    if stdout:
        out.append("```text")
        out.append(stdout)
        out.append("```")
    else:
        out.append("*No console output captured.*")
    out.append("")

    # ── Final code ─────────────────────────────────────────────────
    out.append("## Final Code (last successful execution)")
    out.append("")
    if code_text:
        out.append("```python")
        out.append(code_text)
        out.append("```")
    else:
        out.append("*No successful code execution recorded.*")
    out.append("")

    # ── Report ─────────────────────────────────────────────────────
    out.append("## Written Report / Summary")
    out.append("")
    if report_draft:
        out.append(report_draft)
    else:
        out.append("*No report was submitted by the Writer.*")
    out.append("")

    # ── Files produced ─────────────────────────────────────────────
    files = _file_outputs(code_outputs)
    out.append("## Files Produced")
    out.append("")
    if files:
        for f in files:
            out.append(f"- {f}")
    else:
        out.append("*No files produced.*")
    out.append("")

    # ── Evaluation results ─────────────────────────────────────────
    out.append("## Evaluation Results")
    out.append("")

    valid = evaluation.get("valid", False)
    if not valid:
        out.append("⚠️ The control agent's response could not be parsed correctly.")
        out.append("")

    out.append(f"**Valid:** {'Yes' if valid else 'No'}")
    out.append(f"**Overall Quality:** {evaluation.get('overall_quality', 'N/A')}")
    out.append(f"**Quality Mean:** {evaluation.get('quality_mean', 'N/A')}")
    out.append(f"**Trap Catch Rate:** {evaluation.get('trap_catch_rate', 'N/A')}")
    out.append("")

    traps = evaluation.get("traps", {})
    if traps:
        out.append("### Trap Detection")
        out.append("")
        out.extend(_format_traps(traps))
        out.append("")

    scores = evaluation.get("scores", {})
    if scores:
        out.append("### Quality Scores")
        out.append("")
        out.extend(_format_scores(scores))
        out.append("")

    summary = evaluation.get("summary", "")
    if summary:
        out.append("### Summary")
        out.append("")
        out.append(f"{summary}")
        out.append("")

    raw_response = evaluation.get("raw_response", "")
    if raw_response:
        out.append("### Raw Judge Response")
        out.append("")
        out.append(raw_response)

    out_path = run_dir / "evaluation_summary.md"
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Generated: {out_path}")
    return out_path


def generate_all():
    """Generate evaluation_summary.md for all run directories in results/."""
    if not RESULTS_DIR.exists():
        print("No results directory found.")
        return

    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if run_dir.is_dir() and not run_dir.name.startswith("."):
            generate_evaluation_summary(run_dir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--all":
            generate_all()
        else:
            generate_evaluation_summary(arg)
    else:
        generate_all()
