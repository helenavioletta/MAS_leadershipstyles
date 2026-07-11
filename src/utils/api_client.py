"""
API Client: Wrapper around the Anthropic SDK for the MAS experiment.

Handles:
- Loading API key from .env
- Rate limiting and retry with exponential backoff
- Passing max_tokens per call
- Logging every API call to api_calls.jsonl (full audit trail)

The api_calls.jsonl is the researcher-facing audit trail that documents
exactly what each agent saw (system prompt + messages) and produced (response).
This includes the Boss's hidden leadership style prompt.
"""

import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Any

import anthropic
from dotenv import load_dotenv


log = logging.getLogger(__name__)


class APIClient:
    """
    Wrapper around the Anthropic Messages API.

    Responsibilities:
    - Single Anthropic client instance shared across all agents
    - Rate limiting with exponential backoff
    - Write every API call to api_calls.jsonl for full reproducibility
    - Track token usage per call

    Usage:
        client = APIClient(output_dir="results/coercive_short_run01")
        response = client.call(
            agent="Coder",
            system_prompt="You are a data scientist...",
            messages=[{"role": "user", "content": "Load the CSV and print shape."}],
            model="claude-haiku-4-xx",
            max_tokens=1024,
        )
        print(response["content"])       # the LLM's text response
        print(response["input_tokens"])  # tokens used
    """

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        max_retries: int = 3,
        base_retry_delay: float = 2.0,
    ):
        """
        Initialize the API client.

        Args:
            output_dir: Path to the run's results folder for api_calls.jsonl.
                        If None, API call logging is disabled (useful for testing).
            max_retries: Max number of retries on rate limit or server errors.
            base_retry_delay: Base delay in seconds for exponential backoff.
        """
        load_dotenv()
        self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        self._max_retries = max_retries
        self._base_retry_delay = base_retry_delay
        self._seq_counter: int = 0

        # Cumulative token tracking
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_api_calls: int = 0

        # API call log file
        if output_dir is not None:
            self._output_dir = Path(output_dir)
            self._output_dir.mkdir(parents=True, exist_ok=True)
            self._log_path = self._output_dir / "api_calls.jsonl"
        else:
            self._output_dir = None
            self._log_path = None

    def call(
        self,
        agent: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Make a single API call to the Anthropic Messages API.

        Retries on rate limit (429) and server errors (5xx) with exponential backoff.
        Logs the full call (input + output) to api_calls.jsonl.

        Args:
            agent: Which agent is making this call (e.g., "Boss", "Coder").
            system_prompt: The system prompt for this agent (includes leadership style for Boss).
            messages: The conversation messages list [{"role": "user"/"assistant", "content": "..."}].
            model: Anthropic model identifier.
            max_tokens: Maximum tokens for the response.
            temperature: Sampling temperature.

        Returns:
            Dict with keys: content, input_tokens, output_tokens, model, stop_reason
        """
        if "TBD" in model:
            raise ValueError(
                f"Model is still TBD: '{model}'. "
                "Check Anthropic pricing page and set the exact model ID in experiment_config.yaml."
            )

        response = self._call_with_retry(
            system_prompt=system_prompt,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Extract response data
        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        stop_reason = response.stop_reason

        # Update cumulative counters
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_api_calls += 1

        # Log the full call
        self._log_call(
            agent=agent,
            system_prompt=system_prompt,
            messages=messages,
            response_content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_reason=stop_reason,
        )

        return {
            "content": content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
            "stop_reason": stop_reason,
        }

    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output) across all calls."""
        return self.total_input_tokens + self.total_output_tokens

    def _call_with_retry(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> Any:
        """Call the Anthropic API with exponential backoff on retryable errors."""
        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                )
                return response

            except anthropic.RateLimitError as e:
                last_error = e
                delay = self._base_retry_delay * (2 ** attempt)
                log.warning(f"Rate limited (attempt {attempt + 1}/{self._max_retries + 1}). Retrying in {delay}s...")
                time.sleep(delay)

            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    last_error = e
                    delay = self._base_retry_delay * (2 ** attempt)
                    log.warning(f"Server error {e.status_code} (attempt {attempt + 1}/{self._max_retries + 1}). Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise

        raise last_error

    def _log_call(
        self,
        agent: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        response_content: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        temperature: float,
        max_tokens: int,
        stop_reason: str,
    ) -> None:
        """Append the full API call to api_calls.jsonl."""
        if self._log_path is None:
            return

        self._seq_counter += 1
        entry = {
            "seq": self._seq_counter,
            "agent": agent,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt": system_prompt,
            "messages_sent": messages,
            "response": response_content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "stop_reason": stop_reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
