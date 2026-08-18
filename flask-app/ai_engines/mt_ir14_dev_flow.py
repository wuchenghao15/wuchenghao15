#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
§14 IRON_RULE 强制开发12步骤会话管理器
======================================
flow_id 规则：flow_<topic>_<YYYYMMDD>_<NNN>
5张强制表：mt_dev_flow_session / mt_dev_flow_events / mt_ai_brain_feed_log
           mt_experience_library / mt_anomaly_feature_library
附加：mt_iron_rule_violations（违规审计）
"""
import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_LOCK = threading.Lock()
_MT_IR_DEV_FLOW_EDGES = {
    "STEP_1_PROPOSAL":        ["STEP_2A_ROUND"],
    "STEP_2A_ROUND":          ["STEP_3_ZXF_DECISION"],
    "STEP_3_ZXF_DECISION":    ["STEP_31_B_ROUND", "STEP_32_PASS_SKIP_B"],
    "STEP_31_B_ROUND":        ["STEP_311_SA_JUDGMENT", "STEP_312_AUTO_PASS"],
    "STEP_311_SA_JUDGMENT":   ["STEP_4_CLERK_RECORD"],
    "STEP_312_AUTO_PASS":     ["STEP_4_CLERK_RECORD"],
    "STEP_32_PASS_SKIP_B":    ["STEP_4_CLERK_RECORD"],
    "STEP_4_CLERK_RECORD":    ["STEP_5_IMPL_DOCKING"],
    "STEP_5_IMPL_DOCKING":    ["STEP_6_AI_TEAM_COORD"],
    "STEP_6_AI_TEAM_COORD":   ["STEP_7_EXECUTE"],
    "STEP_7_EXECUTE":         ["STEP_8_ACCEPTANCE"],
    "STEP_8_ACCEPTANCE":      ["STEP_9A_PASS_OR_LOOPBACK"],
    "STEP_9A_PASS_OR_LOOPBACK":["STEP_1_PROPOSAL", "STEP_9B_SUMMARY"],
    "STEP_9B_SUMMARY":        ["STEP_10_SMART_VERSION_UPGRADE"],
    "STEP_10_SMART_VERSION_UPGRADE": ["STEP_11_AUTO_GIT_SYNC"],
    "STEP_11_AUTO_GIT_SYNC":  ["STEP_12_TEST1000"],
    "STEP_12_TEST1000":       ["FINAL_DONE"],
    "FINAL_DONE":             ["FINAL_DONE"],
}

MT_SESSION_TABLE = "mt_dev_flow_session"
MT_EVENTS_TABLE  = "mt_dev_flow_events"
MT_BRAIN_TABLE   = "mt_ai_brain_feed_log"
MT_EXP_TABLE     = "mt_experience_library"
MT_ANOM_TABLE    = "mt_anomaly_feature_library"
MT_VIOL_TABLE    = "mt_iron_rule_violations"

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DB = os.path.join(ROOT, "app.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


SESSION_COLS = [
    ("proposal_title", "TEXT"), ("proposal_summary", "TEXT"),
    ("proposal_json", "TEXT"), ("a_round_panels_json", "TEXT"),
    ("a_round_attendance_json", "TEXT"), ("a_round_discussion_json", "TEXT"),
    ("zhangxiaofeng_decision", "TEXT"), ("b_round_json", "TEXT"),
    ("super_admin_judgment", "TEXT"), ("clerk_record_json", "TEXT"),
    ("clerk_vote_summary", "TEXT"), ("impl_team_contact_json", "TEXT"),
    ("impl_plan_detail_json", "TEXT"), ("ai_team_coord_json", "TEXT"),
    ("ai_core_roles_json", "TEXT"), ("execute_steps_json", "TEXT"),
    ("acceptance_json", "TEXT"), ("acceptance_passed", "INTEGER DEFAULT 0"),
    ("acceptance_step_results_json", "TEXT"),
    ("summary_report_json", "TEXT"), ("db_written", "INTEGER DEFAULT 0"),
    ("brain_fed", "INTEGER DEFAULT 0"), ("experience_fed", "INTEGER DEFAULT 0"),
    ("anomaly_fed", "INTEGER DEFAULT 0"),
    ("super_admin_report_status", "TEXT"),
    ("smart_upgrade_version", "TEXT"),
    ("smart_upgrade_should_upgrade", "INTEGER DEFAULT 0"),
    ("smart_upgrade_reasons_json", "TEXT"),
    ("smart_upgrade_triggered", "INTEGER DEFAULT 0"),
    ("smart_upgrade_log_id", "TEXT"),
    ("git_sync_remote_name", "TEXT"), ("git_sync_target_branch", "TEXT"),
    ("git_sync_auth_mode", "TEXT"), ("git_sync_commit_hash", "TEXT"),
    ("git_sync_commit_subject", "TEXT"), ("git_sync_status", "TEXT"),
    ("git_sync_error", "TEXT"), ("git_sync_json", "TEXT"),
    ("test1000_total", "INTEGER DEFAULT 0"), ("test1000_pass", "INTEGER DEFAULT 0"),
    ("test1000_fail", "INTEGER DEFAULT 0"), ("test1000_vuln", "INTEGER DEFAULT 0"),
    ("test1000_json", "TEXT"),
    ("created_at", "TEXT NOT NULL DEFAULT (datetime('now'))"),
    ("updated_at", "TEXT NOT NULL DEFAULT (datetime('now'))"),
    ("final_status", "TEXT NOT NULL DEFAULT 'OPEN'"),
    ("loopback_count", "INTEGER NOT NULL DEFAULT 0"),
]


def ensure_tables() -> None:
    """§14 IRON_RULE §4 5张强制表 + 1张违规表 建表（幂等 + 缺失列补齐）"""
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.executescript(f"""
        CREATE TABLE IF NOT EXISTS {MT_SESSION_TABLE} (
            flow_id                    TEXT PRIMARY KEY,
            current_step               TEXT NOT NULL DEFAULT 'STEP_1_PROPOSAL',
            loopback_count             INTEGER NOT NULL DEFAULT 0,
            final_status               TEXT NOT NULL DEFAULT 'OPEN',
            proposal_title             TEXT,
            proposal_summary           TEXT,
            proposal_json              TEXT,
            a_round_panels_json        TEXT,
            a_round_attendance_json    TEXT,
            a_round_discussion_json    TEXT,
            zhangxiaofeng_decision     TEXT,
            b_round_json               TEXT,
            super_admin_judgment       TEXT,
            clerk_record_json          TEXT,
            clerk_vote_summary         TEXT,
            impl_team_contact_json     TEXT,
            impl_plan_detail_json      TEXT,
            ai_team_coord_json         TEXT,
            ai_core_roles_json         TEXT,
            execute_steps_json         TEXT,
            acceptance_json            TEXT,
            acceptance_passed          INTEGER DEFAULT 0,
            acceptance_step_results_json TEXT,
            summary_report_json        TEXT,
            db_written                 INTEGER DEFAULT 0,
            brain_fed                  INTEGER DEFAULT 0,
            experience_fed             INTEGER DEFAULT 0,
            anomaly_fed                INTEGER DEFAULT 0,
            super_admin_report_status  TEXT,
            smart_upgrade_version      TEXT,
            smart_upgrade_should_upgrade INTEGER DEFAULT 0,
            smart_upgrade_reasons_json TEXT,
            smart_upgrade_triggered    INTEGER DEFAULT 0,
            smart_upgrade_log_id       TEXT,
            git_sync_remote_name       TEXT,
            git_sync_target_branch     TEXT,
            git_sync_auth_mode         TEXT,
            git_sync_commit_hash       TEXT,
            git_sync_commit_subject    TEXT,
            git_sync_status            TEXT,
            git_sync_error             TEXT,
            git_sync_json              TEXT,
            test1000_total             INTEGER DEFAULT 0,
            test1000_pass              INTEGER DEFAULT 0,
            test1000_fail              INTEGER DEFAULT 0,
            test1000_vuln              INTEGER DEFAULT 0,
            test1000_json              TEXT,
            created_at                 TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at                 TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS {MT_EVENTS_TABLE} (
            ev_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id     TEXT NOT NULL,
            from_step   TEXT NOT NULL,
            to_step     TEXT NOT NULL,
            event_kind  TEXT NOT NULL,
            payload     TEXT,
            operator    TEXT DEFAULT 'AI',
            triggered_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS {MT_BRAIN_TABLE} (
            feed_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id      TEXT NOT NULL,
            feed_kind    TEXT NOT NULL,
            feed_content TEXT NOT NULL,
            triggered_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS {MT_EXP_TABLE} (
            exp_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id     TEXT NOT NULL,
            exp_content TEXT NOT NULL,
            exp_rating  INTEGER DEFAULT 5,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS {MT_ANOM_TABLE} (
            feat_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id        TEXT NOT NULL,
            anomaly_type   TEXT NOT NULL,
            anomaly_feature TEXT NOT NULL,
            created_at     TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS {MT_VIOL_TABLE} (
            viol_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id   TEXT,
            viol_rule TEXT NOT NULL,
            detail    TEXT,
            created_at TEXT NOT NULL
        );
        """)
        # ---------- 缺失列补齐（全部6张表） ----------
        def _cols(table: str) -> set:
            return set(r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall())

        ev_cols = _cols(MT_EVENTS_TABLE)
        for col, deflt in [("payload", "TEXT"), ("operator", "TEXT DEFAULT 'AI'")]:
            if col not in ev_cols:
                try: c.execute(f"ALTER TABLE {MT_EVENTS_TABLE} ADD COLUMN {col} {deflt}")
                except Exception: pass
        sess_cols = _cols(MT_SESSION_TABLE)
        for col, deflt in SESSION_COLS:
            if col not in sess_cols:
                try: c.execute(f"ALTER TABLE {MT_SESSION_TABLE} ADD COLUMN {col} {deflt}")
                except Exception: pass
        # mt_ai_brain_feed_log: 旧版可能只有 feed_id/flow_id 两项
        br_cols = _cols(MT_BRAIN_TABLE)
        for col, deflt in [("flow_id", "TEXT"), ("feed_kind", "TEXT"),
                           ("feed_content", "TEXT"), ("triggered_at", "TEXT")]:
            if col not in br_cols:
                try: c.execute(f"ALTER TABLE {MT_BRAIN_TABLE} ADD COLUMN {col} {deflt}")
                except Exception: pass
        # mt_experience_library
        ex_cols = _cols(MT_EXP_TABLE)
        for col, deflt in [("flow_id", "TEXT"), ("exp_content", "TEXT"),
                           ("exp_rating", "INTEGER DEFAULT 5"), ("created_at", "TEXT")]:
            if col not in ex_cols:
                try: c.execute(f"ALTER TABLE {MT_EXP_TABLE} ADD COLUMN {col} {deflt}")
                except Exception: pass
        # mt_anomaly_feature_library
        an_cols = _cols(MT_ANOM_TABLE)
        for col, deflt in [("flow_id", "TEXT"), ("anomaly_type", "TEXT"),
                           ("anomaly_feature", "TEXT"), ("created_at", "TEXT")]:
            if col not in an_cols:
                try: c.execute(f"ALTER TABLE {MT_ANOM_TABLE} ADD COLUMN {col} {deflt}")
                except Exception: pass
        # mt_iron_rule_violations
        vl_cols = _cols(MT_VIOL_TABLE)
        for col, deflt in [("flow_id", "TEXT"), ("viol_rule", "TEXT"),
                           ("detail", "TEXT"), ("created_at", "TEXT")]:
            if col not in vl_cols:
                try: c.execute(f"ALTER TABLE {MT_VIOL_TABLE} ADD COLUMN {col} {deflt}")
                except Exception: pass
        conn.commit()
        conn.close()


def transition(flow_id: str, to_step: str, *,
               event_kind: str = "AUTO",
               payload: Optional[Dict[str, Any]] = None,
               update_fields: Optional[Dict[str, Any]] = None,
               operator: str = "AI") -> bool:
    """§14 §3.2 状态转移拦截：严格按边进行 + 落库"""
    ensure_tables()
    now = datetime.now().isoformat()
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        row = c.execute(f"SELECT current_step, loopback_count FROM {MT_SESSION_TABLE} WHERE flow_id=?",
                        (flow_id,)).fetchone()
        if not row:
            raise RuntimeError(f"[§14 VIOLATION] flow_id 不存在: {flow_id}")
        from_step = row["current_step"]
        allowed = _MT_IR_DEV_FLOW_EDGES.get(from_step, [])
        if to_step not in allowed:
            msg = (f"[DEV-FLOW-VIOLATION-IRON-RULE] 非法状态转移: "
                   f"{from_step} -> {to_step} (允许={allowed})")
            c.execute(f"INSERT INTO {MT_VIOL_TABLE}(flow_id, viol_rule, detail, created_at) VALUES(?,?,?,?)",
                      (flow_id, "MT_IR_D2", msg, now))
            conn.commit(); conn.close()
            raise RuntimeError(msg)
        loopback_inc = 0
        if from_step == "STEP_9A_PASS_OR_LOOPBACK" and to_step == "STEP_1_PROPOSAL":
            loopback_inc = 1
        updates = ["current_step=?", "updated_at=?"]
        params: List[Any] = [to_step, now]
        if loopback_inc:
            updates.append("loopback_count=loopback_count+?")
            params.append(loopback_inc)
        if update_fields:
            for k, v in update_fields.items():
                updates.append(f"{k}=?")
                params.append(json.dumps(v, ensure_ascii=False)
                              if isinstance(v, (dict, list)) else v)
        params.append(flow_id)
        c.execute(f"UPDATE {MT_SESSION_TABLE} SET {', '.join(updates)} WHERE flow_id=?", params)
        c.execute(
            f"INSERT INTO {MT_EVENTS_TABLE}(flow_id, from_step, to_step, event_kind, payload, operator, triggered_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (flow_id, from_step, to_step, event_kind,
             json.dumps(payload or {}, ensure_ascii=False), operator, now))
        conn.commit(); conn.close()
        return True


def step1_create_proposal(flow_id: str, title: str, summary: str, proposal: Dict) -> str:
    ensure_tables()
    now = datetime.now().isoformat()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        exists = c.execute(f"SELECT 1 FROM {MT_SESSION_TABLE} WHERE flow_id=?",
                           (flow_id,)).fetchone()
        if not exists:
            c.execute(
                f"INSERT INTO {MT_SESSION_TABLE}"
                "(flow_id, current_step, proposal_title, proposal_summary, proposal_json,"
                " created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
                (flow_id, "STEP_1_PROPOSAL", title, summary,
                 json.dumps(proposal, ensure_ascii=False), now, now))
        c.execute(
            f"INSERT INTO {MT_EVENTS_TABLE}(flow_id, from_step, to_step, event_kind, payload, operator, triggered_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (flow_id, "__CREATE__", "STEP_1_PROPOSAL", "CREATE",
             json.dumps({"title": title, "summary": summary}, ensure_ascii=False), "AI", now))
        conn.commit(); conn.close()
    return flow_id


def feed_brain(flow_id: str, kind: str, content: str) -> None:
    ensure_tables()
    now = datetime.now().isoformat()
    with _LOCK:
        conn = _get_conn(); c = conn.cursor()
        c.execute(f"INSERT INTO {MT_BRAIN_TABLE}(flow_id, feed_kind, feed_content, triggered_at) VALUES(?,?,?,?)",
                  (flow_id, kind, content[:16000], now))
        if kind in ("summary_success", "loopback"):
            c.execute(f"INSERT INTO {MT_EXP_TABLE}(flow_id, exp_content, created_at) VALUES(?,?,?)",
                      (flow_id, content[:16000], now))
            c.execute(f"UPDATE {MT_SESSION_TABLE} SET experience_fed=experience_fed+1 WHERE flow_id=?",
                      (flow_id,))
        if kind == "anomaly":
            c.execute(f"INSERT INTO {MT_ANOM_TABLE}(flow_id, anomaly_type, anomaly_feature, created_at) VALUES(?,?,?,?)",
                      (flow_id, "FAIL_SAMPLE", content[:16000], now))
            c.execute(f"UPDATE {MT_SESSION_TABLE} SET anomaly_fed=anomaly_fed+1 WHERE flow_id=?",
                      (flow_id,))
        c.execute(f"UPDATE {MT_SESSION_TABLE} SET brain_fed=brain_fed+1, updated_at=? WHERE flow_id=?",
                  (now, flow_id))
        conn.commit(); conn.close()


def get_session(flow_id: str) -> Optional[Dict]:
    ensure_tables()
    conn = _get_conn()
    r = conn.execute(f"SELECT * FROM {MT_SESSION_TABLE} WHERE flow_id=?", (flow_id,)).fetchone()
    conn.close()
    return {k: r[k] for k in r.keys()} if r else None
