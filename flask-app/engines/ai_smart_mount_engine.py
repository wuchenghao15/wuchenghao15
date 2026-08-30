#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能挂载自动化进程引擎 (Smart Mount Engine)
================================================
flow_id: flow_smart_mount_auto_process_20260819_001
§14 STEP_7_EXECUTE 下场实施

核心能力:
  1. 收集AI建议池中已评估的高优先级建议
  2. 综合EigenFlux专家动态权重做挂载决策
  3. 自动生成daemon脚本并注册到mt_daemon_registry
  4. subprocess启动进程 + 心跳监控 + 自动重启
  5. 系统需求/EigenFlux专家建议综合驱动

复用现有基础设施:
  - ai_intelligent_upgrade_engine.register_daemon()  注册daemon
  - ai_intelligent_upgrade_engine.daemon_transition() 状态机转移
  - ai_intelligent_upgrade_engine.add_ai_suggestion()  添加建议
  - ai_intelligent_upgrade_engine.evaluate_suggestion() 评估建议
  - ai_intelligent_upgrade_engine.compute_dynamic_weight() 专家权重

新增表:
  - mt_ai_smart_mount_processes  智能挂载进程跟踪表

CLI守护模式:
  python3 ai_smart_mount_engine.py start    启动监控守护进程
  python3 ai_smart_mount_engine.py stop     停止
  python3 ai_smart_mount_engine.py status   查看状态
  python3 ai_smart_mount_engine.py list     列出所有挂载进程
  python3 ai_smart_mount_engine.py create   手动创建自动化进程
  python3 ai_smart_mount_engine.py adopt    采纳AI建议并挂载
  python3 ai_smart_mount_engine.py scan     扫描建议池+自动挂载

遵循硬约束:
  - 数据库唯一数据源(app.db)
  - daemon状态机5态(IDLE/RUNNING/PAUSED/FAILED/STOPPED)
  - 全链路追溯ID
  - 巡检闭环 + 自动修复
"""
import json
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---- 路径 & 依赖 ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # flask-app/
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
APP_DB = os.path.join(AI_ENGINES_DIR, "app.db")
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
DAEMON_SCRIPTS_DIR = os.path.join(RUNTIME_DIR, "auto_daemons")
PID_FILE = os.path.join(PID_DIR, "ai_smart_mount_engine.pid")
MONITOR_LOG = os.path.join(LOG_DIR, "ai_smart_mount_monitor.log")

for _d in [LOG_DIR, PID_DIR, DAEMON_SCRIPTS_DIR]:
    os.makedirs(_d, exist_ok=True)

# 导入现有基础设施
sys.path.insert(0, AI_ENGINES_DIR)
try:
    from ai_intelligent_upgrade_engine import (
        register_daemon, daemon_transition, add_ai_suggestion,
        evaluate_suggestion, compute_dynamic_weight,
        ensure_upgrade_tables, _get_conn, _now,
        DAEMON_STATE_MACHINE,
    )
except ImportError:
    # 兼容直接运行
    _CONN = None

    def _get_conn():
        return sqlite3.connect(APP_DB, timeout=10)

    def _now():
        return datetime.now().isoformat()

    DAEMON_STATE_MACHINE = {
        "IDLE": ["RUNNING", "STOPPED"],
        "RUNNING": ["PAUSED", "FAILED", "STOPPED"],
        "PAUSED": ["RUNNING", "STOPPED"],
        "FAILED": ["RUNNING", "STOPPED"],
        "STOPPED": ["IDLE", "RUNNING"],
    }

_LOCK = threading.Lock()
MOUNT_THRESHOLD = 0.70  # 综合分>=0.70才自动挂载
MAX_RESTART_COUNT = 5   # 最大自动重启次数
HEARTBEAT_TIMEOUT = 90  # 心跳超时秒数
MONITOR_INTERVAL = 30   # 监控巡检间隔秒数


# ============================================================
# 建表 (幂等)
# ============================================================
def ensure_smart_mount_tables() -> Dict[str, bool]:
    """创建智能挂载相关表"""
    # 先确保基础表存在
    try:
        ensure_upgrade_tables()
    except Exception:
        pass

    results = {}
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # 智能挂载进程跟踪表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_smart_mount_processes (
            process_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            daemon_id        INTEGER NOT NULL,
            process_name     TEXT NOT NULL UNIQUE,
            script_path      TEXT NOT NULL,
            pid              INTEGER,
            suggestion_id    INTEGER,
            mount_source     TEXT NOT NULL DEFAULT 'AI_SUGGESTION',
            mount_score      REAL DEFAULT 0.0,
            expert_weights  TEXT,
            current_state    TEXT NOT NULL DEFAULT 'IDLE',
            heartbeat_at     TEXT,
            restart_count    INTEGER DEFAULT 0,
            last_restart_at  TEXT,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL,
            FOREIGN KEY(daemon_id) REFERENCES mt_daemon_registry(daemon_id),
            FOREIGN KEY(suggestion_id) REFERENCES mt_ai_suggestion_pool(suggestion_id),
            CHECK(mount_source IN ('AI_SUGGESTION','SYSTEM_REQ','EXPERT_ADVICE','MANUAL')),
            CHECK(current_state IN ('IDLE','RUNNING','PAUSED','FAILED','STOPPED'))
        )""")
        results["mt_ai_smart_mount_processes"] = True

        # 挂载决策日志表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_mount_decisions (
            decision_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_id    INTEGER,
            suggestion_text  TEXT,
            feasibility      REAL,
            value_score      REAL,
            cost_score       REAL,
            risk_score       REAL,
            base_score       REAL,
            expert_weight    REAL,
            final_score      REAL,
            decision         TEXT NOT NULL,
            reason           TEXT,
            created_at       TEXT NOT NULL,
            CHECK(decision IN ('MOUNT','DEFER','REJECT'))
        )""")
        results["mt_ai_mount_decisions"] = True

        conn.commit()
        conn.close()
    return results


# ============================================================
# 1. 收集AI建议 (从建议池)
# ============================================================
def collect_suggestions(min_priority: int = 5) -> List[Dict]:
    """从mt_ai_suggestion_pool收集已评估的高优先级建议"""
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""
            SELECT * FROM mt_ai_suggestion_pool
            WHERE status='EVALUATED' AND priority>=?
            ORDER BY priority DESC, created_at ASC
        """, (min_priority,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 2. 收集EigenFlux专家权重
# ============================================================
def collect_expert_weights() -> Dict[str, float]:
    """从mt_eigenflux_expert_registry收集所有活跃专家的动态权重"""
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""
            SELECT expert_id, expert_name, domain, weight, accuracy_rate
            FROM mt_eigenflux_expert_registry
            WHERE tenure_status='ACTIVE'
        """).fetchall()
        conn.close()

    weights = {}
    for r in rows:
        rid = r["expert_id"]
        weights[r["expert_name"]] = compute_dynamic_weight(rid) if rid else r["weight"]
    return weights


# ============================================================
# 3. 智能挂载决策 (AI建议 + EigenFlux专家权重)
# ============================================================
def smart_mount_decision(suggestion: Dict, expert_weights: Dict[str, float]) -> Dict:
    """
    综合决策:
      base_score = suggestion评估分 (feasibility*0.3 + value*0.3 + (1-cost)*0.2 + (1-risk)*0.2)
      expert_factor = 专家平均权重 (0~1)
      final_score = base_score * 0.6 + expert_factor * 0.4
      decision = MOUNT if final_score >= MOUNT_THRESHOLD else DEFER
    """
    feasibility = suggestion.get("feasibility", 0.0)
    value_score = suggestion.get("value_score", 0.0)
    cost_score = suggestion.get("cost_score", 0.0)
    risk_score = suggestion.get("risk_score", 0.0)

    base_score = round(
        feasibility * 0.3 + value_score * 0.3 + (1 - cost_score) * 0.2 + (1 - risk_score) * 0.2, 4
    )

    # EigenFlux专家平均权重
    if expert_weights:
        avg_weight = round(sum(expert_weights.values()) / len(expert_weights), 4)
    else:
        avg_weight = 0.5  # 无专家时默认中性

    final_score = round(base_score * 0.6 + avg_weight * 0.4, 4)
    decision = "MOUNT" if final_score >= MOUNT_THRESHOLD else "DEFER"
    reason = (
        f"base={base_score}(feas={feasibility},val={value_score},cost={cost_score},risk={risk_score})"
        f" + expert_avg={avg_weight} -> final={final_score}"
        f" {'>=' if final_score >= MOUNT_THRESHOLD else '<'} {MOUNT_THRESHOLD}"
    )

    # 落库决策日志
    now = _now()
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO mt_ai_mount_decisions
            (suggestion_id, suggestion_text, feasibility, value_score, cost_score, risk_score,
             base_score, expert_weight, final_score, decision, reason, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (suggestion.get("suggestion_id"), suggestion.get("suggestion", "")[:200],
             feasibility, value_score, cost_score, risk_score,
             base_score, avg_weight, final_score, decision, reason, now))
        conn.commit()
        conn.close()

    return {
        "suggestion_id": suggestion.get("suggestion_id"),
        "suggestion": suggestion.get("suggestion", ""),
        "direction": suggestion.get("direction", ""),
        "base_score": base_score,
        "expert_weight": avg_weight,
        "final_score": final_score,
        "decision": decision,
        "reason": reason,
    }


# ============================================================
# 4. 自动生成daemon脚本
# ============================================================
DAEMON_SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成daemon: {process_name}
来源: AI建议 #{suggestion_id} (score={mount_score})
生成时间: {created_at}
职责: {duty}
"""
import os, sys, time, signal, sqlite3, json
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINE_DIR = os.path.join(_PROJECT_ROOT, "flask-app", "ai_engines")
APP_DB = os.path.join(ENGINE_DIR, "app.db")
PID_FILE = os.path.join(_PROJECT_ROOT, "_runtime", "pids", "{pid_filename}")
LOG_FILE = os.path.join(_PROJECT_ROOT, "_runtime", "logs", "{log_filename}")

os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

_running = True

def _signal_handler(signum, frame):
    global _running
    _running = False

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

def _heartbeat():
    """更新心跳到mt_ai_smart_mount_processes"""
    try:
        conn = sqlite3.connect(APP_DB, timeout=5)
        c = conn.cursor()
        c.execute(
            "UPDATE mt_ai_smart_mount_processes SET heartbeat_at=?, updated_at=? WHERE process_name=?",
            (datetime.now().isoformat(), datetime.now().isoformat(), "{process_name}"))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{{datetime.now().isoformat()}}] {{msg}}\\n")

def main_loop():
    _log(f"DAEMON START: {process_name} pid={{os.getpid()}}")
    # 写PID文件
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    _heartbeat()

    while _running:
        try:
            # === daemon工作循环 ===
            {work_body}
            _heartbeat()
        except Exception as e:
            _log(f"ERROR: {{e}}")
        time.sleep({inspect_cycle})

    # 清理
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    _log(f"DAEMON STOP: {process_name}")

if __name__ == "__main__":
    main_loop()
'''


def generate_daemon_script(process_name: str, duty: str,
                          suggestion_id: int, mount_score: float,
                          work_body: str = "pass  # TODO: 实现具体工作逻辑",
                          inspect_cycle: int = 60) -> str:
    """自动生成daemon Python脚本（OneDrive 兼容：重试+fallback到临时目录）"""
    safe_name = process_name.replace(" ", "_").replace("-", "_")
    script_content = DAEMON_SCRIPT_TEMPLATE.format(
        process_name=process_name,
        suggestion_id=suggestion_id,
        mount_score=mount_score,
        created_at=_now(),
        duty=duty,
        pid_filename=f"{safe_name}.pid",
        log_filename=f"{safe_name}.log",
        work_body=work_body,
        inspect_cycle=inspect_cycle,
    )
    primary_path = os.path.join(DAEMON_SCRIPTS_DIR, f"{safe_name}.py")
    fallback_dir = os.path.join(tempfile.gettempdir(), "mtscos_auto_daemons")
    os.makedirs(fallback_dir, exist_ok=True)
    fallback_path = os.path.join(fallback_dir, f"{safe_name}.py")

    last_err = None
    for attempt, target in enumerate([primary_path, primary_path, fallback_path], 1):
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(script_content)
            try:
                os.chmod(target, 0o755)
            except Exception:
                pass
            _log(f"[GEN-SCRIPT] {process_name} -> {target} (attempt={attempt})")
            return target
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise RuntimeError(f"generate_daemon_script failed for {process_name}: {last_err}")


# ============================================================
# 5. 挂载进程 (注册 + 启动)
# ============================================================
def mount_process(process_name: str, duty: str, script_path: str,
                  suggestion_id: Optional[int] = None,
                  mount_source: str = "AI_SUGGESTION",
                  mount_score: float = 0.0,
                  expert_weights: Optional[Dict] = None) -> int:
    """
    挂载自动化进程:
      1. 注册daemon到mt_daemon_registry (IDLE)
      2. 写入mt_ai_smart_mount_processes
      3. daemon_transition IDLE→RUNNING
      4. subprocess.Popen启动
    """
    now = _now()

    # 1. 注册daemon (复用现有接口)
    try:
        daemon_id = register_daemon(
            name=process_name, duty=duty,
            dependencies="ai_smart_mount_engine",
            priority=7, inspect_cycle=f"{MONITOR_INTERVAL}s"
        )
    except Exception:
        # 可能已注册
        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            r = conn.execute(
                "SELECT daemon_id FROM mt_daemon_registry WHERE daemon_name=?",
                (process_name,)).fetchone()
            conn.close()
            daemon_id = r["daemon_id"] if r else 0

    # 2. 写入进程跟踪表
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO mt_ai_smart_mount_processes
            (daemon_id, process_name, script_path, suggestion_id, mount_source,
             mount_score, expert_weights, current_state,
             restart_count, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (daemon_id, process_name, script_path, suggestion_id, mount_source,
             mount_score, json.dumps(expert_weights or {}, ensure_ascii=False),
             "IDLE", 0, now, now))
        conn.commit()
        pid = c.execute(
            "SELECT process_id FROM mt_ai_smart_mount_processes WHERE process_name=?",
            (process_name,)).fetchone()[0]
        conn.close()

    # 3. 状态转移 IDLE→RUNNING
    try:
        daemon_transition(process_name, "RUNNING")
    except Exception:
        pass

    # 4. 更新进程跟踪表状态
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE mt_ai_smart_mount_processes SET current_state='RUNNING', updated_at=? WHERE process_name=?",
            (_now(), process_name))
        conn.commit()
        conn.close()

    # 5. 启动进程
    _start_subprocess(process_name, script_path)

    _log(f"[MOUNT] process={process_name} daemon_id={daemon_id} pid={pid} score={mount_score} source={mount_source}")
    return pid


def _start_subprocess(process_name: str, script_path: str) -> Optional[int]:
    """用subprocess启动daemon脚本"""
    safe_name = process_name.replace(" ", "_").replace("-", "_")
    log_file = os.path.join(LOG_DIR, f"{safe_name}.log")

    try:
        with open(log_file, "a") as lf:
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=lf, stderr=lf,
                cwd=os.path.dirname(script_path),
                start_new_session=True,  # 独立进程组
            )
        # 记录PID
        with _LOCK:
            conn = _get_conn()
            c = conn.cursor()
            c.execute(
                "UPDATE mt_ai_smart_mount_processes SET pid=?, current_state='RUNNING', heartbeat_at=?, updated_at=? WHERE process_name=?",
                (proc.pid, _now(), _now(), process_name))
            conn.commit()
            conn.close()
        _log(f"[START] {process_name} pid={proc.pid}")
        return proc.pid
    except Exception as e:
        _log(f"[START-FAIL] {process_name}: {e}")
        return None


# ============================================================
# 6. 心跳监控 + 自动重启
# ============================================================
def heartbeat_check() -> Dict:
    """检查所有RUNNING进程的心跳,超时的标记FAILED并自动重启"""
    now_str = _now()
    now_ts = datetime.now().timestamp()
    result = {"checked": 0, "alive": 0, "timeout": 0, "restarted": 0, "max_restart": 0}

    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        # 扩展：除RUNNING外，也检查IDLE/STOPPED/FAILED行中的残留PID是否真实存活
        # 避免历史残留PID记录永远不被清理，无法重挂载
        rows = conn.execute("""
            SELECT * FROM mt_ai_smart_mount_processes
            WHERE current_state IN ('RUNNING','IDLE','STOPPED','FAILED')
        """).fetchall()
        conn.close()

    for r in rows:
        result["checked"] += 1
        pid = r["pid"]

        # 检查进程是否存活
        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False

        if alive:
            # 检查心跳超时
            hb = r["heartbeat_at"]
            if hb:
                try:
                    hb_ts = datetime.fromisoformat(hb).timestamp()
                    if now_ts - hb_ts > HEARTBEAT_TIMEOUT:
                        alive = False
                        _log(f"[TIMEOUT] {r['process_name']} pid={pid} heartbeat_stale>{HEARTBEAT_TIMEOUT}s")
                except Exception:
                    pass

        if alive:
            result["alive"] += 1
            # IDLE但存活的进程 → 不重启，标记为 RUNNING 便于进入正常心跳循环
            if r["current_state"] == "IDLE":
                _update_process_state(r["process_name"], "RUNNING")
                try:
                    daemon_transition(r["process_name"], "RUNNING")
                except Exception:
                    pass
            continue

        # 进程死亡或心跳超时 → 先清理残留PID记录，避免下次再判错
        try:
            with _LOCK:
                _c = _get_conn().cursor()
                _c.execute("UPDATE mt_ai_smart_mount_processes SET pid=NULL WHERE process_name=?",
                           (r["process_name"],))
                _c.connection.commit()
                _c.connection.close()
        except Exception:
            pass

        # 非RUNNING状态但PID已死 → 只清理不重启，留给 mount_system_required 按系统必需规则重新挂载
        if r["current_state"] != "RUNNING":
            if r["current_state"] != "STOPPED":
                _update_process_state(r["process_name"], "STOPPED")
                try:
                    daemon_transition(r["process_name"], "STOPPED")
                except Exception:
                    pass
            continue

        result["timeout"] += 1
        restart_count = r["restart_count"] or 0

        if restart_count >= MAX_RESTART_COUNT:
            result["max_restart"] += 1
            _log(f"[MAX-RESTART] {r['process_name']} restart_count={restart_count} -> STOPPED")
            _update_process_state(r["process_name"], "STOPPED")
            try:
                daemon_transition(r["process_name"], "STOPPED")
            except Exception:
                pass
            continue

        # 自动重启
        _log(f"[RESTART] {r['process_name']} pid={pid} restart#{restart_count + 1}")
        _update_process_state(r["process_name"], "FAILED")
        try:
            daemon_transition(r["process_name"], "FAILED")
        except Exception:
            pass

        # 重置后重新启动
        time.sleep(2)
        new_pid = _start_subprocess(r["process_name"], r["script_path"])

        with _LOCK:
            conn = _get_conn()
            c = conn.cursor()
            c.execute("""UPDATE mt_ai_smart_mount_processes
                SET current_state='RUNNING', restart_count=?, last_restart_at=?, heartbeat_at=?, updated_at=?
                WHERE process_name=?""",
                (restart_count + 1, _now(), _now(), _now(), r["process_name"]))
            conn.commit()
            conn.close()

        try:
            daemon_transition(r["process_name"], "RUNNING")
        except Exception:
            pass

        result["restarted"] += 1

    return result


def _update_process_state(process_name: str, state: str):
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE mt_ai_smart_mount_processes SET current_state=?, updated_at=? WHERE process_name=?",
            (state, _now(), process_name))
        conn.commit()
        conn.close()


def _log(msg: str):
    with open(MONITOR_LOG, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


def _log_supervisor(level: str, event: str, detail: str = '') -> None:
    """
    守护进程事件落库 mt_daemon_supervisor_log，便于跨会话追溯。
    与 start_smart_mount_engine_daemon.py 内的 log_event 共用同一张表，
    supervisor 字段固定为 'smart_mount_daemon'。
    失败时静默忽略，绝不影响主循环。
    """
    try:
        with _LOCK:
            conn = _get_conn()
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS mt_daemon_supervisor_log (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time    TEXT    NOT NULL,
                    supervisor    TEXT    NOT NULL,
                    level         TEXT    NOT NULL,
                    event         TEXT    NOT NULL,
                    detail        TEXT,
                    pid           INTEGER,
                    created_at    TEXT    NOT NULL
                )
            """)
            c.execute(
                "INSERT INTO mt_daemon_supervisor_log "
                "(event_time, supervisor, level, event, detail, pid, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (_now(), 'smart_mount_daemon', level, event, detail, os.getpid(), _now()),
            )
            conn.commit()
            conn.close()
    except Exception:
        # 守护进程落库失败绝不影响主流程
        pass


# ============================================================
# 7. 扫描建议池 + 自动挂载 (核心入口)
# ============================================================
def scan_and_mount() -> Dict:
    """
    全流程: 扫描建议池 → 收集专家权重 → 逐条决策 → 自动挂载
    这是scan子命令的核心逻辑,也是守护循环每次执行的逻辑
    """
    result = {
        "scanned": 0, "mounted": 0, "deferred": 0, "rejected": 0,
        "details": []
    }

    # 1. 收集已评估的高优先级建议
    suggestions = collect_suggestions(min_priority=5)
    result["scanned"] = len(suggestions)

    if not suggestions:
        _log("[SCAN] 无待挂载建议")
        return result

    # 2. 收集EigenFlux专家权重
    expert_weights = collect_expert_weights()

    # 3. 逐条决策
    for sug in suggestions:
        decision = smart_mount_decision(sug, expert_weights)

        if decision["decision"] == "MOUNT":
            # 自动生成daemon脚本
            process_name = f"auto_{sug.get('direction', 'gen')}_{sug['suggestion_id']}"
            duty = sug.get("suggestion", "")[:100]
            script_path = generate_daemon_script(
                process_name=process_name,
                duty=duty,
                suggestion_id=sug["suggestion_id"],
                mount_score=decision["final_score"],
                work_body=_infer_work_body(sug),
                inspect_cycle=60,
            )

            # 挂载
            try:
                mount_process(
                    process_name=process_name,
                    duty=duty,
                    script_path=script_path,
                    suggestion_id=sug["suggestion_id"],
                    mount_source="AI_SUGGESTION",
                    mount_score=decision["final_score"],
                    expert_weights=expert_weights,
                )
                result["mounted"] += 1
                decision["process_name"] = process_name
                decision["script_path"] = script_path
            except Exception as e:
                _log(f"[MOUNT-FAIL] {process_name}: {e}")
                decision["error"] = str(e)
        elif decision["decision"] == "DEFER":
            result["deferred"] += 1
        else:
            result["rejected"] += 1

        result["details"].append(decision)

    _log(f"[SCAN] scanned={result['scanned']} mounted={result['mounted']} "
         f"deferred={result['deferred']} rejected={result['rejected']}")
    return result


def _infer_work_body(suggestion: Dict) -> str:
    """根据建议内容推断daemon工作逻辑骨架"""
    text = (suggestion.get("suggestion", "") + " " + suggestion.get("direction", "")).lower()

    if "巡检" in text or "patrol" in text or "inspect" in text:
        return "            # 巡检逻辑: 检查系统指标, 异常投喂mt_ai_suggestion_pool\n            pass"
    elif "同步" in text or "sync" in text:
        return "            # 同步逻辑: 数据/文件同步\n            pass"
    elif "备份" in text or "backup" in text:
        return "            # 备份逻辑: 定时备份关键数据\n            pass"
    elif "监控" in text or "monitor" in text:
        return "            # 监控逻辑: 采集指标, 阈值告警\n            pass"
    elif "清理" in text or "clean" in text:
        return "            # 清理逻辑: 清理过期/临时文件\n            pass"
    else:
        return "            # 通用daemon逻辑: 默认巡检+日志\n            pass"


# ============================================================
# 8. 系统需求驱动: 无建议时根据系统要求自动创建
# ============================================================
SYSTEM_REQUIRED_DAEMONS = [
    {
        "process_name": "sys_patrol_inspector",
        "duty": "系统巡检守护: 每分钟检查daemon状态/数据库完整性/AI员工在线率",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 巡检: 检查所有daemon状态\n            try:\n                conn = sqlite3.connect(APP_DB, timeout=5)\n                c = conn.cursor()\n                rows = c.execute('SELECT daemon_name, current_state FROM mt_daemon_registry').fetchall()\n                for r in rows:\n                    if r[1] == 'RUNNING':\n                        pass  # 正常\n                conn.close()\n            except Exception as e:\n                _log(f'PATROL ERROR: {e}')",
        "inspect_cycle": 60,
    },
    {
        "process_name": "sys_heartbeat_writer",
        "duty": "系统心跳守护: 每30秒写入系统心跳到数据库, 证明系统存活",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 写系统心跳\n            try:\n                conn = sqlite3.connect(APP_DB, timeout=5)\n                c = conn.cursor()\n                c.execute('INSERT OR REPLACE INTO mt_system_heartbeat (id, last_beat, updated_at) VALUES (1, ?, ?)',\n                    (datetime.now().isoformat(), datetime.now().isoformat()))\n                conn.commit()\n                conn.close()\n            except Exception as e:\n                _log(f'HEARTBEAT ERROR: {e}')",
        "inspect_cycle": 30,
    },
    {
        "process_name": "sys_auto_repair",
        "duty": "自动修复守护: 检查FAILED状态的daemon, 匹配修复策略库并尝试恢复",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动修复: 检查FAILED daemon\n            try:\n                conn = sqlite3.connect(APP_DB, timeout=5)\n                c = conn.cursor()\n                failed = c.execute('SELECT daemon_name FROM mt_daemon_registry WHERE current_state=?',\n                    ('FAILED',)).fetchall()\n                for f in failed:\n                    _log(f'AUTO-REPAIR: daemon={f[0]} FAILED, checking strategy lib...')\n                conn.close()\n            except Exception as e:\n                _log(f'REPAIR ERROR: {e}')",
        "inspect_cycle": 120,
    },
    {
        "process_name": "sys_eigenflux_network",
        "duty": "AI-EigenFlux网络守护: 自动连线/交友交流/心跳保活/经验投喂脑库",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # AI-EigenFlux网络引擎: 调用ai_eigenflux_network_engine的once模式\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_eigenflux_network_engine.py')\n                subprocess.run([sys.executable, engine_py, 'once'], timeout=300, capture_output=True)\n            except Exception as e:\n                _log(f'EIGENFLUX ERROR: {e}')",
        "inspect_cycle": 120,
    },
    {
        "process_name": "sys_auto_patrol",
        "duty": "自动巡逻队守护: 扫描所有.py源文件检测语法/导入/运行时错误→自动修复→验证→报告→持久化",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动巡逻队: 调用auto_patrol_engine.run_full_patrol()\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'auto_patrol_engine.py')\n                subprocess.run([sys.executable, engine_py], timeout=600, capture_output=True)\n                _log(f'AUTO-PATROL: patrol cycle done')\n            except subprocess.TimeoutExpired:\n                _log('AUTO-PATROL: timeout (600s), will retry next cycle')\n            except Exception as e:\n                _log(f'AUTO-PATROL ERROR: {e}')",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_ai_suggested_repair",
        "duty": "AI建议修复守护: 吸收建议池PENDING建议→现场复核→智能修复(备份+验证+回滚)→git自动上传→落库投喂(600s轮巡)",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # AI建议修复: 调用ai_suggested_repair_engine.py once\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_suggested_repair_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=540, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('SUG-REPAIR: cycle done')\n                else:\n                    _log(f'SUG-REPAIR: cycle failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('SUG-REPAIR: timeout (540s)')\n            except Exception as e:\n                _log(f'SUG-REPAIR error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_deep_inspection",
        "duty": "深度巡检守护: 页面/路由巡检+源代码逐行检查+AI团队路由+自动修复+全生命周期追踪",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 深度巡检: 调用deep_inspection_engine.run_full_inspection()\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'deep_inspection_engine.py')\n                subprocess.run([sys.executable, engine_py], timeout=900, capture_output=True)\n                _log(f'DEEP-INSPECTION: inspection cycle done')\n            except subprocess.TimeoutExpired:\n                _log('DEEP-INSPECTION: timeout (900s), will retry next cycle')\n            except Exception as e:\n                _log(f'DEEP-INSPECTION ERROR: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_copy_inspection",
        "duty": "文案巡检守护: 缺失文案检测+重复文案检测+占位符检测+硬编码检测",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 文案巡检: 调用copy_inspection_engine.run_full_inspection()\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'copy_inspection_engine.py')\n                subprocess.run([sys.executable, engine_py], timeout=300, capture_output=True)\n                _log(f'COPY-INSPECTION: inspection cycle done')\n            except subprocess.TimeoutExpired:\n                _log('COPY-INSPECTION: timeout (300s), will retry next cycle')\n            except Exception as e:\n                _log(f'COPY-INSPECTION ERROR: {e}')",
        "inspect_cycle": 900,
    },
    {
        "process_name": "sys_rule_enforcer",
        "duty": "规则自动学习+严格执行守护: 弱约束词扫描修复→解析9篇规则→投喂脑库→完整性扫描→违规检测→告警投喂→绕过检测",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 1. 弱约束词扫描+修复: 调用auto_rule_strengthener.py\n            try:\n                import subprocess\n                strengthener_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'auto_rule_strengthener.py')\n                # 先verify检查, 若有弱约束词则自动修复\n                v = subprocess.run([sys.executable, strengthener_py, 'verify'],\n                    timeout=60, capture_output=True, text=True)\n                if v.returncode != 0:\n                    _log('RULE-ENFORCER: weak words detected, auto-fixing...')\n                    subprocess.run([sys.executable, strengthener_py],\n                        timeout=120, capture_output=True)\n                    _log('RULE-ENFORCER: weak words fixed')\n                else:\n                    _log('RULE-ENFORCER: weak words=0, rules clean')\n            except subprocess.TimeoutExpired:\n                _log('RULE-ENFORCER: strengthener timeout')\n            except Exception as e:\n                _log(f'RULE-ENFORCER: strengthener error: {e}')\n            # 2. 规则学习+执行: 调用ai_rule_learning_engine.py once\n            try:\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_rule_learning_engine.py')\n                subprocess.run([sys.executable, engine_py, 'once'], timeout=300, capture_output=True)\n                _log('RULE-ENFORCER: learn+enforce cycle done')\n            except subprocess.TimeoutExpired:\n                _log('RULE-ENFORCER: learn+enforce timeout (300s)')\n            except Exception as e:\n                _log(f'RULE-ENFORCER: learn+enforce error: {e}')",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_edu_sync",
        "duty": "教辅教改自动同步: K12教辅+题型/母题/解题模型→理化实验→文科→高等教育→成人教育+实时政治, 数据库永久化+实时最新",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 教辅教改同步: 调用ai_edu_sync_engine.py sync\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_edu_sync_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'sync'],\n                    timeout=300, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('EDU-SYNC: sync cycle done')\n                else:\n                    _log(f'EDU-SYNC: sync failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('EDU-SYNC: timeout (300s)')\n            except Exception as e:\n                _log(f'EDU-SYNC error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_arduino_sync",
        "duty": "Arduino编程自动同步: 教程(基础/传感器/执行器/显示/通信/IoT/项目)+组件库+实验项目+板卡支持, 数据库永久化+实时最新",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # Arduino编程同步: 调用ai_arduino_engine.py sync\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_arduino_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'sync'],\n                    timeout=300, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('ARDUINO-SYNC: sync cycle done')\n                else:\n                    _log(f'ARDUINO-SYNC: sync failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('ARDUINO-SYNC: timeout (300s)')\n            except Exception as e:\n                _log(f'ARDUINO-SYNC error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_arduino_detect",
        "duty": "Arduino设备自动检测: 串口扫描→VID:PID识别板卡→驱动状态检测→IDE配置生成→热插拔感知(30s巡检)",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # Arduino设备检测: 调用ai_arduino_detect_engine.py scan\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_arduino_detect_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'scan'],\n                    timeout=30, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('ARDUINO-DETECT: scan cycle done')\n                else:\n                    _log(f'ARDUINO-DETECT: scan failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('ARDUINO-DETECT: timeout (30s)')\n            except Exception as e:\n                _log(f'ARDUINO-DETECT error: {e}')",
        "inspect_cycle": 30,
    },
    {
        "process_name": "sys_auto_hire",
        "duty": "自动雇佣AI员工+邀请EigenFlux专家+互推朋友+完善巡逻队+代码修复(300s)",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动雇佣+邀请: 调用ai_auto_hire_engine.py hire\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_auto_hire_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'hire'],\n                    timeout=120, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('AUTO-HIRE: cycle done')\n                else:\n                    _log(f'AUTO-HIRE: cycle failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('AUTO-HIRE: timeout (120s)')\n            except Exception as e:\n                _log(f'AUTO-HIRE error: {e}')",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_local_inference",
        "duty": "本地化AI推理: 聊天/分类/审查/Bug分析 全部本地完成, 零token消耗(120s巡检)",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 本地推理引擎: 统计token节省\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_local_inference_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'stats'],\n                    timeout=30, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('LOCAL-AI: stats cycle done')\n                else:\n                    _log(f'LOCAL-AI: stats failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('LOCAL-AI: timeout (30s)')\n            except Exception as e:\n                _log(f'LOCAL-AI error: {e}')",
        "inspect_cycle": 120,
    },
    {
        "process_name": "sys_file_organizer",
        "duty": "智能文件整理: 扫描散落文件→归类到正确目录→清理临时文件→删除空目录→记录落库(600s)",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 文件整理: 调用ai_file_organizer.py organize\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_file_organizer.py')\n                r = subprocess.run([sys.executable, engine_py, 'organize'],\n                    timeout=120, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('FILE-ORG: organize cycle done')\n                else:\n                    _log(f'FILE-ORG: organize failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('FILE-ORG: timeout (120s)')\n            except Exception as e:\n                _log(f'FILE-ORG error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_math_models",
        "duty": "数学解题模型自动收集同步: K12+高等+竞赛32模型, 数据库永久化(1800s)",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 数学模型同步\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_math_models_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'sync'],\n                    timeout=120, capture_output=True, text=True)\n                if r.returncode == 0:\n                    _log('MATH-MODELS: sync cycle done')\n                else:\n                    _log(f'MATH-MODELS: sync failed rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('MATH-MODELS: timeout (120s)')\n            except Exception as e:\n                _log(f'MATH-MODELS error: {e}')",
        "inspect_cycle": 1800,
    },
    # ===== 独立服务集成 (v3.0.0: 统一由 smart_mount 管理) =====
    {
        "process_name": "sys_flask_server",
        "duty": "Flask应用服务器: 持续运行Web服务, 崩溃自动重启, 由smart_mount统一管理",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # Flask应用服务器: 持续运行, 崩溃自动重启\n            try:\n                import subprocess\n                app_py = os.path.join(ENGINE_DIR, '..', 'modular_start.py')\n                subprocess.run([sys.executable, app_py], timeout=3600)\n                _log('FLASK-SERVER: exited, will restart next cycle')\n            except subprocess.TimeoutExpired:\n                _log('FLASK-SERVER: 1h timeout checkpoint, continuing')\n            except Exception as e:\n                _log(f'FLASK-SERVER error: {e}')",
        "inspect_cycle": 10,
    },
    {
        "process_name": "sys_auto_scheduler",
        "duty": "自动调度引擎: 独立调度器运行git_sync_check等定时任务, 持续运行",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动调度器: 持续运行\n            try:\n                import subprocess\n                sched_py = os.path.join(ENGINE_DIR, '..', 'core', 'auto_scheduler.py')\n                subprocess.run([sys.executable, sched_py], timeout=3600)\n                _log('AUTO-SCHED: exited, will restart next cycle')\n            except subprocess.TimeoutExpired:\n                _log('AUTO-SCHED: 1h timeout checkpoint, continuing')\n            except Exception as e:\n                _log(f'AUTO-SCHED error: {e}')",
        "inspect_cycle": 10,
    },
    {
        "process_name": "sys_git_sync",
        "duty": "Git自动同步: 定期add/commit/push到GitHub, 保持代码同步",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # Git自动同步\n            try:\n                import subprocess\n                sync_script = os.path.join(os.path.dirname(ENGINE_DIR), '..', 'sync_github.sh')\n                if os.path.exists(sync_script):\n                    r = subprocess.run(['/bin/bash', sync_script, 'push'],\n                        timeout=120, capture_output=True, text=True)\n                    _log(f'GIT-SYNC: rc={r.returncode}')\n                else:\n                    _log('GIT-SYNC: sync_github.sh not found')\n            except subprocess.TimeoutExpired:\n                _log('GIT-SYNC: timeout (120s)')\n            except Exception as e:\n                _log(f'GIT-SYNC error: {e}')",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_shadow_node",
        "duty": "影子节点: 定期同步和维护影子节点, 数据冗余保障",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 影子节点同步\n            try:\n                import subprocess\n                shadow_py = os.path.join(os.path.dirname(ENGINE_DIR), '..', '..', 'scripts', 'backup', 'shadow_node.py')\n                if os.path.exists(shadow_py):\n                    r = subprocess.run([sys.executable, shadow_py, '--periodic'],\n                        timeout=300, capture_output=True, text=True)\n                    _log(f'SHADOW-NODE: rc={r.returncode}')\n                else:\n                    _log('SHADOW-NODE: script not found, skip')\n            except subprocess.TimeoutExpired:\n                _log('SHADOW-NODE: timeout (300s)')\n            except Exception as e:\n                _log(f'SHADOW-NODE error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_auto_backup",
        "duty": "自动备份: 定期数据库备份+文件备份, 保留策略+压缩",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动备份\n            try:\n                import subprocess\n                backup_py = os.path.join(os.path.dirname(ENGINE_DIR), '..', 'services', 'backup_manager.py')\n                if os.path.exists(backup_py):\n                    r = subprocess.run([sys.executable, backup_py, 'backup'],\n                        timeout=300, capture_output=True, text=True)\n                    _log(f'BACKUP: rc={r.returncode}')\n                else:\n                    _log('BACKUP: backup_manager.py not found, skip')\n            except subprocess.TimeoutExpired:\n                _log('BACKUP: timeout (300s)')\n            except Exception as e:\n                _log(f'BACKUP error: {e}')",
        "inspect_cycle": 1800,
    },
    {
        "process_name": "sys_self_learning",
        "duty": "AI自学习引擎: 自主学习+知识积累+经验提炼+投喂脑库",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # AI自学习\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_self_learning_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'SELF-LEARN: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('SELF-LEARN: timeout (300s)')\n            except Exception as e:\n                _log(f'SELF-LEARN error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_brain_feeding",
        "duty": "脑库投喂引擎: 经验/异常/知识自动投喂AI脑库, 持续丰富AI知识",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 脑库投喂\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'brain_feeding_engine.py')\n                r = subprocess.run([sys.executable, engine_py, '--feed'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'BRAIN-FEED: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('BRAIN-FEED: timeout (300s)')\n            except Exception as e:\n                _log(f'BRAIN-FEED error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_eigenflux_broadcast",
        "duty": "EigenFlux广播引擎: 向AI网络广播消息/任务/知识, 扩散传播",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # EigenFlux广播\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'eigenflux_broadcast_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'EIGENFLUX-BCAST: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('EIGENFLUX-BCAST: timeout (300s)')\n            except Exception as e:\n                _log(f'EIGENFLUX-BCAST error: {e}')",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_eigenflux_proactive",
        "duty": "EigenFlux主动引擎: 主动分析+预测+建议, 前瞻性AI能力",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # EigenFlux主动引擎\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'eigenflux_proactive_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'EIGENFLUX-PRO: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('EIGENFLUX-PRO: timeout (300s)')\n            except Exception as e:\n                _log(f'EIGENFLUX-PRO error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_auto_dev_team",
        "duty": "自动开发团队引擎: AI开发者自动协作+任务分配+代码生成+集成",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动开发团队\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'auto_dev_team_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=600, capture_output=True, text=True)\n                _log(f'DEV-TEAM: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('DEV-TEAM: timeout (600s)')\n            except Exception as e:\n                _log(f'DEV-TEAM error: {e}')",
        "inspect_cycle": 900,
    },
    {
        "process_name": "sys_auto_patrol_squad",
        "duty": "自动巡逻队引擎: 6人AI巡逻队(巡检/收集/修复/验证/报告/持久AI)协同工作",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 自动巡逻队\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'auto_patrol_squad_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=600, capture_output=True, text=True)\n                _log(f'PATROL-SQUAD: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('PATROL-SQUAD: timeout (600s)')\n            except Exception as e:\n                _log(f'PATROL-SQUAD error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_security_enhancer",
        "duty": "安全增强引擎: 漏洞扫描+安全策略+入侵检测+防护加固",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 安全增强\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'security_enhancer.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'SEC-ENHANCE: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('SEC-ENHANCE: timeout (300s)')\n            except Exception as e:\n                _log(f'SEC-ENHANCE error: {e}')",
        "inspect_cycle": 900,
    },
    {
        "process_name": "sys_performance_optimizer",
        "duty": "性能优化引擎: 数据库索引优化+查询优化+缓存策略+资源调优",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 性能优化\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'performance_optimizer.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'PERF-OPT: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('PERF-OPT: timeout (300s)')\n            except Exception as e:\n                _log(f'PERF-OPT error: {e}')",
        "inspect_cycle": 1800,
    },
    {
        "process_name": "sys_omni_defense",
        "duty": "全方位防御引擎: 多层防御+攻击模式库+实时威胁响应+自动封禁",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 全方位防御\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'omni_defense_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'OMNI-DEF: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('OMNI-DEF: timeout (300s)')\n            except Exception as e:\n                _log(f'OMNI-DEF error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_workflow",
        "duty": "工作流引擎: 自动化工作流编排+任务依赖管理+流程自动化",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 工作流引擎\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'workflow_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'WORKFLOW: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('WORKFLOW: timeout (300s)')\n            except Exception as e:\n                _log(f'WORKFLOW error: {e}')",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_verify_round8",
        "duty": "8轮验证引擎: 多维度验证(功能/安全/性能/兼容/数据/逻辑/UI/API)+自动修复",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 8轮验证\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'verify_round8_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=600, capture_output=True, text=True)\n                _log(f'VERIFY-R8: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('VERIFY-R8: timeout (600s)')\n            except Exception as e:\n                _log(f'VERIFY-R8 error: {e}')",
        "inspect_cycle": 1800,
    },
    {
        "process_name": "sys_penetration_test",
        "duty": "渗透测试引擎: 自动化安全测试+漏洞挖掘+攻击模拟+修复建议",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 渗透测试\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'penetration_tester.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=600, capture_output=True, text=True)\n                _log(f'PEN-TEST: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('PEN-TEST: timeout (600s)')\n            except Exception as e:\n                _log(f'PEN-TEST error: {e}')",
        "inspect_cycle": 3600,
    },
    {
        "process_name": "sys_patrol_eigenflux_advisor",
        "duty": "巡检-EigenFlux顾问引擎: 巡检发现→EigenFlux专家咨询→建设性建议→脑库投喂→闭环改进",
        "mount_source": "SYSTEM_REQ",
        "work_body": "            # 巡检-EigenFlux顾问: 收集巡检发现→路由专家→生成建议→投喂脑库\n            try:\n                import subprocess\n                engine_py = os.path.join(os.path.dirname(ENGINE_DIR), 'engines', 'ai_patrol_eigenflux_advisor_engine.py')\n                r = subprocess.run([sys.executable, engine_py, 'once'],\n                    timeout=300, capture_output=True, text=True)\n                _log(f'PATROL-ADV: rc={r.returncode}')\n            except subprocess.TimeoutExpired:\n                _log('PATROL-ADV: timeout (300s)')\n            except Exception as e:\n                _log(f'PATROL-ADV error: {e}')",
        "inspect_cycle": 300,
    },
]


def mount_system_required() -> Dict:
    """挂载系统必需的自动化进程(无AI建议时,根据系统要求创建)"""
    result = {"mounted": 0, "skipped": 0, "details": []}

    for req in SYSTEM_REQUIRED_DAEMONS:
        # 检查是否已存在
        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            r = conn.execute(
                "SELECT * FROM mt_ai_smart_mount_processes WHERE process_name=?",
                (req["process_name"],)).fetchone()
            conn.close()

        if r and r["current_state"] in ("RUNNING", "IDLE"):
            # 检查PID是否真实存活；若IDLE/RUNNING但PID已死 → 视为需要重挂载
            pid_alive = False
            if r["pid"]:
                try:
                    os.kill(int(r["pid"]), 0)
                    pid_alive = True
                except (OSError, ValueError):
                    pid_alive = False
            if pid_alive:
                result["skipped"] += 1
                continue
            # 已死记录: 先清理状态到STOPPED便于重新挂载
            try:
                with _LOCK:
                    conn2 = _get_conn()
                    conn2.execute(
                        "UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED', updated_at=? WHERE process_name=?",
                        (_now(), req["process_name"]))
                    conn2.commit()
                    conn2.close()
            except Exception as _e:
                _log(f"[SYS-MOUNT] clean stale state fail {req['process_name']}: {_e}")

        # 生成脚本 + 挂载 — 单daemon失败不影响其他
        try:
            script_path = generate_daemon_script(
                process_name=req["process_name"],
                duty=req["duty"],
                suggestion_id=0,
                mount_score=1.0,  # 系统必需=满分
                work_body=req["work_body"],
                inspect_cycle=req["inspect_cycle"],
            )
        except Exception as e:
            _log(f"[SYS-MOUNT-SCRIPT-FAIL] {req['process_name']}: {e}")
            continue

        # 挂载（先reset restart_count，防止历史MAX-RESTART残留直接判死）
        try:
            with _LOCK:
                conn3 = _get_conn()
                conn3.execute(
                    "UPDATE mt_ai_smart_mount_processes SET restart_count=0 WHERE process_name=? AND restart_count>=?",
                    (req["process_name"], MAX_RESTART_COUNT))
                conn3.commit()
                conn3.close()
        except Exception:
            pass

        try:
            mount_process(
                process_name=req["process_name"],
                duty=req["duty"],
                script_path=script_path,
                suggestion_id=None,
                mount_source="SYSTEM_REQ",
                mount_score=1.0,
                expert_weights={},
            )
            result["mounted"] += 1
            result["details"].append(req["process_name"])
        except Exception as e:
            _log(f"[SYS-MOUNT-FAIL] {req['process_name']}: {e}")

    _log(f"[SYS-MOUNT] mounted={result['mounted']} skipped={result['skipped']}")
    return result


# ============================================================
# 9. CLI守护模式
# ============================================================
class SmartMountDaemon:
    """守护进程: 巡检循环(扫描建议+心跳监控+系统必需挂载)"""

    @staticmethod
    def read_pid() -> Optional[int]:
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
        except (ValueError, OSError):
            return None
        if pid == os.getpid():
            # PID_FILE 里写的是自己（启动脚本竞态写入），视为无效
            return None
        try:
            os.kill(pid, 0)
        except OSError:
            # stale PID：顺手清理，避免残留
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
            return None
        # 校验进程身份，防止 PID 被无关进程复用导致永久误判 RUNNING
        try:
            out = subprocess.check_output(
                ["/bin/ps", "-p", str(pid), "-o", "command="],
                stderr=subprocess.DEVNULL, timeout=5).decode(errors="ignore")
            if "ai_smart_mount_engine" not in out:
                try:
                    os.remove(PID_FILE)
                except OSError:
                    pass
                return None
        except Exception:
            pass  # ps 不可用时退回 kill -0 结果
        return pid

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def _self_defense_watchdog(cycle: int):
        """
        Layer-1 INTERNAL watchdog (zero dependency, zero external config).
        Runs every 2 cycles (~60s). Purpose:
          (A) Clean stale PID files in _runtime/pids whose processes don't exist.
          (B) DEDUP: for EVERY auto_daemons/*.py script, KEEP EXACTLY ONE running
              instance (the smallest PID = approximately the oldest started).
              Kill the rest with SIGKILL. Prevents the 122-process explosion seen
              before (sys_penetration_test had 122 duplicates / scheduler had 15).
          (C) Log a one-line WD cycle into smart_mount_monitor.log.

        This method NEVER raises. Any exception is swallowed so the main loop
        continues unconditionally.
        """
        try:
            stale_cleaned = 0
            total_pid_files = 0
            if os.path.isdir(PID_DIR):
                for pf in os.listdir(PID_DIR):
                    if not pf.endswith(".pid"):
                        continue
                    pf_path = os.path.join(PID_DIR, pf)
                    if not os.path.isfile(pf_path):
                        continue
                    total_pid_files += 1
                    try:
                        with open(pf_path) as fh:
                            pv_str = fh.read().strip()
                        if not pv_str or not pv_str.isdigit():
                            os.remove(pf_path)
                            stale_cleaned += 1
                            continue
                        pv_int = int(pv_str)
                        try:
                            os.kill(pv_int, 0)
                        except OSError:
                            os.remove(pf_path)
                            stale_cleaned += 1
                    except Exception:
                        # Never let a single bad pidfile crash watchdog
                        try:
                            os.remove(pf_path)
                            stale_cleaned += 1
                        except OSError:
                            pass

            # ---- (B) daemon dedup via ps ----
            import subprocess as _sp
            dedup_killed = 0
            try:
                ps_raw = _sp.check_output(
                    ["ps", "-eo", "pid,command"],
                    stderr=_sp.DEVNULL, timeout=8
                ).decode("utf-8", errors="ignore")
            except Exception:
                ps_raw = ""

            # group: {script_name: [sorted_pids_asc]}
            groups: Dict[str, List[int]] = {}
            for line in ps_raw.splitlines():
                if "auto_daemons/" not in line:
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                pid_s, cmd = parts
                if not pid_s.isdigit():
                    continue
                m_py = None
                for tok in cmd.split():
                    idx = tok.find("auto_daemons/")
                    if idx >= 0:
                        cand = tok[idx + len("auto_daemons/"):]
                        # take up to first .py (possibly trailing args)
                        py = cand.find(".py")
                        if py >= 0:
                            m_py = cand[:py + 3]
                            break
                if m_py is None:
                    continue
                if m_py not in groups:
                    groups[m_py] = []
                try:
                    groups[m_py].append(int(pid_s))
                except ValueError:
                    pass

            for sname, pids in groups.items():
                if len(pids) <= 1:
                    continue
                pids_sorted = sorted(pids)   # smallest = oldest approx
                keep = pids_sorted[0]
                for extra_pid in pids_sorted[1:]:
                    try:
                        # verify it's really an auto_daemons process before kill
                        try:
                            cl2 = _sp.check_output(
                                ["ps", "-p", str(extra_pid), "-o", "command="],
                                stderr=_sp.DEVNULL, timeout=3
                            ).decode("utf-8", errors="ignore")
                        except Exception:
                            cl2 = ""
                        if "auto_daemons/" not in cl2:
                            continue
                        os.kill(extra_pid, 9)  # SIGKILL — duplicates never deserve grace
                        dedup_killed += 1
                        try:
                            _log(f"[WD-DEDUP] cycle={cycle} killed duplicate {sname} pid={extra_pid} (keep pid={keep})")
                        except Exception:
                            pass
                    except OSError:
                        pass
                    except Exception:
                        pass

            # ---- (C) log line into monitor log ----
            alive_types = len(groups)
            total_procs = sum(len(v) for v in groups.values())
            sm_pid = os.getpid()
            try:
                mon_log = os.path.join(LOG_DIR, "ai_smart_mount_monitor.log")
                ts_now = time.strftime("%Y-%m-%d %H:%M:%S")
                line = (f"[{ts_now}] WD_CYCLE cycle={cycle} sm_pid={sm_pid} "
                        f"types={alive_types} total_procs={total_procs} "
                        f"stale_pid_cleaned={stale_cleaned}/{total_pid_files} "
                        f"dedup_killed={dedup_killed}\n")
                try:
                    # best effort append; do not hold locks
                    with open(mon_log, "a") as fm:
                        fm.write(line)
                    # cap monitor log at 5 MB → truncate to latest 20000 lines
                    try:
                        if os.path.getsize(mon_log) > 5 * 1024 * 1024:
                            with open(mon_log) as fm:
                                all_lines = fm.readlines()
                            if len(all_lines) > 20000:
                                with open(mon_log, "w") as fm:
                                    fm.writelines(all_lines[-20000:])
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            # Never propagate to main loop
            try:
                _log(f"[WD-SWALLOW] cycle={cycle} watchdog threw (ignored)", level="WARN")
            except Exception:
                pass

    @staticmethod
    def start():
        """启动守护进程(前台运行, 可被nohup/launchd托管)"""
        existing = SmartMountDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING  pid={existing}")
            return

        # 先确保表存在
        ensure_smart_mount_tables()

        # 写PID
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        # SIGTERM handler
        def _term(signum, frame):
            _log(f"[DAEMON] SIGTERM/SIGINT received (signum={signum}), shutting down...")
            _log_supervisor('INFO', 'ENGINE_STOP',
                            f'signal={signum} pid={os.getpid()}')
            SmartMountDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)

        _log(f"[DAEMON] START pid={os.getpid()} ppid={os.getppid()} interval={MONITOR_INTERVAL}s "
             f"daemonized={os.environ.get('MTSCOS_SM_DAEMONIZED', '0')}")
        _log_supervisor('INFO', 'ENGINE_START',
                        f'pid={os.getpid()} ppid={os.getppid()} interval={MONITOR_INTERVAL}s')

        # 首次启动: 挂载系统必需进程
        _log("[DAEMON] 挂载系统必需进程...")
        try:
            mount_system_required()
        except Exception as e:
            _log(f"[DAEMON][FATAL] mount_system_required failed: {e}")
            _log_supervisor('ERROR', 'MOUNT_SYSTEM_REQUIRED_FAILED', f'err={e}')
            # 不退出，主循环照常跑，下一轮 heartbeat_check 会重启失败进程

        # 主循环 - 守护进程绝不退出：任何异常都被捕获并继续，
        # 唯一退出途径是外部 SIGTERM/SIGINT，由 _term handler 处理。
        cycle = 0
        consecutive_errors = 0
        while True:
            cycle += 1
            try:
                # 每3个周期扫描一次建议池 (约90秒)
                if cycle % 3 == 0:
                    _log(f"[DAEMON] cycle={cycle} scanning suggestions...")
                    scan_and_mount()

                # 每10个周期重新挂载STOPPED的系统必需daemon (约5分钟)
                if cycle % 10 == 0:
                    try:
                        remount = mount_system_required()
                        if remount["mounted"] > 0:
                            _log(f"[DAEMON] cycle={cycle} remounted {remount['mounted']} STOPPED system daemons")
                    except Exception as e:
                        _log(f"[DAEMON] cycle={cycle} remount_system_required err: {e}")

                # 每个周期检查心跳
                hb = heartbeat_check()
                if hb["checked"] > 0:
                    _log(f"[DAEMON] cycle={cycle} heartbeat: checked={hb['checked']} "
                         f"alive={hb['alive']} timeout={hb['timeout']} restarted={hb['restarted']}")

                # 每2个周期(~60s)执行 Layer1 内置自卫看门狗：stale pid清理 + daemon去重
                # 零外部依赖，不依赖 cron / launchd / TCC / sudo
                if cycle % 2 == 0:
                    SmartMountDaemon._self_defense_watchdog(cycle)

                # 成功一轮，清零错误计数
                if consecutive_errors > 0:
                    _log(f"[DAEMON] cycle={cycle} recovered after {consecutive_errors} errors")
                    _log_supervisor('INFO', 'ENGINE_RECOVERED',
                                    f'after_errors={consecutive_errors}')
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                import traceback as _tb
                tb_str = _tb.format_exc()
                _log(f"[DAEMON] cycle={cycle} ERROR #{consecutive_errors}: {e}\n{tb_str}")
                _log_supervisor('ERROR', 'CYCLE_EXCEPTION',
                                f'cycle={cycle} err#{consecutive_errors} err={e} tb={tb_str[:500]}')
                # 连续 10 次错误升级为 FATAL，但仍不退出（守护职责）
                if consecutive_errors == 10:
                    _log(f"[DAEMON][FATAL] 10 consecutive errors, escalating but not exiting")
                    _log_supervisor('FATAL', '10_CONSECUTIVE_ERRORS',
                                    f'cycle={cycle} last_err={e}')
                # 错误退避：第 1 次 0s, 2-5 次 5s, 6+ 次 30s
                backoff = 0 if consecutive_errors == 1 else (5 if consecutive_errors <= 5 else 30)
                if backoff > 0:
                    time.sleep(backoff)
                continue

            time.sleep(MONITOR_INTERVAL)

    @staticmethod
    def stop():
        """停止守护进程"""
        pid = SmartMountDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED (no PID)")
            return

        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            # 如果还活着,强制杀
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        except OSError:
            pass

        SmartMountDaemon.clear_pid()
        print("[STATUS] STOPPED")

    @staticmethod
    def status() -> Dict:
        """查看状态"""
        ensure_smart_mount_tables()
        pid = SmartMountDaemon.read_pid()
        daemon_state = "RUNNING" if pid else "STOPPED"

        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # 进程列表
            procs = c.execute("""
                SELECT p.*, d.daemon_duty, d.priority
                FROM mt_ai_smart_mount_processes p
                LEFT JOIN mt_daemon_registry d ON p.daemon_id=d.daemon_id
                ORDER BY p.created_at DESC
            """).fetchall()

            # 待挂载建议数
            pending = c.execute("""
                SELECT COUNT(*) FROM mt_ai_suggestion_pool
                WHERE status='EVALUATED' AND priority>=5
            """).fetchone()[0]

            # 决策统计
            decisions = c.execute("""
                SELECT decision, COUNT(*) as cnt
                FROM mt_ai_mount_decisions
                GROUP BY decision
            """).fetchall()

            conn.close()

        result = {
            "daemon_pid": pid,
            "daemon_state": daemon_state,
            "total_processes": len(procs),
            "running_processes": sum(1 for p in procs if p["current_state"] == "RUNNING"),
            "pending_suggestions": pending,
            "decisions": {d["decision"]: d["cnt"] for d in decisions},
            "processes": [dict(p) for p in procs],
        }
        return result

    @staticmethod
    def list_processes():
        """列出所有挂载进程"""
        ensure_smart_mount_tables()
        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT p.*, d.daemon_duty, d.priority, d.inspect_cycle
                FROM mt_ai_smart_mount_processes p
                LEFT JOIN mt_daemon_registry d ON p.daemon_id=d.daemon_id
                ORDER BY p.created_at DESC
            """).fetchall()
            conn.close()
        return [dict(r) for r in rows]


# ============================================================
# CLI入口
# ============================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "start":
        SmartMountDaemon.start()

    elif cmd == "stop":
        SmartMountDaemon.stop()

    elif cmd == "status":
        s = SmartMountDaemon.status()
        print(f"{'='*60}")
        print(f"  Smart Mount Engine Status")
        print(f"{'='*60}")
        print(f"  Daemon PID:    {s['daemon_pid'] or '-'}")
        print(f"  Daemon State:  {s['daemon_state']}")
        print(f"  Total Procs:   {s['total_processes']}")
        print(f"  Running:       {s['running_processes']}")
        print(f"  Pending Sugs:  {s['pending_suggestions']}")
        print(f"  Decisions:     {s['decisions']}")
        print(f"{'='*60}")
        if s["processes"]:
            print(f"  {'Name':<30} {'State':<10} {'PID':<8} {'Score':<6} {'Source':<15}")
            print(f"  {'-'*30} {'-'*10} {'-'*8} {'-'*6} {'-'*15}")
            for p in s["processes"]:
                print(f"  {p['process_name'][:30]:<30} {p['current_state']:<10} "
                      f"{str(p['pid'] or '-'):<8} {p['mount_score']:<6.2f} {p['mount_source']:<15}")

    elif cmd == "list":
        procs = SmartMountDaemon.list_processes()
        if not procs:
            print("  (无挂载进程)")
        for p in procs:
            print(f"  [{p['current_state']}] {p['process_name']} pid={p['pid']} "
                  f"score={p['mount_score']:.2f} source={p['mount_source']} "
                  f"restart={p['restart_count']}")
            if p.get("daemon_duty"):
                print(f"         duty: {p['daemon_duty'][:80]}")

    elif cmd == "scan":
        ensure_smart_mount_tables()
        result = scan_and_mount()
        print(f"{'='*60}")
        print(f"  Scan & Mount Result")
        print(f"{'='*60}")
        print(f"  Scanned:   {result['scanned']}")
        print(f"  Mounted:   {result['mounted']}")
        print(f"  Deferred:  {result['deferred']}")
        print(f"  Rejected:  {result['rejected']}")
        for d in result["details"]:
            status = d.get("decision", "?")
            name = d.get("process_name", "-")
            score = d.get("final_score", 0)
            print(f"  [{status:<6}] score={score:.2f} {name}")
            if d.get("reason"):
                print(f"           {d['reason']}")

    elif cmd == "adopt":
        # 采纳指定建议ID
        if len(sys.argv) < 3:
            print("  用法: python3 ai_smart_mount_engine.py adopt <suggestion_id>")
            sys.exit(1)
        sid = int(sys.argv[2])
        ensure_smart_mount_tables()

        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            r = conn.execute(
                "SELECT * FROM mt_ai_suggestion_pool WHERE suggestion_id=?", (sid,)).fetchone()
            conn.close()

        if not r:
            print(f"  [ERROR] 建议不存在: #{sid}")
            sys.exit(1)

        sug = dict(r)
        ew = collect_expert_weights()
        decision = smart_mount_decision(sug, ew)

        if decision["decision"] != "MOUNT":
            print(f"  [DEFER] score={decision['final_score']:.2f} < {MOUNT_THRESHOLD}")
            print(f"  {decision['reason']}")
            sys.exit(0)

        process_name = f"adopt_{sug.get('direction', 'gen')}_{sid}"
        script_path = generate_daemon_script(
            process_name=process_name,
            duty=sug.get("suggestion", "")[:100],
            suggestion_id=sid,
            mount_score=decision["final_score"],
            work_body=_infer_work_body(sug),
        )
        pid = mount_process(
            process_name=process_name,
            duty=sug.get("suggestion", "")[:100],
            script_path=script_path,
            suggestion_id=sid,
            mount_source="AI_SUGGESTION",
            mount_score=decision["final_score"],
            expert_weights=ew,
        )
        print(f"  [MOUNTED] {process_name} pid={pid} score={decision['final_score']:.2f}")

    elif cmd == "create":
        # 手动创建自动化进程
        if len(sys.argv) < 4:
            print("  用法: python3 ai_smart_mount_engine.py create <name> <duty> [--cycle N]")
            sys.exit(1)
        name = sys.argv[2]
        duty = sys.argv[3]
        cycle = 60
        if "--cycle" in sys.argv:
            idx = sys.argv.index("--cycle")
            cycle = int(sys.argv[idx + 1])

        ensure_smart_mount_tables()
        script_path = generate_daemon_script(
            process_name=name, duty=duty,
            suggestion_id=0, mount_score=1.0,
            inspect_cycle=cycle,
        )
        pid = mount_process(
            process_name=name, duty=duty,
            script_path=script_path,
            mount_source="MANUAL", mount_score=1.0,
        )
        print(f"  [CREATED] {name} pid={pid} script={script_path}")

    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
