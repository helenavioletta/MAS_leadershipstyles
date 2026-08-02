"""
Base Agent: Abstract base class for all agents in the MAS experiment.

Wires together APIClient, MessageBus, and SharedState into a coherent agent loop.
Subclasses (Boss, Coder, Writer, Reviewer) override or extend specific behavior.

Responsibilities:
- Load system prompt from a .md file
- Build context for LLM calls (system prompt + shared state)
- Convert message bus history into Anthropic messages format
- Call the LLM via APIClient
- Post the response to the MessageBus
- Track per-agent token usage (input/output/total)
"""

from pathlib import Path
from typing import Optional

from src.message_bus import MessageBus
from src.shared_state import SharedState
from src.utils.api_client import APIClient


PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt(relative_path: str) -> str:
    """
    Load a prompt from the prompts/ directory.

    Args:
        relative_path: Path relative to prompts/ (e.g., "coder.md" or "boss/1_base_role.md").

    Returns:
        The prompt text content.
    """
    path = PROMPTS_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


class BaseAgent:
    """
    Base class for all MAS agents.

    The orchestrator calls `respond()` when it's this agent's turn.
    The agent reads the message history, builds context, calls the LLM,
    posts the response to the shared channel, and tracks token usage.

    Usage:
        agent = BaseAgent(
            name="Coder",
            system_prompt=load_prompt("coder.md"),
            model=WORKER_MODEL,
            api_client=client,
            message_bus=bus,
            shared_state=state,
        )
        response_text = agent.respond(phase=3)
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str,
        api_client: APIClient,
        message_bus: MessageBus,
        shared_state: SharedState,
        max_tokens: int = 1024,
        effort: Optional[str] = None,
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name ("Boss", "Coder", "Writer", "Reviewer").
            system_prompt: The loaded system prompt text (from prompts/*.md).
            model: Anthropic model identifier for this agent.
            api_client: Shared APIClient instance for making LLM calls.
            message_bus: Shared MessageBus for reading/posting messages.
            shared_state: Shared state object for context injection.
            max_tokens: Max tokens per LLM response (per single call).
            effort: Optional effort level for adaptive thinking ("low", "medium", "high").
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.api_client = api_client
        self.message_bus = message_bus
        self.shared_state = shared_state
        self.max_tokens = max_tokens
        self.effort = effort

        # Per-agent token tracking
        self._input_tokens: int = 0
        self._output_tokens: int = 0
        self._call_count: int = 0

    # ─────────────────────────────────────────────
    # Public interface
    # ─────────────────────────────────────────────

    def respond(self, phase: int, instruction: Optional[str] = None) -> str:
        """
        Generate a response: read context → call LLM → post to bus → return text.

        This is the main method the orchestrator calls when it's this agent's turn.

        Args:
            phase: Current workflow phase (1-7).
            instruction: Optional extra instruction from the orchestrator
                         (e.g., "It's your turn to review the deliverable.").
                         Appended as the last user message.

        Returns:
            The agent's response text (also posted to the message bus).
        """
        system = self._build_system_prompt()
        messages = self._build_messages(phase=phase, instruction=instruction)

        response = self.api_client.call(
            agent=self.name,
            system_prompt=system,
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
            effort=self.effort,
        )

        content = response["content"]
        input_tokens = response["input_tokens"]
        output_tokens = response["output_tokens"]
        nudge_used = response.get("nudge_used")

        # Track tokens
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._call_count += 1

        # If a nudge was needed, flag it in the message bus before the response
        if nudge_used is not None:
            nudge_labels = {
                1: "Nudge level 1: 'Please provide your response to the team.'",
                2: "Nudge level 2: 'Respond now.'",
            }
            self.message_bus.system_notify(
                content=(
                    f"[NUDGE] {self.name} required a nudge to produce text output "
                    f"(adaptive thinking returned no text). "
                    f"{nudge_labels.get(nudge_used, f'Nudge level {nudge_used}')}"
                ),
                phase=phase,
            )

        # Post to message bus
        self.message_bus.send(
            sender=self.name,
            recipient="channel",
            content=content,
            phase=phase,
            token_count=input_tokens + output_tokens,
        )

        return content

    # ─────────────────────────────────────────────
    # Token tracking properties
    # ─────────────────────────────────────────────

    @property
    def total_tokens(self) -> int:
        """Total tokens used by this agent (input + output) across all calls."""
        return self._input_tokens + self._output_tokens

    @property
    def input_tokens(self) -> int:
        """Total input tokens consumed by this agent."""
        return self._input_tokens

    @property
    def output_tokens(self) -> int:
        """Total output tokens produced by this agent."""
        return self._output_tokens

    @property
    def call_count(self) -> int:
        """Number of API calls this agent has made."""
        return self._call_count

    # ─────────────────────────────────────────────
    # Context building (internal)
    # ─────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        """
        Build the full system prompt: static prompt + current shared state.

        The shared state context is appended so the agent always has access to
        the task spec, variable names, code outputs, and current phase —
        preventing context loss (lesson from previous MAS build).
        """
        state_context = self.shared_state.get_context_summary()
        return f"{self.system_prompt}\n\n{state_context}"

    def _build_messages(
        self,
        phase: int,
        instruction: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """
        Convert message bus history into Anthropic messages format.

        The Anthropic API expects alternating user/assistant messages.
        Strategy:
        - Messages from OTHER agents and system → role "user"
        - Messages from THIS agent → role "assistant"
        - If instruction is provided, append it as a final "user" message.
        - Ensure the list starts with "user" and alternates properly.

        Args:
            phase: Current phase (not used for filtering — agents see full history).
            instruction: Optional orchestrator instruction appended at the end.

        Returns:
            List of message dicts for the Anthropic API.
        """
        history = self.message_bus.get_history()
        api_messages: list[dict[str, str]] = []

        for msg in history:
            if msg.sender == self.name:
                role = "assistant"
            else:
                role = "user"
            formatted = f"[{msg.sender}]: {msg.content}"
            api_messages.append({"role": role, "content": formatted})

        # Merge consecutive messages with the same role (Anthropic requires alternation)
        api_messages = self._merge_consecutive_roles(api_messages)

        # Append orchestrator instruction if provided
        if instruction:
            orchestrator_msg = {"role": "user", "content": f"[system]: {instruction}"}
            if api_messages and api_messages[-1]["role"] == "user":
                # Merge with last user message
                api_messages[-1]["content"] += f"\n\n{orchestrator_msg['content']}"
            else:
                api_messages.append(orchestrator_msg)

        # Ensure conversation starts with "user" (Anthropic requirement)
        if api_messages and api_messages[0]["role"] == "assistant":
            api_messages.insert(0, {
                "role": "user",
                "content": "[system]: The conversation has started. You are joining the discussion.",
            })

        # If no messages at all, provide a starter
        if not api_messages:
            starter = instruction or "The team is ready. Please contribute to the discussion."
            api_messages.append({"role": "user", "content": f"[system]: {starter}"})

        return api_messages

    def _merge_consecutive_roles(
        self,
        messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """
        Merge consecutive messages with the same role into one.

        The Anthropic API requires strict user/assistant alternation.
        When multiple agents (all mapped to "user") speak in a row,
        their messages are concatenated with newlines.
        """
        if not messages:
            return []

        merged: list[dict[str, str]] = [messages[0].copy()]

        for msg in messages[1:]:
            if msg["role"] == merged[-1]["role"]:
                merged[-1]["content"] += f"\n\n{msg['content']}"
            else:
                merged.append(msg.copy())

        return merged

    # ─────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} model={self.model!r} calls={self._call_count}>"
