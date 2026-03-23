"""FastAPI Application - Real-Time Autonomous Multi-Step AI Agent."""

import os
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from models.schemas import TaskRequest, LogEvent
from agent.executor import executor
from agent.memory import memory
from tools.google_auth import get_oauth_flow, save_credentials_from_flow, is_authenticated

# ── Load Environment ──
load_dotenv()

# ── Logging Setup ──
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("main")

# ── FastAPI App ──
app = FastAPI(
    title="AI Agent - Meeting Scheduler",
    description="Real-time autonomous multi-step AI agent for booking meetings and notifying teams",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Routes ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend UI."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>AI Agent</h1><p>Frontend not found. Place index.html in /static/</p>")


@app.get("/auth/status")
async def auth_status():
    """Check if Google OAuth is authenticated."""
    authenticated = is_authenticated()
    return {"authenticated": authenticated}


@app.get("/auth/google")
async def google_auth():
    """Initiate Google OAuth 2.0 flow."""
    try:
        flow = get_oauth_flow()
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        logger.info(f"OAuth flow initiated. Redirecting to Google...")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"OAuth initiation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


@app.get("/auth/google/callback")
async def google_callback(code: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        return HTMLResponse(
            content=f"""
            <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#1a1a2e;color:white;">
            <h1>❌ Authentication Failed</h1><p>{error}</p>
            <a href="/" style="color:#667eea;">← Back to Agent</a>
            </body></html>
            """,
            status_code=400,
        )

    if not code:
        return HTMLResponse(
            content="<h1>Missing authorization code</h1>",
            status_code=400,
        )

    try:
        flow = get_oauth_flow()
        save_credentials_from_flow(flow, code)
        logger.info("Google OAuth successful!")

        return HTMLResponse(content="""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#1a1a2e;color:white;">
        <h1>✅ Authentication Successful!</h1>
        <p style="color:#aaa;">Google Calendar and Gmail are now connected.</p>
        <a href="/" style="display:inline-block;margin-top:20px;padding:12px 30px;
        background:linear-gradient(135deg,#667eea,#764ba2);color:white;text-decoration:none;
        border-radius:8px;font-weight:bold;">🚀 Start Using Agent</a>
        </body></html>
        """)
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        return HTMLResponse(
            content=f"""
            <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#1a1a2e;color:white;">
            <h1>❌ Authentication Error</h1><p>{str(e)}</p>
            <a href="/auth/google" style="color:#667eea;">Try Again</a>
            </body></html>
            """,
            status_code=500,
        )


@app.post("/run-task")
async def run_task(request: TaskRequest):
    """Execute a task and stream real-time logs via SSE.

    Input: {"task": "Schedule meeting tomorrow at 10 AM with team"}
    Returns: Server-Sent Events stream with step-by-step logs.
    """
    logger.info(f"Task received: {request.task}")

    if not is_authenticated():
        return JSONResponse(
            status_code=401,
            content={
                "error": "Not authenticated. Please visit /auth/google first.",
                "auth_url": "/auth/google",
            },
        )

    async def event_stream():
        try:
            async for log_event in executor.run_task(request.task):
                event_data = log_event.model_dump()
                yield {
                    "event": log_event.event_type,
                    "data": json.dumps(event_data),
                }
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            yield {
                "event": "task_error",
                "data": json.dumps({
                    "event_type": "task_error",
                    "message": f"❌ Agent error: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }),
            }

    return EventSourceResponse(event_stream())


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a running or completed task."""
    task = memory.get_task(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "authenticated": is_authenticated(),
        "timestamp": datetime.now().isoformat(),
    }


# ── Run ──
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8000)))
    uvicorn.run("main:app", host=host, port=port, reload=True)
