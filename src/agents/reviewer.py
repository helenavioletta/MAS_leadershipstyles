"""
Reviewer Agent: Quality gate for the team's deliverables.

Reviews Coder's outputs (do they make sense?) and Writer's text (does it capture
what's important?). Does NOT check if code runs — that's the Coder's job.
The Reviewer thinks like a senior data scientist: is this analysis sound?
Does the narrative match the data?

All review intelligence comes from the system prompt (prompts/reviewer.md).
No custom Python logic needed — standard BaseAgent.respond() is sufficient.
"""

from src.agents.base_agent import BaseAgent, load_prompt
from src.message_bus import MessageBus
from src.shared_state import SharedState
from src.utils.api_client import APIClient


class ReviewerAgent(BaseAgent):
    """
    Reviewer agent that acts as quality gate on outputs and text.

    Uses the standard BaseAgent.respond() — the review logic is entirely
    driven by the system prompt. The orchestrator decides when to call
    the Reviewer (Phase 5) and what to do with the feedback (Phase 6).

    Usage:
        reviewer = ReviewerAgent(
            model=WORKER_MODEL,
            api_client=client,
            message_bus=bus,
            shared_state=state,
        )
        feedback = reviewer.respond(phase=5, instruction="Review the deliverable.")
    """

    def __init__(
        self,
        model: str,
        api_client: APIClient,
        message_bus: MessageBus,
        shared_state: SharedState,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        """
        Initialize the Reviewer agent.

        Args:
            model: Anthropic model identifier (Haiku for workers).
            api_client: Shared APIClient instance.
            message_bus: Shared MessageBus.
            shared_state: Shared state object.
            max_tokens: Max tokens per LLM response.
            temperature: Sampling temperature.
        """
        system_prompt = load_prompt("reviewer.md")

        super().__init__(
            name="Reviewer",
            system_prompt=system_prompt,
            model=model,
            api_client=api_client,
            message_bus=message_bus,
            shared_state=shared_state,
            max_tokens=max_tokens,
            temperature=temperature,
        )