"""Tool Manager - registry pattern for dispatching tool calls."""

import logging
from typing import Dict, Any, Callable
from tools.calendar_tool import check_availability, create_event, find_next_available_slot
from tools.gmail_tool import send_notification
from tools.slack_tool import send_slack_message

logger = logging.getLogger("tools.manager")


class ToolManager:
    """Registry of available tools. Maps tool names to async callable functions."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {
            "check_availability": check_availability,
            "create_event": create_event,
            "find_next_available_slot": find_next_available_slot,
            "send_gmail_notification": send_notification,
            "send_slack_message": send_slack_message,
        }

    def list_tools(self) -> list:
        return list(self._tools.keys())

    async def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with the given arguments."""
        if tool_name not in self._tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        logger.info(f"Executing tool: {tool_name}")
        try:
            result = await self._tools[tool_name](**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"success": False, "error": str(e)}


# Singleton
tool_manager = ToolManager()
