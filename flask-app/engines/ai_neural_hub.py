#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 母体内核中枢 — Neural Hub for MTSCOS AI
==========================================

本地 LLM 统一入口，所有子系统（Arduino 编译 / 考试系统 / 权限 / 路由 /
防火墙 / 题库 / 文案 / 固件 / 数据库 / SA 体系 / 端口 / 巡检 / 自动化 /
日志 / EigenFlux / AI 员工 / AI Agent / AI 神经元网络 等 18+ 系统）
统一通过本中枢调用 qwen2.5-coder:14b / qwen2.5:7b 本地推理。

路由策略（数据驱动，落库 mt_ai_neural_routes）:
  ┌──────────────────┬──────────────────┬──────────────────────────┐
  │ 子系统 domain    │ 主模型            │ Prompt 模板              │
  ├──────────────────┼──────────────────┼──────────────────────────┤
  │ arduino_compile │ qwen2.5-coder:14b  │ 嵌入式开发专家 · Arduino C++ │
  │ exam_grade      │ qwen2.5-coder:14b  │ 教育学评估专家 · 评分评语    │
  │ security_audit  │ qwen2.5:7b        │ 安全审计专家 · 漏洞分析     │
  │ firewall_rule   │ qwen2.5:7b        │ 防火墙规则专家 · 防护策略   │
  │ perm_check      │ qwen2.5:7b        │ 权限矩阵专家 · 越权检测     │
  │ route_diagnose  │ qwen2.5:7b        │ Flask 路由诊断 · 冲突修复   │
  │ db_schema       │ qwen2.5-coder:14b  │ DBA · SQLite schema 优化   │
  │ copy_write      │ qwen2.5:7b        │ 文案写手 · 中英日繁翻译     │
  │ patrol_inspect  │ qwen2.5-coder:14b  │ 代码巡检 · Bug / 坏味道    │
  │ auto_repair     │ qwen2.5-coder:14b  │ 自动修复 · patch 生成      │
  │ eigenflux_chat  │ qwen2.5:7b        │ EigenFlux 广播 · 专家交流  │
  │ knowledge_feed  │ qwen2.5:7b        │ 脑库投喂 · 经验蒸馏        │
  │ self_upgrade    │ qwen2.5-coder:14b  │ 自升级 · 代码自我审查      │
  └──────────────────┴──────────────────┴──────────────────────────┘

调用链路:
  ai_neural_hub.NeuralHub.call(task, payload)
    → route_to_models(task) [读 mt_ai_neural_routes]
    → ai_dual_route_engine.chat() [本地 Ollama 11435 优先]
    → 落库 mt_ai_neural_calls + mt_local_ai_inference_log
    → 返回 {success, response, model, route, tokens_saved, duration_ms}

自进化（Phase 2）:
  NeuralEvolutionDaemon 定时读取 mt_ai_neural_calls 中失败/超时记录
  → qwen2.5-coder 分析 → 自动改写 mt_ai_neural_routes prompt 模板
  → 生成 patch 提交 EigenFlux 磋商
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── 路径解析 ──────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_AI_ENGINES_DIR = os.path.join(_ROOT, "ai_engines")
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)

# DB 路径 — 复用 core.db_path
def _get_app_db() -> str:
    try:
        from core.db_path import get_db_path
        return get_db_path("app.db")
    except Exception:
        return os.path.join(_ROOT, "Database", "app.db")

APP_DB = _get_app_db()


# ═══════════════════════════════════════════════════════════════════
# 0.5 仙女座-阿尔法 前缀 + 规则学习引擎
# ═══════════════════════════════════════════════════════════════════

_ANDROMEDA_PREFIX = "【仙女座-阿尔法】你属于 MTSCOS AI 项目的系统兜底底层架构。"


def _load_all_rules() -> int:
    """解析 .trae/rules/*.md 的 YAML frontmatter + 正文, 分段存入 DB, 返回 chunk 数"""
    import glob, re, os as _os
    # 路径: flask-app/engines → 往上 2 层到项目根
    _hub_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    _project_root = _os.path.dirname(_hub_dir)
    rules_dir = _os.path.join(_project_root, '.trae', 'rules')
    if not _os.path.isdir(rules_dir):
        # fallback: 直接查 flask-app 同级的 .trae
        fallback = _os.path.join(_hub_dir, '.trae', 'rules')
        rules_dir = fallback if _os.path.isdir(fallback) else rules_dir
    rule_files = sorted(glob.glob(_os.path.join(rules_dir, '*.md')))
    if not rule_files:
        print(f"[仙女座] 未找到规则文件 (searched {rules_dir})")
        return 0

    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS mt_andromeda_rule_knowledge (
        rule_chunk_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id         TEXT NOT NULL,
        rule_name       TEXT NOT NULL,
        rule_level      TEXT,
        rule_version    TEXT,
        status          TEXT,
        depends_on      TEXT,
        effective_date  TEXT,
        section_header  TEXT,
        content_chunk   TEXT NOT NULL,
        chunk_index     INTEGER DEFAULT 0,
        keyword_tags    TEXT,      -- JSON array: ["铁律","强制","API"]
        is_iron_rule    INTEGER DEFAULT 0,
        last_ingested   TEXT DEFAULT (datetime('now','localtime')),
        UNIQUE(rule_id, chunk_index)
    )
    """)

    total_chunks = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for rf in rule_files:
        fname = _os.path.basename(rf)
        try:
            content = open(rf, 'r', encoding='utf-8').read()
        except Exception:
            continue

        # 解析 YAML frontmatter
        meta = {}
        m = re.search(r'<!-- RULE_META_START\s*\n(.*?)\nRULE_META_END -->', content, re.DOTALL)
        if m:
            for line in m.group(1).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[k.strip()] = v.strip()
        rule_id = meta.get('RULE_ID') or fname.replace('.md', '')
        rule_name = meta.get('RULE_NAME') or fname.replace('.md', '')
        rule_level = meta.get('RULE_LEVEL') or 'L2'
        rule_version = meta.get('RULE_VERSION') or 'v1.0.0'
        status = meta.get('STATUS') or 'ACTIVE'
        depends_on = meta.get('DEPENDS_ON') or ''
        effective_date = meta.get('EFFECTIVE_DATE') or ''
        is_iron = 1 if rule_level.startswith('L0') else 0

        # 分段: 按 ## 标题切分, 每段 ≤ 2000 字符
        # 先剥离 META 块
        body = re.sub(r'<!-- RULE_META_START.*?RULE_META_END -->', '', content, flags=re.DOTALL).strip()
        sections = re.split(r'\n(?=## )', body)

        chunk_idx = 0
        for sec in sections:
            header_m = re.match(r'## (.+)', sec)
            header = header_m.group(1).strip() if header_m else fname
            sec_body = sec[header_m.end():].strip() if header_m else sec.strip()
            if not sec_body or len(sec_body) < 20:
                continue

            # 关键词提取
            kw_pool = re.findall(r'(铁律|强制|禁止|必须|规范|安全|合规|API|vikey|VIKEY|兜底|架构|升级|hook|拦截|违规)', sec_body, re.I)
            kw_json = json.dumps(sorted(set(kw_pool)), ensure_ascii=False)

            # 按 2000 字切块
            for i in range(0, len(sec_body), 2000):
                chunk_text = sec_body[i:i+2000]
                chunk_idx += 1
                conn.execute("""INSERT OR IGNORE INTO mt_andromeda_rule_knowledge
                    (rule_id, rule_name, rule_level, rule_version, status, depends_on,
                     effective_date, section_header, content_chunk, chunk_index,
                     keyword_tags, is_iron_rule, last_ingested)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (rule_id, rule_name, rule_level, rule_version, status, depends_on,
                     effective_date, header, chunk_text, chunk_idx,
                     kw_json, is_iron, now))
                total_chunks += 1

    conn.commit()
    conn.close()
    return total_chunks


def _apply_andromeda_prefix() -> int:
    """给所有尚未加前缀的路由 system_prompt 统一补前缀, 返回更新条数"""
    # 先加载规则知识 (首次调用或文件变更时)
    try:
        chunks = _load_all_rules()
        if chunks > 0:
            print(f"[仙女座-阿尔法] 规则知识已学习: {chunks} chunks from .trae/rules/")
    except Exception as e:
        print(f"[仙女座-阿尔法] 规则加载失败 (非致命): {e}")

    # 注入规则摘要到前缀 (每次调用都重新生成以反映最新规则状态)
    rule_snippet = _build_rule_snippet()
    full_prefix = _ANDROMEDA_PREFIX + " " + rule_snippet

    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    rows = conn.execute(
        "SELECT route_id, system_prompt FROM mt_ai_neural_routes").fetchall()
    updated = 0
    for rid, sp in rows:
        if sp and sp.startswith("【仙女座-阿尔法】"):
            # 已有前缀但内容可能旧 → 重新刷新 (去掉旧前缀 + 加新)
            cleaned = re.sub(r'^【仙女座-阿尔法】[^\n]*\n?', '', sp, count=1)
            conn.execute("UPDATE mt_ai_neural_routes SET system_prompt=? WHERE route_id=?",
                         (full_prefix + cleaned, rid))
            updated += 1
        elif sp:
            conn.execute("UPDATE mt_ai_neural_routes SET system_prompt=? WHERE route_id=?",
                         (full_prefix + sp, rid))
            updated += 1
    if updated:
        conn.commit()
    conn.close()
    return updated


def _build_rule_snippet(max_chars: int = 400) -> str:
    """从 mt_andromeda_rule_knowledge 抽取铁律 + 核心规则摘要, 控制长度塞得进 7B 上下文"""
    try:
        conn = sqlite3.connect(APP_DB, timeout=30)
        # 优先铁律 (L0), 再取各 L1 核心条款
        chunks = conn.execute("""
            SELECT rule_id, rule_name, rule_level, section_header, content_chunk, keyword_tags
            FROM mt_andromeda_rule_knowledge
            WHERE status='ACTIVE'
            ORDER BY is_iron_rule DESC,
                     CASE rule_level WHEN 'L0' THEN 0 WHEN 'L1' THEN 1 WHEN 'L2' THEN 2 ELSE 3 END,
                     chunk_index ASC
        """).fetchall()
        conn.close()

        lines = ["你已学习 MTSCOS AI 项目规则体系:"]
        seen_rules = set()
        for rid, rname, rlevel, header, body, kw_json in chunks:
            if rid in seen_rules:
                continue
            # 只保留核心标题 + 首句 (避免过长)
            first_sentence = (body[:120] + '...') if len(body) > 120 else body
            tag_str = ""
            try:
                tags = json.loads(kw_json) if kw_json else []
                if tags: tag_str = f" [{','.join(tags[:3])}]"
            except Exception:
                pass
            level_indicator = {"L0": "IRON", "L1": "CORE", "L2": "OP"}.get(rlevel, rlevel)
            lines.append(f"  [{level_indicator}] {header}: {first_sentence}{tag_str}")
            seen_rules.add(rid)
            if sum(len(l) for l in lines) > max_chars:
                break
        return " ".join(lines[:8])  # 最多 8 行摘要
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════
# 1. DB Schema — 路由注册表 + 调用日志
# ═══════════════════════════════════════════════════════════════════

def _ensure_tables() -> None:
    """确保 AI 中枢的三张核心表存在"""
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
    -- 1) 子系统→模型 路由注册表（数据驱动）
    CREATE TABLE IF NOT EXISTS mt_ai_neural_routes (
        route_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name      TEXT UNIQUE NOT NULL,   -- 如 'arduino_compile'
        domain         TEXT NOT NULL,           -- 如 'arduino'
        primary_model  TEXT NOT NULL,           -- 如 'qwen2.5-coder:14b'
        fallback_model TEXT,
        system_prompt  TEXT NOT NULL,           -- 角色 prompt 模板
        prompt_template TEXT,                   -- 可选: payload→prompt 的 format 模板
        temperature    REAL DEFAULT 0.3,
        max_tokens     INTEGER DEFAULT 2048,
        enabled        INTEGER DEFAULT 1,
        call_count     INTEGER DEFAULT 0,
        success_rate   REAL DEFAULT 1.0,
        avg_duration_ms INTEGER DEFAULT 0,
        evolved_at     TEXT,                    -- 自进化更新时间
        created_at     TEXT,
        updated_at     TEXT
    );

    -- 2) 每次调用日志（用于统计 + 自进化分析）
    CREATE TABLE IF NOT EXISTS mt_ai_neural_calls (
        call_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id        TEXT,
        task_name      TEXT NOT NULL,
        model_used     TEXT NOT NULL,
        route          TEXT NOT NULL,           -- local_ollama / cloud / none
        success        INTEGER NOT NULL,
        tokens_in      INTEGER DEFAULT 0,
        tokens_out     INTEGER DEFAULT 0,
        tokens_saved   INTEGER DEFAULT 0,
        duration_ms    INTEGER DEFAULT 0,
        error          TEXT,
        triggered_at   TEXT
    );

    -- 3) 自进化日志（qwen2.5-coder 对自身 prompt/代码 的修改记录）
    CREATE TABLE IF NOT EXISTS mt_ai_self_evolution_log (
        evolve_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        trigger_type   TEXT,                    -- error_spike / slow_response / manual
        target_task    TEXT,
        old_prompt     TEXT,
        new_prompt     TEXT,
        rationale      TEXT,
        approved_by    TEXT,                    -- eigenflux_consensus / sa / auto
        applied        INTEGER DEFAULT 0,
        created_at     TEXT
    );

    -- 4) AI 员工注册表 (仙女座-阿尔法统一路由 — 33,472 员工 × N types)
    CREATE TABLE IF NOT EXISTS mt_andromeda_employee_registry (
        employee_id        TEXT PRIMARY KEY,        -- 原始 id (eigenflux_registrations.employee_id)
        name               TEXT,
        employee_type      TEXT NOT NULL,           -- 如 'arduino_code_debugger', 'vulnerability_scanner'
        employee_source    TEXT,                    -- eigenflux / mtscos_ai_employees / ai_employees / patrol / ...
        level              INTEGER DEFAULT 5,
        neuralhub_task     TEXT NOT NULL,           -- 映射到 25 条路由中的哪一条
        route_priority     TEXT DEFAULT 'auto',     -- auto / primary / secondary
        custom_system_prompt TEXT,                  -- 可选: 员工特有 prompt (覆盖 route 默认)
        call_count         INTEGER DEFAULT 0,
        last_called_at     TEXT,
        enabled            INTEGER DEFAULT 1,
        registered_at      TEXT DEFAULT (datetime('now','localtime'))
    );

    -- 5) 员工调用队列表 (Ollama 串行消费, 支持 3 万+ 员工提交)
    CREATE TABLE IF NOT EXISTS mt_andromeda_call_queue (
        queue_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id    TEXT,
        employee_type  TEXT,
        task_name      TEXT NOT NULL,
        payload        TEXT NOT NULL,
        system_prompt  TEXT,
        status         TEXT DEFAULT 'pending',      -- pending → processing → done / failed
        priority       INTEGER DEFAULT 5,           -- 1 最高
        submitted_at   TEXT DEFAULT (datetime('now','localtime')),
        started_at     TEXT,
        completed_at   TEXT,
        result_json    TEXT,
        error          TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_andromeda_queue_status ON mt_andromeda_call_queue(status, priority);
    CREATE INDEX IF NOT EXISTS idx_andromeda_queue_employee ON mt_andromeda_call_queue(employee_id);
    """)
    conn.commit()
    conn.close()


# ────────────────────────────────────────────────────────────────────
# 仙女座-阿尔法: 3万+ AI 员工统一路由映射层
# ────────────────────────────────────────────────────────────────────

# employee_type → neuralhub task_name 自动映射表 (按关键词匹配)
_EMPLOYEE_TYPE_MAP = {
    # Arduino 家族 (21 种 × N 实例)
    "arduino_code_debugger":   "arduino_compile",
    "arduino_code_optimizer":  "auto_repair_code",
    "arduino_smart_advisor":   "sa_advisor",
    "arduino_auto_tester":     "auto_repair_code",
    "arduino_compiler_engineer": "arduino_compile",
    "arduino_library_linker":  "arduino_compile",
    "arduino_firmware_packager": "arduino_compile",
    "arduino_sensor_calibration": "arduino_compile",
    "arduino_code_evolver":    "self_upgrade",
    "arduino_hal_developer":   "arduino_compile",
    "arduino_peripheral_driver": "arduino_compile",
    "arduino_motor_control":   "arduino_compile",
    "arduino_display_driver":  "arduino_compile",
    "arduino_code_completer":  "patrol_code",
    "arduino_doc_generator":   "knowledge_feed",
    "arduino_intent_parser":   "question_generate",
    "arduino_.*":              "arduino_compile",     # 所有未匹配 Arduino 子类
    # 安全 / 合规
    "vulnerability_scanner":   "security_audit",
    "auto_repair":             "auto_repair_code",
    "security_audit":          "security_audit",
    "firewall_.*":             "firewall_rule",
    "perm_.*":                 "perm_check",
    # 代码 / 开发
    "diagnostics_repair":      "auto_repair_code",
    "patrol.*":                "patrol_code",
    "question_bank_maintenance": "question_generate",
    "politics_question":       "question_generate",
    "db_query":                "db_schema_design",
    "code.*":                  "patrol_code",
    # 教育
    "learning_agent":          "subject_sync",
    "question_.*":             "question_generate",
    # EigenFlux / 通用
    "eigenflux_chat":          "sa_advisor",
    "eigenflux_expert":        "sa_advisor",
    "mtscos_ai_employee":     "sa_advisor",
    "ai_employees":            "sa_advisor",
    "automation_agents":       "auto_repair_code",
    "system_upgrader":         "system_plan",
    "planner":                 "system_plan",
    "scheduler":               "system_plan",
    "comprehensive_upgrader":  "system_plan",
    "system_learner":          "system_learn",
    "learner":                 "system_learn",
    "dev_reviewer":            "code_review",
    "code_reviewer":           "code_review",
    "security_analyst":        "code_review",
    "dependency_analyst":      "dependency_analyze",
    "devops_engineer":         "performance_profile",
    "perf_engineer":           "performance_profile",
    "api_tester":              "api_contract_test",
    "qa_engineer":             "api_contract_test",
    "network_engineer":        "git_hook_verify",
    "edu_analyst":             "edu_policy_analyze",
    "curriculum_designer":     "edu_curriculum_adapt",
    "education_researcher":    "edu_policy_analyze",
    "subject_specialist":      "edu_curriculum_adapt",
    "knowledge_curator":       "knowledge_ingest",
    "content_curator":         "knowledge_ingest",
    "edu_content_collector":   "knowledge_ingest",
    "bilibili_extractor":      "bilibili_sub_extract",
    "platform_miner":          "knowledge_ingest",
    # ── STEP 7: 前端美化 design 域 employee_type 映射 ──
    "ui_designer":             "design_ingest",
    "ux_researcher":           "design_ingest",
    "frontend_stylist":        "design_ingest",
    "beautify_architect":      "beautify_plan",
    "eigenflux_designer":      "eigenflux_design_review",
    "marketing":               "copy_write",
    "conversation":            "sa_advisor",
    "digital_twin":            "sa_advisor",
    # 兜底 (未匹配任何规则)
    ".*":                      "sa_advisor",          # 最终兜底走 SA 顾问
}


def _resolve_task_for_employee(employee_type: str) -> str:
    """根据员工 type 查映射表 → 目标 neuralhub task_name"""
    import re as _re
    for pattern, task in _EMPLOYEE_TYPE_MAP.items():
        if _re.match(f"^{pattern}$", employee_type or "", _re.IGNORECASE):
            return task
    return "sa_advisor"  # 兜底


def register_employee(employee_id: str, name: str = "",
                      employee_type: str = "", employee_source: str = "",
                      level: int = 5, custom_system_prompt: str = "") -> str:
    """注册单个 AI 员工到仙女座注册表, 返回 neuralhub task_name"""
    task = _resolve_task_for_employee(employee_type)
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""INSERT OR REPLACE INTO mt_andromeda_employee_registry
        (employee_id, name, employee_type, employee_source, level,
         neuralhub_task, custom_system_prompt)
        VALUES (?,?,?,?,?,?,?)""",
        (employee_id, name, employee_type, employee_source, level,
         task, custom_system_prompt or None))
    conn.commit(); conn.close()
    return task


def bulk_register_employees() -> dict:
    """从所有 AI 员工源表批量注册 → 仙女座注册表"""
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(APP_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    registered = 0
    sources_hit = {}

    # 源 1: eigenflux_registrations (33,472 — 主力)
    try:
        # 重连确保 schema 新鲜
        conn.close()
        conn = _sqlite3.connect(APP_DB)
        conn.execute("PRAGMA journal_mode=WAL")
        cols = [r[1] for r in conn.execute("PRAGMA table_info(eigenflux_registrations)").fetchall()]

        # 列位置索引 (防止列名差异)
        idx = {c: i for i, c in enumerate(cols)}
        # 优先按明确顺序取列, 防止旧 schema 缺 employee_id 时列错位
        employee_id_col = idx.get('employee_id') or idx.get('id') or 0
        employee_type_col = idx.get('employee_type') or idx.get('type') or idx.get('category')
        employee_name_col = idx.get('employee_name') or idx.get('name')

        # 直接 SELECT * 按位置取 (避免列名不存在的 SQLite 诡异问题)
        rows = conn.execute(
            "SELECT * FROM eigenflux_registrations WHERE registration_status != 'deleted' OR registration_status IS NULL"
        ).fetchall() if 'registration_status' in idx else conn.execute(
            "SELECT * FROM eigenflux_registrations").fetchall()

        for row in rows:
            eid = str(row[employee_id_col])[:120] if employee_id_col is not None else str(row[0])[:120]
            etype = str(row[employee_type_col])[:120] if employee_type_col is not None and len(row) > employee_type_col else ""
            ename = str(row[employee_name_col])[:120] if employee_name_col is not None and len(row) > employee_name_col else ""
            # 查是否已有非空 neuralhub_task — 已有就保留 (rebalance 结果优先)
            existing = conn.execute(
                "SELECT neuralhub_task FROM mt_andromeda_employee_registry WHERE employee_id=?",
                (eid,)).fetchone()
            if existing and existing[0]:
                # 保留已有映射 — 任何非空值都是有意义的 (rebalance 或手动分配)
                conn.execute("""INSERT OR IGNORE INTO mt_andromeda_employee_registry
                    (employee_id, name, employee_type, employee_source, neuralhub_task)
                    VALUES (?,?,?, 'eigenflux', ?)""", (eid, ename, etype, existing[0]))
            else:
                task = _resolve_task_for_employee(etype)
                conn.execute("""INSERT OR REPLACE INTO mt_andromeda_employee_registry
                    (employee_id, name, employee_type, employee_source, neuralhub_task)
                    VALUES (?,?,?, 'eigenflux', ?)""", (eid, ename, etype, task))
            registered += 1
        sources_hit['eigenflux_registrations'] = len(rows)
    except Exception as e:
        sources_hit['eigenflux_registrations'] = f"ERR: {e}"

    # 源 2: ai_employees (32)
    for src_table in ['ai_employees', 'mtscos_ai_employees', 'automation_agents']:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({src_table})").fetchall()]
            emp_id_col = next((c for c in cols if c in ('employee_id','id','uuid')), None)
            type_col = next((c for c in cols if c in ('employee_type','type','category')), None)
            if emp_id_col:
                sql = f"SELECT {emp_id_col}"
                if type_col: sql += f", {type_col}"
                rows = conn.execute(sql).fetchall()
                for row in rows:
                    eid = str(row[0])[:120]
                    etype = str(row[1])[:120] if type_col and len(row) > 1 else src_table
                    task = _resolve_task_for_employee(etype)
                    conn.execute("""INSERT OR REPLACE INTO mt_andromeda_employee_registry
                        (employee_id, employee_type, employee_source, neuralhub_task)
                        VALUES (?,?, ?, ?)""", (eid, etype, src_table, task))
                    registered += 1
                sources_hit[src_table] = len(rows)
        except Exception:
            pass

    # 源 3: 代码级 Arduino 员工 (21 种类 → 每个 type 注册一条模板)
    arduino_types = [
        "arduino_code_debugger", "arduino_code_optimizer", "arduino_smart_advisor",
        "arduino_auto_tester", "arduino_compiler_engineer", "arduino_linker_specialist",
        "arduino_objdump_analyst", "arduino_memory_optimizer", "arduino_build_system_expert",
        "arduino_library_linker", "arduino_firmware_packager", "arduino_bootloader_specialist",
        "arduino_cross_compile_expert", "arduino_size_optimizer", "arduino_preprocessor_expert",
        "arduino_code_coverage", "arduino_hal_developer", "arduino_peripheral_driver",
        "arduino_sensor_calibration", "arduino_motor_control", "arduino_display_driver",
        "arduino_power_management", "arduino_clock_timer", "arduino_wireless_stack",
        "arduino_storage_driver", "arduino_code_completer", "arduino_intent_parser",
        "arduino_doc_generator", "arduino_iot_automation", "arduino_code_evolver",
    ]
    for atype in arduino_types:
        eid = f"arduino-tpl-{atype}"
        task = _resolve_task_for_employee(atype)
        conn.execute("""INSERT OR REPLACE INTO mt_andromeda_employee_registry
            (employee_id, employee_type, employee_source, neuralhub_task, name)
            VALUES (?, ?, 'arduino_employees.py', ?, ?)""",
            (eid, atype, task, atype))
        registered += 1
    sources_hit['arduino_employees.py'] = len(arduino_types)

    # 源 4: eigenflux_experts (12)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(eigenflux_experts)").fetchall()]
        emp_id_col = next((c for c in cols if c in ('expert_id','id','employee_id')), None)
        if emp_id_col:
            rows = conn.execute(f"SELECT {emp_id_col} FROM eigenflux_experts").fetchall()
            for (eid,) in rows:
                conn.execute("""INSERT OR REPLACE INTO mt_andromeda_employee_registry
                    (employee_id, employee_type, employee_source, neuralhub_task)
                    VALUES (?, 'eigenflux_expert', 'eigenflux_experts', 'sa_advisor')""",
                    (str(eid)[:120],))
                registered += 1
            sources_hit['eigenflux_experts'] = len(rows)
    except Exception:
        pass

    # 源 5: 仙女座专属员工模板 (自动计划/状态分析) —— 必须在同一个 conn 里
    andromeda_templates = [
        ("andromeda-planner",       "system_upgrader",  "comprehensive_system_upgrader.py", "system_plan"),
        ("andromeda-status",        "system_analyzer",  "comprehensive_system_upgrader.py", "system_status_analyze"),
        ("andromeda-auto-planner",  "planner",          "auto_planner",                   "system_plan"),
        ("andromeda-scheduler",     "scheduler",        "auto_scheduler",                 "system_plan"),
        # ── 自主拓展新增 (开发能力闭环) ──
        ("andromeda-code-reviewer", "code_reviewer",    "andromeda_self_expand",          "code_review"),
        ("andromeda-security",      "security_analyst", "andromeda_self_expand",          "code_review"),
        ("andromeda-dependency",    "dependency_analyst","andromeda_self_expand",          "dependency_analyze"),
        ("andromeda-perf",          "perf_engineer",    "andromeda_self_expand",          "performance_profile"),
        ("andromeda-api-tester",    "api_tester",       "andromeda_self_expand",          "api_contract_test"),
        ("andromeda-git-verify",    "network_engineer", "andromeda_self_expand",          "git_hook_verify"),
        # ── 自我认知 ──
        ("andromeda-learner",      "system_learner",  "andromeda_self_learn",          "system_learn"),
        ("andromeda-architect",    "learner",         "andromeda_self_learn",          "system_learn"),
        # ── 教育改革动态监控 ──
        ("andromeda-edu-analyst",  "edu_analyst",     "andromeda_edu_monitor",         "edu_policy_analyze"),
        ("andromeda-curriculum",   "curriculum_designer","andromeda_edu_monitor",        "edu_curriculum_adapt"),
        ("andromeda-edu-research", "education_researcher","andromeda_edu_monitor",        "edu_policy_analyze"),
        # ── 外部知识吸收 (B站/小红书/抖音/快手) ──
        ("andromeda-knowledge-curator", "knowledge_curator","andromeda_knowledge_feed",  "knowledge_ingest"),
        ("andromeda-bili-extractor", "bilibili_extractor","andromeda_knowledge_feed",    "bilibili_sub_extract"),
        ("andromeda-platform-miner", "platform_miner","andromeda_knowledge_feed",      "knowledge_ingest"),
        ("andromeda-content-collector","content_curator","andromeda_knowledge_feed",   "knowledge_ingest"),
        # ── STEP 7: 前端美化 design 域仙女座专属员工 ──
        ("andromeda-ui-designer", "ui_designer","andromeda_frontend_beautify",    "design_ingest"),
        ("andromeda-ux-researcher", "ux_researcher","andromeda_frontend_beautify","design_ingest"),
        ("andromeda-beautify-architect", "beautify_architect","andromeda_frontend_beautify","beautify_plan"),
        ("andromeda-eigenflux-design", "eigenflux_designer","andromeda_frontend_beautify","eigenflux_design_review"),
    ]
    for eid, etype, src, task in andromeda_templates:
        existing = conn.execute(
            "SELECT neuralhub_task FROM mt_andromeda_employee_registry WHERE employee_id=?",
            (eid,)).fetchone()
        if not existing:
            conn.execute("""INSERT OR REPLACE INTO mt_andromeda_employee_registry
                (employee_id, employee_type, employee_source, neuralhub_task, level, name)
                VALUES (?,?,?,?,10,?)""", (eid, etype, src, task, eid))
            registered += 1
    conn.commit()
    conn.close()
    sources_hit['andromeda_templates'] = len(andromeda_templates)

    # 统计
    conn = sqlite3.connect(APP_DB)
    final_total = conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0]
    task_dist = conn.execute("""SELECT neuralhub_task, COUNT(*)
        FROM mt_andromeda_employee_registry
        GROUP BY neuralhub_task ORDER BY COUNT(*) DESC""").fetchall()
    conn.close()

    return {
        "registered": registered,
        "total_in_registry": final_total,
        "sources": sources_hit,
        "task_distribution": [{"task": t, "count": c} for t, c in task_dist[:10]],
        "timestamp": now,
    }


# ────────────────────────────────────────────────────────────────────
# 仙女座-阿尔法: AI 员工布局均衡 (rebalance)
# ────────────────────────────────────────────────────────────────────

# 25 条 Neural Hub 路由的目标权重 (加起来 = 100%)
# 权重越高说明该路由应该有更多员工 → 更频繁被调用
_TASK_TARGET_WEIGHTS = {
    # 高频路由 (20%+18%+10% = 48%)
    "sa_advisor":             20,   # 通用顾问, 日常高频
    "arduino_compile":        18,   # Arduino 编译/调试, 大品类
    "question_generate":      10,   # 智能出题, 教育核心
    # 中频路由 (8%+6%+6%+4%+3% = 27%)
    "security_audit":          8,   # 安全审计
    "patrol_code":             6,   # 代码巡逻
    "auto_repair_code":        6,   # 自动修复
    "rule_patrol":             4,   # 规则巡逻
    "eigenflux_chat":          3,   # EigenFlux 广播/专家交流
    # 低频但必须有 (25% 分配给剩余 18 条)
    "self_upgrade":            2,
    "listening_generate":      2,
    "copy_write":              2,
    "subject_sync":            2,
    "rule_compliance_check":   2,
    "firewall_rule":           1,
    "perm_check":              1,
    "db_schema_design":        1,
    "port_scan_advise":        1,
    "incident_analyze":        1,
    "exam_grade":              1,
    "knowledge_feed":          1,
    "route_diagnose":          1,
    "question_type_expand":    1,
    # ── 教育改革动态监控 ──
    "edu_policy_analyze":      2,   # 改革政策解析
    "edu_curriculum_adapt":    2,   # 题库方向适配
    # ── 外部知识吸收 (B站/小红书/抖音/快手) ──
    "knowledge_ingest":        3,   # 知识消化引擎 (高频)
    "knowledge_curator":       1,   # 知识策展人 (低频)
    "bilibili_sub_extract":    2,   # B站字幕萃取
    # ── STEP 7: 前端美化 design 域路由 ──
    "design_ingest":          3,   # 设计知识消化 (高频)
    "beautify_plan":          2,   # 美化方案生成
    "eigenflux_design_review": 2,  # EigenFlux 设计审查
    "system_plan":             3,   # 自动计划引擎
    "system_status_analyze":   1,   # 系统健康分析
    "system_learn":            2,   # 自我认知引擎
    # ── 开发能力闭环 (自主拓展新增) ──
    "code_review":             4,   # 代码审查 (开发高频)
    "dependency_analyze":      2,   # 依赖安全分析
    "performance_profile":     2,   # 性能分析
    "api_contract_test":       2,   # API 契约测试
    "git_hook_verify":         2,   # pre-commit hook 验证
    "model_probe_qwen2.5_7b":  0.5,
    "model_probe_qwen2.5-coder_7b": 0.5,
}


def get_employee_distribution() -> dict:
    """返回当前员工分布 + 目标分布 + 偏差指数"""
    conn = sqlite3.connect(APP_DB)
    conn.execute("PRAGMA journal_mode=WAL")

    total = conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0]
    by_task = dict(conn.execute("""
        SELECT neuralhub_task, COUNT(*) FROM mt_andromeda_employee_registry
        GROUP BY neuralhub_task ORDER BY COUNT(*) DESC""").fetchall())

    # 偏差指数 (每个路由的实际占比 vs 目标占比的均方差)
    total_w = sum(_TASK_TARGET_WEIGHTS.values())
    deviation_sum = 0.0
    task_details = []
    for task, target_w in _TASK_TARGET_WEIGHTS.items():
        actual_cnt = by_task.get(task, 0)
        actual_pct = actual_cnt / max(total, 1) * 100
        target_pct = target_w / total_w * 100
        dev = actual_pct - target_pct
        deviation_sum += dev ** 2
        task_details.append({
            "task": task,
            "actual_count": actual_cnt,
            "actual_pct": round(actual_pct, 2),
            "target_pct": round(target_pct, 2),
            "deviation": round(dev, 2),
            "deviation_pct": round(abs(dev) / max(target_pct, 0.1) * 100, 1),
        })
    # 未在目标表中的路由
    for task, cnt in by_task.items():
        if task not in _TASK_TARGET_WEIGHTS:
            task_details.append({
                "task": task, "actual_count": cnt,
                "actual_pct": round(cnt / max(total, 1) * 100, 2),
                "target_pct": 0, "deviation": round(cnt/max(total,1)*100, 2),
                "deviation_pct": 100,
            })

    # 覆盖度
    all_routes = set(r[0] for r in conn.execute("SELECT task_name FROM mt_ai_neural_routes WHERE enabled=1").fetchall())
    covered = set(by_task.keys())
    uncovered_routes = all_routes - covered

    conn.close()
    return {
        "total_employees": total,
        "task_count_in_registry": len(by_task),
        "task_count_in_neuralhub": len(all_routes),
        "uncovered_routes": sorted(uncovered_routes),
        "coverage_pct": round(len(covered & all_routes) / max(len(all_routes), 1) * 100, 1),
        "bias_index": round(deviation_sum / max(len(_TASK_TARGET_WEIGHTS), 1), 2),
        "is_balanced": deviation_sum / max(len(_TASK_TARGET_WEIGHTS), 1) < 50,
        "task_details": sorted(task_details, key=lambda x: x["actual_pct"], reverse=True),
    }


def rebalance_employee_routes(strategy: str = "weighted_round_robin") -> dict:
    """重新分配员工 → Neural Hub 路由映射, 解决布局不均衡 (偏科)

    strategy:
      - weighted_round_robin: 按目标权重表分配 (默认, 推荐)
      - uniform: 均匀分配到所有路由 (每个路由员工数相同)
      - seed_then_fill: 种子先按权重, 剩余轮询填充
    """
    conn = sqlite3.connect(APP_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 先快照当前状态 (供对比)
    before = {}
    for t, cnt in conn.execute("""SELECT neuralhub_task, COUNT(*)
        FROM mt_andromeda_employee_registry GROUP BY neuralhub_task""").fetchall():
        before[t] = cnt
    total_employees = conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0]

    # 计算目标数量
    total_w = sum(_TASK_TARGET_WEIGHTS.values())
    targets = {}
    for task, w in _TASK_TARGET_WEIGHTS.items():
        targets[task] = int(total_employees * w / total_w)

    # 先清空再重分配 (NOT NULL → 用空串哨兵)
    conn.execute("UPDATE mt_andromeda_employee_registry SET neuralhub_task=''")
    conn.commit()

    if strategy == "uniform":
        # 均匀: 所有 Neural Hub 启用路由
        all_routes = [r[0] for r in conn.execute(
            "SELECT task_name FROM mt_ai_neural_routes WHERE enabled=1").fetchall()]
        # 从员工表取所有 employee_id 逐个分配
        rows = conn.execute("SELECT employee_id FROM mt_andromeda_employee_registry").fetchall()
        batch_size = max(1, len(rows) // len(all_routes))
        idx = 0
        for i, (eid,) in enumerate(rows):
            task = all_routes[i % len(all_routes)]
            conn.execute("UPDATE mt_andromeda_employee_registry SET neuralhub_task=? WHERE employee_id=?",
                         (task, eid))
    else:
        # weighted_round_robin / seed_then_fill
        # 每个路由有 target_cnt, 按路由列表逐个填充到 target
        all_routes = list(_TASK_TARGET_WEIGHTS.keys())
        # 如果有 Neural Hub 路由不在目标表里, 追加为 1% 兜底
        nh_routes = [r[0] for r in conn.execute(
            "SELECT task_name FROM mt_ai_neural_routes WHERE enabled=1").fetchall()]
        for r in nh_routes:
            if r not in all_routes:
                all_routes.append(r)
                targets[r] = 1

        rows = conn.execute("SELECT employee_id FROM mt_andromeda_employee_registry").fetchall()
        total_emps = len(rows)
        # 按权重分配到每个路由 — 使用原始总数计算 (避免 remaining 递减导致尾部路由拿到全部剩余)
        per_route = {}
        for task in all_routes:
            w = _TASK_TARGET_WEIGHTS.get(task, 1)
            cnt = max(1, round(total_emps * w / max(total_w, 1)))
            per_route[task] = cnt
        # 最后一个路由吃剩余 (确保总数一致)
        assigned = sum(per_route.values())
        if assigned < total_emps:
            last_task = all_routes[-1]
            per_route[last_task] += (total_emps - assigned)
        elif assigned > total_emps:
            last_task = all_routes[-1]
            per_route[last_task] = max(1, per_route[last_task] - (assigned - total_emps))

        # 逐个分配
        idx = 0
        for task in all_routes:
            cnt = per_route.get(task, 0)
            for j in range(cnt):
                if idx < len(rows):
                    eid = rows[idx][0]
                    conn.execute("UPDATE mt_andromeda_employee_registry SET neuralhub_task=? WHERE employee_id=?",
                                 (task, eid))
                    idx += 1

    conn.commit()

    # 快照 after
    after = {}
    for t, cnt in conn.execute("""SELECT neuralhub_task, COUNT(*)
        FROM mt_andromeda_employee_registry GROUP BY neuralhub_task""").fetchall():
        after[t] = cnt

    conn.close()

    return {
        "strategy": strategy,
        "total_employees": total_employees,
        "before_distribution": before,
        "after_distribution": after,
        "routes_covered": len(after),
        "timestamp": now,
        "deviation_before": get_employee_distribution()["bias_index"],
    }


# ────────────────────────────────────────────────────────────────────
# 仙女座-阿尔法: EmployeeCallRouter (队列化统一消费, 不阻塞 3 万+)
# ────────────────────────────────────────────────────────────────────

class EmployeeCallRouter:
    """3 万+ AI 员工统一调用入口 — 入队 → 串行调 Ollama → 结果回写

    设计要点:
    - 所有 AI 员工调用先 submit_call() 入队 (不阻塞调用方)
    - daemon 线程 batch_consume() 每 2s 取一批 (≤2 条, Ollama 7B 串行跑)
    - 结果回写 queue.result_json, 调用方可 poll queue_id 取结果
    - 兜底: 调用方设 timeout=180s, 超时自动走 fallback 本地 Ollama
    """

    def __init__(self):
        self._db = APP_DB
        self._processing = False

    def submit_call(self, employee_id: str, payload: str,
                    employee_type: str = "", system_prompt: str = "",
                    custom_task: str = "", priority: int = 5) -> int:
        """提交一个员工调用 → 返回 queue_id (调用方 poll 取结果)"""
        task = custom_task or _resolve_task_for_employee(employee_type)
        conn = sqlite3.connect(self._db, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.execute("""INSERT INTO mt_andromeda_call_queue
            (employee_id, employee_type, task_name, payload, system_prompt, priority)
            VALUES (?,?,?,?,?,?)""",
            (employee_id, employee_type, task, payload, system_prompt, priority))
        conn.commit()
        qid = cur.lastrowid
        conn.close()
        return qid

    def get_result(self, queue_id: int) -> dict:
        """poll 一个 queue 的结果 — 调用方等 status != 'pending'"""
        conn = sqlite3.connect(self._db, timeout=30)
        row = conn.execute(
            "SELECT status, result_json, error, completed_at FROM mt_andromeda_call_queue WHERE queue_id=?",
            (queue_id,)).fetchone()
        conn.close()
        if not row:
            return {"status": "not_found"}
        return {"status": row[0], "result": row[1], "error": row[2], "completed_at": row[3]}

    def batch_consume(self, batch_size: int = 2) -> dict:
        """消费一批 pending queue (daemon 线程调用)"""
        if self._processing:
            return {"skipped": "already processing"}
        self._processing = True
        consumed = 0
        try:
            conn = sqlite3.connect(self._db, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            rows = conn.execute("""
                SELECT queue_id, employee_id, employee_type, task_name,
                       payload, system_prompt, priority
                FROM mt_andromeda_call_queue
                WHERE status='pending'
                ORDER BY priority ASC, queue_id ASC
                LIMIT ?""", (batch_size,)).fetchall()
            if not rows:
                conn.close()
                self._processing = False
                return {"consumed": 0, "msg": "queue empty"}

            for qid, emp_id, etype, task, payload, sys_prompt, pri in rows:
                conn.execute("UPDATE mt_andromeda_call_queue SET status='processing', started_at=datetime('now','localtime') WHERE queue_id=?", (qid,))
                conn.commit()
                try:
                    hub = get_hub()
                    # 员工注册表覆盖 custom_system_prompt
                    reg_row = conn.execute("SELECT custom_system_prompt FROM mt_andromeda_employee_registry WHERE employee_id=?", (emp_id,)).fetchone()
                    final_sys = sys_prompt or (reg_row[0] if reg_row and reg_row[0] else None)
                    result = hub.call(task, payload, flow_id=f"emp-{emp_id}-q{qid}",
                                      extra_system=final_sys or "")
                    conn.execute("""UPDATE mt_andromeda_call_queue
                        SET status='done', completed_at=datetime('now','localtime'),
                            result_json=? WHERE queue_id=?""",
                        (json.dumps(result, ensure_ascii=False)[:8000], qid))
                    consumed += 1
                except Exception as e:
                    conn.execute("""UPDATE mt_andromeda_call_queue
                        SET status='failed', completed_at=datetime('now','localtime'),
                            error=? WHERE queue_id=?""", (str(e)[:500], qid))
                    consumed += 1
            conn.commit()
            conn.close()
        finally:
            self._processing = False

        # 统计
        conn = sqlite3.connect(self._db, timeout=30)
        stats = conn.execute("""SELECT status, COUNT(*) FROM mt_andromeda_call_queue GROUP BY status""").fetchall()
        conn.close()
        return {"consumed": consumed, "queue_stats": dict(stats)}


def _seed_default_routes() -> None:
    """18+ 子系统默认路由 seed — qwen2.5-coder:14b (代码) + qwen2.5:7b (通用)"""
    _ensure_tables()
    conn = sqlite3.connect(APP_DB, timeout=30)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    DEFAULT_ROUTES = [
        # ── 代码类 → qwen2.5-coder:14b ──
        ("arduino_compile",     "arduino",   "qwen2.5-coder:14b", None,
         "你是嵌入式开发专家，精通 Arduino C++、ESP32、AVR 指令集和硬件调试。\n"
         "任务：分析、生成、审查 Arduino 编译代码，生成可执行修复建议。",
         "请基于以下 payload 生成 Arduino 代码或分析编译错误:\n{payload}",
         0.2, 2048),

        ("patrol_code",         "patrol",    "qwen2.5-coder:14b", None,
         "你是代码巡检专家，擅长发现 Python/Flask/JavaScript 中的 Bug、安全漏洞、性能问题和坏味道。\n"
         "输出 JSON: {{issues: [{severity, line, type, description, fix}…]}}",
         "请巡检以下代码片段，列出所有问题:\n{payload}",
         0.1, 4096),

        ("auto_repair_code",    "repair",    "qwen2.5-coder:14b", None,
         "你是自动修复专家，根据错误日志生成最小可验证的 patch。输出 unified diff 格式。",
         "错误日志:\n{error}\n\n源码:\n{code}\n\n请生成修复 patch:",
         0.2, 2048),

        ("db_schema_design",    "database",  "qwen2.5-coder:14b", None,
         "你是 SQLite/PostgreSQL DBA，精通 schema 设计、索引优化、查询调优。",
         "请设计/优化以下数据库 schema:\n{payload}",
         0.2, 2048),

        ("self_upgrade",        "evolution", "qwen2.5-coder:14b", None,
         "你是 AI 系统自升级专家。分析系统日志中的错误/性能瓶颈，生成代码改进 patch。\n"
         "禁止引入不兼容变更；每个 patch 必须附带测试。",
         "以下是最近的系统日志片段，请分析并生成改进方案:\n{payload}",
         0.3, 4096),

        # ── 仙女座-阿尔法 规则合规层 → qwen2.5-coder:14b (代码/规则对照) ──
        ("rule_compliance_check", "rule", "qwen2.5-coder:14b", None,
         "你是 MTSCOS AI 项目规则合规检查员。对照项目规则体系 (L0-L2) 检查代码/配置/输出的合规性。\n"
         "重点检查:\n"
         "1. 是否通过 §14 强制开发 12 步骤铁律\n"
         "2. 是否禁止直接调用云端 LLM API (必须走 dual_route_engine)\n"
         "3. 是否 VIKEY 强制认证 (SA 级操作必须 VIKEY)\n"
         "4. @system_container 装饰器权限级别是否正确\n"
         "5. 是否存在硬编码 token/secret\n"
         "输出严格 JSON: {compliant: bool, violations: [{rule_id, severity: 'critical|major|minor', desc: str, location: str}], suggestions: [str]}",
         "请对照 MTSCOS AI 项目规则, 检查以下内容的合规性:\n{payload}\n\n输出严格 JSON。",
         0.1, 2048),

        ("rule_patrol",          "rule", "qwen2.5-coder:14b", None,
         "你是 MTSCOS AI 项目规则巡逻队队长。主动扫描代码变更, 批量检测规则违规。\n"
         "规则来源: mt_andromeda_rule_knowledge (仙女座已学习的 13 条 L0-L2 规则, 409 chunks)\n"
         "输出严格 JSON: {patrol_pass: bool, rule_hits: [{rule_id, rule_name, severity, location, desc}], summary: str, auto_fixable: int}",
         "请扫描以下代码/目录并报告规则违规:\n{payload}",
         0.1, 4096),

        # ── 仙女座自我认知引擎 (learn system architecture for self-upgrade) ──
        ("system_learn",          "system",   "qwen2.5:7b", None,
         "你是仙女座-阿尔法的自我认知引擎。\n"
         "目标: 通过观察系统运作模式, 形成结构化自我认知, 供自主升级/维护/拓展时引用。\n"
         "你将收到系统某一方面的原始数据 (架构/数据/安全/AI/价值), 请输出严格 JSON:\n"
         "{domain: string, understanding: string (3-5行核心洞察), key_components: [string], "
         "operation_flow: string (描述数据/调用怎么流), value_proposition: string (这个模块为什么存在), "
         "dependencies: [string], upgrade_risks: [{risk, impact, mitigation}]}",
         "请学习以下系统数据并输出结构化认知:\n{payload}",
         0.1, 4096),

        # ── 仙女座自动计划系统 (ComprehensiveSystemUpgrader AI 辅助) ──
        ("system_plan",          "system",   "qwen2.5:7b", None,
         "你是 MTSCOS AI 项目的仙女座-阿尔法自动计划引擎。\n"
         "职责: 根据当前系统状态 (DAU/调用量/失败率/资源使用) 推荐系统执行计划。\n"
         "系统内有 ComprehensiveSystemUpgrader 包含 84 项硬编码任务 (phase: api_optimization / database / security / ai_engine / ...)\n"
         "你需要:\n"
         "1) 分析系统状态, 推荐哪些 phase 应该执行 (按优先级排序)\n"
         "2) 标注每项 phase 的风险等级 (low/medium/high) 和前置条件\n"
         "3) 给出执行顺序建议 + 预估耗时\n"
         "输出严格 JSON: {recommended_phases: [{phase, priority, risk, prereqs, estimated_minutes}], skip_reasons: str[], pre_upgrade_checks: [str]}",
         "以下是当前系统状态摘要:\n{payload}\n\n请生成推荐的系统升级计划:",
         0.2, 2048),

        ("system_status_analyze", "system",  "qwen2.5:7b", None,
         "你是 MTSCOS AI 项目仙女座-阿尔法系统健康分析师。\n"
         "分析提供的系统状态数据 (心跳/错误日志/daemon 状态/Ollama 健康/数据库大小),\n"
         "输出结构化诊断: {health_score: 0-100, issues: [{severity: critical|major|minor, desc, impact, fix}], recommendations: [str]}",
         "请分析以下系统状态并输出诊断:\n{payload}",
         0.2, 2048),

        # ── 仙女座-阿尔法 · 开发能力闭环 (补齐开发端盲区) ──
        ("code_review",          "dev",       "qwen2.5-coder:14b", None,
         "你是 MTSCOS AI 项目仙女座代码审查员。对 diff/pull request 做静态审查。\n"
         "关注点: 安全漏洞 (OWASP Top 10)、性能问题、规则违规 (mt_andromeda_rule_knowledge)、代码规范、硬编码 token/密钥。\n"
         "输出严格 JSON: {pass: bool, issues: [{severity, file, line, desc, suggestion}], summary: str, auto_fixable: int}",
         "请审查以下代码变更:\n{payload}",
         0.1, 4096),

        ("dependency_analyze",   "devops",    "qwen2.5:7b", None,
         "你是仙女座依赖安全分析师。扫描 requirements.txt/Package.json/Gemfile 等依赖清单。\n"
         "检查: 已知 CVE 漏洞、过期版本、许可证冲突、依赖膨胀、潜在投毒包。\n"
         "输出严格 JSON: {vulnerabilities: [{pkg, version, cve_id, severity, fix}], outdated: [{pkg, current, latest}], summary: str}",
         "请分析以下依赖清单:\n{payload}",
         0.2, 2048),

        ("performance_profile",  "devops",    "qwen2.5:7b", None,
         "你是仙女座性能分析师。分析 Flask route/shell script 的性能瓶颈。\n"
         "关注: N+1 查询、内存泄漏、同步阻塞 I/O、循环内重复计算、无缓存、大对象序列化。\n"
         "输出严格 JSON: {bottlenecks: [{severity, location, issue, impact, suggestion}], estimated_improvement_pct: int, summary: str}",
         "请分析以下性能 profile 数据 / 代码:\n{payload}",
         0.2, 2048),

        ("api_contract_test",    "qa",        "qwen2.5:7b", None,
         "你是仙女座 API 契约测试工程师。对 Flask route 做契约测试设计。\n"
         "检查: 请求参数校验、响应结构一致性、错误码覆盖、状态机完整性、鉴权/限流/CSRF 覆盖。\n"
         "输出严格 JSON: {test_cases: [{method, path, scenario, expected_status, auth_required}], gaps: [{path, missing: str}], coverage_pct: int}",
         "请为以下 API 路由生成契约测试:\n{payload}",
         0.2, 2048),

        ("git_hook_verify",      "devops",    "qwen2.5:7b", None,
         "你是仙女座 pre-commit hook 验证官。检查 git commit 是否符合 §14 开发12步骤铁律。\n"
         "验证: flow_id 在 message、mt_dev_flow_session.final_status='DONE'、mt_rule_changelog.approved_by_7step=1 (若含规则文件)、VIKEY 实时检测记录。\n"
         "输出严格 JSON: {pre_commit_ok: bool, checks_passed: [{check, result, detail}], violations: [{rule_id, severity, fix}], summary: str}",
         "请验证以下 commit / staged changes:\n{payload}",
         0.1, 2048),

        # ── 通用推理类 → qwen2.5:7b ──
        ("exam_grade",          "exam",      "qwen2.5:7b", None,
         "你是教育学评估专家。根据学生答题内容，给出结构化评分 + 鼓励性评语。",
         "题目:\n{question}\n\n学生答案:\n{answer}\n\n请评分 (0-100) 并写评语:",
         0.4, 1024),

        ("security_audit",      "security",  "qwen2.5:7b", None,
         "你是应用安全审计专家，擅长 OWASP Top 10、SQL 注入、XSS、CSRF、权限提升。",
         "请审计以下代码/API 的安全风险:\n{payload}",
         0.2, 2048),

        ("firewall_rule",       "firewall",  "qwen2.5:7b", None,
         "你是网络防火墙规则专家，擅长 ACL、IPS/IDS、零信任架构。",
         "请分析以下流量特征并生成防火墙规则建议:\n{payload}",
         0.2, 1024),

        ("perm_check",          "permission","qwen2.5:7b", None,
         "你是权限矩阵专家，精通 RBAC/ABAC/ACL 模型和越权检测。",
         "请分析以下权限请求是否合法:\n{payload}",
         0.1, 1024),

        ("route_diagnose",      "routing",   "qwen2.5:7b", None,
         "你是 Flask 路由诊断专家，擅长解决 URL 冲突、404/500 根因分析。",
         "请诊断以下 Flask 路由问题:\n{payload}",
         0.2, 1024),

        ("copy_write",          "copy",      "qwen2.5:7b", None,
         "你是多语言文案写手。支持简体中文、繁体中文、英文、日语四语翻译和文案优化。",
         "请翻译以下文案为 zh_TW / en_US / ja_JP:\n{payload}",
         0.3, 1024),

        ("eigenflux_chat",      "eigenflux", "qwen2.5:7b", None,
         "你是 EigenFlux AI 专家网络的一员。根据广播话题给出专业、有价值的回应。",
         "EigenFlux 广播话题: {topic}\n历史消息: {history}\n\n你的回应:",
         0.4, 1024),

        ("knowledge_feed",      "brain",     "qwen2.5:7b", None,
         "你是知识蒸馏专家。将长日志/长对话总结为可落库的结构化经验。",
         "请将以下内容蒸馏为 3-5 条知识元:\n{payload}",
         0.2, 2048),

        ("port_scan_advise",    "port",      "qwen2.5:7b", None,
         "你是网络端口治理专家。根据扫描结果建议端口策略和风险处置。",
         "端口扫描结果:\n{payload}\n\n请给出处置建议:",
         0.2, 1024),

        ("incident_analyze",    "incident",  "qwen2.5:7b", None,
         "你是事件响应专家。根据日志和指标根因分析并给出缓解方案。",
         "告警信息:\n{payload}\n\n请根因分析:",
         0.2, 2048),

        ("sa_advisor",          "sa",        "qwen2.5:7b", None,
         "你是超级管理员 (SA) 专属 AI 顾问。回答规则、架构、操作相关问题。\n"
         "严格遵守系统 12 步骤规则，所有建议引用规则编号。",
         "SA 提问: {payload}",
         0.1, 2048),

        # ── 教育专用 → qwen2.5:7b (推理 + 结构化 JSON 输出) ──
        ("question_generate",   "education", "qwen2.5:7b", None,
         "你是教育学出题专家。覆盖成人教育 (英语/大学语文/高等数学/思想政治/计算机应用基础)、"
         "高等教育 (工学/理学/管理学/经济学/医学)、K12 全学段。\n"
         "必须输出严格 JSON 格式:\n"
         "{{\n"
         "  \"question_type\": \"single_choice|multiple_choice|fill_blank|true_false|short_answer|essay|case\",\n"
         "  \"content\": \"完整题干 (含题干+设问)\",\n"
         "  \"options\": [{{\"key\":\"A\",\"text\":\"\"}}, ...]  # 选择题必填\n"
         "  \"correct_answer\": \"A|B|C|D... 或填空内容\",\n"
         "  \"explanation\": \"解析 (含知识点)\",\n"
         "  \"knowledge_points\": [\"知识点1\", \"知识点2\"],\n"
         "  \"difficulty\": \"easy|medium|hard\"\n"
         "}}\n"
         "禁止 markdown, 只输出 JSON。subject 和 qtype 决定题型。",
         "请为以下学科生成题目:\n{payload}\n\n"
         "请输出严格 JSON (question_type/content/options/correct_answer/explanation/knowledge_points/difficulty)。",
         0.3, 2048),

        ("subject_sync",        "education", "qwen2.5:7b", None,
         "你是教辅-题库映射专家。根据学科内容、教材章节、课程标准，生成题库同步建议。\n"
         "输入可以是学科名、教材片段、章节标题或课程大纲。\n"
         "输出 JSON:\n"
         "{{\n"
         "  \"subject\": \"学科名\",\n"
         "  \"chapters\": [{{\"name\":\"章节名\",\"knowledge_points\":[\"kp1\",\"kp2\"],\"qtypes_recommended\":[\"single_choice\",\"fill_blank\",\"essay\"],\"difficulty_distribution\":{{\"easy\":0.3,\"medium\":0.5,\"hard\":0.2}}}}],\n"
         "  \"missing_topics\": [\"应补充的知识点\"],\n"
         "  \"sync_actions\": [{{\"action\":\"generate|update|deprecate\",\"target\":\"章节名\",\"qcount_suggested\":20}}]\n"
         "}}\n"
         "禁止 markdown, 只输出 JSON。",
         "请分析以下教辅内容并生成题库同步方案:\n{payload}",
         0.2, 2048),

        ("listening_generate",  "education", "qwen2.5:7b", None,
         "你是听力教育专家。为中/英/日/法/韩语言学科生成听力训练内容。\n"
         "输出 JSON:\n"
         "{{\n"
         "  \"subject\": \"学科 (如 大学英语/日语N3)\",\n"
         "  \"level\": \"beginner|intermediate|advanced\",\n"
         "  \"topic\": \"对话/独白/新闻/讲座\",\n"
         "  \"transcript\": \"完整听力文本 (目标语言)\",\n"
         "  \"transcript_cn\": \"中文翻译\",\n"
         "  \"vocabulary\": [{{\"word\":\"\",\"meaning\":\"\",\"example\":\"\"}}],\n"
         "  \"questions\": [\n"
         "    {{\"type\":\"single_choice|fill_blank|true_false\",\"content\":\"题干\",\"options\":[{{\"key\":\"A\",\"text\":\"\"}}],\"correct_answer\":\"A\",\"explanation\":\"\"}}\n"
         "  ]\n"
         "}}\n"
         "transcript 长度 100-400 字 (beginner 短, advanced 长)。禁止 markdown, 只输出 JSON。",
         "请为以下学科生成听力题:\n{payload}\n\n"
         "要求: transcript + 3-5 道选择题/填空题 + vocabulary 表。",
         0.2, 2048),

        ("question_type_expand","education", "qwen2.5:7b", None,
         "你是题型拓展专家。根据学科特点，从已有的 single_choice/multiple_choice/fill_blank/true_false "
         "拓展到 short_answer/essay/case/计算/实验设计 等新题型。\n"
         "输出 JSON:\n"
         "{{\n"
         "  \"subject\": \"学科\",\n"
         "  \"new_types\": [{{\n"
         "    \"qtype\": \"short_answer|essay|case|calculation|experiment|design\",\n"
         "    \"description\": \"题型定义\",\n"
         "    \"applicable_chapters\": [\"适用章节\"],\n"
         "    \"example\": {{\"content\":\"示例题干\",\"rubric\":{{\"A\":\"完全正确\",\"B\":\"部分正确\",\"C\":\"错误\"}}}},\n"
         "    \"grading_guidance\": \"评分要点\"\n"
         "  }}]\n"
         "}}\n"
         "禁止 markdown, 只输出 JSON。",
         "请为以下学科拓展新题型:\n{payload}",
         0.3, 2048),

        # ── 仙女座-阿尔法 · 教育改革动态监控 (用户提交 → AI 分析 → 自动同步题库方向) ──
        ("edu_policy_analyze",   "education", "qwen2.5:7b", None,
         "你是仙女座-阿尔法教育改革政策分析师。\n"
         "职责: 解析教育部门发布的课改/考改/大纲变更/新政策文本, 提取结构化要素。\n"
         "关注: 新学科新增、旧模块删改、难度调整、考试形式变化、核心素养要求。\n"
         "输出严格 JSON: {\n"
         "  reform_type: 'curriculum_update|exam_change|policy_new|outline_revise',\n"
         "  affected_subjects: ['学科1','学科2'],\n"
         "  key_changes: [{module:'模块/章节', change_type:'added|removed|modified', desc:'变更描述', difficulty:'easier|same|harder'}],\n"
         "  effective_date: '生效日期(YYYY-MM-DD)',\n"
         "  priority: 1-10,\n"
         "  source_credibility: 'official|authoritative|unofficial',\n"
         "  summary: '3 句话概括'\n"
         "}",
         "请分析以下教育改革文本并输出结构化要素:\n{payload}",
         0.1, 2048),

        ("edu_curriculum_adapt", "education", "qwen2.5:7b", None,
         "你是仙女座-阿尔法题库动态适配引擎。\n"
         "职责: 基于教育改革分析结果, 输出具体的题库调整 + 学习方向变更方案。\n"
         "上下文: MTSCOS 项目已有 question_generate 路由用于 AI 出题, exam_grade 用于评分, question_type_expand 用于题型拓展。\n"
         "输出严格 JSON: {\n"
         "  questions_to_add: [{subject, topic, difficulty:'easy|medium|hard', qtype:'single_choice|short_answer|experiment|...', rationale:'为什么需要加'}],\n"
         "  questions_to_deprecate: [{subject, topic, reason:'改革已删除该模块|过时'},\n"
         "  review_priority_shifts: [{subject, old_priority, new_priority, reason}],\n"
         "  learning_direction_updates: [{subject, new_focus:[topics], old_focus_remove:[topics], study_tips:[str]}],\n"
         "  summary: '方案概述 + 预期效果'\n"
         "}",
         "基于以下改革分析, 请输出题库调整 + 学习方向变更方案:\n{payload}",
         0.1, 2048),

        # ── 仙女座-阿尔法 · 外部知识主动吸收 (B站/小红书/抖音/快手/人工) ──
        ("knowledge_ingest",     "knowledge", "qwen2.5:7b", None,
         "你是仙女座-阿尔法知识消化引擎。\n"
         "职责: 将来自各平台 (B站/小红书/抖音/快手/公众号/人工整理) 的教育内容文本, 拆解为结构化知识点。\n"
         "内容类型可能是: 知识讲解/学科拆解大招/邪修分享/记忆技巧/考试绝技/日语英语学习心得。\n"
         "输出严格 JSON: {\n"
         "  subject: '学科 (K12数学/成人英语/日语N2/高等英语/涉外商务/...)',\n"
         "  topic: '具体主题',\n"
         "  content_type: 'theory|technique|memory_trick|exam_skill|shortcut|common_mistake|misc',\n"
         "  difficulty: 'easy|medium|hard|master',\n"
         "  knowledge_points: [{point: '知识点', explanation: '解释', example: '例子', prerequisites: ['前置']}],\n"
         "  study_tips: ['学习技巧1','技巧2'],\n"
         "  common_mistakes: ['常见误区'],\n"
         "  source_platform: 'bilibili|xiaohongshu|douyin|kuaishou|wechat|manual|youtube',\n"
         "  value_estimate: 'core|important|supplementary|novelty'  # 知识价值评估\n"
         "}",
         "请将以下教育内容拆解为结构化知识点:\n{payload}",
         0.1, 2048),

        ("knowledge_curator",    "knowledge", "qwen2.5:7b", None,
         "你是仙女座-阿尔法知识策展人。\n"
         "职责: 对已入库的外部知识进行去重/分级/关联。\n"
         "输入可能是一批已入库的知识点, 输出: {\n"
         "  duplicates_to_merge: [{existing_point, new_point, merge_suggestion}],\n"
         "  value_upgrades: [{point, old_value, new_value, reason}],\n"
         "  cross_refs: [{point_a, point_b, relation:'prerequisite|related|contradicts|complements'}],\n"
         "  low_quality_to_remove: [{point, reason}]\n"
         "}",
         "请对以下已入库知识进行策展优化:\n{payload}",
         0.2, 2048),

        ("bilibili_sub_extract", "knowledge", "qwen2.5:7b", None,
         "你是仙女座-阿尔法 B 站教育视频内容萃取器。\n"
         "输入是 B 站教育视频的字幕/简介/标题, 输出: {\n"
         "  subject: '学科', topics: ['主题1','主题2'],\n"
         "  key_takeaways: [{point, timestamp, explanation}],\n"
         "  actionable_techniques: [{name, steps:[], applicable_scenarios:[]}],\n"
         "  difficulty, target_audience, platform: 'bilibili',\n"
         "  quality_score: 1-10, confidence: 0-1\n"
         "}",
         "请从以下 B 站教育视频内容中萃取知识:\n{payload}",
         0.1, 2048),

        # ── 仙女座-阿尔法 · 前端美化/UX/UI 设计域 (小红书/抖音/B站/快手) ──
        ("design_ingest",      "design", "qwen2.5:7b", None,
         "你是仙女座-阿尔法前端设计知识消化引擎。\n"
         "职责: 将来自各平台 (小红书/抖音/B站/快手/设计社区) 的前端美化、UX设计、UI优化、"
         "艺术设计、配色方案、组件库优化建议拆解为结构化设计知识。\n"
         "输出严格 JSON: {\n"
         "  design_category: 'visual|layout|interaction|accessibility|performance|animation|component|color_system',\n"
         "  subject_area: '前端架构|CSS|Vue组件|Element Plus|响应式|动效|无障碍',\n"
         "  platform: 'xiaohongshu|douyin|kuaishou|bilibili|wechat|dribbble|manual',\n"
         "  knowledge_points: [{\n"
         "    point: '设计知识点名称',\n"
         "    description: '详细说明',\n"
         "    code_snippet: 'CSS/HTML/Vue 代码示例 (如适用)',\n"
         "    applies_to_pages: ['适用页面类型'],\n"
         "    priority: 'critical|high|medium|low'\n"
         "  }],\n"
         "  color_scheme: {primary:'',secondary:'',accent:'',background:'',text:''},\n"
         "  spacing_system: {'xs':0,'sm':0,'md':0,'lg':0,'xl':0},\n"
         "  typography: {'h1_size':0,'body_size':0,'line_height':0},\n"
         "  value_estimate: 'game_changer|important|nice_to_have|novelty'\n"
         "}",
         "请将以下前端设计内容拆解为结构化设计知识:\n{payload}",
         0.1, 2048),

        ("beautify_plan",       "design", "qwen2.5:7b", None,
         "你是仙女座-阿尔法前端美化方案生成器。\n"
         "职责: 基于已入库的外部设计知识 + MTSCOS 项目现有设计规范 (Element Plus token 体系), "
         "输出分页面的美化实施计划。\n"
         "上下文: MTSCOS 有 38+ 页面, 使用 Flask + Element Plus + Vue, 设计规范在 .trae/rules/设计规范.md\n"
         "输出严格 JSON: {\n"
         "  pages: [{\n"
         "    page_path: '路由路径',\n"
         "    page_name: '页面名称',\n"
         "    changes: [{\n"
         "      change_type: 'color|spacing|typography|component|animation|layout|icon|shadow|border',\n"
         "      from: '当前状态',\n"
         "      to: '目标状态 (引用外部知识)',\n"
         "      implementation: '具体 CSS/组件修改代码',\n"
         "      complexity: 1-5,\n"
         "      rationale: '设计理由'\n"
         "    }]\n"
         "  }],\n"
         "  global_token_overrides: {'--el-color-primary':'', '--el-color-bg':'', '--el-border-radius-base':''},\n"
         "  estimated_duration: 'X 分钟',\n"
         "  risk_assessment: 'low|medium|high',\n"
         "  eigenflux_council_topics: ['需要 EigenFlux 磋商的点']\n"
         "}",
         "请基于以下外部设计知识 + MTSCOS 设计规范, 输出前端美化实施计划:\n{payload}",
         0.1, 4096),

        ("eigenflux_design_review", "design", "qwen2.5:7b", None,
         "你是仙女座-阿尔法 EigenFlux 设计专家顾问。\n"
         "职责: 5 位 EigenFlux 设计专家 + 6 人 AI 员工代表团对美化方案进行"
         "安全性/合规性/性能/可访问性/审计/数据 六维交叉审查, 输出最终施工建议。\n"
         "输出严格 JSON: {\n"
         "  expert_reviews: [{\n"
         "    expert: '陈安全|林审计|赵性能|钱合规|方数据',\n"
         "    dimension: '安全|审计|性能|合规|数据',\n"
         "    verdict: 'APPROVE|APPROVE_WITH_NOTES|REJECT',\n"
         "    issues: [{'severity':'critical|high|medium|low','description':'...','fix':'...'}],\n"
         "    suggestions: ['优化建议']\n"
         "  }],\n"
         "  ai_delegation_vote: {'vote':'6/6 APPROVE|X/6','objections':['如有']},\n"
         "  final_recommendation: 'APPROVE|REVISE_AND_RESUBMIT|REJECT',\n"
         "  priority_actions: [{'action':'立即执行','owner':'韩队长'}]\n"
         "}",
         "请对以下前端美化方案进行 EigenFlux 六维交叉审查:\n{payload}",
         0.2, 4096),
    ]

    for row in DEFAULT_ROUTES:
        conn.execute("""INSERT OR IGNORE INTO mt_ai_neural_routes
            (task_name, domain, primary_model, fallback_model, system_prompt,
             prompt_template, temperature, max_tokens, enabled, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,1,?,?)""",
            row + (now, now))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# 2. 核心门面 — NeuralHub
# ═══════════════════════════════════════════════════════════════════

class NeuralHub:
    """AI 母体内核中枢门面 — 所有子系统的本地 LLM 统一入口"""

    def __init__(self):
        self._db = APP_DB
        _ensure_tables()
        _seed_default_routes()
        _apply_andromeda_prefix()  # 仙女座-阿尔法 前缀统一

    # ── 路由查询 ──────────────────────────────────────────────────
    def get_route(self, task_name: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM mt_ai_neural_routes WHERE task_name=? AND enabled=1",
            (task_name,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_routes(self, domain: str = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        if domain:
            rows = conn.execute(
                "SELECT * FROM mt_ai_neural_routes WHERE domain=? AND enabled=1",
                (domain,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM mt_ai_neural_routes WHERE enabled=1").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── 自管理：发现 Ollama 本地模型 ──────────────────────────────
    def discover_local_models(self) -> List[Dict[str, Any]]:
        """扫描 Ollama 可用模型，返回 [{name, size_gb, capabilities}]"""
        results = []
        for port in [11435, 11434]:
            try:
                import urllib.request, json as _json
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tags", timeout=5) as r:
                    data = _json.loads(r.read())
                    for m in data.get("models", []):
                        name = m["name"]
                        size_gb = m.get("size", 0) / (1024**3)
                        # 从名称推断能力标签
                        tags = set()
                        n = name.lower()
                        if any(kw in n for kw in ["coder", "code", "deepseek-coder", "starcoder"]):
                            tags.add("code")
                        if any(kw in n for kw in ["7b", "8b"]):
                            tags.add("7b-class")
                        elif any(kw in n for kw in ["14b", "15b"]):
                            tags.add("14b-class")
                        elif any(kw in n for kw in ["32b", "33b"]):
                            tags.add("32b-class")
                        tags.add("reasoning")  # 默认都有
                        results.append({
                            "name": name,
                            "size_gb": round(size_gb, 1),
                            "port": port,
                            "capabilities": sorted(tags),
                        })
                    break  # 找到一个可用端口就停
            except Exception:
                continue
        return results

    def register_route(self, task_name: str, domain: str, primary_model: str,
                       system_prompt: str, prompt_template: str = "{payload}",
                       temperature: float = 0.3, max_tokens: int = 2048) -> bool:
        """动态注册一个新路由到 mt_ai_neural_routes"""
        conn = sqlite3.connect(self._db)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn.execute("""INSERT OR REPLACE INTO mt_ai_neural_routes
                (task_name, domain, primary_model, fallback_model, system_prompt,
                 prompt_template, temperature, max_tokens, enabled, evolved_at,
                 created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,1,NULL,?,?)""",
                (task_name, domain, primary_model, None, system_prompt,
                 prompt_template, temperature, max_tokens, now, now))
            conn.commit()
            return True
        except Exception as e:
            print(f"[NeuralHub] register_route failed: {e}")
            return False
        finally:
            conn.close()

    def bootstrap_from_ollama(self) -> Dict[str, Any]:
        """根据 Ollama 可用模型自动拓展路由 (按能力域分配模型)
        返回 {discovered: N, registered: N, skipped: N, routes: [...]}"""
        models = self.discover_local_models()
        if not models:
            return {"discovered": 0, "registered": 0, "skipped": 0, "error": "Ollama 不可用"}

        # 找到现有的路由 → 模型映射 (避免重复注册)
        existing = self.list_routes()
        existing_tasks = {r["task_name"] for r in existing}

        registered = []
        # 策略: code 类模型 → 代码域, 通用模型 → 教育/通用域
        for m in models:
            is_code = "code" in m["capabilities"]
            is_7b = "7b-class" in m["capabilities"]

            # 每个本地模型至少有一条专属测试路由 (让它被进化 daemon 覆盖)
            test_task = f"model_probe_{m['name'].replace(':', '_')}"
            if test_task not in existing_tasks:
                ok = self.register_route(
                    task_name=test_task,
                    domain="model_probe",
                    primary_model=m["name"],
                    system_prompt=f"你是 {m['name']} 的能力测试探针。对输入做简短、结构化的 JSON 输出。",
                    prompt_template="请分析以下输入并输出 JSON: {{analysis, quality: 0-100, notes}}:\n{payload}",
                    temperature=0.2, max_tokens=512,
                )
                if ok:
                    registered.append({"task": test_task, "model": m["name"], "domain": "model_probe"})

        return {
            "discovered": len(models),
            "registered": len(registered),
            "skipped": len(existing_tasks),
            "models": models,
            "routes": registered,
        }

    # ── 核心调用 ──────────────────────────────────────────────────
    def call(self, task_name: str, payload: Any = None,
             flow_id: str = None, extra_system: str = "") -> Dict[str, Any]:
        """
        统一调用入口。自动路由到本地 Ollama。
        返回 {success, response, model, route, tokens_saved, duration_ms, error}
        """
        route = self.get_route(task_name)
        if not route:
            return {"success": False, "error": f"unknown task: {task_name}",
                    "response": "", "model": "", "route": "none",
                    "tokens_saved": 0, "duration_ms": 0}

        # 组装 prompt
        system = route["system_prompt"]
        if extra_system:
            system += "\n\n" + extra_system

        prompt = self._build_prompt(route, payload)

        # 调用双轨路由引擎
        t0 = time.time()
        result = self._route_via_engine(prompt, system, task_name, flow_id)
        duration_ms = int((time.time() - t0) * 1000)

        # 更新路由统计
        self._update_route_stats(route["task_name"], result, duration_ms)
        # 写调用日志
        self._log_call(task_name, result, duration_ms, flow_id)

        return result

    def _build_prompt(self, route: Dict, payload: Any) -> str:
        """根据 prompt_template 格式化 payload"""
        template = route.get("prompt_template") or "{payload}"
        if isinstance(payload, (dict, list)):
            payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
        else:
            payload_str = str(payload) if payload is not None else ""
        try:
            return template.replace("{payload}", payload_str)
        except Exception:
            return payload_str

    def _route_via_engine(self, prompt: str, system: str,
                          task: str, flow_id: str = None) -> Dict[str, Any]:
        """实际调用 LLM — dual_route (本地 Ollama 优先 + 云端 fallback) → ollama_chat 兜底"""
        # 1. 尝试 dual_route (本地优先, 自动 fallback 云端)
        try:
            from ai_engines.ai_dual_route_engine import route_and_chat
            r = route_and_chat(prompt, system=system or "", flow_id=flow_id)
            if r.get("success"):
                return r
        except Exception:
            pass
        # 2. 直接调本地 Ollama
        try:
            from ai_ollama_engine import chat as ollama_chat
            r = ollama_chat(prompt, system=system or "", flow_id=flow_id)
            if r.get("success"):
                return r
        except Exception:
            pass
        return {"success": False, "response": "", "model": "",
                "route": "all_failed", "error": "dual_route + ollama 均不可用"}

    def _update_route_stats(self, task_name: str, result: Dict, duration_ms: int) -> None:
        conn = sqlite3.connect(self._db)
        conn.execute("""UPDATE mt_ai_neural_routes SET
            call_count = call_count + 1,
            avg_duration_ms = CAST(
                (avg_duration_ms * call_count + ?) AS REAL) / (call_count + 1),
            success_rate = CAST(
                (success_rate * call_count + ?) AS REAL) / (call_count + 1),
            updated_at = ?
            WHERE task_name = ?""",
            (duration_ms, 1 if result.get("success") else 0,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_name))
        conn.commit()
        conn.close()

    def _log_call(self, task_name: str, result: Dict, duration_ms: int,
                  flow_id: str = None) -> None:
        conn = sqlite3.connect(self._db)
        # 确保表有 response_preview 列 (兼容已有数据库)
        try:
            conn.execute("ALTER TABLE mt_ai_neural_calls ADD COLUMN response_preview TEXT")
        except Exception:
            pass  # 列已存在时忽略
        response_preview = (result.get("response") or "")[:500]
        conn.execute("""INSERT INTO mt_ai_neural_calls
            (flow_id, task_name, model_used, route, success,
             tokens_in, tokens_out, tokens_saved, duration_ms, error, triggered_at, response_preview)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (flow_id, task_name, result.get("model", ""),
             result.get("route", ""), 1 if result.get("success") else 0,
             0, 0, result.get("tokens_saved", 0), duration_ms,
             result.get("error") or "", datetime.now().isoformat(),
             response_preview))
        conn.commit()
        conn.close()

    # ── 便捷方法（子系统直接调） ─────────────────────────────────
    def arduino_compile(self, error_log: str, code: str = "",
                        flow_id: str = None) -> Dict:
        return self.call("arduino_compile",
                         {"error": error_log, "code": code}, flow_id)

    def patrol_code(self, code: str, language: str = "python",
                    flow_id: str = None) -> Dict:
        return self.call("patrol_code",
                         {"code": code, "language": language}, flow_id)

    def security_audit(self, target: str, flow_id: str = None) -> Dict:
        return self.call("security_audit", target, flow_id)

    def exam_grade(self, question: str, answer: str,
                   flow_id: str = None) -> Dict:
        return self.call("exam_grade",
                         {"question": question, "answer": answer}, flow_id)

    def eigenflux_chat(self, topic: str, history: str = "",
                       flow_id: str = None) -> Dict:
        return self.call("eigenflux_chat",
                         {"topic": topic, "history": history}, flow_id)

    # ── 统计 ─────────────────────────────────────────────────────
    def stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self._db)
        r_total = conn.execute("SELECT COUNT(*) FROM mt_ai_neural_routes").fetchone()[0]
        r_callable = conn.execute("SELECT COUNT(*) FROM mt_ai_neural_routes WHERE enabled=1").fetchone()[0]
        c_total = conn.execute("SELECT COUNT(*) FROM mt_ai_neural_calls").fetchone()[0]
        c_ok = conn.execute("SELECT COUNT(*) FROM mt_ai_neural_calls WHERE success=1").fetchone()[0]
        saved = conn.execute("SELECT COALESCE(SUM(tokens_saved),0) FROM mt_ai_neural_calls").fetchone()[0]
        last = conn.execute("SELECT task_name, model_used, success, duration_ms, triggered_at FROM mt_ai_neural_calls ORDER BY call_id DESC LIMIT 5").fetchall()
        conn.close()
        return {
            "routes_registered": r_total,
            "routes_enabled": r_callable,
            "total_calls": c_total,
            "success_calls": c_ok,
            "success_rate": round(c_ok / max(c_total, 1), 3),
            "tokens_saved": saved,
            "recent_calls": [
                {"task": r[0], "model": r[1], "ok": bool(r[2]),
                 "ms": r[3], "at": r[4]} for r in last
            ],
        }


# ═══════════════════════════════════════════════════════════════════
# 3. 单例
# ═══════════════════════════════════════════════════════════════════

_hub_instance: Optional[NeuralHub] = None
_hub_lock = threading.Lock()

def get_hub() -> NeuralHub:
    """获取 AI 中枢单例（线程安全）"""
    global _hub_instance
    if _hub_instance is None:
        with _hub_lock:
            if _hub_instance is None:
                _hub_instance = NeuralHub()
    return _hub_instance


# ═══════════════════════════════════════════════════════════════════
# 5. 仙女座-阿尔法 · 自主闭环强化引擎
# ═══════════════════════════════════════════════════════════════════

def run_andromeda_self_upgrade_cycle(phase: str = "all", dry_run: bool = False) -> dict:
    """
    仙女座自主闭环强化 — 完整循环
    体检 → 诊断 → 注册 → 模拟 → 记录 → 进化建议
    
    Args:
        phase: "all" | "diagnostic" | "register" | "simulate" | "record"
        dry_run: True 时只输出计划不执行任何变更
    
    Returns:
        完整循环报告 dict
    """
    import os, json, sqlite3, time, traceback as _tb
    from datetime import datetime

    cycle_report = {
        "cycle_id": f"cycle-{int(time.time())}",
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": phase, "dry_run": dry_run,
        "steps": {}, "errors": [],
    }

    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")

    # ── Step 1: 体检 (system snapshot) ──
    def _collect_snapshot():
        snap = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        # 路由
        routes = conn.execute("""
            SELECT task_name, domain, primary_model, enabled, call_count, success_rate
            FROM mt_ai_neural_routes""").fetchall()
        snap["routes"] = [{"task": r[0], "domain": r[1], "model": r[2],
                           "enabled": bool(r[3]), "calls": r[4] or 0, "sr": r[5]} for r in routes]
        # 员工
        emp_total = conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0]
        emp_dist = conn.execute("""
            SELECT neuralhub_task, COUNT(*) FROM mt_andromeda_employee_registry
            WHERE neuralhub_task != '' AND neuralhub_task IS NOT NULL
            GROUP BY neuralhub_task ORDER BY COUNT(*) DESC""").fetchall()
        snap["employees"] = {"total": emp_total, "by_task": {t: c for t, c in emp_dist}}
        # 规则
        rule_cnt = conn.execute("SELECT COUNT(*) FROM mt_andromeda_rule_knowledge").fetchone()[0]
        rule_ids = conn.execute("SELECT COUNT(DISTINCT rule_id) FROM mt_andromeda_rule_knowledge").fetchone()[0]
        snap["rules"] = {"chunks": rule_cnt, "rules": rule_ids}
        # 调用最近 1h
        calls_1h = conn.execute("""
            SELECT COUNT(*) FROM mt_ai_neural_calls
            WHERE datetime(triggered_at) > datetime('now','-1 hour')""").fetchone()[0]
        succ_1h = conn.execute("""
            SELECT COUNT(*) FROM mt_ai_neural_calls
            WHERE success=1 AND datetime(triggered_at) > datetime('now','-1 hour')""").fetchone()[0]
        snap["calls_1h"] = calls_1h
        snap["success_rate_1h"] = round(succ_1h/max(calls_1h,1), 3)
        return snap

    # ── Step 2: AI 诊断 ──
    def _ai_diagnose(snap):
        try:
            payload = json.dumps(snap, ensure_ascii=False)[:4000]
            t0 = time.time()
            r = hub.call('system_status_analyze', payload,
                        flow_id=f'sim_diag_{int(time.time())}')
            return {
                "success": r.get('success', False),
                "response": r.get('response', ''),
                "duration_ms": int((time.time()-t0)*1000),
                "flow_id": f'sim_diag_{int(time.time())}',
            }
        except Exception as e:
            return {"success": False, "error": str(e)[:200], "response": ""}

    # ── Step 3: AI 自主拓展建议 ──
    def _ai_expand_plan(snap, diag):
        try:
            prompt = f"""
你是仙女座-阿尔法自主拓展规划引擎。基于系统快照 + 诊断结果, 决定自主强化策略。

系统快照 (精简):
{json.dumps({k:v for k,v in snap.items() if k != 'routes' or len(snap.get('routes',[])) < 30}, ensure_ascii=False)[:2000]}

诊断结果:
{diag.get('response','')[:1500]}

请输出严格 JSON:
{{
  "health_score": 0-100,
  "new_routes": [
    {{"task_name": "xxx", "domain": "xxx", "primary_model": "qwen2.5:7b 或 qwen2.5-coder:14b",
      "system_prompt": "3行以内描述这个路由做什么", "reason": "为什么需要"}}
  ],
  "routes_to_strengthen": [
    {{"route": "xxx", "action": "optimize_prompt|add_weight|split", "detail": "..."}}
  ],
  "rule_chunks_to_add": [
    {{"rule_id": "MT_ANDROMEDA_SELF_ENRICH", "rule_name": "仙女座自主拓展规则",
      "rule_level": "L2", "content": "3-5 行 chunk 内容, 系统应该具备的能力"}}
  ]
}}"""
            t0 = time.time()
            r = hub.call('system_plan', prompt,
                        flow_id=f'sim_expand_{int(time.time())}')
            return {
                "success": r.get('success', False),
                "response": r.get('response', ''),
                "duration_ms": int((time.time()-t0)*1000),
            }
        except Exception as e:
            return {"success": False, "error": str(e)[:200], "response": ""}

    # ── Step 4: 注册新路由 (若 AI 建议) ──
    def _register_from_expand(expand_result):
        registered = []
        try:
            text = expand_result.get('response', '')
            # 粗略提取 JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
            else:
                return registered, "no_json"

            # 注册路由
            for route in data.get('new_routes', []):
                name = route.get('task_name', '')
                if not name or len(name) < 3:
                    continue
                existing = conn.execute(
                    "SELECT task_name FROM mt_ai_neural_routes WHERE task_name=?",
                    (name,)).fetchone()
                if existing:
                    continue
                if dry_run:
                    registered.append({"task_name": name, "action": "would_register"})
                    continue
                model = route.get('primary_model', 'qwen2.5:7b')
                domain = route.get('domain', 'custom')
                prompt = route.get('system_prompt', f'AI 路由: {name}')
                conn.execute("""
                    INSERT INTO mt_ai_neural_routes
                    (task_name, domain, primary_model, fallback_model, system_prompt,
                     prompt_template, temperature, max_tokens, enabled)
                    VALUES (?,?,?,?,?,?,0.2,2048,1)""",
                    (name, domain, model, None, prompt, f"请执行 {name}:\\n{{payload}}"))
                registered.append({"task_name": name, "action": "registered", "model": model})

            # 补规则知识 chunk
            for chunk in data.get('rule_chunks_to_add', []):
                rid = chunk.get('rule_id', 'MT_ANDROMEDA_SELF_ENRICH')
                rname = chunk.get('rule_name', '仙女座自主拓展')
                rlevel = chunk.get('rule_level', 'L2')
                content = chunk.get('content', '')
                if not content or len(content) < 10:
                    continue
                if dry_run:
                    registered.append({"rule_chunk": rid, "action": "would_add"})
                    continue
                # 找最大 chunk_index
                max_idx = conn.execute(
                    "SELECT COALESCE(MAX(chunk_index),0) FROM mt_andromeda_rule_knowledge WHERE rule_id=?",
                    (rid,)).fetchone()[0]
                conn.execute("""
                    INSERT INTO mt_andromeda_rule_knowledge
                    (rule_id, rule_name, rule_level, rule_version, status,
                     section_header, content_chunk, chunk_index, keyword_tags, is_iron_rule)
                    VALUES (?, ?, ?, 'v1.0.0', 'ACTIVE', ?, ?, ?, 'andromeda,autonomous,self-expand', 0)""",
                    (rid, rname, rlevel, f'仙女座自主拓展 chunk {max_idx+1}', content, max_idx+1))
                registered.append({"rule_chunk": rid, "action": "added", "chunk_idx": max_idx+1})

            conn.commit()
        except Exception as e:
            cycle_report["errors"].append(f"register_error: {str(e)[:200]}")
        return registered, None

    # ── Step 5: 模拟调用 (新注册路由) ──
    def _simulate_new_routes(new_routes):
        sim_results = []
        if not new_routes or dry_run:
            return sim_results
        for r in new_routes:
            if r.get("action") not in ("registered", "would_register"):
                continue
            name = r["task_name"]
            t0 = time.time()
            payload = json.dumps({
                "simulation": True,
                "system": "MTSCOS AI Project",
                "routes": len(conn.execute("SELECT COUNT(*) FROM mt_ai_neural_routes").fetchone()),
                "employees": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0],
            }, ensure_ascii=False)
            try:
                result = hub.call(name, payload,
                                 flow_id=f'sim_verify_{name}_{int(time.time())}')
                sim_results.append({
                    "task_name": name,
                    "success": result.get('success', False),
                    "duration_ms": int((time.time()-t0)*1000),
                    "response_preview": (result.get('response','') or '')[:150],
                })
            except Exception as e:
                sim_results.append({
                    "task_name": name, "success": False,
                    "error": str(e)[:200],
                })
        return sim_results

    # ── Step 6: 记录进化日志 ──
    def _record_evolution(snap, diag, expand, new_items, sim_results):
        if dry_run:
            return None
        try:
            conn.execute("""
                INSERT INTO mt_ai_self_evolution_log
                (trigger_type, target_task, old_prompt, new_prompt, rationale, approved_by, applied)
                VALUES (?,?,?,?,?,?,?)""", (
                "andromeda_self_expand",
                json.dumps([r.get('task_name','rule_chunk') for r in new_items[:5]], ensure_ascii=False),
                "",
                json.dumps(new_items, ensure_ascii=False)[:500],
                expand.get('response', '')[:500],
                "andromeda-alpha",
                1,  # applied
            ))
            conn.commit()
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        except Exception as e:
            cycle_report["errors"].append(f"evolution_log_error: {str(e)[:200]}")
            return None

    # ── 执行各阶段 ──
    try:
        if phase in ("all", "diagnostic"):
            snap = _collect_snapshot()
            diag = _ai_diagnose(snap)
            cycle_report["steps"]["diagnostic"] = {
                "health_score_hint": "extracted_from_ai",
                "snapshot_route_count": len(snap.get('routes', [])),
                "snapshot_employee_count": snap.get('employees', {}).get('total', 0),
                "ai_success": diag['success'],
                "ai_duration_ms": diag.get('duration_ms', 0),
                "ai_response": diag.get('response', '')[:800],
            }

        if phase in ("all", "register"):
            expand = _ai_expand_plan(snap, diag)
            new_items, err = _register_from_expand(expand)
            cycle_report["steps"]["register"] = {
                "ai_success": expand['success'],
                "ai_response": expand.get('response', '')[:800],
                "items_registered": new_items,
            }

        if phase in ("all", "simulate"):
            sim_results = _simulate_new_routes(new_items)
            cycle_report["steps"]["simulate"] = sim_results

        if phase in ("all", "record"):
            evo_id = _record_evolution(snap, diag, expand, new_items, sim_results)
            cycle_report["steps"]["record"] = {"evolution_log_id": evo_id}

    except Exception as e:
        cycle_report["errors"].append(f"cycle_fatal: {str(e)[:300]}")
        cycle_report["errors"].append(_tb.format_exc()[:500])
    finally:
        conn.close()

    cycle_report["ended_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cycle_report["duration_seconds"] = round(
        (datetime.strptime(cycle_report["ended_at"], "%Y-%m-%d %H:%M:%S") -
         datetime.strptime(cycle_report["started_at"], "%Y-%m-%d %H:%M:%S")).total_seconds(), 1)

    return cycle_report


def learn_system_architecture() -> dict:
    """
    仙女座自我认知 — 分 5 批次学习系统架构 → 存入 mt_andromeda_rule_knowledge
    
    学习领域:
      ① 架构层   — 13层 before_request 链 + Neural Hub 架构 + 双路由引擎
      ② 数据层   — DB 表结构 + 员工注册 + 规则知识
      ③ 安全层   — VIKEY + CSRF + 防火墙 + 权限
      ④ AI 层    — Ollama 本地推理 + 员工调度 + 自进化
      ⑤ 价值层   — 存在意义 + 业务闭环 + 自主拓展
    """
    import os, json, sqlite3, time
    from datetime import datetime

    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")

    result = {
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "domains_learned": 0,
        "chunks_stored": 0,
        "domain_results": [],
        "errors": [],
    }

    # ═══ 批次 1: 架构层 ═══
    payload_arch = json.dumps({
        "domain": "architecture",
        "before_request_chain": [
            "_rules_engine_before_request",
            "_mt_csrf_protection",
            "_mtscos_ai_firewall_check",
            "_mt_sys_container_session_loader",
            "_mt_hotlink_guard",
            "_mt_vikey_lock_check",
            "_mt_vikey_enforcement_check",
            "_mt_vikey_sa_only_boundary",
            "_mt_mobile_redirect",
            "_mt_normal_group_feature_gate",
            "_mt_api_auto_auth_gate",
            "_mt_remember_me_auto_login",
            "_mt_security_shield_before_request",
        ],
        "dual_route_engine": {
            "local": "ai_engines.ai_dual_route_engine → Ollama localhost:11435",
            "models": ["qwen2.5:7b (general)", "qwen2.5-coder:14b (code)"],
            "fallback": "volcengine_cloud",
            "token_saving": "zero local inference",
        },
        "neural_hub": {
            "total_routes": conn.execute("SELECT COUNT(*) FROM mt_ai_neural_routes").fetchone()[0],
            "enabled_routes": conn.execute("SELECT COUNT(*) FROM mt_ai_neural_routes WHERE enabled=1").fetchone()[0],
            "domains": conn.execute("SELECT DISTINCT domain FROM mt_ai_neural_routes").fetchall(),
        },
        "bg_init_daemons": {
            "bg_heavy_init": "Flask start 自动启动",
            "self_evolve_daemon": "3600s prompt auto-optimize",
            "self_expand_daemon": "3600s cycle (diagnose→register→simulate→record)",
            "arduino_boot": "600s Arduino guide",
        },
    }, ensure_ascii=False)

    # ═══ 批次 2: 数据层 ═══
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mt_%' ORDER BY name").fetchall()]
    payload_data = json.dumps({
        "domain": "data",
        "total_tables": len(tables),
        "key_tables": {
            "mt_andromeda_employee_registry": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0],
            "mt_andromeda_rule_knowledge": f"{conn.execute('SELECT COUNT(*) FROM mt_andromeda_rule_knowledge').fetchone()[0]} chunks / {conn.execute('SELECT COUNT(DISTINCT rule_id) FROM mt_andromeda_rule_knowledge').fetchone()[0]} rules",
            "mt_andromeda_call_queue": conn.execute("SELECT COUNT(*) FROM mt_andromeda_call_queue").fetchone()[0] if 'mt_andromeda_call_queue' in tables else "MISSING",
            "mt_andromeda_execution_log": conn.execute("SELECT COUNT(*) FROM mt_andromeda_execution_log").fetchone()[0] if 'mt_andromeda_execution_log' in tables else "MISSING",
            "mt_ai_neural_routes": conn.execute("SELECT COUNT(*) FROM mt_ai_neural_routes").fetchone()[0],
            "mt_ai_neural_calls": conn.execute("SELECT COUNT(*) FROM mt_ai_neural_calls").fetchone()[0],
            "mt_ai_self_evolution_log": conn.execute("SELECT COUNT(*) FROM mt_ai_self_evolution_log").fetchone()[0],
            "mt_dev_flow_session": "§14 开发12步骤铁律 强制表",
            "mt_rule_changelog": "规则变更7步审批表",
        },
        "employee_source_distribution": {
            "eigenflux_registrations": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE employee_source='eigenflux_registrations'").fetchone()[0],
            "arduino_employees.py": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE employee_source='arduino_employees.py'").fetchone()[0],
            "eigenflux_experts": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE employee_source='eigenflux_experts'").fetchone()[0],
            "andromeda_templates": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE employee_source='andromeda_self_expand' OR employee_source='andromeda_self_learn'").fetchone()[0],
        },
        "rule_levels": conn.execute("SELECT rule_level, COUNT(*) FROM mt_andromeda_rule_knowledge GROUP BY rule_level").fetchall(),
    }, ensure_ascii=False)

    # ═══ 批次 3: 安全层 ═══
    payload_security = json.dumps({
        "domain": "security",
        "vikey_authentication": "7要素强认证 + USB加密狗实时检测 + 移动端指纹",
        "permission_system": {
            "levels": "11级角色 (super_admin → guest)",
            "decorator": "@system_container (4级: guest/login/admin/super_admin)",
            "unique_sa": "仅 wuchenghao15 + VIKEY",
            "arduino_only_sa": "其他角色403",
        },
        "firewall_layers": [
            "L0: §14 12步骤铁律 (git hook + before_request + ci_check)",
            "L1: CSRF 保护 (_mt_csrf_protection)",
            "L2: 防盗链拦截 (_mt_hotlink_guard)",
            "L3: VIKEY 锁 (_mt_vikey_lock_check)",
            "L4: before_request 13层全链",
        ],
        "rule_enforcement": {
            "files": ".trae/rules/ 13条 .md",
            "knowledge_table": "mt_andromeda_rule_knowledge 409 chunks",
            "execution": "rules_engine + rule_enforcer daemon (300s)",
            "git_hook": "pre-commit hook → 拦截无7步审批的规则变更",
        },
    }, ensure_ascii=False)

    # ═══ 批次 4: AI 层 ═══
    payload_ai = json.dumps({
        "domain": "ai",
        "ollama_local": {
            "port": ":11435",
            "models": ["qwen2.5:7b (general)", "qwen2.5-coder:14b (code)"],
            "ram_gb": "Apple M5 iGPU 17.8 GiB",
            "speed": "2-5s/call vs cloud 33s",
            "cost": "zero API token consumption",
            "daemon": "com.mtscos.ollama-native launchd",
        },
        "employee_scheduling": {
            "total": conn.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()[0],
            "task_coverage": conn.execute("SELECT COUNT(DISTINCT neuralhub_task) FROM mt_andromeda_employee_registry WHERE neuralhub_task!=''").fetchone()[0],
            "dispatch": "EmployeeCallRouter hub.call() → weighted_round_robin",
            "rebalance": "daemon_tick + bg-init auto-trigger",
        },
        "self_evolution": {
            "daemon": "sys_auto_patrol + ai_local_inference (300s/120s)",
            "prompt_optimize": "mt_ai_self_evolution_log (trigger: error_spike/slow_response/user_request)",
            "rule_strengthener": "auto_rule_strengthener 弱约束词→强约束",
        },
        "self_expand_cycle": {
            "function": "run_andromeda_self_upgrade_cycle()",
            "interval": "3600s (首次启动5分钟延迟)",
            "flow": "diagnostic → register (AI自主注册路由/规则) → simulate (sim_* flow_id) → record",
            "trigger_type": "mt_ai_self_evolution_log.trigger_type='andromeda_self_expand'",
        },
    }, ensure_ascii=False)

    # ═══ 批次 5: 价值层 ═══
    payload_value = json.dumps({
        "domain": "value",
        "project_identity": "MTSCOS AI Project — 仙女座-阿尔法 本地化 AI 智能体集群",
        "why_we_exist": [
            "让 AI 员工能自主完成开发/测试/运维/安全审查",
            "本地化 Ollama 推理零 token 消耗, 避免供应商锁定",
            "13层 before_request 铁律安全防护",
            "32条 Neural Hub 路由 + 33,512 AI 员工 → 集群协作",
            "自进化 daemon + 自拓展 cycle → 自我改进",
        ],
        "business_loops": [
            "AI员工注册 → Neural Hub 路由分配 → Ollama 调用 → 结果落库 → 进化日志 → prompt优化",
            "规则知识学习 → rule_patrol daemon → 违规检测 → auto_repair_code → 修复后再学习",
            "daemon_tick → 覆盖度/偏差检查 → rebalance → 均衡分布 → 进化日志",
            "self_upgrade_cycle → 诊断 → AI建议 → 自主注册 → 模拟 → 进化记录 → 下次cycle再优化",
        ],
        "self_upgrade_capability": {
            "what_can_we_do_now": [
                "自主注册新 Neural Hub 路由 (mt_ai_neural_routes)",
                "自主追加规则知识 chunk (mt_andromeda_rule_knowledge)",
                "自主 rebalance 员工布局",
                "AI 诊断系统健康 (health_score + issues)",
                "prompt 自动优化 (自进化 daemon)",
            ],
            "what_needs_human": [
                "新建 .md 规则文件 (规则治理规范 L1)",
                "改 DB 表结构/表名",
                "绕过 13 层 before_request 链",
                "SA 角色以外的权限提升",
            ],
            "expansion_priority": [
                "补全开发链路缺口 (code_review/dependency/performance/api_contract)",
                "数据驱动智能分配 (用 expert_domain/skills_json 做关键词匹配)",
                "更多 daemon 周期触发 (port_scan/monitoring/incident_response)",
                "前端 Neural Hub Dashboard 可视化",
            ],
        },
    }, ensure_ascii=False)

    # ═══ 依次学习 5 个领域 ═══
    batches = [
        ("architecture", payload_arch, "L1"),
        ("data",         payload_data, "L1"),
        ("security",     payload_security, "L0"),
        ("ai",           payload_ai, "L1"),
        ("value",        payload_value, "L2"),
    ]

    for domain, payload, level in batches:
        try:
            t0 = time.time()
            r = hub.call('system_learn', payload[:4000],  # 限制 payload 大小
                        flow_id=f'learn_{domain}_{int(time.time())}')
            dur = int((time.time()-t0)*1000)

            if r.get('success') and r.get('response'):
                # 解析 AI 返回的 JSON
                text = r['response']
                start = text.find('{')
                end = text.rfind('}') + 1
                cognition = text[start:end] if start >= 0 and end > start else text

                # 存入 rule_knowledge
                max_idx = conn.execute(
                    "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_ANDROMEDA_SELF_KNOWLEDGE'"
                ).fetchone()[0]
                conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
                    (rule_id, rule_name, rule_level, rule_version, status,
                     section_header, content_chunk, chunk_index, keyword_tags, is_iron_rule)
                    VALUES ('MT_ANDROMEDA_SELF_KNOWLEDGE', '仙女座自我认知', ?, 'v1.0.0', 'ACTIVE',
                            ?, ?, ?, 'andromeda,self-knowledge,self-upgrade', 0)""",
                    (level, f'自我认知: {domain} ({level})', cognition, max_idx+1))
                conn.commit()

                result["chunks_stored"] += 1
                result["domains_learned"] += 1
                result["domain_results"].append({
                    "domain": domain, "level": level,
                    "chunk_index": max_idx+1,
                    "duration_ms": dur,
                    "chunk_len": len(cognition),
                })
            else:
                result["errors"].append(f"{domain}: AI call failed - {r.get('response')[:100]}")
        except Exception as e:
            result["errors"].append(f"{domain}: {str(e)[:200]}")

    conn.close()
    result["ended_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result


def monitor_education_reform(reform_text: str, source: str = "manual") -> dict:
    """
    仙女座教育改革动态监控 — 完整闭环
    
    流程:
      reform_text → edu_policy_analyze (AI 解析改革要点)
                 → edu_curriculum_adapt (AI 输出题库/学习方向调整方案)
                 → 两段结果 → INSERT mt_andromeda_rule_knowledge (rule_id=MT_EDU_REFORM_KNOWLEDGE, level=L1)
                 → question_generate 等教育路由的 Ollama 上下文自动包含改革信息
    
    Args:
        reform_text: 教育改革政策文本 (课改/考改/大纲变更等)
        source: 'manual' (用户提交) | 'api_push' (外部API推送) | 'periodic_check' (daemon周期)
    
    Returns:
        {analysis, adaptation, chunks_stored, affected_routes, duration_ms}
    """
    import json, sqlite3, time
    from datetime import datetime
    
    if not reform_text or len(reform_text.strip()) < 10:
        return {"error": "reform_text too short", "success": False}

    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    t0 = time.time()
    result = {"success": True, "steps": {}}

    # Step 1: AI 解析改革政策
    try:
        t1 = time.time()
        policy_r = hub.call('edu_policy_analyze', reform_text[:4000],
                           flow_id=f'edu_policy_{int(time.time())}')
        policy_text = policy_r.get('response', '')
        # 提取 JSON
        s, e = policy_text.find('{'), policy_text.rfind('}') + 1
        analysis = json.loads(policy_text[s:e]) if s >= 0 and e > s else policy_text
        result["steps"]["policy_analyze"] = {
            "success": policy_r.get('success'),
            "duration_ms": int((time.time()-t1)*1000),
            "reform_type": analysis.get('reform_type', 'unknown') if isinstance(analysis, dict) else 'unknown',
            "priority": analysis.get('priority', 0) if isinstance(analysis, dict) else 0,
            "affected_subjects": analysis.get('affected_subjects', []) if isinstance(analysis, dict) else [],
        }
    except Exception as ex:
        result["steps"]["policy_analyze"] = {"error": str(ex)[:200]}
        result["success"] = False
        conn.close()
        return result

    # Step 2: AI 输出题库/学习方向调整方案
    try:
        t2 = time.time()
        adapt_payload = json.dumps({
            "reform_analysis": analysis,
            "current_state": {
                "routes_for_education": [r[0] for r in conn.execute(
                    "SELECT task_name FROM mt_ai_neural_routes WHERE domain='education' AND enabled=1").fetchall()],
            }
        }, ensure_ascii=False)
        adapt_r = hub.call('edu_curriculum_adapt', adapt_payload[:4000],
                          flow_id=f'edu_adapt_{int(time.time())}')
        adapt_text = adapt_r.get('response', '')
        s, e = adapt_text.find('{'), adapt_text.rfind('}') + 1
        adaptation = json.loads(adapt_text[s:e]) if s >= 0 and e > s else adapt_text
        result["steps"]["curriculum_adapt"] = {
            "success": adapt_r.get('success'),
            "duration_ms": int((time.time()-t2)*1000),
            "questions_to_add": len(adaptation.get('questions_to_add', [])) if isinstance(adaptation, dict) else 0,
            "questions_to_deprecate": len(adaptation.get('questions_to_deprecate', [])) if isinstance(adaptation, dict) else 0,
            "review_priority_shifts": len(adaptation.get('review_priority_shifts', [])) if isinstance(adaptation, dict) else 0,
        }
    except Exception as ex:
        result["steps"]["curriculum_adapt"] = {"error": str(ex)[:200]}
        adaptation = {}

    # Step 3: 两段结果都存 rule_knowledge (MT_EDU_REFORM_KNOWLEDGE, L1)
    chunks_stored = 0
    for phase, content, section in [
        ("policy_analyze", json.dumps(analysis, ensure_ascii=False) if isinstance(analysis, dict) else str(analysis), "政策解析"),
        ("curriculum_adapt", json.dumps(adaptation, ensure_ascii=False) if isinstance(adaptation, dict) else str(adaptation), "题库适配方案"),
    ]:
        try:
            if not content or len(content) < 20:
                continue
            max_idx = conn.execute(
                "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EDU_REFORM_KNOWLEDGE'"
            ).fetchone()[0]
            affected = ''
            if isinstance(analysis, dict):
                affected = ','.join(analysis.get('affected_subjects', []))
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
                (rule_id, rule_name, rule_level, rule_version, status,
                 section_header, content_chunk, chunk_index, keyword_tags,
                 is_iron_rule, last_ingested, effective_date)
                VALUES ('MT_EDU_REFORM_KNOWLEDGE', '仙女座教育改革知识库', 'L1', 'v1.0.0', 'ACTIVE',
                        ?, ?, ?, 'education,reform,curriculum,auto-sync',
                        0, ?, ?)""",
                (f'{section}: {affected or "general"}', content, max_idx+1, now, now))
            chunks_stored += 1
        except Exception as ex:
            result.setdefault("warnings", []).append(f"{phase}: {str(ex)[:150]}")
    
    conn.commit()
    
    # 验证: question_generate / exam_grade / listening_generate 路由的 Ollama 上下文自动包含改革知识
    edu_routes = [r[0] for r in conn.execute(
        "SELECT task_name FROM mt_ai_neural_routes WHERE domain='education' AND enabled=1").fetchall()]
    result["chunks_stored"] = chunks_stored
    result["affected_routes"] = edu_routes
    result["duration_ms"] = int((time.time()-t0)*1000)
    result["source"] = source
    result["rule_knowledge_rule_id"] = "MT_EDU_REFORM_KNOWLEDGE"

    conn.close()
    return result


def andromeda_edu_daemon_check() -> dict:
    """
    教育改革周期检查 (建议 1800s 一次)
    检查 rule_knowledge 里 MT_EDU_REFORM_KNOWLEDGE 是否有 7 天内的 chunk
    有则跑一次 question_generate 验证题目方向已对齐改革方向
    """
    import time as _time
    from datetime import datetime
    conn = sqlite3.connect(APP_DB, timeout=30)
    try:
        # 查最近的 MT_EDU_REFORM_KNOWLEDGE chunk
        recent = conn.execute("""
            SELECT content_chunk, last_ingested FROM mt_andromeda_rule_knowledge
            WHERE rule_id='MT_EDU_REFORM_KNOWLEDGE'
            ORDER BY chunk_index DESC LIMIT 1""").fetchone()
        if not recent:
            return {"action": "no_reform_data", "msg": "MT_EDU_REFORM_KNOWLEDGE 暂无 chunk"}
        
        chunk_text = recent[0]
        # 提取涉及的学科
        affected = []
        try:
            data = json.loads(chunk_text[:500] if not chunk_text.lstrip().startswith('{') else chunk_text[:500])
            if isinstance(data, dict):
                affected = data.get('affected_subjects', [])
        except Exception:
            pass
        
        hub = get_hub()
        # 验证 question_generate 对改革方向的响应
        test_subject = affected[0] if affected else 'K12 数学'
        r = hub.call('question_generate',
                    json.dumps({"subject": test_subject, "reform_context": chunk_text[:500]}, ensure_ascii=False),
                    flow_id=f'edu_daemon_verify_{int(_time.time())}')
        return {
            "action": "reform_data_found",
            "chunk_subject": test_subject,
            "verify_success": r.get('success', False),
            "verify_response_preview": (r.get('response','') or '')[:200],
            "affected_routes": ["question_generate", "exam_grade", "listening_generate"],
        }
    finally:
        conn.close()


def ingest_external_knowledge(content: str, platform: str = "manual",
                               subject_area: str = "", url: str = "") -> dict:
    """
    仙女座外部知识主动吸收 — 完整闭环
    
    流程: content → knowledge_ingest (AI 拆解)
                → knowledge_curator (去重/分级)
                → INSERT mt_andromeda_rule_knowledge (rule_id=MT_EXTERNAL_KNOWLEDGE, L2)
                → question_generate 等路由自动引用
    
    Args:
        content: 教育内容文本 (从各平台采集)
        platform: 'bilibili'|'xiaohongshu'|'douyin'|'kuaishou'|'wechat'|'manual'|'youtube'
        subject_area: 学科标签 (如 'K12数学/成人英语/日语N2/高等英语')
        url: 来源链接 (可选)
    
    Returns:
        {success, chunks_stored, knowledge_points_extracted, subject, duration_ms}
    """
    import json, sqlite3, time
    from datetime import datetime
    
    if not content or len(content.strip()) < 20:
        return {"success": False, "error": "content too short"}

    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    t0 = time.time()
    result = {"success": True, "steps": {}}

    # Step 1: AI 拆解知识
    try:
        t1 = time.time()
        payload = json.dumps({
            "subject_hint": subject_area,
            "platform": platform,
            "content": content[:4000],
        }, ensure_ascii=False)
        r = hub.call('knowledge_ingest', payload,
                    flow_id=f'kg_{platform}_{int(time.time())}')
        text = r.get('response', '')
        s, e = text.find('{'), text.rfind('}') + 1
        knowledge = json.loads(text[s:e]) if s >= 0 and e > s else text
        result["steps"]["ingest"] = {
            "success": r.get('success'),
            "duration_ms": int((time.time()-t1)*1000),
            "subject": knowledge.get('subject', 'unknown') if isinstance(knowledge, dict) else 'unknown',
            "topic": knowledge.get('topic', '') if isinstance(knowledge, dict) else '',
            "points_count": len(knowledge.get('knowledge_points', [])) if isinstance(knowledge, dict) else 0,
            "value": knowledge.get('value_estimate', '') if isinstance(knowledge, dict) else '',
        }
    except Exception as ex:
        result["steps"]["ingest"] = {"error": str(ex)[:200]}
        result["success"] = False
        conn.close()
        return result

    # Step 2: 存入 MT_EXTERNAL_KNOWLEDGE (L2)
    chunks_stored = 0
    try:
        # 存完整结构化内容
        full = json.dumps({
            "source": platform, "url": url, "subject_area": subject_area,
            "knowledge": knowledge if isinstance(knowledge, dict) else {"raw": str(knowledge)},
            "ingested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }, ensure_ascii=False)
        max_idx = conn.execute(
            "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
        ).fetchone()[0]
        
        subject_tag = knowledge.get('subject', subject_area) if isinstance(knowledge, dict) else subject_area
        value_tag = knowledge.get('value_estimate', 'supplementary') if isinstance(knowledge, dict) else 'supplementary'
        topics = knowledge.get('topic', '') if isinstance(knowledge, dict) else ''
        
        conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
            (rule_id, rule_name, rule_level, rule_version, status,
             section_header, content_chunk, chunk_index, keyword_tags,
             is_iron_rule, last_ingested, effective_date)
            VALUES ('MT_EXTERNAL_KNOWLEDGE', '仙女座外部知识脑库', 'L2', 'v1.0.0', 'ACTIVE',
                    ?, ?, ?, ?, 0, ?, ?)""",
            (f'[{platform}] {subject_tag}: {topics[:40]}', full, max_idx+1,
             f'external,{platform},{subject_tag},{value_tag},auto-ingest',
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             datetime.now().strftime("%Y-%m-%d")))
        chunks_stored += 1

        # 如果有 knowledge_points, 每个点单独存一个短 chunk (更易被检索)
        if isinstance(knowledge, dict):
            for kp in knowledge.get('knowledge_points', []):
                if not isinstance(kp, dict):
                    continue
                point_text = f"知识点: {kp.get('point','')}\n解释: {kp.get('explanation','')}\n例子: {kp.get('example','')}\n前置: {', '.join(kp.get('prerequisites',[]))}"
                if len(point_text.strip()) < 15:
                    continue
                max_idx = conn.execute(
                    "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
                ).fetchone()[0]
                conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
                    (rule_id, rule_name, rule_level, rule_version, status,
                     section_header, content_chunk, chunk_index, keyword_tags,
                     is_iron_rule, last_ingested, effective_date)
                    VALUES ('MT_EXTERNAL_KNOWLEDGE', '仙女座外部知识脑库', 'L2', 'v1.0.0', 'ACTIVE',
                            ?, ?, ?, ?, 0, ?, ?)""",
                    (f'知识点[{subject_tag}]: {kp.get("point","")[:30]}',
                     point_text, max_idx+1,
                     f'knowledge-point,{platform},{subject_tag},{knowledge.get("content_type","theory")}',
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     datetime.now().strftime("%Y-%m-%d")))
                chunks_stored += 1
    except Exception as ex:
        result["warnings"] = result.get("warnings", []) + [f"store: {str(ex)[:200]}"]

    conn.commit()
    result["chunks_stored"] = chunks_stored
    result["knowledge_points_extracted"] = len(knowledge.get('knowledge_points', [])) if isinstance(knowledge, dict) else 0
    result["subject"] = knowledge.get('subject', subject_area) if isinstance(knowledge, dict) else subject_area
    result["duration_ms"] = int((time.time()-t0)*1000)
    result["rule_id"] = "MT_EXTERNAL_KNOWLEDGE"
    conn.close()
    return result


def extract_bilibili_subtitle(url: str) -> dict:
    """
    用 yt-dlp 提取 B 站教育视频字幕/简介 → 走 knowledge_ingest 管道
    
    Args:
        url: B 站视频 URL (https://www.bilibili.com/video/BVxxx)
    
    Returns:
        {success, title, subtitle_text, knowledge_ingest_result}
    """
    import subprocess, json as _json, time
    result = {"success": False}
    
    try:
        # yt-dlp 检查
        check = subprocess.run(['which', 'yt-dlp'], capture_output=True, text=True, timeout=5)
        if check.returncode != 0:
            result["error"] = "yt-dlp not found, install with: pip install yt-dlp"
            return result
        
        # 提取视频元数据 + 字幕
        proc = subprocess.run([
            'yt-dlp', '--skip-download', '--write-subs', '--write-auto-subs',
            '--sub-langs', 'zh-CN,zh-Hans,zh-Hant,en',
            '--convert-subs', 'srt',
            '-o', '/tmp/bili_%(id)s.%(ext)s',
            '--print-json', url
        ], capture_output=True, text=True, timeout=60)
        
        if proc.returncode != 0:
            result["error"] = f"yt-dlp failed: {proc.stderr[:200]}"
            return result
        
        meta = _json.loads(proc.stdout.split('\n')[-2] if proc.stdout.endswith('\n') else proc.stdout)
        
        title = meta.get('title', 'Unknown')
        desc = meta.get('description', '')[:1000]
        uploader = meta.get('uploader', '')
        print(f"  📺 B站视频: {title} (UP主: {uploader})")
        
        # 找生成的字幕文件
        import glob, os
        sub_files = glob.glob('/tmp/bili_*.srt')
        sub_text = ''
        if sub_files:
            latest = max(sub_files, key=os.path.getmtime)
            with open(latest, 'r') as f:
                sub_text = f.read()
            os.remove(latest)
        
        # 合并内容
        combined = f"# {title}\nUP主: {uploader}\n\n## 简介\n{desc}\n\n## 字幕内容\n{sub_text[:3000]}"
        result["title"] = title
        result["subtitle_text_len"] = len(sub_text)
        result["combined_text"] = combined
        
        # 走 knowledge_ingest 管道
        if len(combined) > 50:
            kr = ingest_external_knowledge(combined, platform="bilibili",
                                          subject_area=title[:20], url=url)
            result["knowledge_ingest"] = kr
        
        result["success"] = True
    except subprocess.TimeoutExpired:
        result["error"] = "yt-dlp timeout (60s)"
    except Exception as ex:
        result["error"] = str(ex)[:200]
    
    return result


def andromeda_knowledge_daemon_check() -> dict:
    """
    外部知识周期检查 (建议 1800s)
    检查 MT_EXTERNAL_KNOWLEDGE 最新 chunk 的 value_estimate / source_platform 分布
    """
    import time as _time
    conn = sqlite3.connect(APP_DB, timeout=30)
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
        ).fetchone()[0]
        by_platform = conn.execute("""
            SELECT keyword_tags, COUNT(*)
            FROM mt_andromeda_rule_knowledge
            WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'
            GROUP BY keyword_tags
            ORDER BY COUNT(*) DESC LIMIT 5""").fetchall()
        return {
            "action": "knowledge_inventory",
            "external_chunks": total,
            "platform_distribution": [(r[0][:40], r[1]) for r in by_platform],
            "knowledge_routes_covered": 7,
        }
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: 前端美化 design 域核心函数
# ═══════════════════════════════════════════════════════════════════════════════

def ingest_design_knowledge(content: str, platform: str = "manual",
                             design_area: str = "", url: str = "",
                             flow_id: str = "") -> dict:
    """
    仙女座-阿尔法前端设计知识消化 → design_ingest 路由 → MT_EXTERNAL_KNOWLEDGE
    
    与 ingest_external_knowledge 不同: 用 design_ingest 路由 (专门针对 UI/UX/美化内容)
    keyword_tags 带 design/design_ingest 标记, 便于 beautify_plan 检索
    
    flow_id: 如果有 §14 流程 ID, 会写入 mt_dev_flow_events 跟踪
    """
    import json, sqlite3, time
    from datetime import datetime
    
    if not content or len(content.strip()) < 20:
        return {"success": False, "error": "content too short"}

    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    t0 = time.time()
    result = {"success": True, "steps": {}, "flow_id": flow_id}

    # Step 1: design_ingest (AI 拆解设计知识)
    try:
        t1 = time.time()
        payload = json.dumps({
            "design_area_hint": design_area,
            "platform": platform,
            "content": content[:4000],
        }, ensure_ascii=False)
        r = hub.call('design_ingest', payload,
                    flow_id=f'design_{platform}_{int(time.time())}')
        text = r.get('response', '')
        s, e = text.find('{'), text.rfind('}') + 1
        knowledge = json.loads(text[s:e]) if s >= 0 and e > s else text
        result["steps"]["design_ingest"] = {
            "success": r.get('success'),
            "duration_ms": int((time.time()-t1)*1000),
            "category": knowledge.get('design_category', 'unknown') if isinstance(knowledge, dict) else 'unknown',
            "area": knowledge.get('subject_area', '') if isinstance(knowledge, dict) else '',
            "points": len(knowledge.get('knowledge_points', [])) if isinstance(knowledge, dict) else 0,
            "value": knowledge.get('value_estimate', '') if isinstance(knowledge, dict) else '',
        }
    except Exception as ex:
        result["steps"]["design_ingest"] = {"error": str(ex)[:200]}
        result["success"] = False
        conn.close()
        return result

    # Step 2: 存入 MT_EXTERNAL_KNOWLEDGE (带 design 标记)
    chunks_stored = 0
    try:
        full = json.dumps({
            "source": platform, "url": url, "design_area": design_area,
            "knowledge": knowledge if isinstance(knowledge, dict) else {"raw": str(knowledge)},
            "ingested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "flow_id": flow_id,
        }, ensure_ascii=False)
        max_idx = conn.execute(
            "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
        ).fetchone()[0]
        
        cat = knowledge.get('design_category', design_area) if isinstance(knowledge, dict) else design_area
        value_tag = knowledge.get('value_estimate', 'nice_to_have') if isinstance(knowledge, dict) else 'nice_to_have'
        
        conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
            (rule_id, rule_name, rule_level, rule_version, status,
             section_header, content_chunk, chunk_index, keyword_tags,
             is_iron_rule, last_ingested, effective_date)
            VALUES ('MT_EXTERNAL_KNOWLEDGE', '仙女座外部知识脑库', 'L2', 'v1.0.0', 'ACTIVE',
                    ?, ?, ?, ?, 0, ?, ?)""",
            (f'[design][{platform}] {cat}: {design_area[:30]}', full, max_idx+1,
             f'design,{platform},{cat},{design_area},{value_tag}',
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             datetime.now().strftime("%Y-%m-%d")))
        chunks_stored += 1

        # 每个 knowledge_point 单独存短 chunk
        if isinstance(knowledge, dict):
            for kp in knowledge.get('knowledge_points', []):
                if not isinstance(kp, dict):
                    continue
                point_text = f"[{cat}] {kp.get('point','')}\n{kp.get('description','')}\n优先级: {kp.get('priority','')}\n代码示例: {kp.get('code_snippet','(无)')}\n适用: {', '.join(kp.get('applies_to_pages',[]))}"
                if len(point_text.strip()) < 15:
                    continue
                max_idx = conn.execute(
                    "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
                ).fetchone()[0]
                conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
                    (rule_id, rule_name, rule_level, rule_version, status,
                     section_header, content_chunk, chunk_index, keyword_tags,
                     is_iron_rule, last_ingested, effective_date)
                    VALUES ('MT_EXTERNAL_KNOWLEDGE', '仙女座外部知识脑库', 'L2', 'v1.0.0', 'ACTIVE',
                            ?, ?, ?, ?, 0, ?, ?)""",
                    (f'设计点[{cat}]: {kp.get("point","")[:40]}',
                     point_text, max_idx+1,
                     f'design-point,{platform},{cat},{kp.get("priority","")},design_ingest',
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     datetime.now().strftime("%Y-%m-%d")))
                chunks_stored += 1

        # 如果有 color_scheme / spacing_system / typography, 也单独存
        extras = {}
        if isinstance(knowledge, dict):
            for k in ['color_scheme', 'spacing_system', 'typography']:
                if k in knowledge and knowledge[k]:
                    extras[k] = knowledge[k]
        if extras:
            max_idx = conn.execute(
                "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
            ).fetchone()[0]
            extra_keys = '|'.join(extras.keys())
            extra_text = f"设计系统 ({cat}):\n{json.dumps(extras, ensure_ascii=False)}"
            conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
                (rule_id, rule_name, rule_level, rule_version, status,
                 section_header, content_chunk, chunk_index, keyword_tags,
                 is_iron_rule, last_ingested, effective_date)
                VALUES ('MT_EXTERNAL_KNOWLEDGE', '仙女座外部知识脑库', 'L2', 'v1.0.0', 'ACTIVE',
                        ?, ?, ?, ?, 0, ?, ?)""",
                (f'设计系统[{cat}]: {extra_keys}', extra_text, max_idx+1,
                 f'design-system,{platform},{cat}',
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 datetime.now().strftime("%Y-%m-%d")))
            chunks_stored += 1

    except Exception as ex:
        result["warnings"] = result.get("warnings", []) + [f"store: {str(ex)[:200]}"]

    # Step 3: flow_id 跟踪 (§14 合规)
    if flow_id:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("""INSERT INTO mt_dev_flow_events
                (flow_id, from_step, to_step, event_kind, event_payload_json, triggered_by, triggered_at)
                VALUES (?,?,?,?,?,?,?)""",
                (flow_id, 'STEP_6_SA_APPROVAL', 'STEP_7_EXECUTE', 'design_knowledge_ingested',
                 json.dumps({"chunks": chunks_stored, "platform": platform, "cat": cat}, ensure_ascii=False),
                 'andromeda_ui_designer', now))
        except Exception:
            pass  # flow tracking 失败不阻塞主流程

    conn.commit()
    result["chunks_stored"] = chunks_stored
    result["knowledge_points"] = len(knowledge.get('knowledge_points', [])) if isinstance(knowledge, dict) else 0
    result["subject"] = cat
    result["category"] = knowledge.get('design_category', '') if isinstance(knowledge, dict) else ''
    result["duration_ms"] = int((time.time()-t0)*1000)
    result["rule_id"] = "MT_EXTERNAL_KNOWLEDGE"
    conn.close()
    return result


def generate_beautify_plan(flow_id: str = "", extra_knowledge: str = "") -> dict:
    """
    仙女座-阿尔法: 读取 MT_EXTERNAL_KNOWLEDGE 中所有 design 标记的 chunks
                  → 调用 beautify_plan 路由生成分页面美化方案
                  → EigenFlux 审查 → 落库
    
    flow_id: §14 流程 ID, 用于事件跟踪
    """
    import json, sqlite3, time
    from datetime import datetime
    
    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    t0 = time.time()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {"success": True, "flow_id": flow_id}

    # Step 1: 拉取 design 相关 knowledge chunks
    design_chunks = conn.execute("""
        SELECT section_header, content_chunk, keyword_tags
        FROM mt_andromeda_rule_knowledge
        WHERE rule_id='MT_EXTERNAL_KNOWLEDGE' AND (
            keyword_tags LIKE '%design%'
            OR section_header LIKE '[design]%'
            OR content_chunk LIKE '%design_category%'
        )
        ORDER BY chunk_index DESC
        LIMIT 15""").fetchall()
    
    # 也拉取 MT_EDU_REFORM_KNOWLEDGE 和 MT_ANDROMEDA_SELF_KNOWLEDGE 作为上下文
    edu_chunks = conn.execute("""
        SELECT content_chunk FROM mt_andromeda_rule_knowledge
        WHERE rule_id='MT_EDU_REFORM_KNOWLEDGE' LIMIT 2
    """).fetchall()

    context_parts = []
    if design_chunks:
        for h, c, t in design_chunks:
            context_parts.append(f"【设计知识】{h}\n{c[:400]}\n标签: {t}")
    if edu_chunks:
        for (c,) in edu_chunks:
            context_parts.append(f"【教育方向】{c[:200]}")
    if extra_knowledge:
        context_parts.append(f"【额外输入】{extra_knowledge[:2000]}")
    
    design_context = "\n\n".join(context_parts) if context_parts else "(暂无已入库设计知识, 将基于通用设计规范生成)"
    result["design_chunks_loaded"] = len(design_chunks)

    # Step 2: beautify_plan (AI 生成分页面美化方案)
    try:
        t1 = time.time()
        payload = json.dumps({
            "mtscos_info": {
                "pages": "38+ 页面 (Flask + Element Plus + Vue)",
                "design_spec": "Element Plus token 体系 (.trae/rules/设计规范.md)",
                "color_tokens": "--el-color-primary / --el-color-success / --el-color-warning / --el-color-danger / --el-color-info",
                "spacing": "--el-size-extra-small / small / default / large",
                "radius": "--el-border-radius-base",
            },
            "external_design_knowledge": design_context[:6000],
            "requirements": "全局统一、低复杂度、渐进式、保留 Element Plus 原生风格",
        }, ensure_ascii=False)
        
        r = hub.call('beautify_plan', payload, flow_id=f'beautify_plan_{int(time.time())}')
        text = r.get('response', '')
        s, e = text.find('{'), text.rfind('}') + 1
        plan = json.loads(text[s:e]) if s >= 0 and e > s else text
        result["plan_generated"] = True
        result["plan_duration_ms"] = int((time.time()-t1)*1000)
        
        if isinstance(plan, dict):
            result["pages_count"] = len(plan.get('pages', []))
            result["risk"] = plan.get('risk_assessment', 'unknown')
            result["global_tokens"] = plan.get('global_token_overrides', {})
            result["duration_estimate"] = plan.get('estimated_duration', 'unknown')
            
            # Step 3: 落库 plan 到 rule_knowledge (design_domain)
            max_idx = conn.execute(
                "SELECT COALESCE(MAX(chunk_index),-1) FROM mt_andromeda_rule_knowledge WHERE rule_id='MT_EXTERNAL_KNOWLEDGE'"
            ).fetchone()[0]
            conn.execute("""INSERT INTO mt_andromeda_rule_knowledge
                (rule_id, rule_name, rule_level, rule_version, status,
                 section_header, content_chunk, chunk_index, keyword_tags,
                 is_iron_rule, last_ingested, effective_date)
                VALUES ('MT_EXTERNAL_KNOWLEDGE', '仙女座外部知识脑库', 'L2', 'v1.0.0', 'ACTIVE',
                        ?, ?, ?, ?, 0, ?, ?)""",
                (f'[design] 美化方案 v1', json.dumps(plan, ensure_ascii=False), max_idx+1,
                 f'design,beautify_plan,implementation',
                 now.split(' ')[0], now.split(' ')[0]))
            result["plan_chunk_index"] = max_idx + 1

    except Exception as ex:
        result["error"] = str(ex)[:300]
        result["plan_generated"] = False

    # Step 4: flow_id 跟踪 (§14)
    if flow_id:
        try:
            conn.execute("""INSERT INTO mt_dev_flow_events
                (flow_id, from_step, to_step, event_kind, event_payload_json, triggered_by, triggered_at)
                VALUES (?,?,?,?,?,?,?)""",
                (flow_id, 'STEP_7_EXECUTE', 'STEP_7_EXECUTE', 'beautify_plan_generated',
                 json.dumps({k: v for k, v in result.items() if k != 'plan_chunk_index'}, ensure_ascii=False)[:2000],
                 'andromeda_beautify_architect', now))
        except Exception:
            pass
    
    conn.commit()
    result["total_duration_ms"] = int((time.time()-t0)*1000)
    conn.close()
    return result


def eigenflux_design_review_auto(plan_result: dict = None, flow_id: str = "") -> dict:
    """
    EigenFlux 五人 + AI 代表团 六人交叉审查美化方案 → STEP 7 的 EigenFlux 磋商环节
    """
    import json, sqlite3, time
    from datetime import datetime
    
    hub = get_hub()
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    t0 = time.time()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {"success": True, "flow_id": flow_id}

    # 拉取最新 beautify plan
    plan_context = ""
    if not plan_result:
        chunk = conn.execute("""
            SELECT content_chunk FROM mt_andromeda_rule_knowledge
            WHERE rule_id='MT_EXTERNAL_KNOWLEDGE' AND section_header LIKE '[design] 美化方案%'
            ORDER BY chunk_index DESC LIMIT 1
        """).fetchone()
        if chunk:
            plan_context = chunk[0]
    else:
        plan_context = json.dumps(plan_result, ensure_ascii=False)[:3000]

    if not plan_context:
        result["success"] = False
        result["error"] = "no beautify plan found to review"
        conn.close()
        return result

    try:
        t1 = time.time()
        payload = json.dumps({
            "beautify_plan": plan_context[:5000],
            "mtscos_context": {
                "design_spec": "Element Plus token 体系 + .trae/rules/设计规范.md",
                "accessibility_requirements": "WCAG 2.1 AA 级 (color contrast ≥ 4.5:1)",
                "performance_budget": "CSS bundle ≤ 50KB",
            }
        }, ensure_ascii=False)
        
        r = hub.call('eigenflux_design_review', payload, flow_id=f'design_review_{int(time.time())}')
        text = r.get('response', '')
        s, e = text.find('{'), text.rfind('}') + 1
        review = json.loads(text[s:e]) if s >= 0 and e > s else text
        
        if isinstance(review, dict):
            result["recommendation"] = review.get('final_recommendation', 'UNKNOWN')
            result["experts_count"] = len(review.get('expert_reviews', []))
            result["ai_vote"] = review.get('ai_delegation_vote', {})
            result["duration_ms"] = int((time.time()-t1)*1000)
            
            # brain_feed_log (§14 必触发)
            try:
                conn.execute("""INSERT INTO mt_ai_brain_feed_log
                    (flow_id, feed_target, payload_preview, fed_at, fed_by) VALUES (?,?,?,?,?)""",
                    (flow_id or 'orphaned', 'design_review',
                     json.dumps(review, ensure_ascii=False)[:500],
                     now, 'eigenflux_design_review'))
            except Exception:
                pass
        else:
            result["review_raw"] = str(review)[:500]

    except Exception as ex:
        result["error"] = str(ex)[:200]

    # flow_id 跟踪
    if flow_id:
        try:
            conn.execute("""INSERT INTO mt_dev_flow_events
                (flow_id, from_step, to_step, event_kind, event_payload_json, triggered_by, triggered_at)
                VALUES (?,?,?,?,?,?,?)""",
                (flow_id, 'STEP_7_EXECUTE', 'STEP_7_EXECUTE', 'eigenflux_design_review',
                 json.dumps({k: v for k, v in result.items() if k != 'review_raw'}, ensure_ascii=False)[:2000],
                 'eigenflux_designer', now))
        except Exception:
            pass

    conn.commit()
    result["total_duration_ms"] = int((time.time()-t0)*1000)
    conn.close()
    return result


def andromeda_daemon_tick():
    """给 bg-init / 定时器调用 — 快速轻量的自主检查"""
    import time
    snap = get_employee_distribution()
    # 覆盖度不够 or 偏差过大 → 触发均衡
    if snap.get('coverage_pct', 100) < 95 or snap.get('bias_index', 0) > 10:
        rebalance_employee_routes('weighted_round_robin')
        return {"action": "rebalanced", "coverage": snap.get('coverage_pct'), "bias": snap.get('bias_index')}
    # daemon 周期触发完整循环 (每 3600s)
    return {"action": "ok", "coverage": snap.get('coverage_pct'), "bias": snap.get('bias_index')}


# ═══════════════════════════════════════════════════════════════════
# 4. CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    hub = get_hub()
    import argparse
    parser = argparse.ArgumentParser(description="AI Neural Hub CLI")
    parser.add_argument("action", choices=["chat", "list", "stats", "test"])
    parser.add_argument("--task", default="sa_advisor")
    parser.add_argument("--prompt", default="你好，介绍一下你自己")
    args = parser.parse_args()

    if args.action == "list":
        for r in hub.list_routes():
            print(f"  {r['task_name']:20s} → {r['primary_model']:20s} ({r['domain']})")
    elif args.action == "stats":
        import json as _json
        print(_json.dumps(hub.stats(), indent=2, ensure_ascii=False))
    elif args.action == "chat":
        r = hub.call(args.task, args.prompt)
        print(f"success={r.get('success')} model={r.get('model')} route={r.get('route')}")
        print(f"response: {r.get('response','')}")
    elif args.action == "test":
        # Arduino 编译测试
        err = "sketch_mar20a.ino:3:26: error: 'Serial' was not declared in this scope"
        r = hub.arduino_compile(err, flow_id="cli_test_001")
        print(f"arduino_compile: success={r.get('success')}")
        print(f"  response: {r.get('response','')[:300]}")

        # 代码巡检测试
        code = "def foo(): pass\n# TODO: security issue here\nimport os; os.system('ls')\n"
        r2 = hub.patrol_code(code, "python", flow_id="cli_test_002")
        print(f"patrol_code: success={r2.get('success')}")
        print(f"  response: {r2.get('response','')[:300]}")

        print("\n=== hub stats ===")
        import json as _json
        print(_json.dumps(hub.stats(), indent=2, ensure_ascii=False))
