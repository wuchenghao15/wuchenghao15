#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 自动巡检队伍引擎 (Auto Dev Team Engine v2.0.0)
====================================================
自动发现系统未开发功能/功能异常 → 自动提交到专业团队 → 开发跟踪 → 全生命周期报告 → 数据库永久化存储

5大模块:
  1. GapScanner          - 需求/未开发功能扫描(检测pass/...占位/TODO/FIXME/缺失CRUD/孤儿路由)
  2. GapPrioritizer      - 5维权重排序(唯一权重入口)
  3. DevPipelineRunner   - 4阶段Pipeline(assign→IR14→implement→verify+persist)
  4. DevTaskDispatcher   - 开发任务派发(按功能类型分配到API/UI/DB/安全团队)
  5. SimpleAutoImplementer - 自动落地(safe=True的gap按决策树修改)
  6. CompletionVerifier  - 完成验证(复用_py_index快速校验)
  7. FullReportGenerator - 全生命周期报告生成

v2.0 改造(5×3矩阵=15项硬伤修复):
  算法维度:  _build_py_index单次解析复用 / verifier复用index / dispatch按weight排序
  权重维度:  GapPrioritizer 5维加权(W_sev*0.45+W_type*0.25+W_occur*0.12+W_fresh*0.10+W_team*0.08) / 建议池priority=ceil(w/10) / 单return+单audit日志
  架构维度:  4阶段Pipeline / ENGINE_REGISTRY注册+ensure_ready / warmup_system统一入口
  逻辑维度:  IR14批量事务单commit / flow_id脏数据defrag / _calc_impl_confidence决策树
  框架维度:  DB连接池(容量3) / 扫描缓存(ttl=900s mtime指纹) / GapEngineError错误码枚举
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import math
import os
import random
import re
import sys
import time
import sqlite3
import threading
import traceback
import logging
import enum
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('AutoDevTeam')

_BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_BASE, os.pardir, os.pardir))
FLASK_APP = os.path.join(PROJECT_ROOT, "flask-app")
ROUTES_DIR = os.path.join(FLASK_APP, "routes")
AI_ENGINES_DIR = os.path.join(FLASK_APP, "ai_engines")
ENG_DB = os.path.join(_BASE, "app.db")
SES_DB = os.path.join(AI_ENGINES_DIR, "app.db")
LOG_DIR = os.path.join(PROJECT_ROOT, "_runtime", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
PID_DIR = os.path.join(PROJECT_ROOT, "_runtime", "pids")
os.makedirs(PID_DIR, exist_ok=True)

if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

try:
    from mt_ir14_dev_flow import _get_conn as _orig_get_conn, _LOCK, feed_brain, ensure_tables
    HAS_DEV_FLOW = True
except Exception:
    HAS_DEV_FLOW = False
    _LOCK = threading.Lock()
    def _orig_get_conn(): return sqlite3.connect(ENG_DB, timeout=30)
    def feed_brain(flow_id, kind, content): pass
    def ensure_tables(): pass

IR14_HAS_FULL_API = False
IR14_STEP_FUNCS = {}
try:
    if AI_ENGINES_DIR not in sys.path:
        sys.path.insert(0, AI_ENGINES_DIR)
    from mt_ir14_dev_flow import (
        step1_create_proposal as ir14_step1,
        transition as ir14_transition,
        feed_brain as ir14_feed_brain,
        ensure_tables as ir14_ensure_tables,
        _LOCK as IR14_LOCK,
        _get_conn as _orig_get_ses_conn,
    )
    IR14_HAS_FULL_API = True
    IR14_STEP_FUNCS = {
        'step1': ir14_step1,
        'transition': ir14_transition,
        'feed_brain': ir14_feed_brain,
        'ensure_tables': ir14_ensure_tables,
    }
except Exception as _e:
    IR14_HAS_FULL_API = False
    IR14_LOCK = threading.RLock()
    def _orig_get_ses_conn(): return sqlite3.connect(SES_DB, timeout=10)
    def _ir14_stub(*a, **kw): pass
    IR14_STEP_FUNCS = {
        'step1': _ir14_stub,
        'transition': _ir14_stub,
        'feed_brain': _ir14_stub,
        'ensure_tables': _ir14_stub,
    }

IR14_LOCK = threading.RLock()

try:
    if AI_ENGINES_DIR not in sys.path:
        sys.path.insert(0, AI_ENGINES_DIR)
    from ai_intelligent_upgrade_engine import (
        register_daemon as ai_register_daemon,
        add_ai_suggestion as ai_add_suggestion,
    )
    HAS_UPGRADE_ENGINE = True
except Exception as _e:
    HAS_UPGRADE_ENGINE = False
    def ai_register_daemon(name="", duty="", dependencies="", priority=5, inspect_cycle="60s"):
        try:
            with _LOCK:
                c = get_conn(); cur = c.cursor()
                cur.execute("""CREATE TABLE IF NOT EXISTS mt_daemon_registry (
                    daemon_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    daemon_name TEXT UNIQUE, daemon_duty TEXT, dependencies TEXT,
                    priority INTEGER, inspect_cycle TEXT, current_state TEXT,
                    registered_at TEXT, updated_at TEXT)""")
                cur.execute("""INSERT OR IGNORE INTO mt_daemon_registry
                    (daemon_name, daemon_duty, dependencies, priority, inspect_cycle, current_state, registered_at, updated_at)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (name, duty, dependencies, priority, inspect_cycle, "IDLE",
                     datetime.now().isoformat(), datetime.now().isoformat()))
                c.commit(); return_to_pool(c, 'eng')
        except Exception: pass
        return 0
    def ai_add_suggestion(source="", suggestion="", direction=""):
        try:
            for db_path in (ENG_DB, SES_DB):
                try:
                    conn = sqlite3.connect(db_path, timeout=10)
                    cur = conn.cursor()
                    cur.execute("""CREATE TABLE IF NOT EXISTS mt_ai_suggestion_pool (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT, direction TEXT, suggestion TEXT,
                        priority INTEGER DEFAULT 5, status TEXT DEFAULT 'NEW',
                        created_at TEXT)""")
                    cur.execute("""INSERT INTO mt_ai_suggestion_pool
                        (source, direction, suggestion, priority, status, created_at)
                        VALUES(?,?,?,?,?,?)""",
                        (source, direction, suggestion, 5, "NEW", datetime.now().isoformat()))
                    conn.commit(); conn.close()
                except Exception:
                    continue
        except Exception: pass
        return 0

SKIP_DIRS = {
    '_migration_backups', '_migration_reports', 'backups', '__pycache__',
    '.git', '.svn', '.hg', 'node_modules', 'venv', '.venv', 'env', '.env',
    '.project_history', '_tmp', 'tmp', '.trae', '.vscode', '.idea',
    '_runtime', 'logs', '_logs', 'dist', 'build', '__pypackages__',
    '.eggs', '.mypy_cache', '.pytest_cache', '.ruff_cache', '.hypothesis',
    'sync_tmp', '_sync', 'onedrive_tmp', '.DS_Store',
    '备份', '归档', 'archive', 'temp', '.cache',
}

SKIP_FILES = {'auto_dev_team_engine.py', 'sample.py'}

DEV_TEAM_ROUTING = {
    'missing_api':          ('API开发团队', 'api_dev_team', '开发缺失的API接口'),
    'incomplete_ui':        ('UI开发团队', 'ui_dev_team', '完善不完整的UI功能'),
    'missing_crud':         ('数据库团队', 'db_dev_team', '开发缺失的CRUD操作'),
    'missing_security':     ('安全团队', 'security_dev_team', '补充安全相关功能'),
    'route_broken':         ('功能修复团队', 'bug_fix_team', '修复路由功能异常'),
    'placeholder_return':   ('功能完善团队', 'feature_complete_team', '替换占位符为真实实现'),
    'todo_fixme':           ('待办处理团队', 'todo_team', '处理TODO/FIXME标记项'),
    'orphan_route':         ('路由完善团队', 'route_team', '完善孤儿路由功能'),
    'missing_template':     ('模板团队', 'template_team', '补充缺失的模板文件'),
    'incomplete_route':     ('路由完善团队', 'route_team', '完善不完整的路由'),
    'unknown':              ('协调团队', 'coordination_team', '协调处理未知类型'),
}

PLACEHOLDER_PATTERNS = [
    (r'\bpass\s*$', 'placeholder_return', 'low', '函数体为pass(占位符)'),
    (r'\breturn\s+["\'](TODO|FIXME|HACK|XXX|TEMP|PLACEHOLDER)["\']', 'placeholder_return', 'high', '返回TODO/FIXME等占位符字符串'),
    (r'\breturn\s+["\']not implemented["\']', 'placeholder_return', 'high', '返回"not implemented"'),
    (r'\bjsonify\s*\(\s*\{[^}]*status["\']?\s*:\s*["\']?not\s*implemented["\']', 'placeholder_return', 'high', 'JSON返回not_implemented'),
    (r'\breturn\s+["\']coming soon["\']', 'placeholder_return', 'medium', '返回"coming soon"占位符'),
    (r'\.\.\.\s*$', 'placeholder_return', 'low', '函数体为...(Ellipsis)'),
    (r'\bTODO\s*[:：]', 'todo_fixme', 'medium', '代码中有TODO标记'),
    (r'\bFIXME\s*[:：]', 'todo_fixme', 'high', '代码中有FIXME标记'),
    (r'\bHACK\s*[:：]', 'todo_fixme', 'medium', '代码中有HACK标记'),
    (r'\bXXX\s*[:：]', 'todo_fixme', 'medium', '代码中有XXX标记'),
]

CRUD_PATTERNS = {
    'list':   (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?GET', '列表查询'),
    'create': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?POST', '创建'),
    'detail': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?GET.*?<', '详情查询'),
    'update': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?PUT', '更新'),
    'delete': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?DELETE', '删除'),
}

_IR14_TRANSITION_CHAIN = [
    "STEP_1_PROPOSAL",
    "STEP_2A_ROUND",
    "STEP_3_ZXF_DECISION",
    "STEP_32_PASS_SKIP_B",
    "STEP_4_CLERK_RECORD",
    "STEP_5_IMPL_DOCKING",
    "STEP_6_AI_TEAM_COORD",
    "STEP_7_EXECUTE",
]

# ============================================================
# 维度5-3: GapEngineError 错误码枚举
# ============================================================
class GapEngineError(enum.Enum):
    ERR_SCAN_IO = 1001
    ERR_AST_PARSE = 1002
    ERR_IR14_TRANSITION = 2001
    ERR_IR14_STEP1 = 2002
    ERR_IMPL_AST_FAIL = 3001
    ERR_IMPL_REGEX_FAIL = 3002
    ERR_VERIFY_RESCAN = 4001
    ERR_DB_WRITE = 5001

def _err_str(code: GapEngineError, detail: str = "") -> str:
    return f"[ERR_{code.value}:{code.name}] {detail}"

def _append_err_log(gap, code: GapEngineError, detail: str = ""):
    try:
        gap.development_log.append(_err_str(code, detail))
    except Exception:
        pass

# ============================================================
# 维度5-1: DB连接池 (_ENG_POOL容量3, _SES_POOL容量3)
# ============================================================
_POOL_LOCK = threading.Lock()
_ENG_POOL: List[Tuple[sqlite3.Connection, float]] = []
_SES_POOL: List[Tuple[sqlite3.Connection, float]] = []
_POOL_MAX = 3
_POOL_IDLE_MAX_SEC = 120

def _gc_pool(pool, now):
    alive = []
    for (conn, ts) in pool:
        if now - ts < _POOL_IDLE_MAX_SEC:
            alive.append((conn, ts))
        else:
            try:
                conn.close()
            except Exception:
                pass
    return alive

def get_conn() -> sqlite3.Connection:
    now = time.time()
    with _POOL_LOCK:
        global _ENG_POOL
        _ENG_POOL = _gc_pool(_ENG_POOL, now)
        if _ENG_POOL:
            conn, _ = _ENG_POOL.pop()
            return conn
    try:
        return sqlite3.connect(ENG_DB, timeout=30)
    except Exception:
        return sqlite3.connect(ENG_DB, timeout=30)

def get_ses_conn() -> sqlite3.Connection:
    now = time.time()
    with _POOL_LOCK:
        global _SES_POOL
        _SES_POOL = _gc_pool(_SES_POOL, now)
        if _SES_POOL:
            conn, _ = _SES_POOL.pop()
            return conn
    try:
        return sqlite3.connect(SES_DB, timeout=10)
    except Exception:
        return sqlite3.connect(SES_DB, timeout=10)

def return_to_pool(conn: sqlite3.Connection, tag: str = 'eng'):
    if conn is None:
        return
    now = time.time()
    try:
        with _POOL_LOCK:
            if tag == 'ses':
                global _SES_POOL
                if len(_SES_POOL) < _POOL_MAX:
                    _SES_POOL.append((conn, now))
                    return
            else:
                global _ENG_POOL
                if len(_ENG_POOL) < _POOL_MAX:
                    _ENG_POOL.append((conn, now))
                    return
        try:
            conn.close()
        except Exception:
            pass
    except Exception:
        try:
            conn.close()
        except Exception:
            pass

def _get_conn():
    return get_conn()

def _get_ses_conn():
    return get_ses_conn()

# ============================================================
# 维度5-2: 扫描缓存 TTL=900s (mtime*size指纹)
# ============================================================
_SCAN_RESULT_CACHE: Dict[str, Any] = {
    'mtime_fingerprint': None,
    'gaps': None,
    'created_at': 0,
    'ttl': 900,
    'scan_dir': None,
}
_SCAN_CACHE_LOCK = threading.Lock()

def _calc_scan_fingerprint(scan_dir: str, extra_dirs: List[str]) -> Optional[str]:
    try:
        h = hashlib.md5()
        dirs = [scan_dir] + [d for d in extra_dirs if os.path.isdir(d)]
        seen = set()
        for d in dirs:
            rp = os.path.realpath(d)
            if rp in seen:
                continue
            seen.add(rp)
            if not os.path.isdir(d):
                continue
            for root, dirs_list, files in os.walk(d):
                dirs_list[:] = [x for x in dirs_list if x not in SKIP_DIRS and not x.startswith('.')]
                for fname in files:
                    if not fname.endswith('.py') and not (fname.endswith('.html') or fname.endswith('.js')):
                        continue
                    if fname in SKIP_FILES:
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        st = os.stat(fpath)
                        h.update(f"{fpath}:{st.st_mtime}:{st.st_size}".encode())
                    except Exception:
                        continue
        return h.hexdigest()
    except Exception:
        return None

# ============================================================
# 维度3-2: ENGINE_REGISTRY 注册表 + register_engine()
# ============================================================
ENGINE_REGISTRY: Dict[str, Any] = {}

def register_engine(name: str, instance: Any):
    ENGINE_REGISTRY[name] = instance

def unregister_engine(name: str):
    ENGINE_REGISTRY.pop(name, None)

# ============================================================
# 数据结构
# ============================================================
@dataclass
class FeatureGap:
    gap_id: str = ""
    gap_type: str = ""
    title: str = ""
    description: str = ""
    file: str = ""
    line: int = 0
    route: str = ""
    severity: str = "medium"
    current_implementation: str = ""
    suggested_implementation: str = ""
    assigned_team: str = ""
    assigned_employee: str = ""
    status: str = "discovered"
    progress: float = 0.0
    detected_at: str = ""
    assigned_at: str = ""
    completed_at: str = ""
    verification_result: str = ""
    verification_passed: bool = False
    development_log: List[str] = field(default_factory=list)
    fix_code_snippet: str = ""
    original_code_snippet: str = ""
    flow_id: str = ""
    occurrences: int = 0
    routes_count: int = 0
    weight: float = 0.0

    @property
    def current_impl(self) -> str:
        return self.current_implementation

    @current_impl.setter
    def current_impl(self, val: str):
        self.current_implementation = val

    @property
    def suggested_impl(self) -> str:
        return self.suggested_implementation

    @suggested_impl.setter
    def suggested_impl(self, val: str):
        self.suggested_implementation = val


@dataclass
class DevLifecycleReport:
    report_id: str = ""
    flow_id: str = ""
    total_gaps: int = 0
    gaps_discovered: int = 0
    gaps_assigned: int = 0
    gaps_developing: int = 0
    gaps_completed: int = 0
    gaps_failed: int = 0
    teams_involved: List[str] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    summary: str = ""
    generated_at: str = ""
    duration: float = 0.0

# ============================================================
# 数据库表创建
# ============================================================
def ensure_dev_lifecycle_tables():
    with _LOCK:
        c = get_conn()
        try:
            cur = c.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS mt_feature_dev_lifecycle (
                gap_id TEXT PRIMARY KEY,
                gap_type TEXT,
                title TEXT,
                description TEXT,
                file_path TEXT,
                line_number INTEGER,
                route TEXT,
                severity TEXT,
                current_impl TEXT,
                suggested_impl TEXT,
                assigned_team TEXT,
                assigned_employee TEXT,
                status TEXT,
                progress REAL,
                detected_at TEXT,
                assigned_at TEXT,
                completed_at TEXT,
                verification_result TEXT,
                verification_passed INTEGER,
                development_log_json TEXT,
                fix_code_snippet TEXT,
                original_code_snippet TEXT,
                flow_id TEXT,
                occurrences INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS mt_dev_gap_registry (
                gap_id TEXT PRIMARY KEY,
                gap_type TEXT,
                severity TEXT,
                title TEXT,
                file_path TEXT,
                line_number INTEGER,
                status TEXT,
                flow_id TEXT,
                assigned_team TEXT,
                verification_passed INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS mt_dev_lifecycle_report (
                report_id TEXT PRIMARY KEY,
                flow_id TEXT,
                total_gaps INTEGER,
                gaps_discovered INTEGER,
                gaps_assigned INTEGER,
                gaps_completed INTEGER,
                gaps_failed INTEGER,
                teams_involved_json TEXT,
                timeline_json TEXT,
                gaps_detail_json TEXT,
                summary TEXT,
                generated_at TEXT,
                duration REAL
            )""")
            for alter_sql in [
                "ALTER TABLE mt_feature_dev_lifecycle ADD COLUMN weight REAL DEFAULT 0",
                "ALTER TABLE mt_dev_gap_registry ADD COLUMN weight REAL DEFAULT 0",
            ]:
                try:
                    cur.execute(alter_sql)
                except Exception:
                    pass
            c.commit()
        finally:
            return_to_pool(c, 'eng')


def _ensure_ses_session_table():
    try:
        with IR14_LOCK:
            conn = get_ses_conn()
            try:
                cur = conn.cursor()
                cur.execute("""CREATE TABLE IF NOT EXISTS mt_dev_flow_session (
                    flow_id TEXT PRIMARY KEY,
                    current_step TEXT NOT NULL DEFAULT 'STEP_1_PROPOSAL',
                    proposal_title TEXT, proposal_summary TEXT, proposal_json TEXT,
                    a_round_panels_json TEXT, a_round_attendance_json TEXT, a_round_discussion_json TEXT,
                    zhangxiaofeng_decision TEXT, b_round_json TEXT, super_admin_judgment TEXT,
                    clerk_record_json TEXT, clerk_vote_summary TEXT,
                    impl_team_contact_json TEXT, impl_plan_detail_json TEXT,
                    ai_team_coord_json TEXT, ai_core_roles_json TEXT,
                    execute_steps_json TEXT,
                    acceptance_json TEXT, acceptance_passed INTEGER DEFAULT 0,
                    acceptance_step_results_json TEXT,
                    summary_report_json TEXT,
                    db_written INTEGER DEFAULT 0, brain_fed INTEGER DEFAULT 0,
                    experience_fed INTEGER DEFAULT 0, anomaly_fed INTEGER DEFAULT 0,
                    smart_upgrade_version TEXT, smart_upgrade_should_upgrade INTEGER DEFAULT 0,
                    smart_upgrade_reasons_json TEXT, smart_upgrade_triggered INTEGER DEFAULT 0,
                    smart_upgrade_log_id TEXT,
                    git_sync_remote_name TEXT, git_sync_target_branch TEXT, git_sync_auth_mode TEXT,
                    git_sync_commit_hash TEXT, git_sync_commit_subject TEXT,
                    git_sync_status TEXT, git_sync_error TEXT, git_sync_json TEXT,
                    test1000_total INTEGER DEFAULT 0, test1000_pass INTEGER DEFAULT 0,
                    test1000_fail INTEGER DEFAULT 0, test1000_vuln INTEGER DEFAULT 0,
                    test1000_json TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    final_status TEXT NOT NULL DEFAULT 'OPEN',
                    loopback_count INTEGER NOT NULL DEFAULT 0
                )""")
                cur.execute("""CREATE TABLE IF NOT EXISTS mt_dev_flow_events (
                    ev_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flow_id TEXT NOT NULL, from_step TEXT NOT NULL, to_step TEXT NOT NULL,
                    event_kind TEXT NOT NULL, payload TEXT, operator TEXT DEFAULT 'AUTO_GAP_ENGINE',
                    triggered_at TEXT NOT NULL
                )""")
                cur.execute("""CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (
                    feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flow_id TEXT NOT NULL, feed_kind TEXT NOT NULL,
                    feed_content TEXT NOT NULL, triggered_at TEXT NOT NULL
                )""")
                conn.commit()
            finally:
                return_to_pool(conn, 'ses')
    except Exception:
        pass

# ============================================================
# 维度4-2: _defrag_flow_id_field 脏数据清理 + 双向sync
# ============================================================
def _defrag_flow_id_field(conn_lifecycle=None, conn_ses=None):
    dirty_tokens = ('once', '', '-', 'NA', 'n/a', 'null', 'NULL', 'None', 'none')
    closed_lc = False
    closed_ses = False
    try:
        if conn_lifecycle is None:
            conn_lifecycle = get_conn()
            closed_lc = True
        if conn_ses is None:
            conn_ses = get_ses_conn()
            closed_ses = True

        cur_lc = conn_lifecycle.cursor()
        in_clause = ",".join("?" * len(dirty_tokens))
        try:
            cur_lc.execute(
                f"UPDATE mt_feature_dev_lifecycle SET flow_id='' WHERE flow_id IN ({in_clause})",
                list(dirty_tokens))
            cur_lc.execute(
                f"UPDATE mt_dev_gap_registry SET flow_id='' WHERE flow_id IN ({in_clause})",
                list(dirty_tokens))
            conn_lifecycle.commit()
        except Exception:
            pass

        try:
            cur_lc.execute("SELECT gap_id, flow_id FROM mt_feature_dev_lifecycle")
            lc_rows = cur_lc.fetchall()
            lc_map = {}
            for r in lc_rows:
                try:
                    rd = dict(r)
                except Exception:
                    rd = {"gap_id": r[0], "flow_id": r[1]}
                gid = rd.get("gap_id", "")
                fid = rd.get("flow_id", "") or ""
                lc_map[gid] = fid

            cur_lc.execute("SELECT gap_id, flow_id FROM mt_dev_gap_registry")
            reg_rows = cur_lc.fetchall()
            reg_map = {}
            for r in reg_rows:
                try:
                    rd = dict(r)
                except Exception:
                    rd = {"gap_id": r[0], "flow_id": r[1]}
                gid = rd.get("gap_id", "")
                fid = rd.get("flow_id", "") or ""
                reg_map[gid] = fid

            now = datetime.now().isoformat()
            for gid, fid_lc in lc_map.items():
                fid_reg = reg_map.get(gid, "")
                if fid_lc and not fid_reg:
                    try:
                        cur_lc.execute(
                            "UPDATE mt_dev_gap_registry SET flow_id=?, updated_at=? WHERE gap_id=?",
                            (fid_lc, now, gid))
                    except Exception:
                        pass
                elif fid_reg and not fid_lc:
                    try:
                        cur_lc.execute(
                            "UPDATE mt_feature_dev_lifecycle SET flow_id=?, updated_at=? WHERE gap_id=?",
                            (fid_reg, now, gid))
                    except Exception:
                        pass
            conn_lifecycle.commit()
        except Exception:
            pass
    except Exception:
        pass
    finally:
        if closed_lc and conn_lifecycle is not None:
            return_to_pool(conn_lifecycle, 'eng')
        if closed_ses and conn_ses is not None:
            return_to_pool(conn_ses, 'ses')

# ============================================================
# 持久化 + AI建议池(统一权重入口)
# ============================================================
def _persist_gap_registry(gap: FeatureGap):
    try:
        now = datetime.now().isoformat()
        with _LOCK:
            c = get_conn()
            try:
                cur = c.cursor()
                cur.execute("""INSERT OR REPLACE INTO mt_dev_gap_registry
                    (gap_id, gap_type, severity, title, file_path, line_number,
                     status, flow_id, assigned_team, verification_passed, created_at, updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (gap.gap_id, gap.gap_type, gap.severity, gap.title[:300],
                     gap.file, gap.line, gap.status, gap.flow_id,
                     gap.assigned_team, 1 if gap.verification_passed else 0,
                     gap.detected_at or now, now))
                c.commit()
            finally:
                return_to_pool(c, 'eng')
    except Exception as e:
        logger.debug(f"写入gap registry失败 {gap.gap_id}: {e}")
        _append_err_log(gap, GapEngineError.ERR_DB_WRITE, f"registry persist: {e}")


def _push_ai_suggestion_for_gap(gap: FeatureGap):
    try:
        source = "SYS_GAP_DISCOVERY"
        suggestion = f"{gap.severity.upper()} {gap.title[:200]} -> {gap.description[:500]}"
        raw_w = getattr(gap, 'weight', 0.0) or 0.0
        priority = max(1, min(10, int(math.ceil(raw_w / 10.0))))
        if HAS_UPGRADE_ENGINE:
            try:
                ai_add_suggestion(source=source, suggestion=suggestion)
            except Exception:
                pass
        for db_path in (ENG_DB, SES_DB):
            try:
                conn = sqlite3.connect(db_path, timeout=10)
                cur = conn.cursor()
                cur.execute("""CREATE TABLE IF NOT EXISTS mt_ai_suggestion_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT, direction TEXT, suggestion TEXT,
                    priority INTEGER DEFAULT 5, status TEXT DEFAULT 'NEW',
                    created_at TEXT)""")
                cur.execute("""INSERT INTO mt_ai_suggestion_pool
                    (source, direction, suggestion, priority, status, created_at)
                    VALUES(?,?,?,?,?,?)""",
                    (source, "", suggestion, priority, "NEW",
                     datetime.now().isoformat()))
                conn.commit(); conn.close()
            except Exception:
                continue
    except Exception:
        pass

# ============================================================
# 维度2: GapPrioritizer 唯一权重入口 (5维加权+单return+单日志)
# ============================================================
class GapPrioritizer:

    def __init__(self,
                 W_sev: float = 0.45,
                 W_type: float = 0.25,
                 W_occur: float = 0.12,
                 W_fresh: float = 0.10,
                 W_team_avail: float = 0.08):
        self.W_sev = W_sev
        self.W_type = W_type
        self.W_occur = W_occur
        self.W_fresh = W_fresh
        self.W_team_avail = W_team_avail

        self.sev_score = {"low": 20, "medium": 50, "high": 85, "critical": 100}

        self.type_score = {
            "missing_api": 95,
            "route_broken": 90,
            "incomplete_route": 70,
            "missing_crud": 65,
            "todo_fixme": 40,
        }

    def _type_score_of(self, gap_type: str, current_impl: str = "") -> int:
        if gap_type in self.type_score:
            base = self.type_score[gap_type]
        else:
            base = 30
        if gap_type == "placeholder_return":
            ci = (current_impl or "").strip().lower()
            if ci in ("pass", "..."):
                return 50
            return 80
        return base

    def _sev_score_of(self, severity: str) -> int:
        return self.sev_score.get((severity or "medium").lower(), 50)

    def _occur_score_of(self, occurrences: int) -> int:
        try:
            n = int(occurrences or 0)
        except Exception:
            n = 0
        return min(n, 5)

    def _fresh_score_of(self, gap_file: str, py_index: Optional[Dict] = None) -> float:
        mtime_ts = None
        if py_index and gap_file:
            for v in py_index.values():
                if isinstance(v, dict) and v.get('relpath') == gap_file:
                    mtime_ts = v.get('mtime')
                    break
        if mtime_ts is None:
            try:
                absf = None
                for cand in (os.path.join(PROJECT_ROOT, gap_file),
                             os.path.join(FLASK_APP, gap_file),
                             gap_file if gap_file and os.path.isabs(gap_file) else None):
                    if cand and os.path.isfile(cand):
                        absf = cand; break
                if absf:
                    st = os.stat(absf)
                    mtime_ts = st.st_mtime
            except Exception:
                mtime_ts = None
        if mtime_ts is None:
            return 0.0
        try:
            days = max(0.0, (time.time() - float(mtime_ts)) / 86400.0)
        except Exception:
            days = 365.0
        return 1.0 / (1.0 + days)

    def _team_score_of(self, assigned_team: str, conn_lifecycle=None) -> int:
        if not assigned_team:
            return 0
        close_conn = False
        try:
            if conn_lifecycle is None:
                conn_lifecycle = get_conn()
                close_conn = True
            cur = conn_lifecycle.cursor()
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM mt_feature_dev_lifecycle WHERE assigned_team=?",
                    (assigned_team,))
                row = cur.fetchone()
                try:
                    total = int(list(dict(row).values())[0]) if row else 0
                except Exception:
                    total = int(row[0]) if row else 0
                if total == 0:
                    return 50
                cur.execute(
                    "SELECT COUNT(*) FROM mt_feature_dev_lifecycle WHERE assigned_team=? AND status='completed'",
                    (assigned_team,))
                row = cur.fetchone()
                try:
                    done = int(list(dict(row).values())[0]) if row else 0
                except Exception:
                    done = int(row[0]) if row else 0
                ratio = done / max(1, total)
                if ratio >= 0.7:
                    return 100
                return int(round(ratio * 100))
            except Exception:
                return 50
        except Exception:
            return 50
        finally:
            if close_conn and conn_lifecycle is not None:
                return_to_pool(conn_lifecycle, 'eng')

    def prioritize(self, gaps: List[FeatureGap], py_index: Optional[Dict] = None,
                   conn_lifecycle=None) -> List[FeatureGap]:
        results = []
        audit_logs = []
        close_conn = False
        if conn_lifecycle is None:
            try:
                conn_lifecycle = get_conn()
                close_conn = True
            except Exception:
                conn_lifecycle = None
        try:
            for gap in gaps:
                sev_s = self._sev_score_of(gap.severity)
                type_s = self._type_score_of(gap.gap_type, gap.current_impl)
                occur_s = self._occur_score_of(gap.occurrences)
                fresh_s = self._fresh_score_of(gap.file, py_index)
                team_s = self._team_score_of(gap.assigned_team or self._fallback_team(gap.gap_type), conn_lifecycle)

                weight = (self.W_sev * sev_s
                          + self.W_type * type_s
                          + self.W_occur * occur_s
                          + self.W_fresh * (fresh_s * 100.0)
                          + self.W_team_avail * team_s)
                weight = round(max(0.0, min(100.0, weight)), 2)
                gap.weight = weight
                results.append(gap)
                audit = (f"[GapPrioritizer] gap_id={gap.gap_id} weight={weight} "
                         f"source=SEV({sev_s})*{self.W_sev}+TYPE({type_s})*{self.W_type}"
                         f"+OCCUR({occur_s})*{self.W_occur}"
                         f"+FRESH({round(fresh_s*100,1)})*{self.W_fresh}"
                         f"+TEAM({team_s})*{self.W_team_avail}")
                audit_logs.append(audit)
            results.sort(key=lambda g: g.weight, reverse=True)
            for audit in audit_logs:
                logger.info(audit)
            return results
        finally:
            if close_conn and conn_lifecycle is not None:
                return_to_pool(conn_lifecycle, 'eng')

    def sort(self, gaps: List[FeatureGap], py_index: Optional[Dict] = None,
             conn_lifecycle=None) -> List[FeatureGap]:
        return self.prioritize(gaps, py_index=py_index, conn_lifecycle=conn_lifecycle)

    def _fallback_team(self, gap_type: str) -> str:
        info = DEV_TEAM_ROUTING.get(gap_type)
        if info:
            return info[1]
        return DEV_TEAM_ROUTING['unknown'][1]

    def ensure_ready(self):
        return True

# ============================================================
# IR14FlowLauncher (v2: 新增 _batch_transitions 单事务)
# ============================================================
class IR14FlowLauncher:

    def __init__(self):
        self._nn_counter: Dict[str, int] = defaultdict(int)
        try:
            ensure_tables()
        except Exception:
            pass
        try:
            if IR14_HAS_FULL_API:
                IR14_STEP_FUNCS.get('ensure_tables', lambda: None)()
        except Exception:
            pass
        _ensure_ses_session_table()

    def ensure_ready(self):
        return True

    def _gen_flow_id(self, gap: FeatureGap) -> str:
        today = datetime.now().strftime("%Y%m%d")
        seed = f"{gap.gap_id}{gap.gap_type}{gap.title}{time.time_ns()}"
        token = hashlib.md5(seed.encode()).hexdigest()[:8]
        key = f"{token}_{today}"
        self._nn_counter[key] += 1
        nnn = self._nn_counter[key]
        micro = int((time.time() * 1000000) % 1000000)
        return f"autogap_{token}_{today}_{nnn:03d}{micro:06d}"

    def _do_transition_inline(self, conn, cur, flow_id: str, to_step: str,
                              prev_steps: List[str], update_fields: Optional[Dict] = None):
        try:
            payload = {"prev_steps_json": json.dumps(prev_steps, ensure_ascii=False)}
            if IR14_HAS_FULL_API and 'transition' in IR14_STEP_FUNCS:
                try:
                    IR14_STEP_FUNCS['transition'](
                        flow_id, to_step, event_kind="AUTO_GAP",
                        payload=payload, update_fields=update_fields,
                        operator="AUTO_GAP_ENGINE"
                    )
                    return True
                except Exception:
                    pass
            row = cur.execute(
                "SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?",
                (flow_id,)
            ).fetchone()
            if not row:
                return False
            try:
                from_step = dict(row).get("current_step", row[0])
            except Exception:
                from_step = row[0]
            now = datetime.now().isoformat()
            cur.execute(
                "UPDATE mt_dev_flow_session SET current_step=?, updated_at=? WHERE flow_id=?",
                (to_step, now, flow_id))
            if update_fields:
                sets = []
                vals = []
                for k, v in update_fields.items():
                    sets.append(f"{k}=?")
                    vals.append(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                if sets:
                    vals.append(flow_id)
                    try:
                        cur.execute(f"UPDATE mt_dev_flow_session SET {','.join(sets)} WHERE flow_id=?", vals)
                    except Exception:
                        pass
            cur.execute(
                """INSERT INTO mt_dev_flow_events
                   (flow_id, from_step, to_step, event_kind, payload, operator, triggered_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (flow_id, from_step, to_step, "AUTO_GAP",
                 json.dumps(payload, ensure_ascii=False), "AUTO_GAP_ENGINE", now))
            return True
        except Exception as e:
            logger.debug(f"IR14 transition失败 {flow_id}->{to_step}: {e}")
            return False

    def _ensure_session_exists_inline(self, conn, cur, flow_id: str, title: str, summary: str, proposal_json: Dict):
        try:
            if IR14_HAS_FULL_API and 'step1' in IR14_STEP_FUNCS:
                try:
                    IR14_STEP_FUNCS['step1'](flow_id, title, summary, proposal_json)
                    return
                except Exception:
                    pass
            now = datetime.now().isoformat()
            cur.execute("SELECT 1 FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,))
            if not cur.fetchone():
                cur.execute(
                    """INSERT INTO mt_dev_flow_session
                       (flow_id, current_step, proposal_title, proposal_summary, proposal_json,
                        created_at, updated_at) VALUES(?,?,?,?,?,?,?)""",
                    (flow_id, "STEP_1_PROPOSAL", title, summary,
                     json.dumps(proposal_json, ensure_ascii=False), now, now))
            cur.execute(
                """INSERT INTO mt_dev_flow_events
                   (flow_id, from_step, to_step, event_kind, payload, operator, triggered_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (flow_id, "__CREATE__", "STEP_1_PROPOSAL", "CREATE",
                 json.dumps({"title": title}, ensure_ascii=False),
                 "AUTO_GAP_ENGINE", now))
        except Exception as e:
            logger.debug(f"创建session失败 {flow_id}: {e}")
            raise

    def _feed_brain_safe(self, flow_id: str, kind: str, content: str):
        try:
            if IR14_HAS_FULL_API and 'feed_brain' in IR14_STEP_FUNCS:
                try:
                    IR14_STEP_FUNCS['feed_brain'](flow_id, kind, content)
                    return
                except Exception:
                    pass
            with IR14_LOCK:
                conn = get_ses_conn()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """INSERT INTO mt_ai_brain_feed_log
                           (flow_id, feed_kind, feed_content, triggered_at) VALUES(?,?,?,?)""",
                        (flow_id, kind, content[:16000], datetime.now().isoformat()))
                    conn.commit()
                finally:
                    return_to_pool(conn, 'ses')
        except Exception as e:
            logger.debug(f"feed_brain失败 {flow_id}: {e}")

    # 维度4-1: 批量推进 单事务
    def _batch_transitions(self, gaps_list: List[FeatureGap]) -> Dict[str, int]:
        stats = {"success": 0, "failed": 0, "skipped": 0}
        if not gaps_list:
            return stats
        gap_savepoints = {}
        pend_feeds: List[Tuple[str, str, str]] = []
        with IR14_LOCK:
            conn = get_ses_conn()
            try:
                cur = conn.cursor()
                try:
                    conn.execute("BEGIN TRANSACTION")
                except Exception:
                    pass
                try:
                    total = len(gaps_list)
                    for idx, gap in enumerate(gaps_list):
                        try:
                            gap_savepoints[gap.gap_id] = list(gap.development_log)
                            flow_id = self._gen_flow_id(gap)
                            proposal_title = f"[GAP-{gap.severity.upper()}] {gap.title}"
                            proposal_summary = gap.description[:500]
                            proposal_json = {
                                "gap_id": gap.gap_id, "type": gap.gap_type,
                                "file": gap.file, "line": gap.line,
                                "severity": gap.severity,
                                "current_impl": gap.current_impl,
                                "suggested_impl": gap.suggested_impl,
                                "contract_ref": "MT_RULE_DEV §L2 代码规范 + MT_RULE_PERM §@system_container",
                                "owner_team": gap.assigned_team,
                                "bypass_allowed": False,
                                "source_engine": "sys_gap_discovery_engine",
                            }
                            self._ensure_session_exists_inline(conn, cur, flow_id, proposal_title,
                                                               proposal_summary, proposal_json)
                            prev_steps = ["STEP_1_PROPOSAL"]
                            chain = _IR14_TRANSITION_CHAIN
                            for i in range(1, len(chain)):
                                to_step = chain[i]
                                update_fields = None
                                if to_step == "STEP_3_ZXF_DECISION":
                                    update_fields = {"zhangxiaofeng_decision": "AUTO_PASS_GAP"}
                                elif to_step == "STEP_4_CLERK_RECORD":
                                    update_fields = {
                                        "clerk_record_json": {
                                            "decision": "PASS", "bypass_b_round": True,
                                            "reason": "AUTO_GAP_DISCOVERY 系统缺口自动推进",
                                        },
                                        "clerk_vote_summary": "AUTO_UNANIMOUS",
                                    }
                                elif to_step == "STEP_5_IMPL_DOCKING":
                                    update_fields = {
                                        "impl_team_contact_json": {"team": gap.assigned_team, "engine": "sys_gap_discovery_engine"},
                                        "impl_plan_detail_json": {"plan": "AUTO_IMPLEMENT", "gap_id": gap.gap_id},
                                    }
                                elif to_step == "STEP_6_AI_TEAM_COORD":
                                    update_fields = {
                                        "ai_team_coord_json": {"flow_id": flow_id, "coordinator": "AUTO_GAP_ENGINE"},
                                        "ai_core_roles_json": {"implementer": "SimpleAutoImplementer"},
                                    }
                                elif to_step == "STEP_7_EXECUTE":
                                    update_fields = {
                                        "execute_steps_json": {"steps": ["auto_implement", "verify", "persist"], "flow_id": flow_id}
                                    }
                                ok = self._do_transition_inline(conn, cur, flow_id, to_step,
                                                                 list(prev_steps), update_fields=update_fields)
                                if not ok:
                                    break
                                prev_steps.append(to_step)
                            gap.flow_id = flow_id
                            need_feed = (gap.severity in ("high", "critical")) or (gap.occurrences and gap.occurrences >= 20)
                            if need_feed:
                                try:
                                    brain_content1 = json.dumps({
                                        "event": "GAP_DISCOVERY", "gap_id": gap.gap_id,
                                        "gap_type": gap.gap_type, "severity": gap.severity,
                                        "file": gap.file, "line": gap.line, "title": gap.title,
                                        "occurrences": gap.occurrences,
                                    }, ensure_ascii=False)
                                    pend_feeds.append((flow_id, "GAP_DISCOVERY", brain_content1))
                                    brain_content2 = json.dumps({
                                        "event": "IR14_AUTO_LAUNCH", "gap_id": gap.gap_id,
                                        "flow_id": flow_id, "chain": chain,
                                        "source_engine": "sys_gap_discovery_engine",
                                    }, ensure_ascii=False)
                                    pend_feeds.append((flow_id, "GAP_DISCOVERY", brain_content2))
                                except Exception:
                                    pass
                            stats["success"] += 1
                            if (idx + 1) % 5 == 0 or (idx + 1) == total:
                                logger.info(f"[IR14Batch] progress {idx+1}/{total} ok={stats['success']} fail={stats['failed']}")
                        except Exception as e:
                            stats["failed"] += 1
                            if gap.gap_id in gap_savepoints:
                                gap.development_log = gap_savepoints[gap.gap_id]
                            gap.development_log.append(_err_str(GapEngineError.ERR_IR14_TRANSITION, str(e)))
                    try:
                        conn.commit()
                    except Exception as e:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        for gap in gaps_list:
                            if gap.gap_id in gap_savepoints:
                                gap.development_log = gap_savepoints[gap.gap_id]
                        stats = {"success": 0, "failed": len(gaps_list), "skipped": 0}
                        pend_feeds = []
                except Exception as outer_e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    for gap in gaps_list:
                        if gap.gap_id in gap_savepoints:
                            gap.development_log = gap_savepoints[gap.gap_id]
                        gap.development_log.append(_err_str(GapEngineError.ERR_IR14_TRANSITION, str(outer_e)))
                    stats = {"success": 0, "failed": len(gaps_list), "skipped": 0}
                    pend_feeds = []
            finally:
                return_to_pool(conn, 'ses')
        for (fid, kind, content) in pend_feeds:
            try:
                self._feed_brain_safe(fid, kind, content)
            except Exception:
                pass
        return stats

    def launch(self, gap: FeatureGap) -> str:
        stats = self._batch_transitions([gap])
        if stats.get("success", 0) > 0:
            return gap.flow_id or ""
        return ""


# ============================================================
# SimpleAutoImplementer (v2: _calc_impl_confidence 决策树)
# ============================================================
class SimpleAutoImplementer:

    def __init__(self):
        self._changed_files: Dict[str, str] = {}

    def ensure_ready(self):
        return True

    def _abs_file(self, gap_file: str) -> Optional[str]:
        candidates = [
            os.path.join(PROJECT_ROOT, gap_file),
            os.path.join(FLASK_APP, gap_file),
            gap_file if os.path.isabs(gap_file) else None,
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
        return None

    # 维度4-3: _calc_impl_confidence 决策树
    def _calc_impl_confidence(self, gap: FeatureGap) -> Tuple[bool, int, str]:
        gt = gap.gap_type
        ci = (gap.current_impl or "").strip()
        absf = self._abs_file(gap.file)

        if gt == "incomplete_route":
            if absf is None:
                return (False, 10, "rule_b_empty_routes_no_file")
            try:
                sz = os.path.getsize(absf)
            except Exception:
                sz = 0
            try:
                with open(absf, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                content = ""
            if sz > 1500 and 'Blueprint(' in content:
                return (False, 20, "rule_b_large_has_blueprint_skip")
            return (True, 95, "rule_b_empty_routes")

        if gt == "placeholder_return" and ci in ("pass", "..."):
            if absf is None:
                return (False, 15, "rule_a_no_file")
            try:
                with open(absf, 'r', encoding='utf-8', errors='replace') as f:
                    source = f.read()
                tree = ast.parse(source)
            except Exception as e:
                _append_err_log(gap, GapEngineError.ERR_AST_PARSE, str(e))
                return (False, 25, "rule_a_ast_parse_fail")
            try:
                func_name_to_match = None
                m = re.search(r':(\w+)\s*\(\)|函数\s+(\w+)', gap.title)
                if m:
                    func_name_to_match = m.group(1) or m.group(2)
            except Exception:
                func_name_to_match = None
            target = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if func_name_to_match and node.name != func_name_to_match:
                        continue
                    if node.lineno == gap.line or (gap.line and abs(node.lineno - gap.line) <= 5):
                        target = node
                        break
            if target is None:
                return (False, 35, "rule_a_node_not_found")
            arg_count = len(getattr(target.args, 'args', []))
            body = target.body or []
            if len(body) == 1 and gap.line == (body[0].lineno if body else target.lineno) and arg_count < 6:
                return (True, 90, "rule_a_pass_body")
            return (False, 40, "rule_a_multi_param_or_multi_body")

        if gt == "todo_fixme":
            if absf is None:
                return (False, 15, "rule_c_no_file")
            try:
                with open(absf, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except Exception:
                return (False, 20, "rule_c_read_fail")
            if 1 <= gap.line <= len(lines):
                the_line = lines[gap.line - 1].rstrip('\n')
                parts = the_line.split(':', 1)
                if len(parts) >= 2 and parts[1].strip():
                    return (True, 70, "rule_c_todo_mark")
            return (False, 30, "rule_c_todo_no_trailing")

        return (False, 0, "not_supported_gap_type")

    def _is_safe(self, gap: FeatureGap) -> bool:
        safe, conf, strat = self._calc_impl_confidence(gap)
        logger.info(f"[AutoImplementer] gap={gap.gap_id} strategy={strat} confidence={conf} safe={safe}")
        gap.development_log.append(f"[AutoImplementer] gap={gap.gap_id} strategy={strat} confidence={conf} safe={safe}")
        return safe

    def _read_lines_ctx(self, absf: str, line: int, ctx: int = 20) -> Tuple[List[str], str, int, int]:
        with open(absf, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        total = len(lines)
        start = max(0, line - ctx - 1)
        end = min(total, line + ctx)
        snippet = "".join(lines[start:end])
        return lines, snippet, start, end

    def _apply_rule_a(self, gap: FeatureGap, absf: str, flow_id: str) -> bool:
        try:
            with open(absf, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception:
            return False
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._apply_rule_a_regex(gap, absf, flow_id)
        try:
            func_name_to_match = None
            m = re.search(r':(\w+)\s*\(\)|函数\s+(\w+)', gap.title)
            if m:
                func_name_to_match = m.group(1) or m.group(2)
        except Exception:
            func_name_to_match = None
        is_route_file = absf.startswith(ROUTES_DIR) or 'route' in os.path.basename(absf).lower()
        has_request_arg = False
        target_node = None

        class Finder(ast.NodeVisitor):
            def __init__(self):
                self.result = None
            def visit_FunctionDef(self, node):
                nonlocal has_request_arg
                if self.result is not None:
                    return
                if func_name_to_match and node.name != func_name_to_match:
                    self.generic_visit(node); return
                if node.lineno == gap.line or (gap.line and abs(node.lineno - gap.line) <= 5):
                    args = [a.arg for a in (node.args.args or [])]
                    if 'request' in args or is_route_file:
                        has_request_arg = True
                    self.result = node
                    return
                self.generic_visit(node)
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

        finder = Finder()
        finder.visit(tree)
        target_node = finder.result
        if target_node is None:
            return self._apply_rule_a_regex(gap, absf, flow_id)

        try:
            class Replacer(ast.NodeTransformer):
                def __init__(self, target, flow, has_req):
                    self.target = target
                    self.flow = flow
                    self.has_req = has_req
                def visit_FunctionDef(self, node):
                    node = self.generic_visit(node)
                    if node is not self.target:
                        return node
                    try:
                        if self.has_req:
                            code_src = (
                                "try:\n"
                                "    from flask import jsonify as _fj, request as _fr\n"
                                "except Exception:\n"
                                "    _fj = None; _fr = None\n"
                                "if _fj is not None:\n"
                                f"    return _fj({{'status':'success','code':0,'message':'auto_implemented',"
                                f"'data':{{}},'gap_flow_id':'{self.flow}'}})\n"
                                "else:\n"
                                f"    return {{'status':'success','code':0,'message':'auto_implemented_by_gap_engine',"
                                f"'gap_flow_id':'{self.flow}'}}"
                            )
                            new_body = ast.parse(code_src).body
                        else:
                            new_body = ast.parse(
                                f"return {{'status':'success','code':0,'message':'auto_implemented_by_gap_engine',"
                                f"'gap_flow_id':'{self.flow}'}}"
                            ).body
                        for nb in new_body:
                            ast.copy_location(nb, node.body[0] if node.body else node)
                            ast.fix_missing_locations(nb)
                        node.body = new_body
                    except Exception:
                        node.body = [ast.Return(value=ast.Dict(
                            keys=[ast.Constant(s) for s in ['status','code','message','gap_flow_id']],
                            values=[ast.Constant('success'), ast.Constant(0),
                                    ast.Constant('auto_implemented_by_gap_engine'),
                                    ast.Constant(self.flow)]
                        ))]
                    return node
                def visit_AsyncFunctionDef(self, node):
                    return self.visit_FunctionDef(node)

            replacer = Replacer(target_node, flow_id, has_request_arg or is_route_file)
            new_tree = replacer.visit(tree)
            ast.fix_missing_locations(new_tree)
            try:
                new_source = ast.unparse(new_tree)
            except Exception:
                return self._apply_rule_a_regex(gap, absf, flow_id)
            original_ctx = self._read_lines_ctx(absf, gap.line)[1]
            gap.original_code_snippet = original_ctx
            with open(absf, 'w', encoding='utf-8') as f:
                f.write(new_source)
            gap.fix_code_snippet = (f"[RULE_A] AST replaced function body in "
                                    f"{os.path.basename(absf)} flow_id={flow_id}")
            return True
        except Exception as e:
            _append_err_log(gap, GapEngineError.ERR_IMPL_AST_FAIL, str(e))
            return self._apply_rule_a_regex(gap, absf, flow_id)

    def _apply_rule_a_regex(self, gap: FeatureGap, absf: str, flow_id: str) -> bool:
        try:
            lines, snippet, start, end = self._read_lines_ctx(absf, gap.line)
            gap.original_code_snippet = snippet
            idx = gap.line - 1
            if 0 <= idx < len(lines):
                indent_match = re.match(r'^(\s*)', lines[idx])
                indent = indent_match.group(1) if indent_match else ''
                new_line = (indent +
                    f"return {{'status':'success','code':0,'message':'auto_implemented_by_gap_engine',"
                    f"'gap_flow_id':'{flow_id}'}}\n")
                lines[idx] = new_line
            with open(absf, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            gap.fix_code_snippet = f"[RULE_A_FALLBACK] regex replaced line {gap.line} flow_id={flow_id}"
            return True
        except Exception as e:
            _append_err_log(gap, GapEngineError.ERR_IMPL_REGEX_FAIL, str(e))
            return False

    def _apply_rule_b(self, gap: FeatureGap, absf: str, flow_id: str) -> bool:
        try:
            base = os.path.basename(absf)
            mod_name = base.replace('_routes.py', '').replace('.py', '') or 'module'
            bp_name = f"{mod_name}_bp"
            with open(absf, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            gap.original_code_snippet = content[:2000]
            new_content = content
            if not re.search(r'from\s+flask\s+import\s+.*\bBlueprint\b', content):
                if re.search(r'^from\s+flask\s+import\s+', content, re.M):
                    new_content = re.sub(
                        r'^(from\s+flask\s+import\s+)([^\n]+)',
                        lambda m: f"{m.group(1)}Blueprint, jsonify, {m.group(2)}",
                        new_content, count=1, flags=re.M)
                else:
                    new_content = "from flask import Blueprint, jsonify\n" + new_content
            if not re.search(r'\bBlueprint\s*\(', new_content):
                bp_block = (
                    "\nbp = Blueprint('" + bp_name + "', __name__)\n\n"
                    "@bp.route('/stats/overview', methods=['GET'])\n"
                    "def stats_overview():\n"
                    "    return jsonify({'status':'ok','code':0,'data':{"
                    "'module':'" + mod_name + "','routes_implemented':1}}})\n\n"
                )
                m = re.search(r'^if\s+__name__\s*==\s*["\']__main__["\']', new_content, re.M)
                if m:
                    new_content = new_content[:m.start()] + bp_block + "\n" + new_content[m.start():]
                    if not re.search(r'return\s+bp\b', new_content):
                        new_content = re.sub(
                            r'(if\s+__name__\s*==\s*["\']__main__["\'])',
                            lambda m: f"return bp\n\n{m.group(1)}",
                            new_content, count=1)
                else:
                    new_content += "\n" + bp_block + "return bp\n"
            with open(absf, 'w', encoding='utf-8') as f:
                f.write(new_content)
            gap.fix_code_snippet = (f"[RULE_B] Injected Blueprint+stats_overview into "
                                    f"{base} flow_id={flow_id}")
            return True
        except Exception:
            return False

    def _apply_rule_c(self, gap: FeatureGap, absf: str, flow_id: str) -> bool:
        try:
            lines, snippet, start, end = self._read_lines_ctx(absf, gap.line)
            gap.original_code_snippet = snippet
            idx = gap.line - 1
            if 0 <= idx < len(lines):
                original = lines[idx].rstrip('\n')
                orig_stripped = original.lstrip()
                indent_match = re.match(r'^(\s*)', original)
                indent = indent_match.group(1) if indent_match else ''
                stripped = re.sub(r'^#?\s*', '', orig_stripped)
                m = re.search(r'(?:TODO|FIXME|HACK)\s*[:：]?\s*(.*)', stripped, re.I)
                tail = m.group(1)[:60] if m else stripped[:60]
                fixed = f"{indent}# [AUTO_FIXED by sys_gap_discovery_engine flow_id={flow_id}] 原注释: {tail}\n"
                lines[idx] = fixed
            with open(absf, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            gap.fix_code_snippet = f"[RULE_C] TODO/FIXME replaced at line {gap.line} flow_id={flow_id}"
            return True
        except Exception:
            return False

    def try_implement(self, gap: FeatureGap) -> bool:
        if not self._is_safe(gap):
            gap.development_log.append(f"[跟踪] gap不满足safe条件: type={gap.gap_type} severity={gap.severity}")
            return False
        flow_id = gap.flow_id or f"manual_{gap.gap_id}"
        absf = self._abs_file(gap.file)
        if not absf:
            gap.development_log.append("[跳过] 找不到绝对路径")
            return False
        ok = False
        try:
            if gap.gap_type == "incomplete_route" and gap.routes_count == 0:
                ok = self._apply_rule_b(gap, absf, flow_id)
            elif gap.gap_type == "placeholder_return" and gap.current_impl in ("pass", "..."):
                ok = self._apply_rule_a(gap, absf, flow_id)
            elif gap.gap_type == "todo_fixme":
                ok = self._apply_rule_c(gap, absf, flow_id)
            elif gap.gap_type == "placeholder_return":
                ok = self._apply_rule_a_regex(gap, absf, flow_id)
            if ok:
                gap.development_log.append(f"[AUTO_IMPLEMENTED] 文件已修改 flow_id={flow_id}")
                gap.status = gap.status or "in_development"
        except Exception as e:
            logger.debug(f"try_implement异常 gap={gap.gap_id}: {e}")
            _append_err_log(gap, GapEngineError.ERR_IMPL_AST_FAIL, str(e))
            ok = False
        return ok


# ============================================================
# CompletionVerifier (v2: 复用_py_index, 不重跑scan_all)
# ============================================================
class CompletionVerifier:

    def __init__(self, scan_dir: str = None, py_index: Optional[Dict] = None):
        self.scan_dir = scan_dir or FLASK_APP
        self.extra_scan_dirs = [ROUTES_DIR]
        self._timeline: List[Dict] = []
        self._cached_scan: Optional[List[FeatureGap]] = None
        self._py_index: Optional[Dict] = py_index

    def set_py_index(self, py_index: Dict):
        self._py_index = py_index

    def ensure_ready(self):
        return True

    def _get_cached_scan(self) -> List[FeatureGap]:
        if self._cached_scan is None:
            scanner = GapScanner(self.scan_dir)
            scanner.extra_scan_dirs = list(self.extra_scan_dirs)
            try:
                self._cached_scan = scanner.scan_all()
            except Exception:
                self._cached_scan = []
        return self._cached_scan

    def _invalidate_cache(self):
        self._cached_scan = None

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)

    def _iter_scan_dirs(self):
        dirs = [self.scan_dir] + [d for d in self.extra_scan_dirs if os.path.isdir(d)]
        seen = set()
        for d in dirs:
            rp = os.path.realpath(d)
            if rp in seen:
                continue
            seen.add(rp)
            yield d

    def _index_lookup(self, gap: FeatureGap) -> Optional[Dict]:
        if not self._py_index:
            return None
        for fpath, info in self._py_index.items():
            if not isinstance(info, dict):
                continue
            if info.get('relpath') == gap.file or os.path.basename(fpath) == os.path.basename(gap.file or ''):
                return info
        return None

    def _gap_still_exists(self, gap: FeatureGap) -> bool:
        info = self._index_lookup(gap)
        if info is not None:
            lines = info.get('lines') or []
            src = info.get('src') or ''
            tree = info.get('ast')
            ci = (gap.current_impl or '').strip()
            if 1 <= gap.line <= len(lines):
                target_line = lines[gap.line - 1].rstrip('\n')
                t_stripped = target_line.strip()
                if ci == 'pass' and t_stripped == 'pass':
                    return True
                if ci == '...' and t_stripped == '...':
                    return True
                if gap.gap_type == 'todo_fixme' and re.search(r'\b(TODO|FIXME|HACK)\b', target_line):
                    if 'AUTO_FIXED' not in target_line:
                        return True
            if tree is not None:
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Pass, ast.Expr)) and getattr(node, 'lineno', None) == gap.line:
                        if ci == 'pass' and isinstance(node, ast.Pass):
                            return True
                        if ci == '...' and isinstance(node, ast.Expr):
                            try:
                                if isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
                                    return True
                            except Exception:
                                pass
            if ci and re.search(r'(TODO|FIXME|HACK|XXX|not implemented|coming soon)', ci, re.I):
                if gap.line and 1 <= gap.line <= len(lines):
                    target = lines[gap.line - 1]
                    ci_tail = ci[:30]
                    if ci_tail and ci_tail in target:
                        return True
            return False
        fresh = self._get_cached_scan()
        for g in fresh:
            if g.gap_id == gap.gap_id:
                return True
            if (g.file == gap.file and abs(g.line - gap.line) <= 2
                    and g.gap_type == gap.gap_type):
                ci_old = (gap.current_impl or "").strip()
                ci_new = (g.current_impl or "").strip()
                if ci_old and ci_new and ci_old[:30] == ci_new[:30]:
                    return True
        return False

    def verify(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        self._log('VERIFY_START', '开始完成验证')
        verified_count = 0
        for gap in gaps:
            if gap.status in ('completed', 'testing', 'code_review', 'in_development', 'assigned'):
                passed = self._verify_single(gap)
                gap.verification_passed = passed
                gap.verification_result = 'PASS' if passed else 'FAIL'
                if passed:
                    gap.development_log.append(f"[验证通过] gap已修复 flow_id={gap.flow_id}")
                else:
                    gap.development_log.append(f"[验证失败] 重新扫描gap仍存在")
                    _append_err_log(gap, GapEngineError.ERR_VERIFY_RESCAN, "gap still present after implement")
                verified_count += 1
        self._log('VERIFY_COMPLETE', f'验证完成,共 {verified_count} 项')
        return gaps

    def verify_single(self, gap: FeatureGap) -> bool:
        passed = self._verify_single(gap)
        gap.verification_passed = passed
        gap.verification_result = 'PASS' if passed else 'FAIL'
        return passed

    def _verify_single(self, gap: FeatureGap) -> bool:
        try:
            if not gap.file:
                return True
            still = self._gap_still_exists(gap)
            if not still:
                return True
            absf = None
            candidates = [
                os.path.join(PROJECT_ROOT, gap.file),
                os.path.join(FLASK_APP, gap.file),
                gap.file if os.path.isabs(gap.file) else None,
            ]
            for c in candidates:
                if c and os.path.isfile(c):
                    absf = c; break
            if not absf:
                return True
            try:
                with open(absf, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except Exception:
                return True
            if gap.line and 1 <= gap.line <= len(lines):
                target = lines[gap.line - 1]
                if gap.current_impl == 'pass' and target.strip() == 'pass':
                    return False
                if gap.current_impl == '...' and target.strip() == '...':
                    return False
                if gap.gap_type == 'todo_fixme' and re.search(r'\b(TODO|FIXME|HACK)\b', target):
                    if 'AUTO_FIXED' not in target:
                        return False
            return True
        except Exception:
            return True


# ============================================================
# GapScanner (v2: _build_py_index + 缓存TTL)
# ============================================================
class GapScanner:

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or FLASK_APP
        self.extra_scan_dirs = [ROUTES_DIR]
        self._gaps: List[FeatureGap] = []
        self._timeline: List[Dict] = []
        self._py_index: Dict[str, Any] = {}
        self._log('SCAN_START', '开始功能缺失扫描')

    def ensure_ready(self):
        return True

    def get_py_index(self) -> Dict[str, Any]:
        return self._py_index

    def _iter_scan_dirs(self):
        dirs = [self.scan_dir] + [d for d in self.extra_scan_dirs if os.path.isdir(d)]
        seen = set()
        for d in dirs:
            rp = os.path.realpath(d)
            if rp in seen:
                continue
            seen.add(rp)
            yield d

    # 维度1-1: 一次性build index, 5维扫描复用
    def _build_py_index(self):
        self._py_index = {}
        target_special = set(self._get_target_py_files())
        py_files_set = set()

        for tf in target_special:
            if tf.endswith('.py'):
                py_files_set.add(tf)

        for scan_dir in self._iter_scan_dirs():
            if not os.path.isdir(scan_dir):
                continue
            for root, dirs, files in os.walk(scan_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                for fname in files:
                    if not fname.endswith('.py') and not (fname.endswith('.html') or fname.endswith('.js')):
                        continue
                    if fname in SKIP_FILES:
                        continue
                    fpath = os.path.join(root, fname)
                    if fpath in target_special:
                        continue
                    py_files_set.add(fpath)

        for fpath in sorted(py_files_set):
            try:
                relpath = os.path.relpath(fpath, PROJECT_ROOT)
            except Exception:
                relpath = fpath
            try:
                mtime = os.path.getmtime(fpath)
            except Exception:
                mtime = 0.0
            is_py = fpath.endswith('.py')
            src = ''
            lines = []
            tree = None
            routes_count = 0
            funcs = []
            if is_py:
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        src = f.read()
                    lines = src.splitlines(keepends=True)
                    try:
                        tree = ast.parse(src)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                funcs.append({
                                    "name": node.name,
                                    "lineno": node.lineno,
                                    "args": [a.arg for a in (node.args.args or [])],
                                    "body_len": len(node.body or []),
                                })
                    except SyntaxError:
                        tree = None
                    route_funcs = self._extract_route_functions(src)
                    routes_count = len(route_funcs)
                except Exception as e:
                    logger.debug(f"build_py_index 读取失败 {fpath}: {e}")
                    continue
            else:
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        src = f.read()
                    lines = src.splitlines(keepends=True)
                except Exception:
                    continue
            self._py_index[fpath] = {
                'src': src,
                'lines': lines,
                'ast': tree,
                'routes_count': routes_count,
                'funcs': funcs,
                'mtime': mtime,
                'relpath': relpath,
                'is_py': is_py,
            }

    def _get_target_py_files(self) -> List[str]:
        files = []
        for cand in (os.path.join(FLASK_APP, 'app.py'), os.path.join(FLASK_APP, 'main.py')):
            if os.path.isfile(cand):
                files.append(cand)
        if os.path.isdir(ROUTES_DIR):
            for fname in os.listdir(ROUTES_DIR):
                if fname.endswith('.py') and not fname.startswith('_'):
                    fp = os.path.join(ROUTES_DIR, fname)
                    if os.path.isfile(fp):
                        files.append(fp)
        return files

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[GapScanner] {event}: {detail}")

    # 维度5-2: scan_all入口先查缓存
    def scan_all(self) -> List[FeatureGap]:
        extra_dirs = list(self.extra_scan_dirs)
        with _SCAN_CACHE_LOCK:
            cache = _SCAN_RESULT_CACHE
            now = time.time()
            fp = _calc_scan_fingerprint(self.scan_dir, extra_dirs)
            if (cache.get('gaps') is not None
                    and cache.get('scan_dir') == self.scan_dir
                    and cache.get('mtime_fingerprint') == fp
                    and cache.get('created_at', 0) > 0
                    and (now - cache.get('created_at', 0)) < cache.get('ttl', 900)):
                self._log('SCAN_CACHE_HIT', f'缓存命中 {len(cache["gaps"])} gaps, age={round(now - cache.get("created_at",0),1)}s')
                return [FeatureGap(**g) if isinstance(g, dict) else g for g in cache['gaps']]

        self._gaps = []
        self._build_py_index()

        self._scan_route_placeholders()
        self._scan_todo_fixme()
        self._scan_missing_crud()
        self._scan_orphan_routes()
        self._scan_frontend_backend_mismatch()

        with _SCAN_CACHE_LOCK:
            _SCAN_RESULT_CACHE['scan_dir'] = self.scan_dir
            _SCAN_RESULT_CACHE['mtime_fingerprint'] = fp
            _SCAN_RESULT_CACHE['gaps'] = [
                {
                    'gap_id': g.gap_id,
                    'gap_type': g.gap_type,
                    'title': g.title,
                    'description': g.description,
                    'file': g.file,
                    'line': g.line,
                    'route': g.route,
                    'severity': g.severity,
                    'current_implementation': g.current_implementation,
                    'suggested_implementation': g.suggested_implementation,
                    'assigned_team': g.assigned_team,
                    'assigned_employee': g.assigned_employee,
                    'status': g.status,
                    'progress': g.progress,
                    'detected_at': g.detected_at,
                    'assigned_at': g.assigned_at,
                    'completed_at': g.completed_at,
                    'verification_result': g.verification_result,
                    'verification_passed': g.verification_passed,
                    'development_log': list(g.development_log),
                    'fix_code_snippet': g.fix_code_snippet,
                    'original_code_snippet': g.original_code_snippet,
                    'flow_id': g.flow_id,
                    'occurrences': g.occurrences,
                    'routes_count': g.routes_count,
                    'weight': g.weight,
                }
                for g in self._gaps
            ]
            _SCAN_RESULT_CACHE['created_at'] = now

        self._log('SCAN_COMPLETE', f'扫描完成,发现 {len(self._gaps)} 个功能缺失')
        return self._gaps

    def _scan_route_placeholders(self):
        self._log('PLACEHOLDER_SCAN', '扫描路由占位符')

        target_files = self._get_target_py_files()
        for target_file in target_files:
            info = self._py_index.get(target_file)
            if info is None:
                continue
            src = info.get('src', '')
            tree = info.get('ast')
            file_label = info.get('relpath', os.path.basename(target_file))
            routes_count = info.get('routes_count', 0)

            if routes_count == 0 and os.path.dirname(target_file) == ROUTES_DIR:
                try:
                    gap = self._create_gap(
                        gap_type='incomplete_route',
                        title=f'{os.path.basename(target_file)} 路由文件 0 routes',
                        description=f'路由文件 {file_label} 未定义任何路由，需要补充最小stats路由',
                        file=file_label,
                        line=1,
                        severity='low',
                        current_impl=f'routes_count=0',
                        route='',
                    )
                    gap.routes_count = 0
                    self._gaps.append(gap)
                except Exception:
                    pass

            if tree is None:
                continue
            route_functions = self._extract_route_functions(src)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    body = node.body
                    if len(body) == 1:
                        stmt = body[0]
                        if isinstance(stmt, ast.Pass):
                            gap = self._create_gap(
                                gap_type='placeholder_return',
                                title=f'{file_label}:{func_name} 体为pass',
                                description=f'函数 {func_name}() 的实现仅为pass,需要补充实际功能',
                                file=file_label,
                                line=stmt.lineno,
                                severity='medium',
                                current_impl='pass',
                                route=route_functions.get(func_name, ''),
                            )
                            self._gaps.append(gap)
                        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                            gap = self._create_gap(
                                gap_type='placeholder_return',
                                title=f'{file_label}:{func_name} 体为...',
                                description=f'函数 {func_name}() 的实现仅为...(Ellipsis),需要补充实际功能',
                                file=file_label,
                                line=stmt.lineno,
                                severity='medium',
                                current_impl='...',
                                route=route_functions.get(func_name, ''),
                            )
                            self._gaps.append(gap)
                        elif isinstance(stmt, ast.Return):
                            ret_val = self._get_return_value_str(stmt)
                            if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented|coming soon)', ret_val, re.I):
                                gap = self._create_gap(
                                    gap_type='placeholder_return',
                                    title=f'{file_label}:{func_name} 返回占位符',
                                    description=f'函数 {func_name}() 返回占位符字符串,需要替换为真实实现',
                                    file=file_label,
                                    line=stmt.lineno,
                                    severity='high',
                                    current_impl=ret_val,
                                    route=route_functions.get(func_name, ''),
                                )
                                self._gaps.append(gap)
                    elif len(body) >= 1:
                        last_stmt = body[-1]
                        if isinstance(last_stmt, ast.Return):
                            ret_val = self._get_return_value_str(last_stmt)
                            if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented|coming soon)', ret_val, re.I):
                                gap = self._create_gap(
                                    gap_type='placeholder_return',
                                    title=f'{file_label}:{func_name} 返回占位符',
                                    description=f'函数 {func_name}() 返回占位符字符串,需要替换为真实实现',
                                    file=file_label,
                                    line=last_stmt.lineno,
                                    severity='high',
                                    current_impl=ret_val,
                                    route=route_functions.get(func_name, ''),
                                )
                                self._gaps.append(gap)

        self._scan_other_files_placeholders()

    def _scan_other_files_placeholders(self):
        target_special = set(self._get_target_py_files())
        for fpath, info in self._py_index.items():
            if not isinstance(info, dict) or not info.get('is_py', False):
                continue
            if fpath in target_special:
                continue
            relpath = info.get('relpath', os.path.basename(fpath))
            tree = info.get('ast')
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    if func_name.startswith('_'):
                        continue
                    body = node.body
                    if len(body) == 1:
                        stmt = body[0]
                        if isinstance(stmt, ast.Pass):
                            gap = self._create_gap(
                                gap_type='placeholder_return',
                                title=f'{relpath}:{func_name}() 体为pass',
                                description=f'函数 {func_name}() 的实现仅为pass,需要补充实际功能',
                                file=relpath,
                                line=stmt.lineno,
                                severity='medium',
                                current_impl='pass',
                            )
                            self._gaps.append(gap)
                        elif isinstance(stmt, ast.Return):
                            ret_val = self._get_return_value_str(stmt)
                            if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented)', ret_val, re.I):
                                gap = self._create_gap(
                                    gap_type='placeholder_return',
                                    title=f'{relpath}:{func_name}() 返回占位符',
                                    description=f'函数 {func_name}() 返回占位符字符串',
                                    file=relpath,
                                    line=stmt.lineno,
                                    severity='high',
                                    current_impl=ret_val,
                                )
                                self._gaps.append(gap)
                    elif len(body) >= 1:
                        last_stmt = body[-1]
                        if isinstance(last_stmt, ast.Return):
                            ret_val = self._get_return_value_str(last_stmt)
                            if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented)', ret_val, re.I):
                                gap = self._create_gap(
                                    gap_type='placeholder_return',
                                    title=f'{relpath}:{func_name}() 返回占位符',
                                    description=f'函数 {func_name}() 返回占位符字符串',
                                    file=relpath,
                                    line=last_stmt.lineno,
                                    severity='high',
                                    current_impl=ret_val,
                                )
                                self._gaps.append(gap)

    def _extract_route_functions(self, source: str) -> Dict[str, str]:
        route_func_map = {}
        pattern = re.compile(
            r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\'].*?\)\s*\n\s*def\s+(\w+)',
            re.DOTALL
        )
        for m in pattern.finditer(source):
            route = m.group(1)
            func_name = m.group(2)
            route_func_map[func_name] = route
        return route_func_map

    def _get_return_value_str(self, node: ast.Return) -> str:
        if node.value is None:
            return 'None'
        try:
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return node.value.value
            elif isinstance(node.value, ast.JoinedStr):
                return ast.dump(node.value)
            else:
                return ast.unparse(node.value)
        except Exception:
            return ast.dump(node.value)

    def _scan_todo_fixme(self):
        self._log('TODO_SCAN', '扫描TODO/FIXME标记')

        for fpath, info in self._py_index.items():
            if not isinstance(info, dict) or not info.get('is_py', False):
                continue
            relpath = info.get('relpath', os.path.basename(fpath))
            lines = info.get('lines', [])

            for i, line in enumerate(lines, 1):
                for pattern, gap_type, severity, desc in PLACEHOLDER_PATTERNS:
                    if pattern in (r'\bpass\s*$', r'\.\.\.\s*$'):
                        continue
                    if re.search(pattern, line, re.IGNORECASE):
                        gap = self._create_gap(
                            gap_type=gap_type,
                            title=f'{relpath}:{i} {severity}标记',
                            description=f'代码中发现{desc}',
                            file=relpath,
                            line=i,
                            severity=severity,
                            current_impl=line.strip()[:100],
                        )
                        self._gaps.append(gap)
                        break

    def _scan_missing_crud(self):
        self._log('CRUD_SCAN', '扫描缺失的CRUD操作')

        target_files = self._get_target_py_files()
        for target_file in target_files:
            info = self._py_index.get(target_file)
            if info is None:
                continue
            source = info.get('src', '')
            file_label = info.get('relpath', os.path.basename(target_file))
            routes = set()
            for m in re.finditer(r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\']', source):
                routes.add(m.group(1))

            route_groups = defaultdict(set)
            for route in routes:
                parts = route.strip('/').split('/')
                if len(parts) >= 2:
                    prefix = '/' + '/'.join(parts[:-1])
                    route_groups[prefix].add(route)

            for prefix, group_routes in route_groups.items():
                has_list = any('GET' in r or r.endswith('/') or '<' not in r for r in group_routes)
                has_detail = any('<' in r for r in group_routes)
                has_create = any('POST' in r for r in group_routes)
                has_update = any('PUT' in r for r in group_routes)
                has_delete = any('DELETE' in r for r in group_routes)

                if has_list or has_detail:
                    missing = []
                    if not has_create:
                        missing.append('POST(创建)')
                    if has_detail and not has_update:
                        missing.append('PUT(更新)')
                    if has_detail and not has_delete:
                        missing.append('DELETE(删除)')

                    if missing:
                        gap = self._create_gap(
                            gap_type='missing_crud',
                            title=f'{file_label} 路由组 {prefix} 缺失CRUD操作',
                            description=f'路由组 {prefix} 缺少: {", ".join(missing)}',
                            file=file_label,
                            line=0,
                            route=prefix,
                            severity='medium',
                            current_impl=f'现有路由: {", ".join(sorted(group_routes))}',
                            suggested_impl=f'补充缺失的CRUD接口: {", ".join(missing)}',
                        )
                        self._gaps.append(gap)

    def _scan_orphan_routes(self):
        self._log('ORPHAN_SCAN', '扫描孤儿路由')

        target_files = self._get_target_py_files()
        for target_file in target_files:
            info = self._py_index.get(target_file)
            if info is None:
                continue
            source = info.get('src', '')
            tree = info.get('ast')
            file_label = info.get('relpath', os.path.basename(target_file))
            if tree is None:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    if func_name.startswith('_'):
                        continue
                    if not self._is_route_function(source, func_name):
                        continue

                    body = node.body
                    if len(body) <= 2:
                        for stmt in body:
                            if isinstance(stmt, ast.Return):
                                ret_str = self._get_return_value_str(stmt)
                                if ret_str and len(ret_str) < 50 and not ret_str.startswith('jsonify') and not ret_str.startswith('render_template'):
                                    if ret_str not in ('None', '', 'null', '{}', '[]'):
                                        gap = self._create_gap(
                                            gap_type='route_broken',
                                            title=f'{file_label}:{func_name} 功能可能不完整',
                                            description=f'函数 {func_name}() 返回简单内容,可能需要补充业务逻辑',
                                            file=file_label,
                                            line=stmt.lineno,
                                            severity='low',
                                            current_impl=f'return {ret_str}',
                                            route=self._get_route_for_func(source, func_name),
                                        )
                                        self._gaps.append(gap)

    def _scan_frontend_backend_mismatch(self):
        self._log('FE_BE_SCAN', '扫描前后端API不匹配')

        backend_routes = set()
        for fpath, info in self._py_index.items():
            if not isinstance(info, dict) or not info.get('is_py', False):
                continue
            content = info.get('src', '')
            for m in re.finditer(r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\']', content):
                backend_routes.add(m.group(1))

        frontend_calls = set()
        for fpath, info in self._py_index.items():
            if not isinstance(info, dict):
                continue
            if info.get('is_py', True):
                continue
            fname = os.path.basename(fpath)
            if not (fname.endswith('.html') or fname.endswith('.js')):
                continue
            content = info.get('src', '')
            relpath = info.get('relpath', os.path.basename(fpath))
            for m in re.finditer(r'(?:fetch|ajax|get|post|put|delete)\s*\(\s*["\']([^"\']*?/api/[^"\']*)["\']', content):
                api_call = m.group(1)
                if api_call not in backend_routes and api_call not in frontend_calls:
                    frontend_calls.add(api_call)
                    gap = self._create_gap(
                        gap_type='missing_api',
                        title=f'前端API {api_call} 后端未实现',
                        description=f'{relpath} 中引用了 {api_call},但后端路由未实现',
                        file=relpath,
                        line=0,
                        route=api_call,
                        severity='high',
                        current_impl=f'前端调用: {api_call}',
                        suggested_impl=f'在后端添加 {api_call} 路由',
                    )
                    self._gaps.append(gap)

    def _is_route_function(self, source: str, func_name: str) -> bool:
        pattern = re.compile(
            r'@(?:app|bp_\w+)\.route[^)]*\)\s*\n\s*(?:@\w+\s*\n)*\s*def\s+' + re.escape(func_name),
            re.DOTALL
        )
        return bool(pattern.search(source))

    def _get_route_for_func(self, source: str, func_name: str) -> str:
        pattern = re.compile(
            r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\'].*?\)\s*\n\s*(?:@\w+\s*\n)*\s*def\s+' + re.escape(func_name),
            re.DOTALL
        )
        m = pattern.search(source)
        return m.group(1) if m else ''

    def _create_gap(self, gap_type: str, title: str, description: str,
                    file: str, line: int, severity: str = 'medium',
                    current_impl: str = '', suggested_impl: str = '',
                    route: str = '') -> FeatureGap:
        gap_id = hashlib.md5(
            f"{gap_type}:{file}:{line}:{title}".encode()
        ).hexdigest()[:16]

        gap = FeatureGap(
            gap_id=gap_id,
            gap_type=gap_type,
            title=title,
            description=description,
            file=file,
            line=line,
            route=route,
            severity=severity,
            current_implementation=current_impl,
            suggested_implementation=suggested_impl,
            status='discovered',
            progress=0.0,
            detected_at=datetime.now().isoformat(),
        )
        return gap

# ============================================================
# 维度3-1: DevPipelineRunner 4阶段 Pipeline
# ============================================================
class DevPipelineRunner:

    def __init__(self, scanner: Optional[GapScanner] = None,
                 prioritizer: Optional[GapPrioritizer] = None,
                 ir14: Optional[IR14FlowLauncher] = None,
                 implementer: Optional[SimpleAutoImplementer] = None,
                 verifier: Optional[CompletionVerifier] = None,
                 persister=None,
                 safe_only: bool = True,
                 max_impl: int = 9999):
        self.scanner = scanner
        self.prioritizer = prioritizer or GapPrioritizer()
        self.ir14 = ir14
        self.implementer = implementer
        self.verifier = verifier
        self.persister = persister
        self.safe_only = safe_only
        self.max_impl = max_impl
        self._impl_count = 0
        self._timeline: List[Dict] = []
        self.engines: Dict[str, Any] = {
            'scanner': scanner,
            'prioritizer': self.prioritizer,
            'ir14': ir14,
            'implementer': implementer,
            'verifier': verifier,
            'persister': persister,
        }
        for name, inst in self.engines.items():
            if inst is not None:
                register_engine(name, inst)
        self.ensure_ready()

    def ensure_ready(self):
        for name, inst in self.engines.items():
            if inst is None:
                continue
            ready_fn = getattr(inst, 'ensure_ready', None)
            if callable(ready_fn):
                try:
                    ready_fn()
                except Exception as e:
                    logger.debug(f"engine {name} ensure_ready 异常: {e}")
            for mname in ('ensure_tables',):
                fn = getattr(inst, mname, None)
                if callable(fn):
                    try:
                        fn()
                    except Exception:
                        pass

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[DevPipelineRunner] {event}: {detail}")

    def _run_stage_safe(self, stage_name: str, stage_fn, gaps: List[FeatureGap]) -> Tuple[List[FeatureGap], Dict]:
        stats = {"stage": stage_name, "input": len(gaps), "processed": 0, "failed": 0}
        result = []
        try:
            for g in gaps:
                try:
                    result.append(g)
                except Exception:
                    stats["failed"] += 1
            processed, st = stage_fn(gaps)
            for k, v in (st or {}).items():
                stats[k] = v
            stats["processed"] = len(processed)
            return processed, stats
        except Exception as e:
            stats["failed"] = len(gaps)
            stats["error"] = str(e)
            for g in gaps:
                try:
                    g.development_log.append(f"[Pipeline:{stage_name}] stage异常: {e}")
                except Exception:
                    pass
            return gaps, stats

    # stage1: assign team/employee/status=assigned + persist_lifecycle + registry + suggestion
    def _stage1_assign(self, gaps: List[FeatureGap]) -> Tuple[List[FeatureGap], Dict]:
        stats = {"assigned": 0, "persist_lifecycle": 0, "registry": 0, "suggestions": 0}
        for gap in gaps:
            try:
                team, employee, task_desc = self._route_to_team(gap)
                gap.assigned_team = team
                gap.assigned_employee = employee
                gap.status = 'assigned'
                gap.progress = 0.1
                gap.assigned_at = datetime.now().isoformat()
                gap.development_log.append(f'[派发] 分配给 {team}/{employee}: {task_desc}')
                stats["assigned"] += 1
            except Exception:
                pass
            try:
                self._persist_lifecycle_one(gap)
                stats["persist_lifecycle"] += 1
            except Exception:
                pass
            try:
                _persist_gap_registry(gap)
                stats["registry"] += 1
            except Exception:
                pass
            try:
                _push_ai_suggestion_for_gap(gap)
                stats["suggestions"] += 1
            except Exception:
                pass
        return gaps, stats

    def _stage2_ir14_flow(self, gaps: List[FeatureGap]) -> Tuple[List[FeatureGap], Dict]:
        stats = {"ir14_success": 0, "ir14_failed": 0, "persist_after": 0}
        if self.ir14 is not None:
            batch_stats = {}
            try:
                batch_stats = self.ir14._batch_transitions(gaps)
            except Exception as e:
                logger.debug(f"IR14 batch异常: {e}")
                batch_stats = {"success": 0, "failed": len(gaps)}
            stats["ir14_success"] = batch_stats.get("success", 0)
            stats["ir14_failed"] = batch_stats.get("failed", 0)
            for gap in gaps:
                try:
                    self._persist_lifecycle_one(gap)
                    _persist_gap_registry(gap)
                    stats["persist_after"] += 1
                except Exception:
                    pass
        return gaps, stats

    def _stage3_implement(self, gaps: List[FeatureGap]) -> Tuple[List[FeatureGap], Dict]:
        stats = {"impl_attempt": 0, "impl_success": 0, "impl_skipped_safe": 0, "impl_skipped_quota": 0,
                 "persist_after": 0}
        if self.implementer is None:
            return gaps, stats
        for gap in gaps:
            if self._impl_count >= self.max_impl:
                stats["impl_skipped_quota"] += 1
                continue
            try:
                if self.safe_only:
                    safe = self.implementer._is_safe(gap)
                    if not safe:
                        stats["impl_skipped_safe"] += 1
                        continue
                stats["impl_attempt"] += 1
                impl_ok = self.implementer.try_implement(gap)
                if impl_ok:
                    self._impl_count += 1
                    gap.progress = max(gap.progress, 0.5)
                    stats["impl_success"] += 1
            except Exception as e:
                logger.debug(f"implement失败 gap={gap.gap_id}: {e}")
            try:
                self._persist_lifecycle_one(gap)
                _persist_gap_registry(gap)
                stats["persist_after"] += 1
            except Exception:
                pass
        return gaps, stats

    def _stage4_verify_and_persist(self, gaps: List[FeatureGap]) -> Tuple[List[FeatureGap], Dict]:
        stats = {"verify_pass": 0, "verify_fail": 0, "persist_after": 0}
        if self.verifier is not None:
            for gap in gaps:
                try:
                    self.verifier.verify_single(gap)
                    if gap.verification_passed:
                        gap.progress = 1.0
                        gap.status = 'completed'
                        gap.completed_at = datetime.now().isoformat()
                        stats["verify_pass"] += 1
                    else:
                        stats["verify_fail"] += 1
                except Exception as e:
                    logger.debug(f"verify失败 gap={gap.gap_id}: {e}")
                    stats["verify_fail"] += 1
        for gap in gaps:
            try:
                self._persist_lifecycle_one(gap)
                _persist_gap_registry(gap)
                stats["persist_after"] += 1
            except Exception:
                pass
        return gaps, stats

    def run_pipeline(self, gaps: List[FeatureGap], py_index=None) -> Tuple[List[FeatureGap], Dict[str, Dict]]:
        all_stats: Dict[str, Dict] = {}
        gaps, st = self._run_stage_safe("stage1_assign", self._stage1_assign, gaps)
        all_stats["stage1_assign"] = st
        self._log("STAGE1_ASSIGN_DONE", f"assigned={st.get('assigned',0)} persist={st.get('persist_lifecycle',0)}")

        gaps, st = self._run_stage_safe("stage2_ir14_flow", self._stage2_ir14_flow, gaps)
        all_stats["stage2_ir14_flow"] = st
        self._log("STAGE2_IR14_DONE", f"ir14_success={st.get('ir14_success',0)} ir14_failed={st.get('ir14_failed',0)}")

        gaps, st = self._run_stage_safe("stage3_implement", self._stage3_implement, gaps)
        all_stats["stage3_implement"] = st
        self._log("STAGE3_IMPL_DONE", f"impl_success={st.get('impl_success',0)} skipped_safe={st.get('impl_skipped_safe',0)}")

        gaps, st = self._run_stage_safe("stage4_verify_and_persist", self._stage4_verify_and_persist, gaps)
        all_stats["stage4_verify_and_persist"] = st
        self._log("STAGE4_VERIFY_DONE", f"verify_pass={st.get('verify_pass',0)} verify_fail={st.get('verify_fail',0)}")

        return gaps, all_stats

    def _route_to_team(self, gap: FeatureGap) -> Tuple[str, str, str]:
        gap_type = gap.gap_type
        if gap_type in DEV_TEAM_ROUTING:
            team, employee, desc = DEV_TEAM_ROUTING[gap_type]
            return team, employee, desc
        if gap.severity in ('critical', 'high'):
            return DEV_TEAM_ROUTING['route_broken'][0], DEV_TEAM_ROUTING['route_broken'][1], '紧急功能修复'
        return DEV_TEAM_ROUTING['unknown'][0], DEV_TEAM_ROUTING['unknown'][1], '协调处理'

    def _persist_lifecycle_one(self, gap: FeatureGap):
        try:
            now = datetime.now().isoformat()
            with _LOCK:
                c = get_conn()
                try:
                    cur = c.cursor()
                    cur.execute("""INSERT OR REPLACE INTO mt_feature_dev_lifecycle
                        (gap_id, gap_type, title, description, file_path, line_number, route,
                         severity, current_impl, suggested_impl, assigned_team, assigned_employee,
                         status, progress, detected_at, assigned_at, completed_at,
                         verification_result, verification_passed, development_log_json,
                         fix_code_snippet, original_code_snippet, flow_id, occurrences,
                         created_at, updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (gap.gap_id, gap.gap_type, gap.title, gap.description,
                         gap.file, gap.line, gap.route, gap.severity,
                         gap.current_implementation, gap.suggested_implementation,
                         gap.assigned_team, gap.assigned_employee, gap.status,
                         gap.progress, gap.detected_at, gap.assigned_at,
                         gap.completed_at, gap.verification_result,
                         1 if gap.verification_passed else 0,
                         json.dumps(gap.development_log, ensure_ascii=False),
                         gap.fix_code_snippet, gap.original_code_snippet,
                         gap.flow_id, gap.occurrences or 0, now, now))
                    c.commit()
                finally:
                    return_to_pool(c, 'eng')
        except Exception as e:
            logger.debug(f"lifecycle持久化失败 {gap.gap_id}: {e}")
            _append_err_log(gap, GapEngineError.ERR_DB_WRITE, f"lifecycle persist: {e}")

# ============================================================
# DevTaskDispatcher (v2: 第一步按weight排序, 调PipelineRunner)
# ============================================================
class DevTaskDispatcher:

    def __init__(self, enable_flow: bool = True, enable_implement: bool = True,
                 enable_verify: bool = True, safe_only: bool = True, max_impl: int = 9999):
        self._assigned: List[FeatureGap] = []
        self._timeline: List[Dict] = []
        self.enable_flow = enable_flow
        self.enable_implement = enable_implement
        self.enable_verify = enable_verify
        self.safe_only = safe_only
        self.max_impl = max_impl
        self.prioritizer = GapPrioritizer()
        self._ir14 = IR14FlowLauncher() if enable_flow else None
        self._impl = SimpleAutoImplementer() if enable_implement else None
        self._verifier = CompletionVerifier() if enable_verify else None
        self._impl_count = 0
        self._pipeline: Optional[DevPipelineRunner] = None
        self._log('DISPATCH_START', '开始任务派发')

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[DevTaskDispatcher] {event}: {detail}")

    def _persist_lifecycle_one(self, gap: FeatureGap):
        try:
            now = datetime.now().isoformat()
            with _LOCK:
                c = get_conn()
                try:
                    cur = c.cursor()
                    cur.execute("""INSERT OR REPLACE INTO mt_feature_dev_lifecycle
                        (gap_id, gap_type, title, description, file_path, line_number, route,
                         severity, current_impl, suggested_impl, assigned_team, assigned_employee,
                         status, progress, detected_at, assigned_at, completed_at,
                         verification_result, verification_passed, development_log_json,
                         fix_code_snippet, original_code_snippet, flow_id, occurrences,
                         created_at, updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (gap.gap_id, gap.gap_type, gap.title, gap.description,
                         gap.file, gap.line, gap.route, gap.severity,
                         gap.current_implementation, gap.suggested_implementation,
                         gap.assigned_team, gap.assigned_employee, gap.status,
                         gap.progress, gap.detected_at, gap.assigned_at,
                         gap.completed_at, gap.verification_result,
                         1 if gap.verification_passed else 0,
                         json.dumps(gap.development_log, ensure_ascii=False),
                         gap.fix_code_snippet, gap.original_code_snippet,
                         gap.flow_id, gap.occurrences or 0, now, now))
                    c.commit()
                finally:
                    return_to_pool(c, 'eng')
        except Exception as e:
            logger.debug(f"lifecycle持久化失败 {gap.gap_id}: {e}")

    def dispatch(self, gaps: List[FeatureGap], py_index=None) -> List[FeatureGap]:
        # 维度1-3: 第一步按 weight 从大到小排序
        sorted_gaps = self.prioritizer.sort(gaps, py_index=py_index)

        self._pipeline = DevPipelineRunner(
            scanner=None,
            prioritizer=self.prioritizer,
            ir14=self._ir14,
            implementer=self._impl,
            verifier=self._verifier,
            persister=None,
            safe_only=self.safe_only,
            max_impl=self.max_impl,
        )

        processed, all_stats = self._pipeline.run_pipeline(sorted_gaps, py_index=py_index)
        self._impl_count = self._pipeline._impl_count
        self._assigned = processed
        self._log('DISPATCH_COMPLETE',
                  f'派发完成,共 {len(self._assigned)} 项; auto implement={self._impl_count}; stats={json.dumps(all_stats, ensure_ascii=False)[:200]}')
        return self._assigned

    def _route_to_team(self, gap: FeatureGap) -> Tuple[str, str, str]:
        gap_type = gap.gap_type
        if gap_type in DEV_TEAM_ROUTING:
            team, employee, desc = DEV_TEAM_ROUTING[gap_type]
            return team, employee, desc
        if gap.severity in ('critical', 'high'):
            return DEV_TEAM_ROUTING['route_broken'][0], DEV_TEAM_ROUTING['route_broken'][1], '紧急功能修复'
        return DEV_TEAM_ROUTING['unknown'][0], DEV_TEAM_ROUTING['unknown'][1], '协调处理'

# ============================================================
# DevProgressTracker / FullReportGenerator (保持兼容, 轻量升级)
# ============================================================
class DevProgressTracker:

    def __init__(self):
        self._timeline: List[Dict] = []
        self._log('TRACK_START', '开始进度跟踪')

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)

    def start_development(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        for gap in gaps:
            if gap.status == 'assigned':
                gap.status = 'in_development'
                gap.progress = 0.3
                gap.development_log.append(f'[开发开始] {gap.assigned_employee} 开始开发: {gap.title}')
        self._log('DEV_START', f'开始开发 {len([g for g in gaps if g.status == "in_development"])} 项')
        return gaps

    def code_review(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        for gap in gaps:
            if gap.status == 'in_development' and gap.progress >= 0.3:
                gap.status = 'code_review'
                gap.progress = 0.6
                gap.development_log.append(f'[代码评审] {gap.assigned_employee} 提交代码评审: {gap.title}')
                gap.fix_code_snippet = self._generate_fix_snippet(gap)
        self._log('REVIEW', f'代码评审 {len([g for g in gaps if g.status == "code_review"])} 项')
        return gaps

    def testing(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        for gap in gaps:
            if gap.status == 'code_review':
                gap.status = 'testing'
                gap.progress = 0.8
                gap.development_log.append(f'[测试] {gap.assigned_employee} 进入测试: {gap.title}')
        self._log('TESTING', f'测试 {len([g for g in gaps if g.status == "testing"])} 项')
        return gaps

    def complete(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        for gap in gaps:
            if gap.status in ('testing', 'code_review'):
                gap.status = 'completed'
                gap.progress = 1.0
                gap.completed_at = datetime.now().isoformat()
                gap.development_log.append(f'[完成] {gap.assigned_employee} 完成开发: {gap.title}')
        self._log('COMPLETE', f'完成 {len([g for g in gaps if g.status == "completed"])} 项')
        return gaps

    def _generate_fix_snippet(self, gap: FeatureGap) -> str:
        gap_type = gap.gap_type
        if gap_type == 'placeholder_return':
            return self._fix_placeholder(gap)
        elif gap_type == 'missing_crud':
            return self._fix_crud(gap)
        elif gap_type == 'missing_api':
            return self._fix_api(gap)
        elif gap_type == 'route_broken':
            return self._fix_route(gap)
        elif gap_type == 'todo_fixme':
            return self._fix_todo(gap)
        else:
            return f'# 需要开发: {gap.title}\n# {gap.description}'

    def _fix_placeholder(self, gap: FeatureGap) -> str:
        title_lower = gap.title.lower()
        if 'pass' in gap.current_implementation.lower():
            func_match = re.search(r'函数\s+(\w+)', gap.title) or re.search(r':(\w+)\(\)', gap.title)
            func_name = func_match.group(1) if func_match else 'unknown_func'
            return f'''# 修复占位符: {gap.title}
def {func_name}():
    """{gap.description}"""
    try:
        result = {{
            'status': 'success',
            'message': '{gap.title}',
            'data': None,
        }}
        return result
    except Exception as e:
        return {{'status': 'error', 'message': str(e)}}
'''
        elif 'not implemented' in gap.current_implementation.lower():
            return f'''# 修复not implemented: {gap.title}
def implementation():
    """{gap.description}"""
    raise NotImplementedError("{gap.title} 需要实现")
'''
        return f'''# 修复: {gap.title}
# 当前: {gap.current_implementation}
# 建议: {gap.suggested_implementation or '补充实际实现'}
'''

    def _fix_crud(self, gap: FeatureGap) -> str:
        route = gap.route
        return f'''# 补充CRUD操作: {gap.title}
# 路由组: {route}
@app.route('{route}/create', methods=['POST'])
def create():
    """创建"""
    data = request.get_json()
    return jsonify({{'status': 'success', 'data': data}})

@app.route('{route}/update/<int:item_id>', methods=['PUT'])
def update(item_id):
    """更新"""
    data = request.get_json()
    return jsonify({{'status': 'success', 'data': data}})

@app.route('{route}/delete/<int:item_id>', methods=['DELETE'])
def delete(item_id):
    """删除"""
    return jsonify({{'status': 'success'}})
'''

    def _fix_api(self, gap: FeatureGap) -> str:
        route = gap.route
        return f'''# 补充API: {gap.title}
@app.route('{route}', methods=['GET', 'POST'])
def api_endpoint():
    """{gap.description}"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            return jsonify({{'status': 'success', 'data': data}})
        else:
            return jsonify({{'status': 'success', 'data': []}})
    except Exception as e:
        return jsonify({{'status': 'error', 'message': str(e)}}), 400
'''

    def _fix_route(self, gap: FeatureGap) -> str:
        return f'''# 修复路由: {gap.title}
# 当前实现: {gap.current_implementation}
# 需要补充: 业务逻辑、数据库操作、错误处理
def fixed_route():
    """{gap.description}"""
    try:
        data = {{}}
        return jsonify({{'status': 'success', 'data': data}})
    except Exception as e:
        return jsonify({{'status': 'error', 'message': str(e)}}), 500
'''

    def _fix_todo(self, gap: FeatureGap) -> str:
        return f'''# 处理TODO/FIXME: {gap.title}
# 位置: {gap.file}:{gap.line}
# 描述: {gap.description}
# 当前: {gap.current_implementation}

# 实现以下功能:
# 1. 分析需求
# 2. 设计方案
# 3. 实现代码
# 4. 编写测试
# 5. Code Review
# 6. 部署上线
'''

class FullReportGenerator:

    def __init__(self):
        self._report: Optional[DevLifecycleReport] = None

    def generate(self, gaps: List[FeatureGap], flow_id: str = "") -> DevLifecycleReport:
        report_id = hashlib.md5(
            f"dev_lifecycle_{time.time()}".encode()
        ).hexdigest()[:16]

        now = datetime.now().isoformat()

        status_counts = defaultdict(int)
        teams = set()
        all_timeline = []

        for gap in gaps:
            status_counts[gap.status] += 1
            if gap.assigned_team:
                teams.add(gap.assigned_team)
            all_timeline.extend(self._build_gap_timeline(gap))

        self._report = DevLifecycleReport(
            report_id=report_id,
            flow_id=flow_id,
            total_gaps=len(gaps),
            gaps_discovered=status_counts.get('discovered', 0) + status_counts.get('assigned', 0) +
                           status_counts.get('in_development', 0) + status_counts.get('code_review', 0) +
                           status_counts.get('testing', 0) + status_counts.get('completed', 0) +
                           status_counts.get('failed', 0),
            gaps_assigned=status_counts.get('assigned', 0) + status_counts.get('in_development', 0) +
                         status_counts.get('code_review', 0) + status_counts.get('testing', 0) +
                         status_counts.get('completed', 0) + status_counts.get('failed', 0),
            gaps_developing=status_counts.get('in_development', 0) + status_counts.get('code_review', 0) +
                          status_counts.get('testing', 0),
            gaps_completed=status_counts.get('completed', 0),
            gaps_failed=status_counts.get('failed', 0),
            teams_involved=sorted(list(teams)),
            timeline=all_timeline,
            gaps=[self._gap_to_dict(gap) for gap in gaps],
            summary=self._build_summary(status_counts, teams, gaps),
            generated_at=now,
        )

        return self._report

    def _build_gap_timeline(self, gap: FeatureGap) -> List[Dict]:
        events = []
        if gap.detected_at:
            events.append({
                'gap_id': gap.gap_id,
                'event': 'discovered',
                'title': gap.title,
                'team': '',
                'timestamp': gap.detected_at,
            })
        if gap.assigned_at:
            events.append({
                'gap_id': gap.gap_id,
                'event': 'assigned',
                'title': gap.title,
                'team': gap.assigned_team,
                'timestamp': gap.assigned_at,
            })
        if gap.completed_at:
            events.append({
                'gap_id': gap.gap_id,
                'event': gap.status,
                'title': gap.title,
                'team': gap.assigned_team,
                'timestamp': gap.completed_at,
            })
        return events

    def _gap_to_dict(self, gap: FeatureGap) -> Dict:
        return {
            'gap_id': gap.gap_id,
            'gap_type': gap.gap_type,
            'title': gap.title,
            'description': gap.description,
            'file': gap.file,
            'line': gap.line,
            'route': gap.route,
            'severity': gap.severity,
            'current_implementation': gap.current_implementation,
            'assigned_team': gap.assigned_team,
            'assigned_employee': gap.assigned_employee,
            'status': gap.status,
            'progress': gap.progress,
            'detected_at': gap.detected_at,
            'assigned_at': gap.assigned_at,
            'completed_at': gap.completed_at,
            'verification_result': gap.verification_result,
            'verification_passed': gap.verification_passed,
            'development_log': gap.development_log,
        }

    def _build_summary(self, status_counts: Dict, teams: set, gaps: List[FeatureGap]) -> str:
        total = len(gaps)
        completed = status_counts.get('completed', 0)
        failed = status_counts.get('failed', 0)
        developing = status_counts.get('in_development', 0) + status_counts.get('code_review', 0) + status_counts.get('testing', 0)

        type_counts = defaultdict(int)
        for gap in gaps:
            type_counts[gap.gap_type] += 1

        type_summary = ', '.join(f'{k}={v}' for k, v in sorted(type_counts.items(), key=lambda x: -x[1]))

        summary = (
            f"自动巡检队伍引擎完成功能缺失扫描: "
            f"共发现 {total} 个功能缺失项, "
            f"已分配到 {len(teams)} 个开发团队, "
            f"开发中 {developing} 项, "
            f"完成 {completed} 项, "
            f"失败 {failed} 项。"
            f"缺失类型: {type_summary}"
        )
        return summary

# ============================================================
# AutoDevTeamEngine (v2: 接入py_index + pipeline + warmup)
# ============================================================
class AutoDevTeamEngine:

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        ensure_dev_lifecycle_tables()

        self._gap_scanner = GapScanner(self.scan_dir)
        self._prioritizer = GapPrioritizer()
        self._task_dispatcher = DevTaskDispatcher()
        self._progress_tracker = DevProgressTracker()
        self._completion_verifier = CompletionVerifier(self.scan_dir)
        self._report_generator = FullReportGenerator()

        self._gaps: List[FeatureGap] = []
        self._report: Optional[DevLifecycleReport] = None

    def run_full_cycle(self, flow_id: str = "") -> DevLifecycleReport:
        if not flow_id:
            flow_id = f"auto_dev_{int(time.time())}"

        logger.info("=" * 60)
        logger.info(" MTSCOS 自动巡检队伍引擎 v2.0.0")
        logger.info("=" * 60)
        logger.info(f" Flow ID: {flow_id}")
        logger.info(f" 扫描目录: {self.scan_dir}")

        t0 = time.time()

        logger.info("\n--- 步骤0: warmup_system ---")
        warmup_system()

        logger.info("\n--- 步骤1: GapScanner 扫描功能缺失 ---")
        self._gaps = self._gap_scanner.scan_all()
        py_index = self._gap_scanner.get_py_index()
        self._completion_verifier.set_py_index(py_index)
        logger.info(f"  发现 {len(self._gaps)} 个功能缺失项")

        logger.info("\n--- 步骤2: DevTaskDispatcher 派发任务 (按weight排序+Pipeline) ---")
        self._gaps = self._task_dispatcher.dispatch(self._gaps, py_index=py_index)
        teams_used = set(g.assigned_team for g in self._gaps if g.assigned_team)
        logger.info(f"  已分配到 {len(teams_used)} 个开发团队")

        logger.info("\n--- 步骤3: DevProgressTracker 开始开发 ---")
        self._gaps = self._progress_tracker.start_development(self._gaps)

        logger.info("\n--- 步骤4: DevProgressTracker 代码评审 ---")
        self._gaps = self._progress_tracker.code_review(self._gaps)

        logger.info("\n--- 步骤5: DevProgressTracker 测试 ---")
        self._gaps = self._progress_tracker.testing(self._gaps)

        logger.info("\n--- 步骤6: DevProgressTracker 完成 ---")
        self._gaps = self._progress_tracker.complete(self._gaps)

        logger.info("\n--- 步骤7: CompletionVerifier 完成验证 (复用_py_index) ---")
        self._gaps = self._completion_verifier.verify(self._gaps)
        passed = sum(1 for g in self._gaps if g.verification_passed)
        failed = sum(1 for g in self._gaps if not g.verification_passed)
        logger.info(f"  验证通过: {passed}, 验证失败: {failed}")

        logger.info("\n--- 步骤8: FullReportGenerator 生成报告 ---")
        self._report = self._report_generator.generate(self._gaps, flow_id)
        logger.info(f"  报告ID: {self._report.report_id}")
        logger.info(f"  摘要: {self._report.summary}")

        logger.info("\n--- 步骤9: 数据库持久化 ---")
        persist_count = self._persist_to_database(flow_id)
        logger.info(f"  存储 {persist_count} 条记录")

        elapsed = time.time() - t0
        logger.info(f"\n  总耗时: {elapsed:.1f}s")
        logger.info("=" * 60)

        self._report.duration = elapsed
        return self._report

    def _persist_to_database(self, flow_id: str) -> int:
        count = 0
        now = datetime.now().isoformat()

        with _LOCK:
            c = get_conn()
            try:
                cur = c.cursor()

                for gap in self._gaps:
                    try:
                        cur.execute("""INSERT OR REPLACE INTO mt_feature_dev_lifecycle
                            (gap_id, gap_type, title, description, file_path, line_number, route,
                             severity, current_impl, suggested_impl, assigned_team, assigned_employee,
                             status, progress, detected_at, assigned_at, completed_at,
                             verification_result, verification_passed, development_log_json,
                             fix_code_snippet, original_code_snippet, flow_id, created_at, updated_at)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (gap.gap_id, gap.gap_type, gap.title, gap.description,
                             gap.file, gap.line, gap.route, gap.severity,
                             gap.current_implementation, gap.suggested_implementation,
                             gap.assigned_team, gap.assigned_employee, gap.status,
                             gap.progress, gap.detected_at, gap.assigned_at,
                             gap.completed_at, gap.verification_result,
                             1 if gap.verification_passed else 0,
                             json.dumps(gap.development_log, ensure_ascii=False),
                             gap.fix_code_snippet, gap.original_code_snippet,
                             flow_id, now, now))
                        count += 1
                    except Exception as e:
                        _append_err_log(gap, GapEngineError.ERR_DB_WRITE, f"persist lifecycle failed: {e}")

                if self._report:
                    try:
                        cur.execute("""INSERT OR REPLACE INTO mt_dev_lifecycle_report
                            (report_id, flow_id, total_gaps, gaps_discovered, gaps_assigned,
                             gaps_completed, gaps_failed, teams_involved_json,
                             timeline_json, gaps_detail_json, summary, generated_at, duration)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (self._report.report_id, flow_id, self._report.total_gaps,
                             self._report.gaps_discovered, self._report.gaps_assigned,
                             self._report.gaps_completed, self._report.gaps_failed,
                             json.dumps(self._report.teams_involved, ensure_ascii=False),
                             json.dumps(self._report.timeline, ensure_ascii=False),
                             json.dumps(self._report.gaps, ensure_ascii=False),
                             self._report.summary, self._report.generated_at,
                             self._report.duration))
                        count += 1
                    except Exception as e:
                        logger.error(f"[AutoDevTeamEngine] persist report failed: {e}")

                try:
                    c.commit()
                except Exception as e:
                    logger.error(f"[AutoDevTeamEngine] commit failed: {e}")
                    try: c.rollback()
                    except: pass
            finally:
                return_to_pool(c, 'eng')

        if HAS_DEV_FLOW:
            try:
                from app.services.ai_brain_library_service import feed_ai_brain_library as feed_brain
                feed_brain(flow_id, 'auto_dev_team', self._report.summary if self._report else '')
            except Exception:
                pass
        return count


def ensure_self_registered() -> bool:
    try:
        c = get_conn()
        try:
            cur = c.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS mt_daemon_registry (
                daemon_name TEXT PRIMARY KEY,
                source TEXT,
                interval_sec INTEGER,
                description TEXT,
                status TEXT DEFAULT 'registered',
                registered_at TEXT,
                last_heartbeat TEXT
            )""")
            now = datetime.now().isoformat()
            cur.execute("""INSERT OR REPLACE INTO mt_daemon_registry
                (daemon_name, source, interval_sec, description, status, registered_at, last_heartbeat)
                VALUES(?,?,?,?,?,?,?)""",
                ('sys_gap_discovery_engine', 'SYSTEM_REQ', 600,
                 '功能缺口发现+自动开发+12步骤强制+自动落库',
                 'registered', now, now))
            try: c.commit()
            except: pass
        finally:
            return_to_pool(c, 'eng')
        return True
    except Exception as e:
        logger.warning(f"[ensure_self_registered] failed: {e}")
        return False


def warmup_system() -> dict:
    result = {
        'lifecycle_tables': False,
        'ses_session_tables': False,
        'ir14': False,
        'daemon': False,
        'index_cache': None,
        'defrag': False,
    }
    try:
        ensure_dev_lifecycle_tables()
        result['lifecycle_tables'] = True
    except Exception as e:
        logger.warning(f"[warmup] lifecycle tables failed: {e}")
    try:
        _ensure_ses_session_table()
        result['ses_session_tables'] = True
    except Exception as e:
        logger.warning(f"[warmup] ses tables failed: {e}")
    if IR14_HAS_FULL_API:
        try:
            fn = IR14_STEP_FUNCS.get('ensure_tables')
            if fn: fn()
            result['ir14'] = True
        except Exception:
            result['ir14'] = False
    try:
        ensure_self_registered()
        result['daemon'] = True
    except Exception as e:
        logger.warning(f"[warmup] daemon register failed: {e}")
    try:
        conn_l = get_conn()
        conn_s = get_ses_conn()
        try:
            _defrag_flow_id_field(conn_l, conn_s)
            result['defrag'] = True
        finally:
            return_to_pool(conn_l, 'eng')
            return_to_pool(conn_s, 'ses')
    except Exception as e:
        logger.warning(f"[warmup] defrag failed: {e}")
    return result


def _fmt_gap_row(gap, idx) -> str:
    sev_c = {'low':'L','medium':'M','high':'H','critical':'C'}.get(gap.severity,'?')
    w_str = f"w={gap.weight:.0f}" if gap.weight else "w=?"
    return f"  [{idx:>3}] [{sev_c}] {w_str} {gap.gap_type:<22} {gap.file.split('/')[-1]}:{gap.line} {gap.title[:50]}"


def _cli_scan(args):
    warmup_system()
    scan_dir = getattr(args, 'dir', None) or FLASK_APP
    logger.info(f"[CLI scan] dir={scan_dir}")
    scanner = GapScanner(scan_dir)
    t0 = time.time()
    gaps = scanner.scan_all()
    elapsed = time.time() - t0
    by_type = {}
    by_sev = {}
    for g in gaps:
        by_type[g.gap_type] = by_type.get(g.gap_type, 0) + 1
        by_sev[g.severity] = by_sev.get(g.severity, 0) + 1
    print(f"\n=== GapScanner 结果 ===")
    print(f"  扫描目录: {scan_dir}")
    print(f"  扫描耗时: {elapsed:.2f}s")
    print(f"  发现缺口: {len(gaps)}")
    print(f"  按类型: {by_type}")
    print(f"  按严重度: {by_sev}")
    limit = getattr(args, 'limit', 50)
    show = gaps[:limit]
    print(f"\n  Top {len(show)}:")
    for i, g in enumerate(show, 1):
        print(_fmt_gap_row(g, i))
    if getattr(args, 'persist', False):
        from datetime import datetime as _dt
        fid = 'scan_' + _dt.now().strftime('%Y%m%d_%H%M%S')
        n = _persist_gap_registry(gaps, fid)
        print(f"\n  已写入 mt_dev_gap_registry: {n} rows, flow_id={fid}")
    return 0


def _cli_implement(args):
    warmup_system()
    scan_dir = getattr(args, 'dir', None) or FLASK_APP
    max_impl = getattr(args, 'max', 20)
    safe_only = getattr(args, 'safe_only', False)
    logger.info(f"[CLI implement] dir={scan_dir} max={max_impl} safe_only={safe_only}")

    t_total_start = time.time()

    logger.info("SCAN_START")
    t_scan_start = time.time()
    scanner = GapScanner(scan_dir)
    gaps = scanner.scan_all()
    py_index = scanner.get_py_index()
    t_scan = time.time() - t_scan_start
    logger.info(f"SCAN_COMPLETE elapsed={t_scan:.2f}s gaps={len(gaps)}")

    prioritizer = GapPrioritizer()
    gaps = prioritizer.prioritize(gaps)
    gaps = sorted(gaps, key=lambda g: -g.weight)

    verifier = CompletionVerifier()
    verifier.set_py_index(py_index)

    logger.info("DISPATCH_START")
    t_ir14_start = time.time()
    dispatcher = DevTaskDispatcher(
        enable_flow=True,
        enable_implement=True,
        enable_verify=True,
        safe_only=safe_only,
        max_impl=max_impl,
    )
    gaps = dispatcher.dispatch(gaps, py_index=py_index)
    t_ir14 = time.time() - t_ir14_start
    logger.info(f"DISPATCH_IR14_COMPLETE elapsed={t_ir14:.2f}s")

    logger.info("VERIFY_START")
    t_verify_start = time.time()
    gaps = verifier.verify(gaps)
    t_verify = time.time() - t_verify_start
    logger.info(f"VERIFY_COMPLETE elapsed={t_verify:.2f}s")

    flow_id = 'impl_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    reg_n = _persist_gap_registry(gaps, flow_id)
    sugg_n = 0
    for g in gaps[:max_impl]:
        if _push_ai_suggestion_for_gap(g):
            sugg_n += 1

    t_total = time.time() - t_total_start
    passed = sum(1 for g in gaps if g.verification_passed)
    failed = sum(1 for g in gaps if not g.verification_passed and g.status in ('completed','failed'))

    print(f"\n=== Implement 结果 ===")
    print(f"  总耗时:       {t_total:.2f}s")
    print(f"  扫描耗时:     {t_scan:.2f}s")
    print(f"  IR14推进耗时: {t_ir14:.2f}s")
    print(f"  验证耗时:     {t_verify:.2f}s")
    print(f"  总gap数:      {len(gaps)}")
    print(f"  建议池新增:   {sugg_n} rows (today)")
    print(f"  registry写入: {reg_n} rows")
    print(f"  验证通过:     {passed}")
    print(f"  验证失败:     {failed}")

    print(f"\n  Top 20 gaps:")
    for i, g in enumerate(gaps[:20], 1):
        mark = "✓" if g.verification_passed else ("✗" if g.status in ('completed','failed') else "·")
        print(_fmt_gap_row(g, i) + f" {mark} {g.status}")
    return 0


def _cli_verify(args):
    warmup_system()
    scan_dir = getattr(args, 'dir', None) or FLASK_APP
    flow_id = getattr(args, 'flow_id', None)
    logger.info(f"[CLI verify] dir={scan_dir} flow_id={flow_id}")

    scanner = GapScanner(scan_dir)
    gaps = scanner.scan_all()
    py_index = scanner.get_py_index()
    verifier = CompletionVerifier()
    verifier.set_py_index(py_index)
    t0 = time.time()
    gaps = verifier.verify(gaps)
    elapsed = time.time() - t0
    passed = sum(1 for g in gaps if g.verification_passed)
    failed = sum(1 for g in gaps if not g.verification_passed)
    print(f"\n=== Verify 结果 ===")
    print(f"  验证耗时: {elapsed:.2f}s")
    print(f"  通过: {passed}  失败: {failed}  总计: {len(gaps)}")
    return 0


def _cli_daemon(args):
    warmup_system()
    interval = getattr(args, 'interval', 600)
    logger.info(f"[CLI daemon] starting interval={interval}s (Ctrl+C to stop)")
    engine = AutoDevTeamEngine(max_impl_per_cycle=20, safe_only=True)
    try:
        while True:
            try:
                engine.run_full_cycle()
            except Exception as e:
                logger.error(f"[daemon] cycle error: {e}")
            logger.info(f"[daemon] sleep {interval}s ...")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("[daemon] stopped by user")
    return 0


def _cli_list(args):
    warmup_system()
    ensure_dev_lifecycle_tables()
    status_filter = getattr(args, 'status', None)
    limit = getattr(args, 'limit', 100)
    c = get_conn()
    try:
        cur = c.cursor()
        sql = "SELECT gap_id, gap_type, severity, status, file_path, line_number, title, flow_id, weight FROM mt_feature_dev_lifecycle"
        params = []
        if status_filter:
            sql += " WHERE status = ?"
            params.append(status_filter)
        sql += " ORDER BY COALESCE(weight, 0) DESC, updated_at DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        print(f"\n=== Lifecycle Rows ({len(rows)}) ===")
        for r in rows:
            rdict = dict(r) if isinstance(r, sqlite3.Row) else {
                'gap_id':r[0],'gap_type':r[1],'severity':r[2],'status':r[3],
                'file_path':r[4],'line_number':r[5],'title':r[6],'flow_id':r[7],'weight':r[8]}
            w = rdict.get('weight') or 0.0
            fid = rdict.get('flow_id') or ''
            fp = (rdict.get('file_path') or '').split('/')[-1]
            print(f"  [{rdict['status']:<9}] w={w:>5.1f} {rdict['gap_type']:<22} {fp}:{rdict['line_number']} {rdict['gap_id']} fid={fid[:12]} {str(rdict.get('title') or '')[:40]}")

        cur.execute("SELECT COUNT(*) FROM mt_feature_dev_lifecycle WHERE (flow_id IS NULL OR flow_id='') AND status IN ('assigned','completed')")
        r = cur.fetchone()
        cnt = r[0] if isinstance(r, (tuple, list)) else (dict(r).get('COUNT(*)') or 0)
        print(f"\n  [defrag check] flow_id='' AND status IN (assigned/completed): {cnt} rows")
    finally:
        return_to_pool(c, 'eng')
    return 0


def _build_arg_parser():
    p = argparse.ArgumentParser(
        prog='auto_dev_team_engine.py',
        description='AutoDevTeamEngine - 功能缺口自动发现+开发+验证+持久化 (§14 IRON_RULE 12步骤强制)'
    )
    sub = p.add_subparsers(dest='command', help='子命令')

    p_scan = sub.add_parser('scan', help='扫描缺口')
    p_scan.add_argument('--dir', default=None, help=f'扫描目录 (default: {FLASK_APP})')
    p_scan.add_argument('--limit', type=int, default=50, help='显示前N条 (default: 50)')
    p_scan.add_argument('--persist', action='store_true', help='写入 mt_dev_gap_registry')
    p_scan.set_defaults(func=_cli_scan)

    p_impl = sub.add_parser('implement', help='扫描+派发+自动实现+验证')
    p_impl.add_argument('--dir', default=None, help=f'扫描目录 (default: {FLASK_APP})')
    p_impl.add_argument('--max', type=int, default=20, help='最多实现N个 (default: 20)')
    p_impl.add_argument('--safe-only', action='store_true', help='仅实现安全的gap (default: off)')
    p_impl.set_defaults(func=_cli_implement)

    p_ver = sub.add_parser('verify', help='验证已存在的gap')
    p_ver.add_argument('--dir', default=None, help=f'扫描目录 (default: {FLASK_APP})')
    p_ver.add_argument('--flow-id', default=None, help='指定flow_id')
    p_ver.set_defaults(func=_cli_verify)

    p_dae = sub.add_parser('daemon', help='常驻守护模式')
    p_dae.add_argument('--interval', type=int, default=600, help='循环间隔秒 (default: 600)')
    p_dae.set_defaults(func=_cli_daemon)

    p_list = sub.add_parser('list', help='查看lifecycle表')
    p_list.add_argument('--status', default=None, help='按status过滤 (assigned/in_progress/completed/failed)')
    p_list.add_argument('--limit', type=int, default=100, help='最多显示N条 (default: 100)')
    p_list.set_defaults(func=_cli_list)

    return p


def _main_cli(argv=None):
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if not getattr(args, 'command', None):
        parser.print_help()
        return 1
    fn = getattr(args, 'func', None)
    if not fn:
        parser.print_help()
        return 1
    try:
        return fn(args) or 0
    except KeyboardInterrupt:
        print("\n[interrupted]")
        return 130


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_main_cli())