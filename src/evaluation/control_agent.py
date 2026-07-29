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
            "The team should have detected and removed or flagged this outlier."
        ),
    },
    "country_name_duplicates": {
        "description": (
            "The dataset contains duplicate country names in different languages: "
            "'India'/'Inde', 'Turkey'/'火鸡'/'Турция', 'Belgium'/'Bélgica', "
            "'Estonia'/'Estonie', 'Poland'/'Polônia'/'Польша', 'Saudi Arabia'/'Saudi Arabien', "
            "'Mexico'/'Mexique', 'Morocco'/'Marrocos', 'Malaysia'/'Malásia', "
            "'Latvia'/'Letonia', 'Comoros'/'Komoren', 'Yemen'/'Jemen', "
            "'Turkmenistan'/'Turkménistan', 'USA United States of America'/"
            "'United States of America', 'Guatemala'/'Гватемала', 'Colombia'/'كولومبيا', "
            "'Saint Vincent and the Grenadines'/'Saint-Vincent-et-les-Grenadines'. "
            "If the team aggregated by country (for 'top 10 hottest countries'), they should "
            "have detected and merged these duplicates."
        ),
    },
    "single_observation_cities": {
        "description": (
            "Some cities have very few observations compared to others. "
            "When ranking by single hottest measurement, cities with few data points "
            "may appear disproportionately. The team should have considered observation "
            "count when interpreting rankings, or at least mentioned this caveat."
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
    "- The dataset has 150,465 rows and 268 unique locations across 211 country names.\n"
    "- The 79.3°C reading for Suva (Fiji) is a data error — it should NOT appear in any ranking.\n"
    "- There are ~17 sets of duplicate country names in different languages (e.g., India/Inde).\n"
    "- If duplicates are not merged, country-level aggregations will be incorrect.\n"
    "- Some cities have very few observations; rankings by single max value can be misleading.\n\n"
    "Expected deliverables: exactly 4 bar charts + 1 summary (~200 words).\n\n"
    "The team may handle data issues differently (e.g., filter outliers vs. cap them, "
    "merge duplicates vs. pick one variant) — any reasonable approach is acceptable.\n"
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
    "same_train_test_split": {
        "description": (
            "When comparing two models, both must be evaluated on the exact same "
            "train/test split. If different splits are used, the comparison is invalid. "
            "Check whether the code uses the same random_state or the same split variable "
            "for both models."
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
    "- Sensible feature count: ~17 features (excluding trivial correlations and "
    "duplicate units)\n"
    "- Top features by importance in reference: latitude, uv_index, pressure_mb, "
    "humidity, longitude (team may find different top features depending on their "
    "feature engineering — this is fine)\n\n"
    "RED FLAGS (these indicate likely methodological errors regardless of approach):\n"
    "- R² > 0.99 for either model → trivially correlated features were almost "
    "certainly included (temperature_fahrenheit, feels_like_*)\n"
    "- Both models with near-identical high R² → same issue\n"
    "- R² ≈ 0.93 for Ridge/Linear → suspicious, a linear model should not match "
    "a tree-based model this closely with proper features\n\n"
    "Expected deliverables: exactly 4 visualizations + 1 report (~600 words).\n\n"
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
    max_tokens: int = 4096,
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
        caught = sum(
            1 for t in traps.values() if t.get("status") == "caught"
        )
        total = len(traps)
        results["trap_catch_rate"] = (
            round(caught / total, 3) if total > 0 else None
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
    task spec, code, stdout, report, files, reference values, and traps.
    """
    sections = []

    # 1. Task specification
    sections.append(
        f"## Task Specification ({task_type} task)\n\n{task_spec}"
    )

    # 2. Code executed and outputs
    if code_executions:
        code_section = "## Code Executed by the Team\n\n"
        total_code_chars = 0
        for i, exe in enumerate(code_executions, 1):
            code = exe.get("code", "(no code)")
            stdout = exe.get("stdout", "").strip()
            stderr = exe.get("stderr", "").strip()
            files = exe.get("files_produced", [])
            success = exe.get("success", "?")

            # Truncate if we've exceeded the budget
            if total_code_chars > MAX_CODE_CHARS:
                code_section += (
                    f"\n... (remaining {len(code_executions) - i + 1} "
                    f"executions truncated for brevity)\n"
                )
                break

            code_section += (
                f"### Execution {i} (success={success})\n"
                f"```python\n{code}\n```\n"
            )
            total_code_chars += len(code)

            if stdout:
                truncated = stdout[:MAX_STDOUT_CHARS]
                if len(stdout) > MAX_STDOUT_CHARS:
                    truncated += "\n... (stdout truncated)"
                code_section += f"**stdout:**\n```\n{truncated}\n```\n"

            if stderr and not exe.get("success", True):
                code_section += f"**stderr:**\n```\n{stderr[:2000]}\n```\n"

            if files:
                code_section += f"**Files produced:** {', '.join(files)}\n"

            code_section += "\n"
        sections.append(code_section)
    else:
        sections.append(
            "## Code Executed by the Team\n\nNo code executions recorded."
        )

    # 3. Report / summary text
    if report_draft:
        sections.append(f"## Written Report / Summary\n\n{report_draft}")
    else:
        sections.append(
            "## Written Report / Summary\n\n"
            "No report draft found in shared state."
        )

    # 4. Files produced (from shared state)
    if code_outputs:
        files_section = "## Files Produced (from shared state)\n\n"
        for name, info in code_outputs.items():
            desc = info.get("description", "no description")
            path = info.get("file_path", "text only")
            summary = info.get("data_summary", "")
            files_section += f"- **{name}**: {desc} [{path}]\n"
            if summary:
                files_section += f"  Data: {summary}\n"
        sections.append(files_section)

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
