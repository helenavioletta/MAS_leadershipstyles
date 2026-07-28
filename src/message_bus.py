"""
Message Bus: Shared communication channel for the MAS experiment.

All agents communicate via this single broadcast channel (like a team Slack).
Every message is visible to every agent and is persisted to messages.jsonl
for post-experiment analysis (sentiment, turn counts, token usage).

The Boss's leadership style prompt NEVER passes through this bus.
Team members only observe the Boss's behavior here.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Union


@dataclass
class Message:
    """A single message in the shared channel."""
    seq: int
    sender: str          # "Boss", "Coder", "Writer", "Reviewer", or "system"
    recipient: str       # "channel" (broadcast) or a specific agent name
    content: str
    phase: int           # 1-7 workflow phase
    timestamp: str       # ISO format
    token_count: int = 0 # tokens used for the API call that produced this message


class MessageBus:
    """
    Shared broadcast channel for agent communication.
    
    Responsibilities:
    - Store messages in memory for agent context windows
    - Persist every message to messages.jsonl for post-experiment analysis
    - Provide filtered history retrieval (by phase, sender, etc.)
    
    Usage:
        bus = MessageBus(output_dir="results/coercive_short_run01")
        bus.send(sender="Boss", recipient="channel", content="Let's begin.", phase=1, token_count=120)
        history = bus.get_history()
    """

    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the message bus.
        
        Args:
            output_dir: Path to the run's results folder where messages.jsonl will be written.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.output_dir / "messages.jsonl"
        self._messages: list[Message] = []
        self._seq_counter: int = 0

    def send(
        self,
        sender: str,
        recipient: str,
        content: str,
        phase: int,
        token_count: int = 0,
    ) -> Message:
        """
        Send a message to the shared channel.
        
        Every message is broadcast, so all agents can see it.
        The recipient field indicates who it's addressed to, not access control.
        
        Args:
            sender: Agent name or "system" for phase transitions.
            recipient: "channel" for broadcast or specific agent name.
            content: Full message text.
            phase: Current workflow phase (1-7).
            token_count: Tokens used for the API call that produced this message.
            
        Returns:
            The created Message object.
        """
        self._seq_counter += 1
        message = Message(
            seq=self._seq_counter,
            sender=sender,
            recipient=recipient,
            content=content,
            phase=phase,
            timestamp=datetime.now(timezone.utc).isoformat(),
            token_count=token_count,
        )
        self._messages.append(message)
        self._persist(message)
        return message

    def system_notify(self, content: str, phase: int) -> Message:
        """
        Send a system notification (e.g., phase transitions).
        
        Args:
            content: Notification text (e.g., "Phase 3 complete. Coder's outputs are ready.")
            phase: Current workflow phase.
            
        Returns:
            The created Message object.
        """
        return self.send(
            sender="system",
            recipient="channel",
            content=content,
            phase=phase,
            token_count=0,
        )

    def get_history(
        self,
        phase: Optional[int] = None,
        sender: Optional[str] = None,
        exclude_system: bool = False,
        last_n: Optional[int] = None,
    ) -> list[Message]:
        """
        Retrieve message history with optional filters.
        
        Used by the orchestrator to build agent context windows
        and by analysis tools for post-experiment filtering.
        
        Args:
            phase: Filter to a specific phase (1-7). None = all phases.
            sender: Filter to a specific sender. None = all senders.
            exclude_system: If True, exclude system notifications.
            last_n: Return only the last N messages (after filtering).
            
        Returns:
            List of Message objects matching the filters.
        """
        messages = self._messages

        if phase is not None:
            messages = [m for m in messages if m.phase == phase]
        if sender is not None:
            messages = [m for m in messages if m.sender == sender]
        if exclude_system:
            messages = [m for m in messages if m.sender != "system"]
        if last_n is not None:
            messages = messages[-last_n:]

        return messages

    def get_history_as_dicts(self, **kwargs) -> list[dict]:
        """Get history as list of dicts (useful for serialization or prompt building)."""
        return [asdict(m) for m in self.get_history(**kwargs)]

    def get_formatted_history(
        self,
        **kwargs,
    ) -> str:
        """
        Get message history formatted as readable text for agent context windows.
        
        Returns a string like:
            [Phase 1] Boss → channel: Let's begin the task...
            [Phase 1] Coder → channel: I'll start with loading the data...
        """
        messages = self.get_history(**kwargs)
        lines = []
        for m in messages:
            prefix = f"[Phase {m.phase}] {m.sender} → {m.recipient}"
            lines.append(f"{prefix}: {m.content}")
        return "\n".join(lines)

    @property
    def message_count(self) -> int:
        """Total number of messages sent."""
        return len(self._messages)

    @property
    def total_tokens(self) -> int:
        """Sum of all token_count values across messages."""
        return sum(m.token_count for m in self._messages)

    def get_turn_count_by_phase(self) -> dict[int, int]:
        """Count messages per phase (excludes system messages)."""
        counts: dict[int, int] = {}
        for m in self._messages:
            if m.sender != "system":
                counts[m.phase] = counts.get(m.phase, 0) + 1
        return counts

    def get_intervention_count(self, agent: str = "Boss") -> dict[int, int]:
        """Count how many times a specific agent spoke per phase."""
        counts: dict[int, int] = {}
        for m in self._messages:
            if m.sender == agent:
                counts[m.phase] = counts.get(m.phase, 0) + 1
        return counts

    def save_transcript(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save a human-readable Markdown transcript (transcript.md) of the conversation & code executions.

        Args:
            output_path: Target file path. Defaults to output_dir / "transcript.md".

        Returns:
            Path to the saved transcript.md file.
        """
        from src.utils.transcript_generator import generate_transcript
        res = generate_transcript(self.output_dir)
        return res if res else (self.output_dir / "transcript.md")

    def _persist(self, message: Message) -> None:
        """Append a message to messages.jsonl."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(message), ensure_ascii=False) + "\n")
