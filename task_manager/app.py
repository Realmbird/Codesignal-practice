#!/usr/bin/env python3
"""
Visual practice interface for the Task Manager CodeSignal problem.
Run with:  python app.py
Then open: http://localhost:8000
"""
import json
import sys
import io
import unittest
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib import import_module, reload

PORT = 8000

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodeSignal Practice — Task Manager</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0f1117;
    color: #e2e8f0;
    min-height: 100vh;
  }
  header {
    background: #1a1d2e;
    border-bottom: 1px solid #2d3148;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  header h1 { font-size: 1.1rem; font-weight: 600; color: #a78bfa; }
  header span { font-size: 0.8rem; color: #64748b; }
  .main { display: grid; grid-template-columns: 1fr 1fr; gap: 0; height: calc(100vh - 53px); }
  .panel { padding: 20px; overflow-y: auto; }
  .panel + .panel { border-left: 1px solid #2d3148; }
  h2 { font-size: 0.85rem; font-weight: 600; text-transform: uppercase;
       letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 14px; }

  /* ---- Query Builder ---- */
  .query-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
  .query-row {
    display: flex; gap: 6px; align-items: center;
    background: #1a1d2e; border: 1px solid #2d3148; border-radius: 6px; padding: 6px 8px;
  }
  .query-row select, .query-row input {
    background: #0f1117; border: 1px solid #2d3148; border-radius: 4px;
    color: #e2e8f0; padding: 4px 8px; font-size: 0.82rem; outline: none;
  }
  .query-row select { min-width: 160px; }
  .query-row input { flex: 1; min-width: 0; }
  .query-row input::placeholder { color: #475569; }
  .btn-icon {
    background: none; border: none; color: #64748b; cursor: pointer;
    font-size: 1rem; padding: 2px 6px; border-radius: 4px; line-height: 1;
  }
  .btn-icon:hover { color: #f87171; background: #2d3148; }
  .row-num {
    font-size: 0.7rem; color: #475569; min-width: 18px; text-align: right; user-select: none;
  }

  .btn {
    border: none; border-radius: 6px; padding: 8px 16px;
    font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
  }
  .btn:hover { opacity: 0.85; }
  .btn-primary { background: #7c3aed; color: #fff; }
  .btn-secondary { background: #1e293b; color: #94a3b8; border: 1px solid #2d3148; }
  .btn-sm { padding: 5px 10px; font-size: 0.78rem; }

  .controls { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }

  .results-box {
    background: #0a0c14; border: 1px solid #2d3148; border-radius: 6px;
    padding: 12px; font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 0.8rem; line-height: 1.7; min-height: 120px;
  }
  .res-row { display: flex; gap: 10px; }
  .res-idx { color: #475569; min-width: 24px; }
  .res-ok  { color: #4ade80; }
  .res-err { color: #f87171; }
  .res-val { color: #93c5fd; }
  .res-none { color: #475569; font-style: italic; }

  /* ---- Test Runner ---- */
  .level-card {
    background: #1a1d2e; border: 1px solid #2d3148; border-radius: 8px;
    margin-bottom: 10px; overflow: hidden;
  }
  .level-header {
    display: flex; align-items: center; gap: 10px; padding: 10px 14px;
    cursor: pointer; user-select: none;
  }
  .level-header:hover { background: #1e2235; }
  .level-badge {
    font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 12px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .badge-idle    { background: #1e293b; color: #64748b; }
  .badge-pass    { background: #14532d; color: #4ade80; }
  .badge-fail    { background: #450a0a; color: #f87171; }
  .badge-running { background: #1e3a5f; color: #60a5fa; }
  .level-title { font-size: 0.88rem; font-weight: 500; flex: 1; }
  .level-topic { font-size: 0.75rem; color: #64748b; }
  .level-run { margin-left: auto; }

  .level-body {
    padding: 10px 14px 12px;
    border-top: 1px solid #2d3148;
    display: none;
  }
  .level-body.open { display: block; }
  .test-output {
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 0.75rem; line-height: 1.6;
    background: #0a0c14; border-radius: 4px; padding: 8px 10px;
    white-space: pre-wrap; word-break: break-all;
    max-height: 220px; overflow-y: auto;
  }
  .pass-line { color: #4ade80; }
  .fail-line { color: #f87171; }
  .info-line { color: #94a3b8; }

  .run-all-bar { display: flex; gap: 8px; margin-bottom: 16px; align-items: center; }
  .score-pill {
    font-size: 0.78rem; padding: 3px 10px; border-radius: 12px;
    background: #1e293b; color: #94a3b8; font-weight: 600;
  }
</style>
</head>
<body>
<header>
  <h1>CodeSignal Practice</h1>
  <span>Task Manager — 6 Levels</span>
</header>
<div class="main">

  <!-- LEFT: Query Runner -->
  <div class="panel">
    <h2>Query Runner</h2>
    <div class="controls">
      <button class="btn btn-secondary btn-sm" onclick="addRow()">+ Add Query</button>
      <button class="btn btn-secondary btn-sm" onclick="clearRows()">Clear</button>
      <button class="btn btn-secondary btn-sm" onclick="loadExample()">Load Example</button>
    </div>
    <div class="query-list" id="queryList"></div>
    <div class="controls" style="margin-top:4px">
      <button class="btn btn-primary" onclick="runQueries()">&#9654; Run</button>
    </div>
    <div style="margin-top:16px">
      <h2 style="margin-bottom:10px">Results</h2>
      <div class="results-box" id="resultsBox">
        <span class="res-none">No results yet — add queries and hit Run.</span>
      </div>
    </div>
  </div>

  <!-- RIGHT: Test Runner -->
  <div class="panel">
    <h2>Test Runner</h2>
    <div class="run-all-bar">
      <button class="btn btn-primary btn-sm" onclick="runAll()">&#9654; Run All</button>
      <span class="score-pill" id="scorePill">— / 6</span>
    </div>

    <div id="levelCards"></div>
  </div>
</div>

<script>
const LEVELS = [
  { n:1, title:"Level 1", topic:"ADD / GET / DELETE (dict basics)" },
  { n:2, title:"Level 2", topic:"LIST / SEARCH / UPDATE (sorting)" },
  { n:3, title:"Level 3", topic:"Priority + Tags (multi-key sort, sets)" },
  { n:4, title:"Level 4", topic:"Due dates + Status (filtering)" },
  { n:5, title:"Level 5", topic:"CONCURRENT_ADD (threading)" },
  { n:6, title:"Level 6", topic:"ASYNC_GET (asyncio)" },
];

const OPS = [
  ["ADD_TASK",       "name"],
  ["GET_TASK",       "id"],
  ["DELETE_TASK",    "id"],
  ["LIST_TASKS",     ""],
  ["SEARCH_TASKS",   "prefix"],
  ["UPDATE_TASK",    "id  new_name"],
  ["SET_PRIORITY",   "id  priority"],
  ["LIST_BY_PRIORITY",""],
  ["ADD_TAG",        "id  tag"],
  ["SEARCH_BY_TAG",  "tag"],
  ["SET_DUE",        "id  timestamp"],
  ["LIST_OVERDUE",   "timestamp"],
  ["SET_STATUS",     "id  status"],
  ["LIST_BY_STATUS", "status"],
  ["CONCURRENT_ADD", "name1,name2,..."],
  ["ASYNC_GET",      "id1,id2,..."],
];

// ---- build level cards ----
const levelCards = document.getElementById("levelCards");
LEVELS.forEach(lv => {
  levelCards.innerHTML += `
  <div class="level-card" id="card-${lv.n}">
    <div class="level-header" onclick="toggleCard(${lv.n})">
      <span class="level-badge badge-idle" id="badge-${lv.n}">idle</span>
      <span class="level-title">${lv.title}</span>
      <span class="level-topic">${lv.topic}</span>
      <button class="btn btn-secondary btn-sm level-run"
              onclick="event.stopPropagation();runLevel(${lv.n})">Run</button>
    </div>
    <div class="level-body" id="body-${lv.n}">
      <div class="test-output info-line" id="out-${lv.n}">Not yet run.</div>
    </div>
  </div>`;
});

function toggleCard(n) {
  const b = document.getElementById(`body-${n}`);
  b.classList.toggle("open");
}

// ---- query builder ----
let rowId = 0;
function addRow(op="ADD_TASK", args="") {
  const id = rowId++;
  const opts = OPS.map(([o]) => `<option${o===op?' selected':''}>${o}</option>`).join('');
  const ph = (OPS.find(([o])=>o===op)||[])[1] || "";
  const div = document.createElement('div');
  div.className = 'query-row';
  div.id = `row-${id}`;
  div.innerHTML = `
    <span class="row-num" id="rn-${id}"></span>
    <select onchange="updatePlaceholder(${id},this.value)">${opts}</select>
    <input type="text" placeholder="${ph}" value="${args}">
    <button class="btn-icon" onclick="removeRow(${id})" title="Remove">✕</button>`;
  document.getElementById('queryList').appendChild(div);
  renumber();
}

function updatePlaceholder(id, op) {
  const ph = (OPS.find(([o])=>o===op)||[])[1] || "";
  document.querySelector(`#row-${id} input`).placeholder = ph;
}

function removeRow(id) {
  document.getElementById(`row-${id}`)?.remove();
  renumber();
}

function clearRows() {
  document.getElementById('queryList').innerHTML = '';
  rowId = 0;
}

function renumber() {
  document.querySelectorAll('.query-row').forEach((el,i) => {
    const rn = el.querySelector('.row-num');
    if (rn) rn.textContent = i+1;
  });
}

function getQueries() {
  const rows = document.querySelectorAll('.query-row');
  return Array.from(rows).map(row => {
    const op   = row.querySelector('select').value;
    const args = row.querySelector('input').value.trim();
    if (!args) return [op];
    return [op, ...args.split(/\s+/)];
  });
}

async function runQueries() {
  const queries = getQueries();
  if (!queries.length) return;
  const res = await fetch('/api/run', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({queries})
  });
  const data = await res.json();
  const box = document.getElementById('resultsBox');
  if (data.error) {
    box.innerHTML = `<span class="res-err">Error: ${esc(data.error)}</span>`;
    return;
  }
  box.innerHTML = data.results.map((r,i) =>
    `<div class="res-row"><span class="res-idx">${i+1}</span><span class="res-val">${esc(r)}</span></div>`
  ).join('') || `<span class="res-none">No results.</span>`;
}

function loadExample() {
  clearRows();
  [["ADD_TASK","write_report"],["ADD_TASK","review_code"],["LIST_TASKS"],
   ["SEARCH_TASKS","write"],["SET_PRIORITY","1","3"],["LIST_BY_PRIORITY"]
  ].forEach(([op,...args]) => addRow(op, args.join(' ')));
}

// ---- test runner ----
async function runLevel(n) {
  const badge = document.getElementById(`badge-${n}`);
  const out   = document.getElementById(`out-${n}`);
  const body  = document.getElementById(`body-${n}`);
  badge.className = 'level-badge badge-running';
  badge.textContent = '...';
  body.classList.add('open');
  out.textContent = 'Running…';
  out.className = 'test-output info-line';

  const res = await fetch('/api/test', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({level: n})
  });
  const data = await res.json();

  if (data.passed) {
    badge.className = 'level-badge badge-pass';
    badge.textContent = 'PASS';
    out.className = 'test-output pass-line';
  } else {
    badge.className = 'level-badge badge-fail';
    badge.textContent = 'FAIL';
    out.className = 'test-output fail-line';
  }
  out.textContent = data.output || (data.passed ? 'All assertions passed.' : 'Test failed.');
  updateScore();
}

async function runAll() {
  for (const lv of LEVELS) await runLevel(lv.n);
}

function updateScore() {
  const passes = document.querySelectorAll('.badge-pass').length;
  document.getElementById('scorePill').textContent = `${passes} / 6`;
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// start with a few example rows
loadExample();
</script>
</body>
</html>
"""


def run_test_level(level: int) -> dict:
    """Run a single test level, return {passed, output}."""
    import test_simulation as ts_mod
    reload(ts_mod)

    method = f"test_level_{level}"
    suite = unittest.TestSuite()
    suite.addTest(ts_mod.TestSimulate(method))

    buf = io.StringIO()
    runner = unittest.TextTestRunner(stream=buf, verbosity=2)
    result = runner.run(suite)

    passed = result.wasSuccessful()
    raw = buf.getvalue()

    # humanise the output a bit
    lines = []
    for line in raw.splitlines():
        if "OK" in line or "ok" in line.lower():
            lines.append(f"✓ {line}")
        elif "FAIL" in line or "ERROR" in line:
            lines.append(f"✗ {line}")
        elif line.strip():
            lines.append(line)

    return {"passed": passed, "output": "\n".join(lines)}


def run_queries(queries: list) -> dict:
    """Run a list of queries against simulate(), return {results} or {error}."""
    try:
        import simulation as sim_mod
        reload(sim_mod)
        results = sim_mod.simulate(queries)
        return {"results": results}
    except Exception:
        return {"error": traceback.format_exc()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # silence default access log
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/api/run":
            self._send_json(run_queries(body.get("queries", [])))
        elif self.path == "/api/test":
            level = int(body.get("level", 1))
            self._send_json(run_test_level(level))
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    print(f"Open http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
