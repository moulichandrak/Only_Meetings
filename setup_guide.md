# Setting Up Google Cloud for AI Agent

To use the Google Calendar and Gmail APIs, you need to create OAuth 2.0 credentials in the Google Cloud Console.

## Step 1: Create a Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top and click **New Project**
3. Name it (e.g., "AI Agent Scheduler") and click **Create**

## Step 2: Enable APIs
1. In your new project, go to **APIs & Services** > **Library**
2. Search for **Google Calendar API** and click **Enable**
3. Search for **Gmail API** and click **Enable**

## Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (or Internal if you have a Google Workspace) and click **Create**
3. Fill in the required fields:
   - App name: AI Agent Server
   - User support email: (your email)
   - Developer contact email: (your email)
4. Click **Save and Continue**
5. On the **Scopes** screen, click **Add or Remove Scopes** and manually paste these:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/gmail.send`
6. Click **Save and Continue**
7. On the **Test users** screen, add your own email address (important for testing).
8. Click **Save and Continue**

## Step 4: Create OAuth Credentials
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Application type: **Web application**
4. Name: "FastAPI Client"
5. **Authorized redirect URIs**: Add `http://localhost:8000/auth/google/callback`
6. Click **Create**
7. **Important**: Download the JSON file, rename it to `credentials.json`, and place it in the root folder of this project (`project 726/`).
   - Alternatively, copy the Client ID and Client Secret into the `.env` file.

## Step 5: (Optional) Set up Slack
If you prefer Slack over Gmail for notifications:
1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create an app
2. Go to **OAuth & Permissions**
3. Add these Bot Token Scopes: `chat:write`
4. Install it to your workspace
5. Copy the Bot User OAuth Token (`xoxb-...`) to `.env`
6. Change `NOTIFICATION_METHOD=slack` in `.env`

## Step 6: Start the Server
1. Make sure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
3. Open http://localhost:8000 in your browser
4. Click **Sign in with Google** to authorize the agent!
