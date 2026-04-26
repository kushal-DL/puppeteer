
// ── State ────────────────────────────────────────────────────────────────────
let selectedJobId = null;
let jobsData = [];
let telemetryData = [];
const expandedCallIds = new Set();   // track which LLM calls are expanded
let lastDetailHash = '';              // change-detection for detail panel
let lastTelemetryLen = 0;             // change-detection for telemetry
let currentView = 'jobs';             // 'jobs' | 'analytics'
let analyticsData = null;             // cached analytics payload
let analyticsSort = { col: 'created_at', dir: 'desc' }; // history table sort
let analyticsFilter = { status: 'all', type: 'all', repo: 'all', range: 'all' };

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtTime(ms) {
  if (!ms || ms <= 0) return '—';
  if (ms < 1000) return ms + 'ms';
  if (ms < 60000) return (ms / 1000).toFixed(1) + 's';
  return (ms / 60000).toFixed(1) + 'm';
}

function fmtTimestamp(epoch) {
  if (!epoch) return '';
  const d = new Date(epoch);
  return d.toLocaleTimeString();
}

function fmtTokens(n) {
  if (!n) return '0';
  if (n < 1000) return String(n);
  return (n / 1000).toFixed(1) + 'k';
}

function truncate(s, n) {
  if (!s) return '';
  return s.length > n ? s.slice(0, n) + '…' : s;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── JSON detection & pretty-printing ─────────────────────────────────────────
function formatContent(raw) {
  if (!raw) return '';
  // Replace literal \n with actual newlines
  let s = raw.replace(/\\n/g, '\n');
  // Try to detect and pretty-print JSON
  const trimmed = s.trim();
  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) ||
      (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      const obj = JSON.parse(trimmed);
      const pretty = JSON.stringify(obj, null, 2);
      return syntaxHighlight(pretty);
    } catch (e) { /* not valid JSON, fall through */ }
  }
  return escHtml(s);
}

function syntaxHighlight(json) {
  const escaped = escHtml(json);
  return escaped.replace(
    /("(?:[^"\\]|\\.)*")\s*:/g,
    '<span class="json-key">$1</span>:'
  ).replace(
    /:\s*("(?:[^"\\]|\\.)*")/g,
    ': <span class="json-str">$1</span>'
  ).replace(
    /:\s*(\d+\.?\d*)/g,
    ': <span class="json-num">$1</span>'
  ).replace(
    /:\s*(true|false)/g,
    ': <span class="json-bool">$1</span>'
  ).replace(
    /:\s*(null)/g,
    ': <span class="json-null">$1</span>'
  );
}

// ── Pipeline step mapping ────────────────────────────────────────────────────
const PIPELINE_STEPS = [
  { key: 'cloning', label: 'Clone' },
  { key: 'planning', label: 'Plan' },
  { key: 'running', label: 'Build' },
  { key: 'generating delivery', label: 'Merge' },
  { key: 'self-review', label: 'Review' },
  { key: 'review fix', label: 'Fix' },
  { key: 'pushing', label: 'Push' },
  { key: 'done', label: 'Done' },
];

function getPipelineState(job) {
  const step = (job.current_step || '').toLowerCase();
  const status = job.status;
  let activeIdx = -1;

  for (let i = PIPELINE_STEPS.length - 1; i >= 0; i--) {
    if (step.includes(PIPELINE_STEPS[i].key)) {
      activeIdx = i;
      break;
    }
  }

  return PIPELINE_STEPS.map((s, i) => {
    if (status === 'complete') return 'done';
    if (status === 'failed' && i === activeIdx) return 'error';
    if (status === 'failed' && i < activeIdx) return 'done';
    if (i < activeIdx) return 'done';
    if (i === activeIdx) return 'active';
    return '';
  });
}

// ── Render: Job list ─────────────────────────────────────────────────────────
function renderJobList(jobs) {
  const el = document.getElementById('job-list');
  if (!jobs.length) {
    el.innerHTML = '<div class="no-data">No jobs yet. Start a pipeline!</div>';
    return;
  }
  // Separate parent jobs and revision children
  const parents = jobs.filter(j => !j.parent_job_id);
  const childMap = {};
  for (const j of jobs) {
    if (j.parent_job_id) {
      if (!childMap[j.parent_job_id]) childMap[j.parent_job_id] = [];
      childMap[j.parent_job_id].push(j);
    }
  }
  // Build ordered list: parent followed by its children
  const ordered = [];
  for (const p of parents) {
    ordered.push(p);
    if (childMap[p.job_id]) {
      ordered.push(...childMap[p.job_id]);
    }
  }
  el.innerHTML = ordered.map(j => {
    const active = j.job_id === selectedJobId ? 'active' : '';
    const isRevision = j.parent_job_id || (j.job_type === 'revision');
    const childCls = isRevision ? 'revision-child' : '';
    const typeBadge = isRevision
      ? '<span class="badge type-rev">Revision</span>'
      : '<span class="badge type-gen">Generation</span>';
    const dur = j.duration_ms ? fmtTime(j.duration_ms) : '—';
    const prBit = j.pr_number ? ` · PR #${j.pr_number}` : '';
    return `
      <div class="job-item ${active} ${childCls}" onclick="selectJob('${j.job_id}')">
        <button class="delete-btn" onclick="event.stopPropagation(); deleteJob('${j.job_id}')" title="Delete job">✕</button>
        <div class="goal">${truncate(j.goal, 55)}</div>
        <div class="meta">
          ${typeBadge}
          <span class="badge ${j.status}">${j.status}</span>
          <span>${j.agent_count || 0} agents</span>
          <span>${dur}${prBit}</span>
          <span>${fmtTimestamp(j.started_at)}</span>
        </div>
      </div>`;
  }).join('');
}

// ── Delete job ───────────────────────────────────────────────────────────────
async function deleteJob(jobId) {
  if (!confirm('Delete job ' + jobId.slice(0,8) + '…?')) return;
  try {
    await fetch('/api/jobs/' + jobId, { method: 'DELETE' });
  } catch (e) { /* ignore */ }
  jobsData = jobsData.filter(j => j.job_id !== jobId);
  if (selectedJobId === jobId) {
    selectedJobId = null;
    document.getElementById('main-panel').className = 'main empty';
    document.getElementById('main-panel').innerHTML = 'Select a job from the left.';
  }
  renderJobList(jobsData);
}

// ── Render: Job detail ───────────────────────────────────────────────────────
function renderJobDetail(job) {
  const panel = document.getElementById('main-panel');
  panel.className = 'main';

  const events = job.events || [];
  const agentStates = job.agent_states || {};
  const pipeState = getPipelineState(job);

  // Duration
  const firstT = events.length ? events[0].t : 0;
  const lastT = events.length ? events[events.length - 1].t : 0;
  const dur = firstT ? lastT - firstT : 0;

  // Build agent timeline data
  const agentTimeline = buildAgentTimeline(events, agentStates, firstT, lastT);

  // LLM calls (from telemetry, which now includes token data from DB)
  const llmCalls = buildLLMCalls();

  // Per-job LLM metrics
  const totalPromptTok = llmCalls.reduce((s, c) => s + (c.prompt_tokens || 0), 0);
  const totalRespTok = llmCalls.reduce((s, c) => s + (c.response_tokens || 0), 0);
  const totalLlmTime = llmCalls.reduce((s, c) => s + (c.duration_ms || 0), 0);

  const isRevision = job.job_type === 'revision' || job.parent_job_id;
  const typeBadge = isRevision
    ? '<span class="badge type-rev" style="margin-right:8px">Revision</span>'
    : '<span class="badge type-gen" style="margin-right:8px">Generation</span>';
  const prLink = job.pr_url
    ? `<a class="pr-link" href="${job.pr_url}" target="_blank">&#x1F517; PR #${job.pr_number || ''}</a>`
    : '';
  const parentLink = job.parent_job_id
    ? `<span style="font-size:12px;color:var(--dim);margin-left:8px">Parent: <a href="#" onclick="selectJob('${job.parent_job_id}');return false">${job.parent_job_id.slice(0,8)}…</a></span>`
    : '';
  // Extract repo for analytics link
  const _repoMatch = (job.pr_url || '').replace('https://','').replace('http://','').split('/');
  const _repoName = _repoMatch.length >= 3 ? _repoMatch[1] + '/' + _repoMatch[2] : '';
  const repoLink = _repoName
    ? `<a href="#" onclick="navToRepoAnalytics('${_repoName}');return false" style="font-size:11px;color:var(--cyan);margin-left:8px">📊 Repo Analytics</a>`
    : '';

  panel.innerHTML = `
    <div class="detail-header">
      <h2>${typeBadge}${job.job_id}</h2>
      <div class="goal-text">${job.goal || ''}</div>
      <div style="margin-top:4px;font-size:12px;color:var(--dim)">
        Duration: ${fmtTime(dur)} · Status: <span class="badge ${job.status}">${job.status}</span>
        ${prLink}${parentLink}${repoLink}
        ${job.error ? `<span style="color:var(--red);margin-left:8px">${truncate(job.error, 120)}</span>` : ''}
      </div>
    </div>

    <!-- Pipeline -->
    <div class="pipeline">
      ${PIPELINE_STEPS.map((s, i) =>
        `<div class="step ${pipeState[i]}">${s.label}</div>`
      ).join('<div style="color:var(--dim);line-height:36px">→</div>')}
    </div>

    <!-- Per-job metrics -->
    <div class="metrics-bar">
      <div class="metric"><span class="m-val">${llmCalls.length}</span><span class="m-label">LLM Calls</span></div>
      <div class="metric"><span class="m-val">${fmtTokens(totalPromptTok)}</span><span class="m-label">Prompt Tok</span></div>
      <div class="metric"><span class="m-val">${fmtTokens(totalRespTok)}</span><span class="m-label">Response Tok</span></div>
      <div class="metric"><span class="m-val">${fmtTokens(totalPromptTok + totalRespTok)}</span><span class="m-label">Total Tok</span></div>
      <div class="metric"><span class="m-val">${fmtTime(totalLlmTime)}</span><span class="m-label">LLM Time</span></div>
      <div class="metric"><span class="m-val">${Object.keys(agentStates).length}</span><span class="m-label">Agents</span></div>
      <div class="metric"><span class="m-val">${fmtTime(dur)}</span><span class="m-label">Wall Time</span></div>
    </div>

    <!-- Agent States -->
    <div class="section">
      <div class="section-title">Agents</div>
      <div class="agent-grid">
        ${Object.entries(agentStates).map(([name, state]) => {
          const at = agentTimeline.find(a => a.name === name);
          const agentDur = at ? fmtTime(at.end - at.start) : '';
          return `<div class="agent-card ${state}">
            <div class="name">${name}</div>
            <div style="color:var(--dim);font-size:11px">${state}${agentDur ? ' · ' + agentDur : ''}</div>
          </div>`;
        }).join('')}
        ${Object.keys(agentStates).length === 0 ? '<div class="no-data">No agents yet</div>' : ''}
      </div>
    </div>

    <!-- Timeline -->
    <div class="section">
      <div class="section-title">Timeline</div>
      <div class="timeline-container">
        ${agentTimeline.length ? agentTimeline.map(a => {
          const totalSpan = (lastT - firstT) || 1;
          const left = ((a.start - firstT) / totalSpan * 100).toFixed(1);
          const width = Math.max(((a.end - a.start) / totalSpan * 100), 0.5).toFixed(1);
          return `<div class="timeline-row">
            <div class="timeline-label">${a.name}</div>
            <div class="timeline-track">
              <div class="timeline-bar ${a.state}" style="left:${left}%;width:${width}%"
                title="${a.name}: ${fmtTime(a.end - a.start)}">${fmtTime(a.end - a.start)}</div>
            </div>
          </div>`;
        }).join('') : '<div class="no-data">No timeline data</div>'}
      </div>
    </div>

    <!-- LLM Calls -->
    <div class="section">
      <div class="section-title">LLM Calls (${llmCalls.length})</div>
      <div class="llm-log">
        ${llmCalls.length ? llmCalls.map(c => `
          <div class="llm-call">
            <div class="llm-call-header" onclick="toggleLLM(${c.call_id})">
              <span class="call-id">#${c.call_id}</span>
              <span class="call-schema">${c.schema || 'text'}</span>
              <span class="call-tokens">${fmtTokens(c.prompt_tokens || 0)}→${fmtTokens(c.response_tokens || 0)} tok</span>
              <span style="color:var(--gray);font-size:11px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${truncate(c.prompt, 60)}</span>
              <span class="call-duration">${c.duration_ms ? fmtTime(c.duration_ms) : '⏳'}</span>
            </div>
            <div class="llm-call-body" id="llm-body-${c.call_id}">
              <div class="label">Prompt</div>
              <pre>${formatContent(c.prompt || '')}</pre>
              <div class="label">System</div>
              <pre>${formatContent(c.system || '')}</pre>
              <div class="label">Response</div>
              <pre>${formatContent(c.response || '')}</pre>
            </div>
          </div>
        `).join('') : '<div class="no-data">No LLM calls recorded (start the Mock LLM server)</div>'}
      </div>
    </div>

    <!-- Event Log -->
    <div class="section">
      <div class="section-title">Event Log (${events.length})</div>
      <div class="event-log">
        ${events.map(ev => {
          const detail = ev.agent ? ev.agent : '';
          const extra = ev.error ? ` — ${truncate(ev.error, 80)}` : '';
          const fc = ev.failure_class ? ` [${ev.failure_class}]` : '';
          return `<div class="event-row">
            <span class="ev-time">${fmtTimestamp(ev.t)}</span>
            <span class="ev-type ${ev.type}">${ev.type}</span>
            <span class="ev-detail">${detail}${fc}${extra}</span>
          </div>`;
        }).join('')}
        ${events.length === 0 ? '<div class="no-data">No events</div>' : ''}
      </div>
    </div>
  `;

  // Restore expanded state for LLM call rows
  for (const cid of expandedCallIds) {
    const el = document.getElementById('llm-body-' + cid);
    if (el) el.classList.add('open');
  }
}

// ── Toggle LLM call expand/collapse (by call_id, not index) ──────────────────
function toggleLLM(callId) {
  if (expandedCallIds.has(callId)) {
    expandedCallIds.delete(callId);
  } else {
    expandedCallIds.add(callId);
  }
  const el = document.getElementById('llm-body-' + callId);
  if (el) el.classList.toggle('open');
}

// ── Build agent timeline from events ─────────────────────────────────────────
function buildAgentTimeline(events, agentStates, firstT, lastT) {
  const agents = {};
  for (const ev of events) {
    if (!ev.agent) continue;
    if (!agents[ev.agent]) agents[ev.agent] = { name: ev.agent, start: ev.t, end: ev.t, state: 'pending' };
    if (ev.type === 'agent_started') {
      agents[ev.agent].start = ev.t;
      agents[ev.agent].state = 'running';
    }
    if (ev.type === 'agent_done') {
      agents[ev.agent].end = ev.t;
      agents[ev.agent].state = 'completed';
    }
    if (ev.type === 'agent_failed') {
      agents[ev.agent].end = ev.t;
      agents[ev.agent].state = 'failed';
    }
    if (ev.type === 'agent_pruned') {
      agents[ev.agent].end = ev.t;
      agents[ev.agent].state = 'pruned';
    }
  }
  for (const [name, state] of Object.entries(agentStates)) {
    if (!agents[name]) {
      agents[name] = { name, start: firstT, end: lastT || firstT + 1, state };
    } else if (agents[name].state === 'pending' || agents[name].state === 'running') {
      agents[name].state = state;
      if (state === 'completed' || state === 'failed' || state === 'pruned') {
        agents[name].end = lastT;
      }
    }
  }
  return Object.values(agents).sort((a, b) => a.start - b.start);
}

// ── Build LLM call list from telemetry data ──────────────────────────────────
function buildLLMCalls() {
  // telemetryData now comes from DB (flat list with all fields)
  // or from old telemetry.jsonl (request/response pairs)
  const calls = {};
  for (const r of telemetryData) {
    // DB format: flat records with call_id, prompt, response, duration_ms, etc.
    if (r.call_id !== undefined && !r.type) {
      calls[r.call_id] = {
        call_id: r.call_id,
        prompt: r.prompt || '',
        system: r.system || '',
        schema: r.schema || '',
        response: r.response || '',
        duration_ms: r.duration_ms,
        prompt_tokens: r.prompt_tokens || 0,
        response_tokens: r.response_tokens || 0,
      };
      continue;
    }
    // Legacy telemetry.jsonl format: separate request/response records
    if (r.type === 'llm_request') {
      calls[r.call_id] = {
        call_id: r.call_id,
        prompt: r.prompt || '',
        system: r.system || '',
        schema: r.schema || '',
        response: '',
        duration_ms: null,
        prompt_tokens: 0,
        response_tokens: 0,
      };
    }
    if (r.type === 'llm_response' && calls[r.call_id]) {
      calls[r.call_id].response = r.response || '';
      calls[r.call_id].duration_ms = r.duration_ms;
    }
  }
  return Object.values(calls).sort((a, b) => a.call_id - b.call_id);
}

// ── Select job ───────────────────────────────────────────────────────────────
async function selectJob(jobId) {
  selectedJobId = jobId;
  renderJobList(jobsData);
  try {
    const resp = await fetch('/api/jobs/' + jobId);
    if (!resp.ok) throw new Error('Not found');
    const job = await resp.json();
    renderJobDetail(job);
  } catch (e) {
    document.getElementById('main-panel').innerHTML =
      '<div class="no-data">Failed to load job: ' + e.message + '</div>';
  }
}

// ── Compute a lightweight hash for change detection ──────────────────────────
function jobHash(job) {
  if (!job) return '';
  const events = job.events || [];
  return job.status + ':' + events.length + ':' +
    Object.values(job.agent_states || {}).join(',') + ':' + telemetryData.length;
}

// ── View Switching ───────────────────────────────────────────────────────────
function switchView(view) {
  currentView = view;
  const container = document.getElementById('app-container');
  container.className = 'container view-' + view;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.toLowerCase() === view);
  });
  if (view === 'analytics') fetchAndRenderAnalytics();
}

// Navigate from analytics to a specific job in the Jobs view
function navToJob(jobId) {
  switchView('jobs');
  selectJob(jobId);
}

// Navigate from job detail to analytics filtered by repo
function navToRepoAnalytics(repo) {
  analyticsFilter = { status: 'all', type: 'all', repo: repo, range: 'all' };
  switchView('analytics');
}

// ── Analytics: Fetch & Render ────────────────────────────────────────────────
async function fetchAndRenderAnalytics() {
  try {
    const resp = await fetch('/api/analytics');
    if (!resp.ok) return;
    analyticsData = await resp.json();
    renderAnalytics(analyticsData);
  } catch (e) { /* silent */ }
}

function renderAnalytics(data) {
  const panel = document.getElementById('analytics-panel');
  if (!data || data.error) {
    panel.innerHTML = '<div class="a-table-empty">Analytics unavailable</div>';
    return;
  }
  const k = data.kpis;
  const successCls = k.success_rate >= 90 ? 'success' : k.success_rate >= 70 ? '' : 'danger';

  // Format cost
  function fmtCost(v) { return '$' + v.toFixed(4); }

  panel.innerHTML = `
    <!-- KPI Cards -->
    <h3>Overview</h3>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-val">${k.total_jobs}</div>
        <div class="kpi-sub">${k.gen_count} gen · ${k.rev_count} rev</div>
        <div class="kpi-label">Total Jobs</div>
      </div>
      <div class="kpi-card ${successCls}">
        <div class="kpi-val">${k.success_rate}%</div>
        <div class="kpi-sub">${k.completed} of ${k.total_jobs}</div>
        <div class="kpi-label">Success Rate</div>
      </div>
      <div class="kpi-card info">
        <div class="kpi-val">${fmtTime(k.avg_duration_gen_ms)}</div>
        <div class="kpi-sub">Rev: ${fmtTime(k.avg_duration_rev_ms)}</div>
        <div class="kpi-label">Avg Duration</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">${fmtTokens(k.total_tokens)}</div>
        <div class="kpi-sub">${fmtTokens(k.total_prompt_tokens)} in · ${fmtTokens(k.total_response_tokens)} out</div>
        <div class="kpi-label">Total Tokens</div>
      </div>
      <div class="kpi-card cost">
        <div class="kpi-val">${fmtCost(k.total_cost_usd)}</div>
        <div class="kpi-sub">Gemini 3.1 Pro · $2/$12 per 1M</div>
        <div class="kpi-label">Estimated Cost</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">${k.revision_rate}%</div>
        <div class="kpi-sub">${k.active} active now</div>
        <div class="kpi-label">Revision Rate</div>
      </div>
    </div>

    <!-- Job History Table -->
    <div class="a-table-wrap" id="history-section">
      <div class="a-table-title">
        Job History
        <div class="filter-group">
          <button class="filter-btn ${analyticsFilter.type==='all'?'active':''}" onclick="setHistoryFilter('type','all')">All</button>
          <button class="filter-btn ${analyticsFilter.type==='generation'?'active':''}" onclick="setHistoryFilter('type','generation')">Gen</button>
          <button class="filter-btn ${analyticsFilter.type==='revision'?'active':''}" onclick="setHistoryFilter('type','revision')">Rev</button>
          <span style="color:var(--border)">|</span>
          <button class="filter-btn ${analyticsFilter.status==='all'?'active':''}" onclick="setHistoryFilter('status','all')">All</button>
          <button class="filter-btn ${analyticsFilter.status==='complete'?'active':''}" onclick="setHistoryFilter('status','complete')">✓</button>
          <button class="filter-btn ${analyticsFilter.status==='failed'?'active':''}" onclick="setHistoryFilter('status','failed')">✗</button>
          <span style="color:var(--border)">|</span>
          <button class="filter-btn ${analyticsFilter.range==='all'?'active':''}" onclick="setHistoryFilter('range','all')">All Time</button>
          <button class="filter-btn ${analyticsFilter.range==='24h'?'active':''}" onclick="setHistoryFilter('range','24h')">24h</button>
          <button class="filter-btn ${analyticsFilter.range==='7d'?'active':''}" onclick="setHistoryFilter('range','7d')">7d</button>
          <button class="filter-btn ${analyticsFilter.range==='30d'?'active':''}" onclick="setHistoryFilter('range','30d')">30d</button>
        </div>
      </div>
      <div id="history-table-body"></div>
    </div>

    <!-- Two-column: Failure Analysis + LLM Performance -->
    <div class="analytics-row">
      <div class="a-table-wrap">
        <div class="a-table-title">Failure Analysis</div>
        ${renderFailureTable(data)}
      </div>
      <div class="a-table-wrap">
        <div class="a-table-title">LLM Performance by Schema</div>
        ${renderLLMTable(data)}
      </div>
    </div>

    <!-- Repository Activity -->
    <div class="a-table-wrap">
      <div class="a-table-title">Repository Activity</div>
      ${renderRepoTable(data)}
    </div>
  `;

  // Render the history table (separate so filters can re-render it)
  renderHistoryTable(data);
}

// ── History Table with sort + filter ─────────────────────────────────────────
function renderHistoryTable(data) {
  const el = document.getElementById('history-table-body');
  if (!el) return;

  let rows = [...data.history];

  // Apply filters
  if (analyticsFilter.type !== 'all') rows = rows.filter(r => r.job_type === analyticsFilter.type);
  if (analyticsFilter.status !== 'all') rows = rows.filter(r => r.status === analyticsFilter.status);
  if (analyticsFilter.repo !== 'all') rows = rows.filter(r => r.repo === analyticsFilter.repo);
  if (analyticsFilter.range !== 'all') {
    const now = Date.now();
    const ranges = { '24h': 86400000, '7d': 604800000, '30d': 2592000000 };
    const cutoff = now - (ranges[analyticsFilter.range] || 0);
    rows = rows.filter(r => r.created_at >= cutoff);
  }

  // Sort
  const col = analyticsSort.col;
  const dir = analyticsSort.dir === 'asc' ? 1 : -1;
  rows.sort((a, b) => {
    let va = a[col], vb = b[col];
    if (typeof va === 'string') return va.localeCompare(vb) * dir;
    return ((va || 0) - (vb || 0)) * dir;
  });

  function sortArrow(c) {
    return analyticsSort.col === c ? `<span class="sort-arrow">${analyticsSort.dir==='asc'?'▲':'▼'}</span>` : '';
  }

  if (!rows.length) {
    el.innerHTML = '<div class="a-table-empty">No jobs match the current filters</div>';
    return;
  }

  el.innerHTML = `
    <table class="a-table">
      <thead><tr>
        <th onclick="sortHistory('created_at')">Time ${sortArrow('created_at')}</th>
        <th onclick="sortHistory('job_id')">ID ${sortArrow('job_id')}</th>
        <th onclick="sortHistory('job_type')">Type ${sortArrow('job_type')}</th>
        <th onclick="sortHistory('repo')">Repo ${sortArrow('repo')}</th>
        <th onclick="sortHistory('goal')">Goal ${sortArrow('goal')}</th>
        <th onclick="sortHistory('status')">Status ${sortArrow('status')}</th>
        <th onclick="sortHistory('duration_ms')">Duration ${sortArrow('duration_ms')}</th>
        <th onclick="sortHistory('llm_calls')">LLM ${sortArrow('llm_calls')}</th>
        <th onclick="sortHistory('tokens')">Tokens ${sortArrow('tokens')}</th>
      </tr></thead>
      <tbody>
        ${rows.map(r => `
          <tr class="clickable" onclick="navToJob('${r.job_id}')">
            <td>${fmtTimestamp(r.created_at)}</td>
            <td style="font-family:var(--mono);font-size:11px;color:var(--gold)">${r.job_id.slice(0,8)}…</td>
            <td><span class="badge ${r.job_type==='revision'?'type-rev':'type-gen'}">${r.job_type==='revision'?'Rev':'Gen'}</span></td>
            <td class="repo-cell">${r.repo !== 'unknown' ? r.repo : '—'}</td>
            <td class="goal-cell" title="${escHtml(r.goal || '')}">${truncate(r.goal, 40)}</td>
            <td><span class="badge ${r.status}">${r.status}</span></td>
            <td>${fmtTime(r.duration_ms)}</td>
            <td>${r.llm_calls}</td>
            <td>${fmtTokens(r.tokens)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function sortHistory(col) {
  if (analyticsSort.col === col) {
    analyticsSort.dir = analyticsSort.dir === 'asc' ? 'desc' : 'asc';
  } else {
    analyticsSort.col = col;
    analyticsSort.dir = col === 'created_at' ? 'desc' : 'asc';
  }
  if (analyticsData) renderHistoryTable(analyticsData);
}

function setHistoryFilter(key, val) {
  analyticsFilter[key] = val;
  if (analyticsData) renderAnalytics(analyticsData);
}

// ── Failure Analysis Table ───────────────────────────────────────────────────
function renderFailureTable(data) {
  if (!data.failure_by_class.length && !data.failure_by_stage.length) {
    return '<div class="a-table-empty">No failures recorded</div>';
  }
  let html = '';
  if (data.failure_by_class.length) {
    html += `<table class="a-table">
      <thead><tr><th>Failure Class</th><th>Count</th></tr></thead>
      <tbody>${data.failure_by_class.map(r => `
        <tr><td style="color:var(--red)">${r.class}</td><td>${r.count}</td></tr>
      `).join('')}</tbody>
    </table>`;
  }
  if (data.failure_by_stage.length) {
    html += `<div style="border-top:1px solid var(--border)"></div>
    <table class="a-table">
      <thead><tr><th>Failed at Stage</th><th>Count</th></tr></thead>
      <tbody>${data.failure_by_stage.map(r => `
        <tr><td style="color:var(--orange)">${r.stage}</td><td>${r.count}</td></tr>
      `).join('')}</tbody>
    </table>`;
  }
  return html;
}

// ── LLM Performance Table ────────────────────────────────────────────────────
function renderLLMTable(data) {
  if (!data.llm_by_schema.length) {
    return '<div class="a-table-empty">No LLM calls recorded</div>';
  }
  return `<table class="a-table">
    <thead><tr>
      <th>Schema</th><th>Calls</th><th>Avg Latency</th>
      <th>Input Tok</th><th>Output Tok</th><th>Cost</th>
    </tr></thead>
    <tbody>${data.llm_by_schema.map(r => `
      <tr>
        <td style="color:var(--cyan);font-family:var(--mono);font-size:11px">${r.schema}</td>
        <td>${r.calls}</td>
        <td>${fmtTime(r.avg_duration_ms)}</td>
        <td>${fmtTokens(r.prompt_tokens)}</td>
        <td>${fmtTokens(r.response_tokens)}</td>
        <td class="cost-val">$${r.cost_usd.toFixed(4)}</td>
      </tr>
    `).join('')}</tbody>
  </table>`;
}

// ── Repository Activity Table ────────────────────────────────────────────────
function renderRepoTable(data) {
  if (!data.repos.length) {
    return '<div class="a-table-empty">No repository data</div>';
  }
  return `<table class="a-table">
    <thead><tr>
      <th>Repository</th><th>Jobs</th><th>Success</th>
      <th>Failed</th><th>Tokens</th><th>Last Activity</th>
    </tr></thead>
    <tbody>${data.repos.map(r => `
      <tr class="clickable" onclick="setHistoryFilter('repo','${escHtml(r.repo)}')">
        <td class="repo-cell">${r.repo}</td>
        <td>${r.total_jobs}</td>
        <td style="color:var(--green)">${r.success_rate}%</td>
        <td style="color:${r.failed?'var(--red)':'var(--dim)'}">${r.failed}</td>
        <td>${fmtTokens(r.tokens)}</td>
        <td>${fmtTimestamp(r.last_activity)}</td>
      </tr>
    `).join('')}</tbody>
  </table>`;
}

// ── Polling loop ─────────────────────────────────────────────────────────────
async function poll() {
  try {
    // Fetch jobs
    const jResp = await fetch('/api/jobs');
    if (jResp.ok) {
      jobsData = await jResp.json();
      renderJobList(jobsData);
      // Auto-select first job if none selected
      if (!selectedJobId && jobsData.length) {
        selectJob(jobsData[0].job_id);
      }
    }

    // Fetch telemetry
    const tResp = await fetch('/api/telemetry');
    if (tResp.ok) {
      telemetryData = await tResp.json();
    }

    // Re-render detail only if data changed
    if (selectedJobId) {
      const sel = jobsData.find(j => j.job_id === selectedJobId);
      if (sel) {
        const jResp2 = await fetch('/api/jobs/' + selectedJobId);
        if (jResp2.ok) {
          const job = await jResp2.json();
          const h = jobHash(job);
          if (h !== lastDetailHash) {
            lastDetailHash = h;
            renderJobDetail(job);
          }
        }
      }
    }

    // Fetch stats
    const sResp = await fetch('/api/stats');
    if (sResp.ok) {
      const stats = await sResp.json();
      document.getElementById('stat-total').textContent = stats.total_jobs;
      document.getElementById('stat-rate').textContent = stats.success_rate + '%';
      document.getElementById('stat-failed').textContent = stats.failed || 0;
      document.getElementById('stat-dur').textContent = fmtTime(stats.avg_duration_ms);
      document.getElementById('stat-llm').textContent = stats.total_llm_calls;
      document.getElementById('stat-tokens').textContent = fmtTokens(stats.total_tokens || 0);
      document.getElementById('stat-llm-lat').textContent = fmtTime(stats.avg_llm_duration_ms || 0);
    }
  } catch (e) {
    // Dashboard server or HiveShip not reachable — silent
  }
}

// Start polling
poll();
setInterval(poll, 3000);
// Analytics polls on slower interval
setInterval(() => { if (currentView === 'analytics') fetchAndRenderAnalytics(); }, 10000);
