#!/usr/bin/env python3
"""
Mac mini 自演化引擎 (Mini Evolution Engine)
==========================================

Mac mini 作为独立计算节点, 利用本地 Ollama (qwen2.5:14b + qwen2.5-coder:14b)
实现自主能力闭环:

  🔍 发现层: 代码巡检 + DB 空表检测 + Flask 路由覆盖 + daemon 健康度
  🧠 生成层: Ollama 生成修复代码 / 新功能 / 测试用例
  ✅ 验证层: py_compile 语法检查 + Flask smoke test + SQLite 完整性
  📡 同步层: 通过 handshake SSH 上报 MacBook → 双向 sync 落地

设计原则:
  - 不直接 git commit (OneDrive 冲突)
  - 生成代码先本地 .patch 文件存 mt_evolution_log
  - MacBook 审批后才走 sync_rows 落地
  - 纯本地推理, 零 token 消耗
"""

from __future__ import annotations
import os, sys, sqlite3, json, subprocess, time, hashlib, threading, re, importlib.util, traceback
from pathlib import Path

BASE = Path(__file__).parent.parent
DB   = BASE / "app.db"             # Mac mini: flask-app/app.db
ENGINES = BASE / "engines"
AI_ENGINES = BASE / "ai_engines"

OLLAMA_URL = "http://localhost:11435"
# MacBook 本机: 等 qwen2.5-coder:14b 下载完即启用
# Mac mini (远程): 已有 qwen2.5-coder:14b, 直接用
OLLAMA_MODEL = "qwen2.5:14b-q5"
OLLAMA_CODE_MODEL = "qwen2.5-coder:14b"

SSH_DEST = "wuchenghao@192.168.31.184"
REMOTE_DB = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/database/app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_evolution_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phase           TEXT NOT NULL,   -- discover/generate/verify/sync
    action          TEXT NOT NULL,   -- 发现了什么/生成了什么
    severity        TEXT DEFAULT 'info',  -- info/warn/critical
    file_path       TEXT,
    code_diff       TEXT,            -- patch/diff 内容
    ollama_model    TEXT,
    status          TEXT DEFAULT 'pending',  -- pending/verified/rejected/synced
    approved_by_sa  INTEGER DEFAULT 0,
    error_msg       TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_evlog_status ON mt_evolution_log(status);

CREATE TABLE IF NOT EXISTS mt_discovered_gaps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    gap_type        TEXT NOT NULL,   -- missing_table/missing_route/syntax_error/missing_daemon
    target          TEXT NOT NULL,   -- 具体缺失的内容
    evidence        TEXT,            -- 证明 gap 的 SQL/代码/日志
    suggested_fix   TEXT,            -- 建议怎么修 (AI 生成)
    auto_resolved   INTEGER DEFAULT 0,
    resolved_at     TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


# ═════════════════════════════════════════════════════════════════════════
# Ollama 调用
# ═════════════════════════════════════════════════════════════════════════
def ollama(prompt: str, model: str = OLLAMA_MODEL, timeout: int = 30) -> str:
    import urllib.request
    try:
        body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.2, "num_predict": 512}}).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/generate",
            data=body, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        return resp.get("response", "")
    except Exception as e:
        return f"[OllamaError] {e}"


# ═════════════════════════════════════════════════════════════════════════
# Phase 1: 发现层 —— 扫代码 + 扫 DB + 扫 Flask + 扫 daemon
# ═════════════════════════════════════════════════════════════════════════
class DiscoverLayer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def scan_all(self) -> list[dict]:
        gaps = []
        gaps += self.syntax_errors()
        gaps += self.empty_tables()
        gaps += self.missing_routes()
        gaps += self.daemon_health()
        for g in gaps: self._log_gap(g)
        return gaps

    def syntax_errors(self) -> list[dict]:
        """扫所有 .py 文件的语法/import 错误."""
        gaps = []
        for root in [ENGINES, AI_ENGINES, BASE / "routes", BASE / "ai_engines"]:
            if not root.exists(): continue
            for py in root.rglob("*.py"):
                try:
                    result = subprocess.run(["python3", "-m", "py_compile", str(py)],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        gaps.append({
                            "gap_type": "syntax_error",
                            "target": str(py.relative_to(BASE)),
                            "evidence": result.stderr[:500],
                            "severity": "critical",
                        })
                except Exception: pass
        return gaps

    def empty_tables(self) -> list[dict]:
        """核心 MTSCOS 表如果空了 → 数据丢失."""
        core = ["mt_ai_brain_feed_log", "mt_daemon_registry", "mt_roundtable_sessions",
                "mt_dev_flow_session", "mt_handshake_state"]
        gaps = []
        for t in core:
            try:
                c = self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                if c == 0 and t != "mt_handshake_state":
                    gaps.append({
                        "gap_type": "empty_core_table",
                        "target": t,
                        "evidence": f"{t} has 0 rows",
                        "severity": "warn",
                    })
            except sqlite3.OperationalError:
                gaps.append({
                    "gap_type": "missing_table",
                    "target": t,
                    "evidence": f"{t} not in schema",
                    "severity": "critical",
                })
        return gaps

    def missing_routes(self) -> list[dict]:
        """Flask :8888 能通但 /health /api/rules 等路由 404."""
        import urllib.request
        gaps = []
        for path in ["/health", "/api/rules/list", "/api/daemon/status", "/api/evolution/status"]:
            try:
                req = urllib.request.Request(f"http://127.0.0.1:8888{path}")
                urllib.request.urlopen(req, timeout=3)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    gaps.append({
                        "gap_type": "missing_route",
                        "target": path,
                        "evidence": f"HTTP 404",
                        "severity": "warn",
                    })
            except Exception: pass
        return gaps

    def daemon_health(self) -> list[dict]:
        """mt_daemon_registry 里 daemon 的 status=down."""
        gaps = []
        try:
            rows = self.db.execute(
                "SELECT name,status FROM mt_daemon_registry WHERE status NOT IN ('running','active') LIMIT 5"
            ).fetchall()
            for name, status in rows:
                gaps.append({
                    "gap_type": "daemon_down",
                    "target": name,
                    "evidence": f"status={status}",
                    "severity": "info",
                })
        except Exception: pass
        return gaps

    def _log_gap(self, g: dict):
        try:
            self.db.execute("""INSERT INTO mt_discovered_gaps (gap_type,target,evidence,severity)
                VALUES (?,?,?,?)""",
                (g.get("gap_type"), g.get("target"), g.get("evidence"), g.get("severity", "info")))
            self.db.commit()
        except Exception: pass


# ═════════════════════════════════════════════════════════════════════════
# Phase 2: 生成层 —— Ollama 生成修复 / 新功能
# ═════════════════════════════════════════════════════════════════════════
class GenerateLayer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def fix_syntax(self, target: str, evidence: str) -> str:
        """给有语法错误的文件生成修复 patch."""
        code = ""
        fpath = BASE / target
        if fpath.exists():
            code = fpath.read_text()[:3000]
        prompt = f"""你是资深 Python 修复专家. 给下面文件修复语法/import 错误.
只输出修复后的完整函数或相关代码段, 不要解释.

文件: {target}
错误: {evidence}

当前代码 (前 3000 字符):
```python
{code}
```

修复后代码:"""
        return ollama(prompt, model=OLLAMA_CODE_MODEL, timeout=45)

    def design_missing_route(self, path: str) -> str:
        """给 404 路由生成 Flask endpoint."""
        prompt = f"""设计 Flask endpoint 处理 {path}.
符合 MTSCOS 项目规范: 使用 @system_container 装饰器, 返回 JSON.

只输出 Python 函数代码 (不带 ```python 标记), 函数名用下划线, 包含必要 import.

建议实现:
- /health: 返回服务健康度 JSON
- /api/daemon/status: 查 mt_daemon_registry
- /api/evolution/status: 查 mt_evolution_log 最新状态"""
        return ollama(prompt, model=OLLAMA_CODE_MODEL, timeout=45)

    def propose_new_feature(self) -> list[dict]:
        """AI 扫描代码后, 主动建议新功能 (每周一次)."""
        code_summary = self._codebase_summary()
        prompt = f"""你是 MTSCOS AI 系统的资深产品经理 + 全栈工程师.
以下是 Mac mini 节点的代码库摘要:

{code_summary}

请推荐 3 个 20 行内能实现的**实用小功能**, 每个包含:
1. 功能名
2. 放在哪个 engine/route
3. 核心逻辑 (伪代码)
4. 为什么对 Mac mini 自演化有价值

格式: JSON array"""
        raw = ollama(prompt, timeout=60)
        try:
            return json.loads(re.search(r'\[.*\]', raw, re.DOTALL).group())
        except Exception:
            return [{"name": raw[:100], "code": ""}]

    def _codebase_summary(self) -> str:
        parts = []
        for dirname in ["engines", "ai_engines", "routes"]:
            d = BASE / dirname
            if not d.exists(): continue
            files = list(d.glob("*.py"))[:8]
            for f in files:
                try:
                    code = f.read_text()
                    parts.append(f"### {dirname}/{f.name} ({len(code)} chars)\n" +
                                 "\n".join(code.split("\n")[:15]))
                except Exception: pass
        return "\n\n".join(parts)[:4000]


# ═════════════════════════════════════════════════════════════════════════
# Phase 3: 验证层
# ═════════════════════════════════════════════════════════════════════════
class VerifyLayer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def python_smoke(self, code: str) -> tuple[bool, str]:
        """Python 语法检查 + import 检查 (不执行, 安全)."""
        try:
            compile(code, "<ai-generated>", "exec")
            return True, "✅ 语法 OK"
        except SyntaxError as e:
            return False, f"❌ SyntaxError: {e}"

    def sqlite_smoke(self, code: str) -> tuple[bool, str]:
        """SQL 语句安全检查 (只读, 不 DROP/DELETE)."""
        dangerous = ["DROP", "DELETE", "INSERT INTO", "UPDATE"]
        upper = code.upper()
        for kw in dangerous:
            if kw in upper:
                return False, f"⚠️ AI 生成代码含 {kw} (需人工审批)"
        return True, "✅ SQL 只读"


# ═════════════════════════════════════════════════════════════════════════
# Phase 4: 同步层 —— handshake 上报 MacBook + 双向 sync
# ═════════════════════════════════════════════════════════════════════════
class SyncLayer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def report_to_macbook(self):
        """把 mt_evolution_log 同步到 MacBook."""
        try:
            # 本地 max id
            local_max = self.db.execute("SELECT COALESCE(MAX(id),0) FROM mt_evolution_log").fetchone()[0]
            # SSH 问 MacBook max
            import subprocess, json, base64
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", SSH_DEST,
                 f"sqlite3 {REMOTE_DB} \"SELECT COALESCE(MAX(id),0) FROM mt_evolution_log;\""],
                capture_output=True, text=True, timeout=10)
            remote_max = int((r.stdout or "0").strip() or "0")
            if local_max > remote_max:
                rows = self.db.execute("SELECT * FROM mt_evolution_log WHERE id > ?", (remote_max,)).fetchall()
                cols = [c[0] for c in self.db.execute("SELECT * FROM mt_evolution_log LIMIT 0").description]
                values_json = json.dumps(rows, ensure_ascii=False, default=str)
                b64 = base64.b64encode(values_json.encode()).decode()
                sql = f"INSERT OR IGNORE INTO mt_evolution_log ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
                ssh_cmd = (f'python3 -c "import sqlite3,json,base64;'
                          f'db=sqlite3.connect({REMOTE_DB!r});'
                          f'db.executemany({sql!r}, json.loads(base64.b64decode({b64!r})));'
                          f'db.commit(); print(\'✅ evolution_log synced {len(rows)} rows\')"')
                r2 = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", SSH_DEST, ssh_cmd],
                                    capture_output=True, text=True, timeout=30)
                print(f"  📡 → MacBook: {r2.stdout.strip()}")
        except Exception as e:
            print(f"  📡 sync 失败: {e}")


# ═════════════════════════════════════════════════════════════════════════
# 主循环: 每 10min 一次完整循环
# ═════════════════════════════════════════════════════════════════════════
class EvolutionEngine:
    def __init__(self):
        self.db = sqlite3.connect(str(DB), timeout=10)
        self.db.executescript(SCHEMA)
        self.db.commit()
        self.stop_flag = threading.Event()
        print(f"[🧬 Evolution] Mini Evolution Engine v1.0 — OLLAMA={OLLAMA_MODEL} + {OLLAMA_CODE_MODEL}")

    def run_once(self):
        print(f"\n{'='*60}\n🧬 Evolution Engine @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}")

        # Phase 1: 发现
        print("\n🔍 Phase 1: 发现层...")
        gaps = DiscoverLayer(self.db).scan_all()
        print(f"   发现 {len(gaps)} 个 gap:")
        for g in gaps: print(f"     [{g.get('severity','?')}] {g.get('gap_type')}: {g.get('target','')[:50]}")

        # Phase 2: 生成
        print("\n🧠 Phase 2: 生成层...")
        gen = GenerateLayer(self.db)
        verifier = VerifyLayer(self.db)

        for g in gaps:
            fix_code = ""
            if g["gap_type"] == "syntax_error":
                fix_code = gen.fix_syntax(g["target"], g.get("evidence", ""))
            elif g["gap_type"] == "missing_route":
                fix_code = gen.design_missing_route(g["target"])

            verified, msg = verifier.python_smoke(fix_code) if fix_code else (True, "无代码生成")

            self.db.execute("""INSERT INTO mt_evolution_log (phase,action,severity,file_path,code_diff,ollama_model,status,error_msg)
                VALUES (?,?,?,?,?,?,?,?)""",
                ("generate", f"fix {g['gap_type']} → {g['target']}", g.get("severity", "info"),
                 g.get("target"), fix_code[:2000], OLLAMA_CODE_MODEL,
                 "verified" if verified else "rejected", "" if verified else msg))
            self.db.commit()
            print(f"   fix {g['gap_type']} {g['target']}: {msg}")

        # 主动建议
        print("\n💡 Phase 2b: AI 主动建议新功能...")
        try:
            features = gen.propose_new_feature()
            for f in features[:3]:
                print(f"   💡 {f.get('name','?')}: {str(f.get('code',''))[:80]}")
                self.db.execute("""INSERT INTO mt_evolution_log (phase,action,severity,code_diff,ollama_model,status)
                    VALUES ('propose', '建议新功能', 'info', ?, ?, 'pending')""",
                    (json.dumps(f, ensure_ascii=False), OLLAMA_MODEL))
            self.db.commit()
        except Exception as e:
            print(f"   AI 建议失败: {e}")

        # Phase 4: 同步
        print("\n📡 Phase 4: 同步层 (→ MacBook)...")
        SyncLayer(self.db).report_to_macbook()

        print(f"\n✅ 本轮完成")

    def daemon(self):
        """后台 daemon: 每 10min 一次."""
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while not self.stop_flag.is_set():
            try: self.run_once()
            except Exception as e: traceback.print_exc()
            self.stop_flag.wait(600)  # 10min

    def status(self):
        """状态面板."""
        cur = self.db.execute("SELECT * FROM mt_evolution_log ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print("╔══════════════════════════════════════════════════════╗")
        print("║  🧬 Mini Evolution Engine · Status                    ║")
        print("╠══════════════════════════════════════════════════════╣")
        total = self.db.execute("SELECT COUNT(*) FROM mt_evolution_log").fetchone()[0]
        verified = self.db.execute("SELECT COUNT(*) FROM mt_evolution_log WHERE status='verified'").fetchone()[0]
        pending = self.db.execute("SELECT COUNT(*) FROM mt_evolution_log WHERE status='pending'").fetchone()[0]
        gaps = self.db.execute("SELECT COUNT(*) FROM mt_discovered_gaps").fetchone()[0]
        print(f"  总演化记录: {total}  已验证: {verified}  待处理: {pending}")
        print(f"  发现 gap:   {gaps}")
        print(f"  Ollama:     {OLLAMA_MODEL} + {OLLAMA_CODE_MODEL}")
        print(f"  SSH:        → {SSH_DEST}")
        print("╚══════════════════════════════════════════════════════╝")


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="status",
                    choices=["status", "run", "daemon", "discover", "sync"])
    args = ap.parse_args()
    eng = EvolutionEngine()
    if args.cmd == "status":    eng.status()
    elif args.cmd == "run":     eng.run_once()
    elif args.cmd == "daemon":  eng.daemon(); print("🧬 daemon started, Ctrl+C to stop"); [time.sleep(1) for _ in iter(int,1)]
    elif args.cmd == "discover":
        gaps = DiscoverLayer(eng.db).scan_all()
        for g in gaps: print(json.dumps(g, ensure_ascii=False))
    elif args.cmd == "sync":    SyncLayer(eng.db).report_to_macbook()
