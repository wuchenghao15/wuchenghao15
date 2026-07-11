#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学模型与解题模型数据模型
包含数学知识模型、解题方法、解题步骤等核心模型
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class MathConcept:
    """数学概念模型"""
    id: str = field(default_factory=lambda: f"mc_{uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    category: str = ""
    subcategory: str = ""
    level: int = 1
    prerequisites: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    theorems: List[str] = field(default_factory=list)
    examples: List[Dict] = field(default_factory=list)
    difficulty: int = 1
    source: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'subcategory': self.subcategory,
            'level': self.level,
            'prerequisites': self.prerequisites,
            'formulas': self.formulas,
            'theorems': self.theorems,
            'examples': self.examples,
            'difficulty': self.difficulty,
            'source': self.source,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class SolutionMethod:
    """解题方法模型"""
    id: str = field(default_factory=lambda: f"sm_{uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    category: str = ""
    method_type: str = "general"
    applicable_topics: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    key_formulas: List[str] = field(default_factory=list)
    examples: List[Dict] = field(default_factory=list)
    difficulty: int = 1
    success_rate: float = 0.0
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'method_type': self.method_type,
            'applicable_topics': self.applicable_topics,
            'steps': self.steps,
            'key_formulas': self.key_formulas,
            'examples': self.examples,
            'difficulty': self.difficulty,
            'success_rate': self.success_rate,
            'usage_count': self.usage_count,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ProblemSolution:
    """解题过程模型"""
    id: str = field(default_factory=lambda: f"ps_{uuid4().hex[:12]}")
    problem_id: str = ""
    problem_content: str = ""
    problem_type: str = ""
    difficulty: int = 1
    subject: str = "math"
    solution_method_id: str = ""
    solution_method_name: str = ""
    steps: List[Dict] = field(default_factory=list)
    final_answer: str = ""
    answer_formatted: str = ""
    reasoning: str = ""
    verification: str = ""
    time_spent: float = 0.0
    is_correct: bool = True
    user_id: str = ""
    attempts: int = 1
    hint_used: int = 0
    error_analysis: str = ""
    related_concepts: List[str] = field(default_factory=list)
    related_formulas: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'problem_content': self.problem_content,
            'problem_type': self.problem_type,
            'difficulty': self.difficulty,
            'subject': self.subject,
            'solution_method_id': self.solution_method_id,
            'solution_method_name': self.solution_method_name,
            'steps': self.steps,
            'final_answer': self.final_answer,
            'answer_formatted': self.answer_formatted,
            'reasoning': self.reasoning,
            'verification': self.verification,
            'time_spent': self.time_spent,
            'is_correct': self.is_correct,
            'user_id': self.user_id,
            'attempts': self.attempts,
            'hint_used': self.hint_used,
            'error_analysis': self.error_analysis,
            'related_concepts': self.related_concepts,
            'related_formulas': self.related_formulas,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class MathProblem:
    """数学题目模型"""
    id: str = field(default_factory=lambda: f"mp_{uuid4().hex[:12]}")
    content: str = ""
    problem_type: str = "calculation"
    category: str = ""
    subcategory: str = ""
    difficulty: int = 1
    options: List[Dict] = field(default_factory=list)
    correct_answer: str = ""
    answer_explanation: str = ""
    related_concepts: List[str] = field(default_factory=list)
    related_formulas: List[str] = field(default_factory=list)
    applicable_methods: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    solution_steps: List[Dict] = field(default_factory=list)
    points: float = 1.0
    estimated_time: int = 5
    source: str = ""
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'problem_type': self.problem_type,
            'category': self.category,
            'subcategory': self.subcategory,
            'difficulty': self.difficulty,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'answer_explanation': self.answer_explanation,
            'related_concepts': self.related_concepts,
            'related_formulas': self.related_formulas,
            'applicable_methods': self.applicable_methods,
            'hints': self.hints,
            'solution_steps': self.solution_steps,
            'points': self.points,
            'estimated_time': self.estimated_time,
            'source': self.source,
            'tags': self.tags,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class MathKnowledgeGraph:
    """数学知识图谱节点"""
    id: str = field(default_factory=lambda: f"mkg_{uuid4().hex[:12]}")
    node_type: str = "concept"
    name: str = ""
    description: str = ""
    category: str = ""
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    related_nodes: List[str] = field(default_factory=list)
    weight: float = 1.0
    properties: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'node_type': self.node_type,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'parents': self.parents,
            'children': self.children,
            'related_nodes': self.related_nodes,
            'weight': self.weight,
            'properties': self.properties,
            'created_at': self.created_at.isoformat()
        }


MATH_CATEGORIES = {
    'algebra': {
        'name': '代数',
        'subcategories': ['一元一次方程', '一元二次方程', '方程组', '不等式', '函数', '因式分解', '分式', '根式']
    },
    'geometry': {
        'name': '几何',
        'subcategories': ['三角形', '四边形', '圆', '立体几何', '坐标系', '相似三角形', '全等三角形']
    },
    'calculus': {
        'name': '微积分',
        'subcategories': ['极限', '导数', '积分', '微分方程', '偏导数', '级数']
    },
    'probability': {
        'name': '概率统计',
        'subcategories': ['概率基础', '随机变量', '分布', '统计推断', '假设检验', '回归分析']
    },
    'number_theory': {
        'name': '数论',
        'subcategories': ['整除', '同余', '素数', '不定方程', '进位制']
    },
    'combinatorics': {
        'name': '组合数学',
        'subcategories': ['排列组合', '二项式定理', '递推', '图论基础']
    }
}

SOLUTION_METHOD_TYPES = [
    'general',
    'formula_based',
    'transformation',
    'classification',
    'reduction',
    'constructive',
    'induction',
    'reverse',
    'graphical',
    'algebraic'
]

PROBLEM_TYPES = [
    'calculation',
    'proof',
    'application',
    'multiple_choice',
    'fill_blank',
    'short_answer',
    'synthesis'
]
