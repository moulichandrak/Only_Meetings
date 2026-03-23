"""Task Planner - decomposes natural language tasks into executable steps."""

import re
import logging
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Tuple
from models.schemas import MeetingDetails, AgentStep, StepStatus

logger = logging.getLogger("agent.planner")


class TaskPlanner:
    """Parses natural language and produces ordered AgentStep objects."""

    def extract_meeting_details(self, task_input: str) -> MeetingDetails:
        """Extract meeting details from natural language input.

        Parses: title, date, time, attendees, duration from text like
        'Schedule meeting tomorrow at 10 AM with alice@example.com and bob@example.com'
        """
        task_lower = task_input.lower()

        # --- Extract Time ---
        time_str = None
        time_patterns = [
            r'at\s+(\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm|AM|PM))',
            r'at\s+(\d{1,2}[:\.]?\d{0,2})\s*(?:hours?|hrs?)?',
            r'(\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm|AM|PM))',
        ]
        for pattern in time_patterns:
            match = re.search(pattern, task_input, re.IGNORECASE)
            if match:
                time_str = match.group(1).strip()
                break

        # --- Extract Date ---
        date_str = None
        now = datetime.now()

        if "tomorrow" in task_lower:
            target_date = now + timedelta(days=1)
            date_str = target_date.strftime("%Y-%m-%d")
        elif "today" in task_lower:
            date_str = now.strftime("%Y-%m-%d")
        elif "next week" in task_lower:
            target_date = now + timedelta(days=(7 - now.weekday()))
            date_str = target_date.strftime("%Y-%m-%d")
        elif "day after tomorrow" in task_lower:
            target_date = now + timedelta(days=2)
            date_str = target_date.strftime("%Y-%m-%d")
        else:
            # Try to parse explicit date
            date_patterns = [
                r'on\s+(\d{4}-\d{2}-\d{2})',
                r'on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)',
                r'(\d{1,2}/\d{1,2}/\d{2,4})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, task_input, re.IGNORECASE)
                if match:
                    try:
                        parsed = date_parser.parse(match.group(1), fuzzy=True)
                        date_str = parsed.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        pass
                    break

        if not date_str:
            # Default to tomorrow
            date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        if not time_str:
            time_str = "10:00 AM"

        # --- Extract Attendees (emails) ---
        email_pattern = r'[\w.+-]+@[\w-]+\.[\w.]+'
        attendees = re.findall(email_pattern, task_input)

        # --- Extract Duration ---
        duration = 60
        dur_match = re.search(r'(\d+)\s*(?:min(?:ute)?s?|hour|hr)', task_lower)
        if dur_match:
            val = int(dur_match.group(1))
            if "hour" in task_lower or "hr" in task_lower:
                duration = val * 60
            else:
                duration = val

        # --- Extract Title ---
        title = "Team Meeting"
        title_patterns = [
            r'(?:schedule|book|create|set up)\s+(?:a\s+)?(.+?)(?:\s+(?:tomorrow|today|on|at|with|for)\b)',
            r'(?:schedule|book|create|set up)\s+(?:a\s+)?(.+)',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, task_input, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Clean up
                candidate = re.sub(r'\s+(at|on|with|for|tomorrow|today)\b.*', '', candidate, flags=re.IGNORECASE).strip()
                if len(candidate) > 3 and len(candidate) < 80:
                    title = candidate.title()
                break

        logger.info(f"Extracted: title='{title}', date={date_str}, time={time_str}, "
                     f"attendees={attendees}, duration={duration}min")

        return MeetingDetails(
            title=title,
            date=date_str,
            time=time_str,
            duration_minutes=duration,
            attendees=attendees,
            description=f"Meeting scheduled by AI Agent: {task_input}",
        )

    def create_execution_plan(self, meeting_details: MeetingDetails) -> List[AgentStep]:
        """Create ordered list of execution steps."""
        steps = [
            AgentStep(
                step_number=1,
                action="extract_details",
                description="Extracting meeting details from input",
                status=StepStatus.SUCCESS,  # Already done
            ),
            AgentStep(
                step_number=2,
                action="check_availability",
                description=f"Checking Google Calendar availability for {meeting_details.date} at {meeting_details.time}",
            ),
            AgentStep(
                step_number=3,
                action="create_event",
                description=f"Creating event '{meeting_details.title}' in Google Calendar",
            ),
            AgentStep(
                step_number=4,
                action="send_notification",
                description="Sending notification to attendees",
            ),
        ]
        return steps


# Singleton
planner = TaskPlanner()
