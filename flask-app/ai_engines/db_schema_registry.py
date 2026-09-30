# -*- coding: utf-8 -*-
"""
数据库三维分类注册表
按 "表类型 + 功能模块 + 数据热度" 三维分类所有数据库表，
为 AI 智能分散数据库提供统一的路由元数据。
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TableCategory(Enum):
    """表类型分类"""
    CORE = "core"            # 核心业务表（用户、考试、题目）
    LOGS = "logs"            # 日志表
    BEHAVIOR = "behavior"    # 考试行为表
    AI_ENGINE = "ai_engine"  # AI引擎数据表
    KNOWLEDGE = "knowledge"  # 题库数据表
    ARCHIVE = "archive"      # 归档表


class DataHeat(Enum):
    """数据热度等级"""
    HOT = "hot"    # 高频读写，需快速访问
    WARM = "warm"  # 中频访问
    COLD = "cold"  # 低频归档数据


# 功能模块枚举
class FeatureModule(Enum):
    AUTH = "auth"            # 认证授权
    EXAM = "exam"            # 考试系统
    TEST = "test"            # 测试系统
    LEARNING = "learning"    # 学习系统
    SYSTEM = "system"        # 系统管理
    SECURITY = "security"    # 安全防护
    AI = "ai"                # AI引擎
    K12 = "k12"              # K12教育
    ADULT = "adult"          # 成人教育
    MONITOR = "monitor"      # 监控


# ============================================================
# 三维分类注册表 - 表名 → {category, module, heat, shard_db}
# shard_db 指明该表应该分散到哪个物理数据库文件
# ============================================================
TABLE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # === 日志表（logs.db）- 优先迁移目标 ===
    'system_logs':          {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'access_logs':          {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'error_logs':           {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'operation_logs':       {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'security_audit_logs':  {'category': TableCategory.LOGS,      'module': FeatureModule.SECURITY, 'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'change_logs':          {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'system_events':        {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'ai_repair_logs':       {'category': TableCategory.LOGS,      'module': FeatureModule.AI,       'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'code_fix_logs':        {'category': TableCategory.LOGS,      'module': FeatureModule.AI,       'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'generation_logs':      {'category': TableCategory.LOGS,      'module': FeatureModule.AI,       'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'user_activity_logs':   {'category': TableCategory.LOGS,      'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'logs.db'},
    'user_login_logs':      {'category': TableCategory.LOGS,      'module': FeatureModule.AUTH,     'heat': DataHeat.WARM, 'shard_db': 'logs.db'},

    # === 考试行为表（exam_behavior.db）===
    'exam_behavior_logs':          {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.EXAM,     'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'cheating_detection_results':  {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.EXAM,     'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'screen_switch_logs':          {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.EXAM,     'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'time_anomaly_logs':           {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.EXAM,     'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'answer_pattern_analysis':     {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.EXAM,     'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'exam_records':                {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.EXAM,     'heat': DataHeat.HOT,  'shard_db': 'exam_behavior.db'},

    # === AI引擎表（ai_engine.db）===
    'exam_ai_sessions':      {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'exam_ai_conversations': {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'exam_ai_suggestions':   {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'exam_ai_analysis':      {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'question_generation_logs': {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'question_maintenance_logs': {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'rule_execution_logs':   {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},
    'rule_application_logs': {'category': TableCategory.AI_ENGINE, 'module': FeatureModule.AI,   'heat': DataHeat.WARM, 'shard_db': 'ai_engine.db'},

    # === 题库表（knowledge.db）===
    'knowledge_base_questions':  {'category': TableCategory.KNOWLEDGE, 'module': FeatureModule.EXAM,    'heat': DataHeat.HOT, 'shard_db': 'knowledge.db'},
    'student_mistakes':          {'category': TableCategory.KNOWLEDGE, 'module': FeatureModule.LEARNING, 'heat': DataHeat.HOT, 'shard_db': 'knowledge.db'},
    'learning_paths':            {'category': TableCategory.KNOWLEDGE, 'module': FeatureModule.LEARNING, 'heat': DataHeat.HOT, 'shard_db': 'knowledge.db'},
    'question_analysis':         {'category': TableCategory.KNOWLEDGE, 'module': FeatureModule.EXAM,    'heat': DataHeat.WARM, 'shard_db': 'knowledge.db'},
    'user_learning_records':     {'category': TableCategory.KNOWLEDGE, 'module': FeatureModule.LEARNING, 'heat': DataHeat.WARM, 'shard_db': 'knowledge.db'},
    'db_change_log':             {'category': TableCategory.KNOWLEDGE, 'module': FeatureModule.SYSTEM,   'heat': DataHeat.WARM, 'shard_db': 'knowledge.db'},

    # === 核心业务表（core.db）- 本次不迁移，仅建立路由元数据 ===
    'users':             {'category': TableCategory.CORE, 'module': FeatureModule.AUTH,    'heat': DataHeat.HOT, 'shard_db': 'core.db'},
    'exams':             {'category': TableCategory.CORE, 'module': FeatureModule.EXAM,    'heat': DataHeat.HOT, 'shard_db': 'core.db'},
    'questions':         {'category': TableCategory.CORE, 'module': FeatureModule.EXAM,    'heat': DataHeat.HOT, 'shard_db': 'core.db'},
    'exam_sessions':     {'category': TableCategory.CORE, 'module': FeatureModule.EXAM,    'heat': DataHeat.HOT, 'shard_db': 'core.db'},
    'system_settings':   {'category': TableCategory.CORE, 'module': FeatureModule.SYSTEM, 'heat': DataHeat.HOT, 'shard_db': 'core.db'},
    'version_control':   {'category': TableCategory.CORE, 'module': FeatureModule.SYSTEM, 'heat': DataHeat.HOT, 'shard_db': 'core.db'},
    'user_points':       {'category': TableCategory.CORE, 'module': FeatureModule.AUTH,    'heat': DataHeat.WARM, 'shard_db': 'core.db'},
    'redeem_history':    {'category': TableCategory.CORE, 'module': FeatureModule.AUTH,    'heat': DataHeat.WARM, 'shard_db': 'core.db'},

    # === 测试系统表（exam_behavior.db 共享）===
    'system_test_logs':       {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.TEST, 'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'test_exception_logs':    {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.TEST, 'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'test_operation_logs':    {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.TEST, 'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
    'physics_simulation_steps': {'category': TableCategory.BEHAVIOR, 'module': FeatureModule.TEST, 'heat': DataHeat.WARM, 'shard_db': 'exam_behavior.db'},
}

# 需要优先迁移的膨胀表列表（按预计数据量排序）
PRIORITY_MIGRATION_TABLES = [
    'system_logs',
    'access_logs',
    'error_logs',
    'operation_logs',
    'security_audit_logs',
    'change_logs',
]


def get_table_info(table_name: str) -> Optional[Dict[str, Any]]:
    """获取表的三维分类信息"""
    info = TABLE_REGISTRY.get(table_name)
    if info:
        return {
            'table_name': table_name,
            'category': info['category'].value,
            'module': info['module'].value,
            'heat': info['heat'].value,
            'shard_db': info['shard_db']
        }
    return None


def get_tables_by_category(category: TableCategory) -> list:
    """按分类获取表列表"""
    return [name for name, info in TABLE_REGISTRY.items()
            if info['category'] == category]


def get_tables_by_shard(shard_db: str) -> list:
    """按分片库获取表列表"""
    return [name for name, info in TABLE_REGISTRY.items()
            if info['shard_db'] == shard_db]


def get_all_shard_dbs() -> list:
    """获取所有分片库列表（去重）"""
    return list(set(info['shard_db'] for info in TABLE_REGISTRY.values()))


def get_migration_targets() -> list:
    """获取需要迁移的表列表（按优先级排序）"""
    return PRIORITY_MIGRATION_TABLES[:]
