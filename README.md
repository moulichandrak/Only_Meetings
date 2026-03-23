# 🤖 Only_Meetings: Real-Time Autonomous AI Agent

**Live Demo**: [https://only-meetings.onrender.com/](https://only-meetings.onrender.com/)

Only_Meetings is a powerful, autonomous AI agent designed to handle the entire lifecycle of meeting coordination. From understanding a natural language request like *"Schedule a 30-min sync tomorrow at 10 AM"* to verifying calendar availability, create events with Google Meet links, and notifying the team via Gmail or Slack—this agent handles it all in real-time.

---

## 🚀 How It Works (The "How")

The agent is built with a modular architecture that mimics human reasoning and task execution:

1.  **Task Planner (The Brain)**: Uses a rule-based NLP engine to decompose a simple user request into a multi-step execution plan. It extracts the title, date, time, attendees, and duration.
2.  **Reasoning Engine (The Logic)**: Evaluates the results of each step. If a conflict is found (e.g., the requested time is busy), the Reasoning Engine decides to look for the next available slot automatically.
3.  **Execution Engine (The Hands)**: Orchestrates calls to real-world APIs (Google Calendar, Gmail, Slack) using asynchronous Python (FastAPI). It streams live logs to the frontend via **Server-Sent Events (SSE)**.
4.  **Real-Time Feedback**: Every action taken by the agent is logged and displayed on a premium glassmorphic dashboard, giving the user a "live view" into the agent's thought process.

---

## 🧠 Why We Built This (The "Why")

*   **Eliminate Coordination Friction**: Manual scheduling requires checking calendars, manually creating links, and sending separate emails. Only_Meetings reduces this 10-minute task to 10 seconds.
*   **Real-World Integration**: Unlike many AI demos that use mock data, this agent is built with production-ready OAuth 2.0 flows and direct API integrations.
*   **Autonomous Decision-Making**: The agent doesn't just fail if a slot is busy; it reasons about the failure and attempts to find a solution (the next free slot) on its own.
*   **Premium Experience**: We wanted a scheduling tool that *looks* as smart as it *is*. The UI features a modern, dark-themed dashboard with real-time progress indicators.

---

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI, Uvicorn
*   **Frontend**: Vanilla HTML/CSS/JS (Glassmorphic Design, SSE)
*   **APIs**: Google Calendar API, Gmail API, Slack SDK
*   **Security**: OAuth 2.0, SSL/TLS, Environment Variable Protection
*   **Deployment**: Render (High Performance)

---

## ⚙️ Local Setup

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/moulichandrak/Only_Meetings.git
    cd Only_Meetings
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment**:
    *   Create a `.env` file based on `.env.example`.
    *   Obtain `credentials.json` from the [Google Cloud Console](https://console.cloud.google.com).
4.  **Run the Server**:
    ```bash
    uvicorn main:app --reload --port 8000
    ```

---

## 👨‍💻 Author
**moulichandra8008** — [GitHub Profile](https://github.com/moulichandrak)

---

> [!NOTE]
> This project was developed as a demonstration of autonomous multi-step agent capabilities. It highlights the integration of LLM-style task decomposition with reliable software engineering patterns.
