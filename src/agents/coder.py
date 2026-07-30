"""
Coder Agent: Writes and executes Python code in the sandbox.

The Coder works in two phases:
1. Internal coding loop (private): generate code → execute → retry on error (max 3 tries)
2. Presentation (public): summarize results for the team and post to bus

The team never sees raw code — they see a summary of what was done and the results.
Code is logged to code_executions.jsonl for the researcher audit trail.
Outputs (charts, data summaries) are saved to shared state for Writer and Reviewer.
"""

import re
import logging
from typing import Optional

from src.agents.base_agent import BaseAgent, load_prompt
from src.message_bus import MessageBus
from src.shared_state import SharedState
from src.sandbox import Sandbox, ExecutionResult
from src.utils.api_client import APIClient


log = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    """
    Coder agent with code execution capabilities.

    Overrides respond() to:
    1. Call LLM to generate code
    2. Extract and execute code blocks in the sandbox
    3. Retry on errors (up to max_retries)
    4. Save outputs to shared state
    5. Present a clean summary to the team via message bus

    Usage:
        coder = CoderAgent(
            model=WORKER_MODEL,
            api_client=client,
            message_bus=bus,
            shared_state=state,
            sandbox=sandbox,
        )
        response = coder.respond(phase=3, instruction="Load the CSV and produce the bar charts.")
    """

    def __init__(
        self,
        model: str,
        api_client: APIClient,
        message_bus: MessageBus,
        shared_state: SharedState,
        sandbox: Sandbox,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ):
        """
        Initialize the Coder agent.

        Args:
            model: Anthropic model identifier (should be Haiku for workers).
            api_client: Shared APIClient instance.
            message_bus: Shared MessageBus.
            shared_state: Shared state object.
            sandbox: Sandbox instance for code execution.
            max_tokens: Max tokens per LLM response.
            max_retries: Max attempts to fix code errors before giving up.
        """
        system_prompt = load_prompt("coder.md")

        super().__init__(
            name="Coder",
            system_prompt=system_prompt,
            model=model,
            api_client=api_client,
            message_bus=message_bus,
            shared_state=shared_state,
            max_tokens=max_tokens,
        )

        self.sandbox = sandbox
        self.max_retries = max_retries

    def respond(self, phase: int, instruction: Optional[str] = None) -> str:
        """
        Generate code, execute it, retry on errors, then present results to team.

        Phase 1 (private): LLM generates code → extract → execute → retry on error.
        Phase 2 (public): LLM summarizes what was done → post to bus.

        Args:
            phase: Current workflow phase (1-7).
            instruction: Optional instruction from orchestrator.

        Returns:
            The presentation summary (also posted to the message bus).
        """
        # Phase 1: Internal coding loop (private — nothing goes to bus)
        code_result = self._code_loop(phase, instruction)

        # Phase 2: Present results to the team (public — posted to bus)
        summary = self._present_results(phase, code_result)
        return summary

    def _code_loop(
        self,
        phase: int,
        instruction: Optional[str] = None,
    ) -> dict:
        """
        Internal coding loop: generate code, execute, retry on errors.

        All attempts are logged to code_executions.jsonl but NOT posted to the bus.
        Outputs from successful execution are saved to shared state.

        Returns:
            Dict with keys: success, stdout, files_produced, attempts, last_error
        """
        system = self._build_system_prompt()
        messages = self._build_messages(phase=phase, instruction=instruction)

        last_result: Optional[ExecutionResult] = None
        all_stdout = []

        for attempt in range(1, self.max_retries + 1):
            # Call LLM to generate code
            response = self.api_client.call(
                agent=self.name,
                system_prompt=system,
                messages=messages,
                model=self.model,
                max_tokens=self.max_tokens,
            )

            content = response["content"]
            self._input_tokens += response["input_tokens"]
            self._output_tokens += response["output_tokens"]
            self._call_count += 1

            # Flag nudge if used
            if response.get("nudge_used") is not None:
                self.message_bus.system_notify(
                    content=(
                        f"[NUDGE] {self.name} required a nudge to produce text output "
                        f"(adaptive thinking returned no text). Nudge level {response['nudge_used']}"
                    ),
                    phase=phase,
                )

            # Extract code blocks
            code_blocks = self._extract_code_blocks(content)

            if not code_blocks:
                # LLM responded without code (e.g., asking a question or discussing)
                # Post as a regular message and return
                self.message_bus.send(
                    sender=self.name,
                    recipient="channel",
                    content=content,
                    phase=phase,
                    token_count=response["input_tokens"] + response["output_tokens"],
                )
                return {
                    "success": True,
                    "stdout": "",
                    "files_produced": [],
                    "attempts": attempt,
                    "last_error": None,
                    "no_code": True,
                }

            # Execute all code blocks as a single script
            combined_code = "\n\n".join(code_blocks)
            last_result = self.sandbox.execute(combined_code)

            if last_result.success:
                all_stdout.append(last_result.stdout)
                # Save outputs to shared state
                self._save_outputs(last_result)
                log.info(f"Coder: code executed successfully on attempt {attempt}")
                break

            # Execution failed — feed error back to LLM for retry
            log.warning(f"Coder: attempt {attempt}/{self.max_retries} failed: {last_result.error_message}")

            # Sanitize stderr: replace temp file paths to prevent leaking
            # the results folder name (which contains the leadership style)
            sanitized_stderr = self._sanitize_traceback(last_result.stderr)

            error_feedback = (
                f"[system]: Your code failed with this error:\n"
                f"```\n{sanitized_stderr}\n```\n"
                f"Please fix the code and try again."
            )

            # Add the LLM's response as assistant, then error as user
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": error_feedback})

        # Build result summary
        success = last_result is not None and last_result.success
        return {
            "success": success,
            "stdout": "\n".join(all_stdout) if all_stdout else "",
            "files_produced": last_result.files_produced if last_result else [],
            "attempts": min(attempt, self.max_retries) if last_result else 0,
            "last_error": last_result.error_message if last_result and not success else None,
            "no_code": False,
        }

    @staticmethod
    def _sanitize_traceback(stderr: str) -> str:
        """
        Strip absolute file paths from Python tracebacks to prevent leaking
        the results folder name (which contains the leadership style).

        Replaces patterns like:
            File "/Users/.../results/coercive_short_run01/outputs/tmpXXXX.py", line 5
        with:
            File "script.py", line 5
        """
        return re.sub(
            r'File ".*?/outputs/[^"]*\.py"',
            'File "script.py"',
            stderr,
        )

    def _present_results(self, phase: int, code_result: dict) -> str:
        """
        Make an LLM call to summarize execution results for the team.

        The Coder presents what it did and the key findings — like a real
        developer showing results in a team meeting.

        Args:
            phase: Current workflow phase.
            code_result: Dict from _code_loop with stdout, files, success info.

        Returns:
            Summary text (also posted to the message bus).
        """
        # If there was no code (Coder was just discussing), skip presentation
        if code_result.get("no_code"):
            return code_result.get("stdout", "")

        # Build a presentation prompt
        if code_result["success"]:
            result_info = f"Execution succeeded after {code_result['attempts']} attempt(s).\n"
            if code_result["stdout"]:
                result_info += f"\nConsole output:\n```\n{code_result['stdout']}\n```\n"
            if code_result["files_produced"]:
                result_info += f"\nFiles produced: {', '.join(code_result['files_produced'])}\n"
        else:
            result_info = (
                f"Code execution failed after {code_result['attempts']} attempts.\n"
                f"Last error: {code_result['last_error']}\n"
            )

        presentation_instruction = (
            f"[system]: You have finished your coding work. Here are the results:\n\n"
            f"{result_info}\n"
            f"Now summarize what you did and the key findings for your team. "
            f"Focus on results and insights, not on implementation details. "
            f"Reference any charts or outputs you produced."
        )

        # Build messages: full history + presentation instruction
        system = self._build_system_prompt()
        messages = self._build_messages(phase=phase)

        # Append the presentation instruction
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += f"\n\n{presentation_instruction}"
        else:
            messages.append({"role": "user", "content": presentation_instruction})

        response = self.api_client.call(
            agent=self.name,
            system_prompt=system,
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
        )

        content = response["content"]
        self._input_tokens += response["input_tokens"]
        self._output_tokens += response["output_tokens"]
        self._call_count += 1

        # Flag nudge if used
        if response.get("nudge_used") is not None:
            self.message_bus.system_notify(
                content=(
                    f"[NUDGE] {self.name} required a nudge to produce text output "
                    f"(adaptive thinking returned no text). Nudge level {response['nudge_used']}"
                ),
                phase=phase,
            )

        # Post the presentation to the bus
        self.message_bus.send(
            sender=self.name,
            recipient="channel",
            content=content,
            phase=phase,
            token_count=response["input_tokens"] + response["output_tokens"],
        )

        return content

    def _save_outputs(self, result: ExecutionResult) -> None:
        """
        Save successful execution outputs to shared state.

        Registers produced files and stdout data so Writer and Reviewer
        can access real results (not hallucinated data).
        """
        for file_name in result.files_produced:
            self.shared_state.add_code_output(
                name=file_name,
                file_path=file_name,
                description=f"Produced by Coder (auto-detected)",
            )

        if result.stdout.strip():
            self.shared_state.add_code_output(
                name=f"console_output_{self._call_count}",
                description="Console output from code execution",
                data_summary=result.stdout.strip(),
            )

    @staticmethod
    def _extract_code_blocks(text: str) -> list[str]:
        """
        Extract Python code blocks from LLM output.

        Matches ```python ... ``` and ``` ... ``` fenced blocks.

        Returns:
            List of code strings (empty if no code blocks found).
        """
        # Match only ```python ... ``` blocks (not bare ``` blocks which may contain output text)
        pattern = r"```python\s*\n(.*?)```"
        blocks = re.findall(pattern, text, re.DOTALL)
        return [block.strip() for block in blocks if block.strip()]