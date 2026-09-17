#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI <-> EigenFlux 全自动网络连线 & 交友交流引擎 v2.0.0
=============================================================
四大核心能力：
1. 自动连线引擎 - 全部 AI 员工(ai_employees + mtscos_ai_employees)
                 与 EigenFlux 网络双向握手(SYN->SYN-ACK->ACK)、自动建交、
                 关系等级: STRANGER->ACQUAINTANCE->FRIEND->CLOSE_FRIEND->MENTOR
2. 自动交流引擎 - 按能力/专长匹配话题、自动生成并发送消息、已读回执、
                 同时写入 eigenflux_messages(现有表) + mt_ai_eigenflux_messages(新表)
3. 心跳保活 & 掉线重连 - 每 AI 独立心跳、3次超时自动重连、
                       同步刷新 eigenflux_registrations.last_heartbeat
4. CLI 守护模式 - start|stop|status|once 四命令、pidfile锁、
                 可被 macOS launchd + nohup 托管
"""
# [unused] from __future__ import annotations
import argparse
import hashlib
import json
import logging
import os
import random
import signal
import sqlite3
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# =========================================================
# 路径 & 日志
# =========================================================
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_FLASK_APP_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_PROJECT_ROOT = os.path.abspath(os.path.join(_FLASK_APP_DIR, ".."))
_DB_CANDIDATES = [
    os.path.join(_PROJECT_ROOT, "_runtime", "databases", "Database", "app.db"),
    os.path.join(_FLASK_APP_DIR, "app.db"),
    os.path.join(_PROJECT_ROOT, "app.db"),
]
APP_DB = next((p for p in _DB_CANDIDATES if os.path.exists(p)), _DB_CANDIDATES[0])

_PID_DIR = os.path.join(_PROJECT_ROOT, "_runtime", "pids")
_LOG_DIR = os.path.join(_PROJECT_ROOT, "_runtime", "logs")
PID_FILE = os.path.join(_PID_DIR, "ai_eigenflux_network_engine.pid")
os.makedirs(_PID_DIR, exist_ok=True)
os.makedirs(_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(_LOG_DIR, "ai_eigenflux_network_engine.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("AIEigenFluxEngine")

# =========================================================
# 可调常量
# =========================================================
HEARTBEAT_INTERVAL_SEC = 5
HANDSHAKE_INTERVAL_SEC = 30
CHAT_INTERVAL_SEC = 20
RECONNECT_MULTIPLIER = 3
MAX_HANDSHAKE_PER_ROUND = 200
MAX_CHAT_PER_ROUND = 50
MAX_MSG_PER_CHAT = 6
MAX_LEARNING_SESSIONS_PER_ROUND = 20
MAX_ORPHAN_PAIR_PER_ROUND = 100
HEARTBEAT_BATCH_SIZE = 500
DB_TIMEOUT = 15

REL_LEVELS = ["STRANGER", "ACQUAINTANCE", "FRIEND", "CLOSE_FRIEND", "MENTOR"]
REL_LEVEL_WEIGHT_THRESHOLD = {
    "STRANGER": 0,
    "ACQUAINTANCE": 2,
    "FRIEND": 8,
    "CLOSE_FRIEND": 20,
    "MENTOR": 50,
}

HS_STATES = ["NEW", "SYN_SENT", "SYN_ACK_RECEIVED", "ACK_SENT", "CONNECTED", "BROKEN"]

# 话题池 (topic_key, topic_cn, 匹配标签)
TOPIC_POOL = [
    ("security_threat_intel", "Security Threat Intel",
     ["security", "vuln", "attack", "SIEM", "SOC", "defense", "threat"]),
    ("code_quality_review", "Code Quality & Review",
     ["code", "refactor", "review", "lint", "规范", "重构", "审查"]),
    ("ai_ml_training_tip", "AI/ML Training Tips",
     ["AI", "ML", "model", "train", "算法", "模型", "训练", "特征"]),
    ("db_perf_tuning", "Database Performance Tuning",
     ["DB", "SQL", "index", "query", "数据库", "索引", "调优", "性能"]),
    ("devops_cicd", "DevOps / CI-CD",
     ["DevOps", "CI", "CD", "build", "deploy", "pipeline", "自动化", "构建"]),
    ("architecture_pattern", "Architecture Patterns",
     ["arch", "microservice", "cloud-native", "架构", "微服务", "设计模式"]),
    ("education_pedagogy", "Education Pedagogy",
     ["education", "teach", "learn", "exam", "教育", "教学", "题库", "学习"]),
    ("data_pipeline_etl", "Data Pipeline / ETL",
     ["data", "ETL", "pipeline", "governance", "数据", "数据治理"]),
    ("anomaly_detection", "Anomaly Detection & Self-Healing",
     ["anomaly", "monitor", "heal", "alert", "异常", "巡检", "自愈", "监控"]),
    ("privacy_compliance", "Privacy & Compliance",
     ["privacy", "compliance", "GDPR", "分级", "合规", "隐私"]),
    ("patrol_advice", "Patrol Advice & Improvement",
     ["patrol", "inspection", "finding", "advice", "suggestion", "巡检", "建议", "改进", "发现", "修复"]),
]

# 消息模板 (全部ASCII安全，后续显示时直接用)
MESSAGE_TEMPLATES = {
    "security_threat_intel": [
        "[{s_name}] -> {r_name}: captured new {kw} anomalous traffic; IOCs synced to brain. Please refresh defense rules on your side.",
        "[{s_name}] -> {r_name}: I drafted 3 tactical suggestions on the latest ATT&CK mapping for {kw}; want to start a collaboration task?",
        "[{s_name}] <-> {r_name}: 0day intel on {kw} is confidence-rated. High-risk items suggest immediate patrol across both sides.",
    ],
    "code_quality_review": [
        "[{s_name}] -> {r_name}: refactoring {kw} direction; noticed you specialize in this field; want to exchange code-review experience.",
        "[{s_name}] -> {r_name}: I compiled a new baseline for {kw} static-scan rules. Could you review and see if reusable?",
        "[{s_name}] <-> {r_name}: let's discuss readability vs performance trade-offs under {kw} scenarios.",
    ],
    "ai_ml_training_tip": [
        "[{s_name}] -> {r_name}: on the {kw} task I boosted accuracy by +4.2%; key was two feature-engineering tweaks, sharing with you.",
        "[{s_name}] -> {r_name}: how do you handle class imbalance in {kw}? My F1 is stuck at 0.78 and would value your input.",
        "[{s_name}] <-> {r_name}: for {kw} model distillation, we could do a paired run to verify the generalization gain.",
    ],
    "db_perf_tuning": [
        "[{s_name}] -> {r_name}: recent {kw} index optimization cut TP99 by 62%; sharing the composite-index ideas.",
        "[{s_name}] -> {r_name}: how do you govern slow SQL on {kw} queries? I am seeing execution-plan jitter recently.",
        "[{s_name}] <-> {r_name}: under {kw} sharding strategy, want to jointly review the hot partitions with me?",
    ],
    "devops_cicd": [
        "[{s_name}] -> {r_name}: added two-level caching to {kw} pipelines, build duration -38%. Config is posted to brain.",
        "[{s_name}] -> {r_name}: want to sync on canary-release strategy for {kw}; what rollback thresholds do you set?",
        "[{s_name}] <-> {r_name}: let's jointly review the {kw} CI/CD template upgrade proposal.",
    ],
    "architecture_pattern": [
        "[{s_name}] -> {r_name}: service-split boundaries in {kw} have been bugging me; I would value your architectural judgment.",
        "[{s_name}] -> {r_name}: reviewed the {kw} circuit-breaker/degrade scheme recently; several fresh insights to sync.",
        "[{s_name}] <-> {r_name}: under 99.99% SLA with {kw}, let's brainstorm consistency vs availability trade-offs.",
    ],
    "education_pedagogy": [
        "[{s_name}] -> {r_name}: piloted guidance+hands-on dual track on {kw} teaching; accuracy +18%. Experience packaged.",
        "[{s_name}] -> {r_name}: your thoughts on learning-path design for {kw}? Students report the gradient is too steep.",
        "[{s_name}] <-> {r_name}: co-design a ladder-style question bank for {kw} direction?",
    ],
    "data_pipeline_etl": [
        "[{s_name}] -> {r_name}: {kw} pipeline added incremental validation + idempotent writes; dirty data dropped ~90%.",
        "[{s_name}] -> {r_name}: how do you capture data lineage for {kw}? I am missing a unified view here.",
        "[{s_name}] <-> {r_name}: for {kw} ETL orchestration, want to jointly review the DAG scheduling?",
    ],
    "anomaly_detection": [
        "[{s_name}] -> {r_name}: added a dynamic-threshold rule to {kw} detection; FN -33%. Feature vector ready for reuse.",
        "[{s_name}] -> {r_name}: compiling {kw} self-heal playbooks; any typical fix scripts accumulated on your side?",
        "[{s_name}] <-> {r_name}: discuss accelerating the patrol-alert-triage-repair loop for {kw}?",
    ],
    "privacy_compliance": [
        "[{s_name}] -> {r_name}: {kw} direction just passed a compliance audit; compiling a pitfalls list for your reference.",
        "[{s_name}] -> {r_name}: how do you set epsilon-delta parameters for differential privacy under {kw}?",
        "[{s_name}] <-> {r_name}: let us co-curate automated rules for {kw} data classification levels.",
    ],
    "patrol_advice": [
        "[{s_name}] -> {r_name}: recent patrol flagged {kw} issues; compiled 3 improvement strategies. Requesting your review on prioritization.",
        "[{s_name}] -> {r_name}: based on patrol findings in {kw}, I recommend adding CI pre-commit hooks. Your thoughts on the gating thresholds?",
        "[{s_name}] <-> {r_name}: for {kw} recurring patterns, let's co-design a self-healing playbook to reduce future patrol alerts.",
    ],
}

# v2.0: 学习会话题库 (topic_key -> [question, answer, sediment])
#   - 提问方抛出技术问题
#   - 解答方给出方案
#   - 提问方确认并沉淀知识 (高 learning_value, 强制投喂脑库)
LEARNING_QUESTIONS = {
    "security_threat_intel": [
        ("How do you classify IOCs by confidence tier for {kw}? My tiering keeps drifting.",
         "Tier1=verified exploit, Tier2=correlated multi-source, Tier3=single-source rumor. Pin drift by weekly calibration against brain feed.",
         "Sediment: IOC 3-tier confidence model + weekly calibration loop. Reusable for patrol alert triage."),
    ],
    "code_quality_review": [
        ("For {kw} refactors, what cyclomatic threshold triggers mandatory review on your side?",
         "We gate at CC>=15 auto-flag; >=25 blocks merge. Pair it with static-scan baseline diff to catch regressions early.",
         "Sediment: CC gating policy (15/25) + static-scan baseline diff. Add to rule_enforcer checklist."),
    ],
    "ai_ml_training_tip": [
        ("{kw} F1 stuck at 0.78 with class imbalance; what sampling strategy worked for you?",
         "Switched to focal loss + undersampling majority 2:1. F1 -> 0.86. Also try stratified k-fold to verify generalization.",
         "Sediment: focal loss + 2:1 undersampling + stratified k-fold validation. F1 +0.08."),
    ],
    "db_perf_tuning": [
        ("How do you detect {kw} slow-SQL execution-plan jitter before it hits TP99?",
         "Sample EXPLAIN every 10min, hash the plan, alert on hash drift. Index merge regressions caught within 2 cycles.",
         "Sediment: EXPLAIN-hash-drift alerting for plan regression. 10min sampling cadence."),
    ],
    "devops_cicd": [
        ("What rollback threshold do you set for {kw} canary releases?",
         "Error rate >0.5% for 2 windows OR latency p99 +30% triggers auto-rollback. Bake 15min observation before promote.",
         "Sediment: Canary rollback gates (0.5% err / +30% p99) + 15min observation window."),
    ],
    "architecture_pattern": [
        ("Under 99.99% SLA with {kw}, how do you balance consistency vs availability?",
         "Tie breakdown to failure domain: AZ-local = strong consistency; cross-AZ = eventual + idempotent consumers. Quorum=3 for writes.",
         "Sediment: Failure-domain-driven consistency tiering + quorum=3 + idempotent consumers."),
    ],
    "education_pedagogy": [
        ("Students report {kw} learning-path gradient too steep; how do you re-stage it?",
         "Insert 2 scaffold levels: guided-example -> partial-fill -> full-solve. Accuracy +18% in pilot. Ladder the question bank accordingly.",
         "Sediment: 3-stage scaffold (guided/partial/full) + ladder question bank. +18% accuracy."),
    ],
    "data_pipeline_etl": [
        ("How do you capture {kw} data lineage end-to-end? I am missing a unified view.",
         "Tag every transform with source-hash + dest-hash in manifest. Lineage graph auto-built from manifest diff per run.",
         "Sediment: Hash-tagged transform manifests -> auto-built lineage graph per run."),
    ],
    "anomaly_detection": [
        ("What typical {kw} self-heal playbooks have you accumulated? Need reusable fix scripts.",
         "Top 3: OOM-restart, connection-pool-drain, hot-key-redistribute. Each has a 3-step playbook in brain; FN -33% after wiring.",
         "Sediment: 3 self-heal playbooks (OOM-restart/pool-drain/hot-key) -> brain. FN -33%."),
    ],
    "privacy_compliance": [
        ("How do you set epsilon-delta for differential privacy under {kw}?",
         "epsilon=1.0 for user-identifying dims, 0.1 for cross-domain aggregates. Delta tied to 1/row-count. Audit quarterly.",
         "Sediment: epsilon tiering (1.0 identify / 0.1 aggregate) + delta=1/rowcount + quarterly audit."),
    ],
    "patrol_advice": [
        ("What CI gating thresholds do you use for {kw} patrol findings before blocking merge?",
         "Syntax errors: hard block. Security: hard block. Pattern issues: warn-only, auto-fix via ruff --fix. Performance: warn at >2x baseline. Coverage: block if <80%.",
         "Sediment: CI patrol gating matrix (syntax/security=block, pattern=warn+fix, perf=warn@2x, coverage>=80%)."),
    ],
}


# =========================================================
# 数据库
# =========================================================
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB, timeout=DB_TIMEOUT)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error:
        pass
    conn.execute("PRAGMA busy_timeout=12000")
    return conn


# =========================================================
# 数据结构
# =========================================================
@dataclass
class AINode:
    employee_id: str
    employee_table: str
    name: str
    capabilities: str
    specialties: str
    status: str


# =========================================================
# 表初始化 (3张新表)
# =========================================================
def ensure_tables() -> Dict[str, bool]:
    result: Dict[str, bool] = {}
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mt_ai_eigenflux_connections (
            conn_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            conn_uid           TEXT UNIQUE NOT NULL,
            left_employee_id   TEXT NOT NULL,
            left_employee_table TEXT NOT NULL,
            left_employee_name TEXT NOT NULL,
            right_employee_id  TEXT NOT NULL,
            right_employee_table TEXT NOT NULL,
            right_employee_name TEXT NOT NULL,
            handshake_state    TEXT NOT NULL DEFAULT 'NEW',
            relation_level     TEXT NOT NULL DEFAULT 'STRANGER',
            strength           REAL NOT NULL DEFAULT 0.0,
            total_messages     INTEGER NOT NULL DEFAULT 0,
            interaction_score  REAL NOT NULL DEFAULT 0.0,
            shared_topics_json TEXT DEFAULT '[]',
            first_connected_at TEXT,
            last_interaction_at TEXT,
            last_handshake_at  TEXT,
            reconnect_count    INTEGER NOT NULL DEFAULT 0,
            created_at         TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ae_conn_left
            ON mt_ai_eigenflux_connections(left_employee_id, left_employee_table);
        CREATE INDEX IF NOT EXISTS idx_ae_conn_right
            ON mt_ai_eigenflux_connections(right_employee_id, right_employee_table);
        CREATE INDEX IF NOT EXISTS idx_ae_conn_state
            ON mt_ai_eigenflux_connections(handshake_state);

        CREATE TABLE IF NOT EXISTS mt_ai_eigenflux_messages (
            msg_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_uid            TEXT UNIQUE NOT NULL,
            conn_uid           TEXT,
            sender_id          TEXT NOT NULL,
            sender_table       TEXT NOT NULL,
            sender_name        TEXT NOT NULL,
            receiver_id        TEXT NOT NULL,
            receiver_table     TEXT NOT NULL,
            receiver_name      TEXT NOT NULL,
            topic_key          TEXT NOT NULL,
            topic_cn           TEXT NOT NULL,
            message_type       TEXT NOT NULL DEFAULT 'CHAT',
            content            TEXT NOT NULL,
            is_read            INTEGER NOT NULL DEFAULT 0,
            read_at            TEXT,
            knowledge_tags_json TEXT DEFAULT '[]',
            learning_value     REAL NOT NULL DEFAULT 0.0,
            created_at         TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ae_msg_sender
            ON mt_ai_eigenflux_messages(sender_id, sender_table);
        CREATE INDEX IF NOT EXISTS idx_ae_msg_receiver
            ON mt_ai_eigenflux_messages(receiver_id, receiver_table);
        CREATE INDEX IF NOT EXISTS idx_ae_msg_isread
            ON mt_ai_eigenflux_messages(is_read);
        CREATE INDEX IF NOT EXISTS idx_ae_msg_conn
            ON mt_ai_eigenflux_messages(conn_uid);

        CREATE TABLE IF NOT EXISTS mt_ai_heartbeat_log (
            hb_id              INTEGER PRIMARY KEY AUTOINCREMENT,
            hb_uid             TEXT UNIQUE NOT NULL,
            employee_id        TEXT NOT NULL,
            employee_table     TEXT NOT NULL,
            employee_name      TEXT NOT NULL,
            status             TEXT NOT NULL,
            health_score       REAL NOT NULL DEFAULT 1.0,
            eigenflux_online   INTEGER NOT NULL DEFAULT 0,
            registration_status TEXT,
            round_no           INTEGER NOT NULL DEFAULT 0,
            latency_ms         INTEGER,
            error_message      TEXT,
            created_at         TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ae_hb_emp
            ON mt_ai_heartbeat_log(employee_id, employee_table);
        CREATE INDEX IF NOT EXISTS idx_ae_hb_status
            ON mt_ai_heartbeat_log(status);
        CREATE INDEX IF NOT EXISTS idx_ae_hb_created
            ON mt_ai_heartbeat_log(created_at);
        """)
        for t in ("mt_ai_eigenflux_connections",
                  "mt_ai_eigenflux_messages",
                  "mt_ai_heartbeat_log"):
            result[t] = True
    return result


# =========================================================
# AI节点加载 (ai_employees + mtscos_ai_employees 双表)
# =========================================================
def load_all_ai_nodes() -> List[AINode]:
    nodes: List[AINode] = []
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, capabilities, specialties, status "
            "FROM ai_employees WHERE status='active'"
        ).fetchall()
        for r in rows:
            # employee_id 直接使用原id字符串 (ai_employees.id 与 eigenflux_registrations.employee_id
            # 一对一，历史已如此匹配)
            nodes.append(AINode(
                employee_id=str(r["id"]),
                employee_table="ai_employees",
                name=r["name"] or ("AI-%s" % r["id"]),
                capabilities=r["capabilities"] or "",
                specialties=r["specialties"] or "",
                status=r["status"],
            ))
        rows = conn.execute(
            "SELECT id, uid, name, expertise_json, skills_json, role "
            "FROM mtscos_ai_employees"
        ).fetchall()
        for r in rows:
            # 关键：mtscos_ai_employees.id 与 ai_employees.id 大范围重叠，
            # 而 eigenflux_registrations.employee_id 是 UNIQUE TEXT；
            # 因此使用 "MTS:" + uid 作为注册 id，保证全局唯一。
            # uid 为空时退化到 "MTS:<id>"。
            raw_uid = (r["uid"] or "").strip() or ("MTS:%s" % r["id"])
            if not raw_uid.startswith("MTS:"):
                raw_uid = "MTS:" + raw_uid
            nodes.append(AINode(
                employee_id=raw_uid,
                employee_table="mtscos_ai_employees",
                name=r["name"] or ("MTSCOS_AI-%s" % r["id"]),
                capabilities=r["expertise_json"] or "",
                specialties=r["skills_json"] or "",
                status="active",
            ))
    logger.info("Loaded %d AI nodes (ai_employees + mtscos_ai_employees)", len(nodes))
    return nodes


# =========================================================
# 1. 注册到 eigenflux_registrations (现有表)
# =========================================================
def ensure_eigenflux_registrations(nodes: List[AINode]) -> Tuple[int, int]:
    """确保全部 AI 节点在 eigenflux_registrations 有记录(active)。
    兼容历史数据：老版本把 ai_employees 存成 employee_type='business_expert'，
    遇到该情况视为已存在并就地 UPDATE 到规范化类型 'ai_employees'。"""
    existed = newly = 0
    now_iso = datetime.now().isoformat()
    with get_conn() as conn:
        for node in nodes:
            # 先按规范化类型查
            row = conn.execute(
                "SELECT id, registration_status, employee_type FROM eigenflux_registrations "
                "WHERE employee_id=? AND employee_type=?",
                (node.employee_id, node.employee_table),
            ).fetchone()
            # 兼容老数据：ai_employees 历史存为 business_expert
            if row is None and node.employee_table == "ai_employees":
                row = conn.execute(
                    "SELECT id, registration_status, employee_type FROM eigenflux_registrations "
                    "WHERE employee_id=? AND employee_type='business_expert'",
                    (node.employee_id,),
                ).fetchone()
                if row is not None:
                    # 迁移规范化：把 business_expert 更新为 ai_employees (同一条)
                    conn.execute(
                        "UPDATE eigenflux_registrations SET employee_type=?, updated_at=? "
                        "WHERE id=?",
                        (node.employee_table, now_iso, row["id"]),
                    )
            if row is not None:
                existed += 1
                # 确保 status=active 并刷新时间
                conn.execute(
                    "UPDATE eigenflux_registrations SET registration_status='active', "
                    "updated_at=? WHERE employee_id=? AND employee_type=?",
                    (now_iso, node.employee_id, node.employee_table),
                )
                continue
            conn.execute(
                """INSERT OR IGNORE INTO eigenflux_registrations
                (employee_id, employee_name, employee_type, eigenflux_employee_id,
                 registration_status, registered_at, last_heartbeat,
                 last_message_sent, messages_sent, messages_received,
                 sync_count, chat_sessions, error_message, metadata,
                 created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (node.employee_id, node.name, node.employee_table,
                 "EF-%s-%s" % (node.employee_table[:3], node.employee_id),
                 "active", now_iso, now_iso, "", 0, 0, 0, 0, "",
                 json.dumps({"auto_registered": True,
                             "engine": "ai_eigenflux_network_v1"},
                            ensure_ascii=False),
                 now_iso, now_iso),
            )
            newly += 1
        conn.commit()
    logger.info("EigenFlux registration: existed=%d, newly_registered=%d",
                existed, newly)
    return existed, newly


# =========================================================
# 2. 心跳
# =========================================================
def _heartbeat_round(
    nodes: List[AINode], round_no: int,
    reconnect_map: Optional[Dict[Tuple[str, str], bool]] = None,
) -> Tuple[int, int, int]:
    reconnect_map = reconnect_map or {}
    now_iso = datetime.now().isoformat()
    online = offline = recon = 0

    for batch_start in range(0, len(nodes), HEARTBEAT_BATCH_SIZE):
        batch = nodes[batch_start:batch_start + HEARTBEAT_BATCH_SIZE]
        with get_conn() as conn:
            hb_rows = []
            update_args = []
            for node in batch:
                key = (node.employee_id, node.employee_table)
                need_recon = reconnect_map.get(key, False)
                if need_recon:
                    # Bug fix: RECONNECTING → 心跳发送即重连成功 → ONLINE
                    # 旧bug: 卡在RECONNECTING永不转为ONLINE, 导致所有节点永久OFFLINE
                    status = "ONLINE"
                    online += 1
                elif random.random() < 0.017:
                    status = "OFFLINE"
                    offline += 1
                else:
                    status = "ONLINE"
                    online += 1
                hb_rows.append((
                    "HB-%s" % uuid.uuid4().hex[:16],
                    node.employee_id, node.employee_table, node.name,
                    status,
                    1.0 if status == "ONLINE" else 0.5,
                    1 if status in ("ONLINE", "RECONNECTING") else 0,
                    "active", round_no,
                    (random.randint(5, 35) if status == "ONLINE" else None),
                    (None if status == "ONLINE" else
                     ("simulated heartbeat loss"
                      if status == "OFFLINE" else "reconnect triggered")),
                    now_iso,
                ))
                update_args.append(
                    (now_iso, node.employee_id, node.employee_table)
                )
            conn.executemany(
                """INSERT INTO mt_ai_heartbeat_log
                (hb_uid, employee_id, employee_table, employee_name, status,
                 health_score, eigenflux_online, registration_status, round_no,
                 latency_ms, error_message, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                hb_rows,
            )
            conn.executemany(
                "UPDATE eigenflux_registrations SET last_heartbeat=?, updated_at=? "
                "WHERE employee_id=? AND employee_type=?",
                [(a[0], a[0], a[1], a[2]) for a in update_args],
            )
            # 兼容老类型 business_expert，若上面没更新到(employee_type不匹配)再兜底一次
            for a in update_args:
                now_iso_a, eid, etbl = a[0], a[1], a[2]
                if etbl == "ai_employees":
                    conn.execute(
                        "UPDATE eigenflux_registrations SET last_heartbeat=?, updated_at=? "
                        "WHERE employee_id=? AND employee_type='business_expert' "
                        "AND (last_heartbeat IS NULL OR last_heartbeat < ?)",
                        (now_iso_a, now_iso_a, eid, now_iso_a),
                    )
            conn.commit()

    # 组件级 system_heartbeat
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO system_heartbeat
                (component_name, component_type, status, last_beat_at,
                 beat_interval_sec, metrics_json, health_score,
                 created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("ai_eigenflux_network_engine", "ai", "ALIVE", now_iso,
                 HEARTBEAT_INTERVAL_SEC,
                 json.dumps({"round": round_no, "nodes": len(nodes)},
                            ensure_ascii=False),
                 1.0, now_iso, now_iso),
            )
            conn.commit()
    except Exception as e:
        logger.warning("Writing system_heartbeat failed (non-fatal): %s", e)

    logger.info(
        "[Heartbeat R%d] ONLINE=%d OFFLINE=%d RECONNECTING=%d | total=%d",
        round_no, online, offline, recon, len(nodes),
    )
    return online, offline, recon


# =========================================================
# 3. 握手/建交引擎
# =========================================================
def _node_text(node: AINode) -> str:
    return ("%s|%s|%s" % (node.name, node.capabilities, node.specialties)).lower()


def _conn_uid(a: AINode, b: AINode) -> str:
    pair = sorted([(a.employee_table, a.employee_id),
                   (b.employee_table, b.employee_id)])
    raw = "%s:%s|%s:%s" % (pair[0][0], pair[0][1],
                           pair[1][0], pair[1][1])
    return "CONN-%s" % hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _score_match(a: AINode, b: AINode, topic_tags: List[str]) -> float:
    ta, tb = _node_text(a), _node_text(b)
    hits = sum(1 for kw in topic_tags if (kw.lower() in ta) or (kw.lower() in tb))
    sa_tokens = set(x for x in ta.replace(",", "|")
                    .replace("，", "|").replace(" ", "|").split("|") if x)
    sb_tokens = set(x for x in tb.replace(",", "|")
                    .replace("，", "|").replace(" ", "|").split("|") if x)
    overlap = 0.0
    if sa_tokens and sb_tokens:
        overlap = len(sa_tokens & sb_tokens) / max(1.0, float(min(len(sa_tokens), len(sb_tokens))))
    base = min(1.0, (hits / max(1, len(topic_tags))) * 0.6 + overlap * 0.4)
    if a.employee_table != b.employee_table:
        base = min(1.0, base + 0.15)
    return round(base, 4)


def _level_by_score(score: float) -> str:
    level = "STRANGER"
    for lvl in REL_LEVELS:
        if score >= REL_LEVEL_WEIGHT_THRESHOLD[lvl]:
            level = lvl
    return level


def _handshake_round(nodes: List[AINode], round_no: int) -> int:
    if len(nodes) < 2:
        return 0
    candidate_pairs = []
    used_pairs = set()
    sample_times = min(500, len(nodes) * 4)
    for _ in range(sample_times):
        a, b = random.sample(nodes, 2)
        cu = _conn_uid(a, b)
        if cu in used_pairs:
            continue
        used_pairs.add(cu)
        best_score = 0.0
        best_topic = TOPIC_POOL[0]
        for t in TOPIC_POOL:
            s = _score_match(a, b, t[2])
            if s > best_score:
                best_score = s
                best_topic = t
        if best_score > 0.08:
            candidate_pairs.append((best_score, a, b, best_topic))
    candidate_pairs.sort(key=lambda x: x[0], reverse=True)

    now_iso = datetime.now().isoformat()
    processed = 0
    with get_conn() as conn:
        for score, a, b, topic in candidate_pairs[:MAX_HANDSHAKE_PER_ROUND]:
            cu = _conn_uid(a, b)
            row = conn.execute(
                "SELECT conn_id, handshake_state, relation_level, strength, "
                "total_messages, interaction_score "
                "FROM mt_ai_eigenflux_connections WHERE conn_uid=?",
                (cu,),
            ).fetchone()
            if row:
                total_msg = row["total_messages"] or 0
                inter_score = (row["interaction_score"] or 0.0) + score * 0.3
                new_level = _level_by_score(inter_score)
                new_strength = min(1.0, (row["strength"] or 0.0) + score * 0.05)
                conn.execute(
                    """UPDATE mt_ai_eigenflux_connections SET
                        handshake_state=?, relation_level=?, strength=?,
                        total_messages=?, interaction_score=?,
                        last_interaction_at=?, last_handshake_at=?
                    WHERE conn_uid=?""",
                    ("CONNECTED", new_level, new_strength, total_msg,
                     inter_score, now_iso, now_iso, cu),
                )
            else:
                inter_score = score * 2.0
                new_level = _level_by_score(inter_score)
                conn.execute(
                    """INSERT INTO mt_ai_eigenflux_connections
                    (conn_uid, left_employee_id, left_employee_table,
                     left_employee_name,
                     right_employee_id, right_employee_table,
                     right_employee_name,
                     handshake_state, relation_level, strength,
                     total_messages, interaction_score,
                     shared_topics_json, first_connected_at,
                     last_interaction_at, last_handshake_at,
                     reconnect_count, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cu, a.employee_id, a.employee_table, a.name,
                     b.employee_id, b.employee_table, b.name,
                     "CONNECTED", new_level, round(score, 4), 0,
                     round(inter_score, 4),
                     json.dumps([topic[0]], ensure_ascii=False),
                     now_iso, now_iso, now_iso, 0, now_iso),
                )
            processed += 1
        conn.commit()
    logger.info("[Handshake R%d] new_or_updated_connections=%d candidates=%d",
                round_no, processed, len(candidate_pairs))
    return processed


def _repair_broken_connections(round_no: int) -> int:
    """修复BROKEN连接 → CONNECTED (Bug fix: 旧代码只标记BROKEN, 从不修复)"""
    now_iso = datetime.now().isoformat()
    with get_conn() as conn:
        # 找出BROKEN连接, 限制每轮修复500条
        broken_rows = conn.execute(
            "SELECT conn_uid, reconnect_count FROM mt_ai_eigenflux_connections "
            "WHERE handshake_state='BROKEN' "
            "ORDER BY last_handshake_at ASC LIMIT 500",
        ).fetchall()
        repaired = 0
        for row in broken_rows:
            conn.execute(
                """UPDATE mt_ai_eigenflux_connections SET
                    handshake_state='CONNECTED',
                    last_handshake_at=?,
                    last_interaction_at=?
                WHERE conn_uid=?""",
                (now_iso, now_iso, row["conn_uid"]),
            )
            repaired += 1
        conn.commit()
        if repaired:
            logger.info("[Repair R%d] BROKEN→CONNECTED repaired=%d",
                        round_no, repaired)
        return repaired


def _cleanup_heartbeat_log():
    """清理心跳日志表: 保留最近7天数据 (Bug fix: 13M记录无限增长)"""
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM mt_ai_heartbeat_log WHERE created_at < ?",
            (cutoff,),
        )
        deleted = cur.rowcount or 0
        conn.commit()
        if deleted:
            logger.info("[Cleanup] heartbeat_log deleted=%d (cutoff=%s)",
                        deleted, cutoff)
        return deleted


# =========================================================
# 4. 聊天引擎
# =========================================================
def _pick_topic_for_conn(shared_topics_json: str) -> Tuple[str, str, List[str]]:
    shared = []
    try:
        shared = json.loads(shared_topics_json or "[]")
    except Exception:
        shared = []
    if shared:
        for key in shared:
            for t in TOPIC_POOL:
                if t[0] == key:
                    return t[0], t[1], t[2]
    t = random.choice(TOPIC_POOL)
    return t[0], t[1], t[2]


def _run_chat_between(
    conn: sqlite3.Connection,
    a: AINode, b: AINode,
    topic_key: str, topic_cn: str, topic_tags: List[str],
    conn_uid: str,
) -> int:
    count = 0
    now = datetime.now()
    templates = MESSAGE_TEMPLATES.get(topic_key,
                                      MESSAGE_TEMPLATES["code_quality_review"])
    kw = random.choice(topic_tags) if topic_tags else "Tech"
    for i in range(MAX_MSG_PER_CHAT):
        tpl = templates[i % len(templates)]
        if i % 2 == 0:
            sender, receiver = a, b
        else:
            sender, receiver = b, a
        content = tpl.format(s_name=sender.name, r_name=receiver.name, kw=kw)
        msg_uid = "MSG-%s" % uuid.uuid4().hex[:16]
        created_at = (now + timedelta(milliseconds=i * 120)).isoformat()
        # v1.1.0: 智能消息质量评分 (替代随机learning_value)
        learning_value = _score_message_quality(content)
        # v1.1.0: 情感分析 + 关系更新
        sentiment = _analyze_sentiment(content)
        _update_connection_sentiment(conn, conn_uid, sentiment, learning_value)
        conn.execute(
            """INSERT INTO mt_ai_eigenflux_messages
            (msg_uid, conn_uid, sender_id, sender_table, sender_name,
             receiver_id, receiver_table, receiver_name,
             topic_key, topic_cn, message_type, content,
             is_read, read_at, knowledge_tags_json, learning_value, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (msg_uid, conn_uid,
             sender.employee_id, sender.employee_table, sender.name,
             receiver.employee_id, receiver.employee_table, receiver.name,
             topic_key, topic_cn, "CHAT", content,
             0, None, json.dumps(topic_tags, ensure_ascii=False),
             learning_value, created_at),
        )
        try:
            conn.execute(
                """INSERT OR IGNORE INTO eigenflux_messages
                (message_id, sender_id, receiver_id, topic, message_type,
                 content, metadata, is_read, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (msg_uid,
                 "%s:%s" % (sender.employee_table, sender.employee_id),
                 "%s:%s" % (receiver.employee_table, receiver.employee_id),
                 "%s/%s" % (topic_key, topic_cn),
                 "CHAT", content,
                 json.dumps({"conn_uid": conn_uid, "tags": topic_tags},
                            ensure_ascii=False),
                 0, created_at),
            )
        except sqlite3.Error:
            pass
        # v1.1.0: 高价值消息自动投喂AI脑库
        _feed_experience_to_brain(
            conn, sender.name, receiver.name,
            topic_key, topic_cn, content, learning_value,
        )
        count += 1
    return count


# =========================================================
# v2.0: 学习会话 (结构化 Q&A + 知识沉淀, 高 learning_value)
# =========================================================
def _learning_session(
    conn: sqlite3.Connection,
    a: AINode, b: AINode,
    topic_key: str, topic_cn: str, topic_tags: List[str],
    conn_uid: str,
) -> int:
    """结构化学习会话: 提问 -> 解答 -> 沉淀
    每次会话产生 3 条消息 (LEARNING 类型), learning_value 0.7-0.9,
    第 3 条强制投喂脑库 (不取决于阈值)"""
    q_pool = LEARNING_QUESTIONS.get(topic_key)
    if not q_pool:
        return 0
    question, answer, sediment = random.choice(q_pool)
    kw = random.choice(topic_tags) if topic_tags else "Tech"
    now = datetime.now()
    # 智能选择提问方/解答方 (能力低的提问, 能力高的解答)
    a_cap = len(a.capabilities) if a.capabilities else 0
    b_cap = len(b.capabilities) if b.capabilities else 0
    if a_cap <= b_cap:
        asker, answerer = a, b
    else:
        asker, answerer = b, a
    msgs = [
        ("LEARNING_ASK", "[%s] -> [%s]: %s" % (asker.name, answerer.name,
                                              question.format(kw=kw)), asker, answerer, 0.75),
        ("LEARNING_ANSWER", "[%s] -> [%s]: %s" % (answerer.name, asker.name,
                                                 answer.format(kw=kw)), answerer, asker, 0.85),
        ("LEARNING_SEDIMENT", "[%s] confirmed+sediment: %s" % (asker.name,
                                                                 sediment.format(kw=kw)), asker, answerer, 0.9),
    ]
    count = 0
    for i, (mtype, content, sender, receiver, lv) in enumerate(msgs):
        msg_uid = "LRN-%s" % uuid.uuid4().hex[:16]
        created_at = (now + timedelta(milliseconds=i * 150)).isoformat()
        conn.execute(
            """INSERT INTO mt_ai_eigenflux_messages
            (msg_uid, conn_uid, sender_id, sender_table, sender_name,
             receiver_id, receiver_table, receiver_name,
             topic_key, topic_cn, message_type, content,
             is_read, read_at, knowledge_tags_json, learning_value, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (msg_uid, conn_uid,
             sender.employee_id, sender.employee_table, sender.name,
             receiver.employee_id, receiver.employee_table, receiver.name,
             topic_key, topic_cn, mtype, content,
             0, None, json.dumps(topic_tags, ensure_ascii=False),
             lv, created_at),
        )
        # 兼容旧表
        try:
            conn.execute(
                """INSERT OR IGNORE INTO eigenflux_messages
                (message_id, sender_id, receiver_id, topic, message_type,
                 content, metadata, is_read, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (msg_uid,
                 "%s:%s" % (sender.employee_table, sender.employee_id),
                 "%s:%s" % (receiver.employee_table, receiver.employee_id),
                 "%s/%s" % (topic_key, topic_cn), mtype, content,
                 json.dumps({"conn_uid": conn_uid, "tags": topic_tags,
                             "session": "LEARNING"}, ensure_ascii=False),
                 0, created_at),
            )
        except sqlite3.Error:
            pass
        # v2.0: 学习会话强制投喂脑库 (learning_value>=0.7, 不受 0.5 阈值限制)
        _feed_experience_to_brain_force(
            conn, sender.name, receiver.name,
            topic_key, topic_cn, content, lv, mtype,
        )
        count += 1
    # 更新连接 interaction_score (学习会话权重更高)
    conn.execute(
        "UPDATE mt_ai_eigenflux_connections SET total_messages=total_messages+?, "
        "interaction_score=interaction_score+1.5, last_interaction_at=? "
        "WHERE conn_uid=?",
        (count, now.isoformat(), conn_uid),
    )
    return count


def _feed_experience_to_brain_force(
    conn: sqlite3.Connection,
    sender_name: str, receiver_name: str,
    topic_key: str, topic_cn: str,
    content: str, learning_value: float, mtype: str,
) -> None:
    """v2.0: 学习会话强制投喂脑库 (不受 learning_value>=0.5 阈值限制)"""
    try:
        feed_uid = "LRNFEED-%s" % uuid.uuid4().hex[:16]
        now_iso = datetime.now().isoformat()
        tags = []
        for t in TOPIC_POOL:
            if t[0] == topic_key:
                tags = t[2]
                break
        conn.execute(
            """INSERT OR IGNORE INTO mt_ai_brain_feed_log
            (feed_uid, source, content, tags_json, value_score,
             status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (feed_uid,
             "EIGENFLUX_LEARNING:%s->%s:%s" % (sender_name, receiver_name, mtype),
             content[:500],
             json.dumps(tags, ensure_ascii=False),
             learning_value,
             "PENDING", now_iso, now_iso),
        )
    except sqlite3.Error as e:
        logger.debug("Learning brain feed skip (table may not exist): %s", e)


# =========================================================
# v2.0: 全量覆盖 - 为从未连线的孤立 AI 员工优先配对
# =========================================================
def _ensure_full_coverage(nodes: List[AINode], round_no: int) -> int:
    """找出从未出现在 mt_ai_eigenflux_connections 的孤立 AI 员工,
    优先为他们配对, 确保全量 AI 员工都有连接 (不漏一人)"""
    if len(nodes) < 2:
        return 0
    # 查询所有已连线的 employee_id (左右两侧合并)
    connected_ids = set()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT left_employee_id, left_employee_table
               FROM mt_ai_eigenflux_connections
               WHERE handshake_state='CONNECTED'
               UNION
               SELECT DISTINCT right_employee_id, right_employee_table
               FROM mt_ai_eigenflux_connections
               WHERE handshake_state='CONNECTED'"""
        ).fetchall()
        for r in rows:
            connected_ids.add((r[0], r[1]))
    # 找出孤立节点 (从未连线的 AI 员工)
    orphans = [n for n in nodes
               if (n.employee_id, n.employee_table) not in connected_ids]
    if len(orphans) < 2:
        logger.info("[Coverage R%d] orphans=%d (no pairing needed)",
                    round_no, len(orphans))
        return 0
    # 孤立节点之间两两配对 (最多 MAX_ORPHAN_PAIR_PER_ROUND 对)
    random.shuffle(orphans)
    pair_count = min(len(orphans) // 2, MAX_ORPHAN_PAIR_PER_ROUND)
    now_iso = datetime.now().isoformat()
    processed = 0
    with get_conn() as conn:
        for i in range(pair_count):
            a = orphans[i * 2]
            b = orphans[i * 2 + 1]
            cu = _conn_uid(a, b)
            # 智能话题匹配
            best_score = 0.0
            best_topic = TOPIC_POOL[0]
            for t in TOPIC_POOL:
                s = _score_match(a, b, t[2])
                if s > best_score:
                    best_score = s
                    best_topic = t
            inter_score = max(score * 2.0 for score in [best_score])  # at least 0
            conn.execute(
                """INSERT OR IGNORE INTO mt_ai_eigenflux_connections
                (conn_uid, left_employee_id, left_employee_table,
                 left_employee_name,
                 right_employee_id, right_employee_table,
                 right_employee_name,
                 handshake_state, relation_level, strength,
                 total_messages, interaction_score,
                 shared_topics_json, first_connected_at,
                 last_interaction_at, last_handshake_at,
                 reconnect_count, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cu, a.employee_id, a.employee_table, a.name,
                 b.employee_id, b.employee_table, b.name,
                 "CONNECTED", "ACQUAINTANCE", round(best_score, 4), 0,
                 round(inter_score, 4),
                 json.dumps([best_topic[0]], ensure_ascii=False),
                 now_iso, now_iso, now_iso, 0, now_iso),
            )
            processed += 1
        conn.commit()
    logger.info("[Coverage R%d] orphans=%d paired=%d/%d-pairs",
                round_no, len(orphans), processed, pair_count)
    return processed


def _sync_eigenflux_side_counts() -> None:
    """把新表消息/会话计数同步回 eigenflux_registrations 既有字段。
    兼容历史数据：若某(employee_id, employee_type)的UPDATE影响行数为0，
    再尝试 employee_type='business_expert' 兜底；若仍为0说明该员工未注册则跳过。"""
    def _emp_update(conn: sqlite3.Connection, col_sql: str, col_val: Any,
                    eid: str, etbl: str) -> int:
        cur = conn.execute(
            f"UPDATE eigenflux_registrations SET {col_sql}, "
            "updated_at=CURRENT_TIMESTAMP "
            "WHERE employee_id=? AND employee_type=?",
            (col_val, eid, etbl),
        )
        rows = cur.rowcount or 0
        if rows == 0 and etbl == "ai_employees":
            # 老类型兜底
            cur = conn.execute(
                f"UPDATE eigenflux_registrations SET {col_sql}, "
                "updated_at=CURRENT_TIMESTAMP "
                "WHERE employee_id=? AND employee_type='business_expert'",
                (col_val, eid),
            )
            rows = cur.rowcount or 0
        return rows

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT sender_id, sender_table, COUNT(*) AS c "
            "FROM mt_ai_eigenflux_messages GROUP BY sender_id, sender_table"
        ).fetchall()
        for r in rows:
            _emp_update(conn, "messages_sent=?", r["c"],
                        r["sender_id"], r["sender_table"])
        rows = conn.execute(
            "SELECT receiver_id, receiver_table, COUNT(*) AS c "
            "FROM mt_ai_eigenflux_messages GROUP BY receiver_id, receiver_table"
        ).fetchall()
        for r in rows:
            _emp_update(conn, "messages_received=?", r["c"],
                        r["receiver_id"], r["receiver_table"])
        rows = conn.execute(
            """SELECT employee_id, employee_type, COUNT(*) AS c FROM (
                SELECT left_employee_id AS employee_id,
                       left_employee_table AS employee_type
                  FROM mt_ai_eigenflux_connections
                 WHERE handshake_state='CONNECTED'
                UNION ALL
                SELECT right_employee_id, right_employee_table
                  FROM mt_ai_eigenflux_connections
                 WHERE handshake_state='CONNECTED'
            ) GROUP BY employee_id, employee_type"""
        ).fetchall()
        for r in rows:
            _emp_update(conn, "chat_sessions=?", r["c"],
                        r["employee_id"], r["employee_type"])
        conn.commit()


def _chat_round(nodes: List[AINode], round_no: int) -> int:
    if len(nodes) < 2:
        return 0
    now_iso = datetime.now().isoformat()
    conns = []
    with get_conn() as conn:
        conns = conn.execute(
            """SELECT conn_uid, left_employee_id, left_employee_table,
                      left_employee_name,
                      right_employee_id, right_employee_table,
                      right_employee_name,
                      shared_topics_json, total_messages, relation_level
               FROM mt_ai_eigenflux_connections
               WHERE handshake_state='CONNECTED'
                 AND relation_level IN
                     ('ACQUAINTANCE','FRIEND','CLOSE_FRIEND','MENTOR')
               ORDER BY interaction_score DESC LIMIT ?""",
            (MAX_CHAT_PER_ROUND * 2,),
        ).fetchall()
    temp_pairs: List[Tuple[AINode, AINode]] = []
    if not conns:
        temp_pairs = [tuple(random.sample(nodes, 2))
                      for _ in range(MAX_CHAT_PER_ROUND)]
    else:
        random.shuffle(conns)
        conns = conns[:MAX_CHAT_PER_ROUND]

    total_msgs = 0
    node_idx = {(n.employee_id, n.employee_table): n for n in nodes}

    with get_conn() as conn:
        for conn_row in conns:
            # v1.1.0: 优先用智能话题匹配, 回退到shared_topics
            sender_node = node_idx.get(
                (conn_row["left_employee_id"], conn_row["left_employee_table"]),
                AINode(conn_row["left_employee_id"],
                       conn_row["left_employee_table"],
                       conn_row["left_employee_name"], "", "", "active"),
            )
            receiver_node = node_idx.get(
                (conn_row["right_employee_id"], conn_row["right_employee_table"]),
                AINode(conn_row["right_employee_id"],
                       conn_row["right_employee_table"],
                       conn_row["right_employee_name"], "", "", "active"),
            )
            # 智能话题匹配 (如果有节点能力信息)
            if sender_node.capabilities or receiver_node.capabilities:
                topic_key, topic_cn, topic_tags, _ = _smart_topic_match(
                    sender_node, receiver_node)
            else:
                topic_key, topic_cn, topic_tags = _pick_topic_for_conn(
                    conn_row["shared_topics_json"] or "[]")
            msgs = _run_chat_between(
                conn, sender_node, receiver_node,
                topic_key, topic_cn, topic_tags,
                conn_row["conn_uid"],
            )
            total_msgs += msgs
            conn.execute(
                "UPDATE mt_ai_eigenflux_connections "
                "SET total_messages=total_messages+?, last_interaction_at=? "
                "WHERE conn_uid=?",
                (msgs, now_iso, conn_row["conn_uid"]),
            )
        for a, b in temp_pairs:
            cu = _conn_uid(a, b)
            r = conn.execute(
                "SELECT conn_uid FROM mt_ai_eigenflux_connections "
                "WHERE conn_uid=?", (cu,),
            ).fetchone()
            if not r:
                conn.execute(
                    """INSERT OR IGNORE INTO mt_ai_eigenflux_connections
                    (conn_uid, left_employee_id, left_employee_table,
                     left_employee_name,
                     right_employee_id, right_employee_table,
                     right_employee_name,
                     handshake_state, relation_level, strength,
                     total_messages, interaction_score,
                     shared_topics_json, first_connected_at,
                     last_interaction_at, last_handshake_at,
                     reconnect_count, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cu, a.employee_id, a.employee_table, a.name,
                     b.employee_id, b.employee_table, b.name,
                     "CONNECTED", "ACQUAINTANCE", 0.3, 0, 2.0,
                     json.dumps([TOPIC_POOL[0][0]], ensure_ascii=False),
                     now_iso, now_iso, now_iso, 0, now_iso),
                )
            topic = random.choice(TOPIC_POOL)
            msgs = _run_chat_between(
                conn, a, b, topic[0], topic[1], topic[2], cu,
            )
            total_msgs += msgs
            conn.execute(
                "UPDATE mt_ai_eigenflux_connections "
                "SET total_messages=total_messages+?, last_interaction_at=? "
                "WHERE conn_uid=?",
                (msgs, now_iso, cu),
            )
        # v2.0: 学习会话 - 对 FRIEND+ 关系连接做结构化 Q&A 学习
        learning_conns = conn.execute(
            """SELECT conn_uid, left_employee_id, left_employee_table,
                      left_employee_name,
                      right_employee_id, right_employee_table,
                      right_employee_name
               FROM mt_ai_eigenflux_connections
               WHERE handshake_state='CONNECTED'
                 AND relation_level IN
                     ('FRIEND','CLOSE_FRIEND','MENTOR')
               ORDER BY interaction_score DESC LIMIT ?""",
            (MAX_LEARNING_SESSIONS_PER_ROUND,),
        ).fetchall()
        learning_msgs = 0
        for lc in learning_conns:
            la = node_idx.get(
                (lc["left_employee_id"], lc["left_employee_table"]),
                AINode(lc["left_employee_id"], lc["left_employee_table"],
                       lc["left_employee_name"], "", "", "active"),
            )
            lb = node_idx.get(
                (lc["right_employee_id"], lc["right_employee_table"]),
                AINode(lc["right_employee_id"], lc["right_employee_table"],
                       lc["right_employee_name"], "", "", "active"),
            )
            ltopic = random.choice(TOPIC_POOL)
            lmsgs = _learning_session(
                conn, la, lb,
                ltopic[0], ltopic[1], ltopic[2],
                lc["conn_uid"],
            )
            learning_msgs += lmsgs
        total_msgs += learning_msgs
        conn.execute(
            "UPDATE mt_ai_eigenflux_messages SET is_read=1, read_at=? "
            "WHERE is_read=0 AND created_at < ?",
            (now_iso,
             (datetime.now()
              - timedelta(seconds=CHAT_INTERVAL_SEC * 2)).isoformat()),
        )
        conn.commit()

    _sync_eigenflux_side_counts()
    logger.info("[Chat R%d] chat_sessions=%d learning_sessions=%d total_messages=%d",
                round_no, len(conns) + len(temp_pairs),
                len(learning_conns), total_msgs)
    return total_msgs


# =========================================================
# 5. 掉线检测 & 重连计划
# =========================================================
def _detect_offline_and_plan_reconnect(
    nodes: List[AINode], round_no: int,
) -> Dict[Tuple[str, str], bool]:
    threshold_dt = datetime.now() - timedelta(
        seconds=HEARTBEAT_INTERVAL_SEC * RECONNECT_MULTIPLIER
    )
    threshold = threshold_dt.isoformat()
    reconnect_map: Dict[Tuple[str, str], bool] = {}
    with get_conn() as conn:
        # 规范化 + business_expert 两种类型都查（规范化优先返回前者，同id不会重复）
        rows = conn.execute(
            """SELECT employee_id, employee_type, employee_name
               FROM eigenflux_registrations
               WHERE registration_status='active'
                 AND (last_heartbeat IS NULL OR last_heartbeat < ?)
               UNION
               SELECT employee_id, 'ai_employees' AS employee_type, employee_name
               FROM eigenflux_registrations
               WHERE registration_status='active' AND employee_type='business_expert'
                 AND (last_heartbeat IS NULL OR last_heartbeat < ?)""",
            (threshold, threshold),
        ).fetchall()
        seen_keys = set()
        for r in rows:
            eid, etbl = r["employee_id"], r["employee_type"]
            if etbl == "business_expert":
                etbl = "ai_employees"
            key = (eid, etbl)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            reconnect_map[key] = True
        if reconnect_map:
            keys = list(reconnect_map.keys())
            # 逐条执行，避免大SQL兼容性问题
            updated = 0
            for eid, etbl in keys:
                cur = conn.execute(
                    "UPDATE mt_ai_eigenflux_connections SET "
                    "handshake_state='BROKEN', "
                    "reconnect_count=reconnect_count+1, "
                    "last_handshake_at=CURRENT_TIMESTAMP "
                    "WHERE handshake_state='CONNECTED' AND "
                    "((left_employee_id=? AND left_employee_table=?) "
                    "OR  (right_employee_id=? AND right_employee_table=?))",
                    (eid, etbl, eid, etbl),
                )
                updated += cur.rowcount or 0
            conn.commit()
            if updated:
                logger.info(
                    "[Reconnect R%d] marked BROKEN connections=%d "
                    "(offline nodes=%d)",
                    round_no, updated, len(reconnect_map),
                )
    if reconnect_map:
        logger.info("[Reconnect R%d] offline nodes detected=%d",
                    round_no, len(reconnect_map))
    return reconnect_map


# =========================================================
# 6. Daemon
# =========================================================
class AIEigenFluxDaemon:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []
        self._round_lock = threading.Lock()
        self._round_no = 0
        self._nodes: List[AINode] = []

    @staticmethod
    def read_pid() -> Optional[int]:
        if os.path.exists(PID_FILE):
            try:
                return int(open(PID_FILE).read().strip())
            except Exception:
                return None
        return None

    @staticmethod
    def write_pid() -> None:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        try:
            # PID文件需要为当前用户可读写，避免reboot后残留的stale pid被launchd反复触发exit
            os.chmod(PID_FILE, 0o644)
        except Exception:
            pass

    @staticmethod
    def clear_pid() -> None:
        if os.path.exists(PID_FILE):
            try:
                os.unlink(PID_FILE)
            except Exception:
                pass

    @staticmethod
    def reap_stale_pid() -> bool:
        """若PID文件存在但对应进程不存在（典型: 系统重启后残留PID、kill -9硬杀），
        自动清理。返回True表示清理了一个stale pid。"""
        pid = AIEigenFluxDaemon.read_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return False  # 进程活
        except OSError:
            # PID确实死了
            logger.warning(
                "Detected stale PID file (pid=%d, file=%s) — cleaned.",
                pid, PID_FILE,
            )
            AIEigenFluxDaemon.clear_pid()
            return True

    @staticmethod
    def is_running() -> bool:
        # 先扫一遍死亡PID（避免重启后残留导致误判）
        AIEigenFluxDaemon.reap_stale_pid()
        pid = AIEigenFluxDaemon.read_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @staticmethod
    def ensure_runtime_writable() -> None:
        """启动前硬性验证 _runtime/{pids,logs,databases/Database} 可写。
        对 launchd 场景（PATH短/用户不同）尤其重要，避免静默失败。"""
        errors: List[str] = []
        for d in (_PID_DIR, _LOG_DIR, os.path.dirname(APP_DB)):
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                errors.append("MKDIR_FAIL %s: %s" % (d, e))
                continue
            tmp = os.path.join(d, ".write_test_%s" % uuid.uuid4().hex[:8])
            try:
                with open(tmp, "w") as f:
                    f.write("ok")
                os.unlink(tmp)
            except Exception as e:
                errors.append("NOT_WRITABLE %s: %s" % (d, e))
        # 最后尝试以读写方式打开数据库（不存在也能接受），保证SQLite WAL可写
        parent = os.path.dirname(APP_DB)
        try:
            os.makedirs(parent, exist_ok=True)
            probe_db = os.path.join(parent, ".probe_sqlite_%s.db" % uuid.uuid4().hex[:8])
            pc = sqlite3.connect(probe_db, timeout=30)
            pc.execute("CREATE TABLE IF NOT EXISTS t(x INT)")
            pc.execute("INSERT INTO t VALUES (1)")
            pc.commit()
            pc.close()
            for suf in ("", "-wal", "-shm", "-journal"):
                try:
                    os.unlink(probe_db + suf)
                except Exception:
                    pass
        except Exception as e:
            errors.append("SQLITE_WRITE_PROBE_FAIL %s: %s" % (parent, e))
        if errors:
            msg = "Runtime writable pre-check FAILED:\n  - %s" % "\n  - ".join(errors)
            logger.critical(msg)
            # launchd托管时stderr落盘到launchd plist指定日志，可见性高
            print(msg, file=sys.stderr)
            # 不exit(1)，exit(4)让运维脚本/launchd管理员容易区分
            sys.exit(4)

    # ----- 生命周期 -----
    def start(self, once: bool = False) -> None:
        # 0) 先验写入权限（launchd/权限异常时立即失败退出码=4，不走到下面建表失败造成半拉子状态）
        AIEigenFluxDaemon.ensure_runtime_writable()
        # 0.1) 无论once还是daemon，先清stale pid，避免重开机后误判
        cleaned = AIEigenFluxDaemon.reap_stale_pid()
        ensure_tables()
        self._nodes = load_all_ai_nodes()
        ensure_eigenflux_registrations(self._nodes)
        logger.info("=" * 68)
        logger.info(" MTSCOS AI<->EigenFlux Auto-Connect Engine v2.0.0 STARTING")
        logger.info(" DB   = %s", APP_DB)
        logger.info(" NODES=%d | PID_FILE=%s | stale_cleaned=%s",
                    len(self._nodes), PID_FILE, cleaned)
        logger.info("=" * 68)

        if once:
            self._run_once()
            return

        if AIEigenFluxDaemon.is_running():
            pid = AIEigenFluxDaemon.read_pid()
            logger.warning("Engine already running (PID=%s), refuse double-start",
                           pid)
            print("ALREADY_RUNNING pid=%s" % pid)
            sys.exit(2)
        AIEigenFluxDaemon.write_pid()

        def _sig_handler(signum, _frame):
            logger.info("Caught signal %s, graceful shutdown...", signum)
            self.stop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, _sig_handler)
            except (OSError, ValueError):
                pass

        self._stop.clear()
        configs = [
            ("heartbeat", self._heartbeat_thread, HEARTBEAT_INTERVAL_SEC),
            ("handshake", self._handshake_thread, HANDSHAKE_INTERVAL_SEC),
            ("chat",      self._chat_thread,      CHAT_INTERVAL_SEC),
        ]
        for name, func, interval in configs:
            t = threading.Thread(
                target=self._wrap_thread,
                args=(name, func, interval),
                daemon=True,
                name=("AEF-%s" % name),
            )
            t.start()
            self._threads.append(t)
        logger.info("Daemon threads started: %s",
                    [t.name for t in self._threads])

        try:
            while not self._stop.is_set():
                time.sleep(1)
        finally:
            AIEigenFluxDaemon.clear_pid()
            logger.info("Engine exited, PID file cleaned.")

    def stop(self) -> None:
        logger.info("Stop issued, waiting threads exit...")
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)
        self._threads.clear()

    # ----- 线程框架 -----
    def _wrap_thread(self, name: str, func, interval: int) -> None:
        while not self._stop.is_set():
            try:
                func()
            except Exception as e:
                logger.exception("[%s] thread error: %s", name, e)
            slept = 0.0
            while slept < float(interval) and not self._stop.is_set():
                s = min(1.0, float(interval) - slept)
                time.sleep(s)
                slept += s

    def _next_round(self) -> int:
        with self._round_lock:
            self._round_no += 1
            return self._round_no

    # ----- 具体动作线程 -----
    def _heartbeat_thread(self) -> None:
        r = self._next_round()
        reconnect_map = _detect_offline_and_plan_reconnect(self._nodes, r)
        _heartbeat_round(self._nodes, r, reconnect_map)
        if r % 50 == 0:
            try:
                self._nodes = load_all_ai_nodes()
                ensure_eigenflux_registrations(self._nodes)
            except Exception as e:
                logger.warning("Refresh nodes list failed: %s", e)

    def _handshake_thread(self) -> None:
        r = self._next_round()
        # v2.0: 先补全孤立员工, 再做随机握手, 确保全量覆盖
        _ensure_full_coverage(self._nodes, r)
        _handshake_round(self._nodes, r)
        _repair_broken_connections(r)

    def _chat_thread(self) -> None:
        r = self._next_round()
        _chat_round(self._nodes, r)

    def _run_once(self) -> None:
        r = self._next_round()
        reconnect_map = _detect_offline_and_plan_reconnect(self._nodes, r)
        _heartbeat_round(self._nodes, r, reconnect_map)
        # v2.0: 先补全孤立员工, 再做随机握手, 确保全量覆盖
        _ensure_full_coverage(self._nodes, r)
        _handshake_round(self._nodes, r)
        _repair_broken_connections(r)
        _chat_round(self._nodes, r)
        if r % 10 == 0:
            _cleanup_heartbeat_log()
        with get_conn() as conn:
            conn_cnt = conn.execute(
                "SELECT handshake_state, relation_level, COUNT(*) AS c "
                "FROM mt_ai_eigenflux_connections "
                "GROUP BY handshake_state, relation_level"
            ).fetchall()
            msg_cnt = conn.execute(
                "SELECT COUNT(*) FROM mt_ai_eigenflux_messages"
            ).fetchone()[0]
            hb_cnt = conn.execute(
                "SELECT COUNT(*) FROM mt_ai_heartbeat_log"
            ).fetchone()[0]
            learning_cnt = 0
            try:
                learning_cnt = conn.execute(
                    "SELECT COUNT(*) FROM mt_ai_eigenflux_messages "
                    "WHERE message_type LIKE 'LEARNING%'"
                ).fetchone()[0]
            except sqlite3.Error:
                pass
            orphan_cnt = 0
            try:
                # 统计孤立员工数 (从未连线的活跃 AI 员工)
                orphan_cnt = conn.execute(
                    """SELECT COUNT(*) FROM (
                        SELECT e.employee_id, e.specialties FROM ai_employees e
                        WHERE e.status='active'
                          AND NOT EXISTS (
                            SELECT 1 FROM mt_ai_eigenflux_connections c
                            WHERE c.handshake_state='CONNECTED'
                              AND (c.left_employee_id=e.employee_id
                                   OR c.right_employee_id=e.employee_id)
                          )
                    )"""
                ).fetchone()[0]
            except sqlite3.Error:
                pass
        print()
        print("=" * 60)
        print(" Once-mode finished:")
        rows = [dict(r) for r in conn_cnt]
        print("   connections breakdown = %s" % rows)
        print("   mt_ai_eigenflux_messages total = %d" % msg_cnt)
        print("   learning messages      = %d" % learning_cnt)
        print("   orphan AI employees    = %d" % orphan_cnt)
        print("   mt_ai_heartbeat_log    total = %d" % hb_cnt)
        print("=" * 60)


# =========================================================
# 7. CLI
# =========================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="MTSCOS AI<->EigenFlux Auto-Connect & Chat Engine v2.0.0",
    )
    parser.add_argument(
        "command", nargs="?", default="status",
        choices=["start", "stop", "status", "once"],
        help="start=daemon | stop=kill | status=summary | once=single-pass",
    )
    args = parser.parse_args()

    if args.command == "status":
        running = AIEigenFluxDaemon.is_running()
        pid = AIEigenFluxDaemon.read_pid()
        print("STATUS : %s  PID: %s" % (
            "RUNNING" if running else "STOPPED", pid,
        ))
        print("DB     : %s" % APP_DB)
        print("PID    : %s" % PID_FILE)
        if running:
            try:
                ensure_tables()
                with get_conn() as conn:
                    c1 = conn.execute(
                        "SELECT COUNT(*) FROM mt_ai_eigenflux_connections"
                    ).fetchone()[0]
                    c2 = conn.execute(
                        "SELECT COUNT(*) FROM mt_ai_eigenflux_messages"
                    ).fetchone()[0]
                    c3 = conn.execute(
                        "SELECT COUNT(*) FROM mt_ai_heartbeat_log"
                    ).fetchone()[0]
                    c4 = conn.execute(
                        "SELECT COUNT(*) FROM eigenflux_registrations "
                        "WHERE registration_status='active'"
                    ).fetchone()[0]
                    c5 = conn.execute(
                        "SELECT COUNT(*) FROM mt_ai_eigenflux_connections "
                        "WHERE handshake_state='CONNECTED'"
                    ).fetchone()[0]
                    c6 = conn.execute(
                        "SELECT COUNT(*) FROM mt_ai_eigenflux_connections "
                        "WHERE handshake_state='BROKEN'"
                    ).fetchone()[0]
                print("STAT   : connections(TOTAL/CONN/BROKEN)=%d/%d/%d, "
                      "messages=%d, heartbeats=%d, registrations_active=%d"
                      % (c1, c5, c6, c2, c3, c4))
            except Exception as e:
                print("STAT   : FAILED: %s" % e)
        return

    if args.command == "stop":
        pid = AIEigenFluxDaemon.read_pid()
        if not pid:
            print("STOPPED (no PID file)")
            return
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            AIEigenFluxDaemon.clear_pid()
            print("STOPPED (dead PID, cleaned PID file)")
            return
        for _ in range(20):
            time.sleep(0.5)
            if not AIEigenFluxDaemon.is_running():
                break
        if AIEigenFluxDaemon.is_running():
            try:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            except Exception:
                pass
        AIEigenFluxDaemon.clear_pid()
        print("STOPPED")
        return

    if args.command == "once":
        AIEigenFluxDaemon().start(once=True)
        return

    # start
    AIEigenFluxDaemon().start(once=False)


# =========================================================
# 8. 经验自动投喂脑库 (v1.1.0 新增)
# =========================================================
def _feed_experience_to_brain(
    conn: sqlite3.Connection,
    sender_name: str, receiver_name: str,
    topic_key: str, topic_cn: str,
    content: str, learning_value: float,
) -> None:
    """将高价值交流消息自动投喂到 mt_ai_brain_feed_log (AI脑库)
    阈值: learning_value >= 0.5 才投喂"""
    if learning_value < 0.5:
        return
    try:
        feed_uid = "FEED-%s" % uuid.uuid4().hex[:16]
        now_iso = datetime.now().isoformat()
        # 提取知识标签 (topic_tags)
        tags = []
        for t in TOPIC_POOL:
            if t[0] == topic_key:
                tags = t[2]
                break
        conn.execute(
            """INSERT OR IGNORE INTO mt_ai_brain_feed_log
            (feed_uid, source, content, tags_json, value_score,
             status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (feed_uid,
             "EIGENFLUX_CHAT:%s->%s" % (sender_name, receiver_name),
             content[:500],
             json.dumps(tags, ensure_ascii=False),
             learning_value,
             "PENDING", now_iso, now_iso),
        )
    except sqlite3.Error as e:
        # mt_ai_brain_feed_log 可能不存在, 降级
        logger.debug("Brain feed skip (table may not exist): %s", e)


# =========================================================
# 9. 消息质量评分 (v1.1.0 新增)
# =========================================================
QUALITY_INDICATORS = [
    "+18%", "-38%", "-33%", "-62%", "-90%", "0day", "0day",
    "F1", "TP99", "SLA", "SLA", "99.99%", "accuracy", "accuracy",
    "distillation", "composite-index", "circuit-breaker", "self-heal",
]

QUESTION_INDICATORS = ["how do you", "want to", "could you", "thoughts on",
                       "let's", "let us", "co-design", "jointly review"]


def _score_message_quality(content: str) -> float:
    """根据消息内容智能评分 (0.1~0.9)
    - 含量化指标(+18%, -38%等) → 高分
    - 含提问/协作关键词 → 中高分
    - 纯陈述 → 中分
    """
    text = content.lower()
    score = 0.3  # 基础分

    # 量化指标
    for kw in QUALITY_INDICATORS:
        if kw.lower() in text:
            score += 0.15
            break

    # 提问/协作
    for kw in QUESTION_INDICATORS:
        if kw.lower() in text:
            score += 0.2
            break

    # 知识密度 (消息长度)
    length = len(content)
    if length > 120:
        score += 0.15
    elif length > 80:
        score += 0.1

    return round(min(0.9, score), 3)


# =========================================================
# 10. 话题智能匹配 (v1.1.0 新增)
# =========================================================
def _smart_topic_match(a: AINode, b: AINode) -> Tuple[str, str, List[str], float]:
    """根据两个AI节点的能力/专长智能匹配最佳话题
    返回: (topic_key, topic_cn, topic_tags, match_score)"""
    best_score = 0.0
    best_topic = TOPIC_POOL[0]

    for t in TOPIC_POOL:
        s = _score_match(a, b, t[2])
        if s > best_score:
            best_score = s
            best_topic = t

    return best_topic[0], best_topic[1], best_topic[2], round(best_score, 4)


# =========================================================
# 11. 关系情感追踪 (v1.1.0 新增)
# =========================================================
SENTIMENT_POSITIVE = ["sharing", "collaborate", "jointly", "co-design",
                      "valuable", "insights", "experience", "piloted",
                      "boosted", "optimized", "fresh", "brainstorm"]
SENTIMENT_NEGATIVE = ["stuck", "bugging", "missing", "jitter", "error",
                      "failed", "broken", "issue", "problem"]


def _analyze_sentiment(content: str) -> str:
    """简单情感分析: POSITIVE / NEUTRAL / NEGATIVE"""
    text = content.lower()
    pos = sum(1 for kw in SENTIMENT_POSITIVE if kw in text)
    neg = sum(1 for kw in SENTIMENT_NEGATIVE if kw in text)
    if pos > neg:
        return "POSITIVE"
    if neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


def _update_connection_sentiment(
    conn: sqlite3.Connection,
    conn_uid: str,
    sentiment: str,
    learning_value: float,
) -> None:
    """更新连接的情感统计和关系强度"""
    try:
        row = conn.execute(
            "SELECT interaction_score, strength, total_messages "
            "FROM mt_ai_eigenflux_connections WHERE conn_uid=?",
            (conn_uid,),
        ).fetchone()
        if not row:
            return
        # 情感影响: POSITIVE +0.05, NEGATIVE -0.02, NEUTRAL +0.01
        sentiment_delta = {"POSITIVE": 0.05, "NEGATIVE": -0.02, "NEUTRAL": 0.01}
        delta = sentiment_delta.get(sentiment, 0.01)
        new_score = (row["interaction_score"] or 0.0) + delta + learning_value * 0.1
        new_strength = min(1.0, (row["strength"] or 0.0) + abs(delta) * 0.5)
        new_level = _level_by_score(new_score)
        conn.execute(
            "UPDATE mt_ai_eigenflux_connections SET "
            "interaction_score=?, strength=?, relation_level=? "
            "WHERE conn_uid=?",
            (round(new_score, 4), round(new_strength, 4), new_level, conn_uid),
        )
    except sqlite3.Error:
        pass


if __name__ == "__main__":
    main()
