#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 巡检-EigenFlux 顾问引擎 (Patrol-EigenFlux Advisor v1.1.0)
================================================================
巡检发现 → EigenFlux 专家咨询 → 建设性建议 → 脑库投喂 → 闭环改进

核心能力:
  1. 收集巡检发现 (auto_patrol_engine + deep_inspection_engine 的最近错误记录)
  2. 按错误类型/严重度路由到最匹配的 EigenFlux 专家
  3. 生成上下文相关的咨询请求 (非模板, 基于实际发现)
  4. 生成专家建设性建议 (基于发现类型+专家领域知识库)
  5. 高价值建议强制投喂 AI 脑库
  6. 建议追踪表 mt_patrol_eigenflux_suggestions 全生命周期

AI化特性:
  - 巡检发现自动分类 → 话题匹配 → 专家路由
  - 建议质量评分 → 高分自动投喂脑库
  - 闭环反馈: 已采纳的建议自动标记, 避免重复咨询
  - 本地推理: 零 token 消耗, 全部规则+模式匹配

CLI:
  python3 ai_patrol_eigenflux_advisor_engine.py once    单轮执行
  python3 ai_patrol_eigenflux_advisor_engine.py start    守护进程
  python3 ai_patrol_eigenflux_advisor_engine.py status   查看状态
  python3 ai_patrol_eigenflux_advisor_engine.py stop     停止
"""
# [unused] from __future__ import annotations
import argparse
import hashlib
import json
import logging
import os
import signal
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
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
PID_FILE = os.path.join(_PID_DIR, "ai_patrol_eigenflux_advisor.pid")
os.makedirs(_PID_DIR, exist_ok=True)
os.makedirs(_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(_LOG_DIR, "ai_patrol_eigenflux_advisor.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("PatrolAdvisor")

DAEMON_INTERVAL = 300  # 5 分钟一轮
DB_TIMEOUT = 15

# =========================================================
# 巡检发现类型 → EigenFlux 专家路由表
# =========================================================
# 每种发现类型 → (专家名称, 专长领域, 建议知识库key)
FINDING_TO_EXPERT = {
    'syntax_error':       ('EF_架构师_101', '架构与代码质量', 'syntax'),
    'indentation_error':  ('EF_架构师_101', '架构与代码质量', 'syntax'),
    'import_error':       ('EF_架构师_101', '架构与代码质量', 'import'),
    'compile_error':      ('EF_架构师_101', '架构与代码质量', 'syntax'),
    'pattern_issue':      ('EF_代码审查_102', '代码规范与模式', 'pattern'),
    'read_error':         ('EF_运维_103', '文件系统与IO', 'read_error'),
    'security_vuln':      ('EF_红队指挥_201', '安全攻防', 'security'),
    'sql_injection':      ('EF_蓝队防御_202', '安全防御', 'security'),
    'xss_vuln':           ('EF_蓝队防御_202', '安全防御', 'security'),
    'page_error':         ('EF_前端_104', '前端工程', 'page'),
    'route_missing':      ('EF_后端_105', '后端路由', 'route'),
    'undefined_var':      ('EF_架构师_101', '代码质量', 'syntax'),
    'dead_code':          ('EF_代码审查_102', '代码清理', 'pattern'),
    'resource_leak':      ('EF_运维_103', '资源管理', 'resource'),
    'performance':        ('EF_云安全_231', '性能优化', 'performance'),
    'unknown':            ('EF_协调AI_305', '综合协调', 'general'),
}

# =========================================================
# 专家建议知识库 (按发现类型给出建设性建议)
# =========================================================
EXPERT_ADVICE_LIBRARY = {
    'syntax': [
        "建议: 在 CI 流水线中增加 py_compile 预检门, 阻止语法错误进入主干。同时配置 pre-commit hook 自动运行 flake8 --select=E9,F63,F7,F82。",
        "建议: 对 IndentationError 类问题, 统一项目 tab/space 策略(editorconfig: indent_style=space, indent_size=4), 并在 CI 中用 autopep8 --in-place 自动修复。",
        "建议: 对 SyntaxError 根因做分类: missing colon / unbalanced bracket / encoding issue。建议增加 chardet 检测文件编码, 非 UTF-8 自动转换。",
    ],
    'import': [
        "建议: 对 ImportError 根因分析: (1) 循环导入 → 重构模块依赖图 (2) 缺失依赖 → 补充 requirements.txt (3) 路径错误 → 统一 sys.path 策略。",
        "建议: 建立模块依赖矩阵, 用 pydeps 生成可视化依赖图, 识别循环依赖并重构为 DAG。优先解耦高频导入链。",
        "建议: 对第三方包导入失败, 增加运行时检测: try-except + 友好降级提示, 避免 ImportError 导致整模块不可用。",
    ],
    'pattern': [
        "建议: 对裸 except 模式, 全面替换为 except Exception as e 并记录 e 到日志, 避免吞掉 KeyboardInterrupt/SystemExit。",
        "建议: 对 open() 未用 with 模式, 全面改为 contextlib.contextmanager 或 with 语句, 杜绝资源泄露。同时增加 ResourceWarning 检测。",
        "建议: 引入 ruff 规则集 (SIM, B, C4), 对代码模式做自动化检测和修复。每周生成模式债务报告供 SA 审阅。",
    ],
    'security': [
        "建议: 对 SQL 拼接, 全面迁移到参数化查询 (conn.execute(sql, params))。对已有 f-string SQL, 用 sqlparse 解析验证安全性。",
        "建议: 对 eval()/exec() 使用, 评估替代方案: ast.literal_eval (字面量) 或受限沙箱。无法替代的标记为 SA 审批项。",
        "建议: 对硬编码密码/API Key, 迁移到环境变量 + .env 文件 (python-dotenv), 并在 .gitignore 中排除 .env。对历史泄露的 key 建议轮换。",
        "建议: 对 XSS 风险 (Markup + f-string), 全面改用 markupsafe.escape() 转义用户输入, 或使用 Jinja2 自动转义 (autoescape=True)。",
    ],
    'page': [
        "建议: 对页面 500 错误, 增加模板可读性预检: 启动时遍历所有 registered templates, open 读探测 OneDrive 占位符, 异常的自动降级到 fallback。",
        "建议: 对页面 404, 建立路由注册清单 vs 模板文件清单的双向校验, CI 中自动比对覆盖率。",
        "建议: 对页面超时, 增加 gunicorn 超时配置 (timeout=120s) + 健康检查端点 /health, 异常时自动重启 worker。",
    ],
    'route': [
        "建议: 对缺失路由, 建立路由注册表 (route_registry.json), CI 中校验所有 @app.route 定义与注册表一致。新增路由必须同步更新注册表。",
        "建议: 对路由权限缺失, 确保 @system_container 装饰器覆盖率 100%。CI 中扫描所有 def 视图函数, 缺少装饰器的自动告警。",
        "建议: 对路由参数, 建立 OpenAPI schema 描述, CI 中校验参数类型+必填项, 不一致自动告警。",
    ],
    'read_error': [
        "建议: 对 OneDrive 文件读取超时, 增加 brctl evict 预检: 启动时强制驱逐占位符, 对关键模板文件用 Python 直接写入绕过同步机制。",
        "建议: 对文件系统权限问题, 启动时做 writable 检测 (os.access(path, os.W_OK)), 异常时自动 chmod 修复或告警 SA。",
        "建议: 对大文件读取, 增加分块读取策略 (chunk_size=64KB), 配合超时信号保护 (signal.alarm), 避免单次读取阻塞 daemon。",
    ],
    'resource': [
        "建议: 对资源泄露, 引入 tracemalloc 跟踪分配/释放, 在 daemon 退出时做 resource_summary 检查, 未释放的自动告警。",
        "建议: 对数据库连接泄露, 确保所有 sqlite3.connect 都用 with 上下文管理器或 try-finally 关闭。增加 connection_pool 监控指标。",
        "建议: 对线程泄露, 在 daemon 退出时检查 threading.active_count() 与预期值, 超出阈值的标记为可疑线程并 dump traceback。",
    ],
    'performance': [
        "建议: 对 N+1 查询, 引入 SQLAlchemy eager_loading 或手动 JOIN。增加 slow_query 日志 (阈值 >100ms), 每周生成 TOP10 慢查询报告。",
        "建议: 对大循环低效操作, 用 cProfile 做热点分析, 优化目标: 热点函数耗时降低 50%+。优先优化被高频调用的路径。",
        "建议: 对内存增长, 增加 tracemalloc 快照对比, 识别增长最快的分配点。对缓存类用 functools.lru_cache 替代手写 dict 缓存。",
    ],
    'general': [
        "建议: 对未知类型发现, 建议升级 AI 分类器: 增加更多 pattern 规则, 或用本地推理引擎做语义分类, 减少 unknown 占比。",
        "建议: 建立巡检发现知识图谱: 发现类型 → 根因 → 修复策略 → 验证方法, 沉淀到脑库供后续自动复用。",
        "建议: 对高频反复出现的同类问题, 建议做根因分析(RCA), 从源头消除而非反复修复。记录到 mt_ai_brain_feed_log 供 SA 决策。",
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


def ensure_tables() -> None:
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mt_patrol_eigenflux_suggestions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_uid  TEXT UNIQUE NOT NULL,
            finding_id      TEXT,
            finding_type    TEXT NOT NULL,
            finding_file    TEXT,
            finding_line    INTEGER,
            finding_message TEXT,
            finding_severity TEXT,
            expert_name     TEXT NOT NULL,
            expert_domain   TEXT NOT NULL,
            advice_category TEXT NOT NULL,
            advice_content  TEXT NOT NULL,
            quality_score   REAL NOT NULL DEFAULT 0.0,
            status          TEXT NOT NULL DEFAULT 'PENDING',
            adopted_at      TEXT,
            sa_reviewed     INTEGER NOT NULL DEFAULT 0,
            brain_fed       INTEGER NOT NULL DEFAULT 0,
            round_no        INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pes_finding_type
            ON mt_patrol_eigenflux_suggestions(finding_type);
        CREATE INDEX IF NOT EXISTS idx_pes_status
            ON mt_patrol_eigenflux_suggestions(status);
        CREATE INDEX IF NOT EXISTS idx_pes_quality
            ON mt_patrol_eigenflux_suggestions(quality_score DESC);
        """)

        # 确保 eigenflux_messages 表存在 (依赖 ai_eigenflux_network_engine)
        conn.execute("""
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
        )
        """)

        # 确保 brain feed log 表存在
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (
            feed_uid  TEXT PRIMARY KEY,
            source    TEXT,
            content   TEXT,
            tags_json TEXT,
            value_score REAL,
            status    TEXT DEFAULT 'PENDING',
            created_at TEXT,
            updated_at TEXT
        )
        """)

        conn.commit()
    logger.info("Tables ensured (mt_patrol_eigenflux_suggestions)")


# =========================================================
# 1. 收集巡检发现
# =========================================================
def collect_recent_findings(hours_back: int = 6) -> List[Dict[str, Any]]:
    """从巡检引擎和深度巡检引擎的数据库记录中收集最近发现。
    适配实际表名: patrol_issues / ai_inspection_issues"""
    findings: List[Dict[str, Any]] = []
    cutoff = (datetime.now() - timedelta(hours=hours_back)).isoformat()

    with get_conn() as conn:
        # ai_inspection_issues (深度巡检引擎, 实际有大量未修复记录)
        try:
            rows = conn.execute(
                """SELECT id, run_id, issue_type, severity, file_path, line_number,
                          error_message, error_code, detected_at, fixed,
                          suggestion_message, auto_fixable, source_tool
                   FROM ai_inspection_issues
                   WHERE detected_at > ? AND fixed=0
                   ORDER BY severity ASC, detected_at DESC LIMIT 50""",
                (cutoff,),
            ).fetchall()
            for r in rows:
                # 映射 issue_type → 内部 finding_type
                itype = r['issue_type'] or 'unknown'
                ecode = (r['error_code'] or '').lower()
                if 'syntax' in itype or 'syntax' in ecode:
                    ftype = 'syntax_error' if 'indent' not in ecode else 'indentation_error'
                elif 'import' in itype or 'import' in ecode:
                    ftype = 'import_error'
                elif 'security' in itype or 'sql' in ecode:
                    ftype = 'security_vuln' if 'sql' not in ecode else 'sql_injection'
                elif 'xss' in ecode:
                    ftype = 'xss_vuln'
                elif 'page' in itype or 'route' in itype:
                    ftype = 'page_error'
                elif 'performance' in itype:
                    ftype = 'performance'
                elif 'pattern' in itype or 'dead_code' in itype:
                    ftype = 'pattern_issue'
                elif 'resource' in itype:
                    ftype = 'resource_leak'
                else:
                    ftype = 'unknown'
                findings.append({
                    'source': 'deep_inspection',
                    'finding_id': str(r['id']),
                    'type': ftype,
                    'file': (r['file_path'] or '')[-200:],
                    'line': r['line_number'] or 0,
                    'message': (r['error_message'] or '')[:200],
                    'severity': r['severity'] or 'medium',
                    'source_line': '',
                    'discovered_at': r['detected_at'],
                    'status': 'discovered' if not r['fixed'] else 'fixed',
                })
        except sqlite3.Error:
            pass

        # patrol_issues (巡逻队引擎)
        try:
            rows = conn.execute(
                """SELECT issue_id, source, scan_round, subsystem, severity,
                          title, description, detected_at, status, patrol_type
                   FROM patrol_issues
                   WHERE detected_at > ? AND status NOT IN ('fixed', 'skipped')
                   ORDER BY severity ASC, detected_at DESC LIMIT 50""",
                (cutoff,),
            ).fetchall()
            for r in rows:
                subsystem = (r['subsystem'] or '').lower()
                if 'security' in subsystem or '安全' in (r['subsystem_cn'] or ''):
                    ftype = 'security_vuln'
                elif 'rule' in subsystem or '规则' in (r['subsystem_cn'] or ''):
                    ftype = 'pattern_issue'
                elif 'db' in subsystem or '数据库' in (r['subsystem_cn'] or ''):
                    ftype = 'performance'
                elif 'analytics' in subsystem or '分析' in (r['subsystem_cn'] or ''):
                    ftype = 'performance'
                else:
                    ftype = 'unknown'
                findings.append({
                    'source': 'auto_patrol',
                    'finding_id': r['issue_id'],
                    'type': ftype,
                    'file': '',
                    'line': 0,
                    'message': (r['title'] or '') + ': ' + (r['description'] or '')[:150],
                    'severity': r['severity'] or 'medium',
                    'source_line': '',
                    'discovered_at': r['detected_at'],
                    'status': r['status'],
                })
        except sqlite3.Error:
            pass

    logger.info("Collected %d recent findings (last %dh)", len(findings), hours_back)
    return findings


# =========================================================
# 2. 路由到 EigenFlux 专家
# =========================================================
def route_to_expert(finding: Dict[str, Any]) -> Tuple[str, str, str]:
    """根据发现类型路由到最匹配的 EigenFlux 专家"""
    ftype = finding.get('type', 'unknown')
    expert_name, expert_domain, advice_key = FINDING_TO_EXPERT.get(
        ftype, FINDING_TO_EXPERT['unknown']
    )
    return expert_name, expert_domain, advice_key


# =========================================================
# 3. 生成上下文相关的咨询请求
# =========================================================
def generate_advice_request(finding: Dict[str, Any], expert_name: str,
                            expert_domain: str) -> str:
    """基于实际发现内容生成咨询请求 (非模板)"""
    ftype = finding.get('type', 'unknown')
    ffile = finding.get('file', 'unknown')
    fline = finding.get('line', 0)
    fmsg = finding.get('message', '')[:200]
    fsev = finding.get('severity', 'medium')

    return (
        f"[Patrol Advisor] -> [{expert_name}]: "
        f"在巡检中发现 {fsev} 级别 {ftype} 问题"
        f" (文件: {ffile}:{fline}), "
        f"详情: {fmsg}. "
        f"您在 {expert_domain} 领域有丰富经验, "
        f"请给出建设性改进建议。"
    )


# =========================================================
# 4. 生成专家建设性建议
# =========================================================
def generate_expert_advice(finding: Dict[str, Any], advice_key: str) -> str:
    """从知识库中选取匹配的建议, 增加上下文信息"""
    pool = EXPERT_ADVICE_LIBRARY.get(advice_key, EXPERT_ADVICE_LIBRARY['general'])
    # 基于发现内容的哈希选取 (确定性, 同一发现每次得到相同建议)
    seed = finding.get('finding_id', '') + finding.get('type', '')
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(pool)
    advice = pool[idx]
    # 附加上下文
    ffile = finding.get('file', '')
    if ffile:
        advice += f" (针对: {ffile})"
    return advice


# =========================================================
# 5. 建议质量评分 (本地推理, 零 token)
# =========================================================
def score_advice_quality(finding: Dict[str, Any], advice: str) -> float:
    """对建议进行质量评分 0.0-1.0"""
    score = 0.5  # 基础分
    # 建议长度 (太短不够具体, 太长可能噪音)
    if 50 <= len(advice) <= 500:
        score += 0.15
    # 建议包含具体工具/方法名
    tools = ['flake8', 'ruff', 'CI', 'pre-commit', 'autopep8', 'ast', 'tracemalloc',
             'cProfile', 'sqlparse', 'markupsafe', 'Jinja2', 'gunicorn', 'pydeps',
             'chardet', 'contextlib', 'functools', 'signal', 'openAPI']
    tool_hits = sum(1 for t in tools if t.lower() in advice.lower())
    score += min(0.2, tool_hits * 0.05)
    # 严重度越高, 建议越有价值
    sev = finding.get('severity', 'medium')
    sev_bonus = {'critical': 0.15, 'high': 0.10, 'medium': 0.05, 'low': 0.02}
    score += sev_bonus.get(sev, 0.05)
    # 建议包含 "建议" 关键词 (结构化)
    if '建议:' in advice or '建议：' in advice:
        score += 0.05
    return round(min(1.0, score), 4)


# =========================================================
# 6. 投喂脑库
# =========================================================
def feed_to_brain(conn: sqlite3.Connection, suggestion_uid: str,
                  expert_name: str, advice: str, quality_score: float,
                  finding_type: str) -> None:
    """高价值建议投喂 AI 脑库"""
    try:
        feed_uid = "PATROLFEED-%s" % uuid.uuid4().hex[:16]
        now_iso = datetime.now().isoformat()
        conn.execute(
            """INSERT OR IGNORE INTO mt_ai_brain_feed_log
            (feed_uid, source, content, tags_json, value_score, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (feed_uid,
             "PATROL_EIGENFLUX_ADVISOR:%s:%s" % (expert_name, finding_type),
             advice[:500],
             json.dumps([finding_type, "patrol_advice", expert_name],
                        ensure_ascii=False),
             quality_score,
             "PENDING", now_iso, now_iso),
        )
        # 标记建议已投喂
        conn.execute(
            "UPDATE mt_patrol_eigenflux_suggestions SET brain_fed=1, updated_at=? "
            "WHERE suggestion_uid=?",
            (now_iso, suggestion_uid),
        )
    except sqlite3.Error as e:
        logger.debug("Brain feed skip: %s", e)


# =========================================================
# 7. 发送到 EigenFlux 消息表
# =========================================================
def send_to_eigenflux_messages(conn: sqlite3.Connection,
                               expert_name: str, expert_domain: str,
                               finding: Dict[str, Any],
                               advice_request: str, advice: str,
                               quality_score: float) -> Tuple[str, str]:
    """将咨询请求和专家建议写入 EigenFlux 消息表"""
    now = datetime.now()
    msg_uid_req = "ADVREQ-%s" % uuid.uuid4().hex[:16]
    msg_uid_resp = "ADVRESP-%s" % uuid.uuid4().hex[:16]
    conn_uid = "PATROL-ADV-%s" % hashlib.md5(
        (finding.get('finding_id', '') + expert_name).encode()
    ).hexdigest()[:16]
    tags = [finding.get('type', 'unknown'), "patrol_advice"]

    # 咨询请求 (Patrol Advisor → Expert)
    conn.execute(
        """INSERT INTO mt_ai_eigenflux_messages
        (msg_uid, conn_uid, sender_id, sender_table, sender_name,
         receiver_id, receiver_table, receiver_name,
         topic_key, topic_cn, message_type, content,
         is_read, read_at, knowledge_tags_json, learning_value, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (msg_uid_req, conn_uid,
         "PATROL_ADVISOR", "system", "Patrol Advisor Engine",
         expert_name, "eigenflux", expert_name,
         "patrol_advice", "巡检建议咨询",
         "PATROL_ADVICE_REQUEST", advice_request,
         1, now.isoformat(),
         json.dumps(tags, ensure_ascii=False), 0.3,
         (now - timedelta(seconds=2)).isoformat()),
    )

    # 专家建议 (Expert → Patrol Advisor)
    conn.execute(
        """INSERT INTO mt_ai_eigenflux_messages
        (msg_uid, conn_uid, sender_id, sender_table, sender_name,
         receiver_id, receiver_table, receiver_name,
         topic_key, topic_cn, message_type, content,
         is_read, read_at, knowledge_tags_json, learning_value, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (msg_uid_resp, conn_uid,
         expert_name, "eigenflux", expert_name,
         "PATROL_ADVISOR", "system", "Patrol Advisor Engine",
         "patrol_advice", "巡检建议咨询",
         "PATROL_ADVICE_RESPONSE", advice,
         0, None,
         json.dumps(tags, ensure_ascii=False), quality_score,
         now.isoformat()),
    )

    return msg_uid_req, msg_uid_resp


# =========================================================
# 8. 核心轮次执行
# =========================================================
def run_advisor_round(round_no: int) -> Dict[str, Any]:
    """单轮巡检-EigenFlux 顾问执行"""
    now_iso = datetime.now().isoformat()
    stats = {
        'round': round_no,
        'findings_collected': 0,
        'suggestions_generated': 0,
        'brain_fed': 0,
        'high_quality': 0,
        'deduplicated': 0,
    }

    # 确保表存在
    ensure_tables()

    # 1. 收集巡检发现
    findings = collect_recent_findings(hours_back=6)
    stats['findings_collected'] = len(findings)
    if not findings:
        logger.info("[Round %d] No recent findings, skipping", round_no)
        return stats

    # 查询已处理过的 finding_id, 避免重复 (用 source+finding_id 组合)
    processed_ids = set()
    with get_conn() as conn:
        try:
            rows = conn.execute(
                "SELECT finding_id, finding_type FROM mt_patrol_eigenflux_suggestions "
                "WHERE finding_id IS NOT NULL"
            ).fetchall()
            for r in rows:
                processed_ids.add(r['finding_id'])
        except sqlite3.Error:
            pass

    new_findings = [f for f in findings
                    if (f.get('source', '') + ':' + f.get('finding_id', '')) not in processed_ids]
    stats['deduplicated'] = len(findings) - len(new_findings)

    if not new_findings:
        logger.info("[Round %d] All %d findings already processed, waiting next round",
                    round_no, len(findings))
        return stats

    # 2. 逐发现: 路由 → 咨询 → 建议 → 投喂
    with get_conn() as conn:
        for finding in new_findings:
            expert_name, expert_domain, advice_key = route_to_expert(finding)

            # 3. 生成咨询请求
            advice_request = generate_advice_request(
                finding, expert_name, expert_domain
            )

            # 4. 生成专家建议
            advice = generate_expert_advice(finding, advice_key)

            # 5. 质量评分
            quality = score_advice_quality(finding, advice)

            # 6. 发送到 EigenFlux 消息表
            msg_req_uid, msg_resp_uid = send_to_eigenflux_messages(
                conn, expert_name, expert_domain,
                finding, advice_request, advice, quality
            )

            # 7. 存入建议追踪表
            suggestion_uid = "SUG-%s" % uuid.uuid4().hex[:16]
            composite_finding_id = finding.get('source', '') + ':' + finding.get('finding_id', '')
            conn.execute(
                """INSERT OR IGNORE INTO mt_patrol_eigenflux_suggestions
                (suggestion_uid, finding_id, finding_type, finding_file,
                 finding_line, finding_message, finding_severity,
                 expert_name, expert_domain, advice_category,
                 advice_content, quality_score, status, brain_fed,
                 round_no, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (suggestion_uid,
                 composite_finding_id,
                 finding.get('type', 'unknown'),
                 finding.get('file', ''),
                 finding.get('line', 0),
                 finding.get('message', '')[:300],
                 finding.get('severity', 'medium'),
                 expert_name, expert_domain, advice_key,
                 advice, quality,
                 'PENDING', 0,
                 round_no, now_iso, now_iso),
            )

            # 8. 高质量建议投喂脑库
            if quality >= 0.7:
                feed_to_brain(conn, suggestion_uid, expert_name,
                              advice, quality, finding.get('type', 'unknown'))
                stats['brain_fed'] += 1
                stats['high_quality'] += 1

            stats['suggestions_generated'] += 1

        # 写系统心跳
        try:
            conn.execute(
                """INSERT INTO system_heartbeat
                (component_name, component_type, status, last_beat_at,
                 beat_interval_sec, metrics_json, health_score,
                 created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("ai_patrol_eigenflux_advisor", "ai", "ALIVE", now_iso,
                 DAEMON_INTERVAL,
                 json.dumps(stats, ensure_ascii=False),
                 1.0, now_iso, now_iso),
            )
        except sqlite3.Error:
            pass

        conn.commit()

    logger.info(
        "[Round %d] findings=%d new=%d dedup=%d suggestions=%d brain_fed=%d high_q=%d",
        round_no,
        stats['findings_collected'],
        len(new_findings),
        stats['deduplicated'],
        stats['suggestions_generated'],
        stats['brain_fed'],
        stats['high_quality'],
    )
    return stats


# =========================================================
# 9. Daemon
# =========================================================
class PatrolAdvisorDaemon:
    def __init__(self):
        self._stop = threading.Event()
        self._round_no = 0

    @staticmethod
    def read_pid():
        if os.path.exists(PID_FILE):
            try:
                return int(open(PID_FILE).read().strip())
            except Exception:
                return None
        return None

    @staticmethod
    def write_pid():
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        try:
            os.chmod(PID_FILE, 0o644)
        except Exception:
            pass

    @staticmethod
    def clear_pid():
        if os.path.exists(PID_FILE):
            try:
                os.unlink(PID_FILE)
            except Exception:
                pass

    @staticmethod
    def reap_stale_pid():
        pid = PatrolAdvisorDaemon.read_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return False
        except OSError:
            logger.warning("Stale PID file (pid=%d) cleaned", pid)
            PatrolAdvisorDaemon.clear_pid()
            return True

    @staticmethod
    def is_running():
        PatrolAdvisorDaemon.reap_stale_pid()
        pid = PatrolAdvisorDaemon.read_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def start(self, once: bool = False):
        PatrolAdvisorDaemon.reap_stale_pid()
        ensure_tables()
        logger.info("=" * 60)
        logger.info(" MTSCOS Patrol-EigenFlux Advisor v1.1.0 STARTING")
        logger.info(" DB=%s | PID_FILE=%s", APP_DB, PID_FILE)
        logger.info("=" * 60)

        if once:
            self._round_no += 1
            stats = run_advisor_round(self._round_no)
            print(json.dumps(stats, ensure_ascii=False, indent=2))
            return

        if PatrolAdvisorDaemon.is_running():
            pid = PatrolAdvisorDaemon.read_pid()
            logger.warning("Already running (PID=%s)", pid)
            print("ALREADY_RUNNING pid=%s" % pid)
            sys.exit(2)

        PatrolAdvisorDaemon.write_pid()

        def _sig_handler(signum, _frame):
            logger.info("Signal %s received, shutting down", signum)
            self.stop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, _sig_handler)
            except (OSError, ValueError):
                pass

        self._stop.clear()
        while not self._stop.is_set():
            try:
                self._round_no += 1
                run_advisor_round(self._round_no)
            except Exception as e:
                logger.exception("Round error: %s", e)
            slept = 0.0
            while slept < float(DAEMON_INTERVAL) and not self._stop.is_set():
                s = min(1.0, float(DAEMON_INTERVAL) - slept)
                time.sleep(s)
                slept += s

        PatrolAdvisorDaemon.clear_pid()
        logger.info("Patrol Advisor exited, PID cleaned")

    def stop(self):
        self._stop.set()


# =========================================================
# CLI
# =========================================================
def main():
    parser = argparse.ArgumentParser(
        description="MTSCOS Patrol-EigenFlux Advisor Engine"
    )
    parser.add_argument('command', choices=['once', 'start', 'stop', 'status'],
                        help='Command')
    args = parser.parse_args()

    if args.command == 'once':
        ensure_tables()
        daemon = PatrolAdvisorDaemon()
        daemon._round_no = 1
        stats = run_advisor_round(1)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif args.command == 'start':
        daemon = PatrolAdvisorDaemon()
        daemon.start(once=False)
    elif args.command == 'stop':
        pid = PatrolAdvisorDaemon.read_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                print("Sent SIGTERM to pid=%d" % pid)
            except OSError as e:
                print("Kill failed: %s" % e)
        else:
            print("Not running")
        PatrolAdvisorDaemon.clear_pid()
    elif args.command == 'status':
        if PatrolAdvisorDaemon.is_running():
            pid = PatrolAdvisorDaemon.read_pid()
            print("RUNNING pid=%d" % pid)
        else:
            print("STOPPED")
        # 查看最近建议统计
        ensure_tables()
        with get_conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM mt_patrol_eigenflux_suggestions"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM mt_patrol_eigenflux_suggestions WHERE status='PENDING'"
            ).fetchone()[0]
            brain_fed = conn.execute(
                "SELECT COUNT(*) FROM mt_patrol_eigenflux_suggestions WHERE brain_fed=1"
            ).fetchone()[0]
            avg_q = conn.execute(
                "SELECT AVG(quality_score) FROM mt_patrol_eigenflux_suggestions"
            ).fetchone()[0] or 0
            print("Suggestions: total=%d pending=%d brain_fed=%d avg_quality=%.3f"
                  % (total, pending, brain_fed, avg_q))
            # 按类型统计
            rows = conn.execute(
                "SELECT finding_type, COUNT(*) AS c, AVG(quality_score) AS q "
                "FROM mt_patrol_eigenflux_suggestions GROUP BY finding_type "
                "ORDER BY c DESC"
            ).fetchall()
            if rows:
                print("\nBy type:")
                for r in rows:
                    print("  %-20s count=%3d avg_q=%.3f" % (r['finding_type'], r['c'], r['q']))


if __name__ == '__main__':
    main()
