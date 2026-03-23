/* ── AI Agent Frontend — SSE Client & Log Rendering ── */

let eventSource = null;
let logCount = 0;

// ── Auth Status Check ──
// ── Auth & Guidance Logic ──
async function checkAuth() {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    const guideContent = document.getElementById('guideContent');

    try {
        const res = await fetch('/auth/status');
        const data = await res.json();

        if (data.authenticated) {
            dot.className = 'status-dot connected';
            text.textContent = 'System Connected';
            
            // Show Step 2: Command the Agent
            guideContent.innerHTML = `
                <div class="guide-step reveal">
                    <div class="guide-tag">Step 2</div>
                    <h3>Start Scheduling</h3>
                    <p><strong>Only Meeting</strong> is ready to handle your calendar. Enter a task below to begin the autonomous execution pipeline.</p>
                    <div class="quick-actions" style="margin-top: 0;">
                        <button class="quick-btn" onclick="setTask('Schedule a quick 15min catchup tomorrow at 11am')">📅 Sync tomorrow 11am</button>
                        <button class="quick-btn" onclick="setTask('Book a project review next Friday at 3pm with team')">📋 Friday 3pm</button>
                    </div>
                </div>
            `;
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Sign in required';
            
            // Show Step 1: Secure Connection
            guideContent.innerHTML = `
                <div class="guide-step reveal">
                    <div class="guide-tag">Step 1</div>
                    <h3>Secure Connection Required</h3>
                    <p>To allow <strong>Only Meeting</strong> to manage your schedule, please connect your account. Since this is a specialized agent, click <strong>Advanced</strong> → <strong>Go to Only Meeting (unsafe)</strong> during authorization.</p>
                    <button class="auth-btn-primary" onclick="window.location.href='/auth/google'">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                        Connect with Google
                    </button>
                </div>
            `;
        }
    } catch {
        dot.className = 'status-dot disconnected';
        text.textContent = 'System Offline';
    }
}

// ── Set Task from Quick Actions ──
function setTask(text) {
    document.getElementById('taskInput').value = text;
    document.getElementById('taskInput').focus();
}

// ── Clear Logs ──
function clearLogs() {
    const panel = document.getElementById('logPanel');
    panel.innerHTML = `
        <div class="log-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
            </svg>
            <p>Waiting for task execution...</p>
        </div>
    `;
    logCount = 0;
    document.getElementById('logCounter').textContent = '0 events';
    resetSteps();
    document.getElementById('resultCard').style.display = 'none';
}

// ── Reset Step Indicators ──
function resetSteps() {
    document.querySelectorAll('.step-indicator').forEach(el => {
        el.className = 'step-indicator pending';
    });
    document.querySelectorAll('.step-connector').forEach(el => {
        el.classList.remove('active');
    });
}

// ── Update Step Indicator ──
function updateStep(stepNum, state) {
    const stepItem = document.querySelector(`.step-item[data-step="${stepNum}"]`);
    if (!stepItem) return;

    const indicator = stepItem.querySelector('.step-indicator');
    indicator.className = `step-indicator ${state}`;

    if (state === 'success' || state === 'running') {
        // Activate connector above this step
        const connectors = document.querySelectorAll('.step-connector');
        if (stepNum > 1 && connectors[stepNum - 2]) {
            connectors[stepNum - 2].classList.add('active');
        }
    }

    // Replace number with icon for success/error
    const numEl = indicator.querySelector('.step-num');
    if (state === 'success') {
        numEl.textContent = '✓';
    } else if (state === 'error') {
        numEl.textContent = '✗';
    } else if (state === 'running') {
        numEl.textContent = stepNum;
    }
}

// ── Add Log Entry ──
function addLog(eventType, message) {
    const panel = document.getElementById('logPanel');
    const emptyMsg = panel.querySelector('.log-empty');
    if (emptyMsg) emptyMsg.remove();

    const entry = document.createElement('div');
    entry.className = 'log-entry';

    const time = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    entry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-msg ${eventType}">${escapeHtml(message)}</span>
    `;

    panel.appendChild(entry);
    panel.scrollTop = panel.scrollHeight;

    logCount++;
    document.getElementById('logCounter').textContent = `${logCount} events`;
}

// ── Escape HTML ──
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Show Result Card ──
function showResult(data) {
    const card = document.getElementById('resultCard');
    card.style.display = 'block';

    document.getElementById('resultStatus').textContent = data.status || 'Success';
    document.getElementById('resultTime').textContent = data.scheduled_time
        ? new Date(data.scheduled_time).toLocaleString()
        : 'N/A';
    document.getElementById('resultNotif').textContent =
        data.notifications_sent ? '✅ Sent' : '⚠️ Not sent';

    const linkEl = document.getElementById('resultLink');
    const resultBody = card.querySelector('.result-body');
    
    // Remove existing copy button if any
    const oldBtn = resultBody.querySelector('.copy-btn');
    if (oldBtn) oldBtn.remove();

    if (data.meeting_link) {
        linkEl.textContent = data.meeting_link;
        linkEl.href = data.meeting_link;
        
        // Add Copy Button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            Copy Link
        `;
        copyBtn.onclick = () => copyToClipboard(data.meeting_link, copyBtn);
        linkEl.parentNode.appendChild(copyBtn);
    } else {
        linkEl.textContent = 'No link available';
        linkEl.href = '#';
    }

    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ── Copy to Clipboard ──
function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.classList.remove('copied');
        }, 2000);
    });
}

// ── Run Task (SSE) ──
async function runTask() {
    const input = document.getElementById('taskInput').value.trim();
    if (!input) {
        document.getElementById('taskInput').focus();
        return;
    }

    // Reset UI
    clearLogs();
    const btn = document.getElementById('runBtn');
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        // Check auth first
        const authRes = await fetch('/auth/status');
        const authData = await authRes.json();
        if (!authData.authenticated) {
            addLog('task-error', '❌ Not authenticated. Redirecting to Google Sign-in...');
            setTimeout(() => window.location.href = '/auth/google', 1500);
            return;
        }

        // Use fetch with ReadableStream for SSE via POST
        const response = await fetch('/run-task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task: input })
        });

        if (!response.ok) {
            const err = await response.json();
            addLog('task_error', `❌ ${err.error || 'Request failed'}`);
            if (err.auth_url) {
                setTimeout(() => window.location.href = err.auth_url, 1500);
            }
            return;
        }

        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line

            let currentEvent = '';

            for (const line of lines) {
                if (line.startsWith('event:')) {
                    currentEvent = line.substring(6).trim();
                } else if (line.startsWith('data:')) {
                    const dataStr = line.substring(5).trim();
                    try {
                        const data = JSON.parse(dataStr);
                        handleEvent(currentEvent || data.event_type, data);
                    } catch {
                        // Not JSON, skip
                    }
                }
            }
        }
    } catch (err) {
        addLog('task_error', `❌ Connection error: ${err.message}`);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ── Handle SSE Event ──
function handleEvent(eventType, data) {
    addLog(eventType.replace(/_/g, '-'), data.message);

    switch (eventType) {
        case 'step_start':
            if (data.step_number) updateStep(data.step_number, 'running');
            break;

        case 'step_complete':
            if (data.step_number) updateStep(data.step_number, 'success');
            break;

        case 'step_error':
            if (data.step_number) updateStep(data.step_number, 'error');
            break;

        case 'step_info':
            // Info log, no step change needed
            break;

        case 'task_complete':
            if (data.data) showResult(data.data);
            break;

        case 'task_error':
            // Error already logged
            break;
    }
}

// ── Enter key to Run ──
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    document.getElementById('taskInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') runTask();
    });
});
