# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试系统数据模型
包含考试、试卷、题目、答案、成绩等核心模型
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4


class QuestionType(Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"      # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    TRUE_FALSE = "true_false"            # 判断题
    FILL_BLANK = "fill_blank"            # 填空题
    SHORT_ANSWER = "short_answer"        # 简答题
    ESSAY = "essay"                      # 论述题
    LISTENING = "listening"              # 听力题
    READING = "reading"                  # 阅读题


class ExamStatus(Enum):
    """考试状态"""
    DRAFT = "draft"              # 草稿
    ACTIVE = "active"            # 启用
    INACTIVE = "inactive"        # 停用
    ARCHIVED = "archived"        # 归档


class ExamPaperStatus(Enum):
    """试卷状态"""
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    TIMEOUT = "timeout"          # 超时


@dataclass
class Question:
    """题目模型"""
    id: str = field(default_factory=lambda: str(uuid4()))
    exam_id: Optional[str] = None
    type: QuestionType = QuestionType.SINGLE_CHOICE
    content: str = ""
    options: List[Dict[str, str]] = field(default_factory=list)  # [{"key": "A", "value": "..."}]
    correct_answer: Union[str, List[str]] = ""
    difficulty: int = 1  # 1-5
    points: float = 1.0
    audio_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    explanation: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'type': self.type.value,
            'content': self.content,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'difficulty': self.difficulty,
            'points': self.points,
            'audio_url': self.audio_url,
            'tags': self.tags,
            'explanation': self.explanation,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Exam:
    """考试模型"""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    language: str = "zh"
    level: str = "intermediate"  # beginner, intermediate, advanced, expert
    duration: int = 60  # 分钟
    question_count: int = 20
    total_points: float = 100.0
    passing_score: float = 60.0
    status: ExamStatus = ExamStatus.DRAFT
    shuffle_questions: bool = True
    shuffle_options: bool = True
    allow_retake: bool = False
    max_retakes: int = 3
    time_between_retakes: int = 0  # 分钟
    exam_type: str = "simulation"  # simulation: 拟真试题, real: 历年真题
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'language': self.language,
            'level': self.level,
            'duration': self.duration,
            'question_count': self.question_count,
            'total_points': self.total_points,
            'passing_score': self.passing_score,
            'status': self.status.value,
            'shuffle_questions': self.shuffle_questions,
            'shuffle_options': self.shuffle_options,
            'allow_retake': self.allow_retake,
            'max_retakes': self.max_retakes,
            'time_between_retakes': self.time_between_retakes,
            'exam_type': self.exam_type,
            'exam_type_label': '历年真题' if self.exam_type == 'real' else '拟真试题',
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ExamPaper:
    """试卷模型"""
    id: str = field(default_factory=lambda: str(uuid4()))
    exam_id: str = ""
    user_id: str = ""
    questions: List[str] = field(default_factory=list)  # question ids
    scores: Dict[str, float] = field(default_factory=dict)  # {question_id: score}
    answers: Dict[str, Any] = field(default_factory=dict)  # {question_id: answer}
    status: ExamPaperStatus = ExamPaperStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'user_id': self.user_id,
            'questions': self.questions,
            'scores': self.scores,
            'answers': self.answers,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ExamResult:
    """考试结果模型"""
    id: str = field(default_factory=lambda: str(uuid4()))
    exam_paper_id: str = ""
    exam_id: str = ""
    user_id: str = ""
    total_score: float = 0.0
    correct_count: int = 0
    total_count: int = 0
    accuracy: float = 0.0
    time_taken: int = 0  # 秒
    passed: bool = False
    analysis: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'exam_paper_id': self.exam_paper_id,
            'exam_id': self.exam_id,
            'user_id': self.user_id,
            'total_score': self.total_score,
            'correct_count': self.correct_count,
            'total_count': self.total_count,
            'accuracy': self.accuracy,
            'time_taken': self.time_taken,
            'passed': self.passed,
            'analysis': self.analysis,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class QuestionAnalysis:
    """题目分析模型"""
    question_id: str = ""
    user_id: str = ""
    exam_id: str = ""
    is_correct: bool = False
    time_spent: int = 0  # 秒
    attempts: int = 1
    selected_answer: Any = None
    correct_answer: Any = None
    difficulty: int = 1
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'question_id': self.question_id,
            'user_id': self.user_id,
            'exam_id': self.exam_id,
            'is_correct': self.is_correct,
            'time_spent': self.time_spent,
            'attempts': self.attempts,
            'selected_answer': self.selected_answer,
            'correct_answer': self.correct_answer,
            'difficulty': self.difficulty,
            'tags': self.tags,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class UserExamProgress:
    """用户考试进度模型"""
    user_id: str = ""
    exam_id: str = ""
    current_question: int = 0
    answers: Dict[str, Any] = field(default_factory=dict)
    time_spent: int = 0  # 秒
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'exam_id': self.exam_id,
            'current_question': self.current_question,
            'answers': self.answers,
            'time_spent': self.time_spent,
            'started_at': self.started_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ExamTemplate:
    """考试模板模型"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    language: str = "zh"
    level: str = "intermediate"
    duration: int = 60
    question_count: int = 20
    question_types: List[QuestionType] = field(default_factory=list)
    difficulty_distribution: Dict[int, float] = field(default_factory=dict)  # {1: 0.2, 2: 0.3, ...}
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'language': self.language,
            'level': self.level,
            'duration': self.duration,
            'question_count': self.question_count,
            'question_types': [qt.value for qt in self.question_types],
            'difficulty_distribution': self.difficulty_distribution,
            'tags': self.tags,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
