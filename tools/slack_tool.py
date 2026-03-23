"""Slack Tool - send meeting notifications to Slack channels or users."""

import os
import logging
from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger("tools.slack")


def _get_slack_client() -> WebClient:
    """Create Slack WebClient with bot token."""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN not set in environment variables")
    return WebClient(token=token)


def _format_meeting_blocks(
    meeting_title: str,
    meeting_time: str,
    meeting_link: str,
    meet_link: str = "",
) -> list:
    """Create Slack Block Kit message for meeting notification."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📅 {meeting_title}",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*🕐 When:*\n{meeting_time}",
                },
                {
                    "type": "mrkdwn",
                    "text": "*📍 Where:*\nGoogle Meet",
                },
            ],
        },
    ]

    actions = []
    if meet_link:
        actions.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "🎥 Join Meet", "emoji": True},
            "url": meet_link,
            "style": "primary",
        })

    if meeting_link:
        actions.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "📅 View Calendar", "emoji": True},
            "url": meeting_link,
        })

    if actions:
        blocks.append({"type": "actions", "elements": actions})

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "Scheduled by AI Agent 🤖",
            }
        ],
    })

    return blocks


async def send_slack_message(
    meeting_title: str,
    meeting_time: str,
    meeting_link: str,
    meet_link: str = "",
    channel: str = None,
) -> Dict[str, Any]:
    """Send a meeting notification to a Slack channel.

    Returns:
        {"success": True, "channel": "...", "ts": "..."}
    """
    try:
        client = _get_slack_client()
        target_channel = channel or os.getenv("SLACK_CHANNEL", "#general")

        blocks = _format_meeting_blocks(
            meeting_title, meeting_time, meeting_link, meet_link
        )

        response = client.chat_postMessage(
            channel=target_channel,
            text=f"📅 Meeting: {meeting_title} at {meeting_time}",
            blocks=blocks,
        )

        logger.info(f"Slack message sent to {target_channel}")

        return {
            "success": True,
            "channel": target_channel,
            "ts": response.get("ts"),
            "message": f"Notification sent to {target_channel}",
        }

    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        return {"success": False, "error": e.response["error"]}
    except Exception as e:
        logger.error(f"Slack error: {e}")
        return {"success": False, "error": str(e)}
