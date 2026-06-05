# -*- coding: utf-8 -*-
"""
AI模块
包含各种AI员工和智能系统
"""

from .question_bank_ai import (
    QuestionBankAIEmployee,
    QuestionAnalyzer,
    QuestionOptimizer,
    QuestionStatistics,
    question_bank_ai
)

from .student_learning_optimizer import (
    StudentLearningOptimizer,
    StudentPerformanceAnalyzer,
    KnowledgeGapIdentifier,
    LearningPathOptimizer,
    ExamStrategyAdvisor,
    student_learning_optimizer
)

__all__ = [
    # 题库优化
    'QuestionBankAIEmployee',
    'QuestionAnalyzer',
    'QuestionOptimizer',
    'QuestionStatistics',
    'question_bank_ai',
    
    # 学习优化
    'StudentLearningOptimizer',
    'StudentPerformanceAnalyzer',
    'KnowledgeGapIdentifier',
    'LearningPathOptimizer',
    'ExamStrategyAdvisor',
    'student_learning_optimizer'
]
