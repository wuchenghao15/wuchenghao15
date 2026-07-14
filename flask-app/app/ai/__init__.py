# -*- coding: utf-8 -*-
"""
AI模块
包含各种AI员工和智能系统
"""

from .question_bank_ai import (
    QuestionBankAIAssistant,
    ListeningQuestion,
    ListeningLanguage,
    ListeningAccent,
    ListeningVoice,
    ListeningDifficulty,
    ListeningTopic,
    QuestionBankAIStats
)

from .student_learning_optimizer import (
    StudentLearningOptimizer,
    StudentPerformanceAnalyzer,
    KnowledgeGapIdentifier,
    LearningPathOptimizer,
    ExamStrategyAdvisor,
    student_learning_optimizer
)

from .maintenance_ai import (
    MaintenanceAIEmployee,
    DatabaseCleaner,
    LogCleaner,
    BackupManager,
    SystemHealthChecker,
    maintenance_ai
)

from .self_learning_system import (
    SelfLearningSystem,
    LearningPattern,
    SystemInsight,
    self_learning_system
)

from .ai_skill_evolution import (
    AISkillEvolutionSystem,
    AIEmployeeEvolution,
    SkillMetric,
    ThinkingProfile,
    ai_skill_evolution_system
)

__all__ = [
    # 题库优化
    'QuestionBankAIAssistant',
    'ListeningQuestion',
    'ListeningLanguage',
    'ListeningAccent',
    'ListeningVoice',
    'ListeningDifficulty',
    'ListeningTopic',
    'QuestionBankAIStats',
    
    # 学习优化
    'StudentLearningOptimizer',
    'StudentPerformanceAnalyzer',
    'KnowledgeGapIdentifier',
    'LearningPathOptimizer',
    'ExamStrategyAdvisor',
    'student_learning_optimizer',
    
    # 系统维护
    'MaintenanceAIEmployee',
    'DatabaseCleaner',
    'LogCleaner',
    'BackupManager',
    'SystemHealthChecker',
    'maintenance_ai',
    
    # 自学习系统
    'SelfLearningSystem',
    'LearningPattern',
    'SystemInsight',
    'self_learning_system',
    
    # 技能进化系统
    'AISkillEvolutionSystem',
    'AIEmployeeEvolution',
    'SkillMetric',
    'ThinkingProfile',
    'ai_skill_evolution_system'
]
