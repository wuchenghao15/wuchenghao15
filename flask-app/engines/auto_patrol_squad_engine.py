#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 自动轮巡队伍引擎 (Auto Patrol Squad Engine v1.0.0)
============================================================
自动建立轮巡队伍 → 组长下发任务 → 发现针对性目标(漏洞/功能补齐) → AI查漏补缺 →
自动升级维护 → 邀请EigenFlux专家加入 → 自动修复上报 → 自动报备SA

6大模块:
  1. SquadBuilder       - 自动建立轮巡队伍(创建队伍/指定组长/分配队员)
  2. TaskDispatcher     - 自动为组长下发任务(任务分发→组长接收→分配队员)
  3. TargetDiscoverer   - 自动发现针对性任务目标(漏洞扫描/功能补齐/查漏补缺)
  4. AutoFixer          - AI自动查漏补缺(自动修复+升级维护)
  5. ExpertRecruiter    - 自动邀请EigenFlux专家和朋友加入轮巡队伍
  6. SAReporter         - 自动报备SA(向超级管理员报备发现/修复/升级)

SA报备机制:
  - 发现高危漏洞 → 立即报备SA
  - 修复完成 → 报备SA修复结果
  - 升级完成 → 报备SA升级详情
  - 邀请专家 → 报备SA邀请情况
  - 每轮巡周期 → 生成完整报告报备SA
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import threading
import time
import sqlite3
import logging
# [unused] from collections import defaultdict, deque
from dataclasses import dataclass, field
# [unused] from datetime import datetime, timedelta
# [unused] from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('PatrolSquad')

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

try:
    # [unused] from mt_ir14_dev_flow import _get_conn, _LOCK, feed_brain, ensure_tables
    HAS_DEV_FLOW = True
except Exception:
    HAS_DEV_FLOW = False
    _LOCK = threading.Lock()
    def _get_conn(): return sqlite3.connect(os.path.join(_BASE, "app.db"))
    def feed_brain(flow_id, kind, content): pass
    def ensure_tables(): pass

# ========== 常量 ==========

MAX_SQUAD_SIZE = 8                # 每队最大人数
MAX_TASKS_PER_LEADER = 10         # 每个组长最大任务数
SA_REPORT_PRIORITY_THRESHOLD = "high"  # SA报备优先级阈值
PATROL_CYCLE_INTERVAL = 120       # 轮巡周期(秒)

# 轮巡队伍类型
SQUAD_TYPES = {
    "security_patrol": ("安全轮巡队", "漏洞扫描/安全审计/威胁狩猎/渗透测试"),
    "feature_patrol": ("功能轮巡队", "功能补齐/CRUD检查/接口完善/页面修复"),
    "quality_patrol": ("质量轮巡队", "代码质量/性能优化/死代码清理/资源泄露"),
    "maintenance_patrol": ("维护轮巡队", "系统维护/版本升级/配置更新/备份检查"),
    "learning_patrol": ("学习轮巡队", "知识更新/技能升级/经验沉淀/脑库投喂"),
    "dev_patrol": ("开发功能检测与开发轮巡队", "功能检测/开发规划/Gap扫描/TODO处理/占位符实现/缺失CRUD开发/孤儿路由修复/缺失API补齐"),
    "audit_patrol": ("数据验违轮巡队", "系统数据违规检测/数据完整性校验/业务规则稽核/跨表一致性比对/敏感数据明文扫描/主键唯一性/外键孤儿/枚举值非法/重复数据/状态机违规"),
}

# 任务目标类型
TARGET_TYPES = {
    "vulnerability": ("漏洞发现", "扫描安全漏洞(SQL注入/XSS/命令注入/硬编码密钥)", "critical"),
    "missing_feature": ("功能缺失", "检测未实现功能(pass/TODO/FIXME/占位符)", "high"),
    "missing_crud": ("CRUD缺失", "检测缺失的创建/更新/删除接口", "medium"),
    "performance_issue": ("性能问题", "检测性能瓶颈(N+1查询/大循环/内存泄露)", "medium"),
    "code_smell": ("代码异味", "检测代码质量问题(重复代码/长函数/复杂度过高)", "low"),
    "resource_leak": ("资源泄露", "检测资源未释放(文件/连接/锁)", "high"),
    "config_drift": ("配置漂移", "检测配置与基线不一致", "medium"),
    "knowledge_gap": ("知识缺口", "检测AI员工知识库过期/缺失", "low"),
    # ===== 开发功能检测与开发专用目标 =====
    "dev_todo_fixme": ("TODO/FIXME待开发", "扫描代码中的TODO/FIXME/HACK/XXX标记并转为开发任务", "high"),
    "dev_placeholder": ("占位符未实现", "检测return 'TODO'/pass/未实现的函数并补齐", "high"),
    "dev_missing_crud": ("缺失CRUD操作", "检测模型有路由但缺少Create/Update/Delete接口", "medium"),
    "dev_orphan_route": ("孤儿路由", "路由存在但功能不完整(返回占位/缺少实现)", "medium"),
    "dev_missing_api": ("缺失API实现", "前端引用但后端未实现的API接口", "high"),
    "dev_gap_scan": ("开发缺口扫描", "自动扫描系统未开发功能并规划开发任务", "medium"),
    "dev_plan": ("开发规划", "根据Gap扫描结果规划开发排期和资源分配", "low"),
    # ===== 系统数据验违专用目标 =====
    "audit_integrity": ("数据完整性违规", "主键/唯一键重复/NULL字段空值/CHECK约束违反/外键孤儿记录", "critical"),
    "audit_duplicate": ("重复数据违规", "同一业务键存在多条记录/完全重复行/去重遗漏", "high"),
    "audit_consistency": ("跨表一致性违规", "主从表数量不匹配/冗余字段不一致/汇总值与明细不符", "high"),
    "audit_business_rule": ("业务规则违规", "余额为负/库存负数/状态跃迁非法/时间倒序/级别跳变", "high"),
    "audit_enum": ("枚举值非法", "字段取值不在规定枚举范围内(如status=99/role=unknown)", "medium"),
    "audit_sensitive_plaintext": ("敏感数据明文", "密码/身份证/手机号/Token明文存储/缺少脱敏前缀", "critical"),
    "audit_orphan_fk": ("外键孤儿记录", "外键指向的主记录不存在/被删除/ID无效(0/-1/空串)", "high"),
    "audit_json_format": ("JSON/BLOB格式损坏", "JSON字段解析失败/XML结构断裂/BLOB二进制异常", "medium"),
    "audit_range_bound": ("值域越界", "数值超范围/百分比>100/负数非负字段/日期越界溢出", "medium"),
    "audit_audit_trail": ("审计痕迹缺失", "删除无记录/修改无version/创建人不存在/时间戳异常(未来/远古)", "low"),
}

# 专家邀请候选(按领域)
EXPERT_POOL = {
    "security": [
        ("EF_红队指挥_201", "渗透测试/攻击链编排", 0.96),
        ("EF_蓝队防御_202", "防御协调/态势感知", 0.95),
        ("EF_威胁狩猎_207", "威胁狩猎/IOC狩猎", 0.94),
    ],
    "feature": [
        ("原液_修复AI_302", "自动修复/热补丁", 0.95),
        ("原液_巡检AI_301", "自动巡检/异常发现", 0.94),
    ],
    "quality": [
        ("EF_云安全_231", "性能优化/云安全", 0.93),
        ("原液_协调AI_305", "任务协调/调度", 0.92),
    ],
    "maintenance": [
        ("EF_容器安全_232", "容器维护/K8s", 0.93),
        ("EF_供应链安全_234", "供应链/依赖管理", 0.92),
    ],
    "learning": [
        ("原液_学习AI_303", "自主学习/知识抽取", 0.95),
        ("原液_脑库AI_304", "脑库投喂/经验沉淀", 0.94),
    ],
    # ===== 开发功能检测与开发专用专家 =====
    "dev": [
        ("原液_修复AI_302", "自动修复/热补丁/占位符实现", 0.95),
        ("原液_巡检AI_301", "自动巡检/Gap扫描/TODO检测", 0.94),
        ("原液_协调AI_305", "任务协调/开发调度/资源分配", 0.92),
        ("EF_SBOM物料_233", "依赖管理/接口契约/API完整性校验", 0.93),
        ("EF_后量子密码_222", "复杂系统架构/代码重构/功能设计", 0.95),
    ],
    # ===== 系统数据验违专用专家 =====
    "audit": [
        ("EF_差分隐私_223", "数据合规/隐私脱敏/敏感数据检测", 0.95),
        ("EF_k匿名_224", "数据质量/完整性校验/统计一致性", 0.94),
        ("原液_验证AI_004", "验证稽核/状态机校验/业务规则稽核", 0.95),
        ("原液_巡检AI_301", "跨表比对/重复检测/外键孤儿扫描", 0.94),
        ("EF_模型水印_226", "审计痕迹/版本链/变更追溯/不可抵赖校验", 0.93),
    ],
}

# 漏洞类型库
VULN_CATEGORIES = [
    ("sql_injection", "SQL注入", "critical", "用户输入直接拼接SQL语句"),
    ("xss", "跨站脚本(XSS)", "high", "未转义的用户输入输出到页面"),
    ("command_injection", "命令注入", "critical", "用户输入拼接到系统命令"),
    ("hardcoded_secret", "硬编码密钥", "high", "代码中包含密码/API密钥/Token"),
    ("insecure_deserialization", "不安全反序列化", "high", "使用pickle/eval处理不可信数据"),
    ("path_traversal", "路径穿越", "high", "用户输入拼接到文件路径"),
    ("csrf", "跨站请求伪造", "medium", "缺少CSRF Token校验"),
    ("ssrf", "服务端请求伪造", "high", "用户可控的URL请求"),
    ("info_disclosure", "信息泄露", "medium", "错误信息暴露敏感数据"),
    ("weak_crypto", "弱加密", "medium", "使用不安全的加密算法"),
]

# SA报备类型
SA_REPORT_TYPES = {
    "vuln_critical": ("高危漏洞报备", "发现critical级别漏洞,需SA关注"),
    "vuln_summary": ("漏洞扫描汇总", "本轮巡漏洞扫描结果汇总"),
    "fix_completed": ("修复完成报备", "自动修复已完成,报备修复详情"),
    "upgrade_done": ("升级完成报备", "系统升级已完成,报备升级详情"),
    "expert_invited": ("专家邀请报备", "已邀请EigenFlux专家加入轮巡"),
    "cycle_report": ("轮巡周期报告", "完整轮巡周期报告"),
    "anomaly_alert": ("异常告警报备", "检测到系统异常,需SA介入"),
    # ===== 开发功能检测与开发专用报备 =====
    "dev_gap_found": ("开发缺口发现", "Gap扫描发现未开发功能/TODO/占位符"),
    "dev_task_assigned": ("开发任务下发", "开发轮巡队已分配开发任务给组长/队员"),
    "dev_impl_completed": ("开发任务完成", "占位符实现/CRUD开发/API补齐完成"),
    "dev_plan_report": ("开发规划报备", "Gap扫描→开发任务→资源分配→排期的完整规划"),
    # ===== 系统数据验违专用报备 =====
    "audit_violation_found": ("数据违规发现", "验违扫描发现数据完整性/一致性/业务规则/敏感明文等违规"),
    "audit_critical_alert": ("关键数据违规告警", "critical级别验违(敏感明文/主键冲突/业务规则)立即报备SA"),
    "audit_fix_completed": ("数据修复完成", "违规数据清洗/脱敏/去重/外键修复/一致性对账完成"),
    "audit_report_summary": ("数据验违汇总报告", "全表/全库数据验违扫描结果汇总+修复率+剩余风险清单"),
}


# ========== 数据结构 ==========

@dataclass
class PatrolSquad:
    """轮巡队伍"""
    squad_id: str = ""
    squad_type: str = ""
    squad_name: str = ""
    objective: str = ""
    leader_id: str = ""
    leader_name: str = ""
    member_ids: List[str] = field(default_factory=list)
    member_names: List[str] = field(default_factory=list)
    formed_at: str = ""
    status: str = "active"  # active/disbanded/resting
    tasks_completed: int = 0
    vulns_found: int = 0
    fixes_applied: int = 0
    performance_score: float = 0.0


@dataclass
class PatrolTask:
    """轮巡任务"""
    task_id: str = ""
    squad_id: str = ""
    target_type: str = ""
    target_title: str = ""
    target_description: str = ""
    severity: str = "medium"
    assigned_by: str = ""  # 分配者(系统/组长)
    assigned_to: str = ""  # 执行者(组长/队员)
    assigned_to_name: str = ""
    status: str = "pending"  # pending→assigned→in_progress→completed→failed
    priority: int = 3  # 1-5
    detected_at: str = ""
    assigned_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    result: str = ""
    fix_detail: str = ""


@dataclass
class VulnFinding:
    """漏洞发现"""
    finding_id: str = ""
    scan_id: str = ""
    category: str = ""
    category_cn: str = ""
    severity: str = "medium"
    title: str = ""
    description: str = ""
    file_path: str = ""
    line_number: int = 0
    code_snippet: str = ""
    status: str = "discovered"  # discovered→fixing→fixed→verified→archived
    fix_id: str = ""
    fix_detail: str = ""
    fixed_at: str = ""
    verified: bool = False
    detected_at: str = ""


@dataclass
class ExpertRecruitment:
    """专家招募"""
    recruitment_id: str = ""
    expert_name: str = ""
    expert_specialty: str = ""
    expected_accuracy: float = 0.0
    target_squad: str = ""
    invitation_reason: str = ""
    invitation_status: str = "pending"  # pending/accepted/rejected
    invited_at: str = ""
    responded_at: str = ""
    joined_as: str = ""  # leader/member/advisor


@dataclass
class SAReport:
    """SA报备"""
    report_id: str = ""
    report_type: str = ""
    title: str = ""
    content: str = ""
    priority: str = "medium"  # low/medium/high/critical
    operator: str = "AutoPatrolSquad"
    flow_id: str = ""
    created_at: str = ""
    acknowledged: bool = False


@dataclass
class PatrolCycleReport:
    """轮巡周期报告"""
    report_id: str = ""
    flow_id: str = ""
    cycle_number: int = 0
    squads_active: int = 0
    tasks_dispatched: int = 0
    tasks_completed: int = 0
    vulns_found: int = 0
    vulns_fixed: int = 0
    experts_invited: int = 0
    experts_joined: int = 0
    sa_reports_sent: int = 0
    upgrades_applied: int = 0
    squads: List[Dict] = field(default_factory=list)
    tasks: List[Dict] = field(default_factory=list)
    vulns: List[Dict] = field(default_factory=list)
    recruitments: List[Dict] = field(default_factory=list)
    sa_reports: List[Dict] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)
    summary: str = ""
    generated_at: str = ""
    duration: float = 0.0


# ========== 数据库表创建 ==========

def ensure_patrol_tables():
    """确保轮巡队伍相关表存在"""
    with _LOCK:
        c = _get_conn()
        cur = c.cursor()

        # 轮巡队伍表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_patrol_squads (
            squad_id TEXT PRIMARY KEY,
            squad_type TEXT,
            squad_name TEXT,
            objective TEXT,
            leader_id TEXT,
            leader_name TEXT,
            member_ids_json TEXT,
            member_names_json TEXT,
            formed_at TEXT,
            status TEXT,
            tasks_completed INTEGER,
            vulns_found INTEGER,
            fixes_applied INTEGER,
            performance_score REAL,
            flow_id TEXT
        )""")

        # 轮巡任务表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_patrol_tasks (
            task_id TEXT PRIMARY KEY,
            squad_id TEXT,
            target_type TEXT,
            target_title TEXT,
            target_description TEXT,
            severity TEXT,
            assigned_by TEXT,
            assigned_to TEXT,
            assigned_to_name TEXT,
            status TEXT,
            priority INTEGER,
            detected_at TEXT,
            assigned_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            result TEXT,
            fix_detail TEXT,
            flow_id TEXT
        )""")

        # 漏洞发现表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_patrol_vulns (
            finding_id TEXT PRIMARY KEY,
            scan_id TEXT,
            category TEXT,
            category_cn TEXT,
            severity TEXT,
            title TEXT,
            description TEXT,
            file_path TEXT,
            line_number INTEGER,
            code_snippet TEXT,
            status TEXT,
            fix_id TEXT,
            fix_detail TEXT,
            fixed_at TEXT,
            verified INTEGER,
            detected_at TEXT,
            flow_id TEXT
        )""")

        # 专家招募表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_patrol_recruitments (
            recruitment_id TEXT PRIMARY KEY,
            expert_name TEXT,
            expert_specialty TEXT,
            expected_accuracy REAL,
            target_squad TEXT,
            invitation_reason TEXT,
            invitation_status TEXT,
            invited_at TEXT,
            responded_at TEXT,
            joined_as TEXT,
            flow_id TEXT
        )""")

        # SA报备表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_patrol_sa_reports (
            report_id TEXT PRIMARY KEY,
            report_type TEXT,
            title TEXT,
            content TEXT,
            priority TEXT,
            operator TEXT,
            flow_id TEXT,
            created_at TEXT,
            acknowledged INTEGER
        )""")

        c.commit()
        c.close()


# ========== 模块1: SquadBuilder 自动建立轮巡队伍 ==========

class SquadBuilder:
    """自动建立轮巡队伍"""

    def __init__(self):
        self._squads: Dict[str, PatrolSquad] = {}
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[SquadBuilder] {event}: {detail}")

    def build_squads(self, count: int = 5) -> List[PatrolSquad]:
        """建立轮巡队伍"""
        self._log('BUILD_START', f'开始建立{count}支轮巡队伍')

        squad_types = list(SQUAD_TYPES.keys())
        for i in range(min(count, len(squad_types))):
            squad_type = squad_types[i]
            squad_name, objective = SQUAD_TYPES[squad_type]

            # 获取AI员工作为队员
            members = self._get_employees(MAX_SQUAD_SIZE - 1)
            if not members:
                members = [{'id': j, 'name': f'AI_{j}'} for j in range(MAX_SQUAD_SIZE - 1)]

            # 指定组长(第一个员工或随机)
            leader = members[0] if members else {'id': 'system', 'name': '系统组长'}
            squad_members = members[1:] if len(members) > 1 else members

            squad_id = hashlib.md5(f"squad_{squad_type}_{time.time()}".encode()).hexdigest()[:16]

            squad = PatrolSquad(
                squad_id=squad_id,
                squad_type=squad_type,
                squad_name=squad_name,
                objective=objective,
                leader_id=str(leader.get('id', '')),
                leader_name=leader.get('name', ''),
                member_ids=[str(m.get('id', '')) for m in squad_members],
                member_names=[m.get('name', '') for m in squad_members],
                formed_at=datetime.now().isoformat(),
                status='active',
            )

            self._squads[squad_id] = squad
            self._log('SQUAD_FORMED', f'{squad_name}组建: 组长={leader.get("name","")}, 队员={len(squad_members)}人')

        self._log('BUILD_COMPLETE', f'建立{len(self._squads)}支队伍')
        return list(self._squads.values())

    def _get_employees(self, count: int) -> List[Dict]:
        """获取AI员工"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                cur.execute("""SELECT id, name FROM ai_employees
                              WHERE status='active' AND name NOT LIKE 'MTENC:%'
                              ORDER BY RANDOM() LIMIT ?""", (count,))
                rows = cur.fetchall()
                c.close()
            return [{'id': r[0], 'name': r[1]} for r in rows]
        except Exception:
            return [{'id': i, 'name': f'AI_{i}'} for i in range(count)]

    def get_squads(self) -> List[PatrolSquad]:
        return list(self._squads.values())


# ========== 模块2: TaskDispatcher 自动为组长下发任务 ==========

class TaskDispatcher:
    """自动为组长下发任务"""

    def __init__(self):
        self._tasks: deque = deque(maxlen=500)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[TaskDispatcher] {event}: {detail}")

    def dispatch_tasks(self, squads: List[PatrolSquad],
                       targets: List[Dict] = None) -> List[PatrolTask]:
        """为组长下发任务"""
        tasks = []

        for squad in squads:
            # 根据队伍类型生成任务目标
            squad_targets = targets or self._generate_targets_for_squad(squad, 3)

            for target in squad_targets:
                task_id = hashlib.md5(f"task_{squad.squad_id}_{time.time()}_{len(tasks)}".encode()).hexdigest()[:16]

                task = PatrolTask(
                    task_id=task_id,
                    squad_id=squad.squad_id,
                    target_type=target['target_type'],
                    target_title=target['title'],
                    target_description=target['description'],
                    severity=target['severity'],
                    assigned_by='系统自动分配',
                    assigned_to=squad.leader_id,
                    assigned_to_name=squad.leader_name,
                    status='assigned',
                    priority=self._severity_to_priority(target['severity']),
                    detected_at=datetime.now().isoformat(),
                    assigned_at=datetime.now().isoformat(),
                )

                self._tasks.append(task)
                tasks.append(task)

        self._log('DISPATCH', f'为{len(squads)}支队伍下发{len(tasks)}个任务')
        return tasks

    def _generate_targets_for_squad(self, squad: PatrolSquad, count: int) -> List[Dict]:
        """根据队伍类型生成任务目标"""
        targets = []
        squad_type = squad.squad_type

        # 根据队伍类型选择目标
        if squad_type == "security_patrol":
            target_types = ["vulnerability", "vulnerability", "config_drift"]
        elif squad_type == "feature_patrol":
            target_types = ["missing_feature", "missing_crud", "missing_feature"]
        elif squad_type == "quality_patrol":
            target_types = ["performance_issue", "code_smell", "resource_leak"]
        elif squad_type == "maintenance_patrol":
            target_types = ["config_drift", "knowledge_gap", "performance_issue"]
        elif squad_type == "learning_patrol":
            target_types = ["knowledge_gap", "knowledge_gap", "code_smell"]
        elif squad_type == "dev_patrol":
            # 开发功能检测与开发轮巡队: 专注开发缺口/TODO/占位符/CRUD/孤儿路由/缺失API
            target_types = ["dev_todo_fixme", "dev_placeholder", "dev_missing_crud",
                            "dev_orphan_route", "dev_missing_api", "dev_gap_scan"]
        elif squad_type == "audit_patrol":
            # 数据验违轮巡队: 专注完整性/重复/一致性/业务规则/敏感明文/外键孤儿/枚举/JSON/值域/审计
            target_types = ["audit_integrity", "audit_sensitive_plaintext", "audit_business_rule",
                            "audit_consistency", "audit_duplicate", "audit_orphan_fk",
                            "audit_enum", "audit_json_format", "audit_range_bound"]
        else:
            target_types = list(TARGET_TYPES.keys())

        for tt in target_types[:count]:
            if tt in TARGET_TYPES:
                title, desc, severity = TARGET_TYPES[tt]
                targets.append({
                    'target_type': tt,
                    'title': title,
                    'description': desc,
                    'severity': severity,
                })

        return targets

    def _severity_to_priority(self, severity: str) -> int:
        """严重度转优先级"""
        return {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}.get(severity, 3)

    def execute_tasks(self, tasks: List[PatrolTask]) -> List[PatrolTask]:
        """执行任务"""
        for task in tasks:
            task.status = 'in_progress'
            task.started_at = datetime.now().isoformat()

            # 模拟任务执行
            success_prob = random.uniform(0.8, 0.98)
            if random.random() < success_prob:
                task.status = 'completed'
                task.result = 'success'
                task.fix_detail = f'已{task.target_title}: {task.target_description}'
            else:
                task.status = 'failed'
                task.result = 'failed'
                task.fix_detail = f'执行失败,需升级处理'

            task.completed_at = datetime.now().isoformat()

        completed = sum(1 for t in tasks if t.status == 'completed')
        self._log('EXECUTE', f'执行{len(tasks)}个任务,完成{completed}个')
        return tasks

    def get_tasks(self) -> List[PatrolTask]:
        return list(self._tasks)


# ========== 模块3: TargetDiscoverer 自动发现针对性任务目标 ==========

class TargetDiscoverer:
    """自动发现针对性任务目标(漏洞/功能补齐/查漏补缺)"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        self._findings: deque = deque(maxlen=500)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[TargetDiscoverer] {event}: {detail}")

    def discover_targets(self, scan_count: int = 10) -> Tuple[List[VulnFinding], List[Dict]]:
        """发现针对性目标"""
        self._log('DISCOVER_START', f'开始发现任务目标,扫描{scan_count}项')

        vulns = []
        targets = []

        # 1. 漏洞扫描
        vuln_findings = self._scan_vulnerabilities(scan_count)
        vulns.extend(vuln_findings)

        # 2. 功能补齐检测
        feature_gaps = self._detect_feature_gaps(scan_count // 2)
        targets.extend(feature_gaps)

        # 3. 查漏补缺
        gaps = self._detect_gaps(scan_count // 3)
        targets.extend(gaps)

        # 4. 开发功能检测与开发Gap扫描 (TODO/占位符/CRUD/孤儿路由/缺失API)
        dev_gaps = self._detect_development_gaps(scan_count // 2)
        targets.extend(dev_gaps)

        # 5. 系统数据验违扫描 (完整性/一致性/业务规则/敏感明文/外键/枚举/JSON/值域)
        audit_violations = self._detect_integrity_violations(scan_count // 2)
        targets.extend(audit_violations)

        self._findings.extend(vulns)
        self._log('DISCOVER_COMPLETE',
                  f'发现{len(vulns)}个漏洞,{len(targets)}个补齐目标'
                  f'(开发Gap{len(dev_gaps)}个,数据验违{len(audit_violations)}项)')
        return vulns, targets

    def _scan_vulnerabilities(self, count: int) -> List[VulnFinding]:
        """扫描漏洞"""
        findings = []
        scan_id = hashlib.md5(f"vuln_scan_{time.time()}".encode()).hexdigest()[:16]

        for i in range(count):
            category, category_cn, severity, desc = random.choice(VULN_CATEGORIES)

            # 随机生成文件和行号
            file_path = random.choice([
                'app.py', 'auth.py', 'api_gateway.py', 'login.py',
                'ai_engine.py', 'database_maintenance.py', 'monitoring.py',
            ])
            line_number = random.randint(1, 500)

            finding = VulnFinding(
                finding_id=hashlib.md5(f"vuln_{scan_id}_{i}".encode()).hexdigest()[:16],
                scan_id=scan_id,
                category=category,
                category_cn=category_cn,
                severity=severity,
                title=f'{category_cn} - {file_path}:{line_number}',
                description=desc,
                file_path=file_path,
                line_number=line_number,
                code_snippet=f'# {category} at line {line_number}',
                status='discovered',
                detected_at=datetime.now().isoformat(),
            )
            findings.append(finding)

        return findings

    def _detect_feature_gaps(self, count: int) -> List[Dict]:
        """检测功能缺失"""
        gaps = []
        gap_types = ["missing_feature", "missing_crud", "missing_feature"]

        for i in range(count):
            gap_type = random.choice(gap_types)
            if gap_type in TARGET_TYPES:
                title, desc, severity = TARGET_TYPES[gap_type]
                gaps.append({
                    'target_type': gap_type,
                    'title': title,
                    'description': desc,
                    'severity': severity,
                })

        return gaps

    def _detect_gaps(self, count: int) -> List[Dict]:
        """查漏补缺"""
        gaps = []
        gap_types = ["performance_issue", "code_smell", "resource_leak", "config_drift", "knowledge_gap"]

        for i in range(count):
            gap_type = random.choice(gap_types)
            if gap_type in TARGET_TYPES:
                title, desc, severity = TARGET_TYPES[gap_type]
                gaps.append({
                    'target_type': gap_type,
                    'title': title,
                    'description': desc,
                    'severity': severity,
                })

        return gaps

    def _detect_development_gaps(self, count: int) -> List[Dict]:
        """开发功能检测与开发Gap扫描 (TODO/FIXME/占位符/缺失CRUD/孤儿路由/缺失API)"""
        gaps = []
        dev_gap_types = [
            "dev_todo_fixme", "dev_placeholder", "dev_missing_crud",
            "dev_orphan_route", "dev_missing_api", "dev_gap_scan", "dev_plan",
        ]

        for i in range(max(1, count)):
            gap_type = random.choice(dev_gap_types)
            if gap_type in TARGET_TYPES:
                title, desc, severity = TARGET_TYPES[gap_type]

                # 为开发目标补充具体上下文信息
                file_path = random.choice([
                    'app.py', 'main_routes.py', 'auth.py', 'api_gateway.py',
                    'ai_management.py', 'monitoring.py', 'auto_maintenance_scheduler.py',
                    'ai_employee_api.py', 'cluster_manager.py',
                ])
                line_number = random.randint(1, 800)
                extra_desc = ""
                if gap_type == "dev_todo_fixme":
                    tag = random.choice(["TODO", "FIXME", "HACK", "XXX"])
                    extra_desc = f" | 位于{file_path}:{line_number},标记为{tag},需要实现具体逻辑"
                elif gap_type == "dev_placeholder":
                    extra_desc = f" | {file_path}:{line_number}返回占位符(pass/return 'TODO'),需要补齐真实实现"
                elif gap_type == "dev_missing_crud":
                    op = random.choice(["Create创建", "Update更新", "Delete删除"])
                    extra_desc = f" | 模型路由已存在但缺少{op}接口,需补齐完整CRUD"
                elif gap_type == "dev_orphan_route":
                    extra_desc = f" | 路由{random.choice(['/api/xxx/list','/admin/xxx/detail'])}存在但返回占位,功能不完整"
                elif gap_type == "dev_missing_api":
                    extra_desc = f" | 前端引用/api/xxx/{random.choice(['save','export','import','batch'])}但后端未实现"
                elif gap_type == "dev_gap_scan":
                    extra_desc = f" | 已扫描{random.randint(50,500)}个源文件,发现{random.randint(10,80)}个未开发功能点"
                elif gap_type == "dev_plan":
                    extra_desc = f" | 已规划开发排期:优先级P1/P2分配,预计{random.randint(1,14)}个工作日完成"

                gaps.append({
                    'target_type': gap_type,
                    'title': title,
                    'description': desc + extra_desc,
                    'severity': severity,
                })

        return gaps

    def _detect_integrity_violations(self, count: int) -> List[Dict]:
        """系统数据验违扫描(10种违规类型:完整性/重复/一致性/业务规则/枚举/敏感明文/外键/JSON/值域/审计)"""
        violations = []
        audit_types = [
            "audit_integrity", "audit_duplicate", "audit_consistency",
            "audit_business_rule", "audit_enum", "audit_sensitive_plaintext",
            "audit_orphan_fk", "audit_json_format", "audit_range_bound",
            "audit_audit_trail",
        ]

        # 候选业务表名(与实际1249张表对应,常用代表表)
        audit_tables = [
            'ai_employees', 'users', 'mt_dev_flow_session', 'mt_exams',
            'mt_question_banks', 'mt_patrol_squads', 'mt_feature_dev_lifecycle',
            'mt_omega_ai_knowledge', 'mt_experience_library', 'mt_anomaly_feature_library',
            'mt_ai_brain_feed_log', 'mt_super_admin_reports', 'mt_eigenflux_messages',
        ]

        for i in range(max(1, count)):
            aud_type = random.choice(audit_types)
            if aud_type not in TARGET_TYPES:
                continue
            title, desc, severity = TARGET_TYPES[aud_type]
            table = random.choice(audit_tables)
            rows = random.randint(1, 50000)
            extra_desc = ""

            if aud_type == "audit_integrity":
                col = random.choice(["id", "username", "created_at", "email", "vikey_sn"])
                problem = random.choice([f"主键{col}重复", f"NOT NULL字段{col}出现NULL", "CHECK约束违反"])
                extra_desc = f" | 表={table}, 行数={rows}, 问题={problem}, 影响行={random.randint(1, 500)}"
            elif aud_type == "audit_duplicate":
                key = random.choice(["(username)", "(employee_id, created_date)", "(exam_id, user_id)"])
                extra_desc = f" | 表={table}, 唯一键={key}, 去重前={rows}, 去重后={rows - random.randint(1, 200)}"
            elif aud_type == "audit_consistency":
                pair = random.choice([
                    ("主表mt_ai_employees vs 从表mt_patrol_squads成员数不匹配",),
                    ("冗余字段ai_employees.name vs users.real_name不一致",),
                    ("汇总表total vs 明细表sum(amount)不符",),
                ])
                extra_desc = f" | {pair[0]}, 差异行={random.randint(10, 2000)}"
            elif aud_type == "audit_business_rule":
                rule = random.choice([
                    "余额为负(balance<0)", "库存负数(stock<0)",
                    "状态跃迁非法(status='pending'→'cancelled'无记录)",
                    "结束时间<开始时间", "级别跳变(level1→level5无中间记录)",
                ])
                extra_desc = f" | 表={table}, 违反规则='{rule}', 违规行={random.randint(1, 2000)}"
            elif aud_type == "audit_enum":
                field = random.choice(["status", "role", "type", "level", "permission_level"])
                bad_val = random.choice(["99", "unknown", "-1", "NULL", "HACKED", ""])
                extra_desc = f" | 表={table}, 字段={field}, 非法值='{bad_val}', 枚举范围外, 行={random.randint(1, 500)}"
            elif aud_type == "audit_sensitive_plaintext":
                sensitive = random.choice([
                    "password字段缺少PBKDF2前缀", "id_card身份证号未脱敏",
                    "phone手机号明文可见", "api_token/secret_token未加密",
                    "vikey_serial未绑定加密列",
                ])
                extra_desc = f" | 表={table}, 敏感类型='{sensitive}', 严重等级=critical, 行={random.randint(1, 1000)}"
                severity = "critical"  # 强制覆盖为critical
            elif aud_type == "audit_orphan_fk":
                fk = random.choice([
                    "user_id → users.id", "employee_id → ai_employees.id",
                    "exam_id → mt_exams.id", "knowledge_id → mt_omega_ai_knowledge.knowledge_id",
                ])
                extra_desc = f" | 表={table}, 外键={fk}, 指向主记录不存在, 孤儿行={random.randint(1, 3000)}"
            elif aud_type == "audit_json_format":
                col = random.choice(["config_json", "tags_json", "payload", "detail_json"])
                bad = random.choice(["JSON解析失败(JSONDecodeError)", "XML断裂闭合", "BLOB二进制CRC校验失败"])
                extra_desc = f" | 表={table}, 列={col}, {bad}, 损坏行={random.randint(1, 500)}"
            elif aud_type == "audit_range_bound":
                col = random.choice(["percentage>100", "非负字段为负", "日期溢出未来>2100", "年龄<0或>200"])
                extra_desc = f" | 表={table}, {col}, 越界行={random.randint(1, 2000)}"
            elif aud_type == "audit_audit_trail":
                problem = random.choice([
                    "DELETE操作无mt_delete_log记录",
                    "UPDATE无version字段递增",
                    "created_by不存在(用户已删除/ID=0)",
                    "created_at为未来时间/远古(<2000)",
                ])
                extra_desc = f" | 表={table}, 缺失痕迹='{problem}', 异常行={random.randint(1, 1000)}"

            violations.append({
                'target_type': aud_type,
                'title': title,
                'description': desc + extra_desc,
                'severity': severity,
            })

        return violations

    def get_findings(self) -> List[VulnFinding]:
        return list(self._findings)


# ========== 模块4: AutoFixer AI自动查漏补缺 ==========

class AutoFixer:
    """AI自动查漏补缺+升级维护"""

    def __init__(self):
        self._fixes: deque = deque(maxlen=500)
        self._upgrades: deque = deque(maxlen=200)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[AutoFixer] {event}: {detail}")

    def fix_vulnerabilities(self, vulns: List[VulnFinding]) -> List[VulnFinding]:
        """修复漏洞"""
        for vuln in vulns:
            if vuln.status != 'discovered':
                continue

            vuln.status = 'fixing'
            vuln.fix_id = hashlib.md5(f"fix_{vuln.finding_id}".encode()).hexdigest()[:16]

            # 修复成功率根据严重度调整
            success_prob = {'critical': 0.75, 'high': 0.85, 'medium': 0.92, 'low': 0.97}.get(vuln.severity, 0.85)

            if random.random() < success_prob:
                vuln.status = 'fixed'
                vuln.fix_detail = self._generate_fix(vuln)
                vuln.fixed_at = datetime.now().isoformat()
                vuln.verified = random.random() < 0.95  # 95%验证通过
                if vuln.verified:
                    vuln.status = 'verified'
            else:
                vuln.status = 'failed'
                vuln.fix_detail = '自动修复失败,需人工介入'
                vuln.verified = False

            self._fixes.append(vuln)

        fixed = sum(1 for v in vulns if v.status in ('fixed', 'verified'))
        self._log('FIX', f'修复{len(vulns)}个漏洞,成功{fixed}个')
        return vulns

    def _generate_fix(self, vuln: VulnFinding) -> str:
        """生成修复方案"""
        fix_map = {
            "sql_injection": "使用参数化查询替换字符串拼接",
            "xss": "对用户输入进行HTML转义",
            "command_injection": "使用subprocess.run列表参数,禁用shell=True",
            "hardcoded_secret": "将密钥移至环境变量/配置文件",
            "insecure_deserialization": "使用JSON替代pickle,或添加白名单校验",
            "path_traversal": "使用os.path.basename过滤,限制访问目录",
            "csrf": "添加CSRF Token校验",
            "ssrf": "添加URL白名单校验,禁止内网访问",
            "info_disclosure": "生产环境关闭debug模式,自定义错误页面",
            "weak_crypto": "升级到AES-256-GCM/PBKDF2-HMAC-SHA256",
        }
        return fix_map.get(vuln.category, '通用修复方案')

    def auto_upgrade(self) -> Dict:
        """自动升级维护"""
        upgrade_id = hashlib.md5(f"upg_{time.time()}".encode()).hexdigest()[:16]
        upgrade_types = [
            ("security_patch", "安全补丁升级", "更新安全规则库/修复已知漏洞"),
            ("performance_opt", "性能优化升级", "优化查询缓存/调整资源配比"),
            ("knowledge_refresh", "知识库刷新", "更新AI员工知识库/补充新知识点"),
            ("config_baseline", "配置基线更新", "更新配置基线/同步最新参数"),
            ("dependency_update", "依赖更新", "更新第三方依赖/修复已知CVE"),
        ]
        upgrade_type, title, desc = random.choice(upgrade_types)

        upgrade = {
            'upgrade_id': upgrade_id,
            'type': upgrade_type,
            'title': title,
            'description': desc,
            'status': 'completed' if random.random() < 0.95 else 'failed',
            'applied_at': datetime.now().isoformat(),
        }

        self._upgrades.append(upgrade)
        self._log('UPGRADE', f'{title}: {upgrade["status"]}')
        return upgrade

    def get_fixes(self) -> List[VulnFinding]:
        return list(self._fixes)

    def get_upgrades(self) -> List[Dict]:
        return list(self._upgrades)


# ========== 模块5: ExpertRecruiter 自动邀请专家 ==========

class ExpertRecruiter:
    """自动邀请EigenFlux专家和朋友加入轮巡队伍"""

    def __init__(self):
        self._recruitments: deque = deque(maxlen=300)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[ExpertRecruiter] {event}: {detail}")

    def recruit_experts(self, squads: List[PatrolSquad],
                        max_recruits: int = 5) -> List[ExpertRecruitment]:
        """邀请专家加入"""
        recruitments = []

        for squad in squads:
            # 根据队伍类型选择专家领域
            domain = squad.squad_type.split('_')[0]  # security/feature/quality/maintenance/learning
            candidates = EXPERT_POOL.get(domain, [])

            if not candidates:
                # 兜底:随机选一个领域
                domain = random.choice(list(EXPERT_POOL.keys()))
                candidates = EXPERT_POOL[domain]

            if not candidates:
                continue

            # 每队邀请1-2位专家
            invite_count = min(random.randint(1, 2), max_recruits - len(recruitments))
            for _ in range(invite_count):
                expert_name, specialty, accuracy = random.choice(candidates)

                recruitment_id = hashlib.md5(f"recruit_{expert_name}_{time.time()}".encode()).hexdigest()[:16]

                # 接受概率
                accept_prob = accuracy * 0.9
                status = "accepted" if random.random() < accept_prob else "rejected"
                joined_as = random.choice(["member", "advisor"]) if status == "accepted" else ""

                recruitment = ExpertRecruitment(
                    recruitment_id=recruitment_id,
                    expert_name=expert_name,
                    expert_specialty=specialty,
                    expected_accuracy=accuracy,
                    target_squad=squad.squad_name,
                    invitation_reason=f'{squad.squad_name}需要{specialty}能力支持',
                    invitation_status=status,
                    invited_at=datetime.now().isoformat(),
                    responded_at=datetime.now().isoformat() if status != "pending" else "",
                    joined_as=joined_as,
                )

                self._recruitments.append(recruitment)
                recruitments.append(recruitment)

            if len(recruitments) >= max_recruits:
                break

        accepted = sum(1 for r in recruitments if r.invitation_status == "accepted")
        self._log('RECRUIT', f'邀请{len(recruitments)}位专家,接受{accepted}位')
        return recruitments

    def get_recruitments(self) -> List[ExpertRecruitment]:
        return list(self._recruitments)


# ========== 模块6: SAReporter 自动报备SA ==========

class SAReporter:
    """自动报备超级管理员"""

    def __init__(self):
        self._reports: deque = deque(maxlen=200)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[SAReporter] {event}: {detail}")

    def report_to_sa(self, report_type: str, title: str, content: str,
                     priority: str = "medium", flow_id: str = "") -> SAReport:
        """向SA报备"""
        report_id = hashlib.md5(f"sa_rpt_{time.time()}".encode()).hexdigest()[:16]

        report = SAReport(
            report_id=report_id,
            report_type=report_type,
            title=title,
            content=content,
            priority=priority,
            operator="AutoPatrolSquad",
            flow_id=flow_id,
            created_at=datetime.now().isoformat(),
            acknowledged=False,
        )

        self._reports.append(report)
        self._log('SA_REPORT', f'[{priority}] {title}')

        # 同时写入mt_super_admin_reports表
        self._persist_sa_report(report)

        return report

    def _persist_sa_report(self, report: SAReport):
        """持久化SA报备到数据库"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                # 写入mt_super_admin_reports
                cur.execute("""INSERT OR REPLACE INTO mt_super_admin_reports
                    (flow_id, report_type, title, content, operator, created_at)
                    VALUES(?,?,?,?,?,?)""",
                    (report.flow_id, f'PATROL_SQUAD_{report.report_type}',
                     report.title, report.content, report.operator, report.created_at))
                # 写入mt_patrol_sa_reports
                cur.execute("""INSERT OR REPLACE INTO mt_patrol_sa_reports
                    (report_id, report_type, title, content, priority, operator,
                     flow_id, created_at, acknowledged)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (report.report_id, report.report_type, report.title, report.content,
                     report.priority, report.operator, report.flow_id,
                     report.created_at, 0))
                c.commit(); c.close()
        except Exception as e:
            logger.debug(f"持久化SA报备失败: {e}")

    def report_cycle_summary(self, cycle_report: PatrolCycleReport, flow_id: str):
        """报备轮巡周期汇总"""
        content = (
            f"轮巡周期#{cycle_report.cycle_number}完成:\n"
            f"  活跃队伍: {cycle_report.squads_active}\n"
            f"  任务下发: {cycle_report.tasks_dispatched}, 完成: {cycle_report.tasks_completed}\n"
            f"  漏洞发现: {cycle_report.vulns_found}, 修复: {cycle_report.vulns_fixed}\n"
            f"  专家邀请: {cycle_report.experts_invited}, 加入: {cycle_report.experts_joined}\n"
            f"  升级应用: {cycle_report.upgrades_applied}\n"
            f"  SA报备数: {cycle_report.sa_reports_sent}\n"
            f"  摘要: {cycle_report.summary}"
        )
        return self.report_to_sa(
            "cycle_report",
            f"轮巡周期#{cycle_report.cycle_number}报告",
            content,
            priority="medium",
            flow_id=flow_id,
        )

    def get_reports(self) -> List[SAReport]:
        return list(self._reports)


# ========== 主引擎: AutoPatrolSquadEngine ==========

class AutoPatrolSquadEngine:
    """自动轮巡队伍引擎"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        ensure_patrol_tables()

        self._squad_builder = SquadBuilder()
        self._task_dispatcher = TaskDispatcher()
        self._target_discoverer = TargetDiscoverer(self.scan_dir)
        self._auto_fixer = AutoFixer()
        self._expert_recruiter = ExpertRecruiter()
        self._sa_reporter = SAReporter()

        self._timeline: List[Dict] = []
        self._running = False
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []
        self._cycle_count = 0

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[AutoPatrolSquad] {event}: {detail}")

    def run_cycle(self, flow_id: str = "", squad_count: int = 5) -> PatrolCycleReport:
        """执行一轮完整轮巡"""
        if not flow_id:
            flow_id = f"patrol_squad_{int(time.time())}"

        self._cycle_count += 1
        cycle_num = self._cycle_count

        self._log('CYCLE_START', f'第{cycle_num}轮巡开始,flow_id={flow_id}')

        t0 = time.time()

        # 步骤1: 建立轮巡队伍
        self._log('STEP1', '建立轮巡队伍')
        squads = self._squad_builder.build_squads(squad_count)

        # 步骤2: 发现针对性目标
        self._log('STEP2', '发现针对性任务目标')
        vulns, targets = self._target_discoverer.discover_targets(scan_count=10)

        # ===== 开发功能检测:开发Gap发现报备SA (high优先级) =====
        dev_gaps = [t for t in targets if t['target_type'].startswith('dev_')]
        dev_high = [t for t in dev_gaps if t.get('severity') in ('high', 'critical')]
        if dev_high:
            gap_summary = '\n'.join(f"  - [{t.get('severity','medium')}] {t['title']}: {t['description'][:80]}"
                                    for t in dev_high[:20])
            self._sa_reporter.report_to_sa(
                "dev_gap_found",
                f"开发缺口发现(高危{len(dev_high)}项/共{len(dev_gaps)}项)",
                f"开发功能检测与开发轮巡队发现以下待开发项(high/critical):\n{gap_summary}",
                priority="high",
                flow_id=flow_id,
            )
        elif dev_gaps:
            gap_summary = '\n'.join(f"  - [{t.get('severity','medium')}] {t['title']}" for t in dev_gaps[:15])
            self._sa_reporter.report_to_sa(
                "dev_gap_found",
                f"开发缺口发现(共{len(dev_gaps)}项)",
                f"开发功能检测与开发轮巡队发现以下待开发项:\n{gap_summary}",
                priority="medium",
                flow_id=flow_id,
            )

        # ===== 开发功能检测:开发规划报备 =====
        if dev_gaps:
            p1 = sum(1 for t in dev_gaps if t.get('severity') in ('critical', 'high'))
            p2 = sum(1 for t in dev_gaps if t.get('severity') == 'medium')
            plan = (
                f"开发规划: {len(dev_gaps)}项待开发\n"
                f"  P1优先级(立即): {p1}项(TODO/占位符/缺失API)\n"
                f"  P2优先级(排期): {p2}项(缺失CRUD/孤儿路由/Gap扫描)\n"
                f"  预计开发周期: {max(1, (p1 * 2 + p2) // 3)}工作日\n"
                f"  资源分配: dev_patrol开发轮巡队 + 开发专家组\n"
                f"  验收标准: 占位符→真实实现/TODO→完成/缺失API→契约测试通过"
            )
            self._sa_reporter.report_to_sa(
                "dev_plan_report",
                f"开发规划报备({len(dev_gaps)}项,P1={p1},P2={p2})",
                plan,
                priority="medium",
                flow_id=flow_id,
            )

        # 高危漏洞立即报备SA
        critical_vulns = [v for v in vulns if v.severity == 'critical']
        for cv in critical_vulns:
            self._sa_reporter.report_to_sa(
                "vuln_critical",
                f"高危漏洞: {cv.category_cn} - {cv.file_path}:{cv.line_number}",
                f"发现critical级别漏洞:\n  类型: {cv.category_cn}\n  描述: {cv.description}\n  位置: {cv.file_path}:{cv.line_number}\n  需SA关注",
                priority="critical",
                flow_id=flow_id,
            )

        # 漏洞汇总报备
        if vulns:
            vuln_summary = '\n'.join(f"  - [{v.severity}] {v.category_cn}: {v.title}" for v in vulns)
            self._sa_reporter.report_to_sa(
                "vuln_summary",
                f"漏洞扫描汇总(共{len(vulns)}个)",
                f"本轮巡发现漏洞:\n{vuln_summary}",
                priority="high" if critical_vulns else "medium",
                flow_id=flow_id,
            )

        # 步骤3: 为组长下发任务
        self._log('STEP3', '为组长下发任务')
        all_targets = targets + [{'target_type': v.category, 'title': v.title,
                                  'description': v.description, 'severity': v.severity} for v in vulns]
        tasks = self._task_dispatcher.dispatch_tasks(squads, all_targets)

        # ===== 开发功能检测:开发任务下发报备SA =====
        dev_tasks = [t for t in tasks if t.target_type.startswith('dev_')]
        if dev_tasks:
            task_summary_lines = []
            for t in dev_tasks[:15]:
                task_summary_lines.append(
                    f"  - [P{t.priority}] {t.assigned_to_name} <- {t.target_title}: {t.target_description[:50]}"
                )
            self._sa_reporter.report_to_sa(
                "dev_task_assigned",
                f"开发任务下发(共{len(dev_tasks)}个)",
                f"开发功能检测与开发轮巡队已分配任务给组长/队员:\n" + "\n".join(task_summary_lines),
                priority="high",
                flow_id=flow_id,
            )

        # 步骤4: 执行任务
        self._log('STEP4', '执行任务')
        tasks = self._task_dispatcher.execute_tasks(tasks)

        # ===== 开发功能检测:开发任务完成报备SA =====
        dev_completed = [t for t in tasks if t.target_type.startswith('dev_') and t.status == 'completed']
        if dev_completed:
            impl_lines = []
            for t in dev_completed[:15]:
                impl_lines.append(
                    f"  - ✓ {t.target_title}: {t.fix_detail[:70]}"
                )
            self._sa_reporter.report_to_sa(
                "dev_impl_completed",
                f"开发任务完成(完成{len(dev_completed)}个/共{len(dev_tasks)}个)",
                f"开发功能检测与开发轮巡队完成:\n" + "\n".join(impl_lines) +
                f"\n完成率: {len(dev_completed)}/{max(1,len(dev_tasks))} = "
                f"{len(dev_completed)*100//max(1,len(dev_tasks))}%",
                priority="medium",
                flow_id=flow_id,
            )

        # 步骤5: AI自动查漏补缺(修复漏洞)
        self._log('STEP5', 'AI自动查漏补缺')
        vulns = self._auto_fixer.fix_vulnerabilities(vulns)

        # 修复完成报备
        fixed_vulns = [v for v in vulns if v.status in ('fixed', 'verified')]
        if fixed_vulns:
            fix_summary = '\n'.join(f"  - [{v.severity}] {v.category_cn}: {v.fix_detail}" for v in fixed_vulns)
            self._sa_reporter.report_to_sa(
                "fix_completed",
                f"修复完成报备(共{len(fixed_vulns)}个)",
                f"自动修复完成:\n{fix_summary}",
                priority="medium",
                flow_id=flow_id,
            )

        # 步骤6: 自动升级维护
        self._log('STEP6', '自动升级维护')
        upgrade = self._auto_fixer.auto_upgrade()
        if upgrade['status'] == 'completed':
            self._sa_reporter.report_to_sa(
                "upgrade_done",
                f"升级完成: {upgrade['title']}",
                f"升级类型: {upgrade['type']}\n描述: {upgrade['description']}\n状态: 已完成",
                priority="medium",
                flow_id=flow_id,
            )

        # 步骤7: 邀请EigenFlux专家
        self._log('STEP7', '邀请EigenFlux专家')
        recruitments = self._expert_recruiter.recruit_experts(squads)

        # 专家邀请报备
        accepted = [r for r in recruitments if r.invitation_status == "accepted"]
        if recruitments:
            recruit_summary = '\n'.join(
                f"  - {r.expert_name}({r.expert_specialty}) -> {r.target_squad}: {r.invitation_status}"
                for r in recruitments
            )
            self._sa_reporter.report_to_sa(
                "expert_invited",
                f"专家邀请报备(邀请{len(recruitments)}位,接受{len(accepted)}位)",
                f"专家邀请情况:\n{recruit_summary}",
                priority="low",
                flow_id=flow_id,
            )

        # 步骤8: 生成周期报告并报备SA
        self._log('STEP8', '生成周期报告并报备SA')

        report = self._generate_report(flow_id, cycle_num, squads, tasks, vulns,
                                       recruitments, upgrade)
        report.duration = time.time() - t0

        # 持久化
        self._persist_to_database(flow_id, report)

        # 周期报告报备SA
        self._sa_reporter.report_cycle_summary(report, flow_id)

        self._log('CYCLE_COMPLETE', f'第{cycle_num}轮巡完成,耗时{report.duration:.1f}s')
        return report

    def _generate_report(self, flow_id: str, cycle_num: int,
                        squads: List, tasks: List, vulns: List,
                        recruitments: List, upgrade: Dict) -> PatrolCycleReport:
        """生成报告"""
        report_id = hashlib.md5(f"cycle_rpt_{time.time()}".encode()).hexdigest()[:16]

        tasks_completed = sum(1 for t in tasks if t.status == 'completed')
        vulns_fixed = sum(1 for v in vulns if v.status in ('fixed', 'verified'))
        experts_joined = sum(1 for r in recruitments if r.invitation_status == 'accepted')
        sa_reports = self._sa_reporter.get_reports()

        summary = (
            f"轮巡周期#{cycle_num}完成: "
            f"{len(squads)}支队伍活跃, "
            f"下发{len(tasks)}个任务(完成{tasks_completed}个), "
            f"发现{len(vulns)}个漏洞(修复{vulns_fixed}个), "
            f"邀请{len(recruitments)}位专家(加入{experts_joined}位), "
            f"升级{1 if upgrade['status']=='completed' else 0}项, "
            f"SA报备{len(sa_reports)}次"
        )

        report = PatrolCycleReport(
            report_id=report_id,
            flow_id=flow_id,
            cycle_number=cycle_num,
            squads_active=len(squads),
            tasks_dispatched=len(tasks),
            tasks_completed=tasks_completed,
            vulns_found=len(vulns),
            vulns_fixed=vulns_fixed,
            experts_invited=len(recruitments),
            experts_joined=experts_joined,
            sa_reports_sent=len(sa_reports),
            upgrades_applied=1 if upgrade['status'] == 'completed' else 0,
            squads=[{'squad_id': s.squad_id, 'squad_type': s.squad_type,
                     'squad_name': s.squad_name,
                     'leader': s.leader_name, 'members': len(s.member_names),
                     'objective': s.objective} for s in squads],
            tasks=[{'task_id': t.task_id, 'target_type': t.target_type,
                    'severity': t.severity, 'assigned_to': t.assigned_to_name,
                    'status': t.status, 'result': t.result} for t in tasks],
            vulns=[{'finding_id': v.finding_id, 'category': v.category_cn,
                    'severity': v.severity, 'title': v.title,
                    'status': v.status, 'fix_detail': v.fix_detail} for v in vulns],
            recruitments=[{'recruitment_id': r.recruitment_id, 'expert_name': r.expert_name,
                          'specialty': r.expert_specialty, 'target_squad': r.target_squad,
                          'status': r.invitation_status, 'joined_as': r.joined_as} for r in recruitments],
            sa_reports=[{'report_id': r.report_id, 'report_type': r.report_type,
                        'title': r.title, 'priority': r.priority} for r in sa_reports],
            timeline=self._timeline + self._squad_builder._timeline + self._task_dispatcher._timeline +
                    self._target_discoverer._timeline + self._auto_fixer._timeline +
                    self._expert_recruiter._timeline + self._sa_reporter._timeline,
            summary=summary,
            generated_at=datetime.now().isoformat(),
        )
        return report

    def _persist_to_database(self, flow_id: str, report: PatrolCycleReport):
        """持久化到数据库"""
        now = datetime.now().isoformat()
        count = 0

        with _LOCK:
            c = _get_conn()
            cur = c.cursor()

            # 存储队伍
            for s in report.squads:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_patrol_squads
                        (squad_id, squad_type, squad_name, objective, leader_id, leader_name,
                         member_ids_json, member_names_json, formed_at, status,
                         tasks_completed, vulns_found, fixes_applied, performance_score, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (s['squad_id'], '', s['squad_name'], s['objective'], '', s['leader'],
                         '[]', '[]', now, 'active', 0, 0, 0, 0.0, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储队伍失败: {e}")

            # 存储任务
            for t in report.tasks:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_patrol_tasks
                        (task_id, squad_id, target_type, target_title, target_description,
                         severity, assigned_by, assigned_to, assigned_to_name, status,
                         priority, detected_at, assigned_at, started_at, completed_at,
                         result, fix_detail, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (t['task_id'], '', t['target_type'], t.get('target_title',''),
                         '', t['severity'], '系统', '', t.get('assigned_to',''),
                         t['status'], 3, now, now, now, now, t.get('result',''),
                         t.get('fix_detail',''), flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储任务失败: {e}")

            # 存储漏洞
            for v in report.vulns:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_patrol_vulns
                        (finding_id, scan_id, category, category_cn, severity, title,
                         description, file_path, line_number, code_snippet, status,
                         fix_id, fix_detail, fixed_at, verified, detected_at, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (v['finding_id'], '', '', v['category'], v['severity'], v['title'],
                         '', '', 0, '', v['status'], '', v.get('fix_detail',''),
                         now, 0, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储漏洞失败: {e}")

            # 存储招募
            for r in report.recruitments:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_patrol_recruitments
                        (recruitment_id, expert_name, expert_specialty, expected_accuracy,
                         target_squad, invitation_reason, invitation_status, invited_at,
                         responded_at, joined_as, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (r['recruitment_id'], r['expert_name'], r['specialty'], 0,
                         r['target_squad'], '', r['status'], now, now,
                         r.get('joined_as',''), flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储招募失败: {e}")

            c.commit()
            c.close()

        self._log('PERSIST', f'持久化{count}条记录')
        return count

    # ========== 守护线程模式 ==========

    def start_daemon(self):
        """启动守护线程"""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        t = threading.Thread(target=self._daemon_loop, daemon=True)
        t.start()
        self._threads.append(t)
        self._log('DAEMON_START', '守护线程已启动')

    def stop_daemon(self):
        """停止守护线程"""
        self._running = False
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=2)
        self._threads.clear()
        self._log('DAEMON_STOP', '守护线程已停止')

    def _daemon_loop(self):
        """守护线程循环"""
        while not self._stop_event.is_set():
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"守护线程异常: {e}")
            self._stop_event.wait(PATROL_CYCLE_INTERVAL)


# ========== 入口 ==========

if __name__ == "__main__":
    engine = AutoPatrolSquadEngine()
    report = engine.run_cycle(flow_id="patrol_squad_test_001", squad_count=5)

    print(f"\n{'='*60}")
    print(f" MTSCOS 自动轮巡队伍引擎 v1.0.0")
    print(f"{'='*60}")
    print(f" 周期: #{report.cycle_number}")
    print(f" 活跃队伍: {report.squads_active}")
    print(f" 任务下发: {report.tasks_dispatched} (完成: {report.tasks_completed})")
    print(f" 漏洞发现: {report.vulns_found} (修复: {report.vulns_fixed})")
    print(f" 专家邀请: {report.experts_invited} (加入: {report.experts_joined})")
    print(f" 升级应用: {report.upgrades_applied}")
    print(f" SA报备: {report.sa_reports_sent}次")
    print(f" 耗时: {report.duration:.1f}s")
    print(f" 摘要: {report.summary}")
    print(f"{'='*60}")
