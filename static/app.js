/* ── AI Agent Frontend — SSE Client & Log Rendering ── */

let eventSource = null;
let logCount = 0;

// ── Auth Status Check ──
async function checkAuth() {
    const statusEl = document.getElementById('authStatus');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    try {
        const res = await fetch('/auth/status');
        const data = await res.json();

        if (data.authenticated) {
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
            statusEl.onclick = null;
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Sign in with Google';
            statusEl.onclick = () => window.location.href = '/auth/google';
        }
    } catch {
        dot.className = 'status-dot disconnected';
        text.textContent = 'Offline';
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
    if (data.meeting_link) {
        linkEl.textContent = data.meeting_link;
        linkEl.href = data.meeting_link;
    } else {
        linkEl.textContent = 'No link available';
        linkEl.href = '#';
    }

    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
