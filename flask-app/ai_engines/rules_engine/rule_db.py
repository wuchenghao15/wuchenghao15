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


# ============================================================
# §12.4 仙女座 mt_params 启动自动初始化
# v2.1.0 新增: rules_engine 加载时确保 mt_params 表存在 + 核心 daemon 周期参数
# 来源: flow_andromeda_v62_fix_20260922_001 经验沉淀
# ============================================================
def ensure_mt_params_defaults() -> Optional[int]:
    """
    启动时自动初始化 mt_params:
      1. 确保表存在 (CREATE TABLE IF NOT EXISTS)
      2. INSERT OR IGNORE 18 条核心 daemon CYCLE 参数 (幂等)
      3. 返回实际插入的行数 (0=已全部存在)

    DB 路径优先级:
      a. engines/app.db (仙女座 v6.2 修复后活跃库)
      b. _runtime/databases/Database/app.db (legacy)

    Returns:
        Optional[int]: 插入行数, None 表示 DB 不可用
    """
    # 路径解析 (与 ai_smart_mount_engine.py 保持一致)
    _flask_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _project_root = os.path.dirname(_flask_app_dir)
    candidates = [
        os.path.join(_flask_app_dir, "engines", "app.db"),
        os.path.join(_project_root, "_runtime", "databases", "Database", "app.db"),
    ]
    db_path = None
    for p in candidates:
        if os.path.exists(p):
            db_path = p
            break
    if db_path is None:
        return None

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=60000")
        cur.execute("PRAGMA journal_mode=WAL")

        # 建表 (与 deploy_mac_autoloader.py L92-108 完全对齐)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mt_params (
                param_id INTEGER PRIMARY KEY AUTOINCREMENT,
                param_group TEXT NOT NULL,
                param_key TEXT NOT NULL,
                param_value TEXT,
                param_type TEXT DEFAULT 'string',
                description TEXT,
                is_sensitive INTEGER DEFAULT 0,
                is_readonly INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                updated_by TEXT,
                UNIQUE(param_group, param_key)
            )
        """)

        # 18 条核心 daemon 周期参数 (幂等 INSERT OR IGNORE)
        _now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _DAEMON_DEFAULTS = [
            ("smart_mount","sys_heartbeat_writer_interval_sec","30","int","心跳写入周期"),
            ("smart_mount","sys_patrol_inspector_interval_sec","60","int","巡检周期"),
            ("smart_mount","sys_auto_repair_interval_sec","120","int","自动修复周期"),
            ("smart_mount","sys_local_inference_interval_sec","120","int","本地推理周期"),
            ("smart_mount","sys_rule_enforcer_interval_sec","300","int","规则执行周期"),
            ("smart_mount","sys_auto_patrol_interval_sec","300","int","自动巡逻周期"),
            ("smart_mount","sys_auto_hire_interval_sec","300","int","自动雇佣周期"),
            ("smart_mount","sys_eigenflux_network_interval_sec","120","int","EigenFlux 网络周期"),
            ("smart_mount","sys_deep_inspection_interval_sec","600","int","深度巡检周期"),
            ("smart_mount","sys_file_organizer_interval_sec","600","int","文件整理周期"),
            ("smart_mount","sys_copy_inspection_interval_sec","900","int","文案巡检周期"),
            ("smart_mount","sys_andromeda_auto_evolution_interval_sec","600","int","仙女座演化周期"),
            ("smart_mount","sys_github_fusion_scan_interval_sec","3600","int","GitHub 融合周期"),
            ("smart_mount","sys_error_digest_interval_sec","1800","int","错题消化周期"),
            ("smart_mount","sys_ramanujan_derive_interval_sec","600","int","拉马努金推导周期"),
            ("ollama","host","http://127.0.0.1:11435","str","Ollama 服务地址"),
            ("ollama","embed_model","nomic-embed-text","str","嵌入模型"),
            ("ollama","derive_model","qwen2.5:7b","str","推导模型"),
        ]

        inserted = 0
        for row in _DAEMON_DEFAULTS:
            cur.execute("""
                INSERT OR IGNORE INTO mt_params
                (param_group, param_key, param_value, param_type, description,
                 is_sensitive, is_readonly, created_at, updated_at, updated_by)
                VALUES (?,?,?,?,?,0,0,?,?,?)
            """, row + (_now, _now, "rules_engine_autoseed"))
            inserted += cur.rowcount

        conn.commit()
        conn.close()
        return inserted
    except sqlite3.Error:
        return None
