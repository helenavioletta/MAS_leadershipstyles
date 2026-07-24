"""
Experiment Logger: Creates run folders, writes metadata.json, and coordinates output paths.

This is the top-level coordinator for all logging in a single experiment run.
It sets up the results folder structure and provides paths to the other modules
(MessageBus, APIClient, sandbox) so they know where to write their logs.

At the end of a run, it writes metadata.json with the full run configuration
including the leadership style, task wording, model versions, and token totals.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Any


RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"


class ExperimentLogger:
    """
    Manages the results folder for a single experiment run.

    Responsibilities:
    - Create the run folder (e.g., results/coercive_short_run01/)
    - Create the outputs/ subfolder for charts and reports
    - Provide paths for MessageBus, APIClient, and sandbox to write to
    - Write metadata.json at the end of the run

    Usage:
        logger = ExperimentLogger(
            style="coercive",
            task_type="short",
            run_id=1,
            boss_system_prompt="You are a team lead...",
            task_wording="Produce 3 visualizations...",
            boss_model=BOSS_MODEL,
            worker_model=WORKER_MODEL,
        )

        # Pass logger.run_dir to MessageBus and APIClient
        bus = MessageBus(output_dir=logger.run_dir)
        client = APIClient(output_dir=logger.run_dir)

        # At end of run
        logger.save_metadata(
            total_tokens=client.total_tokens,
            total_input_tokens=client.total_input_tokens,
            total_output_tokens=client.total_output_tokens,
            total_messages=bus.message_count,
            total_api_calls=client.total_api_calls,
        )
    """

    def __init__(
        self,
        style: str,
        task_type: str,
        run_id: int,
        boss_system_prompt: str,
        task_wording: str,
        boss_model: str,
        worker_model: str,
        max_revision_rounds: int = 2,
        results_base_dir: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize the logger and create the run folder.

        Args:
            style: Leadership style name (e.g., "coercive", "baseline").
            task_type: Task type (e.g., "short", "long", "test").
            run_id: Run number for this condition (1, 2, 3, ...).
            boss_system_prompt: The full Boss system prompt (base_role + style).
            task_wording: The exact task text sent to agents.
            boss_model: Model used for Boss.
            worker_model: Model used for workers.
            max_revision_rounds: Max revision rounds allowed.
            results_base_dir: Override for the base results directory.
        """
        self.style = style
        self.task_type = task_type
        self.run_id = run_id
        self.boss_system_prompt = boss_system_prompt
        self.task_wording = task_wording
        self.boss_model = boss_model
        self.worker_model = worker_model
        self.max_revision_rounds = max_revision_rounds

        self._start_time = datetime.now(timezone.utc)

        # Create run folder: results/coercive_short_run01/
        base = Path(results_base_dir) if results_base_dir else RESULTS_DIR
        folder_name = f"{style}_{task_type}_run{run_id:02d}"
        self.run_dir = base / folder_name
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Create outputs subfolder for charts and reports
        self.outputs_dir = self.run_dir / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)

    def save_metadata(
        self,
        total_tokens: int = 0,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0,
        total_messages: int = 0,
        total_api_calls: int = 0,
        total_code_executions: int = 0,
        extra: Optional[dict[str, Any]] = None,
    ) -> Path:
        """
        Write metadata.json with full run configuration and totals.

        Call this at the end of a run, after all experiments are done.

        Args:
            total_tokens: Total tokens (input + output) from APIClient.
            total_input_tokens: Total input tokens from APIClient.
            total_output_tokens: Total output tokens from APIClient.
            total_messages: Total messages from MessageBus.
            total_api_calls: Total API calls from APIClient.
            total_code_executions: Total code executions from sandbox.
            extra: Any additional metadata to include.

        Returns:
            Path to the saved metadata.json file.
        """
        end_time = datetime.now(timezone.utc)

        metadata = {
            "leadership_style": self.style,
            "boss_system_prompt": self.boss_system_prompt,
            "task_type": self.task_type,
            "task_wording": self.task_wording,
            "boss_model": self.boss_model,
            "worker_model": self.worker_model,
            "temperature": self.temperature,
            "max_revision_rounds": self.max_revision_rounds,
            "run_id": self.run_id,
            "total_tokens": total_tokens,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_messages": total_messages,
            "total_api_calls": total_api_calls,
            "total_code_executions": total_code_executions,
            "start_time": self._start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round((end_time - self._start_time).total_seconds(), 2),
        }

        if extra:
            metadata.update(extra)

        path = self.run_dir / "metadata.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return path
