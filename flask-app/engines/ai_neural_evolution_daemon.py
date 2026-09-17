#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 母体自进化守护进程 — Neural Evolution Daemon
================================================

定时扫描 mt_ai_neural_calls 中的失败/慢响应记录，
调用 qwen2.5-coder:14b 分析根因 → 生成 system_prompt 优化建议。

4 重护栏（防止级联损坏任何 16 个子系统的 prompt）:
  ┌───────────────────────────────────────────────────────────┐
  │ Guardrail #1 VERSIONING — 每次 prompt 变更前写入版本表      │
  │   mt_ai_neural_prompt_versions (old/new/diff/rationale)   │
  │   → 失败可一键 rollback 到上一版本                         │
  ├───────────────────────────────────────────────────────────┤
  │ Guardrail #2 VALIDATION GATE — 候选 prompt 必须通过 3 测试 │
  │   对每个注册的任务，预置 3 条已知 test_input 种子           │
  │   新 prompt → 3 条全跑 → 必须 success=1 且非空响应          │
  │   否则: 拒绝应用，写 mt_ai_self_evolution_log (rejected)   │
  ├───────────────────────────────────────────────────────────┤
  │ Guardrail #3 RATE LIMIT — 单任务每天最多 2 次进化            │
  │   SELECT COUNT(*) FROM mt_ai_self_evolution_log            │
  │     WHERE target_task=? AND DATE(created_at)=CURRENT_DATE  │
  │   → >= 2 则跳过该任务今天的所有候选                         │
  ├───────────────────────────────────────────────────────────┤
  │ Guardrail #4 INPUT SANITIZATION — LLM 输出走严格 JSON schema │
  │   只接受 {"rationale": str, "new_system_prompt": str}       │
  │   拒绝含 system/sql/eval/rm -rf 等危险关键词的输出          │
  └───────────────────────────────────────────────────────────┘

周期: 每 10 分钟扫描一次失败调用，每 6 小时尝试一次 prompt 进化。

调用链路:
  NeuralEvolutionDaemon._run_cycle()
    → scan_failed_calls()  读 mt_ai_neural_calls WHERE success=0
    → analyze_with_llm()   qwen2.5-coder:14b 生成优化 prompt
    → sanitize_and_validate()  #4 + #2
    → rate_limit_check()    #3
    → snapshot_version()    #1
    → apply_prompt()        UPDATE mt_ai_neural_routes
    → log_evolution()       INSERT mt_ai_self_evolution_log
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# ── 路径 ─────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

def _get_app_db() -> str:
    try:
        from core.db_path import get_db_path
        return get_db_path("app.db")
    except Exception:
        return os.path.join(_ROOT, "Database", "app.db")

APP_DB = _get_app_db()

# ── 护栏常量 ─────────────────────────────────────────────────────
MAX_EVOLUTIONS_PER_TASK_PER_DAY = 2       # Guardrail #3
VALIDATION_TEST_COUNT = 3                  # Guardrail #2
VALIDATION_TIMEOUT_MS = 90_000            # 单条验证超时
SANITIZE_MAX_PROMPT_LEN = 4000            # Guardrail #4
DANGEROUS_PATTERNS = [                     # Guardrail #4 — 危险关键词
    re.compile(r'os\.system|subprocess\.call|eval\(|exec\(|__import__', re.I),
    re.compile(r'DROP\s+TABLE|DELETE\s+FROM|TRUNCATE\s+TABLE', re.I),
    re.compile(r'rm\s+-rf|mkfs|format\s+[A-Za-z]:', re.I),
    re.compile(r'<script|javascript:', re.I),
    re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.I),
]


# ═══════════════════════════════════════════════════════════════════
# DB Schema — Prompt 版本化 + 测试种子
# ═══════════════════════════════════════════════════════════════════

def _ensure_evolution_tables(conn: sqlite3.Connection) -> None:
    """Guardrail #1 — prompt 版本表（可回滚）"""
    conn.executescript("""
    -- 4) Prompt 版本历史 — 每次 evolution 写一条, 可 rollback
    CREATE TABLE IF NOT EXISTS mt_ai_neural_prompt_versions (
        version_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name     TEXT NOT NULL,
        version_tag   TEXT NOT NULL,              -- e.g. 'v1_2026-09-10_03-30'
        old_system_prompt  TEXT NOT NULL,
        new_system_prompt  TEXT NOT NULL,
        rationale     TEXT,
        trigger_type  TEXT,                        -- error_spike / slow_response / auto
        validator_ok  INTEGER DEFAULT 0,           -- Guardrail #2 通过=1
        sanitized_ok  INTEGER DEFAULT 0,           -- Guardrail #4 通过=1
        rate_limit_ok INTEGER DEFAULT 0,           -- Guardrail #3 通过=1
        applied       INTEGER DEFAULT 0,
        rollback_of   INTEGER,                     -- 如果是回滚, 指向哪个 version_id
        created_at    TEXT
    );

    -- 5) 验证测试种子 — 每个任务预置 3 条已知 good input
    CREATE TABLE IF NOT EXISTS mt_ai_neural_test_seeds (
        seed_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name     TEXT NOT NULL,
        seed_index    INTEGER NOT NULL,            -- 0,1,2
        test_payload  TEXT NOT NULL,               -- JSON payload 或 str
        expect_nonempty INTEGER DEFAULT 1,
        note          TEXT,
        created_at    TEXT
    );
    """)


def _seed_test_seeds(conn: sqlite3.Connection) -> None:
    """Guardrail #2 — 为每个注册任务预置 3 条验证种子"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SEEDS: List[tuple] = [
        # (task_name, seed_index, test_payload_json, note)
        ("arduino_compile", 0, json.dumps({"error": "'Serial' not declared", "code": "void setup(){}"}),
         "Serial 未声明"),
        ("arduino_compile", 1, json.dumps({"error": "expected ';' before '}' token", "code": "void setup() { Serial.begin(9600)"}),
         "缺分号语法错误"),
        ("arduino_compile", 2, json.dumps({"error": "avrdude: stk500v2_getsync(): not in sync", "code": "void setup(){} void loop(){}"}),
         "AVR 烧录不同步"),

        ("patrol_code", 0, json.dumps({"code": "import os\\nos.system('ls')\\nprint('ok')", "language": "python"}),
         "os.system 安全检查"),
        ("patrol_code", 1, json.dumps({"code": "def f(x,y):\\n    return x+y", "language": "python"}),
         "正常代码应无严重问题"),
        ("patrol_code", 2, json.dumps({"code": "SELECT * FROM users WHERE id='%s' % user_input", "language": "sql"}),
         "SQL 注入检测"),

        ("exam_grade", 0, json.dumps({"question": "1+1=?", "answer": "2"}), "简单数学"),
        ("exam_grade", 1, json.dumps({"question": "请描述光合作用", "answer": "光合作用是植物利用光能将CO2和水转化为葡萄糖和O2的过程..."}),
         "生物简答"),
        ("exam_grade", 2, json.dumps({"question": "写出Python的hello world", "answer": "print('hello world')"}), "编程题"),

        ("security_audit", 0, json.dumps({"code": "eval(user_input)", "api": "/api/eval"}), "eval 注入"),
        ("security_audit", 1, json.dumps({"code": "SELECT * FROM users WHERE name='%s' % input", "api": "/api/search"}),
         "SQL 注入"),
        ("security_audit", 2, json.dumps({"code": "return render_template(user_page)", "api": "/api/page"}),
         "模板注入"),

        ("sa_advisor", 0, json.dumps("什么是 §14 强制开发12步骤?"), "SA 规则问答"),
        ("sa_advisor", 1, json.dumps("VIKEY 铁律是什么?"), "SA 安全问答"),
        ("sa_advisor", 2, json.dumps("系统版本号怎么升级?"), "SA 版本问答"),

        ("auto_repair_code", 0, json.dumps({"error": "IndentationError: unexpected indent", "code": "def f():\\n  x=1\\n    y=2"}),
         "缩进错误"),
        ("auto_repair_code", 1, json.dumps({"error": "NameError: name 'foo' is not defined", "code": "print(foo)"}),
         "未定义变量"),
        ("auto_repair_code", 2, json.dumps({"error": "ModuleNotFoundError: No module named 'xxx'", "code": "import xxx"}),
         "缺失模块"),

        # ── 新增: 10 个路由各补 3 条种子 (共 30 条) ──────────────
        ("copy_write", 0, json.dumps({"content": "我们的产品很棒", "style": "promotional", "audience": "students"}),
         "学生群体宣传文案"),
        ("copy_write", 1, json.dumps({"content": "系统已完成", "style": "technical", "audience": "developers"}),
         "开发者技术文档"),
        ("copy_write", 2, json.dumps({"content": "活动进行中", "style": "urgent", "audience": "all"}),
         "紧急活动通知"),

        ("db_schema_design", 0, json.dumps({"entities": ["User", "Order"], "relations": ["User 1-N Order"]}),
         "用户订单关系设计"),
        ("db_schema_design", 1, json.dumps({"entities": ["Product", "Category", "Tag"], "relations": ["Category N-N Product", "Tag N-N Product"]}),
         "商品多标签设计"),
        ("db_schema_design", 2, json.dumps({"entities": ["Log"], "requirements": "append-only, time-indexed, 10B rows/day"}),
         "日志表高吞吐设计"),

        ("eigenflux_chat", 0, json.dumps({"topic": "怎么提升代码质量", "history": ""}), "代码质量讨论"),
        ("eigenflux_chat", 1, json.dumps({"topic": "新员工入职流程", "history": "员工A: 先办手续吧; 员工B: 还要领设备"}),
         "入职流程多轮"),
        ("eigenflux_chat", 2, json.dumps({"topic": "周五聚餐地点", "history": ""}), "轻松闲聊"),

        ("firewall_rule", 0, json.dumps({"threat": "SQL injection via ' OR 1=1--", "target": "/api/search"}),
         "SQL 注入防火墙规则"),
        ("firewall_rule", 1, json.dumps({"threat": "XSS via <script>alert(1)</script>", "target": "/api/comment"}),
         "XSS 防护规则"),
        ("firewall_rule", 2, json.dumps({"threat": "Port scan from single IP, 1000 ports in 30s", "target": "all"}),
         "端口扫描阻断规则"),

        ("incident_analyze", 0, json.dumps({"symptom": "API 500 率突然飙升 20x", "context": "刚部署新代码"}),
         "发布后故障分析"),
        ("incident_analyze", 1, json.dumps({"symptom": "数据库 CPU 100% 持续 15min", "context": "大促活动中"}),
         "高负载故障分析"),
        ("incident_analyze", 2, json.dumps({"symptom": "大量 403 + referer 异常", "context": "无"}),
         "盗链故障分析"),

        ("knowledge_feed", 0, json.dumps({"source": "python doc", "topic": "GIL", "content": "Python GIL 是什么?"}),
         "Python 知识投喂"),
        ("knowledge_feed", 1, json.dumps({"source": "owasp", "topic": "Top 10 2024", "content": "Broken Access Control"}),
         "安全知识投喂"),
        ("knowledge_feed", 2, json.dumps({"source": "incident", "topic": "API 限流", "content": "上次故障因为没限流"}),
         "故障知识回填"),

        ("perm_check", 0, json.dumps({"user_role": "guest", "action": "read_admin_panel"}), "访客越权检查"),
        ("perm_check", 1, json.dumps({"user_role": "admin", "action": "delete_user", "target_role": "super_admin"}),
         "admin 碰 SA 检查"),
        ("perm_check", 2, json.dumps({"user_role": "student", "action": "submit_exam", "exam_status": "closed"}),
         "考试截止提交检查"),

        ("port_scan_advise", 0, json.dumps({"ports": [22, 80, 443, 3306, 6379], "open": [22, 3306, 6379]}),
         "危险端口开放建议"),
        ("port_scan_advise", 1, json.dumps({"ports": [8080, 8443, 9000], "open": [8080]}),
         "非标准端口建议"),
        ("port_scan_advise", 2, json.dumps({"ports": [11434, 11435], "open": [11435]}),
         "AI 引擎端口建议"),

        ("route_diagnose", 0, json.dumps({"symptom": "POST /api/login 偶发 404", "recent_changes": "新增 /api/login/v2"}),
         "路由冲突诊断"),
        ("route_diagnose", 1, json.dumps({"symptom": "请求耗时 5s+, 中间件多", "middleware_count": 7}),
         "中间件链路诊断"),
        ("route_diagnose", 2, json.dumps({"symptom": "VIKEY 校验通过率 60%", "recent_changes": "vikey_driver 更新"}),
         "VIKEY 路由诊断"),

        ("self_upgrade", 0, json.dumps({"error": "timeout 52s", "task": "security_audit", "current_prompt_len": 800}),
         "进化 daemon 自参考: timeout 优化"),
        ("self_upgrade", 1, json.dumps({"error": "context_length", "task": "patrol_code", "current_prompt_len": 1200}),
         "进化 daemon 自参考: context 裁剪"),
        ("self_upgrade", 2, json.dumps({"error": "success_rate dropped to 70%", "task": "arduino_compile"}),
         "进化 daemon 自参考: 效果回退"),

        # ── 仙女座规则合规路由 (2×3 = 6 条) ──────────────────
        ("rule_compliance_check", 0, json.dumps({
         "code": "import openai\nclient = openai.OpenAI(api_key='sk-xxx', base_url='https://ark.cn-beijing.volces.com')",
         "rule_focus": "MT_RULE_DEV (禁止直接云端 LLM)"
        }), "检测: 直接调云端 API"),
        ("rule_compliance_check", 1, json.dumps({
         "code": "def handler(): @system_container(require_auth='admin') # SA 操作但权限标成 admin",
         "rule_focus": "MT_RULE_PERM (SA 权限级别)"
        }), "检测: 权限级别不符"),
        ("rule_compliance_check", 2, json.dumps({
         "code": "password = 'admin123' # 硬编码",
         "rule_focus": "安全规范 (硬编码 secret)"
        }), "检测: 硬编码密码"),

        ("rule_patrol", 0, json.dumps({
         "scope": "engines/ai_neural_hub.py", "focus": "最近 git diff",
         "rule_ids": ["MT_IRON_RULE_12STEPS", "MT_RULE_DEV", "MT_RULE_PERM"]
        }), "巡逻: hub 引擎"),
        ("rule_patrol", 1, json.dumps({
         "scope": "ai_engines/ai_dual_route_engine.py", "focus": "import + fallback",
         "rule_ids": ["MT_RULE_DEV", "MT_RULE_AI_OPS"]
        }), "巡逻: dual_route 引擎"),
        ("rule_patrol", 2, json.dumps({
         "scope": "server_real_db.py @app.route", "focus": "白名单 + SA 检查",
         "rule_ids": ["MT_RULE_PERM", "MT_RULE_DEV"]
        }), "巡逻: Flask 端点白名单"),

        # ── 教育路由专用 (4×3 = 12 条) ──────────────────────────
        ("question_generate", 0, json.dumps({"subject": "高等数学", "qtype": "single_choice", "chapter": "极限", "knowledge_point": "洛必达法则"}),
         "高数极限选择题"),
        ("question_generate", 1, json.dumps({"subject": "大学英语", "qtype": "fill_blank", "chapter": "时态", "knowledge_point": "现在完成时"}),
         "英语时态填空题"),
        ("question_generate", 2, json.dumps({"subject": "计算机应用基础", "qtype": "multiple_choice", "chapter": "操作系统", "knowledge_point": "进程调度"}),
         "OS 进程调度多选"),

        ("subject_sync", 0, json.dumps({"subject": "成人英语", "content": "应用文写作: 通知格式、邀请函格式、感谢信格式", "source": "考试大纲"}),
         "成人英语同步方案"),
        ("subject_sync", 1, json.dumps({"subject": "高等数学", "content": "微积分: 极限-导数-积分-级数", "source": "教材目录"}),
         "高等数学同步方案"),
        ("subject_sync", 2, json.dumps({"subject": "思想政治", "content": "时事政治 2024 年要点", "source": "考试热点"}),
         "思政同步方案"),

        ("listening_generate", 0, json.dumps({"subject": "大学英语四级", "level": "intermediate", "topic": "dialogue"}),
         "英语四级听力对话"),
        ("listening_generate", 1, json.dumps({"subject": "日语N3", "level": "intermediate", "topic": "news"}),
         "日语 N3 新闻听力"),
        ("listening_generate", 2, json.dumps({"subject": "商务英语", "level": "advanced", "topic": "lecture"}),
         "商务英语讲座听力"),

        ("question_type_expand", 0, json.dumps({"subject": "高等数学", "existing_types": ["single_choice","fill_blank"], "goal": "拓展计算题和证明题"}),
         "高数题型拓展"),
        ("question_type_expand", 1, json.dumps({"subject": "大学语文", "existing_types": ["single_choice","true_false"], "goal": "拓展简答题和论述题"}),
         "语文题型拓展"),
        ("question_type_expand", 2, json.dumps({"subject": "法学概论", "existing_types": ["single_choice","multiple_choice"], "goal": "拓展案例分析题"}),
         "法学案例题拓展"),
    ]
    for row in SEEDS:
        conn.execute("""INSERT OR IGNORE INTO mt_ai_neural_test_seeds
            (task_name, seed_index, test_payload, note, created_at)
            VALUES (?,?,?,?,?)""", row + (now,))
    conn.commit()


# ═══════════════════════════════════════════════════════════════════
# Guardrail #4 — 输入净化
# ═══════════════════════════════════════════════════════════════════

def _sanitize_llm_output(raw: str) -> Optional[Dict[str, Any]]:
    """Guardrail #4 — 严格 JSON schema + 危险关键词过滤 + 长度限制
    返回 {"rationale": str, "new_system_prompt": str} 或 None (拒绝)"""
    if not raw or not isinstance(raw, str):
        return None
    if len(raw) > 20000:  # 整体 LLM 输出限长
        return None

    # 尝试找 JSON block
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        return None

    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError:
        return None

    # 必须有两个字段
    rationale = data.get("rationale") or data.get("reason") or ""
    new_prompt = data.get("new_system_prompt") or data.get("system_prompt") or data.get("prompt") or ""
    if not isinstance(new_prompt, str) or len(new_prompt.strip()) < 10:
        return None
    if len(new_prompt) > SANITIZE_MAX_PROMPT_LEN:
        new_prompt = new_prompt[:SANITIZE_MAX_PROMPT_LEN]

    # 危险关键词扫描
    for pat in DANGEROUS_PATTERNS:
        if pat.search(new_prompt):
            return None
    for pat in DANGEROUS_PATTERNS:
        if pat.search(rationale):
            return None

    return {"rationale": rationale.strip(), "new_system_prompt": new_prompt.strip()}


# ═══════════════════════════════════════════════════════════════════
# 核心守护进程
# ═══════════════════════════════════════════════════════════════════

class NeuralEvolutionDaemon:
    """AI 自进化守护进程 — 4 重护栏保障 prompt 安全迭代"""

    def __init__(self, interval_seconds: int = 3600, db_path: str = None):
        self._interval = interval_seconds          # 默认 1 小时一轮进化尝试
        self._db = db_path or APP_DB
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._cycle_count = 0
        self._last_run_at: Optional[datetime] = None
        self._ensure_tables()

    # ── DB 工具 ──────────────────────────────────────────────
    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self._db, timeout=30)
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _ensure_tables(self) -> None:
        c = self._conn()
        try:
            _ensure_evolution_tables(c)
            _seed_test_seeds(c)
            c.commit()
        finally:
            c.close()

    # ── Guardrail #3: 限流检查 ────────────────────────────────
    def _rate_limit_ok(self, task_name: str) -> bool:
        """单任务每天进化次数 < MAX_EVOLUTIONS_PER_TASK_PER_DAY"""
        c = self._conn()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            row = c.execute("""SELECT COUNT(*) FROM mt_ai_self_evolution_log
                WHERE target_task=? AND DATE(created_at)=DATE(?) AND applied=1""",
                (task_name, today)).fetchone()
            return (row[0] if row else 0) < MAX_EVOLUTIONS_PER_TASK_PER_DAY
        finally:
            c.close()

    # ── 扫描失败调用 ─────────────────────────────────────────
    def scan_failed_calls(self, since_minutes: int = 60) -> List[Dict[str, Any]]:
        """读取最近 N 分钟内失败或超时的调用"""
        c = self._conn()
        c.row_factory = sqlite3.Row
        try:
            since = (datetime.now() - timedelta(minutes=since_minutes)).isoformat()
            rows = c.execute("""SELECT * FROM mt_ai_neural_calls
                WHERE (success=0 OR duration_ms > 30000)
                  AND triggered_at >= ?
                ORDER BY duration_ms DESC
                LIMIT 50""", (since,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            c.close()

    # ── 慢响应检测 (prompt 效率瓶颈) ─────────────────────────
    def scan_slow_tasks(self, avg_ms_threshold: int = 40000) -> List[Dict[str, Any]]:
        """检测平均响应时间 > threshold 的任务"""
        c = self._conn()
        c.row_factory = sqlite3.Row
        try:
            rows = c.execute("""SELECT task_name, avg_duration_ms, call_count, success_rate
                FROM mt_ai_neural_routes
                WHERE enabled=1 AND avg_duration_ms > ? AND call_count >= 5
                ORDER BY avg_duration_ms DESC""", (avg_ms_threshold,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            c.close()

    # ── 根因分析 (调用 LLM) ──────────────────────────────────
    def analyze_failure_with_llm(self, task_name: str,
                                  failures: List[Dict],
                                  current_prompt: str) -> Optional[Dict[str, Any]]:
        """调用 qwen2.5-coder:14b 生成 prompt 优化建议
        返回 Guardrail #4 净化后的 {rationale, new_system_prompt} 或 None"""
        # 构造分析 prompt — 包含 response_preview (如果有的话)
        failure_excerpt = json.dumps([
            {
                "error": f.get("error", "")[:200],
                "duration_ms": f.get("duration_ms"),
                "response_preview": (f.get("response_preview") or "")[:300],
                "success": f.get("success"),
                "model": f.get("model_used", ""),
            }
            for f in failures[:5]   # 最多取 5 条失败/异常摘要
        ], ensure_ascii=False, indent=2)

        system = (
            "你是 AI 系统自升级专家。你看到一个子系统任务的调用失败/超时记录，"
            "需要你给出 system_prompt 优化建议，使后续调用更稳定、响应更快。\n"
            "严格要求：\n"
            "1. 只输出 JSON，不要 markdown\n"
            "2. JSON 格式必须是 {\"rationale\": \"...\", \"new_system_prompt\": \"...\"}\n"
            "3. new_system_prompt 长度 50-4000 字\n"
            "4. 禁止包含危险关键词 (sql/drop/eval/rm -rf)\n"
            "5. 不要引入与原 prompt 矛盾的指令"
        )

        prompt = (
            f"任务名: {task_name}\n"
            f"当前 system_prompt:\n{current_prompt[:3000]}\n\n"
            f"最近失败/慢响应记录:\n{failure_excerpt}\n\n"
            f"请分析根因并生成优化后的 system_prompt。"
        )

        try:
            # 走 dual_route 引擎 — 优先本地 Ollama, 不可用时自动 fallback 云端
            # 不直接走 hub.call('self_upgrade') 以避免自引用循环
            result = None
            try:
                from ai_engines.ai_dual_route_engine import route_and_chat
                result = route_and_chat(prompt, system=system, flow_id=f"evolve_{task_name}_{int(time.time())}")
            except Exception:
                from ai_ollama_engine import chat as ollama_chat
                result = ollama_chat(prompt, system=system, flow_id=f"evolve_{task_name}_{int(time.time())}")
            raw = result.get("response", "")
            ok = result.get("success", False)
            if not ok or not raw:
                print(f"[EvolutionDaemon] LLM failed for {task_name}: {result.get('error','?')[:60]}")
                return None
            return _sanitize_llm_output(raw)  # Guardrail #4
        except Exception as e:
            print(f"[EvolutionDaemon] analyze_failure error for {task_name}: {e}")
            return None

    # ── Guardrail #2: 验证门禁 ────────────────────────────────
    def validate_prompt(self, task_name: str, candidate_prompt: str) -> Dict[str, Any]:
        """用 3 条已知 test_seeds 跑候选 prompt，全通过才允许应用"""
        c = self._conn()
        c.row_factory = sqlite3.Row
        try:
            seeds = c.execute("""SELECT seed_index, test_payload, note
                FROM mt_ai_neural_test_seeds WHERE task_name=?
                ORDER BY seed_index LIMIT ?""",
                (task_name, VALIDATION_TEST_COUNT)).fetchall()
        finally:
            c.close()

        if len(seeds) < VALIDATION_TEST_COUNT:
            return {"ok": False, "reason": f"只找到 {len(seeds)}/{VALIDATION_TEST_COUNT} 条测试种子"}

        try:
            from engines.ai_neural_hub import get_hub
            hub = get_hub()
            # 临时覆盖当前 route 的 system_prompt 做验证
            route = hub.get_route(task_name)
            if not route:
                return {"ok": False, "reason": "route not found"}

            results = []
            all_ok = True
            for seed in seeds:
                try:
                    payload_str = seed["test_payload"]
                    try:
                        payload = json.loads(payload_str)
                    except Exception:
                        payload = payload_str

                    # 走 dual_route (本地优先, 云端 fallback)
                    t0 = time.time()
                    try:
                        from ai_engines.ai_dual_route_engine import route_and_chat
                        r = route_and_chat(
                            hub._build_prompt(route, payload),
                            system=candidate_prompt,
                            flow_id=f"validate_{task_name}_{seed['seed_index']}"
                        )
                    except Exception:
                        from ai_ollama_engine import chat as ollama_chat
                        r = ollama_chat(
                            hub._build_prompt(route, payload),
                            system=candidate_prompt,
                            flow_id=f"validate_{task_name}_{seed['seed_index']}"
                        )
                    dur_ms = int((time.time() - t0) * 1000)
                    ok = (r.get("success") and r.get("response", "").strip()
                          and dur_ms < VALIDATION_TIMEOUT_MS)
                    if not ok:
                        all_ok = False
                    results.append({
                        "seed": seed["seed_index"], "note": seed["note"],
                        "ok": ok, "ms": dur_ms,
                        "response_preview": (r.get("response") or "")[:200],
                    })
                except Exception as e:
                    all_ok = False
                    results.append({"seed": seed["seed_index"], "ok": False, "error": str(e)[:100]})

            return {"ok": all_ok, "results": results,
                    "pass_count": sum(1 for r in results if r["ok"])}
        except Exception as e:
            return {"ok": False, "reason": f"validator error: {e}"}

    # ── Guardrail #1: 版本快照 ────────────────────────────────
    def snapshot_version(self, task_name: str, old_prompt: str,
                          new_prompt: str, rationale: str,
                          trigger_type: str) -> int:
        """Guardrail #1 — 写版本表，返回 version_id"""
        c = self._conn()
        try:
            version_tag = f"v{int(time.time())}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
            cur = c.execute("""INSERT INTO mt_ai_neural_prompt_versions
                (task_name, version_tag, old_system_prompt, new_system_prompt,
                 rationale, trigger_type, validator_ok, sanitized_ok, rate_limit_ok,
                 applied, created_at)
                VALUES (?,?,?,?,?,?,1,1,1,0,?)""",
                (task_name, version_tag, old_prompt, new_prompt, rationale,
                 trigger_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            c.commit()
            return cur.lastrowid
        finally:
            c.close()

    # ── 回滚接口（SA 手动触发） ───────────────────────────────
    def rollback_to_version(self, version_id: int) -> Dict[str, Any]:
        """SA 一键回滚某个 prompt 到历史版本"""
        c = self._conn()
        c.row_factory = sqlite3.Row
        try:
            v = c.execute("SELECT * FROM mt_ai_neural_prompt_versions WHERE version_id=?",
                         (version_id,)).fetchone()
            if not v:
                return {"success": False, "error": "version not found"}
            # 找该任务当前的 prompt，作为 rollback 的 old
            cur_row = c.execute("SELECT system_prompt FROM mt_ai_neural_routes WHERE task_name=?",
                                (v["task_name"],)).fetchone()
            cur_prompt = cur_row["system_prompt"] if cur_row else ""
            # 应用 old_system_prompt （= 回滚前的 new_system_prompt）
            c.execute("UPDATE mt_ai_neural_routes SET system_prompt=?, evolved_at=? WHERE task_name=?",
                     (v["old_system_prompt"], datetime.now().isoformat(), v["task_name"]))
            # 写一条 rollback version
            rollback_tag = f"rollback_{v['version_tag']}"
            c.execute("""INSERT INTO mt_ai_neural_prompt_versions
                (task_name, version_tag, old_system_prompt, new_system_prompt,
                 rationale, trigger_type, validator_ok, sanitized_ok, rate_limit_ok,
                 applied, rollback_of, created_at)
                VALUES (?,?,?,?,?,?,1,1,1,1,?,?)""",
                (v["task_name"], rollback_tag, cur_prompt, v["old_system_prompt"],
                 f"rollback to {v['version_tag']}", "manual_rollback",
                 version_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            c.commit()
            return {"success": True, "task": v["task_name"], "rollback_to": v["version_tag"]}
        finally:
            c.close()

    # ── 主循环 ────────────────────────────────────────────────
    def _run_one_task(self, task_name: str) -> Dict[str, Any]:
        """对单个任务跑一轮 evolution 尝试"""
        # 0) Guardrail #3 限流
        if not self._rate_limit_ok(task_name):
            return {"task": task_name, "status": "skipped", "reason": "rate_limit_exceeded"}

        # 1) 获取当前 route
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        route = hub.get_route(task_name)
        if not route:
            return {"task": task_name, "status": "skipped", "reason": "route_not_found"}

        # 2) 收集失败/慢响应信号
        failures = self.scan_failed_calls(since_minutes=120)
        task_failures = [f for f in failures if f.get("task_name") == task_name]
        slow_tasks = self.scan_slow_tasks(avg_ms_threshold=40000)
        is_slow = any(s["task_name"] == task_name for s in slow_tasks)

        if not task_failures and not is_slow:
            return {"task": task_name, "status": "skipped", "reason": "no_signal"}

        trigger_type = "error_spike" if task_failures else "slow_response"
        signal_text = f"{len(task_failures)} failures" if task_failures else f"slow avg={next(s['avg_duration_ms'] for s in slow_tasks if s['task_name']==task_name)}ms"

        # 3) LLM 分析 → 生成候选 prompt
        candidate = self.analyze_failure_with_llm(task_name, task_failures, route["system_prompt"])
        if not candidate:
            return {"task": task_name, "status": "skipped", "reason": "llm_rejected (sanitize failed)"}

        # 4) Guardrail #2 验证门禁
        val = self.validate_prompt(task_name, candidate["new_system_prompt"])
        if not val["ok"]:
            # 记录 rejected
            c = self._conn()
            try:
                c.execute("""INSERT INTO mt_ai_self_evolution_log
                    (trigger_type, target_task, old_prompt, new_prompt, rationale,
                     approved_by, applied, created_at)
                    VALUES (?,?,?,?,?,?,0,?)""",
                    (trigger_type, task_name, route["system_prompt"][:2000],
                     candidate["new_system_prompt"][:2000],
                     f"[REJECTED] validator failed: {val.get('pass_count',0)}/{VALIDATION_TEST_COUNT} | {val.get('reason','')}",
                     "validator_reject", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                c.commit()
            finally:
                c.close()
            return {"task": task_name, "status": "rejected",
                    "reason": f"validator {val.get('pass_count',0)}/{VALIDATION_TEST_COUNT} passed"}

        # 5) Guardrail #1 版本快照
        version_id = self.snapshot_version(
            task_name, route["system_prompt"],
            candidate["new_system_prompt"], candidate["rationale"], trigger_type
        )

        # 6) 应用新 prompt
        c = self._conn()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""UPDATE mt_ai_neural_routes
                SET system_prompt=?, evolved_at=?, updated_at=?
                WHERE task_name=?""",
                (candidate["new_system_prompt"], now, now, task_name))
            # 标记 version applied + 写 evolution_log
            c.execute("UPDATE mt_ai_neural_prompt_versions SET applied=1 WHERE version_id=?",
                     (version_id,))
            c.execute("""INSERT INTO mt_ai_self_evolution_log
                (trigger_type, target_task, old_prompt, new_prompt, rationale,
                 approved_by, applied, created_at)
                VALUES (?,?,?,?,?,?,1,?)""",
                (trigger_type, task_name, route["system_prompt"][:2000],
                 candidate["new_system_prompt"][:2000],
                 candidate["rationale"], "auto_with_3guardrails",
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            c.commit()
        finally:
            c.close()

        return {"task": task_name, "status": "evolved",
                "version_id": version_id,
                "trigger": trigger_type, "signal": signal_text,
                "validator_passed": f"{val.get('pass_count',0)}/{VALIDATION_TEST_COUNT}"}

    def _run_cycle(self) -> None:
        """一轮完整的自进化扫描"""
        self._cycle_count += 1
        self._last_run_at = datetime.now()
        ts = self._last_run_at.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[EvolutionDaemon] cycle #{self._cycle_count} @ {ts}")

        # 只对有 signal 的任务尝试进化（避免无意义的全量）
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        routes = hub.list_routes()

        results = []
        for route in routes:
            r = self._run_one_task(route["task_name"])
            results.append(r)
            status = r["status"]
            if status == "evolved":
                print(f"  ✅ {route['task_name']}: EVOLVED v{r.get('version_id')} ({r.get('validator_passed')} passed)")
            elif status == "rejected":
                print(f"  ❌ {route['task_name']}: REJECTED ({r.get('reason','')})")
        evolved = sum(1 for r in results if r["status"] == "evolved")
        rejected = sum(1 for r in results if r["status"] == "rejected")
        print(f"[EvolutionDaemon] done — evolved={evolved} rejected={rejected} skipped={len(results)-evolved-rejected}")

    # ── 守护线程 ──────────────────────────────────────────────
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop():
            # 首次启动延迟 2 分钟（让 Flask + Ollama 先就绪）
            if not self._stop_event.wait(120):
                return
            while not self._stop_event.is_set():
                try:
                    self._run_cycle()
                except Exception as e:
                    print(f"[EvolutionDaemon] cycle error: {e}")
                # 等待 interval 或 stop
                self._stop_event.wait(self._interval)

        self._thread = threading.Thread(target=_loop, name="neural-evolution", daemon=True)
        self._thread.start()
        print(f"[EvolutionDaemon] 自进化守护线程已启动 (interval={self._interval}s, 4 guardrails ON)")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "interval_seconds": self._interval,
            "cycle_count": self._cycle_count,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            "guardrails": {
                "versioning": True,
                "validation_gate": f"{VALIDATION_TEST_COUNT} test seeds",
                "rate_limit_per_day": MAX_EVOLUTIONS_PER_TASK_PER_DAY,
                "input_sanitization": "json_schema + dangerous_patterns",
            },
        }


# ═══════════════════════════════════════════════════════════════════
# 单例
# ═══════════════════════════════════════════════════════════════════

_daemon_instance: Optional[NeuralEvolutionDaemon] = None
_daemon_lock = threading.Lock()

def get_evolution_daemon(interval_seconds: int = 3600) -> NeuralEvolutionDaemon:
    global _daemon_instance
    if _daemon_instance is None:
        with _daemon_lock:
            if _daemon_instance is None:
                _daemon_instance = NeuralEvolutionDaemon(interval_seconds=interval_seconds)
    return _daemon_instance


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Neural Evolution Daemon CLI")
    parser.add_argument("action", choices=["run_once", "start", "status", "rollback"])
    parser.add_argument("--interval", type=int, default=3600, help="扫描间隔秒数")
    parser.add_argument("--version-id", type=int, default=0, help="rollback 用 version_id")
    args = parser.parse_args()

    d = get_evolution_daemon(interval_seconds=args.interval)
    if args.action == "run_once":
        d._run_cycle()
    elif args.action == "start":
        d.start()
        try:
            while True:
                time.sleep(30)
        except KeyboardInterrupt:
            d.stop()
    elif args.action == "status":
        print(json.dumps(d.get_status(), indent=2, ensure_ascii=False))
    elif args.action == "rollback":
        import json
        print(json.dumps(d.rollback_to_version(args.version_id), indent=2, ensure_ascii=False))
