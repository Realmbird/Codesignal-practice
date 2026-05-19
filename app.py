#!/usr/bin/env python3
"""
CodeSignal practice IDE.
Run from the repo root:  python app.py
Then open:              http://localhost:8000

- Discovers subdirectories that contain test_simulation.py
- Click a level to open its simulation.py in an editor
- Save and run the test without leaving the browser
"""
import json
import sys
import io
import os
import unittest
import importlib.util
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8000
ROOT = Path(__file__).parent


# ── backend helpers ───────────────────────────────────────────────────────────

def discover_problems():
    problems = []
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and (d / "test_simulation.py").exists():
            problems.append({"name": d.name, "path": str(d)})
    return problems


def _load_test_mod(folder: Path):
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location(
            f"ts_{folder.name}", folder / "test_simulation.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(folder))


def count_levels(problem_path: str) -> int:
    try:
        mod = _load_test_mod(Path(problem_path))
        cls = getattr(mod, "TestSimulate", None)
        return sum(1 for m in dir(cls) if m.startswith("test_level_")) if cls else 0
    except Exception:
        return 0


def run_level(problem_path: str, level: int) -> dict:
    folder = Path(problem_path)
    sys.path.insert(0, str(folder))
    try:
        mod = _load_test_mod(folder)
        method = f"test_level_{level}"
        if not hasattr(mod.TestSimulate, method):
            return {"passed": False, "output": f"No {method} found."}
        suite = unittest.TestSuite()
        suite.addTest(mod.TestSimulate(method))
        buf = io.StringIO()
        runner = unittest.TextTestRunner(stream=buf, verbosity=2)
        result = runner.run(suite)
        return {"passed": result.wasSuccessful(), "output": buf.getvalue()}
    except Exception:
        return {"passed": False, "output": traceback.format_exc()}
    finally:
        if str(folder) in sys.path:
            sys.path.remove(str(folder))


def read_code(problem_path: str) -> str:
    p = Path(problem_path) / "simulation.py"
    return p.read_text() if p.exists() else ""


def write_code(problem_path: str, code: str):
    (Path(problem_path) / "simulation.py").write_text(code)


# ── frontend ──────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CodeSignal Practice</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f1117; --panel: #1a1d2e; --border: #2d3148;
    --text: #e2e8f0; --muted: #64748b; --accent: #7c3aed;
    --pass: #4ade80; --fail: #f87171; --pass-bg: #14532d; --fail-bg: #450a0a;
  }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; }

  header { background: var(--panel); border-bottom: 1px solid var(--border); padding: 12px 20px; display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
  header h1 { font-size: 1rem; font-weight: 700; color: #a78bfa; }
  header span { font-size: 0.78rem; color: var(--muted); }
  .saved-pill { font-size: 0.72rem; padding: 2px 8px; border-radius: 10px; background: var(--pass-bg); color: var(--pass); display: none; }
  .saved-pill.show { display: inline; }

  .workspace { display: grid; grid-template-columns: 240px 1fr; flex: 1; overflow: hidden; }

  /* ── sidebar ── */
  .sidebar { border-right: 1px solid var(--border); overflow-y: auto; }
  .problem-section { border-bottom: 1px solid var(--border); }
  .problem-title { padding: 10px 14px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); display: flex; align-items: center; justify-content: space-between; }
  .run-prob-btn { font-size: 0.68rem; background: none; border: 1px solid var(--border); color: var(--muted); border-radius: 4px; padding: 2px 6px; cursor: pointer; }
  .run-prob-btn:hover { color: var(--text); border-color: var(--accent); }
  .level-item { display: flex; align-items: center; gap: 8px; padding: 8px 14px 8px 20px; cursor: pointer; font-size: 0.84rem; }
  .level-item:hover { background: #1e2235; }
  .level-item.active { background: #1e1b3a; border-right: 2px solid var(--accent); }
  .badge { font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 8px; text-transform: uppercase; }
  .badge-idle { background: #1e293b; color: var(--muted); }
  .badge-pass { background: var(--pass-bg); color: var(--pass); }
  .badge-fail { background: var(--fail-bg); color: var(--fail); }
  .badge-run  { background: #1e3a5f; color: #60a5fa; }

  /* ── editor pane ── */
  .editor-pane { display: flex; flex-direction: column; overflow: hidden; }
  .editor-toolbar { background: var(--panel); border-bottom: 1px solid var(--border); padding: 8px 14px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  .editor-toolbar .context { font-size: 0.8rem; color: var(--muted); flex: 1; }
  .editor-toolbar .context strong { color: var(--text); }
  .btn { border: none; border-radius: 5px; padding: 6px 14px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
  .btn:hover { opacity: 0.85; }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-secondary { background: #1e293b; color: #94a3b8; border: 1px solid var(--border); }
  .btn-run { background: #065f46; color: #6ee7b7; }

  .editor-area { flex: 1; overflow: hidden; position: relative; }
  textarea {
    width: 100%; height: 100%; background: #0a0c14; color: #93c5fd;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.82rem; line-height: 1.7; padding: 16px;
    border: none; outline: none; resize: none; tab-size: 4;
  }

  .output-pane { height: 220px; border-top: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; }
  .output-toolbar { background: var(--panel); border-bottom: 1px solid var(--border); padding: 6px 14px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); display: flex; align-items: center; gap: 10px; }
  .output-status { font-size: 0.72rem; padding: 1px 8px; border-radius: 8px; }
  .output-body { flex: 1; overflow-y: auto; padding: 10px 14px; font-family: 'Cascadia Code','Fira Code',monospace; font-size: 0.76rem; line-height: 1.6; white-space: pre-wrap; color: #94a3b8; }
  .output-body.pass { color: var(--pass); }
  .output-body.fail { color: var(--fail); }

  .placeholder { color: var(--muted); font-style: italic; padding: 40px; text-align: center; font-size: 0.88rem; }
</style>
</head>
<body>
<header>
  <h1>CodeSignal Practice</h1>
  <span id="subtitle">loading…</span>
  <span class="saved-pill" id="savedPill">Saved</span>
</header>
<div class="workspace">
  <div class="sidebar" id="sidebar"><div class="placeholder">Loading…</div></div>
  <div class="editor-pane" id="editorPane">
    <div class="editor-toolbar">
      <span class="context" id="editorCtx">Select a level to start editing</span>
    </div>
    <div class="editor-area">
      <textarea id="editor" spellcheck="false" placeholder="Select a level from the sidebar to load its code…" disabled></textarea>
    </div>
    <div class="output-pane">
      <div class="output-toolbar">
        Output
        <span class="output-status badge-idle badge" id="outputStatus"></span>
      </div>
      <div class="output-body" id="outputBody">Run a level to see test output.</div>
    </div>
  </div>
</div>

<script>
let problems = [];
let current = null;  // {problem, level}

// ── init ──────────────────────────────────────────────────────────────────────
async function load() {
  const res = await fetch('/api/problems');
  problems = await res.json();
  document.getElementById('subtitle').textContent =
    `${problems.length} problem${problems.length !== 1 ? 's' : ''} found`;
  renderSidebar();
}

function renderSidebar() {
  const sb = document.getElementById('sidebar');
  if (!problems.length) {
    sb.innerHTML = '<div class="placeholder">No problems found.<br>Add a folder with test_simulation.py</div>';
    return;
  }
  sb.innerHTML = problems.map(p => `
    <div class="problem-section">
      <div class="problem-title">
        ${esc(p.name)}
        <button class="run-prob-btn" onclick="runProblem('${esc(p.name)}')">Run all</button>
      </div>
      ${Array.from({length: p.levels}, (_, i) => i + 1).map(n => `
        <div class="level-item" id="item-${esc(p.name)}-${n}"
             onclick="selectLevel('${esc(p.name)}', ${n})">
          <span class="badge badge-idle" id="badge-${esc(p.name)}-${n}">idle</span>
          Level ${n}
        </div>
      `).join('')}
    </div>
  `).join('');
}

// ── level selection ───────────────────────────────────────────────────────────
async function selectLevel(prob, n) {
  // deactivate old
  if (current) {
    document.getElementById(`item-${current.problem}-${current.level}`)?.classList.remove('active');
  }
  current = {problem: prob, level: n};
  document.getElementById(`item-${prob}-${n}`)?.classList.add('active');

  // load code
  const res = await fetch(`/api/code?problem=${prob}`);
  const data = await res.json();
  const ed = document.getElementById('editor');
  ed.value = data.code;
  ed.disabled = false;

  document.getElementById('editorCtx').innerHTML =
    `<strong>${prob}</strong> &nbsp;/&nbsp; Level ${n} &mdash; editing simulation.py`;

  // update toolbar buttons
  renderToolbar(prob, n);
}

function renderToolbar(prob, n) {
  const tb = document.querySelector('.editor-toolbar');
  // remove old buttons
  tb.querySelectorAll('.btn').forEach(b => b.remove());

  const save = document.createElement('button');
  save.className = 'btn btn-secondary';
  save.textContent = 'Save';
  save.onclick = () => saveCode();

  const run = document.createElement('button');
  run.className = 'btn btn-run';
  run.textContent = `▶ Test Level ${n}`;
  run.onclick = () => saveAndTest(prob, n);

  tb.appendChild(save);
  tb.appendChild(run);
}

// ── save & test ───────────────────────────────────────────────────────────────
async function saveCode() {
  if (!current) return;
  const code = document.getElementById('editor').value;
  await fetch('/api/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({problem: current.problem, code}),
  });
  const pill = document.getElementById('savedPill');
  pill.classList.add('show');
  setTimeout(() => pill.classList.remove('show'), 1500);
}

async function saveAndTest(prob, n) {
  await saveCode();
  const badge = document.getElementById(`badge-${prob}-${n}`);
  badge.className = 'badge badge-run';
  badge.textContent = '…';
  document.getElementById('outputStatus').textContent = 'running';
  document.getElementById('outputStatus').className = 'output-status badge badge-run';
  document.getElementById('outputBody').textContent = 'Running…';
  document.getElementById('outputBody').className = 'output-body';

  const res = await fetch('/api/test', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({problem: prob, level: n}),
  });
  const data = await res.json();

  badge.className = `badge ${data.passed ? 'badge-pass' : 'badge-fail'}`;
  badge.textContent = data.passed ? 'PASS' : 'FAIL';

  const status = document.getElementById('outputStatus');
  status.className = `output-status badge ${data.passed ? 'badge-pass' : 'badge-fail'}`;
  status.textContent = data.passed ? 'PASS' : 'FAIL';

  const body = document.getElementById('outputBody');
  body.className = `output-body ${data.passed ? 'pass' : 'fail'}`;
  body.textContent = data.output;
}

async function runProblem(prob) {
  const p = problems.find(x => x.name === prob);
  if (!p) return;
  for (let n = 1; n <= p.levels; n++) {
    await selectLevel(prob, n);
    await saveAndTest(prob, n);
  }
}

// ── tab key in editor ─────────────────────────────────────────────────────────
document.getElementById('editor').addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const el = e.target;
    const start = el.selectionStart;
    el.value = el.value.slice(0, start) + '    ' + el.value.slice(el.selectionEnd);
    el.selectionStart = el.selectionEnd = start + 4;
  }
});

function esc(s) { return String(s).replace(/[^a-zA-Z0-9_-]/g, '_'); }

load();
</script>
</body>
</html>
"""


# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _prob_by_name(self, name):
        return next((p for p in discover_problems() if p["name"] == name), None)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/api/problems":
            probs = discover_problems()
            for p in probs:
                p["levels"] = count_levels(p["path"])
            self._json(probs)

        elif self.path.startswith("/api/code"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            name = qs.get("problem", [""])[0]
            prob = self._prob_by_name(name)
            if prob:
                self._json({"code": read_code(prob["path"])})
            else:
                self._json({"code": ""}, 404)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/api/test":
            prob = self._prob_by_name(body["problem"])
            if not prob:
                self._json({"passed": False, "output": "Problem not found."})
                return
            self._json(run_level(prob["path"], int(body["level"])))

        elif self.path == "/api/save":
            prob = self._prob_by_name(body["problem"])
            if not prob:
                self._json({"ok": False}, 404)
                return
            write_code(prob["path"], body["code"])
            self._json({"ok": True})

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
