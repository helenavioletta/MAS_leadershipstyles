"""
Writer Agent: Writes narrative text, reports, and summaries based on Coder's outputs.

Reads actual data and charts from shared state. Never invents findings.
After responding, automatically saves the text to shared_state.set_report_draft()
so the Reviewer can access the latest version.
"""

import re
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
        response = writer.respond(phase=4, instruction="Write a 100-word summary.")
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

        self._last_report: Optional[str] = None  # Previous report for revision context

    def respond(self, phase: int, instruction: Optional[str] = None) -> str:
        """
        Generate narrative text and save it as the report draft.

        Calls the base respond() (LLM call + post to bus), then saves
        the output to shared state so Reviewer can access the latest draft.
        Injects previous report if available (for revisions).

        Args:
            phase: Current workflow phase (1-7).
            instruction: Optional instruction from orchestrator.

        Returns:
            The generated text (also posted to bus and saved as report draft).
        """
        # Inject previous report for revision context
        if instruction and self._last_report:
            instruction = (
                f"{instruction}\n\n"
                f"[system]: Here is your previous report from the last round. "
                f"Revise it based on the feedback you received.\n\n"
                f"---REPORT START---\n{self._last_report}\n---REPORT END---"
            )
        elif instruction and not self._last_report:
            instruction = (
                f"{instruction}\n\n"
                f"[system]: WARNING — No report was saved from your previous round "
                f"because you did not wrap it in the required markers. "
                f"You MUST wrap your report between ---REPORT START--- and "
                f"---REPORT END--- markers for it to be saved."
            )

        content = super().respond(phase=phase, instruction=instruction)

        # Extract report from markers
        report_text = self._extract_report(content)

        if report_text:
            # Save to shared state so Reviewer can access the latest draft
            self.shared_state.set_report_draft(report_text)
            self._last_report = report_text

        return content

    @staticmethod
    def _extract_report(content: str) -> Optional[str]:
        """
        Extract report text from between ---REPORT START--- and ---REPORT END--- markers.

        Returns None if markers are not found (report was not properly wrapped).
        """
        pattern = r"---REPORT START---\s*\n?(.*?)\n?\s*---REPORT END---"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None