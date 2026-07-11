#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI题库自动维护系统
使用Python技术和AI技术实现增量题库内容生成和维护
集成现有题库服务和AI助手功能
"""

import os
import sys
import json
import sqlite3
import uuid
import time
import random
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, PROJECT_ROOT)

from app.services.question_bank_service import question_bank_service
from app.ai.question_bank_ai import question_bank_ai_assistant, ListeningLanguage, ListeningAccent, ListeningVoice, ListeningDifficulty, ListeningTopic


class QuestionType(Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CALCULATION = "calculation"
    LISTENING = "listening"
    READING = "reading"


class Subject(Enum):
    """学科类型"""
    MATHEMATICS = "mathematics"
    ENGLISH = "english"
    CHINESE = "chinese"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICS = "politics"
    JAPANESE = "japanese"
    COMPUTER = "computer"


class Difficulty(Enum):
    """难度等级"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class MaintenanceMode(Enum):
    """维护模式"""
    INCREMENTAL = "incremental"
    FULL = "full"
    QUALITY_CHECK = "quality_check"
    DUPLICATE_REMOVAL = "duplicate_removal"
    CATEGORY_OPTIMIZATION = "category_optimization"


@dataclass
class GeneratedQuestion:
    """生成的题目数据类"""
    question_id: str
    type: str
    subject: str
    category: str
    difficulty: str
    content: str
    options: List[Dict[str, str]] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    analysis: str = ""
    knowledge_points: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: str = "AI生成"
    score: float = 5.0
    quality_score: float = 0.0
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'question_id': self.question_id,
            'type': self.type,
            'subject': self.subject,
            'category': self.category,
            'difficulty': self.difficulty,
            'content': self.content,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'analysis': self.analysis,
            'knowledge_points': self.knowledge_points,
            'tags': self.tags,
            'source': self.source,
            'score': self.score,
            'quality_score': self.quality_score,
            'created_at': self.created_at
        }


@dataclass
class MaintenanceResult:
    """维护结果"""
    success: bool = False
    message: str = ""
    total_generated: int = 0
    total_added: int = 0
    total_duplicates: int = 0
    total_quality_issues: int = 0
    processed_categories: int = 0
    execution_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class AIQuestionMaintenance:
    """AI题库自动维护系统"""

    def __init__(self):
        self.db_path = os.path.join(PROJECT_ROOT, 'app.db')
        self._lock = threading.RLock()
        self._init_database()
        self._init_knowledge_base()
        logger.info("[AI题库维护] AI题库自动维护系统初始化完成")

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS ai_maintenance_questions (
            question_id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            subject TEXT NOT NULL,
            category TEXT,
            difficulty TEXT,
            content TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            analysis TEXT,
            knowledge_points TEXT,
            tags TEXT,
            source TEXT DEFAULT 'AI生成',
            score REAL DEFAULT 5.0,
            quality_score REAL DEFAULT 0.0,
            created_at REAL,
            is_valid INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            correct_rate REAL DEFAULT 0.0
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_maintenance_logs (
            log_id TEXT PRIMARY KEY,
            operation TEXT NOT NULL,
            subject TEXT,
            generated_count INTEGER DEFAULT 0,
            added_count INTEGER DEFAULT 0,
            duplicate_count INTEGER DEFAULT 0,
            quality_issues_count INTEGER DEFAULT 0,
            status TEXT,
            started_at REAL,
            completed_at REAL,
            execution_time REAL,
            details TEXT
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_content_hashes (
            hash_id TEXT PRIMARY KEY,
            content_hash TEXT UNIQUE NOT NULL,
            question_id TEXT NOT NULL,
            created_at REAL
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS subject_knowledge_points (
            point_id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            knowledge_point TEXT NOT NULL,
            category TEXT,
            difficulty TEXT,
            question_count INTEGER DEFAULT 0,
            last_generated_at REAL,
            created_at REAL
        )''')

        conn.commit()
        conn.close()

    def _init_knowledge_base(self):
        """初始化知识库"""
        self.knowledge_base = {
            'mathematics': {
                'categories': ['代数', '几何', '概率统计', '函数', '三角函数', '数列', '不等式'],
                'knowledge_points': [
                    ('一元二次方程', '代数', 'easy'),
                    ('二元一次方程组', '代数', 'easy'),
                    ('一元三次方程', '代数', 'medium'),
                    ('集合与逻辑', '代数', 'easy'),
                    ('函数定义与性质', '函数', 'medium'),
                    ('指数函数', '函数', 'medium'),
                    ('对数函数', '函数', 'medium'),
                    ('三角函数', '三角函数', 'hard'),
                    ('平面向量', '几何', 'medium'),
                    ('立体几何', '几何', 'hard'),
                    ('概率', '概率统计', 'medium'),
                    ('统计', '概率统计', 'easy'),
                    ('数列', '数列', 'medium'),
                    ('等差数列', '数列', 'easy'),
                    ('等比数列', '数列', 'medium'),
                    ('不等式', '不等式', 'hard')
                ],
                'templates': {
                    'single_choice': [
                        {
                            'format': '关于{knowledge_point}的说法，正确的是：',
                            'options': [
                                '正确表述', '错误表述1', '错误表述2', '错误表述3'
                            ],
                            'answer_index': 0
                        },
                        {
                            'format': '{knowledge_point}的计算公式是：',
                            'options': [
                                '正确公式', '错误公式1', '错误公式2', '错误公式3'
                            ],
                            'answer_index': 0
                        }
                    ],
                    'fill_blank': [
                        {
                            'format': '{knowledge_point}的核心公式是__________。',
                            'answer': '核心公式内容'
                        }
                    ],
                    'calculation': [
                        {
                            'format': '已知条件，求{knowledge_point}相关问题。',
                            'answer': '计算步骤和结果'
                        }
                    ]
                }
            },
            'english': {
                'categories': ['语法', '词汇', '阅读理解', '听力', '写作', '翻译'],
                'knowledge_points': [
                    ('一般现在时', '语法', 'easy'),
                    ('一般过去时', '语法', 'easy'),
                    ('现在进行时', '语法', 'easy'),
                    ('现在完成时', '语法', 'medium'),
                    ('过去完成时', '语法', 'medium'),
                    ('虚拟语气', '语法', 'hard'),
                    ('定语从句', '语法', 'hard'),
                    ('名词性从句', '语法', 'hard'),
                    ('动词时态', '语法', 'medium'),
                    ('介词搭配', '语法', 'easy'),
                    ('高频词汇', '词汇', 'easy'),
                    ('核心词汇', '词汇', 'medium'),
                    ('专业词汇', '词汇', 'hard'),
                    ('阅读理解技巧', '阅读理解', 'medium'),
                    ('听力技巧', '听力', 'medium')
                ],
                'templates': {
                    'single_choice': [
                        {
                            'format': 'Choose the correct answer: {knowledge_point}',
                            'options': [
                                'Correct answer', 'Wrong answer 1', 'Wrong answer 2', 'Wrong answer 3'
                            ],
                            'answer_index': 0
                        }
                    ],
                    'fill_blank': [
                        {
                            'format': 'Fill in the blank with {knowledge_point}...',
                            'answer': 'Correct word/phrase'
                        }
                    ]
                }
            },
            'chinese': {
                'categories': ['阅读理解', '写作', '文言文', '诗词鉴赏', '现代文阅读'],
                'knowledge_points': [
                    ('文言文实词', '文言文', 'medium'),
                    ('文言文虚词', '文言文', 'hard'),
                    ('诗词鉴赏', '诗词鉴赏', 'hard'),
                    ('现代文阅读', '现代文阅读', 'medium'),
                    ('写作技巧', '写作', 'medium'),
                    ('修辞手法', '阅读理解', 'easy'),
                    ('文章结构', '阅读理解', 'medium'),
                    ('主题分析', '阅读理解', 'hard')
                ],
                'templates': {
                    'single_choice': [
                        {
                            'format': '关于{knowledge_point}的分析，正确的是：',
                            'options': ['正确分析', '错误分析1', '错误分析2', '错误分析3'],
                            'answer_index': 0
                        }
                    ],
                    'short_answer': [
                        {
                            'format': '请分析{knowledge_point}在文中的作用。',
                            'answer': '分析内容'
                        }
                    ]
                }
            },
            'physics': {
                'categories': ['力学', '电学', '光学', '热学', '原子物理'],
                'knowledge_points': [
                    ('牛顿运动定律', '力学', 'medium'),
                    ('动量守恒', '力学', 'hard'),
                    ('能量守恒', '力学', 'medium'),
                    ('电场', '电学', 'medium'),
                    ('磁场', '电学', 'hard'),
                    ('电路', '电学', 'easy'),
                    ('光的反射', '光学', 'easy'),
                    ('光的折射', '光学', 'medium'),
                    ('热力学定律', '热学', 'medium'),
                    ('原子结构', '原子物理', 'hard')
                ],
                'templates': {
                    'calculation': [
                        {
                            'format': '已知条件，运用{knowledge_point}求解。',
                            'answer': '解题步骤'
                        }
                    ],
                    'single_choice': [
                        {
                            'format': '关于{knowledge_point}的物理规律，正确的是：',
                            'options': ['正确规律', '错误规律1', '错误规律2', '错误规律3'],
                            'answer_index': 0
                        }
                    ]
                }
            },
            'chemistry': {
                'categories': ['无机化学', '有机化学', '化学反应', '化学平衡'],
                'knowledge_points': [
                    ('原子结构', '无机化学', 'easy'),
                    ('化学键', '无机化学', 'medium'),
                    ('化学反应方程式', '化学反应', 'medium'),
                    ('化学平衡', '化学平衡', 'hard'),
                    ('有机化合物', '有机化学', 'medium'),
                    ('烃类化合物', '有机化学', 'easy'),
                    ('醇酚醚', '有机化学', 'medium')
                ],
                'templates': {
                    'single_choice': [
                        {
                            'format': '关于{knowledge_point}的化学性质，正确的是：',
                            'options': ['正确性质', '错误性质1', '错误性质2', '错误性质3'],
                            'answer_index': 0
                        }
                    ],
                    'fill_blank': [
                        {
                            'format': '{knowledge_point}的化学式是__________。',
                            'answer': '正确化学式'
                        }
                    ]
                }
            },
            'politics': {
                'categories': ['马克思主义原理', '毛泽东思想', '中国特色社会主义', '时事政治'],
                'knowledge_points': [
                    ('唯物论', '马克思主义原理', 'medium'),
                    ('辩证法', '马克思主义原理', 'hard'),
                    ('认识论', '马克思主义原理', 'medium'),
                    ('历史唯物主义', '马克思主义原理', 'hard'),
                    ('毛泽东思想概论', '毛泽东思想', 'medium'),
                    ('中国特色社会主义理论', '中国特色社会主义', 'medium'),
                    ('时事政治', '时事政治', 'easy')
                ],
                'templates': {
                    'single_choice': [
                        {
                            'format': '关于{knowledge_point}的理论，正确的是：',
                            'options': ['正确理论', '错误理论1', '错误理论2', '错误理论3'],
                            'answer_index': 0
                        }
                    ],
                    'short_answer': [
                        {
                            'format': '请阐述{knowledge_point}的主要内容。',
                            'answer': '阐述内容'
                        }
                    ]
                }
            }
        }

        self.subject_question_templates = {
            'single_choice': {
                'math': [
                    {'question': '若函数f(x)={expr}，则f({val})的值为：', 'options': ['{ans}', '{opt1}', '{opt2}', '{opt3}']},
                    {'question': '关于{topic}的性质，下列说法正确的是：', 'options': ['正确选项', '错误选项1', '错误选项2', '错误选项3']},
                    {'question': '{topic}的计算公式是：', 'options': ['正确公式', '错误公式1', '错误公式2', '错误公式3']}
                ],
                'general': [
                    {'question': '关于{topic}，下列说法正确的是：', 'options': ['正确选项', '错误选项1', '错误选项2', '错误选项3']},
                    {'question': '{topic}的核心要点是：', 'options': ['核心要点', '次要要点', '相关要点', '无关要点']}
                ]
            },
            'multiple_choice': {
                'general': [
                    {'question': '下列关于{topic}的说法，正确的有（多选）：', 'options': ['正确选项1', '正确选项2', '正确选项3', '错误选项']}
                ]
            },
            'fill_blank': {
                'general': [
                    {'question': '{topic}的核心概念是__________。', 'answer': '核心概念'},
                    {'question': '{topic}的计算公式是__________。', 'answer': '计算公式'}
                ]
            },
            'short_answer': {
                'general': [
                    {'question': '请简述{topic}的主要内容。', 'answer': '{topic}的主要内容包括...'}
                ]
            },
            'calculation': {
                'math': [
                    {'question': '已知条件，计算{topic}相关问题。', 'answer': '计算步骤和结果'}
                ],
                'physics': [
                    {'question': '已知物理条件，运用{topic}求解。', 'answer': '解题步骤'}
                ]
            }
        }

    def _generate_question_id(self) -> str:
        """生成题目ID"""
        timestamp = int(time.time())
        random_str = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
        return f"AIQ-{timestamp}-{random_str}"

    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希用于去重"""
        return hashlib.sha256(content.strip().lower().encode()).hexdigest()

    def _is_duplicate(self, content: str) -> bool:
        """检查是否重复"""
        content_hash = self._calculate_content_hash(content)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT hash_id FROM question_content_hashes WHERE content_hash = ?', (content_hash,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None

    def _record_content_hash(self, question_id: str, content: str):
        """记录内容哈希"""
        content_hash = self._calculate_content_hash(content)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT OR IGNORE INTO question_content_hashes
            (hash_id, content_hash, question_id, created_at)
            VALUES (?, ?, ?, ?)''', (str(uuid.uuid4())[:16], content_hash, question_id, time.time()))
        conn.commit()
        conn.close()

    def _calculate_quality_score(self, question: GeneratedQuestion) -> float:
        """计算题目质量分数"""
        score = 0.0
        
        content_length = len(question.content)
        if content_length >= 10:
            score += 20
        elif content_length >= 5:
            score += 10
        
        if len(question.options) >= 4:
            score += 15
        elif len(question.options) >= 2:
            score += 5
        
        if question.correct_answer:
            score += 20
        
        if len(question.explanation) >= 20:
            score += 20
        elif len(question.explanation) >= 10:
            score += 10
        
        if question.analysis:
            score += 10
        
        if question.knowledge_points:
            score += 10
        
        if question.difficulty in ['easy', 'medium', 'hard']:
            score += 5
        
        return score

    def _generate_single_question(self, subject: str, question_type: str, 
                                 difficulty: str = 'medium') -> Optional[GeneratedQuestion]:
        """生成单个题目"""
        try:
            subject_info = self.knowledge_base.get(subject, self.knowledge_base.get('mathematics'))
            
            knowledge_point_info = random.choice(subject_info['knowledge_points'])
            knowledge_point, category, default_difficulty = knowledge_point_info
            
            if difficulty == 'auto':
                difficulty = default_difficulty
            
            templates = subject_info['templates'].get(question_type, subject_info['templates'].get('single_choice', []))
            if not templates:
                templates = self.subject_question_templates.get(question_type, {}).get('general', [])
            
            if not templates:
                templates = self.subject_question_templates.get('single_choice', {}).get('general', [])
            
            template = random.choice(templates)
            
            content = template.get('format', '{topic}相关问题').format(
                knowledge_point=knowledge_point,
                topic=knowledge_point,
                expr=self._generate_math_expression(subject, difficulty),
                val=random.randint(1, 100)
            )
            
            options = []
            if 'options' in template:
                correct_answer = template['options'][template.get('answer_index', 0)]
                option_keys = ['A', 'B', 'C', 'D']
                
                if question_type == 'multiple_choice':
                    correct_indices = [0, 1, 2]
                    correct_answer = ''.join([option_keys[i] for i in correct_indices])
                    for i, opt in enumerate(template['options']):
                        options.append({
                            'key': option_keys[i],
                            'value': opt
                        })
                else:
                    for i, opt in enumerate(template['options']):
                        options.append({
                            'key': option_keys[i],
                            'value': opt
                        })
                    correct_answer = option_keys[template.get('answer_index', 0)]
            else:
                correct_answer = template.get('answer', '')
            
            explanation = f"本题考查{knowledge_point}的相关知识。"
            analysis = f"考点：{knowledge_point}\n难度：{difficulty}"
            
            question = GeneratedQuestion(
                question_id=self._generate_question_id(),
                type=question_type,
                subject=subject,
                category=category,
                difficulty=difficulty,
                content=content,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                analysis=analysis,
                knowledge_points=[knowledge_point],
                tags=[subject, category, difficulty],
                source='AI生成',
                score=self._calculate_score(difficulty, question_type)
            )
            
            question.quality_score = self._calculate_quality_score(question)
            
            return question
        
        except Exception as e:
            logger.error(f"生成题目失败: {e}")
            return None

    def _generate_math_expression(self, subject: str, difficulty: str) -> str:
        """生成数学表达式"""
        if subject == 'mathematics':
            if difficulty == 'easy':
                return f"x^2 + {random.randint(1, 10)}x + {random.randint(1, 10)}"
            elif difficulty == 'medium':
                return f"({random.randint(1, 5)}x + {random.randint(1, 10)})^2"
            else:
                return f"sin({random.randint(1, 5)}x) + cos({random.randint(1, 5)}x)"
        return "x"

    def _calculate_score(self, difficulty: str, question_type: str) -> float:
        """计算题目分值"""
        score_map = {
            "easy": 2.0,
            "medium": 5.0,
            "hard": 10.0,
            "expert": 15.0
        }
        type_multiplier = {
            "single_choice": 1.0,
            "multiple_choice": 1.2,
            "true_false": 0.8,
            "fill_blank": 1.0,
            "short_answer": 1.5,
            "essay": 2.0,
            "calculation": 1.5,
            "listening": 1.5,
            "reading": 1.5
        }
        base = score_map.get(difficulty, 5.0)
        multiplier = type_multiplier.get(question_type, 1.0)
        return base * multiplier

    def _save_question(self, question: GeneratedQuestion) -> bool:
        """保存题目到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''INSERT OR REPLACE INTO ai_maintenance_questions
                (question_id, type, subject, category, difficulty, content, options,
                 correct_answer, explanation, analysis, knowledge_points, tags,
                 source, score, quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (question.question_id, question.type, question.subject,
                 question.category, question.difficulty, question.content,
                 json.dumps(question.options), question.correct_answer,
                 question.explanation, question.analysis,
                 json.dumps(question.knowledge_points), json.dumps(question.tags),
                 question.source, question.score, question.quality_score,
                 question.created_at))
            
            conn.commit()
            conn.close()
            
            self._record_content_hash(question.question_id, question.content)
            
            return True
        except Exception as e:
            logger.error(f"保存题目失败: {e}")
            return False

    def generate_questions(self, subject: str, count: int = 10,
                          question_type: str = 'single_choice',
                          difficulty: str = 'auto') -> List[GeneratedQuestion]:
        """生成题目"""
        questions = []
        for _ in range(count):
            question = self._generate_single_question(subject, question_type, difficulty)
            if question:
                questions.append(question)
        return questions

    def batch_generate_and_save(self, subject: str, count: int = 10,
                                question_type: str = 'all',
                                difficulty: str = 'auto') -> Dict[str, Any]:
        """批量生成并保存题目"""
        generated_count = 0
        added_count = 0
        duplicate_count = 0
        quality_issues_count = 0
        
        types = [question_type] if question_type != 'all' else \
                ['single_choice', 'multiple_choice', 'fill_blank', 'short_answer']
        
        difficulties = ['easy', 'medium', 'hard'] if difficulty == 'auto' else [difficulty]
        
        for _ in range(count):
            q_type = random.choice(types)
            diff = random.choice(difficulties) if difficulty == 'auto' else difficulty
            
            question = self._generate_single_question(subject, q_type, diff)
            
            if not question:
                continue
            
            generated_count += 1
            
            if self._is_duplicate(question.content):
                duplicate_count += 1
                continue
            
            if question.quality_score < 50:
                quality_issues_count += 1
                continue
            
            if self._save_question(question):
                added_count += 1
        
        return {
            'success': True,
            'generated_count': generated_count,
            'added_count': added_count,
            'duplicate_count': duplicate_count,
            'quality_issues_count': quality_issues_count,
            'subject': subject,
            'message': f"生成 {generated_count} 道题，成功添加 {added_count} 道，重复 {duplicate_count} 道，质量问题 {quality_issues_count} 道"
        }

    def run_incremental_maintenance(self, subjects: List[str] = None, 
                                    count_per_subject: int = 20) -> MaintenanceResult:
        """执行增量维护"""
        start_time = time.time()
        
        if subjects is None:
            subjects = list(self.knowledge_base.keys())
        
        total_generated = 0
        total_added = 0
        total_duplicates = 0
        total_quality_issues = 0
        
        details = {}
        
        for subject in subjects:
            result = self.batch_generate_and_save(subject, count_per_subject)
            details[subject] = result
            
            total_generated += result['generated_count']
            total_added += result['added_count']
            total_duplicates += result['duplicate_count']
            total_quality_issues += result['quality_issues_count']
        
        execution_time = time.time() - start_time
        
        self._log_maintenance('incremental', subjects, total_generated, 
                             total_added, total_duplicates, total_quality_issues,
                             execution_time, details)
        
        return MaintenanceResult(
            success=True,
            message=f"增量维护完成，新增 {total_added} 道题目",
            total_generated=total_generated,
            total_added=total_added,
            total_duplicates=total_duplicates,
            total_quality_issues=total_quality_issues,
            processed_categories=len(subjects),
            execution_time=execution_time,
            details=details
        )

    def run_quality_check(self) -> MaintenanceResult:
        """执行质量检查"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT question_id, content, options, correct_answer, explanation, quality_score FROM ai_maintenance_questions WHERE is_valid = 1')
        rows = cursor.fetchall()
        
        issues_found = 0
        fixed_count = 0
        
        for row in rows:
            question_id, content, options, correct_answer, explanation, quality_score = row
            
            issues = []
            
            if len(content) < 5:
                issues.append('内容太短')
            if not correct_answer:
                issues.append('缺少正确答案')
            if len(explanation) < 10:
                issues.append('解析不够详细')
            
            if issues:
                issues_found += 1
                
                if quality_score < 40:
                    cursor.execute('UPDATE ai_maintenance_questions SET is_valid = 0 WHERE question_id = ?', (question_id,))
                    fixed_count += 1
        
        conn.commit()
        conn.close()
        
        execution_time = time.time() - start_time
        
        self._log_maintenance('quality_check', ['all'], 0, 0, 0, issues_found,
                             execution_time, {'issues_found': issues_found, 'fixed_count': fixed_count})
        
        return MaintenanceResult(
            success=True,
            message=f"质量检查完成，发现 {issues_found} 个问题，修复 {fixed_count} 个",
            total_quality_issues=issues_found,
            execution_time=execution_time,
            details={'issues_found': issues_found, 'fixed_count': fixed_count}
        )

    def run_duplicate_removal(self) -> MaintenanceResult:
        """执行去重"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT content FROM ai_maintenance_questions WHERE is_valid = 1')
        rows = cursor.fetchall()
        
        seen_hashes = {}
        duplicates = []
        
        for row in rows:
            content = row[0]
            content_hash = self._calculate_content_hash(content)
            
            if content_hash in seen_hashes:
                duplicates.append(seen_hashes[content_hash])
            else:
                seen_hashes[content_hash] = content
        
        removed_count = len(duplicates)
        
        if duplicates:
            cursor.execute('DELETE FROM ai_maintenance_questions WHERE content IN ({})'.format(
                ','.join('?' * len(duplicates))
            ), duplicates)
            conn.commit()
        
        conn.close()
        
        execution_time = time.time() - start_time
        
        self._log_maintenance('duplicate_removal', ['all'], 0, 0, removed_count, 0,
                             execution_time, {'removed_count': removed_count})
        
        return MaintenanceResult(
            success=True,
            message=f"去重完成，移除 {removed_count} 道重复题目",
            total_duplicates=removed_count,
            execution_time=execution_time,
            details={'removed_count': removed_count}
        )

    def run_full_maintenance(self, subjects: List[str] = None) -> MaintenanceResult:
        """执行全面维护"""
        start_time = time.time()
        
        results = {}
        
        results['incremental'] = self.run_incremental_maintenance(subjects, 15)
        results['quality_check'] = self.run_quality_check()
        results['duplicate_removal'] = self.run_duplicate_removal()
        
        execution_time = time.time() - start_time
        
        total_added = results['incremental'].total_added
        total_duplicates = results['incremental'].total_duplicates + results['duplicate_removal'].total_duplicates
        total_quality_issues = results['incremental'].total_quality_issues + results['quality_check'].total_quality_issues
        
        return MaintenanceResult(
            success=True,
            message=f"全面维护完成，新增 {total_added} 道题目",
            total_added=total_added,
            total_duplicates=total_duplicates,
            total_quality_issues=total_quality_issues,
            execution_time=execution_time,
            details=results
        )

    def _log_maintenance(self, operation: str, subjects: List[str], generated: int,
                        added: int, duplicates: int, quality_issues: int,
                        execution_time: float, details: Dict):
        """记录维护日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''INSERT INTO question_maintenance_logs
                (log_id, operation, subject, generated_count, added_count,
                 duplicate_count, quality_issues_count, status, started_at,
                 completed_at, execution_time, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (str(uuid.uuid4())[:16], operation, ','.join(subjects),
                 generated, added, duplicates, quality_issues, 'completed',
                 time.time() - execution_time, time.time(), execution_time,
                 json.dumps(details)))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录维护日志失败: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM ai_maintenance_questions WHERE is_valid = 1')
        total_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT subject, COUNT(*) FROM ai_maintenance_questions WHERE is_valid = 1 GROUP BY subject')
        by_subject = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('SELECT type, COUNT(*) FROM ai_maintenance_questions WHERE is_valid = 1 GROUP BY type')
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('SELECT difficulty, COUNT(*) FROM ai_maintenance_questions WHERE is_valid = 1 GROUP BY difficulty')
        by_difficulty = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('SELECT AVG(quality_score) FROM ai_maintenance_questions WHERE is_valid = 1')
        avg_quality = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM question_maintenance_logs')
        maintenance_logs_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_questions': total_count,
            'by_subject': by_subject,
            'by_type': by_type,
            'by_difficulty': by_difficulty,
            'avg_quality_score': round(avg_quality, 2),
            'maintenance_logs': maintenance_logs_count
        }

    def search_questions(self, subject: str = None, question_type: str = None,
                        difficulty: str = None, keyword: str = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """搜索题目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ai_maintenance_questions WHERE is_valid = 1'
        params = []
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        if question_type:
            query += ' AND type = ?'
            params.append(question_type)
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        if keyword:
            query += ' AND (content LIKE ? OR explanation LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            question = dict(zip(columns, row))
            if question.get('options'):
                question['options'] = json.loads(question['options'])
            if question.get('knowledge_points'):
                question['knowledge_points'] = json.loads(question['knowledge_points'])
            if question.get('tags'):
                question['tags'] = json.loads(question['tags'])
            results.append(question)
        
        conn.close()
        return results

    def get_maintenance_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取维护日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM question_maintenance_logs ORDER BY completed_at DESC LIMIT ?', (limit,))
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            log = dict(zip(columns, row))
            if log.get('details'):
                log['details'] = json.loads(log['details'])
            results.append(log)
        
        conn.close()
        return results

    def integrate_with_bank_service(self, question: GeneratedQuestion) -> bool:
        """将生成的题目集成到现有题库服务"""
        try:
            for tag_name in question.tags:
                tag = question_bank_service.create_tag(tag_name)
                if tag:
                    question_bank_service.add_tag_to_question(question.question_id, tag['tag_id'])
            
            categories = question_bank_service.get_categories()
            for cat in categories:
                if cat['name'] == question.subject or cat['name'] == question.category:
                    bank = question_bank_service.create_bank(
                        name=f"{question.subject}-{question.category}-题库",
                        description=f"AI自动生成的{question.subject}-{question.category}题库",
                        category_id=cat['category_id']
                    )
                    if bank:
                        question_bank_service.add_question_to_bank(bank['bank_id'], question.question_id)
                    break
            
            logger.info(f"题目 {question.question_id} 已集成到题库服务")
            return True
        except Exception as e:
            logger.error(f"集成题库服务失败: {e}")
            return False

    def generate_listening_questions(self, count: int = 10, language: str = 'english') -> List[Dict]:
        """通过AI助手生成听力题"""
        try:
            lang_enum = ListeningLanguage.ENGLISH if language == 'english' else ListeningLanguage.JAPANESE
            
            accents = ['us', 'uk'] if language == 'english' else ['kanto', 'kansai']
            accent_enum = ListeningAccent(random.choice(accents))
            
            voices = ['female', 'male']
            voice_enum = ListeningVoice(random.choice(voices))
            
            difficulties = [1, 2, 3]
            difficulty_enum = ListeningDifficulty(random.choice(difficulties))
            
            topics = ['daily', 'business', 'campus']
            topic_enum = ListeningTopic(random.choice(topics))
            
            questions = question_bank_ai_assistant.generate_listening_question(
                language=lang_enum,
                accent=accent_enum,
                voice=voice_enum,
                difficulty=difficulty_enum,
                topic=topic_enum,
                count=count
            )
            
            results = []
            for q in questions:
                question_dict = q.to_dict()
                question_dict['quality_analysis'] = question_bank_ai_assistant.analyze_question_quality(q.question_id)
                results.append(question_dict)
            
            logger.info(f"通过AI助手生成了 {len(results)} 道{language}听力题")
            return results
        except Exception as e:
            logger.error(f"生成听力题失败: {e}")
            return []

    def generate_mass_listening_questions(self, count: int = 50) -> int:
        """批量生成海量听力题"""
        try:
            generated = question_bank_ai_assistant.generate_mass_listening_questions(
                count=count,
                languages=['japanese', 'english'],
                accents=['kanto', 'us'],
                voices=['female', 'male'],
                difficulties=[1, 2, 3],
                topics=['daily', 'business', 'campus']
            )
            logger.info(f"批量生成了 {generated} 道听力题")
            return generated
        except Exception as e:
            logger.error(f"批量生成听力题失败: {e}")
            return 0

    def get_integrated_statistics(self) -> Dict[str, Any]:
        """获取集成统计信息"""
        stats = self.get_statistics()
        
        ai_stats = question_bank_ai_assistant.get_statistics()
        stats['listening_questions'] = ai_stats.listening_questions
        stats['by_language'] = ai_stats.by_language
        stats['by_accent'] = ai_stats.by_accent
        
        bank_stats = {
            'categories': len(question_bank_service.get_categories()),
            'tags': len(question_bank_service.get_tags()),
            'banks': len(question_bank_service.get_banks())
        }
        stats['bank_service'] = bank_stats
        
        return stats

    def run_complete_maintenance(self) -> MaintenanceResult:
        """执行完整维护（包含听力题）"""
        start_time = time.time()
        
        results = {}
        
        results['incremental'] = self.run_incremental_maintenance(count_per_subject=15)
        results['listening'] = {
            'generated': self.generate_mass_listening_questions(50)
        }
        results['quality_check'] = self.run_quality_check()
        results['duplicate_removal'] = self.run_duplicate_removal()
        
        execution_time = time.time() - start_time
        
        total_added = results['incremental'].total_added + results['listening']['generated']
        total_duplicates = results['incremental'].total_duplicates + results['duplicate_removal'].total_duplicates
        total_quality_issues = results['incremental'].total_quality_issues + results['quality_check'].total_quality_issues
        
        self._log_maintenance('complete_maintenance', ['all'], 
                             results['incremental'].total_generated + results['listening']['generated'],
                             total_added, total_duplicates, total_quality_issues,
                             execution_time, results)
        
        return MaintenanceResult(
            success=True,
            message=f"完整维护完成，新增 {total_added} 道题目（含听力题）",
            total_added=total_added,
            total_duplicates=total_duplicates,
            total_quality_issues=total_quality_issues,
            execution_time=execution_time,
            details=results
        )


ai_question_maintenance = AIQuestionMaintenance()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AI题库自动维护系统')
    parser.add_argument('--generate', action='store_true', help='生成题目')
    parser.add_argument('--maintain', action='store_true', help='执行增量维护')
    parser.add_argument('--full', action='store_true', help='执行全面维护')
    parser.add_argument('--complete', action='store_true', help='执行完整维护（含听力题）')
    parser.add_argument('--quality', action='store_true', help='执行质量检查')
    parser.add_argument('--dedup', action='store_true', help='执行去重')
    parser.add_argument('--stats', action='store_true', help='获取统计信息')
    parser.add_argument('--integrated-stats', action='store_true', help='获取集成统计信息')
    parser.add_argument('--search', action='store_true', help='搜索题目')
    parser.add_argument('--listening', action='store_true', help='生成听力题')
    parser.add_argument('--mass-listening', action='store_true', help='批量生成听力题')
    parser.add_argument('--subject', default='mathematics', help='学科')
    parser.add_argument('--language', default='english', help='听力题语言(english/japanese)')
    parser.add_argument('--count', type=int, default=10, help='生成数量')
    
    args = parser.parse_args()
    
    if args.generate:
        questions = ai_question_maintenance.generate_questions(args.subject, args.count)
        print(f"生成了 {len(questions)} 道{args.subject}题目")
        for q in questions[:5]:
            print(f"  ID: {q.question_id[:16]}...")
            print(f"  题目: {q.content}")
            print(f"  难度: {q.difficulty}, 质量分: {q.quality_score}")
            print()
    
    elif args.maintain:
        result = ai_question_maintenance.run_incremental_maintenance([args.subject], args.count)
        print(f"维护结果: {'成功' if result.success else '失败'}")
        print(f"消息: {result.message}")
        print(f"生成: {result.total_generated}, 添加: {result.total_added}, 重复: {result.total_duplicates}")
    
    elif args.full:
        result = ai_question_maintenance.run_full_maintenance()
        print(f"全面维护结果: {'成功' if result.success else '失败'}")
        print(f"消息: {result.message}")
        print(f"添加: {result.total_added}, 重复: {result.total_duplicates}")
    
    elif args.complete:
        result = ai_question_maintenance.run_complete_maintenance()
        print(f"完整维护结果: {'成功' if result.success else '失败'}")
        print(f"消息: {result.message}")
        print(f"添加: {result.total_added}, 重复: {result.total_duplicates}")
    
    elif args.quality:
        result = ai_question_maintenance.run_quality_check()
        print(f"质量检查结果: {'成功' if result.success else '失败'}")
        print(f"消息: {result.message}")
    
    elif args.dedup:
        result = ai_question_maintenance.run_duplicate_removal()
        print(f"去重结果: {'成功' if result.success else '失败'}")
        print(f"消息: {result.message}")
    
    elif args.stats:
        stats = ai_question_maintenance.get_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif args.integrated_stats:
        stats = ai_question_maintenance.get_integrated_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif args.search:
        questions = ai_question_maintenance.search_questions(args.subject, limit=5)
        print(f"找到 {len(questions)} 道题目")
        for q in questions:
            print(f"  {q['question_id']}: {q['content'][:50]}...")
    
    elif args.listening:
        questions = ai_question_maintenance.generate_listening_questions(args.count, args.language)
        print(f"生成了 {len(questions)} 道{args.language}听力题")
        for q in questions[:3]:
            print(f"  ID: {q['question_id'][:16]}...")
            print(f"  问题: {q['question_text']}")
            print(f"  答案: {q['correct_answer']}")
            print()
    
    elif args.mass_listening:
        count = ai_question_maintenance.generate_mass_listening_questions(args.count)
        print(f"批量生成了 {count} 道听力题")
    
    else:
        parser.print_help()