#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版AI拓展题库服务 - 海量题库管理与专家AI出题系统
支持历年真题、难题、必考题、压轴题、加分题、专项知识点等
"""

import os
import json
import time
import random
import threading
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field

from app.utils.logging import logger


class QuestionType(Enum):
    """题型枚举"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CALCULATION = "calculation"
    LOGIC_JUDGMENT = "logic_judgment"
    COMPREHENSION = "comprehension"
    PRACTICAL = "practical"
    CODE_ANALYSIS = "code_analysis"
    CASE_STUDY = "case_study"


class DifficultyLevel(Enum):
    """难度等级"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    CHALLENGE = "challenge"


class QuestionCategory(Enum):
    """题目类别"""
    REAL_EXAM = "real_exam"
    MUST_KNOW = "must_know"
    FINAL = "final"
    BONUS = "bonus"
    SPECIAL_TOPIC = "special_topic"
    KEY_POINT = "key_point"
    CALCULATION = "calculation"
    LOGIC = "logic"
    ERROR_PRONE = "error_prone"
    FORMULA = "formula"
    COMPREHENSION = "comprehension"
    CODING = "coding"
    CASE_ANALYSIS = "case_analysis"


@dataclass
class Question:
    """题目数据类"""
    question_id: str
    type: QuestionType
    category: QuestionCategory
    difficulty: DifficultyLevel
    content: str
    options: List[Dict[str, str]] = field(default_factory=list)
    correct_answer: Any = None
    explanation: str = ""
    analysis: str = ""
    tags: List[str] = field(default_factory=list)
    knowledge_points: List[str] = field(default_factory=list)
    formula_used: List[str] = field(default_factory=list)
    year: Optional[int] = None
    source: str = ""
    score: float = 1.0
    usage_count: int = 0
    correct_rate: float = 0.0
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict:
        return {
            'question_id': self.question_id,
            'type': self.type.value,
            'category': self.category.value,
            'difficulty': self.difficulty.value,
            'content': self.content,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'analysis': self.analysis,
            'tags': self.tags,
            'knowledge_points': self.knowledge_points,
            'formula_used': self.formula_used,
            'year': self.year,
            'source': self.source,
            'score': self.score,
            'usage_count': self.usage_count,
            'correct_rate': self.correct_rate,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class QuestionBankStats:
    """题库统计"""
    total_questions: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    by_difficulty: Dict[str, int] = field(default_factory=dict)
    by_year: Dict[int, int] = field(default_factory=dict)
    avg_correct_rate: float = 0.0
    total_usage: int = 0


class EnhancedQuestionBankService:
    """增强版AI拓展题库服务"""

    def __init__(self):
        self._questions: Dict[str, Question] = {}
        self._knowledge_points: Dict[str, List[str]] = {}
        self._categories: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        self._db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'enhanced_question_bank.json')
        
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        
        self._load_question_bank()
        self._init_default_categories()
        self._init_expert_templates()
        
        logger.info("增强版AI拓展题库服务初始化完成")

    def _load_question_bank(self):
        """加载题库数据"""
        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for q_data in data.get('questions', []):
                        question = Question(
                            question_id=q_data['question_id'],
                            type=QuestionType(q_data['type']),
                            category=QuestionCategory(q_data['category']),
                            difficulty=DifficultyLevel(q_data['difficulty']),
                            content=q_data['content'],
                            options=q_data.get('options', []),
                            correct_answer=q_data.get('correct_answer'),
                            explanation=q_data.get('explanation', ''),
                            analysis=q_data.get('analysis', ''),
                            tags=q_data.get('tags', []),
                            knowledge_points=q_data.get('knowledge_points', []),
                            formula_used=q_data.get('formula_used', []),
                            year=q_data.get('year'),
                            source=q_data.get('source', ''),
                            score=q_data.get('score', 1.0),
                            usage_count=q_data.get('usage_count', 0),
                            correct_rate=q_data.get('correct_rate', 0.0),
                            created_at=q_data.get('created_at', time.time()),
                            updated_at=q_data.get('updated_at', time.time())
                        )
                        self._questions[question.question_id] = question
                logger.info(f"已加载 {len(self._questions)} 道题目")
            except Exception as e:
                logger.error(f"加载题库失败: {str(e)}")

    def _save_question_bank(self):
        """保存题库数据"""
        try:
            data = {
                'last_updated': time.time(),
                'questions': [q.to_dict() for q in self._questions.values()]
            }
            with open(self._db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存题库失败: {str(e)}")

    def _init_default_categories(self):
        """初始化默认分类"""
        self._categories = {
            'real_exam': ['历年真题', '真题演练', '真题模拟', '考试原题', '真题解析'],
            'must_know': ['必考知识点', '高频考点', '核心考点', '重点内容', '考试热点'],
            'final': ['压轴题', '综合题', '难题', '拔高题', '能力挑战'],
            'bonus': ['加分题', '拓展题', '提升题', '选做题', '附加题'],
            'special_topic': ['专项突破', '专题训练', '强化训练', '针对性练习', '模块复习'],
            'key_point': ['重点分析', '难点解析', '深度剖析', '核心概念', '要点归纳'],
            'calculation': ['计算题', '应用题', '数值计算', '公式应用', '定量分析'],
            'logic': ['逻辑判断', '推理题', '分析题', '论证题', '思维训练'],
            'error_prone': ['易错题', '常考题', '易错点', '陷阱题', '误区分析'],
            'formula': ['公式运用', '公式推导', '公式应用', '定理证明', '公式记忆'],
            'comprehension': ['阅读理解', '综合理解', '案例分析', '材料分析', '情境理解'],
            'coding': ['代码分析', '编程题', '算法题', '调试题', '代码优化'],
            'case_analysis': ['案例分析', '实务题', '应用题', '综合应用', '情境题']
        }

    def _init_expert_templates(self):
        """初始化专家出题模板"""
        self._templates = {
            'math': {
                'single_choice': [
                    {'question': '设函数 f(x) = {func},则 f({val}) = ?', 'formula': ['函数求值']},
                    {'question': '{concept}的定义是:', 'formula': ['定义']},
                    {'question': '下列关于{concept}的说法正确的是:', 'formula': ['概念理解']}
                ],
                'calculation': [
                    {'question': '已知{condition},求{target}的值.', 'formula': ['综合计算']},
                    {'question': '计算:{expression}', 'formula': ['直接计算']}
                ]
            },
            'physics': {
                'single_choice': [
                    {'question': '{law}适用于下列哪种情况?', 'formula': ['定律应用']},
                    {'question': '关于{concept},以下说法错误的是:', 'formula': ['概念辨析']}
                ],
                'calculation': [
                    {'question': '一个{object},{condition},求{target}.', 'formula': ['物理计算']}
                ]
            },
            'programming': {
                'single_choice': [
                    {'question': 'Python中,{keyword}关键字用于{purpose}.', 'formula': ['语法']},
                    {'question': '{data_structure}的{operation}操作时间复杂度是:', 'formula': ['复杂度分析']}
                ],
                'code_analysis': [
                    {'question': '以下代码的输出结果是:\n{code}', 'formula': ['代码理解']},
                    {'question': '这段代码存在什么问题?\n{code}', 'formula': ['调试']}
                ]
            },
            'logic': {
                'logic_judgment': [
                    {'question': '如果{premise},那么{conclusion}.这个推理是否正确?', 'formula': ['逻辑推理']},
                    {'question': '{statement},这个命题的真值是:', 'formula': ['命题判断']}
                ]
            }
        }

    def _generate_question_id(self) -> str:
        """生成题目ID"""
        import uuid
        return f"EQ-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    def add_question(self, question_data: Dict) -> str:
        """添加题目"""
        question = Question(
            question_id=self._generate_question_id(),
            type=QuestionType(question_data['type']),
            category=QuestionCategory(question_data['category']),
            difficulty=DifficultyLevel(question_data['difficulty']),
            content=question_data['content'],
            options=question_data.get('options', []),
            correct_answer=question_data.get('correct_answer'),
            explanation=question_data.get('explanation', ''),
            analysis=question_data.get('analysis', ''),
            tags=question_data.get('tags', []),
            knowledge_points=question_data.get('knowledge_points', []),
            formula_used=question_data.get('formula_used', []),
            year=question_data.get('year'),
            source=question_data.get('source', ''),
            score=question_data.get('score', 1.0)
        )
        
        with self._lock:
            self._questions[question.question_id] = question
        
        self._save_question_bank()
        logger.info(f"题目已添加: {question.question_id}")
        
        return question.question_id

    def add_questions_batch(self, questions_data: List[Dict]) -> Tuple[int, int]:
        """批量添加题目"""
        success = 0
        failed = 0
        
        for q_data in questions_data:
            try:
                self.add_question(q_data)
                success += 1
            except Exception as e:
                failed += 1
                logger.error(f"批量添加题目失败: {str(e)}")
        
        return success, failed

    def add_real_exam_questions(self, year: int, questions_data: List[Dict]):
        """添加历年真题"""
        for q_data in questions_data:
            q_data['category'] = 'real_exam'
            q_data['year'] = year
            q_data['source'] = f"{year}年真题"
            self.add_question(q_data)

    def add_must_know_questions(self, questions_data: List[Dict]):
        """添加必考题"""
        for q_data in questions_data:
            q_data['category'] = 'must_know'
            q_data['tags'] = q_data.get('tags', []) + ['必考']
            self.add_question(q_data)

    def add_final_challenge_questions(self, questions_data: List[Dict]):
        """添加压轴题"""
        for q_data in questions_data:
            q_data['category'] = 'final'
            q_data['difficulty'] = 'expert' if q_data.get('difficulty') in ['hard', 'expert', 'challenge'] else 'hard'
            q_data['tags'] = q_data.get('tags', []) + ['压轴', '难题']
            q_data['score'] = q_data.get('score', 15.0)
            self.add_question(q_data)

    def add_bonus_questions(self, questions_data: List[Dict]):
        """添加加分题"""
        for q_data in questions_data:
            q_data['category'] = 'bonus'
            q_data['tags'] = q_data.get('tags', []) + ['加分']
            q_data['score'] = q_data.get('score', 10.0)
            self.add_question(q_data)

    def add_special_topic_questions(self, topic: str, questions_data: List[Dict]):
        """添加专项专题题目"""
        for q_data in questions_data:
            q_data['category'] = 'special_topic'
            q_data['tags'] = q_data.get('tags', []) + [topic]
            q_data['knowledge_points'] = q_data.get('knowledge_points', []) + [topic]
            self.add_question(q_data)

    def generate_mass_questions(self, count: int = 1000, **filters) -> int:
        """批量生成海量题目"""
        generated = 0
        
        categories = filters.get('categories', ['special_topic', 'must_know', 'calculation', 'logic', 'error_prone'])
        types = filters.get('types', ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'calculation'])
        difficulties = filters.get('difficulties', ['easy', 'medium', 'hard'])
        
        for _ in range(count):
            try:
                question = self._expert_generate_question(
                    category=random.choice(categories),
                    q_type=random.choice(types),
                    difficulty=random.choice(difficulties)
                )
                self.add_question(question)
                generated += 1
            except Exception as e:
                logger.error(f"生成题目失败: {str(e)}")
        
        return generated

    def _expert_generate_question(self, category: str, q_type: str, difficulty: str) -> Dict:
        """专家AI生成题目"""
        topics = {
            'math': {
                'concepts': ['导数', '积分', '极限', '微分方程', '级数', '矩阵', '概率', '统计'],
                'formulas': ['f(x)', 'dy/dx', '∫f(x)dx', 'lim', 'Σ']
            },
            'physics': {
                'concepts': ['力学', '电磁学', '热学', '光学', '量子力学', '相对论'],
                'formulas': ['F=ma', 'E=mc²', 'P=IV', 'PV=nRT']
            },
            'programming': {
                'concepts': ['数据结构', '算法', '设计模式', '复杂度', '面向对象'],
                'formulas': ['O(n)', 'O(log n)', 'O(n²)']
            },
            'database': {
                'concepts': ['SQL', '索引', '事务', '范式', '优化'],
                'formulas': ['SELECT', 'JOIN', 'INDEX', 'COMMIT']
            },
            'network': {
                'concepts': ['TCP/IP', 'HTTP', 'DNS', 'SSL/TLS', '负载均衡'],
                'formulas': ['3次握手', 'HTTPS', 'CDN']
            }
        }
        
        topic = random.choice(list(topics.keys()))
        concept = random.choice(topics[topic]['concepts'])
        
        templates = {
            'single_choice': self._generate_single_choice(topic, concept, difficulty),
            'multiple_choice': self._generate_multiple_choice(topic, concept, difficulty),
            'true_false': self._generate_true_false(topic, concept),
            'fill_blank': self._generate_fill_blank(topic, concept),
            'calculation': self._generate_calculation(topic, concept, difficulty),
            'logic_judgment': self._generate_logic_judgment(topic, concept)
        }
        
        question = templates.get(q_type, templates['single_choice'])
        question['category'] = category
        question['difficulty'] = difficulty
        question['type'] = q_type
        
        return question

    def _generate_single_choice(self, topic: str, concept: str, difficulty: str) -> Dict:
        """生成单选题"""
        question_templates = [
            f"关于{topic}中的{concept},以下说法正确的是:",
            f"{concept}的核心概念是:",
            f"下列关于{concept}的描述,错误的是:",
            f"{concept}适用于以下哪种情况?",
            f"{concept}的时间复杂度是:",
            f"以下哪个是{concept}的正确定义?"
        ]
        
        content = random.choice(question_templates)
        
        options = [
            {'key': 'A', 'value': f"{concept}的基本定义"},
            {'key': 'B', 'value': f"{concept}的应用场景"},
            {'key': 'C', 'value': f"{concept}的核心原理"},
            {'key': 'D', 'value': f"{concept}的常见误区"}
        ]
        
        return {
            'content': content,
            'options': options,
            'correct_answer': 'C',
            'knowledge_points': [topic, concept],
            'explanation': f"本题考查{topic}中{concept}的核心概念.",
            'analysis': f"{concept}是{topic}中的重要知识点,需要深入理解其原理和应用."
        }

    def _generate_multiple_choice(self, topic: str, concept: str, difficulty: str) -> Dict:
        """生成多选题"""
        questions = [
            {
                'content': f"以下哪些属于{concept}的基本特征?",
                'options': [
                    {'key': 'A', 'value': f'{concept}特征1'},
                    {'key': 'B', 'value': f'{concept}特征2'},
                    {'key': 'C', 'value': f'{concept}特征3'},
                    {'key': 'D', 'value': '无关选项'}
                ],
                'correct_answer': ['A', 'B', 'C']
            },
            {
                'content': f"以下哪些是{concept}的应用场景?",
                'options': [
                    {'key': 'A', 'value': '场景1'},
                    {'key': 'B', 'value': '场景2'},
                    {'key': 'C', 'value': '场景3'},
                    {'key': 'D', 'value': '场景4'}
                ],
                'correct_answer': ['A', 'B']
            }
        ]
        
        question = random.choice(questions)
        question['knowledge_points'] = [topic, concept]
        question['explanation'] = f"本题考查{topic}中{concept}的多方面知识."
        
        return question

    def _generate_true_false(self, topic: str, concept: str) -> Dict:
        """生成判断题"""
        statements = [
            (f"{concept}是{topic}中的核心概念", True),
            (f"{concept}的时间复杂度为O(n)", random.choice([True, False])),
            (f"{concept}适用于所有场景", False),
            (f"{concept}可以提高系统性能", True)
        ]
        
        statement, answer = random.choice(statements)
        
        return {
            'content': statement,
            'options': [{'key': 'A', 'value': '正确'}, {'key': 'B', 'value': '错误'}],
            'correct_answer': 'A' if answer else 'B',
            'knowledge_points': [topic, concept],
            'explanation': f"该陈述{'正确' if answer else '错误'}.",
            'analysis': f"本题考查{topic}中{concept}的基础概念."
        }

    def _generate_fill_blank(self, topic: str, concept: str) -> Dict:
        """生成填空题"""
        blanks = [
            (f"{concept}的时间复杂度是____.", "O(log n)"),
            (f"{topic}中,{concept}的核心公式是____.", "相关公式"),
            (f"{concept}的三个基本特征是:____、____、____.", "特征1、特征2、特征3"),
            (f"{concept}的主要作用是____.", "提高效率")
        ]
        
        question, answer = random.choice(blanks)
        
        return {
            'content': question,
            'correct_answer': answer,
            'knowledge_points': [topic, concept],
            'explanation': f"正确答案是:{answer}",
            'analysis': f"本题考查{topic}中{concept}的基础知识."
        }

    def _generate_calculation(self, topic: str, concept: str, difficulty: str) -> Dict:
        """生成计算题"""
        problems = [
            {
                'content': f"已知{concept}相关条件,计算{concept}的值.",
                'correct_answer': "计算结果",
                'formula': [f"{concept}公式"]
            },
            {
                'content': f"使用{concept}方法求解:给定条件,求目标值.",
                'correct_answer': "答案",
                'formula': [f"{concept}方法"]
            }
        ]
        
        problem = random.choice(problems)
        problem['knowledge_points'] = [topic, concept, '计算能力']
        problem['explanation'] = f"正确答案是:{problem['correct_answer']}"
        
        return problem

    def _generate_logic_judgment(self, topic: str, concept: str) -> Dict:
        """生成逻辑判断题"""
        scenarios = [
            {
                'content': f"如果{concept}满足条件A,那么{concept}满足条件B.这个推理是否正确?",
                'correct_answer': 'A',
                'logic_type': '条件推理'
            },
            {
                'content': f"{concept}具有性质X,因此{concept}也具有性质Y.这个论证是否有效?",
                'correct_answer': random.choice(['A', 'B']),
                'logic_type': '演绎推理'
            }
        ]
        
        scenario = random.choice(scenarios)
        
        return {
            'content': scenario['content'],
            'options': [{'key': 'A', 'value': '正确'}, {'key': 'B', 'value': '错误'}],
            'correct_answer': scenario['correct_answer'],
            'knowledge_points': [topic, concept, '逻辑推理'],
            'explanation': f"这是一个{scenario['logic_type']}问题.",
            'analysis': "本题考查逻辑推理能力和论证结构."
        }

    def get_question(self, question_id: str) -> Optional[Question]:
        """获取题目"""
        return self._questions.get(question_id)

    def search_questions(self, **filters) -> List[Question]:
        """搜索题目"""
        results = list(self._questions.values())
        
        if 'type' in filters:
            results = [q for q in results if q.type == QuestionType(filters['type'])]
        if 'category' in filters:
            results = [q for q in results if q.category == QuestionCategory(filters['category'])]
        if 'difficulty' in filters:
            results = [q for q in results if q.difficulty == DifficultyLevel(filters['difficulty'])]
        if 'keyword' in filters:
            keyword = filters['keyword'].lower()
            results = [q for q in results if keyword in q.content.lower()]
        if 'knowledge_point' in filters:
            kp = filters['knowledge_point']
            results = [q for q in results if kp in q.knowledge_points]
        if 'year' in filters:
            results = [q for q in results if q.year == filters['year']]
        
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def generate_exam_paper(self, 
                           title: str,
                           total_score: float = 100.0,
                           question_counts: Dict[str, int] = None,
                           difficulty_distribution: Dict[str, float] = None,
                           categories: List[str] = None) -> Dict:
        """智能生成试卷"""
        if question_counts is None:
            question_counts = {
                'single_choice': 20,
                'multiple_choice': 10,
                'true_false': 10,
                'fill_blank': 10,
                'short_answer': 5,
                'calculation': 3,
                'essay': 2
            }
        
        if difficulty_distribution is None:
            difficulty_distribution = {
                'easy': 0.2,
                'medium': 0.4,
                'hard': 0.25,
                'expert': 0.15
            }
        
        if categories is None:
            categories = ['must_know', 'special_topic', 'calculation', 'logic']
        
        questions = []
        
        for q_type, count in question_counts.items():
            if count <= 0:
                continue
            
            type_questions = []
            for cat in categories:
                type_questions.extend(self.search_questions(type=q_type, category=cat))
            
            if not type_questions:
                continue
            
            selected = []
            for diff, ratio in difficulty_distribution.items():
                diff_count = int(count * ratio)
                if diff_count <= 0:
                    continue
                
                diff_questions = [q for q in type_questions if q.difficulty.value == diff]
                if diff_questions:
                    selected.extend(random.sample(diff_questions, min(diff_count, len(diff_questions))))
            
            remaining = count - len(selected)
            if remaining > 0:
                available = [q for q in type_questions if q not in selected]
                selected.extend(random.sample(available, min(remaining, len(available))))
            
            questions.extend(selected)
        
        random.shuffle(questions)
        avg_score = total_score / len(questions) if questions else 0
        
        paper = {
            'title': title,
            'total_score': total_score,
            'question_count': len(questions),
            'questions': [],
            'created_at': time.time()
        }
        
        for i, q in enumerate(questions):
            paper['questions'].append({
                'index': i + 1,
                'question_id': q.question_id,
                'type': q.type.value,
                'difficulty': q.difficulty.value,
                'score': round(avg_score * (1.5 if q.difficulty.value in ['hard', 'expert'] else 1), 1),
                'content': q.content,
                'options': q.options
            })
        
        return paper

    def get_statistics(self) -> QuestionBankStats:
        """获取题库统计"""
        stats = QuestionBankStats()
        stats.total_questions = len(self._questions)
        
        for q in self._questions.values():
            stats.by_type[q.type.value] = stats.by_type.get(q.type.value, 0) + 1
            stats.by_category[q.category.value] = stats.by_category.get(q.category.value, 0) + 1
            stats.by_difficulty[q.difficulty.value] = stats.by_difficulty.get(q.difficulty.value, 0) + 1
            
            if q.year:
                stats.by_year[q.year] = stats.by_year.get(q.year, 0) + 1
            
            stats.total_usage += q.usage_count
        
        if stats.total_questions > 0:
            stats.avg_correct_rate = sum(q.correct_rate for q in self._questions.values()) / stats.total_questions
        
        return stats

    def get_categories(self) -> Dict[str, List[str]]:
        """获取所有分类"""
        return self._categories

    def import_from_json(self, file_path: str) -> Tuple[int, int]:
        """从JSON文件导入题目"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            questions_data = data.get('questions', [])
            return self.add_questions_batch(questions_data)
        except Exception as e:
            logger.error(f"导入失败: {str(e)}")
            return 0, 1

    def export_to_json(self, file_path: str) -> bool:
        """导出题目到JSON文件"""
        try:
            data = {
                'exported_at': time.time(),
                'total_questions': len(self._questions),
                'questions': [q.to_dict() for q in self._questions.values()]
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"导出失败: {str(e)}")
            return False


# 创建全局实例
enhanced_question_bank_service = EnhancedQuestionBankService()


def init_mass_question_bank():
    """初始化海量题库"""
    logger.info("开始初始化海量题库...")
    
    # 生成各类题目
    generated = enhanced_question_bank_service.generate_mass_questions(100)
    logger.info(f"已生成 {generated} 道题目")
    
    # 添加历年真题示例
    real_exam_data = [
        {
            'type': 'single_choice',
            'difficulty': 'medium',
            'content': 'Python中,以下哪个关键字用于定义类?',
            'options': [
                {'key': 'A', 'value': 'class'},
                {'key': 'B', 'value': 'def'},
                {'key': 'C', 'value': 'struct'},
                {'key': 'D', 'value': 'type'}
            ],
            'correct_answer': 'A',
            'knowledge_points': ['Python', '面向对象'],
            'tags': ['真题']
        }
    ]
    enhanced_question_bank_service.add_real_exam_questions(2024, real_exam_data)
    
    logger.info("海量题库初始化完成")
