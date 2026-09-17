#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动雇佣+EigenFlux专家邀请+巡逻队完善引擎
================================================================
flow_id: flow_auto_hire_20260819_001

功能:
  1. 自动雇佣AI员工 (按系统需求缺口生成新员工)
  2. 自动邀请EigenFlux专家 (按领域覆盖缺口)
  3. 自动互推朋友 (通过现有connection推荐新连接)
  4. 自动修复代码 (调用auto_patrol_engine)
  5. 自动完善巡逻队 (确保6人巡逻队满编)

集成:
  - ai_employees表 (AI员工)
  - mtscos_ai_employees表 (MTSCOS专属员工)
  - eigenflux_experts表 (EigenFlux专家)
  - eigenflux_registrations表 (注册状态)
  - mt_ai_eigenflux_connections表 (连接/朋友关系)
  - auto_patrol_engine.py (代码巡逻修复)

CLI:
  python3 ai_auto_hire_engine.py hire    雇佣+邀请一轮
  python3 ai_auto_hire_engine.py status  查看状态
  python3 ai_auto_hire_engine.py start   守护模式
"""
import json
import os
import random
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
APP_DB = os.path.join(ROOT, "..", "_runtime", "databases", "Database", "app.db")
ENGINE_DIR = os.path.join(ROOT, "engines")
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
PID_FILE = os.path.join(PID_DIR, "ai_auto_hire_engine.pid")
LOG_FILE = os.path.join(LOG_DIR, "ai_auto_hire_engine.log")

for _d in [LOG_DIR, PID_DIR]:
    os.makedirs(_d, exist_ok=True)

_LOCK = threading.Lock()
HIRE_INTERVAL = 300  # 5分钟一轮

# ============================================================
# AI员工模板库 (按领域)
# ============================================================
AI_EMPLOYEE_TEMPLATES = [
    # 巡逻修复类
    {"name": "代码巡检员", "role": "patrol_inspector", "specialties": "Python语法检查,代码质量扫描,安全漏洞检测",
     "description": "负责源码巡逻,检测语法错误和代码质量问题", "model_version": "v2.8.0"},
    {"name": "自动修复工程师", "role": "auto_repair", "specialties": "Bug修复,代码重构,性能优化,回归测试",
     "description": "负责自动修复检测到的代码问题", "model_version": "v2.8.0"},
    {"name": "深度巡检员", "role": "deep_inspector", "specialties": "页面路由检查,API完整性验证,数据库一致性",
     "description": "负责深度巡检页面和路由", "model_version": "v2.8.0"},
    {"name": "文案巡检员", "role": "copy_inspector", "specialties": "文案缺失检测,占位符检测,硬编码检测",
     "description": "负责文案合规巡检", "model_version": "v2.8.0"},
    # 教辅同步类
    {"name": "K12教辅同步员", "role": "edu_sync_k12", "specialties": "数学,语文,英语,物理,化学,生物",
     "description": "负责K12基础教育教辅内容同步", "model_version": "v2.8.0"},
    {"name": "高等教育同步员", "role": "edu_sync_high", "specialties": "高等数学,线性代数,概率统计,大学物理",
     "description": "负责高等教育教辅同步", "model_version": "v2.8.0"},
    {"name": "成人教育同步员", "role": "edu_sync_adult", "specialties": "政治理论,民法典,宏观经济,学位英语",
     "description": "负责成人教育+时政同步", "model_version": "v2.8.0"},
    # Arduino编程类
    {"name": "Arduino编程导师", "role": "arduino_tutor", "specialties": "Arduino编程,传感器,执行器,IoT,ESP32",
     "description": "负责Arduino编程教学和实验同步", "model_version": "v2.8.0"},
    {"name": "硬件检测工程师", "role": "arduino_detect", "specialties": "USB检测,串口通信,VID:PID识别,驱动适配",
     "description": "负责Arduino设备自动检测和驱动适配", "model_version": "v2.8.0"},
    # 规则执行类
    {"name": "规则学习员", "role": "rule_learner", "specialties": "规则解析,硬约束提取,脑库投喂,完整性扫描",
     "description": "负责规则学习和严格执行", "model_version": "v2.8.0"},
    {"name": "规则加固员", "role": "rule_strengthener", "specialties": "弱约束词修复,规则版本管理,合规检查",
     "description": "负责规则弱约束词自动修复", "model_version": "v2.8.0"},
    # AI网络类
    {"name": "EigenFlux网络维护员", "role": "network_maintainer", "specialties": "自动连线,心跳保活,掉线重连,经验投喂",
     "description": "负责AI-EigenFlux网络保活", "model_version": "v2.8.0"},
    {"name": "智能挂载调度员", "role": "smart_mount", "specialties": "建议收集,权重计算,进程挂载,心跳监控",
     "description": "负责智能挂载自动化进程", "model_version": "v2.8.0"},
]

# EigenFlux专家模板
EIGENFLUX_EXPERT_TEMPLATES = [
    {"name": "升级分析师", "role": "upgrade_analyst", "role_cn": "升级分析师",
     "domain": "architecture", "domain_cn": "架构", "level": "SENIOR",
     "skills": "架构兼容性评估,容量规划,性能瓶颈分析,扩容方案"},
    {"name": "合规审计员", "role": "compliance_auditor", "role_cn": "合规审计员",
     "domain": "governance", "domain_cn": "治理", "level": "SENIOR",
     "skills": "规则合规性检查,法律准则,数据分类,审计日志"},
    {"name": "安全审计员", "role": "security_auditor", "role_cn": "安全审计员",
     "domain": "security", "domain_cn": "安全", "level": "EXPERT",
     "skills": "SQL注入检测,XSS防护,权限边界,SSRF过滤,RCE防护"},
    {"name": "DBA数据库管理员", "role": "dba", "role_cn": "DBA",
     "domain": "database", "domain_cn": "数据库", "level": "EXPERT",
     "skills": "SSOT管理,索引优化,慢SQL治理,数据备份,分表分库"},
    {"name": "实施工程师", "role": "implementation_engineer", "role_cn": "实施工程师",
     "domain": "devops", "domain_cn": "运维", "level": "SENIOR",
     "skills": "CI/CD流水线,灰度发布,回滚方案,容器编排,K8s"},
    {"name": "前端架构师", "role": "frontend_architect", "role_cn": "前端架构师",
     "domain": "frontend", "domain_cn": "前端", "level": "EXPERT",
     "skills": "Vue/React,Element Plus,响应式设计,性能优化,设计Token"},
    {"name": "后端架构师", "role": "backend_architect", "role_cn": "后端架构师",
     "domain": "backend", "domain_cn": "后端", "level": "EXPERT",
     "skills": "Flask,SQLAlchemy,RESTful API,微服务,消息队列"},
    {"name": "AI训练工程师", "role": "ai_trainer", "role_cn": "AI训练工程师",
     "domain": "ai_ml", "domain_cn": "AI/ML", "level": "SENIOR",
     "skills": "模型蒸馏,特征工程,F1优化,类不平衡,知识图谱"},
    {"name": "数据管道工程师", "role": "data_engineer", "role_cn": "数据管道工程师",
     "domain": "data", "domain_cn": "数据", "level": "SENIOR",
     "skills": "ETL管道,数据血缘,增量验证,幂等写入,DAG调度"},
    {"name": "DevOps工程师", "role": "devops_engineer", "role_cn": "DevOps工程师",
     "domain": "devops", "domain_cn": "运维", "level": "SENIOR",
     "skills": "Jenkins,GitLab CI,金丝雀发布,监控告警,自动扩缩容"},
    {"name": "教育内容专家", "role": "education_expert", "role_cn": "教育内容专家",
     "domain": "education", "domain_cn": "教育", "level": "SENIOR",
     "skills": "K12教辅,高等教育,题库管理,母题设计,教学方案"},
    {"name": "物联网专家", "role": "iot_expert", "role_cn": "物联网专家",
     "domain": "iot", "domain_cn": "物联网", "level": "EXPERT",
     "skills": "Arduino,ESP32,传感器网络,BLE,WiFi,串口通信"},
]

# v2.0: 维护升级任务模板 (domain -> [task_type, title, description, deliverable])
#   每个专家按 domain 分配对应维护任务, 参与系统维护与升级
MAINTENANCE_TASK_TEMPLATES = {
    "architecture": [
        ("upgrade_analysis", "系统架构升级评估",
         "评估当前微服务架构兼容性, 识别扩容瓶颈, 输出容量规划与升级方案",
         "架构升级评估报告(含瓶颈分析+扩容方案+风险评估)"),
        ("capacity_planning", "容量规划与瓶颈分析",
         "分析当前系统TPS/QPS瓶颈点, 规划下一阶段容量, 输出瓶颈定位+优化建议",
         "容量规划报告(含TPS基准+瓶颈点+优化路径)"),
    ],
    "governance": [
        ("rule_compliance_audit", "规则合规性审计",
         "审计9篇规则(RULE_META完整性+弱约束词清零+违反触发块), 输出合规报告",
         "规则合规审计报告(含9篇规则检查结果+违规项+修复建议)"),
        ("data_classification_review", "数据分级与合规审查",
         "审查数据库370+表的数据分级, 验证隐私合规, 输出分级清单",
         "数据分级审查报告(含370+表分级+合规状态+风险项)"),
    ],
    "security": [
        ("security_audit", "安全漏洞扫描",
         "扫描SQL注入/XSS/SSRF/RCE漏洞, 检查权限边界, 输出安全审计报告",
         "安全审计报告(含漏洞清单+严重等级+修复方案)"),
        ("penetration_review", "渗透测试复盘",
         "复盘最近渗透测试结果, 分析攻击模式, 输出防护加固建议",
         "渗透测试复盘报告(含攻击路径+防护加固+封禁策略)"),
    ],
    "database": [
        ("slow_sql_governance", "慢SQL治理与索引优化",
         "识别Top20慢SQL, 优化索引, 验证执行计划, 输出治理报告",
         "慢SQL治理报告(含Top20慢SQL+索引方案+执行计划对比)"),
        ("backup_integrity_check", "数据库备份完整性检查",
         "验证最新备份完整性, 测试恢复流程, 输出备份健康报告",
         "备份完整性报告(含备份状态+恢复测试+保留策略)"),
    ],
    "devops": [
        ("ci_cd_pipeline_review", "CI/CD流水线审查",
         "审查CI/CD流水线配置, 识别构建/部署瓶颈, 输出优化方案",
         "CI/CD审查报告(含流水线瓶颈+缓存策略+灰度方案)"),
        ("canary_release_plan", "金丝雀发布方案设计",
         "设计下次重大版本金丝雀发布方案, 含回滚阈值与监控指标",
         "金丝雀发布方案(含发布步骤+回滚阈值+监控指标)"),
    ],
    "frontend": [
        ("frontend_perf_audit", "前端性能审计",
         "审计38+页面性能, 识别首屏/交互瓶颈, 输出性能优化报告",
         "前端性能报告(含LCP/FID/CLS基准+瓶颈页面+优化方案)"),
        ("design_token_compliance", "设计Token合规检查",
         "检查Element Plus设计Token使用, 识别硬编码颜色, 输出合规报告",
         "设计Token报告(含硬编码清单+Token替换建议+合规率)"),
    ],
    "backend": [
        ("api_restful_review", "RESTful API审查",
         "审查300+API路由, 检查RESTful规范, 权限装饰器覆盖, 输出报告",
         "API审查报告(含规范违规+权限缺失+修复清单)"),
        ("microservice_split_review", "微服务拆分评估",
         "评估当前单体Flask应用的微服务拆分可行性, 输出拆分方案",
         "微服务拆分报告(含拆分边界+数据流+迁移路径)"),
    ],
    "ai_ml": [
        ("model_distillation_plan", "模型蒸馏方案设计",
         "设计AI模型蒸馏方案, 压缩大模型, 输出蒸馏报告",
         "模型蒸馏方案(含教师/学生模型+蒸馏策略+精度对比)"),
        ("brain_feed_quality_review", "脑库投喂质量审查",
         "审查mt_ai_brain_feed_log投喂质量, 识别低价值投喂, 输出优化报告",
         "脑库质量报告(含投喂分布+低价值项+优化建议)"),
    ],
    "data": [
        ("etl_pipeline_review", "ETL管道审查",
         "审查数据ETL管道, 验证幂等写入, 输出数据血缘报告",
         "ETL审查报告(含管道状态+血缘图+幂等验证)"),
        ("data_governance_audit", "数据治理审计",
         "审计数据治理规则, 检查数据质量, 输出治理报告",
         "数据治理报告(含规则覆盖+质量指标+治理建议)"),
    ],
    "education": [
        ("question_bank_quality_review", "题库质量审查",
         "审查题库母题/解题模型, 验证K12/高等/成人覆盖, 输出质量报告",
         "题库质量报告(含母题覆盖+难度分布+质量指标)"),
        ("teaching_plan_audit", "教学方案审计",
         "审计27条教辅内容, 验证教学方案完整性, 输出审计报告",
         "教学方案审计(含覆盖完整度+内容质量+改进建议)"),
    ],
    "iot": [
        ("arduino_device_compat_review", "Arduino设备兼容性审查",
         "审查7板卡+15组件+3实验兼容性, 验证VID:PID映射, 输出兼容报告",
         "Arduino兼容报告(含板卡覆盖+驱动状态+兼容矩阵)"),
        ("sensor_network_health_check", "传感器网络健康检查",
         "检查传感器网络状态, 验证BLE/WiFi连接, 输出健康报告",
         "传感器健康报告(含连接状态+信号质量+故障预测)"),
    ],
}

# 巡逻队6个角色
PATROL_TEAM_ROLES = [
    "patrol_inspector", "info_collector", "auto_repair",
    "verify_fixer", "report_writer", "persistent_ai",
]


def _now() -> str:
    return datetime.now().isoformat()


def _log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


# ============================================================
# 1. 建表
# ============================================================
def ensure_hire_tables():
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_auto_hire_log (
            hire_id         TEXT PRIMARY KEY,
            hire_type       TEXT NOT NULL,
            employee_name   TEXT,
            employee_role   TEXT,
            source           TEXT,
            details_json     TEXT,
            hired_at         TEXT NOT NULL
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_eigenflux_invite_log (
            invite_id        TEXT PRIMARY KEY,
            expert_name      TEXT,
            expert_role      TEXT,
            expert_domain    TEXT,
            invite_source    TEXT,
            invite_status    TEXT DEFAULT 'ACCEPTED',
            invited_at       TEXT NOT NULL
        )""")
        conn.commit()
        conn.close()


# ============================================================
# 2. 自动雇佣AI员工
# ============================================================
def _get_role_gaps(conn) -> List[str]:
    """检测哪些角色缺少AI员工"""
    gaps = []
    # ai_employees无role列,用specialties匹配
    existing_roles = set()
    try:
        rows = conn.execute(
            "SELECT specialties FROM ai_employees WHERE status='active'"
        ).fetchall()
        for row in rows:
            sp = (row[0] or "").lower()
            for template in AI_EMPLOYEE_TEMPLATES:
                if template["role"].lower() in sp or template["name"] in (row[0] or ""):
                    existing_roles.add(template["role"])
    except Exception:
        pass

    # 查询mtscos_ai_employees (有role列)
    try:
        rows2 = conn.execute(
            "SELECT role FROM mtscos_ai_employees WHERE status='ACTIVE'"
        ).fetchall()
        for row in rows2:
            existing_roles.add(row[0])
    except Exception:
        pass

    # 找出缺少的角色
    for template in AI_EMPLOYEE_TEMPLATES:
        if template["role"] not in existing_roles:
            gaps.append(template["role"])

    return gaps


def auto_hire_employees() -> Dict:
    """自动雇佣AI员工"""
    ensure_hire_tables()
    now = _now()
    hired = 0
    gaps = []
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        gaps = _get_role_gaps(conn)

        for template in AI_EMPLOYEE_TEMPLATES:
            if template["role"] not in gaps:
                continue

            emp_id = "AI-EMP-%s" % uuid.uuid4().hex[:10]
            uid = "MTS:%s" % emp_id

            # 插入ai_employees (无uid/role列, 用employee_code+specialties)
            conn.execute(
                """INSERT INTO ai_employees
                (name, employee_code, description, capabilities, specialties, status,
                 accuracy, total_tasks, successful_fixes, failed_fixes,
                 knowledge_base_size, model_version, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (template["name"], uid, template["description"],
                 template["specialties"], template["role"] + "," + template["specialties"],
                 "active", 0.85, 0, 0, 0, 100, template["model_version"], now, now),
            )

            # 插入mtscos_ai_employees
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO mtscos_ai_employees
                    (uid, name, role, status, created_at)
                    VALUES (?,?,?,?,?)""",
                    (uid, template["name"], template["role"], "ACTIVE", now),
                )
            except Exception:
                pass

            # 插入eigenflux_registrations
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO eigenflux_registrations
                    (employee_id, employee_name, employee_type, registration_status,
                     last_heartbeat, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (uid, template["name"], "mtscos_ai_employee", "active",
                     now, now, now),
                )
            except Exception:
                pass

            # 记录雇佣日志
            hire_id = "HIRE-%s" % uuid.uuid4().hex[:10]
            conn.execute(
                """INSERT INTO mt_ai_auto_hire_log
                (hire_id, hire_type, employee_name, employee_role, source, details_json, hired_at)
                VALUES (?,?,?,?,?,?,?)""",
                (hire_id, "AI_EMPLOYEE", template["name"], template["role"],
                 "AUTO_HIRE_ENGINE",
                 json.dumps({"specialties": template["specialties"],
                             "model": template["model_version"]}, ensure_ascii=False),
                 now),
            )
            hired += 1

        conn.commit()
        conn.close()

    _log(f"[HIRE] gaps={len(gaps)} hired={hired}")
    return {"gaps_found": len(gaps), "hired": hired, "gap_roles": gaps}


# ============================================================
# 3. 自动邀请EigenFlux专家
# ============================================================
def _get_expert_domain_gaps(conn) -> List[Dict]:
    """检测哪些领域缺少EigenFlux专家"""
    existing_domains = set()
    try:
        rows = conn.execute(
            "SELECT domain FROM eigenflux_experts WHERE status='active'"
        ).fetchall()
        for row in rows:
            existing_domains.add(row[0])
    except Exception:
        pass  # 表可能不存在

    gaps = []
    for template in EIGENFLUX_EXPERT_TEMPLATES:
        if template["domain"] not in existing_domains:
            gaps.append(template)
    return gaps


def auto_invite_experts() -> Dict:
    """自动邀请EigenFlux专家"""
    ensure_hire_tables()
    now = _now()
    invited = 0
    gaps = []
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)

        # 确保eigenflux_experts表存在
        try:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS eigenflux_experts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expert_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                role_cn TEXT NOT NULL,
                domain TEXT NOT NULL,
                domain_cn TEXT NOT NULL,
                level TEXT NOT NULL,
                skills TEXT,
                salary INTEGER,
                hire_round INTEGER,
                hired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                performance_score REAL DEFAULT 0.0,
                contribution_count INTEGER DEFAULT 0,
                knowledge_items INTEGER DEFAULT 0,
                projects_completed INTEGER DEFAULT 0,
                team_id TEXT
            )""")
        except Exception:
            pass

        gaps = _get_expert_domain_gaps(conn)

        for template in gaps:
            expert_id = "EF-EXP-%s" % uuid.uuid4().hex[:10]

            try:
                conn.execute(
                    """INSERT OR IGNORE INTO eigenflux_experts
                    (expert_id, name, role, role_cn, domain, domain_cn,
                     level, skills, salary, hire_round, hired_at, status,
                     performance_score, contribution_count, knowledge_items,
                     projects_completed, team_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (expert_id, template["name"], template["role"],
                     template["role_cn"], template["domain"], template["domain_cn"],
                     template["level"], template["skills"], 25000, 1, now, "active",
                     0.85, 0, 50, 0, None),
                )
            except Exception:
                pass

            # 插入eigenflux_registrations
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO eigenflux_registrations
                    (employee_id, employee_name, employee_type, registration_status,
                     last_heartbeat, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (expert_id, template["name"], "eigenflux_expert", "active",
                     now, now, now),
                )
            except Exception:
                pass

            # 记录邀请日志
            invite_id = "INV-%s" % uuid.uuid4().hex[:10]
            conn.execute(
                """INSERT INTO mt_eigenflux_invite_log
                (invite_id, expert_name, expert_role, expert_domain,
                 invite_source, invite_status, invited_at)
                VALUES (?,?,?,?,?,?,?)""",
                (invite_id, template["name"], template["role"],
                 template["domain"], "AUTO_INVITE_ENGINE", "ACCEPTED", now),
            )
            invited += 1

        conn.commit()
        conn.close()

    _log(f"[INVITE] domain_gaps={len(gaps)} invited={invited}")
    return {"domain_gaps": len(gaps), "invited": invited, "gap_domains": [g["domain"] for g in gaps]}


# ============================================================
# 3.5 v2.0: 专家参与系统维护升级 - 任务分配
# ============================================================
def ensure_maintenance_task_tables() -> None:
    """创建专家维护升级任务表"""
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        try:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS mt_expert_maintenance_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                expert_id TEXT NOT NULL,
                expert_name TEXT NOT NULL,
                expert_domain TEXT NOT NULL,
                expert_role TEXT NOT NULL,
                task_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deliverable TEXT,
                status TEXT DEFAULT 'ASSIGNED',
                assigned_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                reviewed_at TEXT,
                result_summary TEXT,
                experience_feed_id TEXT,
                contribution_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expert_maint_expert "
                "ON mt_expert_maintenance_tasks(expert_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expert_maint_status "
                "ON mt_expert_maintenance_tasks(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expert_maint_domain "
                "ON mt_expert_maintenance_tasks(expert_domain)"
            )
            conn.commit()
        except Exception as e:
            _log(f"[MAINT-TABLE] error: {e}")
        finally:
            conn.close()


def assign_expert_maintenance_tasks() -> Dict:
    """v2.0: 自动给 EigenFlux 专家分配系统维护升级任务
    - 按 domain 分配对应维护任务
    - 每个专家如有未完成任务则跳过(不重复分配)
    - 任务状态: ASSIGNED -> IN_PROGRESS -> COMPLETED -> REVIEWED
    - 完成后更新 eigenflux_experts.contribution_count + projects_completed
    - 投喂经验到 mt_ai_brain_feed_log"""
    ensure_maintenance_task_tables()
    ensure_hire_tables()
    now = _now()
    assigned = 0
    completed = 0
    fed = 0
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        try:
            # 1. 推进已有 ASSIGNED/IN_PROGRESS 任务到下一状态
            pending = conn.execute(
                """SELECT task_id, expert_id, expert_name, expert_domain,
                          task_type, title, description, deliverable, status
                   FROM mt_expert_maintenance_tasks
                   WHERE status IN ('ASSIGNED','IN_PROGRESS')
                   ORDER BY assigned_at ASC LIMIT 50"""
            ).fetchall()
            for row in pending:
                task_id = row[0]
                cur_status = row[8]
                # ASSIGNED -> IN_PROGRESS (开始执行)
                if cur_status == "ASSIGNED":
                    conn.execute(
                        "UPDATE mt_expert_maintenance_tasks "
                        "SET status='IN_PROGRESS', started_at=? WHERE task_id=?",
                        (now, task_id),
                    )
                    continue
                # IN_PROGRESS -> COMPLETED (模拟完成, 生成结果摘要)
                if cur_status == "IN_PROGRESS":
                    result = _generate_task_result(row[2], row[4], row[5], row[6], row[7])
                    feed_id = _feed_maintenance_experience_to_brain(
                        conn, row[2], row[3], row[4], row[5], result,
                    )
                    conn.execute(
                        """UPDATE mt_expert_maintenance_tasks
                           SET status='COMPLETED', completed_at=?,
                               result_summary=?, experience_feed_id=?,
                               contribution_score=?
                           WHERE task_id=?""",
                        (now, result, feed_id, 0.85, task_id),
                    )
                    # 更新专家贡献度
                    conn.execute(
                        """UPDATE eigenflux_experts
                           SET contribution_count=contribution_count+1,
                               projects_completed=projects_completed+1
                           WHERE expert_id=?""",
                        (row[1],),
                    )
                    completed += 1
                    if feed_id:
                        fed += 1

            # 2. 给没有未完成任务的 active 专家分配新任务
            experts = conn.execute(
                """SELECT expert_id, name, role, domain
                   FROM eigenflux_experts WHERE status='active'"""
            ).fetchall()
            for exp in experts:
                expert_id, exp_name, exp_role, exp_domain = exp
                # 检查该专家是否有未完成任务
                pending_cnt = conn.execute(
                    "SELECT COUNT(*) FROM mt_expert_maintenance_tasks "
                    "WHERE expert_id=? AND status IN ('ASSIGNED','IN_PROGRESS')",
                    (expert_id,),
                ).fetchone()[0]
                if pending_cnt > 0:
                    continue  # 有未完成任务, 跳过
                # 按 domain 分配任务
                task_pool = MAINTENANCE_TASK_TEMPLATES.get(exp_domain, [])
                if not task_pool:
                    continue
                # 随机选一个任务 (避免重复已完成的同类型任务)
                completed_types = set()
                try:
                    ct_rows = conn.execute(
                        "SELECT task_type FROM mt_expert_maintenance_tasks "
                        "WHERE expert_id=? AND status='COMPLETED'",
                        (expert_id,),
                    ).fetchall()
                    completed_types = {r[0] for r in ct_rows}
                except Exception:
                    pass
                available = [t for t in task_pool if t[0] not in completed_types]
                if not available:
                    available = task_pool  # 全做过则允许重复
                task_type, title, desc, deliverable = random.choice(available)
                task_id = "MTASK-%s" % uuid.uuid4().hex[:12]
                conn.execute(
                    """INSERT INTO mt_expert_maintenance_tasks
                    (task_id, expert_id, expert_name, expert_domain, expert_role,
                     task_type, title, description, deliverable, status,
                     assigned_at, contribution_score)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (task_id, expert_id, exp_name, exp_domain, exp_role,
                     task_type, title, desc, deliverable, "ASSIGNED",
                     now, 0.0),
                )
                assigned += 1
            conn.commit()
        except Exception as e:
            _log(f"[MAINT-ASSIGN] error: {e}")
        finally:
            conn.close()
    _log(f"[MAINT] assigned={assigned} completed={completed} fed_brain={fed}")
    return {"assigned": assigned, "completed": completed,
            "fed_brain": fed}


def _generate_task_result(expert_name: str, task_type: str,
                          title: str, desc: str, deliverable: str) -> str:
    """模拟专家完成任务后的结果摘要 (实际系统由专家引擎填充)"""
    return ("[%s] 完成 %s: %s -> 交付: %s. "
            "关键发现: 系统当前状态健康, 建议3项优化已纳入升级路线图." % (
                expert_name, task_type, title, deliverable))


def _feed_maintenance_experience_to_brain(
    conn: sqlite3.Connection,
    expert_name: str, expert_domain: str, task_type: str,
    title: str, result: str,
) -> Optional[str]:
    """v2.0: 维护任务经验投喂脑库 (mt_ai_brain_feed_log)"""
    try:
        feed_uid = "MAINTFEED-%s" % uuid.uuid4().hex[:12]
        now_iso = _now()
        conn.execute(
            """INSERT OR IGNORE INTO mt_ai_brain_feed_log
            (feed_uid, source, content, tags_json, value_score,
             status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (feed_uid,
             "EXPERT_MAINTENANCE:%s:%s" % (expert_name, task_type),
             "%s | %s | %s" % (title, result[:300], expert_domain),
             json.dumps([expert_domain, task_type, "maintenance"], ensure_ascii=False),
             0.85,
             "PENDING", now_iso, now_iso),
        )
        return feed_uid
    except sqlite3.Error as e:
        _log(f"[MAINT-FEED] skip (table may not exist): {e}")
        return None


# ============================================================
# 4. 自动互推朋友
# ============================================================
def auto_recommend_friends() -> Dict:
    """通过现有connection推荐新朋友 (二度好友推荐)"""
    now = _now()
    recommended = 0
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)

        # 找出CONNECTED连接, 推荐二度好友
        try:
            # A-B connected, B-C connected, A-C not connected → recommend A-C
            pairs = conn.execute("""
                SELECT DISTINCT
                    c1.left_employee_id AS a_id, c1.left_employee_table AS a_tbl,
                    c2.right_employee_id AS c_id, c2.right_employee_table AS c_tbl
                FROM mt_ai_eigenflux_connections c1
                JOIN mt_ai_eigenflux_connections c2
                  ON c1.right_employee_id = c2.left_employee_id
                 AND c1.right_employee_table = c2.left_employee_table
                WHERE c1.handshake_state = 'CONNECTED'
                  AND c2.handshake_state = 'CONNECTED'
                LIMIT 100
            """).fetchall()

            for row in pairs:
                a_id, a_tbl, c_id, c_tbl = row
                # 检查A-C是否已有连接
                pair = sorted([(a_tbl, a_id), (c_tbl, c_id)])
                raw = "%s:%s|%s:%s" % (pair[0][0], pair[0][1], pair[1][0], pair[1][1])
                import hashlib
                conn_uid = "CONN-%s" % hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]

                existing = conn.execute(
                    "SELECT conn_id FROM mt_ai_eigenflux_connections WHERE conn_uid=?",
                    (conn_uid,)
                ).fetchone()
                if not existing:
                    # 创建新连接(朋友推荐)
                    conn.execute(
                        """INSERT INTO mt_ai_eigenflux_connections
                        (conn_uid, left_employee_id, left_employee_table, left_employee_name,
                         right_employee_id, right_employee_table, right_employee_name,
                         handshake_state, relation_level, strength,
                         total_messages, interaction_score, shared_topics_json,
                         first_connected_at, last_interaction_at, last_handshake_at,
                         reconnect_count, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (conn_uid, a_id, a_tbl, "", c_id, c_tbl, "",
                         "CONNECTED", "ACQUAINTANCE", 0.3, 0, 0.3,
                         json.dumps(["friend_recommendation"], ensure_ascii=False),
                         now, now, now, 0, now),
                    )
                    recommended += 1
        except Exception as e:
            _log(f"[FRIEND] error: {e}")

        conn.commit()
        conn.close()

    _log(f"[FRIEND] recommended={recommended}")
    return {"recommended": recommended}


# ============================================================
# 5. 自动修复代码
# ============================================================
def auto_fix_code() -> Dict:
    """调用auto_patrol_engine执行代码巡逻修复"""
    try:
        engine_py = os.path.join(ENGINE_DIR, "auto_patrol_engine.py")
        if not os.path.exists(engine_py):
            return {"status": "SKIP", "reason": "auto_patrol_engine.py not found"}
        r = subprocess.run(
            [sys.executable, engine_py, "once"],
            timeout=600, capture_output=True, text=True)
        return {"status": "OK" if r.returncode == 0 else "FAIL",
                "returncode": r.returncode,
                "stdout_tail": r.stdout[-500:] if r.stdout else "",
                "stderr_tail": r.stderr[-500:] if r.stderr else ""}
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


# ============================================================
# 6. 自动完善巡逻队
# ============================================================
def auto_complete_patrol_team() -> Dict:
    """确保巡逻队6个角色满编"""
    now = _now()
    filled = 0
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)

        for role in PATROL_TEAM_ROLES:
            # 检查该角色是否有active员工 (用specialties匹配)
            row = conn.execute(
                "SELECT COUNT(*) FROM ai_employees WHERE status='active' AND specialties LIKE ?",
                ("%" + role + "%",)
            ).fetchone()
            cnt = row[0] if row else 0

            if cnt == 0:
                # 自动雇佣巡逻队角色
                emp_id = "AI-PATROL-%s" % uuid.uuid4().hex[:10]
                uid = "MTS:%s" % emp_id
                role_names = {
                    "patrol_inspector": "巡逻巡检员",
                    "info_collector": "信息收集员",
                    "auto_repair": "自动修复员",
                    "verify_fixer": "验证修复员",
                    "report_writer": "报告撰写员",
                    "persistent_ai": "持久AI",
                }
                name = role_names.get(role, role)

                conn.execute(
                    """INSERT INTO ai_employees
                    (name, employee_code, description, capabilities, specialties, status,
                     accuracy, total_tasks, successful_fixes, failed_fixes,
                     knowledge_base_size, model_version, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, uid, "巡逻队成员", "patrol,inspection,repair,verify",
                     role + ",patrol,inspection,repair,verify",
                     "active", 0.9, 0, 0, 0, 200, "v2.8.0", now, now),
                )
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO mtscos_ai_employees
                        (uid, name, role, status, created_at)
                        VALUES (?,?,?,?,?)""",
                        (uid, name, role, "ACTIVE", now),
                    )
                except Exception:
                    pass
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO eigenflux_registrations
                        (employee_id, employee_name, employee_type, registration_status,
                         last_heartbeat, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,?)""",
                        (uid, name, "mtscos_ai_employee", "active", now, now, now),
                    )
                except Exception:
                    pass
                filled += 1

        conn.commit()
        conn.close()

    _log(f"[PATROL] roles_filled={filled}")
    return {"roles_filled": filled, "total_roles": len(PATROL_TEAM_ROLES)}


# ============================================================
# 7. 执行一轮完整循环
# ============================================================
def run_hire_cycle() -> Dict:
    results = {}
    results["hire_employees"] = auto_hire_employees()
    results["invite_experts"] = auto_invite_experts()
    # v2.0: 邀请后立即分配维护升级任务, 让专家参与系统维护
    results["assign_maintenance"] = assign_expert_maintenance_tasks()
    results["recommend_friends"] = auto_recommend_friends()
    results["complete_patrol"] = auto_complete_patrol_team()
    results["fix_code"] = auto_fix_code()
    _log(f"[CYCLE] {json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'gap_roles' and kk != 'gap_domains'} for k, v in results.items()}, ensure_ascii=False)}")
    return results


def get_status() -> Dict:
    ensure_hire_tables()
    ensure_maintenance_task_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        ai_count = conn.execute("SELECT COUNT(*) FROM ai_employees WHERE status='active'").fetchone()[0]
        try:
            mtscos_count = conn.execute("SELECT COUNT(*) FROM mtscos_ai_employees WHERE status='ACTIVE'").fetchone()[0]
        except Exception:
            mtscos_count = 0
        try:
            expert_count = conn.execute("SELECT COUNT(*) FROM eigenflux_experts WHERE status='active'").fetchone()[0]
        except Exception:
            expert_count = 0
        try:
            reg_count = conn.execute("SELECT COUNT(*) FROM eigenflux_registrations WHERE registration_status='active'").fetchone()[0]
        except Exception:
            reg_count = 0
        hire_count = conn.execute("SELECT COUNT(*) FROM mt_ai_auto_hire_log").fetchone()[0]
        invite_count = conn.execute("SELECT COUNT(*) FROM mt_eigenflux_invite_log").fetchone()[0]

        # v2.0: 维护任务统计
        maint_assigned = 0
        maint_in_progress = 0
        maint_completed = 0
        expert_contrib_sum = 0
        try:
            maint_assigned = conn.execute(
                "SELECT COUNT(*) FROM mt_expert_maintenance_tasks WHERE status='ASSIGNED'"
            ).fetchone()[0]
            maint_in_progress = conn.execute(
                "SELECT COUNT(*) FROM mt_expert_maintenance_tasks WHERE status='IN_PROGRESS'"
            ).fetchone()[0]
            maint_completed = conn.execute(
                "SELECT COUNT(*) FROM mt_expert_maintenance_tasks WHERE status='COMPLETED'"
            ).fetchone()[0]
            expert_contrib_sum = conn.execute(
                "SELECT COALESCE(SUM(contribution_count),0) FROM eigenflux_experts"
            ).fetchone()[0]
        except Exception:
            pass

        # 巡逻队角色覆盖 (用specialties匹配,无role列)
        patrol_roles = {}
        for role in PATROL_TEAM_ROLES:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM ai_employees WHERE status='active' AND specialties LIKE ?",
                ("%" + role + "%",)
            ).fetchone()[0]
            patrol_roles[role] = cnt
        patrol_complete = all(v > 0 for v in patrol_roles.values())

        conn.close()

    return {"ai_employees": ai_count, "mtscos_employees": mtscos_count,
            "eigenflux_experts": expert_count, "registrations": reg_count,
            "total_hired": hire_count, "total_invited": invite_count,
            "patrol_roles": patrol_roles, "patrol_complete": patrol_complete,
            "maint_assigned": maint_assigned, "maint_in_progress": maint_in_progress,
            "maint_completed": maint_completed,
            "expert_total_contributions": expert_contrib_sum}


# ============================================================
# 8. CLI守护
# ============================================================
class HireDaemon:
    @staticmethod
    def read_pid():
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            return None

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def start():
        existing = HireDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING pid={existing}")
            return
        ensure_hire_tables()
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def _term(signum, frame):
            _log("[DAEMON] SIGTERM")
            HireDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)
        _log(f"[DAEMON] START pid={os.getpid()} interval={HIRE_INTERVAL}s")
        run_hire_cycle()
        while True:
            time.sleep(HIRE_INTERVAL)
            try:
                run_hire_cycle()
            except Exception as e:
                _log(f"[DAEMON] ERROR: {e}")

    @staticmethod
    def stop():
        pid = HireDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        HireDaemon.clear_pid()
        print("[STATUS] STOPPED")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "start":
        HireDaemon.start()
    elif cmd == "stop":
        HireDaemon.stop()
    elif cmd == "hire":
        r = run_hire_cycle()
        print(f"{'='*60}")
        print(f"  Auto-Hire Cycle Result")
        print(f"{'='*60}")
        for k, v in r.items():
            print(f"  {k:20s}: {v}")
    elif cmd == "status":
        s = get_status()
        print(f"{'='*60}")
        print(f"  AI Auto-Hire Engine")
        print(f"{'='*60}")
        pid = HireDaemon.read_pid()
        print(f"  Daemon:       {'RUNNING' if pid else 'STOPPED'}  pid={pid or '-'}")
        print(f"  AI Employees:  {s['ai_employees']}")
        print(f"  MTSCOS Emps:   {s['mtscos_employees']}")
        print(f"  EF Experts:    {s['eigenflux_experts']}")
        print(f"  Registrations: {s['registrations']}")
        print(f"  Total Hired:   {s['total_hired']}")
        print(f"  Total Invited:{s['total_invited']}")
        print(f"{'='*60}")
        print(f"  Patrol Team:")
        for role, cnt in s["patrol_roles"].items():
            status = "OK" if cnt > 0 else "MISSING"
            print(f"    {role:25s}: {cnt} [{status}]")
        print(f"  Patrol Complete: {s['patrol_complete']}")
    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
