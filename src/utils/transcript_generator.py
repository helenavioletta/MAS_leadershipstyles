"""
Transcript Generator: Converts messages.jsonl into a human-readable transcript.md file.

Can be run standalone:
    python src/utils/transcript_generator.py results/affiliative_test_run01
    python src/utils/transcript_generator.py --all
"""

import json
import sys
from pathlib import Path
from typing import Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

AGENT_ICONS = {
    "Boss": "👑",
    "Coder": "💻",
    "Writer": "✍️",
    "Reviewer": "🧐",
    "system": "⚙️",
}


def generate_transcript(run_dir: Union[str, Path]) -> Optional[Path]:
    """
    Read messages.jsonl from run_dir and write transcript.md.

    Args:
        run_dir: Path to run results folder containing messages.jsonl.

    Returns:
        Path to generated transcript.md or None if messages.jsonl missing.
    """
    run_dir = Path(run_dir)
    messages_path = run_dir / "messages.jsonl"

    if not messages_path.exists():
        print(f"Skipping {run_dir.name}: messages.jsonl not found.")
        return None

    messages = []
    with open(messages_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))

    lines = [
        f"# Conversation Transcript — {run_dir.name}\n",
        f"**Total Messages**: {len(messages)} | **Log File**: `messages.jsonl`\n",
        "---\n",
    ]

    current_phase = None

    for msg in messages:
        phase = msg.get("phase", 0)
        sender = msg.get("sender", "Unknown")
        recipient = msg.get("recipient", "channel")
        seq = msg.get("seq", 0)
        timestamp = msg.get("timestamp", "")
        content = msg.get("content", "")

        if phase != current_phase:
            current_phase = phase
            lines.append(f"\n## Phase {current_phase}\n")

        icon = AGENT_ICONS.get(sender, "💬")
        recipient_str = f" → {recipient}" if recipient != "channel" else ""

        lines.append(f"### {icon} {sender}{recipient_str}")
        lines.append(f"*Phase {phase} | Sequence #{seq} | {timestamp}*\n")
        lines.append(f"{content}\n")
        lines.append("---\n")

    transcript_path = run_dir / "transcript.md"
    transcript_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated: {transcript_path}")
    return transcript_path


def generate_all():
    """Generate transcript.md for all run directories in results/."""
    if not RESULTS_DIR.exists():
        print("No results directory found.")
        return

    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if run_dir.is_dir() and not run_dir.name.startswith("."):
            generate_transcript(run_dir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--all":
            generate_all()
        else:
            generate_transcript(arg)
    else:
        generate_all()
