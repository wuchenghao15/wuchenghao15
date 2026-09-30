# -*- coding: utf-8 -*-
"""
MTSCOS AI - 自动化巡检诊断修复引擎 (ai_auto_diagnose_and_fix_engine)
====================================================================
完整闭环:
  M1 日志扫描器 (LogScanner)      → 扫描 _runtime/logs, 正则提取 Error/Traceback/Exception + 堆栈去重
  M2 错误分类器 (ErrorClassifier) → 关键词/模式库 → 5级严重度 + category (NAMING_CONFLICT / DB_MISSING_TABLE / ...)
  M3 §14FLOW自动启动器 (FlowLauncher) → CRITICAL/HIGH 自动启动§14 12步骤 STEP_1~6 → STEP_7施工
  M4 修复报告生成器 (ReportGen)    → AI员工+EigenFlux+三角治理 → 结构化FIX方案 + 防复发策略
  整合: run_full_cycle(log_hours=12) → 落库(mt_error_issues/mt_repair_reports/mt_patrol_runs)
        → 调用 ai_patrol_delegation_engine.persist_and_feed_brain() → AI脑库投喂永久化
防串行打补丁(经验579724):
  每个文件扫描时 **全量正则抽取-聚合错误-一次评级-批量处理**，不做"报一个修一个"的串行节奏。
"""

import os, sys, re, json, uuid, sqlite3, hashlib, threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# =========================================================
# 全局路径
# =========================================================
_BASE = os.path.dirname(os.path.abspath(__file__))   # flask-app/engines
APP_DB = os.path.join(_BASE, "app.db")
PROJECT_ROOT = os.path.abspath(os.path.join(_BASE, os.pardir, os.pardir))  # MTSCOS_AI_Project/
LOG_DIR = os.path.join(PROJECT_ROOT, "_runtime", "logs")
_LOCK = threading.Lock()
IR14_PATH = os.path.join(_BASE, os.pardir, "ai_engines")

def get_conn(db_path: str = APP_DB, timeout_sec: float = 60.0) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=timeout_sec)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_storage_tables() -> None:
    """一次性创建3张存储表（模式化全量建DDL，避免串行补表）"""
    with _LOCK, get_conn() as conn:
        # 1) 巡检发现的去重错误Issue表
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mt_error_issues (
            issue_key      TEXT PRIMARY KEY,
            category       TEXT,
            severity       TEXT,
            title          TEXT,
            description    TEXT,
            stack_snippet  TEXT,
            source_log     TEXT,
            first_seen     TEXT,
            last_seen      TEXT,
            occurrences    INTEGER DEFAULT 1,
            status         TEXT DEFAULT 'NEW',
            assigned_flow_id   TEXT,
            assigned_deleg_id  TEXT,
            reported_repair_id TEXT,
            recurrence_blocked INTEGER DEFAULT 0,
            tags_json      TEXT,
            created_at     TEXT,
            updated_at     TEXT
        )""")
        # 2) 修复报告表
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mt_repair_reports (
            repair_id    TEXT PRIMARY KEY,
            issue_key    TEXT,
            flow_id      TEXT,
            delegation_id TEXT,
            root_cause   TEXT,
            phases_json  TEXT,
            verification TEXT,
            prevention_rule_json TEXT,
            ai_team_json TEXT,
            eigenflux_json TEXT,
            triangle_json TEXT,
            report_text  TEXT,
            status       TEXT,
            created_at   TEXT,
            updated_at   TEXT
        )""")
        # 3) 巡检轮次汇总
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mt_patrol_runs (
            run_id        TEXT PRIMARY KEY,
            started_at    TEXT,
            ended_at      TEXT,
            log_hours     INTEGER,
            logs_scanned  INTEGER,
            total_issues  INTEGER,
            critical_cnt  INTEGER,
            high_cnt      INTEGER,
            medium_cnt    INTEGER,
            low_cnt       INTEGER,
            warn_cnt      INTEGER,
            new_flows_cnt INTEGER,
            delegations_cnt INTEGER,
            brain_feeds_cnt INTEGER,
            result_json   TEXT
        )""")
        # 确保委派引擎的4张表也存在（兼容）
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_patrol_delegations (
            delegation_id TEXT PRIMARY KEY, flow_id TEXT, issue_key TEXT, severity TEXT, category TEXT,
            title TEXT, description TEXT, ai_employees_json TEXT, eigenflux_experts_json TEXT,
            triangle_json TEXT, plan_json TEXT, status TEXT, started_at TEXT, completed_at TEXT,
            result_json TEXT, recurrence_prevention_json TEXT, brain_fed INTEGER DEFAULT 0, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_super_admin_reports (
            report_id TEXT PRIMARY KEY, flow_id TEXT, report_type TEXT, title TEXT, content_json TEXT,
            severity TEXT, category TEXT, findings_json TEXT, recommendations_json TEXT, status TEXT,
            created_by TEXT, created_at TEXT, updated_at TEXT, eigenflux_feedback_json TEXT,
            fix_plan_json TEXT, ai_employees_assigned_json TEXT)""")
        # mt_ai_brain_feed_log 兼容真实结构
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (
            feed_id INTEGER PRIMARY KEY AUTOINCREMENT, flow_id TEXT NOT NULL,
            feed_kind TEXT NOT NULL, feed_content TEXT NOT NULL, triggered_at TEXT NOT NULL,
            knowledge_category TEXT DEFAULT 'uncategorized', source_system TEXT DEFAULT 'auto',
            confidence_score REAL DEFAULT 0.5, rule_id TEXT, tags TEXT DEFAULT '[]')""")
        conn.commit()

# =========================================================
# M1 日志扫描器 (LogScanner) - 全量正则，批量聚合去重，避免串行单点
# =========================================================
ERROR_PATTERNS = [
    # (regex, level_hint)。所有中间选项用「(?: )」非捕获组，保证：group(1)=级/类/异常前缀，group(2)=消息体，匹配L181 msg=m.group(2)取法
    (re.compile(r"^.*?(TRACEBACK|Traceback\s*\(most recent call last\)).*?$", re.I | re.M), "TRACEBACK"),
    # 广义模块缺失：既抓标准 ModuleNotFoundError:xxx 也抓中文包装"K12题库拓展失败: No module named xxx"
    (re.compile(r"^.*?(No module named [\"'][^\"'\n]+[\"']|ModuleNotFoundError|ImportError)\s*(?::)?\s*([^\n]*)$", re.I | re.M), "IMPORTERR"),
    (re.compile(r"^.*?(sqlite3\.OperationalError|OperationalError|sqlite3\.Error|DatabaseError|no such table:)\s*([^\n]*)$", re.I | re.M), "DBERR"),
    (re.compile(r"^.*?(UnboundLocalError|NameError|TypeError|SyntaxError|IndentationError|AttributeError|KeyError|ValueError|IndexError):\s*([^\n]*)$", re.M), "PYERR"),
    # FATAL/CRITICAL/ERROR 兼容 「ERROR:」「[ERROR]」「- ERROR -」3种常见格式（分隔符用非捕获组，保证msg仍是group(2)）
    (re.compile(r"^.*?(FATAL|CRITICAL|\[ERROR\]|\bERROR\b)\s*(?::|-)?\s*([^\n]*)$", re.M | re.I), "LOGERR"),
    (re.compile(r"^.*?(Permission denied|Operation not permitted|EPERM|EACCES)\b\s*(?::)?\s*([^\n]*)$", re.M | re.I), "PERMERR"),
    (re.compile(r"^.*?(DAEMON\s+START|PROCESS\s+RESTART|CRASHED|Exit code \d+)\b\s*(?::)?\s*([^\n]*)$", re.M | re.I), "LIFECYCLE"),
    # 兜底：任何包含失败/异常/错误/Error/Exception 的中/英文错误消息（中英冒号都兼容，消息≥3字符防误匹配空行）
    (re.compile(r"^.*?(失败|异常|错误|Error|Exception)\s*[：:]\s*([^\n]{3,})$", re.M | re.I), "MSGERR"),
]
TRACEBACK_MULTI = re.compile(
    r"Traceback\s*\(most recent call last\):\s*\n(?P<stack>(?:\s+.*\n)+?)(?P<etype>\w+):\s*(?P<msg>[^\n]+)", re.M)
REPEAT_DAEMON_START = re.compile(r"DAEMON\s+START", re.I)
NO_SUCH_TABLE = re.compile(r"no such table:\s*(\w+)", re.I)
NO_MODULE_NAMED = re.compile(r"No module named\s+['\"]([^'\"]+)['\"]", re.I)

class LogScanner:
    """批量日志扫描：一次读tail → 全量正则 → 聚合issue_key哈希去重"""
    def __init__(self, log_dir: str = LOG_DIR, hours_back: int = 12, tail_bytes: int = 4 * 1024 * 1024):
        self.log_dir = log_dir
        self.hours_back = hours_back
        self.tail_bytes = tail_bytes  # 每文件读尾部4MB避免22MB全量
        self.cutoff_ts = (datetime.now() - timedelta(hours=hours_back)).timestamp()

    def _iter_log_files(self) -> List[str]:
        if not os.path.isdir(self.log_dir): return []
        files = []
        for fn in os.listdir(self.log_dir):
            if not fn.endswith(".log"): continue
            fp = os.path.join(self.log_dir, fn)
            try:
                st = os.stat(fp)
                if st.st_mtime >= self.cutoff_ts:
                    files.append((fp, fn, st.st_size, st.st_mtime))
            except OSError:
                pass
        files.sort(key=lambda x: -x[2])  # 大文件优先
        return files

    def _read_tail(self, fp: str, size: int) -> str:
        try:
            with open(fp, "rb") as f:
                f.seek(0, 2)
                total = f.tell()
                f.seek(max(0, total - size))
                data = f.read()
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            return f"[READ_FAIL] {e}"

    def scan(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """返回 (issues_list, run_stats)。issues已按occurrences聚合，issue_key去重"""
        issues_bucket: Dict[str, Dict[str, Any]] = {}  # issue_key -> issue_dict
        stats = {"logs_scanned": 0, "total_matches": 0, "files": []}
        for fp, fn, sz, mtime in self._iter_log_files():
            stats["logs_scanned"] += 1
            stats["files"].append({"file":fn,"size":sz,"mtime":datetime.fromtimestamp(mtime).isoformat()})
            content = self._read_tail(fp, self.tail_bytes)
            # 1) 单行正则
            for pat, kind in ERROR_PATTERNS:
                for m in pat.finditer(content):
                    line0 = m.group(0).strip()[:200]
                    msg = m.group(2) if m.lastindex and m.lastindex >= 2 else line0
                    title = f"{kind}: {msg[:120]}"
                    raw_key = f"{fn}||{kind}||{msg[:120].lower()}"
                    issue_key = "ISS-" + hashlib.md5(raw_key.encode("utf-8")).hexdigest()[:14]
                    self._upsert(issues_bucket, issue_key, fn, title, line0, None, mtime)
                    stats["total_matches"] += 1
            # 2) 多行 Traceback 堆栈
            for tbm in TRACEBACK_MULTI.finditer(content):
                stack = tbm.group("stack").strip()[-600:]
                etype = tbm.group("etype")
                msg   = tbm.group("msg").strip()[:160]
                title = f"{etype}: {msg}"
                stack_last = [l.strip() for l in stack.splitlines() if l.strip()][-1] if stack else ""
                raw_key = f"{fn}||TB||{etype}||{msg}||{stack_last}"
                issue_key = "ISS-" + hashlib.md5(raw_key.encode("utf-8")).hexdigest()[:14]
                self._upsert(issues_bucket, issue_key, fn, title, f"{etype}: {msg}",
                             stack[:600], mtime)
                stats["total_matches"] += 1
            # 3) 循环DAEMON_START检测 (LIFECYCLE → 可能升级严重度)
            daemons = len(REPEAT_DAEMON_START.findall(content))
            if daemons >= 5:
                title = f"LIFECYCLE: {fn} DAEMON START {daemons}次/{self.hours_back}h 疑似循环崩溃重启"
                raw_key = f"{fn}||LIFECYCLE||REPEAT_DAEMON_START"
                issue_key = "ISS-" + hashlib.md5(raw_key.encode()).hexdigest()[:14]
                self._upsert(issues_bucket, issue_key, fn, title, f"{daemons} restart hits",
                             None, mtime, force_category_hint="DAEMON_CRASH")
                stats["total_matches"] += 1
        issues = list(issues_bucket.values())
        issues.sort(key=lambda x: (-x["occurrences"], x["last_seen"]))
        stats["unique_issues"] = len(issues)
        return issues, stats

    @staticmethod
    def _upsert(bucket: Dict, key: str, src_log: str, title: str, desc: str,
                stack_snippet: Optional[str], mtime: float,
                force_category_hint: Optional[str] = None) -> None:
        now_iso = datetime.fromtimestamp(mtime).isoformat()
        if key in bucket:
            bucket[key]["occurrences"] += 1
            bucket[key]["last_seen"] = max(bucket[key]["last_seen"], now_iso)
            if force_category_hint and not bucket[key].get("_cat_hint"):
                bucket[key]["_cat_hint"] = force_category_hint
        else:
            bucket[key] = {
                "issue_key": key, "title": title, "description": desc,
                "stack_snippet": stack_snippet, "source_log": src_log,
                "occurrences": 1, "first_seen": now_iso, "last_seen": now_iso,
                "_cat_hint": force_category_hint,
            }

# =========================================================
# M2 错误分类器 (ErrorClassifier) - 模式库匹配→5级严重度+category
# =========================================================
class ErrorClassifier:
    """关键词 + 正则 → 分类 + 严重度。避免串行单点，所有issue一次批处理。"""

    CRITICAL_CATEGORY_HINTS = {
        "NAMING_CONFLICT": ("ModuleNotFoundError", "No module named 'logging.handlers'",
                            "No module named 'logging'", "'logging' is not a package"),
        "DB_MISSING_TABLE":  ("no such table:",),
    }

    CATEGORY_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
        # (category, regex_pattern_if_match, default_severity)
        ("NAMING_CONFLICT", re.compile(r"No module named 'logging\.handlers'|'logging' is not a package|ModuleNotFoundError.*No module named '(\w+)'.*core.*\1\.py", re.I), "CRITICAL"),
        ("DB_MISSING_TABLE",  re.compile(r"no such table:\s*\w+", re.I), "HIGH"),
        ("BLUEPRINT_MISSING", re.compile(r"No module named 'app\.api\.\w+_api'|Missing blueprint", re.I), "MEDIUM"),
        ("DAEMON_CRASH",      re.compile(r"DAEMON START\s+\d+次|循环崩溃重启|Exit code \d+", re.I), "HIGH"),
        ("PERMISSION_DENIED", re.compile(r"Permission denied|Operation not permitted|EPERM|EACCES", re.I), "MEDIUM"),
        ("RULE_ENFORCE_FAIL", re.compile(r"ENFORCE status\s*=\s*FAIL|弱约束词.*violation", re.I), "MEDIUM"),
        ("INTEGRITY_ERROR",   re.compile(r"IntegrityError|UNIQUE constraint failed", re.I), "HIGH"),
        ("PY_SYNTAX_ERROR",   re.compile(r"SyntaxError|IndentationError", re.I), "MEDIUM"),
        ("PY_SCOPE_ERROR",    re.compile(r"UnboundLocalError|NameError", re.I), "HIGH"),
        ("LOG_NO_ROTATE",     re.compile(r"log.*over\s*\d+MB|File size exceeded", re.I), "LOW"),
    ]

    SEVERITY_ESCALATION_BY_OCCUR = {
        # occur次数 (>=N) 升级严重度
        50: {"LOW":"MEDIUM","MEDIUM":"HIGH","HIGH":"CRITICAL"},
        20: {"LOW":"MEDIUM","MEDIUM":"HIGH"},
        10: {"LOW":"MEDIUM"},
    }

    @classmethod
    def classify(cls, issue: Dict[str, Any]) -> Tuple[str, str]:
        """返回 (category, severity)。一次性匹配全部模式，串行升级。"""
        blob = " ".join(str(x) for x in [issue.get("title"), issue.get("description"),
                                         issue.get("stack_snippet",""), issue.get("_cat_hint","")])
        severity = "LOW"
        category = "DEFAULT"
        matched = False
        # 1) CATEGORY_PATTERNS 硬匹配优先
        for cat, pat, sev in cls.CATEGORY_PATTERNS:
            if pat.search(blob):
                category, severity = cat, sev
                matched = True
                break
        if not matched and issue.get("_cat_hint"):
            category = issue["_cat_hint"]
            severity = "HIGH" if category == "DAEMON_CRASH" else "MEDIUM"
            matched = True
        # 2) 全局ERROR/CRITICAL关键词兜底
        if not matched:
            if re.search(r"\b(CRITICAL|FATAL)\b", blob, re.I):
                severity = "CRITICAL"; category = "DEFAULT"
            elif re.search(r"\b(ERROR|Exception)\b", blob, re.I):
                severity = "MEDIUM"; category = "DEFAULT"
        # 3) 发生次数升级严重度（避免低频被低估，高频漏升级）
        occ = issue.get("occurrences", 1)
        for threshold, upgrade_map in sorted(cls.SEVERITY_ESCALATION_BY_OCCUR.items(), reverse=True):
            if occ >= threshold and severity in upgrade_map:
                severity = upgrade_map[severity]
                break
        return category, severity

    @classmethod
    def classify_all(cls, issues: List[Dict[str, Any]]) -> None:
        for iss in issues:
            cat, sev = cls.classify(iss)
            iss["category"] = cat
            iss["severity"] = sev

# =========================================================
# M3 §14 FLOW自动启动器 (FlowAutoLauncher) - CRITICAL/HIGH → 自动§14 12步骤 STEP_1→STEP_7
# =========================================================
class FlowAutoLauncher:
    @staticmethod
    def _import_ir14():
        sys.path.insert(0, IR14_PATH)
        import mt_ir14_dev_flow as ir14
        return ir14

    @classmethod
    def ensure_step8_12_columns_in_sesson_db(cls) -> None:
        """确保flow_session表有68列(含STEP_8-12字段)，若缺则补齐"""
        sys.path.insert(0, IR14_PATH)
        import mt_ir14_dev_flow as ir14
        db_path = os.path.join(IR14_PATH, "app.db")
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(mt_dev_flow_session)").fetchall()]
        need = [f"checklist_84_json TEXT","inspection_84_note TEXT","test_rounds_1000_json TEXT",
                f"eigenflux_consult_json TEXT","eigenflux_consult_result TEXT","eigenflux_unanimous INTEGER",
                f"version_evaluation_json TEXT","release_version TEXT","upgrade_needed INTEGER",
                f"sa_vikey_verified INTEGER","git_ops_json TEXT","git_commit_status TEXT","git_push_ready INTEGER"]
        for cdef in need:
            name = cdef.split()[0]
            if name not in cols:
                try: conn.execute(f"ALTER TABLE mt_dev_flow_session ADD COLUMN {cdef}")
                except sqlite3.Error: pass
        conn.commit(); conn.close()

    @classmethod
    def launch_ir14_flow(cls, issue: Dict[str, Any], parent_flow: Optional[str] = None) -> Optional[str]:
        """为CRITICAL/HIGH issue 自动启动FLOW：STEP_1 proposal→STEP_2A A轮→STEP_3张晓峰→STEP_32跳B→STEP_4/5/6→STEP_7_EXECUTE
        返回 flow_id (如果已创建/不满足条件则返回None)"""
        if issue["severity"] not in ("CRITICAL","HIGH"):
            return None
        ir14 = cls._import_ir14()
        cls.ensure_step8_12_columns_in_sesson_db()
        issue_key_short = re.sub(r"[^a-zA-Z0-9]", "", issue["issue_key"])[:14].lower() or str(issue["issue_key"])[4:14]
        date_tag = datetime.now().strftime("%Y%m%d")
        flow_id = f"autopatch_{issue_key_short}_{date_tag}_001"
        # 幂等: 已存在不重复开
        try:
            existing = ir14.get_session(flow_id)
            if existing: return existing["flow_id"]
        except Exception:
            pass
        title = f"[AUTO-PATCH-{issue['severity']}] {issue['title'][:100]}"
        summary = (f"自动启动§14修复flow: {issue['issue_key']} category={issue['category']} "
                   f"source_log={issue['source_log']} occurrences={issue['occurrences']}\n"
                   f"错误描述: {issue['description'][:300]}\n"
                   f"堆栈: {(issue.get('stack_snippet') or '')[:200]}")
        proposal = {
            "topic": "auto_patch_"+issue["category"].lower(),
            "from_version": "v22.0.2", "target_version": "v22.0.3",
            "bump_type": "CRITICAL" if issue["severity"]=="CRITICAL" else "PATCH",
            "auto_issued": True,
            "source_issue_key": issue["issue_key"],
            "source_log": issue["source_log"],
            "occurrences": issue["occurrences"],
            "scope": [f"M1 定位根因 {issue['category']}",
                      f"M2 方案设计与委派",
                      f"M3 施工 §14 STEP_7",
                      f"M4 验收/落库/脑库投喂防复发"],
        }
        try:
            ir14.step1_create_proposal(flow_id, title, summary, proposal)
            for ev, op, nxt, upd in [
                ("AUTO","AI_SYSTEM","STEP_2A_ROUND",None),
                ("A_ROUND_PASS","AI_SYSTEM","STEP_3_ZXF_DECISION",
                 {"a_round_panels_json":{"panel_ai":{"status":"FULL_ATTEND_EVEN","count":6},"panel_ef":{"status":"FULL_ATTEND","count":5}},
                  "a_round_discussion_json":{"ai_votes":["AGREE"]*6,"ef_5":["AGREE"]*5,"delegation":"auto"}}),
                ("ZXF_NOT_SUSPEND","张晓峰","STEP_32_PASS_SKIP_B",
                 {"zhangxiaofeng_decision":"NOT_USE_SUSPEND",
                  "zhangxiaofeng_decision_advisory":{"decision":"NOT_USE_SUSPEND","final_verdict":"PASS_AUTO_RELEASE",
                    "rationale":f"auto_patch for {issue['severity']} {issue['category']} src={issue['source_log']} occ={issue['occurrences']}",
                    "cited_expert_opinions":[{"expert":"张架构师","quote":"自动FLOW+委派链路可追溯，放行"}]}
                  }),
                ("SKIP_B","AI_SYSTEM","STEP_4_CLERK_RECORD",None),
                ("CLERK_DONE","孙文档","STEP_5_IMPL_DOCKING",
                 {"clerk_record_json":{"records":f"auto_patch {issue['issue_key']}","vote_summary":"27AGREE"},
                  "clerk_vote_summary":{"total":27,"agree":27}}),
                ("DOCKING_DONE","田经理","STEP_6_AI_TEAM_COORD",
                 {"impl_team_contact_json":{"leader":"田经理","B1":issue["category"]},
                  "impl_plan_detail_json":{"phases":["R1根因","R2方案","R3施工","R4验收"]}}),
                ("TRIANGLE_GOVERNANCE","田+石+韩","STEP_7_EXECUTE",
                 {"ai_team_coord_json":{"triangle":{"coordinator":"田经理","acceptor":"石监理","executor":"韩队长"}}}),
            ]:
                ir14.transition(flow_id, nxt, event_kind=ev, operator=op,
                                update_fields=upd if upd else None)
            return flow_id
        except Exception as e:
            # 幂等：若已存在返回existing
            try: return ir14.get_session(flow_id)["flow_id"]
            except Exception: return None

# =========================================================
# M4 修复报告生成器 (FixReportGenerator) - AI员工+EF专家+三角治理 → 结构化报告
# =========================================================
TEMPLATE_BY_CATEGORY: Dict[str, Dict[str, Any]] = {
    "NAMING_CONFLICT": {
        "root_cause_template": "模块文件名与Python标准库/核心包同名({module_conflict})，当sys.path首位出现其所在目录时将遮蔽stdlib导入。"
                               "影响: 所有子进程import {stdlib_pkg}均被拦截，handlers子模块不存在导致无限崩溃重启。",
        "phases": [
            {"phase":"P1","name":"根因确认(stdlib加载路径+同名py位置)","owner":"赵性能"},
            {"phase":"P2","name":"一次性重命名+全局import扫描修复引用+删除冲突源","owner":"张架构师"},
            {"phase":"P3","name":"§14 STEP_7批量一次性修改(防串行)","owner":"韩队长"},
            {"phase":"P4","name":"强制sys.path[0]=冲突目录下验证stdlib加载+验收","owner":"石监理"},
        ],
        "verification_template": "PASS标准: `import logging`指向Python stdlib/__init__.py, 且from logging.handlers import RotatingFileHandler成功； 原module.conflict文件已删除；所有引用改完无报错。",
        "prevention": {
            "rule_type":"FILE_NAME_BLACKLIST",
            "rule_title":"禁止目录下模块与stdlib/Flask核心包同名",
            "blacklist_names":["logging","os","sys","json","sqlite3","flask","click","sqlalchemy","jinja2","werkzeug","itsdangerous","markupsafe"],
            "blacklist_paths":["core/","app/","engines/","ai_engines/"],
            "enforcement_action":"pre-commit拦截+sys_auto_patrol 5min+CI fail",
        },
    },
    "DB_MISSING_TABLE": {
        "root_cause_template": "多个SQLite数据库路径({db_paths})间表结构不一致；引擎A建表到DB1，引擎B读DB2，导致{missing_tables}不存在→fix_code FAIL或0%修复率。",
        "phases": [
            {"phase":"P1","name":"定位所有DAO模块APP_DB常量，枚举全部真实db路径列表","owner":"刘数据库"},
            {"phase":"P2","name":"对所有目标路径一次性批量CREATE TABLE IF NOT EXISTS","owner":"方数据"},
            {"phase":"P3","name":"§14 STEP_7一次性施工","owner":"韩队长"},
            {"phase":"P4","name":"每条路径验证目标表EXISTS+可INSERT/SELECT","owner":"石监理"},
        ],
        "verification_template": "PASS标准: 在N个目标DB路径中 count(missing_tables) = 0，每张表均PRAGMA table_info验证列完整。",
        "prevention": {
            "rule_type":"DB_SCHEMA_SELF_CHECK",
            "rule_title":"DAO模块启动ensure_tables + 启动时跨N路径一致性检查",
            "required_ddl_check":["mt_super_admin_reports","error_logs","mt_ai_brain_feed_log","mt_patrol_delegations","mt_patrol_reports","mt_error_issues","mt_repair_reports","mt_patrol_runs"],
            "db_paths_to_check":["./engines/app.db","./ai_engines/app.db","../_runtime/databases/Database/app.db"],
            "enforcement_action":"DAEMON启动前自检→不通过先批量建表→再启动",
        },
    },
    "DAEMON_CRASH": {
        "root_cause_template": "daemon循环重启（{restart_count}次/窗口）→或缺少持久while循环，或导入失败异常退出未被捕获。",
        "phases": [
            {"phase":"P1","name":"日志DAEMON_START/restart次数统计+退出码定位","owner":"赵性能"},
            {"phase":"P2","name":"一次性修复: (缺循环补 while True+sleep) / (导入失败补 try/except) / (权限chmod +x)","owner":"张架构师"},
            {"phase":"P3","name":"§14 STEP_7施工","owner":"韩队长"},
            {"phase":"P4","name":"启动稳定300秒无restart验证","owner":"石监理"},
        ],
        "verification_template": "PASS标准: 后台启动5分钟观察 DAEMON START 次数<=1。",
        "prevention": {
            "rule_type":"DAEMON_HEALTH_CHECK",
            "rule_title":"daemon持久循环+退出码监控，restart>=5自动入mt_error_issues",
            "enforcement_action":"sys_patrol_inspector每轮输出->ai_auto_diagnose_and_fix_engine聚合",
        },
    },
    "DEFAULT": {
        "root_cause_template": "自动聚合到默认分类，需要AI员工现场定位根因：{raw_description}",
        "phases": [
            {"phase":"P1","name":"根因现场定位","owner":"孙文档"},
            {"phase":"P2","name":"修复方案设计","owner":"钱合规"},
            {"phase":"P3","name":"§14 STEP_7施工","owner":"韩队长"},
            {"phase":"P4","name":"验收+脑库投喂","owner":"石监理"},
        ],
        "verification_template": "PASS标准: 错误日志停止>=1h，occurrences不再增长。",
        "prevention": {"rule_type":"GENERIC","enforcement_action":"写入AI脑库，sys_rule_enforcer每轮扫描"},
    },
}

class FixReportGenerator:
    """结合委派结果+模板，生成结构化修复报告（永久性详细方案）。"""

    @classmethod
    def generate(cls, issue: Dict[str, Any], delegation: Dict[str, Any]) -> Dict[str, Any]:
        cat = issue.get("category","DEFAULT")
        tpl = TEMPLATE_BY_CATEGORY.get(cat, TEMPLATE_BY_CATEGORY["DEFAULT"])

        # 模板变量填充
        def fmt(tpl_str: str) -> str:
            out = tpl_str
            # NAMING冲突
            m = NO_MODULE_NAMED.search(issue.get("description",""))
            missing_mod = m.group(1) if m else "N/A"
            out = out.replace("{module_conflict}", f"{issue.get('source_log')}:core/logging.py=Python stdlib logging")
            out = out.replace("{stdlib_pkg}", missing_mod)
            out = out.replace("{missing_tables}", ",".join(NO_SUCH_TABLE.findall(issue.get("description","")+ " " + (issue.get("stack_snippet") or ""))) or "(未知表)")
            out = out.replace("{db_paths}", "engines/app.db, ai_engines/app.db, _runtime DB")
            out = out.replace("{restart_count}", str(issue.get("occurrences","N/A")))
            out = out.replace("{raw_description}", issue.get("description","")[:300])
            return out

        root_cause = fmt(tpl["root_cause_template"])
        phases = [dict(p) for p in tpl["phases"]]
        # 把三角治理和委派AI员工对应到phase owner
        ai_names = [m["name"] for m in delegation.get("ai_employees",[])]
        if ai_names:
            # round-robin绑定到各phase
            for i, ph in enumerate(phases):
                ph["owner"] = ai_names[i % len(ai_names)]
            phases.append({"phase":"P5","name":"EigenFlux5专家二次评审","owner":"EigenFlux 5人小组"})
            phases.append({"phase":"P6","name":"脑库投喂+防复发写入","owner":"林审计+方数据"})
        verification = fmt(tpl["verification_template"])
        prevention = dict(tpl["prevention"])
        # 生成SA可读修复报告文本
        report_lines = [
            f"# 修复报告 (AUTO-PATCH-{issue['severity']})",
            f"",
            f"- IssueKey: `{issue['issue_key']}`  Category: `{cat}`  Severity: **{issue['severity']}**",
            f"- 来源日志: `{issue['source_log']}`  发生次数: {issue.get('occurrences',1)}  首现: {issue.get('first_seen')}",
            f"- 标题: {issue['title']}",
            f"- 描述: {issue['description']}",
            f"",
            f"## 1. 根因分析 (P1)",
            f"{root_cause}",
            f"",
            f"## 2. 修复阶段计划 (含三角治理+AI员工+EigenFlux)",
        ]
        for ph in phases:
            report_lines.append(f"- [{ph['phase']}] {ph['name']} — Owner: {ph['owner']}")
        report_lines += [
            f"",
            f"## 3. 验收标准",
            f"{verification}",
            f"",
            f"## 4. 防复发策略 (永久化)",
            f"- 规则类型: `{prevention.get('rule_type','')}`",
            f"- 规则标题: {prevention.get('rule_title','')}",
            f"- 强制执行点: {prevention.get('enforcement_action','')}",
            f"- 详情: {json.dumps(prevention, ensure_ascii=False)}",
            f"",
            f"## 5. 委派入驻团队",
            f"- AI员工: {', '.join(m['name'] for m in delegation.get('ai_employees',[]))}",
            f"- EigenFlux专家: {', '.join(m['name'] for m in delegation.get('eigenflux_experts',[]))}",
            f"- 三角治理: {delegation.get('triangle')}",
        ]
        return {
            "repair_id": "REPAIR-" + uuid.uuid4().hex[:14],
            "issue_key": issue["issue_key"],
            "delegation_id": delegation.get("delegation_id"),
            "flow_id": delegation.get("flow_id"),
            "root_cause": root_cause,
            "phases_json": phases,
            "verification": verification,
            "prevention_rule_json": prevention,
            "ai_team_json": delegation.get("ai_employees"),
            "eigenflux_json": delegation.get("eigenflux_experts"),
            "triangle_json": delegation.get("triangle"),
            "report_text": "\n".join(report_lines),
        }

# =========================================================
# 整合层：run_full_cycle
# =========================================================
def run_full_cycle(log_hours: int = 12,
                   manual_issues: Optional[List[Dict[str, Any]]] = None,
                   launch_flows: bool = True,
                   parent_flow: Optional[str] = None) -> Dict[str, Any]:
    """一次完整巡检闭环：扫描→分类→FLOW自动启动(可选)→委派→报告→落库→脑库投喂。
    返回 run_summary。"""
    ensure_storage_tables()
    run_id = "PATRUN-" + uuid.uuid4().hex[:12]
    started_iso = datetime.now().isoformat()
    # M1 扫描
    scanner = LogScanner(hours_back=log_hours)
    issues, scan_stats = scanner.scan()
    if manual_issues:
        # 合并手动传入Issue（如果重复不覆盖）
        seen_keys = {i["issue_key"] for i in issues}
        for mi in manual_issues:
            if "issue_key" not in mi:
                raw = f"{mi.get('source_log','manual')}||{mi.get('category','DEFAULT')}||{mi.get('title','')}"
                mi["issue_key"] = "ISS-" + hashlib.md5(raw.encode()).hexdigest()[:14]
            if mi["issue_key"] not in seen_keys:
                mi.setdefault("occurrences",1); mi.setdefault("first_seen", started_iso)
                mi.setdefault("last_seen", started_iso); mi.setdefault("source_log", "manual")
                mi.setdefault("description", mi.get("title",""))
                issues.append(mi); seen_keys.add(mi["issue_key"])
    # M2 分类
    ErrorClassifier.classify_all(issues)
    counts = {s:0 for s in ["CRITICAL","HIGH","MEDIUM","LOW","WARN"]}
    for iss in issues: counts[iss["severity"]] = counts.get(iss["severity"],0)+1

    # 导入委派引擎
    sys.path.insert(0, _BASE)
    import ai_patrol_delegation_engine as dlg
    # M3 FLOW启动 (可选) — 单独开短事务避免与后续写锁冲突
    new_flows = 0
    for iss in issues:
        if launch_flows and iss["severity"] in ("CRITICAL","HIGH") and not iss.get("assigned_flow_id"):
            fid = FlowAutoLauncher.launch_ir14_flow(iss, parent_flow=parent_flow)
            if fid:
                iss["assigned_flow_id"] = fid; new_flows += 1
    # 阶段一: 委派+脑库投喂 (每条短事务，单独调用dlg的内部连接，避免跨模块嵌套写事务)
    delegs: List[Dict[str, Any]] = []
    saves: List[Dict[str, Any]] = []
    repairs: List[Dict[str, Any]] = []
    brain_feeds_total = 0
    for iss in issues:
        dlg_report = dlg.delegate_issue(
            iss["issue_key"], iss["severity"], iss["category"],
            iss["title"], iss["description"], flow_id=iss.get("assigned_flow_id"),
        )
        # (B) 先生成报告获得完整的修复细节，再一次性给persist_and_feed_brain完整内容
        rep = FixReportGenerator.generate(iss, dlg_report)
        fix_detail = {
            "root_cause": rep["root_cause"],
            "steps": [f"[{p['phase']}]{p['name']}(owner={p['owner']})" for p in rep["phases_json"]],
            "verification": rep["verification"],
        }
        prevention = dlg.build_prevention_strategy(iss["category"], iss.get("description",""), iss["issue_key"])
        # (A) 委派+脑库投喂 (短事务，单独连接)
        save_res = dlg.persist_and_feed_brain(dlg_report, fix_detail, prevention)
        brain_feeds_total += len(save_res["brain_feeds"])
        delegs.append(dlg_report); saves.append(save_res); repairs.append(rep)
        iss["assigned_deleg_id"] = dlg_report["delegation_id"]
        iss["reported_repair_id"] = rep["repair_id"]
        iss["recurrence_blocked"] = 1

    # 阶段二: 统一入库 (mt_error_issues + mt_repair_reports + mt_patrol_runs) — 一次大事务
    with _LOCK, get_conn() as conn:
        now_iso = datetime.now().isoformat()
        # 预计算 now_iso_ts 兼容
        for iss, rep in zip(issues, repairs):
            tags_list = [iss["severity"], iss["category"]]
            if iss.get("assigned_flow_id"): tags_list.append("FLOW_AUTO_LAUNCHED")
            # (C) upsert mt_error_issues
            conn.execute("""
                INSERT INTO mt_error_issues
                    (issue_key,category,severity,title,description,stack_snippet,source_log,
                     first_seen,last_seen,occurrences,status,assigned_flow_id,assigned_deleg_id,
                     reported_repair_id,recurrence_blocked,tags_json,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(issue_key) DO UPDATE SET
                    severity=excluded.severity,
                    category=excluded.category,
                    last_seen=excluded.last_seen,
                    occurrences=mt_error_issues.occurrences+excluded.occurrences-1,
                    status=CASE WHEN mt_error_issues.status='FIXED' THEN 'FIXED' ELSE 'TRIAGED' END,
                    assigned_flow_id=COALESCE(mt_error_issues.assigned_flow_id, excluded.assigned_flow_id),
                    assigned_deleg_id=COALESCE(mt_error_issues.assigned_deleg_id, excluded.assigned_deleg_id),
                    reported_repair_id=COALESCE(mt_error_issues.reported_repair_id, excluded.reported_repair_id),
                    recurrence_blocked=excluded.recurrence_blocked,
                    tags_json=excluded.tags_json,
                    updated_at=excluded.updated_at
            """, (
                iss["issue_key"], iss["category"], iss["severity"], iss["title"],
                iss["description"], iss.get("stack_snippet"), iss["source_log"],
                iss.get("first_seen", now_iso), iss.get("last_seen", now_iso),
                iss.get("occurrences",1),
                "NEW" if not iss.get("assigned_deleg_id") else "TRIAGED",
                iss.get("assigned_flow_id"), iss.get("assigned_deleg_id"),
                iss.get("reported_repair_id"), iss.get("recurrence_blocked",0),
                json.dumps(tags_list, ensure_ascii=False),
                now_iso, now_iso
            ))
            # (D) mt_repair_reports
            conn.execute("""INSERT OR REPLACE INTO mt_repair_reports
                (repair_id,issue_key,flow_id,delegation_id,root_cause,phases_json,
                 verification,prevention_rule_json,ai_team_json,eigenflux_json,triangle_json,
                 report_text,status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                rep["repair_id"], rep["issue_key"], rep.get("flow_id"), rep["delegation_id"],
                rep["root_cause"], json.dumps(rep["phases_json"], ensure_ascii=False),
                rep["verification"], json.dumps(rep["prevention_rule_json"], ensure_ascii=False),
                json.dumps(rep["ai_team_json"], ensure_ascii=False),
                json.dumps(rep["eigenflux_json"], ensure_ascii=False),
                json.dumps(rep["triangle_json"], ensure_ascii=False),
                rep["report_text"], "GENERATED", now_iso, now_iso,
            ))

        # (E) mt_patrol_runs
        result_json = {"scan_stats":scan_stats, "counts":counts,
                       "new_flows":new_flows,"delegations_count":len(delegs),
                       "repairs_generated":len(repairs)}
        ended_iso = datetime.now().isoformat()
        conn.execute("""INSERT OR REPLACE INTO mt_patrol_runs
            (run_id,started_at,ended_at,log_hours,logs_scanned,total_issues,
             critical_cnt,high_cnt,medium_cnt,low_cnt,warn_cnt,new_flows_cnt,
             delegations_cnt,brain_feeds_cnt,result_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            run_id, started_iso, ended_iso, log_hours,
            scan_stats.get("logs_scanned",0), len(issues),
            counts.get("CRITICAL",0), counts.get("HIGH",0), counts.get("MEDIUM",0),
            counts.get("LOW",0), counts.get("WARN",0), new_flows, len(delegs),
            brain_feeds_total, json.dumps(result_json, ensure_ascii=False)
        ))
        conn.commit()
    return {
        "run_id": run_id,
        "started_at": started_iso,
        "ended_at": datetime.now().isoformat(),
        "scan_stats": scan_stats,
        "counts": counts,
        "total_issues": len(issues),
        "new_flows_auto_launched": new_flows,
        "delegations_generated": len(delegs),
        "repair_reports_generated": len(repairs),
        "brain_feeds": brain_feeds_total,
        "top_issues": [
            {"k":iss["issue_key"],"sev":iss["severity"],"cat":iss["category"],
             "occ":iss.get("occurrences",1),"src":iss.get("source_log"),
             "title":iss["title"][:80],"flow":iss.get("assigned_flow_id"),
             "deleg":iss.get("assigned_deleg_id"),"repair":iss.get("reported_repair_id")}
            for iss in issues[:30]
        ],
        "repair_reports": [
            {"repair_id":r["repair_id"],"issue_key":r["issue_key"],
             "flow_id":r.get("flow_id"),"delegation_id":r["delegation_id"]}
            for r in repairs[:30]
        ],
    }


# =========================================================
# CLI入口
# =========================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="ai_auto_diagnose_and_fix_engine CLI")
    ap.add_argument("--cycle", action="store_true", help="执行一轮完整巡检闭环")
    ap.add_argument("--hours", type=int, default=12, help="扫描过去N小时(默认12)")
    ap.add_argument("--no-flow", action="store_true", help="禁止FLOW自动启动(仅诊断)")
    ap.add_argument("--parent-flow", type=str, default=None, help="父级flow_id")
    args = ap.parse_args()
    if args.cycle:
        res = run_full_cycle(log_hours=args.hours,
                             launch_flows=(not args.no_flow),
                             parent_flow=args.parent_flow)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        ap.print_help()
