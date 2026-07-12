"""
Code Execution Sandbox: Runs Python code produced by the Coder agent.

Executes code in a subprocess, captures stdout/stderr, detects produced files,
and logs every execution to code_executions.jsonl for the researcher audit trail.

Safety: runs in a subprocess with a timeout to prevent hangs.
The Coder is the only agent that uses this module.
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass, field, asdict


@dataclass
class ExecutionResult:
    """Result of a single code execution."""
    code: str
    stdout: str
    stderr: str
    exit_code: int
    files_produced: list[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


class Sandbox:
    """
    Executes Python code in an isolated subprocess.

    Responsibilities:
    - Run code strings as Python scripts in a subprocess
    - Capture stdout and stderr
    - Detect files produced during execution (charts, CSVs, etc.)
    - Enforce a timeout to prevent infinite loops
    - Log every execution to code_executions.jsonl

    Usage:
        sandbox = Sandbox(
            output_dir="results/coercive_short_run01",
            working_dir="results/coercive_short_run01/outputs",
        )
        result = sandbox.execute("import pandas as pd; print(pd.read_csv('data/global_weather.csv').shape)")
        print(result.stdout)       # "(7804, 41)"
        print(result.success)      # True
        print(result.files_produced)  # ["chart_1.png"] if any files were created
    """

    def __init__(
        self,
        output_dir: Union[str, Path],
        working_dir: Optional[Union[str, Path]] = None,
        timeout: int = 120,
    ):
        """
        Initialize the sandbox.

        Args:
            output_dir: Path to the run's results folder (for code_executions.jsonl).
            working_dir: Directory where code executes and saves files (charts, CSVs).
                         Defaults to output_dir/outputs.
            timeout: Max seconds a code execution is allowed to run before being killed.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.output_dir / "code_executions.jsonl"

        self.working_dir = Path(working_dir) if working_dir else self.output_dir / "outputs"
        self.working_dir.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self._seq_counter: int = 0
        self.total_executions: int = 0

    def execute(self, code: str) -> ExecutionResult:
        """
        Execute a Python code string in a subprocess.

        The code runs in self.working_dir so any files it creates (e.g., plt.savefig("chart.png"))
        end up in the outputs folder. Files existing before execution are tracked so we can
        detect which files were newly produced.

        Args:
            code: Python code string to execute.

        Returns:
            ExecutionResult with stdout, stderr, exit_code, files_produced, etc.
        """
        # Snapshot files before execution to detect new ones
        files_before = set(self._list_files(self.working_dir))

        # Write code to a temp file and execute as subprocess
        start_time = datetime.now(timezone.utc)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.working_dir,
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            proc = subprocess.run(
                ["python3", tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.working_dir),
                env=self._build_env(),
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
            success = exit_code == 0
            error_message = stderr.strip() if not success else None

        except subprocess.TimeoutExpired:
            stdout = ""
            stderr = f"Execution timed out after {self.timeout} seconds."
            exit_code = -1
            success = False
            error_message = stderr

        except Exception as e:
            stdout = ""
            stderr = str(e)
            exit_code = -1
            success = False
            error_message = stderr

        finally:
            # Clean up temp script file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Detect newly produced files
        files_after = set(self._list_files(self.working_dir))
        new_files = sorted(files_after - files_before)

        result = ExecutionResult(
            code=code,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            files_produced=new_files,
            success=success,
            error_message=error_message,
            duration_seconds=round(duration, 2),
        )

        # Log and count
        self._persist(result)
        self.total_executions += 1

        return result

    def _list_files(self, directory: Path) -> list[str]:
        """List all files in a directory (non-recursive, relative names)."""
        if not directory.exists():
            return []
        return [f.name for f in directory.iterdir() if f.is_file()]

    def _build_env(self) -> dict[str, str]:
        """Build environment variables for the subprocess."""
        env = os.environ.copy()
        # Ensure non-interactive matplotlib backend for chart generation
        env["MPLBACKEND"] = "Agg"
        return env

    def _persist(self, result: ExecutionResult) -> None:
        """Append an execution result to code_executions.jsonl."""
        self._seq_counter += 1
        entry = {
            "seq": self._seq_counter,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **asdict(result),
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
