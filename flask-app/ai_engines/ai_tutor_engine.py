# -*- coding: utf-8 -*-
"""
AI助教答疑引擎
提供智能答疑、知识讲解、学习辅导、对话历史等功能
基于知识库和规则引擎进行教学辅导
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_tutor_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AITutorEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class AITutorEngine:
    """AI助教答疑引擎 - 智能答疑和学习辅导"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._qa_templates = self._init_qa_templates()
        self._concept_explanations = self._init_concept_explanations()
        self._init_database()
        self._initialized = True
        logger.info("AITutorEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tutor_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        subject TEXT,
                        topic TEXT,
                        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        satisfaction_rating INTEGER,
                        resolved INTEGER DEFAULT 0
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tutor_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text',
                        metadata TEXT DEFAULT '{}',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES tutor_sessions(session_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_explanations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        concept TEXT NOT NULL,
                        subject TEXT,
                        grade TEXT,
                        explanation TEXT NOT NULL,
                        examples TEXT DEFAULT '[]',
                        related_concepts TEXT DEFAULT '[]',
                        difficulty INTEGER DEFAULT 3,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(concept, subject, grade)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tutor_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        rating INTEGER,
                        feedback_text TEXT,
                        helpful INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS faq_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question_pattern TEXT NOT NULL,
                        subject TEXT,
                        answer TEXT NOT NULL,
                        confidence REAL DEFAULT 0.8,
                        use_count INTEGER DEFAULT 0,
                        last_used TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(question_pattern, subject)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ts_user ON tutor_sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tm_session ON tutor_messages(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tm_user ON tutor_messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_faq_pattern ON faq_cache(question_pattern)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化AI助教数据库失败: {e}")

    def _init_qa_templates(self):
        """初始化问答模板"""
        return {
            'greeting': [
                '你好！我是AI助教，有什么学习问题可以帮你解答吗？',
                '欢迎！请告诉我你想学习什么知识点？',
                '你好同学，需要我帮你解答什么问题吗？'
            ],
            'math': {
                'equation': '解方程的一般步骤：1. 移项把未知数项移到一边 2. 合并同类项 3. 系数化为1。请告诉我具体的方程，我可以帮你详细解答。',
                'geometry': '几何题解题思路：1. 仔细读题画图 2. 标记已知条件 3. 寻找全等/相似三角形 4. 应用相关定理。需要具体题目来分析。',
                'function': '函数问题分析：1. 确定定义域 2. 分析函数性质（单调性/奇偶性）3. 画函数图像辅助理解。请提供具体题目。'
            },
            'chinese': {
                'reading': '阅读理解技巧：1. 通读全文把握主旨 2. 分析段落结构 3. 关注关键词句 4. 结合上下文推断。请提供文章我可以帮你分析。',
                'writing': '作文写作要点：1. 审题立意 2. 选材构思 3. 结构安排（开头-主体-结尾）4. 语言润色。需要具体指导哪个方面？',
                'classical': '文言文学习：1. 积累常见实词虚词 2. 掌握特殊句式 3. 翻译时注意直译为主意译为辅 4. 理解文章背景。'
            },
            'english': {
                'grammar': '英语语法学习：1. 理解时态用法 2. 掌握句型结构 3. 多做练习巩固。请告诉我具体的语法点。',
                'reading': '英语阅读技巧：1. 先看题目 2. 略读找主旨 3. 扫读找细节 4. 推断词义。需要具体阅读材料。',
                'writing': '英语写作：1. 审题 2. 列提纲 3. 写主体段 4. 检查语法。建议多背诵范文。'
            }
        }

    def _init_concept_explanations(self):
        """初始化概念解释库"""
        return {
            '勾股定理': {
                'subject': '数学',
                'explanation': '勾股定理：在直角三角形中，两条直角边的平方和等于斜边的平方。即 a² + b² = c²。这是几何学中最基本的定理之一。',
                'examples': ['3²+4²=5² (3,4,5三角形)', '5²+12²=13² (5,12,13三角形)'],
                'related': ['直角三角形', '三角函数', '距离公式']
            },
            '一元二次方程': {
                'subject': '数学',
                'explanation': '一元二次方程：形如 ax²+bx+c=0 (a≠0) 的方程。求根公式：x=(-b±√(b²-4ac))/2a。判别式 Δ=b²-4ac 决定根的情况。',
                'examples': ['x²-5x+6=0 → x=2或x=3', 'x²+2x+1=0 → x=-1（重根）'],
                'related': ['韦达定理', '判别式', '配方法']
            },
            '二次函数': {
                'subject': '数学',
                'explanation': '二次函数：形如 y=ax²+bx+c (a≠0) 的函数。图像是抛物线，顶点坐标为 (-b/2a, (4ac-b²)/4a)。a>0开口向上，a<0开口向下。',
                'examples': ['y=x² 是最简二次函数', 'y=x²-2x-3 顶点为(1,-4)'],
                'related': ['抛物线', '顶点式', '配方法']
            },
            '主谓宾': {
                'subject': '语文',
                'explanation': '主谓宾是现代汉语最基本的句子结构。主语是动作的发出者，谓语是动作本身，宾语是动作的承受者。如"我吃饭"中"我"是主语，"吃"是谓语，"饭"是宾语。',
                'examples': ['小明读书（主+谓+宾）', '猫抓老鼠（主+谓+宾）'],
                'related': ['定语', '状语', '补语']
            },
            '现在完成时': {
                'subject': '英语',
                'explanation': '现在完成时(Present Perfect)：表示过去发生的动作对现在造成的影响，或过去开始的动作持续到现在。结构：have/has + 过去分词。',
                'examples': ['I have finished my homework.（我已经完成了作业）', 'She has lived here for 3 years.（她在这里住了3年）'],
                'related': ['过去分词', '现在完成进行时', '一般过去时']
            }
        }

    def start_session(self, user_id: str, subject: str = None, topic: str = None) -> Dict[str, Any]:
        """开始助教对话会话"""
        with self._lock:
            try:
                session_id = f"tutor_{user_id}_{int(time.time())}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tutor_sessions
                        (session_id, user_id, subject, topic)
                        VALUES (?, ?, ?, ?)
                    ''', (session_id, user_id, subject or 'general', topic))

                    greeting = self._generate_greeting(subject, topic)
                    cursor.execute('''
                        INSERT INTO tutor_messages
                        (session_id, user_id, role, content, message_type)
                        VALUES (?, ?, 'assistant', ?, 'greeting')
                    ''', (session_id, user_id, greeting))
                    conn.commit()

                return {
                    'success': True,
                    'session_id': session_id,
                    'user_id': user_id,
                    'subject': subject,
                    'topic': topic,
                    'greeting': greeting,
                    'message': '助教会话已开始'
                }
            except Exception as e:
                logger.error(f"开始助教会话失败: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_greeting(self, subject: str = None, topic: str = None) -> str:
        import random
        greetings = self._qa_templates['greeting']
        greeting = random.choice(greetings)
        if subject:
            greeting += f'\n\n我注意到你想学习{subject}'
            if topic:
                greeting += f'的{topic}相关内容，我会重点帮你解答这方面的问题。'
            else:
                greeting += '，请告诉我具体想了解哪个知识点？'
        return greeting

    def ask_question(self, session_id: str, user_id: str, question: str) -> Dict[str, Any]:
        """向AI助教提问"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('SELECT subject, topic FROM tutor_sessions WHERE session_id = ?',
                                   (session_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '会话不存在'}
                    subject, topic = row

                    cursor.execute('''
                        INSERT INTO tutor_messages
                        (session_id, user_id, role, content, message_type)
                        VALUES (?, ?, 'user', ?, 'question')
                    ''', (session_id, user_id, question))

                    cursor.execute('''
                        UPDATE tutor_sessions
                        SET message_count = message_count + 1,
                            last_activity = ?
                        WHERE session_id = ?
                    ''', (datetime.now().isoformat(), session_id))
                    conn.commit()

                answer_result = self._generate_answer(question, subject, user_id)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tutor_messages
                        (session_id, user_id, role, content, message_type, metadata)
                        VALUES (?, ?, 'assistant', ?, 'answer', ?)
                    ''', (session_id, user_id, answer_result['answer'],
                          json.dumps({
                              'confidence': answer_result.get('confidence', 0.5),
                              'source': answer_result.get('source', 'template'),
                              'related_concepts': answer_result.get('related_concepts', [])
                          }, ensure_ascii=False)))

                    cursor.execute('''
                        UPDATE tutor_sessions
                        SET message_count = message_count + 1
                        WHERE session_id = ?
                    ''', (session_id,))
                    conn.commit()

                return {
                    'success': True,
                    'session_id': session_id,
                    'question': question,
                    'answer': answer_result['answer'],
                    'confidence': answer_result.get('confidence', 0.5),
                    'source': answer_result.get('source', 'template'),
                    'related_concepts': answer_result.get('related_concepts', []),
                    'suggestions': answer_result.get('suggestions', [])
                }
            except Exception as e:
                logger.error(f"AI助教答疑失败: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_answer(self, question: str, subject: str = None, user_id: str = None) -> Dict[str, Any]:
        """生成回答"""
        question_lower = question.lower().strip()

        for concept, info in self._concept_explanations.items():
            if concept in question or concept.lower() in question_lower:
                return {
                    'answer': info['explanation'],
                    'confidence': 0.9,
                    'source': 'knowledge_base',
                    'related_concepts': info.get('related', []),
                    'suggestions': [
                        f'想了解更多关于「{c}」的知识吗？' for c in info.get('related', [])[:2]
                    ]
                }

        cached_answer = self._search_faq_cache(question, subject)
        if cached_answer:
            return {
                'answer': cached_answer,
                'confidence': 0.8,
                'source': 'faq_cache',
                'related_concepts': [],
                'suggestions': []
            }

        category = self._classify_question(question)
        if category:
            templates = self._qa_templates.get(subject, {}).get(category) if subject else None
            if not templates:
                for subj_templates in self._qa_templates.values():
                    if isinstance(subj_templates, dict) and category in subj_templates:
                        templates = subj_templates[category]
                        break

            if templates:
                return {
                    'answer': templates,
                    'confidence': 0.6,
                    'source': 'template',
                    'related_concepts': [],
                    'suggestions': ['请提供具体题目，我可以帮你详细解答']
                }

        return {
            'answer': f'我理解你的问题是关于「{question}」。这是一个很好的问题！建议你：\n1. 查阅相关教材和资料\n2. 结合具体例子理解\n3. 多做练习巩固\n\n如果你能提供更具体的题目或知识点，我可以给出更详细的解答。',
            'confidence': 0.4,
            'source': 'fallback',
            'related_concepts': [],
            'suggestions': ['请提供更具体的题目', '可以告诉我具体的学科和年级吗？']
        }

    def _classify_question(self, question: str) -> Optional[str]:
        """分类问题类型"""
        question_lower = question.lower()

        if any(kw in question for kw in ['方程', '解方程', '求解']):
            return 'equation'
        if any(kw in question for kw in ['几何', '三角形', '证明', '角度']):
            return 'geometry'
        if any(kw in question for kw in ['函数', '图像', '坐标']):
            return 'function'
        if any(kw in question for kw in ['阅读', '理解', '文章']):
            return 'reading'
        if any(kw in question for kw in ['作文', '写作', '写文章']):
            return 'writing'
        if any(kw in question for kw in ['文言文', '古文', '古诗']):
            return 'classical'
        if any(kw in question for kw in ['语法', '时态', '句型']):
            return 'grammar'
        return None

    def _search_faq_cache(self, question: str, subject: str = None) -> Optional[str]:
        """搜索FAQ缓存"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT answer FROM faq_cache
                    WHERE ? LIKE '%' || question_pattern || '%'
                    ORDER BY use_count DESC LIMIT 1
                ''', (question,))
                row = cursor.fetchone()
                if row:
                    cursor.execute('''
                        UPDATE faq_cache SET use_count = use_count + 1, last_used = ?
                        WHERE question_pattern = ?
                    ''', (datetime.now().isoformat(), question))
                    conn.commit()
                    return row[0]
        except Exception:
            pass
        return None

    def add_faq(self, question_pattern: str, answer: str, subject: str = None,
                confidence: float = 0.8) -> Dict[str, Any]:
        """添加FAQ"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO faq_cache
                        (question_pattern, subject, answer, confidence)
                        VALUES (?, ?, ?, ?)
                    ''', (question_pattern, subject, answer, confidence))
                    conn.commit()
                return {'success': True, 'message': 'FAQ已添加'}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def explain_concept(self, concept: str, subject: str = None) -> Dict[str, Any]:
        """解释概念"""
        try:
            concept_info = self._concept_explanations.get(concept)
            if not concept_info:
                return {
                    'success': False,
                    'message': f'暂无「{concept}」的解释，请联系管理员添加'
                }

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO knowledge_explanations
                    (concept, subject, grade, explanation, examples, related_concepts)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (concept, concept_info['subject'], None,
                      concept_info['explanation'],
                      json.dumps(concept_info.get('examples', []), ensure_ascii=False),
                      json.dumps(concept_info.get('related', []), ensure_ascii=False)))
                conn.commit()

            return {
                'success': True,
                'concept': concept,
                'subject': concept_info['subject'],
                'explanation': concept_info['explanation'],
                'examples': concept_info.get('examples', []),
                'related_concepts': concept_info.get('related', []),
                'suggestions': [f'继续学习「{c}」' for c in concept_info.get('related', [])[:3]]
            }
        except Exception as e:
            logger.error(f"概念解释失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_session_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """获取会话历史"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, user_id, subject, topic, started_at,
                           last_activity, message_count, status
                    FROM tutor_sessions WHERE session_id = ?
                ''', (session_id,))
                session = cursor.fetchone()
                if not session:
                    return {'success': False, 'message': '会话不存在'}

                cursor.execute('''
                    SELECT role, content, message_type, metadata, created_at
                    FROM tutor_messages WHERE session_id = ?
                    ORDER BY created_at ASC LIMIT ?
                ''', (session_id, limit))
                messages = [{
                    'role': r[0],
                    'content': r[1],
                    'type': r[2],
                    'metadata': json.loads(r[3]) if r[3] else {},
                    'created_at': r[4]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'session': {
                    'session_id': session[0],
                    'user_id': session[1],
                    'subject': session[2],
                    'topic': session[3],
                    'started_at': session[4],
                    'last_activity': session[5],
                    'message_count': session[6],
                    'status': session[7]
                },
                'messages': messages,
                'message_count': len(messages)
            }
        except Exception as e:
            logger.error(f"获取会话历史失败: {e}")
            return {'success': False, 'error': str(e)}

    def end_session(self, session_id: str, rating: int = None,
                    feedback: str = None) -> Dict[str, Any]:
        """结束助教会话"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    resolved = 1 if rating and rating >= 4 else 0
                    cursor.execute('''
                        UPDATE tutor_sessions
                        SET status = 'ended', satisfaction_rating = ?, resolved = ?
                        WHERE session_id = ?
                    ''', (rating, resolved, session_id))

                    if rating or feedback:
                        cursor.execute('''
                            INSERT INTO tutor_feedback
                            (session_id, user_id, rating, feedback_text, helpful)
                            SELECT ?, user_id, ?, ?, ?
                            FROM tutor_sessions WHERE session_id = ?
                        ''', (session_id, rating, feedback,
                              1 if rating and rating >= 4 else 0, session_id))
                    conn.commit()

                return {
                    'success': True,
                    'session_id': session_id,
                    'message': '会话已结束',
                    'rating': rating,
                    'resolved': bool(resolved)
                }
            except Exception as e:
                logger.error(f"结束助教会话失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_user_sessions(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """获取用户的所有助教会话"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, subject, topic, started_at, last_activity,
                           message_count, status, satisfaction_rating
                    FROM tutor_sessions WHERE user_id = ?
                    ORDER BY started_at DESC LIMIT ?
                ''', (user_id, limit))
                sessions = [{
                    'session_id': r[0],
                    'subject': r[1],
                    'topic': r[2],
                    'started_at': r[3],
                    'last_activity': r[4],
                    'message_count': r[5],
                    'status': r[6],
                    'rating': r[7]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'user_id': user_id,
                'sessions': sessions,
                'total': len(sessions)
            }
        except Exception as e:
            logger.error(f"获取用户助教会话失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取AI助教统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM tutor_sessions')
                total_sessions = cursor.fetchone()[0]
                cursor.execute('SELECT status, COUNT(*) FROM tutor_sessions GROUP BY status')
                by_status = dict(cursor.fetchall())
                cursor.execute('SELECT COUNT(*) FROM tutor_messages')
                total_messages = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(satisfaction_rating) FROM tutor_sessions WHERE satisfaction_rating IS NOT NULL')
                avg_rating = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM tutor_sessions WHERE resolved = 1')
                resolved_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM faq_cache')
                faq_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM knowledge_explanations')
                explanation_count = cursor.fetchone()[0]

            return {
                'success': True,
                'total_sessions': total_sessions,
                'by_status': by_status,
                'total_messages': total_messages,
                'average_rating': round(avg_rating, 1),
                'resolved_sessions': resolved_count,
                'resolution_rate': round(resolved_count / max(total_sessions, 1) * 100, 1),
                'faq_count': faq_count,
                'concept_explanations': explanation_count
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


ai_tutor_engine = AITutorEngine()
