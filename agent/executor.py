"""Execution Engine - orchestrates step-by-step agent execution with SSE streaming."""

import os
import logging
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from models.schemas import MeetingDetails, AgentStep, StepStatus, LogEvent
from agent.memory import memory
from agent.planner import planner
from agent.reasoning import reasoning_engine
from agent.feedback import feedback_handler
from tools.tool_manager import tool_manager

logger = logging.getLogger("agent.executor")


class ExecutionEngine:
    """Runs agent steps sequentially, yielding SSE log events."""

    async def run_task(self, task_input: str) -> AsyncGenerator[LogEvent, None]:
        """Execute a full task pipeline, yielding real-time log events.

        Pipeline:
        1. Extract meeting details from input
        2. Check Google Calendar availability
        3. Create event in Google Calendar
        4. Send notification via Gmail or Slack
        """
        task_id = memory.create_task(task_input)

        yield LogEvent(
            event_type="task_start",
            message=f"🚀 Task started: {task_input}",
            data={"task_id": task_id},
        )

        # ── Step 1: Extract Details ──
        yield LogEvent(
            event_type="step_start",
            step_number=1,
            message="[Step 1] Extracting meeting details from input...",
        )

        try:
            details = planner.extract_meeting_details(task_input)
            memory.set_meeting_details(task_id, details)
            steps = planner.create_execution_plan(details)
            for step in steps:
                memory.add_step(task_id, step)

            memory.update_step(task_id, 1, StepStatus.SUCCESS,
                               f"Title: {details.title}, Date: {details.date}, Time: {details.time}, "
                               f"Attendees: {details.attendees}, Duration: {details.duration_minutes}min")

            yield LogEvent(
                event_type="step_complete",
                step_number=1,
                message=f"✅ [Step 1] Details extracted: {details.title} on {details.date} at {details.time}",
                data=details.model_dump(),
            )
        except Exception as e:
            memory.set_error(task_id, str(e))
            yield LogEvent(event_type="step_error", step_number=1, message=f"❌ [Step 1] Failed: {str(e)}")
            yield LogEvent(event_type="task_error", message=f"❌ Task failed: {str(e)}", data={"task_id": task_id})
            return

        await asyncio.sleep(0.3)

        # ── Step 2: Check Availability ──
        yield LogEvent(
            event_type="step_start",
            step_number=2,
            message=f"[Step 2] Checking Google Calendar availability for {details.date} at {details.time}...",
        )

        try:
            availability = await feedback_handler.execute_with_retry(
                tool_manager.execute,
                "check_availability",
                date_str=details.date,
                time_str=details.time,
                duration_minutes=details.duration_minutes,
                attendees=details.attendees,
            )

            decision, context = reasoning_engine.evaluate_step_result(
                steps[1], availability
            )

            if decision == "reschedule":
                yield LogEvent(
                    event_type="step_info",
                    step_number=2,
                    message=f"⚠️ [Step 2] Slot busy. Finding next available slot...",
                )

                next_slot = await feedback_handler.execute_with_retry(
                    tool_manager.execute,
                    "find_next_available_slot",
                    date_str=details.date,
                    time_str=details.time,
                    duration_minutes=details.duration_minutes,
                    attendees=details.attendees,
                )

                if next_slot.get("success"):
                    details.date = next_slot["date"]
                    details.time = next_slot["time"]
                    memory.set_meeting_details(task_id, details)

                    yield LogEvent(
                        event_type="step_info",
                        step_number=2,
                        message=f"🔄 [Step 2] Rescheduled to {details.date} at {details.time}",
                    )
                else:
                    raise Exception(next_slot.get("error", "No available slots found"))

            elif decision == "fail":
                raise Exception(context.get("error", "Availability check failed"))

            memory.update_step(task_id, 2, StepStatus.SUCCESS,
                               f"Slot available: {details.date} at {details.time}")

            yield LogEvent(
                event_type="step_complete",
                step_number=2,
                message=f"✅ [Step 2] Slot available: {details.date} at {details.time}",
                data=availability,
            )
        except Exception as e:
            memory.update_step(task_id, 2, StepStatus.FAILED, str(e))
            memory.set_error(task_id, str(e))
            yield LogEvent(event_type="step_error", step_number=2, message=f"❌ [Step 2] Failed: {str(e)}")
            yield LogEvent(event_type="task_error", message=f"❌ Task failed: {str(e)}", data={"task_id": task_id})
            return

        await asyncio.sleep(0.3)

        # ── Step 3: Create Event ──
        yield LogEvent(
            event_type="step_start",
            step_number=3,
            message=f"[Step 3] Creating event '{details.title}' in Google Calendar...",
        )

        try:
            event_result = await feedback_handler.execute_with_retry(
                tool_manager.execute,
                "create_event",
                title=details.title,
                date_str=details.date,
                time_str=details.time,
                duration_minutes=details.duration_minutes,
                attendees=details.attendees,
                description=details.description,
            )

            decision, context = reasoning_engine.evaluate_step_result(steps[2], event_result)

            if decision == "fail":
                raise Exception(context.get("error", "Event creation failed"))
            elif decision == "retry":
                raise Exception(context.get("reason", "Event creation error"))

            meeting_link = event_result.get("event_link", "")
            meet_link = event_result.get("meet_link", "")
            scheduled_time = event_result.get("scheduled_time", "")

            memory.update_step(task_id, 3, StepStatus.SUCCESS,
                               f"Event created. Meet link: {meet_link}")

            yield LogEvent(
                event_type="step_complete",
                step_number=3,
                message=f"✅ [Step 3] Event created! Meet link: {meet_link or 'N/A'}",
                data=event_result,
            )
        except Exception as e:
            memory.update_step(task_id, 3, StepStatus.FAILED, str(e))
            memory.set_error(task_id, str(e))
            yield LogEvent(event_type="step_error", step_number=3, message=f"❌ [Step 3] Failed: {str(e)}")
            yield LogEvent(event_type="task_error", message=f"❌ Task failed: {str(e)}", data={"task_id": task_id})
            return

        await asyncio.sleep(0.3)

        # ── Step 4: Send Notification ──
        notification_method = os.getenv("NOTIFICATION_METHOD", "gmail").lower()
        yield LogEvent(
            event_type="step_start",
            step_number=4,
            message=f"[Step 4] Sending notification via {notification_method.upper()}...",
        )

        notifications_sent = False

        try:
            if notification_method == "slack":
                notif_result = await feedback_handler.execute_with_retry(
                    tool_manager.execute,
                    "send_slack_message",
                    meeting_title=details.title,
                    meeting_time=f"{details.date} at {details.time}",
                    meeting_link=meeting_link,
                    meet_link=meet_link,
                )
            else:
                # Gmail (default)
                recipients = details.attendees if details.attendees else []
                if recipients:
                    notif_result = await feedback_handler.execute_with_retry(
                        tool_manager.execute,
                        "send_gmail_notification",
                        to_emails=recipients,
                        meeting_title=details.title,
                        meeting_time=f"{details.date} at {details.time}",
                        meeting_link=meeting_link,
                        meet_link=meet_link,
                    )
                else:
                    notif_result = {
                        "success": True,
                        "message": "No attendee emails provided. Calendar invites sent via Google Calendar.",
                    }

            decision, context = reasoning_engine.evaluate_step_result(steps[3], notif_result)

            if decision == "fail":
                raise Exception(context.get("error", "Notification failed"))

            notifications_sent = notif_result.get("success", False)
            memory.update_step(task_id, 4, StepStatus.SUCCESS,
                               notif_result.get("message", "Notifications sent"))

            yield LogEvent(
                event_type="step_complete",
                step_number=4,
                message=f"✅ [Step 4] {notif_result.get('message', 'Notifications sent')}",
                data=notif_result,
            )
        except Exception as e:
            memory.update_step(task_id, 4, StepStatus.FAILED, str(e))
            yield LogEvent(
                event_type="step_error",
                step_number=4,
                message=f"⚠️ [Step 4] Notification warning: {str(e)} (meeting was still created)",
            )

        # ── Final Result ──
        memory.set_result(task_id, meeting_link=meet_link or meeting_link,
                          scheduled_time=scheduled_time, notifications_sent=notifications_sent)

        final_data = {
            "status": "success",
            "task_id": task_id,
            "meeting_link": meet_link or meeting_link,
            "scheduled_time": scheduled_time,
            "notifications_sent": notifications_sent,
        }

        yield LogEvent(
            event_type="task_complete",
            message="🎉 Task completed successfully!",
            data=final_data,
        )


# Singleton
executor = ExecutionEngine()
