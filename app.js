/* ═══════════════════════════════════════════════════════════════
   EduGuard — Frontend Logic
   Dashboard + Students + AI Chat
   ═══════════════════════════════════════════════════════════════ */

let studentsData = [];

// ── Navigation ──────────────────────────────────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        const view = link.dataset.view;
        switchView(view);
    });
});

function switchView(viewName) {
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
    document.getElementById(`view-${viewName}`).classList.add('active');
}

// ── Dashboard ───────────────────────────────────────────────────
async function loadDashboard() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();

        document.getElementById('stat-total').textContent = stats.total_students;
        document.getElementById('stat-critical').textContent = stats.critical_risk;
        document.getElementById('stat-high').textContent = stats.high_risk;
        document.getElementById('stat-dropped').textContent = stats.dropped_out;
        document.getElementById('stat-gpa').textContent = stats.avg_gpa;
        document.getElementById('stat-attendance').textContent = stats.avg_attendance + '%';

        renderRiskChart(stats.risk_distribution, stats.total_students);
        renderStatusChart(stats.status_distribution);
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

function renderRiskChart(distribution, total) {
    const container = document.getElementById('risk-chart');
    container.innerHTML = '';

    distribution.forEach(item => {
        const pct = Math.round((item.count / total) * 100);
        const row = document.createElement('div');
        row.className = 'risk-bar-row';
        row.innerHTML = `
            <span class="risk-bar-label">${item.risk_level}</span>
            <div class="risk-bar-track">
                <div class="risk-bar-fill ${item.risk_level}" style="width: 0%">${item.count} (${pct}%)</div>
            </div>
        `;
        container.appendChild(row);

        // Animate the bar
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                row.querySelector('.risk-bar-fill').style.width = Math.max(pct, 15) + '%';
            });
        });
    });
}

function renderStatusChart(distribution) {
    const container = document.getElementById('status-chart');
    container.innerHTML = '';

    distribution.forEach(item => {
        const div = document.createElement('div');
        div.className = 'status-item';
        const label = item.current_status.replace('_', ' ');
        div.innerHTML = `
            <span class="status-dot-indicator ${item.current_status}"></span>
            <span class="status-text">${label}</span>
            <span class="status-count">${item.count}</span>
        `;
        container.appendChild(div);
    });
}

// ── Students ────────────────────────────────────────────────────
async function loadStudents() {
    try {
        const res = await fetch('/api/students');
        studentsData = await res.json();
        renderStudents(studentsData);
        renderRiskStudentsList(studentsData);
    } catch (e) {
        console.error('Failed to load students:', e);
    }
}

function renderStudents(data) {
    const tbody = document.getElementById('students-tbody');
    tbody.innerHTML = '';

    data.forEach(s => {
        const tr = document.createElement('tr');
        tr.onclick = () => openStudentModal(s);

        const gpaClass = s.gpa >= 7 ? 'gpa-good' : s.gpa >= 5 ? 'gpa-mid' : 'gpa-bad';
        const attClass = s.attendance_pct >= 80 ? 'attendance-good' : s.attendance_pct >= 60 ? 'attendance-mid' : 'attendance-bad';
        const income = s.parent_income ? `₹${(s.parent_income / 1000).toFixed(0)}K` : '—';
        const factors = s.contributing_factors && s.contributing_factors !== 'none'
            ? s.contributing_factors.replace(/,/g, ', ')
            : '—';
        const statusLabel = s.current_status.replace('_', ' ');

        tr.innerHTML = `
            <td><strong>${s.name}</strong><br><span style="color:var(--text-muted);font-size:11px">${s.gender} · Age ${s.age}</span></td>
            <td>${s.grade}</td>
            <td><span class="risk-pill ${s.risk_level}">● ${s.risk_level} (${(s.risk_score * 100).toFixed(0)}%)</span></td>
            <td class="${gpaClass}">${s.gpa}</td>
            <td class="${attClass}">${s.attendance_pct}%</td>
            <td>${s.distance_from_school_km} km</td>
            <td>${income}</td>
            <td><span class="status-badge ${s.current_status}">${statusLabel}</span></td>
            <td><span class="factors-text" title="${factors}">${factors}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderRiskStudentsList(data) {
    const container = document.getElementById('risk-students-list');
    container.innerHTML = '';

    const atRisk = data.filter(s => s.risk_level === 'critical' || s.risk_level === 'high');

    if (!atRisk.length) {
        container.innerHTML = '<p style="color:var(--text-muted);padding:12px">No critical or high risk students.</p>';
        return;
    }

    atRisk.forEach(s => {
        const initials = s.name.split(' ').map(n => n[0]).join('');
        const factors = s.contributing_factors && s.contributing_factors !== 'none'
            ? s.contributing_factors.replace(/,/g, ', ')
            : '';
        const div = document.createElement('div');
        div.className = 'risk-student-item';
        div.onclick = () => openStudentModal(s);
        div.innerHTML = `
            <div class="risk-avatar ${s.risk_level}">${initials}</div>
            <div class="risk-student-info">
                <div class="risk-student-name">${s.name} <span style="color:var(--text-muted);font-weight:400">· Grade ${s.grade}</span></div>
                <div class="risk-student-detail">${factors}</div>
            </div>
            <span class="risk-score-badge ${s.risk_level}">${(s.risk_score * 100).toFixed(0)}%</span>
        `;
        container.appendChild(div);
    });
}

// Filters
document.getElementById('student-search')?.addEventListener('input', applyFilters);
document.getElementById('risk-filter')?.addEventListener('change', applyFilters);
document.getElementById('status-filter')?.addEventListener('change', applyFilters);

function applyFilters() {
    const search = document.getElementById('student-search').value.toLowerCase();
    const risk = document.getElementById('risk-filter').value;
    const status = document.getElementById('status-filter').value;

    let filtered = studentsData;

    if (search) {
        filtered = filtered.filter(s =>
            s.name.toLowerCase().includes(search) ||
            (s.contributing_factors || '').toLowerCase().includes(search) ||
            (s.school_name || '').toLowerCase().includes(search)
        );
    }
    if (risk !== 'all') {
        filtered = filtered.filter(s => s.risk_level === risk);
    }
    if (status !== 'all') {
        filtered = filtered.filter(s => s.current_status === status);
    }

    renderStudents(filtered);
}

// ── Student Modal ───────────────────────────────────────────────
function openStudentModal(s) {
    const modal = document.getElementById('student-modal');
    const body = document.getElementById('modal-body');

    const initials = s.name.split(' ').map(n => n[0]).join('');
    const bgClass = s.risk_level === 'critical' ? 'background:var(--gradient-danger)' :
                    s.risk_level === 'high' ? 'background:var(--gradient-warning)' :
                    s.risk_level === 'medium' ? 'background:linear-gradient(135deg,#f59e0b,#eab308)' :
                    'background:var(--gradient-success)';

    const income = s.parent_income ? `₹${s.parent_income.toLocaleString('en-IN')}` : '—';
    const factors = s.contributing_factors && s.contributing_factors !== 'none'
        ? s.contributing_factors.split(',').map(f => `<span class="factor-tag">${f.trim()}</span>`).join('')
        : '<span style="color:var(--text-muted)">None</span>';
    const interventions = s.recommended_intervention
        ? s.recommended_intervention.split(',').map(i => `<span class="intervention-tag">${i.trim()}</span>`).join('')
        : '<span style="color:var(--text-muted)">None</span>';

    body.innerHTML = `
        <div class="modal-student-header">
            <div class="modal-avatar" style="${bgClass}">${initials}</div>
            <div>
                <div class="modal-name">${s.name}</div>
                <div class="modal-subtitle">${s.gender === 'M' ? 'Male' : 'Female'} · Age ${s.age} · Grade ${s.grade} · ${s.school_name}</div>
            </div>
        </div>

        <div class="modal-grid">
            <div class="modal-field">
                <div class="modal-field-label">Risk Level</div>
                <div class="modal-field-value"><span class="risk-pill ${s.risk_level}">● ${s.risk_level} (${(s.risk_score * 100).toFixed(0)}%)</span></div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Status</div>
                <div class="modal-field-value"><span class="status-badge ${s.current_status}">${s.current_status.replace('_', ' ')}</span></div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">GPA</div>
                <div class="modal-field-value ${s.gpa >= 7 ? 'gpa-good' : s.gpa >= 5 ? 'gpa-mid' : 'gpa-bad'}">${s.gpa} / 10</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Attendance</div>
                <div class="modal-field-value ${s.attendance_pct >= 80 ? 'attendance-good' : s.attendance_pct >= 60 ? 'attendance-mid' : 'attendance-bad'}">${s.attendance_pct}%</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Distance to School</div>
                <div class="modal-field-value">${s.distance_from_school_km} km</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Parent Income</div>
                <div class="modal-field-value">${income}</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Criminal History</div>
                <div class="modal-field-value">${s.has_criminal_history ? '⚠️ Yes' : '✅ No'}</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Lives With</div>
                <div class="modal-field-value" style="text-transform:capitalize">${(s.lives_with || '').replace('_', ' ')}</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Income Bracket</div>
                <div class="modal-field-value" style="text-transform:capitalize">${(s.family_income_bracket || '').replace('_', ' ')}</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Siblings</div>
                <div class="modal-field-value">${s.number_of_siblings}</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Scholarship</div>
                <div class="modal-field-value">${s.receives_scholarship ? '✅ Yes' : '❌ No'}</div>
            </div>
            <div class="modal-field">
                <div class="modal-field-label">Internet Access</div>
                <div class="modal-field-value">${s.has_internet_access ? '✅ Yes' : '❌ No'}</div>
            </div>
        </div>

        <div class="modal-section-title">Contributing Risk Factors</div>
        <div class="modal-factors">${factors}</div>

        <div class="modal-section-title">Recommended Interventions</div>
        <div class="modal-factors">${interventions}</div>

        ${s.predicted_dropout_year ? `
        <div class="modal-section-title">Prediction</div>
        <p style="color:var(--accent-red);font-weight:600;font-size:14px">⚠️ Predicted to drop out by ${s.predicted_dropout_year}</p>
        ` : ''}
    `;

    modal.classList.add('open');
}

function closeModal() {
    document.getElementById('student-modal').classList.remove('open');
}

// Close modal on overlay click
document.getElementById('student-modal')?.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
});

// Close on Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
});

// ── Chat ────────────────────────────────────────────────────────
let chatBusy = false;

function askSuggestion(btn) {
    const input = document.getElementById('chat-input');
    input.value = btn.textContent;
    sendMessage(new Event('submit'));
}

async function sendMessage(e) {
    e.preventDefault();
    if (chatBusy) return;

    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;

    input.value = '';
    chatBusy = true;
    document.getElementById('send-btn').disabled = true;

    // Remove welcome screen
    const welcome = document.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const msgArea = document.getElementById('chat-messages');

    // User message
    addChatMsg('user', `<div class="msg-text">${escHtml(question)}</div>`);

    // Loading indicator
    const loadingId = 'loading-' + Date.now();
    addChatMsg('assistant', `<div class="loading-dots" id="${loadingId}"><span></span><span></span><span></span></div>`);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });
        const data = await res.json();

        // Remove loading
        document.getElementById(loadingId)?.closest('.chat-msg')?.remove();

        if (data.error && !data.sql) {
            addChatMsg('assistant', `<div class="msg-error">❌ ${escHtml(data.error)}</div>`);
        } else {
            let html = '';

            if (data.commentary) {
                html += `<div class="msg-text">${escHtml(data.commentary)}</div>`;
            }

            if (data.sql) {
                html += `<div class="msg-sql"><div class="msg-sql-label">SQL Query</div>${escHtml(data.sql)}</div>`;
            }

            if (data.error) {
                html += `<div class="msg-error">⚠️ ${escHtml(data.error)}</div>`;
            }

            if (data.data && data.data.length > 0) {
                html += renderDataTable(data.data);
            } else if (!data.error) {
                html += `<div class="msg-text" style="color:var(--text-muted)">No rows returned.</div>`;
            }

            html += `<div class="msg-meta">${data.tool_calls || 0} tool calls</div>`;
            addChatMsg('assistant', html);
        }
    } catch (err) {
        document.getElementById(loadingId)?.closest('.chat-msg')?.remove();
        addChatMsg('assistant', `<div class="msg-error">❌ Connection error: ${escHtml(err.message)}</div>`);
    }

    chatBusy = false;
    document.getElementById('send-btn').disabled = false;
    scrollChat();
}

function addChatMsg(role, innerHtml) {
    const msgArea = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.innerHTML = `
        <div class="msg-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="msg-body">${innerHtml}</div>
    `;
    msgArea.appendChild(div);
    scrollChat();
}

function renderDataTable(rows) {
    if (!rows.length) return '';
    const cols = Object.keys(rows[0]);
    let html = '<div class="msg-data-wrap"><table class="msg-data-table"><thead><tr>';
    cols.forEach(c => html += `<th>${escHtml(c)}</th>`);
    html += '</tr></thead><tbody>';
    rows.slice(0, 20).forEach(row => {
        html += '<tr>';
        cols.forEach(c => html += `<td>${escHtml(String(row[c] ?? ''))}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    if (rows.length > 20) {
        html += `<div class="msg-meta" style="margin-top:4px">Showing 20 of ${rows.length} rows</div>`;
    }
    return html;
}

function scrollChat() {
    const el = document.getElementById('chat-messages');
    setTimeout(() => el.scrollTop = el.scrollHeight, 50);
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadStudents();
});
