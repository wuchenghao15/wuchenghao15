#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI拓展题库服务 - 海量题库管理与专家AI出题系统
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


class AIQuestionBankService:
    """AI拓展题库服务"""

    def __init__(self):
        self._questions: Dict[str, Question] = {}
        self._knowledge_points: Dict[str, List[str]] = {}
        self._categories: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        self._db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'question_bank.json')
        
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        
        self._load_question_bank()
        self._init_default_categories()
        
        logger.info("AI拓展题库服务初始化完成")

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
            'real_exam': ['历年真题', '真题演练', '真题模拟'],
            'must_know': ['必考知识点', '高频考点', '核心考点'],
            'final': ['压轴题', '综合题', '难题'],
            'bonus': ['加分题', '拓展题', '提升题'],
            'special_topic': ['专项突破', '专题训练', '强化训练'],
            'key_point': ['重点分析', '难点解析', '深度剖析'],
            'calculation': ['计算题', '应用题', '数值计算'],
            'logic': ['逻辑判断', '推理题', '分析题'],
            'error_prone': ['易错题', '常考题', '易错点'],
            'formula': ['公式运用', '公式推导', '公式应用'],
            'comprehension': ['阅读理解', '综合理解', '案例分析']
        }

    def _generate_question_id(self) -> str:
        """生成题目ID"""
        import uuid
        return f"Q-{int(time.time())}-{uuid.uuid4().hex[:6]}"

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

    def get_question(self, question_id: str) -> Optional[Question]:
        """获取题目"""
        return self._questions.get(question_id)

    def delete_question(self, question_id: str) -> bool:
        """删除题目"""
        with self._lock:
            if question_id in self._questions:
                del self._questions[question_id]
                self._save_question_bank()
                return True
        return False

    def update_question(self, question_id: str, updates: Dict) -> bool:
        """更新题目"""
        with self._lock:
            if question_id in self._questions:
                question = self._questions[question_id]
                for key, value in updates.items():
                    if hasattr(question, key):
                        if key in ['type', 'category', 'difficulty']:
                            setattr(question, key, QuestionType(value) if key == 'type' else 
                                   QuestionCategory(value) if key == 'category' else 
                                   DifficultyLevel(value))
                        else:
                            setattr(question, key, value)
                question.updated_at = time.time()
                self._save_question_bank()
                return True
        return False

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

    def get_random_questions(self, count: int = 10, **filters) -> List[Question]:
        """获取随机题目"""
        results = self.search_questions(**filters)
        return random.sample(results, min(count, len(results)))

    def generate_exam_paper(self, 
                           title: str,
                           total_score: float = 100.0,
                           question_counts: Dict[str, int] = None,
                           difficulty_distribution: Dict[str, float] = None) -> Dict:
        """生成试卷"""
        if question_counts is None:
            question_counts = {
                'single_choice': 10,
                'multiple_choice': 5,
                'true_false': 5,
                'fill_blank': 5,
                'short_answer': 3,
                'calculation': 2
            }
        
        if difficulty_distribution is None:
            difficulty_distribution = {
                'easy': 0.3,
                'medium': 0.4,
                'hard': 0.2,
                'expert': 0.1
            }
        
        questions = []
        total_count = sum(question_counts.values())
        remaining_score = total_score
        
        for q_type, count in question_counts.items():
            if count <= 0:
                continue
            
            # 根据难度分布获取题目
            type_questions = self.search_questions(type=q_type)
            if not type_questions:
                continue
            
            # 按难度分层选择
            selected = []
            for diff, ratio in difficulty_distribution.items():
                diff_count = int(count * ratio)
                if diff_count <= 0:
                    continue
                
                diff_questions = [q for q in type_questions if q.difficulty.value == diff]
                if diff_questions:
                    selected.extend(random.sample(diff_questions, min(diff_count, len(diff_questions))))
            
            # 补充剩余题目
            remaining = count - len(selected)
            if remaining > 0:
                available = [q for q in type_questions if q not in selected]
                selected.extend(random.sample(available, min(remaining, len(available))))
            
            questions.extend(selected)
        
        # 随机打乱顺序
        random.shuffle(questions)
        
        # 分配分数
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
                'score': round(avg_score, 1),
                'content': q.content,
                'options': q.options
            })
        
        return paper

    def ai_generate_question(self, 
                            knowledge_points: List[str],
                            question_type: str = "single_choice",
                            difficulty: str = "medium",
                            category: str = "special_topic") -> Dict:
        """AI生成题目"""
        templates = {
            'single_choice': self._generate_single_choice,
            'multiple_choice': self._generate_multiple_choice,
            'true_false': self._generate_true_false,
            'fill_blank': self._generate_fill_blank,
            'calculation': self._generate_calculation,
            'logic_judgment': self._generate_logic_judgment
        }
        
        generator = templates.get(question_type, self._generate_single_choice)
        return generator(knowledge_points, difficulty, category)

    def _generate_single_choice(self, kp: List[str], difficulty: str, category: str) -> Dict:
        """生成单选题"""
        topics = {
            '数学': {
                '基础': ['函数的定义域', '导数计算', '积分应用'],
                '进阶': ['极限计算', '微分方程', '级数收敛']
            },
            '物理': {
                '基础': ['牛顿定律', '能量守恒', '动量定理'],
                '进阶': ['电磁感应', '量子力学', '相对论']
            },
            '编程': {
                '基础': ['变量定义', '条件判断', '循环结构'],
                '进阶': ['算法复杂度', '数据结构', '设计模式']
            }
        }
        
        topic = random.choice(list(topics.keys()))
        level = '进阶' if difficulty in ['hard', 'expert', 'challenge'] else '基础'
        sub_topic = random.choice(topics[topic].get(level, topics[topic]['基础']))
        
        question_templates = [
            f"关于{topic}中的{sub_topic},以下说法正确的是:",
            f"{sub_topic}的核心概念是:",
            f"下列关于{sub_topic}的描述,错误的是:",
            f"{sub_topic}适用于以下哪种情况?"
        ]
        
        content = random.choice(question_templates)
        
        options = [
            {'key': 'A', 'value': f"{sub_topic}的基本定义"},
            {'key': 'B', 'value': f"{sub_topic}的应用场景"},
            {'key': 'C', 'value': f"{sub_topic}的核心原理"},
            {'key': 'D', 'value': f"{sub_topic}的常见误区"}
        ]
        
        return {
            'type': 'single_choice',
            'category': category,
            'difficulty': difficulty,
            'content': content,
            'options': options,
            'correct_answer': 'C',
            'knowledge_points': kp + [sub_topic],
            'explanation': f"本题考查{topic}中{sub_topic}的核心概念.",
            'analysis': f"{sub_topic}是{topic}中的重要知识点,需要深入理解其原理和应用."
        }

    def _generate_multiple_choice(self, kp: List[str], difficulty: str, category: str) -> Dict:
        """生成多选题"""
        return {
            'type': 'multiple_choice',
            'category': category,
            'difficulty': difficulty,
            'content': "以下哪些属于面向对象编程的基本原则?",
            'options': [
                {'key': 'A', 'value': '封装性'},
                {'key': 'B', 'value': '继承性'},
                {'key': 'C', 'value': '多态性'},
                {'key': 'D', 'value': '过程化'}
            ],
            'correct_answer': ['A', 'B', 'C'],
            'knowledge_points': kp + ['面向对象', '封装', '继承', '多态'],
            'explanation': "面向对象编程的三大基本原则是封装、继承和多态.",
            'analysis': "本题考查面向对象编程的基本概念,需要理解每个原则的含义和作用."
        }

    def _generate_true_false(self, kp: List[str], difficulty: str, category: str) -> Dict:
        """生成判断题"""
        statements = [
            ("Python中的列表是可变的", True),
            ("TCP协议是无连接的", False),
            ("二叉树的前序遍历顺序是根-左-右", True),
            ("SQL中的SELECT语句用于更新数据", False)
        ]
        
        statement, answer = random.choice(statements)
        
        return {
            'type': 'true_false',
            'category': category,
            'difficulty': difficulty,
            'content': statement,
            'options': [{'key': 'A', 'value': '正确'}, {'key': 'B', 'value': '错误'}],
            'correct_answer': 'A' if answer else 'B',
            'knowledge_points': kp + ['基础概念'],
            'explanation': f"该陈述{'正确' if answer else '错误'}.",
            'analysis': "本题考查基础知识的掌握程度."
        }

    def _generate_fill_blank(self, kp: List[str], difficulty: str, category: str) -> Dict:
        """生成填空题"""
        blanks = [
            ("在Python中,使用____关键字定义函数.", "def"),
            ("HTTP协议默认端口号是____.", "80"),
            ("二叉搜索树的平均查找时间复杂度是____.", "O(log n)")
        ]
        
        question, answer = random.choice(blanks)
        
        return {
            'type': 'fill_blank',
            'category': category,
            'difficulty': difficulty,
            'content': question,
            'correct_answer': answer,
            'knowledge_points': kp + ['基础语法', '网络协议', '数据结构'],
            'explanation': f"正确答案是:{answer}",
            'analysis': "本题考查基础知识点的记忆和理解."
        }

    def _generate_calculation(self, kp: List[str], difficulty: str, category: str) -> Dict:
        """生成计算题"""
        problems = [
            {
                'content': "已知函数 f(x) = x^2 + 2x + 1,求 f'(x) 在 x=2 处的值.",
                'correct_answer': "6",
                'formula': ["导数公式", "幂函数求导"]
            },
            {
                'content': "一个等差数列的首项为2,公差为3,求第10项的值.",
                'correct_answer': "29",
                'formula': ["等差数列通项公式"]
            }
        ]
        
        problem = random.choice(problems)
        
        return {
            'type': 'calculation',
            'category': category,
            'difficulty': difficulty,
            'content': problem['content'],
            'correct_answer': problem['correct_answer'],
            'knowledge_points': kp + ['计算能力'],
            'formula_used': problem['formula'],
            'explanation': f"正确答案是:{problem['correct_answer']}",
            'analysis': "本题考查公式的应用和计算能力."
        }

    def _generate_logic_judgment(self, kp: List[str], difficulty: str, category: str) -> Dict:
        """生成逻辑判断题"""
        scenarios = [
            {
                'content': "如果所有程序员都会编程,小明是程序员,那么小明会编程.这个推理是否正确?",
                'correct_answer': 'A',
                'logic_type': '三段论'
            }
        ]
        
        scenario = random.choice(scenarios)
        
        return {
            'type': 'logic_judgment',
            'category': category,
            'difficulty': difficulty,
            'content': scenario['content'],
            'options': [{'key': 'A', 'value': '正确'}, {'key': 'B', 'value': '错误'}],
            'correct_answer': scenario['correct_answer'],
            'knowledge_points': kp + ['逻辑推理', scenario['logic_type']],
            'explanation': "这是一个有效的三段论推理.",
            'analysis': "本题考查逻辑推理能力和论证结构."
        }

    def ai_generate_batch(self, 
                         count: int = 10,
                         knowledge_points: List[str] = None,
                         categories: List[str] = None) -> List[Dict]:
        """批量AI生成题目"""
        if knowledge_points is None:
            knowledge_points = ['综合知识']
        
        if categories is None:
            categories = ['special_topic', 'must_know', 'key_point']
        
        questions = []
        types = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'calculation', 'logic_judgment']
        difficulties = ['easy', 'medium', 'hard']
        
        for _ in range(count):
            q_type = random.choice(types)
            difficulty = random.choice(difficulties)
            category = random.choice(categories)
            
            question = self.ai_generate_question(
                knowledge_points=knowledge_points,
                question_type=q_type,
                difficulty=difficulty,
                category=category
            )
            questions.append(question)
        
        return questions

    def get_statistics(self) -> QuestionBankStats:
        """获取题库统计"""
        stats = QuestionBankStats()
        stats.total_questions = len(self._questions)
        
        for q in self._questions.values():
            type_key = q.type.value
            cat_key = q.category.value
            diff_key = q.difficulty.value
            
            stats.by_type[type_key] = stats.by_type.get(type_key, 0) + 1
            stats.by_category[cat_key] = stats.by_category.get(cat_key, 0) + 1
            stats.by_difficulty[diff_key] = stats.by_difficulty.get(diff_key, 0) + 1
            
            if q.year:
                stats.by_year[q.year] = stats.by_year.get(q.year, 0) + 1
            
            stats.total_usage += q.usage_count
        
        if stats.total_questions > 0:
            avg_correct = sum(q.correct_rate for q in self._questions.values())
            stats.avg_correct_rate = avg_correct / stats.total_questions
        
        return stats

    def get_categories(self) -> Dict[str, List[str]]:
        """获取所有分类"""
        return self._categories

    def add_knowledge_point(self, category: str, kp: str):
        """添加知识点"""
        if category not in self._categories:
            self._categories[category] = []
        if kp not in self._categories[category]:
            self._categories[category].append(kp)

    def get_knowledge_points(self, category: str = None) -> List[str]:
        """获取知识点"""
        if category:
            return self._categories.get(category, [])
        all_kp = []
        for kps in self._categories.values():
            all_kp.extend(kps)
        return list(set(all_kp))


# 创建全局实例
ai_question_bank_service = AIQuestionBankService()
