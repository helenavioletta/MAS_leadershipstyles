"""
Writer Agent: Writes narrative text, reports, and summaries based on Coder's outputs.

Reads actual data and charts from shared state. Never invents findings.
After responding, automatically saves the text to shared_state.set_report_draft()
so the Reviewer can access the latest version.
"""

from typing import Optional

from src.agents.base_agent import BaseAgent, load_prompt
from src.message_bus import MessageBus
from src.shared_state import SharedState
from src.utils.api_client import APIClient


class WriterAgent(BaseAgent):
    """
    Writer agent that produces narrative text grounded in real data.

    Overrides respond() to save the generated text as the report draft
    in shared state after posting to the bus.

    Usage:
        writer = WriterAgent(
            model=WORKER_MODEL,
            api_client=client,
            message_bus=bus,
            shared_state=state,
        )
        response = writer.respond(phase=4, instruction="Write a 200-word summary.")
    """

    def __init__(
        self,
        model: str,
        api_client: APIClient,
        message_bus: MessageBus,
        shared_state: SharedState,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Writer agent.

        Args:
            model: Anthropic model identifier (Haiku for workers).
            api_client: Shared APIClient instance.
            message_bus: Shared MessageBus.
            shared_state: Shared state object.
            max_tokens: Max tokens per LLM response.
        """
        system_prompt = load_prompt("writer.md")

        super().__init__(
            name="Writer",
            system_prompt=system_prompt,
            model=model,
            api_client=api_client,
            message_bus=message_bus,
            shared_state=shared_state,
            max_tokens=max_tokens,
        )

    def respond(self, phase: int, instruction: Optional[str] = None) -> str:
        """
        Generate narrative text and save it as the report draft.

        Calls the base respond() (LLM call + post to bus), then saves
        the output to shared state so Reviewer can access the latest draft.

        Args:
            phase: Current workflow phase (1-7).
            instruction: Optional instruction from orchestrator.

        Returns:
            The generated text (also posted to bus and saved as report draft).
        """
        content = super().respond(phase=phase, instruction=instruction)

        # Save to shared state so Reviewer can access the latest draft
        self.shared_state.set_report_draft(content)

        return content