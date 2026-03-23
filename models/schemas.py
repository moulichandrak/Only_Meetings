"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskRequest(BaseModel):
    task: str = Field(..., description="Natural language task description", example="Schedule meeting tomorrow at 10 AM with team")


class MeetingDetails(BaseModel):
    title: str = "Team Meeting"
    date: Optional[str] = None
    time: Optional[str] = None
    duration_minutes: int = 60
    attendees: List[str] = Field(default_factory=list)
    description: str = ""
    timezone: str = "Asia/Kolkata"


class AgentStep(BaseModel):
    step_number: int
    action: str
    description: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    timestamp: Optional[str] = None


class TaskResponse(BaseModel):
    status: str = "success"
    task_id: str = ""
    meeting_link: Optional[str] = None
    scheduled_time: Optional[str] = None
    notifications_sent: bool = False
    steps: List[AgentStep] = Field(default_factory=list)
    error: Optional[str] = None


class LogEvent(BaseModel):
    """SSE log event sent to the frontend."""
    event_type: str  # "step_start", "step_complete", "step_error", "result"
    step_number: Optional[int] = None
    message: str
    data: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
