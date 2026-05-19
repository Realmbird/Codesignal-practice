#!/usr/bin/env python3
"""
CodeSignal practice IDE.
Run from the repo root:  python app.py
Then open:              http://localhost:8000
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
from urllib.parse import urlparse, parse_qs

PORT = 8000
ROOT = Path(__file__).parent
EXCLUDE = {"test_simulation.py", "__init__.py"}


# ── helpers ───────────────────────────────────────────────────────────────────

def discover_problems():
    problems = []
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and (d / "test_simulation.py").exists():
            problems.append({"name": d.name, "path": str(d)})
    return problems


def list_files(problem_path: str):
    """All .py files in the folder except test_simulation.py."""
    folder = Path(problem_path)
    return sorted(
        f.name for f in folder.glob("*.py")
        if f.name not in EXCLUDE and not f.name.startswith("__")
    )


def _load_module_from_file(folder: Path, filename: str):
    """Load a module from an arbitrary .py file, with the folder on sys.path."""
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location(
            f"_{folder.name}_{filename}", folder / filename
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if str(folder) in sys.path:
            sys.path.remove(str(folder))


def count_levels(problem_path: str) -> int:
    try:
        folder = Path(problem_path)
        sys.path.insert(0, str(folder))
        mod = _load_module_from_file(folder, "test_simulation.py")
        cls = getattr(mod, "TestSimulate", None)
        return sum(1 for m in dir(cls) if m.startswith("test_level_")) if cls else 0
    except Exception:
        return 0
    finally:
        if str(folder) in sys.path:
            sys.path.remove(str(folder))


def run_level(problem_path: str, filename: str, level: int) -> dict:
    """Run test_level_N, but patch the test's 'simulation' import to use filename."""
    folder = Path(problem_path)
    sys.path.insert(0, str(folder))
    try:
        # load the user's chosen file as 'simulation' so the test import works
        target = _load_module_from_file(folder, filename)
        sys.modules["simulation"] = target

        mod = _load_module_from_file(folder, "test_simulation.py")
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
        sys.modules.pop("simulation", None)
        if str(folder) in sys.path:
            sys.path.remove(str(folder))


def run_queries(problem_path: str, filename: str, queries: list) -> dict:
    """Run simulate(queries) from the chosen file."""
    folder = Path(problem_path)
    try:
        mod = _load_module_from_file(folder, filename)
        fn = getattr(mod, "simulate", None)
        if fn is None:
            return {"error": f"No simulate() function found in {filename}"}
        results = fn(queries)
        return {"results": [str(r) for r in (results or [])]}
    except Exception:
        return {"error": traceback.format_exc()}


# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CodeSignal Practice</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:#0f1117; --panel:#1a1d2e; --border:#2d3148;
    --text:#e2e8f0; --muted:#64748b; --accent:#7c3aed;
    --pass:#4ade80; --fail:#f87171; --pass-bg:#14532d; --fail-bg:#450a0a;
  }
  body { font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); height:100vh; display:flex; flex-direction:column; overflow:hidden; }

  /* header */
  header { background:var(--panel); border-bottom:1px solid var(--border); padding:10px 18px; display:flex; align-items:center; gap:10px; flex-shrink:0; }
  header h1 { font-size:.95rem; font-weight:700; color:#a78bfa; }
  header .sub { font-size:.75rem; color:var(--muted); }
  .pill { font-size:.68rem; padding:2px 8px; border-radius:8px; }
  .pill-saved { background:var(--pass-bg); color:var(--pass); display:none; }
  .pill-saved.show { display:inline; }

  /* layout */
  .workspace { display:grid; grid-template-columns:210px 1fr 300px; flex:1; overflow:hidden; }

  /* ── sidebar ── */
  .sidebar { border-right:1px solid var(--border); overflow-y:auto; display:flex; flex-direction:column; }
  .prob-hdr { padding:9px 14px; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--border); }
  .run-all-btn { font-size:.65rem; background:none; border:1px solid var(--border); color:var(--muted); border-radius:4px; padding:2px 6px; cursor:pointer; }
  .run-all-btn:hover { color:var(--text); }
  .lvl-item { display:flex; align-items:center; gap:8px; padding:8px 14px 8px 18px; cursor:pointer; font-size:.82rem; border-bottom:1px solid #161929; }
  .lvl-item:hover { background:#1e2235; }
  .lvl-item.active { background:#1e1b3a; border-right:2px solid var(--accent); }
  .badge { font-size:.6rem; font-weight:700; padding:1px 6px; border-radius:8px; text-transform:uppercase; min-width:44px; text-align:center; }
  .idle { background:#1e293b; color:var(--muted); }
  .pass { background:var(--pass-bg); color:var(--pass); }
  .fail { background:var(--fail-bg); color:var(--fail); }
  .running { background:#1e3a5f; color:#60a5fa; }

  /* ── editor column ── */
  .editor-col { display:flex; flex-direction:column; overflow:hidden; border-right:1px solid var(--border); }

  /* file tabs */
  .file-tabs { background:var(--panel); border-bottom:1px solid var(--border); display:flex; align-items:center; gap:0; overflow-x:auto; flex-shrink:0; min-height:36px; }
  .file-tab { padding:8px 14px; font-size:.76rem; cursor:pointer; white-space:nowrap; color:var(--muted); border-right:1px solid var(--border); display:flex; align-items:center; gap:6px; }
  .file-tab:hover { color:var(--text); background:#1e2235; }
  .file-tab.active { color:var(--text); background:var(--bg); border-bottom:2px solid var(--accent); }
  .file-tab .del { color:var(--muted); font-size:.7rem; cursor:pointer; padding:0 2px; border-radius:2px; }
  .file-tab .del:hover { color:var(--fail); }
  .new-file-btn { padding:8px 12px; font-size:.76rem; color:var(--muted); cursor:pointer; background:none; border:none; white-space:nowrap; }
  .new-file-btn:hover { color:var(--text); }

  /* editor */
  .editor-wrap { flex:1; overflow:hidden; position:relative; }
  textarea.code {
    width:100%; height:100%; background:#0a0c14; color:#93c5fd;
    font-family:'Cascadia Code','Fira Code','Consolas',monospace;
    font-size:.8rem; line-height:1.7; padding:14px 16px;
    border:none; outline:none; resize:none; tab-size:4;
  }

  /* test output strip */
  .test-strip { height:180px; border-top:1px solid var(--border); display:flex; flex-direction:column; flex-shrink:0; }
  .strip-hdr { background:var(--panel); border-bottom:1px solid var(--border); padding:5px 12px; font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); display:flex; align-items:center; gap:8px; }
  .strip-body { flex:1; overflow-y:auto; padding:8px 12px; font-family:'Cascadia Code','Fira Code',monospace; font-size:.72rem; line-height:1.6; white-space:pre-wrap; color:#64748b; }
  .strip-body.pass-out { color:var(--pass); }
  .strip-body.fail-out { color:var(--fail); }

  /* action bar */
  .action-bar { background:var(--panel); border-top:1px solid var(--border); padding:7px 12px; display:flex; gap:7px; flex-shrink:0; align-items:center; }
  .btn { border:none; border-radius:5px; padding:5px 13px; font-size:.78rem; font-weight:600; cursor:pointer; }
  .btn:hover { opacity:.85; }
  .btn-save { background:#1e293b; color:#94a3b8; border:1px solid var(--border); }
  .btn-test { background:#065f46; color:#6ee7b7; }
  .btn-run  { background:#1e3a5f; color:#93c5fd; }
  .active-file-label { font-size:.72rem; color:var(--muted); flex:1; }

  /* ── example runner column ── */
  .runner-col { display:flex; flex-direction:column; overflow:hidden; }
  .runner-hdr { background:var(--panel); border-bottom:1px solid var(--border); padding:9px 14px; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); display:flex; align-items:center; justify-content:space-between; flex-shrink:0; }
  .runner-body { flex:1; overflow-y:auto; padding:10px; display:flex; flex-direction:column; gap:6px; }

  .qrow { display:flex; gap:5px; align-items:center; }
  .qrow select { background:#0a0c14; border:1px solid var(--border); color:var(--text); border-radius:4px; padding:4px 6px; font-size:.74rem; min-width:150px; outline:none; }
  .qrow input { flex:1; min-width:0; background:#0a0c14; border:1px solid var(--border); color:var(--text); border-radius:4px; padding:4px 7px; font-size:.74rem; outline:none; }
  .qrow input::placeholder { color:var(--muted); }
  .del-btn { background:none; border:none; color:var(--muted); cursor:pointer; font-size:.85rem; padding:0 4px; border-radius:3px; }
  .del-btn:hover { color:var(--fail); }
  .row-num { font-size:.65rem; color:var(--muted); min-width:16px; text-align:right; }

  .runner-actions { padding:8px 10px; display:flex; gap:6px; border-top:1px solid var(--border); flex-shrink:0; }
  .btn-add  { background:#1e293b; color:#94a3b8; border:1px solid var(--border); }

  .results-box { margin:0 10px 10px; background:#0a0c14; border:1px solid var(--border); border-radius:5px; padding:10px; font-family:'Cascadia Code','Fira Code',monospace; font-size:.74rem; line-height:1.7; min-height:80px; flex-shrink:0; }
  .res-row { display:flex; gap:8px; }
  .res-i { color:var(--muted); min-width:20px; }
  .res-v { color:#93c5fd; }
  .res-none { color:var(--muted); font-style:italic; }
  .res-err  { color:var(--fail); white-space:pre-wrap; font-size:.68rem; }

  .placeholder { color:var(--muted); padding:30px; text-align:center; font-size:.85rem; font-style:italic; }
</style>
</head>
<body>
<header>
  <h1>CodeSignal Practice</h1>
  <span class="sub" id="subtitle">loading…</span>
  <span class="pill pill-saved" id="savedPill">Saved</span>
</header>

<div class="workspace">

  <!-- SIDEBAR -->
  <div class="sidebar" id="sidebar">
    <div class="placeholder">Loading…</div>
  </div>

  <!-- EDITOR -->
  <div class="editor-col">
    <div class="file-tabs" id="fileTabs">
      <span class="file-tab active" style="color:var(--muted);cursor:default">No file open</span>
    </div>
    <div class="editor-wrap">
      <textarea class="code" id="editor" spellcheck="false"
        placeholder="Click a level in the sidebar to begin." disabled></textarea>
    </div>
    <div class="action-bar">
      <span class="active-file-label" id="activeFileLabel">—</span>
      <button class="btn btn-save" onclick="saveFile()">Save</button>
      <button class="btn btn-test" id="testBtn" onclick="saveAndTest()" disabled>▶ Test</button>
    </div>
    <div class="test-strip">
      <div class="strip-hdr">
        Test output
        <span class="badge idle" id="testBadge"></span>
      </div>
      <div class="strip-body" id="testBody">Run a test to see output.</div>
    </div>
  </div>

  <!-- EXAMPLE RUNNER -->
  <div class="runner-col">
    <div class="runner-hdr">
      Example runner
      <button class="btn btn-add" onclick="clearQueries()" style="font-size:.65rem;padding:2px 7px;">Clear</button>
    </div>
    <div class="runner-body" id="queryRows"></div>
    <div class="runner-actions">
      <button class="btn btn-add" onclick="addQuery()">+ Query</button>
      <button class="btn btn-add" onclick="loadExample()">Load example</button>
      <button class="btn btn-run" onclick="runQueries()">▶ Run</button>
    </div>
    <div class="results-box" id="resultsBox">
      <span class="res-none">No results yet.</span>
    </div>
  </div>
</div>

<script>
const OPS = [
  ["ADD_TASK","name"],["GET_TASK","id"],["DELETE_TASK","id"],
  ["LIST_TASKS",""],["SEARCH_TASKS","prefix"],["UPDATE_TASK","id  new_name"],
  ["SET_PRIORITY","id  priority"],["LIST_BY_PRIORITY",""],
  ["ADD_TAG","id  tag"],["SEARCH_BY_TAG","tag"],
  ["SET_DUE","id  timestamp"],["LIST_OVERDUE","timestamp"],
  ["SET_STATUS","id  status"],["LIST_BY_STATUS","status"],
  ["CONCURRENT_ADD","name1,name2,..."],["ASYNC_GET","id1,id2,..."],
];

let problems = [];
let current = null;   // {problem, level, file}
let qId = 0;

// ── init ──────────────────────────────────────────────────────────────────────
async function init() {
  const res = await fetch('/api/problems');
  problems = await res.json();
  document.getElementById('subtitle').textContent =
    `${problems.length} problem${problems.length!==1?'s':''} found`;
  renderSidebar();
}

function renderSidebar() {
  const sb = document.getElementById('sidebar');
  if (!problems.length) {
    sb.innerHTML = '<div class="placeholder">No problems found.</div>';
    return;
  }
  sb.innerHTML = problems.map(p => `
    <div>
      <div class="prob-hdr">
        ${esc(p.name)}
        <button class="run-all-btn" onclick="runAllLevels('${esc(p.name)}')">Run all</button>
      </div>
      ${Array.from({length:p.levels},(_,i)=>i+1).map(n=>`
        <div class="lvl-item" id="item-${esc(p.name)}-${n}"
             onclick="selectLevel('${esc(p.name)}',${n})">
          <span class="badge idle" id="badge-${esc(p.name)}-${n}">idle</span>
          Level ${n}
        </div>`).join('')}
    </div>`).join('');
}

// ── file tabs ─────────────────────────────────────────────────────────────────
async function renderFileTabs(probName) {
  const res = await fetch(`/api/files?problem=${probName}`);
  const {files} = await res.json();
  const tabs = document.getElementById('fileTabs');
  tabs.innerHTML = files.map(f => `
    <div class="file-tab ${f===current?.file?'active':''}" id="tab-${probName}-${CSS.escape(f)}"
         onclick="switchFile('${probName}','${f}')">
      ${f}
      ${f!=='simulation.py'?`<span class="del" onclick="event.stopPropagation();deleteFile('${probName}','${f}')">✕</span>`:''}
    </div>`).join('');
  tabs.innerHTML += `<button class="new-file-btn" onclick="newFile('${probName}')">+ New file</button>`;
}

async function switchFile(probName, filename) {
  if (current) current.file = filename;
  const res = await fetch(`/api/code?problem=${probName}&file=${encodeURIComponent(filename)}`);
  const {code} = await res.json();
  const ed = document.getElementById('editor');
  ed.value = code; ed.disabled = false;
  document.getElementById('activeFileLabel').textContent = `${probName} / ${filename}`;
  document.getElementById('testBtn').disabled = !current?.level;
  updateTabActive(probName, filename);
}

function updateTabActive(probName, filename) {
  document.querySelectorAll('.file-tab').forEach(t=>t.classList.remove('active'));
  document.getElementById(`tab-${probName}-${CSS.escape(filename)}`)?.classList.add('active');
}

async function newFile(probName) {
  const name = prompt('New filename (e.g. attempt2.py):');
  if (!name) return;
  const fname = name.endsWith('.py') ? name : name+'.py';
  await fetch('/api/save', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({problem:probName, file:fname, code:'import threading\nimport asyncio\n\n\ndef simulate(queries):\n    results = []\n    for q in queries:\n        pass  # TODO\n    return results\n'})
  });
  await renderFileTabs(probName);
  await switchFile(probName, fname);
}

async function deleteFile(probName, filename) {
  if (!confirm(`Delete ${filename}?`)) return;
  await fetch('/api/delete', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({problem:probName, file:filename})
  });
  if (current?.file === filename) {
    current.file = 'simulation.py';
    await switchFile(probName, 'simulation.py');
  }
  await renderFileTabs(probName);
}

// ── level selection ───────────────────────────────────────────────────────────
async function selectLevel(probName, n) {
  if (current) document.getElementById(`item-${current.problem}-${current.level}`)?.classList.remove('active');
  const file = current?.problem===probName ? (current.file||'simulation.py') : 'simulation.py';
  current = {problem:probName, level:n, file};
  document.getElementById(`item-${probName}-${n}`).classList.add('active');
  document.getElementById('testBtn').disabled = false;
  document.getElementById('testBtn').textContent = `▶ Test Level ${n}`;
  await renderFileTabs(probName);
  await switchFile(probName, current.file);
}

// ── save / test ───────────────────────────────────────────────────────────────
async function saveFile() {
  if (!current) return;
  const code = document.getElementById('editor').value;
  await fetch('/api/save', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({problem:current.problem, file:current.file, code})
  });
  const pill = document.getElementById('savedPill');
  pill.classList.add('show');
  setTimeout(()=>pill.classList.remove('show'), 1500);
}

async function saveAndTest() {
  if (!current) return;
  await saveFile();
  const {problem, file, level} = current;
  const badge = document.getElementById(`badge-${problem}-${level}`);
  badge.className='badge running'; badge.textContent='…';
  const tb = document.getElementById('testBadge');
  tb.className='badge running'; tb.textContent='running';
  document.getElementById('testBody').textContent='Running…';
  document.getElementById('testBody').className='strip-body';

  const res = await fetch('/api/test', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({problem, file, level})
  });
  const data = await res.json();
  const ok = data.passed;
  badge.className=`badge ${ok?'pass':'fail'}`; badge.textContent=ok?'PASS':'FAIL';
  tb.className=`badge ${ok?'pass':'fail'}`; tb.textContent=ok?'PASS':'FAIL';
  document.getElementById('testBody').className=`strip-body ${ok?'pass-out':'fail-out'}`;
  document.getElementById('testBody').textContent=data.output;
}

async function runAllLevels(probName) {
  const p = problems.find(x=>x.name===probName);
  if (!p) return;
  for (let n=1; n<=p.levels; n++) { await selectLevel(probName,n); await saveAndTest(); }
}

// ── example runner ────────────────────────────────────────────────────────────
function addQuery(op='ADD_TASK', args='') {
  const id = qId++;
  const opts = OPS.map(([o])=>`<option${o===op?' selected':''}>${o}</option>`).join('');
  const ph = (OPS.find(([o])=>o===op)||[])[1]||'';
  const div = document.createElement('div');
  div.className='qrow'; div.id=`qr-${id}`;
  div.innerHTML=`
    <span class="row-num" id="rn-${id}"></span>
    <select onchange="updatePh(${id},this.value)">${opts}</select>
    <input type="text" placeholder="${ph}" value="${args}">
    <button class="del-btn" onclick="removeQuery(${id})">✕</button>`;
  document.getElementById('queryRows').appendChild(div);
  renumber();
}

function updatePh(id, op) {
  const ph=(OPS.find(([o])=>o===op)||[])[1]||'';
  document.querySelector(`#qr-${id} input`).placeholder=ph;
}
function removeQuery(id) { document.getElementById(`qr-${id}`)?.remove(); renumber(); }
function renumber() { document.querySelectorAll('.qrow').forEach((el,i)=>{ const rn=el.querySelector('.row-num'); if(rn) rn.textContent=i+1; }); }
function clearQueries() { document.getElementById('queryRows').innerHTML=''; qId=0; }

function getQueries() {
  return Array.from(document.querySelectorAll('.qrow')).map(row=>{
    const op=row.querySelector('select').value;
    const args=row.querySelector('input').value.trim();
    return args ? [op,...args.split(/\s+/)] : [op];
  });
}

async function runQueries() {
  if (!current) { alert('Select a level first.'); return; }
  const queries = getQueries();
  if (!queries.length) return;
  await saveFile();
  const res = await fetch('/api/run', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({problem:current.problem, file:current.file, queries})
  });
  const data = await res.json();
  const box = document.getElementById('resultsBox');
  if (data.error) {
    box.innerHTML=`<span class="res-err">${esc(data.error)}</span>`;
    return;
  }
  if (!data.results?.length) { box.innerHTML='<span class="res-none">No results.</span>'; return; }
  box.innerHTML=data.results.map((r,i)=>
    `<div class="res-row"><span class="res-i">${i+1}</span><span class="res-v">${esc(r)}</span></div>`
  ).join('');
}

function loadExample() {
  clearQueries();
  [['ADD_TASK','write_report'],['ADD_TASK','review_code'],['LIST_TASKS',''],
   ['SEARCH_TASKS','write'],['SET_PRIORITY','1 3'],['LIST_BY_PRIORITY','']
  ].forEach(([op,args])=>addQuery(op,args));
}

// ── editor tab key ────────────────────────────────────────────────────────────
document.getElementById('editor').addEventListener('keydown', e=>{
  if (e.key==='Tab') {
    e.preventDefault();
    const el=e.target, s=el.selectionStart;
    el.value=el.value.slice(0,s)+'    '+el.value.slice(el.selectionEnd);
    el.selectionStart=el.selectionEnd=s+4;
  }
});

function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

init();
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

    def _prob(self, name):
        return next((p for p in discover_problems() if p["name"] == name), None)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/api/problems":
            probs = discover_problems()
            for p in probs:
                p["levels"] = count_levels(p["path"])
            self._json(probs)

        elif parsed.path == "/api/files":
            prob = self._prob(qs.get("problem", [""])[0])
            if prob:
                self._json({"files": list_files(prob["path"])})
            else:
                self._json({"files": []}, 404)

        elif parsed.path == "/api/code":
            prob = self._prob(qs.get("problem", [""])[0])
            fname = qs.get("file", ["simulation.py"])[0]
            if prob:
                p = Path(prob["path"]) / fname
                self._json({"code": p.read_text() if p.exists() else ""})
            else:
                self._json({"code": ""}, 404)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        parsed = urlparse(self.path)

        if parsed.path == "/api/test":
            prob = self._prob(body["problem"])
            if not prob:
                self._json({"passed": False, "output": "Problem not found."}); return
            self._json(run_level(prob["path"], body.get("file", "simulation.py"), int(body["level"])))

        elif parsed.path == "/api/run":
            prob = self._prob(body["problem"])
            if not prob:
                self._json({"error": "Problem not found."}); return
            self._json(run_queries(prob["path"], body.get("file", "simulation.py"), body["queries"]))

        elif parsed.path == "/api/save":
            prob = self._prob(body["problem"])
            if not prob:
                self._json({"ok": False}, 404); return
            fname = body.get("file", "simulation.py")
            if ".." in fname or "/" in fname:
                self._json({"ok": False, "error": "Invalid filename"}, 400); return
            (Path(prob["path"]) / fname).write_text(body["code"])
            self._json({"ok": True})

        elif parsed.path == "/api/delete":
            prob = self._prob(body["problem"])
            if not prob:
                self._json({"ok": False}, 404); return
            fname = body.get("file", "")
            if fname in ("simulation.py", "test_simulation.py") or ".." in fname or "/" in fname:
                self._json({"ok": False, "error": "Cannot delete this file"}); return
            target = Path(prob["path"]) / fname
            if target.exists():
                target.unlink()
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
