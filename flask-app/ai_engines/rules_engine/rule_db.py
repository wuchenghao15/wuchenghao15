"""
规则相关表的 DAO 操作
================================

维护 3 张规则治理表:
- mt_rule_changelog:       规则变更日志
- mt_rule_violation_alert: 违反告警投喂记录
- mt_rule_integrity_scan:  完整性自检报告

依赖 SQLite 主库 (与系统主 DB 同源, 避免新建连接池)
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional


# 主库路径 (仙女座 v5.0 修复: 从 app.db 改为 mtscos.db)
_DB_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "_runtime",
        "databases",
        "Database",
        "mtscos.db",
    )
)

# 兼容回退 (历史路径 app.db / ai_engines/app.db)
_LEGACY_PATHS = [
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "_runtime", "databases", "Database", "app.db")
    ),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.db")),
]


def _resolve_db_path() -> str:
    """优先 mtscos.db, 回退 legacy app.db, 最后 :memory:"""
    if os.path.exists(_DB_PATH):
        return _DB_PATH
    for p in _LEGACY_PATHS:
        if os.path.exists(p):
            return p
    return ":memory:"


_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS mt_rule_changelog (
        change_id              INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id                TEXT NOT NULL,
        rule_file              TEXT NOT NULL,
        from_version           TEXT,
        to_version             TEXT NOT NULL,
        change_type            TEXT NOT NULL,
        change_summary         TEXT NOT NULL,
        change_diff            TEXT,
        approved_by_7step      INTEGER NOT NULL DEFAULT 0,
        sa_final_decision      TEXT,
        sa_vikey_verified      INTEGER NOT NULL DEFAULT 0,
        proposer               TEXT NOT NULL,
        eigenflux_panel_json   TEXT,
        admin_approvers_json   TEXT,
        created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        effective_at          TIMESTAMP,
        is_secret_withdrawn   INTEGER DEFAULT 0,
        CONSTRAINT uk_rule_version UNIQUE (rule_id, to_version)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_rule_changelog_rule_id ON mt_rule_changelog(rule_id)",
    "CREATE INDEX IF NOT EXISTS idx_rule_changelog_created ON mt_rule_changelog(created_at)",
    """
    CREATE TABLE IF NOT EXISTS mt_rule_violation_alert (
        alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id         TEXT NOT NULL,
        violation_code  TEXT NOT NULL,
        violation_detail TEXT,
        triggered_by    TEXT,
        triggered_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        eigenflux_fed   INTEGER DEFAULT 0,
        brain_fed       INTEGER DEFAULT 0,
        sa_notified     INTEGER DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_rva_rule_id ON mt_rule_violation_alert(rule_id)",
    "CREATE INDEX IF NOT EXISTS idx_rva_triggered ON mt_rule_violation_alert(triggered_at)",
    """
    CREATE TABLE IF NOT EXISTS mt_rule_integrity_scan (
        scan_id              INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_rules          INTEGER NOT NULL,
        scanned_rules        INTEGER NOT NULL,
        passed_rules         INTEGER NOT NULL,
        failed_rules         INTEGER NOT NULL,
        weak_words_count     INTEGER NOT NULL,
        missing_meta_count   INTEGER NOT NULL,
        missing_trigger_count INTEGER NOT NULL,
        scan_report_json     TEXT NOT NULL,
        scan_status          TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ris_scan_at ON mt_rule_integrity_scan(scan_at)",
]


class RuleDB:
    """规则相关表的 DAO"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _resolve_db_path()
        self._ensure_tables()

    def _get_conn(self) -> sqlite3.Connection:
        # 🔧 仙女座 v5.0: timeout=30s + WAL + checkpoint=10000
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA wal_autocheckpoint = 10000")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _ensure_tables(self) -> None:
        try:
            with self._get_conn() as conn:
                for ddl in _DDL_STATEMENTS:
                    conn.execute(ddl)
                conn.commit()
        except sqlite3.Error as exc:
            print(f"[ERROR] 初始化规则表失败: {exc}")

    def insert_rule_changelog(
        self,
        rule_id: str,
        rule_file: str,
        from_version: str,
        to_version: str,
        change_type: str,
        change_summary: str,
        change_diff: str = "",
        approved_by_7step: int = 0,
        sa_final_decision: str = "",
        sa_vikey_verified: int = 0,
        proposer: str = "AI管理员",
        eigenflux_panel_json: str = "",
        admin_approvers_json: str = "",
        effective_at: Optional[str] = None,
        is_secret_withdrawn: int = 0,
    ) -> int:
        sql = """
            INSERT INTO mt_rule_changelog
                (rule_id, rule_file, from_version, to_version, change_type,
                 change_summary, change_diff, approved_by_7step,
                 sa_final_decision, sa_vikey_verified, proposer,
                 eigenflux_panel_json, admin_approvers_json,
                 effective_at, is_secret_withdrawn)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            rule_id, rule_file, from_version, to_version, change_type,
            change_summary, change_diff, approved_by_7step,
            sa_final_decision, sa_vikey_verified, proposer,
            eigenflux_panel_json, admin_approvers_json,
            effective_at, is_secret_withdrawn,
        )
        try:
            with self._get_conn() as conn:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur.lastrowid or 0
        except sqlite3.IntegrityError:
            print(f"[WARN] 重复 changelog 记录: {rule_id} {to_version}")
            return 0

    def insert_violation_alert(
        self,
        rule_id: str,
        violation_code: str,
        violation_detail: str = "",
        triggered_by: str = "",
        eigenflux_fed: int = 0,
        brain_fed: int = 0,
        sa_notified: int = 0,
    ) -> int:
        sql = """
            INSERT INTO mt_rule_violation_alert
                (rule_id, violation_code, violation_detail, triggered_by,
                 eigenflux_fed, brain_fed, sa_notified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            rule_id, violation_code, violation_detail, triggered_by,
            eigenflux_fed, brain_fed, sa_notified,
        )
        try:
            with self._get_conn() as conn:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur.lastrowid or 0
        except sqlite3.Error as exc:
            print(f"[ERROR] 写入违反告警失败: {exc}")
            return 0

    def mark_violation_alert_fed(
        self, alert_id: int, eigenflux_fed: int = 1, brain_fed: int = 0, sa_notified: int = 0
    ) -> None:
        sql = """
            UPDATE mt_rule_violation_alert
            SET eigenflux_fed = ?, brain_fed = ?, sa_notified = ?
            WHERE alert_id = ?
        """
        try:
            with self._get_conn() as conn:
                conn.execute(sql, (eigenflux_fed, brain_fed, sa_notified, alert_id))
                conn.commit()
        except sqlite3.Error as exc:
            print(f"[ERROR] 更新告警投喂标记失败: {exc}")

    def insert_integrity_scan(
        self,
        total_rules: int,
        scanned_rules: int,
        passed_rules: int,
        failed_rules: int,
        weak_words_count: int,
        missing_meta_count: int,
        missing_trigger_count: int,
        scan_report_json: str,
        scan_status: str,
    ) -> int:
        sql = """
            INSERT INTO mt_rule_integrity_scan
                (total_rules, scanned_rules, passed_rules, failed_rules,
                 weak_words_count, missing_meta_count, missing_trigger_count,
                 scan_report_json, scan_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            total_rules, scanned_rules, passed_rules, failed_rules,
            weak_words_count, missing_meta_count, missing_trigger_count,
            scan_report_json, scan_status,
        )
        try:
            with self._get_conn() as conn:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur.lastrowid or 0
        except sqlite3.Error as exc:
            print(f"[ERROR] 写入完整性自检报告失败: {exc}")
            return 0

    def query_latest_changelog(self, rule_id: str) -> Optional[dict]:
        sql = """
            SELECT * FROM mt_rule_changelog
            WHERE rule_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        try:
            with self._get_conn() as conn:
                cur = conn.execute(sql, (rule_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None


def init_tables(db_path: Optional[str] = None) -> RuleDB:
    """初始化3张规则治理表, 返回 RuleDB 实例"""
    return RuleDB(db_path=db_path)
