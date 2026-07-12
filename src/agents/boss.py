"""
Boss Agent: Team lead with variable leadership style.

The Boss uses Claude Sonnet (smarter model) and loads two prompt components:
1. Base role (shared across all styles) — defines the team lead responsibilities
2. Style overlay (varies per experiment) — defines the leadership personality

The Boss's leadership style prompt is NEVER visible to workers in the message bus.
It only appears in api_calls.jsonl and metadata.json (researcher-facing audit trail).
"""

from src.agents.base_agent import BaseAgent, load_prompt
from src.message_bus import MessageBus
from src.shared_state import SharedState
from src.utils.api_client import APIClient


class BossAgent(BaseAgent):
    """
    Boss agent with configurable leadership style.

    The system prompt is constructed from:
        prompts/boss/1_base_role.md + prompts/boss/{style}.md

    Usage:
        boss = BossAgent(
            style="3_coercive",
            model=BOSS_MODEL,
            api_client=client,
            message_bus=bus,
            shared_state=state,
        )
        response = boss.respond(phase=1, instruction="Assign the task to your team.")
    """

    def __init__(
        self,
        style: str,
        model: str,
        api_client: APIClient,
        message_bus: MessageBus,
        shared_state: SharedState,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        """
        Initialize the Boss agent.

        Args:
            style: Style prompt filename (e.g., "3_coercive", "4_authoritative").
                   Loaded from prompts/boss/{style}.md.
            model: Anthropic model identifier (should be Sonnet for the Boss).
            api_client: Shared APIClient instance.
            message_bus: Shared MessageBus.
            shared_state: Shared state object.
            max_tokens: Max tokens per response.
            temperature: Sampling temperature.
        """
        base_role = load_prompt("boss/1_base_role.md")
        style_prompt = load_prompt(f"boss/{style}.md")
        system_prompt = f"{base_role}\n\n{style_prompt}"

        self.style = style

        super().__init__(
            name="Boss",
            system_prompt=system_prompt,
            model=model,
            api_client=api_client,
            message_bus=message_bus,
            shared_state=shared_state,
            max_tokens=max_tokens,
            temperature=temperature,
        )
