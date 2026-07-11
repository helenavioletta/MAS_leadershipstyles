"""
Shared State: Central state object accessible to all agents during an experiment run.

Prevents context loss and hallucinated data.
All agents read from and write to this object so that:
- Coder's variable names and outputs are never lost
- Writer reads real data, not hallucinated results
- Reviewer can cross-check code outputs against report claims

Serialized to shared_state_final.json at the end of each run.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Any


class SharedState:
    """
    Central state object for a single experiment run.

    Sections:
    - task_spec: The exact task description (pinned, immutable after init)
    - variable_registry: Named references to dataset, columns, file paths
    - code_outputs: Charts (file paths) and data summaries (text) produced by Coder
    - report_draft: Current version of the written report (Writer updates this)
    - status: Current phase, active agent, completion flags

    Usage:
        state = SharedState(
            task_spec="Produce 3 visualizations and a 300-word summary...",
            dataset_path="data/global_weather.csv"
        )
        state.register_variable("target_column", "temperature_celsius")
        state.add_code_output("chart_1", file_path="outputs/chart_1.png", description="Bar chart of top 5 hottest cities")
        state.set_report_draft("## Executive Summary\\n...")
        state.set_phase(3, active_agent="Coder")
    """

    def __init__(
        self,
        task_spec: str,
        dataset_path: str,
        task_type: str = "short",
        output_dir: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize the shared state for a run.

        Args:
            task_spec: The exact task description text (immutable after init).
            dataset_path: Path to the dataset CSV file.
            task_type: "test", "short", or "long".
            output_dir: Path to the run's results folder (for saving final snapshot).
        """
        # Task specification (immutable, always accessible to all agents)
        self.task_spec: str = task_spec
        self.task_type: str = task_type
        self.dataset_path: str = dataset_path

        # Variable registry: named references agents can look up
        # Prevents "Coder forgot the variable name" problem
        self._variables: dict[str, Any] = {
            "dataset_path": dataset_path,
        }

        # Code outputs: what Coder has produced
        # Each entry: {"file_path": str|None, "description": str, "data_summary": str|None}
        self._code_outputs: dict[str, dict[str, Any]] = {}

        # Report draft: Writer's current version (Reviewer reads this)
        self._report_draft: str = ""
        self._report_history: list[dict[str, str]] = []  # previous versions for tracking revisions

        # Status tracker
        self._current_phase: int = 0  # 0 = not started, 1-7 = workflow phases
        self._active_agent: Optional[str] = None
        self._phase_log: list[dict[str, Any]] = []  # phase transition history
        self._completed_phases: list[int] = []

        # Output directory for final snapshot
        self._output_dir: Optional[Path] = Path(output_dir) if output_dir else None

    # ─────────────────────────────────────────────
    # Variable Registry
    # ─────────────────────────────────────────────

    def register_variable(self, name: str, value: Any) -> None:
        """
        Register a named variable so all agents can reference it.

        Examples:
            state.register_variable("target_column", "temperature_celsius")
            state.register_variable("features", ["humidity", "wind_kph", "pressure_mb"])
            state.register_variable("df_shape", (7804, 41))
        """
        self._variables[name] = value

    def get_variable(self, name: str) -> Any:
        """Get a registered variable by name. Returns None if not found."""
        return self._variables.get(name)

    def list_variables(self) -> dict[str, Any]:
        """Return all registered variables."""
        return dict(self._variables)

    # ─────────────────────────────────────────────
    # Code Outputs
    # ─────────────────────────────────────────────

    def add_code_output(
        self,
        name: str,
        file_path: Optional[str] = None,
        description: str = "",
        data_summary: Optional[str] = None,
    ) -> None:
        """
        Record a code output produced by Coder.

        Args:
            name: Identifier for this output (e.g., "chart_1", "cleaned_data_summary").
            file_path: Path to saved file (e.g., "outputs/chart_1.png"). None if text-only.
            description: What this output shows (e.g., "Bar chart of top 5 hottest cities").
            data_summary: Text summary of data results (e.g., "Mean temp: 22.3C, Max: 79.3C").
        """
        self._code_outputs[name] = {
            "file_path": file_path,
            "description": description,
            "data_summary": data_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_code_output(self, name: str) -> Optional[dict[str, Any]]:
        """Get a specific code output by name."""
        return self._code_outputs.get(name)

    def list_code_outputs(self) -> dict[str, dict[str, Any]]:
        """Return all code outputs."""
        return dict(self._code_outputs)

    # ─────────────────────────────────────────────
    # Report Draft
    # ─────────────────────────────────────────────

    def set_report_draft(self, content: str) -> None:
        """
        Update the report draft. Previous version is saved to history.
        Writer calls this; Reviewer reads it.
        """
        if self._report_draft:
            self._report_history.append({
                "content": self._report_draft,
                "replaced_at": datetime.now(timezone.utc).isoformat(),
            })
        self._report_draft = content

    def get_report_draft(self) -> str:
        """Get the current report draft."""
        return self._report_draft

    def get_report_revision_count(self) -> int:
        """How many times the report has been revised."""
        return len(self._report_history)

    # ─────────────────────────────────────────────
    # Phase / Status Tracking
    # ─────────────────────────────────────────────

    def set_phase(self, phase: int, active_agent: Optional[str] = None) -> None:
        """
        Transition to a new phase.

        Args:
            phase: Phase number (1-7).
            active_agent: Which agent is currently working (e.g., "Coder").
        """
        if self._current_phase > 0:
            self._completed_phases.append(self._current_phase)

        self._current_phase = phase
        self._active_agent = active_agent
        self._phase_log.append({
            "phase": phase,
            "active_agent": active_agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @property
    def current_phase(self) -> int:
        """Current workflow phase (0 = not started, 1-7 = active)."""
        return self._current_phase

    @property
    def active_agent(self) -> Optional[str]:
        """Which agent is currently working."""
        return self._active_agent

    def is_phase_completed(self, phase: int) -> bool:
        """Check if a specific phase has been completed."""
        return phase in self._completed_phases

    # ─────────────────────────────────────────────
    # Context Summary (for agent prompts)
    # ─────────────────────────────────────────────

    def get_context_summary(self) -> str:
        """
        Generate a text summary of the current state for inclusion in agent prompts.
        This is what gets injected into the agent's context window so they never
        lose track of the task, variables, or outputs.
        """
        lines = []
        lines.append("=== SHARED STATE ===")
        lines.append(f"\n## Task\n{self.task_spec}")
        lines.append(f"\n## Current Phase: {self._current_phase}")
        if self._active_agent:
            lines.append(f"Active Agent: {self._active_agent}")

        lines.append(f"\n## Variables")
        for name, value in self._variables.items():
            lines.append(f"  - {name}: {value}")

        if self._code_outputs:
            lines.append(f"\n## Code Outputs ({len(self._code_outputs)} items)")
            for name, output in self._code_outputs.items():
                desc = output["description"] or "no description"
                path = output["file_path"] or "text only"
                lines.append(f"  - {name}: {desc} [{path}]")
                if output["data_summary"]:
                    lines.append(f"    Data: {output['data_summary']}")

        if self._report_draft:
            preview = self._report_draft[:200] + "..." if len(self._report_draft) > 200 else self._report_draft
            lines.append(f"\n## Report Draft (revision #{self.get_report_revision_count()})")
            lines.append(f"  {preview}")

        lines.append("\n=== END SHARED STATE ===")
        return "\n".join(lines)

    # ─────────────────────────────────────────────
    # Serialization
    # ─────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full state to a dictionary (for shared_state_final.json)."""
        return {
            "task_spec": self.task_spec,
            "task_type": self.task_type,
            "dataset_path": self.dataset_path,
            "variables": self._variables,
            "code_outputs": self._code_outputs,
            "report_draft": self._report_draft,
            "report_history": self._report_history,
            "current_phase": self._current_phase,
            "active_agent": self._active_agent,
            "completed_phases": self._completed_phases,
            "phase_log": self._phase_log,
        }

    def save_snapshot(self, path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save current state to shared_state_final.json.

        Args:
            path: Override path. Defaults to output_dir/shared_state_final.json.

        Returns:
            Path to the saved file.
        """
        if path is None:
            if self._output_dir is None:
                raise ValueError("No output_dir set. Provide a path or set output_dir at init.")
            self._output_dir.mkdir(parents=True, exist_ok=True)
            path = self._output_dir / "shared_state_final.json"
        else:
            path = Path(path)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        return path
