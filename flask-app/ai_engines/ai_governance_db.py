#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动化治理中枢 - 数据库核心
覆盖表: mt_ai_brain_feed_log / mt_anomaly_feature_library / mt_experience_library
        mt_auto_repair_log / mt_upgrade_log / mt_skill_sim_log
连接管理带 SIGALRM 看门狗, 规避 OneDrive Files On-Demand IO 挂起.
所有 AI 生成数据实时落库, 数据库为唯一权威源.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ai_governance_db")

# ---------- 配置常量 (本地离线优先, 在线仅辅助) ----------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ONEDRIVE_DB = os.path.expanduser(
    "~/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/ai_engines/app.db"
)
LOCAL_FALLBACK_DB = os.path.join(PROJECT_ROOT, "_runtime", "governance_hub.db")
# 默认本地独立库, 避免破坏 OneDrive 主库 schema; 如需对接主库显式设置 MT_GOV_DB_PATH
DB_PATH = os.environ.get("MT_GOV_DB_PATH", LOCAL_FALLBACK_DB)

IO_WATCHDOG_SEC = int(os.environ.get("MT_GOV_IO_WATCHDOG", "8"))

INTERVAL_BRAIN_FEED = 300
INTERVAL_LOG_PCAP = 120
INTERVAL_SYSTEM_UPGRADE = 1800
INTERVAL_SKILL_SIM = 900
INTERVAL_GOVERNANCE_ROUND = 1200

MAX_BRAIN_FEEDS_PER_ROUND = 20
MAX_REPAIRS_PER_ROUND = 10
MAX_UPGRADES_PER_ROUND = 3
MAX_SKILL_SIMS_PER_ROUND = 8

CONSENSUS_THRESHOLD = 0.65
BYPASS_ALLOWED = False
# 弱约束词映射 (20 词完整映射, 对齐项目铁律)
WEAK_WORDS = {
    "应该": "必须", "建议": "强制", "推荐": "强制", "尽量": "必须",
    "原则上": "强制", "一般": "强制", "应当": "必须", "可考虑": "必须",
    "适当": "强制", "酌情": "强制", "适宜": "强制", "最好": "必须",
    "尽可能": "必须", "一般来说": "强制", "视情况": "强制",
    "根据情况": "强制", "如有必要": "强制", "如有需要": "强制",
    "酌量": "强制", "量力": "强制",
}



class _IOWatchdog(Exception):
    """OneDrive IO 看门狗触发异常"""


def _arm_watchdog(timeout_sec: int):
    def _handler(signum, frame):
        raise _IOWatchdog("OneDrive IO 挂起被看门狗中断")
    try:
        signal.signal(signal.SIGALRM, _handler)
        signal.alarm(timeout_sec)
    except (ValueError, OSError):
        pass


def _disarm_watchdog():
    try:
        signal.alarm(0)
    except (ValueError, OSError):
        pass


def get_conn(timeout_ms: int = 30000) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    _arm_watchdog(IO_WATCHDOG_SEC)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=timeout_ms / 1000.0)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {timeout_ms}")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    finally:
        _disarm_watchdog()


def init_schema() -> bool:
    stmts = [
        "CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (feed_id TEXT PRIMARY KEY, flow_id TEXT NOT NULL, category TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, source TEXT NOT NULL, consensus_score REAL DEFAULT 0.0, tags TEXT, created_at TEXT NOT NULL)",
        "CREATE INDEX IF NOT EXISTS idx_brain_flow ON mt_ai_brain_feed_log(flow_id)",
        "CREATE INDEX IF NOT EXISTS idx_brain_created ON mt_ai_brain_feed_log(created_at)",
        "CREATE TABLE IF NOT EXISTS mt_anomaly_feature_library (feature_id TEXT PRIMARY KEY, source_type TEXT NOT NULL, feature_signature TEXT NOT NULL, severity TEXT NOT NULL, context_json TEXT, detected_at TEXT NOT NULL, repaired INTEGER DEFAULT 0)",
        "CREATE INDEX IF NOT EXISTS idx_anomaly_sig ON mt_anomaly_feature_library(feature_signature)",
        "CREATE TABLE IF NOT EXISTS mt_experience_library (exp_id TEXT PRIMARY KEY, domain TEXT NOT NULL, lesson TEXT NOT NULL, origin TEXT NOT NULL, created_at TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS mt_auto_repair_log (repair_id TEXT PRIMARY KEY, anomaly_id TEXT, strategy TEXT NOT NULL, target TEXT, before_hash TEXT, after_hash TEXT, success INTEGER DEFAULT 0, detail TEXT, created_at TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS mt_upgrade_log (upgrade_id TEXT PRIMARY KEY, target TEXT NOT NULL, from_version TEXT, to_version TEXT, status TEXT NOT NULL, rollback_to TEXT, detail TEXT, created_at TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS mt_skill_sim_log (sim_id TEXT PRIMARY KEY, skill_name TEXT NOT NULL, scenario TEXT NOT NULL, score REAL DEFAULT 0.0, passed INTEGER DEFAULT 0, detail TEXT, created_at TEXT NOT NULL)",
    ]
    try:
        conn = get_conn()
        try:
            for s in stmts:
                conn.execute(s)
            conn.commit()
            return True
        finally:
            conn.close()
    except _IOWatchdog:
        logger.error("init_schema 被 OneDrive IO 看门狗中断")
        return False
    except Exception as e:
        logger.error("init_schema 失败: %s", e)
        return False


def _new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{int(time.time()*1000) % 1000000}"


def insert_brain_feed(flow_id, category, title, content, source, consensus_score=0.0, tags=None):
    feed_id = _new_id("feed")
    try:
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_ai_brain_feed_log (feed_id, flow_id, category, title, content, source, consensus_score, tags, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (feed_id, flow_id, category, title, content, source, float(consensus_score),
                 json.dumps(tags or [], ensure_ascii=False), datetime.now().isoformat())
            )
            conn.commit()
            return feed_id
        finally:
            conn.close()
    except _IOWatchdog:
        logger.error("insert_brain_feed IO 看门狗中断: %s", title)
        return None
    except Exception as e:
        logger.error("insert_brain_feed 失败: %s", e)
        return None


def insert_anomaly(source_type, feature_signature, severity, context=None):
    feature_id = _new_id("anom")
    try:
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_anomaly_feature_library (feature_id, source_type, feature_signature, severity, context_json, detected_at, repaired) VALUES (?, ?, ?, ?, ?, ?, 0)",
                (feature_id, source_type, feature_signature, severity,
                 json.dumps(context or {}, ensure_ascii=False), datetime.now().isoformat())
            )
            conn.commit()
            return feature_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_anomaly 失败: %s", e)
        return None


def mark_anomaly_repaired(feature_id):
    try:
        conn = get_conn()
        try:
            conn.execute("UPDATE mt_anomaly_feature_library SET repaired=1 WHERE feature_id=?", (feature_id,))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error("mark_anomaly_repaired 失败: %s", e)
        return False


def insert_experience(domain, lesson, origin):
    exp_id = _new_id("exp")
    try:
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_experience_library (exp_id, domain, lesson, origin, created_at) VALUES (?, ?, ?, ?, ?)",
                (exp_id, domain, lesson, origin, datetime.now().isoformat())
            )
            conn.commit()
            return exp_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_experience 失败: %s", e)
        return None


def insert_repair_log(anomaly_id, strategy, target, before_hash, after_hash, success, detail=""):
    repair_id = _new_id("rep")
    try:
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_auto_repair_log (repair_id, anomaly_id, strategy, target, before_hash, after_hash, success, detail, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (repair_id, anomaly_id, strategy, target, before_hash, after_hash,
                 1 if success else 0, detail, datetime.now().isoformat())
            )
            conn.commit()
            return repair_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_repair_log 失败: %s", e)
        return None


def insert_upgrade_log(target, from_version, to_version, status, rollback_to=None, detail=""):
    upgrade_id = _new_id("upg")
    try:
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_upgrade_log (upgrade_id, target, from_version, to_version, status, rollback_to, detail, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (upgrade_id, target, from_version, to_version, status, rollback_to,
                 detail, datetime.now().isoformat())
            )
            conn.commit()
            return upgrade_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_upgrade_log 失败: %s", e)
        return None


def insert_skill_sim(skill_name, scenario, score, passed, detail=""):
    sim_id = _new_id("sim")
    try:
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_skill_sim_log (sim_id, skill_name, scenario, score, passed, detail, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sim_id, skill_name, scenario, float(score), 1 if passed else 0, detail, datetime.now().isoformat())
            )
            conn.commit()
            return sim_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_skill_sim 失败: %s", e)
        return None


_ALLOWED_TABLES = {
    "mt_ai_brain_feed_log", "mt_anomaly_feature_library",
    "mt_experience_library", "mt_auto_repair_log",
    "mt_upgrade_log", "mt_skill_sim_log",
}


def query_recent(table, limit=10):
    if table not in _ALLOWED_TABLES:
        return []
    try:
        conn = get_conn()
        try:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (int(limit),)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as e:
        logger.error("query_recent %s 失败: %s", table, e)
        return []


def stats():
    out = {}
    for t in _ALLOWED_TABLES:
        try:
            conn = get_conn()
            try:
                row = conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()
                out[t] = int(row["c"]) if row else 0
            finally:
                conn.close()
        except Exception:
            out[t] = -1
    return out
