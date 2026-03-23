"""Gmail Tool - send notification emails via Gmail API."""

import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from googleapiclient.discovery import build
from tools.google_auth import get_credentials

logger = logging.getLogger("tools.gmail")


def _get_gmail_service():
    """Build Gmail API service."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def _create_meeting_email(
    to: str,
    subject: str,
    meeting_title: str,
    meeting_time: str,
    meeting_link: str,
    meet_link: str = "",
) -> str:
    """Create a professional HTML email for meeting notification."""
    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">📅 Meeting Invitation</h1>
        </div>
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 12px 12px;">
            <h2 style="color: #333; margin-top: 0;">{meeting_title}</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0; color: #555;">
                    <strong>🕐 When:</strong> {meeting_time}
                </p>
                <p style="margin: 5px 0; color: #555;">
                    <strong>📍 Where:</strong> Google Meet
                </p>
            </div>
            {"<a href='" + meet_link + "' style='display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;'>🎥 Join Google Meet</a><br><br>" if meet_link else ""}
            <a href="{meeting_link}" style="display: inline-block; background: #f0f0f0; color: #333; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold;">📅 View in Calendar</a>
            <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
            <p style="color: #999; font-size: 12px; margin: 0;">
                This meeting was scheduled by AI Agent. If you have questions, please contact the organizer.
            </p>
        </div>
    </div>
    """

    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject

    # Plain text fallback
    plain_text = f"""
Meeting Invitation: {meeting_title}

When: {meeting_time}
Where: Google Meet

{"Join Meeting: " + meet_link if meet_link else ""}
View in Calendar: {meeting_link}

This meeting was scheduled by AI Agent.
    """
    message.attach(MIMEText(plain_text, "plain"))
    message.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


async def send_notification(
    to_emails: List[str],
    meeting_title: str,
    meeting_time: str,
    meeting_link: str,
    meet_link: str = "",
) -> Dict[str, Any]:
    """Send meeting notification emails to all attendees.

    Returns:
        {"success": True, "sent_to": [...], "failed": [...]}
    """
    try:
        service = _get_gmail_service()

        sent_to = []
        failed = []

        subject = f"📅 Meeting Invitation: {meeting_title}"

        for email in to_emails:
            try:
                raw_message = _create_meeting_email(
                    to=email,
                    subject=subject,
                    meeting_title=meeting_title,
                    meeting_time=meeting_time,
                    meeting_link=meeting_link,
                    meet_link=meet_link,
                )

                service.users().messages().send(
                    userId="me",
                    body={"raw": raw_message},
                ).execute()

                sent_to.append(email)
                logger.info(f"Email sent to {email}")

            except Exception as e:
                logger.warning(f"Failed to send email to {email}: {e}")
                failed.append({"email": email, "error": str(e)})

        if sent_to:
            return {
                "success": True,
                "sent_to": sent_to,
                "failed": failed,
                "message": f"Notifications sent to {len(sent_to)} recipient(s)",
            }
        else:
            return {
                "success": False,
                "error": "Failed to send any emails",
                "failed": failed,
            }

    except Exception as e:
        logger.error(f"Gmail service error: {e}")
        return {"success": False, "error": str(e)}
