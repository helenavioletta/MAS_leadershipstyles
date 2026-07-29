"""
Transcript Generator: Converts experiment logs into a human-readable transcript.md.

Merges messages.jsonl and code_executions.jsonl into a unified chronological timeline
with KPI dashboard, run configuration, per-phase statistics, and inline code executions.

Can be run standalone:
    python src/utils/transcript_generator.py results/coercive_test_run01
    python src/utils/transcript_generator.py --all
"""

import json
import re
import sys
from datetime import datetime
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

PHASE_NAMES = {
    1: "BRIEFING",
    2: "PLANNING",
    3: "CODING",
    4: "WRITING",
    5: "REVIEW",
    6: "REVISION",
    7: "DELIVERY",
}


# ── Helper Functions ──────────────────────────────────────────────────────────


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse ISO timestamp string into datetime object."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def _format_relative_time(dt: Optional[datetime], start: Optional[datetime]) -> str:
    """Format datetime as relative time from start (e.g., '+1:23')."""
    if dt is None or start is None:
        return ""
    delta = dt - start
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    minutes, seconds = divmod(total_seconds, 60)
    return f"+{minutes}:{seconds:02d}"


def _demote_headings(content: str) -> str:
    """Demote markdown headings in message content by 3 levels.

    Skips headings inside fenced code blocks to avoid mangling code.
    """
    result = []
    in_code_block = False

    for line in content.split("\n"):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        if not in_code_block:
            heading_match = re.match(r"^(#{1,6})\s", line)
            if heading_match:
                old_level = len(heading_match.group(1))
                new_level = min(old_level + 3, 6)
                line = "#" * new_level + line[old_level:]

        result.append(line)

    return "\n".join(result)


def _strip_agent_labels(content: str) -> str:
    """Strip redundant agent self-labels like '[Coder]:' from message start."""
    return re.sub(r"^\[(?:Coder|Writer|Reviewer|Boss)\]:\s*", "", content.strip())


def _is_phase_transition(msg: dict) -> bool:
    """Check if a message is a system phase transition notification."""
    if msg.get("sender") != "system":
        return False
    content = msg.get("content", "")
    return bool(re.match(r"^---\s*Phase\s+\d+", content))


def _determine_phase(timestamp: Optional[datetime], messages: list) -> int:
    """Determine which phase a timestamp falls into based on surrounding messages."""
    if timestamp is None:
        return 0
    phase = 0
    for msg in messages:
        msg_ts = _parse_timestamp(msg.get("timestamp", ""))
        if msg_ts and msg_ts <= timestamp:
            phase = msg.get("phase", phase)
        elif msg_ts and msg_ts > timestamp:
            break
    return phase


# ── Data Loading & Stats ─────────────────────────────────────────────────────


def _load_jsonl(path: Path) -> list:
    """Load a JSONL file into a list of dicts. Returns empty list if missing."""
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def _load_json(path: Path) -> dict:
    """Load a JSON file into a dict. Returns empty dict if missing."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _count_agent_messages(messages: list) -> dict:
    """Count messages per agent, excluding system messages."""
    counts = {}
    for msg in messages:
        sender = msg.get("sender", "Unknown")
        if sender != "system":
            counts[sender] = counts.get(sender, 0) + 1
    return counts


def _compute_phase_stats(phases_dict: dict) -> dict:
    """Compute per-phase statistics (message count, agents, exec stats, time span)."""
    stats = {}
    for p, entries in phases_dict.items():
        msg_entries = [e for e in entries if e["type"] == "message"]
        exec_entries = [e for e in entries if e["type"] == "code_execution"]

        agent_names = [
            e["data"].get("sender", "Unknown")
            for e in msg_entries
            if e["data"].get("sender") != "system"
        ]

        exec_success = sum(
            1 for e in exec_entries if e["data"].get("success", False)
        )

        timestamps = [e["timestamp"] for e in entries if e["timestamp"]]

        stats[p] = {
            "message_count": len(agent_names),
            "agent_names": agent_names,
            "exec_count": len(exec_entries),
            "exec_success": exec_success,
            "exec_failed": len(exec_entries) - exec_success,
            "time_start": min(timestamps) if timestamps else None,
            "time_end": max(timestamps) if timestamps else None,
        }

    return stats


# ── Render Helpers ────────────────────────────────────────────────────────────


def _render_message(lines: list, entry: dict, start_time: Optional[datetime]) -> None:
    """Render a single agent or system message into the output lines."""
    msg = entry["data"]
    sender = msg.get("sender", "Unknown")
    recipient = msg.get("recipient", "channel")
    seq = msg.get("seq", 0)
    content = msg.get("content", "")
    ts = entry["timestamp"]
    rel_time = _format_relative_time(ts, start_time)

    # System messages (non-phase-transition): compact italic line
    if sender == "system":
        time_suffix = f" — {rel_time}" if rel_time else ""
        lines.append(f"*⚙️ {content}*{time_suffix}")
        lines.append("")
        return

    # Agent message header
    icon = AGENT_ICONS.get(sender, "💬")
    recipient_str = f" → {recipient}" if recipient != "channel" else ""
    lines.append(f"## {icon} {sender}{recipient_str}")
    lines.append(f"*{rel_time} | Seq #{seq}*")
    lines.append("")

    # Process content
    content = _strip_agent_labels(content)
    content = _demote_headings(content)

    # Collapse very long messages (>40 lines)
    content_lines = content.split("\n")
    if len(content_lines) > 40:
        preview = "\n".join(content_lines[:10])
        remaining = "\n".join(content_lines[10:])
        remaining_count = len(content_lines) - 10
        lines.append(preview)
        lines.append("")
        lines.append(
            f"<details><summary>Show remaining {remaining_count} lines</summary>"
        )
        lines.append("")
        lines.append(remaining)
        lines.append("")
        lines.append("</details>")
    else:
        lines.append(content)

    lines.append("")


def _render_code_execution(
    lines: list,
    entry: dict,
    start_time: Optional[datetime],
    run_dir: Path,
) -> None:
    """Render a code execution entry inline in the conversation timeline."""
    exec_item = entry["data"]
    seq = exec_item.get("seq", 1)
    success = exec_item.get("success", False)
    exit_code = exec_item.get("exit_code", 0)
    duration = exec_item.get("duration_seconds", 0.0)
    code = exec_item.get("code", "")
    stdout = exec_item.get("stdout", "")
    stderr = exec_item.get("stderr", "")
    files = exec_item.get("files_produced", []) or []
    ts = entry["timestamp"]
    rel_time = _format_relative_time(ts, start_time)

    # Status line (blockquote for visual distinction)
    if success:
        status_str = "✅ SUCCESS"
    else:
        error_match = re.search(r"(\w+Error):", stderr) if stderr else None
        error_type = (
            error_match.group(1) if error_match else f"Exit Code {exit_code}"
        )
        status_str = f"❌ FAILED ({error_type})"

    lines.append(
        f"> 💻 **Code Execution #{seq}** — {status_str} | {rel_time} | {duration:.2f}s"
    )
    lines.append("")

    # Code block — collapse if >15 lines
    code_text = code.strip()
    code_line_list = code_text.split("\n") if code_text else []
    if len(code_line_list) > 15:
        lines.append(
            f"<details><summary>Submitted code ({len(code_line_list)} lines)</summary>"
        )
        lines.append("")
        lines.append("```python")
        lines.append(code_text)
        lines.append("```")
        lines.append("")
        lines.append("</details>")
    elif code_line_list:
        lines.append("```python")
        lines.append(code_text)
        lines.append("```")
    lines.append("")

    # stdout — collapse if >15 lines
    if stdout.strip():
        stdout_text = stdout.strip()
        stdout_line_list = stdout_text.split("\n")
        if len(stdout_line_list) > 15:
            lines.append(
                f"<details><summary>Console output ({len(stdout_line_list)} lines)</summary>"
            )
            lines.append("")
            lines.append("```")
            lines.append(stdout_text)
            lines.append("```")
            lines.append("")
            lines.append("</details>")
        else:
            lines.append("**Output:**")
            lines.append("```")
            lines.append(stdout_text)
            lines.append("```")
        lines.append("")

    # stderr — always show the key error line
    if stderr.strip():
        stderr_line_list = stderr.strip().split("\n")
        error_line = stderr_line_list[-1] if stderr_line_list else stderr.strip()
        lines.append(f"**Error:** `{error_line}`")
        lines.append("")

    # Files produced — verify against filesystem and link
    if files:
        for f_name in files:
            file_path = run_dir / "outputs" / f_name
            if file_path.exists():
                lines.append(
                    f"📁 **File saved:** [{f_name}](file://{file_path})"
                )
            else:
                # Try as absolute path (sandbox may store full paths)
                abs_path = Path(f_name)
                if abs_path.is_absolute() and abs_path.exists():
                    lines.append(
                        f"📁 **File saved:** [{abs_path.name}](file://{abs_path})"
                    )
                else:
                    lines.append(
                        f"⚠️ **File claimed but not found:** `{f_name}`"
                    )
        lines.append("")


# ── Section Writers ───────────────────────────────────────────────────────────


def _write_kpi_dashboard(
    lines: list,
    metadata: dict,
    agent_msg_counts: dict,
    non_system_count: int,
    total_execs: int,
    exec_ok: int,
    exec_fail: int,
) -> None:
    """Write the KPI summary dashboard table."""
    lines.append("## Run Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

    style = metadata.get("leadership_style", "unknown")
    task_type = metadata.get("task_type", "unknown")
    duration = metadata.get("duration_seconds", 0)
    total_tokens = metadata.get("total_tokens", 0)
    input_tokens = metadata.get("total_input_tokens", 0)
    output_tokens = metadata.get("total_output_tokens", 0)
    revision_rounds = metadata.get("revision_rounds", 0)

    lines.append(f"| **Leadership Style** | {style.title()} |")
    lines.append(f"| **Task Type** | {task_type.title()} |")
    lines.append(f"| **Duration** | {duration:.1f}s |")
    lines.append(
        f"| **Total Tokens** | {total_tokens:,} "
        f"(in: {input_tokens:,} / out: {output_tokens:,}) |"
    )
    lines.append(f"| **Messages** | {non_system_count} (excl. system) |")

    agent_parts = [f"{a}: {c}" for a, c in agent_msg_counts.items()]
    lines.append(f"| **Messages by Agent** | {', '.join(agent_parts)} |")

    lines.append(
        f"| **Code Executions** | {total_execs} total "
        f"({exec_ok} ✅, {exec_fail} ❌) |"
    )
    lines.append(f"| **Revision Rounds** | {revision_rounds} |")

    # Time window
    start_str = metadata.get("start_time", "")
    end_str = metadata.get("end_time", "")
    if start_str and end_str:
        start_dt = _parse_timestamp(start_str)
        end_dt = _parse_timestamp(end_str)
        if start_dt and end_dt:
            lines.append(
                f"| **Time Window** | "
                f"{start_dt.strftime('%H:%M:%S')} → {end_dt.strftime('%H:%M:%S')} |"
            )

    # Per-agent token breakdown
    token_by_agent = metadata.get("token_usage_by_agent", {})
    if token_by_agent:
        lines.append("| | |")
        lines.append("| **Token Breakdown** | |")
        for agent, usage in token_by_agent.items():
            t = usage.get("total_tokens", 0)
            calls = usage.get("call_count", 0)
            icon = AGENT_ICONS.get(agent, "💬")
            lines.append(
                f"| ↳ {icon} {agent} | {t:,} tokens / {calls} API calls |"
            )

    lines.append("")


def _write_run_configuration(lines: list, metadata: dict) -> None:
    """Write the run configuration section with task prompt and system prompts."""
    lines.append("## Run Configuration")
    lines.append("")

    # Task prompt
    task_wording = metadata.get("task_wording", "")
    if task_wording:
        lines.append("### Task Prompt")
        lines.append("")
        for tl in task_wording.split("\n"):
            lines.append(f"> {tl}")
        lines.append("")

    # Models and experiment config
    boss_model = metadata.get("boss_model", "unknown")
    worker_model = metadata.get("worker_model", "unknown")
    max_rev = metadata.get("max_revision_rounds", "N/A")
    lines.append(
        f"**Boss Model:** `{boss_model}` | **Worker Model:** `{worker_model}` "
        f"| **Max Revision Rounds:** {max_rev}"
    )
    lines.append("")

    # Boss system prompt (collapsible — can be long)
    boss_prompt = metadata.get("boss_system_prompt", "")
    if boss_prompt:
        lines.append(
            "<details><summary><strong>Boss System Prompt</strong> "
            "(click to expand)</summary>"
        )
        lines.append("")
        lines.append("```")
        lines.append(boss_prompt)
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # Worker prompts (collapsible — tracked per run)
    worker_prompts = metadata.get("worker_prompts", {})
    if worker_prompts:
        for agent_name in ("Coder", "Writer", "Reviewer"):
            prompt_text = worker_prompts.get(agent_name, "")
            if prompt_text:
                icon = AGENT_ICONS.get(agent_name, "💬")
                lines.append(
                    f"<details><summary><strong>{icon} {agent_name} System Prompt</strong> "
                    f"(click to expand)</summary>"
                )
                lines.append("")
                lines.append("```")
                lines.append(prompt_text)
                lines.append("```")
                lines.append("")
                lines.append("</details>")
                lines.append("")
    else:
        # Fallback: link to prompt files if not stored in metadata
        prompts_dir = PROJECT_ROOT / "prompts"
        lines.append(
            f"**Worker Prompts (fixed):** "
            f"[coder.md](file://{prompts_dir / 'coder.md'}) | "
            f"[writer.md](file://{prompts_dir / 'writer.md'}) | "
            f"[reviewer.md](file://{prompts_dir / 'reviewer.md'})"
        )
        lines.append("")


def _write_toc(lines: list, phases_dict: dict, phase_stats: dict) -> None:
    """Write the table of contents with per-phase summaries."""
    lines.append("## Table of Contents")
    lines.append("")

    for p in sorted(phases_dict.keys()):
        phase_name = PHASE_NAMES.get(p, "UNKNOWN")
        stats = phase_stats[p]
        agents_str = (
            ", ".join(stats["agent_names"]) if stats["agent_names"] else "system only"
        )
        parts = [f"{stats['message_count']} messages ({agents_str})"]
        if stats["exec_count"] > 0:
            parts.append(f"{stats['exec_count']} code executions")
        anchor = f"phase-{p}-{phase_name.lower()}"
        lines.append(
            f"- [Phase {p}: {phase_name}](#{anchor}) — {' | '.join(parts)}"
        )

    lines.append("")


# ── Main Generation ──────────────────────────────────────────────────────────


def generate_transcript(run_dir: Union[str, Path]) -> Optional[Path]:
    """
    Read messages.jsonl, code_executions.jsonl, and metadata.json from run_dir
    and write a human-readable transcript.md.

    Produces a unified chronological timeline merging agent messages and code
    executions, with a KPI dashboard, run configuration, and per-phase stats.

    Args:
        run_dir: Path to run results folder.

    Returns:
        Path to generated transcript.md or None if messages.jsonl missing.
    """
    run_dir = Path(run_dir)
    messages_path = run_dir / "messages.jsonl"

    if not messages_path.exists():
        print(f"Skipping {run_dir.name}: messages.jsonl not found.")
        return None

    # ── Load data ─────────────────────────────────────────────────
    messages = _load_jsonl(messages_path)
    code_executions = _load_jsonl(run_dir / "code_executions.jsonl")
    metadata = _load_json(run_dir / "metadata.json")

    # ── Determine start time (first message timestamp) ────────────
    start_time = None
    for msg in messages:
        ts = _parse_timestamp(msg.get("timestamp", ""))
        if ts:
            start_time = ts
            break

    # ── Build unified timeline ────────────────────────────────────
    # Merge messages and code executions into one list sorted by timestamp.
    # Phase transition system messages are excluded (absorbed into headers).
    timeline = []

    for msg in messages:
        if _is_phase_transition(msg):
            continue
        ts = _parse_timestamp(msg.get("timestamp", ""))
        timeline.append({
            "type": "message",
            "timestamp": ts,
            "phase": msg.get("phase", 0),
            "data": msg,
        })

    for exec_item in code_executions:
        ts = _parse_timestamp(exec_item.get("timestamp", ""))
        phase = _determine_phase(ts, messages)
        timeline.append({
            "type": "code_execution",
            "timestamp": ts,
            "phase": phase,
            "data": exec_item,
        })

    timeline.sort(key=lambda x: x["timestamp"] or datetime.min)

    # ── Group by phase ────────────────────────────────────────────
    phases_dict = {}
    for entry in timeline:
        p = entry["phase"]
        if p not in phases_dict:
            phases_dict[p] = []
        phases_dict[p].append(entry)

    # ── Compute stats ─────────────────────────────────────────────
    phase_stats = _compute_phase_stats(phases_dict)
    agent_msg_counts = _count_agent_messages(messages)
    non_system_count = sum(agent_msg_counts.values())
    exec_ok = sum(1 for e in code_executions if e.get("success", False))
    exec_fail = len(code_executions) - exec_ok

    # ── Build output ──────────────────────────────────────────────
    out = []

    # Title
    out.append(f"# Transcript — {run_dir.name}")
    out.append("")

    # KPI Dashboard
    _write_kpi_dashboard(
        out, metadata, agent_msg_counts, non_system_count,
        len(code_executions), exec_ok, exec_fail,
    )

    # Run Configuration
    _write_run_configuration(out, metadata)

    # Table of Contents
    _write_toc(out, phases_dict, phase_stats)

    # Conversation — phase by phase
    out.append("---")
    out.append("")

    for p in sorted(phases_dict.keys()):
        phase_name = PHASE_NAMES.get(p, "UNKNOWN")
        stats = phase_stats[p]

        # Phase header (top-level heading — biggest, most visible)
        out.append(f"# Phase {p}: {phase_name}")
        out.append("")

        # Per-phase stats line
        stat_parts = []
        if stats["agent_names"]:
            stat_parts.append(
                f"**Messages:** {stats['message_count']} "
                f"({', '.join(stats['agent_names'])})"
            )
        if stats["exec_count"] > 0:
            stat_parts.append(
                f"**Code Executions:** {stats['exec_count']} "
                f"({stats['exec_success']} ✅, {stats['exec_failed']} ❌)"
            )
        if stats["time_start"] and stats["time_end"] and start_time:
            t0 = _format_relative_time(stats["time_start"], start_time)
            t1 = _format_relative_time(stats["time_end"], start_time)
            stat_parts.append(f"**Time:** {t0} – {t1}")

        if stat_parts:
            out.append(f"*{' | '.join(stat_parts)}*")
            out.append("")

        out.append("---")
        out.append("")

        # Render all entries in chronological order
        for entry in phases_dict[p]:
            if entry["type"] == "message":
                _render_message(out, entry, start_time)
            elif entry["type"] == "code_execution":
                _render_code_execution(out, entry, start_time, run_dir)

    # ── Write file ────────────────────────────────────────────────
    transcript_path = run_dir / "transcript.md"
    transcript_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Generated: {transcript_path}")
    return transcript_path


# ── CLI Entry Points ─────────────────────────────────────────────────────────


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
