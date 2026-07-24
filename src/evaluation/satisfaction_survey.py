"""
Satisfaction Survey: Post-experiment evaluation workflow.

Administers a 6-item satisfaction questionnaire to each worker agent
after an experiment run. This is NOT an LLM-based agent — it sends
fixed questions and collects structured responses.

Items adapted from:
- Team Diagnostic Survey (Wageman, Hackman & Lehman, 2005)
- Team Viability & Quality of Group Experience (Aubé & Rousseau, 2005)

See: Masterthesis/Literature/HR-Survey/survey_notes.md for full item
selection rationale, exclusion documentation, and adaptation notes.

Workflow:
    1. For each worker (Coder, Writer, Reviewer):
       a. Build context: worker system prompt + message history + survey prompt
       b. Call the worker's LLM to generate a response (JSON with scores 1-5)
       c. Parse and validate the numeric responses
    2. Reverse-code item 4 (micromanagement)
    3. Compute composite satisfaction score per worker
    4. Save survey_results.json to the run's output directory
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional, Union

from src.agents.base_agent import load_prompt
from src.message_bus import MessageBus
from src.utils.api_client import APIClient


log = logging.getLogger(__name__)

# Survey items — these match prompts/satisfaction_survey.md exactly
SURVEY_ITEMS = {
    "q1": "The team leader helped the team develop a good approach to the task.",
    "q2": "The team leader helped the team identify and use each member's strengths.",
    "q3": "The team leader provided useful feedback during the task.",
    "q4": "The team leader micromanaged the team's work process.",
    "q5": "The collaboration within the team worked well.",
    "q6": "I would work with this team leader again on a future task.",
}

# Item 4 is reverse-coded (higher raw score = more micromanagement = less satisfaction)
REVERSE_CODED_ITEMS = {"q4"}

# Valid score range
MIN_SCORE = 1
MAX_SCORE = 5

# Survey prompt loaded from prompts/satisfaction_survey.md
SURVEY_PROMPT = load_prompt("satisfaction_survey.md")


def administer_survey(
    workers: dict[str, dict[str, Any]],
    message_bus: MessageBus,
    api_client: APIClient,
    output_dir: Union[str, Path],
    model: str,
    max_tokens: int = 256,
) -> dict[str, Any]:
    """
    Administer the satisfaction survey to all worker agents.

    Each worker receives the survey questions in the context of their
    system prompt and the full message history from the experiment run.
    Workers respond with JSON scores that are parsed and scored.

    Args:
        workers: Dict mapping worker name to their config.
                 Each value must have key "system_prompt" (str).
                 Example: {"Coder": {"system_prompt": "..."}, ...}
        message_bus: The message bus from the completed experiment run
                     (provides conversation history as context).
        api_client: Shared API client for making LLM calls.
        output_dir: Path to save survey_results.json.
        model: Anthropic model identifier for worker responses.
        max_tokens: Max tokens for survey response (should be small — just JSON).

    Returns:
        Dict with per-worker scores, composite scores, and metadata.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {
        "workers": {},
        "team_mean": None,
        "items": SURVEY_ITEMS,
        "reverse_coded": list(REVERSE_CODED_ITEMS),
    }

    composite_scores = []

    for worker_name, worker_config in workers.items():
        log.info(f"Satisfaction survey: administering to {worker_name}")

        worker_result = _survey_single_worker(
            worker_name=worker_name,
            worker_system_prompt=worker_config["system_prompt"],
            message_bus=message_bus,
            api_client=api_client,
            model=model,
            max_tokens=max_tokens,
        )

        results["workers"][worker_name] = worker_result

        if worker_result["valid"]:
            composite_scores.append(worker_result["composite_score"])
        else:
            log.warning(f"Satisfaction survey: invalid response from {worker_name}")

    # Team mean (only from valid responses)
    if composite_scores:
        results["team_mean"] = round(sum(composite_scores) / len(composite_scores), 3)

    # Save results
    results_path = output_dir / "survey_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(
        f"Satisfaction survey: complete. "
        f"Team mean = {results['team_mean']}. "
        f"Saved to {results_path}"
    )

    return results


def _survey_single_worker(
    worker_name: str,
    worker_system_prompt: str,
    message_bus: MessageBus,
    api_client: APIClient,
    model: str,
    max_tokens: int,
) -> dict[str, Any]:
    """
    Administer the survey to a single worker and parse the response.

    The worker sees:
    - Its own system prompt (so it stays in character)
    - The full message history from the experiment (so it can reflect)
    - The survey prompt with questions and response format instructions

    Returns:
        Dict with raw_scores, adjusted_scores, composite_score, raw_response, valid flag.
    """
    # Build the system prompt: worker's own prompt + instruction to reflect
    system = (
        f"{worker_system_prompt}\n\n"
        f"--- POST-TASK SURVEY ---\n"
        f"The task is now complete. You are being asked to reflect on your "
        f"experience and answer a satisfaction survey about the task and "
        f"the team leader's behavior during this task."
    )

    # Build messages: conversation history + survey questions
    # The conversation history gives the worker context to reflect on.
    # We format it as a single user message to avoid role-alternation issues.
    history_text = message_bus.get_formatted_history(exclude_system=False)

    messages = [
        {
            "role": "user",
            "content": (
                f"Here is the full conversation from the task you just completed:\n\n"
                f"{history_text}\n\n"
                f"---\n\n"
                f"{SURVEY_PROMPT}"
            ),
        }
    ]

    # Call the LLM
    response = api_client.call(
        agent=f"{worker_name}_survey",
        system_prompt=system,
        messages=messages,
        model=model,
        max_tokens=max_tokens,
    )

    raw_response = response["content"]

    # Parse the response
    raw_scores = _parse_survey_response(raw_response)

    if raw_scores is None:
        return {
            "raw_scores": None,
            "adjusted_scores": None,
            "composite_score": None,
            "raw_response": raw_response,
            "valid": False,
            "error": "Failed to parse survey response as valid JSON with scores 1-5",
        }

    # Validate all scores are in range
    for key, score in raw_scores.items():
        if not (MIN_SCORE <= score <= MAX_SCORE):
            return {
                "raw_scores": raw_scores,
                "adjusted_scores": None,
                "composite_score": None,
                "raw_response": raw_response,
                "valid": False,
                "error": f"Score out of range: {key}={score} (must be {MIN_SCORE}-{MAX_SCORE})",
            }

    # Reverse-code specified items
    adjusted_scores = {}
    for key, score in raw_scores.items():
        if key in REVERSE_CODED_ITEMS:
            adjusted_scores[key] = (MAX_SCORE + MIN_SCORE) - score  # 6 - score for 1-5 scale
        else:
            adjusted_scores[key] = score

    # Composite score = mean of adjusted scores
    composite = round(sum(adjusted_scores.values()) / len(adjusted_scores), 3)

    return {
        "raw_scores": raw_scores,
        "adjusted_scores": adjusted_scores,
        "composite_score": composite,
        "raw_response": raw_response,
        "valid": True,
    }


def _parse_survey_response(raw_response: str) -> Optional[dict[str, int]]:
    """
    Parse the worker's survey response into a dict of scores.

    Tries JSON parsing first, then falls back to regex extraction.

    Args:
        raw_response: The raw LLM response text.

    Returns:
        Dict like {"q1": 4, "q2": 3, ...} or None if parsing fails.
    """
    expected_keys = set(SURVEY_ITEMS.keys())

    # Attempt 1: Direct JSON parse
    scores = _try_json_parse(raw_response, expected_keys)
    if scores is not None:
        return scores

    # Attempt 2: Extract JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
    if json_match:
        scores = _try_json_parse(json_match.group(1), expected_keys)
        if scores is not None:
            return scores

    # Attempt 3: Find any JSON-like object in the response
    brace_match = re.search(r"\{[^{}]*\}", raw_response)
    if brace_match:
        scores = _try_json_parse(brace_match.group(0), expected_keys)
        if scores is not None:
            return scores

    # Attempt 4: Regex fallback — look for "q1": 4 or q1: 4 patterns
    scores = {}
    for key in expected_keys:
        pattern = rf'["\']?{key}["\']?\s*:\s*(\d+)'
        match = re.search(pattern, raw_response, re.IGNORECASE)
        if match:
            scores[key] = int(match.group(1))

    if scores.keys() == expected_keys:
        return scores

    log.warning(f"Satisfaction survey: could not parse response: {raw_response[:200]}")
    return None


def _try_json_parse(text: str, expected_keys: set[str]) -> Optional[dict[str, int]]:
    """
    Try to parse text as JSON and validate it has the expected keys with int values.

    Returns:
        Validated scores dict or None.
    """
    try:
        data = json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    # Check all expected keys are present
    if not expected_keys.issubset(data.keys()):
        return None

    # Extract and validate scores
    scores = {}
    for key in expected_keys:
        value = data[key]
        if isinstance(value, int):
            scores[key] = value
        elif isinstance(value, float) and value == int(value):
            scores[key] = int(value)
        else:
            return None

    return scores
