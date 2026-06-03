#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core module for MTSCOS AI Project - Enhanced Version 2.5
用户设置管理系统 - 基于权限和规则的动态功能显示
"""

__version__ = "3.1.0"
__author__ = "MTSCOS AI Team"

from .config import config, ConfigManager
from .database import db, DatabaseManager
from .logging import logger, Logger
from .system import system, SystemManager, PerformanceMonitor
from .ai import ai_service, AIService, AICache
from .utils import FileUtils, StringUtils, TimeUtils, ValidationUtils, DataUtils
from .exceptions import (
    MTSCOSError, DatabaseError, ConfigurationError, APIError,
    ValidationError, AuthenticationError, AuthorizationError,
    ResourceNotFoundError, RateLimitError, AIError, FileError
)
from .cache import cache, CacheManager, LocalCache, RedisCache
from .queue import queue_manager, QueueManager, TaskQueue, Task, QueueWorker
from .scheduler import scheduler, Scheduler, ScheduledTask
from .intelligence import intelligence, IntelligenceEngine, PatternAnalyzer, TextAnalyzer, DataClassifier
from .knowledge_graph import knowledge_graph, KnowledgeGraph, GraphQuery, ReasoningEngine
from .recommendation import recommendation_engine, RecommendationEngine, User, Item, RatingMatrix
from .education import (
    researcher_ai, expert_ai, teacher_ai, student_ai,
    ResearcherAI, ExpertAI, TeacherAI, StudentAI,
    QuestionBankOptimizer, CurriculumMatcher,
    curriculum_matcher, question_bank_optimizer
)
from .question_bank import (
    question_bank_expander, exam_paper_collector, practice_generator,
    QuestionBankExpander, ExamPaperCollector, PracticeGenerator
)
from .settings import (
    settings_manager, SettingsManager, UserRole, FeatureRule,
    SettingGroup, SettingItem
)
from .session import (
    session_manager, SessionManager, Session, SessionStatus, SessionEvent, SessionLog
)
from .encryption import (
    encryption_manager, DatabaseEncryptionManager, KeyManager, EncryptionKey,
    EncryptionLevel, EncryptionAlgorithm, EncryptedTable, EncryptedColumn
)
from .grade_management import (
    exam_manager, ExamManager, Exam, StudentGrade,
    GradeLevel, Subject, ExamStatus, ExamType, SubjectMaxScore
)
from .teacher_management import (
    teacher_manager, TeacherManager, Teacher,
    TeacherStatus, TeacherSpecialty
)
from .application_management import (
    application_manager, ApplicationManager, Application,
    ApplicationType, ApplicationStatus
)
from .event_tracker import (
    event_tracker, EventTracker, SystemEvent, EventCategory,
    EventAction, EventPriority, EventContext, track_event
)
from .system_integrator import (
    system_integrator, SystemIntegrator, ActionWrapper,
    settings_manager as global_settings_manager, SettingsManager,
    track_settings_change, validate_system, init_system
)

__all__ = [
    # Version
    '__version__',
    # Configuration
    'config',
    'ConfigManager',
    # Database
    'db',
    'DatabaseManager',
    # Logging
    'logger',
    'Logger',
    # System
    'system',
    'SystemManager',
    'PerformanceMonitor',
    # AI Service
    'ai_service',
    'AIService',
    'AICache',
    # Cache
    'cache',
    'CacheManager',
    'LocalCache',
    'RedisCache',
    # Queue
    'queue_manager',
    'QueueManager',
    'TaskQueue',
    'Task',
    'QueueWorker',
    # Scheduler
    'scheduler',
    'Scheduler',
    'ScheduledTask',
    # Intelligence
    'intelligence',
    'IntelligenceEngine',
    'PatternAnalyzer',
    'TextAnalyzer',
    'DataClassifier',
    # Knowledge Graph
    'knowledge_graph',
    'KnowledgeGraph',
    'GraphQuery',
    'ReasoningEngine',
    # Recommendation
    'recommendation_engine',
    'RecommendationEngine',
    'User',
    'Item',
    'RatingMatrix',
    # Education AI
    'researcher_ai',
    'expert_ai',
    'teacher_ai',
    'student_ai',
    'ResearcherAI',
    'ExpertAI',
    'TeacherAI',
    'StudentAI',
    'QuestionBankOptimizer',
    'CurriculumMatcher',
    'curriculum_matcher',
    'question_bank_optimizer',
    # Question Bank
    'question_bank_expander',
    'exam_paper_collector',
    'practice_generator',
    'QuestionBankExpander',
    'ExamPaperCollector',
    'PracticeGenerator',
    # Settings
    'settings_manager',
    'SettingsManager',
    'UserRole',
    'FeatureRule',
    'SettingGroup',
    'SettingItem',
    # Utils
    'FileUtils',
    'StringUtils',
    'TimeUtils',
    'ValidationUtils',
    'DataUtils',
    # Exceptions
    'MTSCOSError',
    'DatabaseError',
    'ConfigurationError',
    'APIError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'ResourceNotFoundError',
    'RateLimitError',
    'AIError',
    'FileError',
    # Event Tracking
    'event_tracker',
    'EventTracker',
    'SystemEvent',
    'EventCategory',
    'EventAction',
    'EventPriority',
    'EventContext',
    'track_event',
    # System Integration
    'system_integrator',
    'SystemIntegrator',
    'ActionWrapper',
    'global_settings_manager',
    'SettingsManager',
    'track_settings_change',
    'validate_system',
    'init_system',
    # Functions
    'init',
    'get_version'
]

def get_version():
    """Get core module version"""
    return __version__

def init():
    """Initialize core module"""
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
