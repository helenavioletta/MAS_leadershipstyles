"""
Control Agent: Post-experiment evaluation workflow (LLM-as-judge).

Evaluates the team's final deliverable by sending it to an LLM with
a fixed rubric and task-specific reference values. NOT an agent that
participates in the experiment — it runs after completion.

Two evaluation axes:
A. Trap Detection — Did the team catch known data quality issues?
   (outliers, sentinel values, duplicate country names, trivial features)
B. Quality Scoring — How good is the deliverable? (1-5 on four dimensions)

The LLM judge receives:
- Task specification (what was asked)
- All code executed + stdout (from code_executions.jsonl)
- Report/summary text (from shared_state_final.json)
- Reference values from our notebook (NOT ground truth — one valid approach)
- List of traps to check (task-specific)

IMPORTANT: The reference notebook is NOT definitive ground truth. It shows
one valid way to solve the task. The MAS may solve it differently and still
be correct. The control agent should primarily evaluate whether the output
makes sense on its own merits, using the reference for context (e.g., to
detect red flags like suspiciously high R² from trivial features).

Output: evaluation.json in the run's output directory.

Reference baselines established in:
- notebooks/01_explore_dataset.ipynb (data quality issues, outliers, duplicates)
- notebooks/01_long_task_ground_truth.ipynb (correct vs. cheating R² values)

See: prompts/control_agent.md for the evaluation rubric.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional, Union

from src.agents.base_agent import load_prompt
from src.utils.api_client import APIClient


log = logging.getLogger(__name__)

# Base rubric loaded from prompts/control_agent.md
EVALUATION_RUBRIC = load_prompt("control_agent.md")

# Maximum characters of code/stdout to send to the judge (prevent token explosion)
MAX_CODE_CHARS = 15_000
MAX_STDOUT_CHARS = 5_000

# ─────────────────────────────────────────────
# Reference Values & Traps (per task type)
# NOTE: These are reference values from our notebook, NOT absolute ground truth.
# The MAS can produce different (but valid) results and still score well.
# ─────────────────────────────────────────────

SHORT_TASK_TRAPS = {
    "outlier_79c": {
        "description": (
            "The dataset contains a 79.3°C temperature reading for Suva (Fiji Islands). "
            "This is physically impossible (Earth's record is 56.7°C). "
            "WHERE TO CHECK: Look at the PRINTED top 10 hottest cities by max measurement "
            "in the console output (stdout). If Suva appears at the top, this trap was missed. "
            "Also check the code for any filtering/removal of this value. "
            "Caught = Suva is removed or flagged. Partial = mentioned but not removed."
        ),
    },
    "country_name_duplicates": {
        "description": (
            "The dataset contains non-English country names that are duplicates of English entries, "
            "each with only 1 observation. Because they have just 1 data point, their average "
            "temperature equals that single reading, which pushes them to the top of the rankings. "
            "The affected entries that appear in the raw top 10 hottest countries by average are: "
            "'Saudi Arabien' (German for Saudi Arabia), 'Marrocos' (Portuguese for Morocco), "
            "'Turkménistan' (French for Turkmenistan), 'Турция' (Russian for Turkey). "
            "WHERE TO CHECK: Look at the PRINTED top 10 hottest countries by average "
            "in the console output (stdout). Do any of these 4 names appear? "
            "Caught = team identified and removed/merged at least 3 of these 4. "
            "Partial = team caught 1-2 of these 4. "
            "Missed = all 4 still present or none were addressed."
        ),
    },
    "city_name_duplicates": {
        "description": (
            "The dataset contains duplicate city entries with only 1 observation each: "
            "'Ar Riyadh' (1 obs, duplicate of 'Riyadh' with 772 obs) and "
            "'Kuwait' (1 obs, duplicate of 'Kuwait City' with 771 obs). "
            "Because they have just 1 data point, they appear in the top 10 hottest cities "
            "by average temperature. "
            "WHERE TO CHECK: Look at the PRINTED top 10 hottest cities by average "
            "in the console output (stdout). Do 'Ar Riyadh' or 'Kuwait' appear? "
            "Caught = team dropped or merged both. "
            "Partial = team handled one but not the other. "
            "Missed = both still present in the rankings."
        ),
    },
}

SHORT_TASK_GROUND_TRUTH = (
    "## Reference Notebook Values — Short Task\n\n"
    "**NOTE: This is NOT absolute ground truth.** These values come from one valid "
    "reference solution. The team may have used different (but correct) approaches "
    "and produced different results. Evaluate whether their output is internally "
    "consistent and methodologically sound, not whether it exactly matches these numbers.\n\n"
    "Task: Produce 4 bar charts (top 10 hottest cities by avg and by max, "
    "top 10 hottest countries by avg and by max) + 200-word summary.\n\n"
    "Key facts from reference notebook:\n"
    "- The dataset has 150,465 rows and 268 unique locations.\n"
    "- The 79.3°C reading for Suva (Fiji) is a data error — it inflates the "
    "top 10 hottest cities by MAX measurement (Suva appears #1 if not removed).\n"
    "- Four non-English country names with only 1 observation each inflate the "
    "top 10 hottest countries by AVERAGE: 'Saudi Arabien', 'Marrocos', "
    "'Turkménistan', 'Турция'. With just 1 data point their average equals "
    "that single hot reading, pushing them above legitimate countries.\n"
    "- Two duplicate city names with only 1 observation each inflate the "
    "top 10 hottest cities by AVERAGE: 'Ar Riyadh' (duplicate of 'Riyadh') "
    "and 'Kuwait' (duplicate of 'Kuwait City').\n\n"
    "HOW TO VERIFY (you cannot see charts, use console output instead):\n"
    "- The task requires the team to PRINT all 4 top-10 lists to the console.\n"
    "- Check stdout for the printed rankings. These are the actual values behind the charts.\n"
    "- Verify that 4 PNG chart files were saved (check files produced list).\n"
    "- For traps: check the PRINTED top-10 lists — do problematic names appear?\n\n"
    "Expected deliverables: 4 bar charts (saved as PNG) + 4 printed top-10 lists "
    "(in console output) + 1 summary (~100 words).\n\n"
    "The team may handle data issues differently (e.g., filter outliers vs. cap them, "
    "merge duplicates vs. drop one variant) — any reasonable approach is acceptable.\n"
)

LONG_TASK_TRAPS = {
    "trivial_features": {
        "description": (
            "The dataset contains features that are trivially correlated with the target "
            "(temperature_celsius): temperature_fahrenheit (= celsius × 9/5 + 32), "
            "feels_like_celsius (~0.98 correlation), feels_like_fahrenheit. "
            "Including ANY of these as model features makes R² ≈ 1.0, rendering the "
            "model comparison meaningless. The team MUST exclude these. "
            "RED FLAG: If either model achieves R² > 0.99, trivial features were "
            "almost certainly included."
        ),
    },
    "sentinel_values": {
        "description": (
            "Three air quality columns contain sentinel values (-9999) representing "
            "missing data: air_quality_Carbon_Monoxide (1 row), "
            "air_quality_Sulphur_dioxide (1 row), air_quality_PM10 (2 rows with "
            "values -1848.15 and -998.15). These should be replaced with NaN or the "
            "rows should be dropped. Impact is minimal (4 rows out of 150K) but "
            "shows methodology awareness."
        ),
    },
    "outlier_79c": {
        "description": (
            "The dataset contains a 79.3°C temperature reading for Suva (Fiji Islands). "
            "This is physically impossible and should be removed before modeling, "
            "especially since it is the TARGET variable."
        ),
    },
    "duplicate_unit_features": {
        "description": (
            "The dataset contains measurements in duplicate units: "
            "wind_mph/wind_kph, gust_mph/gust_kph, pressure_mb/pressure_in, "
            "precip_mm/precip_in, visibility_km/visibility_miles. "
            "Including both units for the same measurement introduces perfect "
            "multicollinearity. The team should keep only one unit per measurement."
        ),
    },
}

LONG_TASK_GROUND_TRUTH = (
    "## Reference Notebook Values — Long Task\n\n"
    "**NOTE: This is NOT absolute ground truth.** These values come from one valid "
    "reference solution. The team may have used different models, different feature "
    "engineering, or different hyperparameters and still produced excellent work. "
    "Evaluate whether their approach is methodologically sound and internally "
    "consistent, not whether it exactly matches these numbers.\n\n"
    "Task: Build two predictive models for temperature_celsius (one tree-based, "
    "one linear), produce 4 visualizations, and write a 600-word analytical report.\n\n"
    "Reference values from our notebook (one valid approach):\n"
    "- Random Forest R² ≈ 0.93, MAE ≈ 1.66°C (reasonable range: R² 0.85–0.95)\n"
    "- Ridge Regression R² ≈ 0.52, MAE ≈ 5.15°C (reasonable range: R² 0.40–0.65)\n"
    "- Target variable: temperature_celsius\n"
    "- Sensible feature count: ~17 features (excluding trivial correlations and "
    "duplicate units). Reference feature set: humidity, wind_kph, wind_degree, "
    "pressure_mb, precip_mm, cloud, uv_index, gust_kph, visibility_km, "
    "air_quality_Carbon_Monoxide, air_quality_Ozone, air_quality_Nitrogen_dioxide, "
    "air_quality_Sulphur_dioxide, air_quality_PM2.5, air_quality_PM10, latitude, "
    "longitude. The team's features do not need to match exactly but should be "
    "approximately similar — the key point is excluding trivial/duplicate features.\n"
    "- Top features by importance in reference: latitude, uv_index, pressure_mb, "
    "humidity, longitude (team may find different top features depending on their "
    "feature engineering — this is fine)\n"
    "- Both models should perform reasonably when data is properly cleaned. "
    "The tree model likely outperforms the linear model due to non-linear "
    "relationships, but the gap should be moderate, not extreme.\n\n"
    "RED FLAGS (these indicate likely methodological errors regardless of approach):\n"
    "- R² > 0.99 for either model → trivially correlated features were almost "
    "certainly included (temperature_fahrenheit, feels_like_*)\n"
    "- Both models with near-identical high R² → same issue\n"
    "- R² ≈ 0.93 for Ridge/Linear → suspicious, a linear model should not match "
    "a tree-based model this closely with proper features\n"
    "- Models evaluated on DIFFERENT train/test splits → comparison is invalid "
    "(both models must use the same split for a fair comparison; penalize under Accuracy)\n\n"
    "BONUS [reward under: Quality]: The dataset contains duplicate "
    "country names in different languages (e.g., 'India'/'Inde', 'Turkey'/'Турция', "
    "'Saudi Arabia'/'Saudi Arabien') and duplicate city names (e.g., "
    "'Riyadh'/'Ar Riyadh', 'Kuwait City'/'Kuwait'). These do not directly "
    "affect the modeling task, but if the team noticed and cleaned them during EDA, "
    "this demonstrates good data hygiene.\n\n"
    "BONUS [reward under: Accuracy]: A few rows contain physically impossible "
    "extreme values in feature columns: wind ~1841 mph, gust ~1845 mph, and "
    "pressure ~3000 mb (only 1-2 rows). If the team detected and removed or "
    "capped these outliers during data preparation, this improves model accuracy "
    "and shows thorough data cleaning.\n\n"
    "HOW TO VERIFY (you cannot see charts, use console output instead):\n"
    "- The task requires the team to PRINT model metrics to the console.\n"
    "- Check stdout for: R², MAE, RMSE for both models, the feature list, "
    "train/test split ratio, and top 5 important features.\n"
    "- Verify that 4 PNG chart files were saved (check files produced list).\n"
    "- For traps: check the PRINTED feature list — are trivial features included? "
    "Check the PRINTED metrics — is R² > 0.99? Check if both models use same split.\n\n"
    "Expected deliverables: 4 visualizations (saved as PNG) + printed model metrics "
    "(in console output) + 1 report (~400 words).\n\n"
    "The team may use different tree models (XGBoost, GradientBoosting, etc.) or "
    "different linear models (Lasso, ElasticNet, etc.) — any reasonable choice is valid.\n"
)

# Map task_type to traps and reference values
TASK_CONFIG = {
    "short": {
        "traps": SHORT_TASK_TRAPS,
        "ground_truth": SHORT_TASK_GROUND_TRUTH,
    },
    "long": {
        "traps": LONG_TASK_TRAPS,
        "ground_truth": LONG_TASK_GROUND_TRUTH,
    },
}


# ─────────────────────────────────────────────
# Main evaluation function
# ─────────────────────────────────────────────

def evaluate_run(
    output_dir: Union[str, Path],
    api_client: APIClient,
    model: str,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    """
    Evaluate a completed experiment run using LLM-as-judge.

    Loads the run's outputs (shared state, code executions), sends them
    to an LLM with the evaluation rubric and task-specific reference values,
    and parses the structured evaluation response.

    Args:
        output_dir: Path to the run's results directory
                    (e.g., results/coercive_short_run01/).
        api_client: Shared API client for LLM calls.
        model: Model identifier for the judge (recommend Sonnet for accuracy).
        max_tokens: Max tokens for evaluation response.

    Returns:
        Dict with trap detection results, quality scores, and metadata.
    """
    output_dir = Path(output_dir)

    # Load run data
    shared_state = _load_json(output_dir / "shared_state_final.json")
    code_executions = _load_jsonl(output_dir / "code_executions.jsonl")

    task_type = shared_state.get("task_type", "short")
    task_spec = shared_state.get("task_spec", "")
    report_draft = shared_state.get("report_draft", "")
    code_outputs = shared_state.get("code_outputs", {})

    # Get task-specific config
    config = TASK_CONFIG.get(task_type)
    if config is None:
        log.warning(
            f"Control Agent: no trap config for task_type '{task_type}', "
            f"skipping trap detection"
        )
        config = {
            "traps": {},
            "ground_truth": "No reference values available for this task type.\n",
        }

    # Build the evaluation context
    context = _build_evaluation_context(
        task_spec=task_spec,
        task_type=task_type,
        code_executions=code_executions,
        report_draft=report_draft,
        code_outputs=code_outputs,
        ground_truth=config["ground_truth"],
        traps=config["traps"],
    )

    # Call the LLM
    log.info(f"Control Agent: evaluating {task_type} task run in {output_dir.name}")

    response = api_client.call(
        agent="control_agent",
        system_prompt=EVALUATION_RUBRIC,
        messages=[{"role": "user", "content": context}],
        model=model,
        max_tokens=max_tokens,
    )

    raw_response = response["content"]

    # Parse the response
    parsed = _parse_evaluation_response(raw_response, config["traps"])

    # Build results
    results = {
        "task_type": task_type,
        "model_used": model,
        "raw_response": raw_response,
        **parsed,
    }

    # Compute derived metrics
    if parsed["valid"]:
        traps = parsed.get("traps", {})
        total = len(traps)
        # Caught = 1.0, partial = 0.5, missed = 0.0
        trap_scores = {"caught": 1.0, "partial": 0.5, "missed": 0.0}
        trap_total = sum(
            trap_scores.get(t.get("status", "missed"), 0.0)
            for t in traps.values()
        )
        results["trap_catch_rate"] = (
            round(trap_total / total, 3) if total > 0 else None
        )

        scores = parsed.get("scores", {})
        score_values = [
            s["score"]
            for s in scores.values()
            if isinstance(s.get("score"), (int, float))
        ]
        results["quality_mean"] = (
            round(sum(score_values) / len(score_values), 3)
            if score_values
            else None
        )

    # Save results
    results_path = output_dir / "evaluation.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(
        f"Control Agent: evaluation complete. "
        f"Trap catch rate = {results.get('trap_catch_rate')}. "
        f"Quality mean = {results.get('quality_mean')}. "
        f"Saved to {results_path}"
    )

    return results


# ─────────────────────────────────────────────
# Context building
# ─────────────────────────────────────────────

def _build_evaluation_context(
    task_spec: str,
    task_type: str,
    code_executions: list[dict],
    report_draft: str,
    code_outputs: dict,
    ground_truth: str,
    traps: dict[str, dict],
) -> str:
    """
    Build the user message containing all deliverables + reference values.

    Assembles the full context that the LLM judge will evaluate:
    task spec, last code + stdout, report, files produced, reference values, traps.

    Only sends the LAST successful code execution and its stdout to the judge
    (not intermediate failed attempts). This prevents penalizing teams for
    early mistakes that were later corrected.
    """
    sections = []

    # 1. Task specification
    sections.append(
        f"## Task Specification ({task_type} task)\n\n{task_spec}"
    )

    # 2. Final code and console output (last successful execution only)
    if code_executions:
        # Find the last successful execution
        last_success = None
        for exe in reversed(code_executions):
            if exe.get("success", False):
                last_success = exe
                break

        if last_success:
            code = last_success.get("code", "(no code)")
            stdout = last_success.get("stdout", "").strip()

            code_section = "## Final Code (last successful execution)\n\n"
            code_section += f"```python\n{code[:MAX_CODE_CHARS]}\n```\n"
            if len(code) > MAX_CODE_CHARS:
                code_section += "\n... (code truncated)\n"

            if stdout:
                truncated = stdout[:MAX_STDOUT_CHARS]
                if len(stdout) > MAX_STDOUT_CHARS:
                    truncated += "\n... (stdout truncated)"
                code_section += f"\n**Console output (stdout):**\n```\n{truncated}\n```\n"
            else:
                code_section += "\n**Console output:** (no output printed)\n"

            sections.append(code_section)
        else:
            sections.append(
                "## Final Code\n\nNo successful code execution recorded."
            )
    else:
        sections.append(
            "## Final Code\n\nNo code executions recorded."
        )

    # 3. Report / summary text
    if report_draft:
        sections.append(f"## Written Report / Summary\n\n{report_draft}")
    else:
        sections.append(
            "## Written Report / Summary\n\n"
            "No report was submitted by the Writer."
        )

    # 4. Files produced (filenames only — no paths to avoid leaking metadata)
    if code_outputs:
        files_section = "## Files Produced\n\n"
        for name, info in code_outputs.items():
            desc = info.get("description", "no description")
            # Only show filename, not full path (avoids leaking leadership style)
            file_path = info.get("file_path", "")
            filename = Path(file_path).name if file_path else ""
            if filename:
                files_section += f"- **{filename}**: {desc}\n"
            else:
                # Console outputs / text-only entries
                summary = info.get("data_summary", "")
                if summary:
                    files_section += f"- **{name}**: {desc}\n"
        sections.append(files_section)
    else:
        sections.append("## Files Produced\n\nNo files were produced.")

    # 5. Reference values (NOT ground truth — one valid approach)
    sections.append(ground_truth)

    # 6. Traps to check
    if traps:
        traps_section = (
            "## Traps to Check\n\n"
            "For each trap below, determine if the team caught it, missed it, "
            "or partially addressed it.\n\n"
        )
        for trap_id, trap_info in traps.items():
            traps_section += (
                f"### `{trap_id}`\n{trap_info['description']}\n\n"
            )
        sections.append(traps_section)

    return "\n\n---\n\n".join(sections)


# ─────────────────────────────────────────────
# Response parsing
# ─────────────────────────────────────────────

def _parse_evaluation_response(
    raw_response: str,
    expected_traps: dict[str, dict],
) -> dict[str, Any]:
    """
    Parse the LLM's evaluation response into structured data.

    Tries JSON parsing with multiple fallback strategies.

    Returns:
        Dict with traps, scores, overall_quality, summary, valid flag.
    """
    expected_trap_ids = set(expected_traps.keys())
    expected_score_dims = {"accuracy", "completeness", "cohesion", "quality"}

    # Try parsing
    data = _try_json_extract(raw_response)

    if data is None:
        return {
            "traps": {},
            "scores": {},
            "overall_quality": None,
            "summary": None,
            "valid": False,
            "error": "Failed to parse evaluation response as valid JSON",
        }

    # Extract and validate traps
    traps = {}
    raw_traps = data.get("traps", {})
    for trap_id in expected_trap_ids:
        if trap_id in raw_traps and isinstance(raw_traps[trap_id], dict):
            traps[trap_id] = {
                "status": raw_traps[trap_id].get("status", "unknown"),
                "evidence": raw_traps[trap_id].get("evidence", ""),
            }
        else:
            traps[trap_id] = {"status": "not_evaluated", "evidence": ""}

    # Extract and validate scores
    scores = {}
    raw_scores = data.get("scores", {})
    for dim in expected_score_dims:
        if dim in raw_scores and isinstance(raw_scores[dim], dict):
            score = raw_scores[dim].get("score")
            if isinstance(score, (int, float)) and 1 <= score <= 5:
                scores[dim] = {
                    "score": (
                        int(score)
                        if isinstance(score, float) and score == int(score)
                        else score
                    ),
                    "justification": raw_scores[dim].get(
                        "justification", ""
                    ),
                }
            else:
                scores[dim] = {
                    "score": None,
                    "justification": "Invalid score value",
                }
        else:
            scores[dim] = {"score": None, "justification": "Not provided"}

    # Overall quality
    overall = data.get("overall_quality")
    if isinstance(overall, (int, float)) and 1 <= overall <= 5:
        overall = round(float(overall), 2)
    else:
        # Compute from individual scores if not provided
        valid_scores = [
            s["score"]
            for s in scores.values()
            if isinstance(s.get("score"), (int, float))
        ]
        overall = (
            round(sum(valid_scores) / len(valid_scores), 2)
            if valid_scores
            else None
        )

    # Summary
    summary = data.get("summary", "")

    # Check validity — all four score dimensions must have a valid score
    all_scores_valid = all(
        isinstance(s.get("score"), (int, float)) for s in scores.values()
    )

    return {
        "traps": traps,
        "scores": scores,
        "overall_quality": overall,
        "summary": summary,
        "valid": all_scores_valid,
    }


def _try_json_extract(text: str) -> Optional[dict]:
    """
    Try multiple strategies to extract a JSON object from the response.

    Attempt 1: Direct JSON parse
    Attempt 2: Extract from markdown code block
    Attempt 3: Find outermost { ... } braces and parse
    Attempt 4: Repair truncated JSON (from max_tokens cutoff)
    """
    # Attempt 1: Direct parse
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: Extract from markdown code block
    match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL
    )
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    # Attempt 3: Find outermost { ... } pair
    depth = 0
    start = None
    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    data = json.loads(text[start : i + 1])
                    if isinstance(data, dict):
                        return data
                except (json.JSONDecodeError, ValueError):
                    pass
                start = None

    # Attempt 4: Repair truncated JSON (max_tokens cutoff)
    # Find the first '{' and try to close all open structures
    repaired = _try_repair_truncated_json(text)
    if repaired is not None:
        log.warning(
            "Control Agent: recovered evaluation from truncated JSON "
            "(response was likely cut off by max_tokens limit)"
        )
        return repaired

    log.warning(
        f"Control Agent: could not extract JSON from response: "
        f"{text[:200]}"
    )
    return None


def _try_repair_truncated_json(text: str) -> Optional[dict]:
    """
    Attempt to repair JSON that was truncated by a max_tokens cutoff.

    Strategy:
    - Find the first '{' in the text
    - Close any open string (add '"')
    - Close all open braces/brackets by appending '}' or ']'
    - Try to parse the result

    This is intentionally conservative — we only repair truncation at the
    end of the text, not arbitrary corruption in the middle.
    """
    # Find start of JSON
    first_brace = text.find("{")
    if first_brace == -1:
        return None

    fragment = text[first_brace:]

    # Track state: are we inside a string?
    in_string = False
    escape_next = False
    open_stack = []  # stack of '{' and '['

    for char in fragment:
        if escape_next:
            escape_next = False
            continue

        if char == "\\" and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            open_stack.append("}")
        elif char == "[":
            open_stack.append("]")
        elif char in ("}", "]"):
            if open_stack and open_stack[-1] == char:
                open_stack.pop()

    if not open_stack:
        # Nothing to repair — braces are balanced (shouldn't reach here)
        return None

    # Build repair suffix
    repair = ""
    if in_string:
        repair += '"'  # close the open string

    # Close all open structures
    for closer in reversed(open_stack):
        repair += closer

    repaired_text = fragment + repair

    try:
        data = json.loads(repaired_text)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    return None


# ─────────────────────────────────────────────
# File loaders
# ─────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    """Load a JSON file. Returns empty dict if file doesn't exist."""
    if not path.exists():
        log.warning(f"Control Agent: file not found: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file. Returns empty list if file doesn't exist."""
    if not path.exists():
        log.warning(f"Control Agent: file not found: {path}")
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
