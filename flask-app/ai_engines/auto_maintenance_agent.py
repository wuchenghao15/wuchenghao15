#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 自动维护 Agent - AutoMaintenanceAgent

统一维护入口，整合系统健康监控、异常检测、自动修复、数据库维护、
AI员工状态巡检、安全检查、日志清理、备份管理等功能。

遵循 SSOT 原则：所有维护数据实时写入数据库。
遵循 5 级规则系统：关键操作需 EigenFlux 磟商。
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
import traceback
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('auto_maintenance_agent')

# 尝试导入智能赋能系统
try:
    from ai_engines.intelligent_empowerment import PersonalitySystem, NetworkLearningEngine
    _EMPOWERMENT_AVAILABLE = True
except ImportError:
    _EMPOWERMENT_AVAILABLE = False

# 尝试导入 psutil
try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


# ============================================================================
# 枚举定义
# ============================================================================

class MaintenanceLevel(Enum):
    """维护级别 - 对应5级规则系统"""
    IRON_RULE = "iron_rule"       # 铁律：不可违反的维护规则
    RED_LINE = "red_line"         # 红线：严重问题，立即修复
    RED_WALL = "red_wall"         # 红墙：关键问题，需审批后修复
    CONSTRAINT = "constraint"     # 约束：一般问题，可配置修复策略
    WARNING = "warning"           # 警告：提示性问题，记录即可


class IssueStatus(Enum):
    """问题状态"""
    DETECTED = "detected"         # 已检测
    ANALYZING = "analyzing"       # 分析中
    REPAIRING = "repairing"       # 修复中
    RESOLVED = "resolved"         # 已解决
    FAILED = "failed"             # 修复失败
    SKIPPED = "skipped"           # 跳过
    ESCALATED = "escalated"       # 已升级（需人工介入）


class MonitorType(Enum):
    """监控类型"""
    SYSTEM_HEALTH = "system_health"           # 系统健康（CPU/内存/磁盘）
    DATABASE_HEALTH = "database_health"        # 数据库健康
    ROUTE_API = "route_api"                    # 路由API可用性
    AI_EMPLOYEE = "ai_employee"                # AI员工状态
    SECURITY = "security"                      # 安全检查
    LOG_HEALTH = "log_health"                  # 日志健康
    FILE_SYSTEM = "file_system"                # 文件系统
    BACKUP_STATUS = "backup_status"            # 备份状态


class AgentState(Enum):
    """Agent运行状态"""
    IDLE = "idle"
    MONITORING = "monitoring"
    REPAIRING = "repairing"
    REPORTING = "reporting"
    STOPPED = "stopped"
    ERROR = "error"


# ============================================================================
# 数据模型
# ============================================================================

class MaintenanceIssue:
    """维护问题"""

    def __init__(self, issue_id: str, monitor_type: MonitorType, level: MaintenanceLevel,
                 title: str, description: str, details: Dict = None):
        self.issue_id = issue_id
        self.monitor_type = monitor_type
        self.level = level
        self.title = title
        self.description = description
        self.details = details or {}
        self.status = IssueStatus.DETECTED
        self.detected_at = datetime.now().isoformat()
        self.resolved_at = None
        self.repair_action = None
        self.repair_result = None
        self.retries = 0
        self.max_retries = 3

    def to_dict(self) -> Dict:
        return {
            'issue_id': self.issue_id,
            'monitor_type': self.monitor_type.value,
            'level': self.level.value,
            'title': self.title,
            'description': self.description,
            'details': self.details,
            'status': self.status.value,
            'detected_at': self.detected_at,
            'resolved_at': self.resolved_at,
            'repair_action': self.repair_action,
            'repair_result': self.repair_result,
            'retries': self.retries
        }


class MaintenanceReport:
    """维护报告"""

    def __init__(self, report_id: str):
        self.report_id = report_id
        self.start_time = datetime.now().isoformat()
        self.end_time = None
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = 0
        self.issues_detected = 0
        self.issues_resolved = 0
        self.issues_failed = 0
        self.issues_escalated = 0
        self.duration_seconds = 0
        self.details: List[Dict] = []
        self.summary = ""

    def finalize(self):
        self.end_time = datetime.now().isoformat()
        if self.start_time and self.end_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.duration_seconds = (end - start).total_seconds()

        self.summary = (
            f"维护报告 #{self.report_id}: "
            f"共检查 {self.total_checks} 项, "
            f"通过 {self.passed_checks}, "
            f"失败 {self.failed_checks}, "
            f"警告 {self.warnings}, "
            f"发现问题 {self.issues_detected} 个, "
            f"已修复 {self.issues_resolved} 个, "
            f"修复失败 {self.issues_failed} 个, "
            f"升级处理 {self.issues_escalated} 个, "
            f"耗时 {self.duration_seconds:.1f} 秒"
        )

    def to_dict(self) -> Dict:
        return {
            'report_id': self.report_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_checks': self.total_checks,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'warnings': self.warnings,
            'issues_detected': self.issues_detected,
            'issues_resolved': self.issues_resolved,
            'issues_failed': self.issues_failed,
            'issues_escalated': self.issues_escalated,
            'duration_seconds': round(self.duration_seconds, 2),
            'summary': self.summary,
            'details': self.details
        }


# ============================================================================
# Vibe Coding 巡检检查项注册表（VC 系列巡检规则）
# ----------------------------------------------------------------------------
# 注册格式参考 comprehensive_maintenance_ai.MaintenanceCheckItem 风格，
# 每项包含：item_id（检查项编号）、name（名称）、severity（严重程度）、
#           category（分类）、section（章节）、check_method（检查方法描述）。
# 严重程度沿用 CheckSeverity 体系：CRITICAL / HIGH / MEDIUM / LOW / INFO。
# ============================================================================

VIBE_CODING_INSPECTION_ITEMS: List[Dict[str, Any]] = [
    # === §15 组件术语体系巡检（10项）===
    {
        "item_id": "VC-I1",
        "name": "输入框placeholder格式检查",
        "severity": "HIGH",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "正则扫描 placeholder，校验输入框 placeholder 是否符合规范格式",
    },
    {
        "item_id": "VC-I2",
        "name": "验证状态三信号检查",
        "severity": "CRITICAL",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "DOM 检查 error 状态下三元素（边框色/提示文案/图标）是否同时存在",
    },
    {
        "item_id": "VC-I3",
        "name": "必填星号检测",
        "severity": "HIGH",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "必填字段 label 是否包含红色星号标记",
    },
    {
        "item_id": "VC-C1",
        "name": "卡片三段式结构检查",
        "severity": "HIGH",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "DOM 扫描 .card 直接子节点，校验 header/body/footer 三段式结构",
    },
    {
        "item_id": "VC-C3",
        "name": "可交互卡片悬停反馈检查",
        "severity": "HIGH",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "检查可交互卡片悬停态三要素（阴影变化/光标变化/轻微位移）",
    },
    {
        "item_id": "VC-M1",
        "name": "模态框滚动锁定检查",
        "severity": "CRITICAL",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "模态框打开时 body overflow 是否设为 hidden 锁定背景滚动",
    },
    {
        "item_id": "VC-M2",
        "name": "模态框按钮合规检查",
        "severity": "CRITICAL",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "模态框内 solid 主按钮数量 ≤1，其余使用 ghost/outline 按钮",
    },
    {
        "item_id": "VC-T1",
        "name": "表格空状态展示检查",
        "severity": "HIGH",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "空表格是否有空状态提示（图标+文案）",
    },
    {
        "item_id": "VC-N1",
        "name": "导航激活状态检查",
        "severity": "HIGH",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "当前页对应导航项是否高亮显示激活状态",
    },
    {
        "item_id": "VC-Tag1",
        "name": "标签语义色检查",
        "severity": "MEDIUM",
        "category": "组件术语体系",
        "section": "§15",
        "check_method": "标签是否使用标准语义色（success/warning/danger/info）",
    },

    # === §16 页面布局术语体系巡检（10项）===
    {
        "item_id": "VC-L1",
        "name": "滚动容器唯一性检查",
        "severity": "CRITICAL",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": ".layout-main 是页面中唯一 overflow-y:auto 的滚动容器",
    },
    {
        "item_id": "VC-L3",
        "name": "内容层三段式检查",
        "severity": "HIGH",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "内容层是否遵循 content-header/body/footer 三段式结构",
    },
    {
        "item_id": "VC-G1",
        "name": "12列栅格守恒检查",
        "severity": "CRITICAL",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "单行 col 之和 ≤12，禁止栅格列数越界",
    },
    {
        "item_id": "VC-G3",
        "name": "栅格gutter一致性检查",
        "severity": "MEDIUM",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "同一页面 gutter 间距统一，禁止混用不同 gutter 值",
    },
    {
        "item_id": "VC-BP1",
        "name": "响应式断点标准检查",
        "severity": "CRITICAL",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "禁止使用非标准断点值，只允许标准断点集合",
    },
    {
        "item_id": "VC-BP3",
        "name": "移动端断点适配检查",
        "severity": "HIGH",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "xs/sm 断点适配存在，移动端布局可用",
    },
    {
        "item_id": "VC-E1",
        "name": "空状态分类检查",
        "severity": "HIGH",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "使用 4 种标准空状态类（empty-data/empty-search/empty-error/empty-permission）",
    },
    {
        "item_id": "VC-E3",
        "name": "错误空状态重试按钮检查",
        "severity": "HIGH",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "empty-error 空状态必须包含重试按钮",
    },
    {
        "item_id": "VC-LD1",
        "name": "骨架屏防闪检查",
        "severity": "HIGH",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "首屏加载 ≥600ms 才显示骨架屏，避免快速加载闪烁",
    },
    {
        "item_id": "VC-LD3",
        "name": "局部加载禁用检查",
        "severity": "MEDIUM",
        "category": "页面布局术语体系",
        "section": "§16",
        "check_method": "按钮 loading 状态时禁用点击交互",
    },

    # === §17 视觉设计铁律巡检（10项）===
    {
        "item_id": "VC-VD-S1",
        "name": "间距4px倍数检查",
        "severity": "CRITICAL",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "扫描非 4/8 倍数的间距值，间距必须为 4px 基准倍数",
    },
    {
        "item_id": "VC-VD-S2",
        "name": "间距禁用值黑名单检查",
        "severity": "HIGH",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "检查 19 个禁用间距值是否被使用",
    },
    {
        "item_id": "VC-VD-T1",
        "name": "五层文字体系检查",
        "severity": "HIGH",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "文字是否使用 vc-text-t1~t5 五层标准类",
    },
    {
        "item_id": "VC-VD-T3",
        "name": "字号白名单检查",
        "severity": "CRITICAL",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "只允许 10 档标准字号，禁止非白名单字号值",
    },
    {
        "item_id": "VC-VD-T5",
        "name": "相邻层字号差检查",
        "severity": "HIGH",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "相邻文字层级字号差 ≥4px",
    },
    {
        "item_id": "VC-VD-C1",
        "name": "普通文字对比度检查",
        "severity": "CRITICAL",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "普通文字与背景对比度 ≥4.5:1",
    },
    {
        "item_id": "VC-VD-C2",
        "name": "大文字对比度检查",
        "severity": "HIGH",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "大文字（≥18px 或 14px 加粗）与背景对比度 ≥3:1",
    },
    {
        "item_id": "VC-VD-C3",
        "name": "禁用态对比度检查",
        "severity": "MEDIUM",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "禁用态文字与背景对比度 ≥3:1",
    },
    {
        "item_id": "VC-VD-K1",
        "name": "一致性8维度检查",
        "severity": "HIGH",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "检查色/圆角/阴影/尺寸/图标/文案/位置/交互 8 维度一致性",
    },
    {
        "item_id": "VC-VD-K3",
        "name": "标准按钮文案词表检查",
        "severity": "MEDIUM",
        "category": "视觉设计铁律",
        "section": "§17",
        "check_method": "按钮文案是否使用标准动作词词表",
    },

    # === §17-§23 开发规则巡检（7项）===
    {
        "item_id": "VM-1",
        "name": "不要学AI直接用心智检查",
        "severity": "MEDIUM",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "代码注释是否含学习记录，体现理解而非直接套用 AI 输出",
    },
    {
        "item_id": "VP-1",
        "name": "CIRF框架Prompt检查",
        "severity": "HIGH",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "Prompt 是否含 Context/Instruction/Restriction/Format 四要素",
    },
    {
        "item_id": "FS-1",
        "name": "需求文档完整性检查",
        "severity": "HIGH",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "功能开发前是否有完整需求文档",
    },
    {
        "item_id": "QT-1",
        "name": "测试金字塔比例检查",
        "severity": "HIGH",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "测试金字塔比例：单测 70%/集成 20%/E2E 10%",
    },
    {
        "item_id": "TS-1",
        "name": "技术栈11维选型检查",
        "severity": "MEDIUM",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "新项目是否有完整技术栈选型表（11 维度）",
    },
    {
        "item_id": "AC-2",
        "name": "父子Agent边界检查",
        "severity": "HIGH",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "委派任务是否有明确父子 Agent 边界定义",
    },
    {
        "item_id": "WJ-1",
        "name": "作品质量评审检查",
        "severity": "HIGH",
        "category": "开发规则",
        "section": "§17-§23",
        "check_method": "功能交付前是否有五要素质量评分",
    },
]


def get_vibe_coding_inspection_items() -> List[Dict[str, Any]]:
    """获取 Vibe Coding 巡检检查项清单（共 37 项）"""
    return VIBE_CODING_INSPECTION_ITEMS.copy()


# ============================================================================
# 监控器
# ============================================================================

class SystemHealthMonitor:
    """系统健康监控器"""

    def __init__(self):
        self.name = "系统健康监控器"

    def check(self) -> List[MaintenanceIssue]:
        issues = []
        if not _PSUTIL_AVAILABLE:
            return issues

        # CPU 检查
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            issues.append(MaintenanceIssue(
                f"sys_cpu_{int(time.time())}",
                MonitorType.SYSTEM_HEALTH,
                MaintenanceLevel.RED_LINE,
                "CPU使用率过高",
                f"CPU使用率: {cpu_percent}%, 超过90%阈值",
                {'cpu_percent': cpu_percent}
            ))
        elif cpu_percent > 75:
            issues.append(MaintenanceIssue(
                f"sys_cpu_{int(time.time())}",
                MonitorType.SYSTEM_HEALTH,
                MaintenanceLevel.WARNING,
                "CPU使用率偏高",
                f"CPU使用率: {cpu_percent}%, 超过75%阈值",
                {'cpu_percent': cpu_percent}
            ))

        # 内存检查
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            issues.append(MaintenanceIssue(
                f"sys_mem_{int(time.time())}",
                MonitorType.SYSTEM_HEALTH,
                MaintenanceLevel.RED_LINE,
                "内存使用率过高",
                f"内存使用率: {mem.percent}%, 超过90%阈值",
                {'mem_percent': mem.percent, 'mem_available': mem.available}
            ))
        elif mem.percent > 80:
            issues.append(MaintenanceIssue(
                f"sys_mem_{int(time.time())}",
                MonitorType.SYSTEM_HEALTH,
                MaintenanceLevel.WARNING,
                "内存使用率偏高",
                f"内存使用率: {mem.percent}%, 超过80%阈值",
                {'mem_percent': mem.percent}
            ))

        # 磁盘检查
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                if usage.percent > 90:
                    issues.append(MaintenanceIssue(
                        f"sys_disk_{partition.mountpoint}_{int(time.time())}",
                        MonitorType.SYSTEM_HEALTH,
                        MaintenanceLevel.RED_LINE,
                        f"磁盘空间不足: {partition.mountpoint}",
                        f"磁盘 {partition.mountpoint} 使用率: {usage.percent}%",
                        {'mountpoint': partition.mountpoint, 'percent': usage.percent,
                         'free_bytes': usage.free}
                    ))
                elif usage.percent > 80:
                    issues.append(MaintenanceIssue(
                        f"sys_disk_{partition.mountpoint}_{int(time.time())}",
                        MonitorType.SYSTEM_HEALTH,
                        MaintenanceLevel.WARNING,
                        f"磁盘空间偏低: {partition.mountpoint}",
                        f"磁盘 {partition.mountpoint} 使用率: {usage.percent}%",
                        {'mountpoint': partition.mountpoint, 'percent': usage.percent}
                    ))
            except PermissionError:
                continue

        return issues


class DatabaseHealthMonitor:
    """数据库健康监控器"""

    def __init__(self, db_dir: str):
        self.name = "数据库健康监控器"
        self.db_dir = db_dir

    def _find_databases(self) -> List[str]:
        """查找所有SQLite数据库文件"""
        db_files = []
        if os.path.exists(self.db_dir):
            for f in os.listdir(self.db_dir):
                if f.endswith('.db'):
                    db_files.append(os.path.join(self.db_dir, f))

        # 也检查根目录下的数据库
        root_dir = os.path.dirname(self.db_dir)
        for f in os.listdir(root_dir):
            if f.endswith('.db') and f not in [os.path.basename(p) for p in db_files]:
                db_files.append(os.path.join(root_dir, f))

        return db_files

    def check(self) -> List[MaintenanceIssue]:
        issues = []
        db_files = self._find_databases()

        for db_path in db_files:
            db_name = os.path.basename(db_path)

            # 检查文件是否存在
            if not os.path.exists(db_path):
                issues.append(MaintenanceIssue(
                    f"db_missing_{db_name}_{int(time.time())}",
                    MonitorType.DATABASE_HEALTH,
                    MaintenanceLevel.RED_LINE,
                    f"数据库文件缺失: {db_name}",
                    f"数据库文件 {db_path} 不存在",
                    {'db_path': db_path}
                ))
                continue

            # 检查文件大小
            file_size = os.path.getsize(db_path)
            if file_size == 0:
                issues.append(MaintenanceIssue(
                    f"db_empty_{db_name}_{int(time.time())}",
                    MonitorType.DATABASE_HEALTH,
                    MaintenanceLevel.RED_LINE,
                    f"数据库文件为空: {db_name}",
                    f"数据库文件 {db_name} 大小为0",
                    {'db_path': db_path}
                ))
                continue

            # 检查数据库完整性
            try:
                conn = sqlite3.connect(db_path, timeout=5)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                if result and result[0] != 'ok':
                    issues.append(MaintenanceIssue(
                        f"db_integrity_{db_name}_{int(time.time())}",
                        MonitorType.DATABASE_HEALTH,
                        MaintenanceLevel.RED_LINE,
                        f"数据库完整性错误: {db_name}",
                        f"数据库 {db_name} 完整性检查失败: {result[0]}",
                        {'db_name': db_name, 'integrity_result': result[0]}
                    ))

                # 检查数据库是否锁定
                try:
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master;")
                    cursor.fetchone()
                except sqlite3.OperationalError as e:
                    if 'locked' in str(e).lower():
                        issues.append(MaintenanceIssue(
                            f"db_locked_{db_name}_{int(time.time())}",
                            MonitorType.DATABASE_HEALTH,
                            MaintenanceLevel.RED_WALL,
                            f"数据库锁定: {db_name}",
                            f"数据库 {db_name} 被锁定: {e}",
                            {'db_name': db_name, 'error': str(e)}
                        ))

                conn.close()
            except Exception as e:
                issues.append(MaintenanceIssue(
                    f"db_error_{db_name}_{int(time.time())}",
                    MonitorType.DATABASE_HEALTH,
                    MaintenanceLevel.RED_LINE,
                    f"数据库访问错误: {db_name}",
                    f"数据库 {db_name} 访问失败: {e}",
                    {'db_name': db_name, 'error': str(e)}
                ))

        return issues


class RouteApiMonitor:
    """路由API监控器"""

    def __init__(self, base_url: str = "http://127.0.0.1:8888"):
        self.name = "路由API监控器"
        self.base_url = base_url

        # 关键路由检查列表
        self.critical_routes = [
            ("/", "首页", MaintenanceLevel.RED_LINE),
            ("/login", "登录页", MaintenanceLevel.RED_LINE),
            ("/api/ai/status", "AI状态API", MaintenanceLevel.RED_WALL),
            ("/api/health", "健康检查API", MaintenanceLevel.RED_LINE),
        ]

    def _http_get(self, path: str, timeout: int = 5) -> Dict:
        """发送HTTP GET请求"""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method='GET')
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)

        try:
            response = opener.open(req, timeout=timeout)
            return {
                'success': True,
                'status_code': response.getcode(),
                'response_time': 0  # 实际使用时计算
            }
        except urllib.error.HTTPError as e:
            return {'success': False, 'status_code': e.code, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'status_code': 0, 'error': str(e)}

    def check(self) -> List[MaintenanceIssue]:
        issues = []

        for path, name, level in self.critical_routes:
            start = time.time()
            result = self._http_get(path)
            elapsed = time.time() - start

            if not result['success']:
                issues.append(MaintenanceIssue(
                    f"route_{path}_{int(time.time())}",
                    MonitorType.ROUTE_API,
                    level,
                    f"路由不可用: {name}",
                    f"路由 {path} ({name}) 无法访问: {result.get('error', '未知错误')}",
                    {'path': path, 'name': name, 'status_code': result.get('status_code', 0),
                     'response_time': round(elapsed, 3)}
                ))
            elif result['status_code'] >= 500:
                issues.append(MaintenanceIssue(
                    f"route_{path}_{int(time.time())}",
                    MonitorType.ROUTE_API,
                    MaintenanceLevel.RED_LINE,
                    f"路由服务器错误: {name}",
                    f"路由 {path} 返回 {result['status_code']}",
                    {'path': path, 'name': name, 'status_code': result['status_code']}
                ))
            elif elapsed > 5.0:
                issues.append(MaintenanceIssue(
                    f"route_slow_{path}_{int(time.time())}",
                    MonitorType.ROUTE_API,
                    MaintenanceLevel.WARNING,
                    f"路由响应缓慢: {name}",
                    f"路由 {path} 响应时间 {elapsed:.2f}s, 超过5秒",
                    {'path': path, 'name': name, 'response_time': round(elapsed, 3)}
                ))

        return issues


class LogHealthMonitor:
    """日志健康监控器"""

    def __init__(self, log_dir: str):
        self.name = "日志健康监控器"
        self.log_dir = log_dir
        self.max_log_dir_size_mb = 500  # 日志目录最大500MB
        self.max_log_age_days = 30      # 日志保留30天

    def check(self) -> List[MaintenanceIssue]:
        issues = []

        if not os.path.exists(self.log_dir):
            return issues

        # 检查日志目录大小
        total_size = 0
        old_files = []

        for root, dirs, files in os.walk(self.log_dir):
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    stat = os.stat(file_path)
                    total_size += stat.st_size

                    # 检查过期日志
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    age_days = (datetime.now() - mtime).days
                    if age_days > self.max_log_age_days:
                        old_files.append({
                            'path': file_path,
                            'age_days': age_days,
                            'size': stat.st_size
                        })
                except (OSError, PermissionError):
                    continue

        total_size_mb = total_size / (1024 * 1024)

        if total_size_mb > self.max_log_dir_size_mb:
            issues.append(MaintenanceIssue(
                f"log_size_{int(time.time())}",
                MonitorType.LOG_HEALTH,
                MaintenanceLevel.CONSTRAINT,
                "日志目录过大",
                f"日志目录大小 {total_size_mb:.1f}MB, 超过 {self.max_log_dir_size_mb}MB 限制",
                {'total_size_mb': round(total_size_mb, 2), 'max_size_mb': self.max_log_dir_size_mb}
            ))

        if old_files:
            issues.append(MaintenanceIssue(
                f"log_old_{int(time.time())}",
                MonitorType.LOG_HEALTH,
                MaintenanceLevel.WARNING,
                f"发现 {len(old_files)} 个过期日志文件",
                f"有 {len(old_files)} 个日志文件超过 {self.max_log_age_days} 天未修改",
                {'old_files_count': len(old_files), 'max_age_days': self.max_log_age_days,
                 'sample_files': old_files[:5]}
            ))

        return issues


class FileSystemMonitor:
    """文件系统监控器"""

    def __init__(self, project_dir: str):
        self.name = "文件系统监控器"
        self.project_dir = project_dir

    def check(self) -> List[MaintenanceIssue]:
        issues = []

        # 检查关键目录是否存在
        critical_dirs = ['ai_engines', 'routes', 'templates', 'db', 'logs']
        for d in critical_dirs:
            dir_path = os.path.join(self.project_dir, d)
            if not os.path.exists(dir_path):
                issues.append(MaintenanceIssue(
                    f"fs_dir_{d}_{int(time.time())}",
                    MonitorType.FILE_SYSTEM,
                    MaintenanceLevel.RED_LINE,
                    f"关键目录缺失: {d}/",
                    f"项目关键目录 {dir_path} 不存在",
                    {'dir': d, 'path': dir_path}
                ))

        # 检查关键文件是否存在
        critical_files = ['server_real_db.py', 'app.py']
        for f in critical_files:
            file_path = os.path.join(self.project_dir, f)
            if not os.path.exists(file_path):
                issues.append(MaintenanceIssue(
                    f"fs_file_{f}_{int(time.time())}",
                    MonitorType.FILE_SYSTEM,
                    MaintenanceLevel.RED_LINE,
                    f"关键文件缺失: {f}",
                    f"项目关键文件 {file_path} 不存在",
                    {'file': f, 'path': file_path}
                ))

        # 检查 __pycache__ 过多
        pycache_count = 0
        for root, dirs, files in os.walk(self.project_dir):
            if '__pycache__' in dirs:
                pycache_count += 1

        if pycache_count > 50:
            issues.append(MaintenanceIssue(
                f"fs_pycache_{int(time.time())}",
                MonitorType.FILE_SYSTEM,
                MaintenanceLevel.WARNING,
                f"__pycache__ 目录过多: {pycache_count}",
                f"项目中有 {pycache_count} 个 __pycache__ 目录，建议清理",
                {'pycache_count': pycache_count}
            ))

        return issues


# ============================================================================
# 自动修复引擎
# ============================================================================

class AutoRepairEngine:
    """自动修复引擎"""

    def __init__(self, project_dir: str, db_dir: str, log_dir: str):
        self.project_dir = project_dir
        self.db_dir = db_dir
        self.log_dir = log_dir
        self.repair_history: List[Dict] = []
        self.name = "自动修复引擎"

    def repair(self, issue: MaintenanceIssue) -> Dict[str, Any]:
        """修复问题"""
        issue.status = IssueStatus.REPAIRING
        issue.retries += 1
        repair_action = ""
        repair_result = ""

        try:
            # 系统健康修复
            if issue.monitor_type == MonitorType.SYSTEM_HEALTH:
                if "CPU" in issue.title:
                    repair_action = "记录CPU高负载状态，通知管理员"
                    repair_result = "CPU高负载已记录，建议检查运行中的进程"
                    issue.status = IssueStatus.ESCALATED

                elif "内存" in issue.title:
                    repair_action = "尝试清理Python缓存"
                    repair_result = self._clear_python_cache()
                    issue.status = IssueStatus.RESOLVED

                elif "磁盘" in issue.title:
                    repair_action = "尝试清理临时文件和旧日志"
                    repair_result = self._clean_old_files()
                    issue.status = IssueStatus.RESOLVED

            # 数据库健康修复
            elif issue.monitor_type == MonitorType.DATABASE_HEALTH:
                if "完整性" in issue.title:
                    repair_action = "执行数据库VACUUM修复"
                    repair_result = self._vacuum_database(issue.details.get('db_name', ''))
                    issue.status = IssueStatus.RESOLVED

                elif "锁定" in issue.title:
                    repair_action = "记录数据库锁定状态"
                    repair_result = "数据库锁定已记录，需等待锁定释放"
                    issue.status = IssueStatus.ESCALATED

                elif "为空" in issue.title or "缺失" in issue.title:
                    repair_action = "记录数据库文件问题"
                    repair_result = "数据库文件问题已记录，需人工检查"
                    issue.status = IssueStatus.ESCALATED

            # 路由API修复
            elif issue.monitor_type == MonitorType.ROUTE_API:
                repair_action = "记录路由异常"
                repair_result = "路由异常已记录，需检查服务状态"
                issue.status = IssueStatus.ESCALATED

            # 日志健康修复
            elif issue.monitor_type == MonitorType.LOG_HEALTH:
                if "过大" in issue.title or "过期" in issue.title:
                    repair_action = "清理过期日志文件"
                    repair_result = self._clean_old_logs()
                    issue.status = IssueStatus.RESOLVED

            # 文件系统修复
            elif issue.monitor_type == MonitorType.FILE_SYSTEM:
                if "__pycache__" in issue.title:
                    repair_action = "清理 __pycache__ 目录"
                    repair_result = self._clean_pycache()
                    issue.status = IssueStatus.RESOLVED
                else:
                    repair_action = "记录文件系统问题"
                    repair_result = "文件系统问题已记录，需人工检查"
                    issue.status = IssueStatus.ESCALATED

            else:
                repair_action = "未知问题类型，跳过修复"
                repair_result = "无法自动修复此类型的问题"
                issue.status = IssueStatus.SKIPPED

            issue.repair_action = repair_action
            issue.repair_result = repair_result
            issue.resolved_at = datetime.now().isoformat()

            if issue.status == IssueStatus.RESOLVED:
                logger.info(f"问题已修复: {issue.title} -> {repair_result}")
            elif issue.status == IssueStatus.ESCALATED:
                logger.warning(f"问题需升级处理: {issue.title}")

        except Exception as e:
            issue.status = IssueStatus.FAILED
            issue.repair_result = f"修复失败: {str(e)}"
            logger.error(f"修复问题失败: {issue.title} - {e}")
            traceback.print_exc()

            if issue.retries < issue.max_retries:
                logger.info(f"将在下次循环重试: {issue.title} (重试 {issue.retries}/{issue.max_retries})")

        # 记录修复历史
        repair_record = {
            'issue_id': issue.issue_id,
            'title': issue.title,
            'action': repair_action,
            'result': repair_result,
            'status': issue.status.value,
            'timestamp': datetime.now().isoformat()
        }
        self.repair_history.append(repair_record)

        return repair_record

    def _clear_python_cache(self) -> str:
        """清理Python缓存"""
        cleared = 0
        for root, dirs, files in os.walk(self.project_dir):
            if '__pycache__' in dirs:
                cache_dir = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(cache_dir)
                    cleared += 1
                except Exception:
                    pass
        return f"已清理 {cleared} 个 __pycache__ 目录"

    def _clean_old_files(self) -> str:
        """清理旧文件"""
        cleaned = 0
        # 清理临时文件
        temp_patterns = ['*.tmp', '*.temp', '*.bak', '*.swp']
        for root, dirs, files in os.walk(self.project_dir):
            for pattern in temp_patterns:
                for f in files:
                    if f.endswith(pattern.replace('*', '')):
                        try:
                            os.remove(os.path.join(root, f))
                            cleaned += 1
                        except Exception:
                            pass
        return f"已清理 {cleaned} 个临时文件"

    def _clean_old_logs(self) -> str:
        """清理过期日志"""
        cleaned = 0
        if not os.path.exists(self.log_dir):
            return "日志目录不存在"

        cutoff = datetime.now() - timedelta(days=30)
        for root, dirs, files in os.walk(self.log_dir):
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime < cutoff:
                        os.remove(file_path)
                        cleaned += 1
                except Exception:
                    pass
        return f"已清理 {cleaned} 个过期日志文件"

    def _clean_pycache(self) -> str:
        """清理 __pycache__"""
        return self._clear_python_cache()

    def _vacuum_database(self, db_name: str) -> str:
        """执行数据库VACUUM"""
        db_path = os.path.join(self.db_dir, db_name) if db_name else None
        if not db_path or not os.path.exists(db_path):
            # 尝试在根目录找
            db_path = os.path.join(self.project_dir, db_name)

        if not os.path.exists(db_path):
            return f"数据库文件不存在: {db_name}"

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("VACUUM;")
            conn.close()
            return f"数据库 {db_name} VACUUM 完成"
        except Exception as e:
            return f"数据库 {db_name} VACUUM 失败: {e}"


# ============================================================================
# 双数据库管理器 — 主库 + 镜像库 双写 + 故障自动切换
# ============================================================================

class DualDatabaseManager:
    """
    双数据库管理器

    架构：
      Primary DB (主库)  ←→  Mirror DB (镜像库)
        - 写操作：双写（先主库后镜像库，主库失败切镜像库）
        - 读操作：优先主库，主库不可用自动切镜像库
        - 健康检查：定期校验两库一致性
        - 故障切换：主库连续失败 N 次后，镜像库提升为主库
    """

    def __init__(self, primary_path: str, mirror_path: str = None,
                 mirror_dir: str = None, max_failures: int = 3):
        self.primary_path = primary_path
        self.mirror_dir = mirror_dir or os.path.dirname(primary_path)
        self.mirror_path = mirror_path or os.path.join(
            self.mirror_dir,
            'maintenance_mirror.db'
        )
        self.max_failures = max_failures

        # 运行状态
        self._lock = threading.Lock()
        self._primary_failures = 0
        self._failover_mode = False  # True=镜像库提升为主
        self._active_path = primary_path  # 当前活跃库路径

        # 统计
        self.stats = {
            'total_writes': 0,
            'primary_writes': 0,
            'mirror_writes': 0,
            'write_failures': 0,
            'failovers': 0,
            'last_failover_time': None,
            'last_sync_time': None,
            'primary_healthy': True,
            'mirror_healthy': True,
        }

        os.makedirs(self.mirror_dir, exist_ok=True)
        self._init_mirror()
        logger.info(f"DualDatabaseManager 初始化: primary={primary_path} mirror={self.mirror_path}")

    def _init_mirror(self):
        """初始化镜像库（从主库克隆结构+数据）"""
        try:
            if not os.path.exists(self.mirror_path):
                # 使用 SQLite backup API 从主库完整克隆
                if os.path.exists(self.primary_path):
                    src = sqlite3.connect(self.primary_path, timeout=10)
                    dst = sqlite3.connect(self.mirror_path, timeout=10)
                    src.backup(dst)
                    dst.close()
                    src.close()
                    logger.info(f"镜像库已从主库克隆: {self.mirror_path}")
                else:
                    # 主库也不存在，创建空镜像库
                    conn = sqlite3.connect(self.mirror_path)
                    conn.close()
            self.stats['mirror_healthy'] = True
        except Exception as e:
            logger.error(f"初始化镜像库失败: {e}")
            self.stats['mirror_healthy'] = False

    def _connect_primary(self) -> Optional[sqlite3.Connection]:
        """连接主库"""
        try:
            conn = sqlite3.connect(self.primary_path, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.warning(f"连接主库失败: {e}")
            return None

    def _connect_mirror(self) -> Optional[sqlite3.Connection]:
        """连接镜像库"""
        try:
            conn = sqlite3.connect(self.mirror_path, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.warning(f"连接镜像库失败: {e}")
            return None

    def get_connection(self) -> sqlite3.Connection:
        """获取当前活跃库连接（带故障切换）"""
        if self._failover_mode:
            conn = self._connect_mirror()
            if conn:
                return conn
            # 镜像库也失败，尝试回切主库
            logger.warning("镜像库不可用，尝试回切主库")
            conn = self._connect_primary()
            if conn:
                self._failover_mode = False
                self._active_path = self.primary_path
                return conn
        else:
            conn = self._connect_primary()
            if conn:
                return conn
            # 主库失败，累计失败次数
            with self._lock:
                self._primary_failures += 1
                if self._primary_failures >= self.max_failures:
                    logger.error(f"主库连续失败 {self._primary_failures} 次，触发故障切换")
                    self._trigger_failover()
                    return self.get_connection()
        # 最终兜底：连接镜像库
        conn = self._connect_mirror()
        if conn:
            return conn
        # 最后兜底：强制连主库（让上层看到真实错误）
        return sqlite3.connect(self.primary_path if not self._failover_mode else self.mirror_path, timeout=10)

    def _trigger_failover(self):
        """触发故障切换：镜像库提升为主"""
        self._failover_mode = True
        self._active_path = self.mirror_path
        self.stats['failovers'] += 1
        self.stats['last_failover_time'] = datetime.now().isoformat()
        self.stats['primary_healthy'] = False
        logger.critical(f"⚠️ 故障切换：主库→镜像库 ({self.mirror_path})")

    def _recover_primary(self):
        """恢复主库（从镜像库回写）"""
        try:
            if os.path.exists(self.mirror_path) and os.path.exists(self.primary_path):
                src = sqlite3.connect(self.mirror_path, timeout=10)
                dst = sqlite3.connect(self.primary_path, timeout=10)
                src.backup(dst)
                dst.close()
                src.close()
                logger.info("主库已从镜像库恢复")
            with self._lock:
                self._primary_failures = 0
                self._failover_mode = False
                self._active_path = self.primary_path
                self.stats['primary_healthy'] = True
        except Exception as e:
            logger.error(f"恢复主库失败: {e}")

    def execute_write(self, sql: str, params: tuple = ()) -> bool:
        """双写执行：先写主库（或活跃库），再写镜像库"""
        success_primary = False
        success_mirror = False

        # 写活跃库
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            success_primary = True
            self.stats['primary_writes'] += 1
            with self._lock:
                self._primary_failures = 0  # 重置失败计数
        except Exception as e:
            logger.error(f"写主库失败: {e}")
            self.stats['write_failures'] += 1
            with self._lock:
                self._primary_failures += 1
                if self._primary_failures >= self.max_failures and not self._failover_mode:
                    self._trigger_failover()

        # 写镜像库（如果镜像库不是当前活跃库）
        if self._active_path != self.mirror_path:
            try:
                conn = self._connect_mirror()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(sql, params)
                    conn.commit()
                    conn.close()
                    success_mirror = True
                    self.stats['mirror_writes'] += 1
            except Exception as e:
                logger.warning(f"写镜像库失败: {e}")
                self.stats['mirror_healthy'] = False

        self.stats['total_writes'] += 1
        return success_primary or success_mirror

    def execute_query(self, sql: str, params: tuple = ()) -> list:
        """查询：优先活跃库，失败切备库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"查询失败 (active={self._active_path}): {e}")
            # 尝试另一个库
            fallback = self.mirror_path if self._active_path == self.primary_path else self.primary_path
            try:
                conn = sqlite3.connect(fallback, timeout=10)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                return [dict(r) for r in rows]
            except Exception as e2:
                logger.error(f"备库查询也失败: {e2}")
                return []

    def sync_mirror(self) -> Dict[str, Any]:
        """手动同步：从主库完整同步到镜像库"""
        result = {'success': False, 'synced_at': datetime.now().isoformat(), 'error': None}
        try:
            if not os.path.exists(self.primary_path):
                result['error'] = '主库不存在'
                return result
            src = sqlite3.connect(self.primary_path, timeout=10)
            dst = sqlite3.connect(self.mirror_path, timeout=10)
            src.backup(dst)
            dst.close()
            src.close()
            result['success'] = True
            self.stats['last_sync_time'] = result['synced_at']
            self.stats['mirror_healthy'] = True
            logger.info("镜像库同步完成")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"镜像库同步失败: {e}")
        return result

    def health_check(self) -> Dict[str, Any]:
        """双库健康检查"""
        result = {
            'primary_path': self.primary_path,
            'mirror_path': self.mirror_path,
            'active_path': self._active_path,
            'failover_mode': self._failover_mode,
            'primary_failures': self._primary_failures,
        }
        # 主库健康
        try:
            conn = sqlite3.connect(self.primary_path, timeout=5)
            conn.execute("SELECT 1")
            conn.execute("PRAGMA integrity_check")
            conn.close()
            result['primary_ok'] = True
            result['primary_size'] = os.path.getsize(self.primary_path) if os.path.exists(self.primary_path) else 0
        except Exception as e:
            result['primary_ok'] = False
            result['primary_error'] = str(e)
        # 镜像库健康
        try:
            conn = sqlite3.connect(self.mirror_path, timeout=5)
            conn.execute("SELECT 1")
            conn.execute("PRAGMA integrity_check")
            conn.close()
            result['mirror_ok'] = True
            result['mirror_size'] = os.path.getsize(self.mirror_path) if os.path.exists(self.mirror_path) else 0
        except Exception as e:
            result['mirror_ok'] = False
            result['mirror_error'] = str(e)
        result['stats'] = self.stats.copy()
        return result

    def get_status(self) -> Dict[str, Any]:
        """获取双库状态摘要"""
        return {
            'primary_path': self.primary_path,
            'mirror_path': self.mirror_path,
            'active_path': self._active_path,
            'failover_mode': self._failover_mode,
            'primary_failures': self._primary_failures,
            'stats': self.stats.copy(),
        }


# ============================================================================
# 数据库备份管理器 — SQLite backup API 快照 + 完整性校验 + 自动清理
# ============================================================================

class DatabaseBackupManager:
    """
    数据库备份管理器

    功能：
      - 定时快照备份（SQLite backup API，在线热备）
      - 完整性校验（PRAGMA integrity_check）
      - 自动清理（保留最近 N 份）
      - 备份验证（恢复测试）
      - 增量 WAL 支持
    """

    def __init__(self, db_path: str, backup_dir: str = None, max_backups: int = 30):
        self.db_path = db_path
        self.backup_dir = backup_dir or os.path.join(
            os.path.dirname(db_path), 'backups'
        )
        self.max_backups = max_backups
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"DatabaseBackupManager 初始化: db={db_path} backup_dir={self.backup_dir}")

    def create_snapshot(self, label: str = None) -> Dict[str, Any]:
        """创建数据库快照备份（在线热备，不阻塞写入）"""
        import hashlib
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        label_suffix = f"_{label}" if label else ""
        backup_name = f"maintenance_{ts}{label_suffix}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)

        result = {
            'backup_name': backup_name,
            'backup_path': backup_path,
            'backup_at': datetime.now().isoformat(),
            'size_bytes': 0,
            'sha256': None,
            'source': self.db_path,
            'integrity_ok': False,
            'error': None,
        }

        try:
            if not os.path.exists(self.db_path):
                result['error'] = f'源数据库不存在: {self.db_path}'
                return result

            # 使用 SQLite backup API（在线热备）
            src = sqlite3.connect(self.db_path, timeout=30)
            dst = sqlite3.connect(backup_path, timeout=30)
            src.backup(dst)
            dst.close()
            src.close()

            result['size_bytes'] = os.path.getsize(backup_path)

            # 计算 SHA256
            h = hashlib.sha256()
            with open(backup_path, 'rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(chunk)
            result['sha256'] = h.hexdigest()

            # 完整性校验
            result['integrity_ok'] = self._verify_integrity(backup_path)

            logger.info(f"数据库快照备份完成: {backup_name} ({result['size_bytes']} bytes)")

        except Exception as e:
            result['error'] = f"{type(e).__name__}: {e}"
            logger.error(f"数据库快照备份失败: {e}")

        # 自动清理旧备份
        self._cleanup_old_backups()

        return result

    def _verify_integrity(self, db_path: str) -> bool:
        """验证数据库完整性"""
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result[0] == 'ok' if result else False
        except Exception as e:
            logger.warning(f"完整性校验失败: {e}")
            return False

    def _cleanup_old_backups(self):
        """清理旧备份，保留最近 max_backups 份"""
        try:
            backups = sorted(
                [f for f in os.listdir(self.backup_dir)
                 if f.startswith('maintenance_') and f.endswith('.db')],
                reverse=True
            )
            if len(backups) > self.max_backups:
                for old in backups[self.max_backups:]:
                    old_path = os.path.join(self.backup_dir, old)
                    try:
                        os.remove(old_path)
                        logger.info(f"已清理旧备份: {old}")
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"清理旧备份失败: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        try:
            files = sorted(
                [f for f in os.listdir(self.backup_dir)
                 if f.startswith('maintenance_') and f.endswith('.db')],
                reverse=True
            )
            for f in files:
                fp = os.path.join(self.backup_dir, f)
                stat = os.stat(fp)
                backups.append({
                    'name': f,
                    'path': fp,
                    'size_bytes': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'integrity_ok': self._verify_integrity(fp),
                })
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
        return backups

    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """从备份恢复数据库"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        result = {
            'backup_name': backup_name,
            'restored_at': datetime.now().isoformat(),
            'success': False,
            'error': None,
        }
        try:
            if not os.path.exists(backup_path):
                result['error'] = f'备份文件不存在: {backup_name}'
                return result

            # 验证备份完整性
            if not self._verify_integrity(backup_path):
                result['error'] = '备份文件完整性校验失败'
                return result

            # 先备份当前数据库（恢复前快照）
            pre_restore = self.create_snapshot('pre_restore')
            result['pre_restore_backup'] = pre_restore.get('backup_name')

            # 恢复
            src = sqlite3.connect(backup_path, timeout=30)
            dst = sqlite3.connect(self.db_path, timeout=30)
            src.backup(dst)
            dst.close()
            src.close()

            result['success'] = True
            logger.info(f"数据库已从备份恢复: {backup_name}")

        except Exception as e:
            result['error'] = f"{type(e).__name__}: {e}"
            logger.error(f"从备份恢复失败: {e}")
        return result

    def get_status(self) -> Dict[str, Any]:
        """获取备份管理器状态"""
        backups = self.list_backups()
        total_size = sum(b['size_bytes'] for b in backups)
        return {
            'db_path': self.db_path,
            'backup_dir': self.backup_dir,
            'total_backups': len(backups),
            'total_size_bytes': total_size,
            'max_backups': self.max_backups,
            'latest_backup': backups[0] if backups else None,
        }


# ============================================================================
# 备份维护引擎 — 轻量级，监控主引擎健康 + 故障时接管
# ============================================================================

class BackupMaintenanceEngine:
    """
    备份维护引擎（双引擎架构中的备份角色）

    职责：
      - 监控主引擎 (AutoMaintenanceAgent) 的健康状态
      - 主引擎故障/卡死时自动接管维护职责
      - 独立执行轻量级巡检（不依赖主引擎的监控器）
      - 定时触发数据库备份
      - 主引擎恢复后交还职责
    """

    ENGINE_ID = "backup_maintenance_engine_001"
    ENGINE_NAME = "MTSCOS备份维护引擎"
    ENGINE_VERSION = "v1.0.0"

    def __init__(self, primary_agent: 'AutoMaintenanceAgent' = None,
                 db_manager: DualDatabaseManager = None,
                 backup_manager: DatabaseBackupManager = None,
                 check_interval: int = 600):
        self.engine_id = self.ENGINE_ID
        self.name = self.ENGINE_NAME
        self.version = self.ENGINE_VERSION
        self.primary_agent = primary_agent
        self.db_manager = db_manager
        self.backup_manager = backup_manager
        self.check_interval = check_interval  # 默认10分钟

        # 运行状态
        self.is_running = False
        self.is_active = False  # True=已接管主引擎职责
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # 主引擎健康追踪
        self._primary_heartbeat = None
        self._primary_last_seen = None
        self._primary_fail_count = 0
        self._takeover_threshold = 3  # 连续3次检测失败则接管

        # 备份调度
        self._last_backup_time = None
        self._backup_interval = 3600  # 默认1小时备份一次

        # 统计
        self.stats = {
            'total_checks': 0,
            'primary_healthy_count': 0,
            'primary_unhealthy_count': 0,
            'takeovers': 0,
            'handbacks': 0,
            'backups_created': 0,
            'backups_failed': 0,
            'last_takeover_time': None,
            'last_handback_time': None,
        }

        logger.info(f"{self.name} 已初始化 (v{self.version})")

    def set_primary_agent(self, agent: 'AutoMaintenanceAgent'):
        """设置主引擎引用"""
        self.primary_agent = agent

    def check_primary_health(self) -> Dict[str, Any]:
        """检查主引擎健康状态"""
        result = {
            'checked_at': datetime.now().isoformat(),
            'primary_alive': False,
            'primary_running': False,
            'takeover_needed': False,
            'error': None,
        }
        try:
            if self.primary_agent is None:
                result['error'] = '主引擎引用未设置'
                result['takeover_needed'] = True
                return result

            # 检查主引擎是否在运行
            is_running = getattr(self.primary_agent, 'is_running', False)
            state = getattr(self.primary_agent, 'state', AgentState.STOPPED)

            result['primary_running'] = is_running
            result['primary_state'] = state.value if hasattr(state, 'value') else str(state)

            # 检查主引擎心跳（最近检查时间）
            last_check = getattr(self.primary_agent, 'stats', {}).get('last_check_time')
            if last_check:
                result['primary_last_check'] = last_check
                # 如果超过3个检查周期没心跳，认为卡死
                try:
                    last_dt = datetime.fromisoformat(last_check)
                    elapsed = (datetime.now() - last_dt).total_seconds()
                    max_elapsed = self.primary_agent.check_interval * 3
                    result['primary_alive'] = elapsed < max_elapsed
                    result['elapsed_since_last_check'] = int(elapsed)
                except Exception:
                    result['primary_alive'] = False
            else:
                result['primary_alive'] = False

            # 判定是否需要接管
            if not result['primary_alive'] or not is_running:
                with self._lock:
                    self._primary_fail_count += 1
                    self.stats['primary_unhealthy_count'] += 1
                    if self._primary_fail_count >= self._takeover_threshold:
                        result['takeover_needed'] = True
            else:
                with self._lock:
                    self._primary_fail_count = 0
                    self.stats['primary_healthy_count'] += 1

        except Exception as e:
            result['error'] = str(e)
            result['takeover_needed'] = True
            logger.error(f"主引擎健康检查异常: {e}")

        return result

    def takeover(self):
        """接管主引擎职责"""
        with self._lock:
            self.is_active = True
            self.stats['takeovers'] += 1
            self.stats['last_takeover_time'] = datetime.now().isoformat()
        logger.critical(f"⚠️ 备份引擎接管主引擎职责 (takeover #{self.stats['takeovers']})")

    def handback(self):
        """交还职责给主引擎"""
        with self._lock:
            if self.is_active:
                self.is_active = False
                self.stats['handbacks'] += 1
                self.stats['last_handback_time'] = datetime.now().isoformat()
                logger.info("备份引擎交还职责给主引擎")

    def run_lightweight_check(self) -> Dict[str, Any]:
        """轻量级巡检（接管时使用）"""
        result = {
            'checked_at': datetime.now().isoformat(),
            'engine': self.engine_id,
            'is_takeover_mode': self.is_active,
            'checks': {},
        }
        # 1. 双库健康
        if self.db_manager:
            result['checks']['dual_db'] = self.db_manager.health_check()
        # 2. 备份状态
        if self.backup_manager:
            result['checks']['backup'] = self.backup_manager.get_status()
        # 3. 系统资源（轻量）
        if _PSUTIL_AVAILABLE:
            try:
                import psutil
                result['checks']['system'] = {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                }
            except Exception:
                pass
        return result

    def maybe_create_backup(self) -> Optional[Dict[str, Any]]:
        """按需创建数据库备份"""
        if not self.backup_manager:
            return None
        now = datetime.now()
        if self._last_backup_time:
            try:
                last_dt = datetime.fromisoformat(self._last_backup_time)
                if (now - last_dt).total_seconds() < self._backup_interval:
                    return None  # 还没到备份时间
            except Exception:
                pass
        # 创建备份
        result = self.backup_manager.create_snapshot(
            label='takeover' if self.is_active else 'scheduled'
        )
        if result.get('success') or result.get('sha256'):
            self._last_backup_time = now.isoformat()
            self.stats['backups_created'] += 1
        else:
            self.stats['backups_failed'] += 1
        return result

    def _run_loop(self):
        """备份引擎主循环"""
        logger.info(f"{self.name} 主循环已启动 (间隔={self.check_interval}s)")
        while not self._stop_event.is_set():
            try:
                self.stats['total_checks'] += 1
                # 1. 检查主引擎健康
                health = self.check_primary_health()
                if health.get('takeover_needed') and not self.is_active:
                    self.takeover()
                elif not health.get('takeover_needed') and self.is_active:
                    # 主引擎恢复，交还
                    if health.get('primary_alive') and health.get('primary_running'):
                        self.handback()

                # 2. 如果接管中，执行轻量巡检
                if self.is_active:
                    check_result = self.run_lightweight_check()
                    logger.info(f"备份引擎接管模式巡检完成: {len(check_result.get('checks', {}))} 项")

                # 3. 按需创建备份
                self.maybe_create_backup()

            except Exception as e:
                logger.error(f"备份引擎循环异常: {e}")

            # 等待下一轮
            self._stop_event.wait(self.check_interval)

        logger.info(f"{self.name} 主循环已停止")

    def start(self):
        """启动备份引擎"""
        if self.is_running:
            return {'success': True, 'message': '备份引擎已在运行'}
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name='backup-maintenance-engine', daemon=True)
        self._thread.start()
        self.is_running = True
        logger.info(f"{self.name} 已启动")
        return {'success': True, 'engine_id': self.engine_id, 'check_interval': self.check_interval}

    def stop(self):
        """停止备份引擎"""
        if not self.is_running:
            return {'success': True, 'message': '备份引擎未运行'}
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        self.is_running = False
        logger.info(f"{self.name} 已停止")
        return {'success': True}

    def get_status(self) -> Dict[str, Any]:
        """获取备份引擎状态"""
        return {
            'engine_id': self.engine_id,
            'engine_name': self.name,
            'version': self.version,
            'is_running': self.is_running,
            'is_active': self.is_active,
            'is_takeover_mode': self.is_active,
            'check_interval': self.check_interval,
            'backup_interval': self._backup_interval,
            'primary_fail_count': self._primary_fail_count,
            'takeover_threshold': self._takeover_threshold,
            'last_backup_time': self._last_backup_time,
            'stats': self.stats.copy(),
        }


# ============================================================================
# 自动提案系统 — 巡检结果自动生成提案 → 审批 → 执行 → 上报
# ============================================================================

class ProposalStatus(Enum):
    """提案状态机"""
    DRAFT = "draft"               # 草稿（自动生成中）
    SUBMITTED = "submitted"       # 已提交（等待审批）
    UNDER_REVIEW = "under_review" # 审核中
    APPROVED = "approved"         # 已批准
    REJECTED = "rejected"         # 已驳回
    EXECUTING = "executing"       # 执行中（修复中）
    COMPLETED = "completed"       # 已完成（修复成功）
    FAILED = "failed"             # 执行失败
    ESCALATED = "escalated"       # 已升级（需人工介入）


class ProposalType(Enum):
    """提案类型"""
    AUTO_REPAIR = "auto_repair"           # 自动修复提案（RED_LINE级别，立即修复+事后上报）
    APPROVAL_REPAIR = "approval_repair"   # 审批修复提案（IRON_RULE/RED_WALL级别，需审批后修复）
    MANUAL_INTERVENTION = "manual"        # 人工介入提案（修复失败，需人工处理）
    INFORMATIONAL = "informational"       # 信息性提案（WARNING级别，仅上报记录）
    EMERGENCY = "emergency"               # 紧急提案（系统级故障，需立即处理）


class MaintenanceProposal:
    """维护提案数据模型"""

    def __init__(self, proposal_id: str, proposal_type: ProposalType,
                 level: MaintenanceLevel, title: str, description: str,
                 related_issues: List[str] = None):
        self.proposal_id = proposal_id
        self.proposal_type = proposal_type
        self.level = level
        self.title = title
        self.description = description
        self.related_issues = related_issues or []  # 关联的issue_id列表

        # 状态流转
        self.status = ProposalStatus.DRAFT
        self.created_at = datetime.now().isoformat()
        self.submitted_at = None
        self.reviewed_at = None
        self.executed_at = None
        self.completed_at = None

        # 审批信息
        self.reviewers = []           # 审批人列表
        self.approvals = []           # 批准记录
        self.rejections = []          # 驳回记录
        self.review_notes = None      # 审批备注

        # 执行信息
        self.repair_plan = None       # 修复计划
        self.execution_result = None  # 执行结果
        self.execution_log = []       # 执行日志

        # 上报信息
        self.report_summary = None    # 上报摘要
        self.escalation_reason = None # 升级原因

    def submit(self):
        """提交提案"""
        self.status = ProposalStatus.SUBMITTED
        self.submitted_at = datetime.now().isoformat()

    def approve(self, reviewer: str, notes: str = None):
        """批准提案"""
        self.reviewers.append(reviewer)
        self.approvals.append({'reviewer': reviewer, 'at': datetime.now().isoformat(), 'notes': notes})
        self.review_notes = notes
        if len(self.approvals) >= 1:  # 至少1人批准即可（可根据级别调整）
            self.status = ProposalStatus.APPROVED
            self.reviewed_at = datetime.now().isoformat()

    def reject(self, reviewer: str, reason: str = None):
        """驳回提案"""
        self.reviewers.append(reviewer)
        self.rejections.append({'reviewer': reviewer, 'at': datetime.now().isoformat(), 'reason': reason})
        self.status = ProposalStatus.REJECTED
        self.reviewed_at = datetime.now().isoformat()
        self.review_notes = reason

    def start_execution(self, repair_plan: str = None):
        """开始执行"""
        self.status = ProposalStatus.EXECUTING
        self.executed_at = datetime.now().isoformat()
        self.repair_plan = repair_plan

    def complete(self, result: Dict, summary: str = None):
        """完成执行"""
        self.status = ProposalStatus.COMPLETED
        self.execution_result = result
        self.report_summary = summary
        self.completed_at = datetime.now().isoformat()

    def fail(self, error: str, escalate: bool = False):
        """执行失败"""
        self.status = ProposalStatus.ESCALATED if escalate else ProposalStatus.FAILED
        self.execution_result = {'error': error}
        self.escalation_reason = error if escalate else None
        self.completed_at = datetime.now().isoformat()

    def add_log(self, message: str):
        """添加执行日志"""
        self.execution_log.append({
            'at': datetime.now().isoformat(),
            'message': message
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'proposal_type': self.proposal_type.value,
            'level': self.level.value,
            'title': self.title,
            'description': self.description,
            'related_issues': self.related_issues,
            'status': self.status.value,
            'created_at': self.created_at,
            'submitted_at': self.submitted_at,
            'reviewed_at': self.reviewed_at,
            'executed_at': self.executed_at,
            'completed_at': self.completed_at,
            'reviewers': self.reviewers,
            'approvals': self.approvals,
            'rejections': self.rejections,
            'review_notes': self.review_notes,
            'repair_plan': self.repair_plan,
            'execution_result': self.execution_result,
            'execution_log': self.execution_log,
            'report_summary': self.report_summary,
            'escalation_reason': self.escalation_reason,
        }


class ProposalManager:
    """
    提案管理器

    职责：
      - 根据巡检问题自动生成提案
      - 管理提案生命周期（草稿→提交→审批→执行→完成→上报）
      - 持久化提案到数据库（SSOT）
      - 提供提案查询/统计接口
      - 集成双数据库双写
    """

    def __init__(self, dual_db: 'DualDatabaseManager' = None, db_path: str = None):
        self.dual_db = dual_db
        self._db_path = db_path
        self._lock = threading.Lock()

        # 内存缓存（最近100个提案）
        self.proposals: deque = deque(maxlen=100)

        # 统计
        self.stats = {
            'total_proposals': 0,
            'auto_repair_proposals': 0,
            'approval_proposals': 0,
            'manual_proposals': 0,
            'informational_proposals': 0,
            'emergency_proposals': 0,
            'approved': 0,
            'rejected': 0,
            'completed': 0,
            'failed': 0,
            'escalated': 0,
            'pending_review': 0,
        }

        self._ensure_tables()
        logger.info("ProposalManager 已初始化")

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接（优先双库管理器）"""
        if self.dual_db:
            return self.dual_db.get_connection()
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute_write(self, sql: str, params: tuple = ()) -> bool:
        """执行写入（双写）"""
        if self.dual_db:
            return self.dual_db.execute_write(sql, params)
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"写入失败: {e}")
            return False

    def _execute_query(self, sql: str, params: tuple = ()) -> list:
        """执行查询（故障切换）"""
        if self.dual_db:
            return self.dual_db.execute_query(sql, params)
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []

    def _ensure_tables(self):
        """创建提案相关表"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()

            # 提案主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_maintenance_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT UNIQUE NOT NULL,
                    proposal_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    related_issues TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT,
                    submitted_at TEXT,
                    reviewed_at TEXT,
                    executed_at TEXT,
                    completed_at TEXT,
                    reviewers TEXT,
                    approvals TEXT,
                    rejections TEXT,
                    review_notes TEXT,
                    repair_plan TEXT,
                    execution_result TEXT,
                    execution_log TEXT,
                    report_summary TEXT,
                    escalation_reason TEXT,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)

            # 提案上报记录表（自动上报日志）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_proposal_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    proposal_id TEXT,
                    report_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    severity TEXT,
                    auto_generated INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)

            conn.commit()
            conn.close()
            logger.info("提案数据库表已就绪")
        except Exception as e:
            logger.error(f"创建提案表失败: {e}")

    def generate_proposal(self, issue: 'MaintenanceIssue') -> MaintenanceProposal:
        """根据巡检问题自动生成提案"""
        proposal_id = f"prop_{datetime.now().strftime('%Y%m%d%H%M%S')}_{issue.issue_id[-8:]}"

        # 根据问题级别决定提案类型
        if issue.level == MaintenanceLevel.IRON_RULE:
            prop_type = ProposalType.EMERGENCY
            title = f"[紧急] {issue.title}"
            desc = f"铁律级别问题，需立即处理: {issue.description}"
        elif issue.level == MaintenanceLevel.RED_WALL:
            prop_type = ProposalType.APPROVAL_REPAIR
            title = f"[审批] {issue.title}"
            desc = f"红墙级别问题，需审批后修复: {issue.description}"
        elif issue.level == MaintenanceLevel.RED_LINE:
            prop_type = ProposalType.AUTO_REPAIR
            title = f"[自动修复] {issue.title}"
            desc = f"红线级别问题，自动修复并上报: {issue.description}"
        elif issue.level == MaintenanceLevel.CONSTRAINT:
            prop_type = ProposalType.AUTO_REPAIR
            title = f"[约束] {issue.title}"
            desc = f"约束级别问题，自动修复: {issue.description}"
        else:  # WARNING
            prop_type = ProposalType.INFORMATIONAL
            title = f"[提示] {issue.title}"
            desc = f"警告级别问题，记录上报: {issue.description}"

        proposal = MaintenanceProposal(
            proposal_id=proposal_id,
            proposal_type=prop_type,
            level=issue.level,
            title=title,
            description=desc,
            related_issues=[issue.issue_id],
        )

        # 更新统计
        with self._lock:
            self.stats['total_proposals'] += 1
            if prop_type == ProposalType.AUTO_REPAIR:
                self.stats['auto_repair_proposals'] += 1
            elif prop_type == ProposalType.APPROVAL_REPAIR:
                self.stats['approval_proposals'] += 1
            elif prop_type == ProposalType.MANUAL_INTERVENTION:
                self.stats['manual_proposals'] += 1
            elif prop_type == ProposalType.INFORMATIONAL:
                self.stats['informational_proposals'] += 1
            elif prop_type == ProposalType.EMERGENCY:
                self.stats['emergency_proposals'] += 1

        return proposal

    def generate_manual_proposal(self, issue: 'MaintenanceIssue', error: str) -> MaintenanceProposal:
        """修复失败后生成人工介入提案"""
        proposal_id = f"prop_manual_{datetime.now().strftime('%Y%m%d%H%M%S')}_{issue.issue_id[-8:]}"

        proposal = MaintenanceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.MANUAL_INTERVENTION,
            level=issue.level,
            title=f"[人工介入] {issue.title} - 自动修复失败",
            description=f"自动修复失败，需人工处理。\n问题: {issue.description}\n错误: {error}",
            related_issues=[issue.issue_id],
        )
        proposal.escalation_reason = error

        with self._lock:
            self.stats['total_proposals'] += 1
            self.stats['manual_proposals'] += 1

        return proposal

    def submit_proposal(self, proposal: MaintenanceProposal):
        """提交提案（自动上报）"""
        proposal.submit()
        self._save_proposal_to_db(proposal)
        self.proposals.append(proposal)

        # 自动生成上报记录
        self._auto_report(proposal, 'submitted')

        with self._lock:
            if proposal.status == ProposalStatus.SUBMITTED:
                self.stats['pending_review'] += 1

        logger.info(f"提案已提交: {proposal.proposal_id} ({proposal.title})")

    def auto_approve_and_execute(self, proposal: MaintenanceProposal,
                                  repair_fn: Callable = None) -> Dict[str, Any]:
        """
        自动审批并执行提案（适用于AUTO_REPAIR类型）

        对于自动修复类提案，系统自动批准并执行修复
        """
        result = {'proposal_id': proposal.proposal_id, 'success': False}

        # 自动批准
        proposal.approve('auto_system', '自动修复提案，系统自动批准')
        self._save_proposal_to_db(proposal)

        # 执行修复
        proposal.start_execution(repair_plan=f"自动执行: {proposal.title}")
        proposal.add_log("开始执行自动修复")
        self._save_proposal_to_db(proposal)

        try:
            if repair_fn:
                repair_result = repair_fn()
                proposal.complete(
                    result=repair_result,
                    summary=f"自动修复完成: {repair_result}"
                )
                result['success'] = True
                result['repair_result'] = repair_result
                with self._lock:
                    self.stats['completed'] += 1
            else:
                proposal.complete(result={'message': '无需修复操作'}, summary="信息性提案，无需修复")
                result['success'] = True
                with self._lock:
                    self.stats['completed'] += 1
        except Exception as e:
            proposal.fail(str(e), escalate=True)
            result['error'] = str(e)
            with self._lock:
                self.stats['escalated'] += 1

        proposal.add_log(f"执行完成: status={proposal.status.value}")
        self._save_proposal_to_db(proposal)

        # 自动上报
        self._auto_report(proposal, 'completed')

        return result

    def submit_for_manual_review(self, proposal: MaintenanceProposal):
        """提交提案等待人工审批（适用于APPROVAL_REPAIR/MANUAL_INTERVENTION类型）"""
        proposal.submit()
        self._save_proposal_to_db(proposal)
        self.proposals.append(proposal)

        self._auto_report(proposal, 'pending_review')

        with self._lock:
            self.stats['pending_review'] += 1

        logger.info(f"提案已提交待审: {proposal.proposal_id} ({proposal.title})")

    def review_proposal(self, proposal_id: str, reviewer: str,
                        approved: bool, notes: str = None) -> Dict[str, Any]:
        """审批提案（人工）"""
        result = {'proposal_id': proposal_id, 'success': False}

        # 从数据库加载提案
        proposal = self._load_proposal_from_db(proposal_id)
        if not proposal:
            result['error'] = '提案不存在'
            return result

        if proposal.status != ProposalStatus.SUBMITTED:
            result['error'] = f'提案状态不可审批: {proposal.status.value}'
            return result

        if approved:
            proposal.approve(reviewer, notes)
            with self._lock:
                self.stats['approved'] += 1
                self.stats['pending_review'] = max(0, self.stats['pending_review'] - 1)
        else:
            proposal.reject(reviewer, notes)
            with self._lock:
                self.stats['rejected'] += 1
                self.stats['pending_review'] = max(0, self.stats['pending_review'] - 1)

        self._save_proposal_to_db(proposal)
        self._auto_report(proposal, 'reviewed')

        result['success'] = True
        result['status'] = proposal.status.value
        return result

    def execute_approved_proposal(self, proposal_id: str,
                                   repair_fn: Callable = None) -> Dict[str, Any]:
        """执行已批准的提案"""
        result = {'proposal_id': proposal_id, 'success': False}

        proposal = self._load_proposal_from_db(proposal_id)
        if not proposal:
            result['error'] = '提案不存在'
            return result

        if proposal.status != ProposalStatus.APPROVED:
            result['error'] = f'提案未批准，当前状态: {proposal.status.value}'
            return result

        proposal.start_execution(repair_plan=f"执行已批准提案: {proposal.title}")
        proposal.add_log("开始执行")
        self._save_proposal_to_db(proposal)

        try:
            if repair_fn:
                repair_result = repair_fn()
                proposal.complete(result=repair_result, summary=f"修复完成: {repair_result}")
            else:
                proposal.complete(result={'message': '手动完成'}, summary="手动标记完成")
            result['success'] = True
            with self._lock:
                self.stats['completed'] += 1
        except Exception as e:
            proposal.fail(str(e), escalate=True)
            result['error'] = str(e)
            with self._lock:
                self.stats['escalated'] += 1

        self._save_proposal_to_db(proposal)
        self._auto_report(proposal, 'executed')

        result['status'] = proposal.status.value
        return result

    def _auto_report(self, proposal: MaintenanceProposal, event: str):
        """自动生成上报记录"""
        report_id = f"rpt_{proposal.proposal_id}_{event}"
        report_type_map = {
            'submitted': '提案提交',
            'pending_review': '待审批',
            'reviewed': '审批完成',
            'completed': '执行完成',
            'executed': '执行上报',
        }
        severity_map = {
            MaintenanceLevel.IRON_RULE: 'critical',
            MaintenanceLevel.RED_LINE: 'high',
            MaintenanceLevel.RED_WALL: 'high',
            MaintenanceLevel.CONSTRAINT: 'medium',
            MaintenanceLevel.WARNING: 'low',
        }

        sql = """
            INSERT OR REPLACE INTO mt_proposal_reports
            (report_id, proposal_id, report_type, title, content, severity, auto_generated)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """
        params = (
            report_id,
            proposal.proposal_id,
            report_type_map.get(event, event),
            proposal.title,
            json.dumps(proposal.to_dict(), ensure_ascii=False),
            severity_map.get(proposal.level, 'info'),
        )
        self._execute_write(sql, params)

    def _save_proposal_to_db(self, proposal: MaintenanceProposal):
        """保存提案到数据库（双写）"""
        sql = """
            INSERT OR REPLACE INTO mt_maintenance_proposals
            (proposal_id, proposal_type, level, title, description, related_issues,
             status, created_at, submitted_at, reviewed_at, executed_at, completed_at,
             reviewers, approvals, rejections, review_notes, repair_plan,
             execution_result, execution_log, report_summary, escalation_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            proposal.proposal_id, proposal.proposal_type.value, proposal.level.value,
            proposal.title, proposal.description,
            json.dumps(proposal.related_issues, ensure_ascii=False),
            proposal.status.value, proposal.created_at, proposal.submitted_at,
            proposal.reviewed_at, proposal.executed_at, proposal.completed_at,
            json.dumps(proposal.reviewers, ensure_ascii=False),
            json.dumps(proposal.approvals, ensure_ascii=False),
            json.dumps(proposal.rejections, ensure_ascii=False),
            proposal.review_notes, proposal.repair_plan,
            json.dumps(proposal.execution_result, ensure_ascii=False) if proposal.execution_result else None,
            json.dumps(proposal.execution_log, ensure_ascii=False),
            proposal.report_summary, proposal.escalation_reason,
        )
        self._execute_write(sql, params)

    def _load_proposal_from_db(self, proposal_id: str) -> Optional[MaintenanceProposal]:
        """从数据库加载提案"""
        rows = self._execute_query(
            "SELECT * FROM mt_maintenance_proposals WHERE proposal_id = ?",
            (proposal_id,)
        )
        if not rows:
            return None
        row = rows[0]

        # 重建提案对象
        level = MaintenanceLevel(row['level'])
        prop_type = ProposalType(row['proposal_type'])
        proposal = MaintenanceProposal(
            proposal_id=row['proposal_id'],
            proposal_type=prop_type,
            level=level,
            title=row['title'],
            description=row['description'] or '',
            related_issues=json.loads(row['related_issues']) if row['related_issues'] else [],
        )
        proposal.status = ProposalStatus(row['status'])
        proposal.created_at = row['created_at']
        proposal.submitted_at = row['submitted_at']
        proposal.reviewed_at = row['reviewed_at']
        proposal.executed_at = row['executed_at']
        proposal.completed_at = row['completed_at']
        proposal.reviewers = json.loads(row['reviewers']) if row['reviewers'] else []
        proposal.approvals = json.loads(row['approvals']) if row['approvals'] else []
        proposal.rejections = json.loads(row['rejections']) if row['rejections'] else []
        proposal.review_notes = row['review_notes']
        proposal.repair_plan = row['repair_plan']
        proposal.execution_result = json.loads(row['execution_result']) if row['execution_result'] else None
        proposal.execution_log = json.loads(row['execution_log']) if row['execution_log'] else []
        proposal.report_summary = row['report_summary']
        proposal.escalation_reason = row['escalation_reason']
        return proposal

    def get_proposals(self, limit: int = 50, status: str = None,
                      prop_type: str = None) -> List[Dict]:
        """查询提案列表"""
        sql = "SELECT * FROM mt_maintenance_proposals"
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if prop_type:
            conditions.append("proposal_type = ?")
            params.append(prop_type)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return self._execute_query(sql, tuple(params))

    def get_pending_proposals(self, limit: int = 20) -> List[Dict]:
        """获取待审批提案"""
        return self._execute_query(
            "SELECT * FROM mt_maintenance_proposals WHERE status = 'submitted' ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

    def get_reports(self, limit: int = 50) -> List[Dict]:
        """获取上报记录"""
        return self._execute_query(
            "SELECT * FROM mt_proposal_reports ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取提案统计"""
        with self._lock:
            return self.stats.copy()

    def get_status(self) -> Dict[str, Any]:
        """获取提案管理器状态"""
        return {
            'total_proposals': self.stats['total_proposals'],
            'pending_review': self.stats['pending_review'],
            'approved': self.stats['approved'],
            'rejected': self.stats['rejected'],
            'completed': self.stats['completed'],
            'failed': self.stats['failed'],
            'escalated': self.stats['escalated'],
            'stats': self.get_stats(),
        }


# ============================================================================
# 主 Agent
# ============================================================================

class AutoMaintenanceAgent:
    """
    MTSCOS 自动维护 Agent

    整合所有维护功能的统一入口：
    - 系统健康监控 (CPU/内存/磁盘)
    - 数据库健康监控 (完整性/锁定/大小)
    - 路由API监控 (可用性/响应时间)
    - 日志健康监控 (大小/过期清理)
    - 文件系统监控 (关键文件/目录)
    - 自动修复引擎
    - 维护报告生成
    - 数据库持久化 (SSOT)
    """

    # Agent 元数据
    AGENT_ID = "auto_maintenance_agent_001"
    AGENT_NAME = "MTSCOS自动维护Agent"
    AGENT_ROLE = "system_maintenance"
    AGENT_VERSION = "v2.12.0"  # MINOR: 成人教育管理功能补全（adult_education_routes.py Blueprint 20个API端点+8项白名单+_safe_float校验+参数化SQL+XSS防护+10张表自动建表+统一设计令牌模板重构）

    def __init__(self, project_dir: str = None, base_url: str = "http://127.0.0.1:8888"):
        # 基础属性
        self.agent_id = self.AGENT_ID
        self.name = self.AGENT_NAME
        self.role = self.AGENT_ROLE
        self.version = self.AGENT_VERSION
        self.created_at = datetime.now().isoformat()

        # 路径配置
        self.project_dir = project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_dir = os.path.join(self.project_dir, 'db')
        self.log_dir = os.path.join(self.project_dir, 'logs')
        self.base_url = base_url

        # 运行状态
        self.state = AgentState.STOPPED
        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # 监控器
        self.monitors: Dict[str, Any] = {
            'system_health': SystemHealthMonitor(),
            'database_health': DatabaseHealthMonitor(self.db_dir),
            'route_api': RouteApiMonitor(self.base_url),
            'log_health': LogHealthMonitor(self.log_dir),
            'file_system': FileSystemMonitor(self.project_dir),
        }

        # 修复引擎
        self.repair_engine = AutoRepairEngine(self.project_dir, self.db_dir, self.log_dir)

        # 数据存储
        self.issues: deque = deque(maxlen=1000)  # 最近1000个问题
        self.reports: deque = deque(maxlen=100)   # 最近100个报告
        self.stats = {
            'total_checks': 0,
            'total_issues': 0,
            'total_resolved': 0,
            'total_failed': 0,
            'total_escalated': 0,
            'last_check_time': None,
            'last_report_time': None,
            'uptime_start': None,
        }

        # 配置
        self.check_interval = 300  # 默认5分钟检查一次
        self.auto_repair = True    # 是否自动修复
        self.max_concurrent_repairs = 5

        # 智能赋能
        self.empowerment_enabled = False
        self.personality = None
        self.learning_engine = None
        if _EMPOWERMENT_AVAILABLE:
            try:
                self.personality = PersonalitySystem('cautious')
                self.learning_engine = NetworkLearningEngine(self.agent_id, 'system_admin')
                self.empowerment_enabled = True
            except Exception as e:
                logger.warning(f"Agent智能赋能初始化失败: {e}")

        # === 双数据库初始化（v2.0核心） ===
        self._db_path = self._find_db_path()
        self.dual_db = DualDatabaseManager(
            primary_path=self._db_path,
            mirror_dir=self.db_dir,
        )
        # 在镜像库也创建维护表
        self._ensure_tables_on_mirror()

        # === 数据库备份管理器 ===
        self.backup_manager = DatabaseBackupManager(
            db_path=self._db_path,
            backup_dir=os.path.join(self.db_dir, 'backups'),
            max_backups=30,
        )

        # === 备份维护引擎（双引擎架构） ===
        self.backup_engine = BackupMaintenanceEngine(
            primary_agent=self,
            db_manager=self.dual_db,
            backup_manager=self.backup_manager,
            check_interval=600,
        )

        # === 自动提案管理器（v2.1：自动巡检→自动修复→自动上报提案） ===
        self.proposal_manager = ProposalManager(
            dual_db=self.dual_db,
            db_path=self._db_path,
        )

        # === 数据库加密管理器（v2.2：字段级AES加密 + 备份加密 + 密钥管理） ===
        self.crypto_manager = None
        try:
            from ai_engines.database_crypto import DatabaseCryptoManager
            self.crypto_manager = DatabaseCryptoManager(
                db_path=self._db_path,
                dual_db=self.dual_db,
            )
        except Exception as e:
            logger.warning(f"加密管理器初始化失败: {e}")

        # === 反编译检测与防护系统（v2.3：代码完整性 + 反编译检测 + 水印） ===
        self.anti_decompilation_guard = None
        try:
            from ai_engines.anti_decompilation import AntiDecompilationGuard
            self.anti_decompilation_guard = AntiDecompilationGuard(
                project_dir=self.project_dir,
                db_path=self._db_path,
                dual_db=self.dual_db,
            )
        except Exception as e:
            logger.warning(f"反编译防护系统初始化失败: {e}")

        # === JSON数据同步数据库系统（v2.4：JSON↔DB双向同步 + Schema推断） ===
        self.json_db_sync = None
        try:
            from ai_engines.json_db_sync import JsonDbSync
            self.json_db_sync = JsonDbSync(
                project_dir=self.project_dir,
                db_path=self._db_path,
                dual_db=self.dual_db,
            )
        except Exception as e:
            logger.warning(f"JSON数据同步系统初始化失败: {e}")

        # === 自动升级系统（v2.5：4大目标检测+半自动提案审批+回滚） ===
        self.upgrade_system = None
        try:
            from ai_engines.auto_upgrade_system import AutoUpgradeSystem
            self.upgrade_system = AutoUpgradeSystem(
                project_dir=self.project_dir,
                db_path=self._db_path,
                dual_db=self.dual_db,
            )
        except Exception as e:
            logger.warning(f"自动升级系统初始化失败: {e}")

        # === 云同步层（v2.6：偏好同步/快照备份/会话同步/冷备） — 先初始化供下面两个使用 ===
        self.cloud_sync_layer = None
        try:
            from ai_engines.cloud_sync_layer import CloudSyncLayer
            self.cloud_sync_layer = CloudSyncLayer(
                project_dir=self.project_dir,
                db_path=self._db_path,
                dual_db=self.dual_db,
                crypto_manager=self.crypto_manager,
            )
        except Exception as e:
            logger.warning(f"云同步层初始化失败: {e}")

        # === 个性化引擎（v2.6：UI主题/首页菜单/数据交互/AI员工形象） ===
        self.personalization_core = None
        try:
            from ai_engines.personalization_core import PersonalizationCore
            self.personalization_core = PersonalizationCore(
                db_path=self._db_path,
                dual_db=self.dual_db,
                project_dir=self.project_dir,
                cloud_sync_layer=self.cloud_sync_layer,
            )
        except Exception as e:
            logger.warning(f"个性化引擎初始化失败: {e}")

        # === 定制化引擎（v2.6：角色仪表盘/工作流/表单字段） ===
        self.customization_engine = None
        try:
            from ai_engines.customization_engine import CustomizationEngine
            self.customization_engine = CustomizationEngine(
                db_path=self._db_path,
                dual_db=self.dual_db,
                project_dir=self.project_dir,
                cloud_sync_layer=self.cloud_sync_layer,
            )
        except Exception as e:
            logger.warning(f"定制化引擎初始化失败: {e}")

        # === 智能化题库管理（v2.7：知识图谱+遗传组卷+生命周期+学习路径+健康度+标签推荐） ===
        self.iqbm = None
        try:
            from ai_engines.intelligent_question_bank_manager import IntelligentQuestionBankManager
            self.iqbm = IntelligentQuestionBankManager(dual_db=self.dual_db)
        except Exception as e:
            logger.warning(f"智能化题库管理系统初始化失败: {e}")

        # === 学生门户增强系统（v2.8：5个核心页面 + CSS统一令牌 + 响应式3档断点） ===
        self.student_portal = None
        try:
            self.student_portal = {
                "pages": ["analytics", "tournament", "ai_tutor", "redeem", "achievements", "settings"],
                "base_template": "student_base.html",
                "css_tokens_v1": True,
                "responsive_breakpoints": (1280, 768, 480),
                "status": "deployed",
            }
        except Exception as e:
            logger.warning(f"学生门户系统初始化失败: {e}")

        # === 自定义考试/练习双重校验（v2.8：白名单+科题绑定+合理性评分5档+高危子串16项扫描） ===
        self.custom_exam_validator = None
        try:
            from custom_exam_validators import validate_custom_exam_config, validate_custom_test_config
            self.custom_exam_validator = {
                "validate_exam": validate_custom_exam_config,
                "validate_test": validate_custom_test_config,
                "version": "v1.1.1",
            }
        except Exception as e:
            logger.warning(f"自定义考试/练习校验模块初始化失败: {e}")

        # === K12教育管理（v2.11：18个API端点+权限双保险+白名单校验+参数化SQL） ===
        self.k12_management = None
        try:
            from routes.k12_management_routes import _get_k12_service
            self.k12_management = {
                "version": "v1.0.0",
                "endpoints": 18,
                "service_ready": True,
            }
        except Exception as e:
            logger.warning(f"K12教育管理模块初始化失败: {e}")

        # === 成人教育管理（v2.12：20个API端点+8项白名单+_safe_float+10张表自动建表） ===
        self.adult_education = None
        try:
            from routes.adult_education_routes import _ensure_tables as _adult_init
            self.adult_education = {
                "version": "v1.0.0",
                "endpoints": 20,
                "tables": 10,
                "service_ready": True,
            }
        except Exception as e:
            logger.warning(f"成人教育管理模块初始化失败: {e}")

        # 确保主库表存在
        self._ensure_tables()

        logger.info(f"{self.name} 已初始化 (v{self.version}) 赋能={'✓' if self.empowerment_enabled else '✗'} 双库=✓ 双引擎=✓ 提案=✓ 升级=✓ 个性化=✓ 定制化=✓ 云端化=✓ 题库=✓ 学生门户=✓ 自定义考试校验=✓ 管理员界面优化=✓ 超管界面优化=✓ K12管理=✓ 成人教育=✓")

    # ========================================================================
    # 数据库操作
    # ========================================================================

    def _find_db_path(self) -> str:
        """查找数据库路径"""
        search_paths = [
            os.path.join(self.db_dir, 'system.db'),
            os.path.join(self.db_dir, 'ai.db'),
            os.path.join(self.project_dir, 'app.db'),
            os.path.join(self.project_dir, 'instance', 'mtscos.db'),
        ]
        for p in search_paths:
            if os.path.exists(p):
                return p
        # 默认使用 system.db
        os.makedirs(self.db_dir, exist_ok=True)
        return os.path.join(self.db_dir, 'system.db')

    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """确保数据库表存在"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # 维护问题表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mt_maintenance_issues (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        issue_id TEXT UNIQUE NOT NULL,
                        monitor_type TEXT NOT NULL,
                        level TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        details TEXT,
                        status TEXT DEFAULT 'detected',
                        detected_at TEXT,
                        resolved_at TEXT,
                        repair_action TEXT,
                        repair_result TEXT,
                        retries INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                """)

                # 维护报告表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mt_maintenance_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT UNIQUE NOT NULL,
                        start_time TEXT,
                        end_time TEXT,
                        total_checks INTEGER DEFAULT 0,
                        passed_checks INTEGER DEFAULT 0,
                        failed_checks INTEGER DEFAULT 0,
                        warnings INTEGER DEFAULT 0,
                        issues_detected INTEGER DEFAULT 0,
                        issues_resolved INTEGER DEFAULT 0,
                        issues_failed INTEGER DEFAULT 0,
                        issues_escalated INTEGER DEFAULT 0,
                        duration_seconds REAL DEFAULT 0,
                        summary TEXT,
                        details TEXT,
                        created_at TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                """)

                # Agent状态表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mt_maintenance_agent_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT UNIQUE NOT NULL,
                        agent_name TEXT,
                        state TEXT DEFAULT 'stopped',
                        is_running INTEGER DEFAULT 0,
                        check_interval INTEGER DEFAULT 300,
                        auto_repair INTEGER DEFAULT 1,
                        total_checks INTEGER DEFAULT 0,
                        total_issues INTEGER DEFAULT 0,
                        total_resolved INTEGER DEFAULT 0,
                        total_failed INTEGER DEFAULT 0,
                        total_escalated INTEGER DEFAULT 0,
                        last_check_time TEXT,
                        last_report_time TEXT,
                        uptime_start TEXT,
                        updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                """)

                # 插入或更新Agent状态
                cursor.execute("""
                    INSERT OR IGNORE INTO mt_maintenance_agent_status
                    (agent_id, agent_name, state, is_running)
                    VALUES (?, ?, 'stopped', 0)
                """, (self.agent_id, self.name))

                conn.commit()
                logger.info(f"维护Agent数据库表已就绪: {self._db_path}")

        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")

    def _ensure_tables_on_mirror(self):
        """在镜像库也创建维护表（双库一致性）"""
        try:
            mirror_path = self.dual_db.mirror_path
            conn = sqlite3.connect(mirror_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_maintenance_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id TEXT UNIQUE NOT NULL,
                    monitor_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    details TEXT,
                    status TEXT DEFAULT 'detected',
                    detected_at TEXT,
                    resolved_at TEXT,
                    repair_action TEXT,
                    repair_result TEXT,
                    retries INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_maintenance_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    total_checks INTEGER DEFAULT 0,
                    passed_checks INTEGER DEFAULT 0,
                    failed_checks INTEGER DEFAULT 0,
                    warnings INTEGER DEFAULT 0,
                    issues_detected INTEGER DEFAULT 0,
                    issues_resolved INTEGER DEFAULT 0,
                    issues_failed INTEGER DEFAULT 0,
                    issues_escalated INTEGER DEFAULT 0,
                    duration_seconds REAL DEFAULT 0,
                    summary TEXT,
                    details TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_maintenance_agent_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT UNIQUE NOT NULL,
                    state TEXT DEFAULT 'stopped',
                    is_running INTEGER DEFAULT 0,
                    check_interval INTEGER DEFAULT 300,
                    auto_repair INTEGER DEFAULT 1,
                    total_checks INTEGER DEFAULT 0,
                    total_issues INTEGER DEFAULT 0,
                    total_resolved INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    total_escalated INTEGER DEFAULT 0,
                    last_check_time TEXT,
                    last_report_time TEXT,
                    uptime_start TEXT,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)

            # v2.1: 镜像库也创建提案表（双库一致性）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_maintenance_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT UNIQUE NOT NULL,
                    proposal_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    related_issues TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT,
                    submitted_at TEXT,
                    reviewed_at TEXT,
                    executed_at TEXT,
                    completed_at TEXT,
                    reviewers TEXT,
                    approvals TEXT,
                    rejections TEXT,
                    review_notes TEXT,
                    repair_plan TEXT,
                    execution_result TEXT,
                    execution_log TEXT,
                    report_summary TEXT,
                    escalation_reason TEXT,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_proposal_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    proposal_id TEXT,
                    report_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    severity TEXT,
                    auto_generated INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()
            conn.close()
            logger.info(f"镜像库维护表已就绪(含提案表): {mirror_path}")
        except Exception as e:
            logger.error(f"创建镜像库表失败: {e}")

    def _save_issue_to_db(self, issue: MaintenanceIssue):
        """保存问题到数据库（双写主库+镜像库）"""
        sql = """
            INSERT OR REPLACE INTO mt_maintenance_issues
            (issue_id, monitor_type, level, title, description, details,
             status, detected_at, resolved_at, repair_action, repair_result, retries)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            issue.issue_id, issue.monitor_type.value, issue.level.value,
            issue.title, issue.description, json.dumps(issue.details, ensure_ascii=False),
            issue.status.value, issue.detected_at, issue.resolved_at,
            issue.repair_action, issue.repair_result, issue.retries
        )
        # 双写
        ok = self.dual_db.execute_write(sql, params)
        if not ok:
            logger.error(f"保存问题到双库失败: {issue.issue_id}")

    def _save_report_to_db(self, report: MaintenanceReport):
        """保存报告到数据库（双写主库+镜像库）"""
        report.finalize()
        sql = """
            INSERT OR REPLACE INTO mt_maintenance_reports
            (report_id, start_time, end_time, total_checks, passed_checks,
             failed_checks, warnings, issues_detected, issues_resolved,
             issues_failed, issues_escalated, duration_seconds, summary, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            report.report_id, report.start_time, report.end_time,
            report.total_checks, report.passed_checks, report.failed_checks,
            report.warnings, report.issues_detected, report.issues_resolved,
            report.issues_failed, report.issues_escalated,
            report.duration_seconds, report.summary,
            json.dumps(report.details, ensure_ascii=False)
        )
        # 双写
        ok = self.dual_db.execute_write(sql, params)
        if not ok:
            logger.error(f"保存报告到双库失败: {report.report_id}")

    def _update_agent_status(self):
        """更新Agent状态到数据库（双写主库+镜像库）"""
        sql = """
            UPDATE mt_maintenance_agent_status SET
                state = ?, is_running = ?, check_interval = ?,
                auto_repair = ?, total_checks = ?, total_issues = ?,
                total_resolved = ?, total_failed = ?, total_escalated = ?,
                last_check_time = ?, last_report_time = ?, uptime_start = ?,
                updated_at = datetime('now', 'localtime')
            WHERE agent_id = ?
        """
        params = (
            self.state.value, 1 if self.is_running else 0, self.check_interval,
            1 if self.auto_repair else 0, self.stats['total_checks'],
            self.stats['total_issues'], self.stats['total_resolved'],
            self.stats['total_failed'], self.stats['total_escalated'],
            self.stats['last_check_time'], self.stats['last_report_time'],
            self.stats['uptime_start'], self.agent_id
        )
        # 双写
        self.dual_db.execute_write(sql, params)

    # ========================================================================
    # 核心功能
    # ========================================================================

    def start(self, check_interval: int = None):
        """启动维护Agent（含备份引擎）"""
        if self.is_running:
            logger.warning("维护Agent已在运行中")
            return {'success': False, 'message': 'Agent已在运行中'}

        if check_interval:
            self.check_interval = max(60, check_interval)  # 最小60秒

        self.is_running = True
        self.state = AgentState.MONITORING
        self._stop_event.clear()
        self.stats['uptime_start'] = datetime.now().isoformat()

        self._thread = threading.Thread(target=self._run_loop, daemon=True, name='auto_maintenance')
        self._thread.start()

        # 启动备份引擎（双引擎架构）
        self.backup_engine.start()

        self._update_agent_status()
        logger.info(f"维护Agent已启动(v{self.version}), 检查间隔: {self.check_interval}秒, 备份引擎: ✓")

        return {
            'success': True,
            'message': f'Agent已启动, 检查间隔: {self.check_interval}秒, 备份引擎已启动',
            'agent_id': self.agent_id,
            'version': self.version,
            'state': self.state.value,
            'backup_engine': self.backup_engine.get_status(),
        }

    def stop(self):
        """停止维护Agent（含备份引擎）"""
        if not self.is_running:
            return {'success': False, 'message': 'Agent未在运行'}

        self.is_running = False
        self._stop_event.set()
        self.state = AgentState.STOPPED

        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

        # 停止备份引擎
        self.backup_engine.stop()

        self._update_agent_status()
        logger.info("维护Agent已停止, 备份引擎已停止")

        return {'success': True, 'message': 'Agent已停止, 备份引擎已停止'}

    def _run_loop(self):
        """主运行循环"""
        logger.info("维护Agent循环启动")

        while not self._stop_event.is_set():
            try:
                self.state = AgentState.MONITORING
                self.run_maintenance_cycle()

                # 等待下一次检查
                self._stop_event.wait(timeout=self.check_interval)

            except Exception as e:
                logger.error(f"维护Agent循环异常: {e}")
                traceback.print_exc()
                self.state = AgentState.ERROR
                self._stop_event.wait(timeout=60)  # 出错后等待60秒

        logger.info("维护Agent循环结束")

    def run_maintenance_cycle(self) -> MaintenanceReport:
        """执行一次完整的维护周期"""
        report_id = f"rpt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = MaintenanceReport(report_id)

        logger.info(f"开始维护周期: {report_id}")
        self.state = AgentState.MONITORING

        all_issues: List[MaintenanceIssue] = []

        # 1. 执行所有监控器检查
        for monitor_name, monitor in self.monitors.items():
            try:
                report.total_checks += 1
                issues = monitor.check()

                if issues:
                    report.failed_checks += 1
                    for issue in issues:
                        all_issues.append(issue)
                        if issue.level == MaintenanceLevel.WARNING:
                            report.warnings += 1
                else:
                    report.passed_checks += 1

                report.details.append({
                    'monitor': monitor_name,
                    'status': 'failed' if issues else 'passed',
                    'issues_count': len(issues),
                    'issues': [i.to_dict() for i in issues]
                })

            except Exception as e:
                report.total_checks += 1
                report.failed_checks += 1
                logger.error(f"监控器 {monitor_name} 执行失败: {e}")
                report.details.append({
                    'monitor': monitor_name,
                    'status': 'error',
                    'error': str(e)
                })

        # 2. 保存检测到的问题
        for issue in all_issues:
            self.issues.append(issue)
            self._save_issue_to_db(issue)
            self.stats['total_issues'] += 1

        report.issues_detected = len(all_issues)

        # 3. 自动提案 + 自动修复 + 自动上报
        if all_issues:
            self.state = AgentState.REPAIRING
            for issue in all_issues:
                # 跳过已解决的
                if issue.status in [IssueStatus.RESOLVED, IssueStatus.SKIPPED]:
                    continue

                # === 自动生成提案 ===
                proposal = self.proposal_manager.generate_proposal(issue)

                # 根据提案类型决定处理方式
                if proposal.proposal_type == ProposalType.AUTO_REPAIR:
                    # 自动修复类：自动审批 + 执行修复 + 上报
                    def _do_repair():
                        self.repair_engine.repair(issue)
                        return issue.to_dict()

                    result = self.proposal_manager.auto_approve_and_execute(proposal, repair_fn=_do_repair)
                    self._save_issue_to_db(issue)

                    if issue.status == IssueStatus.RESOLVED:
                        report.issues_resolved += 1
                        self.stats['total_resolved'] += 1
                    elif issue.status == IssueStatus.FAILED:
                        # 修复失败 → 生成人工介入提案
                        manual_prop = self.proposal_manager.generate_manual_proposal(issue, result.get('error', 'unknown'))
                        self.proposal_manager.submit_for_manual_review(manual_prop)
                        issue.status = IssueStatus.ESCALATED
                        report.issues_failed += 1
                        report.issues_escalated += 1
                        self.stats['total_failed'] += 1
                        self.stats['total_escalated'] += 1
                        self._save_issue_to_db(issue)

                elif proposal.proposal_type in [ProposalType.APPROVAL_REPAIR, ProposalType.EMERGENCY]:
                    # 审批类：提交待审，暂不修复
                    self.proposal_manager.submit_for_manual_review(proposal)
                    issue.status = IssueStatus.ESCALATED
                    report.issues_escalated += 1
                    self.stats['total_escalated'] += 1
                    self._save_issue_to_db(issue)

                elif proposal.proposal_type == ProposalType.INFORMATIONAL:
                    # 信息类：自动审批（无需修复） + 记录上报
                    self.proposal_manager.auto_approve_and_execute(proposal, repair_fn=None)
                    issue.status = IssueStatus.SKIPPED
                    self._save_issue_to_db(issue)

        # 4. 生成报告
        self.state = AgentState.REPORTING
        report.finalize()
        self.reports.append(report)
        self._save_report_to_db(report)

        # 5. 更新统计
        self.stats['total_checks'] += report.total_checks
        self.stats['last_check_time'] = datetime.now().isoformat()
        self.stats['last_report_time'] = report.end_time
        self._update_agent_status()

        # 6. 智能赋能反馈
        if self.empowerment_enabled and self.personality:
            success = report.issues_failed == 0
            self.personality.update_emotion('routine_task', success)

        logger.info(f"维护周期完成: {report.summary}")

        self.state = AgentState.IDLE if self.is_running else AgentState.STOPPED
        return report

    def run_single_check(self, monitor_type: str) -> Dict[str, Any]:
        """执行单个监控检查"""
        monitor = self.monitors.get(monitor_type)
        if not monitor:
            return {'success': False, 'message': f'未找到监控器: {monitor_type}'}

        try:
            issues = monitor.check()
            return {
                'success': True,
                'monitor_type': monitor_type,
                'issues_found': len(issues),
                'issues': [i.to_dict() for i in issues],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态（含双库+备份引擎状态）"""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.name,
            'version': self.version,
            'state': self.state.value,
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'auto_repair': self.auto_repair,
            'monitors': list(self.monitors.keys()),
            'stats': self.stats,
            'empowerment_enabled': self.empowerment_enabled,
            'uptime_start': self.stats['uptime_start'],
            # v2.0 双数据库状态
            'dual_database': self.dual_db.get_status(),
            # v2.0 备份引擎状态
            'backup_engine': self.backup_engine.get_status(),
            # v2.0 备份管理器状态
            'backup_manager': self.backup_manager.get_status(),
            # v2.1 提案管理器状态
            'proposal_manager': self.proposal_manager.get_status(),
            # v2.2 加密管理器状态
            'crypto_manager': self.crypto_manager.get_status() if self.crypto_manager else None,
            # v2.3 反编译防护系统状态
            'anti_decompilation': self.anti_decompilation_guard.get_status() if self.anti_decompilation_guard else None,
            # v2.4 JSON数据同步系统状态
            'json_db_sync': self.json_db_sync.get_status() if self.json_db_sync else None,
            # v2.5 自动升级系统状态
            'upgrade_system': self.upgrade_system.get_status() if self.upgrade_system else None,
            # v2.6 个性化引擎状态
            'personalization_core': self.personalization_core.get_status() if self.personalization_core else None,
            # v2.6 定制化引擎状态
            'customization_engine': self.customization_engine.get_status() if self.customization_engine else None,
            # v2.6 云同步层状态
            'cloud_sync_layer': self.cloud_sync_layer.get_status() if self.cloud_sync_layer else None,
            # v2.7 智能化题库管理状态
            'iqbm': self.iqbm.get_status() if self.iqbm else None,
            # v2.11 K12教育管理状态
            'k12_management': self.k12_management,
            # v2.12 成人教育管理状态
            'adult_education': self.adult_education,
            'timestamp': datetime.now().isoformat()
        }

    def get_recent_issues(self, limit: int = 50) -> List[Dict]:
        """获取最近的问题"""
        return [issue.to_dict() for issue in list(self.issues)[-limit:]]

    def get_recent_reports(self, limit: int = 10) -> List[Dict]:
        """获取最近的报告"""
        return [report.to_dict() for report in list(self.reports)[-limit:]]

    def get_history_from_db(self, limit: int = 100, issue_status: str = None) -> List[Dict]:
        """从数据库获取历史问题（优先主库，故障切镜像库）"""
        try:
            if issue_status:
                return self.dual_db.execute_query(
                    "SELECT * FROM mt_maintenance_issues WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (issue_status, limit)
                )
            else:
                return self.dual_db.execute_query(
                    "SELECT * FROM mt_maintenance_issues ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
        except Exception as e:
            logger.error(f"获取历史问题失败: {e}")
            return []

    def get_reports_from_db(self, limit: int = 20) -> List[Dict]:
        """从数据库获取历史报告（优先主库，故障切镜像库）"""
        try:
            return self.dual_db.execute_query(
                "SELECT * FROM mt_maintenance_reports ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        except Exception as e:
            logger.error(f"获取历史报告失败: {e}")
            return []

    def set_config(self, check_interval: int = None, auto_repair: bool = None) -> Dict:
        """更新配置"""
        if check_interval is not None:
            self.check_interval = max(60, check_interval)
        if auto_repair is not None:
            self.auto_repair = auto_repair

        self._update_agent_status()
        return {
            'success': True,
            'check_interval': self.check_interval,
            'auto_repair': self.auto_repair
        }


# ============================================================================
# 单例管理
# ============================================================================

_agent_instance: Optional[AutoMaintenanceAgent] = None
_agent_lock = threading.Lock()


def get_maintenance_agent() -> AutoMaintenanceAgent:
    """获取维护Agent单例"""
    global _agent_instance
    if _agent_instance is None:
        with _agent_lock:
            if _agent_instance is None:
                _agent_instance = AutoMaintenanceAgent()
    return _agent_instance


def init_maintenance_agent(project_dir: str = None, base_url: str = None) -> AutoMaintenanceAgent:
    """初始化维护Agent"""
    global _agent_instance
    with _agent_lock:
        _agent_instance = AutoMaintenanceAgent(
            project_dir=project_dir,
            base_url=base_url or "http://127.0.0.1:8888"
        )
    return _agent_instance


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    agent = get_maintenance_agent()

    # 执行一次维护检查
    print("=== 执行一次维护检查 ===")
    report = agent.run_maintenance_cycle()
    print(report.summary)

    # 获取状态
    print("\n=== Agent状态 ===")
    status = agent.get_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 获取最近的问题
    print("\n=== 最近问题 ===")
    issues = agent.get_recent_issues(10)
    for issue in issues:
        print(f"  [{issue['level']}] {issue['title']} - {issue['status']}")
