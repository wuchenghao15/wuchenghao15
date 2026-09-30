#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneDrive 主库 Schema 对齐器 (零侵入老列)
策略:
  1) 老表 mt_ai_brain_feed_log / mt_anomaly_feature_library / mt_experience_library
     → 不改列, 创建 VIEW `v_governance_*` 提供统一列名, 并提供"字段适配 INSERT"写入交集列
  2) 缺表 mt_auto_repair_log / mt_upgrade_log / mt_skill_sim_log /
        mt_ai_decision_log / mt_ai_action_log
     → 直接 CREATE TABLE (与 ai_governance_db.py 定义一致, 便于回退)
  3) 提供 insert_* 适配函数, 统一给治理中枢/决策引擎调用

使用: 启动前调用 align_main_db(), 成功后所有 ai_governance_db.py 的 CRUD
      通过本模块的"兼容写法"路由到老表或新表.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("schema_aligner")

# OneDrive 主库路径
MAIN_DB = os.path.expanduser(
    "~/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/ai_engines/app.db"
)

# -------- IO 看门狗 (同 ai_governance_db, 规避 OneDrive 挂起) --------
import signal as _sig


class _IOWatchdog(Exception):
    pass


def _arm(to: int = 10):
    try:
        _sig.signal(_sig.SIGALRM, lambda *_: (_ for _ in ()).throw(_IOWatchdog("OneDrive IO hang")))
        _sig.alarm(to)
    except (ValueError, OSError):
        pass


def _disarm():
    try:
        _sig.alarm(0)
    except (ValueError, OSError):
        pass


def main_conn(timeout_ms=20000) -> sqlite3.Connection:
    assert os.path.exists(MAIN_DB), f"OneDrive 主库不存在: {MAIN_DB}"
    _arm(10)
    try:
        conn = sqlite3.connect(MAIN_DB, timeout=timeout_ms / 1000.0)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {timeout_ms}")
        conn.execute("PRAGMA foreign_keys = OFF")  # 视图/新表不引入FK
        return conn
    finally:
        _disarm()


# ---------- schema 对齐 ----------
ALIGN_REPORT: Dict[str, Any] = {}


def _cols_of(conn, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _create_if_missing(conn, create_sql: str) -> str:
    try:
        conn.execute(create_sql)
        return "created"
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            return "exists"
        raise


def align_main_db() -> Dict[str, Any]:
    """执行 schema 对齐并返回报告. 所有写操作幂等, 可重复调用."""
    report: Dict[str, Any] = {"target_db": MAIN_DB, "at": datetime.now().isoformat()}
    conn = main_conn()
    try:
        # ---- 1) 脑库 VIEW + 安全写 ----
        _align_brain_feed(conn, report)
        # ---- 2) 异常特征 VIEW + 安全写 ----
        _align_anomaly(conn, report)
        # ---- 3) 经验库 VIEW + 安全写 ----
        _align_experience(conn, report)
        # ---- 4) 新建 5 张独立表 (不存在则建) ----
        report["mt_auto_repair_log"] = _create_new_tables(conn, "mt_auto_repair_log",
            "repair_id TEXT PRIMARY KEY, anomaly_id TEXT, strategy TEXT NOT NULL, target TEXT, "
            "before_hash TEXT, after_hash TEXT, success INTEGER DEFAULT 0, detail TEXT, created_at TEXT NOT NULL")
        report["mt_upgrade_log"] = _create_new_tables(conn, "mt_upgrade_log",
            "upgrade_id TEXT PRIMARY KEY, target TEXT NOT NULL, from_version TEXT, to_version TEXT, "
            "status TEXT NOT NULL, rollback_to TEXT, detail TEXT, created_at TEXT NOT NULL")
        report["mt_skill_sim_log"] = _create_new_tables(conn, "mt_skill_sim_log",
            "sim_id TEXT PRIMARY KEY, skill_name TEXT NOT NULL, scenario TEXT NOT NULL, "
            "score REAL DEFAULT 0.0, passed INTEGER DEFAULT 0, detail TEXT, created_at TEXT NOT NULL")
        report["mt_log_decision_log"] = _create_new_tables(conn, "mt_log_decision_log",
            "id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id TEXT UNIQUE NOT NULL, "
            "severity TEXT, signal TEXT, sig_count INTEGER DEFAULT 0, "
            "consensus_score REAL DEFAULT 0.0, reasoning TEXT, "
            "actions_recommended_json TEXT, created_at TEXT NOT NULL")
        report["mt_log_action_log"] = _create_new_tables(conn, "mt_log_action_log",
            "id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT UNIQUE NOT NULL, "
            "decision_id TEXT, action_type TEXT NOT NULL, signal TEXT, target_path TEXT, "
            "detail_json TEXT, success INTEGER DEFAULT 0, before_hash TEXT, after_hash TEXT, "
            "run_ms INTEGER DEFAULT 0, created_at TEXT NOT NULL")
        # ---- 5) 索引 (IF NOT EXISTS) ----
        _ensure_indexes(conn)
        conn.commit()
    finally:
        conn.close()
    report["compatible_view_count"] = 3
    report["new_table_count"] = 5
    return report


def _align_brain_feed(conn, report):
    """老表: feed_id(int PK), flow_id, feed_kind, feed_content, triggered_at,
             knowledge_category, source_system, confidence_score, rule_id, tags
      视图 v_governance_mt_ai_brain_feed_log 提供:
             feed_id(text), flow_id, category, title, content, source, consensus_score, tags, created_at
    """
    cols = _cols_of(conn, "mt_ai_brain_feed_log")
    report["mt_ai_brain_feed_log_old_cols"] = cols
    # 视图 (幂等)
    conn.execute("DROP VIEW IF EXISTS v_governance_mt_ai_brain_feed_log")
    conn.execute("""
        CREATE VIEW v_governance_mt_ai_brain_feed_log AS
        SELECT
            CAST(feed_id AS TEXT) AS feed_id,
            flow_id,
            COALESCE(knowledge_category, 'uncategorized') AS category,
            substr(feed_content, 1, 80) AS title,
            feed_content AS content,
            COALESCE(source_system, 'auto') AS source,
            COALESCE(confidence_score, 0.5) AS consensus_score,
            COALESCE(tags, '[]') AS tags,
            COALESCE(triggered_at, datetime('now')) AS created_at
        FROM mt_ai_brain_feed_log
    """)
    report["v_governance_mt_ai_brain_feed_log"] = "created"


def _align_anomaly(conn, report):
    """老表: feat_id(int PK), flow_id, anomaly_type, anomaly_feature, created_at,
             feature_hash, feature_kind, feature_vector_json, source_flow
      视图 v_governance_mt_anomaly_feature_library:
             feature_id(text), source_type, feature_signature, severity, context_json, detected_at, repaired
    """
    cols = _cols_of(conn, "mt_anomaly_feature_library")
    report["mt_anomaly_feature_library_old_cols"] = cols
    # 补 repaired 列 (ALTER ADD 安全, 不影响老引擎)
    if "repaired" not in cols:
        try:
            conn.execute("ALTER TABLE mt_anomaly_feature_library ADD COLUMN repaired INTEGER DEFAULT 0")
            report["mt_anomaly_feature_library.new_col.repaired"] = "added"
        except sqlite3.OperationalError as e:
            report["mt_anomaly_feature_library.new_col.repaired"] = f"skip: {e}"
    conn.execute("DROP VIEW IF EXISTS v_governance_mt_anomaly_feature_library")
    conn.execute("""
        CREATE VIEW v_governance_mt_anomaly_feature_library AS
        SELECT
            CAST(feat_id AS TEXT) AS feature_id,
            COALESCE(feature_kind, 'runtime') AS source_type,
            COALESCE(feature_hash, anomaly_feature) AS feature_signature,
            CASE COALESCE(source_flow, '')
                WHEN 'critical' THEN 'critical'
                WHEN 'high' THEN 'high'
                WHEN 'medium' THEN 'medium'
                ELSE 'medium'
            END AS severity,
            COALESCE(feature_vector_json, '{}') AS context_json,
            COALESCE(created_at, datetime('now')) AS detected_at,
            COALESCE(repaired, 0) AS repaired
        FROM mt_anomaly_feature_library
    """)
    report["v_governance_mt_anomaly_feature_library"] = "created"


def _align_experience(conn, report):
    """老表: exp_id(int PK), flow_id, exp_content, exp_rating, created_at,
             experience_hash, title, content_json, source_flow
      视图 v_governance_mt_experience_library:
             exp_id(text), domain, lesson, origin, created_at
    """
    cols = _cols_of(conn, "mt_experience_library")
    report["mt_experience_library_old_cols"] = cols
    conn.execute("DROP VIEW IF EXISTS v_governance_mt_experience_library")
    conn.execute("""
        CREATE VIEW v_governance_mt_experience_library AS
        SELECT
            CAST(exp_id AS TEXT) AS exp_id,
            COALESCE(source_flow, 'general') AS domain,
            COALESCE(title, substr(exp_content, 1, 120)) AS lesson,
            'legacy_alignment' AS origin,
            COALESCE(created_at, datetime('now')) AS created_at
        FROM mt_experience_library
    """)
    report["v_governance_mt_experience_library"] = "created"


def _create_new_tables(conn, name: str, body: str) -> str:
    try:
        conn.execute(f"CREATE TABLE IF NOT EXISTS {name} ({body})")
        return "created_or_exists"
    except sqlite3.OperationalError as e:
        return f"error: {e}"


def _ensure_indexes(conn):
    idxs = [
        "CREATE INDEX IF NOT EXISTS idx_repair_anomaly ON mt_auto_repair_log(anomaly_id)",
        "CREATE INDEX IF NOT EXISTS idx_upgrade_status ON mt_upgrade_log(status)",
        "CREATE INDEX IF NOT EXISTS idx_skill_sim_skill ON mt_skill_sim_log(skill_name)",
        "CREATE INDEX IF NOT EXISTS idx_decision_sig ON mt_log_decision_log(signal)",
        "CREATE INDEX IF NOT EXISTS idx_action_action ON mt_log_action_log(action_type)",
        "CREATE INDEX IF NOT EXISTS idx_action_success ON mt_log_action_log(success)",
        "CREATE INDEX IF NOT EXISTS idx_action_decision ON mt_log_action_log(decision_id)",
    ]
    for s in idxs:
        try:
            conn.execute(s)
        except Exception:
            pass


# ---------- 兼容 CRUD: 统一写入主库 ----------
def _id(prefix: str) -> str:
    import time
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{int(time.time()*1000) % 1000000}"


def brain_insert(flow_id: str, category: str, title: str, content: str,
                 source: str, consensus_score: float = 0.0,
                 tags: Optional[List[str]] = None) -> Optional[str]:
    """写入 mt_ai_brain_feed_log (老字段口径), 返回老表 feed_id 文本形式."""
    try:
        conn = main_conn()
        try:
            tags_j = json.dumps(tags or [], ensure_ascii=False)
            content_full = (f"[{title}] " if title else "") + content
            conn.execute(
                "INSERT INTO mt_ai_brain_feed_log "
                "(flow_id, feed_kind, feed_content, triggered_at, knowledge_category,"
                " source_system, confidence_score, tags) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (flow_id, category or "uncategorized", content_full,
                 datetime.now().isoformat(), category or "uncategorized",
                 source or "auto", float(consensus_score or 0.0), tags_j),
            )
            conn.commit()
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            return str(new_id)
        finally:
            conn.close()
    except _IOWatchdog:
        logger.error("brain_insert 挂起中断")
        return None
    except Exception as e:
        logger.error("brain_insert 失败: %s", e)
        return None


def anomaly_insert(source_type: str, feature_signature: str, severity: str,
                   context: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """写入老表 mt_anomaly_feature_library (新列 repaired 走安全 ALTER 补列)."""
    try:
        conn = main_conn()
        try:
            cols = _cols_of(conn, "mt_anomaly_feature_library")
            base_flow = severity  # 复用 severity 做 source_flow, 视图可映射回 severity
            sql_parts = [
                "INSERT INTO mt_anomaly_feature_library",
                "(flow_id, anomaly_type, anomaly_feature, created_at, feature_hash, feature_kind, source_flow",
            ]
            vals = [_id("flow"), source_type or "runtime",
                    json.dumps(context or {}, ensure_ascii=False)[:5000],
                    datetime.now().isoformat(),
                    feature_signature or "", source_type or "runtime", base_flow]
            if "feature_vector_json" in cols:
                sql_parts[1] += ", feature_vector_json"
                vals.append(json.dumps(context or {}, ensure_ascii=False))
            if "repaired" in cols:
                sql_parts[1] += ", repaired"
                vals.append(0)
            sql_parts.append(") VALUES (" + ",".join("?" for _ in vals) + ")")
            sql = "".join(sql_parts)
            conn.execute(sql, vals)
            conn.commit()
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            return str(new_id)
        finally:
            conn.close()
    except Exception as e:
        logger.error("anomaly_insert 失败: %s", e)
        return None


def anomaly_mark_repaired(feature_id: str) -> bool:
    """按文本 feature_id 回写 repaired=1 (兼容 int PK)."""
    try:
        conn = main_conn()
        try:
            cols = _cols_of(conn, "mt_anomaly_feature_library")
            if "repaired" not in cols:
                return False
            # feature_id 可能是 文本 PK(新表) 或 数字 PK(老表文本化)
            try:
                pk_int = int(feature_id)
            except ValueError:
                pk_int = None
            if pk_int is not None:
                r = conn.execute(
                    "UPDATE mt_anomaly_feature_library SET repaired=1 WHERE feat_id=?", (pk_int,)
                )
            else:
                r = conn.execute(
                    "UPDATE mt_anomaly_feature_library SET repaired=1 WHERE CAST(feat_id AS TEXT)=?",
                    (feature_id,),
                )
            conn.commit()
            return r.rowcount > 0 if r.rowcount else False
        finally:
            conn.close()
    except Exception as e:
        logger.error("anomaly_mark_repaired 失败: %s", e)
        return False


def experience_insert(domain: str, lesson: str, origin: str) -> Optional[str]:
    """写入 mt_experience_library 老表."""
    try:
        conn = main_conn()
        try:
            conn.execute(
                "INSERT INTO mt_experience_library "
                "(flow_id, exp_content, exp_rating, created_at, title, source_flow, experience_hash) "
                "VALUES (?, ?, 5, ?, ?, ?, ?)",
                (_id("flow"), lesson, datetime.now().isoformat(),
                 lesson[:80], domain or "general",
                 _id("hash")),
            )
            conn.commit()
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            return str(new_id)
        finally:
            conn.close()
    except Exception as e:
        logger.error("experience_insert 失败: %s", e)
        return None


def repair_insert(anomaly_id, strategy, target, before_hash, after_hash,
                  success, detail="") -> Optional[str]:
    return _simple_insert(
        "mt_auto_repair_log", "repair_id",
        dict(anomaly_id=anomaly_id, strategy=strategy, target=target,
             before_hash=before_hash, after_hash=after_hash,
             success=1 if success else 0, detail=detail),
    )


def upgrade_insert(target, from_version, to_version, status, rollback_to=None,
                   detail="") -> Optional[str]:
    return _simple_insert(
        "mt_upgrade_log", "upgrade_id",
        dict(target=target, from_version=from_version, to_version=to_version,
             status=status, rollback_to=rollback_to, detail=detail),
    )


def skill_insert(skill_name, scenario, score, passed, detail="") -> Optional[str]:
    return _simple_insert(
        "mt_skill_sim_log", "sim_id",
        dict(skill_name=skill_name, scenario=scenario, score=float(score),
             passed=1 if passed else 0, detail=detail),
    )


def decision_insert(sig_id, signal, action, confidence, severity, reasoning,
                    consensus_pass) -> Optional[str]:
    return _simple_insert(
        "mt_log_decision_log", "decision_id",
        dict(sig_id=sig_id, signal=signal, action=action,
             confidence=float(confidence or 0), severity=severity,
             reasoning=reasoning, consensus_pass=1 if consensus_pass else 0),
    )


def action_insert(decision_id, action, target_file, success, detail,
                  before_hash, after_hash) -> Optional[str]:
    return _simple_insert(
        "mt_log_action_log", "action_id",
        dict(decision_id=decision_id, action=action, target_file=target_file,
             success=1 if success else 0, detail=detail,
             before_hash=before_hash, after_hash=after_hash),
    )


def _simple_insert(table: str, pk: str, values: Dict[str, Any]) -> Optional[str]:
    """新建独立表通用 INSERT, 含 created_at/executed_at/decided_at 自动填充."""
    now = datetime.now().isoformat()
    new_id = _id(pk[:3])
    row = dict(values)
    row[pk] = new_id
    for ts_col in ("created_at", "executed_at", "decided_at", "detected_at"):
        if ts_col not in row and _has_col(table, ts_col):
            row[ts_col] = now
    cols = list(row.keys())
    qs = ",".join("?" * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({qs})"
    try:
        conn = main_conn()
        try:
            conn.execute(sql, [row[c] for c in cols])
            conn.commit()
            return new_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("_simple_insert %s 失败: %s", table, e)
        return None


_COL_CACHE: Dict[str, List[str]] = {}


def _has_col(table: str, col: str) -> bool:
    if table not in _COL_CACHE:
        try:
            conn = main_conn()
            try:
                _COL_CACHE[table] = _cols_of(conn, table)
            finally:
                conn.close()
        except Exception:
            _COL_CACHE[table] = []
    return col in _COL_CACHE[table]


def main_stats() -> Dict[str, int]:
    """主库 8 张目标表计数 (视图 + 新表)."""
    out: Dict[str, int] = {}
    reads = [
        ("mt_ai_brain_feed_log", "v_governance_mt_ai_brain_feed_log"),
        ("mt_anomaly_feature_library", "v_governance_mt_anomaly_feature_library"),
        ("mt_experience_library", "v_governance_mt_experience_library"),
        ("mt_auto_repair_log", "mt_auto_repair_log"),
        ("mt_upgrade_log", "mt_upgrade_log"),
        ("mt_skill_sim_log", "mt_skill_sim_log"),
        ("mt_log_decision_log", "mt_log_decision_log"),
        ("mt_log_action_log", "mt_log_action_log"),
    ]
    try:
        conn = main_conn()
        try:
            for name, src in reads:
                try:
                    r = conn.execute(f"SELECT COUNT(*) AS c FROM {src}").fetchone()
                    out[name] = int(r["c"]) if r else -1
                except sqlite3.OperationalError:
                    out[name] = -1
        finally:
            conn.close()
    except Exception:
        pass
    return out


# 方便 --cli 用
if __name__ == "__main__":
    import sys, json as _j
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s %(levelname)s] %(message)s")
    mode = sys.argv[1] if len(sys.argv) > 1 else "align"
    if mode == "align":
        rep = align_main_db()
        print(_j.dumps(rep, ensure_ascii=False, indent=2, default=str))
    elif mode == "stats":
        align_main_db()
        print(_j.dumps(main_stats(), ensure_ascii=False, indent=2))
    else:
        print("用法: schema_aligner.py {align|stats}")
        sys.exit(2)

# ───────────────────────────────────────────────
# v22.11.0 兼容层: 治理面板 / _cron_engine_runner 统一入口
# ───────────────────────────────────────────────
def ensure_schema_ready() -> Dict[str, Any]:
    """align_main_db() + 列迁移 + 真实 PRAGMA 校验。供治理面板/决策引擎统一调用。"""
    rep = align_main_db()
    import sqlite3 as _sq
    _c = _sq.connect(MAIN_DB, timeout=15); _cu = _c.cursor()

    # --- 列迁移: 老列名 → 新列名 (RENAME COLUMN, SQLite 3.25+) ---
    _aliases = {
        "mt_log_decision_log": {"sig_id":"sig_count","action":"actions_recommended_json",
                                 "confidence":"consensus_score","consensus_pass":"sig_count",
                                 "decided_at":"created_at"},
        "mt_log_action_log":   {"action":"action_type","target_file":"target_path",
                                 "detail":"detail_json","executed_at":"created_at"},
    }
    for tbl, mapping in _aliases.items():
        _cu.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
        if not _cu.fetchone():
            continue
        _cu.execute(f"PRAGMA table_info({tbl})")
        existing = {r[1] for r in _cu.fetchall()}
        for old_col, new_col in mapping.items():
            if old_col in existing and new_col not in existing:
                try:
                    _cu.execute(f'ALTER TABLE {tbl} RENAME COLUMN "{old_col}" TO "{new_col}"')
                    rep.setdefault("column_rename", []).append(f"{tbl}.{old_col}→{new_col}")
                except Exception:
                    pass
        # 补缺失列
        _cu.execute(f"PRAGMA table_info({tbl})")
        existing = {r[1] for r in _cu.fetchall()}
        _target_dec = {"id","decision_id","severity","signal","sig_count","consensus_score",
                       "reasoning","actions_recommended_json","created_at"}
        _target_act = {"id","action_id","decision_id","action_type","signal","target_path",
                       "detail_json","success","before_hash","after_hash","run_ms","created_at"}
        _targets = {"mt_log_decision_log": _target_dec, "mt_log_action_log": _target_act}
        for col in _targets.get(tbl, set()):
            if col not in existing and col != "id":
                try:
                    _cu.execute(f'ALTER TABLE {tbl} ADD COLUMN "{col}" TEXT')
                    rep.setdefault("column_add", []).append(f"{tbl}.{col}")
                except Exception:
                    pass
    _c.commit()

    # --- 兼容视图: drop 旧表 → 创建同名视图映射新表 (治理面板查询兼容) ---
    try:
        _cu.execute("DROP TABLE IF EXISTS mt_ai_decision_log")
        _cu.execute("DROP TABLE IF EXISTS mt_ai_action_log")
        _cu.execute("""CREATE VIEW IF NOT EXISTS mt_ai_decision_log AS
            SELECT decision_id, sig_count AS sig_id, signal,
                   actions_recommended_json AS action, consensus_score AS confidence,
                   severity, reasoning, consensus_pass, created_at AS decided_at
            FROM mt_log_decision_log""")
        _cu.execute("""CREATE VIEW IF NOT EXISTS mt_ai_action_log AS
            SELECT action_id, decision_id, action_type AS action,
                   target_path AS target_file, success, detail_json AS detail,
                   before_hash, after_hash, created_at AS executed_at, signal, run_ms
            FROM mt_log_action_log""")
        _c.commit()
        rep["compat_views"] = ["mt_ai_decision_log", "mt_ai_action_log"]
    except Exception as _e:
        rep["compat_views_error"] = str(_e)

    # --- 真实校验: VIEW / repaired 列 / 5 新表 ---
    _views_target = ["v_governance_mt_ai_brain_feed_log",
                     "v_governance_mt_anomaly_feature_library",
                     "v_governance_mt_experience_library"]
    views_found = []
    for v in _views_target:
        _cu.execute("SELECT name FROM sqlite_master WHERE type='view' AND name=?", (v,))
        if _cu.fetchone():
            views_found.append(v)
    views_ok = len(views_found)

    _cu.execute("PRAGMA table_info(mt_anomaly_feature_library)")
    repaired_column_added = int(any(r[1] == "repaired" for r in _cu.fetchall()))

    _new_target = ["mt_auto_repair_log","mt_upgrade_log","mt_skill_sim_log",
                   "mt_log_decision_log","mt_log_action_log"]
    new_status = {}
    for t in _new_target:
        _cu.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
        new_status[t] = bool(_cu.fetchone())
    _c.close()

    new_tables_created = sum(1 for v in new_status.values() if v)
    out = dict(rep)
    out.update({
        "views_ok": views_ok,
        "repaired_column_added": repaired_column_added,
        "new_tables_created": new_tables_created,
        "views": views_found,
        "new_tables": [t for t,v in new_status.items() if v],
        "all_ok": views_ok == 3 and new_tables_created >= 5,
        "new_tables_status": new_status,
        "target_db": MAIN_DB,
    })
    global ALIGN_REPORT
    ALIGN_REPORT = out
    return out


# 向后兼容: 把蓝图/决策引擎的 insert_* / decision_insert / action_insert 等别名直接对齐
def decision_insert(**kw):
    """治理决策落库 → 对应治理面板 mt_log_decision_log。
    兼容引擎签名: sig_id/signal_name/action/confidence/severity/reasoning/consensus_pass
    兼容面板签名: decision_id/signal/sig_count/consensus_score/actions_recommended_json
    """
    from datetime import datetime as _dt
    import sqlite3 as _sq, time as _time
    _signal = kw.get("signal") or kw.get("signal_name") or "UNKNOWN"
    _score = kw.get("consensus_score")
    if _score is None:
        _score = kw.get("confidence", 0.0)
    _act = kw.get("action")
    _arj = kw.get("actions_recommended_json")
    if _arj is None:
        _ar = kw.get("actions_recommended")
        _arj = _json_dumps(_ar if _ar is not None else ([_act] if _act else []))
    _did = kw.get("decision_id") or f"dec_{_dt.now().strftime('%Y%m%d%H%M%S')}_{int(_time.time()*1000)%1000000}"
    conn = _sq.connect(MAIN_DB, timeout=10); cur = conn.cursor()
    cur.execute("""INSERT OR IGNORE INTO mt_log_decision_log
        (decision_id,severity,signal,sig_count,consensus_score,reasoning,actions_recommended_json,consensus_pass,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (_did, kw.get("severity") or "medium", _signal,
         int(kw.get("sig_count") or 1), float(_score or 0.0),
         kw.get("reasoning") or "", _arj,
         1 if kw.get("consensus_pass") else 0,
         kw.get("created_at") or _dt.now().isoformat(timespec="seconds")))
    conn.commit(); conn.close()
    return _did

def action_insert(**kw):
    """治理动作落库 → 对应治理面板 mt_log_action_log。
    兼容引擎签名: decision_id/action/target_file/success/detail/before_hash/after_hash
    兼容面板签名: action_id/action_type/target_path/detail_json/signal/run_ms
    """
    from datetime import datetime as _dt
    import sqlite3 as _sq, time as _time
    _atype = kw.get("action_type") or kw.get("action") or "UNKNOWN"
    _tpath = kw.get("target_path") or kw.get("target_file")
    _djson = kw.get("detail_json")
    if _djson is None:
        _djson = _json_dumps(kw.get("detail") or {})
    _aid = kw.get("action_id") or f"act_{_dt.now().strftime('%Y%m%d%H%M%S')}_{int(_time.time()*1000)%1000000}"
    conn = _sq.connect(MAIN_DB, timeout=10); cur = conn.cursor()
    cur.execute("""INSERT OR IGNORE INTO mt_log_action_log
        (action_id,decision_id,action_type,signal,target_path,detail_json,success,before_hash,after_hash,run_ms,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (_aid, kw.get("decision_id"), _atype, kw.get("signal") or "",
         _tpath, _djson,
         1 if kw.get("success") else 0,
         kw.get("before_hash"), kw.get("after_hash"),
         int(kw.get("run_ms") or 0),
         kw.get("created_at") or _dt.now().isoformat(timespec="seconds")))
    conn.commit(); conn.close()
    return _aid

def _json_dumps(obj):
    import json as _json
    try:
        return _json.dumps(obj, ensure_ascii=False)
    except Exception:
        return _json.dumps({"raw": str(obj)}, ensure_ascii=False)

