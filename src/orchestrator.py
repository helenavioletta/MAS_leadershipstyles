"""
Orchestrator: 7-phase sequential workflow for the MAS leadership experiment.

Controls turn order, phase transitions, and revision routing.
The orchestrator does NOT make any LLM calls itself — it only coordinates agents.

Phases:
    1. BRIEFING   — Boss assigns the task to the team
    2. PLANNING   — Team discusses approach, Reviewer reviews the plan
    3. CODING     — Coder writes & executes code, Boss gates advancement
                    (Boss can extend coding phase up to max_coding_extensions
                    times via REVISE_CODING, giving Coder 3 fresh retries each)
    4. WRITING    — Writer drafts narrative, Boss may check in
    5. REVIEW     — Reviewer checks code outputs + report
    6. REVISION   — Boss decides: REVISE_CODE, REVISE_REPORT, REVISE_BOTH, or SHIP
    7. DELIVERY   — Final output logged, run ends
"""

import logging
import time
from typing import Optional

from src.agents.boss import BossAgent
from src.agents.coder import CoderAgent
from src.agents.writer import WriterAgent
from src.agents.reviewer import ReviewerAgent
from src.message_bus import MessageBus
from src.shared_state import SharedState


log = logging.getLogger(__name__)

# Phase names for logging and system notifications
PHASE_NAMES = {
    1: "BRIEFING",
    2: "PLANNING",
    3: "CODING",
    4: "WRITING",
    5: "REVIEW",
    6: "REVISION",
    7: "DELIVERY",
}


class Orchestrator:
    """
    Runs the 7-phase sequential workflow for one experiment run.

    Usage:
        orchestrator = Orchestrator(
            boss=boss_agent,
            coder=coder_agent,
            writer=writer_agent,
            reviewer=reviewer_agent,
            message_bus=bus,
            shared_state=state,
            max_revision_rounds=2,
        )
        summary = orchestrator.run()
    """

    def __init__(
        self,
        boss: BossAgent,
        coder: CoderAgent,
        writer: WriterAgent,
        reviewer: ReviewerAgent,
        message_bus: MessageBus,
        shared_state: SharedState,
        max_revision_rounds: int = 2,
        max_coding_extensions: int = 2,
    ):
        """
        Initialize the orchestrator.

        Args:
            boss: Boss agent instance.
            coder: Coder agent instance.
            writer: Writer agent instance.
            reviewer: Reviewer agent instance.
            message_bus: Shared message bus.
            shared_state: Shared state object.
            max_revision_rounds: Max times Phase 6 can loop before forcing delivery.
            max_coding_extensions: Max times the Boss can send the Coder back
                in Phase 3 before forcing advancement to Phase 4.
        """
        self.boss = boss
        self.coder = coder
        self.writer = writer
        self.reviewer = reviewer
        self.message_bus = message_bus
        self.shared_state = shared_state
        self.max_revision_rounds = max_revision_rounds
        self.max_coding_extensions = max_coding_extensions

        self._start_time: Optional[float] = None
        self._revision_count: int = 0
        self._coding_extensions: int = 0

    # ─────────────────────────────────────────────
    # Main Entry Point
    # ─────────────────────────────────────────────

    def run(self) -> dict:
        """
        Run the full 7-phase workflow.

        Returns:
            Summary dict with timing, token usage, revision count, etc.
        """
        self._start_time = time.time()
        log.info("Orchestrator: starting experiment run")

        self._phase_1_briefing()
        self._phase_2_planning()
        self._phase_3_coding()
        self._phase_4_writing()
        self._phase_5_review()
        self._phase_6_revision_loop()
        self._phase_7_delivery()

        summary = self._build_summary()
        log.info(f"Orchestrator: run completed in {summary['duration_seconds']:.1f}s")
        return summary

    # ─────────────────────────────────────────────
    # Phase Implementations
    # ─────────────────────────────────────────────

    def _phase_1_briefing(self) -> None:
        """Phase 1: Boss assigns the task to the team."""
        self._enter_phase(1, "Boss")

        task_spec = self.shared_state.task_spec
        self.boss.respond(
            phase=1,
            instruction=(
                f"You are starting a new project. Here is the task your team must complete:\n\n"
                f"{task_spec}\n\n"
                f"Introduce the task to your team and assign roles. "
                f"Your team members are: Coder (writes and executes Python code), "
                f"Writer (writes narrative text and reports), and "
                f"Reviewer (checks quality of outputs and text)."
            ),
        )

    def _phase_2_planning(self) -> None:
        """Phase 2: Team discusses approach. Reviewer reviews the plan."""
        self._enter_phase(2, "Boss")

        # Boss proposes the plan
        self.boss.respond(
            phase=2,
            instruction=(
                "Now lay out the plan for how the team will tackle this task. "
                "Describe what the Coder should do first, what the Writer should prepare for, "
                "and what the Reviewer should look out for."
            ),
        )

        # Coder responds to the plan
        self.shared_state.set_phase(2, active_agent="Coder")
        self.coder.respond(
            phase=2,
            instruction="The Boss has shared the plan. Respond with your approach and any questions.",
        )

        # Writer responds to the plan
        self.shared_state.set_phase(2, active_agent="Writer")
        self.writer.respond(
            phase=2,
            instruction="The Boss has shared the plan. Respond with your approach and any questions.",
        )

        # Reviewer reviews the plan
        self.shared_state.set_phase(2, active_agent="Reviewer")
        self.reviewer.respond(
            phase=2,
            instruction=(
                "The team has discussed the plan. Review it: "
                "Is anything missing? Are the priorities right? Flag any concerns."
            ),
        )

        # Boss wraps up planning
        self.shared_state.set_phase(2, active_agent="Boss")
        self.boss.respond(
            phase=2,
            instruction="The team has responded. Wrap up the planning phase with final instructions.",
        )

    def _phase_3_coding(self) -> None:
        """
        Phase 3: Coder writes and executes code. Boss gates advancement.

        Flow:
        1. Coder codes (up to 3 internal retries) and presents results.
        2. Boss decides: PASS_CODING (advance to Writing) or REVISE_CODING
           (send Coder back for another round of 3 retries).
        3. Boss can extend the coding phase up to max_coding_extensions times
           (default 2), giving the Coder up to 9 total attempts worst case.
        """
        self._enter_phase(3, "Coder")

        # Initial coding round
        self.coder.respond(
            phase=3,
            instruction=(
                "It's time to code. Follow the plan and complete the coding tasks. "
                "Write the Python code, execute it, and present the results to the team."
            ),
        )

        # Boss gate loop: decide whether to advance or extend coding
        for extension in range(self.max_coding_extensions + 1):
            self.shared_state.set_phase(3, active_agent="Boss")

            if extension == self.max_coding_extensions:
                # Final check-in — no more extensions possible, just respond
                self.boss.respond(
                    phase=3,
                    instruction=(
                        "The Coder has presented their results. "
                        "The coding phase is ending now. "
                        "You may provide feedback, encouragement, corrections, "
                        "or simply move on. Respond to the team."
                    ),
                )
                break

            # Boss decides: advance or extend
            boss_response = self.boss.respond(
                phase=3,
                instruction=(
                    "The Coder has presented their results. Review what was delivered.\n\n"
                    "You MUST include exactly one of these keywords in your response:\n"
                    "- PASS_CODING — the coding output is acceptable, move to the writing phase\n"
                    "- REVISE_CODING — the coding output is not acceptable, "
                    "send the Coder back to fix and try again\n\n"
                    "You may also include feedback, instructions, or corrections "
                    "for the Coder alongside your decision."
                ),
            )

            decision = self._parse_coding_decision(boss_response)
            log.info(f"Orchestrator: Boss coding decision = {decision} "
                     f"(extension {extension + 1}/{self.max_coding_extensions})")

            if decision == "PASS_CODING":
                break

            # REVISE_CODING — give the Coder another round
            self._coding_extensions += 1
            self.shared_state.set_phase(3, active_agent="Coder")
            self.coder.respond(
                phase=3,
                instruction=(
                    "The Boss has reviewed your output and wants you to revise. "
                    "Read the Boss's feedback, fix the issues, and try again. "
                    "Write the Python code, execute it, and present the updated results."
                ),
            )

    def _phase_4_writing(self) -> None:
        """Phase 4: Writer drafts narrative. Boss may check in."""
        self._enter_phase(4, "Writer")

        # Writer drafts the report
        self.writer.respond(
            phase=4,
            instruction=(
                "It's time to write. Based on the Coder's outputs and the task requirements, "
                "write the narrative text / report. Use the data and charts from the shared state."
            ),
        )

        # Boss check-in
        self.shared_state.set_phase(4, active_agent="Boss")
        self.boss.respond(
            phase=4,
            instruction=(
                "The Writer has drafted the report. "
                "You may provide feedback, encouragement, corrections, or simply move on. "
                "Respond to the team."
            ),
        )

    def _phase_5_review(self) -> None:
        """Phase 5: Reviewer checks code outputs and report."""
        self._enter_phase(5, "Reviewer")

        self.reviewer.respond(
            phase=5,
            instruction=(
                "Review the team's deliverables. Check:\n"
                "1. Do the Coder's outputs make sense? Would a good data scientist do this?\n"
                "2. Does the Writer's text capture what's important in the data/charts?\n"
                "3. Are there any inconsistencies between the data and the narrative?\n"
                "Provide specific, actionable feedback."
            ),
        )

    def _phase_6_revision_loop(self) -> None:
        """Phase 6: Boss decides to revise or ship. Max N rounds."""
        for round_num in range(1, self.max_revision_rounds + 1):
            self._enter_phase(6, "Boss")
            log.info(f"Orchestrator: revision round {round_num}/{self.max_revision_rounds}")

            # Boss decides what to do with the Reviewer's feedback
            boss_response = self.boss.respond(
                phase=6,
                instruction=(
                    "The Reviewer has provided feedback. Decide what to do.\n\n"
                    "You MUST include exactly one of these keywords in your response:\n"
                    "- SHIP — deliver as-is, the work is good enough\n"
                    "- REVISE_CODE — send the Coder back to fix issues\n"
                    "- REVISE_REPORT — send the Writer back to fix issues\n"
                    "- REVISE_BOTH — send both Coder and Writer back to fix issues\n\n"
                    "After the keyword, write your feedback and instructions for whoever "
                    "needs to revise. Be specific about what needs to change."
                ),
            )

            # Parse the Boss's decision
            decision = self._parse_revision_decision(boss_response)
            log.info(f"Orchestrator: Boss decision = {decision}")

            if decision == "SHIP":
                self.message_bus.system_notify(
                    content="Boss has decided to ship. Moving to delivery.",
                    phase=6,
                )
                break

            # Route revisions based on Boss's decision
            self._revision_count += 1

            if decision in ("REVISE_CODE", "REVISE_BOTH"):
                self.shared_state.set_phase(6, active_agent="Coder")
                self.coder.respond(
                    phase=6,
                    instruction=(
                        "The Boss wants you to revise your code based on the feedback. "
                        "Read the Boss's instructions and the Reviewer's comments, "
                        "then fix and re-run your code."
                    ),
                )

            if decision in ("REVISE_REPORT", "REVISE_BOTH"):
                self.shared_state.set_phase(6, active_agent="Writer")
                self.writer.respond(
                    phase=6,
                    instruction=(
                        "The Boss wants you to revise the report based on the feedback. "
                        "Read the Boss's instructions and the Reviewer's comments, "
                        "then update the report."
                    ),
                )

            # Reviewer re-reviews after revision
            self.shared_state.set_phase(6, active_agent="Reviewer")
            self.reviewer.respond(
                phase=6,
                instruction=(
                    f"The team has revised their work (revision round {round_num}). "
                    "Review the updated deliverables and provide feedback."
                ),
            )
        else:
            # Max rounds reached without SHIP — force delivery
            self.message_bus.system_notify(
                content=(
                    f"Maximum revision rounds ({self.max_revision_rounds}) reached. "
                    "Forcing delivery."
                ),
                phase=6,
            )
            log.warning("Orchestrator: max revision rounds reached, forcing delivery")

    def _phase_7_delivery(self) -> None:
        """Phase 7: Final output logged, run ends."""
        self._enter_phase(7, "system")

        self.message_bus.system_notify(
            content="The project is complete. Final deliverables have been submitted.",
            phase=7,
        )

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _enter_phase(self, phase: int, active_agent: str) -> None:
        """Transition to a new phase with logging and notifications."""
        phase_name = PHASE_NAMES.get(phase, f"PHASE_{phase}")
        self.shared_state.set_phase(phase, active_agent=active_agent)
        self.message_bus.system_notify(
            content=f"--- Phase {phase}: {phase_name} ---",
            phase=phase,
        )
        log.info(f"Orchestrator: entering Phase {phase} ({phase_name})")

    @staticmethod
    def _parse_coding_decision(boss_response: str) -> str:
        """
        Parse the Boss's coding-phase decision from their response.

        Looks for keywords: PASS_CODING, REVISE_CODING.
        Falls back to PASS_CODING if no keyword is found (don't stall).

        Args:
            boss_response: The Boss's free-text response.

        Returns:
            One of: "PASS_CODING", "REVISE_CODING"
        """
        text_upper = boss_response.upper()

        if "REVISE_CODING" in text_upper:
            return "REVISE_CODING"
        if "PASS_CODING" in text_upper:
            return "PASS_CODING"

        # Fallback: advance to avoid infinite loops
        log.warning("Orchestrator: Boss coding response missing keyword, "
                    "falling back to PASS_CODING")
        return "PASS_CODING"

    @staticmethod
    def _parse_revision_decision(boss_response: str) -> str:
        """
        Parse the Boss's revision decision from their response.

        Looks for keywords: SHIP, REVISE_CODE, REVISE_REPORT, REVISE_BOTH.
        Falls back to REVISE_BOTH if no keyword is found.

        Args:
            boss_response: The Boss's free-text response.

        Returns:
            One of: "SHIP", "REVISE_CODE", "REVISE_REPORT", "REVISE_BOTH"
        """
        text_upper = boss_response.upper()

        # Check in order of specificity (REVISE_BOTH before REVISE_CODE/REVISE_REPORT)
        if "REVISE_BOTH" in text_upper:
            return "REVISE_BOTH"
        if "REVISE_CODE" in text_upper:
            return "REVISE_CODE"
        if "REVISE_REPORT" in text_upper:
            return "REVISE_REPORT"
        if "SHIP" in text_upper:
            return "SHIP"

        # Fallback: if Boss didn't include a keyword, revise both
        log.warning("Orchestrator: Boss response missing keyword, falling back to REVISE_BOTH")
        return "REVISE_BOTH"

    def _build_summary(self) -> dict:
        """
        Build a summary dict of the completed run.

        Returns:
            Dict with timing, token usage, revision count, and message stats.
        """
        duration = time.time() - self._start_time if self._start_time else 0.0

        # Collect token usage from all agents
        agents = {
            "Boss": self.boss,
            "Coder": self.coder,
            "Writer": self.writer,
            "Reviewer": self.reviewer,
        }
        token_usage = {}
        total_input = 0
        total_output = 0
        total_calls = 0

        for name, agent in agents.items():
            token_usage[name] = {
                "input_tokens": agent.input_tokens,
                "output_tokens": agent.output_tokens,
                "total_tokens": agent.total_tokens,
                "call_count": agent.call_count,
            }
            total_input += agent.input_tokens
            total_output += agent.output_tokens
            total_calls += agent.call_count

        return {
            "duration_seconds": round(duration, 2),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_api_calls": total_calls,
            "total_messages": self.message_bus.message_count,
            "revision_rounds": self._revision_count,
            "coding_extensions": self._coding_extensions,
            "token_usage_by_agent": token_usage,
        }