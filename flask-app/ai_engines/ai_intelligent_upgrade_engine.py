#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能化AI驱动全系统升级引擎(骨架优先实现)
=========================================
flow_id: flow_intelligent_ai_upgrade_20260817_001
§14 STEP_7_EXECUTE 下场实施

6大方向骨架表 + 基础CRUD逻辑:
  方向1: mt_daemon_registry        (daemon注册表 + 状态机)
  方向2: mt_eigenflux_expert_registry (专家注册表 + 动态权重)
  方向3: mt_ai_intervene_audit     (AI介入审计 + 4类节点)
  方向4: mt_repair_strategy_lib    (修复策略库 + 匹配引擎)
  方向5: mt_ai_suggestion_pool     (AI建议池 + 评估矩阵)
  方向6: mt_version_registry       (5级版本注册表)

遵循硬约束:
  - 数据库唯一数据源(app.db)
  - 权限装饰器@system_container(路由层)
  - 状态机5态(IDLE/RUNNING/PAUSED/FAILED/STOPPED)
  - 全链路追溯ID
"""
import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DB = os.path.join(ROOT, "app.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now().isoformat()


# ============================================================
# 6大方向骨架表建表(幂等)
# ============================================================
def ensure_upgrade_tables() -> Dict[str, bool]:
    """创建6大方向骨架表,返回各表创建结果"""
    results = {}
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()

        # 方向1: mt_daemon_registry (daemon注册表 + 状态机5态)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_daemon_registry (
            daemon_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            daemon_name      TEXT NOT NULL UNIQUE,
            daemon_duty      TEXT,
            dependencies     TEXT,
            priority         INTEGER DEFAULT 5,
            inspect_cycle    TEXT,
            current_state    TEXT NOT NULL DEFAULT 'IDLE',
            registered_at    TEXT NOT NULL,
            updated_at       TEXT NOT NULL,
            CHECK(current_state IN ('IDLE','RUNNING','PAUSED','FAILED','STOPPED'))
        )""")
        results["mt_daemon_registry"] = True

        # 方向2: mt_eigenflux_expert_registry (专家注册表 + 动态权重)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_eigenflux_expert_registry (
            expert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            expert_name      TEXT NOT NULL UNIQUE,
            expert_ai_id     TEXT,
            domain           TEXT NOT NULL,
            weight           REAL DEFAULT 1.0,
            tenure_status    TEXT DEFAULT 'ACTIVE',
            accuracy_rate    REAL DEFAULT 0.0,
            registered_at    TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        )""")
        results["mt_eigenflux_expert_registry"] = True

        # 方向3: mt_ai_intervene_audit (AI介入审计,独立表融入异议2隔离)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_intervene_audit (
            audit_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id         TEXT NOT NULL,
            node_type        TEXT NOT NULL,
            change_request   TEXT NOT NULL,
            audit_mode       TEXT DEFAULT 'READ_ONLY',
            intervene_decision TEXT,
            vote_result      TEXT,
            operator         TEXT,
            created_at       TEXT NOT NULL,
            CHECK(node_type IN ('ROUTE','PERMISSION','PARAM','DATABASE')),
            CHECK(audit_mode IN ('READ_ONLY','INTERVENE_VOTE'))
        )""")
        results["mt_ai_intervene_audit"] = True

        # 方向4: mt_repair_strategy_lib (修复策略库)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_repair_strategy_lib (
            strategy_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            anomaly_type     TEXT NOT NULL,
            strategy_class   TEXT NOT NULL,
            strategy_content TEXT NOT NULL,
            match_feature    TEXT,
            success_rate     REAL DEFAULT 0.0,
            is_auto          INTEGER DEFAULT 1,
            created_at       TEXT NOT NULL,
            CHECK(strategy_class IN ('CONFIG','CODE','SERVICE','DATA'))
        )""")
        results["mt_repair_strategy_lib"] = True

        # 方向5: mt_ai_suggestion_pool (AI建议池)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_suggestion_pool (
            suggestion_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            source           TEXT NOT NULL,
            direction        TEXT,
            suggestion       TEXT NOT NULL,
            feasibility      REAL DEFAULT 0.0,
            value_score      REAL DEFAULT 0.0,
            cost_score       REAL DEFAULT 0.0,
            risk_score       REAL DEFAULT 0.0,
            priority         INTEGER DEFAULT 5,
            status           TEXT DEFAULT 'PENDING',
            created_at       TEXT NOT NULL,
            CHECK(source IN ('DAEMON_PATROL','ANOMALY','LEARNING','EXPERT'))
        )""")
        results["mt_ai_suggestion_pool"] = True

        # 方向6: mt_version_registry (5级版本注册表)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_version_registry (
            version_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            version_level    TEXT NOT NULL,
            version_number   TEXT NOT NULL UNIQUE,
            change_type      TEXT NOT NULL,
            bump_reason      TEXT,
            committee_approved INTEGER DEFAULT 0,
            arch_review_passed INTEGER DEFAULT 0,
            git_tag          TEXT,
            created_at       TEXT NOT NULL,
            CHECK(version_level IN ('L1_MAIN','L2_MINOR','L3_FIX','L4_PATCH','L5_BUILD'))
        )""")
        results["mt_version_registry"] = True

        conn.commit()
        conn.close()
    return results


# ============================================================
# 方向1: 调度中枢 - daemon注册/状态机
# ============================================================
DAEMON_STATE_MACHINE = {
    "IDLE":     ["RUNNING", "STOPPED"],
    "RUNNING":  ["PAUSED", "FAILED", "STOPPED"],
    "PAUSED":   ["RUNNING", "STOPPED"],
    "FAILED":   ["RUNNING", "STOPPED"],
    "STOPPED":  ["IDLE", "RUNNING"],
}


def register_daemon(name: str, duty: str, dependencies: str = "",
                    priority: int = 5, inspect_cycle: str = "60s") -> int:
    """注册daemon到mt_daemon_registry"""
    now = _now()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO mt_daemon_registry
            (daemon_name, daemon_duty, dependencies, priority, inspect_cycle, current_state, registered_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
                  (name, duty, dependencies, priority, inspect_cycle, "IDLE", now, now))
        conn.commit()
        rid = c.execute("SELECT daemon_id FROM mt_daemon_registry WHERE daemon_name=?", (name,)).fetchone()[0]
        conn.close()
    return rid


def daemon_transition(daemon_name: str, to_state: str) -> bool:
    """daemon状态机转移(严格按边)"""
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        r = c.execute("SELECT current_state FROM mt_daemon_registry WHERE daemon_name=?", (daemon_name,)).fetchone()
        if not r:
            conn.close(); return False
        from_state = r["current_state"]
        allowed = DAEMON_STATE_MACHINE.get(from_state, [])
        if to_state not in allowed:
            conn.close()
            raise RuntimeError(f"[DAEMON-VIOLATION] 非法状态转移: {daemon_name} {from_state}->{to_state} (允许={allowed})")
        c.execute("UPDATE mt_daemon_registry SET current_state=?, updated_at=? WHERE daemon_name=?",
                  (to_state, _now(), daemon_name))
        conn.commit(); conn.close()
    return True


# ============================================================
# 方向2: EigenFlux专家组扩建 - 注册/权重/轮值
# ============================================================
EXPERT_DOMAINS = ["SECURITY", "PERFORMANCE", "ARCHITECTURE", "DATA", "AI", "COMPLIANCE"]


def register_expert(name: str, ai_id: str, domain: str, weight: float = 1.0) -> int:
    """注册专家到mt_eigenflux_expert_registry"""
    now = _now()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO mt_eigenflux_expert_registry
            (expert_name, expert_ai_id, domain, weight, tenure_status, accuracy_rate, registered_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
                  (name, ai_id, domain, weight, "ACTIVE", 0.0, now, now))
        conn.commit()
        rid = c.execute("SELECT expert_id FROM mt_eigenflux_expert_registry WHERE expert_name=?", (name,)).fetchone()[0]
        conn.close()
    return rid


def compute_dynamic_weight(expert_id: int) -> float:
    """动态权重计算(专业匹配度+历史表决准确率,融入张晓峰综1)"""
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        r = c.execute("SELECT weight, accuracy_rate FROM mt_eigenflux_expert_registry WHERE expert_id=?", (expert_id,)).fetchone()
        conn.close()
        if not r:
            return 0.0
        # 动态权重 = 基础权重*0.5 + 准确率*0.5
        return round(r["weight"] * 0.5 + r["accuracy_rate"] * 0.5, 4)


# ============================================================
# 方向3: AI介入决策引擎 - 只读审计/4类节点/追溯
# ============================================================
def log_intervene_audit(trace_id: str, node_type: str, change_request: str,
                        audit_mode: str = "READ_ONLY", operator: str = "AI") -> int:
    """记录AI介入审计(只读观察期模式,融入张晓峰综2)"""
    now = _now()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""INSERT INTO mt_ai_intervene_audit
            (trace_id, node_type, change_request, audit_mode, operator, created_at)
            VALUES(?,?,?,?,?,?)""",
                  (trace_id, node_type, change_request, audit_mode, operator, now))
        conn.commit()
        aid = c.execute("SELECT audit_id FROM mt_ai_intervene_audit WHERE trace_id=? ORDER BY audit_id DESC LIMIT 1",
                        (trace_id,)).fetchone()[0]
        conn.close()
    return aid


# ============================================================
# 方向4: 巡检闭环 - 修复策略库/匹配
# ============================================================
def add_repair_strategy(anomaly_type: str, strategy_class: str, content: str,
                        match_feature: str = "", is_auto: int = 1) -> int:
    """添加修复策略到mt_repair_strategy_lib"""
    now = _now()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""INSERT INTO mt_repair_strategy_lib
            (anomaly_type, strategy_class, strategy_content, match_feature, is_auto, created_at)
            VALUES(?,?,?,?,?,?)""",
                  (anomaly_type, strategy_class, content, match_feature, is_auto, now))
        conn.commit()
        sid = c.lastrowid
        conn.close()
    return sid


def match_repair_strategy(anomaly_type: str) -> List[Dict]:
    """匹配修复策略(异常特征→策略)"""
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        rows = c.execute("""SELECT * FROM mt_repair_strategy_lib
            WHERE anomaly_type=? ORDER BY success_rate DESC""", (anomaly_type,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 方向5: 系统功能拓展 - AI建议池/评估
# ============================================================
def add_ai_suggestion(source: str, suggestion: str, direction: str = "") -> int:
    """添加AI建议到建议池"""
    now = _now()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""INSERT INTO mt_ai_suggestion_pool
            (source, direction, suggestion, status, created_at)
            VALUES(?,?,?,?,?)""",
                  (source, direction, suggestion, "PENDING", now))
        conn.commit()
        sid = c.lastrowid
        conn.close()
    return sid


def evaluate_suggestion(suggestion_id: int, feasibility: float, value: float,
                        cost: float, risk: float) -> float:
    """评估建议(评估矩阵:可行性/价值/成本/风险)"""
    # 综合分 = 可行性*0.3 + 价值*0.3 + (1-成本)*0.2 + (1-风险)*0.2
    score = round(feasibility * 0.3 + value * 0.3 + (1 - cost) * 0.2 + (1 - risk) * 0.2, 4)
    priority = int(score * 10)
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""UPDATE mt_ai_suggestion_pool
            SET feasibility=?, value_score=?, cost_score=?, risk_score=?, priority=?, status='EVALUATED'
            WHERE suggestion_id=?""",
                  (feasibility, value, cost, risk, priority, suggestion_id))
        conn.commit(); conn.close()
    return score


# ============================================================
# 方向6: 5级版本管理 - 注册/bump/委员会
# ============================================================
VERSION_LEVELS = ["L1_MAIN", "L2_MINOR", "L3_FIX", "L4_PATCH", "L5_BUILD"]
VERSION_COMMITTEE = ["田经理_AI_004", "石监理_AI_005", "钱合规_AI_008"]


def register_version(level: str, number: str, change_type: str,
                     reason: str = "", arch_review: bool = False,
                     committee_approved: bool = False) -> int:
    """注册版本(融入张晓峰综3:L1/L2需委员会一致通过;综1:L1需架构评审)"""
    if level not in VERSION_LEVELS:
        raise RuntimeError(f"[VERSION-VIOLATION] 非法版本级别: {level}")
    # L1需架构评审(张晓峰综1)
    if level == "L1_MAIN" and not arch_review:
        raise RuntimeError("[VERSION-VIOLATION] L1主版本必须通过架构评审(张晓峰综1)")
    # L1/L2需委员会一致通过(张晓峰综3)
    if level in ("L1_MAIN", "L2_MINOR") and not committee_approved:
        raise RuntimeError(f"[VERSION-VIOLATION] {level}版本必须版本变更委员会一致通过(张晓峰综3)")
    now = _now()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO mt_version_registry
            (version_level, version_number, change_type, bump_reason, committee_approved,
             arch_review_passed, created_at)
            VALUES(?,?,?,?,?,?,?)""",
                  (level, number, change_type, reason, int(committee_approved),
                   int(arch_review), now))
        conn.commit()
        vid = c.execute("SELECT version_id FROM mt_version_registry WHERE version_number=?", (number,)).fetchone()
        conn.close()
    return vid[0] if vid else 0


def smart_bump(change_type: str, arch_review: bool = False,
               committee_approved: bool = False) -> str:
    """智能bump引擎(变更类型→级别)"""
    mapping = {
        "ARCHITECTURE": "L1_MAIN",
        "FEATURE": "L2_MINOR",
        "BUGFIX": "L3_FIX",
        "PATCH": "L4_PATCH",
        "BUILD": "L5_BUILD"
    }
    level = mapping.get(change_type, "L5_BUILD")
    now = datetime.now()
    number = f"v{now.year % 100}.{now.month}.{now.day}.{level.split('_')[0]}"
    register_version(level, number, change_type, arch_review=arch_review,
                     committee_approved=committee_approved)
    return number


# ============================================================
# 执行步骤记录(STEP_7_EXECUTE落库依据)
# ============================================================
def get_execution_status() -> Dict[str, Any]:
    """获取6方向执行状态(供execute_steps_json落库)"""
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        status = {}
        for table, direction in [
            ("mt_daemon_registry", "方向1_调度中枢"),
            ("mt_eigenflux_expert_registry", "方向2_EigenFlux扩建"),
            ("mt_ai_intervene_audit", "方向3_AI介入引擎"),
            ("mt_repair_strategy_lib", "方向4_巡检闭环"),
            ("mt_ai_suggestion_pool", "方向5_功能拓展"),
            ("mt_version_registry", "方向6_版本管理"),
        ]:
            try:
                cnt = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                status[direction] = {"table": table, "rows": cnt, "skeleton_ready": True}
            except Exception:
                status[direction] = {"table": table, "rows": 0, "skeleton_ready": False}
        conn.close()
    return status
