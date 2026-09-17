#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core module for MTSCOS AI Project - Enhanced Version 2.5
用户设置管理系统 - 基于权限和规则的动态功能显示

注意：本包采用 PEP 562 惰性加载。`import core.db_path` 等子模块导入
不再连带触发 database/ai/encryption 等 25 个重型兄弟子模块的初始化
（在 OneDrive 云盘 + 4.9GB 库的场景下，急切导入会让启动耗时 6 分钟以上）。
公开 API 完全兼容：`from core import db` / `core.logger` 按需加载并缓存。
"""

__version__ = "3.1.0"
__author__ = "MTSCOS AI Team"

import importlib

# 公开属性名 -> 提供它的相对子模块路径（按需惰性导入）
# 注意：原始代码中 .system_integrator 在 .settings 之后导入，
# 因此 'SettingsManager' 以 .system_integrator 为准（后者覆盖前者）。
_NAME_TO_SUBMOD = {
    # .config
    'config': '.config', 'ConfigManager': '.config',
    # .database
    'db': '.database', 'DatabaseManager': '.database',
    # .logging
    'logger': '.logging', 'Logger': '.logging',
    # .system
    'system': '.system', 'SystemManager': '.system', 'PerformanceMonitor': '.system',
    # .ai
    'ai_service': '.ai', 'AIService': '.ai', 'AICache': '.ai',
    # .utils
    'FileUtils': '.utils', 'StringUtils': '.utils', 'TimeUtils': '.utils',
    'ValidationUtils': '.utils', 'DataUtils': '.utils',
    # .exceptions
    'MTSCOSError': '.exceptions', 'DatabaseError': '.exceptions',
    'ConfigurationError': '.exceptions', 'APIError': '.exceptions',
    'ValidationError': '.exceptions', 'AuthenticationError': '.exceptions',
    'AuthorizationError': '.exceptions', 'ResourceNotFoundError': '.exceptions',
    'RateLimitError': '.exceptions', 'AIError': '.exceptions', 'FileError': '.exceptions',
    # .cache
    'cache': '.cache', 'CacheManager': '.cache', 'LocalCache': '.cache', 'RedisCache': '.cache',
    # .queue
    'queue_manager': '.queue', 'QueueManager': '.queue', 'TaskQueue': '.queue',
    'Task': '.queue', 'QueueWorker': '.queue',
    # .scheduler
    'scheduler': '.scheduler', 'Scheduler': '.scheduler', 'ScheduledTask': '.scheduler',
    # .intelligence
    'intelligence': '.intelligence', 'IntelligenceEngine': '.intelligence',
    'PatternAnalyzer': '.intelligence', 'TextAnalyzer': '.intelligence',
    'DataClassifier': '.intelligence',
    # .knowledge_graph
    'knowledge_graph': '.knowledge_graph', 'KnowledgeGraph': '.knowledge_graph',
    'GraphQuery': '.knowledge_graph', 'ReasoningEngine': '.knowledge_graph',
    # .recommendation
    'recommendation_engine': '.recommendation', 'RecommendationEngine': '.recommendation',
    'User': '.recommendation', 'Item': '.recommendation', 'RatingMatrix': '.recommendation',
    # .education
    'researcher_ai': '.education', 'expert_ai': '.education', 'teacher_ai': '.education',
    'student_ai': '.education', 'ResearcherAI': '.education', 'ExpertAI': '.education',
    'TeacherAI': '.education', 'StudentAI': '.education',
    'QuestionBankOptimizer': '.education', 'CurriculumMatcher': '.education',
    'curriculum_matcher': '.education', 'question_bank_optimizer': '.education',
    # .question_bank
    'question_bank_expander': '.question_bank', 'exam_paper_collector': '.question_bank',
    'practice_generator': '.question_bank', 'QuestionBankExpander': '.question_bank',
    'ExamPaperCollector': '.question_bank', 'PracticeGenerator': '.question_bank',
    # .settings
    'settings_manager': '.settings', 'UserRole': '.settings', 'FeatureRule': '.settings',
    'SettingGroup': '.settings', 'SettingItem': '.settings',
    # .session
    'session_manager': '.session', 'SessionManager': '.session', 'Session': '.session',
    'SessionStatus': '.session', 'SessionEvent': '.session', 'SessionLog': '.session',
    # .encryption
    'encryption_manager': '.encryption', 'DatabaseEncryptionManager': '.encryption',
    'KeyManager': '.encryption', 'EncryptionKey': '.encryption',
    'EncryptionLevel': '.encryption', 'EncryptionAlgorithm': '.encryption',
    'EncryptedTable': '.encryption', 'EncryptedColumn': '.encryption',
    # .grade_management
    'exam_manager': '.grade_management', 'ExamManager': '.grade_management',
    'Exam': '.grade_management', 'StudentGrade': '.grade_management',
    'GradeLevel': '.grade_management', 'Subject': '.grade_management',
    'ExamStatus': '.grade_management', 'ExamType': '.grade_management',
    'SubjectMaxScore': '.grade_management',
    # .teacher_management
    'teacher_manager': '.teacher_management', 'TeacherManager': '.teacher_management',
    'Teacher': '.teacher_management', 'TeacherStatus': '.teacher_management',
    'TeacherSpecialty': '.teacher_management',
    # .application_management
    'application_manager': '.application_management', 'ApplicationManager': '.application_management',
    'Application': '.application_management', 'ApplicationType': '.application_management',
    'ApplicationStatus': '.application_management',
    # .event_tracker
    'event_tracker': '.event_tracker', 'EventTracker': '.event_tracker',
    'SystemEvent': '.event_tracker', 'EventCategory': '.event_tracker',
    'EventAction': '.event_tracker', 'EventPriority': '.event_tracker',
    'EventContext': '.event_tracker', 'track_event': '.event_tracker',
    # .system_integrator（原代码末尾导入，SettingsManager 以此为准）
    'system_integrator': '.system_integrator', 'SystemIntegrator': '.system_integrator',
    'ActionWrapper': '.system_integrator', 'global_settings_manager': '.system_integrator',
    'SettingsManager': '.system_integrator', 'track_settings_change': '.system_integrator',
    'validate_system': '.system_integrator', 'init_system': '.system_integrator',
}

# 缓存已加载的子模块导出的所有公开名，避免重复 import 开销
_LOADED_SUBMODS = set()


def _lazy_load(submod_rel):
    """惰性导入子模块，并把其所有公开名一次性缓存进本包 globals。"""
    if submod_rel in _LOADED_SUBMODS:
        return
    mod = importlib.import_module(submod_rel, __name__)
    g = globals()
    for attr_name, sm in _NAME_TO_SUBMOD.items():
        if sm == submod_rel and attr_name not in g:
            if hasattr(mod, attr_name):
                g[attr_name] = getattr(mod, attr_name)
    _LOADED_SUBMODS.add(submod_rel)


def __getattr__(name):
    submod = _NAME_TO_SUBMOD.get(name)
    if submod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    _lazy_load(submod)
    g = globals()
    if name in g:
        return g[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(list(globals().keys()) + list(_NAME_TO_SUBMOD.keys()) + ['__all__']))


__all__ = [
    # Version
    '__version__',
    # Configuration
    'config', 'ConfigManager',
    # Database
    'db', 'DatabaseManager',
    # Logging
    'logger', 'Logger',
    # System
    'system', 'SystemManager', 'PerformanceMonitor',
    # AI Service
    'ai_service', 'AIService', 'AICache',
    # Cache
    'cache', 'CacheManager', 'LocalCache', 'RedisCache',
    # Queue
    'queue_manager', 'QueueManager', 'TaskQueue', 'Task', 'QueueWorker',
    # Scheduler
    'scheduler', 'Scheduler', 'ScheduledTask',
    # Intelligence
    'intelligence', 'IntelligenceEngine', 'PatternAnalyzer', 'TextAnalyzer', 'DataClassifier',
    # Knowledge Graph
    'knowledge_graph', 'KnowledgeGraph', 'GraphQuery', 'ReasoningEngine',
    # Recommendation
    'recommendation_engine', 'RecommendationEngine', 'User', 'Item', 'RatingMatrix',
    # Education AI
    'researcher_ai', 'expert_ai', 'teacher_ai', 'student_ai',
    'ResearcherAI', 'ExpertAI', 'TeacherAI', 'StudentAI',
    'QuestionBankOptimizer', 'CurriculumMatcher',
    'curriculum_matcher', 'question_bank_optimizer',
    # Question Bank
    'question_bank_expander', 'exam_paper_collector', 'practice_generator',
    'QuestionBankExpander', 'ExamPaperCollector', 'PracticeGenerator',
    # Settings
    'settings_manager', 'SettingsManager', 'UserRole', 'FeatureRule',
    'SettingGroup', 'SettingItem',
    # Utils
    'FileUtils', 'StringUtils', 'TimeUtils', 'ValidationUtils', 'DataUtils',
    # Exceptions
    'MTSCOSError', 'DatabaseError', 'ConfigurationError', 'APIError',
    'ValidationError', 'AuthenticationError', 'AuthorizationError',
    'ResourceNotFoundError', 'RateLimitError', 'AIError', 'FileError',
    # Event Tracking
    'event_tracker', 'EventTracker', 'SystemEvent', 'EventCategory',
    'EventAction', 'EventPriority', 'EventContext', 'track_event',
    # System Integration
    'system_integrator', 'SystemIntegrator', 'ActionWrapper',
    'global_settings_manager', 'SettingsManager',
    'track_settings_change', 'validate_system', 'init_system',
    # Functions
    'init', 'get_version',
]


def get_version():
    """Get core module version"""
    return __version__


def init():
    """Initialize core module（显式导入所需子模块，避免依赖惰性加载顺序）"""
    from .logging import logger
    from .database import db
    from .ai import ai_service
    from .cache import cache

    logger.info(f"Initializing MTSCOS Core Module v{__version__}")

    try:
        db.execute("SELECT 1")
        logger.info("Database connection established")
    except Exception as e:
        logger.warning(f"Database initialization check: {e}")

    logger.info(f"AI service status: {'available' if ai_service.available else 'not available'}")
    logger.info(f"Cache backend: {cache.backend}")
    logger.info(f"Intelligence Engine: initialized")
    logger.info(f"Knowledge Graph: initialized")
    logger.info(f"Recommendation Engine: initialized")
    logger.info(f"Education AI: Researcher, Expert, Teacher, Student")
    logger.info(f"Question Bank: Expander, Exam Collector, Practice Generator")
    logger.info(f"Settings Manager: initialized with roles and permissions")
    logger.info("Core module initialized successfully")
