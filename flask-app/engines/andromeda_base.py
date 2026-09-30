#!/usr/bin/env python3
"""
仙女位子系统基类 (BaseAndromedaSubsystem)
==========================================

所有仙女座子系统共享的基础设施:
  1. Ollama 自动发现 (端口 11434/11435/11436 + 模型名)
  2. DB 连接 + 自动建表 (参数化表名)
  3. _ollama_generate() 本地推理 (零 token)
  4. artifact 文件落库 (static/<subdir>/<task_id>.<ext>)
  5. AI 员工注册 (mt_andromeda_employee_registry)
  6. daemon 注册 (mt_daemon_registry)

子系统只需:
  - SUBSYSTEM_NAME / SUBSYSTEM_ICON / SUBSYSTEM_DESC
  - DB_TABLE_NAME + DB_SCHEMA
  - ARTIFACT_DIR + ARTIFACT_EXT
  - MODES 字典 (prompt 模板)
  - AI_EMPLOYEES 列表
  - write() 入口 (调 _ollama_generate + _save_artifact + _db_insert)

当前 6 个子系统:
  📜 文曲星 (WENQUXING) — 文字编辑       ✅ 已实现
  🎨 瑶池   (YAOCHI)    — 绘画美术       (PIL+numpy)
  🎵 梵音   (FANYIN)    — 音乐乐理       (wave+struct)
  🎬 繁花   (FANHUA)    — 影视短视频     (ffmpeg)
  🤲 千手   (QIANSHOU)  — 中枢神经元     (路由/汇聚)
  🌀 混天绫 (HUNTIANLING)— API 网关层    (统一API)
  ⚖️ 太极   (TAIJI)     — 动态平衡器     (负载/适配)
"""

from __future__ import annotations
import json, os, sqlite3, sys, time, uuid, threading
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# 公共路径
# ═══════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).parent.parent
DB_CANDIDATES = [
    PROJECT_ROOT / "database" / "app.db",
    PROJECT_ROOT / "app.db",
]
DB_PATH = next((p for p in DB_CANDIDATES if p.exists()), DB_CANDIDATES[0])


# ═══════════════════════════════════════════════════════════
# Ollama 自动发现 (进程级单例)
# ═══════════════════════════════════════════════════════════
_OLLAMA_CACHE = None

def detect_ollama(preferred_models: list[str] | None = None) -> tuple[int, str, list[str]]:
    """返回 (port, best_model, all_models). 端口+模型列表缓存, best_model 按 preferred 每次重选."""
    global _OLLAMA_CACHE
    # 端口 + 全模型列表缓存 (不常变)
    if _OLLAMA_CACHE is None:
        import urllib.request as _ur, json as _j
        for p in [11434, 11435, 11436]:
            try:
                resp = _j.loads(_ur.urlopen(f"http://127.0.0.1:{p}/api/tags", timeout=2).read())
                all_models = [m["name"] for m in resp.get("models", [])]
                _OLLAMA_CACHE = (p, all_models)
                break
            except Exception: continue
        if _OLLAMA_CACHE is None:
            _OLLAMA_CACHE = (11434, [])
    port, all_models = _OLLAMA_CACHE

    # best_model 按 preferred 每次重选 (避免进程级缓存污染)
    best = None
    if preferred_models:
        for pref in preferred_models:
            if pref in all_models: best = pref; break
    if not best:
        for pref in ["qwen2.5:14b-q5", "qwen2.5:14b", "qwen2.5-coder:14b", "qwen2.5:7b"]:
            if pref in all_models: best = pref; break
    if not best: best = all_models[0] if all_models else "qwen2.5:7b"
    return port, best, all_models


# ═══════════════════════════════════════════════════════════
# 基类
# ═══════════════════════════════════════════════════════════
class BaseAndromedaSubsystem:
    """所有仙女位子系统的公共基类"""

    # 子类必须覆盖
    SUBSYSTEM_NAME = "Base"
    SUBSYSTEM_ICON = "⚙️"
    SUBSYSTEM_DESC = "仙女位子系统"
    DB_TABLE = "mt_base_tasks"
    DB_SCHEMA = ""          # CREATE TABLE IF NOT EXISTS ...
    ARTIFACT_DIR = "base_artifacts"
    ARTIFACT_EXT = "md"
    PREFERRED_MODELS = None # ["qwen2.5:14b-q5", ...] 或 None 用默认
    AI_EMPLOYEES = []       # [(employee_id, name, type, level, prompt), ...]
    DAEMON_NAME = "sys_base"
    DAEMON_DUTY = "仙女位子系统"

    def __init__(self):
        # Ollama
        self._ollama_port, self._ollama_model, self._ollama_all = detect_ollama(self.PREFERRED_MODELS)
        self.ollama_url = f"http://127.0.0.1:{self._ollama_port}"
        self._ollama_online = self._check_ollama()

        # DB
        self.db = sqlite3.connect(str(DB_PATH), timeout=10)
        if self.DB_SCHEMA:
            self.db.executescript(self.DB_SCHEMA)
            self.db.commit()
        self._ensure_standard_columns()

        # Artifact 目录
        self.artifact_path = PROJECT_ROOT / "static" / self.ARTIFACT_DIR
        self.artifact_path.mkdir(parents=True, exist_ok=True)

        print(f"[{self.SUBSYSTEM_ICON} {self.SUBSYSTEM_NAME}] "
              f"Ollama={self.ollama_url} model={self._ollama_model} "
              f"online={self._ollama_online} DB={DB_PATH.name}")

    def _ensure_standard_columns(self):
        """确保子系统表有 final_text/status/created_at/done_at 标准列."""
        try:
            existing = {c[1] for c in self.db.execute(f"PRAGMA table_info({self.DB_TABLE})").fetchall()}
            standard_cols = [
                ("final_text", "TEXT"),
                ("status", "TEXT DEFAULT 'pending'"),
                ("duration_sec", "INTEGER"),
                ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
                ("done_at", "TEXT"),
            ]
            for col, typ in standard_cols:
                if col not in existing:
                    self.db.execute(f"ALTER TABLE {self.DB_TABLE} ADD COLUMN {col} {typ}")
            self.db.commit()
        except Exception: pass  # 有些表是纯设计的 (如 mt_huntianling_routes)

    def write_task(self, task_id: str, raw_output: str, **extra_cols) -> str:
        """统一收口: 把 Ollama 输出 + 元数据落库 + 写 artifact.
        子系统 write() 方法结尾统一调这个."""
        import time as _t
        now = _t.time()
        extra_cols.setdefault("final_text", raw_output)
        extra_cols.setdefault("status", "done")
        extra_cols.setdefault("done_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.db_update_task(task_id, **extra_cols)
        return task_id

    def _check_ollama(self) -> bool:
        try:
            import urllib.request as _ur
            _ur.urlopen(f"{self.ollama_url}/api/tags", timeout=3)
            return True
        except Exception: return False

    def ollama_generate(self, prompt: str, model: str | None = None,
                         temperature: float = 0.8, max_tokens: int = 2048,
                         timeout_sec: int = 300) -> str:
        """本地 Ollama 推理 — 零 token 消耗"""
        import urllib.request, json as _j
        if not self._ollama_online:
            return f"[OllamaOffline] {prompt[:80]}"
        m = model or self._ollama_model
        try:
            body = _j.dumps({
                "model": m, "prompt": prompt, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            }).encode()
            req = urllib.request.Request(f"{self.ollama_url}/api/generate",
                data=body, headers={"Content-Type": "application/json"})
            resp = _j.loads(urllib.request.urlopen(req, timeout=timeout_sec).read())
            return resp.get("response", "")
        except Exception as e:
            return f"[OllamaError:{type(e).__name__}] {str(e)[:80]}"

    def save_artifact(self, task_id: str, content: str, header_lines: list[str] | None = None) -> Path:
        """写入 artifact 文件, 返回路径"""
        p = self.artifact_path / f"{task_id}.{self.ARTIFACT_EXT}"
        if header_lines:
            header = "\n".join(header_lines) + "\n\n---\n\n"
            content = header + content
        p.write_text(content, encoding="utf-8")
        return p

    def db_insert_task(self, task_id: str, **kwargs):
        """往子系统 DB_TABLE 插入一条 task. kwargs 是 {col: val}."""
        cols = list(kwargs.keys())
        vals = list(kwargs.values())
        placeholders = ",".join(["?"] * len(cols))
        col_names = ",".join(cols)
        self.db.execute(
            f"INSERT OR IGNORE INTO {self.DB_TABLE} ({col_names}) VALUES ({placeholders})", vals)
        self.db.commit()

    def db_update_task(self, task_id: str, **kwargs):
        set_clause = ",".join([f"{k}=?" for k in kwargs.keys()])
        self.db.execute(
            f"UPDATE {self.DB_TABLE} SET {set_clause} WHERE task_id=?",
            list(kwargs.values()) + [task_id])
        self.db.commit()

    def db_get_task(self, task_id: str) -> dict | None:
        row = self.db.execute(
            f"SELECT * FROM {self.DB_TABLE} WHERE task_id=?", (task_id,)).fetchone()
        if not row: return None
        cols = [c[1] for c in self.db.execute(f"PRAGMA table_info({self.DB_TABLE})").fetchall()]
        return dict(zip(cols, row))

    def db_list_tasks(self, limit: int = 20, where: str = "", args: list | None = None) -> list[dict]:
        sql = f"SELECT * FROM {self.DB_TABLE}"
        a = args or []
        if where: sql += f" WHERE {where}"
        sql += " ORDER BY id DESC LIMIT ?"
        a.append(limit)
        rows = self.db.execute(sql, a).fetchall()
        cols = [c[1] for c in self.db.execute(f"PRAGMA table_info({self.DB_TABLE})").fetchall()]
        return [dict(zip(cols, r)) for r in rows]

    # ─── 注册工具 ───────────────────────────────────────────
    def register_daemon(self, duty: str | None = None):
        """往 mt_daemon_registry 注册自己"""
        self.db.execute("""
            INSERT OR IGNORE INTO mt_daemon_registry
                (process_name, status, duty, restart_count, pid, last_heartbeat, config_json)
            VALUES (?, 'RUNNING', ?, 0, 0, CURRENT_TIMESTAMP, ?)
        """, (
            self.DAEMON_NAME,
            duty or f"{self.SUBSYSTEM_ICON} {self.SUBSYSTEM_NAME} — {self.SUBSYSTEM_DESC}",
            json.dumps({"subsystem": self.SUBSYSTEM_NAME, "model": self._ollama_model,
                        "port": self._ollama_port}, ensure_ascii=False)
        ))
        self.db.commit()

    def register_ai_employees(self, employees: list | None = None):
        """批量注册 AI 员工分身"""
        emps = employees or self.AI_EMPLOYEES
        if not emps: return
        for eid, name, etype, level, prompt in emps:
            self.db.execute("""
                INSERT OR REPLACE INTO mt_andromeda_employee_registry
                    (employee_id, name, employee_type, employee_source, level,
                     custom_system_prompt, enabled, registered_at, neuralhub_task, route_priority)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?, 'high')
            """, (eid, name, etype, self.SUBSYSTEM_NAME.upper(), level, prompt[:2000], self.SUBSYSTEM_NAME))
        self.db.commit()

    # ─── 工具 ───────────────────────────────────────────────
    @staticmethod
    def new_task_id(prefix: str = None) -> str:
        return f"{prefix or 'wqx'}_{uuid.uuid4().hex[:10]}"


# ═══════════════════════════════════════════════════════════
# 一键批量注册所有子系统 (daemon + AI 员工)
# ═══════════════════════════════════════════════════════════
def register_all_subsystems():
    """扫描 engines/ 下的 ai_*_engine.py, 找 BaseAndromedaSubsystem 子类, 批量注册"""
    import importlib, inspect
    eng_dir = PROJECT_ROOT / "engines"
    registered = {"daemons": 0, "employees": 0, "subsystems": []}
    for f in sorted(eng_dir.glob("ai_*_engine.py")):
        mod_name = f.stem
        try:
            spec = importlib.util.spec_from_file_location(mod_name, f)
            if not spec or not spec.loader: continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
            # 找 BaseAndromedaSubsystem 子类
            for name, obj in inspect.getmembers(mod):
                if (inspect.isclass(obj)
                    and issubclass(obj, BaseAndromedaSubsystem)
                    and obj is not BaseAndromedaSubsystem):
                    try:
                        inst = obj()
                        inst.register_daemon()
                        inst.register_ai_employees()
                        registered["daemons"] += 1
                        registered["employees"] += len(inst.AI_EMPLOYEES)
                        registered["subsystems"].append(inst.SUBSYSTEM_NAME)
                    except Exception as e:
                        print(f"  ⚠️ {name} 注册失败: {e}")
        except Exception as e:
            pass  # 不是所有 engine 都用基类
    print(f"\n📊 批量注册: {registered['daemons']} 个子系统, {registered['employees']} 位 AI 员工")
    return registered


if __name__ == "__main__":
    register_all_subsystems()
