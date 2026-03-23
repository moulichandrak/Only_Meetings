"""Google Calendar Tool - check availability, create events, find slots."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from googleapiclient.discovery import build
from tools.google_auth import get_credentials
from dateutil import parser as date_parser

logger = logging.getLogger("tools.calendar")


def _get_calendar_service():
    """Build Google Calendar API service."""
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)


def _parse_datetime(date_str: str, time_str: str, timezone: str = "Asia/Kolkata") -> datetime:
    """Parse date and time strings into a datetime object."""
    combined = f"{date_str} {time_str}"
    try:
        return date_parser.parse(combined)
    except (ValueError, TypeError):
        # Fallback
        return datetime.fromisoformat(f"{date_str}T10:00:00")


async def check_availability(
    date_str: str,
    time_str: str,
    duration_minutes: int = 60,
    attendees: List[str] = None,
    timezone: str = "Asia/Kolkata",
) -> Dict[str, Any]:
    """Check if the time slot is available on Google Calendar.

    Returns:
        {"success": True, "available": True/False, "busy_slots": [...]}
    """
    try:
        service = _get_calendar_service()

        start_dt = _parse_datetime(date_str, time_str, timezone)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Build FreeBusy request
        items = [{"id": "primary"}]
        if attendees:
            items.extend([{"id": email} for email in attendees])

        body = {
            "timeMin": start_dt.isoformat() + "+05:30",
            "timeMax": end_dt.isoformat() + "+05:30",
            "timeZone": timezone,
            "items": items,
        }

        result = service.freebusy().query(body=body).execute()

        # Check all calendars for busy slots
        busy_slots = []
        calendars = result.get("calendars", {})
        for cal_id, cal_data in calendars.items():
            busy = cal_data.get("busy", [])
            if busy:
                busy_slots.extend(busy)

        available = len(busy_slots) == 0

        logger.info(f"Availability check: {'Available' if available else 'Busy'} "
                     f"for {date_str} {time_str}")

        return {
            "success": True,
            "available": available,
            "busy_slots": busy_slots,
            "checked_time": f"{date_str} {time_str}",
        }

    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        return {"success": False, "error": str(e)}


async def create_event(
    title: str,
    date_str: str,
    time_str: str,
    duration_minutes: int = 60,
    attendees: List[str] = None,
    description: str = "",
    timezone: str = "Asia/Kolkata",
) -> Dict[str, Any]:
    """Create a Google Calendar event with Google Meet conferencing.

    Returns:
        {"success": True, "event_link": "...", "meet_link": "...", "event_id": "..."}
    """
    try:
        service = _get_calendar_service()

        start_dt = _parse_datetime(date_str, time_str, timezone)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        event_body = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": timezone,
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": f"agent-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 30},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",
        ).execute()

        event_link = event.get("htmlLink", "")
        meet_link = ""
        conference_data = event.get("conferenceData", {})
        entry_points = conference_data.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                meet_link = ep.get("uri", "")
                break

        logger.info(f"Event created: {title} at {date_str} {time_str}")
        logger.info(f"Event link: {event_link}")
        logger.info(f"Meet link: {meet_link}")

        return {
            "success": True,
            "event_id": event.get("id"),
            "event_link": event_link,
            "meet_link": meet_link,
            "scheduled_time": start_dt.isoformat(),
            "attendees": attendees or [],
        }

    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        return {"success": False, "error": str(e)}


async def find_next_available_slot(
    date_str: str,
    time_str: str,
    duration_minutes: int = 60,
    attendees: List[str] = None,
    timezone: str = "Asia/Kolkata",
    max_attempts: int = 16,
) -> Dict[str, Any]:
    """Find the next available slot by iterating 30-minute windows.

    Returns:
        {"success": True, "date": "...", "time": "...", "slot_start": "..."}
    """
    start_dt = _parse_datetime(date_str, time_str, timezone)

    for i in range(max_attempts):
        candidate = start_dt + timedelta(minutes=30 * (i + 1))
        candidate_date = candidate.strftime("%Y-%m-%d")
        candidate_time = candidate.strftime("%I:%M %p")

        result = await check_availability(
            candidate_date, candidate_time, duration_minutes, attendees, timezone
        )

        if result.get("success") and result.get("available"):
            logger.info(f"Found available slot: {candidate_date} {candidate_time}")
            return {
                "success": True,
                "date": candidate_date,
                "time": candidate_time,
                "slot_start": candidate.isoformat(),
            }

    return {
        "success": False,
        "error": f"No available slots found in the next {max_attempts * 30} minutes",
    }
