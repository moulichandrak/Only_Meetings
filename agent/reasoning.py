"""Reasoning Engine - decides next action based on current state and step results."""

import logging
from typing import Optional, Tuple
from models.schemas import AgentStep, StepStatus

logger = logging.getLogger("agent.reasoning")


class ReasoningEngine:
    """Evaluates step results and decides what to do next."""

    def evaluate_step_result(self, step: AgentStep, result: dict) -> Tuple[str, Optional[dict]]:
        """Evaluate a step's result and decide the next action.

        Returns:
            Tuple of (decision, context):
            - ("proceed", None) — move to next step
            - ("retry", {"reason": ...}) — retry current step
            - ("reschedule", {"new_time": ...}) — slot unavailable, try new time
            - ("fail", {"error": ...}) — unrecoverable failure
        """
        if result.get("success"):
            logger.info(f"Step {step.step_number} ({step.action}) succeeded")
            return ("proceed", None)

        error = result.get("error", "Unknown error")
        error_lower = str(error).lower()

        # Slot unavailable — reschedule
        if step.action == "check_availability" and ("busy" in error_lower or "unavailable" in error_lower or "conflict" in error_lower):
            logger.info(f"Slot unavailable: {error}. Will try next available slot.")
            return ("reschedule", {"reason": error})

        # Rate limit or temporary errors — retry
        if any(keyword in error_lower for keyword in ["rate limit", "timeout", "503", "502", "429", "temporary"]):
            logger.info(f"Temporary error: {error}. Will retry.")
            return ("retry", {"reason": error})

        # Auth errors — fail immediately
        if any(keyword in error_lower for keyword in ["401", "403", "unauthorized", "forbidden", "invalid_grant"]):
            logger.error(f"Auth error: {error}. Cannot retry.")
            return ("fail", {"error": f"Authentication error: {error}. Please re-authenticate."})

        # Default: retry
        logger.warning(f"Unexpected error: {error}. Will attempt retry.")
        return ("retry", {"reason": error})

    def should_skip_notification(self, meeting_details: dict) -> bool:
        """Decide if notification should be skipped (e.g., no attendees)."""
        attendees = meeting_details.get("attendees", [])
        if not attendees:
            logger.info("No attendees specified — notification step will send to organizer only")
            return False
        return False


# Singleton
reasoning_engine = ReasoningEngine()
