"""
Code Execution Sandbox: Runs Python code produced by the Coder agent.

Executes code in a subprocess, captures stdout/stderr, detects produced files,
and logs every execution to code_executions.jsonl for the researcher audit trail.

Safety: runs in a subprocess with a timeout to prevent hangs.
The Coder is the only agent that uses this module.
"""

import json
import os
import sys
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

        A security preamble is injected before the user's code to prevent:
        - Writing files outside self.working_dir (via open(), savefig, to_csv, etc.)
        - Creating directories anywhere (os.makedirs, os.mkdir)
        - Discovering the real working directory path (which contains the leadership style)

        Args:
            code: Python code string to execute.

        Returns:
            ExecutionResult with stdout, stderr, exit_code, files_produced, etc.
        """
        # Snapshot files before execution to detect new ones
        files_before = set(self._list_files(self.working_dir))

        # Inject security preamble + user code
        secured_code = self._build_security_preamble() + "\n\n" + code

        # Write code to a temp file and execute as subprocess
        start_time = datetime.now(timezone.utc)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.working_dir,
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(secured_code)
            tmp_path = tmp.name

        try:
            proc = subprocess.run(
                [sys.executable, tmp_path],
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
            code=code,  # Log the original code (without preamble) for clean audit trail
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

    def _build_security_preamble(self) -> str:
        """
        Build a Python code preamble that restricts file operations to self.working_dir.

        Monkey-patches:
        - builtins.open: blocks write/append modes to paths outside working_dir
        - os.chdir: prevents changing working directory outside working_dir
        - os.makedirs / os.mkdir / Path.mkdir: blocks directory creation outside working_dir
        - os.getcwd: returns a generic path to prevent leaking the leadership style

        Read access is unrestricted (Coder needs to read the dataset from data/).
        """
        working_dir_str = str(self.working_dir.resolve())
        # Project root: restrict directory creation and writes within the MAS project tree
        project_root_str = str(Path(__file__).resolve().parent.parent)

        return f'''
# ═══ SANDBOX SECURITY PREAMBLE (injected by sandbox.py) ═══
import builtins as _builtins
import os as _os
from pathlib import Path as _Path

_SANDBOX_DIR = _Path("{working_dir_str}").resolve()
_PROJECT_ROOT = _Path("{project_root_str}").resolve()
_original_open = _builtins.open
_original_makedirs = _os.makedirs
_original_mkdir = _os.mkdir
_original_chdir = _os.chdir

def _is_in_project(path_str):
    """Check if a resolved path is inside the MAS project directory."""
    try:
        resolved = str(_Path(path_str).resolve())
        return resolved.startswith(str(_PROJECT_ROOT))
    except Exception:
        return False

def _is_in_sandbox(path_str):
    """Check if a resolved path is inside or equal to the sandbox directory."""
    try:
        resolved = str(_Path(path_str).resolve())
        sandbox_str = str(_SANDBOX_DIR)
        return resolved == sandbox_str or resolved.startswith(sandbox_str + _os.sep)
    except Exception:
        return False

def _sandboxed_open(file, mode="r", *args, **kwargs):
    """Wrapper: allow reads anywhere, but writes inside the project only in the sandbox dir."""
    is_write = any(c in mode for c in "wxa")
    if is_write:
        target_str = str(_Path(file).resolve())
        # Block writes inside the project that aren't in the sandbox dir
        if _is_in_project(target_str) and not _is_in_sandbox(target_str):
            raise PermissionError(
                f"SANDBOX VIOLATION: Cannot write to '{{file}}' — "
                f"all output files must be saved with relative paths inside the outputs folder. "
                f"Do NOT use absolute paths or write outside the current working directory."
            )
    return _original_open(file, mode, *args, **kwargs)

def _guarded_chdir(path, *args, **kwargs):
    """Block chdir outside the sandbox directory."""
    target_str = str(_Path(path).resolve())
    if _is_in_project(target_str) and not _is_in_sandbox(target_str):
        raise PermissionError(
            f"SANDBOX VIOLATION: Cannot change working directory to '{{path}}'. "
            f"All operations must stay within the assigned outputs directory."
        )
    return _original_chdir(path, *args, **kwargs)

def _guarded_makedirs(name, *args, **kwargs):
    """Block makedirs inside project tree if outside sandbox dir, allow system dirs."""
    target_str = str(_Path(name).resolve())
    if _is_in_project(target_str) and not _is_in_sandbox(target_str):
        raise PermissionError(
            "SANDBOX VIOLATION: Creating directories outside the outputs folder is not allowed. "
            "Save files directly with relative paths (e.g., plt.savefig('chart.png'))."
        )
    return _original_makedirs(name, *args, **kwargs)

def _guarded_mkdir(name, *args, **kwargs):
    """Block mkdir inside project tree if outside sandbox dir, allow system dirs."""
    target_str = str(_Path(name).resolve())
    if _is_in_project(target_str) and not _is_in_sandbox(target_str):
        raise PermissionError(
            "SANDBOX VIOLATION: Creating directories outside the outputs folder is not allowed. "
            "Save files directly with relative paths (e.g., plt.savefig('chart.png'))."
        )
    return _original_mkdir(name, *args, **kwargs)

def _safe_getcwd():
    """Return a generic path so the Coder cannot see the leadership style in the folder name."""
    return "/workspace/outputs"

_builtins.open = _sandboxed_open
_os.chdir = _guarded_chdir
_os.makedirs = _guarded_makedirs
_os.mkdir = _guarded_mkdir
_os.getcwd = _safe_getcwd

# Also patch Path.mkdir to prevent directory creation via pathlib
_original_path_mkdir = _Path.mkdir
def _guarded_path_mkdir(self, *args, **kwargs):
    target_str = str(self.resolve())
    if _is_in_project(target_str) and not _is_in_sandbox(target_str):
        raise PermissionError(
            "SANDBOX VIOLATION: Creating directories outside the outputs folder is not allowed. "
            "Save files directly with relative paths (e.g., plt.savefig('chart.png'))."
        )
    return _original_path_mkdir(self, *args, **kwargs)
_Path.mkdir = _guarded_path_mkdir

# ═══ END SECURITY PREAMBLE ═══
'''

    def _list_files(self, directory: Path) -> list[str]:
        """List all files in a directory (recursive, relative names)."""
        if not directory.exists():
            return []
        return [
            str(p.relative_to(directory))
            for p in directory.rglob("*")
            if p.is_file()
        ]

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
