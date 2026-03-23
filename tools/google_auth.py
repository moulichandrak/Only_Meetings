"""Google OAuth 2.0 authentication for Calendar and Gmail APIs."""

import os
import json
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

logger = logging.getLogger("tools.google_auth")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def get_oauth_flow(redirect_uri: str = None) -> Flow:
    """Create OAuth flow from credentials.json or environment variables."""
    creds_path = Path(CREDENTIALS_FILE)

    if creds_path.exists():
        flow = Flow.from_client_secrets_file(
            str(creds_path),
            scopes=SCOPES,
            redirect_uri=redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback"),
        )
    else:
        # Build from environment variables
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError(
                "Google OAuth credentials not found. Either place credentials.json "
                "in the project root or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
            )

        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")
                ],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback"),
        )

    return flow


def get_credentials() -> Credentials:
    """Get valid Google API credentials, refreshing if needed."""
    creds = None
    token_path = Path(TOKEN_FILE)

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token.json: {e}")
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
            _save_credentials(creds)
        except Exception as e:
            logger.warning(f"Failed to refresh token: {e}")
            creds = None

    if not creds or not creds.valid:
        raise ValueError(
            "No valid Google credentials. Please authenticate via http://localhost:8001/auth/google"
        )

    return creds


def save_credentials_from_flow(flow: Flow, code: str) -> Credentials:
    """Exchange authorization code for credentials and save."""
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_credentials(creds)
    logger.info("Google credentials saved successfully")
    return creds


def _save_credentials(creds: Credentials):
    """Save credentials to token.json."""
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes and list(creds.scopes),
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def is_authenticated() -> bool:
    """Check if we have valid credentials."""
    try:
        get_credentials()
        return True
    except (ValueError, Exception):
        return False
