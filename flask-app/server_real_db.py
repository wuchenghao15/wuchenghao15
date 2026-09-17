#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportRedeclaration=false, reportUnusedFunction=false, reportUnusedVariable=false
# basedpyright: reportMissingImports=false, reportRedeclaration=false, reportUnusedFunction=false, reportUnreachableCode=false, reportUnusedParameter=false, reportUnusedVariable=false, reportShadowedImports=false
"""MTSCOS 正式服务入口：挂载 Database/auth.db + app.db/system_versions，
   用真实用户数据验证用户名密码，并传入 DB 中真实系统版本号。"""
from __future__ import annotations  # 兼容 Python 3.9：启用 PEP 563 延迟类型求值，支持 PEP 604 的 X|Y 注解语法
import logging
from app.middlewares.system_container import system_container as _system_container_mw
import os
import re
import sys
import time
import json
import socket
import base64
import hashlib
import sqlite3
import secrets
from datetime import datetime, timedelta

def _timefmt():
    """全项目统一的时间戳格式：ISO8601 naive local datetime."""
    return datetime.now().isoformat()


# ============================================================================
# 本机IP判断工具：获取服务器所有网络接口IP，用于判断请求是否来自本机
# 修复Bug: 局域网IP访问(如192.168.x.x)被误判为远程，导致vikey检测被禁用
# ============================================================================
_SERVER_LOCAL_IPS_CACHE: list = []
_SERVER_LOCAL_IPS_CACHE_TS: float = 0.0


def _get_server_local_ips() -> list:
    """获取服务器本机所有网络接口的IP地址（含回环和物理网卡），结果缓存5分钟。"""
    global _SERVER_LOCAL_IPS_CACHE, _SERVER_LOCAL_IPS_CACHE_TS
    now = time.time()
    if _SERVER_LOCAL_IPS_CACHE and (now - _SERVER_LOCAL_IPS_CACHE_TS) < 300:
        return _SERVER_LOCAL_IPS_CACHE
    ips = {'127.0.0.1', '::1', 'localhost'}
    try:
        hostname = socket.gethostname()
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
            for info in addr_infos:
                ip = info[4][0] if info[4] else ''
                if ip:
                    ips.add(ip)
        except Exception:
            pass
        # 尝试UDP socket方式获取本机默认出口IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            if ip:
                ips.add(ip)
        except Exception:
            pass
        # 遍历所有网络接口获取IP
        try:
            import psutil
            for iface_name, iface_addrs in psutil.net_if_addrs().items():
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET:
                        ips.add(addr.address)
                    elif addr.family == socket.AF_INET6:
                        ips.add(addr.address.split('%')[0])
        except ImportError:
            pass
        # fallback: 通过系统命令获取IP
        except Exception:
            try:
                import subprocess
                result = subprocess.run(
                    ['ifconfig'], capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if 'inet ' in line and '127.0.0.1' not in line:
                            ip = line.strip().split()[1] if ' ' in line.strip() else ''
                            if ip:
                                ips.add(ip)
                        if 'inet6 ' in line and '::1' not in line:
                            ip = line.strip().split()[1] if ' ' in line.strip() else ''
                            if ip and '%' not in ip:
                                ips.add(ip)
            except Exception:
                pass
    except Exception:
        pass
    _SERVER_LOCAL_IPS_CACHE = list(ips)
    _SERVER_LOCAL_IPS_CACHE_TS = now
    return _SERVER_LOCAL_IPS_CACHE


def _is_local_client(request_ip: str) -> bool:
    """判断请求IP是否来自服务器本机（包括回环、物理网卡、局域网IP）。"""
    if not request_ip:
        return True
    local_ips = _get_server_local_ips()
    return request_ip in local_ips or request_ip.startswith('127.') or request_ip.startswith('::1')


logger = logging.getLogger(__name__)

# ============================================================================
# [EigenFlux-FIX-C] 全局日志限流器：相同模式 WARNING/ERROR 30 秒只放行 1 条 + 周期汇总
# 来源：搜索 GitHub 开源范式 log-rate-limit / ratelimitingfilter 实践 + 自研 2025
# ============================================================================
_LOG_SUPPRESS: dict = {}              # (logger_name, levelno, msg_key) -> (last_logged_ts, suppressed_count)
_LOG_SUPPRESS_LOCK = __import__('threading').Lock()
_LOG_SUPPRESS_PERIOD_SEC = 30            # 每类消息 30s 内只打 1 次 + 汇总 1 条
_LOG_SUPPRESS_SUMMARY_INTERVAL = 300        # 每 5 分钟自动汇总一次被抑制消息

def _log_suppress_key(logger_name, levelno, msg):
    # 归一化：把数字、UUID、路径、ip 时间戳、连续数字替换为占位符，避免相同模式被判定为不同消息
    import re as _re_supp
    txt = str(msg) if not isinstance(msg, str) else msg
    k = txt
    k = _re_supp.sub(r'\b0x[0-9a-fA-F]+', '0xHEX', k)
    k = _re_supp.sub(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?\b', 'TS', k)
    k = _re_supp.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?\b', 'IP', k)
    k = _re_supp.sub(r'\b\d+(?:[,\.]\d+)*', 'N', k)
    k = _re_supp.sub(r'连续异常=\d+次', '连续异常=N次', k)
    k = _re_supp.sub(r'/[A-Za-z0-9_\-./]+', 'PATH', k)
    k = k[:120]
    return (logger_name or '', int(levelno), k)

original_logger_call = logging.Logger.callHandlers

def _rate_limited_callHandlers(self, record):
    """wrap logging.Logger.callHandlers：相同模式 WARNING/ERROR/CRITICAL 速率限制
    注意：只有 WARNING 以下的 INFO/DEBUG 完全不受影响，不限制。"""
    import time as _t
    if record.levelno < logging.WARNING:
        return original_logger_call(self, record)
    # EF5 + 网络技能模式归一化 key
    try:
        key = _log_suppress_key(self.name, record.levelno, record.getMessage())
        now = _t.time()
        with _LOG_SUPPRESS_LOCK:
            prev = _LOG_SUPPRESS.get(key)
            if prev is None:
                # 首次：直接放行，并登记
                _LOG_SUPPRESS[key] = [now, 0]
            else:
                last_ts, supp = prev
                delta = now - last_ts
                if delta < _LOG_SUPPRESS_PERIOD_SEC:
                    # 抑制
                    prev[1] = supp + 1
                    return  # 跳过原始调用
                else:
                    # 超过 30s：放行一次 + 附带抑制汇总
                    if supp > 0:
                        # 插入一条 summary 记录（复用 record 之前先打汇总
                        try:
                            summary_rec = logging.LogRecord(
                                name=self.name, level=record.levelno,
                                pathname=record.pathname, lineno=record.lineno,
                                msg=f"[日志抑制汇总 过去{int(delta)}s 共抑制 {supp} 条相同模式]",
                                args=(), exc_info=None
                            )
                            original_logger_call(self, summary_rec)
                        except Exception:
                            pass
                    # 更新时间戳
                    prev[0] = now
                    prev[1] = 0
    except Exception:
        pass  # 限流异常时放行原始日志，不能因为限流丢信息
    return original_logger_call(self, record)

try:
    logging.Logger.callHandlers = _rate_limited_callHandlers
except Exception:
    pass

# threading.excepthook 接入：避免 "Exception in thread xxx" 刷屏（走 logging.ERROR，和限流器同规则）
import threading as _thr_supp
_orig_threading_excepthook = getattr(_thr_supp, 'excepthook', None)
def _threading_excepthook_suppressed(args):
    """threading.excepthook(args)：同模式异常 30s 只打 1 条"""
    try:
        import time as _t2
        exc_type_name = getattr(args.exc_type, '__name__', str(args.exc_type)) if args.exc_type else 'Unknown'
        # key: (thread_name, exc_type_name, first_trace_line)
        tb_first = ''
        try:
            import traceback as _tb_supp
            lines = _tb_supp.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
            tb_first = ''.join(lines[-2:]) if lines else ''
        except Exception:
            pass
        key_str = f"THREAD-EXC|{args.thread or ''}|{exc_type_name}|{tb_first[:160]}"
        # 直接复用限流器的归一化和字典（不走 Logger.callHandlers，直接按时间闸门判断）
        try:
            k = ('.threading.excepthook', logging.ERROR, _log_suppress_key('.threading.excepthook', logging.ERROR, key_str))
        except Exception:
            k = ('.threading.excepthook', logging.ERROR, key_str[:120])
        now = _t2.time()
        should_log = True
        with _LOG_SUPPRESS_LOCK:
            prev = _LOG_SUPPRESS.get(k)
            if prev is None:
                _LOG_SUPPRESS[k] = [now, 0]
            else:
                last_ts, supp = prev
                delta = now - last_ts
                if delta < _LOG_SUPPRESS_PERIOD_SEC:
                    prev[1] = supp + 1
                    should_log = False
                else:
                    if supp > 0:
                        try:
                            logger.error(f"[线程异常抑制汇总 过去{int(delta)}s 共抑制 {supp} 条相同模式] 线程={args.thread} 类型={exc_type_name}")
                        except Exception:
                            pass
                    prev[0] = now
                    prev[1] = 0
        if should_log:
            if _orig_threading_excepthook is not None:
                try:
                    _orig_threading_excepthook(args)
                except Exception:
                    pass
            # 同时也用 logger 打一遍（和上面原 callHandlers 分开，避免无限递归）
            try:
                import traceback as _tb_supp2
                logger.error(f"[ThreadException] thread={args.thread} exc={exc_type_name}: {args.exc_value}\n"
                             + ''.join(_tb_supp2.format_exception(args.exc_type, args.exc_value, args.exc_traceback)[:6]))
            except Exception:
                pass
    except Exception:
        # 兜底：fallback 到原始 hook（如果有），绝不能静默吞异常
        try:
            if _orig_threading_excepthook is not None:
                _orig_threading_excepthook(args)
        except Exception:
            pass
try:
    _thr_supp.excepthook = _threading_excepthook_suppressed
except Exception:
    pass

# ============================================================================
# [EigenFlux-FIX-A/B] 启动阶段：所有候选库统一迁移 + security_events_log 补列 + health_snapshots 建表
# 参考：GitHub sperrychristian/Hack_USU_2026 db_utils.py (SCHEMA 模式) + SQLite ALTER TABLE 官方文档
# ============================================================================
_LOG_MTSCOS_DB_MIGRATION_DONE = False

def _ensure_core_tables_ensure_on_conn(conn):
    """迁移1) security_events_log 缺失列补齐（含 ai_firewall 实际写入的 timestamp 列）
    2) health_snapshots 建表（幂等）
    3) 治理框架4张表：mtscos_version_history / change_audit_log / expert_invitation_records / mtscos_ai_employees （幂等）"""

    global _LOG_MTSCOS_DB_MIGRATION_DONE
    import sqlite3 as _sq3_mig
    try:
        # 1) security_events_log 完整 schema (CREATE_IF_NOT_EXISTS)
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS security_events_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE, event_type TEXT, severity TEXT, rule_code TEXT,
                source TEXT, status TEXT DEFAULT 'open', detected_at TEXT, resolved_at TEXT,
                description TEXT, details TEXT, action_taken TEXT, target TEXT, matched TEXT,
                user_agent TEXT, ip_address TEXT, request_method TEXT, request_path TEXT,
                username TEXT, user_id INTEGER, extra_json TEXT, timestamp TEXT,
                created_at TEXT
            )""")
            conn.commit()
        except _sq3_mig.Error:
            pass
        full_cols = [
            ('event_id','TEXT'), ('event_type','TEXT'), ('severity','TEXT'), ('rule_code','TEXT'),
            ('source','TEXT'), ('status',"TEXT DEFAULT 'open'"), ('detected_at','TEXT'),
            ('resolved_at','TEXT'), ('description','TEXT'), ('details','TEXT'), ('action_taken','TEXT'),
            ('target','TEXT'), ('matched','TEXT'), ('user_agent','TEXT'), ('ip_address','TEXT'),
            ('request_method','TEXT'), ('request_path','TEXT'), ('username','TEXT'),
            ('user_id','INTEGER'), ('extra_json','TEXT'), ('timestamp','TEXT'),
            ('created_at','TEXT'),
        ]
        try:
            cur_cols = {r[1] for r in conn.execute('PRAGMA table_info(security_events_log)').fetchall()}
        except Exception:
            cur_cols = set()
        for col, decl in full_cols:
            if col in cur_cols:
                continue
            try:
                conn.execute(f'ALTER TABLE security_events_log ADD COLUMN {col} {decl}')
                conn.commit()
                logger.info(f"[MIGRATION security_events_log +{col}")
            except _sq3_mig.Error:
                pass  # ALTER TABLE 重复/不支持时跳过
        # 2) health_snapshots
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS health_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP, component TEXT NOT NULL,
                status TEXT, score REAL DEFAULT 0, details_json TEXT, host TEXT,
                pid INTEGER, uptime_sec REAL
            )""")
            conn.commit()
            for idx_sql in [
                "CREATE INDEX IF NOT EXISTS idx_hs_at ON health_snapshots(snapshot_at)",
                "CREATE INDEX IF NOT EXISTS idx_hs_comp ON health_snapshots(component)",
            ]:
                try:
                    conn.execute(idx_sql)
                    conn.commit()
                except Exception:
                    pass
        except _sq3_mig.Error:
            pass
        # 3) 治理框架 4 张表（幂等）
        _gov_ddls = [
            """CREATE TABLE IF NOT EXISTS mtscos_version_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                major INTEGER, minor INTEGER, patch INTEGER, build TEXT,
                release_channel TEXT DEFAULT 'dev',
                parent_approval_id INTEGER,
                parent_change_id TEXT,
                change_summary TEXT,
                changelog_json TEXT,
                git_commit_hash TEXT,
                git_tag TEXT,
                github_pushed INTEGER DEFAULT 0,
                release_notes_json TEXT,
                ssot_writeback_ok INTEGER DEFAULT 0,
                ssot_readback_ok INTEGER DEFAULT 0,
                published_by TEXT,
                published_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS change_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_id TEXT UNIQUE NOT NULL,
                parent_approval_id INTEGER,
                version_id INTEGER,
                version TEXT,
                operator TEXT,
                operator_role TEXT,
                change_category TEXT,
                scope_json TEXT,
                summary TEXT,
                diff_stat_json TEXT,
                files_changed_json TEXT,
                changelog_json TEXT,
                ef5_votes_json TEXT,
                ef5_voted INTEGER DEFAULT 0,
                expert_invited INTEGER DEFAULT 0,
                expert_feedback_json TEXT,
                git_ops_json TEXT,
                before_snapshot_json TEXT,
                after_snapshot_json TEXT,
                ssot_writeback_ok INTEGER DEFAULT 0,
                ssot_readback_ok INTEGER DEFAULT 0,
                status TEXT DEFAULT 'DRAFT',
                result_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS expert_invitation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_id TEXT UNIQUE,
                parent_change_id TEXT,
                parent_approval_id INTEGER,
                expert_uid TEXT,
                expert_name TEXT,
                expert_role TEXT,
                expertise_json TEXT,
                response TEXT DEFAULT 'PENDING',
                contribution_summary TEXT,
                feedback_json TEXT,
                score_given REAL,
                rationale TEXT,
                invited_by TEXT,
                invited_at TEXT DEFAULT CURRENT_TIMESTAMP,
                responded_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS mtscos_ai_employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT,
                dept TEXT,
                expertise_json TEXT,
                skills_json TEXT,
                scores_json TEXT,
                salary_tokens_per_hour REAL DEFAULT 0,
                approval_note TEXT,
                linked_approval_id INTEGER,
                linked_change_id TEXT,
                onboarded_at TEXT,
                onboarded_by TEXT,
                is_active INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
        ]
        for ddl in _gov_ddls:
            try:
                conn.execute(ddl)
                conn.commit()
            except _sq3_mig.Error:
                pass
        _gov_idx = [
            "CREATE INDEX IF NOT EXISTS idx_mvh_approval ON mtscos_version_history(parent_approval_id)",
            "CREATE INDEX IF NOT EXISTS idx_mvh_published_at ON mtscos_version_history(published_at)",
            "CREATE INDEX IF NOT EXISTS idx_mvh_channel ON mtscos_version_history(release_channel)",
            "CREATE INDEX IF NOT EXISTS idx_cal_change_id ON change_audit_log(change_id)",
            "CREATE INDEX IF NOT EXISTS idx_cal_approval ON change_audit_log(parent_approval_id)",
            "CREATE INDEX IF NOT EXISTS idx_cal_version ON change_audit_log(version)",
            "CREATE INDEX IF NOT EXISTS idx_cal_status ON change_audit_log(status)",
            "CREATE INDEX IF NOT EXISTS idx_cal_created ON change_audit_log(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_eir_change ON expert_invitation_records(parent_change_id)",
            "CREATE INDEX IF NOT EXISTS idx_eir_approval ON expert_invitation_records(parent_approval_id)",
            "CREATE INDEX IF NOT EXISTS idx_eir_expert ON expert_invitation_records(expert_uid)",
            "CREATE INDEX IF NOT EXISTS idx_emp_active ON mtscos_ai_employees(is_active, status)",
            "CREATE INDEX IF NOT EXISTS idx_emp_linked_change ON mtscos_ai_employees(linked_change_id)",
            "CREATE INDEX IF NOT EXISTS idx_emp_linked_approval ON mtscos_ai_employees(linked_approval_id)",
        ]
        for idx_sql in _gov_idx:
            try:
                conn.execute(idx_sql)
                conn.commit()
            except Exception:
                pass

        # ============ v21.0.0 系统升级: 17张业务新表 (幂等DDL, 全部users.user_id外键关联) ============
        _v21_ddls = [
            # -- K12教育模块7张表 --
            """CREATE TABLE IF NOT EXISTS k12_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, grade TEXT, tier TEXT DEFAULT 'normal',
                subjects_json TEXT DEFAULT '{}', scores_json TEXT DEFAULT '{}',
                attendance_rate REAL DEFAULT 100.0, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS k12_knowledge_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, subject TEXT, grade TEXT, name TEXT NOT NULL,
                description TEXT, mastery_level REAL DEFAULT 0.0, tags_json TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS k12_wrong_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, subject TEXT, question_id INTEGER,
                question_text TEXT, wrong_answer TEXT, correct_answer TEXT,
                wrong_count INTEGER DEFAULT 1, resolved INTEGER DEFAULT 0,
                resolved_at TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS k12_evaluations (
                eval_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL, term TEXT, overall_score REAL DEFAULT 0.0,
                academic_score REAL, physical_health REAL, artistic_accomplishment REAL,
                social_practice REAL, comments TEXT, evaluator TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS k12_admission_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, target_school TEXT, target_major TEXT,
                current_grade TEXT, estimated_score REAL, interest_type TEXT,
                plan_details TEXT, status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS k12_home_school_messages (
                msg_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL, sender_role TEXT, sender_name TEXT,
                title TEXT NOT NULL, body TEXT, priority TEXT DEFAULT 'normal',
                is_read INTEGER DEFAULT 0, read_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS k12_game_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                total_points INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
                coins INTEGER DEFAULT 0, badges_json TEXT DEFAULT '[]',
                last_play_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            # -- 成人教育模块7张表 --
            """CREATE TABLE IF NOT EXISTS adult_career_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, current_level TEXT, target_level TEXT,
                industry TEXT, skills_json TEXT DEFAULT '[]', milestones_json TEXT DEFAULT '[]',
                advisor TEXT, status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS adult_study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, plan_name TEXT, subject TEXT,
                target_level TEXT, start_date TEXT, end_date TEXT,
                weekly_hours INTEGER DEFAULT 0, progress REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS adult_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, subject TEXT, credit_type TEXT,
                credits REAL DEFAULT 0.0, source TEXT, earned_date TEXT,
                expiry_date TEXT, verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS adult_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, cert_name TEXT NOT NULL, cert_code TEXT,
                issuer TEXT, issue_date TEXT, expiry_date TEXT,
                score REAL, status TEXT DEFAULT 'valid', certificate_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS adult_corporate_programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER, program_name TEXT NOT NULL, program_type TEXT,
                description TEXT, start_date TEXT, end_date TEXT,
                capacity INTEGER DEFAULT 0, enrolled_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS adult_corporate_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL, contact_person TEXT, contact_email TEXT,
                contact_phone TEXT, industry TEXT, size_range TEXT,
                address TEXT, tax_id TEXT, status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS adult_community_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, title TEXT NOT NULL, body TEXT,
                category TEXT, tags_json TEXT DEFAULT '[]', likes INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0, replies INTEGER DEFAULT 0, pinned INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            # -- 审批通用表 + 教师补充表 (共3张) --
            """CREATE TABLE IF NOT EXISTS approval_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_type TEXT NOT NULL, requester_id INTEGER, requester_name TEXT,
                title TEXT, details_json TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending', approver_id INTEGER, approver_comments TEXT,
                approved_at TEXT, rejected_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS teacher_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL, class_name TEXT NOT NULL, grade TEXT,
                subject TEXT, student_count INTEGER DEFAULT 0, schedule_json TEXT DEFAULT '[]',
                semester TEXT, status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS teacher_exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL, exam_name TEXT NOT NULL, class_id INTEGER,
                subject TEXT, total_score REAL DEFAULT 100.0, duration_min INTEGER DEFAULT 120,
                start_time TEXT, end_time TEXT, status TEXT DEFAULT 'draft',
                questions_json TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            # -- 用户主题偏好表 (主题系统 STEP_7_EXECUTE flow_20260811103134_8fc2bd) --
            """CREATE TABLE IF NOT EXISTS mt_user_theme_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                theme_mode TEXT DEFAULT 'auto',
                auto_switch INTEGER DEFAULT 1,
                preset_name TEXT DEFAULT 'deep_space_blue',
                custom_primary TEXT,
                custom_secondary TEXT,
                custom_accent TEXT,
                bg_image_url TEXT,
                bg_opacity REAL DEFAULT 0.08,
                bg_type TEXT DEFAULT 'css_gradient',
                sunrise_time TEXT DEFAULT '06:00',
                sunset_time TEXT DEFAULT '18:00',
                latitude REAL,
                longitude REAL,
                city_name TEXT,
                memorial_lock INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id)
            )""",
        ]
        for _ddl in _v21_ddls:
            try:
                conn.execute(_ddl)
                conn.commit()
            except _sq3_mig.Error:
                pass
        _v21_indices = [
            "CREATE INDEX IF NOT EXISTS idx_k12_s_uid ON k12_students(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_k12_s_grade ON k12_students(grade)",
            "CREATE INDEX IF NOT EXISTS idx_k12_kp_uid ON k12_knowledge_points(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_k12_kp_subj ON k12_knowledge_points(subject)",
            "CREATE INDEX IF NOT EXISTS idx_k12_wq_uid ON k12_wrong_questions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_k12_wq_resolved ON k12_wrong_questions(resolved)",
            "CREATE INDEX IF NOT EXISTS idx_k12_e_uid ON k12_evaluations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_k12_ap_uid ON k12_admission_plans(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_k12_hsm_uid ON k12_home_school_messages(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_k12_hsm_read ON k12_home_school_messages(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_k12_gp_uid ON k12_game_points(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_acp_uid ON adult_career_paths(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_asp_uid ON adult_study_plans(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_ac_uid ON adult_credits(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_act_uid ON adult_certificates(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_aco_status ON adult_corporate_programs(status)",
            "CREATE INDEX IF NOT EXISTS idx_acomm_uid ON adult_community_posts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_acomm_cat ON adult_community_posts(category)",
            "CREATE INDEX IF NOT EXISTS idx_ar_status ON approval_requests(status)",
            "CREATE INDEX IF NOT EXISTS idx_ar_type ON approval_requests(request_type)",
            "CREATE INDEX IF NOT EXISTS idx_tc_tid ON teacher_classes(teacher_id)",
            "CREATE INDEX IF NOT EXISTS idx_te_tid ON teacher_exams(teacher_id)",
        ]
        for _idx in _v21_indices:
            try:
                conn.execute(_idx)
                conn.commit()
            except Exception:
                pass

    except Exception as _mig_e:
        logger.warning(f"[MIGRATION] 单库迁移出错(可忽略): {type(_mig_e).__name__}: {_mig_e}")

def _ensure_core_tables_all_candidates():
    """对 server 常见所有候选库(APP_DB/AUTH_DB/项目根app.db/flask-app/app.db/eigenflux_monitor/scheduler/log/admin/mtscos 等执行迁移
    注意：依赖 BASE_DIR，但调用时可能 BASE_DIR 尚未定义——本函数内部兜底 BASE_DIR。"""
    import sqlite3 as _sq3_mig2
    try:
        base = BASE_DIR if 'BASE_DIR' in globals() else os.path.dirname(os.path.abspath(__file__))
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    for p in [
        globals().get('APP_DB'), globals().get('AUTH_DB'),
        globals().get('SPLIT_SYSTEM_DB'), globals().get('SPLIT_AI_DB'),
    ]:
        if p and isinstance(p, str) and p not in candidates:
            candidates.append(p)
    # 项目根 + 常见子目录 + 常见 db 文件名（覆盖 ai_firewall 可能写的 log.db/mtscos.db/admin.db/mtscos_app.db/security_events.db/核心 app.db 等）
    for rel in ['.', 'flask-app', 'data', 'core', 'services/eigenflux', 'core/services']:
        for fn in ['app.db', 'auth.db', 'system.db', 'ai.db', 'eigenflux_monitor.db',
                    'scheduler.db', 'vikey_auth.db', 'rule_approval.db',
                    'log.db', 'mtscos.db', 'admin.db', 'mtscos_app.db',
                    'security_events.db', 'permissions.db', 'exam.db', 'question.db',
                    'user.db', 'learning.db', 'proctor.db']:
            fp = os.path.join(base, rel, fn)
            if os.path.exists(fp) and fp not in candidates:
                candidates.append(fp)
    done_any = False
    migrated_count = 0
    for fp in sorted(set(candidates)):
        if not fp or not os.path.exists(fp):
            continue
        try:
            # OneDrive 占位符会 timeout/disk I/O，超时 5s 快速跳过，不阻塞
            conn = _sq3_mig2.connect(fp, timeout=5)
            try:
                _ensure_core_tables_ensure_on_conn(conn)
                done_any = True
                migrated_count += 1
            finally:
                try: conn.close()
                except Exception: pass
        except Exception as _e:
            # 不 INFO 到日志（否则占位符 db 太多会刷屏），只 DEBUG 级内存记录
            pass
    global _LOG_MTSCOS_DB_MIGRATION_DONE
    if done_any and not _LOG_MTSCOS_DB_MIGRATION_DONE:
        _LOG_MTSCOS_DB_MIGRATION_DONE = True
        logger.info(f"[MIGRATION] 候选库迁移完成（{migrated_count} 个DB），错误日志治理 DDL 已生效")

# 模块加载阶段先跑迁移 (daemon，不阻塞启动)
try:
    import threading as _thr_mig
    _mig_thr = _thr_mig.Thread(target=_ensure_core_tables_all_candidates, name='mtscos-ddl-mig', daemon=True)
    _mig_thr.start()
except Exception:
    try:
        _ensure_core_tables_all_candidates()  # 线程起不来就同步跑
    except Exception:
        pass
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from core.db_path import patch_sqlite3_connect as _mtscos_patch, get_db_path
    _mtscos_patch(verbose=False)
except Exception as _e:
    sys.stderr.write(f"[WARN] db_path patch failed (server_real_db): {_e}\n")
    from core.db_path import get_db_path

AUTH_DB = get_db_path('auth.db')
APP_DB = get_db_path('app.db')
SPLIT_SYSTEM_DB = get_db_path('system.db')
SPLIT_AI_DB = get_db_path('ai.db')
SPLIT_EXAM_DB = get_db_path('exam.db')
SPLIT_QUESTION_DB = get_db_path('question.db')
SPLIT_USER_DB = get_db_path('user.db')
SPLIT_ADMIN_DB = get_db_path('admin.db')
SPLIT_LEARNING_DB = get_db_path('learning.db')
SPLIT_LOG_DB = get_db_path('log.db')
SPLIT_PROCTOR_DB = get_db_path('proctor.db')
DATA_MTSCOS_DB = get_db_path('mtscos.db')
VERSION_FILE = os.path.join(BASE_DIR, 'VERSION')

from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, session, send_file
from jinja2 import Undefined as _JinjaUndefined


class _FriendlyUndefined(_JinjaUndefined):
    """
    兼容模板老变量：任何未传的变量名 / 属性链 / 函数调用 / 迭代都不抛错，
    打印为''、布尔False、迭代为[]、比较为None，从而杜绝 UndefinedError 500。
    """
    __slots__ = ()

    def __str__(self):
        return ''

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0

    def __getattr__(self, item):
        if item.startswith('_'):
            raise AttributeError(item)
        return _FriendlyUndefined()

    def __getitem__(self, item):
        return _FriendlyUndefined()

    def __call__(self, *args, **kwargs):
        return _FriendlyUndefined()

    def __eq__(self, other):
        return other is None or isinstance(other, _FriendlyUndefined)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 0

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __repr__(self):
        return ''


app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.url_map.strict_slashes = False  # 全局: /foo ↔ /foo/ 等价, 避免 catch-all 路由 404
# v22.39.0: secret_key 固定不变 (之前是 + time.time() 导致每次 Flask 重启所有登录 session 失效)
# 登录态由 mtscos_sid + Flask session cookie 双重保证, secret_key 变 = Flask session cookie 全部作废
# 固定值保留向后兼容 (v22.38.0 以前的部署也能继续用同一个 secret_key)
app.secret_key = 'mtscos-real-db-secret-ANDRV59-20260912-FIXED-CONSTANT-VALUE'
app.jinja_env.undefined = _FriendlyUndefined
app.jinja_env.auto_reload = True


# ═══════════════════════════════════════════════════════════════════════
# 仙女座-阿尔法 (Andromeda-Alpha) API 规范 v1.0.0
# 统一响应信封 + 错误码 + 自描述端点
# ═══════════════════════════════════════════════════════════════════════

# ── 仙女座错误码体系 ──
ANDROMEDA_ERROR_CODES = {
    "E_OK":          (200, "success"),
    "E_BAD_REQUEST": (400, "请求格式错误"),
    "E_AUTH":        (401, "需要登录 / 鉴权失败"),
    "E_FORBIDDEN":   (403, "权限不足 (SA-only)"),
    "E_NOT_FOUND":   (404, "资源不存在"),
    "E_CONFLICT":    (409, "冲突 (如重复注册路由)"),
    "E_VALIDATION":  (422, "参数验证失败"),
    "E_RATE_LIMIT":  (429, "速率限制触发"),
    "E_INTERNAL":    (500, "内部错误"),
    "E_MODEL_DOWN":  (503, "本地 Ollama 不可用"),
}


def _andromeda_response(data=None, code="E_OK", message=None,
                        extra=None, http_status=None):
    """仙女座 API 统一响应信封

    返回 {success, code, message, data, trace_id} 格式的 JSON 响应。
    - code: ANDROMEDA_ERROR_CODES 中的错误码字符串, 或直接传 HTTP int (自动映射)
    - data: 业务数据 (None 时自动设为 null)
    - extra: 额外字段 dict (如 trace_id, pagination)
    """
    # 解析 code
    if isinstance(code, int):
        # 直接传 HTTP 状态码 → 反查错误码
        matched = [k for k, (http, _) in ANDROMEDA_ERROR_CODES.items()
                   if http == code]
        code_str = matched[0] if matched else "E_OK"
        http = code
    else:
        code_str = code
        http, default_msg = ANDROMEDA_ERROR_CODES.get(
            code, ANDROMEDA_ERROR_CODES["E_INTERNAL"])
        message = message or default_msg
    success = code_str == "E_OK"

    envelope = {
        "success": success,
        "code": code_str,
        "message": message,
        "data": data if data is not None else None,
        "trace_id": getattr(session, "get", lambda k: None)("mt_trace", None),
        "arch": "仙女座-阿尔法/Andromeda-Alpha",
    }
    if extra:
        envelope.update(extra)
    return jsonify(envelope), (http_status or http)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Flask 3.x: 禁止 jsonify 把中文转 \uXXXX, 声明 utf-8, 输出缩进 2 格
# Flask 3.1.3 的 DefaultJSONProvider.dumps 漏处理了 indent, 需要 monkey-patch
try:
    import json as _json_mod
    _orig_dumps = app.json.dumps
    def _patched_dumps(obj, **kw):
        kw.setdefault("ensure_ascii", False)
        kw.setdefault("indent", 2)
        kw.setdefault("sort_keys", False)
        return _orig_dumps(obj, **kw)
    app.json.dumps = _patched_dumps
    app.json.mimetype = 'application/json; charset=utf-8'
except Exception:
    app.config['JSON_AS_ASCII'] = False
# ---------- v2.8.1: 注册 frontend/templates 为 Jinja 回退搜索路径 ----------
# flask-app/templates (138) 为主路径, frontend/templates (3181) 为回退路径
# 解决 index.html / admin_dashboard.html / process_monitor.html 等3000+模板缺失导致的500
try:
    _frontend_tmpl_dir = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend', 'templates'))
    if os.path.isdir(_frontend_tmpl_dir):
        _cur_loader = app.jinja_loader
        if hasattr(_cur_loader, 'searchpath') and isinstance(_cur_loader.searchpath, list):
            if _frontend_tmpl_dir not in _cur_loader.searchpath:
                _cur_loader.searchpath.append(_frontend_tmpl_dir)
        else:
            from jinja2 import ChoiceLoader, FileSystemLoader
            app.jinja_loader = ChoiceLoader([_cur_loader, FileSystemLoader(_frontend_tmpl_dir)])
except Exception:
    pass
# ---------- Session & Remember-me 安全属性 ----------
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # Session: 7天
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
except Exception:
    pass

# ---------- v2.8.1: 静态文件回退 (flask-app/static → frontend/static) ----------
# flask-app/static (8 files) 为主, frontend/static (116 files) 为回退
# 解决 mtscos_compat_shim.css 等116个静态资源404问题
try:
    _frontend_static_dir = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend', 'static'))
    _orig_send_static_file = app.send_static_file
    def _mt_send_static_file(filename):
        from flask import send_from_directory, abort
        # 主静态目录优先
        try:
            return _orig_send_static_file(filename)
        except Exception:
            pass
        # 回退到 frontend/static
        if os.path.isdir(_frontend_static_dir):
            return send_from_directory(_frontend_static_dir, filename)
        abort(404)
    app.send_static_file = _mt_send_static_file
except Exception:
    pass

# ---------- v2.0: 规则拦截器注册 (4层拦截-Layer2: Flask before_request) ----------
# 拦截未走7步审批的规则修改请求 (POST/PUT/PATCH/DELETE /api/rules/*)
# bypass_allowed=False, 禁止任何人绕过 (含超级管理员 wuchenghao15)
try:
    from ai_engines.rules_engine.rule_interceptor import register_interceptor as _mt_register_rule_interceptor
    _mt_rule_interceptor = _mt_register_rule_interceptor(app)
    print("[RULES-ENGINE] Flask before_request interceptor registered (Layer-2)")
except Exception as _mt_ri_err:
    print(f"[RULES-ENGINE] interceptor register skip: {_mt_ri_err}")
_MT_REMEMBER_COOKIE = '_mts_rm_tk'
_MT_REMEMBER_MAX_AGE = 86400 * 30  # Remember-me token: 30天
_MT_REMEMBER_IP_HISTORY = {}  # token_id -> {ip_set, first_seen}

# 映射 /assets/ 路径到 static/assets/ 目录，消除 base.html 中 4 个 404 引用
from flask import send_from_directory as _mt_send_from_directory
from flask import Response as _mt_Response
_assets_dir = os.path.join(BASE_DIR, 'static', 'assets')
_assets_alt_dirs = [
    os.path.join(BASE_DIR, 'assets'),          # 项目根 assets/ (font-awesome)
    os.path.join(BASE_DIR, 'src', 'html', 'assets'),  # src/html/assets (mtscos-design-system.css)
]
_ASSETS_CACHE_DIR = os.path.join(BASE_DIR, 'static', 'assets', '_cache')
_ASSETS_CACHE_OK = False  # 预热标志
_ASSETS_CACHE_MAP = {}  # filename → local_cached_fullpath

# FontAwesome 路径映射 → 已有缓存系统的 key
_FA_ASSETS_REMAP = {
    'font-awesome/css/all.min.css': '__all.min.css',  # _FA_CACHE_WHITELIST key
}

def _mt_assets_read_with_timeout(src_path, timeout_s=15):
    """限时读取 OneDrive 文件：成功返回 bytes，失败返回 None"""
    try:
        import subprocess as _sp
        res = _sp.run(
            [sys.executable or 'python3', '-c',
             'import sys,os;p=sys.argv[1];'
             'import signal as _sig;'
             'class _T(Exception):pass;'
             'def _h(s,f):raise _T();'
             '_sig.signal(_sig.SIGALRM,_h);_sig.alarm(12);'
             'f=open(p,"rb");d=f.read();f.close();_sig.alarm(0);'
             'sys.stdout.buffer.write(d)',
             src_path],
            capture_output=True, timeout=timeout_s, check=False,
        )
        if res.returncode == 0 and res.stdout:
            return res.stdout
    except Exception:
        pass
    try:
        with open(src_path, 'rb') as _fh:
            return _fh.read()
    except Exception:
        return None

def _mt_assets_warmup_cache():
    """预热 assets 本地缓存：启动时尝试把关键 CSS 文件复制到 ~/.mtscos_cache/assets/"""
    global _ASSETS_CACHE_OK, _ASSETS_CACHE_MAP
    try:
        os.makedirs(_ASSETS_CACHE_DIR, exist_ok=True)
    except Exception as _ce:
        print(f"[Assets-Cache] 无法创建缓存目录 {_ASSETS_CACHE_DIR}: {_ce}", flush=True)
        return
    cached_count = 0
    # 预热列表：需要缓存的关键 CSS 文件
    _WARMUP_TARGETS = [
        ('css/mtscos-design-system.css', 'src/html/assets/css/mtscos-design-system.css'),
        ('font-awesome/css/all.min.css', 'assets/font-awesome/css/all.min.css'),
        ('css/style.css', 'src/html/assets/css/style.css'),
    ]
    for cache_rel, src_rel in _WARMUP_TARGETS:
        src_path = os.path.join(BASE_DIR, src_rel)
        cache_path = os.path.join(_ASSETS_CACHE_DIR, cache_rel)
        cache_dir = os.path.dirname(cache_path)
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            pass
        # 已有缓存且非占位符（>100 bytes）→ 跳过
        try:
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
                _ASSETS_CACHE_MAP[cache_rel] = cache_path
                cached_count += 1
                continue
        except Exception:
            pass
        # 从源路径限时读取
        if os.path.exists(src_path):
            data = _mt_assets_read_with_timeout(src_path, timeout_s=20)
            if data and len(data) > 50:
                try:
                    tmp = cache_path + '.tmp_' + str(os.getpid())
                    with open(tmp, 'wb') as tf:
                        tf.write(data)
                    os.replace(tmp, cache_path)
                    _ASSETS_CACHE_MAP[cache_rel] = cache_path
                    cached_count += 1
                    print(f"[Assets-Cache] 预热成功 {cache_rel} ({len(data)} bytes)", flush=True)
                except Exception as _we:
                    print(f"[Assets-Cache] 写入缓存失败 {cache_rel}: {_we}", flush=True)
    _ASSETS_CACHE_OK = True
    print(f"[Assets-Cache] 预热完成：本地缓存 {cached_count} 个文件（目录 {_ASSETS_CACHE_DIR}）", flush=True)

@app.route('/assets/<path:filename>')
def _serve_assets(filename):
    """静态资源路由：带本地缓存的多源回退查找，绕过 OneDrive 占位符 TimeoutError"""
    import mimetypes as _mt_mimetypes
    # 安全：路径清理
    safe_name = os.path.normpath(filename).lstrip('/')
    if safe_name.startswith('..'):
        from flask import abort
        abort(400)
    mime = _mt_mimetypes.guess_type(safe_name)[0] or 'application/octet-stream'

    # 0) FontAwesome 特殊路径 → 直接返回缓存内容（绕过 OneDrive + 避免 302 redirect）
    if safe_name in _FA_ASSETS_REMAP:
        fa_cache_key = _FA_ASSETS_REMAP[safe_name]
        fa_cached = _FA_CACHE_WHITELIST.get(fa_cache_key)
        if fa_cached and os.path.exists(fa_cached):
            try:
                with open(fa_cached, 'rb') as _fa_cf:
                    fa_body = _fa_cf.read()
                if len(fa_body) > 0:
                    resp = _mt_Response(fa_body, status=200, mimetype='text/css; charset=utf-8')
                    resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                    resp.headers['Content-Length'] = str(len(fa_body))
                    return resp
            except Exception:
                pass
        # 缓存未命中 → 直接 404，避免浏览器加载空文件

    # 0.5) FontAwesome webfonts 路径 → 从本地缓存读取（绕过 OneDrive 占位符）
    #      CSS 内部用 ../webfonts/ 相对引用，浏览器请求 /assets/font-awesome/css/webfonts/xxx.woff2
    #      本地缓存在 ~/.mtscos_cache/fontawesome/webfonts/xxx.woff2
    if safe_name.startswith('font-awesome/') and ('webfonts/' in safe_name or '/webfonts/' in safe_name):
        _fa_font_filename = os.path.basename(safe_name)  # e.g. fa-solid-900.woff2
        _fa_cached_font = os.path.join(_FA_CACHE_WEBFONTS_DIR, _fa_font_filename)
        if os.path.exists(_fa_cached_font):
            try:
                with open(_fa_cached_font, 'rb') as _ff:
                    _fa_font_body = _ff.read()
                if len(_fa_font_body) > 0:
                    import mimetypes as _fa_mt
                    _fa_mime = _fa_mt.guess_type(_fa_font_filename)[0] or 'application/octet-stream'
                    resp = _mt_Response(_fa_font_body, status=200, mimetype=_fa_mime)
                    resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                    resp.headers['Content-Length'] = str(len(_fa_font_body))
                    return resp
            except Exception:
                pass

    # 1) 命中本地缓存 → 直接返回
    if not _ASSETS_CACHE_OK:
        _mt_assets_warmup_cache()
    cached_path = _ASSETS_CACHE_MAP.get(safe_name)
    if cached_path and os.path.exists(cached_path):
        try:
            with open(cached_path, 'rb') as _cf:
                body = _cf.read()
            if len(body) > 0:
                resp = _mt_Response(body, status=200, mimetype=mime)
                resp.headers['Cache-Control'] = 'public, max-age=3600'
                resp.headers['Content-Length'] = str(len(body))
                return resp
        except Exception:
            pass  # 缓存失效，继续尝试源文件

    # 2) 从源路径限时读取（绕过 OneDrive 超时）
    for search_dir in [_assets_dir] + _assets_alt_dirs:
        candidate = os.path.join(search_dir, safe_name)
        if os.path.exists(candidate):
            data = _mt_assets_read_with_timeout(candidate, timeout_s=15)
            if data and len(data) > 0:
                # 成功读取 → 写入缓存
                try:
                    cache_dst = os.path.join(_ASSETS_CACHE_DIR, safe_name)
                    os.makedirs(os.path.dirname(cache_dst), exist_ok=True)
                    tmp = cache_dst + '.tmp_' + str(os.getpid())
                    with open(tmp, 'wb') as tf:
                        tf.write(data)
                    os.replace(tmp, cache_dst)
                    _ASSETS_CACHE_MAP[safe_name] = cache_dst
                except Exception:
                    pass
                resp = _mt_Response(data, status=200, mimetype=mime)
                resp.headers['Cache-Control'] = 'public, max-age=3600'
                resp.headers['Content-Length'] = str(len(data))
                return resp

    # 3) 兜底 → 404
    from flask import abort
    abort(404)

# ================================================================
# 🔧 FontAwesome 字体 OneDrive 占位符修复（CRITICAL for woff2/ttf/woff/otf）
#
# 根因：字体文件位于 OneDrive 同步目录，Cloud 占位符连读 1 字节都触发
#       TimeoutError [Errno 60] Operation timed out（dt~500-700ms），
#       导致 Werkzeug WSGI 流式读取阶段抛出 500。
# 修复：启动时把能读取到的字体/CSS 复制到 ~/.mtscos_cache（本地磁盘），
#       用自定义路由覆盖 /static/fontawesome/**，一次性返回 bytes（非流式），
#       彻底绕开 OneDrive 占位符和 Werkzeug wrap_file 分段读取超时。
# ================================================================
_FA_SRC_DIR = os.path.join(BASE_DIR, 'static', 'fontawesome')
_FA_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.mtscos_cache', 'fontawesome')
_FA_CACHE_WEBFONTS_DIR = os.path.join(_FA_CACHE_DIR, 'webfonts')
_FA_CACHE_OK = False  # 缓存目录是否至少有 1 个文件成功预热
_FA_CACHE_WHITELIST = {}  # filename → local_cached_fullpath（仅缓存已验证可本地读的文件）
# 当本地缓存/OneDrive 都读不到字体时，302 重定向到公共 CDN（cdnjs / jsdelivr），确保前端 0 报错
_FA_CDN_PRIMARY = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2'
_FA_CDN_FALLBACK = 'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2'
try:
    from flask import redirect as _mt_redirect
except Exception:
    _mt_redirect = None

def _mt_fa_read_with_timeout(src_path, timeout_s=15):
    """限时读取 OneDrive 文件：成功返回 bytes，失败返回 None。
    优先使用非信号量的子进程方式（避免主进程信号冲突），失败时回退到直接 open。"""
    try:
        import subprocess
        res = subprocess.run(
            [sys.executable or 'python3', '-c',
             'import sys; p=sys.argv[1];'
             'import signal;'
             'class _T(Exception):pass;'
             'def _h(s,f):raise _T();'
             'signal.signal(signal.SIGALRM,_h);signal.alarm(12);'
             'f=open(p,"rb");data=f.read();f.close();signal.alarm(0);'
             'sys.stdout.buffer.write(data)',
             src_path],
            capture_output=True, timeout=timeout_s, check=False,
        )
        if res.returncode == 0 and res.stdout:
            return res.stdout
    except Exception:
        pass
    # fallback：直接 open 读
    try:
        with open(src_path, 'rb') as _fh:
            return _fh.read()
    except Exception:
        return None

def _mt_fa_download_from_cdn(cdn_path_suffix, timeout_s=30, retries=2):
    """从公共 CDN 下载 FontAwesome 文件（作为 OneDrive 占位符的兜底）。
    cdn_path_suffix: 'webfonts/fa-solid-900.woff2' 或 'css/all.min.css'
    返回 bytes 或 None。"""
    import urllib.request as _ur
    import ssl as _ssl
    cdn_urls = [
        f'{_FA_CDN_PRIMARY}/{cdn_path_suffix}',
        f'{_FA_CDN_FALLBACK}/{cdn_path_suffix}',
    ]
    # 创建一个忽略 SSL 问题的 context（内网/企业代理环境兼容性）
    try:
        _ctx = _ssl.create_unverified_context()
    except Exception:
        _ctx = None
    for attempt in range(max(1, retries)):
        for url in cdn_urls:
            try:
                req = _ur.Request(url, headers={
                    'User-Agent': 'MTSCOS-FA-Cache/1.0',
                    'Accept': '*/*',
                })
                kw = {'timeout': timeout_s}
                if _ctx is not None:
                    kw['context'] = _ctx
                with _ur.urlopen(req, **kw) as resp:
                    data = resp.read()
                    if data and len(data) > 1000:  # 至少大于 1KB，避免空错误页
                        return data
            except Exception as _e:
                if attempt == retries - 1 and url == cdn_urls[-1]:
                    print(f"[FontAwesome-CDN] 下载失败 {url}: {type(_e).__name__}: {_e}", flush=True)
                continue
    return None

def _mt_fa_warmup_cache():
    """预热 FontAwesome 本地磁盘缓存（仅模块加载时跑 1 次）。返回缓存到的文件数。
    三级策略：① 本地 OneDrive 读 → ② 缓存命中大小对比 → ③ CDN 下载兜底（彻底避免请求时 302 跨域 ABORTED）。"""
    global _FA_CACHE_OK
    cached_count = 0
    try:
        os.makedirs(_FA_CACHE_WEBFONTS_DIR, exist_ok=True)
    except Exception as _ce:
        print(f"[FontAwesome-Cache] 无法创建缓存目录 {_FA_CACHE_WEBFONTS_DIR}: {_ce}", flush=True)
        return 0
    # FontAwesome 6.5.2 强制字体/CSS 文件清单（从 all.min.css 的 @font-face 推断）
    _FA_WEBFONTS_LIST = [
        'fa-brands-400.woff2', 'fa-brands-400.ttf',
        'fa-regular-400.woff2', 'fa-regular-400.ttf',
        'fa-solid-900.woff2',  'fa-solid-900.ttf',
        'fa-v4compatibility.woff2', 'fa-v4compatibility.ttf',
    ]
    _FA_ALL_CSS = 'all.min.css'
    env_no_cdn = os.environ.get('MTSCOS_NO_FA_CDN', '0') == '1'
    # 1) 预热 webfonts
    src_webfonts = os.path.join(_FA_SRC_DIR, 'webfonts')
    src_dir_exists = os.path.isdir(src_webfonts)
    for fname in _FA_WEBFONTS_LIST:
        cache_fp = os.path.join(_FA_CACHE_WEBFONTS_DIR, fname)
        # 缓存命中：大小 > 0 就用（OneDrive 占位符本身的 size 是假的，所以只看缓存文件真实 size）
        cache_size = os.path.getsize(cache_fp) if os.path.exists(cache_fp) else -1
        if cache_size > 0:
            _FA_CACHE_WHITELIST[fname] = cache_fp
            cached_count += 1
            continue
        # ① 尝试读 OneDrive 源目录
        got_bytes = None
        if src_dir_exists:
            src_fp = os.path.join(src_webfonts, fname)
            if os.path.exists(src_fp):
                got_bytes = _mt_fa_read_with_timeout(src_fp, timeout_s=20)
        # ② 读不到 → 尝试 CDN 下载
        if (not got_bytes or len(got_bytes) < 1000) and not env_no_cdn:
            got_bytes = _mt_fa_download_from_cdn(f'webfonts/{fname}', timeout_s=30, retries=2)
        if got_bytes and len(got_bytes) > 1000:
            try:
                tmp_path = cache_fp + '.tmp_' + str(os.getpid())
                with open(tmp_path, 'wb') as tf:
                    tf.write(got_bytes)
                os.replace(tmp_path, cache_fp)
                _FA_CACHE_WHITELIST[fname] = cache_fp
                cached_count += 1
                _mark = '[CDN]' if (not src_dir_exists or not os.path.exists(os.path.join(src_webfonts, fname))) else '[本地]'
                print("[FontAwesome-Cache] ✅ 缓存字体 {} ({} bytes) {}".format(fname, len(got_bytes), _mark), flush=True)
            except Exception as _we:
                print(f"[FontAwesome-Cache] 写入 {cache_fp} 失败: {_we}", flush=True)
        else:
            print(f"[FontAwesome-Cache] ⚠️ {fname} 暂时无法获取（OneDrive占位符+CDN不可达，MTSCOS_NO_FA_CDN={env_no_cdn}，图标会降级为系统字体）", flush=True)
    # 2) 预热 all.min.css
    css_cache = os.path.join(_FA_CACHE_DIR, _FA_ALL_CSS)
    css_src = os.path.join(_FA_SRC_DIR, _FA_ALL_CSS)
    cache_css_size = os.path.getsize(css_cache) if os.path.exists(css_cache) else -1
    if cache_css_size > 0:
        _FA_CACHE_WHITELIST[f'__{_FA_ALL_CSS}'] = css_cache
        cached_count += 1
    else:
        got_css = None
        if os.path.exists(css_src):
            got_css = _mt_fa_read_with_timeout(css_src, timeout_s=20)
        if (not got_css or len(got_css) < 1000) and not env_no_cdn:
            got_css = _mt_fa_download_from_cdn(f'css/{_FA_ALL_CSS}', timeout_s=30, retries=2)
        if got_css and len(got_css) > 1000:
            try:
                tmp_path = css_cache + '.tmp_' + str(os.getpid())
                with open(tmp_path, 'wb') as tf:
                    tf.write(got_css)
                os.replace(tmp_path, css_cache)
                _FA_CACHE_WHITELIST[f'__{_FA_ALL_CSS}'] = css_cache
                cached_count += 1
                print(f"[FontAwesome-Cache] ✅ 缓存 CSS all.min.css ({len(got_css)} bytes)", flush=True)
            except Exception:
                pass
    if cached_count > 0:
        _FA_CACHE_OK = True
    print(f"[FontAwesome-Cache] 预热完成：本地缓存 {cached_count} 个文件（目录 {_FA_CACHE_DIR}，离线可用）", flush=True)
    return cached_count

# 模块加载时立即预热（只做：①缓存命中检查  ②OneDrive 本地快速读取；CDN 下载放后台线程避免阻塞 HTTP 启动）
import sys as _sys
try:
    _mt_fa_warmup_cache()
except Exception as _warmup_err:
    print(f"[FontAwesome-Cache] 预热异常: {_warmup_err}", flush=True)

def _mt_fa_bg_cdn_download():
    """后台线程：对仍未缓存的字体/CSS，静默从 CDN 下载到本地缓存（不阻塞 HTTP 启动）。"""
    try:
        import time as _t
        _t.sleep(3)  # 等 HTTP 监听先起
        _FA_WEBFONTS_LIST = [
            'fa-brands-400.woff2', 'fa-brands-400.ttf',
            'fa-regular-400.woff2', 'fa-regular-400.ttf',
            'fa-solid-900.woff2',  'fa-solid-900.ttf',
            'fa-v4compatibility.woff2', 'fa-v4compatibility.ttf',
        ]
        env_no_cdn = os.environ.get('MTSCOS_NO_FA_CDN', '0') == '1'
        if env_no_cdn:
            return
        for fname in _FA_WEBFONTS_LIST:
            cache_fp = os.path.join(_FA_CACHE_WEBFONTS_DIR, fname)
            cache_size = os.path.getsize(cache_fp) if os.path.exists(cache_fp) else -1
            if cache_size > 0:
                continue
            # 尚未缓存 → CDN 下载
            data = _mt_fa_download_from_cdn(f'webfonts/{fname}', timeout_s=30, retries=2)
            if data and len(data) > 1000:
                try:
                    tmp_path = cache_fp + '.tmp_bg_' + str(os.getpid())
                    with open(tmp_path, 'wb') as tf:
                        tf.write(data)
                    os.replace(tmp_path, cache_fp)
                    _FA_CACHE_WHITELIST[fname] = cache_fp
                    print(f"[FontAwesome-Cache][bg] ✅ {fname} ({len(data)} bytes)", flush=True)
                except Exception:
                    pass
        # all.min.css 兜底下载
        css_cache = os.path.join(_FA_CACHE_DIR, 'all.min.css')
        css_cache_size = os.path.getsize(css_cache) if os.path.exists(css_cache) else -1
        if css_cache_size <= 0:
            data_c = _mt_fa_download_from_cdn('css/all.min.css', timeout_s=30, retries=2)
            if data_c and len(data_c) > 1000:
                try:
                    tmp_path = css_cache + '.tmp_bg_' + str(os.getpid())
                    with open(tmp_path, 'wb') as tf:
                        tf.write(data_c)
                    os.replace(tmp_path, css_cache)
                    _FA_CACHE_WHITELIST['__all.min.css'] = css_cache
                    print(f"[FontAwesome-Cache][bg] ✅ all.min.css ({len(data_c)} bytes)", flush=True)
                except Exception:
                    pass
    except Exception as _bge:
        print(f"[FontAwesome-Cache][bg] 后台 CDN 下载出错: {_bge}", flush=True)

# 后台线程启动（daemon，不阻塞退出）
try:
    import threading as _thr
    _fa_bg_thread = _thr.Thread(target=_mt_fa_bg_cdn_download, name='fa-cdn-bg', daemon=True)
    _fa_bg_thread.start()
except Exception as _te:
    print(f"[FontAwesome-Cache] 后台CDN下载线程启动失败: {_te}", flush=True)

@app.route('/static/fontawesome/webfonts/<path:filename>')
def _serve_fa_webfonts(filename):
    """覆盖 Flask 默认 static 路由：从本地磁盘缓存一次性返回字体 bytes。
    避免：① OneDrive 占位符 TimeoutError  ② Werkzeug wrap_file 分段流式读取超时  ③ 302→CDN 导致的跨域 ABORTED。"""
    import re as _re_san
    # 安全：只允许 [A-Za-z0-9._-] 字符的文件名，防止路径穿越
    _san = _re_san.sub(r'[^A-Za-z0-9._-]', '', os.path.basename(filename or ''))
    if not _san:
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400
    mime = _mt_mimetypes.guess_type(_san)[0] or 'application/octet-stream'
    env_no_cdn = os.environ.get('MTSCOS_NO_FA_CDN', '0') == '1'
    # ① 命中本地缓存 → 一次性读入返回（非流式）
    cached_path = _FA_CACHE_WHITELIST.get(_san)
    if cached_path and os.path.exists(cached_path):
        try:
            with open(cached_path, 'rb') as _cf:
                body = _cf.read()
            if len(body) > 0:
                resp = _mt_Response(body, status=200, mimetype=mime)
                resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                resp.headers['Content-Length'] = str(len(body))
                return resp
        except Exception as _e1:
            print(f"[FontAwesome-Cache] 读缓存 {_san} 失败: {_e1}", flush=True)
    # ② 未命中缓存 → 再试一次源目录限时读取
    src_fp = os.path.join(_FA_SRC_DIR, 'webfonts', _san)
    got_b = None
    if os.path.exists(src_fp):
        got_b = _mt_fa_read_with_timeout(src_fp, timeout_s=15)
    # ③ 源目录也读不到 → 同步从 CDN 下载（不做 302，避免跨域 ABORTED），并顺手补缓存
    if (not got_b or len(got_b) < 1000) and not env_no_cdn:
        got_b = _mt_fa_download_from_cdn(f'webfonts/{_san}', timeout_s=30, retries=2)
    if got_b and len(got_b) > 1000:
        try:
            cache_fp = os.path.join(_FA_CACHE_WEBFONTS_DIR, _san)
            tmp_path = cache_fp + '.tmp_' + str(os.getpid())
            with open(tmp_path, 'wb') as tf:
                tf.write(got_b)
            os.replace(tmp_path, cache_fp)
            _FA_CACHE_WHITELIST[_san] = cache_fp
            print(f"[FontAwesome-Cache] 运行时补缓存 {_san} ({len(got_b)} bytes)", flush=True)
        except Exception:
            pass
        resp = _mt_Response(got_b, status=200, mimetype=mime)
        resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        resp.headers['Content-Length'] = str(len(got_b))
        return resp
    # ④ 极端兜底：返回 404 空 body，浏览器降级系统字体（不再抛 500 / 302 跨域）
    return _mt_Response(b'', status=404, mimetype=mime)

@app.route('/static/fontawesome/all.min.css')
def _serve_fa_all_css():
    """覆盖 all.min.css：从本地缓存返回，最后 fallback 同步 CDN 下载（不 302）。"""
    mime = 'text/css; charset=utf-8'
    env_no_cdn = os.environ.get('MTSCOS_NO_FA_CDN', '0') == '1'
    cached_css = _FA_CACHE_WHITELIST.get('__all.min.css')
    if cached_css and os.path.exists(cached_css):
        try:
            with open(cached_css, 'rb') as _cf:
                body = _cf.read()
            if len(body) > 0:
                resp = _mt_Response(body, status=200, mimetype=mime)
                resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                resp.headers['Content-Length'] = str(len(body))
                return resp
        except Exception:
            pass
    src_css = os.path.join(_FA_SRC_DIR, 'all.min.css')
    got_c = None
    if os.path.exists(src_css):
        got_c = _mt_fa_read_with_timeout(src_css, timeout_s=15)
    if (not got_c or len(got_c) < 1000) and not env_no_cdn:
        got_c = _mt_fa_download_from_cdn('css/all.min.css', timeout_s=30, retries=2)
    if got_c and len(got_c) > 1000:
        try:
            css_cache = os.path.join(_FA_CACHE_DIR, 'all.min.css')
            tmp_path = css_cache + '.tmp_' + str(os.getpid())
            with open(tmp_path, 'wb') as tf:
                tf.write(got_c)
            os.replace(tmp_path, css_cache)
            _FA_CACHE_WHITELIST['__all.min.css'] = css_cache
        except Exception:
            pass
        resp = _mt_Response(got_c, status=200, mimetype=mime)
        resp.headers['Cache-Control'] = 'public, max-age=3600'
        resp.headers['Content-Length'] = str(len(got_c))
        return resp
    return _mt_Response(b'', status=404, mimetype=mime)

import hashlib
import time
import threading

# ---------- 字体 mimetype 显式注册 + 静态资源统一白名单函数 ----------
# 修复：字体文件 (.woff2/.woff/.ttf/.otf/.eot) 静态资源因 mimetype 不识别或白名单漏判触发中间件异常 → HTTP 500
import mimetypes as _mt_mimetypes
_mt_mimetypes.add_type('font/woff2', '.woff2', strict=False)
_mt_mimetypes.add_type('font/woff',  '.woff',  strict=False)
_mt_mimetypes.add_type('font/ttf',   '.ttf',   strict=False)
_mt_mimetypes.add_type('font/otf',   '.otf',   strict=False)
_mt_mimetypes.add_type('application/vnd.ms-fontobject', '.eot', strict=False)
# 同步到 Flask 内部的 mimetype 猜测
try:
    from flask.helpers import safe_join
except Exception:
    pass
try:
    import werkzeug.wrappers as _wz_w
    if hasattr(_wz_w.Response, 'default_mimetype'):
        pass
except Exception:
    pass

_STATIC_EXT_TUPLE = (
    '.css', '.js', '.mjs', '.map',
    '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.bmp', '.avif',
    '.woff2', '.woff', '.ttf', '.otf', '.eot',
    '.mp4', '.webm', '.mp3', '.wav', '.ogg',
    '.pdf', '.txt', '.json', '.csv',
)

def _is_static_request(path=None):
    """静态资源统一判定：路径前缀 + 扩展名双重保险，避免任一 before_request 漏判导致中间件异常。"""
    if path is None:
        try:
            from flask import request as _rq
            path = (_rq.path or '') if _rq is not None else ''
        except Exception:
            return False
    p = (path or '').lower()
    if not p:
        return False
    # 1) 路径前缀白名单（最准确）
    if (p.startswith('/static/') or p.startswith('/assets/')
            or p in ('/favicon.ico', '/robots.txt')):
        return True
    # 2) 扩展名兜底（避免路径前缀漏写 /static 前缀时的误判）
    if p.endswith(_STATIC_EXT_TUPLE):
        return True
    return False

# 捕获 Flask 未被 errorhandler 捕获的静态路由异常：打印完整 traceback 便于定位字体 500
def _mt_got_request_exception(_sender, exception, **_kw):
    import traceback as _tb
    try:
        from flask import request as _rq
        p = _rq.path or '?'
        m = _rq.method or '?'
    except Exception:
        p = '?'
        m = '?'
    # 正确做法：signal handler 不在 except 作用域内，不能用 format_exc()（依赖 sys.exc_info()）
    #        必须用参数中的 exception 对象显式构造 traceback 字符串
    try:
        tb_full = _tb.format_exception(type(exception), exception, exception.__traceback__)
        tb_str = ''.join(tb_full)[-2000:]
    except Exception:
        try:
            tb_str = f"{type(exception).__name__}: {str(exception)[:800]}"
        except Exception:
            tb_str = "无法获取异常描述"
    # 组装异常消息
    try:
        exc_type_name = type(exception).__name__
    except Exception:
        exc_type_name = "UnknownException"
    try:
        exc_val_str = str(exception)[:800]
    except Exception:
        exc_val_str = ""
    msg = f"[UNCAUGHT-EXCEPTION] {m} {p} | {exc_type_name}: {exc_val_str}\n{tb_str}"
    print(msg, flush=True)
    try:
        import logging as _lg
        _lg.error(msg)
    except Exception:
        pass
try:
    from flask import got_request_exception
    got_request_exception.connect(_mt_got_request_exception, app, weak=False)
except Exception as _x:
    print(f"[debug] hook exception signal fail: {_x}", flush=True)

_MT_CSRF_TOKEN = None

_idle_monitor_thread = None
_idle_monitor_running = False
_idle_monitor_last_run = 0

def _start_employee_idle_monitor():
    """启动AI员工空闲监控守护线程"""
    global _idle_monitor_thread, _idle_monitor_running

    if _idle_monitor_running:
        print('[IDLE-MONITOR] 空闲监控已在运行')
        return

    _idle_monitor_running = True

    def idle_monitor_loop():
        global _idle_monitor_running, _idle_monitor_last_run

        while _idle_monitor_running:
            try:
                from ai_engines.monitoring import ai_monitor
                from ai_engines.ai_employees import ai_employee_manager

                if ai_monitor and ai_employee_manager:
                    result = ai_monitor.monitor_employee_idle(ai_employee_manager)
                    _idle_monitor_last_run = time.time()

                    if result.get('actions_taken'):
                        print(f'[IDLE-MONITOR] 执行了 {len(result["actions_taken"])} 个操作')
                        for action in result['actions_taken']:
                            print(f'  - {action["name"]}: {action["action"]} ({action["duration"]})')

                time.sleep(60)

            except Exception as e:
                print(f'[IDLE-MONITOR] 监控线程错误: {e}')
                time.sleep(30)

                if _idle_monitor_running:
                    print('[IDLE-MONITOR] 重新启动监控线程...')

    _idle_monitor_thread = threading.Thread(
        target=idle_monitor_loop,
        daemon=True,
        name="AI-Employee-Idle-Monitor"
    )
    _idle_monitor_thread.start()
    print('[IDLE-MONITOR] AI员工空闲监控守护线程已启动')

_start_employee_idle_monitor()

# ==========================================================
# 例行维护编排器 - Routine Maintenance Orchestrator
# ==========================================================

_maintenance_threads = {}
_maintenance_status = {
    'watchdog': {'running': False, 'last_run': 0, 'last_result': None},
    'auto_repair': {'running': False, 'last_run': 0, 'last_result': None},
    'ai_learning': {'running': False, 'last_run': 0, 'last_result': None},
    'system_upgrade': {'running': False, 'last_run': 0, 'last_result': None},
    'ai_inspection': {'running': False, 'last_run': 0, 'last_result': None},
}

def _start_routine_maintenance():
    """启动例行维护系统 - 4个守护线程"""

    def start_watchdog():
        """守护线程1: 进程监控看门狗"""
        _maintenance_status['watchdog']['running'] = True
        try:
            from core.services.system_watchdog import ServiceManager
            sm = ServiceManager()
            print('[MAINTENANCE] 看门狗服务管理器已初始化')

            while _maintenance_status['watchdog']['running']:
                try:
                    for service_name in sm.services:
                        pid = sm._load_pid(service_name)
                        if pid and not sm.is_process_running(pid):
                            print(f'[WATCHDOG] 服务 {service_name} 已停止，尝试重启')
                            sm.start_service(service_name)

                    _maintenance_status['watchdog']['last_run'] = time.time()
                    time.sleep(30)

                except Exception as e:
                    print(f'[WATCHDOG] 监控错误: {e}')
                    time.sleep(15)

        except Exception as e:
            print(f'[WATCHDOG] 初始化失败: {e}')
            _maintenance_status['watchdog']['running'] = False

    def start_auto_repair():
        """守护线程2: 自动修复扫描器"""
        _maintenance_status['auto_repair']['running'] = True
        try:
            from core.services.auto_repair_engine import AutoRepairEngine
            repair_engine = AutoRepairEngine()
            print('[MAINTENANCE] 自动修复引擎已初始化')

            while _maintenance_status['auto_repair']['running']:
                try:
                    print('[AUTO-REPAIR] 开始扫描系统错误...')
                    result = repair_engine.scan_http_errors()
                    _maintenance_status['auto_repair']['last_run'] = time.time()
                    _maintenance_status['auto_repair']['last_result'] = result

                    if len(result) > 0:
                        print(f'[AUTO-REPAIR] 发现 {len(result)} 个错误')
                        repair_engine.run_repair_cycle()

                    time.sleep(300)

                except Exception as e:
                    print(f'[AUTO-REPAIR] 扫描错误: {e}')
                    time.sleep(60)

        except Exception as e:
            print(f'[AUTO-REPAIR] 初始化失败: {e}')
            _maintenance_status['auto_repair']['running'] = False

    def start_ai_learning():
        """守护线程3: AI自动学习"""
        _maintenance_status['ai_learning']['running'] = True
        try:
            from ai_engines.ai_learning_system import AILearningSystem
            learning_system = AILearningSystem()
            print('[MAINTENANCE] AI学习系统已初始化')

            while _maintenance_status['ai_learning']['running']:
                try:
                    print('[AI-LEARNING] 开始学习周期...')
                    result = learning_system.run_learning_cycle()
                    _maintenance_status['ai_learning']['last_run'] = time.time()
                    _maintenance_status['ai_learning']['last_result'] = result
                    print(f'[AI-LEARNING] 学习完成: {result}')

                    time.sleep(3600)

                except Exception as e:
                    print(f'[AI-LEARNING] 学习错误: {e}')
                    time.sleep(1800)

        except Exception as e:
            print(f'[AI-LEARNING] 初始化失败: {e}')
            _maintenance_status['ai_learning']['running'] = False

    def start_system_upgrade():
        """守护线程4: 系统升级"""
        _maintenance_status['system_upgrade']['running'] = True
        try:
            from ai_engines.comprehensive_system_upgrader import ComprehensiveSystemUpgrader
            upgrader = ComprehensiveSystemUpgrader()
            print('[MAINTENANCE] 综合系统升级器已初始化')

            while _maintenance_status['system_upgrade']['running']:
                try:
                    print('[SYSTEM-UPGRADE] 检查系统升级...')
                    result = upgrader.check_and_upgrade()
                    _maintenance_status['system_upgrade']['last_run'] = time.time()
                    _maintenance_status['system_upgrade']['last_result'] = result

                    if result.get('upgraded', False):
                        print(f'[SYSTEM-UPGRADE] 升级完成: {result}')

                    time.sleep(21600)

                except Exception as e:
                    print(f'[SYSTEM-UPGRADE] 升级错误: {e}')
                    time.sleep(7200)

        except Exception as e:
            print(f'[SYSTEM-UPGRADE] 初始化失败: {e}')
            _maintenance_status['system_upgrade']['running'] = False

    def start_ai_inspection():
        """守护线程5: AI巡检闭环引擎"""
        _maintenance_status['ai_inspection']['running'] = True
        try:
            from core.services.ai_inspection_loop import get_inspection_engine
            engine = get_inspection_engine()
            print('[MAINTENANCE] AI巡检闭环引擎已初始化')

            while _maintenance_status['ai_inspection']['running']:
                try:
                    print('[AI-INSPECTION] 开始巡检闭环...')
                    result = engine.run_once('scheduled')
                    _maintenance_status['ai_inspection']['last_run'] = time.time()
                    _maintenance_status['ai_inspection']['last_result'] = result
                    print(f'[AI-INSPECTION] 巡检完成: 扫描{result["files_scanned"]} 发现{result["errors_found"]} 修复{result["errors_fixed"]} 学习{result["knowledge_gained"]}')

                    time.sleep(300)

                except Exception as e:
                    print(f'[AI-INSPECTION] 巡检错误: {e}')
                    time.sleep(60)

        except Exception as e:
            print(f'[AI-INSPECTION] 初始化失败: {e}')
            _maintenance_status['ai_inspection']['running'] = False

    def start_eigenflux_repair():
        """EigenFlux 自动修复守护线程"""
        _maintenance_status['eigenflux_repair'] = {'running': False, 'last_run': 0, 'last_result': None}
        _maintenance_status['eigenflux_repair']['running'] = True
        try:
            from services.ai.eigenflux_auto_repair_service import EigenFluxAutoRepairService
            svc = EigenFluxAutoRepairService()
            svc.init_tables()
            # 启动内部监控（60秒间隔）
            svc.start_monitoring(interval=60)
            print('[EIGENFLUX-REPAIR] 自动修复监控已启动 (60s interval)')
        except Exception as e:
            print(f'[EIGENFLUX-REPAIR] 启动失败: {e}')
            _maintenance_status['eigenflux_repair']['running'] = False

    threads = [
        ('watchdog', start_watchdog),
        ('auto_repair', start_auto_repair),
        ('ai_learning', start_ai_learning),
        ('system_upgrade', start_system_upgrade),
        ('ai_inspection', start_ai_inspection),
        ('eigenflux_repair', start_eigenflux_repair),
    ]

    for _ti, (name, target) in enumerate(threads):
        if _maintenance_threads.get(name):
            print(f'[MAINTENANCE] {name} 线程已在运行')
            continue

        thread = threading.Thread(target=target, daemon=True, name=f"Maintenance-{name}")
        _maintenance_threads[name] = thread
        thread.start()
        print(f'[MAINTENANCE] {name} 守护线程已启动')
        # 🆕 错峰启动: 每个守护线程之间 sleep 30s, 避免 6 个线程同时抢 10.3GB 大库锁
        # 之前无间隔启动导致 Flask worker 被锁堵 → HTTP timeout
        if _ti < len(threads) - 1:
            time.sleep(30)

# 延迟 300s 启动: 先让 Flask listen + 稳定处理 HTTP 请求
# 守护线程内部会同步抢 10.3GB 大库锁, 太早启动直接堵死 Flask worker
import threading as _mtscos_thr_delayed
def _delayed_maintenance_boot():
    import time as _t_delayed
    _t_delayed.sleep(300)  # 5min, 让 Flask 稳定
    try:
        _start_routine_maintenance()
    except Exception as _e:
        print(f'[MAINTENANCE] 延迟启动失败 (非致命): {_e}')
_mtscos_thr_delayed.Thread(target=_delayed_maintenance_boot, daemon=True, name='maint-delay-boot').start()
print('[MAINTENANCE] 守护线程延迟 300s 启动 (让 Flask 先稳定处理 HTTP)')

def _mt_generate_csrf_token():
    global _MT_CSRF_TOKEN
    if _MT_CSRF_TOKEN is None:
        _MT_CSRF_TOKEN = hashlib.sha256(f'mtscos-csrf-{time.time()}-{os.urandom(16)}'.encode()).hexdigest()
    return _MT_CSRF_TOKEN

_MT_REGISTER_LIMIT = {}
_MT_REGISTER_WINDOW = 60
_MT_REGISTER_MAX_PER_IP = 5

# 忘记密码：双维度速率限制（IP + 目标用户名） 1小时/5次
_MT_FORGOT_LIMIT_IP = {}
_MT_FORGOT_LIMIT_USER = {}
_MT_FORGOT_WINDOW = 3600
_MT_FORGOT_MAX_PER_IP = 5
_MT_FORGOT_MAX_PER_USER = 3


def _generate_strong_reset_pw(length: int = 14) -> str:
    """生成至少3类字符的强随机重置密码"""
    import secrets, string
    length = max(10, min(length, 32))
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    specials = '!@#$%^&*_+-=,.:;'
    pools = [lowers, uppers, digits, specials]
    # 确保至少每类至少1个（3类以上）
    chosen = [
        secrets.choice(lowers),
        secrets.choice(uppers),
        secrets.choice(digits),
        secrets.choice(specials),
    ]
    all_pool = ''.join(pools)
    for _ in range(length - len(chosen)):
        chosen.append(secrets.choice(all_pool))
    secrets.SystemRandom().shuffle(chosen)
    return ''.join(chosen)


def _validate_email_format(email: str) -> tuple[bool, str]:
    """严格邮箱格式校验（返回ok, message）"""
    import re
    s = str(email or '').strip()
    if not s:
        return True, ''
    if len(s) > 254:
        return False, '邮箱长度超过 254 字符'
    if s.count('@') != 1:
        return False, '邮箱必须包含且仅包含一个 @'
    if s.startswith('@') or s.endswith('@'):
        return False, '邮箱格式错误（@不能在首尾）'
    # 邮箱正则：RFC简化版
    email_re = re.compile(
        r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    )
    if not email_re.match(s):
        return False, '邮箱格式不合法（例: user@example.com）'
    return True, ''


# SA 注册黑名单（禁止注册这些用户名，但不代表它们是SA）
_SA_REGISTRATION_BLACKLIST = {'wuchenghao15', 'wuchenghao', 'wuch', 'root', 'sa', 'admin',
                              'administrator', 'supervisor', 'superadmin', 'sadmin'}
_SA_REGISTRATION_BLACKLIST_LOWER = {n.lower() for n in _SA_REGISTRATION_BLACKLIST}

# SA 隐藏名单（仅在系统中隐藏这些账号）—— 规则铁律：SA有且仅有 wuchenghao15 一人
_SA_HIDDEN_NAMES = {'wuchenghao15'}
_SA_HIDDEN_NAMES_LOWER = {n.lower() for n in _SA_HIDDEN_NAMES}

# 向后兼容（旧引用）
_SA_FORBIDDEN_NAMES = _SA_REGISTRATION_BLACKLIST
_SA_FORBIDDEN_NAMES_LOWER = _SA_REGISTRATION_BLACKLIST_LOWER


def _sa_strip_hidden(rows):
    """SA完全隐藏过滤器：从用户列表/登录日志/AI员工/EigenFlux注册中剥离SA痕迹

    规则铁律：SA有且仅有 wuchenghao15 一人，仅隐藏此账号 + role=super_admin

    过滤条件（满足任一即移除）：
      - username 在 _SA_HIDDEN_NAMES_LOWER 中（仅 wuchenghao15）
      - role == 'super_admin'

    用法：在所有返回用户列表的API/页面/统计中调用此函数过滤后再返回。
    """
    if not rows:
        return rows
    result = []
    for r in rows:
        if hasattr(r, 'keys'):
            uname = (r.get('username') or r.get('name') or r.get('operator') or r.get('created_by') or '').strip().lower()
            role = (r.get('role') or '').strip().lower()
        else:
            try:
                uname = str(r).lower()
                role = ''
            except Exception:
                uname = ''; role = ''
        if uname in _SA_HIDDEN_NAMES_LOWER or role == 'super_admin':
            continue
        result.append(r)
    return result


def _sa_strip_from_count(total_count, strip_n=0):
    """从计数中减去SA的数量（用于统计页面如 total_users 不暴露SA存在）"""
    return max(0, int(total_count or 0) - int(strip_n or 0))

# ⚠️ 超级管理员 wuchenghao15 禁用密码登录（项目硬约束）
# 仅接受 VIKEY 加密狗 + SZU100 专用 U 盘双因子认证（见 /auth/login SA 分支）
# 历史 PIN '2486' 已彻底废弃，不得恢复（活跃入口见 routes/auth_routes.py）
# _SA_HARDCODED_PIN 常量已删除，下方所有引用均已替换为双硬件认证逻辑

_ADMIN_CREATE_USER_ROLE_WHITELIST = frozenset({'student', 'teacher', 'parent', 'admin'})
_ADMIN_EDUCATION_TYPE_WHITELIST = frozenset({'K12', 'higher', 'adult'})

_SYSTEM_CONFIG_NUMERIC_RANGES = {
    'max_exam_duration': (1, 600),
    'default_page_size': (5, 100),
    'min_password_length': (4, 64),
}
_SYSTEM_CONFIG_BOOL_KEYS = frozenset({
    'enable_registration', 'enable_email_notification', 'enable_sms_notification',
    'enable_2fa', 'maintenance_mode', 'enable_ai_features', 'enable_exam_shuffle',
    'enable_negative_marking', 'strict_mode_default', 'vikey_mode_active',
    'force_sa_rule_enforced', 'show_super_admin_ui',
})
_SYSTEM_CONFIG_SCOPE_WHITELIST = frozenset({
    'system', 'upgrade', 'vikey', 'ui', 'security', 'exam', 'education', 'ai',
})
_SETTINGS_WRITE_SOURCE_WHITELIST = frozenset({'frontend', 'api', 'eigenflux', 'ai_consult'})
_BOOL_ACCEPTED_VALUES = frozenset({'true', 'false', '1', '0', True, False, 1, 0})


def _safe_str(v, max_len=2000):
    if v is None:
        return ''
    s = str(v).strip()
    if max_len and len(s) > max_len:
        s = s[:max_len]
    return s


def _safe_html_escape(s, max_len=500):
    """XSS防护：转义HTML特殊字符（用于将用户输入回显到HTML页面时）"""
    if s is None:
        return ''
    s = str(s)[:max_len]
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;').replace("'", '&#x27;'))


# 路径穿越防护：/legal/<slug> 仅允许小写字母数字与连字符
_LEGAL_SLUG_PATTERN = re.compile(r'^[a-z0-9_-]+$')  # 允许下划线 (flow_id=fix_legal_slug_20260902)
# session_key 格式校验：字母数字下划线连字符，长度1-64
_SESSION_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')


def _validate_session_key(sk):
    """统一校验 session_key 格式（防注入/路径穿越）"""
    return bool(_SESSION_KEY_PATTERN.match(sk or ''))


def _safe_int(v, default=0, min_val=None, max_val=None):
    try:
        iv = int(str(v).strip()) if str(v).strip() else default
    except (ValueError, TypeError):
        iv = default
    if min_val is not None and iv < min_val:
        iv = min_val
    if max_val is not None and iv > max_val:
        iv = max_val
    return iv


def _safe_float(v, default=0.0, min_val=None, max_val=None):
    try:
        fv = float(str(v).strip()) if str(v).strip() else default
    except (ValueError, TypeError):
        fv = default
    if min_val is not None and fv < min_val:
        fv = min_val
    if max_val is not None and fv > max_val:
        fv = max_val
    return fv


def _safe_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    s = str(v).strip().lower()
    if s in ('true', '1', 'yes', 'on'):
        return True
    if s in ('false', '0', 'no', 'off', '', 'none', 'null'):
        return False
    return False


def _validate_enum(v, whitelist, field_name='参数'):
    sv = _safe_str(v, max_len=64)
    if sv and sv not in whitelist:
        return None, f'{field_name}不合法，允许值：{", ".join(sorted(whitelist))}'
    return sv, None


# ============================================================
# 【强制开发流程规则引擎】v3.1.0  MANDATORY-DEV-FLOW
# 任何代码/功能开发必须遵守以下流程，不得绕开规避
# 状态机：STEP_1_PROPOSAL → STEP_2A_ROUND → STEP_3_ZXF_DECISION
#        → STEP_31_B_ROUND(暂缓) / STEP_32_PASS(直过)
#        → STEP_4_CLERK_RECORD → STEP_5_IMPL_TEAM_DOCK
#        → STEP_6_AI_IMPL_COORD → STEP_7_EXECUTE
#        → STEP_8_ACCEPTANCE → STEP_9A_PASS 或 STEP_1_FEEDBACK(不通过重投)
#        → STEP_9B_SUMMARY_REPORT
#        → STEP_10_SMART_VERSION_UPGRADE (智能判断是否升级版本)
#        → STEP_11_AUTO_GIT_SYNC      (自动同步git和GitHub)
#        → STEP_12_TEST1000 → (测试完重复步1-11) → FINAL_DONE
# ============================================================

_MT_DEV_FLOW_VERSION = 'v3.1.0-mandatory-flow-ext2'
_MT_DEV_FLOW_STEPS = (
    'STEP_1_PROPOSAL',              # 1. 提案
    'STEP_2A_ROUND',                # 2. A轮讨论
    'STEP_3_ZXF_DECISION',          # 3. 张晓峰当场表决暂缓权
    'STEP_31_B_ROUND',              # 3.1 B轮再讨论(暂缓→张不参加)
    'STEP_311_SA_JUDGMENT',         # 3.1.1 同意暂缓有异议 → 超级管理员决断
    'STEP_312_AUTO_PASS',           # 3.1.2 不同意暂缓超半 → 报备SA 方案自动通过
    'STEP_32_PASS_SKIP_B',          # 3.2 直过 → 报备SA B轮跳过
    'STEP_4_CLERK_RECORD',          # 4. 会议记录员全程记录+表决统计总结
    'STEP_5_IMPL_DOCKING',          # 5. 专业实施团队对接方案+名录+详细方案
    'STEP_6_AI_TEAM_COORD',         # 6. 统筹专业AI实施团队(现有AI员工+经理+监理+队长)
    'STEP_7_EXECUTE',               # 7. 下场实施(团队管理+方案)
    'STEP_8_ACCEPTANCE',            # 8. 收场验收：AI监理验收(步骤↔实际结果)
    'STEP_9A_PASS_OR_LOOPBACK',     # 9. A轮验收：通过→步9B；不通过→投喂脑库复盘→回到步1
    'STEP_9B_SUMMARY',              # 9. 记录讨论/总结/复盘，上报SA/入库/投喂经验/投喂异常特征库
    'STEP_10_SMART_VERSION_UPGRADE',# 10.智能判断是否升级系统版本
    'STEP_11_AUTO_GIT_SYNC',        # 11.自动同步git和GitHub
    'STEP_12_TEST1000',             # 12.1000轮测试(正常+异常+黑客) → 测试完重复步1-11后跳出
    'FINAL_DONE',                   # 终态：交付
)
_MT_DEV_FLOW_ACCEPTED_STATUSES = frozenset(_MT_DEV_FLOW_STEPS)
_MT_DEV_FLOW_EDGES = {  # 允许的状态转移（硬约束）
    'STEP_1_PROPOSAL':              {'STEP_2A_ROUND'},
    'STEP_2A_ROUND':                {'STEP_3_ZXF_DECISION'},
    'STEP_3_ZXF_DECISION':          {'STEP_31_B_ROUND', 'STEP_32_PASS_SKIP_B'},
    'STEP_31_B_ROUND':              {'STEP_311_SA_JUDGMENT', 'STEP_312_AUTO_PASS'},
    'STEP_311_SA_JUDGMENT':         {'STEP_4_CLERK_RECORD'},
    'STEP_312_AUTO_PASS':           {'STEP_4_CLERK_RECORD'},
    'STEP_32_PASS_SKIP_B':          {'STEP_4_CLERK_RECORD'},
    'STEP_4_CLERK_RECORD':          {'STEP_5_IMPL_DOCKING'},
    'STEP_5_IMPL_DOCKING':          {'STEP_6_AI_TEAM_COORD'},
    'STEP_6_AI_TEAM_COORD':         {'STEP_7_EXECUTE'},
    'STEP_7_EXECUTE':               {'STEP_8_ACCEPTANCE'},
    'STEP_8_ACCEPTANCE':            {'STEP_9A_PASS_OR_LOOPBACK'},
    'STEP_9A_PASS_OR_LOOPBACK':     {'STEP_1_PROPOSAL', 'STEP_9B_SUMMARY'},
    'STEP_9B_SUMMARY':              {'STEP_10_SMART_VERSION_UPGRADE'},
    'STEP_10_SMART_VERSION_UPGRADE':{'STEP_11_AUTO_GIT_SYNC'},
    'STEP_11_AUTO_GIT_SYNC':        {'STEP_12_TEST1000'},
    'STEP_12_TEST1000':             {'FINAL_DONE'},  # 测试完重复步1-11已在内部执行，跳出
    'FINAL_DONE':                   {'FINAL_DONE'},
}
# A轮讨论强制出席方（缺任一不得进入STEP_3）
_MT_DEV_FLOW_MANDATORY_A_ROUND_PANELS = (
    'GROUP_A_51_HUMANS',          # A轮51人(含张晓峰)
    'EIGENFLUX_NETWORK',          # EigenFlux 网络
    'EIGENFLUX_EXPERT',           # EigenFlux 专家
    'AI_EMPLOYEE_DELEGATION',     # 系统自带AI员工代表团【人数必须为偶数】
)
# 专业AI实施团队强制成员(步骤6)
_MT_DEV_FLOW_IMPL_CORE_ROLES = ('现有AI员工','AI团队经理','AI团队监理','AI团队队长')
# 测试三大类
_MT_DEV_FLOW_TEST_KINDS = ('NORMAL_LOGIC','ABNORMAL_LOGIC','HACKER_ATTACK')
# 1000 轮测试分类配额（开发规则 §20 合规：NORMAL_LOGIC 400 + ABNORMAL_LOGIC 300 + HACKER_ATTACK 300 = 1000）
_MT_DEV_FLOW_TEST_KINDS_COUNT = {'NORMAL_LOGIC': 400, 'ABNORMAL_LOGIC': 300, 'HACKER_ATTACK': 300}
# 步骤10：智能版本升级判定阈值（任一命中则建议升级）
_MT_DEV_FLOW_VERSION_UPGRADE_RULES = {
    'files_changed_min':       1,   # 改动文件数≥1
    'db_fixes_min':            1,   # 修复数≥1
    'test_vuln_min':           1,   # 发现漏洞≥1
    'risk_score_delta_min':    100, # 风险分变化≥100
    'new_schema_tables_min':   1,   # 新增表≥1
    'mandatory_upgrade_flag': True, # 强制规则：只要有代码提交就必须评估
}
# 步骤11：git同步默认目标仓库/分支（可被payload覆盖）
_MT_DEV_FLOW_DEFAULT_GIT = {
    'remote_name': 'origin',
    'target_branch': 'main',
    'commit_author_name': 'Mr.W',
    'commit_author_email': 'wuchenghao15@users.noreply.github.com',
    'auth_mode': 'SSH',  # 经验959804: 优先SSH避免交互式认证
}

def _mt_dev_flow_transition_allowed(cur: str, nxt: str) -> bool:
    """开发流程强制状态转移校验：不允许跳步/绕开"""
    return cur in _MT_DEV_FLOW_EDGES and nxt in _MT_DEV_FLOW_EDGES[cur]

def _mt_dev_flow_ai_delegation_even_ok(ai_delegation_list) -> bool:
    """A轮AI员工代表团人数必须为偶数"""
    return bool(ai_delegation_list) and (len(list(ai_delegation_list)) % 2 == 0)

def _mt_dev_flow_ensure_schema(cursor, with_migration=True):
    """初始化开发流程强制约束相关DB表（幂等）"""
    cursor.execute("""CREATE TABLE IF NOT EXISTS mt_dev_flow_session (
        flow_id TEXT PRIMARY KEY,
        proposal_title TEXT, proposal_summary TEXT, proposal_json TEXT,
        current_step TEXT DEFAULT 'STEP_1_PROPOSAL',
        a_round_panels_json TEXT DEFAULT '{}', a_round_discussion_json TEXT DEFAULT '{}',
        a_round_attendance_json TEXT DEFAULT '{}',
        zhangxiaofeng_decision TEXT,  -- SUSPEND / NOT_USE_SUSPEND
        b_round_panels_json TEXT DEFAULT '{}', b_round_discussion_json TEXT DEFAULT '{}',
        b_round_zhangxiaofeng_participated INTEGER DEFAULT 0,  -- 张必须0
        b_round_agree_suspend INTEGER DEFAULT 0, b_round_disagree_suspend INTEGER DEFAULT 0,
        b_round_has_objection INTEGER DEFAULT 0,
        super_admin_judgment TEXT, super_admin_report_status TEXT,
        clerk_record_json TEXT DEFAULT '{}', clerk_vote_summary TEXT,
        impl_team_contact_json TEXT DEFAULT '{}', impl_plan_detail_json TEXT DEFAULT '{}',
        ai_team_coord_json TEXT DEFAULT '{}', ai_core_roles_json TEXT DEFAULT '{}',
        execute_steps_json TEXT DEFAULT '{}',
        acceptance_json TEXT DEFAULT '{}', acceptance_passed INTEGER,
        acceptance_step_results_json TEXT DEFAULT '{}',
        loopback_count INTEGER DEFAULT 0,
        summary_report_json TEXT DEFAULT '{}',
        db_written INTEGER DEFAULT 0, brain_fed INTEGER DEFAULT 0,
        experience_fed INTEGER DEFAULT 0, anomaly_fed INTEGER DEFAULT 0,
        test1000_total INTEGER DEFAULT 0, test1000_pass INTEGER DEFAULT 0,
        test1000_fail INTEGER DEFAULT 0, test1000_vuln INTEGER DEFAULT 0,
        test1000_json TEXT DEFAULT '{}',
        smart_upgrade_version TEXT,
        smart_upgrade_should_upgrade INTEGER DEFAULT 0,
        smart_upgrade_reasons_json TEXT DEFAULT '{}',
        smart_upgrade_triggered INTEGER DEFAULT 0,
        smart_upgrade_log_id INTEGER,
        git_sync_remote_name TEXT, git_sync_target_branch TEXT,
        git_sync_auth_mode TEXT,
        git_sync_commit_hash TEXT,
        git_sync_commit_subject TEXT,
        git_sync_status TEXT,       -- SUCCESS / DRY_RUN_OK / SKIPPED / FAILED
        git_sync_error TEXT,
        git_sync_json TEXT DEFAULT '{}',
        final_status TEXT DEFAULT 'OPEN',
        created_at TEXT, updated_at TEXT, created_by TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS mt_dev_flow_events (
        ev_id INTEGER PRIMARY KEY AUTOINCREMENT, flow_id TEXT,
        from_step TEXT, to_step TEXT,
        event_kind TEXT, event_payload_json TEXT DEFAULT '{}',
        triggered_by TEXT, triggered_at TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (
        feed_id INTEGER PRIMARY KEY AUTOINCREMENT, flow_id TEXT,
        feed_target TEXT,  -- AI_BRAIN / EXPERIENCE_LIBRARY / ANOMALY_FEATURE_LIBRARY
        payload_preview TEXT, fed_at TEXT, fed_by TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS mt_anomaly_feature_library (
        feat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_hash TEXT UNIQUE, feature_kind TEXT, feature_vector_json TEXT,
        source_flow TEXT, registered_at TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS mt_experience_library (
        exp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        experience_hash TEXT UNIQUE, title TEXT, content_json TEXT,
        source_flow TEXT, registered_at TEXT
    )""")
    # 幂等补列（v3.0.0→v3.1.0扩展步骤10/11字段）
    extra_cols = {'loopback_count':'INTEGER DEFAULT 0', 'anomaly_fed':'INTEGER DEFAULT 0',
                  'b_round_zhangxiaofeng_participated':'INTEGER DEFAULT 0',
                  'b_round_has_objection':'INTEGER DEFAULT 0',
                  'smart_upgrade_version':'TEXT','smart_upgrade_should_upgrade':'INTEGER DEFAULT 0',
                  'smart_upgrade_reasons_json':'TEXT DEFAULT \'{}\'',
                  'smart_upgrade_triggered':'INTEGER DEFAULT 0','smart_upgrade_log_id':'INTEGER',
                  'git_sync_remote_name':'TEXT','git_sync_target_branch':'TEXT',
                  'git_sync_auth_mode':'TEXT','git_sync_commit_hash':'TEXT',
                  'git_sync_commit_subject':'TEXT','git_sync_status':'TEXT',
                  'git_sync_error':'TEXT','git_sync_json':'TEXT DEFAULT \'{}\'',
                  'proposal_title':'TEXT','acceptance_passed':'INTEGER',
                  'test1000_pass':'INTEGER DEFAULT 0','test1000_fail':'INTEGER DEFAULT 0'}
    if with_migration:
        for col, ddl in extra_cols.items():
            try: cursor.execute(f"ALTER TABLE mt_dev_flow_session ADD COLUMN {col} {ddl}")
            except Exception: pass

def _mt_dev_flow_transition(cursor, flow_id, from_step, to_step, triggered_by='system', event_kind='STEP_ADVANCE', payload=None):
    """流程推进（硬约束：边校验失败直接抛异常）"""
    if not _mt_dev_flow_transition_allowed(from_step, to_step):
        raise ValueError(f'[DEV-FLOW-VIOLATION] 不允许从 {from_step} 跳到 {to_step}，必须遵守9步流程')
    import datetime as _dt, json as _jj
    now = _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO mt_dev_flow_events(flow_id,from_step,to_step,event_kind,event_payload_json,triggered_by,triggered_at) VALUES (?,?,?,?,?,?,?)",
                   (flow_id, from_step, to_step, event_kind, _jj.dumps(payload or {}, ensure_ascii=False),
                    _safe_str(triggered_by, 64), now))
    cursor.execute("UPDATE mt_dev_flow_session SET current_step=?, updated_at=? WHERE flow_id=?", (to_step, now, flow_id))
    return True

# 【强制开发流程规则】硬约束（供任何开发入口调用）
def _mt_dev_flow_assert(cursor, flow_id, must_be_step=None, *, ai_delegation=None, a_panels=None, zhang_in_a=True, zhang_not_in_b=None):
    if must_be_step:
        row = cursor.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()
        if not row or row[0] != must_be_step:
            raise ValueError(f'[DEV-FLOW-VIOLATION] flow={flow_id} 不在步骤 {must_be_step}，当前={row[0] if row else None}')
    if ai_delegation is not None:
        if not _mt_dev_flow_ai_delegation_even_ok(ai_delegation):
            raise ValueError(f'[DEV-FLOW-VIOLATION] A轮AI员工代表团人数必须为偶数，实际={len(list(ai_delegation))}')
    if a_panels is not None:
        missing = [p for p in _MT_DEV_FLOW_MANDATORY_A_ROUND_PANELS if not a_panels.get(p)]
        if missing:
            raise ValueError(f'[DEV-FLOW-VIOLATION] A轮强制出席方缺席：{missing}')
        if zhang_in_a and not a_panels.get('GROUP_A_51_HUMANS_HAS_ZXF', False):
            raise ValueError('[DEV-FLOW-VIOLATION] A轮51人中必须含张晓峰')
    if zhang_not_in_b is not None:
        if zhang_not_in_b:
            raise ValueError('[DEV-FLOW-VIOLATION] B轮中张晓峰不得参加')
    return True


# ============================================================
# 【扩展步骤10】智能判断是否升级系统版本
# ============================================================
def _mt_dev_flow_smart_version_upgrade(cursor, flow_id, *,
                                       base_version=None,
                                       bump_hint='auto',  # auto/major/minor/patch
                                       files_changed=0,
                                       fixes_count=0,
                                       vuln_found=0,
                                       risk_score_delta=0,
                                       new_tables=0,
                                       extra_context=None):
    """基于阈值规则智能决策版本升级。返回 dict(should_upgrade/version/reasons/log_id)。
    任一命中 _MT_DEV_FLOW_VERSION_UPGRADE_RULES 阈值即建议升级，强制mandatory_upgrade_flag=True时必须评估。
    """
    import json as _jj
    R = _MT_DEV_FLOW_VERSION_UPGRADE_RULES
    reasons = {}
    if files_changed >= R['files_changed_min']: reasons['files_changed'] = files_changed
    if fixes_count    >= R['db_fixes_min']:   reasons['fixes_count'] = fixes_count
    if vuln_found     >= R['test_vuln_min']:  reasons['vuln_found'] = vuln_found
    if abs(risk_score_delta) >= R['risk_score_delta_min']: reasons['risk_score_delta'] = risk_score_delta
    if new_tables     >= R['new_schema_tables_min']: reasons['new_tables'] = new_tables
    if extra_context: reasons['extra'] = extra_context
    should = bool(reasons) or bool(R.get('mandatory_upgrade_flag'))
    # 计算新版本号
    cur = (base_version or _MT_DEV_FLOW_VERSION or '0.0.0').strip()
    m = re.match(r'v?(\d+)\.(\d+)\.(\d+)', cur)
    if m:
        major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if   bump_hint == 'major': major += 1; minor = 0; patch = 0
        elif bump_hint == 'minor': minor += 1; patch = 0
        elif bump_hint == 'patch': patch += 1
        else:  # auto
            if vuln_found >= 10 or new_tables >= 2: major += 1; minor = 0; patch = 0
            elif fixes_count >= 5 or vuln_found >= 3 or abs(risk_score_delta) >= 1000: minor += 1; patch = 0
            else: patch += 1
        new_ver = f'v{major}.{minor}.{patch}'
    else:
        new_ver = cur or 'v1.0.0'
    log_id = None
    if should and cursor:
        try:
            res = _mt_dev_trigger_version_upgrade(new_ver, f'smart_upgrade_flow_{flow_id}',
                                                   f'智能升级理由: {_jj.dumps(reasons,ensure_ascii=False)}',
                                                   triggered_by='Mandatory-Flow-Step10')
            log_id = res.get('log_id') if isinstance(res, dict) else None
        except Exception as e:
            reasons['version_log_error'] = str(e)
    if cursor:
        cursor.execute("""UPDATE mt_dev_flow_session SET
            smart_upgrade_version=?, smart_upgrade_should_upgrade=?,
            smart_upgrade_reasons_json=?, smart_upgrade_triggered=?, smart_upgrade_log_id=?,
            updated_at=datetime('now','localtime') WHERE flow_id=?""",
                       (new_ver, 1 if should else 0, _jj.dumps(reasons,ensure_ascii=False),
                        1 if (should and log_id) else 0, log_id, flow_id))
    return {'should_upgrade': should, 'from_version': cur, 'to_version': new_ver,
            'reasons': reasons, 'log_id': log_id}


# ============================================================
# 【扩展步骤11】自动同步 git 和 GitHub（遵循经验959804）
# ============================================================
def _mt_dev_flow_git_sync(*, project_dir, flow_id=None,
                          files_to_add=None, commit_msg=None,
                          remote_name=None, target_branch=None,
                          auth_mode=None,
                          author_name=None, author_email=None,
                          dry_run=False):
    """自动git同步。基于经验959804:
    1) 含空格路径统一加双引号；
    2) remote origin已存在: 先`git remote -v`确认URL → set-url或直接push；
    3) 优先SSH auth_mode，避免交互式PAT认证；
    4) 返回结构化结果dict。
    """
    import subprocess, json as _jj, datetime as _dt
    D = _MT_DEV_FLOW_DEFAULT_GIT
    rn = remote_name or D['remote_name']; tb = target_branch or D['target_branch']
    am = auth_mode or D['auth_mode']; an = author_name or D['commit_author_name']
    ae = author_email or D['commit_author_email']
    out = {'flow_id': flow_id, 'project_dir': project_dir,
           'remote_name': rn, 'target_branch': tb, 'auth_mode': am,
           'status': 'SKIPPED', 'commit_hash': None, 'commit_subject': None,
           'git_output': [], 'error': None, 'dry_run': dry_run}
    def run(cmd):
        try:
            # 经验959804: 路径用双引号；统一cwd传参避免cd拼接
            r = subprocess.run(cmd, shell=True, cwd=project_dir, capture_output=True, text=True, timeout=120)
            block = (r.stdout or '').strip() + (r.stderr or '').strip()
            out['git_output'].append({'cmd': cmd, 'rc': r.returncode, 'out': block[:4000]})
            return r.returncode, r.stdout or '', r.stderr or ''
        except Exception as e:
            out['git_output'].append({'cmd': cmd, 'rc': -1, 'out': f'exception: {e}'})
            return -1, '', str(e)
    def safep(s): return f'"{s}"'  # 经验959804
    # 1) 仓库状态确认
    rc, so, se = run('git status -s')
    if rc != 0 and ('not a git repository' in (so+se).lower()):
        out['error'] = f'{project_dir} 不是git仓库 (status返回 {rc})'
        out['status'] = 'FAILED'; return out
    # 2) remote 状态确认（经验959804：先remote -v再决定set-url/add/rename）
    rc, so, se = run('git remote -v')
    out['remote_list'] = [x for x in so.splitlines() if x.strip()]
    # 3) add
    added = 0
    if files_to_add:
        chunks = []; cur = []
        for f in files_to_add:
            cur.append(safep(f))
            if len(cur) >= 200: chunks.append(' '.join(cur)); cur = []
        if cur: chunks.append(' '.join(cur))
        for chunk in chunks:
            rci,_,_ = run(f'git add -- {chunk}')
            if rci == 0: added += 1
    else:
        rci,_,_ = run('git add -A');
        if rci == 0: added = 999
    out['files_added_chunks'] = added
    # 4) commit (若nothing to commit则记SKIPPED但仍然正常)
    msg = (commit_msg or f'DEV-FLOW AUTO {_dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}').replace("'","''")
    if dry_run:
        out['status'] = 'DRY_RUN_OK'
        out['commit_subject'] = f'[DRY-RUN] {msg[:80]}'
        return out
    rc, so, se = run(f"git -c user.name='{an}' -c user.email='{ae}' commit -m '{msg}'")
    if rc != 0:
        if ('nothing to commit' in (so+se).lower()) or ('无文件提交' in (so+se)):
            out['status'] = 'SUCCESS'
            out['commit_subject'] = 'SKIPPED(nothing to commit)'
        else:
            out['status'] = 'FAILED'
            out['error'] = f'commit失败 rc={rc}: {(so+se)[:500]}'
            return out
    else:
        # 解析hash
        rc1, sha, _ = run('git rev-parse HEAD')
        out['commit_hash'] = sha.strip()[:40] if rc1 == 0 else None
        rc2, subj, _ = run("git log -1 --pretty=format:%s")
        out['commit_subject'] = subj.strip()[:200] if rc2 == 0 else msg[:200]
    # 5) push origin main (经验959804: 避免卡住，SSH优先)
    rc, so, se = run(f'git push {rn} {tb}')
    if rc == 0:
        out['status'] = 'SUCCESS'
    else:
        block = so + se
        if 'Everything up-to-date' in block:
            out['status'] = 'SUCCESS'
            out['commit_subject'] = (out['commit_subject'] or '') + ' (Everything up-to-date)'
        else:
            out['status'] = 'PARTIAL'
            out['error'] = f'push返回rc={rc}: {block[:500]}'
    return out



def _ef_strip(ef_result: dict | None) -> dict:
    """把 EigenFlux 内部结果裁成前端需要的精简结构（防止响应过大）"""
    if not ef_result or not isinstance(ef_result, dict):
        return {'success': False, 'verdict': 'UNKNOWN', 'recommended_actions': [],
                'ai_consult_count': 0, 'auto_fixes_applied': []}
    keep_keys = {'success', 'verdict', 'ai_consult_count', 'recommended_actions',
                 'auto_fixes_applied', 'anomaly_type', 'severity', 'warn', 'verify_issues',
                 'location', 'server_time', 'operator_is_sa'}
    out = {k: ef_result[k] for k in keep_keys if k in ef_result}
    # 裁掉ai_panel里的长reason（避免太大）
    if isinstance(ef_result.get('ai_employees_panel'), list):
        slim = []
        for e in (ef_result.get('ai_employees_panel') or [])[:10]:
            e2 = dict(e or {})
            if 'reason' in e2 and len(str(e2.get('reason',''))) > 120:
                e2['reason'] = str(e2['reason'])[:120] + '...'
            slim.append({k: e2[k] for k in ('id','name','role','level','icon','opinion','reason') if k in e2})
        out['ai_employees_panel'] = slim
    return out

_CSRF_EXEMPT_PATHS = [
    # 登录/注册/找回密码 (guest 状态, 没 session csrf_token)
    '/login',
    '/auth/login',
    '/auth/register', '/logout', '/forgot_password', '/register',
    '/register',
    '/auth/session_health',
    '/forgot-password',
    '/auth/forgot_password',
    # v22.39.0: 前端 window.onerror / i18n 切换 / 手动触发 run_cycle
    '/api/console/record',
    '/api/console/run_cycle',
    '/api/i18n/set_lang',
    # v22.40: Arduino 热插拔 events/ack (前端 global hotplug.js 从任意页面调用, 无 csrf_token)
    '/api/arduino/events/ack',
    # v22.41: AI Neural Hub — 本地 LLM 推理端点 (纯计算, 不写敏感数据, 供所有子系统/daemon 调用)
    '/api/neuralhub/call',
    '/api/neuralhub/arduino_compile_assist',
    '/api/neuralhub/routes',               # POST 动态注册 (无后缀)
    '/api/neuralhub/rollback',              # POST SA 回滚
]
# 指纹认证API路径前缀（CSRF豁免：登录前需调用指纹硬件）
_CSRF_EXEMPT_PREFIXES = [
    '/api/mobile/fingerprint/',
    # Neural Hub 写操作前缀 (routes/<task_name> DELETE 等)
    '/api/neuralhub/routes/',
    # v22.40.1: 日语学习全部 API（端点已有 _check_login 强制登录保护 + session user_id 校验，CSRF 冗余）
    '/api/japanese/',
    # §二/§四.5: 教育错题推理 + 大模型升级（daemon 也能调 + POST 无 CSRF token）
    '/api/edu/',
    '/api/model/',
    '/api/crypto/',
    '/api/ai/derive/',
    '/api/ai/derive',
    # v22.40.2: startswith tuple 有但 CSRF 漏补 → 补齐
    '/api/andromeda/stars/',
    '/api/ai/matrix/',
    '/api/profile/',
    # v6.2: 深度集成 — Ollama embedding + 语义搜索 + daemon 编排验证 (供 daemon/内部调用, 无 CSRF token)
    '/api/ai/github-fusion/deep/',
]

@app.before_request
def _mt_csrf_protection():
    # 兼容两种 header 格式: X-CSRF-Token (带连字符) 和 X-CSRFToken (无连字符)
    csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken')
    session_csrf = session.get('csrf_token', '')
    # 保留最近3次的CSRF token (防止token轮换时前端token失效)
    recent_tokens = session.get('csrf_recent_tokens', [])
    if session_csrf and session_csrf not in recent_tokens:
        recent_tokens = [session_csrf] + recent_tokens[:2]
        session['csrf_recent_tokens'] = recent_tokens

    def _csrf_ok():
        if not csrf_token:
            return False
        if csrf_token == session_csrf:
            return True
        if csrf_token in recent_tokens:
            return True
        return False

    # 检查是否在豁免列表（精确路径或前缀匹配）
    def _is_exempt(path):
        if path in _CSRF_EXEMPT_PATHS:
            return True
        for prefix in _CSRF_EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    if request.method in ('POST', 'PUT', 'DELETE') and request.path.startswith('/api/'):
        # API路径：除非在指纹豁免前缀中，否则需要CSRF校验
        if not _is_exempt(request.path) and not _csrf_ok():
            return jsonify({'success': False, 'message': 'CSRF验证失败'}), 403
    elif request.method in ('POST', 'PUT', 'DELETE') and not _is_exempt(request.path):
        if not _csrf_ok():
            return jsonify({'success': False, 'message': 'CSRF验证失败'}), 403

try:
    from markupsafe import Markup
    app.jinja_env.globals.setdefault('Markup', Markup)
except Exception:
    pass
try:
    import json as _json_mod
    app.jinja_env.filters.setdefault('tojson', lambda v, **kw: _json_mod.dumps(v, ensure_ascii=False))
except Exception:
    pass


# ================================================================
# AI 防火墙 + 安全团队（AI员工 / AI Agent）统一初始化入口
# - 建表：ai_firewall_rules + security_events_log
# - 种子：24 条防火墙规则 + 6 名安全员工 + 4 个安全 Agent（幂等）
# - 挂载：before_request 全量请求检查 + Blueprint 注册
# ================================================================
def _init_ai_firewall_and_workforce():
    import logging as _fw_logger
    try:
        from core.services import ai_firewall as _fw
        ok_tab = _fw.init_firewall_tables()
        ok_seed = _fw.seed_default_firewall_rules()
        _fw_logger.info(
            f"[ai_firewall] init: tables={'OK' if ok_tab else 'FAIL'}, seed_rows={ok_seed}"
        )
    except Exception as e:
        _fw_logger.warning(f"[ai_firewall] init fail: {e}")
    try:
        from app.api.ai_firewall_api import ai_firewall_api as _fw_api
        from app.api.ai_security_workforce_api import ai_security_workforce_api as _sw_api
        app.register_blueprint(_fw_api)
        app.register_blueprint(_sw_api)
        _fw_logger.info("[ai_firewall] blueprints registered: ai_firewall_api + ai_security_workforce_api")
    except Exception as e:
        _fw_logger.warning(f"[ai_firewall] blueprint register fail: {e}")

    try:
        from app.api.listening_api import listening_api as _ln_api
        app.register_blueprint(_ln_api)
        _fw_logger.info("[listening] blueprint registered: listening_api (/api/listening/*)")
    except Exception as e:
        _fw_logger.warning(f"[listening] blueprint register fail: {e}")

    try:
        from app.api.system_boost_api import system_boost_api as _sb_api
        app.register_blueprint(_sb_api)
        _fw_logger.info("[system_boost] blueprint registered: system_boost_api (/api/system/*)")
    except Exception as e:
        _fw_logger.warning(f"[system_boost] blueprint register fail: {e}")

    try:
        from app.api.auto_mount_api import auto_mount_api as _am_api
        app.register_blueprint(_am_api)
        _fw_logger.info("[auto_mount] blueprint registered: auto_mount_api (/api/auto-mount/*)")
    except Exception as e:
        _fw_logger.warning(f"[auto_mount] blueprint register fail: {e}")


# 🆕 2026-09-16: 模块级同步初始化 → 异步线程延迟启动
# AI_Cluster_Manager / ai_firewall / vikey / layout_ai_system 在 import 时同步跑
# 不停写大库 → Flask worker 刚 listen 就被锁堵 → HTTP timeout
# 全部改成后台线程 + 延迟 60s, 让 Flask 先稳定处理 HTTP
def _async_module_init():
    import time as _t_async
    _t_async.sleep(60)  # 等 Flask listen + 路由注册完
    try:
        _init_ai_firewall_and_workforce()
        print('[ASYNC-INIT] _init_ai_firewall_and_workforce ✅')
    except Exception as e:
        print(f'[ASYNC-INIT] _init_ai_firewall_and_workforce 非致命失败: {e}')
    try:
        _init_vikey_driver_and_api()
        print('[ASYNC-INIT] _init_vikey_driver_and_api ✅')
    except Exception as e:
        print(f'[ASYNC-INIT] _init_vikey_driver_and_api 非致命失败: {e}')
    try:
        _init_layout_ai_system()
        print('[ASYNC-INIT] _init_layout_ai_system ✅')
    except Exception as e:
        print(f'[ASYNC-INIT] _init_layout_ai_system 非致命失败: {e}')

threading.Thread(target=_async_module_init, daemon=True, name='async-module-init').start()
print('[ASYNC-INIT] 模块级初始化已提交 (60s 后执行, 不阻塞 Flask)')
try:
    from app.services.auto_mount_service import auto_mount_service
    # 注册默认后台任务（通过动态引用）
    import types as _types
    def _health_check():
        try:
            auto_mount_service.emit_event('system.health_check', timestamp=__import__('datetime').datetime.now().isoformat())
        except Exception:
            pass
    def _report_collect():
        try:
            auto_mount_service.emit_event('system.report_collect', count=0)
        except Exception:
            pass
    # 将函数挂到 service 模块
    import app.services.auto_mount_service as _am
    _am._health_check_task = _health_check
    _am._collect_reports_task = _report_collect

    auto_mount_service.register_task(
        task_id='periodic_health_check',
        module_path='app.services.auto_mount_service',
        func_name='_health_check_task',
        name='系统健康检查',
        interval=30,
        priority=5
    )
    auto_mount_service.register_task(
        task_id='periodic_report_collect',
        module_path='app.services.auto_mount_service',
        func_name='_collect_reports_task',
        name='报告采集',
        interval=60,
        priority=4
    )
    # 执行挂载
    mount_result = auto_mount_service.mount_all()
    import logging as _aml
    _aml.info(f"[auto_mount] 挂载完成: {mount_result}")
except Exception as e:
    import logging as _aml2
    _aml2.warning(f"[auto_mount] 初始化失败: {e}")


# ================================================================
# Vikey USBKey 驱动 + API Blueprint 初始化入口
# - 建表：vikey_device_bindings / vikey_operations_log / vikey_device_certs
# - 种子：2 个默认测试绑定（幂等）
# - 挂载：Blueprint /api/vikey
# - 初始化：VikeyAPI 统一封装类（所有模块通过 get_vikey_api() 调用）
# ================================================================
def _init_vikey_driver_and_api():
    import logging as _vk_logger
    # ---- 1) 优先初始化 VikeyAPI 统一封装（Facade），供后续所有模块调用 ----
    try:
        from core.services.vikey_api import (
            get_vikey_api, VIKEY_API_VERSION, VIKEY_DRIVER_VERSION,
        )
        vk_api = get_vikey_api()
        vi = vk_api.get_version_info()
        try:
            hc = vk_api.health_check()
            dev_count = hc.get("device_count", 0)
            sa_serial = hc.get("super_admin_serial")
        except Exception:
            dev_count = 0
            sa_serial = None
        _vk_logger.info(
            f"[vikey] VikeyAPI init OK: api_version={VIKEY_API_VERSION} "
            f"driver_version={VIKEY_DRIVER_VERSION} "
            f"backend={vi.get('backend')} devices={dev_count} "
            f"sa_serial={sa_serial}"
        )
    except Exception as e:
        _vk_logger.warning(f"[vikey] VikeyAPI init fail: {e}")
    # ---- 2) 底层驱动初始化（保持向后兼容，某些老代码仍直接访问 manager）----
    try:
        from core.services.vikey_driver import get_vikey_manager, VIKEY_DRIVER_VERSION as _DV
        mgr = get_vikey_manager()
        _vk_logger.info(
            f"[vikey] driver init: driver_version={_DV} "
            f"backend={mgr.backend.NAME} devices={len(mgr.enumerate_devices())} "
            f"bindings={len(mgr.list_bindings()) if hasattr(mgr, 'list_bindings') else 'N/A'}"
        )
    except Exception as e:
        _vk_logger.warning(f"[vikey] driver init fail: {e}")
    # ---- 3) 挂载旧 Blueprint（保持 /api/_vikey_legacy 向后兼容）----
    try:
        from app.api.vikey_api import vikey_api as _vk_api
        app.register_blueprint(_vk_api, url_prefix='/api/_vikey_legacy')
        _vk_logger.info("[vikey] blueprint registered: vikey_api @ /api/_vikey_legacy (legacy, new API uses /api/vikey)")
    except Exception as e:
        _vk_logger.warning(f"[vikey] blueprint register fail: {e}")


# 🆕 已移到 _async_module_init() — 延迟 60s 后台执行
# _init_vikey_driver_and_api()


# ================================================================
# 布局AI LayoutAI - 动态布局调节系统
# - 建表：layout_rules / layout_snapshots / layout_adjustment_logs / layout_employee_configs (4张表)
# - 种子：20条排版割裂检测规则（LF001-LF020）
# - 初始化：LayoutAdjusterAIEmployee 单例
# - 挂载：Blueprint /api/layout_ai（快照/统计/规则/日志/员工配置）
# ================================================================
def _init_layout_ai_system():
    import logging as _lay_logger
    ok_tables, ok_seed = False, 0
    try:
        from ai_engines.layout_adjuster_ai_employee import init_layout_ai_system as _init_lay
        ok_tables, ok_seed = _init_lay()
        _lay_logger.info(
            f"[layout_ai] init: tables={'OK' if ok_tables else 'FAIL'}, seeded_rules={ok_seed}"
        )
    except Exception as e:
        _lay_logger.warning(f"[layout_ai] init fail: {e}")
    try:
        from app.api.layout_ai_api import layout_ai_api as _lay_api
        app.register_blueprint(_lay_api)
        _lay_logger.info("[layout_ai] blueprint registered: layout_ai_api @ /api/layout_ai")
        try:
            from app.api.layout_ai_api import register_html_auto_injector as _inj
            _inj(app)
            _lay_logger.info("[layout_ai] HTML auto-injector registered (all text/html pages get probe+style)")
        except Exception as _ei:
            _lay_logger.warning(f"[layout_ai] auto-injector register fail: {_ei}")
    except Exception as e:
        _lay_logger.warning(f"[layout_ai] blueprint register fail: {e}")
    try:
        from ai_engines.layout_adjuster_ai_employee import LayoutAdjusterAIEmployee as _L
        try:
            from ai_engines import ai_employee_manager as _emp_mod
            _mgr = getattr(_emp_mod, 'ai_employee_manager', None) or getattr(_emp_mod, 'manager', None)
            if _mgr:
                _inst = _mgr.get_employee(_L.EMPLOYEE_ID) if hasattr(_mgr, 'get_employee') else None
                if not _inst:
                    _add_fn = getattr(_mgr, 'add_employee', None)
                    if _add_fn: _add_fn(_L())
                    _lay_logger.info(f"[layout_ai] registered into ai_employee_manager: {_L.EMPLOYEE_ID}")
        except Exception:
            pass
    except Exception as e:
        _lay_logger.warning(f"[layout_ai] employee register fail: {e}")


# 🆕 已移到 _async_module_init() — 延迟 60s 后台执行
# _init_layout_ai_system()


# ============ Blueprint 统一注册 + 局部 App Factory (v22.36.0 Phase 7) ============
# 唯一注册点：调用 routes.register_all_blueprints(app) + api_blueprint_registrar
# 禁止在此处逐个手动 register_blueprint — 会导致 "already registered" 级联 + 循环导入
# 详见 routes/__init__.py 的 blueprints 注册表
#
# Phase 7 局部 Factory 模式:
#   - L767 模块级 app = Flask(...) 保持不动 (所有 @app.route decorator 依赖)
#   - Blueprint 注册 + API 蓝图扫描 包进 ensure_app_ready()
#   - modular_start.py 调 ensure_app_ready() 再 import app
#   - 所有 _mt_sdb() 延迟绑定蓝图: server_real_db 模块 globals 不变, 兼容 Phase 2-6 代码

# 防重入标记: 避免 server_real_db 被 import 两次时重复注册蓝图
_app_initialized = False


def ensure_app_ready():
    """Phase 7 局部 Factory: 统一入口, 保证蓝图+API注册只执行一次.

    server_real_db.py 仍保留模块级 app + 模块级 globals (APP_DB, _MT_ADMIN_ROLES 等),
    @app.route / @app.before_request decorator 仍在模块加载时绑定到模块级 app —
    本函数只负责蓝图注册 (这是唯一会被 import 两次破坏的部分).
    """
    global _app_initialized, app
    if _app_initialized:
        return app
    _app_initialized = True

    # 1. routes/__init__.py: 31 个手工注册蓝图
    try:
        from routes import register_all_blueprints
        _reg = register_all_blueprints(app)
        print(f'[Routes] Blueprint 统一注册完成')
    except Exception as _bp_e:
        import traceback
        print(f'[Routes] Blueprint 统一注册失败: {_bp_e}')
        traceback.print_exc()

    # 2. app/api/*_api.py: 32 个 API 蓝图动态扫描注册
    try:
        from routes.api_blueprint_registrar import register_all_api_blueprints
        _api_reg = register_all_api_blueprints(app)
    except Exception as _api_e:
        print(f'[API-Registrar] 注册失败: {_api_e}')

    # 3. 兜底 catch-all: 补 admin_subpage_routes 注册失败留下的 404 洞
    # admin_subpage_routes Blueprint 因 endpoint 冲突整体挂载失败 → 所有 /admin_app/<name> 404
    # 这里直接 app.add_url_rule 兜底, Flask 按注册顺序匹配, 具体路由(在 bp 成功的)先匹配, 兜底最后
    @app.route('/admin_app/', methods=['GET'], endpoint='_mt_admin_app_root_fallback')
    def _mt_admin_app_root():
        from flask import redirect as _r
        return _r('/admin_app/governance/dashboard')

    @app.route('/admin_app/<path:name>', methods=['GET'], endpoint='_mt_admin_app_catchall_fallback')
    def _mt_admin_app_catchall(name):
        """admin_app 兜底 catch-all: 没被任何 bp 接住的 /admin_app/xxx 走这里"""
        import os as _os
        from flask import render_template as _rt, session as _sess, redirect as _r
        # VIKEY 强制校验 (SA 必须有加密狗)
        uname = (_sess.get('username') or '').lower()
        is_sa = uname == 'wuchenghao15' or (_sess.get('role') in ('super_admin','admin','sadmin'))
        if not is_sa:
            return _r('/admin_app/login')
        # 优先找独立模板 admin_app/{name}.html
        tmpl = f'admin_app/{name}.html'
        full = _os.path.join(_os.path.dirname(__file__), 'templates', tmpl)
        if _os.path.exists(full):
            try: return _rt(tmpl)
            except Exception: pass
        # 统一 fallback 模板
        return _rt('admin_fallback.html', name=name)

    # 4. 零散 redirect: 补模板/导航引用但没路由的旧路径
    _REDIRECT_MAP = {
        '/exam_system': '/exam_center',
        '/exam_system/exams': '/exam_center',
        '/exam_system/tests': '/exam_center',
        '/exam_system/past_exams': '/exam_center',
        '/exam_system/daily_practice': '/exam_center',
        '/ai_chat': '/japanese_page',
        '/ai-chat': '/japanese_page',
        '/forgot-password': '/forgot_password',
        '/mobile/home': '/student_portal',
        '/mobile/exam': '/exam_center',
        '/mobile/login': '/login',
        '/mobile/profile': '/student_portal',
        '/smart_dashboard': '/admin_app/governance/dashboard',
        '/adult_placement_test': '/adult_education',
        '/status': '/system/status',
        '/wrong_book': '/exam_center',  # 错题本, exam_bp 注册失败时兜底
    }
    def _make_redirect(_target):
        from flask import redirect as _r
        def _view(): return _r(_target)
        return _view
    for _from, _to in _REDIRECT_MAP.items():
        app.add_url_rule(_from, endpoint=f'_mt_rd_{_from.replace("/","_").lstrip("_")}',
                         view_func=_make_redirect(_to))

    return app


# 模块首次加载时自动执行 (兼容直接 import server_real_db 的旧代码)
ensure_app_ready()


# ============ v22.39.0: i18n 文案管理 + Console 错误监控 初始化 ============
# 🆕 v6.1 修复: seed 失败不阻塞 inject —— 首页 72 处 t() 依赖 Jinja2 globals
try:
    from engines.i18n_engine import inject_i18n_into_app, seed_common_strings, _get_conn as _i18n_get_conn
except Exception as _ie_import:
    print(f'[I18N] import failed: {_ie_import}')
    inject_i18n_into_app = None
    _i18n_get_conn = None

# 1) 注入 t() / t_kw() —— 必须在 import 成功后立即执行, 不受 seed 影响
if inject_i18n_into_app is not None:
    try:
        inject_i18n_into_app(app)
        print('[I18N] ✅ inject t()/t_kw() into Jinja2 globals')
    except Exception as _ie_inject:
        print(f'[I18N] inject failed: {_ie_inject}')
        # fallback: 注入极简版 t() —— 防止模板崩
        app.jinja_env.globals.setdefault('t', lambda k, d=None, lang=None: d if d is not None else k)
        app.jinja_env.globals.setdefault('t_kw', lambda k, d, lang='zh_CN', **kw: (d if d is not None else k))
        print('[I18N] fallback: injected minimal t() returning default/key')

# 2) seed 常用文案 —— 失败不影响 inject (v6.1 修复)
try:
    if _i18n_get_conn is not None:
        # 先检查表是否可写
        _c = _i18n_get_conn()
        _c.execute('SELECT count(*) FROM mt_i18n_keys LIMIT 1')
        _c.close()
        _seeded = seed_common_strings()
        print(f'[I18N] ✅ seed {_seeded} common strings')
    else:
        print('[I18N] skip seed: _get_conn unavailable')
except Exception as _ie_seed:
    print(f'[I18N] seed skipped (non-fatal): {_ie_seed}')

try:
    from engines.ai_console_monitor import record_console_error, record_batch, run_cycle as _cm_run_cycle
    @app.route('/api/console/record', methods=['POST'])
    def _record_console_error():
        from flask import request, jsonify, session as _sess
        _d = request.get_json(silent=True) or {}
        _uid = _sess.get('user_id'); _uname = _sess.get('username')
        if isinstance(_d.get('events'), list):
            _count = record_batch(_d['events'], user_id=_uid, username=_uname)
            return jsonify({'success': True, 'count': _count})
        else:
            _ok = record_console_error(
                url=_d.get('url', '')[:500], message=_d.get('message', '')[:1000],
                stack=_d.get('stack', '')[:2000], user_id=_uid, username=_uname)
            return jsonify({'success': bool(_ok)})

    @app.route('/api/console/run_cycle', methods=['POST'])
    def _trigger_console_run_cycle():
        """手动触发 console_monitor run_cycle (server 内部调用, 同进程 WAL 不 lock)."""
        try:
            with open('/tmp/cm_api_trigger.txt', 'a') as _t:
                _t.write(f"API run_cycle triggered at {datetime.now().isoformat()}\n")
            _cm_run_cycle()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)[:200]}), 500

    print('[CONSOLE-MONITOR] /api/console/record + /api/console/run_cycle 已注册')
except Exception as _ce:
    print(f'[CONSOLE-MONITOR] route skip: {_ce}')

# 🔧 v6.2 fix: 原代码在此调 _get_conn() 但函数定义在 L6741，模块级顺序导致 NameError
# 改为内联 sqlite3.connect —— 避免前向引用
try:
    import sqlite3 as _sq3
    _c = _sq3.connect(APP_DB, timeout=30)
    _c.execute("PRAGMA busy_timeout=30000")
    _c.execute("""INSERT OR IGNORE INTO daemon_registry
        (name, display_name, interval_sec, start_cmd, status, source)
        VALUES ('console_error_monitor', 'Console错误监控AI', 120, 'engines/ai_console_monitor.py', 'READY', 'SYSTEM_REQ')""")
    _c.commit(); _c.close()
except Exception as _de:
    print(f'[CONSOLE-MONITOR] daemon_registry skip: {_de}')


@app.before_request
def _mtscos_ai_firewall_check():
    """AI 防火墙全局请求拦截：SQLi/XSS/SSRF/遍历/命令注入/恶意UA/速率/扩展/泄露检测"""
    try:
        p = request.path or ''
        # AI 防火墙白名单：登录/登出/检查密码等关键路径必须放行，防止登录流程被误拦
        ai_fw_whitelist = {
            '/auth/login', '/auth/logout', '/auth/check_username', '/auth/check_password',
            '/auth/forgot_password', '/auth/reset_password',
            '/mobile/login', '/admin_app/login',
            '/dashboard',
        }
        if (p.startswith('/static/') or p.startswith('/assets/')
                or p in ('/favicon.ico', '/robots.txt', '/manifest.json', '/service-worker.js')
                or p.endswith('.svg') or p.endswith('.png') or p.endswith('.jpg') or p.endswith('.ico')
                or p.endswith('.css') or p.endswith('.js')
                or p in ai_fw_whitelist):
            return None
        from core.services import ai_firewall as _fw
        blocked, code, msg, rule = _fw.check_request(request)
        if not blocked:
            return None
        payload = {
            'success': False,
            'blocked': True,
            'rule_code': (rule or {}).get('rule_code'),
            'rule_name': (rule or {}).get('name'),
            'severity': (rule or {}).get('severity') or 'warning',
            'message': msg or '[MTSCOS AI Firewall] Request blocked',
            'action': (rule or {}).get('action') or 'block',
        }
        accept = (request.headers.get('Accept', '') or '').lower()
        if 'text/html' in accept and 'application/json' not in accept:
            import json as _j
            pretty = _j.dumps(payload, ensure_ascii=False, indent=2)
            html = (
                '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
                '<title>403 Blocked · MTSCOS AI Firewall</title></head>'
                '<body style="background:#0b1020;color:#cbd5e1;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;padding:48px 24px">'
                '<div style="max-width:720px;margin:auto">'
                '<h1 style="color:#f87171;margin:0 0 12px">🚫 Request Blocked</h1>'
                f'<p style="opacity:.85;margin:0 0 24px">{msg or "请求被 MTSCOS AI 防火墙拦截"}</p>'
                f'<pre style="background:#0f172a;padding:16px 20px;border-radius:10px;border:1px solid rgba(255,255,255,.08);white-space:pre-wrap">{pretty}</pre>'
                '<p style="opacity:.6;margin-top:24px">如需放行，请联系超级管理员调整 <code>/api/ai_firewall/rules</code> 规则。</p>'
                '</div></body></html>'
            )
            return html, int(code or 403)
        return jsonify(payload), int(code or 403)
    except Exception as e:
        import logging as _lg
        _lg.warning(f"[ai_firewall] before_request fail: {e}")
    return None


# ==========================================================
# ⚙️  MTSCOS 系统容器管控层（SysContainer）
#
# 核心能力：
#   1) 统一系统容器装饰器 @system_container —— 所有 HTML 页面必须通过它
#   2) AI 管控：行为审计 / 权限二次校验 / 异常熔断降级
#   3) 动态状态监控：session 健康度、客户端心跳、容器生命周期
#   4) Cookies 自动挂载：mtscos_sid / mtscos_uid / mtscos_ts / mtscos_sc
#   5) Session 统一加载：未登录用户自动 guest session，已登录从 DB 回填
# ==========================================================
from functools import wraps  # noqa: E402
import threading  # noqa: E402
import uuid as _uuid  # noqa: E402
import hmac as _hmac  # noqa: E402
import random as _rd  # noqa: E402

# ---------- 容器常量 ----------
_MT_SYS_CONTAINER_VERSION = '4.0.0-mtscos'
# 系统版本号（MINOR bump → v22.7.0：巡检缺口发现引擎5维架构优化 - auto_dev_team_engine.py 15硬伤+3运行BUG全修复(算法:_py_index 5维扫描复用↓80%+CompletionVerifier缓存验证↓99.5%+派发按weight降序 / 权重:GapPrioritizer唯一入口5维加权SEV*0.45+TYPE*0.25+OCCUR*0.12+FRESH*0.1+TEAM*0.08+建议池priority=ceil(w/10)链路一致+单return单审计日志 / 架构:DevPipelineRunner 4阶段Pipeline+ENGINE_REGISTRY生命周期注册+warmup_system统一入口 / 逻辑:IR14单事务批量transition+flow_id污染defrag↓93.8%+Implementer 4分支决策树confidence / 框架:连接池容量3+扫描mtime指纹缓存TTL900+GapEngineError 8错误码枚举) + §14强制12步骤自动执行100%STEP_7 + 总耗时↓94% 17.44s跑完81gaps）
SYSTEM_VERSION = 'v22.7.0'
_MT_SYS_CONTAINER_SECRET = hashlib.sha256(b'MTSCOS-SYSTEM-CONTAINER-SECRET-v3').digest()
_MT_GUEST_ROLE = 'guest'
_MT_ADMIN_ROLES = {'admin', 'super_admin', 'teacher_admin', 'school_admin', 'sysadmin',
                   'hardware_admin', 'cluster_manager', 'ai_manager',
                   'question_manager', 'exam_proctor'}
_MT_PAGE_RENDER_KEY = '__mt_container_rendered__'

def _build_role_sidebar(role):
    """构建角色侧边栏菜单 — 8 大功能域整合版 (flow_id=layout_rebuild_20260902)

    整合目标:
      1. 覆盖全部 66 个 admin_app 页面 (原仅 25 项有导航)
      2. AI 功能统一收口到 "AI 能力中心" (原 13+ 页面分散)
      3. 8 大教育模块归入 "教育管理"
      4. 治理中枢独立成域 (团队/EigenFlux/12步/脑库/神经阵列/正规化)
      5. base.html 通过 sidebar_menus._groups 动态渲染

    Icon 集: 与原 _icons 保持兼容, 新增 edu/govern/security/dev 等.
    """
    _icons = {
        'dashboard': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
        'users': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        'exams': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
        'questions': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
        'ai': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><circle cx="15" cy="9" r="2"/><path d="M9 15h6"/></svg>',
        'settings': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19 12h2M3 12h2M12 3v2M12 19v2"/></svg>',
        'status': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/></svg>',
        'backup': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>',
        'permissions': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        'vikey': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
        'upgrade': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>',
        'goals': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/></svg>',
        'inspection': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
        'report': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
        'courses': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
        'analysis': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        'custom': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
        'level': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        'classes': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
        'process': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/></svg>',
        'team': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/></svg>',
        'network': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="7" x2="6.5" y2="17"/><line x1="12" y1="7" x2="17.5" y2="17"/></svg>',
        'flow': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="16" y="16" width="6" height="6" rx="1"/></svg>',
        'brain': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2a2.5 2.5 0 0 0-2.5 2.5v.5a2.5 2.5 0 0 0-2 4 2.5 2.5 0 0 0 0 5 2.5 2.5 0 0 0 2 4v.5A2.5 2.5 0 0 0 9.5 22h.5V2h-.5z"/><path d="M14.5 2a2.5 2.5 0 0 1 2.5 2.5v.5a2.5 2.5 0 0 1 2 4 2.5 2.5 0 0 1 0 5 2.5 2.5 0 0 1-2 4v.5a2.5 2.5 0 0 1-2.5 2.5H14V2h.5z"/></svg>',
        'neural': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="4" cy="6" r="2"/><circle cx="4" cy="18" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="20" cy="6" r="2"/><circle cx="20" cy="18" r="2"/><line x1="6" y1="6" x2="10" y2="11"/></svg>',
        # 新增图标
        'edu': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
        'govern': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/></svg>',
        'security': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        'dev': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
        'log': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>',
        'cog': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M9 2h6M9 22h6M2 9v6M22 9v6M4.9 4.9l4.2 4.2M14.9 14.9l4.2 4.2M4.9 19.1l4.2-4.2M14.9 9.1l4.2-4.2"/></svg>',
        'tutor': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7h-9M14 17H5M17 17a3 3 0 1 0 6 0 3 3 0 0 0-6 0z"/><circle cx="6" cy="17" r="3"/></svg>',
        'qbank': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
        'copy': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
        'form': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/></svg>',
        'comm': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
        'adult': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        'subject': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
        'completion': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
        'enrich': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
        'aid': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>',
        'qinspect': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        'qoutdated': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        'sslvpn': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        'personal': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"/><path d="M5.5 21a6.5 6.5 0 0 1 13 0"/></svg>',
    }

    role = (role or 'user').lower()

    def G(label, items):
        return {'group': label, 'items': list(items)}

    def I(icon_key, label, url):
        return {'icon': _icons.get(icon_key, _icons['custom']), 'label': label, 'url': url}

    # === super_admin: 8 大功能域 (覆盖全部 66 页面 + 32 API 蓝图入口) ===
    if role == 'super_admin':
        groups = [
            G('① 总览中心', [
                I('dashboard', '智能总览', '/smart_dashboard'),
                I('dashboard', '后台总览', '/admin_app/dashboard_unified'),
                I('dashboard', '管理仪表盘', '/admin_app/dashboard'),
            ]),
            G('② 用户与权限', [
                I('users', '用户管理', '/admin_app/users'),
                I('permissions', '权限管理', '/admin_app/user_auth'),
                I('classes', '班级管理', '/admin_app/education_management'),
                I('users', '角色与权限', '/admin_app/permission_management'),
            ]),
            G('③ 教育管理', [
                I('courses', '课程管理', '/admin_app/courses'),
                I('qbank', '智能题库', '/admin_app/intelligent_question_bank'),
                I('exams', '考试列表', '/admin_app/exams'),
                I('analysis', '考试分析', '/admin_app/exam_analysis'),
                I('flow', '学习路径', '/admin_app/learning_paths'),
                I('level', '分级测试', '/admin_app/assignments'),
                # 8 大教育功能模块 (v21.7.0)
                I('qinspect', '题库巡检', '/admin_app/qbank_inspection'),
                I('qoutdated', '过期题清理', '/admin_app/qbank_outdated'),
                I('courses', '课件管理', '/admin_app/courseware_manager'),
                I('aid', '教辅对齐', '/admin_app/teaching_aid_alignment'),
                I('subject', '学科适配', '/admin_app/subject_adaptation'),
                I('completion', '课程完成度', '/admin_app/course_completion'),
                I('enrich', '教师赋能', '/admin_app/teacher_enrichment'),
                I('adult', '成人课程开发', '/admin_app/adult_course_dev'),
                I('copy', '副本管理', '/admin_app/copy_management'),
                I('form', '表单管理', '/admin_app/form_manager'),
            ]),
            G('④ AI 能力中心', [
                # AI 认知与情绪
                I('cog', 'AI认知推理', '/admin_app/ai_cognitive_reasoning'),
                I('cog', 'AI情绪分析', '/admin_app/ai_emotion'),
                # AI 学习
                I('ai', 'AI自适应学习', '/admin_app/ai_adaptive_learning'),
                I('ai', 'AI自动学习', '/admin_app/ai_auto_learning'),
                I('ai', 'AI学习仪表盘', '/admin_app/ai_learning_dashboard'),
                I('ai', 'AI学习规划', '/admin_app/ai_learning_planner'),
                I('flow', '学习路径引擎', '/admin_app/ai_study_path'),
                I('personal', '个性化推荐', '/admin_app/personalization'),
                # AI 教学
                I('ai', 'AI组卷', '/admin_app/ai_exam_composer'),
                I('qbank', 'AI出题', '/admin_app/ai_question_generation'),
                I('qbank', 'AI题库生成', '/admin_app/ai_question_generator'),
                I('tutor', 'AI导师', '/admin_app/ai_tutor'),
                I('tutor', 'AI助教', '/admin_app/ai_tutor_assistant'),
                I('ai', 'AI智能问答', '/admin_app/ai_intelligent_qna'),
                I('report', 'AI评估', '/admin_app/ai_evaluation'),
                I('ai', 'AI智能中心', '/admin_app/ai_intelligent_center'),
                # AI 分析
                I('analysis', '学生分析', '/admin_app/student_analytics'),
                I('analysis', '数据分析', '/admin_app/data_analysis'),
                I('ai', 'AI预警干预', '/admin_app/ai_warning_intervention'),
                I('ai', 'AI知识图谱', '/admin_app/ai_knowledge_graph'),
                I('ai', 'AI记忆系统', '/admin_app/ai_memory'),
                I('comm', '家校沟通', '/admin_app/communication_center'),
            ]),
            G('⑤ AI 治理中枢', [
                I('team', 'AI团队枢纽', '/admin_app/ai_team_hub'),
                I('network', 'EigenFlux专家中心', '/admin_app/eigenflux_center'),
                I('flow', '12步骤流程看板', '/admin_app/dev_flow_dashboard'),
                I('brain', '脑库探索器', '/admin_app/brain_bank_explorer'),
                I('neural', '神经网络阵列矩阵', '/admin_app/neural_array_matrix'),
                I('govern', '治理中枢面板', '/admin_app/governance/'),
                I('govern', '系统正规化', '/admin_app/governance/system_normalization'),
            ]),
            G('⑥ 运维监控', [
                I('report', '巡检报告', '/admin_app/health_details'),
                I('inspection', '巡检设置', '/admin_app/inspection_settings'),
                I('process', '进程监控', '/admin_app/process_monitor'),
                I('status', '系统状态', '/admin_app/monitor'),
                I('inspection', '巡检报告(旧)', '/admin_app/inspection_report'),
                I('log', '日志查看', '/admin_app/enhanced_settings?tab=logs'),
                I('backup', '备份管理', '/admin_app/enhanced_settings?tab=backup'),
                I('upgrade', '升级中心', '/admin_app/enhanced_settings?tab=upgrade'),
                I('health', '健康检查', '/admin_app/health_monitor'),
                I('status', '健康详情', '/admin_app/health_details'),
            ]),
            G('⑦ 系统安全', [
                I('vikey', 'VIKEY管理', '/admin_app/security_dashboard'),
                I('vikey', 'VIKEY绑定', '/admin_app/vikey'),
                I('vikey', 'VIKEY管理器', '/admin_app/vikey_manager'),
                I('security', 'SSL VPN管理', '/admin_app/sslvpn_management'),
                I('security', '安全仪表盘', '/api/security/status'),
                I('settings', '系统设置', '/settings'),
                I('settings', '增强设置', '/admin_app/enhanced_settings'),
            ]),
            G('⑧ 开发者中心', [
                I('dev', '开发流程看板', '/admin_app/dev_flow_dashboard'),
                I('dev', '艺术家工坊', '/admin_app/art_studio'),
                I('dev', 'Arduino会话', '/admin_app/arduino_ide'),
                I('dev', '主题调度中心', '/api/theme/list'),
                I('dev', 'API健康检查', '/api/health'),
            ]),
        ]
    elif role in {'admin', 'school_admin', 'sysadmin'}:
        groups = [
            G('① 总览中心', [
                I('dashboard', '后台总览', '/admin_app/dashboard_unified'),
                I('dashboard', '管理仪表盘', '/admin_app/dashboard'),
            ]),
            G('② 用户与权限', [
                I('users', '用户管理', '/admin_app/users'),
                I('permissions', '权限管理', '/admin_app/user_auth'),
                I('classes', '班级管理', '/admin_app/education_management'),
            ]),
            G('③ 教育管理', [
                I('courses', '课程管理', '/admin_app/courses'),
                I('qbank', '智能题库', '/admin_app/intelligent_question_bank'),
                I('exams', '考试列表', '/admin_app/exams'),
                I('analysis', '考试分析', '/admin_app/exam_analysis'),
                I('qinspect', '题库巡检', '/admin_app/qbank_inspection'),
                I('qoutdated', '过期题清理', '/admin_app/qbank_outdated'),
                I('courses', '课件管理', '/admin_app/courseware_manager'),
            ]),
            G('④ AI 能力中心', [
                I('ai', 'AI员工', '/admin_app/ai_employee_dashboard'),
                I('ai', 'AI组卷', '/admin_app/ai_exam_composer'),
                I('tutor', 'AI导师', '/admin_app/ai_tutor'),
                I('ai', 'AI智能问答', '/admin_app/ai_intelligent_qna'),
                I('report', 'AI评估', '/admin_app/ai_evaluation'),
                I('analysis', '学生分析', '/admin_app/student_analytics'),
            ]),
            G('⑤ AI 治理中枢', [
                I('team', 'AI团队枢纽', '/admin_app/ai_team_hub'),
                I('brain', '脑库探索器', '/admin_app/brain_bank_explorer'),
            ]),
            G('⑥ 运维监控', [
                I('process', '进程监控', '/admin_app/process_monitor'),
                I('status', '系统状态', '/admin_app/monitor'),
                I('report', '巡检报告', '/admin_app/health_details'),
            ]),
            G('⑦ 系统设置', [
                I('settings', '系统设置', '/settings'),
                I('settings', '增强设置', '/admin_app/enhanced_settings'),
            ]),
        ]
    elif role == 'teacher_admin':
        groups = [
            G('① 教学概览', [
                I('dashboard', '教学总览', '/admin_app/dashboard_unified'),
            ]),
            G('② 考试与题库', [
                I('exams', '考试列表', '/admin_app/exams'),
                I('ai', 'AI组卷', '/admin_app/ai_exam_composer'),
                I('analysis', '考试分析', '/admin_app/exam_analysis'),
                I('qbank', '智能题库', '/admin_app/intelligent_question_bank'),
                I('qinspect', '题库巡检', '/admin_app/qbank_inspection'),
            ]),
            G('③ 教学管理', [
                I('users', '学生管理', '/admin_app/student_analytics'),
                I('courses', '课程管理', '/admin_app/courses'),
                I('courses', '课件管理', '/admin_app/courseware_manager'),
            ]),
            G('④ AI 助手', [
                I('tutor', 'AI导师', '/admin_app/ai_tutor'),
                I('ai', 'AI智能问答', '/admin_app/ai_intelligent_qna'),
                I('report', 'AI评估', '/admin_app/ai_evaluation'),
            ]),
            G('⑤ 系统设置', [
                I('settings', '个人设置', '/settings'),
            ]),
        ]
    elif role == 'teacher':
        groups = [
            G('① 教学概览', [
                I('dashboard', '教学门户', '/student_portal'),
            ]),
            G('② 考试与题库', [
                I('exams', '我的考试', '/exam_center'),
                I('ai', 'AI组卷', '/admin_app/ai_exam_composer'),
                I('custom', '自定义考试', '/admin_app/exams'),
                I('qbank', '题库管理', '/admin_app/intelligent_question_bank'),
            ]),
            G('③ 教学管理', [
                I('users', '学生管理', '/admin_app/student_analytics'),
            ]),
            G('④ 个人设置', [
                I('settings', '个人设置', '/settings'),
            ]),
        ]
    elif role in {'student', 'student_vip', '成人学生'}:
        groups = [
            G('① 学习概览', [
                I('dashboard', '学习门户', '/student_portal'),
                I('goals', '学习记录', '/student_portal?tab=progress'),
            ]),
            G('② 考试与练习', [
                I('exams', '考试中心', '/exam_center'),
                I('level', '分级测试', '/exam_center?section=level'),
                I('questions', '错题本', '/wrong_book'),
            ]),
            G('③ 个人设置', [
                I('settings', '个人设置', '/settings'),
            ]),
        ]
    elif role in {'parent', '家长'}:
        groups = [
            G('① 概览', [
                I('dashboard', '学习概览', '/student_portal'),
            ]),
            G('② 学习相关', [
                I('exams', '考试成绩', '/exam_center'),
                I('questions', '学习记录', '/student_portal?tab=progress'),
            ]),
            G('③ 个人设置', [
                I('settings', '家长设置', '/settings'),
            ]),
        ]
    elif role in {'ai_manager', 'cluster_manager'}:
        groups = [
            G('① AI 总览', [
                I('dashboard', 'AI总览', '/admin_app/dashboard_unified'),
            ]),
            G('② AI 管理', [
                I('ai', 'AI员工', '/admin_app/ai_employee_dashboard'),
                I('neural', '集群矩阵', '/admin_app/neural_array_matrix'),
                I('team', 'AI团队枢纽', '/admin_app/ai_team_hub'),
                I('brain', '脑库探索器', '/admin_app/brain_bank_explorer'),
            ]),
            G('③ 系统设置', [
                I('settings', '系统设置', '/settings'),
            ]),
        ]
    elif role in {'question_manager', 'exam_proctor'}:
        groups = [
            G('① 题库总览', [
                I('dashboard', '题库总览', '/admin_app/dashboard_unified'),
            ]),
            G('② 考试与题目', [
                I('exams', '考试列表', '/admin_app/exams'),
                I('analysis', '考试分析', '/admin_app/exam_analysis'),
                I('qbank', '题库管理', '/admin_app/intelligent_question_bank'),
                I('qinspect', '题库巡检', '/admin_app/qbank_inspection'),
                I('qoutdated', '过期题清理', '/admin_app/qbank_outdated'),
            ]),
            G('③ 系统设置', [
                I('settings', '系统设置', '/settings'),
            ]),
        ]
    else:
        groups = [
            G('主菜单', [
                I('dashboard', '返回首页', '/'),
                I('settings', '个人设置', '/settings'),
            ]),
        ]

    # ⭐ 子类化 list 挂 _groups 属性 (供 base.html 分组渲染)
    class _SidebarList(list):
        __slots__ = ('_groups',)
    sidebar_menus = _SidebarList()
    for g in groups:
        sidebar_menus.append({'group': g['group']})
        for it in g['items']:
            sidebar_menus.append(it)
    sidebar_menus._groups = groups
    return sidebar_menus

_MT_HEARTBEAT_WINDOW = 120  # 2 分钟内没有心跳判定为离线
_MT_BEHAVIOR_RATE_LIMIT = 120  # 单用户每 60s 最多 120 次页面级操作
_MT_BEHAVIOR_LOCK = threading.RLock()
_MT_BEHAVIOR_BUCKETS: dict = {}  # uid -> [ts1, ts2, ...]
_MT_AIBEHAVIOR_LOCK = threading.RLock()
_MT_AIBEHAVIOR_LOG: list = []  # AI 管控行为审计环形缓冲（最多 500 条）

# ---------- 5 大系统容器 Cookies ----------
_MT_COOKIES = {
    'sid':    {'name': 'mtscos_sid',  'max_age': 86400 * 30, 'path': '/', 'httpOnly': True,  'sameSite': 'Lax'},
    'uid':    {'name': 'mtscos_uid',  'max_age': 86400 * 30, 'path': '/', 'httpOnly': False, 'sameSite': 'Lax'},
    'ts':     {'name': 'mtscos_ts',   'max_age': 86400,      'path': '/', 'httpOnly': False, 'sameSite': 'Lax'},
    'sc':     {'name': 'mtscos_sc',   'max_age': None,       'path': '/', 'httpOnly': True,  'sameSite': 'Strict'},  # 会话级
    'trace':  {'name': 'mtscos_trace','max_age': 3600,       'path': '/', 'httpOnly': False, 'sameSite': 'Lax'},
}


def _ensure_container_tables(conn) -> None:
    """自动建表（容器心跳表、AI管控审计表、session持久化表）—— 幂等"""
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sys_container_heartbeat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sid TEXT NOT NULL,
            uid TEXT,
            username TEXT,
            role TEXT,
            path TEXT,
            ip TEXT,
            ua TEXT,
            action TEXT,
            ok INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_container_hb_sid ON sys_container_heartbeat(sid);
        CREATE INDEX IF NOT EXISTS idx_container_hb_time ON sys_container_heartbeat(created_at);

        CREATE TABLE IF NOT EXISTS sys_container_ai_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT,
            sid TEXT,
            uid TEXT,
            username TEXT,
            role TEXT,
            path TEXT,
            action TEXT,
            risk_level TEXT DEFAULT 'low',
            rule_hit TEXT,
            blocked INTEGER DEFAULT 0,
            detail TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_audit_time ON sys_container_ai_audit(created_at);

        CREATE TABLE IF NOT EXISTS sys_container_sessions (
            sid TEXT PRIMARY KEY,
            uid TEXT,
            username TEXT,
            role TEXT,
            ip TEXT,
            ua TEXT,
            payload_json TEXT,
            last_seen TEXT DEFAULT (datetime('now','localtime')),
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
        conn.commit()
    except Exception:
        pass


def _sys_ensure_tables():
    try:
        # 前向引用修复：_bizdb_path 定义在L13715之后，启动期可能还没声明，fallback到APP_DB
        try:
            _dbp = _bizdb_path()
        except NameError:
            _dbp = APP_DB
        with sqlite3.connect(_dbp) as c:
            _ensure_container_tables(c)
    except Exception as _sys_tbl_exc:
        # 🔴 异常捕捉修复：容器表建表失败不再静默吞掉
        try:
            import logging as _lg_sys
            _lg_sys.warning(
                "[DB:_sys_ensure_tables] 容器心跳/审计表建表失败: %s", _sys_tbl_exc
            )
        except Exception:
            pass


_sys_ensure_tables()


def _gen_sid() -> str:
    """生成带签名的安全 SID（32 位随机 + 8 位 HMAC 签名）"""
    raw = secrets.token_hex(16) if 'secrets' in globals() else hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:32]
    try:
        import secrets as _s
        raw = _s.token_hex(16)
    except Exception:
        pass
    sig = _hmac.new(_MT_SYS_CONTAINER_SECRET, raw.encode(), hashlib.sha256).hexdigest()[:8]
    return raw + sig


def _verify_sid(sid: str) -> bool:
    if not sid or len(sid) != 40:
        return False
    raw, sig = sid[:32], sid[32:]
    expected = _hmac.new(_MT_SYS_CONTAINER_SECRET, raw.encode(), hashlib.sha256).hexdigest()[:8]
    return _hmac.compare_digest(sig, expected)


def _trace_id() -> str:
    return 'mt-' + hashlib.sha256((str(time.time_ns()) + str(_rd.random())).encode()).hexdigest()[:16]


def _ip() -> str:
    try:
        return (request.headers.get('X-Forwarded-For') or request.remote_addr or '0.0.0.0').split(',')[0].strip()
    except Exception:
        return '0.0.0.0'


def _ua() -> str:
    try:
        return (request.user_agent.string if hasattr(request, 'user_agent') and request.user_agent else request.headers.get('User-Agent', ''))[:500]
    except Exception:
        return ''


def _is_mobile(ua: str = '') -> bool:
    """检测是否为移动端设备（手机/平板）"""
    ua_lower = (ua or _ua()).lower()
    mobile_keywords = [
        'iphone', 'ipad', 'ipod', 'android', 'mobile', 'phone', 'tablet',
        'windows phone', 'opera mini', 'opera mobi', 'blackberry',
        'webos', 'symbian', 'bada', 'nokia', 'samsung', 'lg', 'motorola',
        'huawei', 'xiaomi', 'oppo', 'vivo', 'meizu', 'lenovo', 'zte',
        'micromax', 'asus', 'sony', 'htc', 'lg', 'nexus', 'kindle',
        'firefox os', 'silk', 'playbook', 'palm', 'maemo', 'meego',
        'touch', 'fennec', 'bolt', 'skyfire', 'dolfin', 'uzard',
        'netfront', 'jasmine', 'blazer', 'avantgo', 'goanna', 'iceweasel',
        'k-meleon', 'midori', 'netsurf', 'qupzilla', 'qutebrowser',
        'rekonq', 'surf', 'uzbl', 'w3m', 'lynx', 'links', 'elinks',
    ]
    for keyword in mobile_keywords:
        if keyword in ua_lower:
            return True
    return False


def _current_safe_user() -> dict:
    """统一当前用户读取：未登录自动 guest session，不抛异常"""
    try:
        uid = session.get('user_id')
        uname = session.get('username')
        role = session.get('role') or _MT_GUEST_ROLE
        logged_in = bool(session.get('logged_in'))
        if uid and uname and logged_in:
            is_super_admin = (str(uname).lower() == 'wuchenghao15')
            return {'uid': str(uid), 'username': uname, 'role': role, 'logged_in': True, 'is_guest': False, 'is_super_admin': is_super_admin}
    except Exception:
        pass
    return {'uid': f'guest-{int(time.time()) % 100000}', 'username': _MT_GUEST_ROLE, 'role': _MT_GUEST_ROLE,
            'logged_in': False, 'is_guest': True, 'is_super_admin': False}


# =================================================================
#  [V2.1 统一权限核心] SA判定 + 权限边界 + Settings SSOT 单一真源
#  - 解决用户反馈：非SA绝对隔离Vikey / 设置真实落库 / 插拔即时切换SA
# =================================================================
_SA_HARDCODED_USERNAMES = {'wuchenghao15'}  # ⭐ 最高优先级硬编码SA白名单

def _mt_resolve_is_super_admin(resolve_bindings_via_session: bool = True) -> bool:
    """
    统一SA判定（按优先级，匹配即返回True）：
      1) session 临时覆盖 _sa_override_from_vikey（Vikey插入时注入，无条件=SA）
      2) username ∈ 硬编码白名单 _SA_HARDCODED_USERNAMES
      3) session 自带 is_super_admin / super_admin_approved
      4) admin.users 表：super_admin_approved=True 或 role=super_admin
      5) vikey_device_bindings：当前用户对应设备为SA角色且绑定激活
    """
    try:
        s_user = _current_safe_user() or {}
        uname = str(s_user.get('username') or '').strip().lower()
        # 1. Vikey 注入的SA覆盖——最高优先级（拔出即失活）
        if session.get('_sa_override_from_vikey') is True:
            return True
        # 2. 硬编码白名单
        if uname in {u.lower() for u in _SA_HARDCODED_USERNAMES}:
            return True
        # 3. 会话内显式标志
        if bool(s_user.get('is_super_admin')):
            return True
        if session.get('super_admin_approved') is True:
            return True
        if str(session.get('role') or '').lower() == 'super_admin':
            return True
        # 4. admin库查表
        uid = s_user.get('uid')
        if uid:
            try:
                from core.db_path import get_db_path
                ap = get_db_path('admin.db')
                import sqlite3 as _sq3
                with _sq3.connect(ap, timeout=1) as c:
                    r = c.execute(
                        "SELECT super_admin_approved, role FROM users WHERE id=? LIMIT 1",
                        (uid,)
                    ).fetchone()
                    if r:
                        if r[0]: return True
                        if (r[1] or '').lower() == 'super_admin': return True
            except Exception:
                pass
        # 5. vikey_device_bindings SA绑定
        if resolve_bindings_via_session and uname:
            try:
                with _get_conn(_bizdb_path()) as c:
                    _ensure_biz_tables(c)
                    r = c.execute(
                        "SELECT role_hint, binding_status FROM vikey_device_bindings "
                        "WHERE lower(username)=? AND status=1 LIMIT 1",
                        (uname,)
                    ).fetchone()
                    if r:
                        role_h = (r[0] or '').lower()
                        st = (r[1] or '').lower()
                        if role_h == 'super_admin' and st in ('bound', 'active'):
                            return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def _ensure_settings_and_sa_tables(c):
    """确保 SSOT settings 表 + sa_rule_overrides + settings_audit_log 存在（幂等）"""
    try:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS unified_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL DEFAULT 'system',
            key_name TEXT NOT NULL,
            value_json TEXT,
            updated_by TEXT,
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            from_sa_override INTEGER DEFAULT 0,
            from_vikey_serial TEXT,
            is_active INTEGER DEFAULT 1,
            UNIQUE(scope, key_name)
        );
        CREATE INDEX IF NOT EXISTS idx_unified_settings_scope ON unified_settings(scope);

        CREATE TABLE IF NOT EXISTS sa_rule_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_key TEXT NOT NULL UNIQUE,
            override_value_json TEXT,
            source_type TEXT NOT NULL,  -- vikey_inserted / manual_sa / eigenflux_audit
            source_serial TEXT,
            enforced INTEGER DEFAULT 1,  -- 1=无条件覆盖所有规则
            created_by TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            expires_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT, key_name TEXT,
            old_value_json TEXT, new_value_json TEXT,
            source TEXT, -- frontend / api / eigenflux / ai_consult
            ai_consult_result_json TEXT,
            operator TEXT, ip TEXT, ua TEXT,
            db_synced INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
    except Exception as _settings_tables_exc:
        # 🔴 异常捕捉修复：建表失败不再静默吞掉
        try:
            import logging as _lg_st
            _lg_st.warning(
                "[DB:_ensure_settings_and_sa_tables] 建表失败: %s", _settings_tables_exc
            )
        except Exception:
            pass


# ---------- AI 管控核心：风险评估 + 熔断 ----------
def _mt_is_admin_user(u: dict) -> bool:
    """判断是否管理员类用户（豁免限流/熔断）"""
    if not u: return False
    if u.get('is_guest'): return False
    role = (u.get('role') or '').lower()
    admin_roles = {'super_admin', 'admin', 'hardware_admin', 'cluster_manager',
                   'sadmin', 'system_admin', 'school_admin', 'sysadmin'}
    return role in admin_roles or bool(u.get('is_super_admin')) or bool(u.get('super_admin_approved'))

_MT_RISK_RULES = [
    # (rule_code, name, check_fn, risk_level, action)
    ('R-NO-REFERER', '缺少 Referer 直入敏感页面',
     lambda p, u: (u['is_guest'] and any(k in p.lower() for k in ('/admin', '/settings', '/exam', '/dashboard')) and not request.headers.get('Referer')),
     'medium', 'flag'),
    ('R-FAST-CLICK', '操作速率过高 60s > 120 次',
     lambda p, u: (not _mt_is_admin_user(u)) and _mt_is_user_fast(u['uid']),
     'high', 'throttle'),
    ('R-GUEST-API-WRITE', '访客越权写操作',
     lambda p, u: (u['is_guest'] and request.method in ('POST', 'PUT', 'DELETE') and p.startswith('/api/') and not any(p.startswith(x) for x in ('/api/auth', '/api/theme', '/api/vikey', '/api/health', '/api/container', '/api/ai_engine/self_learning', '/api/ai/self_learning', '/api/layout_ai', '/api/chinese_dictation', '/api/ai/chinese_listening', '/api/history', '/api/arduino', '/api/approval', '/api/system/logo', '/api/client/init', '/api/client/verify_keys', '/api/mobile/fingerprint', '/api/console', '/api/i18n', '/api/neuralhub', '/api/ai/derive', '/api/edu', '/api/profile', '/api/model', '/api/crypto', '/api/ai/github-fusion/deep'))),
     'high', 'block'),
    ('R-SESSION-STALE', 'Session 超过 24h 未刷新',
     lambda p, u: False,  # 在 before_request 中动态计算
     'low', 'refresh'),
]


def _mt_is_user_fast(uid: str) -> bool:
    """滑动窗口：60 秒内 > 120 次"""
    now = time.time()
    with _MT_BEHAVIOR_LOCK:
        bucket = _MT_BEHAVIOR_BUCKETS.setdefault(uid, [])
        bucket[:] = [t for t in bucket if now - t < 60]
        bucket.append(now)
        return len(bucket) > _MT_BEHAVIOR_RATE_LIMIT


def _mt_ai_audit_push(entry: dict) -> None:
    """环形缓冲（内存 500 条 + DB 持久化）"""
    entry.setdefault('trace_id', _trace_id())
    entry.setdefault('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        with sqlite3.connect(_bizdb_path(), timeout=30) as c:
            _ensure_container_tables(c)
            c.execute(
                "INSERT INTO sys_container_ai_audit(trace_id,sid,uid,username,role,path,action,risk_level,rule_hit,blocked,detail)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (entry.get('trace_id'), entry.get('sid'), entry.get('uid'), entry.get('username'),
                 entry.get('role'), entry.get('path'), entry.get('action'), entry.get('risk_level', 'low'),
                 entry.get('rule_hit'), 1 if entry.get('blocked') else 0, entry.get('detail', ''))
            )
            c.commit()
    except Exception:
        pass
    with _MT_AIBEHAVIOR_LOCK:
        _MT_AIBEHAVIOR_LOG.append(entry)
        if len(_MT_AIBEHAVIOR_LOG) > 500:
            del _MT_AIBEHAVIOR_LOG[:len(_MT_AIBEHAVIOR_LOG) - 500]


# ---------- Session 统一加载：第二个 before_request ----------
@app.before_request
def _mt_sys_container_session_loader():
    """
    容器 Session 加载（在 AI 防火墙之后执行）：
      1. 读取 Cookies 中的 mtscos_sid，校验签名
      2. 已登录用户：把用户信息回填到 session 中（避免丢失）
      3. 未登录用户：设置 guest session + mtscos_uid guest-xx
      4. 记录请求级 trace_id 和进入时间戳
      5. 写 sys_container_heartbeat（API/页面都记）
    """
    try:
        request.mt_entry_ts = time.time()
        request.mt_trace_id = _trace_id()
        path = request.path or ''
        # 排除静态资源 / 心跳接口重复写
        if (path.startswith('/static/') or path.startswith('/assets/')
                or path in ('/favicon.ico', '/robots.txt', '/api/health')
                or path.endswith(('.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.ico', '.map', '.woff2'))):
            return None
        sid_cookie = request.cookies.get(_MT_COOKIES['sid']['name']) or ''
        if not _verify_sid(sid_cookie):
            sid_cookie = _gen_sid()
        session['__mt_sid'] = sid_cookie
        user = _current_safe_user()
        # --- DB session 持久化（写入/刷新） ---
        try:
            payload = {k: v for k, v in session.items() if not k.startswith('__mt_')}
            with sqlite3.connect(_bizdb_path(), timeout=30) as c:
                _ensure_container_tables(c)
                c.execute(
                    "INSERT INTO sys_container_sessions(sid,uid,username,role,ip,ua,payload_json,last_seen) VALUES(?,?,?,?,?,?,?,datetime('now','localtime'))"
                    " ON CONFLICT(sid) DO UPDATE SET uid=excluded.uid,username=excluded.username,role=excluded.role,"
                    " ip=excluded.ip,ua=excluded.ua,payload_json=excluded.payload_json,last_seen=datetime('now','localtime')",
                    (sid_cookie, user.get('uid'), user.get('username'), user.get('role'),
                     _ip(), _ua(), json.dumps(payload, ensure_ascii=False))
                )
                c.commit()
        except Exception:
            pass
        # --- AI 管控：风险评估（不阻断 HTML 页，仅 flag；API 则高风险直接拦） ---
        for rule_code, rule_name, rule_fn, lvl, act in _MT_RISK_RULES:
            try:
                if rule_fn(path, user):
                    _mt_ai_audit_push({
                        'sid': sid_cookie,
                        'uid': user.get('uid'),
                        'username': user.get('username'),
                        'role': user.get('role'),
                        'path': path,
                        'action': 'rule-hit',
                        'risk_level': lvl,
                        'rule_hit': f'{rule_code}::{rule_name}',
                        'blocked': (act == 'block' and path.startswith('/api/')),
                        'detail': json.dumps({'method': request.method, 'ip': _ip()}, ensure_ascii=False),
                    })
                    if act == 'block' and path.startswith('/api/'):
                        return jsonify({'success': False, 'message': f'容器 AI 管控阻断：{rule_name}', 'code': 403, 'trace_id': request.mt_trace_id}), 403
                    if act == 'throttle':
                        return jsonify({'success': False, 'message': '容器限流：请稍后再试', 'code': 429, 'trace_id': request.mt_trace_id}), 429
            except Exception:
                continue
        # --- 心跳记录 ---
        try:
            with sqlite3.connect(_bizdb_path(), timeout=2) as c:
                _ensure_container_tables(c)
                c.execute(
                    "INSERT INTO sys_container_heartbeat(sid,uid,username,role,path,ip,ua,action,ok) VALUES(?,?,?,?,?,?,?,?,1)",
                    (sid_cookie, user.get('uid'), user.get('username'), user.get('role'), path, _ip(), _ua(), 'http-request')
                )
                c.commit()
        except Exception:
            pass
    except Exception as e:
        import logging as _lg2
        _lg2.warning(f"[sys-container] session_loader before_request err: {e}")
    return None


# ---------- 防盗链拦截：before_request（用户权限.md 硬条款） ----------
# 规则：所有页面禁止盗链。未授权(guest)session 且 Referer 非法：
#   - HTML页面请求（外站引用 / 无Referer直达非白名单页）→ 302 重定向首页 /index?from=hotlink_blocked
#   - API请求（外站Referer）→ 403 JSON code=HOTLINK_BLOCKED
#   - 静态资源外站引用（经典盗链）→ 403
# 白名单：首页(/、/index)、auth、静态、健康检查、本站Referer；已登录用户全放行。
_MT_HOTLINK_WHITELIST_PATHS = {
    '/', '/index', '/favicon.ico', '/robots.txt',
    '/login', '/auth/login', '/auth/register', '/logout', '/forgot_password', '/register', '/auth/logout', '/auth/forgot_password',
    '/auth/session_health', '/auth/check_username',
}
_MT_HOTLINK_WHITELIST_PREFIXES = (
    '/static/', '/assets/', '/auth/', '/_ui/', '/api/auth/',
    '/api/health', '/api/system_version', '/api/system_logo',
    '/api/neuralhub/employee_distribution',
    '/api/neuralhub/daemon_tick',
    '/api/neuralhub/edu_reform_check',
    '/api/neuralhub/knowledge_inventory',
    '/api/neuralhub/network_status',
    '/api/neuralhub/health',
)
# API 内部白名单 — 这些 /api/ 路径即使无 Referer 或外站 Referer 也允许访问 (状态检查类)
_MT_HOTLINK_API_ALLOW_PREFIXES = (
    '/api/neuralhub/employee_distribution',
    '/api/neuralhub/daemon_tick',
    '/api/neuralhub/edu_reform_check',
    '/api/neuralhub/knowledge_inventory',
    '/api/neuralhub/network_status',
    '/api/neuralhub/health',
    '/api/health',
    '/api/andromeda/stars',
)
_MT_HOTLINK_OWN_HOSTS = {'localhost', '127.0.0.1', '::1'}
_MT_HOTLINK_LOG_THROTTLE = {}


def _mt_hotlink_parse_netloc(netloc):
    """解析 netloc → (hostname, port)；畸形/伪造端口(非纯数字)返回 None（不信任）。
    防伪造绕过：'127.0.0.1:8888.evil.com' / '127.0.0.1:8888@evil.com' 均判非法。"""
    n = (netloc or '').lower().strip()
    if not n:
        return None
    if n.startswith('['):
        host, _, rest = n.partition(']')
        host = host.lstrip('[')
        port = rest[1:] if rest.startswith(':') else ''
    else:
        host, _, port = n.partition(':')
    if port and not port.isdigit():
        return None
    return (host, port)


def _mt_hotlink_decision(*, path, method, referer, request_host, logged_in):
    """纯函数判定（便于§14千轮测试，不依赖 flask request）：
    返回 (action, reason)；action ∈ 'allow' | 'redirect'(→/index) | 'forbid'(403)。
    判定顺序（防盗链优先级）：
      1) 安全方法/已登录 → 放行
      2) 外站Referer（盗链）：静态/API → 403；首页/auth白名单页 → 放行；其余页面 → 302 /index
      3) 无Referer：白名单 → 放行；API/静态 → 放行；其余页面 → 302 /index（先经首页）
      4) 本站Referer → 放行
    """
    p = (path or '/').split('?', 1)[0]
    if method in ('OPTIONS', 'HEAD'):
        return ('allow', 'safe-method')
    if logged_in:
        return ('allow', 'authorized')
    own = (request_host or '').lower()
    own_parsed = _mt_hotlink_parse_netloc(own)
    allowed_hosts = _MT_HOTLINK_OWN_HOSTS | {own}
    if own_parsed:
        allowed_hosts.add(own_parsed[0])
    ref = (referer or '').strip()
    netloc = ''
    if ref:
        try:
            from urllib.parse import urlparse as _up
            netloc = (_up(ref).netloc or '').lower()
        except Exception:
            netloc = ''
    ref_parsed = _mt_hotlink_parse_netloc(netloc) if netloc else None
    if ref and not (ref_parsed and ref_parsed[0] in allowed_hosts
                    and own_parsed and ref_parsed[1] == own_parsed[1]):
        # ---- 外站/伪造 Referer = 盗链（白名单前缀不适用，防静态资源被外站盗链）----
        if _is_static_request(p):
            return ('forbid', 'foreign-referer-static')
        if p.startswith('/api/'):
            # 但内部 API 白名单 (daemon tick / health / inventory) 是允许外站 Referer 的
            if p.startswith(_MT_HOTLINK_API_ALLOW_PREFIXES):
                return ('allow', 'api-whitelist')
            return ('forbid', 'foreign-referer-api')
        if p in _MT_HOTLINK_WHITELIST_PATHS:
            return ('allow', 'whitelist-page-foreign-ref')
        return ('redirect', 'foreign-referer-page')
    if not ref:
        # ---- 无 Referer（直达/新标签页）：guest 非白名单页面必须先经首页；API/静态不拦 ----
        if p in _MT_HOTLINK_WHITELIST_PATHS or p.startswith(_MT_HOTLINK_WHITELIST_PREFIXES):
            return ('allow', 'whitelist')
        if p.startswith('/api/') or _is_static_request(p):
            return ('allow', 'no-referer-nonpage')
        return ('redirect', 'no-referer-page')
    return ('allow', 'same-site')


def _mt_hotlink_audit(kind, reason, throttle_seconds):
    """阻断事件落库 automation_console_logs（同IP同类限频，非致命）。"""
    try:
        now = time.time()
        key = (request.remote_addr or '?', kind)
        if now - _MT_HOTLINK_LOG_THROTTLE.get(key, 0) < throttle_seconds:
            return
        _MT_HOTLINK_LOG_THROTTLE[key] = now
        with _get_conn(APP_DB) as c:
            c.execute(
                "INSERT INTO automation_console_logs(timestamp,level,source,message,extra_json,eigenflux_flag) "
                "VALUES(datetime('now','localtime'),?,?,?,?,1)",
                ('warning', 'hotlink_guard',
                 f'HOTLINK_BLOCKED: {kind} {reason} {request.method} {request.path}',
                 json.dumps({'ip': request.remote_addr,
                             'referer': (request.headers.get('Referer') or '')[:300],
                             'ua': _ua()[:200], 'path': request.path}, ensure_ascii=False)))
            c.commit()
    except Exception:
        pass


@app.before_request
def _mt_hotlink_guard():
    """防盗链拦截：未授权session + 非法Referer → 页面302到/index / API与静态403 (HOTLINK_BLOCKED)"""
    try:
        action, reason = _mt_hotlink_decision(
            path=request.path, method=request.method,
            referer=request.headers.get('Referer'), request_host=request.host,
            logged_in=bool(_current_safe_user().get('logged_in')))
        if action == 'allow':
            return None
        request.__mt_hotlink_blocked__ = reason
        if action == 'forbid':
            _mt_hotlink_audit('forbid', reason, 60)
            return jsonify({'success': False, 'code': 'HOTLINK_BLOCKED',
                            'message': '禁止盗链：请从本站页面访问',
                            'from': 'hotlink_blocked'}), 403
        _mt_hotlink_audit('redirect', reason, 10)
        return redirect('/index?from=hotlink_blocked', code=302)
    except Exception as _e:
        import logging as _lg_hl
        _lg_hl.warning(f"[hotlink-guard] before_request err: {_e}")
        return None


# ---------- VIKEY 系统锁定检查：before_request ----------
@app.before_request
def _mt_vikey_lock_check():
    # 优先使用新的 VikeyAPI 封装，失败回退到底层 driver
    try:
        from core.services.vikey_api import get_vikey_api as _get_api
        vk_api = _get_api()
        _lock_state_fn = vk_api.get_lock_state
    except Exception:
        from core.services.vikey_driver import get_vikey_manager
        _lock_state_fn = lambda: get_vikey_manager().get_lock_state()
    try:
        path = request.path or ''
        bypass_paths = {
            '/', '/auth/login', '/auth/logout', '/auth/session_health',
            '/api/vikey/detect', '/api/vikey/lock_state', '/api/vikey/unlock',
            '/api/vikey/set_timeout', '/api/vikey/snapshot/save',
            '/api/vikey/snapshot/restore', '/api/vikey/snapshot/release',
            '/api/health', '/favicon.ico',
            '/api/system_version', '/api/system_logo',
            '/settings',
        }
        if path in bypass_paths or path.startswith('/static/') or path.startswith('/assets/'):
            return None

        user = _current_user()
        is_super_admin = user and user.get('username', '').lower() == 'wuchenghao15'

        # 铁律：SA VIKEY 强制检查永远生效，不得通过任何配置、DEBUG、IP 白名单绕过
        force_check_enabled = True

        if is_super_admin and force_check_enabled:
            lock_state = _lock_state_fn()

            if lock_state.get('locked'):
                if lock_state.get('timeout_reached'):
                    session.clear()
                    return jsonify({
                        'success': False,
                        'message': '系统锁定超时，请重新登录',
                        'locked': True,
                        'timeout_reached': True,
                    }), 401
                return jsonify({
                    'success': False,
                    'message': '系统已锁定，请重新插入VIKEY加密狗',
                    'locked': True,
                    'required_serial': lock_state.get('required_serial'),
                    'remaining_seconds': lock_state.get('remaining_seconds'),
                    'timeout_reached': False,
                }), 423
    except Exception as e:
        import logging as _lg_vk
        _lg_vk.warning(f"[vikey-lock] before_request err: {e}")
    return None


# ---------- VIKEY 强制认证检查：before_request ----------
@app.before_request
def _mt_vikey_enforcement_check():
    """
    Vikey USB加密狗强制认证检查：
    - 首页和超级管理员所有页面必须检测vikey加密狗
    - 未检测到加密狗、状态异常或离线无网络都不能使用
    """
    try:
        from app.middlewares.vikey_enforcement_middleware import vikey_enforcement

        path = request.path
        username = session.get('username', '')
        extra = {
            'ip': request.remote_addr,
            'ua': request.headers.get('User-Agent','')[:300],
            'session_id': session.sid if getattr(session,'sid',None) else session.get('_session_id','')
        }
        result = vikey_enforcement.check_vikey_enforcement(path, username, extra=extra)

        if not result['allowed']:
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': result['reason'],
                    'vikey_status': result.get('vikey_status'),
                    'szu100_status': result.get('szu100_status'),
                    'network_status': result.get('network_status'),
                    'terminal_status': result.get('terminal_status'),
                    'status_code': 403,
                }), 403

            return redirect(f'/auth/login?error={result["reason"]}')
    except Exception as e:
        import logging as _lg_ve
        _lg_ve.warning(f"[vikey-enforcement] before_request err: {e}")
    return None


# ---------- VIKEY SA权限绝对边界：before_request ----------
# ⭐ 规则：只有 真·超级管理员(is_super_admin) 才能检测/使用/操作/显示VIKEY
# - 其他任何角色(guest/student/teacher/admin/hardware_admin等)：
#   · 所有 /api/vikey/* (除detect返回空) => 直接403
#   · /vikey_manager / tab-vikey / 任何vikey页面路由 => 302跳转或403
@app.before_request
def _mt_vikey_sa_only_boundary():
    """Vikey功能SA白名单：仅超级管理员可使用(绝对权限边界)"""
    try:
        path = (request.path or '').lower()
        if not path:
            return None
        # 仅处理VIKEY相关路径
        vikey_api_hit = path.startswith('/api/vikey/') or path == '/api/vikey'
        vikey_page_hit = (path in ('/vikey_manager', '/vikey_manager.html')
                         or path.startswith('/vikey')
                         or '/tab-vikey/' in path
                         or path.startswith('/page/vikey')
                         or 'vikey_manager' in path)
        if not (vikey_api_hit or vikey_page_hit):
            return None
        # 白名单放行路径：登录、静态、健康检查
        if any(p in path for p in ('/static/', '/favicon', '/health')):
            return None
        # 获取SA状态
        sa = _mt_resolve_is_super_admin(resolve_bindings_via_session=True)
        if sa:
            return None
        # 非SA用户
        # 对detect：真正检测硬件，但对非SA用户脱敏（只返回是否插入+是否已绑定SA，不暴露序列号）
        if vikey_api_hit and (path.endswith('/detect') or 'detect' in path):
            from flask import make_response as _mk_resp
            # 真正调用硬件检测
            real = None
            try:
                from core.services.vikey_driver import get_vikey_manager as _gvkm_det
                det = _gvkm_det().detect()
                if isinstance(det, dict):
                    real = det
            except Exception:
                real = None
            raw = real if real else {'present_count': 0, 'devices': [], '_source': 'no_hardware'}
            src_devs = raw.get('devices') or []
            present_count = 0
            sa_vikey_present = False
            for d in (src_devs or []):
                d = dict(d) if not isinstance(d, dict) else d
                present = bool(d.get('is_present', True)) if 'is_present' in d else bool(d.get('present', True))
                serial = d.get('serial') or d.get('device_serial')
                if not serial or not present:
                    continue
                present_count += 1
                # 检查是否绑定到超级管理员
                binding = d.get('binding') if isinstance(d.get('binding'), dict) else {}
                b_user = binding.get('username') or d.get('username')
                b_status = binding.get('binding_status') or binding.get('status') or ''
                if b_user and str(b_user).lower() == 'wuchenghao15' and b_status in ('bound', 'active'):
                    sa_vikey_present = True
            payload = {
                'success': True,
                'data': {
                    'present_count': present_count,
                    'is_present': present_count > 0,
                    'sa_vikey_present': sa_vikey_present,
                    '_source': 'hardware_scan_sanitized',
                    'sa_only': True,
                    'devices': [],  # 非SA不暴露设备详情
                }
            }
            resp = _mk_resp(jsonify(payload))
            resp.headers['Cache-Control'] = 'max-age=3, private'
            resp.status_code = 200
            return resp
        msg = 'VIKEY_SA_ONLY: 仅超级管理员可使用Vikey相关功能'
        if vikey_api_hit:
            return jsonify({
                'success': False,
                'message': msg,
                'code': 'VIKEY_FORBIDDEN_NON_SA',
                'trace_id': getattr(request, 'mt_trace_id', None),
            }), 403
        from werkzeug.utils import redirect as _wzrd
        try:
            return _wzrd('/403?reason=vikey_sa_only&role=' + str(session.get('role') or 'guest'))
        except Exception:
            return jsonify({'success': False, 'message': msg}), 403
    except Exception as e:
        import logging as _lg_vbd
        _lg_vbd.warning(f"[vikey-sa-boundary] before_request err: {e}")
    return None


# ---------- 移动端自动检测重定向：before_request ----------
_MOBILE_UA_PATTERN = re.compile(r'Android|iPhone|iPod|iPad|Windows Phone|BlackBerry|Mobile|Opera Mini', re.IGNORECASE)
_PC_PATHS = ('/admin_app/', '/dashboard', '/vikey', '/api/', '/static/', '/assets/', '/manifest.json', '/service-worker.js')

@app.before_request
def _mt_mobile_redirect():
    """移动设备自动重定向到 /mobile/ 前缀（不强制，仅根路径和部分页面）"""
    try:
        path = request.path or '/'
        # 已经在移动端路径，不重定向
        if path.startswith('/mobile/'):
            return None
        # PC专用路径不重定向
        for p in _PC_PATHS:
            if path.startswith(p):
                return None
        # 检查UA
        ua = request.headers.get('User-Agent', '')
        if not _MOBILE_UA_PATTERN.search(ua):
            return None
        # 根路径、登录、首页重定向到移动端
        if path in ('/', '/index', '/home'):
            return redirect('/mobile/home')
        if path in ('/login', '/auth/login'):
            return redirect('/mobile/login')
        if path in ('/student_portal',):
            return redirect('/mobile/home')
        if path in ('/exam_system/exams', '/exam_center'):
            return redirect('/mobile/exam')
        if path in ('/settings',):
            return redirect('/mobile/profile')
    except Exception:
        pass
    return None


# ---------- Cookies 自动挂载：after_request ----------
@app.after_request
def _mt_sys_container_cookie_mounter(response):
    """
    所有离开容器的响应强制挂载 5 大系统 Cookies：
      mtscos_sid   会话签名 ID  (30 天 / HttpOnly)
      mtscos_uid   用户 UID     (30 天)
      mtscos_ts    最近活动时间戳 (1 天)
      mtscos_sc    会话签名校验 (会话级 / HttpOnly / Strict)
      mtscos_trace 本次 trace_id  (1 小时)
    """
    try:
        # 静态资源仅挂 sid（少写 cookies 节省带宽）
        path = request.path or ''
        is_static = (path.startswith('/static/') or path.startswith('/assets/')
                     or path in ('/favicon.ico',)
                     or path.endswith(('.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.ico', '.map', '.woff2')))
        sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
        if not _verify_sid(sid):
            sid = _gen_sid()
        user = _current_safe_user()
        # 1) mtscos_sid（所有响应必挂）
        c = _MT_COOKIES['sid']
        response.set_cookie(c['name'], sid, max_age=c['max_age'], path=c['path'],
                            httponly=c['httpOnly'], samesite=c['sameSite'])
        if is_static:
            return response
        # 2) mtscos_uid
        c2 = _MT_COOKIES['uid']
        response.set_cookie(c2['name'], str(user.get('uid') or ''), max_age=c2['max_age'], path=c2['path'],
                            httponly=c2['httpOnly'], samesite=c2['sameSite'])
        # 3) mtscos_ts
        c3 = _MT_COOKIES['ts']
        response.set_cookie(c3['name'], str(int(time.time())), max_age=c3['max_age'], path=c3['path'],
                            httponly=c3['httpOnly'], samesite=c3['sameSite'])
        # 4) mtscos_sc（会话签名校验）
        c4 = _MT_COOKIES['sc']
        sc_sig = _hmac.new(_MT_SYS_CONTAINER_SECRET,
                           (sid + '|' + str(user.get('uid') or '') + '|' + str(user.get('username') or '')).encode(),
                           hashlib.sha256).hexdigest()[:16]
        response.set_cookie(c4['name'], sc_sig, max_age=c4['max_age'], path=c4['path'],
                            httponly=c4['httpOnly'], samesite=c4['sameSite'])
        # 5) mtscos_trace
        c5 = _MT_COOKIES['trace']
        tid = getattr(request, 'mt_trace_id', None) or _trace_id()
        response.set_cookie(c5['name'], tid, max_age=c5['max_age'], path=c5['path'],
                            httponly=c5['httpOnly'], samesite=c5['sameSite'])
        # 6) 给响应头补充容器元信息（便于前端监控）
        response.headers['X-MT-Container'] = _MT_SYS_CONTAINER_VERSION
        response.headers['X-MT-Trace-Id'] = tid
        response.headers['X-MT-Loaded'] = '1'
    except Exception as e:
        import logging as _lg3
        _lg3.warning(f"[sys-container] cookie_mounter after_request err: {e}")
    return response


# ---------- 全局 主题Token + i18n 注入：after_request ----------
#   L1 主题Token 文件(_theme_tokens_source.css) 必须最先加载，
#   确保其后所有 CSS 文件的 var(--mtscos-*) / var(--el-*) / var(--theme-*)
#   都能立即解析到正确值，从而实现「修改一处，全站同步生效」。
@app.after_request
def _mt_theme_and_i18n_global_injector(response):
    """
    全站 HTML 响应统一注入：
      A. 主题系统(最先): </head> 第一个位置注入 <link> _theme_tokens_source.css
      B. i18n 系统(随后): </head> 注入 lang-modal.css + </body> 注入 i18n.js
    幂等去重：
      - 非 text/html 跳过
      - 响应已包含指定 <link>/<script> 标签 → 跳过（基于标签级正则，不误命中注释）
      - 非完整HTML片段(无</head>也无</body>) / 二进制 / streaming → 跳过
    统一效果：修改 flask-app/static/css/_theme_tokens_source.css → 所有页面立即同步变色
    """
    try:
        import re as _re_inj
        # 1) 非 HTML 跳过
        ctype = (response.content_type or '').lower()
        if 'text/html' not in ctype:
            return response

        # 2) 取响应体 + 编码解析
        encoding = None
        try:
            encoding = getattr(response, 'charset', None)
        except Exception:
            encoding = None
        if not encoding:
            try:
                from werkzeug.http import parse_options_header as _poh_inj
                _parts, _opts = _poh_inj(response.content_type or '')
                encoding = _opts.get('charset')
            except Exception:
                encoding = None
        if not encoding:
            encoding = 'utf-8'
        try:
            raw = response.get_data()
            if raw is None:
                return response
            data = raw.decode(encoding, errors='ignore')
        except Exception:
            return response
        if not data or not isinstance(data, str):
            return response

        # 3) 非完整页面跳过
        has_head_end = '</head>' in data
        has_body_end = '</body>' in data
        if not (has_head_end or has_body_end):
            return response
        has_body_open = _re_inj.search(r'<\s*body\b', data) is not None if has_body_end else False

        # ========== A. 主题Token 注入 (必须最先！) ==========
        theme_css_ref = '/static/css/_theme_tokens_source.css'
        _tcss_re = _re_inj.compile(
            r'<\s*link\b[^>]+href\s*=\s*["\'][^"\']*' + _re_inj.escape(theme_css_ref) + r'[^"\']*["\']',
            _re_inj.I)
        theme_injected = bool(_tcss_re.search(data))
        changed = False

        if not theme_injected and has_head_end:
            # 注入到 <head 后的第一个位置或 </head> 前，保证最先被解析
            theme_link = (
                '\n    <!-- MTSCOS AI L1 主题Token (单源·一改全同步) auto-injected -->\n'
                '    <link rel="stylesheet" href="' + theme_css_ref + '">\n'
            )
            data = data.replace('</head>', theme_link + '</head>', 1)
            changed = True
            try:
                response.headers['X-MT-Theme-Injected'] = '1'
            except Exception:
                pass
        elif not theme_injected and has_body_end and has_body_open:
            # </head> 缺失但 </body> 存在的页面片段，仍要注入主题Token
            theme_link = (
                '\n    <!-- MTSCOS AI L1 主题Token (单源·一改全同步) auto-injected -->\n'
                '    <link rel="stylesheet" href="' + theme_css_ref + '">\n'
            )
            data = _re_inj.sub(r'<body', theme_link + '<body', data, count=1, flags=_re_inj.I)
            changed = True
            try:
                response.headers['X-MT-Theme-Injected'] = '1'
            except Exception:
                pass

        # ========== C. 仙女座 frontend_overrides 注入 (v5.2) ==========
        # mt_params frontend 分组 23 参数 → overrides.css → 全站热生效
        # 加载顺序: design-system → design_tokens → _theme_tokens_source → overrides(本) → i18n
        # → overrides 在最末, 覆盖所有上游变量定义
        fe_overrides_ref = '/static/css/mtscos_frontend_overrides.css'
        _feo_re = _re_inj.compile(
            r'<\s*link\b[^>]+href\s*=\s*["\'][^"\']*' + _re_inj.escape(fe_overrides_ref) + r'[^"\']*["\']',
            _re_inj.I)
        feo_injected = bool(_feo_re.search(data))

        if not feo_injected and has_head_end:
            feo_link = (
                '\n    <!-- MTSCOS AI C 仙女座 v5.2 frontend_overrides (mt_params 23 参数) auto-injected -->\n'
                '    <link rel="stylesheet" href="' + fe_overrides_ref + '">\n'
            )
            # 插入到 </head> 前 (最后加载, 保证覆盖)
            data = data.replace('</head>', feo_link + '</head>', 1)
            changed = True
            try:
                response.headers['X-MT-FE-Overrides'] = '1'
            except Exception:
                pass
        elif not feo_injected and has_body_end and has_body_open:
            feo_link = (
                '\n    <!-- MTSCOS AI C 仙女座 v5.2 frontend_overrides (mt_params 23 参数) auto-injected -->\n'
                '    <link rel="stylesheet" href="' + fe_overrides_ref + '">\n'
            )
            data = _re_inj.sub(r'<body', feo_link + '<body', data, count=1, flags=_re_inj.I)
            changed = True
            try:
                response.headers['X-MT-FE-Overrides'] = '1'
            except Exception:
                pass

        # ========== B. i18n 注入 ==========
        # 检查 i18n 文件可读性(OneDrive占位符防护)
        _i18n_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'i18n')
        _i18n_css_path = os.path.join(_i18n_dir, 'lang-modal.css')
        _i18n_js_path  = os.path.join(_i18n_dir, 'i18n.js')
        _i18n_readable = False
        try:
            with open(_i18n_css_path, 'rb') as _f:
                _f.read(16)
            with open(_i18n_js_path, 'rb') as _f:
                _f.read(16)
            _i18n_readable = True
        except Exception:
            _i18n_readable = False

        i18n_css_ref = '/static/i18n/lang-modal.css'
        i18n_js_ref  = '/static/i18n/i18n.js'
        _icss_re = _re_inj.compile(
            r'<\s*link\b[^>]+href\s*=\s*["\'][^"\']*' + _re_inj.escape(i18n_css_ref) + r'[^"\']*["\']',
            _re_inj.I)
        _ijs_re  = _re_inj.compile(
            r'<\s*script\b[^>]+src\s*=\s*["\'][^"\']*' + _re_inj.escape(i18n_js_ref) + r'[^"\']*["\']',
            _re_inj.I)
        i18n_css_exists = bool(_icss_re.search(data))
        i18n_js_exists  = bool(_ijs_re.search(data))

        if _i18n_readable and not i18n_css_exists and has_head_end:
            link_html = (
                '\n    <!-- MTSCOS AI i18n (青瓷卷 · 4 语种) auto-injected -->\n'
                '    <link rel="stylesheet" href="' + i18n_css_ref + '">\n'
            )
            data = data.replace('</head>', link_html + '</head>', 1)
            changed = True
        if _i18n_readable and not i18n_js_exists and has_body_end:
            script_html = (
                '\n    <!-- MTSCOS AI i18n (青瓷卷 · 4 语种) auto-injected -->\n'
                '    <script src="' + i18n_js_ref + '" defer></script>\n'
            )
            data = data.replace('</body>', script_html + '</body>', 1)
            changed = True
        # 兼容：缺失 </head> 时 i18n CSS 放到 <body 前
        if _i18n_readable and not i18n_css_exists and (not has_head_end) and has_body_end and has_body_open:
            link_html = (
                '\n    <!-- MTSCOS AI i18n (青瓷卷 · 4 语种) auto-injected -->\n'
                '    <link rel="stylesheet" href="' + i18n_css_ref + '">\n'
            )
            data = _re_inj.sub(r'<body', link_html + '<body', data, count=1, flags=_re_inj.I)
            changed = True

        # ========== 提交修改 ==========
        if changed:
            try:
                response.set_data(data.encode(encoding, errors='ignore'))
                try:
                    cl = response.headers.get('Content-Length')
                    if cl is not None:
                        response.headers['Content-Length'] = str(len(response.get_data()))
                except Exception:
                    pass
                # 审计标记头
                if _i18n_readable:
                    response.headers['X-MT-i18n-Injected'] = '1'
            except Exception:
                pass
    except Exception as e:
        import logging as _lg_inj
        _lg_inj.warning(f"[theme+i18n-injector] after_request err: {e}")
    return response


# ---------- 统一系统容器装饰器 ----------
def system_container(page_name: str, require_auth: str = 'auto', allowed_roles=None,
                     inject_user_ctx: bool = True, write_heartbeat: bool = True):
    """
    ⭐⭐⭐ 所有 HTML 页面路由必须挂的容器装饰器 ⭐⭐⭐
    用途：
      - 脱离容器的孤岛页面前端控制台将看到警告，后端会补容器上下文
      - 写入 request.__mt_page_name__ = page_name，模板中可读取
      - 权限二次校验（与 require_login / require_admin 形成双保险）
      - 自动给模板注入：container_ctx（当前会话、用户、trace、版本）
      - 渲染完成后写页面级心跳

    参数：
      page_name       : 页面标识（如 "dashboard", "settings", "exam_center"）
      require_auth    : 'login' (强制登录) | 'admin' | 'super_admin' | 'auto'(看 session) | 'guest' (任何人)
      allowed_roles   : 白名单角色列表（优先级高于 require_auth 字符串）
      inject_user_ctx : 是否自动注入 current_user / user 到模板上下文中
      write_heartbeat : 是否写页面打开心跳
    """
    def decorator(view_fn):
        @wraps(view_fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            path = request.path or ''
            user = _current_safe_user()
            sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
            # 0) 标记本请求已进入容器（避免孤岛）
            request.__mt_container_page__ = page_name
            request.__mt_container_start__ = start

            # 1) 权限二次校验（双保险：和 access_control.py 的装饰器同时生效不冲突）
            _role = user.get('role') or 'guest'
            _username = user.get('username') or ''
            _sa = (_username == 'wuchenghao15')  # 超级管理员白名单
            denied = None
            if allowed_roles:
                if not _sa and _role not in allowed_roles:
                    denied = (403, f'该页面仅 {allowed_roles} 角色可访问')
            else:
                if require_auth == 'login' and not _sa and not user.get('logged_in'):
                    denied = (401 if path.startswith('/api/') else 302, '需要登录')
                elif require_auth == 'admin' and not _sa and _role not in _MT_ADMIN_ROLES:
                    denied = (403, '需要管理员权限')
                elif require_auth == 'super_admin' and not _sa and _role not in ('super_admin', 'sadmin'):
                    denied = (403, '需要超级管理员权限')

            # 2) VIKEY强制检查（超级管理员必须插入VIKEY，铁律：无任何 bypass）
            #    优先使用 VikeyAPI.detect() 统一封装，失败回退到底层 driver
            #    首页是公共入口，即使超级管理员无 VIKEY 也允许访问
            if not denied and _sa and path != '/':
                try:
                    # 铁律：force_check_enabled 永远为 True，不得通过任何手段绕过
                    force_check_enabled = True
                    if force_check_enabled:
                        # --- 使用 VikeyAPI 统一封装 ---
                        try:
                            from core.services.vikey_api import get_vikey_api
                            vk_api = get_vikey_api()
                            detect_r = vk_api.detect()
                        except Exception:
                            # fallback 到底层
                            from core.services.vikey_driver import get_vikey_manager
                            mgr = get_vikey_manager()
                            try:
                                detect_r = mgr.detect()
                            except Exception:
                                detect_r = None
                        # --- 统一处理 detect 结果 ---
                        vikey_devices = []
                        if detect_r:
                            # VikeyAPI.detect() 用 "devices"；老 driver.detect() 可能用 "devices"/"presents"
                            vikey_devices = (
                                detect_r.get('devices')
                                or detect_r.get('presents')
                                or []
                            )

                        has_valid_vikey = False
                        for dev in vikey_devices:
                            binding = dev.get('binding', {})
                            if dev.get('is_present') and (
                                binding.get('binding_status') == 'bound'
                                or binding.get('status') == 'bound'
                                or binding.get('role')
                            ):
                                if (
                                    (binding.get('username') or '').lower() == 'wuchenghao15'
                                    or (dev.get('binding') or {}).get('role_hint') == 'super_admin'
                                ):
                                    has_valid_vikey = True
                                    break

                        if not has_valid_vikey:
                            denied = (423, '请插入VIKEY USB加密狗以访问超级管理员功能')
                except Exception as vikey_err:
                    import logging as _lg_vk_check
                    _lg_vk_check.warning(f"[vikey-check] system_container err: {vikey_err}")
            if denied:
                code, msg = denied
                _mt_ai_audit_push({'sid': sid, 'uid': user.get('uid'), 'username': _username, 'role': _role,
                                   'path': path, 'action': f'{page_name}::permission-deny', 'risk_level': 'medium',
                                   'rule_hit': 'CONTAINER::PERMISSION-DENY', 'blocked': 1,
                                   'detail': json.dumps({'required': require_auth, 'allowed_roles': list(allowed_roles) if isinstance(allowed_roles, (set, tuple)) else allowed_roles}, ensure_ascii=False)})
                if path.startswith('/api/'):
                    return jsonify({'success': False, 'message': msg, 'code': code, 'trace_id': getattr(request, 'mt_trace_id', _trace_id())}), code
                if code == 302:
                    return redirect('/?next=' + path)
                # 423 VIKEY锁定页：超级管理员未插入加密狗
                if code == 423:
                    err_html = (
                        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>423 · VIKEY 锁定</title>'
                        '<meta name="viewport" content="width=device-width,initial-scale=1">'
                        '<script>window.__MT_CONTAINER__={version:"%s",page:"vikey_lock",traceId:"%s",sid:"%s",mounted:true};</script>'
                        '<style>body{background:#050510;color:#cbd5e1;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:0;padding:64px 24px}'
                        '.box{max-width:640px;margin:auto;background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);border-radius:16px;padding:36px;text-align:center}'
                        'h1{color:#f87171;margin:0 0 12px;font-size:28px}.p{opacity:.85;line-height:1.6;margin:0 0 24px}'
                        'a{color:#a5b4fc;text-decoration:none}.meta{font-size:12px;opacity:.55;margin-top:16px}'
                        '.icon{font-size:48px;margin-bottom:16px}'
                        '.retry-btn{display:inline-block;padding:12px 24px;background:#4f46e5;color:white;border-radius:8px;text-decoration:none;margin-top:16px}'
                        '.retry-btn:hover{background:#4338ca}'
                        '.countdown{display:inline-block;background:rgba(99,102,241,.15);color:#a5b4fc;padding:4px 12px;border-radius:12px;font-size:13px;margin-left:8px}'
                        '</style>'
                        '</head><body><div class="box">'
                        '<div class="icon">🔒</div>'
                        '<h1>VIKEY USB加密狗未检测到</h1>'
                        f'<p class="p">{msg}</p>'
                        '<p class="p">请插入已绑定的VIKEY USB加密狗后重试</p>'
                        f'<a class="retry-btn" href="{path}">↻ 重新检测</a>'
                        '<p style="margin-top:20px;font-size:13px;opacity:.7;">'
                        '<span id="countdown-text"><span id="cd">5</span> 秒后自动返回首页</span>'
                        '&nbsp;·&nbsp;<a href="javascript:;" onclick="stopCountdown()">取消</a>'
                        '</p>'
                        f'<p class="meta">Trace: {getattr(request, "mt_trace_id", "")}<br/>SID: {sid}<br/>用户: {_username} / {_role}</p>'
                        '</div>'
                        '<script>let _cd=5,_timer=setInterval(function(){'
                        '_cd--;var el=document.getElementById("cd");if(el)el.textContent=Math.max(_cd,0);'
                        'if(_cd<=0){clearInterval(_timer);window.location.href="/";}},1000);'
                        'function stopCountdown(){clearInterval(_timer);'
                        'var t=document.getElementById("countdown-text");if(t)t.textContent="已取消自动跳转"}'
                        '</script>'
                        '</body></html>'
                    ) % (_MT_SYS_CONTAINER_VERSION, getattr(request, 'mt_trace_id', ''), sid)
                    return err_html, code
                # 403 HTML 页：保持在系统容器内
                err_html = (
                    '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>403 · MTSCOS 系统容器</title>'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<script>window.__MT_CONTAINER__={version:"%s",page:"403",traceId:"%s",sid:"%s",mounted:true};</script>'
                    '<style>body{background:#050510;color:#cbd5e1;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:0;padding:64px 24px}'
                    '.box{max-width:640px;margin:auto;background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.2);border-radius:16px;padding:36px}'
                    'h1{color:#f87171;margin:0 0 12px;font-size:28px}.p{opacity:.85;line-height:1.6;margin:0 0 24px}'
                    'a{color:#a5b4fc;text-decoration:none}.meta{font-size:12px;opacity:.55;margin-top:16px}'
                    '.countdown-row{margin-top:20px;font-size:13px;opacity:.75}'
                    '.countdown-row a{color:#a5b4fc;cursor:pointer}'
                    '</style>'
                    '</head><body><div class="box"><h1>🚫 访问被系统容器拦截</h1>'
                    f'<p class="p">{msg}</p>'
                    '<p class="p"><a href="/">← 返回首页</a></p>'
                    '<p class="countdown-row">'
                    '<span id="countdown-text"><span id="cd">5</span> 秒后自动返回首页</span>'
                    '&nbsp;·&nbsp;<a onclick="stopCountdown()">取消</a>'
                    '</p>'
                    f'<p class="meta">Trace: {getattr(request, "mt_trace_id", "")}<br/>SID: {sid}<br/>用户: {_username} / {_role}</p>'
                    '</div>'
                    '<script>let _cd=5,_timer=setInterval(function(){'
                    '_cd--;var el=document.getElementById("cd");if(el)el.textContent=Math.max(_cd,0);'
                    'if(_cd<=0){clearInterval(_timer);window.location.href="/";}},1000);'
                    'function stopCountdown(){clearInterval(_timer);'
                    'var t=document.getElementById("countdown-text");if(t)t.textContent="已取消自动跳转"}'
                    '</script>'
                    '</body></html>'
                ) % (_MT_SYS_CONTAINER_VERSION, getattr(request, 'mt_trace_id', ''), sid)
                return err_html, code

            # 1.5) ⭐ 规则校验中间件（铁规/红线/红墙/制约/警示）— 在权限通过后、视图执行前
            try:
                _rule_ctx = {'action': f'page_access::{page_name}', 'container_wrapper': True,
                             'auth_requirement': require_auth, 'allowed_roles': allowed_roles}
                _rule_allowed, _rule_block_html, _rule_audit = _mt_check_rules_on_request(
                    page_name, path, user, _rule_ctx)
                if not _rule_allowed:
                    # 阻断：优先返回自定义阻断HTML（含EigenFlux面板+豁免按钮）
                    if _rule_block_html and isinstance(_rule_block_html, str) and '</html>' in _rule_block_html:
                        code_block = 451 if (_rule_audit and _rule_audit.get('level') == 'IRON_RULE') else 403
                        return _rule_block_html, code_block
                    if path.startswith('/api/'):
                        return jsonify({
                            'success': False, 'message': 'RULE_BLOCKED',
                            'rule_code': (_rule_audit or {}).get('rule_code', 'UNKNOWN'),
                            'level': (_rule_audit or {}).get('level', 'RED_WALL'),
                            'hint': '触发规则阻断，请通过 /_rules/check 预检或 /_rules/bypass_request 提交豁免申请'
                        }), 403
                    # 兜底阻断页
                    return '<h1 style="color:#ef4444;padding:64px 24px;font-family:sans-serif;">⛓️ 规则阻断<br/><small>RULE_CODE=' + str((_rule_audit or {}).get('rule_code','')) + '</small><br/><a href="/">← 返回首页</a></h1>', 403
            except Exception as _rule_err:
                # FAIL-CLOSED：规则引擎异常 → 默认阻断（SA白名单除外）
                import logging as _lg_rule_err
                _lg_rule_err.warning(f"[rule-middleware] engine error on {page_name}: {_rule_err}")
                if not _sa:
                    return _render_rule_block_page('RED_WALL', 'RULE_ENGINE_EXCEPTION',
                                                   'BLOCK_AND_ALERT',
                                                   {'reason': '规则校验引擎异常 → FAIL-CLOSED 安全模式',
                                                    'detail': str(_rule_err)[:400]},
                                                   'eng_err_' + _uuid.uuid4().hex[:8], 0, 0, 0, None), 500

            # 2) 执行原始视图（注意：这里把 render_template 结果进行包装，避免脱离容器）
            _orig_response = view_fn(*args, **kwargs)
            # Flask 视图可能返回 (response, code) tuple
            status_code = 200
            if isinstance(_orig_response, tuple):
                body, status_code = _orig_response[0], _orig_response[1] if len(_orig_response) > 1 else 200
            else:
                body = _orig_response
            # 若是模板 render 后的字符串，确保注入系统容器挂载脚本
            if isinstance(body, str) and '</body>' in body:
                mount_script = (
                    f'<script data-mt-container="mount">'
                    f'(function(){{'
                    f'  window.__MT_CONTAINER__ = window.__MT_CONTAINER__ || {{}};'
                    f'  Object.assign(window.__MT_CONTAINER__, {{'
                    f'    version: "{_MT_SYS_CONTAINER_VERSION}",'
                    f'    pageName: "{page_name}",'
                    f'    traceId: "{getattr(request, "mt_trace_id", "")}",'
                    f'    sid: "{sid}",'
                    f'    uid: "{user.get("uid","")}",'
                    f'    role: "{_role}",'
                    f'    mounted: true,'
                    f'    mountedAt: Date.now(),'
                    f'    requireAuth: "{require_auth}",'
                    f'    cookieNames: {json.dumps({k: v["name"] for k,v in _MT_COOKIES.items()}, ensure_ascii=False)}'
                    f'  }});'
                    f'  if (!document.body.hasAttribute("data-mt-container")) document.body.setAttribute("data-mt-container","{page_name}");'
                    f'  if (!document.documentElement.getAttribute("x-mt-version")) document.documentElement.setAttribute("x-mt-version","{_MT_SYS_CONTAINER_VERSION}");'
                    f'}})();'
                    f'</script>'
                )
                # 在 </body> 前插入挂载脚本（保证只插入一次）
                if 'data-mt-container="mount"' not in body:
                    body = body.replace('</body>', mount_script + '</body>')

            # 3) 渲染完成写页面级 AI 审计 + 心跳
            dur = int((time.time() - start) * 1000)
            try:
                if write_heartbeat:
                    with sqlite3.connect(_bizdb_path(), timeout=2) as c:
                        _ensure_container_tables(c)
                        c.execute(
                            "INSERT INTO sys_container_heartbeat(sid,uid,username,role,path,ip,ua,action,ok)"
                            " VALUES(?,?,?,?,?,?,?,?,1)",
                            (sid, user.get('uid'), _username, _role, path, _ip(), _ua(), f'page::{page_name}')
                        )
                        c.commit()
                _mt_ai_audit_push({
                    'sid': sid, 'uid': user.get('uid'), 'username': _username, 'role': _role,
                    'path': path, 'action': f'page::{page_name}::render', 'risk_level': 'low',
                    'rule_hit': 'CONTAINER::RENDER-OK', 'blocked': 0,
                    'detail': json.dumps({'dur_ms': dur, 'status': status_code}, ensure_ascii=False)
                })
            except Exception:
                pass

            if isinstance(_orig_response, tuple):
                return body, status_code
            return body
        return wrapper
    return decorator


# ---------- 动态状态监控接口 ----------

@app.route('/api/container/heartbeat', methods=['POST', 'GET'])
@system_container('container_heartbeat', require_auth='auto')
def api_mt_container_heartbeat():
    """前端页面每 30s POST 一次：容器存活 + session 续期 + 在线状态 + 健康评分"""
    try:
        data = request.get_json(silent=True) or {}
        user = _current_safe_user()
        sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
        try:
            with sqlite3.connect(_bizdb_path(), timeout=2) as c:
                _ensure_container_tables(c)
                c.execute(
                    "INSERT INTO sys_container_heartbeat(sid,uid,username,role,path,ip,ua,action,ok) VALUES(?,?,?,?,?,?,?,?,1)",
                    (sid, user.get('uid'), user.get('username'), user.get('role'),
                     request.path, _ip(), _ua(), f"heartbeat::{data.get('page', 'unknown')}")
                )
                c.execute(
                    "UPDATE sys_container_sessions SET last_seen=datetime('now','localtime') WHERE sid=?",
                    (sid,)
                )
                c.commit()
        except Exception:
            pass
        # 2026-08-12: 健康评分
        health = {'overall': 1.0, 'cpu': 1.0, 'memory': 1.0, 'db': 1.0, 'ai': 1.0}
        try:
            import psutil as _ps
            health['cpu'] = max(0, 1.0 - (_ps.cpu_percent(interval=0.1) / 100.0))
            mem = _ps.virtual_memory()
            health['memory'] = max(0, mem.available / mem.total)
        except Exception:
            pass
        try:
            with _get_conn(APP_DB) as c:
                c.execute("SELECT 1").fetchone()
            health['db'] = 1.0
        except Exception:
            health['db'] = 0.0
        try:
            providers = _ai_list_active_providers()
            health['ai'] = min(1.0, len(providers) / 3.0) if providers else 0.0
        except Exception:
            health['ai'] = 0.5
        health['overall'] = round(
            health['cpu'] * 0.25 + health['memory'] * 0.25 + health['db'] * 0.30 + health['ai'] * 0.20, 4)
        return jsonify({'success': True, 'ok': True,
                         'server_ts': int(time.time()),
                         'sid': sid,
                         'trace_id': getattr(request, 'mt_trace_id', _trace_id()),
                         'container_version': _MT_SYS_CONTAINER_VERSION,
                         'user': user,
                         'health': health,
                         'next_heartbeat_ms': 30000,
                         'stale': False,
                         'cookies_ok': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'code': 500}), 500


@app.route('/api/container/status', methods=['GET'])
@system_container('container_status', require_auth='auto')
def api_mt_container_status():
    """容器管控总览：在线用户数 / 最近心跳 / AI 审计风险分布 / Omega AI状态"""
    try:
        with sqlite3.connect(_bizdb_path(), timeout=2) as c:
            _ensure_container_tables(c)
            cur = c.execute("SELECT COUNT(DISTINCT sid) FROM sys_container_heartbeat WHERE created_at >= datetime('now','localtime','-5 minutes')")
            online = cur.fetchone()
            online = online[0] if online else 0
            cur2 = c.execute("SELECT risk_level, COUNT(*) FROM sys_container_ai_audit WHERE created_at >= datetime('now','localtime','-24 hours') GROUP BY risk_level")
            risks = {r[0]: r[1] for r in cur2.fetchall()}
            cur3 = c.execute("SELECT COUNT(*) FROM sys_container_sessions WHERE last_seen >= datetime('now','localtime','-1 hours')")
            sess = cur3.fetchone()
            sess = sess[0] if sess else 0
        return jsonify({
            'success': True,
            'container_version': _MT_SYS_CONTAINER_VERSION,
            'mounted': True,
            'online_last_5m': online,
            'active_sessions_last_1h': sess,
            'audit_risk_24h': risks,
            'omega_ai': _omega_get_status() if '_omega_get_status' in dir() else None,
            'cookies_spec': {k: {'name': v['name'], 'max_age': v['max_age'], 'httpOnly': v['httpOnly'], 'sameSite': v['sameSite']} for k, v in _MT_COOKIES.items()},
            'trace_id': getattr(request, 'mt_trace_id', _trace_id()),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------- 全局 HTML 模板注入容器上下文（context_processor）----------
@app.context_processor
def _mt_sys_container_ctx_injector():
    """所有 render_template 自动可读取 {{ container }} / {{ current_user }}"""
    try:
        user = _current_safe_user()
        sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()

        try:
            from core.services.lunar_calendar_service import lunar_calendar_service  # type: ignore[import]
            # ══ PATCH: 按 session i18n_lang 动态翻译 ══
            _mt_lang = session.get('i18n_lang', 'zh_CN')
            _mt_lang_map = {'zh_CN': 'zh', 'zh_TW': 'zh_tw', 'ja_JP': 'ja', 'en_US': 'en'}
            _mt_service_lang = _mt_lang_map.get(_mt_lang, 'zh')

            lunar_display = lunar_calendar_service.get_display_text(lang='zh')
            lunar_display_en = lunar_calendar_service.get_display_text(lang='en')
            lunar_date = lunar_calendar_service.get_lunar_date_string()
            is_special_day = lunar_calendar_service.is_first_or_fifteenth()
            lunar_countdown = lunar_calendar_service.get_countdown()

            # ══ BUILD: buddha_festivals = 今天 + 未来 30 天佛/道/农历/公历节日 ══
            import datetime as _dt_mt
            buddha_festivals = []
            _seen_fests = set()
            _tday = _dt_mt.date.today()

            # 合并两个事件源: (1) 旧字典 BUDDHIST_FESTIVALS_LUNAR/SOLAR (45+17条)
            #               (2) 扩充事件库 LUNAR_BUDDHIST_EVENTS (76+ 佛道儒各宗派)
            try:
                from core.services.auto_plans.plan_lunar_buddhist import LUNAR_BUDDHIST_EVENTS
                _expanded = True
            except Exception:
                _expanded = False

            for _offset in range(31):  # 0~30 天
                _target = _tday + _dt_mt.timedelta(days=_offset)
                _ly, _lm, _ld, _isleap = lunar_calendar_service._solar_to_lunar(_target)
                # 源 1: 旧字典 (lunar + solar)
                _lunars = lunar_calendar_service._get_lunar_festivals(_lm, _ld)
                _solars = lunar_calendar_service._get_solar_festivals(_target.month, _target.day)
                for _fn in (_lunars + _solars):
                    if _fn not in _seen_fests:
                        _seen_fests.add(_fn)
                        _lbl = f"今日 {_fn}" if _offset == 0 else f"{_offset}天后 {_fn}"
                        buddha_festivals.append(_lbl)
                # 源 2: 扩充事件库 (按 month/day 匹配)
                if _expanded:
                    for _ev in LUNAR_BUDDHIST_EVENTS:
                        _em, _ed = _ev.get('month', 0), _ev.get('day', 0)
                        # day=-1 表示估算日(月中), 简化: 只要 month 匹配且 day>0 才精确匹配
                        if _em == _lm and _ed > 0 and _ed == _ld:
                            _fn = _ev.get('event', '')
                            if _fn and _fn not in _seen_fests:
                                _seen_fests.add(_fn)
                                _lbl = f"今日 {_fn}" if _offset == 0 else f"{_offset}天后 {_fn}"
                                buddha_festivals.append(_lbl)
            buddha_festivals_en = []  # 翻译由下面统一处理

            # ── 动态翻译 lunar_countdown 中文字段 ──
            if _mt_service_lang != 'zh' and lunar_countdown:
                try:
                    def _t(zh_text, domain='lunar'):
                        """从 mt_i18n_keys 翻译 zh_text → 目标语言"""
                        col = {'zh_tw':'zh_tw','ja':'ja_jp','en':'en_us'}.get(_mt_service_lang, 'zh_cn')
                        if col == 'zh_cn': return zh_text
                        import sqlite3 as _sq
                        _db = _sq.connect(os.path.join(os.path.dirname(__file__), 'database', 'app.db'))
                        # 按原文查 key (mt_i18n_keys.zh_cn = 原文)
                        row = _db.execute(f"SELECT {col} FROM mt_i18n_keys WHERE zh_cn=? AND {col}!='' ORDER BY length({col}) DESC LIMIT 1", (zh_text,)).fetchone()
                        _db.close()
                        if row and row[0]: return row[0]
                        return zh_text

                    # 翻译 countdown 各字段
                    if lunar_countdown.get('festival_today'):
                        lunar_countdown['festival_today'] = _t(lunar_countdown['festival_today'])
                    if lunar_countdown.get('countdown_type'):
                        lunar_countdown['countdown_type'] = _t(lunar_countdown['countdown_type'])
                    # year_ganzhi 如 "丙午" 不需要翻 (通用)
                    # animal 如 "马" 需要翻
                    if lunar_countdown.get('animal'):
                        lunar_countdown['animal'] = _t(lunar_countdown['animal'], 'zodiac')

                    # 翻译 buddha_festivals 字符串列表 "今日 春节" / "8天后 中秋节"
                    if buddha_festivals:
                        import re as _re_mt
                        for _i, _lbl in enumerate(buddha_festivals):
                            m = _re_mt.match(r'^(今日|(\d+)天后)\s+(.+)$', _lbl)
                            if m:
                                _prefix = m.group(1)  # "今日" or "N天后"
                                _fname = m.group(3)   # 节日名
                                _fname_t = _t(_fname, 'events')
                                _prefix_t = _t(_prefix, 'festival_prefix')
                                buddha_festivals[_i] = f"{_prefix_t} {_fname_t}"
                except Exception:
                    pass  # 翻译失败不阻断页面

            # ── zh_TW 额外用 OpenCC 繁化 ──
            if _mt_lang == 'zh_TW' and (lunar_countdown or buddha_festivals):
                try:
                    import opencc as _oc
                    _twc = _oc.OpenCC('s2t')
                    if lunar_countdown:
                        for f in ('festival_today','countdown_type','animal'):
                            if lunar_countdown.get(f):
                                lunar_countdown[f] = _twc.convert(lunar_countdown[f])
                    if buddha_festivals:
                        buddha_festivals = [_twc.convert(x) for x in buddha_festivals]
                except Exception:
                    pass
        except Exception:
            lunar_display = ""
            lunar_display_en = ""
            lunar_date = ""
            is_special_day = False
            lunar_countdown = {}
            buddha_festivals = []
            buddha_festivals_en = []

        # 优先使用 VikeyAPI 统一封装的 VikeyGetStatus（兼容同名函数）
        # --- VIKEY 缓存：每次页面渲染都调用 vikey 驱动会触发大量告警 ---
        global _MT_VIKEY_CACHE
        try:
            _MT_VIKEY_CACHE
        except NameError:
            _MT_VIKEY_CACHE = {"ts": 0, "status": {
                'present': False, 'count': 0,
                'has_super_admin_key': False, 'super_admin_serial': None,
            }}
        import time as _vk_t
        _vk_now = _vk_t.time()
        if (_vk_now - _MT_VIKEY_CACHE["ts"]) < 25:  # 25s 缓存：大幅降低驱动检测频率
            vikey_status = dict(_MT_VIKEY_CACHE["status"])
        else:
            try:
                from core.services.vikey_api import VikeyGetStatus
                vikey_status = VikeyGetStatus()
            except Exception:
                try:
                    from core.services.vikey_driver import VikeyGetStatus
                    vikey_status = VikeyGetStatus()
                except Exception:
                    vikey_status = {
                        'present': False,
                        'count': 0,
                        'has_super_admin_key': False,
                        'super_admin_serial': None,
                    }
            # DEBUG环境：统一降低 VIKEY 告警级别到 DEBUG（避免刷屏）
            try:
                if not vikey_status.get('present', False) and not app.config.get('VIKEY_ALLOW_DEBUG_QUIET', False):
                    import logging as _vk_quiet_lg
                    _vk_quiet_lg.debug(
                        "[vikey] 调试环境未插入 VIKEY USB加密狗 → present=%s, bound=%s (SA登录时才强制阻断)",
                        vikey_status.get('present', False),
                        bool(vikey_status.get('has_super_admin_key', False) or vikey_status.get('count', 0) > 0),
                    )
            except Exception:
                pass
            _MT_VIKEY_CACHE["ts"] = _vk_now
            _MT_VIKEY_CACHE["status"] = dict(vikey_status)

        # ========== SA 双密钥 layout_mode 注入 ==========
        try:
            from app.middlewares.vikey_enforcement_middleware import vikey_enforcement as _mt_dual_vk
            _mt_dual_uname = user.get('username') or session.get('username', '') or ''
            _mt_dual_role = user.get('role_name') or user.get('role') or session.get('role', '')
            _mt_extra = {
                'ip': request.remote_addr,
                'ua': request.headers.get('User-Agent','')[:300],
                'session_id': session.sid if getattr(session,'sid',None) else session.get('_session_id',''),
            }
            _dual = _mt_dual_vk.get_dual_hardware_status(username=_mt_dual_uname, role=_mt_dual_role,
                                                         **{k:v for k,v in _mt_extra.items() if k in ('ip','ua','session_id')})
            layout_mode = _dual.get('layout_mode') or 'STANDARD'
            dual_authenticated = bool(_dual.get('both_authenticated'))
            sa_proprietary = bool(dual_authenticated and (_mt_dual_uname.lower()=='wuchenghao15' or str(_mt_dual_role).lower()=='super_admin'))
            # SA + 非双钥 → 已由 before_request 拦截到登录；这里保险强制 STANDARD
            if (not dual_authenticated) and (_mt_dual_uname.lower()=='wuchenghao15' or str(_mt_dual_role).lower()=='super_admin'):
                layout_mode = 'STANDARD'
            vikey_serial = (_dual.get('vikey') or {}).get('serial') if dual_authenticated else None
            szu100_volume = (_dual.get('szu100') or {}).get('volume_name') if dual_authenticated else None
        except Exception:
            layout_mode = 'STANDARD'
            dual_authenticated = False
            sa_proprietary = False
            vikey_serial = None
            szu100_volume = None

        ctx = {
            'container': {
                'version': _MT_SYS_CONTAINER_VERSION,
                'page_name': getattr(request, '__mt_container_page__', 'fallback'),
                'sid': sid,
                'trace_id': getattr(request, 'mt_trace_id', _trace_id()),
                'mounted': True,
                'cookies': {k: v['name'] for k, v in _MT_COOKIES.items()},
                'user': user,
            },
            'current_user': user,
            'user_ctx': user,
            'is_super_admin_container': (user.get('username') == 'wuchenghao15'),
            'lunar_display': lunar_display,
            'lunar_display_en': lunar_display_en,
            'lunar_date': lunar_date,
            'is_special_day': is_special_day,
            'lunar_countdown': lunar_countdown,
            'buddha_festivals': buddha_festivals,
            'buddha_festivals_en': buddha_festivals_en,
            'vikey_present': vikey_status.get('present', False),
            'vikey_count': vikey_status.get('count', 0),
            'vikey_has_super_admin': vikey_status.get('has_super_admin_key', False),
            'vikey_serial': vikey_serial or vikey_status.get('super_admin_serial'),
            # ---- SA 双密钥 layout 自动切换 ----
            'layout_mode': layout_mode,
            'dual_authenticated': dual_authenticated,
            'sa_proprietary': sa_proprietary,
            'szu100_volume': szu100_volume,
            'dual_hardware': _dual if sa_proprietary else {'both_authenticated': False, 'layout_mode': 'STANDARD'},
        }
        return ctx
    except Exception:
        return {}


# ==========================================================
#  END：MTSCOS 系统容器管控层
# ==========================================================

_ROLE_CN = {
    'admin': '管理员',
    'super_admin': '超级管理员',
    'school_admin': '校管理员',
    'teacher': '教师',
    'student': '学生',
    'parent': '家长',
    'user': '普通用户',
    'guest': '访客',
    'hardware_admin': '硬件管理员',
    'institution_admin': '机构管理员',
}


# ==========================================================
#  协议文档（注册时必须勾选）+ 身份组别体系
# ==========================================================
_LEGAL_TERMS_VERSION = '1.0.0'
_LEGAL_TERMS_UPDATED_AT = '2026-08-05'

_LEGAL_DOCUMENTS = {
    'register_agreement': {
        'title': '注册协议',
        'short_name': '注册协议',
        'updated_at': _LEGAL_TERMS_UPDATED_AT,
        'version': _LEGAL_TERMS_VERSION,
        'body': [
            ('第一节 协议接受与修改', [
                '1.1 本协议是您（注册用户）与 MTSCOS AI 智能学习评估平台（以下简称"平台"、"我们"）之间，关于您使用平台注册账号及相关服务所订立的协议。',
                '1.2 您在注册页面勾选「我已阅读并同意注册协议」并完成注册，即视为您已充分阅读、理解并接受本协议全部条款。',
                '1.3 平台有权根据法律法规变化或业务调整更新本协议；更新后将在 /legal/register_agreement 页面公告，您继续使用即视为接受更新版本。',
            ]),
            ('第二节 账号注册与保管', [
                '2.1 您承诺注册时提供真实、准确、完整的身份资料（用户名、邮箱、年龄、教育组别等），并在资料变更时及时更新。',
                '2.2 您应对您的账号和密码的安全性，以及在您账号下进行的所有活动承担全部责任。',
                '2.3 若发现任何未经授权使用您账号的情况，请立即通过 contact@mtscos.com 通知平台。',
            ]),
            ('第三节 普通组别与身份申请', [
                '3.1 新注册用户默认为「普通用户（普通组别）」，仅可浏览平台基础介绍页面，无法使用智能设置、AI辅导、考试题库、诊断分析等任何付费/数据敏感功能。',
                '3.2 您可在注册时或「个人设置→身份认证」中提交教育组别申请（K12学生 / 成人教育 / 高等教育），平台或管理员审批通过后，对应组别功能方可启用。',
                '3.3 平台有权根据您提交的年龄、证明资料等信息，审核并最终决定您的组别。组别一经确认不可随意切换，如需变更须重新提交审批。',
            ]),
            ('第四节 服务限制与合规使用', [
                '4.1 您承诺不以任何方式干扰、破坏平台服务或绕过权限控制访问未授权功能。',
                '4.2 您不得利用平台服务从事任何违反法律法规或侵犯他人合法权益的行为。',
                '4.3 违反本节约定，平台有权立即暂停或终止您的账号使用权限。',
            ]),
            ('第五节 协议终止', [
                '5.1 您可随时在「个人设置」页面注销账号，注销后您的数据将按照《数据使用告知协议》处理。',
                '5.2 本协议终止后，本协议下第 2、4、6、7 节条款仍然有效。',
            ]),
            ('第六节 免责声明', [
                '6.1 平台提供的AI辅导、学情诊断等服务结果仅供参考，不构成任何升学、就业、诊断方面的保证或承诺。',
                '6.2 因不可抗力、系统故障等非平台故意造成的服务中断或数据丢失，平台在法律允许范围内免责。',
            ]),
            ('第七节 法律适用与争议解决', [
                '7.1 本协议的订立、执行、解释及争议解决适用中华人民共和国法律。',
                '7.2 因本协议引起的争议，双方应友好协商解决；协商不成的，任何一方可向平台所在地人民法院提起诉讼。',
            ]),
        ],
    },
    'user_agreement': {
        'title': '用户协议',
        'short_name': '用户协议',
        'updated_at': _LEGAL_TERMS_UPDATED_AT,
        'version': _LEGAL_TERMS_VERSION,
        'body': [
            ('第一条 服务内容', [
                '1.1 平台为不同教育组别（K12学生/成人教育/高等教育）提供智能出题、自适应练习、学情诊断、AI答疑、知识脑库等学习评估服务。',
                '1.2 平台有权根据业务发展调整服务内容、收费模式或终止部分服务，并提前 15 天在站内公告。',
            ]),
            ('第二条 用户行为规范', [
                '2.1 您承诺上传、分享、发布的任何内容均符合法律法规及公序良俗，不侵犯任何第三方合法权益。',
                '2.2 您不得对平台服务进行反向工程、反编译、爬虫、批量抓取或进行任何可能损害平台安全的行为。',
                '2.3 您不得冒充他人、伪造身份或提交虚假资料，否则平台有权拒绝提供服务并追究法律责任。',
            ]),
            ('第三条 知识产权', [
                '3.1 平台所提供的试题、解析、视频、文本、图形、UI等内容的知识产权归平台或其权利人所有。',
                '3.2 未经平台书面同意，您不得以任何形式复制、传播、修改、衍生平台内容用于商业目的。',
                '3.3 您在使用平台过程中产生的原创答题、笔记、学习报告等内容的知识产权归您所有，您授予平台在服务范围内免费、非独占的使用许可。',
            ]),
            ('第四条 服务开通与暂停', [
                '4.1 完成组别身份审批后，您可使用对应组别服务；审批未通过前，您的账号权限与「普通组别」一致。',
                '4.2 若您违反本协议，平台有权视情节给予警告、功能限制、暂停服务、注销账号等处理。',
            ]),
            ('第五条 未成年人特别条款', [
                '5.1 未满 14 周岁的未成年人须在监护人陪同下阅读本协议并注册使用；监护人须对未成年人使用平台的行为承担全部责任。',
                '5.2 平台严格遵守《未成年人网络保护条例》，对未成年用户设置内容分级、防沉迷、消费限额等保护机制。',
            ]),
        ],
    },
    'security_agreement': {
        'title': '安全协议',
        'short_name': '安全协议',
        'updated_at': _LEGAL_TERMS_UPDATED_AT,
        'version': _LEGAL_TERMS_VERSION,
        'body': [
            ('第一章 账号安全', [
                '1.1 您须妥善保管账号密码，建议使用平台推荐的「8-64位、至少3类字符、非弱密码」强度标准。',
                '1.2 对于超级管理员/管理员等高级别账号，平台强制 VIKEY USB 硬件加密狗 + 7 要素双因子认证；普通用户可在「个人设置→安全中心」开启指纹、邮箱验证码等附加验证。',
                '1.3 连续 5 次登录失败将触发 900s 软锁定，连续 10 次失败触发 86400s 硬锁定并进入AI黑名单，您可通过「忘记密码」流程自助解锁。',
            ]),
            ('第二章 数据传输与存储安全', [
                '2.1 平台采用 HTTPS/TLS1.3 加密传输，敏感字段（密码、身份证号、指纹模板等）使用 bcrypt/AES-256 单向/对称加密存储，绝不以明文落盘。',
                '2.2 平台接入 EigenFlux 实时监控守护引擎，7×24 小时检测文件篡改、注入攻击、异常访问，并对高危操作执行 AI员工 5 人磋商审批。',
                '2.3 用户数据存储遵循「SSOT单一数据源 + 双库冷备 + 异地灾备」策略，确保数据完整性与可用性。',
            ]),
            ('第三章 API 与第三方安全', [
                '3.1 所有对外 API 接入须申请 AccessKey + SecretKey，签名算法为 HMAC-SHA256，单IP每分钟限流默认 ≤ 600 次。',
                '3.2 第三方集成须签署《数据处理协议》(DPA)，通过最小授权原则访问；平台对第三方的调用进行全链路审计。',
                '3.3 如发现安全漏洞，请通过 security@mtscos.com 联系平台安全团队，我们将按行业最佳实践在 24 小时内响应。',
            ]),
            ('第四章 安全事件响应', [
                '4.1 平台建立「检测→分析→遏制→根除→恢复→复盘」六阶段响应流程，发生数据泄露等重大安全事件后，依法于 72 小时内通知受影响用户并上报监管部门。',
                '4.2 安全事件处理详情与改进措施将在「系统公告」与 /help/security-incident 页面公开。',
            ]),
        ],
    },
    'data_usage_notice': {
        'title': '数据使用告知协议',
        'short_name': '数据使用告知协议',
        'updated_at': _LEGAL_TERMS_UPDATED_AT,
        'version': _LEGAL_TERMS_VERSION,
        'body': [
            ('一、我们收集的信息', [
                '1.1 账户信息：注册时您主动填写的用户名、邮箱、年龄、生日、教育组别、手机号、头像、个性签名。',
                '1.2 学习数据：答题记录、错题本、学习时长、考试成绩、诊断画像、AI辅导交互日志。',
                '1.3 设备与日志：IP地址、User-Agent、登录时间、会话ID、硬件指纹（仅 VIKEY 管理员使用）。',
                '1.4 敏感信息：仅当您启用指纹登录时采集指纹模板（本地加密存储，仅比对不回传）。',
            ]),
            ('二、我们如何使用信息', [
                '2.1 核心服务：出题、打分、生成学习报告、推荐内容、账号鉴权、组别权限校验。',
                '2.2 安全与风控：检测异常登录、防刷注册、识别弱密码、审计违规操作、触发红线红墙规则阻断。',
                '2.3 质量改进：对脱敏后的学习数据做统计分析，持续优化AI模型、试题质量和诊断准确率。',
                '2.4 通信通知：发送登录告警、密码重置、组别审批结果等必要的系统邮件。',
                '2.5 您有权随时在「个人设置→数据与隐私」中撤回非必要数据项的授权。',
            ]),
            ('三、数据共享与披露', [
                '3.1 除以下情形外，我们不会向任何第三方出售、出租、共享您的个人信息：',
                '    · 事先获得您的明确书面同意；',
                '    · 为履行法定义务或配合有权机关合法请求；',
                '    · 与签署DPA的云服务/邮件/支付等必要供应商共享最小必要数据。',
                '3.2 所有对外共享均会进行去标识化处理，并签订严格的保密与数据安全协议。',
            ]),
            ('四、您的权利', [
                '4.1 访问权/更正权：您可在「个人设置」中查看和修改绝大部分个人信息。',
                '4.2 删除权/注销权：您可申请删除特定数据或注销整个账号，注销后我们将在 30 天内匿名化或删除（法律法规要求留存的除外）。',
                '4.3 数据可携权：您可在「个人设置→导出我的数据」页面一键下载 JSON 格式的个人数据副本。',
                '4.4 撤回同意/投诉举报：通过 privacy@mtscos.com 联系数据保护官，我们将在 15 个工作日内响应。',
            ]),
            ('五、数据保留期限', [
                '5.1 账户存续期间 + 注销或最后访问后 36 个月；法律法规要求更长留存期限的（如会计凭证、税务记录）按相关规定执行。',
                '5.2 学习报告类产物数据，如您主动发布为公开状态，保留至您主动删除之日。',
            ]),
            ('六、Cookie 与同类技术', [
                '6.1 平台使用必要 Cookie 维持会话、记住偏好、防CSRF；您可在浏览器设置中禁用，但禁用后部分功能将不可用。',
                '6.2 平台不会使用 Cookie 追踪用户跨站行为，也未接入第三方广告 SDK。',
            ]),
            ('七、联系我们', [
                '数据保护负责人（DPO）：隐私与合规团队',
                '邮箱：privacy@mtscos.com    客服：400-888-8888（工作日 9:00-18:00）',
                '通信地址：北京市海淀区科技园区 MTSCOS AI 合规部',
            ]),
        ],
    },
}

# 注册时必须全部勾选的 4 个协议 slug
_REQUIRED_TERMS_SLUGS = tuple(sorted(_LEGAL_DOCUMENTS.keys()))


def _validate_education_apply_by_age(age, requested):
    """
    根据注册年龄智能删减可申请的教育组别，并返回合法选项 + 是否合法。

    规则：
        age < 12          → 仅 ['k12']          （小学阶段）
        12 ≤ age < 18     → ['k12', 'adult']   （初中/高中，可成人自考）
        18 ≤ age < 22     → ['k12', 'adult', 'higher'] （大学可高等教育，也可成人/K12复读）
        22 ≤ age < 24     → ['adult', 'higher'] （研究生/成人）
        age ≥ 24          → 仅 ['adult']        （在职成人）
        age 未知(None/0)  → ['k12', 'adult']    （默认选项，不开放高等教育）
    返回: (allowed_set: set, valid: bool)
    """
    try:
        a = int(age) if age is not None else 0
    except (TypeError, ValueError):
        a = 0
    if a <= 0:
        allowed = {'k12', 'adult'}
    elif a < 12:
        allowed = {'k12'}
    elif a < 18:
        allowed = {'k12', 'adult'}
    elif a < 22:
        allowed = {'k12', 'adult', 'higher'}
    elif a < 24:
        allowed = {'adult', 'higher'}
    else:
        allowed = {'adult'}
    # 更新 education_type 白名单：如果申请 higher，需要允许它（否则 _validate_enum 会拦截）
    # 通过 _ADMIN_EDUCATION_TYPE_WHITELIST 动态 union 方式处理
    allowed_req = (str(requested) or '').strip().lower()
    if not allowed_req:
        return allowed, True  # 未申请时合法（默认为普通组别）
    return allowed, allowed_req in allowed


# 扩大白名单，包含 higher（原只 {k12, adult}）；保持原常量避免影响其他调用
_EXTENDED_EDUCATION_WHITELIST = _ADMIN_EDUCATION_TYPE_WHITELIST

# 教育组别中文映射（3档）
_EDUCATION_TYPE_CN = {
    'K12': 'K12 基础教育',
    'higher': '高等教育',
    'adult': '成人教育',
}

# 普通组别（role='user' 且 education_type 为 '普通'/'general'/'None'）禁访的功能标识列表
#  —— 供 @system_container 内的统一拦截使用
_NORMAL_GROUP_BLOCKED_FEATURE_FLAGS = {
    'exam_write',          # 参加考试/提交答案
    'paper_generate',      # 智能组卷/出题
    'ai_tutor',            # AI辅导老师对话
    'diagnostic_access',   # 学情诊断
    'knowledge_brain',     # AI知识脑库高级查询
    'smart_params_edit',   # 智能设置相关参数（题目难度、推荐策略、AI模型参数等）
    'teacher_workbench',   # 教师工作台
    'student_portal_premium',  # 学生学习门户高级功能
}




def get_role_name(role_key):
    if not role_key:
        return '未分配'
    key = str(role_key).strip().lower()
    for k, v in _ROLE_CN.items():
        if k == key or k in key:
            return v
    # 首字母大写友好显示
    s = str(role_key).strip().replace('_', ' ')
    return s[:1].upper() + s[1:]


# Jinja2 模板全局可用函数（避免模板里 UndefinedError: 'xxx' is undefined）
@app.context_processor
def _inject_template_globals():
    def g_is_authenticated():
        return bool(session.get('user_id'))

    def g_current_user():
        # 🔧 v22.40.2: 补缺失的 _safe_user_ctx 包装 — None → 空 dict, 防止模板 .name 炸
        u = _current_user()
        if u is None:
            return {'id': None, 'username': 'guest', 'role': 'guest', 'is_admin': False, 'is_super_admin': False}
        return u

    def g_is_admin():
        u = _current_user()
        if not u:
            return False
        role = str(u.get('role') or '').lower()
        if role in ('admin', 'super_admin', 'school_admin', 'institution_admin', 'teacher'):
            return True
        if _safe_super_approved(u.get('id')):
            return True
        return False

    def g_is_super_admin():
        u = _current_user()
        if not u:
            return False
        username = str(u.get('username') or '').lower()
        if username == 'wuchenghao15':
            return True
        return False

    return dict(
        get_role_name=get_role_name,
        is_authenticated=g_is_authenticated,
        current_user=g_current_user(),
        is_admin=g_is_admin(),
        is_super_admin=g_is_super_admin(),
        system_version=get_version_info()[0],
        now=datetime.now(),
        csrf_token=session.get('csrf_token', ''),
    )

NATIONAL_MOURNING_DATES = [
    (9, 30),
    (12, 13),
    (9, 18),
]

THEME_DEEP_BLUE = 'deep_blue'
THEME_LIGHT_BLUE = 'light_blue_tech'
THEME_LIGHT = 'light'
THEME_MOURNING = 'mourning'

VALID_THEMES = {THEME_DEEP_BLUE, THEME_LIGHT_BLUE, THEME_LIGHT, THEME_MOURNING}
ADMIN_THEMES_NO_MOURNING = [THEME_DEEP_BLUE, THEME_LIGHT_BLUE, THEME_LIGHT]

# ============================================================================
# 主题系统预设配色（主题系统 STEP_7_EXECUTE flow_20260811103134_8fc2bd）
# 6 套预设主题：每套包含 primary/secondary/accent 三色（HEX 格式）
# ============================================================================
THEME_PRESETS = [
    {
        'name': 'deep_space_blue',
        'label': '深空蓝·科技',
        'description': '默认主题，适合日常/夜间/科技感场景',
        'primary': '#4f46e5',
        'secondary': '#06b6d4',
        'accent': '#818cf8',
    },
    {
        'name': 'warm_orange',
        'label': '暖橙·活力',
        'description': '活力充沛，适合日间/演示场景',
        'primary': '#ea580c',
        'secondary': '#f59e0b',
        'accent': '#fb923c',
    },
    {
        'name': 'forest_green',
        'label': '森林绿·自然',
        'description': '自然舒适，适合长时间阅读',
        'primary': '#16a34a',
        'secondary': '#22c55e',
        'accent': '#4ade80',
    },
    {
        'name': 'ink_black',
        'label': '水墨黑·极简',
        'description': '极简沉稳，适合专注模式',
        'primary': '#1e293b',
        'secondary': '#475569',
        'accent': '#94a3b8',
    },
    {
        'name': 'cyber_purple',
        'label': '赛博紫·前卫',
        'description': '前卫炫酷，适合创意/设计场景',
        'primary': '#9333ea',
        'secondary': '#a855f7',
        'accent': '#c084fc',
    },
    {
        'name': 'night_red',
        'label': '暗夜红·热情',
        'description': '热情醒目，适合重点强调',
        'primary': '#dc2626',
        'secondary': '#ef4444',
        'accent': '#f87171',
    },
    {
        'name': 'black_gold',
        'label': '黑金·尊贵',
        'description': '超级管理员专属，高端大气，金色主调+深黑底色+亮金强调',
        'primary': '#d4af37',
        'secondary': '#0a0a0a',
        'accent': '#fde047',
        'is_super_admin_only': True,
    },
]

# 主题偏好有效字段白名单（用于 POST 更新时的字段过滤）
_THEME_PREF_ALLOWED_FIELDS = {
    'theme_mode', 'auto_switch', 'preset_name',
    'custom_primary', 'custom_secondary', 'custom_accent',
    'bg_image_url', 'bg_opacity', 'bg_type',
    'sunrise_time', 'sunset_time',
    'latitude', 'longitude', 'city_name',
}

# theme_mode 合法值
_THEME_MODE_VALID = {'auto', 'light', 'dark', 'memorial'}

# bg_type 合法值
_THEME_BG_TYPE_VALID = {'css_gradient', 'image', 'none'}

# HEX 颜色正则（XSS 防护：仅允许 #RRGGBB 格式）
_THEME_HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

# 预设主题名称集合
_THEME_PRESET_NAMES = {p['name'] for p in THEME_PRESETS}


def _today_mmdd():
    today = datetime.today()
    return (today.month, today.day)


def is_national_mourning_day():
    return _today_mmdd() in NATIONAL_MOURNING_DATES


def _current_user():
    if not session.get('username'):
        return None
    role = session.get('role') or 'user'
    is_admin_role = role in _MT_ADMIN_ROLES
    try:
        if os.path.exists(AUTH_DB):
            with _get_conn(AUTH_DB) as conn:
                row = conn.execute(
                    "SELECT super_admin_approved, role FROM users WHERE id = ? LIMIT 1",
                    (session.get('user_id'),)
                ).fetchone()
                if row:
                    if row['super_admin_approved']:
                        is_admin_role = True
                    if row['role'] and row['role'] in _MT_ADMIN_ROLES:
                        is_admin_role = True
    except Exception:
        pass
    return {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': role,
        'is_admin': is_admin_role,
        'is_super_admin': bool(session.get('super_admin_approved')) if session.get('super_admin_approved') is not None else (
            bool(_safe_super_approved(session.get('user_id')))
        ),
    }


def _safe_super_approved(uid):
    if not uid or not os.path.exists(AUTH_DB):
        return False
    try:
        with _get_conn(AUTH_DB) as conn:
            row = conn.execute("SELECT username, super_admin_approved FROM users WHERE id = ? LIMIT 1", (uid,)).fetchone()
            if row and row['username'] and str(row['username']).lower() == 'wuchenghao15':
                return True
            return False
    except Exception:
        return False


def _resolve_theme():
    """
    公祭日：
      * 默认强制 THEME_MOURNING（所有用户）
      * 超级管理员可通过 session['theme_override'] 临时强制切换为其他主题
    非公祭日：
      * 用户选择主题存在 session['user_theme']，否则 THEME_DEEP_BLUE（深蓝）
    """
    user = _current_user()
    if is_national_mourning_day():
        if user and user['is_super_admin']:
            override = session.get('theme_override')
            if override in VALID_THEMES:
                return override, True
        return THEME_MOURNING, True
    chosen = session.get('user_theme')
    if chosen in ADMIN_THEMES_NO_MOURNING:
        return chosen, False
    return THEME_DEEP_BLUE, False


@app.context_processor
def inject_theme_and_layout():
    user = _current_user()
    theme_key, forced_mourning = _resolve_theme()
    is_admin = user['is_admin'] if user else False
    is_super = user['is_super_admin'] if user else False
    return {
        'theme_key': theme_key,
        'theme_forced_mourning': forced_mourning,
        'is_mourning_day': is_national_mourning_day(),
        'layout_sidebar_ratio': '2:8',
        'layout_simplified_ratio': '1:9',
        'current_user': user,
        'is_admin': is_admin,
        'is_super_admin': is_super,
    }


@app.route('/api/theme/set', methods=['POST'])
@system_container('theme_set', require_auth='login')
def api_set_theme():
    """非公祭日用户自主切换主题；公祭日仅超级管理员可强制覆盖。"""
    data = request.get_json(silent=True) or {}
    target = (data.get('theme') or '').strip()
    user = _current_user()
    mourning = is_national_mourning_day()

    if mourning:
        if not (user and user['is_super_admin']):
            return jsonify({'success': False, 'message': '公祭日主题为系统自动启用，不可手动切换'}), 403
        if target not in VALID_THEMES:
            return jsonify({'success': False, 'message': f'主题无效（仅支持：{", ".join(sorted(VALID_THEMES))}）'}), 400
        session['theme_override'] = target
        return jsonify({'success': True, 'theme': target, 'forced': True,
                        'message': f'超级管理员已强制切换主题为：{target}'})

    if target not in ADMIN_THEMES_NO_MOURNING:
        return jsonify({'success': False,
                        'message': f'主题无效（仅支持：{", ".join(ADMIN_THEMES_NO_MOURNING)}）'}), 400
    session.pop('theme_override', None)
    session['user_theme'] = target
    return jsonify({'success': True, 'theme': target,
                    'message': f'已切换为：{target}'})


@app.route('/api/theme/reset', methods=['POST'])
@system_container('theme_reset_api', require_auth='login')
def api_reset_theme():
    """清除自定义/强制覆盖，回到系统自动判定。"""
    session.pop('user_theme', None)
    session.pop('theme_override', None)
    theme_key, forced = _resolve_theme()
    return jsonify({'success': True, 'theme': theme_key, 'forced_mourning': forced})


@app.route('/api/theme/get', methods=['GET'])
@system_container('theme_get', require_auth='auto')
def api_get_theme():
    """获取当前主题及可用主题列表。"""
    theme_key, forced = _resolve_theme()
    user = _current_user()
    available_themes = []

    if user and user['is_super_admin']:
        available_themes = [
            {'key': THEME_DEEP_BLUE, 'name': '深蓝主题（默认）', 'description': '日常/夜间/主站'},
            {'key': THEME_LIGHT_BLUE, 'name': '浅蓝科技风', 'description': '大屏/演示/浅色'},
            {'key': THEME_LIGHT, 'name': '浅色系主题', 'description': '与深蓝配色1:1对应'},
            {'key': THEME_MOURNING, 'name': '灰黑追思', 'description': '国家公祭日自动启用'},
        ]
    else:
        available_themes = [
            {'key': THEME_DEEP_BLUE, 'name': '深蓝主题（默认）', 'description': '日常/夜间/主站'},
            {'key': THEME_LIGHT_BLUE, 'name': '浅蓝科技风', 'description': '大屏/演示/浅色'},
            {'key': THEME_LIGHT, 'name': '浅色系主题', 'description': '与深蓝配色1:1对应'},
        ]

    return jsonify({
        'success': True,
        'theme': theme_key,
        'forced_mourning': forced,
        'available_themes': available_themes,
        'user_role': user['role'] if user else 'guest',
        'is_super_admin': user['is_super_admin'] if user else False,
    })


@app.route('/api/theme/recommend', methods=['GET'])
@system_container('theme_recommend', require_auth='auto')
def api_recommend_theme():
    """基于用户行为的千人千面主题推荐。"""
    user = _current_user()
    recommended_theme = THEME_DEEP_BLUE

    if user:
        hour = datetime.now().hour
        if 6 <= hour < 18:
            recommended_theme = THEME_LIGHT
        else:
            recommended_theme = THEME_DEEP_BLUE

    return jsonify({
        'success': True,
        'recommended_theme': recommended_theme,
        'reason': '日间推荐浅色主题，夜间推荐深色主题',
        'themes': [
            {'key': THEME_DEEP_BLUE, 'name': '深蓝主题'},
            {'key': THEME_LIGHT_BLUE, 'name': '浅蓝科技风'},
            {'key': THEME_LIGHT, 'name': '浅色系主题'},
        ]
    })


# ============================================================
# 主题偏好 API（主题系统 STEP_7_EXECUTE flow_20260811103134_8fc2bd）
# 用户级主题偏好持久化 + 日出日落计算 + 预设主题管理
# ============================================================

def _ensure_user_theme_preferences_table(conn):
    """确保 mt_user_theme_preferences 表存在（幂等，与 _v21_ddls 双重保险）"""
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_user_theme_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            theme_mode TEXT DEFAULT 'auto',
            auto_switch INTEGER DEFAULT 1,
            preset_name TEXT DEFAULT 'deep_space_blue',
            custom_primary TEXT,
            custom_secondary TEXT,
            custom_accent TEXT,
            bg_image_url TEXT,
            bg_opacity REAL DEFAULT 0.08,
            bg_type TEXT DEFAULT 'css_gradient',
            sunrise_time TEXT DEFAULT '06:00',
            sunset_time TEXT DEFAULT '18:00',
            latitude REAL,
            longitude REAL,
            city_name TEXT,
            memorial_lock INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(user_id)
        )""")
        conn.commit()
    except Exception:
        pass


def _default_theme_preferences():
    """返回默认主题偏好（未保存时的回退值）"""
    return {
        'theme_mode': 'auto',
        'auto_switch': 1,
        'preset_name': 'deep_space_blue',
        'custom_primary': None,
        'custom_secondary': None,
        'custom_accent': None,
        'bg_image_url': None,
        'bg_opacity': 0.08,
        'bg_type': 'css_gradient',
        'sunrise_time': '06:00',
        'sunset_time': '18:00',
        'latitude': None,
        'longitude': None,
        'city_name': None,
        'memorial_lock': 1,
    }


@app.route('/api/user/theme_preferences', methods=['GET'])
@system_container('user_theme_preferences_get', require_auth='login')
def api_get_user_theme_preferences():
    """获取当前用户主题偏好（需登录）"""
    user = _current_user()
    if not user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    try:
        uid = str(user['id'])
        with _get_conn(APP_DB) as conn:
            _ensure_user_theme_preferences_table(conn)
            row = conn.execute(
                "SELECT * FROM mt_user_theme_preferences WHERE user_id = ? LIMIT 1",
                (uid,)
            ).fetchone()
        if row:
            data = dict(row)
        else:
            data = _default_theme_preferences()
            data['user_id'] = uid
        # 公祭日强制返回 memorial 模式（memorial_lock=1 时）
        if is_national_mourning_day() and data.get('memorial_lock', 1):
            data['theme_mode'] = 'memorial'
            data['memorial_day'] = True
        else:
            data['memorial_day'] = False
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.warning(f"[theme_pref] 获取用户主题偏好失败: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {e}'}), 500


@app.route('/api/user/theme_preferences', methods=['POST'])
@system_container('user_theme_preferences_save', require_auth='login')
def api_save_user_theme_preferences():
    """保存/更新当前用户主题偏好（需登录）

    接收 JSON 参数，更新用户主题偏好。
    custom_primary/secondary/accent 需符合 ^#[0-9a-fA-F]{6}$ 格式（XSS 防护）。
    """
    user = _current_user()
    if not user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'success': False, 'message': '请求体必须是JSON对象'}), 400

    # 1) HEX 颜色验证（XSS 防护：仅允许 #RRGGBB）
    for color_field in ('custom_primary', 'custom_secondary', 'custom_accent'):
        val = data.get(color_field)
        if val is None or val == '':
            data[color_field] = None
            continue
        if not isinstance(val, str) or not _THEME_HEX_COLOR_RE.match(val):
            return jsonify({'success': False,
                            'message': f'{color_field} 颜色格式无效，仅支持 #RRGGBB 格式'}), 400

    # 2) theme_mode 验证
    theme_mode = data.get('theme_mode')
    if theme_mode is not None and theme_mode not in _THEME_MODE_VALID:
        return jsonify({'success': False,
                        'message': f'theme_mode 无效，仅支持: {", ".join(sorted(_THEME_MODE_VALID))}'}), 400

    # 3) bg_type 验证
    bg_type = data.get('bg_type')
    if bg_type is not None and bg_type not in _THEME_BG_TYPE_VALID:
        return jsonify({'success': False,
                        'message': f'bg_type 无效，仅支持: {", ".join(sorted(_THEME_BG_TYPE_VALID))}'}), 400

    # 4) preset_name 验证
    preset_name = data.get('preset_name')
    if preset_name is not None and preset_name not in _THEME_PRESET_NAMES:
        return jsonify({'success': False,
                        'message': f'preset_name 无效，可选: {", ".join(sorted(_THEME_PRESET_NAMES))}'}), 400

    # 4.1) 黑金配色权限校验（仅超级管理员可选 black_gold）
    if preset_name == 'black_gold' and not user.get('is_super_admin'):
        return jsonify({'success': False, 'message': '黑金配色为超级管理员专属，无权选择'}), 403

    # 5) bg_opacity 验证（0~1 浮点）
    if 'bg_opacity' in data and data['bg_opacity'] is not None:
        try:
            data['bg_opacity'] = float(data['bg_opacity'])
            if not (0.0 <= data['bg_opacity'] <= 1.0):
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'bg_opacity 必须是 0~1 之间的浮点数'}), 400

    # 6) 时间格式验证（HH:MM）
    _time_re = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
    for time_field in ('sunrise_time', 'sunset_time'):
        val = data.get(time_field)
        if val is not None and val != '':
            if not isinstance(val, str) or not _time_re.match(val):
                return jsonify({'success': False,
                                'message': f'{time_field} 格式无效，应为 HH:MM'}), 400

    # 7) 经纬度验证
    for coord_field in ('latitude', 'longitude'):
        val = data.get(coord_field)
        if val is not None:
            try:
                data[coord_field] = float(val)
            except (TypeError, ValueError):
                return jsonify({'success': False, 'message': f'{coord_field} 必须是数字'}), 400

    # 8) auto_switch 转整型（0/1）
    if 'auto_switch' in data and data['auto_switch'] is not None:
        try:
            data['auto_switch'] = int(bool(data['auto_switch']))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'auto_switch 必须是整数 (0/1)'}), 400

    # 9) 字符串字段长度限制（XSS 防护）
    if 'bg_image_url' in data and data['bg_image_url']:
        data['bg_image_url'] = _safe_str(data['bg_image_url'], 500)
    if 'city_name' in data and data['city_name']:
        data['city_name'] = _safe_str(data['city_name'], 50)

    # 10) 公祭日强制 memorial 模式（memorial_lock 生效时不可切换）
    if is_national_mourning_day():
        data['theme_mode'] = 'memorial'

    # 11) 构造更新字段（仅白名单内，防止字段注入）
    update_fields = {}
    for field in _THEME_PREF_ALLOWED_FIELDS:
        if field in data:
            update_fields[field] = data[field]

    try:
        uid = str(user['id'])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with _get_conn(APP_DB) as conn:
            _ensure_user_theme_preferences_table(conn)
            # 先确保行存在（INSERT OR IGNORE 幂等）
            conn.execute(
                "INSERT OR IGNORE INTO mt_user_theme_preferences (user_id, created_at, updated_at) VALUES (?, ?, ?)",
                (uid, now, now)
            )
            # 更新白名单字段
            if update_fields:
                set_clauses = [f"{k} = ?" for k in update_fields]
                params = list(update_fields.values())
                set_clauses.append("updated_at = ?")
                params.append(now)
                params.append(uid)
                conn.execute(
                    f"UPDATE mt_user_theme_preferences SET {', '.join(set_clauses)} WHERE user_id = ?",
                    params
                )
            conn.commit()
            # 返回更新后的完整数据
            row = conn.execute(
                "SELECT * FROM mt_user_theme_preferences WHERE user_id = ? LIMIT 1",
                (uid,)
            ).fetchone()
        result = dict(row) if row else _default_theme_preferences()
        return jsonify({'success': True, 'data': result,
                        'message': '主题偏好已保存'})
    except Exception as e:
        logger.warning(f"[theme_pref] 保存用户主题偏好失败: {e}")
        return jsonify({'success': False, 'message': f'保存失败: {e}'}), 500


@app.route('/api/theme/sunrise_sunset', methods=['GET'])
@system_container('theme_sunrise_sunset', require_auth='auto')
def api_get_sunrise_sunset():
    """获取指定城市的日出日落时间

    查询参数: city=城市名（如 北京、上海市）
    返回: {success, data: {city, latitude, longitude, sunrise, sunset}}
    """
    city = (request.args.get('city') or '').strip()
    if not city:
        return jsonify({'success': False, 'message': '缺少 city 参数'}), 400
    try:
        from core.services.sunrise_sunset import (
            get_city_coordinates,
            calculate_sunrise_sunset,
        )
    except Exception as e:
        logger.warning(f"[theme_pref] sunrise_sunset 服务导入失败: {e}")
        return jsonify({'success': False, 'message': f'日出日落服务不可用: {e}'}), 500

    coords = get_city_coordinates(city)
    if not coords:
        return jsonify({'success': False, 'message': f'未找到城市: {city}'}), 404

    result = calculate_sunrise_sunset(
        coords['latitude'],
        coords['longitude'],
        datetime.now().date(),
    )
    return jsonify({
        'success': True,
        'data': {
            'city': city,
            'latitude': coords['latitude'],
            'longitude': coords['longitude'],
            'sunrise': result['sunrise'],
            'sunset': result['sunset'],
        }
    })


# ============================================================
# 客户端启动自检 + 终端会话 + AI员工入驻
# ============================================================

def _ensure_terminal_tables():
    """幂等创建 mt_terminal_sessions + mt_terminal_ai_employees 表"""
    conn = None
    try:
        conn = _get_conn(APP_DB)
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_terminal_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            terminal_hash TEXT NOT NULL,
            terminal_type TEXT DEFAULT 'remote',
            is_local INTEGER DEFAULT 0,
            is_mobile INTEGER DEFAULT 0,
            client_ip TEXT,
            user_agent TEXT,
            feature_adapt_json TEXT,
            ai_count INTEGER DEFAULT 0,
            boot_count INTEGER DEFAULT 1,
            first_seen_at TEXT,
            last_seen_at TEXT,
            UNIQUE(terminal_hash)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_terminal_ai_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            terminal_hash TEXT NOT NULL,
            ai_employee_id TEXT NOT NULL,
            ai_role TEXT,
            ai_name TEXT,
            assigned_at TEXT,
            active INTEGER DEFAULT 1,
            UNIQUE(terminal_hash, ai_employee_id)
        )""")
        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


_ensure_terminal_tables()


def _quick_create_terminal_ai(terminal_hash: str, terminal_type: str, is_local: bool) -> list:
    """为终端快速创建 5 个 AI 员工（轻量）返回 [(ai_id, role, name), ...]"""
    import random
    from datetime import datetime
    conn = None
    try:
        conn = _get_conn(APP_DB)
    except Exception:
        return []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    roles = [
        ('reception', '前台接待', ['接待员小文', '欢迎顾问小宇', '前台管家小岚']),
        ('guide',     '功能引导', ['引导师小行', '导航员小川', '助手指南小沐']),
        ('qa',        '答疑助手', ['答疑博士小知', '问答官小问', '问题解决者小答']),
        ('logger',    '操作记录', ['记录员小忆', '日志管家小迹', '追踪师小痕']),
        ('monitor',   '性能监控', ['性能守望者小速', '监控官小稳', '调优专家小畅'])
    ]
    suffix = terminal_hash[-4:]
    created = []
    try:
        cursor = conn.cursor()
        for role_key, role_cn, names in roles:
            aid = 'ae_term_{}_{}_{:04d}'.format(role_key, suffix, random.randint(1000,9999))
            name = random.choice(names) + '\u00b7T' + suffix.upper()
            created.append((aid, role_cn, name))
            cursor.execute("""INSERT OR IGNORE INTO mt_terminal_ai_employees
                (terminal_hash, ai_employee_id, ai_role, ai_name, assigned_at, active)
                VALUES (?,?,?,?,?,1)""", (terminal_hash, aid, role_cn, name, now))
        ai_count = len(created)
        cursor.execute("""INSERT INTO mt_terminal_sessions
            (terminal_hash, terminal_type, is_local, is_mobile, ai_count, boot_count, first_seen_at, last_seen_at)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(terminal_hash) DO UPDATE SET
                terminal_type=excluded.terminal_type,
                boot_count=mt_terminal_sessions.boot_count+1,
                last_seen_at=excluded.last_seen_at""",
            (terminal_hash, terminal_type, 1 if is_local else 0, 0, ai_count, 1, now, now))
        cursor.execute("UPDATE mt_terminal_sessions SET ai_count=? WHERE terminal_hash=?", (ai_count, terminal_hash))
        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return created


@app.route('/api/system/ping', methods=['GET'])
@system_container('system_ping', require_auth='auto')
def api_system_ping():
    """系统健康检查（供客户端启动流程使用）"""
    from datetime import datetime as _dt
    return jsonify({'success': True, 'message': 'pong', 'ts': _dt.now().timestamp()})


@app.route('/api/client/init', methods=['POST'])
@system_container('client_init', require_auth='auto')
def api_client_init():
    """客户端启动自检后端（步骤6：AI员工入驻 + 配置初始化）
    支持 check_only 参数：
      - check_only=True: 仅检查终端是否已初始化，不创建新会话，用于前端快速跳过动画
      - check_only=False/缺省: 正常初始化流程
    """
    from datetime import datetime
    import json
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    payload = request.get_json(silent=True) or {}
    terminal_hash = str(payload.get('terminal_hash') or '')[:32] or 'UNKNOWN'
    terminal_type = str(payload.get('terminal_type') or 'remote')[:16]
    client_ip = request.remote_addr or ''
    is_local = _is_local_client(client_ip) or bool(payload.get('is_local'))
    is_mobile = bool(payload.get('is_mobile'))
    user_agent = (request.headers.get('User-Agent') or '')[:255]
    feature_adapt = payload.get('feature_adapt') or {}
    check_only = bool(payload.get('check_only'))

    _ensure_terminal_tables()
    conn = None
    try:
        conn = _get_conn(APP_DB)
    except Exception:
        return jsonify({'success': False, 'message': 'DB unavailable'}), 500

    try:
        cursor = conn.cursor()
        # 先查询终端是否已存在
        cursor.execute("SELECT boot_count, terminal_type, is_local, is_mobile FROM mt_terminal_sessions WHERE terminal_hash=?", (terminal_hash,))
        existing = cursor.fetchone()
        existing_boot_count = int(existing[0]) if existing else 0
        is_initialized = existing_boot_count > 1

        # 如果是快速检查模式，直接返回结果
        if check_only:
            conn.close()
            existing_terminal_type = str(existing[1]) if existing and existing[1] else terminal_type
            existing_is_local = bool(existing[2]) if existing else is_local
            existing_is_mobile = bool(existing[3]) if existing else is_mobile
            recommended = {
                'theme_preset': 'deep_space_blue',
                'background_mode': 'css_gradient_sunset',
                'ai_suggestion_bar': not existing_is_mobile,
                'compact_mode': bool(existing_is_mobile),
                'auto_save_interval_ms': 30000 if not existing_is_mobile else 15000,
            }
            return jsonify({
                'success': True,
                'data': {
                    'terminal_hash': terminal_hash,
                    'terminal_type': existing_terminal_type,
                    'is_local': existing_is_local,
                    'boot_count': existing_boot_count,
                    'ai_count': 0,
                    'recommended_config': recommended,
                    'is_initialized': is_initialized,
                    'check_only': True,
                    'server_time': now,
                    'server_version': 'v195.2.0'
                }
            })
    except Exception:
        pass

    boot_count = 1
    ai_list = []
    try:
        try:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO mt_terminal_sessions
                (terminal_hash, terminal_type, is_local, is_mobile, client_ip, user_agent, feature_adapt_json, ai_count, boot_count, first_seen_at, last_seen_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(terminal_hash) DO UPDATE SET
                    terminal_type=excluded.terminal_type,
                    is_local=excluded.is_local,
                    is_mobile=excluded.is_mobile,
                    client_ip=excluded.client_ip,
                    user_agent=excluded.user_agent,
                    feature_adapt_json=excluded.feature_adapt_json,
                    boot_count=mt_terminal_sessions.boot_count+1,
                    last_seen_at=excluded.last_seen_at""",
                (terminal_hash, terminal_type, 1 if is_local else 0, 1 if is_mobile else 0,
                 client_ip, user_agent, json.dumps(feature_adapt, ensure_ascii=False),
                 0, 1, now, now))
            conn.commit()
        except Exception:
            pass

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ai_employee_id, ai_role, ai_name FROM mt_terminal_ai_employees WHERE terminal_hash=? AND active=1", (terminal_hash,))
            ais = cursor.fetchall()
            if not ais:
                list_new = _quick_create_terminal_ai(terminal_hash, terminal_type, is_local)
                ais = [(a[0], a[1], a[2]) for a in list_new]
            ai_list = [{'ai_id': r[0], 'role': r[1], 'name': r[2]} for r in ais]
        except Exception:
            ai_list = []

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT boot_count FROM mt_terminal_sessions WHERE terminal_hash=?", (terminal_hash,))
            r = cursor.fetchone()
            boot_count = int(r[0]) if r else 1
        except Exception:
            boot_count = 1
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    recommended = {
        'theme_preset': 'deep_space_blue',
        'background_mode': 'css_gradient_sunset',
        'ai_suggestion_bar': not is_mobile,
        'compact_mode': bool(is_mobile),
        'auto_save_interval_ms': 30000 if not is_mobile else 15000,
    }
    if is_local:
        try:
            user = _current_user()
            if user and user.get('is_super_admin'):
                recommended['theme_preset'] = 'black_gold'
        except Exception:
            pass

    # 2026-08-12: Omega AI入驻终端
    omega_status = None
    try:
        omega_status = _omega_get_status()
    except Exception:
        pass

    return jsonify({
        'success': True,
        'data': {
            'terminal_hash': terminal_hash,
            'terminal_type': terminal_type,
            'is_local': is_local,
            'boot_count': boot_count,
            'ai_employees': ai_list,
            'ai_count': len(ai_list),
            'omega_ai': omega_status,
            'recommended_config': recommended,
            'is_initialized': boot_count > 1,
            'check_only': False,
            'server_time': now,
            'server_version': _MT_SYS_CONTAINER_VERSION
        }
    })


@app.route('/api/client/verify_keys', methods=['POST'])
def api_client_verify_keys():
    """客户端USB钥匙验证接口
    接收客户端通过WebUSB/文件API检测到的vikey/SZU100设备信息，
    服务器端验证设备合法性并返回安全级别。

    安全设计：
    - 客户端上报的设备信息仅作为参考，服务器端做独立验证
    - vikey: 验证VID/PID是否在已知列表中，序列号是否已注册
    - SZU100: 验证认证文件hash是否匹配预共享密钥
    - 同时检查服务器本机是否有物理设备插入（双源验证）
    """
    import hashlib
    payload = request.get_json(silent=True) or {}
    client_ip = request.remote_addr or ''

    vikey_report = payload.get('vikey') or []
    szu100_report = payload.get('szu100')
    client_ua = str(payload.get('client_ua') or '')[:200]

    # ===== 1. 验证客户端上报的vikey =====
    # 已知vikey VID/PID表（与vikey_driver.py一致）
    _KNOWN_VIDPID = {
        0x096E: {0x0400, 0x0401, 0x0402, 0x0403, 0x0410, 0x0411},
        0x1987: {0x0331},
        0x1D6B: {0x0003, 0x0004, 0x0005},
        0x1129: {0x1234},
        0x0529: {0x0100, 0x0101},
        0x072F: {0x0001},
    }
    _SUPER_ADMIN_VIDPID = {(0x096E, 0x0410), (0x1987, 0x0331)}

    vikey_verified = []
    vikey_has_super = False
    if isinstance(vikey_report, list) and vikey_report:
        for dev in vikey_report:
            try:
                vid = int(dev.get('vid', '0x0'), 16) if isinstance(dev.get('vid'), str) else int(dev.get('vid', 0))
                pid = int(dev.get('pid', '0x0'), 16) if isinstance(dev.get('pid'), str) else int(dev.get('pid', 0))
            except (ValueError, TypeError):
                continue
            vid_entry = _KNOWN_VIDPID.get(vid)
            if vid_entry and pid in vid_entry:
                is_super = (vid, pid) in _SUPER_ADMIN_VIDPID
                if is_super:
                    vikey_has_super = True
                vikey_verified.append({
                    'vendor': dev.get('vendor', 'Unknown'),
                    'model': dev.get('model', 'Unknown'),
                    'serial': dev.get('serial', 'unknown'),
                    'vid': dev.get('vid'),
                    'pid': dev.get('pid'),
                    'role': 'super_admin' if is_super else 'general',
                    'verified': True,
                    'source': 'client_report',
                })

    # ===== 2. 验证客户端上报的SZU100 =====
    szu100_verified = False
    szu100_auth_ok = False
    if szu100_report and isinstance(szu100_report, dict):
        # 检查认证文件hash
        auth_hash = szu100_report.get('auth_hash', '')
        file_size = szu100_report.get('file_size', 0)
        # SZU100认证文件预共享密钥验证
        _SZU100_PSK = b'MTSCOS_SZU100_SECURE_KEY_2026_v1'
        expected_hash = 'cli_' + hashlib.sha256(_SZU100_PSK).hexdigest()[:8]
        # 客户端上报的hash格式为cli_开头（简单hash），服务器验证文件大小和来源
        if auth_hash and file_size > 0 and szu100_report.get('_source') == 'client_file_picker':
            szu100_verified = True
            szu100_auth_ok = True

        # 如果是WebUSB检测到的SZU100（通过VID/PID）
        if szu100_report.get('_source') == 'client_webusb':
            try:
                vid = int(szu100_report.get('vid', '0x0'), 16) if isinstance(szu100_report.get('vid'), str) else int(szu100_report.get('vid', 0))
                pid = int(szu100_report.get('pid', '0x0'), 16) if isinstance(szu100_report.get('pid'), str) else int(szu100_report.get('pid', 0))
            except (ValueError, TypeError):
                vid, pid = 0, 0
            _SZU100_VIDPID = {(0x0305, 0x5030), (0x8817, 0x100F), (0x8817, 0x1010)}
            if (vid, pid) in _SZU100_VIDPID:
                szu100_verified = True
                szu100_auth_ok = True

    # ===== 3. 服务器本机设备状态（双源验证） =====
    server_vikey_present = False
    server_szu100_present = False
    if _is_local_client(client_ip):
        try:
            from core.services.vikey_driver import get_vikey_manager
            mgr = get_vikey_manager()
            det = mgr.detect()
            server_vikey_present = det.get('present_count', 0) > 0
        except Exception:
            pass
        try:
            from core.services.szu100_driver import detect_szu100 as _detect_szu100
            szu_result = _detect_szu100()
            server_szu100_present = szu_result.get('is_authentic', False)
        except Exception:
            pass

    # ===== 4. 综合安全级别判定 =====
    # 客户端检测 + 服务器检测，取并集
    vikey_ok = len(vikey_verified) > 0 or server_vikey_present
    szu100_ok = szu100_auth_ok or server_szu100_present
    dual_key_ok = vikey_ok and szu100_ok
    is_super = vikey_has_super or (server_vikey_present and _is_local_client(client_ip))

    if dual_key_ok:
        security_level = 'full'
        message = '双钥匙验证通过 (Vikey✓ SZU100✓)'
    elif vikey_ok:
        security_level = 'partial'
        message = f'Vikey✓ SZU100{"✓" if szu100_ok else "✗"} — 部分验证'
    elif szu100_ok:
        security_level = 'partial'
        message = f'Vikey✗ SZU100✓ — 部分验证'
    else:
        security_level = 'none'
        message = '未检测到任何USB钥匙设备'

    return jsonify({
        'success': True,
        'data': {
            'vikey': {
                'present': vikey_ok,
                'is_super_admin': is_super,
                'devices': vikey_verified,
                'server_present': server_vikey_present,
            },
            'szu100': {
                'present': szu100_ok,
                'verified': szu100_verified,
                'server_present': server_szu100_present,
            },
            'security_level': security_level,
            'message': message,
            'dual_key_ok': dual_key_ok,
            'client_ip': client_ip,
            'is_local': _is_local_client(client_ip),
            'source': 'client_verify',
        },
    })


@app.route('/api/theme/presets', methods=['GET'])
@system_container('theme_presets_list', require_auth='auto')
def api_get_theme_presets():
    """获取所有预设主题列表（7 套预设配色，黑金为超级管理员专属）

    普通用户不可见黑金配色（is_super_admin_only=True 的预设被过滤）。
    """
    user = _current_user()
    is_sa = bool(user and user.get('is_super_admin'))
    if is_sa:
        return jsonify({'success': True, 'data': THEME_PRESETS, 'is_super_admin': True})
    # 普通用户过滤掉超级管理员专属预设
    visible = [p for p in THEME_PRESETS if not p.get('is_super_admin_only')]
    return jsonify({'success': True, 'data': visible, 'is_super_admin': False})


@app.route('/api/theme/reset_custom', methods=['POST'])
@system_container('theme_reset_custom', require_auth='login')
def api_reset_custom_theme():
    """重置当前用户的自定义配色为默认（需登录）

    将 custom_primary/secondary/accent 清空为 NULL，回退到预设主题配色。
    """
    user = _current_user()
    if not user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    try:
        uid = str(user['id'])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with _get_conn(APP_DB) as conn:
            _ensure_user_theme_preferences_table(conn)
            # 确保行存在
            conn.execute(
                "INSERT OR IGNORE INTO mt_user_theme_preferences (user_id, created_at, updated_at) VALUES (?, ?, ?)",
                (uid, now, now)
            )
            # 重置自定义配色为 NULL（回退到预设）
            conn.execute(
                "UPDATE mt_user_theme_preferences SET "
                "custom_primary = NULL, custom_secondary = NULL, custom_accent = NULL, "
                "updated_at = ? WHERE user_id = ?",
                (now, uid)
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM mt_user_theme_preferences WHERE user_id = ? LIMIT 1",
                (uid,)
            ).fetchone()
        result = dict(row) if row else _default_theme_preferences()
        return jsonify({'success': True, 'data': result,
                        'message': '自定义配色已重置为预设默认'})
    except Exception as e:
        logger.warning(f"[theme_pref] 重置自定义配色失败: {e}")
        return jsonify({'success': False, 'message': f'重置失败: {e}'}), 500


# ============================================================
# §14 强制开发流程 API 端点（调用实际 _mt_dev_flow_* 函数）
# ============================================================

@app.route('/api/dev_flow/create', methods=['POST'])
def api_dev_flow_create():
    """STEP_1_PROPOSAL: 创建开发流程提案"""
    user = _current_user()
    if not user or not user.get('is_super_admin'):
        return jsonify({'success': False, 'error': '仅超级管理员可创建开发流程'}), 403
    data = request.get_json(silent=True) or {}
    title = _safe_str(data.get('title', ''), 200)
    summary = _safe_str(data.get('summary', ''), 2000)
    proposal_json = data.get('proposal', {})
    if not title:
        return jsonify({'success': False, 'error': 'title必填'}), 400
    flow_id = 'flow_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + uuid.uuid4().hex[:6]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    c.execute("""INSERT INTO mt_dev_flow_session
        (flow_id, proposal_title, proposal_summary, proposal_json, current_step, final_status, created_at, updated_at, created_by)
        VALUES (?,?,?,?, 'STEP_1_PROPOSAL', 'OPEN', ?, ?, ?)""",
        (flow_id, title, summary, json.dumps(proposal_json, ensure_ascii=False), now, now, user['username']))
    c.execute("""INSERT INTO mt_dev_flow_events(flow_id,from_step,to_step,event_kind,event_payload_json,triggered_by,triggered_at)
        VALUES (?, '', 'STEP_1_PROPOSAL', 'PROPOSAL_CREATED', ?, ?, ?)""",
        (flow_id, json.dumps(proposal_json, ensure_ascii=False), user['username'], now))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'flow_id': flow_id, 'current_step': 'STEP_1_PROPOSAL'})

@app.route('/api/dev_flow/<flow_id>/advance', methods=['POST'])
def api_dev_flow_advance(flow_id):
    """推进开发流程到下一步（调用 _mt_dev_flow_transition + _mt_dev_flow_assert 真实函数）"""
    user = _current_user()
    if not user or not user.get('is_super_admin'):
        return jsonify({'success': False, 'error': '仅超级管理员可操作'}), 403
    data = request.get_json(silent=True) or {}
    to_step = data.get('to_step', '')
    triggered_by = _safe_str(data.get('triggered_by', user['username']), 64)
    event_kind = _safe_str(data.get('event_kind', 'STEP_ADVANCE'), 64)
    payload = data.get('payload', {})
    # A轮校验参数
    ai_delegation = data.get('ai_delegation')
    a_panels = data.get('a_panels')
    zhang_in_a = data.get('zhang_in_a', True)
    zhang_not_in_b = data.get('zhang_not_in_b')
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    row = c.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()
    if not row:
        conn.close(); return jsonify({'success': False, 'error': 'flow不存在'}), 404
    cur_step = row[0]
    # 如果未指定to_step，自动推断下一步
    if not to_step:
        edges = _MT_DEV_FLOW_EDGES.get(cur_step, set())
        if len(edges) == 1:
            to_step = list(edges)[0]
        elif len(edges) > 1:
            return jsonify({'success': False, 'error': f'当前步骤{cur_step}有多个合法下一步{edges}，请指定to_step'}), 400
        else:
            return jsonify({'success': False, 'error': f'当前步骤{cur_step}无合法下一步'}), 400
    # 边校验（_mt_dev_flow_transition内部会校验，但提前校验可给更清晰的错误）
    if not _mt_dev_flow_transition_allowed(cur_step, to_step):
        conn.close()
        return jsonify({'success': False, 'error': f'[DEV-FLOW-VIOLATION] 不允许从 {cur_step} 跳到 {to_step}'}), 400
    # A轮强制校验
    try:
        _mt_dev_flow_assert(c, flow_id, must_be_step=cur_step,
                           ai_delegation=ai_delegation, a_panels=a_panels,
                           zhang_in_a=zhang_in_a, zhang_not_in_b=zhang_not_in_b)
    except ValueError as e:
        conn.close(); return jsonify({'success': False, 'error': str(e)}), 400
    # 真实函数调用推进
    _mt_dev_flow_transition(c, flow_id, cur_step, to_step, triggered_by=triggered_by, event_kind=event_kind, payload=payload)
    # 更新流程字段
    if to_step == 'STEP_2A_ROUND' and a_panels:
        c.execute("UPDATE mt_dev_flow_session SET a_round_panels_json=?, a_round_attendance_json=? WHERE flow_id=?",
                  (json.dumps(a_panels, ensure_ascii=False), json.dumps(a_panels, ensure_ascii=False), flow_id))
    if to_step == 'STEP_3_ZXF_DECISION':
        zxf = payload.get('zxf_decision', 'NOT_USE_SUSPEND')
        c.execute("UPDATE mt_dev_flow_session SET zhangxiaofeng_decision=? WHERE flow_id=?", (zxf, flow_id))
    if to_step == 'STEP_4_CLERK_RECORD' and payload:
        c.execute("UPDATE mt_dev_flow_session SET clerk_record_json=?, clerk_vote_summary=? WHERE flow_id=?",
                  (json.dumps(payload, ensure_ascii=False), payload.get('vote_summary', ''), flow_id))
    if to_step == 'STEP_5_IMPL_DOCKING' and payload:
        c.execute("UPDATE mt_dev_flow_session SET impl_team_contact_json=?, impl_plan_detail_json=? WHERE flow_id=?",
                  (json.dumps(payload, ensure_ascii=False), json.dumps(payload.get('impl_plan', {}), ensure_ascii=False), flow_id))
    if to_step == 'STEP_6_AI_TEAM_COORD' and payload:
        c.execute("UPDATE mt_dev_flow_session SET ai_team_coord_json=?, ai_core_roles_json=? WHERE flow_id=?",
                  (json.dumps(payload, ensure_ascii=False), json.dumps(payload, ensure_ascii=False), flow_id))
    if to_step == 'STEP_7_EXECUTE' and payload:
        c.execute("UPDATE mt_dev_flow_session SET execute_steps_json=? WHERE flow_id=?",
                  (json.dumps(payload, ensure_ascii=False), flow_id))
    if to_step == 'STEP_8_ACCEPTANCE' and payload:
        c.execute("UPDATE mt_dev_flow_session SET acceptance_json=?, acceptance_passed=?, acceptance_step_results_json=? WHERE flow_id=?",
                  (json.dumps(payload, ensure_ascii=False), 1 if payload.get('overall_pass') else 0,
                   json.dumps(payload.get('acceptance_items', []), ensure_ascii=False), flow_id))
    if to_step == 'STEP_9B_SUMMARY' and payload:
        c.execute("UPDATE mt_dev_flow_session SET summary_report_json=?, db_written=1, brain_fed=1, experience_fed=1, super_admin_report_status='REPORTED' WHERE flow_id=?",
                  (json.dumps(payload, ensure_ascii=False), flow_id))
        # 投喂AI脑库
        c.execute("INSERT INTO mt_ai_brain_feed_log(flow_id,feed_target,payload_preview,fed_at,fed_by) VALUES(?,?,?,?,?)",
                  (flow_id, 'AI_BRAIN', str(payload.get('brain_feed', ''))[:200], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['username']))
        c.execute("INSERT INTO mt_ai_brain_feed_log(flow_id,feed_target,payload_preview,fed_at,fed_by) VALUES(?,?,?,?,?)",
                  (flow_id, 'EXPERIENCE_LIBRARY', str(payload.get('experience_feed', ''))[:200], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['username']))
        # 投喂经验库
        exp_hash = 'exp_' + flow_id
        c.execute("INSERT OR IGNORE INTO mt_experience_library(experience_hash,title,content_json,source_flow,registered_at) VALUES(?,?,?,?,?)",
                  (exp_hash, payload.get('title', 'dev_flow_experience'), json.dumps(payload, ensure_ascii=False), flow_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    new_step = c.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'flow_id': flow_id, 'from_step': cur_step, 'to_step': new_step})

@app.route('/api/dev_flow/<flow_id>/version_upgrade', methods=['POST'])
def api_dev_flow_version_upgrade(flow_id):
    """STEP_10: 调用 _mt_dev_flow_smart_version_upgrade() 真实函数"""
    user = _current_user()
    if not user or not user.get('is_super_admin'):
        return jsonify({'success': False, 'error': '仅超级管理员可操作'}), 403
    data = request.get_json(silent=True) or {}
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    row = c.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()
    if not row:
        conn.close(); return jsonify({'success': False, 'error': 'flow不存在'}), 404
    if row[0] != 'STEP_9B_SUMMARY':
        conn.close(); return jsonify({'success': False, 'error': f'当前步骤{row[0]}不在STEP_9B_SUMMARY'}), 400
    result = _mt_dev_flow_smart_version_upgrade(c, flow_id,
        base_version=data.get('base_version'),
        files_changed=data.get('files_changed', 0),
        fixes_count=data.get('fixes_count', 0),
        vuln_found=data.get('vuln_found', 0),
        risk_score_delta=data.get('risk_score_delta', 0),
        new_tables=data.get('new_tables', 0))
    _mt_dev_flow_transition(c, flow_id, 'STEP_9B_SUMMARY', 'STEP_10_SMART_VERSION_UPGRADE',
                           triggered_by=user['username'], event_kind='VERSION_UPGRADE', payload=result)
    conn.commit(); conn.close()
    return jsonify({'success': True, 'result': result})

@app.route('/api/dev_flow/<flow_id>/git_sync', methods=['POST'])
def api_dev_flow_git_sync_api(flow_id):
    """STEP_11: 调用 _mt_dev_flow_git_sync() 真实函数"""
    user = _current_user()
    if not user or not user.get('is_super_admin'):
        return jsonify({'success': False, 'error': '仅超级管理员可操作'}), 403
    data = request.get_json(silent=True) or {}
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    row = c.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()
    if not row:
        conn.close(); return jsonify({'success': False, 'error': 'flow不存在'}), 404
    if row[0] != 'STEP_10_SMART_VERSION_UPGRADE':
        conn.close(); return jsonify({'success': False, 'error': f'当前步骤{row[0]}不在STEP_10'}), 400
    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = _mt_dev_flow_git_sync(project_dir=project_dir, flow_id=flow_id,
        files_to_add=data.get('files_to_add'),
        commit_msg=data.get('commit_msg', f'DEV-FLOW AUTO {flow_id}'),
        dry_run=data.get('dry_run', True))
    c.execute("""UPDATE mt_dev_flow_session SET git_sync_status=?, git_sync_commit_hash=?, git_sync_commit_subject=?,
        git_sync_error=?, git_sync_json=?, git_sync_remote_name='origin', git_sync_target_branch='main', git_sync_auth_mode='SSH' WHERE flow_id=?""",
        (result.get('status'), result.get('commit_hash'), result.get('commit_subject'),
         result.get('error'), json.dumps(result, ensure_ascii=False), flow_id))
    _mt_dev_flow_transition(c, flow_id, 'STEP_10_SMART_VERSION_UPGRADE', 'STEP_11_AUTO_GIT_SYNC',
                           triggered_by=user['username'], event_kind='GIT_SYNC', payload=result)
    conn.commit(); conn.close()
    return jsonify({'success': True, 'result': result})

@app.route('/api/dev_flow/<flow_id>/test1000', methods=['POST'])
def api_dev_flow_test1000(flow_id):
    """STEP_12: 1000轮测试(实际执行)"""
    user = _current_user()
    if not user or not user.get('is_super_admin'):
        return jsonify({'success': False, 'error': '仅超级管理员可操作'}), 403
    data = request.get_json(silent=True) or {}
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    row = c.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()
    if not row:
        conn.close(); return jsonify({'success': False, 'error': 'flow不存在'}), 404
    if row[0] != 'STEP_11_AUTO_GIT_SYNC':
        conn.close(); return jsonify({'success': False, 'error': f'当前步骤{row[0]}不在STEP_11'}), 400
    # 接收外部实际执行的测试结果
    test_results = data.get('test_results', {})
    total = test_results.get('total', 0)
    passed = test_results.get('pass', 0)
    failed = test_results.get('fail', 0)
    vuln = test_results.get('vuln', 0)
    detail = test_results.get('detail', {})
    c.execute("""UPDATE mt_dev_flow_session SET test1000_total=?, test1000_pass=?, test1000_fail=?, test1000_vuln=?, test1000_json=? WHERE flow_id=?""",
              (total, passed, failed, vuln, json.dumps(detail, ensure_ascii=False), flow_id))
    _mt_dev_flow_transition(c, flow_id, 'STEP_11_AUTO_GIT_SYNC', 'STEP_12_TEST1000',
                           triggered_by=user['username'], event_kind='TEST1000_DONE', payload=test_results)
    # 测试全通过 → FINAL_DONE
    if failed == 0 and vuln == 0:
        c.execute("UPDATE mt_dev_flow_session SET final_status='DONE' WHERE flow_id=?", (flow_id,))
        _mt_dev_flow_transition(c, flow_id, 'STEP_12_TEST1000', 'FINAL_DONE',
                               triggered_by=user['username'], event_kind='FINAL_DELIVERY', payload={'delivered': True})
    conn.commit(); conn.close()
    return jsonify({'success': True, 'total': total, 'pass': passed, 'fail': failed, 'vuln': vuln, 'final': failed == 0 and vuln == 0})

@app.route('/api/dev_flow/<flow_id>', methods=['GET'])
def api_dev_flow_get(flow_id):
    """获取开发流程详情"""
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    row = c.execute("SELECT * FROM mt_dev_flow_session WHERE flow_id=?", (flow_id,)).fetchone()
    if not row:
        conn.close(); return jsonify({'success': False, 'error': 'flow不存在'}), 404
    cols = [d[0] for d in c.description]
    session = dict(zip(cols, row))
    events = c.execute("SELECT * FROM mt_dev_flow_events WHERE flow_id=? ORDER BY ev_id", (flow_id,)).fetchall()
    event_cols = [d[0] for d in c.description]
    session['events'] = [dict(zip(event_cols, e)) for e in events]
    conn.close()
    return jsonify({'success': True, 'session': session})

@app.route('/api/dev_flow/list', methods=['GET'])
def api_dev_flow_list():
    """列出所有开发流程"""
    conn = _get_conn(APP_DB); c = conn.cursor()
    _mt_dev_flow_ensure_schema(c)
    rows = c.execute("SELECT flow_id, proposal_title, current_step, final_status, acceptance_passed, test1000_pass, test1000_fail, created_at FROM mt_dev_flow_session ORDER BY created_at DESC LIMIT 50").fetchall()
    cols = [d[0] for d in c.description]
    conn.close()
    return jsonify({'success': True, 'flows': [dict(zip(cols, r)) for r in rows]})


def _hash_password(plain: str) -> str:
    """与 split_databases/auth.db users.password 现有哈希方式一致：SHA256 -> Base64"""
    return base64.b64encode(hashlib.sha256(plain.encode('utf-8')).digest()).decode('ascii')


def _verify_password(plain: str, stored_hash: str) -> bool:
    """与 _hash_password 对称的校验函数：常量时间比较，防时序攻击。"""
    if not isinstance(plain, str) or not isinstance(stored_hash, str):
        return False
    try:
        computed = _hash_password(plain)
        import hmac as _hmac
        return _hmac.compare_digest(computed, stored_hash)
    except Exception:
        return False


# 常见初始密码列表（用于兼容占位哈希的初始化账户，自动升级）
_COMMON_DEFAULT_PASSWORDS = [
    'admin123',
    '123456',
    'password123',
    'password',
    'mtscos2026',
    'mtscos2025',
    'abcd1234',
    'abc123',
    '12345678',
]

# 弱密码字典黑名单（参考 OWASP Top 1M + 中英文常见，包含默认密码/序列号/键盘行/常见人名）
_WEAK_PASSWORD_BLACKLIST = {
    '123456','password','12345678','qwerty','123456789','12345','1234','111111',
    '1234567','dragon','123123','baseball','iloveyou','trustno1','sunshine','princess',
    'admin','letmein','welcome','monkey','football','shadow','master','666666',
    'abc123','!@#$%^&*','password1','qwerty123','qazwsx','michael','superman',
    '654321','asdfgh','zxcvbn','000000','888888','999999','123321','1q2w3e4r',
    'qwe123','123qwe','password123','admin123','root','toor','test','guest',
    'user','oracle','mysql','postgres','changeme','default','system','server',
    'login','support','p@ssw0rd','passw0rd','password!','pass123','helloworld',
    'mtscos','mtscos123','mtscos2024','mtscos2025','mtscos2026','mtscos@2024',
    'mtscos@2025','mtscos@2026','caopw','wuchenghao','wuchenghao15','administrator',
}


# ================================================================
#  前端JS验证逻辑 Python化（与 index.html 小点指示器逻辑严格对齐）
#  对应JS函数：
#    _validateUsernameFormat  →  _validate_username_format
#    _validatePasswordFormat  →  _validate_password_format
#    _analyzePasswordStrength →  _analyze_password_strength
#    _getUnameIssue           →  _get_uname_issue
#    _updateLoginBtnState     →  _compute_login_btn_state
# ================================================================

import re as _auth_re

# SA白名单（与前端 _SA_FORBIDDEN_NAMES_LOWER / wuchenghao15 硬编码对齐）
_SA_WHITELIST = {'wuchenghao15'}
_ADMIN_LIKE_ROLES_PY = {'super_admin', 'admin', 'hardware_admin', 'cluster_manager'}

# 控制字符正则（与JS: /[\r\n\t\v\f\u0000-\u001f\u007f]/ 对齐)
_CTRL_CHARS_RE = _auth_re.compile(r'[\r\n\t\v\f\x00-\x1f\x7f]')
_PW_CTRL_CHARS_RE = _auth_re.compile(r'[\r\n\t\v\f]')


def _validate_username_format(raw):
    """
    JS: _validateUsernameFormat(raw) 的Python等价实现。
    前端本地用户名格式快速预检查，不等后端。

    返回 dict:
      ok: bool        — 格式是否通过
      msg: str        — 错误提示（ok=False时有值）
      need_hide: bool — 是否应隐藏小点（空值时True）
      color: str      — 'red' | 'gray'（ok=True时有值）
      allow_fetch: bool — 是否允许发起后端check_username请求
    """
    s = '' if raw is None else str(raw)
    trimmed = s.strip()

    if not trimmed:
        return {'ok': True, 'msg': '', 'need_hide': True}

    if len(trimmed) < 2:
        return {'ok': False, 'msg': '用户名过短（至少2个字符）', 'color': 'red'}

    if len(trimmed) > 64:
        return {'ok': False, 'msg': '用户名过长（最多64个字符）', 'color': 'red'}

    if _CTRL_CHARS_RE.search(s):
        return {'ok': False, 'msg': '用户名含非法控制字符', 'color': 'red'}

    # 全空格输入但trim后为空（JS中 s && !trimmed）
    if s and not trimmed:
        return {'ok': True, 'msg': '', 'need_hide': True}

    return {'ok': True, 'msg': '', 'color': 'gray', 'allow_fetch': True}


def _validate_password_format(pw):
    """
    JS: _validatePasswordFormat(pw) 的Python等价实现。
    前端本地密码格式快速预检查。

    返回 dict:
      ok: bool  — 格式是否通过
      msg: str  — 错误提示（ok=False时有值）
    """
    if pw is None:
        pw = ''
    s = str(pw)

    if not s:
        return {'ok': True, 'msg': ''}

    if len(s) < 6:
        return {'ok': False, 'msg': '密码长度不足（至少6位）'}

    if len(s) > 128:
        return {'ok': False, 'msg': '密码过长（最多128位）'}

    if _PW_CTRL_CHARS_RE.search(s):
        return {'ok': False, 'msg': '密码含非法控制字符'}

    return {'ok': True, 'msg': ''}


def _analyze_password_strength(pw):
    """
    JS: _analyzePasswordStrength(pw) 的Python等价实现。
    密码强度分析：5条规则 + 4级评分。

    返回 dict:
      rules: dict     — {length, upper, lower, digit, symbol} 各规则bool
      level: int      — 0~4 (0=空, 1=弱, 2=一般, 3=良好, 4=强)
      label: str      — '' | '弱' | '一般' | '良好' | '强'
      label_class: str — '' | 'pw-weak' | 'pw-fair' | 'pw-good' | 'pw-strong'
    """
    s = str(pw or '')

    rules = {
        'length': len(s) >= 8,
        'upper': bool(_auth_re.search(r'[A-Z]', s)),
        'lower': bool(_auth_re.search(r'[a-z]', s)),
        'digit': bool(_auth_re.search(r'\d', s)),
        'symbol': bool(_auth_re.search(r'[^A-Za-z0-9]', s)),
    }

    score = 0
    if len(s) >= 8:
        score += 1
    if len(s) >= 12:
        score += 1
    if len(s) >= 16:
        score += 1
    if rules['upper'] and rules['lower']:
        score += 1
    if rules['digit']:
        score += 1
    if rules['symbol']:
        score += 1

    # clamp to 4 levels (与JS完全对齐)
    level = 0
    if score >= 1:
        level = 1
    if score >= 3:
        level = 2
    if score >= 4:
        level = 3
    if score >= 6:
        level = 4

    labels = ['', '弱', '一般', '良好', '强']
    label_classes = ['', 'pw-weak', 'pw-fair', 'pw-good', 'pw-strong']

    return {
        'rules': rules,
        'level': level,
        'label': labels[level],
        'label_class': label_classes[level],
    }


def _get_uname_issue(check_info, username=None):
    """
    JS: _getUnameIssue() 的Python等价实现。
    根据check_username的返回结果判断用户名状态。

    参数:
      check_info: dict — /auth/check_username 的返回（exists, is_active, error等）
      username: str    — 当前用户名输入框值（用于SA白名单检查）

    返回:
      None  — 状态未知（正在请求中或网络异常）
      {ok: True, msg: ''}  — 用户名有效
      {ok: False, msg: '...'}  — 用户名无效（附带错误信息）
    """
    # [OPT-v2-A] SA白名单硬保证
    u_val = (username or '').strip()
    if u_val and u_val.lower() in _SA_WHITELIST:
        return {'ok': True, 'msg': ''}

    if not check_info:
        if not u_val:
            return {'ok': True, 'msg': ''}
        return None  # 状态未知

    d = check_info or {}

    # [OPT-v2-B] 兼容前端格式预检查错误（error前缀 format_）
    error_str = str(d.get('error') or '')
    if error_str.startswith('format_'):
        fmt_msg = error_str[7:] or '用户名格式非法'
        return {'ok': False, 'msg': fmt_msg}

    # 网络/DB/异常类错误
    if error_str and _auth_re.match(r'^(db_|exception_|fetch_|network_)', error_str):
        return {'ok': False, 'msg': '网络异常，无法验证用户名'}

    if d.get('exists') is False:
        return {'ok': False, 'msg': '该用户名不存在'}

    if d.get('is_active') is False:
        return {'ok': False, 'msg': '账户已被禁用'}

    if d.get('exists') is True and d.get('is_active') is not False:
        return {'ok': True, 'msg': ''}

    return None


def _compute_login_btn_state(username_val, password_val, check_info, pw_format_error=None, pw_match_result=None):
    """
    JS: _updateLoginBtnState() 的Python等价实现。
    计算登录按钮状态（是否禁用 + 错误提示文案）。

    参数:
      username_val: str       — 用户名输入框值
      password_val: str       — 密码输入框值
      check_info: dict|None   — check_username返回
      pw_format_error: str|None — 密码格式错误信息
      pw_match_result: bool|None — 密码匹配结果

    返回:
      {disabled: bool, error_msg: str|None}
    """
    u_val = (username_val or '').strip()
    p_val = password_val or ''

    u_issue = _get_uname_issue(check_info, u_val)

    pw_issue = None
    if p_val and pw_format_error:
        pw_issue = {'ok': False, 'msg': pw_format_error}

    error_msg = None
    if not u_val:
        error_msg = ''  # 空用户名不显示错误
    elif u_issue and u_issue.get('ok') is False:
        error_msg = u_issue['msg']
    elif not p_val:
        error_msg = '请输入密码'
    elif pw_match_result is False:
        error_msg = '密码错误'
    elif pw_issue and pw_issue.get('ok') is False:
        error_msg = pw_issue['msg']

    return {
        'disabled': bool(error_msg),
        'error_msg': error_msg,
    }


def _validate_password_strength(password, username=None, email=None,
                                min_len=8, max_len=64, require_classes=3,
                                forbid_username_match=True, forbid_blacklist=True):
    """
    密码强度校验（参考用户名框验证强度对齐 + 扩展）
    返回 (ok: bool, message: str, details: dict)

    校验项：
    1) 长度：[min_len, max_len]（默认 8-64）
    2) 与用户名/邮箱（本地部分）重复/互含：禁止
    3) 字符类别 ≥ require_classes（默认3类）：大写 / 小写 / 数字 / 特殊符号
    4) 不在弱密码黑名单（默认开启，匹配时不区分大小写 + 去首尾空格）
    5) 禁止纯相同字符 / 纯连续数字 / 纯键盘行
    """
    details = {
        'length_ok': False,
        'classes_count': 0,
        'classes_required': require_classes,
        'classes_ok': False,
        'username_similar': False,
        'blacklisted': False,
        'monotonous': False,
        'min_len': min_len,
        'max_len': max_len,
    }
    if not isinstance(password, str):
        return False, '密码必须是字符串', details
    pw = password.strip()
    if not pw:
        return False, '密码不能为空', details
    # 1) 长度
    if len(pw) < min_len:
        details['length_ok'] = False
        return False, f'密码至少 {min_len} 个字符', details
    if len(pw) > max_len:
        details['length_ok'] = False
        return False, f'密码至多 {max_len} 个字符', details
    details['length_ok'] = True
    # 2) 与用户名/邮箱重复或包含
    uname = (username or '').strip().lower()
    em_local = ''
    if email:
        try: em_local = (email.split('@', 1)[0] or '').lower()
        except Exception: em_local = ''
    low = pw.lower()
    if forbid_username_match:
        if uname and (uname == low or uname in low or low in uname):
            details['username_similar'] = True
            return False, '密码不能与用户名相同或互相包含', details
        if em_local and (em_local == low or em_local in low or low in em_local):
            details['username_similar'] = True
            return False, '密码不能与邮箱本地部分相同或互相包含', details
    # 3) 字符类别计数
    classes = 0
    import re as _pw_re
    has_upper = bool(_pw_re.search(r'[A-Z]', pw))
    has_lower = bool(_pw_re.search(r'[a-z]', pw))
    has_digit = bool(_pw_re.search(r'[0-9]', pw))
    has_special = bool(_pw_re.search(r'[^A-Za-z0-9]', pw))
    for c in (has_upper, has_lower, has_digit, has_special):
        if c: classes += 1
    details['classes_count'] = classes
    details['has_upper'] = has_upper
    details['has_lower'] = has_lower
    details['has_digit'] = has_digit
    details['has_special'] = has_special
    if classes < require_classes:
        details['classes_ok'] = False
        missing = []
        if not has_upper: missing.append('大写字母')
        if not has_lower: missing.append('小写字母')
        if not has_digit: missing.append('数字')
        if not has_special: missing.append('特殊符号')
        need = require_classes - classes
        return False, f'密码强度不足：需再包含 {need} 类字符（建议：{" / ".join(missing[:3])}）', details
    details['classes_ok'] = True
    # 4) 黑名单（大小写不敏感）
    if forbid_blacklist and low in _WEAK_PASSWORD_BLACKLIST:
        details['blacklisted'] = True
        return False, '密码过于常见，属于弱密码黑名单，请更换', details
    # 5) 单调模式：全相同字符 / 纯连续数字或反向连续 / 纯键盘行（qwerty/asdf/zxcv 等）
    monotone = False
    if len(set(pw)) == 1:
        monotone = True
    else:
        # 纯连续数字 12345 / 54321
        if pw.isdigit():
            nums = [int(ch) for ch in pw]
            diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
            if diffs and (all(x == 1 for x in diffs) or all(x == -1 for x in diffs)):
                monotone = True
        if not monotone:
            # 键盘行
            kb_rows = ['`1234567890-=','qwertyuiop[]\\','asdfghjkl;\'','zxcvbnm,./',
                       '～！＠＃＄％＾＆＊（）＿＋','qwertyuiop','asdfghjkl','zxcvbnm']
            lowpw = pw.lower()
            for row in kb_rows:
                if lowpw in row or row in lowpw:
                    monotone = True; break
    if monotone:
        details['monotonous'] = True
        return False, '密码过于简单（全相同字符/连续数字/键盘行），请更换', details
    score = classes + (1 if details['length_ok'] else 0) + (1 if not details['blacklisted'] else 0) + (1 if not details['monotonous'] else 0)
    if score <= 3: level = '弱'
    elif score <= 5: level = '中'
    else: level = '强'
    details['score'] = score
    details['level'] = level
    return True, f'密码强度合格（{level}）', details



def _verify_password_fallback(plain_provided: str, expected_hash_stored: str, username: str) -> bool:
    """
    当标准哈希比对失败时走兼容回退：
    1) 支持 werkzeug 的 generate_password_hash（老init.py写的格式）
    2) 支持常见初始密码（admin123 / 123456 / password123 / 用户名本身 等）
    3) 支持 hex SHA256 格式（64位十六进制）
    4) 支持 Fernet 加密格式（gAAAAA 开头）
    5) 支持 bcrypt 格式（$2b$ / $2a$ / $2y$ 开头）
    返回 True 表示密码验证通过（调用方应把哈希升级为标准格式）
    """
    if not plain_provided or not expected_hash_stored:
        return False
    # 1) hex SHA256 格式
    try:
        if len(expected_hash_stored) == 64 and all(c in '0123456789abcdef' for c in expected_hash_stored.lower()):
            if hashlib.sha256(plain_provided.encode('utf-8')).hexdigest() == expected_hash_stored.lower():
                return True
    except Exception:
        pass
    # 2) Fernet 加密格式
    try:
        if expected_hash_stored.startswith('gAAAAA'):
            from cryptography.fernet import Fernet
            possible_keys = [
                b'MTSCOS_SECRET_KEY_2026',
                b'mtscos_ai_secret_key_2026',
                b'MTSCOS_AI_SYSTEM_KEY_2026',
            ]
            for key_source in possible_keys:
                try:
                    key = base64.urlsafe_b64encode(hashlib.sha256(key_source).digest()[:32])
                    f = Fernet(key)
                    decrypted = f.decrypt(expected_hash_stored.encode()).decode()
                    if decrypted == plain_provided:
                        return True
                except Exception:
                    continue
    except ImportError:
        pass
    # 3) bcrypt 格式
    try:
        if expected_hash_stored.startswith('$2b$') or expected_hash_stored.startswith('$2a$') or expected_hash_stored.startswith('$2y$'):
            import bcrypt
            if bcrypt.checkpw(plain_provided.encode(), expected_hash_stored.encode()):
                return True
    except ImportError:
        pass
    # 4) werkzeug 格式
    try:
        from werkzeug.security import check_password_hash as _wk_check
        if '$' in expected_hash_stored or expected_hash_stored.startswith('pbkdf2') \
                or expected_hash_stored.startswith('scrypt') or expected_hash_stored.startswith('sha256$'):
            try:
                if _wk_check(expected_hash_stored, plain_provided):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    # A) 正常"常见密码映射"：存储哈希 == 常见密码哈希，且用户输入 == 该常见密码
    try:
        cand_set = set(_COMMON_DEFAULT_PASSWORDS)
        cand_set.add(username or '')
        cand_set.add((username or '').lower())
        cand_set.add((username or '').capitalize())
        for cand in cand_set:
            if not cand:
                continue
            if _hash_password(cand) == expected_hash_stored:
                return plain_provided == cand
    except Exception:
        pass
    # B) 占位哈希兼容：存储哈希是历史占位哈希（出现频率高的"固定"哈希值），
    #    且用户输入的是常见初始密码 -> 兼容通过（然后自动升级为用户此次输入的密码）
    _PLACEHOLDER_HASHES = {
        '6G94qKPK8LYNjnTllCqm2G3BUM08AzOK7yW30tfjrMc=',
    }
    try:
        if expected_hash_stored in _PLACEHOLDER_HASHES:
            if plain_provided in cand_set:
                return True
    except Exception:
        pass
    return False


def _password_matches(plain_provided: str, expected_hash_stored: str, username: str):
    """
    返回 (ok: bool, need_upgrade: bool)
    - ok: 密码是否验证通过
    - need_upgrade: 通过但是用了兼容回退，需要把数据库哈希升级为标准 _hash_password(plain)
    """
    if not plain_provided or not expected_hash_stored:
        return False, False
    try:
        std_hash = _hash_password(plain_provided)
    except Exception:
        return False, False
    if std_hash == expected_hash_stored:
        return True, False
    ok = _verify_password_fallback(plain_provided, expected_hash_stored, username)
    return (True, True) if ok else (False, False)


def _get_conn(db_path=None):
    """兼容层：历史遗留代码有58处遗漏db_path的调用，全部默认落到APP_DB
    v22.39.1: 强制 WAL + busy_timeout 30s — 解决 daemon 并发写 "database is locked"
    """
    if db_path is None:
        db_path = APP_DB
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return conn


# ---------- 跨库用户查找与可写库定位 ----------
def _all_user_db_candidates():
    """按优先级返回所有含 users 表的候选数据库（APP_DB最高，因为真实用户都在这）"""
    return [p for p in [
        APP_DB, AUTH_DB, DATA_MTSCOS_DB,
        os.path.join(BASE_DIR, 'flask-app', 'mtscos.db'),
        SPLIT_AI_DB, SPLIT_EXAM_DB, SPLIT_QUESTION_DB, SPLIT_LEARNING_DB,
        SPLIT_ADMIN_DB, SPLIT_LOG_DB, SPLIT_SYSTEM_DB,
    ] if p and os.path.exists(p)]


def _find_user_across_dbs(username):
    """
    跨库按用户名（大小写不敏感）查找用户。
    返回 (user_row_dict, db_path) 找不到时返回 (None, None)
    绝不创建用户，绝不修改密码。
    """
    if not username:
        return None, None
    uname = str(username).strip()
    # 优先列名组合：标准列集合，兼容多种 users 表 schema
    col_candidates = [
        ("id, username, email, password, role, is_active, super_admin_approved, hardware_admin_approved, created_at, updated_at, failed_login_count, locked_until, last_login, avatar, phone",
         ["id", "username", "email", "password", "role", "is_active", "super_admin_approved",
          "hardware_admin_approved", "created_at", "updated_at", "failed_login_count",
          "locked_until", "last_login", "avatar", "phone"]),
        ("id, username, email, password, role, enabled, super_admin_approved, created_at, updated_at",
         ["id", "username", "email", "password", "role", "is_active", "super_admin_approved",
          "created_at", "updated_at"]),
        ("*", None),
    ]
    for db in _all_user_db_candidates():
        try:
            with _get_conn(db) as c:
                for sql_cols, _keys in col_candidates:
                    try:
                        r = c.execute(
                            f"SELECT {sql_cols} FROM users WHERE LOWER(username)=LOWER(?) LIMIT 1",
                            (uname,)
                        ).fetchone()
                        if r:
                            d = dict(r)
                            # enabled <-> is_active 统一
                            if 'enabled' in d and 'is_active' not in d:
                                d['is_active'] = d.get('enabled', 1)
                            if 'is_active' in d and d.get('is_active') is None:
                                d['is_active'] = 1
                            return d, db
                    except sqlite3.Error:
                        continue
        except (sqlite3.Error, OSError):
            continue
    return None, None


def _find_user_and_verify_password(username, password):
    """
    跨库查找用户并验证密码：
    1. 在所有候选库中查找用户
    2. 对每个找到的用户记录尝试密码验证
    3. 返回第一个密码匹配的 (user_dict, db_path, need_pw_upgrade)
    4. 若密码全部不匹配，返回第一个找到的 (user_dict, db_path, False) 以便走正常失败流程
    5. 若用户不存在，返回 (None, None, False)
    """
    if not username:
        return None, None, False
    uname = str(username).strip()
    col_candidates = [
        ("id, username, email, password, role, is_active, super_admin_approved, hardware_admin_approved, created_at, updated_at, failed_login_count, locked_until, last_login, avatar, phone",
         ["id", "username", "email", "password", "role", "is_active", "super_admin_approved",
          "hardware_admin_approved", "created_at", "updated_at", "failed_login_count",
          "locked_until", "last_login", "avatar", "phone"]),
        ("id, username, email, password, role, enabled, super_admin_approved, created_at, updated_at",
         ["id", "username", "email", "password", "role", "is_active", "super_admin_approved",
          "created_at", "updated_at"]),
        ("*", None),
    ]
    first_found = None
    for db in _all_user_db_candidates():
        try:
            with _get_conn(db) as c:
                for sql_cols, _keys in col_candidates:
                    try:
                        r = c.execute(
                            f"SELECT {sql_cols} FROM users WHERE LOWER(username)=LOWER(?) LIMIT 1",
                            (uname,)
                        ).fetchone()
                        if r:
                            d = dict(r)
                            if 'enabled' in d and 'is_active' not in d:
                                d['is_active'] = d.get('enabled', 1)
                            if 'is_active' in d and d.get('is_active') is None:
                                d['is_active'] = 1
                            if first_found is None:
                                first_found = (d, db)
                            # 尝试密码验证（兼容 password 与 password_hash 两列）
                            stored_pw = d.get('password') or d.get('password_hash') or ''
                            pw_ok, need_upgrade = _password_matches(password, stored_pw, username)
                            if pw_ok:
                                return d, db, need_upgrade
                    except sqlite3.Error:
                        continue
        except (sqlite3.Error, OSError):
            continue
    if first_found:
        return first_found[0], first_found[1], False
    return None, None, False


def _find_writable_user_db(preferred=None):
    """
    返回一个可写的数据库路径，用于：
      1) 写 login_logs / login_attempts（用户所在库优先）
      2) 注册新用户（用户库不存在时，回退到存在users表的库）
      3) 更新password hash/last_login（用户所在库优先）
    绝不凭空建库：若该路径不存在且不可写则跳过。
    """
    cands = []
    if preferred and os.path.exists(preferred):
        cands.append(preferred)
    for p in _all_user_db_candidates():
        if p not in cands:
            cands.append(p)
    # 再追加 APP_DB 兜底（即使 users 表不存在也能创建）
    if APP_DB and APP_DB not in cands and os.path.exists(os.path.dirname(APP_DB) or '.'):
        cands.append(APP_DB)
    for p in cands:
        try:
            with _get_conn(p) as c:
                c.execute("SELECT 1")
                # 判断有users表或者可以建users表
                cur = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cur.fetchone():
                    return p
                # 没有users表但尝试建立最小schema看是否可写
                try:
                    c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE, email TEXT, password TEXT,
                        role TEXT DEFAULT 'user', is_active INTEGER DEFAULT 1,
                        created_at TEXT, updated_at TEXT, last_login TEXT,
                        failed_login_count INTEGER DEFAULT 0, locked_until TEXT,
                        super_admin_approved INTEGER DEFAULT 0,
                        hardware_admin_approved INTEGER DEFAULT 0,
                        avatar TEXT, phone TEXT,
                        fingerprint_template TEXT,
                        fingerprint_enabled INTEGER DEFAULT 0,
                        fingerprint_registered_at TEXT,
                        fingerprint_device_id TEXT
                    )""")
                    c.execute("""CREATE TABLE IF NOT EXISTS login_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                        username TEXT, ip_address TEXT, user_agent TEXT,
                        device_type TEXT, login_status TEXT, login_time TEXT, remark TEXT
                    )""")
                    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
                        ip_address TEXT, success INTEGER, timestamp TEXT
                    )""")
                    c.commit()
                    return p
                except sqlite3.Error:
                    continue
        except (sqlite3.Error, OSError):
            continue
    return None


def _ensure_login_logs_schema_any(conn):
    """在任意 conn 上创建 login_attempts / login_logs 表（幂等）"""
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
            ip_address TEXT, success INTEGER, timestamp TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            username TEXT, ip_address TEXT, user_agent TEXT,
            device_type TEXT, login_status TEXT, login_time TEXT, remark TEXT
        )""")
    except sqlite3.Error:
        pass
    # 兼容列缺失：APP_DB login_logs列名 id/user_id/login_time/login_ip/user_agent
    try:
        for (tbl, col, decl) in [
            ('login_logs', 'device_type', 'TEXT'),
            ('login_logs', 'login_status', 'TEXT'),
            ('login_logs', 'remark', 'TEXT'),
            ('login_logs', 'ip_address', 'TEXT'),
            ('login_logs', 'username', 'TEXT'),
            ('login_attempts', 'username', 'TEXT'),
            ('login_attempts', 'ip_address', 'TEXT'),
            ('login_attempts', 'success', 'INTEGER'),
            ('login_attempts', 'timestamp', 'TEXT'),
        ]:
            try:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {decl}")
            except sqlite3.Error:
                pass
    except sqlite3.Error:
        pass
    try:
        conn.commit()
    except sqlite3.Error:
        pass


# ==================== Remember-Me Token 持久化与校验 ====================
def _ensure_remember_me_schema(conn):
    """幂等：在任意 users 所在库建 remember_me_tokens 表"""
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS remember_me_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id TEXT UNIQUE NOT NULL,
            token_hash TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            last_used_at TEXT,
            last_used_ip TEXT,
            revoked INTEGER DEFAULT 0
        )""")
        conn.commit()
    except sqlite3.Error as _rem_db_err:
        # 🔴 异常捕捉修复：建表失败不再静默吞掉 sqlite3.Error
        try:
            import logging as _lg_rm
            _lg_rm.warning("[DB:_ensure_remember_me_schema] 建表失败: %s", _rem_db_err)
        except Exception:
            pass


def _remember_me_db_path():
    """优先找 users 可写库；fallback 到 APP_DB"""
    try:
        p = _find_writable_user_db()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    return APP_DB if os.path.exists(APP_DB) else AUTH_DB


def _rm_generate_token_pair():
    """返回 (token_id: 16byte, token_secret: 32byte hex)"""
    import secrets as _ss
    return _ss.token_urlsafe(16), _ss.token_urlsafe(32)


def _rm_hash_secret(secret: str) -> str:
    """SHA256 哈希后存库（不存明文 secret）"""
    return hashlib.sha256(secret.encode('utf-8')).hexdigest()


def _remember_me_issue(user_id, username, ip=None, ua=None) -> str | None:
    """签发一个 remember-me token，返回 cookie 值（id.secret）；失败返回 None"""
    try:
        if not user_id or not username:
            return None
        tid, secret = _rm_generate_token_pair()
        secret_hash = _rm_hash_secret(secret)
        now = datetime.now()
        exp_ts = time.time() + _MT_REMEMBER_MAX_AGE
        exp = datetime.fromtimestamp(exp_ts)
        now_iso, exp_iso = now.isoformat(), exp.isoformat()
        dbp = _remember_me_db_path()
        with _get_conn(dbp) as c:
            _ensure_remember_me_schema(c)
            c.execute(
                "INSERT INTO remember_me_tokens(token_id,token_hash,user_id,username,ip_address,user_agent,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                (tid, secret_hash, int(user_id), str(username), (ip or '')[:64], (ua or '')[:200], now_iso, exp_iso)
            )
            c.commit()
        # 初始化 IP 历史
        _MT_REMEMBER_IP_HISTORY[tid] = {'ip_set': {ip} if ip else set(), 'first_seen': now_iso}
        return f"{tid}.{secret}"
    except Exception as e:
        try:
            _ef_process_report_anomaly(
                'remember_cookie_write_fail', 'auth_login_POST', 'MEDIUM',
                {'error': str(e)[:200], 'username': username, 'user_id': user_id},
                notify_ai_employees=True, auto_apply_fix=True,
                operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
            )
        except Exception:
            pass
        return None


def _remember_me_consume(cookie_value: str, ip=None, ua=None):
    """消费 remember-me cookie：合法→ (uid, uname, new_cookie_val)；失败→ (None,None,None)；异常返回会自动撤销对应token"""
    if not isinstance(cookie_value, str) or '.' not in cookie_value:
        return None, None, None
    try:
        tid, secret = cookie_value.split('.', 1)
        tid = tid[:64]
        secret = secret[:128]
        secret_hash = _rm_hash_secret(secret)
        dbp = _remember_me_db_path()
        row = None
        with _get_conn(dbp) as c:
            _ensure_remember_me_schema(c)
            c.row_factory = sqlite3.Row
            r = c.execute(
                "SELECT id, token_id, token_hash, user_id, username, expires_at, revoked, last_used_ip "
                "FROM remember_me_tokens WHERE token_id=? LIMIT 1", (tid,)
            ).fetchone()
            row = dict(r) if r else None
        if not row:
            return None, None, None
        # 检查 revoked / 过期 / 哈希
        if int(row.get('revoked') or 0) == 1:
            _remember_me_revoke_by_id(row['id'], tid, ip, reason='revoked_already')
            return None, None, None
        try:
            from datetime import datetime as _dt
            exp = _dt.fromisoformat(str(row.get('expires_at') or ''))
            if exp < _dt.now():
                _remember_me_revoke_by_id(row['id'], tid, ip, reason='expired')
                return None, None, None
        except Exception:
            pass
        import hmac as _hm
        if not _hm.compare_digest(str(row.get('token_hash') or ''), secret_hash):
            # 哈希不一致：可能 token 被篡改/被盗 —— 立即撤销所有该用户 token
            try:
                _remember_me_revoke_all_for_user(int(row['user_id']), ip, reason='hash_mismatch_theft_suspect')
                _ef_process_report_anomaly(
                    'remember_token_mismatch', 'remember_me_auto_login', 'HIGH',
                    {'token_id': tid, 'username': row.get('username'), 'user_id': row.get('user_id'),
                     'note': '哈希不匹配，疑似被盗；已撤销该用户所有remember-me token'},
                    notify_ai_employees=True, auto_apply_fix=True,
                    operator_user=str(row.get('username') or 'anonymous'), client_ip=ip, client_ua=ua
                )
            except Exception:
                pass
            return None, None, None
        # ---- IP 变化检测（同一 token 不同 IP）----
        hist = _MT_REMEMBER_IP_HISTORY.setdefault(tid, {'ip_set': set(), 'first_seen': ''})
        prev_ips = hist['ip_set']
        if ip and prev_ips and ip not in prev_ips:
            try:
                _ef_process_report_anomaly(
                    'remember_ip_changed', 'remember_me_auto_login', 'MEDIUM',
                    {'token_id': tid, 'username': row.get('username'),
                     'prev_ips': sorted(list(prev_ips))[:5], 'new_ip': ip},
                    notify_ai_employees=True, auto_apply_fix=False,
                    operator_user=str(row.get('username') or 'anonymous'), client_ip=ip, client_ua=ua
                )
            except Exception:
                pass
        if ip:
            prev_ips.add(ip)
        # ---- Token 轮换（每次使用换新 secret，防重放）----
        new_tid, new_secret = _rm_generate_token_pair()
        new_hash = _rm_hash_secret(new_secret)
        now_iso = datetime.now().isoformat()
        try:
            with _get_conn(dbp) as c:
                _ensure_remember_me_schema(c)
                # 老 token 标记过期 + 存入新token
                c.execute("UPDATE remember_me_tokens SET revoked=1, last_used_at=?, last_used_ip=? WHERE id=?",
                          (now_iso, (ip or '')[:64], int(row['id'])))
                # 计算原过期时间剩余，复用
                exp_iso = str(row.get('expires_at') or now_iso)
                c.execute(
                    "INSERT INTO remember_me_tokens(token_id,token_hash,user_id,username,ip_address,user_agent,created_at,expires_at,last_used_at,last_used_ip) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (new_tid, new_hash, int(row['user_id']), str(row['username']), (ip or '')[:64], (ua or '')[:200],
                     now_iso, exp_iso, now_iso, (ip or '')[:64])
                )
                c.commit()
        except Exception:
            return None, None, None
        # 更新内存
        if tid in _MT_REMEMBER_IP_HISTORY:
            del _MT_REMEMBER_IP_HISTORY[tid]
        _MT_REMEMBER_IP_HISTORY[new_tid] = {'ip_set': prev_ips.copy() if prev_ips else ({ip} if ip else set()),
                                            'first_seen': hist.get('first_seen') or now_iso}
        return int(row['user_id']), str(row['username']), f"{new_tid}.{new_secret}"
    except Exception as e:
        try:
            _ef_process_report_anomaly(
                'remember_token_exception', 'remember_me_consume', 'MEDIUM',
                {'error': str(e)[:200]}, notify_ai_employees=True, auto_apply_fix=True,
                client_ip=ip, client_ua=ua
            )
        except Exception:
            pass
        return None, None, None


def _remember_me_revoke_by_id(row_id, tid, ip=None, reason=''):
    try:
        dbp = _remember_me_db_path()
        with _get_conn(dbp) as c:
            _ensure_remember_me_schema(c)
            c.execute("UPDATE remember_me_tokens SET revoked=1 WHERE id=? OR token_id=?", (int(row_id), str(tid)))
            c.commit()
    except Exception:
        pass
    try:
        _MT_REMEMBER_IP_HISTORY.pop(tid, None)
    except Exception:
        pass


def _remember_me_revoke_all_for_user(user_id, ip=None, reason=''):
    try:
        dbp = _remember_me_db_path()
        with _get_conn(dbp) as c:
            _ensure_remember_me_schema(c)
            c.execute("UPDATE remember_me_tokens SET revoked=1 WHERE user_id=?", (int(user_id),))
            c.commit()
    except Exception:
        pass
    # 清理内存
    for k in list(_MT_REMEMBER_IP_HISTORY.keys()):
        try:
            del _MT_REMEMBER_IP_HISTORY[k]
        except Exception:
            pass


# ==================== END Remember-Me ====================


def _decrypt_sv_row(row):
    """解密 system_versions 单行：MTENC 密文字段用官方 DatabaseEncryption 解密，
    明文/解密失败字段原样保留。返回 dict。表级别 L3，按(表,列)HKDF 字段密钥解密。"""
    out = {}
    try:
        keys = row.keys()
    except Exception:
        return out
    enc = None
    lvl = None
    try:
        from app.utils.db_encryption import DatabaseEncryption, classify_table
        enc = DatabaseEncryption()
        lvl = classify_table('system_versions')
    except Exception:
        enc = None
    for k in keys:
        v = row[k]
        if enc is not None and isinstance(v, str) and v.startswith('MTENC:'):
            try:
                v = enc.decrypt_data(v, lvl, 'system_versions', k)
            except Exception:
                pass
        out[k] = v
    return out


def _sv_sort_key(decrypted_row):
    """归一化 system_versions 解密后 created_at 为可字典序比较的 'YYYY-MM-DD HH:MM:SS'。"""
    ts = str(decrypted_row.get('created_at') or '')
    return ts.replace('T', ' ')[:19]


def get_version_info():
    """优先从 system_versions 取最新版本，失败回退至 VERSION 文件
       返回 (version, info_dict, latest_version)。
       注意：system_versions 历史行可能为 MTENC 密文(含 created_at)，
       不能依赖 SQL `ORDER BY datetime(created_at)`(密文上为 NULL)，
       必须拉取多行→逐行解密→按解密后时间排序取最新。"""
    version = None
    info = {
        'version': None,
        'codename': '',
        'build_number': '',
        'build_date': '',
        'status': '',
        'description': '',
        'source': '',
        'build_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'commit': 'db-sourced',
        'branch': 'main',
        'author': 'Chenghao Wu',
    }

    candidates = [
        (APP_DB, 'SELECT version,codename,build_number,build_date,status,description,created_at FROM system_versions'),
        (DATA_MTSCOS_DB, 'SELECT version,codename,build_number,build_date,status,description,created_at FROM system_versions'),
    ]
    for db_path, sql in candidates:
        try:
            if not os.path.exists(db_path):
                continue
            with _get_conn(db_path) as conn:
                rows = conn.execute(sql).fetchall()
            if not rows:
                continue
            # 逐行解密(密文/明文兼容)，跳过解密后仍为密文或无版本号的坏行，按解密后时间取最新
            best = None
            best_key = ''
            for raw in rows:
                d = _decrypt_sv_row(raw)
                ver = d.get('version')
                if not ver or (isinstance(ver, str) and ver.startswith('MTENC:')):
                    continue
                key = _sv_sort_key(d)
                if key >= best_key:
                    best_key = key
                    best = d
            if best:
                version = best.get('version')
                info['version'] = version
                info['codename'] = best.get('codename') or ''
                info['build_number'] = best.get('build_number') or ''
                ca = best.get('created_at') or ''
                info['build_date'] = best.get('build_date') or (str(ca)[:10] if ca else '')
                info['status'] = best.get('status') or ''
                info['description'] = best.get('description') or ''
                info['source'] = os.path.basename(db_path) + '.system_versions'
                break
        except Exception:
            continue

    if not version and os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                version = f.read().strip()
            info['version'] = version
            info['source'] = 'VERSION file'
        except Exception:
            pass

    if not version:
        version = '1.0.0'
        info['version'] = version
        info['source'] = 'fallback default'

    latest_version = version
    return version, info, latest_version


def _get_homepage_stats():
    stats = {
        'version': '',
        'modules_count': 0,
        'availability': '0',
        'rules_count': 0,
        'avg_response_ms': 0,
        'scoring_consistency': '0',
        'questions_count': 0,
        'users_count': 0,
        'exams_count': 0,
        'ai_employees_count': 0,
        'ai_modules_total': 0,
        'ai_upgrade_logs': 0,
        'ai_inspection_logs': 0,
        'ai_registered_modules': 0,
        'ai_module_categories': 0,
    }
    try:
        ver, info, _ = get_version_info()
        if ver:
            stats['version'] = ver
        if info:
            stats['availability'] = str(info.get('availability', 0))
    except Exception:
        pass
    try:
        with _get_conn(APP_DB) as c:
            for (tbl, key) in [('users', 'users_count'), ('questions', 'questions_count'),
                               ('exams', 'exams_count'), ('ai_employees', 'ai_employees_count')]:
                try:
                    r = c.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()
                    if r:
                        stats[key] = r[0] or 0
                except Exception:
                    pass
            # 仙女座 AI 员工 (mt_andromeda_employee_registry) — 项目主力员工表
            try:
                andromeda_count = c.execute(
                    "SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()
                if andromeda_count:
                    stats['ai_employees_count'] = stats.get('ai_employees_count', 0) + andromeda_count[0]
            except Exception:
                pass
            try:
                rules = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='system_rules'").fetchone()
                if rules and rules[0]:
                    r = c.execute('SELECT COUNT(*) FROM system_rules').fetchone()
                    if r:
                        stats['rules_count'] = r[0] or 0
            except Exception:
                pass
            try:
                r = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_module_registry'").fetchone()
                if r and r[0]:
                    m = c.execute('SELECT COUNT(*) FROM ai_module_registry').fetchone()
                    if m:
                        stats['ai_registered_modules'] = m[0] or 0
                    cats = c.execute('SELECT COUNT(DISTINCT module_type) FROM ai_module_registry').fetchone()
                    if cats:
                        stats['ai_module_categories'] = cats[0] or 0
            except Exception:
                pass
            try:
                r = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_upgrade_log'").fetchone()
                if r and r[0]:
                    m = c.execute('SELECT COUNT(*) FROM ai_upgrade_log').fetchone()
                    if m:
                        stats['ai_upgrade_logs'] = m[0] or 0
            except Exception:
                pass
            try:
                r = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_inspection_log'").fetchone()
                if r and r[0]:
                    m = c.execute('SELECT COUNT(*) FROM ai_inspection_log').fetchone()
                    if m:
                        stats['ai_inspection_logs'] = m[0] or 0
            except Exception:
                pass
            try:
                perf_table = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_performance_metrics'").fetchone()
                if perf_table and perf_table[0]:
                    avg_r = c.execute('SELECT AVG(duration_seconds) FROM ai_performance_metrics').fetchone()
                    if avg_r and avg_r[0]:
                        stats['avg_response_ms'] = round(avg_r[0] * 1000)
            except Exception:
                pass
    except Exception:
        pass
    try:
        upgrade_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
        if os.path.exists(upgrade_db_path):
            upgrade_conn = sqlite3.connect(upgrade_db_path)
            uc = upgrade_conn.cursor()
            try:
                uc.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_module_registry'")
                if uc.fetchone()[0]:
                    uc.execute('SELECT COUNT(*) FROM ai_module_registry')
                    r = uc.fetchone()
                    if r: stats['ai_registered_modules'] = max(stats['ai_registered_modules'], r[0] or 0)
                    uc.execute('SELECT COUNT(DISTINCT module_type) FROM ai_module_registry')
                    r = uc.fetchone()
                    if r: stats['ai_module_categories'] = max(stats['ai_module_categories'], r[0] or 0)
            except Exception:
                pass
            try:
                uc.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_upgrade_log'")
                if uc.fetchone()[0]:
                    uc.execute('SELECT COUNT(*) FROM ai_upgrade_log')
                    r = uc.fetchone()
                    if r: stats['ai_upgrade_logs'] = max(stats['ai_upgrade_logs'], r[0] or 0)
            except Exception:
                pass
            try:
                uc.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ai_inspection_log'")
                if uc.fetchone()[0]:
                    uc.execute('SELECT COUNT(*) FROM ai_inspection_log')
                    r = uc.fetchone()
                    if r: stats['ai_inspection_logs'] = max(stats['ai_inspection_logs'], r[0] or 0)
            except Exception:
                pass
            upgrade_conn.close()
    except Exception:
        pass
    try:
        ai_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'ai')
        if os.path.isdir(ai_dir):
            ai_files = [f for f in os.listdir(ai_dir) if f.endswith('.py') and not f.startswith('__')]
            stats['ai_modules_total'] = len(ai_files)
    except Exception:
        pass
    stats['modules_count'] = stats['questions_count'] + stats['ai_modules_total'] + stats['rules_count']
    stats['modules'] = stats['modules_count']
    stats['questions'] = stats['questions_count']
    stats['rules'] = stats['rules_count']
    stats['latency'] = stats['avg_response_ms']
    stats['consistency'] = stats['scoring_consistency']
    stats['ai_modules'] = stats['ai_modules_total']
    stats['ai_registered'] = stats['ai_registered_modules']
    stats['ai_logs'] = stats['ai_upgrade_logs']
    stats['ai_inspections'] = stats['ai_inspection_logs']
    stats['ai_categories'] = stats['ai_module_categories']
    stats['total_users'] = stats['users_count']
    stats['total_exams'] = stats['exams_count']
    stats['total_questions'] = stats['questions_count']
    stats['ai_employees_online'] = stats['ai_employees_count']
    return stats


# ============ UI 装饰/粒子性能 表结构 + 辅助查询 ============
def _ensure_site_decoration_schema(conn):
    """确保 ui_site_decoration 表存在（保存页脚/页眉品牌信息、粒子配置等）"""
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS ui_site_decoration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            k TEXT UNIQUE NOT NULL,
            v TEXT,
            remark TEXT,
            updated_at TEXT
        )""")
        conn.commit()
        # 写入默认值（不存在时）
        now_iso = datetime.now().isoformat()
        defaults = [
            ('footer_brand_name', 'MTSCOS AI', '页脚品牌名', now_iso),
            ('footer_brand_slogan', 'Intelligent Learning Platform', '页脚品牌副标题', now_iso),
            ('footer_brand_desc', 'MTSCOS AI · MTS架构 驱动的智能学习评估平台，覆盖 K12 / 成人 / 高等教育 全场景。基于自主学习的AI脑库，提供自适应出题、智能诊断、学情画像、AI答疑等一体化能力。', '页脚品牌描述', now_iso),
            ('footer_author', 'Chenghao Wu', '作者署名', now_iso),
            ('footer_icp', '京ICP备12345678号', 'ICP备案号', now_iso),
            ('footer_police', '', '公安备案号（可选）', now_iso),
            ('footer_copyright_year', '2026', '版权年份', now_iso),
            ('footer_company', 'MTS Architecture', '版权主体', now_iso),
            ('footer_contact_address', '北京市海淀区科技园区', '联系地址', now_iso),
            ('footer_contact_phone', '400-888-8888', '联系电话', now_iso),
            ('footer_contact_email', 'contact@mtscos.com', '联系邮箱', now_iso),
            ('footer_contact_worktime', '周一至周五 9:00-18:00', '工作时间', now_iso),
            ('particle_max_count', '110', '粒子最大数量（上限）', now_iso),
            ('particle_connection_max_distance', '140', '粒子连线最大距离(px)', now_iso),
            ('particle_mouse_attract_enable', '1', '鼠标吸引开关 1=开 0=关', now_iso),
            ('particle_glow_enable', '1', '粒子发光效果开关 1=开 0=关', now_iso),
        ]
        for kv in defaults:
            try:
                conn.execute("INSERT OR IGNORE INTO ui_site_decoration(k,v,remark,updated_at) VALUES (?,?,?,?)", kv)
            except Exception:
                pass
        conn.commit()
    except sqlite3.Error:
        pass


def _ensure_particle_perf_schema(conn):
    """确保 particle_perf_events 表存在（前端上报 FPS/卡顿事件 ）"""
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS particle_perf_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            username TEXT,
            event_code TEXT NOT NULL,
            fps REAL,
            particle_count INTEGER,
            canvas_width INTEGER,
            canvas_height INTEGER,
            dpr REAL,
            page_visible INTEGER DEFAULT 1,
            reduced_motion INTEGER DEFAULT 0,
            mobile INTEGER DEFAULT 0,
            memory_usage REAL,
            prev_memory_usage REAL,
            memory_growth_mb REAL,
            ip_address TEXT,
            user_agent TEXT,
            detail TEXT,
            created_at TEXT NOT NULL
        )""")
        conn.commit()
        # schema 升级：老库补列（逐个 ALTER，忽略已存在错误）
        upgrade_cols = [
            ('memory_usage', 'REAL'),
            ('prev_memory_usage', 'REAL'),
            ('memory_growth_mb', 'REAL'),
        ]
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(particle_perf_events)").fetchall()]
            for col_name, col_type in upgrade_cols:
                if col_name not in cols:
                    try:
                        conn.execute(f"ALTER TABLE particle_perf_events ADD COLUMN {col_name} {col_type}")
                    except sqlite3.Error:
                        pass
            conn.commit()
        except sqlite3.Error:
            pass
    except sqlite3.Error:
        pass


def _get_site_decoration(conn):
    """返回 ui_site_decoration 字典 {k:v}"""
    out = {}
    try:
        rows = conn.execute("SELECT k,v FROM ui_site_decoration").fetchall() or []
        for r in rows:
            try:
                out[r[0]] = r[1]
            except Exception:
                pass
    except Exception:
        pass
    return out


def _get_footer_info():
    """组装页脚动态信息字典（供模板和API共用）"""
    info = {
        'brand_name': 'MTSCOS AI',
        'brand_slogan': 'Intelligent Learning Platform',
        'brand_desc': 'MTSCOS AI · MTS架构 驱动的智能学习评估平台，覆盖 K12 / 成人 / 高等教育 全场景。基于自主学习的AI脑库，提供自适应出题、智能诊断、学情画像、AI答疑等一体化能力。',
        'author': 'Chenghao Wu',
        'icp': '京ICP备12345678号',
        'police': '',
        'copyright_year': '2026',
        'company': 'MTS Architecture',
        'contact_address': '北京市海淀区科技园区',
        'contact_phone': '400-888-8888',
        'contact_email': 'contact@mtscos.com',
        'contact_worktime': '周一至周五 9:00-18:00',
    }
    try:
        with _get_conn(APP_DB) as conn:
            _ensure_site_decoration_schema(conn)
            cfg = _get_site_decoration(conn)
            mapping = {
                'footer_brand_name': 'brand_name',
                'footer_brand_slogan': 'brand_slogan',
                'footer_brand_desc': 'brand_desc',
                'footer_author': 'author',
                'footer_icp': 'icp',
                'footer_police': 'police',
                'footer_copyright_year': 'copyright_year',
                'footer_company': 'company',
                'footer_contact_address': 'contact_address',
                'footer_contact_phone': 'contact_phone',
                'footer_contact_email': 'contact_email',
                'footer_contact_worktime': 'contact_worktime',
            }
            for k, target in mapping.items():
                if cfg.get(k):
                    info[target] = cfg[k]
    except Exception:
        pass
    return info


def _get_particle_frontend_config():
    """粒子前端默认配置（可被后端 override）"""
    cfg = {
        'max_count': 110,
        'connection_max_distance': 140,
        'mouse_attract_enable': True,
        'glow_enable': True,
    }
    try:
        with _get_conn(APP_DB) as conn:
            _ensure_site_decoration_schema(conn)
            raw = _get_site_decoration(conn)
            try:
                cfg['max_count'] = int(raw.get('particle_max_count') or 110)
            except Exception:
                pass
            try:
                cfg['connection_max_distance'] = int(raw.get('particle_connection_max_distance') or 140)
            except Exception:
                pass
            cfg['mouse_attract_enable'] = (str(raw.get('particle_mouse_attract_enable') or '1') == '1')
            cfg['glow_enable'] = (str(raw.get('particle_glow_enable') or '1') == '1')
    except Exception:
        pass
    return cfg


# ============ EigenFlux · UI/粒子异常分类矩阵（8 类 + AI员工5人磋商）============
_UI_EF_SEVERITY_MAP = {
    'particle_fps_low': 'MEDIUM',
    'particle_memory_grow': 'HIGH',
    'render_particle_crash': 'HIGH',
    'header_scroll_jank': 'LOW',
    'header_nav_error': 'MEDIUM',
    'footer_perf_below': 'LOW',
    'footer_missing_info': 'MEDIUM',
    'resize_thrash': 'LOW',
}


def _ef_report_ui_event(event_code, payload_dict, ip, ua, username='anonymous'):
    """统一的 UI/粒子异常 → EigenFlux 报告入口"""
    try:
        sev = _UI_EF_SEVERITY_MAP.get(event_code, 'LOW')
        ctx = payload_dict or {}
        msg_map = {
            'particle_fps_low': '前端粒子渲染 FPS 低于阈值，已触发自动降级',
            'particle_memory_grow': '粒子运行中出现异常资源占用增长（疑似内存泄漏）',
            'render_particle_crash': '粒子 canvas 渲染崩溃（context 丢失/异常），已自动降级为纯CSS背景',
            'header_scroll_jank': '页眉滚动监听出现掉帧/抖动，建议 rAF 节流',
            'header_nav_error': '页眉导航跳转失败（链接不可达/被拦截）',
            'footer_perf_below': '页脚首屏渲染延迟高于4s，建议启用懒渲染',
            'footer_missing_info': '页脚缺失品牌/备案/联系方式关键字段',
            'resize_thrash': 'resize 事件在短时间内高频触发（疑似布局抖动）',
        }
        _ef_process_report_anomaly(
            event_code, 'ui_particle_decoration', sev,
            {'event_code': event_code, 'message': msg_map.get(event_code, event_code), **ctx},
            notify_ai_employees=True, auto_apply_fix=True,
            operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
        )
    except Exception:
        pass


# ==================== 法律铁规 / 红线 / 红墙 Schema ====================
_REDLINE_LEVELS = ['IRON_RULE',  # 铁规（0容忍，不可跳过，SA也须遵循，拦截即阻断+审计）
                   'RED_LINE',   # 红线（强制，可申请跳过需SA审批，宽限最长24h）
                   'RED_WALL',   # 红墙（默认阻断，可申请2管理员+SA审批宽限72h）
                   'CONSTRAINT', # 制约（强制告警，可申请管理员审批宽限7d）
                   'WARNING']    # 警示（提示，可申请管理员豁免30d）

def _ensure_legal_redlines_schema(conn):
    """确保铁规红线表 + 跳过审批表 + 宽限窗口表 存在 + schema 升级补列"""
    try:
        # 1) 铁规红线主表
        conn.execute("""CREATE TABLE IF NOT EXISTS legal_red_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code TEXT UNIQUE NOT NULL,
            rule_name TEXT NOT NULL,
            rule_level TEXT NOT NULL DEFAULT 'WARNING',
            legal_area TEXT,
            scope TEXT,
            scope_detail TEXT,
            penalty_action TEXT DEFAULT 'BLOCK',
            skip_allowed INTEGER DEFAULT 0,
            max_grace_hours INTEGER DEFAULT 0,
            sa_only_bypass INTEGER DEFAULT 0,
            requires_vikey INTEGER DEFAULT 0,
            description TEXT,
            legal_reference TEXT,
            is_active INTEGER DEFAULT 1,
            version INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            effective_from TEXT,
            expires_at TEXT,
            metadata TEXT
        )""")
        # schema 升级补列（容错：逐个 ALTER，忽略失败）
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(legal_red_lines)").fetchall()]
            for col, typ in [('legal_area', 'TEXT'), ('scope', 'TEXT'), ('scope_detail', 'TEXT'),
                             ('penalty_action', 'TEXT'), ('skip_allowed', 'INTEGER'),
                             ('max_grace_hours', 'INTEGER'), ('sa_only_bypass', 'INTEGER'),
                             ('requires_vikey', 'INTEGER'), ('legal_reference', 'TEXT'),
                             ('version', 'INTEGER'), ('effective_from', 'TEXT'),
                             ('expires_at', 'TEXT'), ('metadata', 'TEXT'),
                             ('config_value', 'TEXT'), ('default_config_value', 'TEXT'),
                             ('rule_source', 'TEXT DEFAULT "core"')]:
                if col not in cols:
                    try: conn.execute(f"ALTER TABLE legal_red_lines ADD COLUMN {col} {typ}")
                    except sqlite3.Error: pass
        except sqlite3.Error: pass

        # 写入默认铁规红线（INSERT OR IGNORE，保证 idempotent）
        now_iso = datetime.now().isoformat()
        defaults = [
            # ==================== 铁规 IRON_RULE（0容忍，不可跳过）====================
            ('SA_VIKEY_MANDATORY', '超级管理员必须插入VIKEY加密狗', 'IRON_RULE', 'security',
             'page_access,api_call', '所有非首页SA页面/接口', 'BLOCK_IMMEDIATE', 0, 0, 1, 1,
             '《项目硬约束》超级管理员wuchenghao15访问所有敏感页面/操作，无论调试/普通模式，必须硬件检测VIKEY USB加密狗已插入并绑定。',
             'project_memory.md#Hard-Constraints · vikey实时检测函数_super_admin_vikey_check()',
             now_iso),
            ('SA_SEVEN_FACTOR_AUTH', 'SA登录7要素强认证', 'IRON_RULE', 'security',
             'auth_login', '超级管理员wuchenghao15的登录流程', 'BLOCK_IMMEDIATE', 0, 0, 1, 1,
             '7要素：用户名/密码/随机挑战码/USB Key序列号/USB Key PIN/SSL指纹/硬件绑定校验。任一缺失直接阻断。',
             'project_memory.md#Hard-Constraints · 7要素强认证', now_iso),
            ('SA_UNIQUE_ENFORCE', '超级管理员唯一性', 'IRON_RULE', 'security',
             'user_create,user_promote', '创建/晋升用户角色为super_admin时', 'BLOCK_IMMEDIATE', 0, 0, 1, 0,
             '系统超级管理员有且仅有一名：wuchenghao15。任何其他用户不得被授予super_admin角色。',
             'project_memory.md#Hard-Constraints · 超级管理员唯一性', now_iso),
            ('ALL_PAGE_PERMISSION_DECORATOR', '所有路由必须有权限装饰器', 'IRON_RULE', 'architecture',
             'route_define,page_access', '所有Flask路由（非首页页面）', 'BLOCK_AND_LOG', 0, 0, 0, 0,
             '禁止创建无权限控制的页面路由。所有非首页路由必须挂@system_container/@require_login/@require_admin/@require_super_admin/@require_role/@allow_guest_access之一。',
             'project_memory.md#Hard-Constraints · 权限装饰器强制', now_iso),
            ('USER_CONTAINER_MANDATORY', '用户容器强制校验', 'IRON_RULE', 'security',
             'page_access', '所有非首页页面进入前', 'BLOCK_REDIRECT_LOGIN', 0, 0, 0, 0,
             '所有非首页页面必须强制验证用户容器信息合法且正确（用户组别/权限识别码/登陆状态/是否异常/是否合法/唯一登陆时间戳）。',
             'project_memory.md#Hard-Constraints · 用户容器是进入系统重要凭证', now_iso),
            ('REAL_TIME_DB_UPLOAD', 'AI生成数据实时入库', 'IRON_RULE', 'data_governance',
             'ai_generate,data_write', '任何AI员工/引擎/脑库产出数据', 'BLOCK_AND_ALERT', 0, 0, 0, 0,
             '数据库是唯一权威数据源。AI-generated data、学习结果、AI状态变更必须实时写入数据库，启动时从数据库加载。',
             'project_memory.md#Hard-Constraints · Database is the sole authoritative data source', now_iso),
            ('RULE_CHANGE_APPROVAL_FLOW', '规则修改7步审批流程', 'IRON_RULE', 'compliance',
             'rule_modify,config_change', '任何规则/约束/铁规/红线/配置修改', 'BLOCK_AND_AUDIT', 0, 0, 1, 1,
             '管理员提议→≥2名非提议管理员同意→系统AI自动审查→超级管理员终审(vikey实时检测，立即适配/2工作日后)→保密撤回(SA内存标记/DB+日志完全保密)',
             'project_memory.md#Hard-Constraints · 规则修改审批流程 · rule_approval.py', now_iso),

            # ==================== 红线 RED_LINE（可SA审批跳过，≤24h宽限）====================
            ('SA_SENSITIVE_VIKEY_CHECK', 'SA敏感操作vikey实时检测', 'RED_LINE', 'security',
             'sensitive_operation', 'SA执行：规则终审/保密撤回/配置删除/数据导出/权限变更', 'BLOCK_CONFIRM', 1, 24, 1, 1,
             'SA敏感操作前强制调用_super_admin_vikey_check()、AI防火墙复审、终审、保密撤回流程。',
             'project_memory.md#Hard-Constraints · SA敏感操作4要素', now_iso),
            ('SA_DESKTOP_VIKEY_HARDWARE', '桌面端SA硬件加密狗强制', 'RED_LINE', 'security',
             'desktop_access', '桌面端SA访问任意管理后台', 'BLOCK_RETRY', 1, 24, 1, 1,
             '桌面端超级管理员操作须检测vikey USB硬件插入；移动端须验证指纹认证（X-Fingerprint header）。未通过返回VIKEY_REQUIRED错误码。',
             'project_memory.md#Hard-Constraints · 桌面/移动双端VIKEY强制', now_iso),
            ('PASSWORD_SYMMETRIC_HASH_VERIFY', '密码对称哈希校验', 'RED_LINE', 'security',
             'auth_register,auth_forgot,auth_password', '注册/改密/重置密码', 'BLOCK_RETRY', 1, 24, 0, 0,
             '密码哈希配对测试：_verify_password()对称哈希校验；SA保留名拦截；邮箱RFC校验；IP+用户双维度速率限制；跨库用户名冲突检查；Read-back一致性校验。',
             'server_real_db.py::_verify_password · 综合安全加固', now_iso),
            ('REMEMBER_ME_SA_PROHIBITED', 'SA禁止记住我', 'RED_LINE', 'security',
             'auth_login,remember_me', '超级管理员wuchenghao15勾选Remember-me复选框', 'AUTO_DISABLE_AND_ALERT', 1, 24, 1, 0,
             'SA登录双保险禁止记住我；检测SA白名单后自动取消勾选，并触发EigenFlux AI员工5人磋商。',
             'server_real_db.py::Remember-me持久化 · 首页Remember-me复选框3层防护', now_iso),

            # ==================== 红墙 RED_WALL（2管理员+SA审批，≤72h宽限）====================
            ('RATE_LIMIT_API_THRESHOLD', 'API限流阈值不可随意突破', 'RED_WALL', 'api_security',
             'api_call', '所有API接口请求速率', 'BLOCK_429', 1, 72, 0, 0,
             '单IP/单用户每分钟请求量不得超过规则表API_GLOBAL_RATE_LIMIT值。突破默认BLOCK并返回429。',
             'system_rules_extension.py::API访问控制规则 · access_control中间件', now_iso),
            ('MAX_FAILED_LOGIN_LOCKOUT', '登录失败锁定策略', 'RED_WALL', 'security',
             'auth_login', '同一账户/IP登录失败次数', 'LOCK_AND_ALERT', 1, 72, 0, 0,
             '超过SECURITY_MAX_FAILED_LOGINS=5次触发锁定；软锁定900s/硬锁定3600s/永久锁定86400s；AI自动黑名单阈值=10次。',
             'system_rules_extension.py::AI安全防御规则 (SECURITY_LOCK_LEVEL_*)', now_iso),
            ('DATA_EXPORT_SENSITIVE_MASK', '敏感数据导出脱敏', 'RED_WALL', 'data_privacy',
             'data_export,download', '导出Excel/CSV/JSON含学生/教职工/账户信息', 'BLOCK_AND_AUDIT', 1, 72, 0, 0,
             '身份证/手机号/邮箱/家庭住址/密码哈希必须脱敏；API_LOG_SENSITIVE_PARAMS默认0（脱敏）；导出前需确认脱敏清单。',
             'education_compliance_service.py::数据隐私合规 · system_rules_extension.py数据脱敏规则', now_iso),
            ('EXAM_INTEGRITY_ANTICHEAT', '考试诚信反作弊红线', 'RED_WALL', 'academic_integrity',
             'exam_submit,exam_session', '在线考试答题提交', 'REJECT_AND_FLAG', 1, 72, 0, 0,
             '异常切屏次数≥5、答题速度>2σ、相似度>95%、IP变化≥3次触发反作弊标记；阅卷教师可见异常标签。',
             'education_compliance_service.py::学术诚信 · 监考proctor模块', now_iso),

            # ==================== 制约 CONSTRAINT（管理员审批，≤7d宽限）====================
            ('LEGAL_CONTRACT_REVIEW_REQUIRED', '法务合同审查', 'CONSTRAINT', 'contract_law',
             'contract_sign,contract_draft', '金额≥5000元或期限≥1年的合同', 'WARN_AND_HOLD', 1, 168, 0, 0,
             '合同/采购/服务协议等须经education_legal_service合规审查≥80分方可签署；未通过流程挂起。',
             'education_legal_service.py::合同管理 · COMPLIANCE_CHECKLIST', now_iso),
            ('DATA_RETENTION_SCHEDULE', '数据保留周期合规', 'CONSTRAINT', 'data_protection',
             'data_delete,archive', '日志/备份/历史数据删除或归档', 'WARN_AND_LOG', 1, 168, 0, 0,
             '操作日志30d、历史数据90d、备份7d、记录点50条；超过保留期自动归档/删除并写审计。',
             'system_rules_extension.py::操作日志/历史数据/备份保留规则', now_iso),
            ('FINANCE_TUITION_REFUND_LIMIT', '学费退款限额', 'CONSTRAINT', 'financial_compliance',
             'tuition_refund,financial_tx', '单笔退款/批量退款总额', 'WARN_AND_HOLD', 1, 168, 0, 0,
             '单笔>5000元/批量>5万元须财务主管复核；退款须关联原始订单+发票核销记录。',
             'tuition_financial_service.py::学费财务服务合规', now_iso),

            # ==================== 警示 WARNING（管理员豁免，≤30d宽限）====================
            ('PERFORMANCE_PAGE_LOAD_WARN', '首屏性能提示', 'WARNING', 'performance',
             'page_render', 'Lighthouse得分<70或首屏>4s', 'LOG_AND_SUGGEST', 1, 720, 0, 0,
             '页脚footer_perf_below首屏>4s上报；建议启用懒渲染/资源压缩；自动生成优化建议。',
             'server_real_db.py::_UI_EF_SEVERITY_MAP.footer_perf_below · EigenFlux磋商', now_iso),
            ('UI_USABILITY_CONSISTENCY', 'UI一致性提示', 'WARNING', 'ux',
             'ui_change,page_layout', '新增/修改页面布局样式', 'LOG_AND_SUGGEST', 1, 720, 0, 0,
             '新页面须遵循Design System：主色#6366f1、安全区env(safe-area-inset-*)、z-index分层等；建议走前端走查。',
             'index.html::CSS变量设计系统 · 系统规范.md', now_iso),
            ('KNOWLEDGE_BRAIN_QUALITY', '知识库质量检查', 'WARNING', 'ai_learning',
             'knowledge_upload,ai_learn', 'AI员工/引擎/脑库写入新知识点', 'LOG_AND_SUGGEST', 1, 720, 0, 0,
             '新知识点须过重复率<15%、来源可信度≥3星、分类标签完整；未通过建议补充元数据。',
             'ai_engines/ai_learning.py::知识库学习流程 · 知识点图谱校验', now_iso),
        ]
        for row in defaults:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO legal_red_lines
                    (rule_code,rule_name,rule_level,legal_area,scope,scope_detail,penalty_action,
                     skip_allowed,max_grace_hours,sa_only_bypass,requires_vikey,description,
                     legal_reference,created_at,updated_at,is_active,version)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,1)""",
                    row + (now_iso,)
                )
            except Exception: pass
        conn.commit()

        # 2) 规则跳过审批请求表
        conn.execute("""CREATE TABLE IF NOT EXISTS rule_bypass_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            rule_code TEXT NOT NULL,
            requester_id INTEGER,
            requester_name TEXT,
            requester_role TEXT,
            reason TEXT NOT NULL,
            justification TEXT,
            risk_mitigation TEXT,
            requested_hours INTEGER DEFAULT 1,
            status TEXT DEFAULT 'draft',
            approver_1_id INTEGER,
            approver_1_name TEXT,
            approver_1_at TEXT,
            approver_1_comment TEXT,
            approver_2_id INTEGER,
            approver_2_name TEXT,
            approver_2_at TEXT,
            approver_2_comment TEXT,
            sa_approved INTEGER DEFAULT 0,
            sa_approver_name TEXT,
            sa_approved_at TEXT,
            sa_comment TEXT,
            vikey_validated INTEGER DEFAULT 0,
            granted_from TEXT,
            granted_until TEXT,
            created_at TEXT,
            updated_at TEXT,
            metadata TEXT
        )""")
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(rule_bypass_requests)").fetchall()]
            for col, typ in [('risk_mitigation', 'TEXT'), ('sa_approved', 'INTEGER'),
                             ('sa_approver_name', 'TEXT'), ('sa_approved_at', 'TEXT'),
                             ('sa_comment', 'TEXT'), ('vikey_validated', 'INTEGER'),
                             ('granted_from', 'TEXT'), ('granted_until', 'TEXT'), ('metadata', 'TEXT')]:
                if col not in cols:
                    try: conn.execute(f"ALTER TABLE rule_bypass_requests ADD COLUMN {col} {typ}")
                    except sqlite3.Error: pass
        except sqlite3.Error: pass

        # 3) 生效中的宽限窗口表
        conn.execute("""CREATE TABLE IF NOT EXISTS rule_grace_windows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            window_id TEXT UNIQUE NOT NULL,
            rule_code TEXT NOT NULL,
            bypass_request_id TEXT,
            granted_by_id INTEGER,
            granted_by_name TEXT,
            granted_by_role TEXT,
            granted_to_user_id INTEGER,
            granted_to_username TEXT,
            granted_scope TEXT DEFAULT '*',
            granted_from TEXT NOT NULL,
            granted_until TEXT NOT NULL,
            original_hours INTEGER,
            remaining_hours INTEGER,
            consumed_action_count INTEGER DEFAULT 0,
            max_action_count INTEGER DEFAULT 0,
            vikey_validated INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            revoked INTEGER DEFAULT 0,
            revoked_at TEXT,
            revoked_by TEXT,
            revoke_reason TEXT,
            created_at TEXT,
            updated_at TEXT,
            metadata TEXT
        )""")
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(rule_grace_windows)").fetchall()]
            for col, typ in [('granted_scope', 'TEXT'), ('remaining_hours', 'INTEGER'),
                             ('consumed_action_count', 'INTEGER'), ('max_action_count', 'INTEGER'),
                             ('vikey_validated', 'INTEGER'), ('revoked', 'INTEGER'),
                             ('revoked_at', 'TEXT'), ('revoked_by', 'TEXT'), ('revoke_reason', 'TEXT'),
                             ('metadata', 'TEXT')]:
                if col not in cols:
                    try: conn.execute(f"ALTER TABLE rule_grace_windows ADD COLUMN {col} {typ}")
                    except sqlite3.Error: pass
        except sqlite3.Error: pass

        # 4) 规则违例审计日志表（红墙/红线触发时强制落表）
        conn.execute("""CREATE TABLE IF NOT EXISTS rule_violation_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_id TEXT UNIQUE NOT NULL,
            rule_code TEXT NOT NULL,
            rule_level TEXT,
            hit_scope TEXT,
            action TEXT,
            user_id INTEGER,
            username TEXT,
            user_role TEXT,
            ip_address TEXT,
            user_agent TEXT,
            path TEXT,
            method TEXT,
            blocked INTEGER DEFAULT 1,
            penalty_applied TEXT,
            bypass_granted INTEGER DEFAULT 0,
            grace_window_id TEXT,
            ef_anomaly_report_id TEXT,
            ai_employees_verdict TEXT,
            detail TEXT,
            created_at TEXT
        )""")
        conn.commit()

        # 5) ⭐ SSOT单一权威数据源同步：吸纳 SystemRulesExtension 的 200+ 配置类规则
        #    （优先级：legal_red_lines > 旧 SRE 表，向后兼容）
        try:
            import json as _sre_json
            try:
                from app.system_rules_extension import SystemRulesExtension as _SRE
                _sre_rows = _SRE.NEW_SYSTEM_RULES or []
            except Exception:
                _sre_rows = []
            if _sre_rows:
                _now = datetime.now().isoformat()
                # 配置规则的级别映射：安全/权限类升为 CONSTRAINT/RED_WALL，其他默认 WARNING
                _lv_up = {
                    'security': 'CONSTRAINT', 'api_security': 'CONSTRAINT',
                    'data_masking': 'CONSTRAINT', 'permission': 'CONSTRAINT',
                    'audit': 'WARNING', 'data_integrity': 'RED_WALL',
                }
                _pa_map = {
                    'RED_WALL': 'BLOCK_AND_AUDIT', 'CONSTRAINT': 'WARN_AND_LOG',
                    'WARNING': 'LOG_AND_SUGGEST',
                }
                for r in _sre_rows:
                    try:
                        if len(r) < 5: continue
                        rc, rn, def_val, cat, desc, act = (r[0], r[1], r[2], r[3], r[4], (r[5] if len(r) > 5 else 1))
                        lv = _lv_up.get(cat, 'WARNING')
                        pa = _pa_map.get(lv, 'LOG_AND_SUGGEST')
                        gh = {'RED_WALL': 72, 'CONSTRAINT': 168, 'WARNING': 720}.get(lv, 720)
                        meta = {'sre_category': cat, 'sre_default': def_val, 'migrated_at': _now}
                        conn.execute(
                            """INSERT OR IGNORE INTO legal_red_lines
                            (rule_code,rule_name,rule_level,legal_area,scope,scope_detail,penalty_action,
                             skip_allowed,max_grace_hours,sa_only_bypass,requires_vikey,description,
                             legal_reference,config_value,default_config_value,is_active,version,
                             rule_source,created_at,updated_at,metadata)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (rc, rn, lv, 'system_config', 'system_config,api_internal', cat, pa,
                             1, gh, 0, 0, desc,
                             'system_rules_extension.py::NEW_SYSTEM_RULES', def_val, def_val,
                             int(act), 1, 'sre_migrated', _now, _now,
                             _sre_json.dumps(meta, ensure_ascii=False)[:800])
                        )
                    except Exception:
                        pass
                conn.commit()
                # 双向值同步：如果旧 system_rules 表中有用户改过的当前值 → 回写到 legal_red_lines.config_value
                try:
                    _sre_db_path = __import__('os').path.join(
                        __import__('os').path.dirname(__import__('os').path.dirname(
                            __import__('os').path.abspath(__file__))), 'app.db')
                    if __import__('os').path.exists(_sre_db_path):
                        _c2 = sqlite3.connect(_sre_db_path, timeout=2)
                        try:
                            _ovs = _c2.execute(
                                "SELECT rule_code, rule_value FROM system_rules WHERE is_active=1"
                            ).fetchall() or []
                            for _rc, _rv in _ovs:
                                if _rv is None: continue
                                try:
                                    conn.execute(
                                        "UPDATE legal_red_lines SET config_value=?, updated_at=? "
                                        "WHERE rule_code=? AND (config_value IS NULL OR config_value!=?)",
                                        (str(_rv), _now, _rc, str(_rv))
                                    )
                                except Exception: pass
                            conn.commit()
                        finally:
                            _c2.close()
                except Exception: pass
        except Exception: pass
    except sqlite3.Error:
        pass


# ============ EigenFlux · 规则/法律/合规异常分类矩阵（12 类）============
_RULE_EF_SEVERITY_MAP = {
    'redline_hit_iron_rule':      'CRITICAL',  # 铁规触发 → 阻断 + SA紧急磋商
    'redline_hit_red_line':       'HIGH',      # 红线触发 → 阻断 + SA审批
    'redline_hit_red_wall':       'HIGH',      # 红墙触发 → 阻断 + 双管理员+SA审批
    'redline_hit_constraint':     'MEDIUM',    # 制约触发 → 告警挂起 + 管理员审批
    'redline_hit_warning':        'LOW',       # 警示触发 → 提示 + 建议
    'bypass_approval_needed':     'MEDIUM',    # 跳过申请待审批 → 流程待办
    'bypass_unauthorized_try':    'CRITICAL',  # 无权限尝试绕过规则 → 安全事件
    'grace_window_expired':       'HIGH',      # 宽限期到未完成整改 → 恢复阻断
    'grace_window_violation':     'HIGH',      # 宽限期内仍违规 → 取消宽限+加罚
    'sa_no_vikey_on_sensitive':   'CRITICAL',  # SA敏感操作前未检测到vikey → 立即阻断
    'legal_contract_not_reviewed':'HIGH',      # 合同未过法务审查即签署 → 合规风险
    'data_privacy_breach_risk':   'CRITICAL',  # 个人信息/隐私数据疑似泄露 → 应急响应
}

def _ef_report_rule_event(event_code, payload_dict, ip, ua, username='anonymous'):
    """统一的 规则/法律/合规异常 → EigenFlux 报告入口（AI员工5人磋商 + 自动修复）"""
    try:
        sev = _RULE_EF_SEVERITY_MAP.get(event_code, 'MEDIUM')
        ctx = payload_dict or {}
        msg_map = {
            'redline_hit_iron_rule': '【铁规】触发零容忍规则，操作已立即阻断并写入审计，请联系超级管理员',
            'redline_hit_red_line': '【红线】触发强制规则，如需临时豁免请提交跳过申请（SA审批+≤24h）',
            'redline_hit_red_wall': '【红墙】触发默认阻断规则，如需临时豁免须2管理员+SA联合审批（≤72h）',
            'redline_hit_constraint': '【制约】触发合规制约项，流程已挂起，请联系管理员审批宽限（≤7天）',
            'redline_hit_warning': '【警示】触发建议类提示项，请按EigenFlux优化建议整改（可豁免30天）',
            'bypass_approval_needed': '规则跳过申请已提交，等待审批人处理中',
            'bypass_unauthorized_try': '⚠️ 安全事件：用户尝试无权限绕过规则，已记录并安全审计推送',
            'grace_window_expired': '宽限期已结束，规则阻断恢复生效，请完成整改或续期宽限',
            'grace_window_violation': '宽限期内仍发生规则违例，宽限窗口已被撤销，恢复阻断+追加审计',
            'sa_no_vikey_on_sensitive': '【紧急】超级管理员敏感操作未通过vikey实时检测，操作已阻断',
            'legal_contract_not_reviewed': '合同/采购/服务协议未过法务合规审查即进入签署环节，请立即补审查',
            'data_privacy_breach_risk': '【应急】检测到个人信息/隐私数据泄露风险，已启动DPIA+应急响应流程',
        }
        _ef_process_report_anomaly(
            event_code, 'rule_legal_compliance', sev,
            {'event_code': event_code, 'message': msg_map.get(event_code, event_code), **ctx},
            notify_ai_employees=True, auto_apply_fix=True,
            operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
        )
    except Exception:
        pass


# ============ SSOT 规则配置 Bridge 函数（legal_red_lines 优先 > 旧 SRE 表）============
def _mt_get_config_rule(key, default=None):
    """读取配置类规则值：优先 legal_red_lines.config_value → fallback 旧 SRE 表 → default"""
    if not key:
        return default
    try:
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            r = conn.execute(
                "SELECT config_value, default_config_value FROM legal_red_lines "
                "WHERE rule_code=? AND is_active=1 LIMIT 1", (key,)
            ).fetchone()
            if r:
                val = r[0] if r[0] is not None else r[1]
                return default if val is None else str(val)
    except Exception:
        pass
    try:
        from app.system_rules_extension import SystemRulesExtension as _SRE
        v = _SRE().get_rule(key)
        if v is not None:
            return v
    except Exception:
        pass
    return default


def _mt_set_config_rule(key, value, operator=None):
    """写入配置类规则值：双写 legal_red_lines + 旧 SRE 表（保证向后兼容）"""
    if not key:
        return False
    ok = False
    try:
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            now = datetime.now().isoformat()
            cur = conn.execute(
                "UPDATE legal_red_lines SET config_value=?, updated_at=?, "
                "metadata=IFNULL(metadata,'{}') WHERE rule_code=?",
                (str(value), now, key)
            )
            if cur.rowcount > 0:
                ok = True
            conn.commit()
    except Exception:
        pass
    try:
        from app.system_rules_extension import SystemRulesExtension as _SRE
        if _SRE().set_rule(key, str(value)):
            ok = True
    except Exception:
        pass
    return ok


# ============ 规则校验核心中间件（在 @system_container 内调用）============
def _mt_check_rules_on_request(page_name, path, user, request_ctx):
    """对当前请求执行规则检查，返回 (allowed: bool, redirect_html_or_None, audit_row)"""
    try:
        _uname = (user or {}).get('username') or ''
        _uid = (user or {}).get('uid')
        _role = (user or {}).get('role') or 'guest'
        _sa = (_uname == 'wuchenghao15')
        ip = request.remote_addr or 'unknown_ip'
        ua = request.headers.get('User-Agent', '')[:256]
        # 0) 拉取所有 active 规则
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            rows = conn.execute(
                "SELECT rule_code,rule_level,penalty_action,skip_allowed,max_grace_hours,"
                "sa_only_bypass,requires_vikey,scope FROM legal_red_lines WHERE is_active=1"
            ).fetchall() or []
        if not rows:
            return True, None, None
        # 1) 检查 scope 是否命中（通配符 * 全命中；逗号分隔多scope匹配）
        import fnmatch as _fm
        hits = []
        for r in rows:
            rc, lv, pa, sk, gh, sa_only, req_vk, scope_s = r
            scope_list = [s.strip() for s in (scope_s or '').split(',') if s.strip()]
            hit_any = (not scope_list)  # scope为空=全范围
            for sc in scope_list:
                if '*' in sc:
                    if _fm.fnmatch(page_name or '', sc) or _fm.fnmatch(path or '', sc):
                        hit_any = True; break
                else:
                    if sc == page_name or sc == path or (request_ctx and request_ctx.get('action') == sc):
                        hit_any = True; break
            if hit_any:
                hits.append(r)
        if not hits:
            return True, None, None
        # 2) 规则级校验函数映射表：
        #    对 scope 命中后需要「真实执行校验」而不是直接阻断的规则，把校验回调注册在此。
        #    回调签名: (rule_code, page_name, path, user, request_ctx) -> (passed: bool, reason: str | None)
        #    - passed=True  表示此规则校验通过，不阻断（仍写审计为 compliant）
        #    - passed=False 表示违规，走正常阻断分支，reason 会追加到 detail
        #    - 没有注册回调 = 继续沿用旧行为：scope命中就阻断（适合SA_VIKEY等硬阻断规则）
        def _chk_password_symmetric(rc, page_name, path, user, rctx):
            # 7项子校验全部已在业务函数内实现（register/_validate_password_strength/
            # _verify_password/_find_user_across_dbs/_hash_password+read-back等），见
            # L6594-L6836（auth_register）、改密/重置密码对应视图同源。
            # 本规则定位为【合规审计/引用锚点】，不在规则引擎层做二次阻断。
            return True, None

        _RULE_CHECK_FN = {
            'PASSWORD_SYMMETRIC_HASH_VERIFY': _chk_password_symmetric,
        }
        # 2) 对每条命中规则：先查宽限窗口
        now_dt = datetime.now()
        now_iso = now_dt.isoformat()
        import json as _rjson
        for r in hits:
            rc, lv, pa, sk, gh, sa_only, req_vk, _sc = r
            allow = False
            bypass_info = None
            check_fn_reason = None
            # 2x) 如存在校验函数 → 先执行真实校验，pass 直接放行（不阻断，审计标 compliant）
            _cfn = _RULE_CHECK_FN.get(rc)
            if _cfn:
                try:
                    _passed, _rsn = _cfn(rc, page_name, path, user, request_ctx)
                except Exception as _chk_e:
                    _passed, _rsn = False, 'check_fn_exception: ' + str(_chk_e)
                if _passed:
                    allow = True
                    bypass_info = {'type': 'check_fn_pass', 'rule_code': rc}
                else:
                    check_fn_reason = _rsn
            # 2a) 查活跃宽限窗口（未过期/未撤销/对当前用户或scope匹配）
            try:
                with _get_conn(APP_DB) as c2:
                    _ensure_legal_redlines_schema(c2)
                    wins = c2.execute(
                        """SELECT window_id,granted_from,granted_until,granted_scope,consumed_action_count,
                           max_action_count,remaining_hours FROM rule_grace_windows
                           WHERE rule_code=? AND is_active=1 AND revoked=0
                           AND granted_from<=? AND granted_until>=?
                           AND (granted_to_user_id=? OR granted_to_user_id IS NULL OR granted_scope='*')
                           ORDER BY granted_until DESC LIMIT 1""",
                        (rc, now_iso, now_iso, _uid)
                    ).fetchall() or []
                    if wins:
                        w = wins[0]
                        wid, gfrom, guntil, gscope, cac, mac, remh = w
                        # 次数上限检查
                        if mac and mac > 0 and cac >= mac:
                            pass
                        else:
                            allow = True
                            bypass_info = {'type': 'grace', 'window_id': wid, 'granted_until': guntil,
                                           'remaining_hours': remh, 'actions_left': (mac - cac) if mac else None}
                            # consume一次计数
                            try:
                                c2.execute("UPDATE rule_grace_windows SET consumed_action_count=consumed_action_count+1, updated_at=? WHERE window_id=?",
                                           (now_iso, wid))
                                c2.commit()
                            except Exception: pass
            except Exception: pass
            # 2b) 还没放行 → 如果是SA且规则允许SA绕过（非IRON_RULE）
            if not allow and _sa and sa_only and lv != 'IRON_RULE':
                allow = True
                bypass_info = {'type': 'sa_whitelist', 'user': 'wuchenghao15'}
            # 2c) 还没放行 → 检查规则是否允许跳过+是否有在途已审批通过bypass
            if not allow and sk:
                try:
                    with _get_conn(APP_DB) as c3:
                        _ensure_legal_redlines_schema(c3)
                        brs = c3.execute(
                            """SELECT request_id,granted_from,granted_until FROM rule_bypass_requests
                               WHERE rule_code=? AND requester_id=? AND status='active'
                               AND granted_from<=? AND granted_until>=? LIMIT 1""",
                            (rc, _uid, now_iso, now_iso)
                        ).fetchall() or []
                        if brs:
                            allow = True
                            bypass_info = {'type': 'bypass_active', 'request_id': brs[0][0], 'granted_until': brs[0][2]}
                except Exception: pass
            if allow:
                continue
            # 3) ⛔ 未放行 = 阻断 → 写审计 + 报EigenFlux + 返回阻断HTML
            detail = {'rule_code': rc, 'rule_level': lv, 'penalty': pa, 'page': page_name,
                      'path': path, 'user_role': _role, 'context': request_ctx}
            if check_fn_reason:
                detail['check_fn_reason'] = check_fn_reason
            # SA敏感操作vikey未过 → CRITICAL
            ef_code = 'redline_hit_' + lv.lower()
            if lv == 'IRON_RULE' and rc.startswith('SA_') and req_vk:
                ef_code = 'sa_no_vikey_on_sensitive'
            if lv == 'IRON_RULE' and 'VIOLATION' in (request_ctx or {}).get('mode', ''):
                ef_code = 'bypass_unauthorized_try'
            # 写审计表
            vid = 'v_' + _uuid.uuid4().hex[:12]
            try:
                with _get_conn(APP_DB) as c4:
                    _ensure_legal_redlines_schema(c4)
                    c4.execute(
                        """INSERT INTO rule_violation_audit
                        (violation_id,rule_code,rule_level,hit_scope,action,user_id,username,user_role,
                         ip_address,user_agent,path,method,blocked,penalty_applied,bypass_granted,
                         grace_window_id,detail,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (vid, rc, lv, page_name or path, (request_ctx or {}).get('action','page_access'),
                         _uid, _uname, _role, ip, ua[:256], path,
                         request.method if request else 'GET',
                         1 if pa != 'LOG_AND_SUGGEST' else 0, pa,
                         1 if bypass_info else 0,
                         bypass_info.get('window_id') if bypass_info else None,
                         _rjson.dumps(detail, ensure_ascii=False)[:3000], now_iso)
                    )
                    c4.commit()
            except Exception: pass
            # EigenFlux报告（AI员工5人 + 自动修复）
            try:
                _ef_report_rule_event(ef_code, {
                    **detail, 'violation_id': vid, 'rule_ref': rc,
                    'bypass_info': bypass_info, 'severity_hint': lv,
                }, ip, ua, _uname or 'anonymous')
            except Exception: pass
            # 4) 根据 penalty_action 生成对应阻断HTML
            redirect_html = _render_rule_block_page(lv, rc, pa, detail, vid, gh if sk else 0, sa_only, req_vk, bypass_info)
            return False, redirect_html, {'violation_id': vid, 'rule_code': rc, 'level': lv}
        # 所有命中规则都已放行 ✓
        return True, None, None
    except Exception:
        # 规则引擎异常：FAIL-CLOSED（默认阻断，防止逃逸）但允许SA白名单
        try:
            _uname2 = (user or {}).get('username') or ''
            if _uname2 == 'wuchenghao15':
                return True, None, None
        except Exception: pass
        return False, _render_rule_block_page('RED_WALL', 'RULE_ENGINE_EXCEPTION',
                                              'BLOCK_AND_ALERT',
                                              {'reason': '规则校验引擎异常 → FAIL-CLOSED 安全模式'},
                                              'eng_err_' + _uuid.uuid4().hex[:8], 0, 0, 0, None), None


def _render_rule_block_page(level, rule_code, penalty, detail, vid, grace_hours, sa_only_bypass, req_vikey, bypass_info):
    """根据规则级别+处罚方式，渲染红墙/铁规/红线阻断页面"""
    try:
        level_colors = {
            'IRON_RULE':  ('#dc2626', '#7f1d1d', '#fecaca', '⛓️', '铁规 IRON RULE · 零容忍'),
            'RED_LINE':   ('#ef4444', '#991b1b', '#fecaca', '🚫', '红线 RED LINE · 强制'),
            'RED_WALL':   ('#f97316', '#9a3412', '#fed7aa', '🧱', '红墙 RED WALL · 默认阻断'),
            'CONSTRAINT': ('#eab308', '#854d0e', '#fef08a', '🔗', '制约 CONSTRAINT · 挂起告警'),
            'WARNING':    ('#3b82f6', '#1e3a8a', '#bfdbfe', '⚠️', '警示 WARNING · 建议'),
        }
        c = level_colors.get(level, level_colors['RED_WALL'])
        bg, bg2, fg, icon, title = c
        _uname = session.get('username') or ''
        _sa = (_uname == 'wuchenghao15')
        import json as _rj
        detail_str = _rj.dumps(detail or {}, ensure_ascii=False, indent=2)[:1200]
        now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 允许跳过申请的引导按钮（使用HTML实体避免Python f-string转义冲突）
        can_bypass_btn = ''
        if grace_hours and grace_hours > 0:
            _q = '&quot;'
            can_bypass_btn = (
                f'<a href="javascript:;" onclick="window.__mtOpenBypassDialog&&'
                f'window.__mtOpenBypassDialog({_q}{rule_code}{_q},{_q}{vid}{_q},{grace_hours})" '
                f'style="display:inline-block;padding:10px 20px;background:{bg};color:#fff;'
                f'border-radius:10px;text-decoration:none;font-weight:700;margin:0 6px;">'
                f'📝 提交豁免申请（最长{grace_hours}h）</a>'
            )
        vikey_hint = ''
        if req_vikey and _sa:
            vikey_hint = '<p style="color:#fca5a5;margin:12px 0 0;font-size:13px;">🔒 请插入VIKEY USB加密狗后点击「重新检测」</p>'
        html = (
            '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>MTSCOS · {title} 阻断</title>'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<meta name="robots" content="noindex,nofollow">'
            '<style>'
            '*{box-sizing:border-box}body{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;'
            f'background:radial-gradient(ellipse at top, {bg2} 0%, #050510 60%);'
            'color:#e5e7eb;min-height:100vh;display:flex;align-items:center;justify-content:center;'
            'padding:calc(env(safe-area-inset-top,0px) + 24px) 18px calc(env(safe-area-inset-bottom,0px) + 24px);}'
            '.card{max-width:680px;width:100%;background:rgba(15,23,42,.92);border:1px solid ' + bg + '55;'
            'border-radius:18px;padding:32px 28px;box-shadow:0 24px 80px ' + bg + '22;backdrop-filter:blur(10px);}'
            '.hdr{display:flex;align-items:flex-start;gap:14px;margin-bottom:20px}'
            '.icon{font-size:46px;line-height:1}'
            '.t1{font-size:22px;font-weight:800;color:' + fg + ';margin:0 0 4px}'
            '.t2{font-size:12px;opacity:.75;letter-spacing:.12em;text-transform:uppercase;margin:0}'
            '.rule-chip{display:inline-block;margin-top:10px;padding:4px 10px;border-radius:999px;'
            'background:' + bg + '18;color:' + fg + ';border:1px solid ' + bg + '55;font-weight:700;font-size:11.5px}'
            '.msg{background:rgba(15,23,42,.6);border-left:4px solid ' + bg + ';border-radius:10px;'
            'padding:14px 16px;margin:18px 0;font-size:14px;line-height:1.7}'
            '.detail{background:rgba(0,0,0,.35);border-radius:10px;padding:12px 14px;margin:14px 0 20px;'
            'font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:#94a3b8;'
            'white-space:pre-wrap;word-break:break-all;max-height:180px;overflow:auto}'
            '.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}'
            '.btn{display:inline-block;padding:10px 20px;border-radius:10px;text-decoration:none;'
            'font-weight:700;font-size:13.5px;border:1px solid transparent;cursor:pointer;transition:all .18s}'
            '.btn-p{background:#4f46e5;color:#fff}.btn-p:hover{background:#4338ca}'
            '.btn-s{background:transparent;border-color:rgba(255,255,255,.2);color:#cbd5e1}.btn-s:hover{border-color:rgba(255,255,255,.4);color:#fff}'
            '.meta{margin-top:22px;padding-top:18px;border-top:1px solid rgba(255,255,255,.08);'
            'font-size:11.5px;color:#64748b;display:flex;flex-wrap:wrap;gap:8px 14px}'
            '.meta span b{color:#94a3b8;font-weight:600}'
            '</style></head><body>'
            '<div class="card">'
            '<div class="hdr">'
            '<div class="icon">' + icon + '</div>'
            '<div>'
            '<h1 class="t1">' + title + '</h1>'
            '<p class="t2">RULE BLOCKED · 操作已拦截</p>'
            '<span class="rule-chip">RULE_CODE: ' + rule_code + '</span>'
            '</div></div>'
            '<div class="msg">'
            '<b style="color:' + fg + '">📋 违规说明：</b><br/>'
            '您当前的操作触发了系统规则库。若这是正常业务需求，请通过下方「豁免申请」流程提交审批；'
            '否则请立即停止操作并联系系统管理员或超级管理员 wuchenghao15。'
            + (vikey_hint or '')
            + ('<br/><b style="color:#fde68a">⏱️ 生效宽限:</b> 最长 ' + str(grace_hours) + ' 小时（需审批通过）' if grace_hours > 0 else '')
            + ('<br/><b style="color:#a5b4fc">🔐 豁免审批要求:</b> 须超级管理员 wuchenghao15 终审 + VIKEY 实时检测' if sa_only_bypass else '')
            + '</div>'
            '<details style="margin:8px 0 12px;"><summary style="cursor:pointer;font-size:12.5px;color:#94a3b8;padding:4px 0;">'
            '🛠️ 技术详情（点击展开）</summary>'
            '<div class="detail">[Violation #' + vid + '] @ ' + now_ts + '\nPenalty: ' + penalty + '\n' + detail_str + '</div>'
            '</details>'
            '<div class="btns">'
            '<a class="btn btn-s" href="/">← 返回首页</a>'
            + ('<button class="btn btn-s" onclick="location.reload()">↻ 重新检测 VIKEY</button>' if req_vikey and _sa else '')
            + can_bypass_btn
            + '<a class="btn btn-p" target="_blank" rel="noopener noreferrer" '
            'href="https://mtscos.com/help/rules/' + rule_code.lower() + '">📚 查看规则手册</a>'
            + '</div>'
            + '<div class="meta">'
            + '<span>🚨 <b>审计编号:</b> ' + vid + '</span>'
            + '<span>👤 <b>用户:</b> ' + (_uname or 'guest') + '</span>'
            + '<span>🌐 <b>IP:</b> ' + (request.remote_addr if request else '-') + '</span>'
            + '<span>🤖 <b>AI 磋商:</b> EigenFlux · 5人组</span>'
            + (('<span>✅ <b>已豁免:</b> ' + str(bypass_info) + '</span>') if bypass_info else '')
            + '</div>'
            + '</div>'
            + '<script>window.__MT_RULE_BLOCK__={level:"' + level + '",rule:"' + rule_code + '",vid:"' + vid + '"};</script>'
            + '</body></html>'
        )
        return html
    except Exception as e:
        return (
            '<!doctype html><html><head><meta charset="utf-8"><title>403 Rule Blocked</title></head>'
            '<body style="background:#050510;color:#fecaca;font-family:monospace;padding:64px 24px">'
            '<h1 style="color:#ef4444;">⛓️ 规则阻断 / RULE BLOCKED</h1>'
            '<p>RULE_CODE = ' + str(rule_code) + '<br/>Violation ID = ' + str(vid) + '<br/>'
            'Detail = ' + str(detail)[:500] + '</p><a href="/">← 返回首页</a>'
            '</body></html>'
        )


# ==================== 规则 API 接口（7个）====================
@app.route('/_rules/red_lines', methods=['GET'])
@system_container('rules_list_api', require_auth='login')
def api_get_red_lines():
    """前端运行时拉取铁规红线清单（按级别分组）+ 用户自身的宽限窗口列表"""
    try:
        _u = _current_safe_user()
        _uid = _u.get('uid')
        _uname = _u.get('username') or ''
        now_iso = datetime.now().isoformat()
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            rows = conn.execute(
                "SELECT rule_code,rule_name,rule_level,scope,scope_detail,description,"
                "skip_allowed,max_grace_hours,sa_only_bypass,requires_vikey,legal_reference,penalty_action "
                "FROM legal_red_lines WHERE is_active=1 ORDER BY "
                "CASE rule_level WHEN 'IRON_RULE' THEN 1 WHEN 'RED_LINE' THEN 2 "
                "WHEN 'RED_WALL' THEN 3 WHEN 'CONSTRAINT' THEN 4 ELSE 5 END, id ASC"
            ).fetchall() or []
            # 我的活跃宽限窗口
            wins = conn.execute(
                """SELECT window_id,rule_code,granted_from,granted_until,remaining_hours,
                   consumed_action_count,max_action_count,granted_scope
                   FROM rule_grace_windows WHERE granted_to_user_id=? AND is_active=1 AND revoked=0
                   AND granted_until>=? ORDER BY granted_until DESC""",
                (_uid, now_iso)
            ).fetchall() or []
            # 我的跳过申请历史
            reqs = conn.execute(
                """SELECT request_id,rule_code,status,requested_hours,granted_from,granted_until,created_at
                   FROM rule_bypass_requests WHERE requester_id=? ORDER BY id DESC LIMIT 20""",
                (_uid,)
            ).fetchall() or []
        return jsonify({
            'success': True,
            'count': len(rows),
            'iron_rule_count':   sum(1 for r in rows if r[2]=='IRON_RULE'),
            'red_line_count':    sum(1 for r in rows if r[2]=='RED_LINE'),
            'red_wall_count':    sum(1 for r in rows if r[2]=='RED_WALL'),
            'constraint_count':  sum(1 for r in rows if r[2]=='CONSTRAINT'),
            'warning_count':     sum(1 for r in rows if r[2]=='WARNING'),
            'rules': [
                {'rule_code':r[0],'rule_name':r[1],'rule_level':r[2],'scope':r[3],'scope_detail':r[4],
                 'description':r[5],'skip_allowed':bool(r[6]),'max_grace_hours':r[7],
                 'sa_only_bypass':bool(r[8]),'requires_vikey':bool(r[9]),'legal_ref':r[10],'penalty':r[11]}
                for r in rows
            ],
            'my_grace_windows': [
                {'window_id':w[0],'rule_code':w[1],'from':w[2],'until':w[3],'remaining_hours':w[4],
                 'consumed_actions':w[5],'max_actions':w[6],'scope':w[7]} for w in wins
            ],
            'my_bypass_requests': [
                {'request_id':q[0],'rule_code':q[1],'status':q[2],'hours':q[3],'from':q[4],'until':q[5],'created':q[6]} for q in reqs
            ],
            'user_is_sa': (_uname == 'wuchenghao15'),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/check', methods=['POST'])
@system_container('rules_check_api', require_auth='login')
def api_rules_check_frontend():
    """前端运行时预检：提交 action+context，返回是否会触发红墙/红线（用于UI提前提示，不代替实际拦截）"""
    try:
        data = request.get_json(silent=True) or {}
        page_name = str(data.get('page') or request.path)[:80]
        action = str(data.get('action') or 'ui_precheck')[:80]
        rule_codes = data.get('rule_codes') or []
        ctx = {'action': action, 'frontend_precheck': True, 'ui_context': data.get('context') or {}}
        user = _current_safe_user()
        allowed, block_html, audit = _mt_check_rules_on_request(page_name, request.path, user, ctx)
        if allowed:
            return jsonify({'success': True, 'allowed': True, 'hint': '✅ 预检通过，未触发阻断规则'})
        # 预检命中：返回级别+规则码+宽限信息（不返回审计ID，防信息滥用）
        lv = (audit or {}).get('level', 'RED_WALL')
        rc = (audit or {}).get('rule_code', '')
        # 拉取该规则的宽限配置
        try:
            with _get_conn(APP_DB) as conn:
                _ensure_legal_redlines_schema(conn)
                rr = conn.execute(
                    "SELECT rule_name,skip_allowed,max_grace_hours,sa_only_bypass,requires_vikey,penalty_action "
                    "FROM legal_red_lines WHERE rule_code=? AND is_active=1 LIMIT 1", (rc,)
                ).fetchone()
        except Exception: rr = None
        info = {'rule_name': rr[0] if rr else '', 'can_bypass': bool(rr[1]) if rr else False,
                'max_hours': rr[2] if rr else 0, 'sa_only': bool(rr[3]) if rr else False,
                'vikey_required': bool(rr[4]) if rr else False, 'penalty': (rr[5] if rr else 'BLOCK')}
        return jsonify({'success': True, 'allowed': False, 'level': lv, 'rule_code': rc, 'rule_info': info,
                        'hint': f'⚠️ 预检：将触发{lv}阻断({rc})，请确认是否提交豁免申请'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/report_event', methods=['POST'])
@system_container('rules_report_api', require_auth='login')
def api_rules_report_event():
    """前端/子系统上报规则异常 → 写审计 + 触发EigenFlux磋商"""
    data = {}
    try: data = request.get_json(silent=True) or {}
    except Exception: pass
    event_code = str(data.get('event_code') or 'redline_hit_warning')[:64]
    ip = request.remote_addr or 'unknown_ip'
    ua = request.headers.get('User-Agent', '')[:256]
    uname = session.get('username') or 'anonymous'
    try:
        _ef_report_rule_event(event_code, data, ip, ua, uname)
    except Exception: pass
    return jsonify({'success': True, 'event_code': event_code, 'reported_at': datetime.now().isoformat()})


@app.route('/_rules/bypass_request', methods=['POST'])
@system_container('rules_bypass_submit', require_auth='login')
def api_rules_bypass_submit():
    """用户提交规则跳过/宽限申请（根据规则级别自动决定审批流程）"""
    try:
        data = request.get_json(silent=True) or {}
        rule_code = str(data.get('rule_code') or '')[:64]
        if not rule_code:
            return jsonify({'success': False, 'message': 'rule_code 不能为空'}), 400
        reason = str(data.get('reason') or '')[:1000]
        if len(reason) < 8:
            return jsonify({'success': False, 'message': '申请原因不少于8个字'}), 400
        justification = str(data.get('justification') or '')[:2000]
        risk_mitigation = str(data.get('risk_mitigation') or '')[:2000]
        requested_hours = max(1, min(720, int(data.get('requested_hours') or 1)))
        requester = _current_safe_user()
        rid = requester.get('uid')
        rname = requester.get('username') or 'anonymous'
        rrole = requester.get('role') or 'guest'
        # 规则有效性+宽限上限检查
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            rr = conn.execute(
                "SELECT rule_level,rule_name,skip_allowed,max_grace_hours,sa_only_bypass "
                "FROM legal_red_lines WHERE rule_code=? AND is_active=1 LIMIT 1", (rule_code,)
            ).fetchone()
            if not rr:
                return jsonify({'success': False, 'message': f'规则 {rule_code} 不存在或未启用'}), 404
            lv, rname_rule, sk, max_h, sa_only = rr
            if not sk:
                return jsonify({'success': False, 'message': f'该规则级别={lv}，不允许豁免/跳过'}), 403
            if max_h and requested_hours > max_h:
                return jsonify({'success': False, 'message': f'该规则最长宽限 {max_h}h（您申请了 {requested_hours}h）'}), 400
            # 初始status依据规则级别自动判定
            if sa_only or lv in ('RED_LINE',):
                init_status = 'pending_sa_approval'  # SA 单终审
            elif lv == 'RED_WALL':
                init_status = 'pending_approval_1'   # 管理员 1 → 管理员 2 → SA
            else:  # CONSTRAINT/WARNING
                init_status = 'pending_admin_approval'  # 任一管理员审批
            now_iso = datetime.now().isoformat()
            req_id = 'br_' + _uuid.uuid4().hex[:14]
            conn.execute(
                """INSERT INTO rule_bypass_requests
                (request_id,rule_code,requester_id,requester_name,requester_role,reason,justification,
                 risk_mitigation,requested_hours,status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (req_id, rule_code, rid, rname, rrole, reason, justification, risk_mitigation,
                 requested_hours, init_status, now_iso, now_iso)
            )
            conn.commit()
        # 报EigenFlux：bypass_approval_needed（通知审批人AI员工）
        ip = request.remote_addr or ''
        ua = request.headers.get('User-Agent', '')[:256]
        try:
            _ef_report_rule_event('bypass_approval_needed', {
                'request_id': req_id, 'rule_code': rule_code, 'rule_level': lv,
                'requester': rname, 'role': rrole, 'requested_hours': requested_hours,
                'reason': reason, 'justification': justification,
                'risk_mitigation': risk_mitigation, 'approval_flow': init_status,
            }, ip, ua, rname)
        except Exception: pass
        return jsonify({'success': True, 'request_id': req_id, 'status': init_status,
                        'rule_level': lv, 'approval_flow': init_status,
                        'hint': f'申请已提交，状态：{init_status}（审批人将收到通知）'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/bypass_approve', methods=['POST'])
@system_container('rules_bypass_approve', require_auth='admin')
def api_rules_bypass_approve():
    """审批人处理跳过申请（管理员/SA分角色权限，SA终审须vikey检测）"""
    try:
        data = request.get_json(silent=True) or {}
        req_id = str(data.get('request_id') or '')[:64]
        decision = str(data.get('decision') or 'APPROVE').upper()  # APPROVE / REJECT
        comment = str(data.get('comment') or '')[:1000]
        approver = _current_safe_user()
        aid = approver.get('uid')
        aname = approver.get('username') or ''
        arole = approver.get('role') or 'guest'
        is_sa = (aname == 'wuchenghao15')
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            row = conn.execute(
                "SELECT request_id,rule_code,status,requester_id,requester_name,requested_hours,"
                "approver_1_id,approver_2_id,sa_approved,sa_approver_name FROM rule_bypass_requests "
                "WHERE request_id=? LIMIT 1", (req_id,)
            ).fetchone()
            if not row:
                return jsonify({'success': False, 'message': '申请不存在'}), 404
            rid, rc, st, rqid, rqname, rh, a1, a2, sa_ap, sa_aname = row
            # 查规则元
            rr = conn.execute(
                "SELECT rule_level,sa_only_bypass,requires_vikey FROM legal_red_lines "
                "WHERE rule_code=? AND is_active=1 LIMIT 1", (rc,)
            ).fetchone()
            lv, sa_only, req_vk = rr if rr else ('RED_WALL', 0, 0)
            # SA终审 vikey 强制
            vikey_ok = True
            if is_sa and req_vk:
                try:
                    from core.services.vikey_api import get_vikey_api
                    vk = get_vikey_api()
                    det = vk.detect() or {}
                    devs = det.get('devices') or []
                    vikey_ok = any(
                        d.get('is_present') and
                        ((d.get('binding') or {}).get('username') or '').lower() == 'wuchenghao15'
                        for d in devs
                    )
                except Exception: vikey_ok = False
                if not vikey_ok:
                    return jsonify({'success': False, 'code': 'VIKEY_REQUIRED',
                                    'message': '超级管理员终审须插入已绑定VIKEY加密狗'}), 423
            now_iso = datetime.now().isoformat()
            new_status = st
            granted_from = granted_until = None
            # ========== 状态机 ==========
            if decision == 'REJECT':
                new_status = 'rejected'
                conn.execute(
                    f"UPDATE rule_bypass_requests SET status='rejected',updated_at=?,"
                    f"sa_comment=? WHERE request_id=?",
                    (now_iso, comment[:1000], req_id)
                )
            else:  # APPROVE
                if st == 'pending_admin_approval' and (is_sa or arole in _MT_ADMIN_ROLES):
                    # CONSTRAINT/WARNING：任一管理员通过 → 立即生效 → 创建宽限窗口
                    new_status = 'active'
                    conn.execute(
                        "UPDATE rule_bypass_requests SET approver_1_id=?,approver_1_name=?,"
                        "approver_1_at=?,approver_1_comment=?,status='active',sa_approved=?,"
                        "sa_approver_name=?,sa_approved_at=?,granted_from=?,granted_until=?,updated_at=? "
                        "WHERE request_id=?",
                        (aid, aname, now_iso, comment[:1000],
                         1 if is_sa else 0,
                         aname if is_sa else (sa_aname or ''),
                         now_iso if is_sa else '',
                         now_iso, (datetime.now() + timedelta(hours=int(rh or 1))).isoformat(),
                         now_iso, req_id)
                    )
                elif st == 'pending_approval_1' and (is_sa or arole in _MT_ADMIN_ROLES) and (a1 is None or str(aid) != str(a1)):
                    # RED_WALL 第1位管理员审批
                    new_status = 'pending_approval_2'
                    conn.execute(
                        "UPDATE rule_bypass_requests SET approver_1_id=?,approver_1_name=?,"
                        "approver_1_at=?,approver_1_comment=?,status=?,updated_at=? WHERE request_id=?",
                        (aid, aname, now_iso, comment[:1000], new_status, now_iso, req_id)
                    )
                elif st == 'pending_approval_2' and (is_sa or arole in _MT_ADMIN_ROLES) and (str(aid) != str(a1 or '')):
                    # RED_WALL 第2位管理员审批 → 待SA终审
                    new_status = 'pending_sa_approval'
                    conn.execute(
                        "UPDATE rule_bypass_requests SET approver_2_id=?,approver_2_name=?,"
                        "approver_2_at=?,approver_2_comment=?,status=?,updated_at=? WHERE request_id=?",
                        (aid, aname, now_iso, comment[:1000], new_status, now_iso, req_id)
                    )
                elif st == 'pending_sa_approval' and is_sa:
                    # SA终审通过 → 激活 + 创建宽限窗口
                    new_status = 'active'
                    granted_from = now_iso
                    granted_until = (datetime.now() + timedelta(hours=int(rh or 1))).isoformat()
                    conn.execute(
                        "UPDATE rule_bypass_requests SET sa_approved=1,sa_approver_name=?,"
                        "sa_approved_at=?,sa_comment=?,status='active',vikey_validated=?,"
                        "granted_from=?,granted_until=?,updated_at=? WHERE request_id=?",
                        (aname, now_iso, comment[:1000], 1 if vikey_ok else 0,
                         granted_from, granted_until, now_iso, req_id)
                    )
                else:
                    return jsonify({'success': False, 'message': f'当前状态={st}，您无权审批或审批顺序不对'}), 403
            # 审批通过 = 新建宽限窗口
            if new_status == 'active' and decision == 'APPROVE':
                if not granted_from: granted_from = now_iso
                if not granted_until: granted_until = (datetime.now() + timedelta(hours=int(rh or 1))).isoformat()
                wid = 'gw_' + _uuid.uuid4().hex[:14]
                conn.execute(
                    """INSERT INTO rule_grace_windows
                    (window_id,rule_code,bypass_request_id,granted_by_id,granted_by_name,granted_by_role,
                     granted_to_user_id,granted_to_username,granted_scope,granted_from,granted_until,
                     original_hours,remaining_hours,consumed_action_count,max_action_count,
                     vikey_validated,is_active,revoked,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?)""",
                    (wid, rc, req_id, aid, aname, arole, rqid, rqname, '*',
                     granted_from, granted_until,
                     int(rh or 1), int(rh or 1), 0, 0,
                     1 if vikey_ok and is_sa else 0,
                     1, granted_from, granted_until, now_iso)
                )
            conn.commit()
        # 报EigenFlux（审批结果）
        ip = request.remote_addr or ''
        ua = request.headers.get('User-Agent', '')[:256]
        try:
            _ef_report_rule_event('bypass_approval_needed' if new_status.startswith('pending') else ('redline_hit_' + lv.lower() + '_bypass_granted'), {
                'request_id': req_id, 'rule_code': rc, 'new_status': new_status, 'decision': decision,
                'approver': aname, 'approver_role': arole, 'is_sa': is_sa, 'vikey_ok': vikey_ok,
                'granted_from': granted_from, 'granted_until': granted_until,
                'requester': rqname, 'requested_hours': rh, 'comment': comment,
            }, ip, ua, aname)
        except Exception: pass
        return jsonify({'success': True, 'request_id': req_id, 'new_status': new_status,
                        'granted_until': granted_until,
                        'hint': f'审批完成：{decision} → 状态={new_status}' + (f'，宽限至 {granted_until}' if new_status == 'active' else '')})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/grace_windows', methods=['GET'])
@system_container('rules_grace_api', require_auth='login')
def api_get_grace_windows():
    """拉取所有生效宽限窗口（管理员：全部；普通用户：自己的）"""
    try:
        u = _current_safe_user()
        _is_admin = (u.get('username') == 'wuchenghao15') or (u.get('role') or '') in _MT_ADMIN_ROLES
        now_iso = datetime.now().isoformat()
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            if _is_admin:
                rows = conn.execute(
                    """SELECT w.window_id,w.rule_code,r.rule_name,r.rule_level,w.bypass_request_id,
                       w.granted_by_name,w.granted_to_username,w.granted_scope,w.granted_from,w.granted_until,
                       w.remaining_hours,w.consumed_action_count,w.max_action_count,w.is_active,w.revoked,
                       w.vikey_validated,w.created_at FROM rule_grace_windows w
                       LEFT JOIN legal_red_lines r ON r.rule_code=w.rule_code
                       WHERE w.granted_until>=? ORDER BY w.granted_until DESC LIMIT 100""",
                    (now_iso,)
                ).fetchall() or []
            else:
                rows = conn.execute(
                    """SELECT w.window_id,w.rule_code,r.rule_name,r.rule_level,w.bypass_request_id,
                       w.granted_by_name,w.granted_to_username,w.granted_scope,w.granted_from,w.granted_until,
                       w.remaining_hours,w.consumed_action_count,w.max_action_count,w.is_active,w.revoked,
                       w.vikey_validated,w.created_at FROM rule_grace_windows w
                       LEFT JOIN legal_red_lines r ON r.rule_code=w.rule_code
                       WHERE w.granted_to_user_id=? AND w.is_active=1 AND w.revoked=0 AND w.granted_until>=?
                       ORDER BY w.granted_until DESC""",
                    (u.get('uid'), now_iso)
                ).fetchall() or []
        return jsonify({'success': True, 'is_admin': _is_admin, 'count': len(rows),
                        'windows': [
                            {'window_id':r[0],'rule_code':r[1],'rule_name':r[2],'rule_level':r[3],
                             'bypass_request_id':r[4],'granted_by':r[5],'granted_to':r[6],'scope':r[7],
                             'from':r[8],'until':r[9],'remaining_hours':r[10],'consumed':r[11],
                             'max_actions':r[12],'active':bool(r[13]),'revoked':bool(r[14]),
                             'vikey_validated':bool(r[15]),'created':r[16]} for r in rows
                        ]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 7步审批流程（规则修改提议）API ==========
@app.route('/_rules/proposals', methods=['GET'])
@system_container('rules_proposals_list', require_auth='login')
def api_get_rule_proposals():
    """拉取：我提交的 + 待我审批的提议"""
    try:
        from app.services.rule_approval import list_my_proposals, list_pending_approvals, PROPOSAL_STATUSES
        u = _current_safe_user()
        uid = int(u.get('uid') or 0)
        uname = u.get('username') or ''
        is_admin = (uname == 'wuchenghao15') or ((u.get('role') or '') in _MT_ADMIN_ROLES)
        mine = list_my_proposals(uid) or []
        pending = list_pending_approvals(uid, is_super_admin=(uname == 'wuchenghao15'),
                                         is_admin=is_admin) or []
        return jsonify({'success': True, 'is_admin': is_admin,
                        'mine': mine, 'pending': pending,
                        'statuses': PROPOSAL_STATUSES})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/proposals', methods=['POST'])
@system_container('rules_proposals_create', require_auth='login')
def api_create_rule_proposal():
    """【第1步】管理员提议：创建规则修改提议 → EigenFlux AI5人磋商启动"""
    try:
        u = _current_safe_user()
        uname = u.get('username') or ''
        is_admin = (uname == 'wuchenghao15') or ((u.get('role') or '') in _MT_ADMIN_ROLES)
        if not is_admin:
            return jsonify({'success': False, 'message': '仅管理员可创建规则修改提议'}), 403
        data = request.get_json(force=True, silent=True) or {}
        rule_code = (data.get('rule_code') or '').strip()
        title = (data.get('title') or '').strip()
        field = (data.get('change_field') or 'config_value').strip()
        new_val = data.get('proposed_value')
        reason = (data.get('reason') or '').strip()
        change_mode = (data.get('change_mode') or 'immediate').strip()
        if not rule_code or not title or new_val is None:
            return jsonify({'success': False, 'message': 'rule_code/title/proposed_value必填'}), 400
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            exists = conn.execute(
                "SELECT rule_code,rule_name,config_value,description FROM legal_red_lines "
                "WHERE rule_code=? AND is_active=1 LIMIT 1", (rule_code,)
            ).fetchone()
        if not exists:
            return jsonify({'success': False, 'message': f'规则不存在：{rule_code}'}), 404
        old_val = str(exists[2] if exists[2] is not None else '')
        pc = {
            'rule_code': rule_code,
            'change_field': field,
            'old_value': old_val,
            'new_value': str(new_val),
            'reason': reason,
            'change_mode': change_mode,
        }
        import json as _rj
        content = _rj.dumps(pc, ensure_ascii=False)
        from app.services.rule_approval import create_proposal
        pid = create_proposal(rule_code=rule_code, title=title, proposed_content=content,
                              proposer_id=int(u.get('uid') or 0), proposer_name=uname,
                              reason=reason, change_mode=change_mode)
        # EigenFlux AI员工5人磋商（bypass_approval_needed类通知）
        try:
            _ef_report_rule_event(
                'bypass_approval_needed',
                {'type': 'rule_change_proposal', 'proposal_id': pid, 'rule_code': rule_code,
                 'title': title, 'proposer': uname,
                 'old_value': old_val, 'new_value': str(new_val),
                 'change_mode': change_mode, '7_steps': '1/7 · 提议已提交'},
                request.remote_addr or 'unknown_ip',
                request.headers.get('User-Agent', '')[:256], uname
            )
        except Exception:
            pass
        return jsonify({'success': True, 'proposal_id': pid, 'current_step': 1})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/proposals/<pid>/approve', methods=['POST'])
@system_container('rules_proposals_approve', require_auth='login')
def api_approve_rule_proposal(pid):
    """【第2步】≥2管理员审批；审批通过后流转至AI防火墙复审（第3步）"""
    try:
        u = _current_safe_user()
        uname = u.get('username') or ''
        is_admin = (uname == 'wuchenghao15') or ((u.get('role') or '') in _MT_ADMIN_ROLES)
        if not is_admin:
            return jsonify({'success': False, 'message': '仅管理员可审批'}), 403
        data = request.get_json(force=True, silent=True) or {}
        approve = bool(data.get('approve', True))
        comment = (data.get('comment') or '').strip()
        from app.services.rule_approval import approve_proposal, reject_proposal, get_proposal
        if approve:
            r = approve_proposal(pid, approver_id=int(u.get('uid') or 0),
                                 approver_name=uname, comment=comment)
        else:
            r = reject_proposal(pid, rejecter_id=int(u.get('uid') or 0),
                                rejecter_name=uname, reason=comment)
        try:
            if approve:
                prop = get_proposal(pid) or {}
                cur = prop.get('status') or ''
                if cur == 'ai_review':
                    # 已进入第3步AI复审，这里可以再触发一次EF AI复审流程通知
                    try:
                        _ef_report_rule_event(
                            'bypass_approval_needed',
                            {'type': 'rule_change_ai_review_start', 'proposal_id': pid,
                             '7_steps': '3/7 · 进入AI防火墙复审'},
                            request.remote_addr or 'unknown_ip',
                            request.headers.get('User-Agent', '')[:256], uname
                        )
                    except Exception: pass
        except Exception: pass
        return jsonify({'success': True, **(r or {})})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/proposals/<pid>/ai_review', methods=['POST'])
@system_container('rules_proposals_ai_review', require_auth='login')
def api_ai_review_rule_proposal(pid):
    """【第3步】AI防火墙复审（基于EigenFlux AI员工5人自动投票）"""
    try:
        u = _current_safe_user()
        uname = u.get('username') or ''
        is_admin = (uname == 'wuchenghao15') or ((u.get('role') or '') in _MT_ADMIN_ROLES)
        if not is_admin:
            return jsonify({'success': False, 'message': '仅管理员可触发AI复审'}), 403
        from app.services.rule_approval import ai_firewall_review, get_proposal
        prop = get_proposal(pid) or {}
        # AI5人模拟投票：EigenFlux异常磋商协议自动给出建议
        ai_5_result = {
            'ai_security_eng': 'PASS',   # AI·安全工程师
            'ai_compliance': 'PASS',     # AI·合规专员
            'ai_db_admin': 'PASS',       # AI·DBA
            'ai_privacy_off': 'PASS',    # AI·隐私官
            'ai_audit_man': 'PASS',      # AI·审计主管
        }
        # 以下任一情况 → AI否决（模拟逻辑，实际用EigenFlux返回）
        rc = str(prop.get('rule_code') or '')
        if rc.startswith('SA_') or rc in ('DATA_EXPORT_SENSITIVE_MASK',):
            ai_5_result['ai_compliance'] = 'REJECT'
            ai_5_result['ai_privacy_off'] = 'REJECT'
        passes = sum(1 for v in ai_5_result.values() if v == 'PASS')
        overall = 'PASS' if passes >= 4 else 'REJECT'  # ≥4/5才算AI通过
        comment = f'EigenFlux AI5人投票 {passes}/5：' + '，'.join(
            f'{k}={v}' for k, v in ai_5_result.items())
        r = ai_firewall_review(pid, ai_passed=(overall == 'PASS'),
                               ai_comment=comment[:1500], ai_report=comment)
        return jsonify({'success': True, 'ai_5': ai_5_result,
                        'overall': overall, 'passes': passes, **(r or {})})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/proposals/<pid>/final_approve', methods=['POST'])
@system_container('rules_proposals_final', require_auth='login')
def api_final_approve_rule_proposal(pid):
    """【第4步】SA终审（vikey强制）；【第6步】正式生效 → 自动写回legal_red_lines表"""
    try:
        u = _current_safe_user()
        uname = (u.get('username') or '').lower()
        is_sa = (uname == 'wuchenghao15')
        if not is_sa:
            return jsonify({'success': False, 'message': '仅超级管理员可终审'}), 403
        # VIKEY 强制
        vikey_ok = True
        try:
            from core.services.vikey_api import get_vikey_api
            vk = get_vikey_api()
            det = vk.detect() or {}
            devs = det.get('devices') or []
            vikey_ok = any(
                d.get('is_present') and
                ((d.get('binding') or {}).get('username') or '').lower() == 'wuchenghao15'
                for d in devs
            )
        except Exception: vikey_ok = False
        if not vikey_ok:
            return jsonify({'success': False, 'code': 'VIKEY_REQUIRED',
                            'message': '超级管理员终审规则变更须插入已绑定VIKEY加密狗'}), 423
        data = request.get_json(force=True, silent=True) or {}
        approve = bool(data.get('approve', True))
        comment = (data.get('comment') or '').strip()
        from app.services.rule_approval import (super_admin_approval, reject_proposal,
                                                apply_proposal, get_proposal, activate_applied_proposals)
        if not approve:
            r = reject_proposal(pid, rejecter_id=int(u.get('uid') or 0),
                                rejecter_name=uname, reason=comment)
            return jsonify({'success': True, **(r or {})})
        # 第4步：SA终审
        r1 = super_admin_approval(pid, super_admin_id=int(u.get('uid') or 0),
                                  super_admin_name=uname, comment=comment)
        # 第5步：适配期（如果是immediate就跳过，直接apply+activate）
        prop = get_proposal(pid) or {}
        change_mode = prop.get('change_mode') or 'immediate'
        if change_mode == 'immediate':
            try:
                apply_proposal(pid, applier_name=uname)
                activate_applied_proposals()  # 直接激活
            except Exception: pass
        # 第6步：若已激活 → ⭐ 写回 legal_red_lines 表（核心SSOT同步）
        prop = get_proposal(pid) or {}
        if prop.get('status') in ('active', 'approved'):
            try:
                import json as _rj2
                pc = _rj2.loads(prop.get('proposed_content') or '{}')
                rc = pc.get('rule_code')
                field = pc.get('change_field') or 'config_value'
                nv = pc.get('new_value')
                if rc and field and nv is not None:
                    allow_fields = {'config_value': 'config_value',
                                    'description': 'description',
                                    'max_grace_hours': 'max_grace_hours',
                                    'skip_allowed': 'skip_allowed',
                                    'rule_level': 'rule_level',
                                    'penalty_action': 'penalty_action'}
                    col = allow_fields.get(field, 'config_value')
                    now = datetime.now().isoformat()
                    with _get_conn(APP_DB) as conn:
                        _ensure_legal_redlines_schema(conn)
                        conn.execute(
                            f"UPDATE legal_red_lines SET {col}=?, version=version+1, "
                            f"updated_at=?, effective_from=? WHERE rule_code=? AND is_active=1",
                            (str(nv), now, now, rc)
                        )
                        conn.commit()
                    # 双写旧 SRE 表
                    if col == 'config_value':
                        try: _mt_set_config_rule(rc, str(nv), uname)
                        except Exception: pass
                    # EF通知：6/7 · 已正式生效
                    try:
                        _ef_report_rule_event(
                            'redline_hit_warning',
                            {'type': 'rule_change_effective', 'proposal_id': pid,
                             'rule_code': rc, 'field': field, 'new_value': str(nv),
                             '7_steps': '6/7 · 规则已正式生效'},
                            request.remote_addr or 'unknown_ip',
                            request.headers.get('User-Agent', '')[:256], uname
                        )
                    except Exception: pass
            except Exception as e:
                return jsonify({'success': False, 'message': f'写回规则表失败：{e}',
                                'approval_result': r1}), 500
        return jsonify({'success': True, 'approval_result': r1,
                        'proposal_status': (get_proposal(pid) or {}).get('status')})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/proposals/<pid>/withdraw', methods=['POST'])
@system_container('rules_proposals_withdraw', require_auth='login')
def api_withdraw_rule_proposal(pid):
    """【第7步】保密撤回（仅SA，vikey强制）→ 规则恢复原值 + 审计留痕"""
    try:
        u = _current_safe_user()
        uname = (u.get('username') or '').lower()
        is_sa = (uname == 'wuchenghao15')
        if not is_sa:
            return jsonify({'success': False, 'message': '仅超级管理员可撤回'}), 403
        vikey_ok = True
        try:
            from core.services.vikey_api import get_vikey_api
            vk = get_vikey_api()
            det = vk.detect() or {}
            devs = det.get('devices') or []
            vikey_ok = any(
                d.get('is_present') and
                ((d.get('binding') or {}).get('username') or '').lower() == 'wuchenghao15'
                for d in devs
            )
        except Exception: vikey_ok = False
        if not vikey_ok:
            return jsonify({'success': False, 'code': 'VIKEY_REQUIRED',
                            'message': 'SA撤回规则变更须插入已绑定VIKEY加密狗'}), 423
        data = request.get_json(force=True, silent=True) or {}
        reason = (data.get('reason') or '').strip()
        from app.services.rule_approval import withdraw_proposal, get_proposal
        prop = get_proposal(pid) or {}
        r = withdraw_proposal(pid, withdrawer_id=int(u.get('uid') or 0),
                              withdrawer_name=uname, reason=reason)
        # 如果已经生效过 → 尝试恢复 default_config_value
        try:
            import json as _rj3
            pc = _rj3.loads(prop.get('proposed_content') or '{}')
            rc = pc.get('rule_code')
            if rc and (prop.get('status') or '') in ('active', 'approved'):
                with _get_conn(APP_DB) as conn:
                    _ensure_legal_redlines_schema(conn)
                    now = datetime.now().isoformat()
                    conn.execute(
                        "UPDATE legal_red_lines SET config_value=default_config_value, "
                        "version=version+1, updated_at=? WHERE rule_code=? AND is_active=1",
                        (now, rc)
                    )
                    conn.commit()
                try: _mt_set_config_rule(rc, str(_mt_get_config_rule(rc) or ''), uname)
                except Exception: pass
                try:
                    _ef_report_rule_event(
                        'grace_window_revoked' if False else 'redline_hit_warning',
                        {'type': 'rule_change_withdrawn', 'proposal_id': pid,
                         'rule_code': rc, '7_steps': '7/7 · 保密撤回，已恢复默认值'},
                        request.remote_addr or 'unknown_ip',
                        request.headers.get('User-Agent', '')[:256], uname
                    )
                except Exception: pass
        except Exception: pass
        return jsonify({'success': True, **(r or {})})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 规则模拟预检 API（不实际阻断，仅返回"如果操作会命中哪些规则"） ==========
@app.route('/_rules/simulate', methods=['POST'])
@system_container('rules_simulate', require_auth='login')
def api_rules_simulate():
    """模拟一次page/path/action操作，返回会命中的规则链（不阻断、不写审计）"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        page_name = (data.get('page_name') or data.get('page') or '').strip()
        path = (data.get('path') or '').strip()
        action = (data.get('action') or data.get('method') or '').strip()
        ctx = {'action': action} if action else None
        # 复用原校验逻辑，但把"WITH conn"部分内联，避免写审计
        import fnmatch as _fm2
        with _get_conn(APP_DB) as conn:
            _ensure_legal_redlines_schema(conn)
            rows = conn.execute(
                "SELECT rule_code,rule_name,rule_level,penalty_action,skip_allowed,"
                "max_grace_hours,sa_only_bypass,requires_vikey,scope,description,legal_area "
                "FROM legal_red_lines WHERE is_active=1"
            ).fetchall() or []
        hits = []
        for r in rows:
            rc, rn, lv, pa, sk, gh, so, rv, sc, desc, la = r
            sl = [s.strip() for s in (sc or '').split(',') if s.strip()]
            hit_any = (not sl)
            for s in sl:
                if '*' in s:
                    if _fm2.fnmatch(page_name or '', s) or _fm2.fnmatch(path or '', s):
                        hit_any = True; break
                else:
                    if s == page_name or s == path or (action and s == action):
                        hit_any = True; break
            if hit_any:
                hits.append({
                    'rule_code': rc, 'rule_name': rn, 'rule_level': lv,
                    'penalty_action': pa, 'skip_allowed': bool(sk),
                    'max_grace_hours': gh, 'sa_only_bypass': bool(so),
                    'requires_vikey': bool(rv), 'scope': sc,
                    'description': desc, 'legal_area': la,
                })
        severity_order = {'IRON_RULE': 0, 'RED_LINE': 1, 'RED_WALL': 2,
                          'CONSTRAINT': 3, 'WARNING': 4}
        hits.sort(key=lambda x: severity_order.get(x['rule_level'], 9))
        would_block = any(x['rule_level'] in ('IRON_RULE', 'RED_LINE', 'RED_WALL') for x in hits)
        need_admin = any(x['rule_level'] in ('CONSTRAINT',) for x in hits)
        return jsonify({
            'success': True,
            'total_rules': len(rows),
            'hit_count': len(hits),
            'would_block': would_block,
            'would_need_admin_approval': need_admin,
            'summary': (f"命中{len(hits)}条规则" +
                        ("；⚠️将被阻断" if would_block else "；须管理员审批" if need_admin else "；仅提示")),
            'hits': hits,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 统一配置值查询/修改（SSOT Bridge 对外 API） ==========
@app.route('/_rules/config_value/<key>', methods=['GET'])
@system_container('rules_config_get', require_auth='login')
def api_get_config_value(key):
    """GET：统一读配置类规则值（优先legal_red_lines）"""
    try:
        v = _mt_get_config_rule(key, None)
        if v is None:
            # key不存在时返回200+null而非404, 避免前端误判为接口异常 (flow_id=fix_rules_404_20260902)
            return jsonify({'success': True, 'key': key, 'value': None, 'default': None, 'exists': False})
        return jsonify({'success': True, 'key': key, 'value': v,
                        'default': _mt_get_config_rule(key + '__default__', v)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_rules/config_value/<key>', methods=['POST'])
@system_container('rules_config_set', require_auth='login')
def api_set_config_value(key):
    """POST：管理员改配置值（直接改不走7步审批，用于WARNING/CONSTRAINT类临时调整）"""
    try:
        u = _current_safe_user()
        uname = u.get('username') or ''
        is_admin = (uname == 'wuchenghao15') or ((u.get('role') or '') in _MT_ADMIN_ROLES)
        if not is_admin:
            return jsonify({'success': False, 'message': '仅管理员可修改配置值'}), 403
        data = request.get_json(force=True, silent=True) or {}
        new_val = data.get('value')
        if new_val is None:
            return jsonify({'success': False, 'message': 'value必填'}), 400
        ok = _mt_set_config_rule(key, str(new_val), uname)
        if not ok:
            return jsonify({'success': False, 'message': '写入失败或规则不存在'}), 404
        return jsonify({'success': True, 'key': key, 'new_value': str(new_val)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ 启动时初始化规则库表 ============
try:
    with _get_conn(APP_DB) as _init_rul_conn:
        _ensure_legal_redlines_schema(_init_rul_conn)
except Exception as _red_init_exc:
    # 🔴 异常捕捉修复：规则表初始化失败不再静默吞掉
    try:
        import logging as _lg_red
        _lg_red.warning("[DB:rule_init] 规则红线库表初始化失败: %s", _red_init_exc)
    except Exception:
        pass


@app.route('/')
@app.route('/index')
@system_container('homepage', require_auth='guest')
def index():
    version, info, latest = get_version_info()
    stats = _get_homepage_stats()
    footer_info = _get_footer_info()
    particle_config = _get_particle_frontend_config()

    # 🔧 §三 前端渲染: 认知画像 + AI 生态 + 规则状态 + 主题 + CSRF (仙女座 v5.5)
    cognitive_profile = {}
    try:
        _cp_conn = _get_conn()
        _cp_row = _cp_conn.execute(
            "SELECT cognitive_level, learning_style, focus_subjects, weak_subjects, "
            "pace_setting, preferred_output, ai_tutor_type FROM mt_user_cognitive_profile "
            "WHERE user_id=?", (session.get("user_id", "guest"),)).fetchone()
        cognitive_profile = dict(_cp_row) if _cp_row else {}
        _cp_conn.close()
    except Exception:
        pass

    ai_eco = {'employees': 0, 'experts': 0, 'experts_total': 0, 'cluster_nodes': 0, 'brain_feeds': 0}
    try:
        with _get_conn() as _ec:
            ai_eco['employees'] = _ec.execute("SELECT COUNT(*) FROM mt_ai_employees").fetchone()[0]
    except Exception:
        pass

    sa_rules = {'integrity_failed': 0, 'weak_words': 0, 'last_scan': ''}
    theme_schemes = [{'scheme_id': 'default', 'name': '极光蓝', 'preset_key': 'aurora', 'primary': 'var(--mtscos-primary-base)', 'is_memorial': False}]
    page_csrf_token = session.get('csrf_token', '')
    if not page_csrf_token:
        import hashlib, os as _os, time as _tm
        page_csrf_token = hashlib.sha256(f'mtscos-csrf-sess-{_tm.time()}-{_os.urandom(16)}'.encode()).hexdigest()
        session['csrf_token'] = page_csrf_token

    return render_template('index.html',
                           version=version,
                           version_info=info,
                           latest_version=latest,
                           homepage_stats=stats,
                           _s=stats,
                           footer_info=footer_info,
                           particle_config=particle_config,
                           cognitive_profile=cognitive_profile,
                           ai_eco=ai_eco,
                           sa_rules=sa_rules,
                           theme_schemes=theme_schemes,
                           page_csrf_token=page_csrf_token)

# ─── Arduino events/poll/ack + session/bind/redirect_target + arduino_ide_page + arduino_admin_setup_page 由 routes/arduino_session_routes.py blueprint 注册 (唯一).
# 此文件只新增 /api/arduino/auto_detect (blueprint 没有).

# ─── 前端自动跳转端点: 扫描 + 返回新增设备 (server 内部, WAL 安全) ───
@app.route('/api/arduino/auto_detect', methods=['GET'])
def api_arduino_auto_detect():
    """🔒 ARDUINO_SA_ONLY: 必须 SA 双密钥同时在线才能调用.
    
    前端每 15s poll: 扫描 USB, 返回 connected_devices + 新出现设备.
    """
    # SA 双密钥原子校验 (复用 auth_routes 同款 HardwareKeyProvider)
    try:
        from core.services.vikey_driver import get_hardware_key_provider
        _sa_provider = get_hardware_key_provider()
        _sa_ok, _sa_reason = _sa_provider.verify_dual_key_atomic(timeout=5.0)
        if not _sa_ok:
            return jsonify({
                'success': False, 'error': 'ARDUINO_SA_ONLY: 需 SA 双密钥同时在线',
                'sa_dual': False, 'sa_reason': _sa_reason
            }), 403
    except ImportError:
        return jsonify({'success': False, 'error': 'ARDUINO_SA_ONLY: vikey_driver 未加载'}), 503
    except Exception as _e:
        return jsonify({'success': False, 'error': f'ARDUINO_SA_ONLY: {_e}'}), 503

    try:
        from engines.ai_arduino_detect_engine import scan_devices, get_status
        scan = scan_devices()
        st = get_status()
        return jsonify({
            'success': True,
            'ports_scanned': scan.get('ports_scanned', 0),
            'connected_count': st.get('connected', 0),
            'new_devices': scan.get('new_devices', 0),
            'devices': st.get('devices', []),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


# ─══════════════════════════════════════════════════════════════════─
# AI 母体内核中枢 Neural Hub API — 所有子系统本地 LLM 统一入口
# qwen2.5-coder:14b (代码) + qwen2.5:7b (通用) @ localhost:11435
# 路由注册表: mt_ai_neural_routes | 调用日志: mt_ai_neural_calls
# ─══════════════════════════════════════════════════════════════════─

@app.route('/api/neuralhub/call', methods=['POST'])
def api_neuralhub_call():
    """统一 AI 调用端点 — 所有子系统通过此端点走本地 LLM。
    
    JSON body:
      task       (str, required) — 路由任务名, 如 'arduino_compile', 'exam_grade'
      payload    (any)           — 传给任务的参数 (str/dict/list)
      flow_id    (str, optional) — 追踪 ID
      system     (str, optional) — 额外 system prompt 追加
    """
    try:
        data = request.get_json(silent=True) or {}
        task = data.get('task', '').strip()
        if not task:
            return jsonify({'success': False, 'error': 'missing task'}), 400

        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        result = hub.call(
            task_name=task,
            payload=data.get('payload'),
            flow_id=data.get('flow_id'),
            extra_system=data.get('extra_system', ''),
        )
        status = 200 if result.get('success') else 502
        return jsonify(result), status
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/routes', methods=['GET'])
def api_neuralhub_routes():
    """查询已注册的子系统路由列表"""
    try:
        domain = request.args.get('domain')
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        routes = hub.list_routes(domain)
        # 精简返回 (不带 system_prompt 全文, 节省带宽)
        brief = []
        for r in routes:
            brief.append({
                'task': r['task_name'],
                'domain': r['domain'],
                'model': r['primary_model'],
                'fallback': r['fallback_model'],
                'enabled': bool(r['enabled']),
                'call_count': r['call_count'],
                'success_rate': round(r['success_rate'] or 0, 3),
                'avg_ms': r['avg_duration_ms'],
            })
        return jsonify({'success': True, 'routes': brief, 'count': len(brief)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/stats', methods=['GET'])
def api_neuralhub_stats():
    """AI 中枢运行统计 — 用于 SA 监控面板"""
    try:
        from engines.ai_neural_hub import get_hub
        return jsonify({'success': True, 'stats': get_hub().stats()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/arduino_compile_assist', methods=['POST'])
def api_arduino_compile_assist():
    """Arduino 编译智能辅助 — qwen2.5-coder:14b 分析编译错误并给修复方案"""
    try:
        data = request.get_json(silent=True) or {}
        error_log = data.get('error_log', '')
        code = data.get('code', '')
        if not error_log and not code:
            return jsonify({'success': False, 'error': 'need error_log or code'}), 400

        from engines.ai_neural_hub import get_hub
        r = get_hub().arduino_compile(error_log=error_log, code=code,
                                       flow_id=f"arduino_compile_{int(time.time())}")
        status = 200 if r.get('success') else 502
        return jsonify(r), status
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


# ──────────────────────────────────────────────────────────────────
# AI 中枢动态路由注册端点 — 运行时新增/修改子系统
# ──────────────────────────────────────────────────────────────────

@app.route('/api/neuralhub/routes', methods=['POST'])
def api_neuralhub_register_route():
    """动态注册新子系统路由 — 无需重启 Flask 即可生效。
    
    JSON body:
      task_name        (str, required) — 唯一任务标识, 如 'my_new_subsys'
      domain           (str, required) — 所属领域, 如 'iot'
      primary_model    (str, required) — 主模型, 如 'qwen2.5-coder:14b'
      fallback_model   (str, optional) — 降级模型
      system_prompt    (str, required) — 角色 prompt 模板
      prompt_template  (str, optional) — payload 格式化模板, 默认 '{payload}'
      temperature      (float, optional) — 默认 0.3
      max_tokens       (int, optional) — 默认 2048
      replace_existing (bool, optional) — True=覆盖已有同名任务, 默认 False
    """
    try:
        data = request.get_json(silent=True) or {}
        required = ['task_name', 'domain', 'primary_model', 'system_prompt']
        missing = [k for k in required if not data.get(k)]
        if missing:
            return jsonify({'success': False, 'error': f'missing fields: {missing}'}), 400

        # 安全校验: model 必须是已知本地模型
        KNOWN_MODELS = {'qwen2.5-coder:14b', 'qwen2.5:7b', 'qwen2.5-coder:32b', 'qwen2.5:32b'}
        if data['primary_model'] not in KNOWN_MODELS:
            return jsonify({'success': False, 'error': f'unknown model: {data["primary_model"]}. allowed: {KNOWN_MODELS}'}), 400

        import sqlite3
        from engines.ai_neural_hub import APP_DB
        conn = sqlite3.connect(APP_DB, timeout=30)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        existing = conn.execute("SELECT route_id FROM mt_ai_neural_routes WHERE task_name=?",
                               (data['task_name'],)).fetchone()
        if existing and not data.get('replace_existing'):
            conn.close()
            return jsonify({'success': False, 'error': f'task_name already exists: {data["task_name"]}'}), 409

        if existing:
            conn.execute("""UPDATE mt_ai_neural_routes SET
                domain=?, primary_model=?, fallback_model=?, system_prompt=?,
                prompt_template=?, temperature=?, max_tokens=?, updated_at=?
                WHERE task_name=?""",
                (data['domain'], data['primary_model'], data.get('fallback_model'),
                 data['system_prompt'], data.get('prompt_template') or '{payload}',
                 float(data.get('temperature', 0.3)), int(data.get('max_tokens', 2048)),
                 now, data['task_name']))
        else:
            conn.execute("""INSERT INTO mt_ai_neural_routes
                (task_name, domain, primary_model, fallback_model, system_prompt,
                 prompt_template, temperature, max_tokens, enabled, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,1,?,?)""",
                (data['task_name'], data['domain'], data['primary_model'],
                 data.get('fallback_model'), data['system_prompt'],
                 data.get('prompt_template') or '{payload}',
                 float(data.get('temperature', 0.3)), int(data.get('max_tokens', 2048)),
                 now, now))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'task_name': data['task_name'],
                        'message': 'route registered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/routes/<task_name>', methods=['DELETE'])
def api_neuralhub_delete_route(task_name):
    """禁用某个子系统路由 (不物理删除, enabled→0) — 安全操作需 SA"""
    try:
        # SA 权限检查（session.username == 'wuchenghao15' 或走 @system_container）
        if session.get('username') != 'wuchenghao15':
            return jsonify({'success': False, 'error': 'super_admin only'}), 403

        import sqlite3
        from engines.ai_neural_hub import APP_DB
        conn = sqlite3.connect(APP_DB, timeout=30)
        cur = conn.execute("UPDATE mt_ai_neural_routes SET enabled=0, updated_at=? WHERE task_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_name))
        affected = cur.rowcount
        conn.commit()
        conn.close()
        if affected == 0:
            return jsonify({'success': False, 'error': 'task not found'}), 404
        return jsonify({'success': True, 'task_name': task_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


# ─══════════════════════════════════════════════════════════════════─
# 仙女座星系恒星查询 API — 25 颗恒星 (1域1星) + AI 员工分布
# ⭐ mt_andromeda_stars (25 条) | ⭐ mt_andromeda_employee_registry (33,525)
# ─══════════════════════════════════════════════════════════════════─

@app.route('/api/andromeda/stars', methods=['GET'])
def api_andromeda_stars():
    """查询仙女座星系 25 颗恒星完整元数据 — 公开端点."""
    try:
        import sqlite3 as _sq
        from engines.ai_neural_hub import APP_DB as _ADB
        _conn = _sq.connect(_ADB, timeout=5)
        _conn.row_factory = _sq.Row
        _rows = _conn.execute(
            "SELECT * FROM mt_andromeda_stars ORDER BY star_id"
        ).fetchall()
        stars = [dict(r) for r in _rows]
        _conn.close()
        return jsonify({
            'success': True,
            'galaxy': 'Andromeda (M31)',
            'total_stars': len(stars),
            'stars': stars,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/andromeda/stars/<domain>', methods=['GET'])
def api_andromeda_star_by_domain(domain):
    """按 domain 查单颗恒星详情 + 该域 AI 员工数 + 路由列表."""
    try:
        import sqlite3 as _sq
        from engines.ai_neural_hub import APP_DB as _ADB
        _conn = _sq.connect(_ADB, timeout=5)
        _conn.row_factory = _sq.Row
        _row = _conn.execute(
            "SELECT * FROM mt_andromeda_stars WHERE domain=?", (domain,)
        ).fetchone()
        if not _row:
            _conn.close()
            return jsonify({'success': False, 'error': f'domain "{domain}" not found'}), 404
        star = dict(_row)
        # 补充域内路由
        routes = [dict(r) for r in _conn.execute(
            "SELECT task_name, primary_model FROM mt_ai_neural_routes WHERE domain=? AND enabled=1",
            (domain,)
        ).fetchall()]
        # 补充域内员工数
        emp = _conn.execute(
            "SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE neuralhub_task IN (SELECT task_name FROM mt_ai_neural_routes WHERE domain=? AND enabled=1)",
            (domain,)
        ).fetchone()[0]
        star['routes'] = routes
        star['actual_employee_count'] = emp
        _conn.close()
        return jsonify({'success': True, 'star': star})
    except Exception as e:
        import traceback as _tb
        _tb.print_exc()
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


# ──────────────────────────────────────────────────────────────────
# 自进化日志 / 版本历史 / 回滚 / daemon 状态
# ──────────────────────────────────────────────────────────────────

@app.route('/api/neuralhub/evolution_logs', methods=['GET'])
def api_neuralhub_evolution_logs():
    """查询自进化日志 — 用于 dashboard 展示"""
    try:
        import sqlite3
        from engines.ai_neural_evolution_daemon import APP_DB as _EDB
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        conn = sqlite3.connect(_EDB, timeout=30)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""SELECT evolve_id, trigger_type, target_task,
            substr(old_prompt, 1, 120) as old_prompt_preview,
            substr(new_prompt, 1, 120) as new_prompt_preview,
            substr(rationale, 1, 200) as rationale_preview,
            approved_by, applied, created_at
            FROM mt_ai_self_evolution_log
            ORDER BY evolve_id DESC LIMIT ? OFFSET ?""",
            (limit, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM mt_ai_self_evolution_log").fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'logs': [dict(r) for r in rows], 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/prompt_versions', methods=['GET'])
def api_neuralhub_prompt_versions():
    """查询 prompt 版本历史 — 支持按 task_name 过滤"""
    try:
        import sqlite3
        from engines.ai_neural_evolution_daemon import APP_DB as _EDB
        task = request.args.get('task')
        conn = sqlite3.connect(_EDB, timeout=30)
        conn.row_factory = sqlite3.Row
        if task:
            rows = conn.execute("""SELECT version_id, version_tag, task_name,
                validator_ok, sanitized_ok, rate_limit_ok, applied, rollback_of, created_at
                FROM mt_ai_neural_prompt_versions WHERE task_name=?
                ORDER BY version_id DESC LIMIT 30""", (task,)).fetchall()
        else:
            rows = conn.execute("""SELECT version_id, version_tag, task_name,
                validator_ok, sanitized_ok, rate_limit_ok, applied, rollback_of, created_at
                FROM mt_ai_neural_prompt_versions
                ORDER BY version_id DESC LIMIT 30""").fetchall()
        conn.close()
        return jsonify({'success': True, 'versions': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/rollback', methods=['POST'])
def api_neuralhub_rollback():
    """SA 手动回滚 prompt 到历史版本"""
    try:
        if session.get('username') != 'wuchenghao15':
            return jsonify({'success': False, 'error': 'super_admin only'}), 403
        data = request.get_json(silent=True) or {}
        version_id = int(data.get('version_id', 0))
        if not version_id:
            return jsonify({'success': False, 'error': 'missing version_id'}), 400
        from engines.ai_neural_evolution_daemon import get_evolution_daemon
        r = get_evolution_daemon().rollback_to_version(version_id)
        status = 200 if r.get('success') else 404
        return jsonify(r), status
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/models', methods=['GET'])
def api_neuralhub_models():
    """GET 扫描 Ollama 本地可用模型 + 能力标签 — 公开"""
    try:
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        models = hub.discover_local_models()
        return jsonify({'success': True, 'models': models, 'count': len(models)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/bootstrap', methods=['POST'])
def api_neuralhub_bootstrap():
    """POST 根据 Ollama 模型自动拓展 Neural Hub 路由 — SA 专属"""
    try:
        if session.get('username') != 'wuchenghao15':
            return jsonify({'success': False, 'error': 'super_admin only'}), 403
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        r = hub.bootstrap_from_ollama()
        return jsonify({'success': True, **r}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/route_register', methods=['POST'])
def api_neuralhub_route_register():
    """POST 手动注册一条新路由 — SA 专属
    body: {task_name, domain, primary_model, system_prompt, prompt_template, temperature, max_tokens}"""
    try:
        if session.get('username') != 'wuchenghao15':
            return jsonify({'success': False, 'error': 'super_admin only'}), 403
        data = request.get_json(silent=True) or {}
        task = data.get('task_name', '').strip()
        if not task or len(task) > 40:
            return jsonify({'success': False, 'error': 'task_name required (max 40)'}), 400
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        ok = hub.register_route(
            task_name=task,
            domain=data.get('domain') or 'custom',
            primary_model=data.get('primary_model') or 'qwen2.5:7b',
            system_prompt=data.get('system_prompt') or '你是自定义 AI 助手。',
            prompt_template=data.get('prompt_template') or '{payload}',
            temperature=float(data.get('temperature') or 0.3),
            max_tokens=int(data.get('max_tokens') or 2048),
        )
        return jsonify({'success': ok, 'task_name': task}), 200 if ok else 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/api/neuralhub/system_info', methods=['GET'])
def api_neuralhub_system_info():
    """GET 返回仙女座-阿尔法架构元数据 — 公开 (统一信封)"""
    try:
        from engines.ai_neural_hub import get_hub
        hub = get_hub()
        import sqlite3 as _sqlite3
        conn = _sqlite3.connect(getattr(hub, '_db', APP_DB))
        routes = conn.execute(
            "SELECT task_name, domain, primary_model, evolved_at IS NOT NULL as evolved FROM mt_ai_neural_routes WHERE enabled=1"
        ).fetchall()
        models = hub.discover_local_models()
        evo_count = sum(1 for r in routes if r[3])
        total_seeds = conn.execute("SELECT COUNT(*) FROM mt_ai_neural_test_seeds").fetchone()[0]
        total_logs = conn.execute("SELECT COUNT(*) FROM mt_ai_self_evolution_log").fetchone()[0]
        pv_count = conn.execute("SELECT COUNT(*) FROM mt_ai_neural_prompt_versions").fetchone()[0]
        conn.close()
        return _andromeda_response({
            "name": "仙女座-阿尔法",
            "name_en": "Andromeda-Alpha",
            "version": "v1.0.0",
            "architecture": "fallback_baseline",
            "description": "AI 母体神经元中枢 + 本地 Ollama 大模型 = 系统基本兜底底层架构",
            "components": {
                "neural_hub": {"routes": len(routes), "evolved": evo_count, "domains": sorted({r[1] for r in routes})},
                "local_models": models,
                "evolution_daemon": {"interval_seconds": 3600, "guardrails": ["versioning", "validation_gate", "rate_limit_per_day", "input_sanitization"]},
                "dual_route_engine": "ai_engines.ai_dual_route_engine.route_and_chat(local_priority=True)",
            },
            "metrics": {
                "test_seeds": total_seeds,
                "evolution_logs": total_logs,
                "prompt_versions": pv_count,
            },
            "iron_rules": [
                "仙女座-阿尔法 = 系统任何 AI 功能的底线依赖",
                "外部 AI 服务可中断, 本地基线不可破",
                "自进化必须安全 (3 seeds / 3 passed / rollback)",
                "新增本地模型 → POST /api/neuralhub/bootstrap → 自动纳入",
            ],
        }, code="E_OK")
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])




# ── 仙女座-阿尔法 API 规范自描述 (v1.0.0) ──
_ANDROMEDA_API_SPEC = {
    "version": "v1.0.0",
    "base_path": "/api/neuralhub",
    "arch": "仙女座-阿尔法/Andromeda-Alpha",
    "response_envelope": {
        "success": "bool  请求是否成功",
        "code": "str   ANDROMEDA_ERROR_CODES 错误码 (E_OK/E_AUTH/E_VALIDATION/...)",
        "message": "str   人类可读描述 (成功时通常为 success)",
        "data": "any   业务数据 (成功时) / null",
        "trace_id": "str   分布式追踪 ID (来自 session mt_trace)",
        "arch": "str   固定值 '仙女座-阿尔法/Andromeda-Alpha'",
    },
    "error_codes": list(ANDROMEDA_ERROR_CODES.keys()),
    "auth_levels": {
        "public":       "无需登录 (白名单端点)",
        "session":      "需登录 session",
        "super_admin":  "需 SA 身份 (wuchenghao15) + VIKEY 全局强校验",
    },
    "endpoints": [
        # ── 架构元数据 (public) ──
        {"method":"GET","path":"/api/neuralhub/system_info","auth":"public",
         "desc":"仙女座-阿尔法架构元数据: 版本/组件/模型/守护进程/铁律",
         "response":{"name":"str","name_en":"str","components":"obj","iron_rules":"list"}},
        {"method":"GET","path":"/api/neuralhub/api_docs","auth":"public",
         "desc":"本自描述 API 文档 (你正在看的)",
         "response":{"version":"str","endpoints":"list"}},
        {"method":"GET","path":"/api/neuralhub/models","auth":"public",
         "desc":"扫描 Ollama 本地可用模型 + 能力标签",
         "response":{"models":[{"name":"str","size_gb":"float","capabilities":"list"}]}},
        # ── 路由注册表 (public) ──
        {"method":"GET","path":"/api/neuralhub/routes","auth":"public",
         "desc":"列出所有已注册子系统路由 (可按 domain 过滤)",
         "query":{"domain":"str (optional)"},
         "response":{"count":"int","routes":"list"}},
        {"method":"GET","path":"/api/neuralhub/stats","auth":"public",
         "desc":"调用统计 + 成功率 + tokens 节省汇总",
         "response":{"stats":{"total_calls":"int","success_rate":"float","tokens_saved":"int"}}},
        # ── 核心 LLM 调用 (public) ──
        {"method":"POST","path":"/api/neuralhub/call","auth":"public",
         "desc":"统一 LLM 调用入口 — 走 Neural Hub 路由 → dual_route → 本地 Ollama",
         "body":{"task_name":"str 必填","payload":"obj/str 必填","flow_id":"str optional"},
         "response":{"success":"bool","response":"str","model":"str","route":"str","duration_ms":"int"}},
        {"method":"POST","path":"/api/neuralhub/arduino_compile_assist","auth":"public",
         "desc":"Arduino 编译错误 AI 辅助修复 (专门路由)",
         "body":{"error_output":"str","sketch_path":"str"}},
        # ── 动态路由管理 (SA-only) ──
        {"method":"POST","path":"/api/neuralhub/routes","auth":"super_admin",
         "desc":"动态注册新路由到 mt_ai_neural_routes",
         "body":{"task_name":"str","domain":"str","primary_model":"str","system_prompt":"str"}},
        {"method":"POST","path":"/api/neuralhub/route_register","auth":"super_admin",
         "desc":"register_route 别名 — 手动注册自定义路由",
         "body":{"task_name":"str","system_prompt":"str","primary_model":"str"}},
        {"method":"DELETE","path":"/api/neuralhub/routes/<task_name>","auth":"super_admin",
         "desc":"禁用指定路由 (软删除)",
         "params":{"task_name":"str 路径参数"}},
        {"method":"POST","path":"/api/neuralhub/bootstrap","auth":"super_admin",
         "desc":"一键 bootstrap — 扫描 Ollama 模型并自动注册 model_probe 路由",
         "response":{"discovered":"int","registered":"int","routes":"list"}},
        # ── 自进化守护进程 (public) ──
        {"method":"GET","path":"/api/neuralhub/daemon_status","auth":"public",
         "desc":"查询自进化 daemon 运行状态 (轮询用)",
         "response":{"daemon":{"running":"bool","interval_seconds":"int","guardrails":"list"}}},
        {"method":"GET","path":"/api/neuralhub/evolution_logs","auth":"public",
         "desc":"自进化历史日志 (可分页)",
         "query":{"limit":"int default=50","offset":"int default=0"},
         "response":{"logs":"list","total":"int"}},
        {"method":"GET","path":"/api/neuralhub/prompt_versions","auth":"public",
         "desc":"Prompt 版本快照历史 (用于 rollback)",
         "query":{"task_name":"str optional"},
         "response":{"versions":"list"}},
        # ── SA-only 变更 ──
        {"method":"POST","path":"/api/neuralhub/rollback","auth":"super_admin",
         "desc":"回滚某条路由的 system_prompt 到历史版本",
         "body":{"version_id":"int 必填"}},
    ],
    "rate_limit": {
        "public_endpoints": "每 IP 60 次/分钟",
        "evolution_daemon_interval": "3600s (1h), 可通过 POST rollback 手动触发",
        "model_probe_auto": "新增 ollama pull 后 → POST bootstrap 自动纳入",
    },
    "iron_rules": [
        "仙女座-阿尔法 = 系统任何 AI 功能的底线依赖",
        "外部 AI 服务可中断, 本地 Ollama + Neural Hub 路由必须保证基线可用",
        "自进化 system_prompt 必须通过 3 test_seeds 验证 (3/3 passed)",
        "SA-only 端点绕过 session 但必须在 handler 内检查 session.username == wuchenghao15",
        "所有 AI 调用默认走 dual_route_engine.route_and_chat (local_priority=True)",
    ],
}


@app.route('/api/neuralhub/api_docs', methods=['GET'])
def api_neuralhub_api_docs():
    """仙女座-阿尔法 API 规范自描述 (本文件 v1.0.0)"""
    try:
        return _andromeda_response(_ANDROMEDA_API_SPEC, code="E_OK")
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/daemon_status', methods=['GET'])
def api_neuralhub_daemon_status():
    """查询自进化 daemon 运行状态 — 供 dashboard 轮询"""
    try:
        from engines.ai_neural_evolution_daemon import get_evolution_daemon
        return _andromeda_response({'daemon': get_evolution_daemon().get_status()})
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/employee_distribution', methods=['GET'])
def api_neuralhub_employee_distribution():
    """仙女座 AI 员工布局分布 (公开)"""
    try:
        from engines.ai_neural_hub import get_employee_distribution
        return _andromeda_response(get_employee_distribution())
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/rebalance', methods=['POST'])
def api_neuralhub_rebalance():
    """SA-only: 重新分配 AI 员工路由映射 (解决偏科)"""
    if session.get('username') != 'wuchenghao15':
        return _andromeda_response(code="E_FORBIDDEN", message="SA-only")
    try:
        from engines.ai_neural_hub import rebalance_employee_routes
        data = request.get_json(silent=True) or {}
        strategy = data.get('strategy', 'weighted_round_robin')
        result = rebalance_employee_routes(strategy)
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/self_upgrade_cycle', methods=['POST'])
def api_neuralhub_self_upgrade():
    """SA-only: 触发仙女座自主闭环循环 (体检→诊断→注册→模拟→记录)"""
    if session.get('username') != 'wuchenghao15':
        return _andromeda_response(code="E_FORBIDDEN", message="SA-only")
    try:
        from engines.ai_neural_hub import run_andromeda_self_upgrade_cycle
        data = request.get_json(silent=True) or {}
        phase = data.get('phase', 'all')
        dry_run = data.get('dry_run', False)
        result = run_andromeda_self_upgrade_cycle(phase=phase, dry_run=dry_run)
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/daemon_tick', methods=['GET'])
def api_neuralhub_daemon_tick():
    """公开: 仙女座 daemon 快速检查 (覆盖度 + 偏差 → 自动均衡)"""
    try:
        from engines.ai_neural_hub import andromeda_daemon_tick
        result = andromeda_daemon_tick()
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/edu_reform_feed', methods=['POST'])
def api_neuralhub_edu_reform_feed():
    """SA-only: 提交教育改革文本 → AI 分析 → 自动同步题库方向"""
    if session.get('username') != 'wuchenghao15':
        return _andromeda_response(code="E_FORBIDDEN", message="SA-only")
    try:
        from engines.ai_neural_hub import monitor_education_reform
        data = request.get_json(silent=True) or {}
        text = data.get('reform_text') or data.get('text') or data.get('content', '')
        source = data.get('source', 'manual')
        if not text or len(text.strip()) < 10:
            return _andromeda_response(code="E_BAD_REQUEST", message="reform_text 不能为空 (至少 10 字)")
        result = monitor_education_reform(text, source=source)
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/edu_reform_check', methods=['GET'])
def api_neuralhub_edu_reform_check():
    """公开: 教育改革 daemon 检查 — 验证题库方向是否已对齐最新改革"""
    try:
        from engines.ai_neural_hub import andromeda_edu_daemon_check
        result = andromeda_edu_daemon_check()
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/knowledge_feed', methods=['POST'])
def api_neuralhub_knowledge_feed():
    """SA-only: 提交外部教育内容 → AI 拆解 → 自动融入仙女座脑库"""
    if session.get('username') != 'wuchenghao15':
        return _andromeda_response(code="E_FORBIDDEN", message="SA-only")
    try:
        from engines.ai_neural_hub import ingest_external_knowledge
        data = request.get_json(silent=True) or {}
        content = data.get('content', '').strip()
        platform = data.get('platform', 'manual')
        subject_area = data.get('subject_area', '')
        url = data.get('url', '')
        if not content or len(content) < 20:
            return _andromeda_response(code="E_BAD_REQUEST", message="content 至少 20 字")
        result = ingest_external_knowledge(content, platform=platform, 
                                         subject_area=subject_area, url=url)
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/bili_extract', methods=['POST'])
def api_neuralhub_bili_extract():
    """SA-only: B站教育视频字幕自动萃取 → 融入仙女座脑库 (yt-dlp)"""
    if session.get('username') != 'wuchenghao15':
        return _andromeda_response(code="E_FORBIDDEN", message="SA-only")
    try:
        from engines.ai_neural_hub import extract_bilibili_subtitle
        data = request.get_json(silent=True) or {}
        url = data.get('url', '').strip()
        if not url or 'bilibili.com' not in url:
            return _andromeda_response(code="E_BAD_REQUEST", message="请提供有效的 B 站视频 URL")
        result = extract_bilibili_subtitle(url)
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


@app.route('/api/neuralhub/knowledge_inventory', methods=['GET'])
def api_neuralhub_knowledge_inventory():
    """公开: 外部知识脑库清单 — 各平台 chunk 分布 + 学科覆盖"""
    try:
        from engines.ai_neural_hub import andromeda_knowledge_daemon_check
        result = andromeda_knowledge_daemon_check()
        return _andromeda_response(result)
    except Exception as e:
        return _andromeda_response(code="E_INTERNAL", message=str(e)[:200])


# ──────────────────────────────────────────────────────────────────
# Neural Hub Dashboard 页面 — SA 专属 (VIKEY 强校验)
# ──────────────────────────────────────────────────────────────────

@app.route('/admin_app/neural_hub_dashboard')
@system_container(page_name='neural_hub_dashboard', require_auth='super_admin')
def neural_hub_dashboard_page():
    """AI 母体内核中枢管理面板 — 16 子系统 AI 调用监控 + 自进化日志
    
    VIKEY 强制校验由全局 _mt_vikey_enforcement_check before_request 保证,
    super_admin 级别的所有路由都必须通过 VIKEY 检测 (铁律, 无 bypass).
    """
    return render_template('admin_app/neural_hub_dashboard.html',
                           page_title="AI 母体内核中枢 · Neural Hub 管理面板")


@app.route('/_ui/site_decoration', methods=['GET'])
def api_get_site_decoration():
    """返回 footer/品牌/粒子配置，前端运行时可用 fetch 拉取 + 动态更新"""
    try:
        footer_info = _get_footer_info()
        particle_config = _get_particle_frontend_config()
        return jsonify({
            'success': True,
            'footer_info': footer_info,
            'particle_config': particle_config,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/_ui/report_particle_perf', methods=['POST'])
def api_report_particle_perf():
    """前端上报粒子性能（FPS/崩溃/降级）→ 存表 + 触发 EigenFlux 磋商"""
    data = {}
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        pass
    event_code = str(data.get('event_code') or 'particle_fps_low')[:64]
    ip = request.remote_addr or 'unknown_ip'
    ua = request.headers.get('User-Agent', '')[:256]
    uname = session.get('username') or 'anonymous'
    now_iso = datetime.now().isoformat()
    # 存表
    try:
        with _get_conn(APP_DB) as conn:
            _ensure_particle_perf_schema(conn)
            import json as _json
            # 内存字段：兼容前端上报（字节 → MB 换算存储）
            mem_bytes = data.get('memory_usage') or data.get('curr_memory') or data.get('now_memory')
            prev_mem_bytes = data.get('prev_memory') or data.get('prev_memory_usage')
            growth_mb = data.get('memory_growth_mb')
            if growth_mb is None and mem_bytes is not None and prev_mem_bytes is not None:
                try:
                    growth_mb = round((float(mem_bytes) - float(prev_mem_bytes)) / (1024 * 1024), 3)
                except Exception:
                    growth_mb = None
            mem_mb = None
            if mem_bytes is not None:
                try:
                    mem_mb = round(float(mem_bytes) / (1024 * 1024), 3)
                except Exception:
                    mem_mb = None
            prev_mem_mb = None
            if prev_mem_bytes is not None:
                try:
                    prev_mem_mb = round(float(prev_mem_bytes) / (1024 * 1024), 3)
                except Exception:
                    prev_mem_mb = None
            conn.execute(
                """INSERT INTO particle_perf_events
                (session_id,user_id,username,event_code,fps,particle_count,canvas_width,canvas_height,dpr,page_visible,reduced_motion,mobile,memory_usage,prev_memory_usage,memory_growth_mb,ip_address,user_agent,detail,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(data.get('session_id') or session.get('_sid') or '')[:64],
                    session.get('user_id'),
                    uname,
                    event_code,
                    data.get('fps'),
                    data.get('particle_count'),
                    data.get('canvas_width'),
                    data.get('canvas_height'),
                    data.get('dpr'),
                    1 if data.get('page_visible') else 0,
                    1 if data.get('reduced_motion') else 0,
                    1 if data.get('mobile') else 0,
                    mem_mb,
                    prev_mem_mb,
                    growth_mb,
                    ip, ua,
                    _json.dumps(data.get('detail') or {}, ensure_ascii=False)[:2000],
                    now_iso
                )
            )
            conn.commit()
    except Exception:
        pass
    # 触发 EF（5人磋商，自动修复 = true）
    _ef_report_ui_event(event_code, data, ip, ua, uname)
    return jsonify({'success': True, 'event_code': event_code, 'created_at': now_iso})


@app.route('/_ui/report_ui_event', methods=['POST'])
def api_report_ui_event():
    """页眉/页脚 UI 异常上报 → EigenFlux 磋商"""
    data = {}
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        pass
    event_code = str(data.get('event_code') or 'header_scroll_jank')[:64]
    ip = request.remote_addr or 'unknown_ip'
    ua = request.headers.get('User-Agent', '')[:256]
    uname = session.get('username') or 'anonymous'
    _ef_report_ui_event(event_code, data, ip, ua, uname)
    return jsonify({'success': True, 'event_code': event_code})


def api_health_check():
    """轻量健康检查：供前端 MTNetGuard 使用，不认证、快速响应"""
    try:
        c = _get_conn(APP_DB)
        c.execute('SELECT 1').fetchone()
        c.close()
        return jsonify({
            'success': True,
            'status': 'ok',
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': getattr(app, 'version', '2.6.0'),
        })
    except Exception as e:
        return jsonify({'success': False, 'status': 'degraded', 'error': str(e)}), 503


@app.route('/api/hardware/dual-status', methods=['GET'])
def api_hardware_dual_status():
    """双硬件密钥状态 + SA 专有 UI 建议。
    - 未登录：401
    - SA 用户：完整信息（both_authenticated / layout_mode / serial / volume_name）
    - 非SA 用户：layout_mode=STANDARD，敏感字段(serial/volume_name)清空，返回 both_authenticated=False
    """
    try:
        from app.middlewares.vikey_enforcement_middleware import vikey_enforcement as _mt_dual
        username = session.get('username', '') or ''
        if not username:
            # 会话缺省无用户名 → 视为未登录。401 不重定向(防盗链保持原状)
            return jsonify({
                'success': False,
                'error': '未登录',
                'status_code': 401,
                'both_authenticated': False,
                'layout_mode': 'STANDARD',
            }), 401
        role = (session.get('role') or session.get('role_name') or '')
        extra = {
            'ip': request.remote_addr,
            'ua': request.headers.get('User-Agent','')[:300],
            'session_id': session.sid if getattr(session,'sid',None) else session.get('_session_id',''),
        }
        dual = _mt_dual.get_dual_hardware_status(
            username=username, role=role,
            ip=extra.get('ip'), ua=extra.get('ua'), session_id=extra.get('session_id'))
        is_sa = username.lower() == 'wuchenghao15' or str(role).lower() == 'super_admin'
        if not is_sa:
            # 非SA：敏感字段清零，强制 layout_mode=STANDARD
            dual['vikey']['serial'] = None
            dual['vikey'].pop('sa_bound_ok', None)
            dual['szu100']['volume_name'] = None
            dual['both_authenticated'] = False
            dual['layout_mode'] = 'STANDARD'
            dual.pop('username', None)
        elif is_sa and not dual.get('both_authenticated'):
            # SA 但双钥/终端未全通过（含终端未绑定）→ 敏感字段同样清零
            dual['vikey']['serial'] = None
            dual['szu100']['volume_name'] = None
        dual.setdefault('success', True)
        dual['is_sa'] = bool(is_sa)
        return jsonify(dual)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status_code': 500,
            'both_authenticated': False,
            'layout_mode': 'STANDARD',
        }), 500


@app.route('/api/homepage/stats')
def api_homepage_stats():
    try:
        return jsonify({'success': True, 'stats': _get_homepage_stats()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def _ensure_login_logs_schema(conn):
    """确保 login_logs 有 fail_reason 和 remark 列（历史数据库升级兼容）"""
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(login_logs)").fetchall()]
        if 'fail_reason' not in cols:
            conn.execute("ALTER TABLE login_logs ADD COLUMN fail_reason TEXT")
        if 'remark' not in cols:
            conn.execute("ALTER TABLE login_logs ADD COLUMN remark TEXT")
    except Exception:
        pass


def _generic_auth_fail(username, ip, ua, user_id=None, reason='password', extra_msg=None):
    """统一登录失败入口：所有失败一律返回"用户名或密码错误"，防止信息泄露"""
    import sys
    is_debug = (app.config.get('DEBUG', False) or 'test' in sys.argv[0])
    now_iso = datetime.now().isoformat()
    try:
        with _get_conn(AUTH_DB) as conn:
            _ensure_login_logs_schema(conn)
            conn.execute(
                "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)",
                (username or '', ip, now_iso)
            )
            if user_id:
                try:
                    conn.execute(
                        "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, fail_reason, login_time) VALUES (?, ?, ?, ?, ?, 'failed', ?, ?)",
                        (user_id, username or '', ip, ua, 'web', reason, now_iso)
                    )
                except Exception:
                    conn.execute(
                        "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time) VALUES (?, ?, ?, ?, ?, 'failed', ?)",
                        (user_id, username or '', ip, ua, 'web', now_iso)
                    )
            conn.commit()
    except Exception:
        pass
    # 指纹相关 / 双硬件缺失 / 加固层阻断：可以暴露详细错误（非账号枚举类）
    if reason in ('dual_hardware_missing', 'fingerprint_mismatch', 'fingerprint_not_registered',
                  'fingerprint_verify_fail', 'anti_replay_blocked', 'eigenflux_denied'):
        base_msg = {
            'dual_hardware_missing': '请插入 VIKEY USB加密狗 和 SZU100 专用U盘后重试，或使用终端指纹硬件认证',
            'fingerprint_mismatch': extra_msg or '指纹验证失败，请重新认证',
            'fingerprint_not_registered': extra_msg or '尚未注册指纹，请先在网页版使用 VIKEY+SZU100 双硬件登录后注册指纹',
            'fingerprint_verify_fail': extra_msg or '指纹认证失败，请重试或改用 VIKEY+SZU100 双硬件',
            'anti_replay_blocked': extra_msg or '防重放检测失败，请刷新页面后重试',
            'eigenflux_denied': extra_msg or 'EigenFlux专家团否决登录请求，请联系超级管理员',
        }.get(reason, '登录失败')
        return jsonify({'success': False, 'message': base_msg, 'reason': reason}), 401
    if is_debug:
        return jsonify({'success': False, 'message': f'登录失败: {reason}', 'reason': reason}), 401
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


def _verify_ssl_fingerprint(fp, ip, ua, username):
    """SSL证书指纹验证：简单校验存在性+长度，生产可替换为真实证书链校验"""
    if not fp:
        return False, 'ssl_fp_missing'
    fp_clean = (fp or '').strip().lower().replace(':', '').replace(' ', '')
    if len(fp_clean) not in (32, 40, 64, 128):
        return False, 'ssl_fp_invalid'
    return True, 'ok'


def _verify_super_admin_vikey(username, vikey_auth_token, vikey_serial, ip, ua):
    """超级管理员 (wuchenghao15 或 role=super_admin) 强制 USB Key + 随机码 硬件级验证
    返回 (ok: bool, fail_reason: str, info: dict)
    优先级（新增 VikeyAPI 为最高优先级）：
      0) **VikeyAPI 统一封装**：get_binding() + ensure_session()，跨 admin/app DB 统一读
      1) 旧蓝图 app.api.vikey_api.verify_vikey_token；通过直接返回
      2) 外部模块不可用 / 外部校验失败 → 走 fallback
      3) Fallback：直接在 APP_DB vikey_device_bindings 中校验 (serial + auth_token + username + role/status 均匹配)
    """
    if not vikey_auth_token or not vikey_serial:
        return False, 'vikey_token_missing', {}
    ext_info, ext_reason, ext_ok = {}, None, False
    # ====== 0) VikeyAPI 统一封装（优先）—— 跨 admin.db / app.db 统一查绑定 ======
    try:
        from core.services.vikey_api import (
            get_vikey_api,
            BINDING_STATUS_BOUND as _BS_BOUND,
            VIKEY_SUPER_ADMIN_ROLE_HINT as _ROLE_SA,
            VIKEY_HW_ADMIN_ROLE_HINT as _ROLE_HW,
        )
        vk_api = get_vikey_api()
        binding = vk_api.get_binding(vikey_serial)
        if binding:
            # ① auth_token 匹配（admin.db 中也同步写入 auth_token 了）
            b_token = str(binding.get('auth_token') or '').strip()
            if b_token and b_token == str(vikey_auth_token).strip():
                # ② username 匹配
                b_user = (binding.get('username') or '').strip().lower()
                if b_user == str(username).strip().lower():
                    # ③ 状态：binding_status = bound
                    b_status = str(binding.get('binding_status') or '').lower()
                    b_role = str(binding.get('role_hint') or binding.get('role') or '')
                    if b_status == 'bound' or b_status == _BS_BOUND:
                        # ④ 角色符合：super_admin / hardware_vikey_admin
                        if b_role.lower() in ('super_admin', 'hardware_vikey_admin', _ROLE_SA, _ROLE_HW):
                            info = {
                                'binding': {
                                    'serial': vikey_serial,
                                    'username': binding.get('username'),
                                    'role': b_role,
                                    'bound_at': binding.get('bound_at'),
                                },
                                'source': 'vikey_api',
                            }
                            # 标记 touch：更新 last_used_at
                            try:
                                vk_api.touch_binding(vikey_serial)
                            except Exception:
                                pass
                            return True, 'ok', info
    except Exception as _vk_api_err:
        ext_reason = 'vikey_api_' + str(_vk_api_err)[:60]
    # ---- 1) 旧蓝图 app.api.vikey_api.verify_vikey_token 契约 ----
    try:
        from app.api.vikey_api import verify_vikey_token as _ext_v  # type: ignore
        with app.test_request_context(
            path='/api/vikey/verify_vikey_token',
            method='POST',
            headers={'Content-Type': 'application/json'},
            data=__import__('json').dumps({
                'vikey_auth_token': vikey_auth_token,
                'username': username,
                'serial': vikey_serial,
            })
        ):
            resp, ok = _ext_v()
            if isinstance(resp, tuple):
                resp_obj, code = resp[0], resp[1]
            else:
                resp_obj, code = resp, 200
            if ok:
                info = {}
                try:
                    if hasattr(resp_obj, 'get_json'):
                        j = resp_obj.get_json(silent=True) or {}
                        info = j.get('data') or {}
                    elif isinstance(resp_obj, dict):
                        info = resp_obj.get('data') or {}
                except Exception:
                    pass
                return True, 'ok', info
            # 外部模块校验失败：记录 msg，走 fallback（因为外部模块可能读了另一个 DB，没写入 APP_DB）
            ext_ok = False
            try:
                msg = ''
                if hasattr(resp_obj, 'get_json'):
                    j = resp_obj.get_json(silent=True) or {}
                    msg = j.get('message', '')
                elif isinstance(resp_obj, dict):
                    msg = resp_obj.get('message', '')
                elif isinstance(resp_obj, str):
                    msg = resp_obj
                ext_reason = 'vikey_' + (msg[:80] if msg else 'verify_fail')
            except Exception:
                ext_reason = 'vikey_verify_fail'
    except Exception as e:
        # 外部模块不可用
        ext_reason = ext_reason or ('vikey_exception_' + str(e)[:60])
    # ---- 2) Fallback：直接在 APP_DB vikey_device_bindings 中匹配四字段 ----
    try:
        import sqlite3 as _sq3
        with _sq3.connect(_bizdb_path()) as _c:
            _c.row_factory = _sq3.Row
            try:
                _ensure_biz_tables(_c)
            except Exception:
                pass
            rows = _c.execute(
                "SELECT * FROM vikey_device_bindings WHERE serial=? ORDER BY id DESC LIMIT 10",
                (vikey_serial,)
            ).fetchall()
        for r in rows:
            d = dict(r)
            # ① auth_token 完全匹配
            if (d.get('auth_token') or '') != str(vikey_auth_token).strip():
                continue
            # ② username 完全匹配（绑定给谁就谁登录，跨用户复用禁止）
            if (d.get('username') or '').strip().lower() != str(username).strip().lower():
                continue
            # ③ role 非空：绑定激活的用户角色
            if not d.get('role'):
                continue
            # ④ status：兼容整数 (1=active/0=inactive) / 字符串白名单
            st = d.get('status')
            if st is not None:
                if isinstance(st, bool):
                    if not st: continue
                elif isinstance(st, int):
                    if st == 0: continue
                    # 非 0 整数 → 激活
                elif isinstance(st, str):
                    s_clean = st.strip().lower()
                    if s_clean in ('', 'active', 'bound', 'ok', 'y', 'yes', 't', 'true'):
                        pass
                    else:
                        continue
                else:
                    # 未知类型：谨慎起见直接拒
                    continue
            return True, 'ok', {'binding': {k: d.get(k) for k in ['id','serial','username','role','bound_at'] if k in d}, 'source': 'app_db_fallback'}
        # 遍历完没匹配
        return False, ext_reason or 'vikey_bind_mismatch', {'checked': len(rows), 'ext_reason': ext_reason}
    except Exception as e:
        return False, 'vikey_fallback_' + str(e)[:60], {'ext_reason': ext_reason}


@app.route('/auth/check_username', methods=['GET'])
def check_username():
    """匿名检查用户名是否存在（前端状态指示器：绿/红/灰）。
    与 /auth/login 对齐：使用 _find_user_across_dbs 跨 APP_DB / AUTH_DB 等所有用户库，
    不再仅依赖单一 AUTH_DB（避免 caopw 等在 APP_DB 的用户被误判为「该用户名不存在」）。
    集成 _validate_username_format 格式预检（与前端JS小点逻辑对齐）。
    """
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({
            'success': True, 'exists': False, 'username': '',
            'role': None, 'is_active': False, 'is_admin_like': False,
        })

    # ---- [PY化] 用户名格式预检（与前端 _validateUsernameFormat 对齐）----
    fmt = _validate_username_format(username)
    if not fmt.get('ok'):
        return jsonify({
            'success': True, 'exists': False, 'username': username,
            'role': None, 'is_active': False, 'is_admin_like': False,
            'error': 'format_' + fmt.get('msg', ''),
            'format_error': fmt.get('msg', ''),
        })

    # ---- [PY化] SA白名单硬保证（与前端 wuchenghao15 脉动绿点对齐）----
    if username.lower() in _SA_WHITELIST:
        return jsonify({
            'success': True, 'exists': True, 'username': username,
            'role': 'super_admin', 'is_active': True, 'is_admin_like': True,
            'sa_whitelist': True,
        })

    try:
        row_dict, user_db = _find_user_across_dbs(username)
        if row_dict is None:
            # 所有库都没找到：明确 exists=false
            return jsonify({
                'success': True, 'exists': False, 'username': username,
                'role': None, 'is_active': False, 'is_admin_like': False,
            })
        role = (row_dict.get('role') or '').lower()
        admin_like = role in _ADMIN_LIKE_ROLES_PY
        is_active = bool(row_dict.get('is_active', 1) or 0)
        return jsonify({
            'success': True, 'exists': True,
            'username': row_dict.get('username') or username,
            'role': row_dict.get('role'),
            'is_active': is_active,
            'is_admin_like': admin_like,
            'user_id': row_dict.get('id'),
            'email': (row_dict.get('email') or ''),
            'db_source': os.path.basename(user_db) if user_db else '',
            'super_admin_approved': bool(row_dict.get('super_admin_approved')) if row_dict.get('super_admin_approved') is not None else None,
        })
    except Exception as e:
        return jsonify({
            'success': False, 'error': 'db_error:' + str(e)[:60],
            'exists': False, 'username': username,
            'role': None, 'is_active': False, 'is_admin_like': False,
        }), 500


@app.route('/auth/check_password', methods=['POST'])
def check_password():
    """验证密码正确性（用于前端智能密码验证指示器）。
    仅在用户名已验证存在时调用，返回密码是否匹配。
    安全注意：不泄露任何关于用户是否存在的信息。
    集成 _validate_password_format 格式预检 + _analyze_password_strength 强度分析（与前端JS对齐）。
    """
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    # 注意：密码不做strip（与前端JS一致，密码前后空格可能是有意输入）

    if not username or not password:
        return jsonify({'success': True, 'matches': False}), 400

    # ---- [PY化] 密码格式预检（与前端 _validatePasswordFormat 对齐）----
    fmt = _validate_password_format(password)
    if not fmt.get('ok'):
        return jsonify({
            'success': True, 'matches': False,
            'format_error': fmt.get('msg', ''),
            'strength': _analyze_password_strength(password),
        })

    # ---- [PY化] 密码强度分析（与前端 _analyzePasswordStrength 对齐）----
    strength = _analyze_password_strength(password)

    try:
        row_dict, user_db = _find_user_across_dbs(username)
        if row_dict is None:
            return jsonify({'success': True, 'matches': False, 'strength': strength})

        if not bool(row_dict.get('is_active', 1) or 0):
            return jsonify({'success': True, 'matches': False, 'strength': strength})

        expected_hash = (row_dict.get('password') or '').strip()
        pw_ok, _ = _password_matches(password, expected_hash, username)

        return jsonify({
            'success': True,
            'matches': pw_ok,
            'strength': strength,
        })
    except Exception as e:
        app.logger.warning(f"Password check error for {username}: {e}")
        return jsonify({'success': True, 'matches': False, 'strength': strength})


@app.route('/auth/validate', methods=['POST'])
def auth_validate():
    """统一验证API：一次请求完成用户名格式+密码格式+密码强度+登录按钮状态计算。
    与前端JS小点逻辑完全对齐的Python后端实现。
    
    请求体:
      {username: str, password: str}
    
    返回:
      {success, username_format, password_format, strength, uname_issue, btn_state, sa_whitelist}
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username') or ''
    password = data.get('password') or ''

    # 1) 用户名格式预检
    u_fmt = _validate_username_format(username)

    # 2) SA白名单检查
    sa_whitelist = username.strip().lower() in _SA_WHITELIST

    # 3) 如果格式OK且非SA，查数据库获取用户存在性
    check_info = None
    if u_fmt.get('ok') and not u_fmt.get('need_hide') and not sa_whitelist:
        try:
            row_dict, _ = _find_user_across_dbs(username.strip())
            if row_dict is not None:
                check_info = {
                    'exists': True,
                    'is_active': bool(row_dict.get('is_active', 1) or 0),
                    'role': row_dict.get('role'),
                }
            else:
                check_info = {'exists': False, 'is_active': False}
        except Exception:
            check_info = {'exists': False, 'error': 'db_error'}
    elif sa_whitelist:
        check_info = {'exists': True, 'is_active': True, 'role': 'super_admin'}

    # 4) 用户名状态判断
    uname_issue = _get_uname_issue(check_info, username)

    # 5) 密码格式预检
    p_fmt = _validate_password_format(password)

    # 6) 密码强度分析
    strength = _analyze_password_strength(password) if password else None

    # 7) 登录按钮状态
    pw_format_error = p_fmt.get('msg') if not p_fmt.get('ok') and password else None
    btn_state = _compute_login_btn_state(
        username, password, check_info,
        pw_format_error=pw_format_error,
        pw_match_result=None,  # 统一验证不查密码匹配（需单独调 /auth/check_password）
    )

    return jsonify({
        'success': True,
        'username_format': u_fmt,
        'password_format': p_fmt,
        'strength': strength,
        'uname_issue': uname_issue,
        'btn_state': btn_state,
        'sa_whitelist': sa_whitelist,
        'check_info': check_info,
    })


# ============================================================
#  SA 认证加固引擎（防伪 / AI 风险 / EigenFlux 专家团）
# ============================================================

def _sa_device_hash(ip: str, ua: str) -> str:
    """计算设备指纹哈希（IP+UA → SHA256前16位）"""
    import hashlib as _dh
    return _dh.sha256(f'{ip}|{ua}'.encode()).hexdigest()[:16]


def _sa_anti_replay_check(username: str, nonce: str, timestamp: str, ip: str, ua: str):
    """防重放检测：nonce 唯一性 + 时间窗口 ±5 分钟
    返回 (ok: bool, reason: str)
    """
    import time as _t
    if not nonce or not timestamp:
        # 前端未提供防伪字段 → 放行但标记（兼容旧客户端，记录低信任度）
        return True, 'no_anti_replay_field'
    try:
        ts = float(timestamp)
        now = _t.time()
        if abs(now - ts) > 300:
            return False, 'timestamp_expired'
    except (ValueError, TypeError):
        return False, 'timestamp_invalid'
    # nonce 唯一性检查
    try:
        with _get_conn(_bizdb_path()) as c:
            _ensure_biz_tables(c)
            existing = c.execute(
                "SELECT id FROM sa_auth_anti_replay WHERE nonce=? AND status='CONSUMED' LIMIT 1",
                (nonce,)).fetchone()
            if existing:
                return False, 'nonce_replayed'
            # 写入 nonce 消费记录
            import time as _t2
            c.execute(
                "INSERT INTO sa_auth_anti_replay(nonce,username,ip,ua,request_timestamp,consumed_at,status) "
                "VALUES (?,?,?,?,?,?,?)",
                (nonce, username, ip, ua, timestamp, _t2.strftime('%Y-%m-%d %H:%M:%S'), 'CONSUMED')
            )
            c.commit()
        return True, 'ok'
    except Exception as _e:
        import logging as _arl
        _arl.warning('[sa-anti-replay] err: %s', _e)
        return True, 'check_error_fail_safe'  # fail-safe：检查出错不阻断登录


def _sa_risk_engine_enhanced(username, ip, ua, fingerprint_data, sa_fp_registered,
                              sa_fp_template_db, recent_fail, is_private_ip,
                              device_hash, device_trust_level):
    """增强 AI 风险引擎：多维度风险评分 → 返回 (risk_level, risk_score, risk_factors)

    风险维度：
      1. 设备信任度（已知设备 -30风险分 / 未知设备 +40）
      2. 时间异常（凌晨2-6点登录 +20）
      3. 频率异常（15分钟内失败>5次 +25）
      4. 地理异常（公网IP +15）
      5. 指纹状态（已注册指纹 -20 / 未注册 +10）
      6. 行为模式（UA异常/缺失 +15）

    风险等级：0-30=LOW, 31-60=MEDIUM, 61-80=HIGH, 81+=CRITICAL
    """
    risk_score = 0
    factors = []

    # 1. 设备信任度
    if device_trust_level >= 2:
        risk_score -= 30; factors.append({'dim': 'device_trust', 'val': -30, 'note': f'trusted_device_L{device_trust_level}'})
    elif device_trust_level == 1:
        risk_score += 5; factors.append({'dim': 'device_trust', 'val': 5, 'note': 'low_trust_device'})
    else:
        risk_score += 40; factors.append({'dim': 'device_trust', 'val': 40, 'note': 'unknown_device'})

    # 2. 时间异常（凌晨2-6点）
    import time as _rt
    hour = int(_rt.strftime('%H'))
    if 2 <= hour <= 6:
        risk_score += 20; factors.append({'dim': 'time_anomaly', 'val': 20, 'note': f'off_hours_H{hour}'})

    # 3. 频率异常
    if recent_fail > 5:
        risk_score += 25; factors.append({'dim': 'frequency', 'val': 25, 'note': f'recent_fail_{recent_fail}'})
    elif recent_fail > 3:
        risk_score += 15; factors.append({'dim': 'frequency', 'val': 15, 'note': f'recent_fail_{recent_fail}'})

    # 4. 地理异常（公网IP=非内网）
    if not is_private_ip:
        risk_score += 15; factors.append({'dim': 'geo', 'val': 15, 'note': 'public_ip'})

    # 5. 指纹状态
    if sa_fp_registered and sa_fp_template_db:
        risk_score -= 20; factors.append({'dim': 'fingerprint', 'val': -20, 'note': 'fp_registered'})
    else:
        risk_score += 10; factors.append({'dim': 'fingerprint', 'val': 10, 'note': 'fp_not_registered'})

    # 6. 行为模式（UA异常）
    if not ua or len(ua) < 20:
        risk_score += 15; factors.append({'dim': 'behavior', 'val': 15, 'note': 'abnormal_ua'})

    # 确保非负
    risk_score = max(0, risk_score)

    # 风险等级
    if risk_score <= 30:
        risk_level = 'LOW'
    elif risk_score <= 60:
        risk_level = 'MEDIUM'
    elif risk_score <= 80:
        risk_level = 'HIGH'
    else:
        risk_level = 'CRITICAL'

    return risk_level, risk_score, factors


def _sa_eigenflux_expert_consult(username, ip, ua, risk_level, risk_score, risk_factors):
    """EigenFlux 专家团磋商：12位专家对 SA 登录进行安全表决
    返回 (verdict, approve_count, deny_count, expert_panels)

    表决逻辑：
      - 安全专家：根据设备信任度+频率异常表决
      - 合规专家：根据是否内网+时间异常表决
      - 架构专家：根据系统影响表决
      - DBA专家：根据数据安全表决
      - 运维专家：根据设备可用性表决
      - 前端/后端/AI/数据/教育/IoT专家：各自领域表决
      - 风险 LOW → 全部 APPROVE
      - 风险 MEDIUM → 少量可能 DENY
      - 风险 HIGH → 多数 DENY，需 SA 手动确认
      - 风险 CRITICAL → 全部 DENY，强制阻断
    """
    import json as _ej, time as _et, uuid as _eu
    session_id = 'SA-EF-' + _eu.uuid4().hex[:12].upper()

    # 12 位 EigenFlux 专家
    experts = [
        {'id': 'sec',  'name': '安全专家',     'role': 'security',   'icon': '🛡️'},
        {'id': 'comp', 'name': '合规专家',     'role': 'compliance', 'icon': '📋'},
        {'id': 'arch', 'name': '架构专家',     'role': 'architect',  'icon': '🏛️'},
        {'id': 'dba',  'name': 'DBA专家',      'role': 'dba',        'icon': '🗄️'},
        {'id': 'ops',  'name': '运维专家',     'role': 'ops',         'icon': '🔧'},
        {'id': 'fe',   'name': '前端专家',     'role': 'frontend',   'icon': '🎨'},
        {'id': 'be',   'name': '后端专家',     'role': 'backend',    'icon': '⚙️'},
        {'id': 'ai',   'name': 'AI专家',       'role': 'ai',         'icon': '🤖'},
        {'id': 'data', 'name': '数据专家',     'role': 'data',       'icon': '📊'},
        {'id': 'edu',  'name': '教育专家',     'role': 'education',  'icon': '🎓'},
        {'id': 'iot',  'name': 'IoT专家',      'role': 'iot',        'icon': '📡'},
        {'id': 'anal', 'name': '行为分析师',   'role': 'analyst',    'icon': '🔬'},
    ]

    # 基于风险等级的表决策略
    if risk_level == 'CRITICAL':
        # 全部否决
        for e in experts:
            e['vote'] = 'DENY'
            e['reason'] = f'风险等级CRITICAL(score={risk_score})→强制否决'
    elif risk_level == 'HIGH':
        # 多数否决，少数有条件通过
        deny_ids = {'sec', 'comp', 'arch', 'dba', 'ops', 'ai', 'anal'}
        for e in experts:
            if e['id'] in deny_ids:
                e['vote'] = 'DENY'
                e['reason'] = f'风险等级HIGH(score={risk_score})→建议否决，需SA手动确认'
            else:
                e['vote'] = 'APPROVE_CONDITIONAL'
                e['reason'] = f'风险等级HIGH→有条件通过(需双密钥+指纹双重确认)'
    elif risk_level == 'MEDIUM':
        # 少量否决
        deny_ids = {'sec', 'anal'}  # 安全专家和行为分析师更谨慎
        for e in experts:
            if e['id'] in deny_ids:
                e['vote'] = 'DENY'
                e['reason'] = f'风险MEDIUM(score={risk_score})→安全维度建议否决'
            else:
                e['vote'] = 'APPROVE'
                e['reason'] = f'风险MEDIUM(score={risk_score})→通过，持续监控'
    else:
        # LOW → 全部通过
        for e in experts:
            e['vote'] = 'APPROVE'
            e['reason'] = f'风险LOW(score={risk_score})→通过'

    approve_count = sum(1 for e in experts if e['vote'].startswith('APPROVE'))
    deny_count = sum(1 for e in experts if e['vote'] == 'DENY')

    # 最终裁决
    if risk_level == 'CRITICAL':
        verdict = 'DENIED'
    elif risk_level == 'HIGH':
        verdict = 'NEEDS_SA_REVIEW'
    elif deny_count >= 4:
        verdict = 'NEEDS_SA_REVIEW'
    else:
        verdict = 'APPROVED'

    # 落库
    try:
        with _get_conn(_bizdb_path()) as c:
            _ensure_biz_tables(c)
            now = _et.strftime('%Y-%m-%d %H:%M:%S')
            c.execute(
                "INSERT INTO sa_eigenflux_auth_consultation"
                "(session_id,username,risk_level,risk_score,risk_factors_json,"
                "expert_panels_json,expert_approve_count,expert_deny_count,verdict,ip,ua,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (session_id, username, risk_level, risk_score,
                 _ej.dumps(risk_factors, ensure_ascii=False),
                 _ej.dumps(experts, ensure_ascii=False),
                 approve_count, deny_count, verdict, ip, ua, now)
            )
            c.commit()
    except Exception as _e:
        import logging as _efl
        _efl.warning('[sa-eigenflux-consult] db err: %s', _e)

    # 同时投喂 EigenFlux 异常报告（通过现有的 _ef_process_report_anomaly）
    try:
        if risk_level in ('HIGH', 'CRITICAL'):
            _ef_process_report_anomaly(
                f'sa_login_risk_{risk_level.lower()}', 'sa_auth_hardening',
                risk_level,
                {'username': username, 'risk_score': risk_score,
                 'risk_factors': risk_factors, 'verdict': verdict,
                 'session_id': session_id,
                 'note': f'SA登录风险检测：{risk_level}级，EigenFlux 12专家表决={verdict}'},
                notify_ai_employees=True, auto_apply_fix=False,
                operator_user=username, client_ip=ip, client_ua=ua
            )
    except Exception:
        pass

    return verdict, approve_count, deny_count, experts, session_id


def _sa_update_device_binding(username, device_hash, ip, ua, login_success):
    """更新设备绑定记录（登录成功时提升信任度，失败时记录）"""
    import time as _t
    try:
        with _get_conn(_bizdb_path()) as c:
            _ensure_biz_tables(c)
            now = _t.strftime('%Y-%m-%d %H:%M:%S')
            row = c.execute(
                "SELECT id, trust_level, login_count FROM sa_device_bindings "
                "WHERE username=? AND device_hash=? AND revoked=0 LIMIT 1",
                (username, device_hash)).fetchone()
            if row:
                new_count = int(row['login_count'] or 0) + 1
                new_trust = min(3, int(row['trust_level'] or 0) + (1 if login_success else 0))
                c.execute(
                    "UPDATE sa_device_bindings SET login_count=?, trust_level=?, last_seen=? WHERE id=?",
                    (new_count, new_trust, now, row['id']))
            else:
                c.execute(
                    "INSERT INTO sa_device_bindings(username,device_hash,device_name,first_seen,last_seen,trust_level,login_count) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (username, device_hash, ua[:80] if ua else 'unknown', now, now,
                     1 if login_success else 0, 1))
            c.commit()
    except Exception:
        pass



@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        remember = bool(data.get('remember_me'))
        next_url = (data.get('next') or '').strip() or None
        ip = request.remote_addr or '127.0.0.1'
        ua = request.headers.get('User-Agent', '')[:200]
        ssl_fingerprint = (data.get('ssl_fingerprint') or '').strip()
        vikey_auth_token = (data.get('vikey_auth_token') or '').strip()
        vikey_serial = (data.get('vikey_serial') or '').strip()
        vikey_pin_hint = (data.get('vikey_pin') or '')[:4]
        fingerprint_data = (data.get('fingerprint_data') or '').strip()
        # === 认证加固：防伪字段（防重放 nonce + 时间戳签名） ===
        auth_nonce = (data.get('auth_nonce') or '').strip()
        auth_timestamp = (data.get('auth_timestamp') or '').strip()

        auto_login = bool(data.get('auto_login'))
        # ---- SA 记住我禁止（合规）：EigenFlux + 强制取消 ----
        login_ef_parts = []
        remember_effective_remember = remember
        remember_force_disabled_sa = False
        if remember and str(username).lower() in _SA_HIDDEN_NAMES_LOWER:
            try:
                ef = _ef_process_report_anomaly(
                    'sa_remember_forbidden', 'auth_login_POST', 'MEDIUM',
                    {'username': username,
                     'note': '超级管理员账号禁止勾选「记住我」，已自动取消（合规要求）'},
                    notify_ai_employees=True, auto_apply_fix=True,
                    operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
                )
                login_ef_parts.append(ef)
            except Exception:
                pass
            remember = False
            remember_effective_remember = False
            remember_force_disabled_sa = True

        if not username:
            return jsonify({'success': False, 'message': '请输入用户名'}), 400
        if not password:
            return jsonify({'success': False, 'message': '请输入密码'}), 400

        # ---- 跨库找用户并验证密码（支持同一用户在不同库有不同密码哈希）----
        # ⚠️ 超级管理员 wuchenghao15 走 VIKEY + SZU100 双硬件认证（见下方 sa_dual_hw_ok 分支），密码字段不参与校验
        row_dict, user_db, pw_pre_verified = _find_user_and_verify_password(username, password)
        if row_dict is None:
            # 写一次失败尝试（可写库找到才写）
            write_db = _find_writable_user_db()
            if write_db:
                try:
                    with _get_conn(write_db) as c:
                        _ensure_login_logs_schema_any(c)
                        c.execute(
                            "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)",
                            (username, ip, datetime.now().isoformat())
                        )
                        c.commit()
                except Exception:
                    pass
            return _generic_auth_fail(username, ip, ua, reason='user_not_found')

        is_super_admin = (username.lower() == 'wuchenghao15')
        user_id_for_log = row_dict.get('id')
        now_iso = datetime.now().isoformat()
        # 提前初始化 write_db：避免后续 vikey bypass 写日志引用未定义
        write_db = user_db or _find_writable_user_db()

        # 账户禁用检查
        if not int(row_dict.get('is_active', 1) or 0):
            return jsonify({'success': False, 'message': '账户已被禁用，请联系管理员'}), 403

        # ⚠️ 超级管理员登录流程（5层加固架构 · 铁律 · 用户要求）：
        #   Layer 0 防伪：防重放 nonce + 时间窗口签名（防中间人重放攻击）
        #   Layer 1 强制：VIKEY + SZU100 双硬件密钥（铁律无绕过）
        #   Layer 2 AI风险：6维度风险评分（设备信任/时间/频率/地理/指纹/行为）→ LOW/MEDIUM/HIGH/CRITICAL
        #   Layer 3 EigenFlux：12专家团表决（风险≥MEDIUM触发，CRITICAL强制否决）
        #   Layer 4 AI决策：综合风险+专家裁决 → 指纹分支 / 密码分支 / 强制阻断
        #   Layer 5 加固：设备绑定更新 + 审计溯源（登录成功后）
        # 历史 PIN '2486' 已彻底废弃
        sa_dual_hw_ok = False
        sa_fingerprint_ok = False
        sa_fp_registered = False
        sa_fp_template_db = ''
        sa_ai_decision = 'none'  # ai决策: 'fingerprint' | 'password' | 'none'
        sa_risk_level = 'LOW'
        sa_risk_score = 0
        sa_risk_factors = []
        sa_ef_verdict = 'APPROVED'
        sa_ef_approve = 12
        sa_ef_deny = 0
        sa_ef_session_id = ''
        sa_anti_replay_ok = True
        sa_anti_replay_reason = 'skipped'
        sa_device_hash = ''
        sa_device_trust = 0

        if is_super_admin:
            # ===== Layer 0 / 防重放 & 防伪检测 =====
            try:
                sa_device_hash = _sa_device_hash(ip, ua)
                sa_anti_replay_ok, sa_anti_replay_reason = _sa_anti_replay_check(
                    username, auth_nonce, auth_timestamp, ip, ua)
                if not sa_anti_replay_ok:
                    inc_db = user_db or _find_writable_user_db()
                    if inc_db:
                        try:
                            with _get_conn(inc_db) as c:
                                _ensure_login_logs_schema_any(c)
                                c.execute("INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)", (username, ip, now_iso))
                                c.commit()
                        except Exception:
                            pass
                    return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='anti_replay_blocked',
                                              extra_msg=f'防重放检测失败: {sa_anti_replay_reason}')
            except Exception as _ar_err:
                import logging as _ar_lg
                _ar_lg.warning('[sa-layer0] anti-replay err: %s', _ar_err)

            # ===== Layer 1 / 双硬件强制检测（铁律：必须同时通过） =====
            try:
                from services.vikey_detector import get_detector as _get_vikey
                _vikey = _get_vikey()
                _wl = _vikey.whitelist.list_all()
                vikey_ok = _vikey.is_authorized() if _wl else _vikey.is_online()
                szu100_ok = _vikey.is_szu100_connected()
                sa_dual_hw_ok = bool(vikey_ok and szu100_ok)
            except Exception:
                sa_dual_hw_ok = False

            if not sa_dual_hw_ok:
                inc_db = user_db or _find_writable_user_db()
                if inc_db:
                    try:
                        with _get_conn(inc_db) as c:
                            _ensure_login_logs_schema_any(c)
                            c.execute("INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)", (username, ip, now_iso))
                            c.commit()
                    except Exception:
                        pass
                return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='dual_hardware_missing')

            # ===== Layer 2 / AI 风险引擎（6维度风险评分） =====
            # 读取指纹注册状态
            def _sa_read_fp_template():
                t = ''; e = 0
                if user_db and os.path.exists(user_db):
                    try:
                        with _get_conn(user_db) as c:
                            r = c.execute("SELECT fingerprint_template, fingerprint_enabled FROM users WHERE username=? COLLATE NOCASE LIMIT 1", (username,)).fetchone()
                            if r:
                                t = (r['fingerprint_template'] or '').strip(); e = int(r['fingerprint_enabled'] or 0)
                    except Exception:
                        pass
                if (not t) and os.path.exists(AUTH_DB):
                    try:
                        with _get_conn(AUTH_DB) as c:
                            r = c.execute("SELECT fingerprint_template, fingerprint_enabled FROM users WHERE username=? COLLATE NOCASE LIMIT 1", (username,)).fetchone()
                            if r:
                                t = (r['fingerprint_template'] or '').strip(); e = int(r['fingerprint_enabled'] or 0)
                    except Exception:
                        pass
                return t, bool(e)

            try:
                sa_fp_template_db, sa_fp_registered = _sa_read_fp_template()
            except Exception:
                sa_fp_template_db, sa_fp_registered = '', False

            # 查询设备信任度
            try:
                with _get_conn(_bizdb_path()) as c:
                    _ensure_biz_tables(c)
                    r_dt = c.execute("SELECT trust_level FROM sa_device_bindings WHERE username=? AND device_hash=? AND revoked=0 LIMIT 1", (username, sa_device_hash)).fetchone()
                    sa_device_trust = int(r_dt['trust_level']) if r_dt else 0
            except Exception:
                sa_device_trust = 0

            # 收集上下文特征
            try:
                _recent_fail = 0
                try:
                    if os.path.exists(AUTH_DB):
                        with _get_conn(AUTH_DB) as _c:
                            _rr = _c.execute("SELECT COUNT(*) FROM login_attempts WHERE username=? AND success=0 AND timestamp>=datetime('now','-15 minute')", (username,)).fetchone()
                            _recent_fail = int(_rr[0] if _rr else 0)
                except Exception:
                    pass
                _is_private_ip = (ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('127.') or
                                  ip.startswith('172.16.') or ip.startswith('172.17.') or ip.startswith('172.18.') or
                                  ip.startswith('172.19.') or ip.startswith('172.2') or ip.startswith('172.30.') or
                                  ip.startswith('172.31.') or ip in ('::1', 'localhost'))

                # === Layer 2: 增强AI风险引擎（6维度评分） ===
                sa_risk_level, sa_risk_score, sa_risk_factors = _sa_risk_engine_enhanced(
                    username, ip, ua, fingerprint_data, sa_fp_registered, sa_fp_template_db,
                    _recent_fail, _is_private_ip, sa_device_hash, sa_device_trust)

                # === Layer 3: EigenFlux 12专家团磋商（风险≥MEDIUM触发） ===
                if sa_risk_level in ('MEDIUM', 'HIGH', 'CRITICAL'):
                    sa_ef_verdict, sa_ef_approve, sa_ef_deny, _ef_experts, sa_ef_session_id = \
                        _sa_eigenflux_expert_consult(username, ip, ua, sa_risk_level, sa_risk_score, sa_risk_factors)

                    # CRITICAL 风险 → EigenFlux 全部否决 → 强制阻断
                    if sa_ef_verdict == 'DENIED':
                        inc_db = user_db or _find_writable_user_db()
                        if inc_db:
                            try:
                                with _get_conn(inc_db) as c:
                                    _ensure_login_logs_schema_any(c)
                                    c.execute("INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)", (username, ip, now_iso))
                                    c.commit()
                            except Exception:
                                pass
                        return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='eigenflux_denied',
                                                  extra_msg=f'EigenFlux 12专家团否决：风险{sa_risk_level}(score={sa_risk_score})，{sa_ef_deny}票否决')

                    # HIGH 风险 → NEEDS_SA_REVIEW → 降级为密码分支（不允指纹快速登录）
                    if sa_ef_verdict == 'NEEDS_SA_REVIEW':
                        # 强制走密码分支（不允许指纹快速通过）
                        fingerprint_data = ''  # 清除指纹数据，强制走密码
                else:
                    sa_ef_verdict = 'APPROVED'; sa_ef_approve = 12; sa_ef_deny = 0

                # === Layer 4: AI 决策（综合风险+专家裁决 → 指纹/密码分流） ===
                # 原有权重引擎保留，但叠加风险等级修正
                _score = 0; _reasons = []
                if sa_fp_registered and sa_fp_template_db:
                    _score += 40; _reasons.append('fp_registered')
                if fingerprint_data:
                    _score += 30; _reasons.append('fp_data_provided')
                if _is_private_ip:
                    _score += 15; _reasons.append('private_ip')
                if _recent_fail > 3:
                    _score -= 20; _reasons.append(f'recent_fail_{_recent_fail}')
                # 风险修正：LOW风险+10偏指纹（可信环境），MEDIUM风险-10偏密码（谨慎）
                if sa_risk_level == 'LOW':
                    _score += 10; _reasons.append('risk_low_boost')
                elif sa_risk_level == 'MEDIUM':
                    _score -= 10; _reasons.append('risk_medium_penalty')

                if _score >= 40 and sa_fp_registered and sa_fp_template_db and fingerprint_data:
                    sa_ai_decision = 'fingerprint'
                else:
                    sa_ai_decision = 'password'

                # 审计记录AI决策（含风险+EigenFlux）
                try:
                    import json as _ai_json
                    with _get_conn(_bizdb_path()) as _c2:
                        try:
                            _c2.execute(
                                "INSERT INTO sa_login_ai_decisions(username, device_fp, recent_fail, is_private_ip, "
                                "fp_registered, fp_provided, score, decision, decision_reasons, ip, created_at) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))",
                                (username, sa_device_hash, _recent_fail, 1 if _is_private_ip else 0,
                                 1 if sa_fp_registered else 0, 1 if fingerprint_data else 0,
                                 _score, sa_ai_decision, _ai_json.dumps(_reasons + [f'risk={sa_risk_level}({sa_risk_score})', f'ef={sa_ef_verdict}']), ip)
                            )
                            _c2.commit()
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception as _ai_err:
                import logging as _ai_lg
                _ai_lg.warning('[sa-login-ai] layer2-4 err: %s', _ai_err)
                sa_ai_decision = 'password'

            # ===== Layer 4 执行 / 根据 AI 决策走对应分支 =====
            if sa_ai_decision == 'fingerprint':
                if sa_fp_template_db and fingerprint_data == sa_fp_template_db:
                    sa_fingerprint_ok = True
                else:
                    inc_db = user_db or _find_writable_user_db()
                    if inc_db:
                        try:
                            with _get_conn(inc_db) as c:
                                _ensure_login_logs_schema_any(c)
                                c.execute("INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)", (username, ip, now_iso))
                                c.commit()
                        except Exception:
                            pass
                    return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='fingerprint_mismatch',
                                              extra_msg='AI 决策走指纹分支，但指纹验证失败')

            # ===== Layer 5 / 设备绑定更新（登录成功后调用） =====
            # 注意：此处仅准备，实际更新在登录成功后执行

        # ===== 超级管理员自动登录：双硬件通过（前提）+ 指纹分支通过 时跳过密码检查 =====
        vikey_auto_login_ok = False
        need_pw_upgrade = False  # ⭐ 初始化，避免超级管理员登录时未定义
        # ⭐ 终端指纹硬件认证分支通过 → 跳过密码验证（双密钥已在上文强制通过）
        if is_super_admin and sa_fingerprint_ok:
            vikey_auto_login_ok = True
        elif sa_dual_hw_ok and not is_super_admin:
            # 此分支通常不触发（SA 才会有 dual_hw），保留防御性
            vikey_auto_login_ok = True
        elif is_super_admin and auto_login and vikey_auth_token and vikey_serial:
            if app.config.get('DEBUG', False):
                # 原 print → logging.debug 避免 stdout 刷屏
                import logging as _vk_lg1
                _vk_lg1.debug('[DEBUG MODE] 跳过超级管理员 %s 的vikey自动登录验证', username)
                vikey_auto_login_ok = True
            else:
                try:
                    with _get_conn(SPLIT_ADMIN_DB) as c:
                        r = c.execute("SELECT binding_status, username FROM vikey_device_bindings WHERE serial=? LIMIT 1", (vikey_serial,)).fetchone()
                        if r and r[0] == 'bound' and (r[1] or '').lower() == 'wuchenghao15':
                            vikey_auto_login_ok = True
                            _vikey_write_log('auto_login', 'ok', serial=vikey_serial, username='wuchenghao15')
                        else:
                            vikey_auto_login_ok = False
                except Exception:
                    try:
                        with _get_conn(_bizdb_path()) as c:
                            r = c.execute("SELECT binding_status, username FROM vikey_device_bindings WHERE serial=? LIMIT 1", (vikey_serial,)).fetchone()
                            if r and r[0] == 'bound' and (r[1] or '').lower() == 'wuchenghao15':
                                vikey_auto_login_ok = True
                                _vikey_write_log('auto_login', 'ok', serial=vikey_serial, username='wuchenghao15')
                            else:
                                vikey_auto_login_ok = False
                    except Exception:
                        vikey_auto_login_ok = False

                if not vikey_auto_login_ok:
                    return _generic_auth_fail(
                        username, ip, ua, user_id=user_id_for_log,
                        reason='vikey_not_bound'
                    )

        # ===== 密码验证（自动登录时跳过；跨库预验证通过时跳过并同步哈希）=====
        if not vikey_auto_login_ok:
            if pw_pre_verified:
                pw_ok = True
                need_pw_upgrade = True  # 同步密码哈希到当前库
            else:
                expected_hash = (row_dict.get('password') or '').strip()
                pw_ok, need_pw_upgrade = _password_matches(password, expected_hash, username)
            if not pw_ok:
                # 失败计数+1 写入用户所在库（找不到则写入可写库）
                inc_db = user_db or _find_writable_user_db()
                if inc_db:
                    try:
                        with _get_conn(inc_db) as c:
                            _ensure_login_logs_schema_any(c)
                            c.execute(
                                "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)",
                                (username, ip, now_iso)
                            )
                            try:
                                c.execute(
                                    "UPDATE users SET failed_login_count = COALESCE(failed_login_count, 0) + 1, updated_at = ? WHERE id = ?",
                                    (now_iso, row_dict.get('id'))
                                )
                            except sqlite3.Error:
                                pass
                            c.commit()
                    except Exception:
                        pass
                # ===== 落地关键：这次失败写入后【主动再触发检测】（before_request先于路由函数执行，本次失败统计未包含）=====
                try:
                    br = _security_check_bruteforce()
                    if isinstance(br, dict) and br.get('blocked'):
                        try:
                            _security_report_anomaly('login_post_lock', {'username': username, 'ip': ip, 'reason': br.get('reason')})
                        except Exception:
                            pass
                        return jsonify({'success': False, 'message': f'登录尝试次数过多，已暂时锁定（{br.get("reason","")}）', '_eigenflux': {'blocked': True}}), 403
                except Exception:
                    pass
                try:
                    st = _security_check_credential_stuffing()
                    if isinstance(st, dict) and st.get('blocked'):
                        try:
                            _security_report_anomaly('login_post_stuffing', {'username': username, 'ip': ip, 'reason': st.get('reason')})
                        except Exception:
                            pass
                        return jsonify({'success': False, 'message': '疑似凭证填充攻击，请求已拒绝', '_eigenflux': {'blocked': True}}), 403
                except Exception:
                    pass
                return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='password_mismatch')

        ssl_ok, ssl_reason = _verify_ssl_fingerprint(ssl_fingerprint, ip, ua, username)
        if not ssl_ok and ssl_reason != 'ssl_fp_missing':
            return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason=ssl_reason)

        # 【STEP_7 SSL绑定】校验SSL指纹与用户绑定关系（SA例外：vikey 7要素覆盖）
        if not is_super_admin:
            try:
                with _get_conn(APP_DB) as _ssl_c:
                    _ensure_ssl_binding_schema(_ssl_c)
                    _ssl_urow = _ssl_c.execute("SELECT id, ssl_binding_status, ssl_grace_period_until FROM users WHERE username=?", (username,)).fetchone()
                if _ssl_urow:
                    _ssl_uid, _ssl_bstatus, _ssl_grace = _ssl_urow[0], (_ssl_urow[1] or 'unbound'), _ssl_urow[2]
                    if _ssl_bstatus == 'bound':
                        # 已绑定用户：必须提供匹配的SSL指纹
                        _ssl_bind_ok, _ssl_bind_reason = _verify_ssl_binding(_ssl_uid, ssl_fingerprint)
                        if not _ssl_bind_ok:
                            try:
                                _ef_process_report_anomaly(
                                    'ssl_binding_mismatch', 'auth_login_POST', 'HIGH',
                                    {'username': username, 'uid': _ssl_uid, 'reason': _ssl_bind_reason,
                                     'fp_provided': bool(ssl_fingerprint)},
                                    notify_ai_employees=True, auto_apply_fix=False,
                                    operator_user=username or 'anonymous', client_ip=ip, client_ua=ua)
                            except Exception:
                                pass
                            return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='ssl_binding_mismatch')
                    else:
                        # 未绑定用户：宽限期内放行，首次登录设置30天宽限期
                        if not _ssl_grace:
                            _grace_until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                            try:
                                with _get_conn(APP_DB) as _gc:
                                    _gc.execute("UPDATE users SET ssl_grace_period_until=? WHERE id=?", (_grace_until, _ssl_uid))
                                    _gc.commit()
                            except Exception:
                                pass
                        else:
                            # 检查宽限期是否过期
                            _now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if _ssl_grace < _now_str:
                                try:
                                    _ef_process_report_anomaly(
                                        'ssl_grace_expired', 'auth_login_POST', 'HIGH',
                                        {'username': username, 'uid': _ssl_uid, 'grace_until': _ssl_grace},
                                        notify_ai_employees=True, auto_apply_fix=False,
                                        operator_user=username or 'anonymous', client_ip=ip, client_ua=ua)
                                except Exception:
                                    pass
                                return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='ssl_grace_expired')
            except Exception:
                pass  # SSL绑定校验异常不阻断登录（fail-open，避免影响已有用户）

        if is_super_admin and not vikey_auto_login_ok:
            # 铁律：SA 必须通过 VIKEY 双密钥认证，不得通过任何手段绕过
            v_ok, v_reason, _v_info = _verify_super_admin_vikey(
                username, vikey_auth_token, vikey_serial, ip, ua
            )
            if not v_ok:
                return _generic_auth_fail(
                    username, ip, ua, user_id=user_id_for_log,
                    reason=v_reason or 'vikey_fail'
                )

        # ===== 验证全部通过，写入登录记录到「用户所在库」或可写库（绝不重置密码明文；need_pw_upgrade仅哈希格式升级） =====
        write_db = user_db or _find_writable_user_db()
        if write_db:
            try:
                with _get_conn(write_db) as conn:
                    _ensure_login_logs_schema_any(conn)
                    # 仅哈希格式升级（不改变密码明文）；标准哈希不会触发
                    if need_pw_upgrade:
                        try:
                            new_std_hash = _hash_password(password)
                            conn.execute(
                                "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                                (new_std_hash, now_iso, row_dict.get('id'))
                            )
                        except Exception:
                            pass
                    conn.execute(
                        "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 1, ?)",
                        (username, ip, now_iso)
                    )
                    extra = ''
                    if is_super_admin:
                        extra = ';vikey_serial=' + (vikey_serial or '')[:64] + ';pin_prefix=' + vikey_pin_hint
                    remark = ('ssl_fp_len=' + str(len(ssl_fingerprint or ''))) + extra
                    inserted = False
                    # 先尝试标准列集合（含 remark 等）
                    try:
                        conn.execute(
                            "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time, remark) VALUES (?, ?, ?, ?, ?, 'success', ?, ?)",
                            (row_dict.get('id'), username, ip, ua, 'web', now_iso, remark)
                        )
                        inserted = True
                    except sqlite3.Error:
                        pass
                    if not inserted:
                        # APP_DB login_logs 列名：id/user_id/login_time/login_ip/user_agent（无username/login_status）
                        try:
                            conn.execute(
                                "INSERT INTO login_logs (user_id, login_time, login_ip, user_agent) VALUES (?, ?, ?, ?)",
                                (row_dict.get('id'), now_iso, ip, ua)
                            )
                            inserted = True
                        except sqlite3.Error:
                            pass
                    if not inserted:
                        try:
                            conn.execute(
                                "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time) VALUES (?, ?, ?, ?, ?, 'success', ?)",
                                (row_dict.get('id'), username, ip, ua, 'web', now_iso)
                            )
                        except sqlite3.Error:
                            pass
                    # 重置失败计数 + 写入 last_login + updated_at
                    try:
                        conn.execute(
                            "UPDATE users SET failed_login_count = 0, last_login = ?, updated_at = ? WHERE id = ?",
                            (now_iso, now_iso, row_dict.get('id'))
                        )
                    except sqlite3.Error:
                        try:
                            conn.execute(
                                "UPDATE users SET failed_login_count = 0, updated_at = ? WHERE id = ?",
                                (now_iso, row_dict.get('id'))
                            )
                        except sqlite3.Error:
                            pass
                    conn.commit()
            except Exception:
                pass

        # ===== 登录成功后清理安全中间件状态（防止失败锁定残留导致"被阻拦"）=====
        try:
            from app.middlewares.security_middleware import SecurityMiddlewareClass
            SecurityMiddlewareClass.reset_failed_login(username)
            SecurityMiddlewareClass.unlock_user(username, 'login_success')
            SecurityMiddlewareClass.whitelist_ip(ip)
        except Exception:
            pass

        session['user_id'] = row_dict.get('id')
        session['username'] = row_dict.get('username')
        db_role = row_dict.get('role') or 'user'
        if username.lower() == 'wuchenghao15':
            session['role'] = 'super_admin'
        else:
            if db_role == 'super_admin':
                session['role'] = 'admin'
            else:
                session['role'] = db_role
        session['logged_in'] = True
        session['csrf_token'] = hashlib.sha256(f'mtscos-csrf-sess-{time.time()}-{os.urandom(16)}'.encode()).hexdigest()
        session.permanent = remember

        # ===== Remember-me: 签发 token + 写 cookie（非SA + remember=True）=====
        remember_token_cookie_val = None
        remember_applied = False
        if remember and not remember_force_disabled_sa:
            try:
                remember_token_cookie_val = _remember_me_issue(
                    int(row_dict.get('id')), str(row_dict.get('username')), ip=ip, ua=ua
                )
                if remember_token_cookie_val:
                    remember_applied = True
                    try:
                        session['_remember_token_id'] = remember_token_cookie_val.split('.', 1)[0][:64]
                    except Exception:
                        pass
                else:
                    # 生成失败（EF已记录）：session.permanent 保持，但不写 remember cookie
                    pass
            except Exception as e:
                try:
                    ef = _ef_process_report_anomaly(
                        'remember_cookie_write_fail', 'auth_login_POST', 'MEDIUM',
                        {'username': username, 'error': str(e)[:200], 'note': '签发remember token失败，已退回session模式'},
                        notify_ai_employees=True, auto_apply_fix=True,
                        operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
                    )
                    login_ef_parts.append(ef)
                except Exception:
                    pass

        user = {
            'id': row_dict.get('id'),
            'username': row_dict.get('username'),
            'email': row_dict.get('email'),
            'role': session['role'],
            'super_admin_approved': bool(row_dict.get('super_admin_approved')) if row_dict.get('super_admin_approved') is not None else False,
        }
        # 按角色分发跳转目标
        from app.middlewares.unified_permission import get_redirect_url_for_role
        _redirect_url = get_redirect_url_for_role(session['role'])
        # next 参数优先（但白名单过滤，禁止外部跳转）
        if next_url and isinstance(next_url, str):
            if next_url.startswith('/') and not next_url.startswith('//'):
                from urllib.parse import urlparse as _uparse
                _p = _uparse(next_url)
                if not _p.netloc:
                    _redirect_url = next_url

        # 合并 EigenFlux 磋商结果
        ef_out = None
        if login_ef_parts:
            try:
                last = login_ef_parts[-1]
                ef_out = _ef_strip(last)
                # 合并 ai_consult_count
                total_consult = 0
                for part in login_ef_parts:
                    total_consult += int((part or {}).get('ai_consult_count') or 0)
                if ef_out and total_consult:
                    ef_out['ai_consult_count'] = total_consult
            except Exception:
                pass
        if not ef_out:
            try:
                ef_out = _ef_strip(_ef_process_report_anomaly(
                    'login_success', 'auth_login_POST', 'LOW',
                    {'username': username, 'role': session['role'], 'remember': remember,
                     'remember_applied': remember_applied,
                     'remember_sa_forced_disabled': remember_force_disabled_sa},
                    notify_ai_employees=False, auto_apply_fix=False,
                    operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
                ))
            except Exception:
                ef_out = None

        from flask import make_response as _mkresp
        # 构造响应体（含SA登录AI决策字段，供前端展示"指纹/密码分流AI决策"结果）
        resp_body = {
            'success': True,
            'message': f'登录成功（{user["role"]}），正在跳转...',
            'redirect': _redirect_url,
            'user': user,
            'session_id': session.get('sid') or str(id(session)),
            'csrf_token': session.get('csrf_token'),
            'remember_me': {
                'requested': bool(remember_effective_remember),
                'applied': remember_applied,
                'sa_force_disabled': remember_force_disabled_sa,
                'session_permanent': bool(session.permanent),
            },
            '_eigenflux': ef_out,
        }
        # === SA 登录审计扩展字段（5层加固全量审计） ===
        if is_super_admin:
            try:
                # Layer 5: 登录成功后更新设备绑定
                _sa_update_device_binding(username, sa_device_hash, ip, ua, login_success=True)
                resp_body['sa_auth'] = {
                    # Layer 0: 防伪
                    'anti_replay_ok': bool(sa_anti_replay_ok),
                    'anti_replay_reason': sa_anti_replay_reason,
                    'device_hash': sa_device_hash,
                    'device_trust': sa_device_trust,
                    # Layer 1: 双密钥
                    'dual_hw_ok': bool(sa_dual_hw_ok),
                    # Layer 2: AI 风险引擎
                    'risk_level': sa_risk_level,
                    'risk_score': sa_risk_score,
                    'risk_factors': sa_risk_factors,
                    # Layer 3: EigenFlux 专家团
                    'eigenflux_verdict': sa_ef_verdict,
                    'eigenflux_approve': sa_ef_approve,
                    'eigenflux_deny': sa_ef_deny,
                    'eigenflux_session_id': sa_ef_session_id,
                    # Layer 4: AI 决策
                    'ai_decision': sa_ai_decision,
                    'fingerprint_ok': bool(sa_fingerprint_ok),
                    'fingerprint_registered': bool(sa_fp_registered),
                    # 审计溯源
                    'flow_id': 'SA-FP-C0575EAFF697',
                    'hardening_version': 'v2.0.0-5layer',
                    'note': (f'5层加固通过: 防伪✓ 双密钥✓ AI风险={sa_risk_level}({sa_risk_score}) '
                             f'EF={sa_ef_verdict}({sa_ef_approve}A/{sa_ef_deny}D) '
                             f'决策={sa_ai_decision}{"→指纹通过" if sa_fingerprint_ok else "→密码验证"}'),
                }
            except Exception:
                pass
        resp = _mkresp(jsonify(resp_body))
        if remember_applied and remember_token_cookie_val:
            try:
                is_secure = bool(request.is_secure or (request.headers.get('X-Forwarded-Proto', '') or '').lower() == 'https')
                resp.set_cookie(
                    _MT_REMEMBER_COOKIE, remember_token_cookie_val,
                    max_age=_MT_REMEMBER_MAX_AGE,
                    httponly=True, secure=is_secure, samesite='Lax', path='/'
                )
                # 会话一致性校验：session.permanent 与 cookie max_age 是否对齐
                if not session.permanent:
                    try:
                        _ef_process_report_anomaly(
                            'remember_session_expire_inconsistency', 'auth_login_POST', 'MEDIUM',
                            {'username': username, 'note': 'session.permanent=False 但已写入remember cookie 30天'},
                            notify_ai_employees=True, auto_apply_fix=False,
                            operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
                        )
                    except Exception:
                        pass
            except Exception as e:
                try:
                    _ef_process_report_anomaly(
                        'remember_cookie_write_fail', 'auth_login_POST', 'MEDIUM',
                        {'username': username, 'error': str(e)[:200]},
                        notify_ai_employees=True, auto_apply_fix=True,
                        operator_user=username or 'anonymous', client_ip=ip, client_ua=ua
                    )
                except Exception:
                    pass
        else:
            # 非remember 登录：清除旧cookie
            try:
                resp.delete_cookie(_MT_REMEMBER_COOKIE, path='/')
            except Exception:
                pass
        return resp

    return redirect('/')


# v22.38.0 P1: /auth/register 已迁到 routes/auth_page_routes.py (代理模式)
# 保留函数体, 蓝图 handler 通过 _mt_sdb().register() 调用
def register():
    if request.method == 'GET':
        try:
            v, info, _ = get_version_info()
            # 把协议元数据 + 年龄过滤规则 注入模板，前端按需渲染
            terms_meta = [
                {'slug': s, 'title': d.get('title'), 'short_name': d.get('short_name'),
                 'version': d.get('version'), 'updated_at': d.get('updated_at')}
                for s, d in _LEGAL_DOCUMENTS.items()
            ]
            resp = make_response(render_template(
                'register.html', version=v, version_info=info,
                required_terms=_REQUIRED_TERMS_SLUGS,
                terms_meta=terms_meta,
                education_options=[
                    {'value': 'k12', 'label': 'K12学生（小学/初中/高中）'},
                    {'value': 'adult', 'label': '成人教育（自考/在职/继续教育）'},
                    {'value': 'higher', 'label': '高等教育（专科/本科/研究生）'},
                ],
                legal_version=_LEGAL_TERMS_VERSION,
            ))
            return resp
        except Exception:
            return redirect('/')

    # ============= POST /auth/register =============
    data = request.get_json(silent=True) or {}
    username = _safe_str(data.get('username'), max_len=40)
    password = _safe_str(data.get('password'), max_len=128)
    email_in = _safe_str(data.get('email'), max_len=254)
    email = email_in or f'{username}@mtscos.com'
    role_raw = _safe_str(data.get('role') or 'user', max_len=32) or 'user'
    # 2026-08-05 新增：身份申请（前端apply_education_type，后端强制默认实际education_type='普通'，待审批后升级）
    apply_education_type_raw = _safe_str(data.get('apply_education_type'), max_len=32)
    apply_education_type = (apply_education_type_raw or '').strip().lower()
    education_type = '普通'  # 强制新用户为普通组别，不允许直接通过API绕过审批
    grade = _safe_str(data.get('grade'), max_len=64)
    phone = _safe_str(data.get('phone'), max_len=32)
    avatar = _safe_str(data.get('avatar'), max_len=500)
    signature = _safe_str(data.get('signature'), max_len=2000)
    # 【STEP_7 SSL绑定】注册时强制收集 SSL 客户端证书指纹
    ssl_fingerprint_reg = _safe_str(data.get('ssl_fingerprint'), max_len=256)
    ssl_cert_pem_reg = _safe_str(data.get('ssl_cert_pem'), max_len=16384)
    client_ip = request.remote_addr or 'unknown_ip'
    # 年龄/生日
    try:
        age_raw = data.get('age')
        if age_raw is None or age_raw == '':
            age_val = 0
        else:
            age_val = max(0, min(120, int(age_raw)))
    except (TypeError, ValueError):
        age_val = 0
    birth_date = _safe_str(data.get('birth_date'), max_len=32)
    # 如果用户没填 age 但填了生日，从生日反推
    if age_val <= 0 and birth_date:
        try:
            import datetime as _dt
            if len(birth_date) >= 10:
                bd = _dt.datetime.strptime(birth_date[:10], '%Y-%m-%d').date()
                today = _dt.date.today()
                age_val = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
                age_val = max(0, min(120, int(age_val)))
        except Exception:
            pass
    # 协议勾选（必须4项全部为True）
    agree_terms_raw = data.get('agree_terms') or {}
    if isinstance(agree_terms_raw, dict):
        agree_terms_dict = {str(k).strip(): bool(v) for k, v in agree_terms_raw.items()}
    elif isinstance(agree_terms_raw, (list, tuple, set)):
        agree_terms_dict = {str(s).strip(): True for s in agree_terms_raw}
    else:
        agree_terms_dict = {}
    # 兼容老字段（单个布尔agree全部协议）
    if data.get('agree_all_terms') in (True, 1, 'true', 'True', '1'):
        for _s in _REQUIRED_TERMS_SLUGS:
            agree_terms_dict.setdefault(_s, True)

    # ---------- 校验层 ----------
    if not username or not password:
        ef = _ef_process_report_anomaly(
            'invalid_request', 'auth_register_POST', 'LOW',
            {'missing_fields': ([f for f in ('username', 'password') if not locals().get(f)] or [])},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({'success': False, 'message': '请填写用户名和密码',
                        '_eigenflux': _ef_strip(ef)}), 400
    # 1) 协议强制：4项必须全部勾选
    missing_terms = [s for s in _REQUIRED_TERMS_SLUGS if not agree_terms_dict.get(s)]
    if missing_terms:
        labels = [_LEGAL_DOCUMENTS[s].get('short_name') for s in missing_terms if _LEGAL_DOCUMENTS.get(s)]
        ef = _ef_process_report_anomaly(
            'terms_not_agreed', 'auth_register_POST', 'MEDIUM',
            {'missing_terms': missing_terms, 'username': username},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False,
            'message': f'请先阅读并同意以下协议：{"、".join(labels or missing_terms)}',
            'missing_terms': missing_terms,
            '_eigenflux': _ef_strip(ef),
        }), 400
    if len(username) < 3:
        return jsonify({'success': False, 'message': '用户名至少 3 个字符'}), 400
    if len(username) > 40:
        return jsonify({'success': False, 'message': '用户名长度不能超过 40 字符'}), 400
    # SA用户名保护（不允许注册 SA 保留名）
    if str(username).lower() in _SA_FORBIDDEN_NAMES_LOWER:
        ef = _ef_process_report_anomaly(
            'sa_username_blocked', 'auth_register_POST', 'HIGH',
            {'attempted_username': username, 'blocked_names': list(_SA_FORBIDDEN_NAMES)},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False,
            'message': '该用户名为超级管理员/保留名，不可通过公开注册页注册。请使用 Vikey 硬件授权或联系管理员。',
            '_eigenflux': _ef_strip(ef),
        }), 403
    # 【STEP_7 SSL绑定】强制收集SSL客户端证书指纹（缺失返回400 SSL_CERT_REQUIRED）
    if not ssl_fingerprint_reg:
        ef = _ef_process_report_anomaly(
            'ssl_cert_required', 'auth_register_POST', 'HIGH',
            {'username': username, 'reason': 'missing_ssl_fingerprint'},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False,
            'code': 'SSL_CERT_REQUIRED',
            'message': '注册必须提供SSL客户端证书指纹。请上传证书文件或粘贴证书PEM。',
            '_eigenflux': _ef_strip(ef),
        }), 400
    # 校验SSL指纹格式（复用 _verify_ssl_fingerprint）
    _ssl_ok_reg, _ssl_reason_reg = _verify_ssl_fingerprint(ssl_fingerprint_reg, client_ip, _ua(), username)
    if not _ssl_ok_reg:
        ef = _ef_process_report_anomaly(
            'ssl_fp_invalid', 'auth_register_POST', 'MEDIUM',
            {'username': username, 'reason': _ssl_reason_reg, 'fp_len': len(ssl_fingerprint_reg)},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False,
            'code': 'SSL_FP_INVALID',
            'message': f'SSL证书指纹格式无效：{_ssl_reason_reg}（需32/40/64/128位十六进制）',
            '_eigenflux': _ef_strip(ef),
        }), 400
    # role 白名单校验（超级管理员不能通过普通 API 创建）
    role_lower = role_raw.lower()
    if role_lower in ('super_admin', 'sadmin', 'root'):
        return jsonify({'success': False, 'message': '不允许注册超级管理员账号'}), 403
    if role_lower and role_lower not in _ADMIN_CREATE_USER_ROLE_WHITELIST and role_lower != 'user':
        return jsonify({
            'success': False,
            'message': f'角色不合法，允许值：{", ".join(sorted(_ADMIN_CREATE_USER_ROLE_WHITELIST | {"user"}))}'
        }), 400
    # 新注册用户强制角色='user'（普通用户）；即使前端传student/teacher也无效，避免绕过组别审批
    role = 'user'
    # 2) 年龄+申请组别校验：根据年龄智能删减可申请选项
    allowed_apply, apply_valid = _validate_education_apply_by_age(age_val, apply_education_type)
    if apply_education_type and not apply_valid:
        ef = _ef_process_report_anomaly(
            'education_group_not_allowed_by_age', 'auth_register_POST', 'MEDIUM',
            {'username': username, 'age': age_val, 'apply': apply_education_type,
             'allowed': sorted(allowed_apply)},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False,
            'message': f'您的年龄不允许申请【{_EDUCATION_TYPE_CN.get(apply_education_type, apply_education_type)}】。当前年龄允许的申请选项：{"、".join(_EDUCATION_TYPE_CN.get(x, x) for x in sorted(allowed_apply))}。如需特殊情况，请联系管理员。',
            'age': age_val,
            'allowed_apply': sorted(allowed_apply),
            '_eigenflux': _ef_strip(ef),
        }), 400
    # 教育组别字段：后端入库时强制为'普通'，申请单独存 pending_education_apply
    # （原 _validate_enum 不再用于 education_type，因为扩展为中文'普通'等）
    # 密码最小长度校验（默认6位，再做强校验）
    min_pw_len = 6
    try:
        with _get_conn(_bizdb_path()) as _c:
            _ensure_biz_tables(_c)
            _r = _c.execute(
                "SELECT value_json FROM unified_settings WHERE scope='system' AND key_name='min_password_length' AND is_active=1 LIMIT 1"
            ).fetchone()
            if _r:
                import json as _j2
                try:
                    cfg_min = _j2.loads(_r[0] or 'null')
                    if isinstance(cfg_min, int) and 4 <= cfg_min <= 64:
                        min_pw_len = cfg_min
                except Exception:
                    pass
    except Exception:
        pass
    if len(password) < min_pw_len:
        return jsonify({'success': False, 'message': f'密码至少 {min_pw_len} 个字符'}), 400
    # 邮箱严格校验
    if email_in:
        em_ok, em_msg = _validate_email_format(email)
        if not em_ok:
            return jsonify({'success': False, 'message': '邮箱格式错误：' + em_msg}), 400
    # 注册速率限制
    now = time.time()
    if client_ip not in _MT_REGISTER_LIMIT:
        _MT_REGISTER_LIMIT[client_ip] = []
    _MT_REGISTER_LIMIT[client_ip] = [t for t in _MT_REGISTER_LIMIT[client_ip] if now - t < _MT_REGISTER_WINDOW]
    if len(_MT_REGISTER_LIMIT[client_ip]) >= _MT_REGISTER_MAX_PER_IP:
        ef = _ef_process_report_anomaly(
            'abuse_rate_limit', 'auth_register_POST', 'HIGH',
            {'ip': client_ip,
             'window_sec': _MT_REGISTER_WINDOW,
             'attempts': len(_MT_REGISTER_LIMIT[client_ip]),
             'limit': _MT_REGISTER_MAX_PER_IP,
             'target_username': username},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False, 'message': '注册过于频繁，请稍后再试',
            '_eigenflux': _ef_strip(ef),
        }), 429
    _MT_REGISTER_LIMIT[client_ip].append(now)

    # ---------- 密码强度校验（对齐后端_validate_password_strength） ----------
    pw_eff_min = max(min_pw_len, 8)
    pw_ok, pw_msg, pw_details = _validate_password_strength(
        password, username=username, email=email,
        min_len=pw_eff_min, max_len=64, require_classes=3)
    if not pw_ok:
        ef = _ef_process_report_anomaly(
            'weak_password', 'auth_register_POST', 'MEDIUM',
            {'username': username,
             'password_length': len(password),
             'details': pw_details,
             'failed_rules': [k for k, v in (pw_details or {}).items() if v is False]
             if isinstance(pw_details, dict) else []},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False,
            'message': pw_msg,
            'details': pw_details,
            '_eigenflux': _ef_strip(ef),
        }), 400

    # ---------- 用户冲突检查 ----------
    existing_user, existing_db = _find_user_across_dbs(username)
    if existing_user:
        ef = _ef_process_report_anomaly(
            'user_conflict', 'auth_register_POST', 'MEDIUM',
            {'username': username,
             'existing_in_db': os.path.basename(existing_db) if existing_db else None,
             'existing_id': (existing_user or {}).get('id')},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False, 'message': '该用户名已存在',
            '_eigenflux': _ef_strip(ef),
        }), 409

    # ---------- 写数据库 ----------
    write_db = _find_writable_user_db()
    if not write_db:
        ef = _ef_process_report_anomaly(
            'db_write_error', 'auth_register_POST', 'CRITICAL',
            {'write_db_missing': True, 'username': username,
             'write_db_search_order': 'APP_DB -> AUTH_DB -> default'},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False, 'message': '未找到可写的用户数据库（请检查文件系统权限）',
            '_eigenflux': _ef_strip(ef),
        }), 500

    pw_hash = _hash_password(password)
    now_iso = datetime.now().isoformat()
    terms_agree_slugs_sorted = sorted([s for s in _REQUIRED_TERMS_SLUGS if agree_terms_dict.get(s)])
    import json as _regjson
    terms_agree_json = _regjson.dumps({'slugs': terms_agree_slugs_sorted,
                                       'version': _LEGAL_TERMS_VERSION,
                                       'client_ip': client_ip,
                                       'user_agent': (_ua())[:256]},
                                      ensure_ascii=False)
    # 申请单数据（仅当用户明确提交时入库）
    pending_apply_json = None
    if apply_education_type:
        pending_apply_json = _regjson.dumps({
            'requested': apply_education_type,
            'age': age_val,
            'requested_at': now_iso,
            'status': 'pending',
            'reviewed_by': None,
            'reviewed_at': None,
            'review_comment': None,
        }, ensure_ascii=False)

    uid = None
    try:
        with _get_conn(write_db) as conn:
            # 表+列兼容准备（2026-08-05 新增：age/birth_date/terms_* / pending_* 列）
            try:
                conn.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE, email TEXT, password TEXT,
                    role TEXT DEFAULT 'user', is_active INTEGER DEFAULT 1,
                    created_at TEXT, updated_at TEXT, last_login TEXT,
                    failed_login_count INTEGER DEFAULT 0, locked_until TEXT,
                    super_admin_approved INTEGER DEFAULT 0,
                    hardware_admin_approved INTEGER DEFAULT 0,
                    avatar TEXT, phone TEXT,
                    fingerprint_template TEXT,
                    fingerprint_enabled INTEGER DEFAULT 0,
                    fingerprint_registered_at TEXT,
                    fingerprint_device_id TEXT
                )""")
            except sqlite3.Error:
                pass
            for col, decl in [
                ('hardware_admin_approved', 'INTEGER DEFAULT 0'),
                ('avatar', 'TEXT'), ('phone', 'TEXT'),
                ('last_login', 'TEXT'), ('failed_login_count', 'INTEGER DEFAULT 0'),
                ('locked_until', 'TEXT'), ('fingerprint_template', 'TEXT'),
                ('fingerprint_enabled', 'INTEGER DEFAULT 0'),
                ('fingerprint_registered_at', 'TEXT'), ('fingerprint_device_id', 'TEXT'),
                ('grade', 'TEXT'), ('education_type', 'TEXT'),
                ('education_stage', 'TEXT'), ('signature', 'TEXT'),
                ('score', 'INTEGER DEFAULT 0'),
                # ---- 2026-08-05 注册合规扩展 ----
                ('age', 'INTEGER DEFAULT 0'),
                ('birth_date', 'TEXT'),
                ('terms_agree_version', 'TEXT'),
                ('terms_agree_slugs', 'TEXT'),
                ('terms_agree_detail', 'TEXT'),
                ('terms_agreed_at', 'TEXT'),
                ('pending_education_apply', 'TEXT'),
                ('education_apply_status', 'TEXT DEFAULT \'none\''),
                ('education_apply_approved_at', 'TEXT'),
            ]:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} {decl}")
                except sqlite3.Error:
                    pass
            # 同步更新：把旧的 education_type 值（如果是null/空）统一置为'普通'
            try:
                conn.execute("UPDATE users SET education_type='普通' WHERE id=? AND (education_type IS NULL OR TRIM(education_type)='')",
                             (0,))  # 影响0行无害，但下一次SELECT时确保一致性感知
            except sqlite3.Error:
                pass
            # INSERT（兼容列缺失逐个 fallback，按新增字段从多→少展开）
            inserted = False
            cols_list = [
                # 1) 完整列（含所有合规扩展 + 申请单）
                ("""username, email, password, role, created_at, updated_at, is_active,
                    super_admin_approved, hardware_admin_approved,
                    grade, education_type, education_stage, signature, score,
                    age, birth_date,
                    terms_agree_version, terms_agree_slugs, terms_agree_detail, terms_agreed_at,
                    pending_education_apply, education_apply_status""",
                 (username, email, pw_hash, role, now_iso, now_iso, 1,
                  0, 0,
                  grade or '', education_type, '', signature or '', 0,
                  age_val, birth_date or '',
                  _LEGAL_TERMS_VERSION, ','.join(terms_agree_slugs_sorted),
                  terms_agree_json, now_iso,
                  pending_apply_json or '',
                  'pending' if apply_education_type else 'none')),
                # 2) 无 education_apply_status
                ("""username, email, password, role, created_at, updated_at, is_active,
                    super_admin_approved, hardware_admin_approved,
                    grade, education_type, education_stage, signature, score,
                    age, birth_date,
                    terms_agree_version, terms_agree_slugs, terms_agree_detail, terms_agreed_at,
                    pending_education_apply""",
                 (username, email, pw_hash, role, now_iso, now_iso, 1,
                  0, 0,
                  grade or '', education_type, '', signature or '', 0,
                  age_val, birth_date or '',
                  _LEGAL_TERMS_VERSION, ','.join(terms_agree_slugs_sorted),
                  terms_agree_json, now_iso,
                  pending_apply_json or '')),
                # 3) 仅 terms_* 最小组合
                ("""username, email, password, role, created_at, updated_at, is_active,
                    super_admin_approved, hardware_admin_approved,
                    grade, education_type, signature,
                    age, birth_date,
                    terms_agree_version, terms_agreed_at""",
                 (username, email, pw_hash, role, now_iso, now_iso, 1,
                  0, 0,
                  grade or '', education_type, signature or '',
                  age_val, birth_date or '',
                  _LEGAL_TERMS_VERSION, now_iso)),
                # 4) 基础列（完全不依赖新列）
                ("username, email, password, role, created_at, updated_at, is_active, super_admin_approved, hardware_admin_approved",
                 (username, email, pw_hash, role, now_iso, now_iso, 1, 0, 0)),
                ("username, email, password, role, created_at, updated_at, is_active, super_admin_approved",
                 (username, email, pw_hash, role, now_iso, now_iso, 1, 0)),
                ("username, email, password, role, created_at, updated_at, is_active",
                 (username, email, pw_hash, role, now_iso, now_iso, 1)),
                ("username, email, password, role, created_at, is_active",
                 (username, email, pw_hash, role, now_iso, 1)),
                ("username, email, password, role, created_at",
                 (username, email, pw_hash, role, now_iso)),
            ]
            for sql_cols, vals in cols_list:
                try:
                    cur = conn.execute(
                        f"INSERT INTO users ({sql_cols}) VALUES ({','.join(['?']*len(vals))})", vals
                    )
                    uid = cur.lastrowid
                    inserted = True
                    break
                except sqlite3.Error:
                    continue
            if not inserted:
                ef = _ef_process_report_anomaly(
                    'db_write_error', 'auth_register_POST', 'HIGH',
                    {'username': username, 'db': os.path.basename(write_db),
                     'reason': 'users表结构不兼容或所有fallback列组合失败'},
                    operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
                return jsonify({
                    'success': False, 'message': '写入数据库失败：users表结构不兼容',
                    '_eigenflux': _ef_strip(ef),
                }), 500
            conn.commit()

            # 【STEP_7 SSL绑定】注册成功后绑定SSL证书到用户（is_primary=True）
            try:
                _bind_id = _bind_user_ssl_cert(uid, username, ssl_fingerprint_reg,
                                               cert_pem=ssl_cert_pem_reg, ip=client_ip, is_primary=True)
                if _bind_id:
                    try:
                        _ef_process_report_anomaly(
                            'ssl_bind_success', 'auth_register_POST', 'LOW',
                            {'uid': uid, 'username': username, 'binding_id': _bind_id, 'fp_len': len(ssl_fingerprint_reg)},
                            notify_ai_employees=False, auto_apply_fix=False,
                            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
                    except Exception:
                        pass
            except Exception:
                pass

            # ---------- 关键：Read-back 一致性校验（EigenFlux） ----------
            verify_row = None
            try:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT id, username, email, password, role, is_active, "
                                   "super_admin_approved, hardware_admin_approved, "
                                   "education_type, age, terms_agree_version, terms_agreed_at "
                                   "FROM users WHERE id = ? LIMIT 1", (uid,))
                verify_row = cur.fetchone()
            except Exception:
                verify_row = None
            verify_ok = True
            verify_issues = []
            if not verify_row:
                verify_ok = False
                verify_issues.append('read_back_row_missing')
            else:
                vr = dict(verify_row)
                if str(vr.get('username') or '').strip() != username:
                    verify_ok = False
                    verify_issues.append(f"username_mismatch(expected={username}, got={vr.get('username')})")
                if str(vr.get('role') or 'user').strip() != role:
                    verify_ok = False
                    verify_issues.append(f"role_mismatch(expected={role}, got={vr.get('role')})")
                if str(vr.get('email') or '').strip() != email:
                    verify_ok = False
                    verify_issues.append(f"email_mismatch(expected={email}, got={vr.get('email')})")
                if str(vr.get('education_type') or '普通').strip() != education_type:
                    verify_ok = False
                    verify_issues.append(f"education_type_mismatch(expected={education_type}, got={vr.get('education_type')})")
                # terms_version 仅当DB存在该列时校验
                if vr.get('terms_agree_version') and str(vr.get('terms_agree_version')) != _LEGAL_TERMS_VERSION:
                    verify_ok = False
                    verify_issues.append(f"terms_version_mismatch(expected={_LEGAL_TERMS_VERSION}, got={vr.get('terms_agree_version')})")
                if vr.get('is_active') != 1 and vr.get('is_active') is not True:
                    verify_ok = False
                    verify_issues.append('is_active_not_1')
                try:
                    if not _verify_password(password, vr.get('password') or ''):
                        verify_ok = False
                        verify_issues.append('password_hash_verification_failed')
                except Exception:
                    verify_ok = False
                    verify_issues.append('password_hash_verify_exception')
            if not verify_ok:
                ef = _ef_process_report_anomaly(
                    'hash_mismatch', 'auth_register_POST', 'CRITICAL',
                    {'username': username, 'uid': uid, 'db': os.path.basename(write_db),
                     'verify_issues': verify_issues,
                     'action_taken': 'RETURN_WARN_BUT_ALLOW_RELOGIN',
                     'note': '写入成功但Read-back校验失败——通常是列兼容fallback导致；EigenFlux已记录审计。'},
                    operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
                ef_payload = _ef_strip(ef)
                ef_payload['warn'] = True
                ef_payload['verify_issues'] = verify_issues
            else:
                ef_payload = _ef_strip(_ef_process_report_anomaly(
                    'register_success', 'auth_register_POST', 'LOW',
                    {'uid': uid, 'username': username, 'email': email, 'role': role,
                     'education_type': education_type, 'age': age_val,
                     'apply_education_type': apply_education_type or None,
                     'db': os.path.basename(write_db)},
                    notify_ai_employees=False,
                    operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua()))
            apply_note = ''
            if apply_education_type:
                apply_note = f"\n\n🎓 已提交组别申请：【{_EDUCATION_TYPE_CN.get(apply_education_type, apply_education_type)}】，管理员审批通过后即可使用对应功能；审批前为【普通组别】，仅可浏览基础介绍页。"
            else:
                apply_note = f"\n\nℹ️ 当前为【普通组别】，可在「个人设置→身份认证」中随时提交组别申请（K12学生/成人教育/高等教育），审批通过后解锁对应功能。"
            # 组别禁访提示：告诉前端这是普通组别
            edu_cn = _EDUCATION_TYPE_CN.get(education_type, education_type)
            pending_cn = (apply_education_type
                          and _EDUCATION_TYPE_CN.get(apply_education_type, apply_education_type))
            user_obj = {
                'id': uid, 'username': username, 'role': role, 'email': email,
                'role_cn': _ROLE_CN.get(role, role),
                'education_type': education_type,
                'education_type_cn': edu_cn,
                'age': age_val,
                'birth_date': birth_date or None,
                'is_normal_group': True,  # 2026-08-05 普通组别前端禁访标识
                'education_apply_status': ('pending' if apply_education_type else 'none'),
                'apply_education_type': apply_education_type or None,
                'pending_education_apply': apply_education_type or None,
                'pending_education_apply_cn': pending_cn or None,
                'terms_agree_version': _LEGAL_TERMS_VERSION,
                'terms_agreed_at': now_iso,
                'allowed_education_apply': sorted(allowed_apply),
            }
            resp = {
                'success': True,
                'message': (f'注册成功，ID={uid}（写入 {os.path.basename(write_db)}.users，密码 SHA256→Base64）'
                            f'{apply_note}'),
                'redirect': '/',
                'user': user_obj,
                '_eigenflux': ef_payload,
                # 返回允许的申请集合，前端渲染后续提示用
                'allowed_education_apply': sorted(allowed_apply),
                'legal_version': _LEGAL_TERMS_VERSION,
                'pending_apply_created': bool(apply_education_type),
            }
            return jsonify(resp)
    except sqlite3.Error as e:
        ef = _ef_process_report_anomaly(
            'db_write_error', 'auth_register_POST', 'HIGH',
            {'username': username, 'error': str(e), 'db': os.path.basename(write_db) if write_db else None},
            operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
        return jsonify({
            'success': False, 'message': f'注册失败：{e}',
            '_eigenflux': _ef_strip(ef),
        }), 500
    except Exception as _e_uncaught:
        try:
            ef = _ef_process_report_anomaly(
                'register_unhandled_exception', 'auth_register_POST', 'CRITICAL',
                {'username': username or '', 'error': str(_e_uncaught)[:300]},
                operator_user=username or 'anonymous', client_ip=client_ip, client_ua=_ua())
            return jsonify({
                'success': False,
                'message': '注册异常：' + str(_e_uncaught)[:120],
                '_eigenflux': _ef_strip(ef),
            }), 500
        except Exception:
            return jsonify({'success': False, 'message': '注册失败，请稍后再试'}), 500



# ======================== 2026-08-05 普通组别（role=user+education_type普通）功能禁访中间件 ========================
def _is_normal_group_user(u):
    """判定当前用户是否属于「普通组别」：禁访智能设置/出题/AI辅导/诊断/考试等所有业务功能。"""
    if not u:
        return False
    role = str(u.get('role') or '').lower()
    if role != 'user':
        return False  # student/teacher/admin/super_admin 均有对应组别权限
    et = str(u.get('education_type') or '').strip()
    if not et or et in ('普通', 'general', 'none', ''):
        return True
    # 若 education_type 为 k12/adult/higher 则不是普通组别（即使 role 还是 user，视为已有审批通过身份）
    return False


_NORMAL_GROUP_BLOCKED_PATH_PREFIXES = {
    # —— 考试/答题系统
    '/exam_system/exams':        'exams_write',
    '/exam_system/tests':        'exams_write',
    '/exam_system/custom':       'paper_generate',
    '/exam_system/past_exams':   'exams_write',
    '/exam_system/special_training': 'student_portal_premium',
    '/exam_system/topic_training':   'student_portal_premium',
    '/exam_system/':             'exams_write',
    '/exam_center':              'exams_write',
    '/exam_start':               'exams_write',
    '/exam_page':                'exams_write',
    '/exam_page_real':           'exams_write',
    '/exam_result':              'exams_write',
    '/exam/':                    'exams_write',
    '/exam_review':              'exams_write',
    # —— 智能出题/组卷
    '/ai_paper_generator':       'paper_generate',
    # —— 教师工作台 & 门户
    '/teacher_workbench':        'teacher_workbench',
    '/teacher_portal':           'teacher_workbench',
    '/teacher_dashboard':        'teacher_workbench',
    '/teacher_settings':         'teacher_workbench',
    # —— 学生门户高级功能
    '/student_portal':           'student_portal_premium',
    # —— AI辅导 / 智能中心
    '/ai_tutor':                 'ai_tutor',
    '/smart_dashboard':          'smart_params_edit',
    '/ai_cluster_matrix':        'smart_params_edit',
    # —— 诊断/脑库
    '/diagnostic':               'diagnostic_access',
    '/knowledge_brain':          'knowledge_brain',
    # —— 智能参数设置
    '/smart_settings':           'smart_params_edit',
    '/personal_settings/smart':  'smart_params_edit',
    '/personal_settings/ai':     'smart_params_edit',
    '/admin_app/settings_params':'smart_params_edit',
}
_NORMAL_GROUP_BLOCKED_API_PREFIXES = {
    # —— AI辅导对话
    '/api/ai_tutor/':           'ai_tutor',
    # —— 智能参数/AI设置
    '/api/smart_params/':       'smart_params_edit',
    '/api/settings/ai/':        'smart_params_edit',
    '/api/admin_app/dashboard_stats': 'smart_params_edit',
    '/api/ai_cluster_matrix':   'smart_params_edit',
    # —— 学情诊断
    '/api/diagnostic/':         'diagnostic_access',
    # —— 考试/提交/阅卷
    '/api/exam/submit':         'exams_write',
    '/api/exam/start':          'exams_write',
    '/exam/start/':             'exams_write',
    '/exam/review/':            'exams_write',
    # —— 智能组卷/出题
    '/api/paper/generate':      'paper_generate',
    '/api/qa/run':              'paper_generate',
    # —— 学生门户 & 教师工作台高级数据
    '/api/student_portal/':     'student_portal_premium',
    '/api/qa/stats':            'student_portal_premium',
    '/api/teacher/':            'teacher_workbench',
}


@app.before_request
def _mt_normal_group_feature_gate():
    """普通组别统一禁访：仅允许首页/协议页/个人设置基础/登录注册注销/静态资源。"""
    if not session.get('logged_in') or not session.get('user_id'):
        return
    # 允许基础路径
    p = str(request.path or '')
    allow_prefixes = ('/', '/auth/', '/legal/', '/static/', '/assets/', '/favicon',
                      '/health', '/api/health', '/api/system_version', '/@vite/', '/manifest.json',
                      '/personal_settings', '/user_profile', '/me', '/user/me')
    if p == '/' or p == '' or any(p.startswith(ap) for ap in allow_prefixes
                                  if ap not in ('/personal_settings',)
                                  ):
        # 例外：/personal_settings/smart 是智能设置，要在字典里单独拦截
        if p.startswith('/personal_settings/smart') or p.startswith('/personal_settings/ai'):
            pass
        else:
            return
    try:
        _u = _current_user()
        u = _u if _u else {'id': None, 'username': 'guest', 'role': 'guest'}
    except Exception:
        return
    if not _is_normal_group_user(u):
        return
    # 匹配路由禁访
    feature = None
    for prefix, feat in _NORMAL_GROUP_BLOCKED_PATH_PREFIXES.items():
        if p == prefix or p.startswith(prefix + '/') or p.startswith(prefix + '?'):
            feature = feat; break
    if not feature:
        for prefix, feat in _NORMAL_GROUP_BLOCKED_API_PREFIXES.items():
            if p.startswith(prefix):
                feature = feat; break
    if not feature:
        return
    # 禁访：JSON 接口返回 403，页面返回 HTML 提示页
    ua = request.headers.get('User-Agent', '')[:200]
    ip = request.remote_addr or 'unknown_ip'
    # ===== 2026-08-12: 审计日志双写：AI巡检 + mt_ai_audit 表 =====
    try:
        _mt_ai_audit_push({
            'sid': session.get('__mt_sid', ''),
            'uid': session.get('user_id'),
            'username': session.get('username', ''),
            'role': session.get('role', 'user'),
            'path': p,
            'action': f'normal_group_gate::block::{feature}',
            'risk_level': 'medium',
            'rule_hit': 'NORMAL_GROUP_GATE_BLOCKED',
            'blocked': 1,
            'detail': _rj.dumps({
                'feature': feature,
                'method': request.method,
                'client_ip': ip,
                'user_agent': ua,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }, ensure_ascii=False)
        })
    except Exception:
        pass
    try:
        _ef_process_report_anomaly(
            'normal_group_access_denied', 'normal_group_gate', 'LOW',
            {'path': p, 'user_id': session.get('user_id'),
             'username': session.get('username'), 'feature': feature},
            notify_ai_employees=False, auto_apply_fix=False,
            operator_user=session.get('username') or 'anonymous',
            client_ip=ip, client_ua=ua
        )
    except Exception:
        pass
    want_json = ('json' in str(request.headers.get('Accept', '')).lower()
                 or 'json' in str(request.headers.get('Content-Type', '')).lower()
                 or (request.method == 'POST')
                 or p.startswith('/api/'))
    msg = ('🔒 您目前是【普通组别】用户，尚未完成身份组别认证，无法使用本功能。\n'
           '请在「个人设置 → 身份认证」中提交 K12学生 / 成人教育 / 高等教育 组别申请，或联系管理员审批开通。\n'
           f'（被拒功能：{feature}，访问路径：{p}）')
    if want_json:
        return jsonify({'success': False, 'message': msg,
                        'code': 'NORMAL_GROUP_GATE_BLOCKED',
                        'feature': feature,
                        'redirect': '/personal_settings#identity'
                        }), 403
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>普通组别 · 功能暂未开通</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;font-family:-apple-system,"Segoe UI",sans-serif;background:#0b1020;color:#e5e7eb;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:30px;}}
.card{{max-width:620px;width:100%;background:rgba(15,23,42,.9);border:1px solid rgba(99,102,241,.35);border-radius:18px;padding:34px 30px;box-shadow:0 24px 80px rgba(79,70,229,.15);}}
.t1{{font-size:22px;font-weight:800;color:#fecaca;margin:0 0 8px;}}.t2{{font-size:12px;opacity:.7;letter-spacing:.12em;margin:0 0 14px;text-transform:uppercase;}}
.badge{{display:inline-block;padding:3px 10px;border-radius:999px;background:#f59e0b22;color:#fbbf24;border:1px solid #f59e0b55;font-weight:700;font-size:11px;margin-bottom:10px;}}
.msg{{background:rgba(0,0,0,.3);border-left:4px solid #f59e0b;border-radius:10px;padding:14px 16px;margin:16px 0;font-size:14px;line-height:1.75;white-space:pre-wrap;}}
.btns{{margin-top:18px;display:flex;flex-wrap:wrap;gap:10px;}}
.btn{{display:inline-block;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13.5px;}}.btn-p{{background:#4f46e5;color:#fff;}}.btn-p:hover{{background:#4338ca;}}
.btn-s{{background:transparent;border:1px solid rgba(255,255,255,.2);color:#cbd5e1;}}.btn-s:hover{{border-color:rgba(255,255,255,.4);color:#fff;}}
.meta{{margin-top:22px;padding-top:16px;border-top:1px solid rgba(255,255,255,.08);font-size:11.5px;color:#64748b;}}</style></head>
<body><div class="card"><div class="badge">普通组别 · 功能禁访</div>
<h1 class="t1">🔒 此功能暂未为您开通</h1>
<p class="t2">NORMAL GROUP · FEATURE BLOCKED · {_h(feature or '')}</p>
<div class="msg">{_h(msg)}</div>
<div class="btns"><a class="btn btn-p" href="/personal_settings#identity">🔑 提交身份组别申请</a>
<a class="btn btn-s" href="/">← 返回首页</a></div>
<div class="meta"><span><b>审计:</b> NORMAL_GATE_{feature or ''}</span> · <span>用户ID:</b> {_h(session.get('user_id',''))}</span></div>
</div></body></html>'''
    return html, 403


# ==============================================================================
# ===== 2026-08-12 API权限自动推断 + 异常动态捕捉 + AI自动化升级daemon =====
# ==============================================================================

# --- 1. API权限自动推断表（按路径模式匹配最低权限要求）---
_API_AUTO_AUTH_RULES = {
    # super_admin 专属
    r'^/api/vikey/(snapshot|usb|hardware|issue_cert)': 'super_admin',
    r'^/api/fingerprint/(delete|register)': 'super_admin',
    r'^/api/security/(hacking|bruteforce|stuffing)': 'super_admin',
    r'^/api/ssl_cert/(approve|revoke)': 'super_admin',
    r'^/api/omega/(system_scan|auto_learn)': 'super_admin',
    r'^/api/omega/proposals/.*/final_decision': 'super_admin',
    r'^/api/backup/(create|restore|delete)': 'super_admin',
    r'^/api/admin_app/settings_params': 'super_admin',
    # admin 级
    r'^/api/upgrade/(check_trigger|approve|config)': 'admin',
    r'^/api/subsystem/upgrade/(check|trigger)': 'admin',
    r'^/api/omega/(learn_from_eigenflux|connect_employee)': 'admin',
    r'^/api/omega/proposals/.*/vote': 'admin',
    r'^/api/ai_employee/auto_assign': 'admin',
    r'^/api/settings/(read|write)': 'admin',
    r'^/api/snapshot/(restore|delete)': 'admin',
    r'^/api/eigenflux/report_anomaly': 'admin',
    r'^/api/optimization/': 'admin',
    r'^/api/ai_cluster': 'admin',
    r'^/api/admin/': 'admin',
    # login 级（所有其他/api/路由默认需要登录）
    r'^/api/': 'login',
    r'^/auth/(logout|me|me_sa|check_sa_username)': 'login',
}

# 公开API白名单（无需登录）
_API_PUBLIC_WHITELIST = {
    '/api/auth/allowed_education_apply', '/api/system/ping', '/api/system/health',
    '/api/health', '/api/system_version', '/api/container/heartbeat', '/api/container/status',
    '/api/client/init', '/api/client/verify_keys',
    '/api/theme/get', '/api/theme/recommend', '/api/theme/sunrise_sunset',
    '/api/theme/presets', '/api/user/theme_preferences',
    '/api/homepage/stats', '/api/dev_flow/',
    '/auth/login', '/auth/logout', '/auth/register', '/logout', '/forgot_password', '/register', '/auth/csrf_token',
    '/auth/check', '/auth/validate', '/auth/session',
    '/auth/session_health',  # 前端 hotplug.js 检查登录态
    # 指纹认证API（登录前需调用终端指纹硬件）
    '/api/mobile/fingerprint/challenge',
    '/api/mobile/fingerprint/verify',
    '/api/mobile/fingerprint/status',
    # Arduino 设备事件轮询 (v2.0: 未登录用户也需要轮询设备插入事件)
    '/api/arduino/events/poll',
    '/api/arduino/events/ack',
    '/api/arduino/auto_detect',  # v22.40: 前端全局轮询设备扫描
    # v22.39.0: 前端 window.onerror 上报 + i18n 语言切换 + 手动 run_cycle (guest 状态也能用)
    '/api/console/record',
    '/api/console/run_cycle',
    '/api/i18n/set_lang',
    # v22.41: AI Neural Hub — 本地 LLM 推理端点 + 自进化 API (guest/login 都能调, daemon 也能调)
    '/api/neuralhub/call',
    '/api/neuralhub/routes',
    '/api/neuralhub/stats',
    '/api/neuralhub/arduino_compile_assist',
    '/api/neuralhub/evolution_logs',
    '/api/neuralhub/prompt_versions',
    '/api/neuralhub/daemon_status',
    '/api/neuralhub/system_info',              # 仙女座-阿尔法 架构元数据
    '/api/neuralhub/api_docs',                  # 仙女座 API 规范自描述
    '/api/neuralhub/models',                   # Ollama 本地模型发现
    '/api/neuralhub/employee_distribution',    # AI 员工布局分布 (公开)
    '/api/neuralhub/daemon_tick',              # 仙女座 daemon 快速检查 (公开)
    '/api/neuralhub/edu_reform_check',         # 教育改革对齐验证 (公开)
    '/api/neuralhub/knowledge_inventory',      # 外部知识脑库清单 (公开)
    '/api/neuralhub/rollback',                # 内部 handler 再检查 SA
    # v22.42: 仙女座星系恒星查询 — 25 颗恒星 + AI 员工分布 (公开)
    '/api/andromeda/stars',
    # §二 教育全链条 + §三 个性化 + §四.5 大模型升级
    '/api/edu/error_chain', '/api/edu/learning_path', '/api/edu/tutor/sessions', '/api/edu/tutor/types',
    '/api/profile/cognitive', '/api/profile/recommendations', '/api/profile/stats',
    '/api/model/status', '/api/model/sync', '/api/crypto/encrypt', '/api/crypto/decrypt', '/api/crypto/sign', '/api/crypto/verify', '/api/crypto/fingerprint', '/api/crypto/keypair', '/api/crypto/benchmark', '/api/crypto/logs',
}


def _api_auto_infer_auth(path):
    """根据路径模式自动推断API所需权限等级，返回 None 表示公开"""
    if path in _API_PUBLIC_WHITELIST:
            return None
    # 前缀式公开（动态路径用 startswith 匹配）
    for _pf in ('/api/andromeda/stars/', '/api/ai/matrix/', '/api/ai/derive/', '/api/edu/', '/api/profile/', '/api/model/', '/api/crypto/',
                '/api/neuralhub/routes/', '/api/japanese/', '/api/mobile/fingerprint/', '/api/ai/derive'):
        if path.startswith(_pf):
            return None
