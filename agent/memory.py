"""Agent Memory - stores meeting details, intermediate results, and task state."""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from models.schemas import MeetingDetails, AgentStep, StepStatus


class AgentMemory:
    """In-memory store for agent task state, keyed by task_id."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def create_task(self, task_description: str) -> str:
        """Create a new task entry and return its ID."""
        task_id = str(uuid.uuid4())[:8]
        self._store[task_id] = {
            "task_id": task_id,
            "task_description": task_description,
            "meeting_details": None,
            "steps": [],
            "current_step": 0,
            "status": "running",
            "meeting_link": None,
            "scheduled_time": None,
            "notifications_sent": False,
            "created_at": datetime.now().isoformat(),
            "error": None,
        }
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(task_id)

    def set_meeting_details(self, task_id: str, details: MeetingDetails):
        if task_id in self._store:
            self._store[task_id]["meeting_details"] = details.model_dump()

    def add_step(self, task_id: str, step: AgentStep):
        if task_id in self._store:
            self._store[task_id]["steps"].append(step.model_dump())

    def update_step(self, task_id: str, step_number: int, status: StepStatus, result: str = None):
        if task_id in self._store:
            for step in self._store[task_id]["steps"]:
                if step["step_number"] == step_number:
                    step["status"] = status.value
                    step["result"] = result
                    step["timestamp"] = datetime.now().isoformat()
                    break

    def set_result(self, task_id: str, meeting_link: str = None, scheduled_time: str = None,
                   notifications_sent: bool = False):
        if task_id in self._store:
            self._store[task_id]["meeting_link"] = meeting_link
            self._store[task_id]["scheduled_time"] = scheduled_time
            self._store[task_id]["notifications_sent"] = notifications_sent
            self._store[task_id]["status"] = "success"

    def set_error(self, task_id: str, error: str):
        if task_id in self._store:
            self._store[task_id]["error"] = error
            self._store[task_id]["status"] = "failed"

    def get_meeting_details(self, task_id: str) -> Optional[dict]:
        task = self.get_task(task_id)
        return task.get("meeting_details") if task else None


# Singleton instance
memory = AgentMemory()
