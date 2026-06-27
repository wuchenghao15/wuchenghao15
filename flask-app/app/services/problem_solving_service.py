#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学模型与解题服务
提供数学概念管理、解题方法管理、数学题库管理、解题过程记录等功能
"""

import os
import sys
import json
import sqlite3
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logging import logger
from app.models.math_models import (
    MathConcept, SolutionMethod, ProblemSolution, MathProblem,
    MATH_CATEGORIES, SOLUTION_METHOD_TYPES, PROBLEM_TYPES
)


class MathModelService:
    """数学模型与解题服务"""

    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

        self._init_tables()
        self._init_default_data()
        logger.info("[数学模型服务] 初始化完成")

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        """初始化数据库表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS math_concepts (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        subcategory TEXT,
                        level INTEGER DEFAULT 1,
                        prerequisites TEXT DEFAULT '[]',
                        formulas TEXT DEFAULT '[]',
                        theorems TEXT DEFAULT '[]',
                        examples TEXT DEFAULT '[]',
                        difficulty INTEGER DEFAULT 1,
                        source TEXT,
                        tags TEXT DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS solution_methods (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        method_type TEXT DEFAULT 'general',
                        applicable_topics TEXT DEFAULT '[]',
                        steps TEXT DEFAULT '[]',
                        key_formulas TEXT DEFAULT '[]',
                        examples TEXT DEFAULT '[]',
                        difficulty INTEGER DEFAULT 1,
                        success_rate REAL DEFAULT 0.0,
                        usage_count INTEGER DEFAULT 0,
                        tags TEXT DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS math_problems (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        problem_type TEXT DEFAULT 'calculation',
                        category TEXT,
                        subcategory TEXT,
                        difficulty INTEGER DEFAULT 1,
                        options TEXT DEFAULT '[]',
                        correct_answer TEXT,
                        answer_explanation TEXT,
                        related_concepts TEXT DEFAULT '[]',
                        related_formulas TEXT DEFAULT '[]',
                        applicable_methods TEXT DEFAULT '[]',
                        hints TEXT DEFAULT '[]',
                        solution_steps TEXT DEFAULT '[]',
                        points REAL DEFAULT 1.0,
                        estimated_time INTEGER DEFAULT 5,
                        source TEXT,
                        tags TEXT DEFAULT '[]',
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS problem_solutions (
                        id TEXT PRIMARY KEY,
                        problem_id TEXT,
                        problem_content TEXT,
                        problem_type TEXT,
                        difficulty INTEGER DEFAULT 1,
                        subject TEXT DEFAULT 'math',
                        solution_method_id TEXT,
                        solution_method_name TEXT,
                        steps TEXT DEFAULT '[]',
                        final_answer TEXT,
                        answer_formatted TEXT,
                        reasoning TEXT,
                        verification TEXT,
                        time_spent REAL DEFAULT 0.0,
                        is_correct INTEGER DEFAULT 1,
                        user_id TEXT,
                        attempts INTEGER DEFAULT 1,
                        hint_used INTEGER DEFAULT 0,
                        error_analysis TEXT,
                        related_concepts TEXT DEFAULT '[]',
                        related_formulas TEXT DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS math_knowledge_graph (
                        id TEXT PRIMARY KEY,
                        node_type TEXT DEFAULT 'concept',
                        name TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        parents TEXT DEFAULT '[]',
                        children TEXT DEFAULT '[]',
                        related_nodes TEXT DEFAULT '[]',
                        weight REAL DEFAULT 1.0,
                        properties TEXT DEFAULT '{}',
                        created_at TEXT NOT NULL
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mc_category ON math_concepts(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mc_difficulty ON math_concepts(difficulty)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sm_category ON solution_methods(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sm_method_type ON solution_methods(method_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mp_category ON math_problems(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mp_difficulty ON math_problems(difficulty)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ps_problem_id ON problem_solutions(problem_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ps_user_id ON problem_solutions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mkg_category ON math_knowledge_graph(category)')

                conn.commit()
                logger.info("[数学模型服务] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[数学模型服务] 初始化表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _init_default_data(self):
        """初始化默认数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM math_concepts")
                count = cursor.fetchone()[0]
                if count > 0:
                    return

            self._seed_default_concepts()
            self._seed_default_methods()
            self._seed_default_problems()
            logger.info("[数学模型服务] 默认数据初始化完成")
        except Exception as e:
            logger.error(f"[数学模型服务] 初始化默认数据失败: {e}")

    def _seed_default_concepts(self):
        """种子数学概念数据"""
        concepts = [
            {
                'name': '一元一次方程',
                'description': '只含有一个未知数，且未知数的最高次数是1的整式方程',
                'category': 'algebra',
                'subcategory': '一元一次方程',
                'level': 1,
                'prerequisites': ['有理数运算', '整式的加减'],
                'formulas': ['ax + b = 0 (a≠0)', 'x = -b/a'],
                'theorems': ['等式的基本性质'],
                'difficulty': 1,
                'tags': ['基础', '方程', '代数']
            },
            {
                'name': '一元二次方程',
                'description': '只含有一个未知数，且未知数的最高次数是2的整式方程',
                'category': 'algebra',
                'subcategory': '一元二次方程',
                'level': 2,
                'prerequisites': ['一元一次方程', '因式分解'],
                'formulas': ['ax² + bx + c = 0 (a≠0)', 'x = (-b ± √(b²-4ac))/(2a)', 'Δ = b² - 4ac'],
                'theorems': ['韦达定理', '判别式定理'],
                'difficulty': 2,
                'tags': ['方程', '二次', '代数']
            },
            {
                'name': '勾股定理',
                'description': '直角三角形两直角边的平方和等于斜边的平方',
                'category': 'geometry',
                'subcategory': '三角形',
                'level': 2,
                'prerequisites': ['三角形基本概念', '平方根'],
                'formulas': ['a² + b² = c²', 'c = √(a² + b²)'],
                'theorems': ['勾股定理', '勾股定理逆定理'],
                'difficulty': 2,
                'tags': ['几何', '三角形', '定理']
            },
            {
                'name': '导数基础',
                'description': '函数在某一点处的瞬时变化率',
                'category': 'calculus',
                'subcategory': '导数',
                'level': 3,
                'prerequisites': ['极限基础', '函数'],
                'formulas': ['f\'(x) = lim(Δx→0) [f(x+Δx)-f(x)]/Δx', '(x^n)\' = nx^(n-1)', '(sinx)\' = cosx'],
                'theorems': ['费马定理', '罗尔定理', '拉格朗日中值定理'],
                'difficulty': 3,
                'tags': ['微积分', '导数', '高等数学']
            },
            {
                'name': '古典概型',
                'description': '随机试验所有可能结果有限且各结果等可能的概率模型',
                'category': 'probability',
                'subcategory': '概率基础',
                'level': 2,
                'prerequisites': ['排列组合基础'],
                'formulas': ['P(A) = m/n', 'P(A∪B) = P(A) + P(B) - P(A∩B)'],
                'theorems': ['加法原理', '乘法原理'],
                'difficulty': 2,
                'tags': ['概率', '统计', '基础']
            },
            {
                'name': '等差数列',
                'description': '从第二项起，每一项与前一项的差等于同一个常数的数列',
                'category': 'algebra',
                'subcategory': '数列',
                'level': 2,
                'prerequisites': ['数列基础'],
                'formulas': ['an = a1 + (n-1)d', 'Sn = n(a1+an)/2', 'Sn = na1 + n(n-1)d/2'],
                'theorems': ['等差中项定理'],
                'difficulty': 2,
                'tags': ['数列', '代数', '基础']
            }
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            for i, c in enumerate(concepts):
                concept = MathConcept(
                    id=f"mc_seed_{i+1:03d}",
                    name=c['name'],
                    description=c['description'],
                    category=c['category'],
                    subcategory=c['subcategory'],
                    level=c['level'],
                    prerequisites=c['prerequisites'],
                    formulas=c['formulas'],
                    theorems=c['theorems'],
                    difficulty=c['difficulty'],
                    tags=c['tags'],
                    created_at=datetime.fromisoformat(now),
                    updated_at=datetime.fromisoformat(now)
                )
                cursor.execute('''
                    INSERT OR IGNORE INTO math_concepts
                    (id, name, description, category, subcategory, level, prerequisites, formulas,
                     theorems, examples, difficulty, source, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    concept.id, concept.name, concept.description, concept.category, concept.subcategory,
                    concept.level, json.dumps(concept.prerequisites, ensure_ascii=False),
                    json.dumps(concept.formulas, ensure_ascii=False),
                    json.dumps(concept.theorems, ensure_ascii=False),
                    json.dumps(concept.examples, ensure_ascii=False),
                    concept.difficulty, concept.source,
                    json.dumps(concept.tags, ensure_ascii=False),
                    concept.created_at.isoformat(), concept.updated_at.isoformat()
                ))
            conn.commit()
            logger.info(f"[数学模型服务] 种子数学概念数据 {len(concepts)} 条")

    def _seed_default_methods(self):
        """种子解题方法数据"""
        methods = [
            {
                'name': '公式法',
                'description': '直接运用数学公式求解问题',
                'category': 'algebra',
                'method_type': 'formula_based',
                'applicable_topics': ['一元一次方程', '一元二次方程', '等差数列', '等比数列'],
                'steps': ['分析题目类型', '确定适用公式', '代入已知量', '计算求解', '检验答案'],
                'key_formulas': ['求根公式', '求和公式', '通项公式'],
                'difficulty': 1,
                'tags': ['基础方法', '公式应用']
            },
            {
                'name': '换元法',
                'description': '通过变量替换简化复杂表达式',
                'category': 'algebra',
                'method_type': 'transformation',
                'applicable_topics': ['高次方程', '分式方程', '根式方程', '复合函数'],
                'steps': ['识别可换元部分', '设定新变量', '转化为简单问题', '求解新问题', '回代得到原解'],
                'key_formulas': ['变量替换定理', '等价变形原理'],
                'difficulty': 2,
                'tags': ['转化思想', '代数变形']
            },
            {
                'name': '数形结合法',
                'description': '通过图形与代数相结合的方式解决问题',
                'category': 'geometry',
                'method_type': 'graphical',
                'applicable_topics': ['函数图像', '几何证明', '不等式', '坐标系问题'],
                'steps': ['分析代数关系', '构造几何图形', '利用几何性质', '转化为代数运算', '得出结论'],
                'key_formulas': ['坐标公式', '距离公式', '斜率公式'],
                'difficulty': 2,
                'tags': ['几何', '数形结合', '重要思想']
            },
            {
                'name': '分类讨论法',
                'description': '根据不同情况分别求解',
                'category': 'general',
                'method_type': 'classification',
                'applicable_topics': ['绝对值方程', '分段函数', '排列组合', '概率问题'],
                'steps': ['确定分类标准', '逐类讨论', '确保分类完整', '合并各类结果', '验证答案'],
                'key_formulas': ['分类加法计数原理'],
                'difficulty': 2,
                'tags': ['逻辑', '分类', '重要方法']
            },
            {
                'name': '待定系数法',
                'description': '先设出表达式形式，再根据条件确定系数',
                'category': 'algebra',
                'method_type': 'constructive',
                'applicable_topics': ['函数解析式', '数列通项', '因式分解', '曲线方程'],
                'steps': ['设定表达式形式', '建立系数方程', '解方程组求系数', '代入得到结果', '检验正确性'],
                'key_formulas': ['多项式恒等定理'],
                'difficulty': 2,
                'tags': ['代数', '构造', '常用方法']
            },
            {
                'name': '反证法',
                'description': '从结论反面出发，导出矛盾从而证明结论',
                'category': 'general',
                'method_type': 'reverse',
                'applicable_topics': ['几何证明', '数论问题', '不等式', '存在性问题'],
                'steps': ['反设结论', '推导过程', '导出矛盾', '肯定原结论'],
                'key_formulas': ['排中律', '矛盾律'],
                'difficulty': 3,
                'tags': ['证明方法', '逻辑推理', '高级方法']
            }
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            for i, m in enumerate(methods):
                method = SolutionMethod(
                    id=f"sm_seed_{i+1:03d}",
                    name=m['name'],
                    description=m['description'],
                    category=m['category'],
                    method_type=m['method_type'],
                    applicable_topics=m['applicable_topics'],
                    steps=m['steps'],
                    key_formulas=m['key_formulas'],
                    difficulty=m['difficulty'],
                    tags=m['tags'],
                    created_at=datetime.fromisoformat(now),
                    updated_at=datetime.fromisoformat(now)
                )
                cursor.execute('''
                    INSERT OR IGNORE INTO solution_methods
                    (id, name, description, category, method_type, applicable_topics, steps,
                     key_formulas, examples, difficulty, success_rate, usage_count, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    method.id, method.name, method.description, method.category, method.method_type,
                    json.dumps(method.applicable_topics, ensure_ascii=False),
                    json.dumps(method.steps, ensure_ascii=False),
                    json.dumps(method.key_formulas, ensure_ascii=False),
                    json.dumps(method.examples, ensure_ascii=False),
                    method.difficulty, method.success_rate, method.usage_count,
                    json.dumps(method.tags, ensure_ascii=False),
                    method.created_at.isoformat(), method.updated_at.isoformat()
                ))
            conn.commit()
            logger.info(f"[数学模型服务] 种子解题方法数据 {len(methods)} 条")

    def _seed_default_problems(self):
        """种子数学题目数据"""
        problems = [
            {
                'content': '解方程：2x + 5 = 13',
                'problem_type': 'calculation',
                'category': 'algebra',
                'subcategory': '一元一次方程',
                'difficulty': 1,
                'correct_answer': 'x = 4',
                'answer_explanation': '移项得 2x = 13 - 5 = 8，两边除以2得 x = 4',
                'related_concepts': ['mc_seed_001'],
                'related_formulas': ['ax + b = 0'],
                'applicable_methods': ['sm_seed_001'],
                'hints': ['先把常数项移到等号右边', '然后两边同除以系数'],
                'solution_steps': [
                    {'step': 1, 'description': '移项', 'formula': '2x = 13 - 5'},
                    {'step': 2, 'description': '计算右边', 'formula': '2x = 8'},
                    {'step': 3, 'description': '两边除以2', 'formula': 'x = 4'}
                ],
                'points': 1.0,
                'estimated_time': 3,
                'tags': ['基础', '方程', '入门']
            },
            {
                'content': '解方程：x² - 5x + 6 = 0',
                'problem_type': 'calculation',
                'category': 'algebra',
                'subcategory': '一元二次方程',
                'difficulty': 2,
                'correct_answer': 'x = 2 或 x = 3',
                'answer_explanation': '因式分解得(x-2)(x-3)=0，所以x=2或x=3',
                'related_concepts': ['mc_seed_002'],
                'related_formulas': ['ax² + bx + c = 0', '求根公式'],
                'applicable_methods': ['sm_seed_001', 'sm_seed_005'],
                'hints': ['试试因式分解', '或者用求根公式', '判别式 = b² - 4ac'],
                'solution_steps': [
                    {'step': 1, 'description': '因式分解', 'formula': '(x-2)(x-3) = 0'},
                    {'step': 2, 'description': '令每个因子为0', 'formula': 'x-2=0 或 x-3=0'},
                    {'step': 3, 'description': '求解', 'formula': 'x = 2 或 x = 3'}
                ],
                'points': 2.0,
                'estimated_time': 5,
                'tags': ['方程', '二次', '因式分解']
            },
            {
                'content': '直角三角形两条直角边分别为3和4，求斜边长',
                'problem_type': 'calculation',
                'category': 'geometry',
                'subcategory': '三角形',
                'difficulty': 2,
                'correct_answer': '5',
                'answer_explanation': '根据勾股定理 c² = a² + b² = 9 + 16 = 25，所以 c = 5',
                'related_concepts': ['mc_seed_003'],
                'related_formulas': ['a² + b² = c²'],
                'applicable_methods': ['sm_seed_001', 'sm_seed_003'],
                'hints': ['回忆勾股定理', '斜边的平方等于两直角边的平方和'],
                'solution_steps': [
                    {'step': 1, 'description': '应用勾股定理', 'formula': 'c² = a² + b²'},
                    {'step': 2, 'description': '代入数值', 'formula': 'c² = 3² + 4² = 9 + 16 = 25'},
                    {'step': 3, 'description': '开方', 'formula': 'c = √25 = 5'}
                ],
                'points': 2.0,
                'estimated_time': 4,
                'tags': ['几何', '勾股定理', '基础']
            },
            {
                'content': '等差数列首项为2，公差为3，求第10项',
                'problem_type': 'calculation',
                'category': 'algebra',
                'subcategory': '数列',
                'difficulty': 2,
                'correct_answer': '29',
                'answer_explanation': 'an = a1 + (n-1)d = 2 + 9×3 = 29',
                'related_concepts': ['mc_seed_006'],
                'related_formulas': ['an = a1 + (n-1)d'],
                'applicable_methods': ['sm_seed_001'],
                'hints': ['使用等差数列通项公式', 'a1是首项，d是公差，n是项数'],
                'solution_steps': [
                    {'step': 1, 'description': '写出通项公式', 'formula': 'an = a1 + (n-1)d'},
                    {'step': 2, 'description': '代入已知', 'formula': 'a10 = 2 + (10-1)×3'},
                    {'step': 3, 'description': '计算', 'formula': 'a10 = 2 + 27 = 29'}
                ],
                'points': 2.0,
                'estimated_time': 3,
                'tags': ['数列', '等差数列', '基础']
            },
            {
                'content': '从5个不同元素中任取3个的排列数是多少？',
                'problem_type': 'calculation',
                'category': 'combinatorics',
                'subcategory': '排列组合',
                'difficulty': 2,
                'correct_answer': '60',
                'answer_explanation': 'A(5,3) = 5×4×3 = 60',
                'related_concepts': [],
                'related_formulas': ['A(n,m) = n!/(n-m)!'],
                'applicable_methods': ['sm_seed_001'],
                'hints': ['排列数公式', '从n个中取m个排列'],
                'solution_steps': [
                    {'step': 1, 'description': '应用排列公式', 'formula': 'A(5,3) = 5×4×3'},
                    {'step': 2, 'description': '计算', 'formula': '5×4×3 = 60'}
                ],
                'points': 2.0,
                'estimated_time': 3,
                'tags': ['组合数学', '排列', '基础']
            },
            {
                'content': '抛一枚硬币两次，至少有一次正面的概率是多少？',
                'problem_type': 'calculation',
                'category': 'probability',
                'subcategory': '概率基础',
                'difficulty': 2,
                'correct_answer': '3/4',
                'answer_explanation': '总情况有4种：正正、正反、反正、反反。至少一次正面有3种，概率为3/4',
                'related_concepts': ['mc_seed_005'],
                'related_formulas': ['P(A) = m/n'],
                'applicable_methods': ['sm_seed_001', 'sm_seed_004'],
                'hints': ['列出所有可能的结果', '或者用对立事件计算'],
                'solution_steps': [
                    {'step': 1, 'description': '总情况数', 'formula': '2×2 = 4'},
                    {'step': 2, 'description': '对立事件（全反面）', 'formula': 'P(全反) = 1/4'},
                    {'step': 3, 'description': '至少一次正面', 'formula': 'P = 1 - 1/4 = 3/4'}
                ],
                'points': 2.0,
                'estimated_time': 4,
                'tags': ['概率', '古典概型', '基础']
            }
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            for i, p in enumerate(problems):
                problem = MathProblem(
                    id=f"mp_seed_{i+1:03d}",
                    content=p['content'],
                    problem_type=p['problem_type'],
                    category=p['category'],
                    subcategory=p['subcategory'],
                    difficulty=p['difficulty'],
                    correct_answer=p['correct_answer'],
                    answer_explanation=p['answer_explanation'],
                    related_concepts=p['related_concepts'],
                    related_formulas=p['related_formulas'],
                    applicable_methods=p['applicable_methods'],
                    hints=p['hints'],
                    solution_steps=p['solution_steps'],
                    points=p['points'],
                    estimated_time=p['estimated_time'],
                    tags=p['tags'],
                    created_at=datetime.fromisoformat(now),
                    updated_at=datetime.fromisoformat(now)
                )
                cursor.execute('''
                    INSERT OR IGNORE INTO math_problems
                    (id, content, problem_type, category, subcategory, difficulty, options,
                     correct_answer, answer_explanation, related_concepts, related_formulas,
                     applicable_methods, hints, solution_steps, points, estimated_time,
                     source, tags, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    problem.id, problem.content, problem.problem_type, problem.category,
                    problem.subcategory, problem.difficulty,
                    json.dumps(problem.options, ensure_ascii=False),
                    problem.correct_answer, problem.answer_explanation,
                    json.dumps(problem.related_concepts, ensure_ascii=False),
                    json.dumps(problem.related_formulas, ensure_ascii=False),
                    json.dumps(problem.applicable_methods, ensure_ascii=False),
                    json.dumps(problem.hints, ensure_ascii=False),
                    json.dumps(problem.solution_steps, ensure_ascii=False),
                    problem.points, problem.estimated_time, problem.source,
                    json.dumps(problem.tags, ensure_ascii=False),
                    1, problem.created_at.isoformat(), problem.updated_at.isoformat()
                ))
            conn.commit()
            logger.info(f"[数学模型服务] 种子数学题目数据 {len(problems)} 条")

    def add_concept(self, concept_data: Dict) -> Optional[str]:
        """添加数学概念"""
        try:
            concept = MathConcept(**{k: v for k, v in concept_data.items()
                                      if k in MathConcept.__dataclass_fields__})
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now(timezone.utc).isoformat()
                cursor.execute('''
                    INSERT INTO math_concepts
                    (id, name, description, category, subcategory, level, prerequisites, formulas,
                     theorems, examples, difficulty, source, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    concept.id, concept.name, concept.description, concept.category, concept.subcategory,
                    concept.level, json.dumps(concept.prerequisites, ensure_ascii=False),
                    json.dumps(concept.formulas, ensure_ascii=False),
                    json.dumps(concept.theorems, ensure_ascii=False),
                    json.dumps(concept.examples, ensure_ascii=False),
                    concept.difficulty, concept.source,
                    json.dumps(concept.tags, ensure_ascii=False),
                    now, now
                ))
                conn.commit()
                logger.info(f"[数学模型服务] 添加概念: {concept.name}")
                return concept.id
        except Exception as e:
            logger.error(f"[数学模型服务] 添加概念失败: {e}")
            return None

    def get_concepts(self, category: str = '', difficulty: int = None, keyword: str = '',
                     limit: int = 50, offset: int = 0) -> Dict:
        """获取数学概念列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM math_concepts WHERE 1=1"
                params = []

                if category:
                    query += " AND category = ?"
                    params.append(category)
                if difficulty is not None:
                    query += " AND difficulty = ?"
                    params.append(difficulty)
                if keyword:
                    query += " AND (name LIKE ? OR description LIKE ?)"
                    params.extend([f'%{keyword}%', f'%{keyword}%'])

                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cursor.execute(count_query, tuple(params))
                total = cursor.fetchone()[0]

                query += " ORDER BY difficulty ASC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

                concepts = []
                for row in rows:
                    concepts.append({
                        'id': row['id'],
                        'name': row['name'],
                        'description': row['description'],
                        'category': row['category'],
                        'subcategory': row['subcategory'],
                        'level': row['level'],
                        'prerequisites': json.loads(row['prerequisites']) if row['prerequisites'] else [],
                        'formulas': json.loads(row['formulas']) if row['formulas'] else [],
                        'theorems': json.loads(row['theorems']) if row['theorems'] else [],
                        'difficulty': row['difficulty'],
                        'tags': json.loads(row['tags']) if row['tags'] else [],
                        'created_at': row['created_at']
                    })

                return {'success': True, 'data': concepts, 'total': total}
        except Exception as e:
            logger.error(f"[数学模型服务] 获取概念列表失败: {e}")
            return {'success': False, 'error': str(e)}

    def add_solution_method(self, method_data: Dict) -> Optional[str]:
        """添加解题方法"""
        try:
            method = SolutionMethod(**{k: v for k, v in method_data.items()
                                         if k in SolutionMethod.__dataclass_fields__})
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now(timezone.utc).isoformat()
                cursor.execute('''
                    INSERT INTO solution_methods
                    (id, name, description, category, method_type, applicable_topics, steps,
                     key_formulas, examples, difficulty, success_rate, usage_count, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    method.id, method.name, method.description, method.category, method.method_type,
                    json.dumps(method.applicable_topics, ensure_ascii=False),
                    json.dumps(method.steps, ensure_ascii=False),
                    json.dumps(method.key_formulas, ensure_ascii=False),
                    json.dumps(method.examples, ensure_ascii=False),
                    method.difficulty, method.success_rate, method.usage_count,
                    json.dumps(method.tags, ensure_ascii=False),
                    now, now
                ))
                conn.commit()
                logger.info(f"[数学模型服务] 添加解题方法: {method.name}")
                return method.id
        except Exception as e:
            logger.error(f"[数学模型服务] 添加解题方法失败: {e}")
            return None

    def get_solution_methods(self, category: str = '', method_type: str = '',
                              keyword: str = '', limit: int = 50, offset: int = 0) -> Dict:
        """获取解题方法列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM solution_methods WHERE 1=1"
                params = []

                if category:
                    query += " AND category = ?"
                    params.append(category)
                if method_type:
                    query += " AND method_type = ?"
                    params.append(method_type)
                if keyword:
                    query += " AND (name LIKE ? OR description LIKE ?)"
                    params.extend([f'%{keyword}%', f'%{keyword}%'])

                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cursor.execute(count_query, tuple(params))
                total = cursor.fetchone()[0]

                query += " ORDER BY difficulty ASC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

                methods = []
                for row in rows:
                    methods.append({
                        'id': row['id'],
                        'name': row['name'],
                        'description': row['description'],
                        'category': row['category'],
                        'method_type': row['method_type'],
                        'applicable_topics': json.loads(row['applicable_topics']) if row['applicable_topics'] else [],
                        'steps': json.loads(row['steps']) if row['steps'] else [],
                        'key_formulas': json.loads(row['key_formulas']) if row['key_formulas'] else [],
                        'difficulty': row['difficulty'],
                        'success_rate': row['success_rate'],
                        'usage_count': row['usage_count'],
                        'tags': json.loads(row['tags']) if row['tags'] else [],
                        'created_at': row['created_at']
                    })

                return {'success': True, 'data': methods, 'total': total}
        except Exception as e:
            logger.error(f"[数学模型服务] 获取解题方法列表失败: {e}")
            return {'success': False, 'error': str(e)}

    def add_problem(self, problem_data: Dict) -> Optional[str]:
        """添加数学题目"""
        try:
            problem = MathProblem(**{k: v for k, v in problem_data.items()
                                      if k in MathProblem.__dataclass_fields__})
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now(timezone.utc).isoformat()
                cursor.execute('''
                    INSERT INTO math_problems
                    (id, content, problem_type, category, subcategory, difficulty, options,
                     correct_answer, answer_explanation, related_concepts, related_formulas,
                     applicable_methods, hints, solution_steps, points, estimated_time,
                     source, tags, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    problem.id, problem.content, problem.problem_type, problem.category,
                    problem.subcategory, problem.difficulty,
                    json.dumps(problem.options, ensure_ascii=False),
                    problem.correct_answer, problem.answer_explanation,
                    json.dumps(problem.related_concepts, ensure_ascii=False),
                    json.dumps(problem.related_formulas, ensure_ascii=False),
                    json.dumps(problem.applicable_methods, ensure_ascii=False),
                    json.dumps(problem.hints, ensure_ascii=False),
                    json.dumps(problem.solution_steps, ensure_ascii=False),
                    problem.points, problem.estimated_time, problem.source,
                    json.dumps(problem.tags, ensure_ascii=False),
                    1, now, now
                ))
                conn.commit()
                logger.info(f"[数学模型服务] 添加题目: {problem.id}")
                return problem.id
        except Exception as e:
            logger.error(f"[数学模型服务] 添加题目失败: {e}")
            return None

    def get_problems(self, category: str = '', difficulty: int = None, problem_type: str = '',
                     keyword: str = '', limit: int = 50, offset: int = 0) -> Dict:
        """获取数学题目列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM math_problems WHERE is_active = 1"
                params = []

                if category:
                    query += " AND category = ?"
                    params.append(category)
                if difficulty is not None:
                    query += " AND difficulty = ?"
                    params.append(difficulty)
                if problem_type:
                    query += " AND problem_type = ?"
                    params.append(problem_type)
                if keyword:
                    query += " AND content LIKE ?"
                    params.append(f'%{keyword}%')

                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cursor.execute(count_query, tuple(params))
                total = cursor.fetchone()[0]

                query += " ORDER BY difficulty ASC, RANDOM() LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

                problems = []
                for row in rows:
                    problems.append({
                        'id': row['id'],
                        'content': row['content'],
                        'problem_type': row['problem_type'],
                        'category': row['category'],
                        'subcategory': row['subcategory'],
                        'difficulty': row['difficulty'],
                        'options': json.loads(row['options']) if row['options'] else [],
                        'correct_answer': row['correct_answer'],
                        'answer_explanation': row['answer_explanation'],
                        'related_concepts': json.loads(row['related_concepts']) if row['related_concepts'] else [],
                        'related_formulas': json.loads(row['related_formulas']) if row['related_formulas'] else [],
                        'applicable_methods': json.loads(row['applicable_methods']) if row['applicable_methods'] else [],
                        'hints': json.loads(row['hints']) if row['hints'] else [],
                        'solution_steps': json.loads(row['solution_steps']) if row['solution_steps'] else [],
                        'points': row['points'],
                        'estimated_time': row['estimated_time'],
                        'tags': json.loads(row['tags']) if row['tags'] else [],
                        'created_at': row['created_at']
                    })

                return {'success': True, 'data': problems, 'total': total}
        except Exception as e:
            logger.error(f"[数学模型服务] 获取题目列表失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_problem(self, problem_id: str) -> Optional[Dict]:
        """获取单个题目详情"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM math_problems WHERE id = ?", (problem_id,))
                row = cursor.fetchone()
                if not row:
                    return None

                return {
                    'id': row['id'],
                    'content': row['content'],
                    'problem_type': row['problem_type'],
                    'category': row['category'],
                    'subcategory': row['subcategory'],
                    'difficulty': row['difficulty'],
                    'options': json.loads(row['options']) if row['options'] else [],
                    'correct_answer': row['correct_answer'],
                    'answer_explanation': row['answer_explanation'],
                    'related_concepts': json.loads(row['related_concepts']) if row['related_concepts'] else [],
                    'related_formulas': json.loads(row['related_formulas']) if row['related_formulas'] else [],
                    'applicable_methods': json.loads(row['applicable_methods']) if row['applicable_methods'] else [],
                    'hints': json.loads(row['hints']) if row['hints'] else [],
                    'solution_steps': json.loads(row['solution_steps']) if row['solution_steps'] else [],
                    'points': row['points'],
                    'estimated_time': row['estimated_time'],
                    'tags': json.loads(row['tags']) if row['tags'] else []
                }
        except Exception as e:
            logger.error(f"[数学模型服务] 获取题目详情失败: {e}")
            return None

    def save_solution(self, solution_data: Dict) -> Optional[str]:
        """保存解题记录"""
        try:
            solution = ProblemSolution(**{k: v for k, v in solution_data.items()
                                            if k in ProblemSolution.__dataclass_fields__})
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now(timezone.utc).isoformat()
                cursor.execute('''
                    INSERT INTO problem_solutions
                    (id, problem_id, problem_content, problem_type, difficulty, subject,
                     solution_method_id, solution_method_name, steps, final_answer, answer_formatted,
                     reasoning, verification, time_spent, is_correct, user_id, attempts,
                     hint_used, error_analysis, related_concepts, related_formulas,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    solution.id, solution.problem_id, solution.problem_content, solution.problem_type,
                    solution.difficulty, solution.subject, solution.solution_method_id,
                    solution.solution_method_name,
                    json.dumps(solution.steps, ensure_ascii=False),
                    solution.final_answer, solution.answer_formatted,
                    solution.reasoning, solution.verification,
                    solution.time_spent, 1 if solution.is_correct else 0,
                    solution.user_id, solution.attempts, solution.hint_used,
                    solution.error_analysis,
                    json.dumps(solution.related_concepts, ensure_ascii=False),
                    json.dumps(solution.related_formulas, ensure_ascii=False),
                    now, now
                ))
                conn.commit()

                if solution.solution_method_id:
                    cursor.execute('''
                        UPDATE solution_methods SET usage_count = usage_count + 1
                        WHERE id = ?
                    ''', (solution.solution_method_id,))
                    conn.commit()

                logger.info(f"[数学模型服务] 保存解题记录: {solution.id}")
                return solution.id
        except Exception as e:
            logger.error(f"[数学模型服务] 保存解题记录失败: {e}")
            return None

    def get_user_solutions(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict:
        """获取用户解题记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM problem_solutions WHERE user_id = ?", (user_id,))
                total = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT * FROM problem_solutions WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT ? OFFSET ?
                ''', (user_id, limit, offset))
                rows = cursor.fetchall()

                solutions = []
                for row in rows:
                    solutions.append({
                        'id': row['id'],
                        'problem_id': row['problem_id'],
                        'problem_content': row['problem_content'],
                        'problem_type': row['problem_type'],
                        'difficulty': row['difficulty'],
                        'solution_method_name': row['solution_method_name'],
                        'final_answer': row['final_answer'],
                        'is_correct': bool(row['is_correct']),
                        'time_spent': row['time_spent'],
                        'attempts': row['attempts'],
                        'created_at': row['created_at']
                    })

                return {'success': True, 'data': solutions, 'total': total}
        except Exception as e:
            logger.error(f"[数学模型服务] 获取用户解题记录失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_stats(self, user_id: str = '') -> Dict:
        """获取统计数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM math_concepts")
                concepts_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM solution_methods")
                methods_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM math_problems WHERE is_active = 1")
                problems_count = cursor.fetchone()[0]

                stats = {
                    'concepts_count': concepts_count,
                    'methods_count': methods_count,
                    'problems_count': problems_count
                }

                if user_id:
                    cursor.execute("SELECT COUNT(*) FROM problem_solutions WHERE user_id = ?", (user_id,))
                    total_solved = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM problem_solutions WHERE user_id = ? AND is_correct = 1", (user_id,))
                    correct_count = cursor.fetchone()[0]

                    cursor.execute("SELECT AVG(time_spent) FROM problem_solutions WHERE user_id = ?", (user_id,))
                    avg_time = cursor.fetchone()[0] or 0

                    accuracy = (correct_count / total_solved * 100) if total_solved > 0 else 0

                    stats.update({
                        'user_total_solved': total_solved,
                        'user_correct_count': correct_count,
                        'user_accuracy': round(accuracy, 2),
                        'user_avg_time': round(avg_time, 2)
                    })

                return {'success': True, 'data': stats}
        except Exception as e:
            logger.error(f"[数学模型服务] 获取统计数据失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_categories(self) -> Dict:
        """获取数学分类列表"""
        return {
            'success': True,
            'data': MATH_CATEGORIES
        }


_math_model_service = None


def get_math_model_service(db_path=None) -> MathModelService:
    """获取数学模型服务单例"""
    global _math_model_service
    if _math_model_service is None:
        _math_model_service = MathModelService(db_path)
    return _math_model_service


if __name__ == '__main__':
    service = MathModelService()

    print("=== 数学概念 ===")
    result = service.get_concepts(limit=5)
    for c in result['data']:
        print(f"  [{c['difficulty']}级] {c['name']} - {c['category']}")

    print("\n=== 解题方法 ===")
    result = service.get_solution_methods(limit=5)
    for m in result['data']:
        print(f"  [{m['difficulty']}级] {m['name']} - {m['method_type']}")

    print("\n=== 数学题目 ===")
    result = service.get_problems(limit=5)
    for p in result['data']:
        print(f"  [{p['difficulty']}级] {p['content'][:40]}...")

    print("\n=== 统计 ===")
    result = service.get_stats()
    print(f"  概念: {result['data']['concepts_count']}")
    print(f"  方法: {result['data']['methods_count']}")
    print(f"  题目: {result['data']['problems_count']}")
