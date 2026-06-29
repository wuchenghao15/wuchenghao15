#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试管理服务模块
集成数据库优化工具,实现高效的考试系统管理
"""

import json
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from app.utils.logging import logger
from app.utils.db import db_manager
from app.utils.db_index_manager import index_manager
from app.utils.fast_query_engine import fast_query
from app.utils.lock_sync_manager import lock_sync_manager, LockType, synchronized
from app.utils.db_sync_manager import db_sync_manager, ChangeType
from app.utils.config_manager import get_config, get_config_manager
from app.models.exam_system import (
    Question, QuestionType, Exam, ExamStatus, ExamPaper, ExamPaperStatus,
    ExamResult, QuestionAnalysis, UserExamProgress, ExamTemplate
)


class ExamService:
    """考试管理服务类"""

    def __init__(self):
        """初始化考试管理服务"""
        self._init_tables()
        self._init_indexes()
        self._init_exam_config()
        logger.info("考试管理服务初始化完成")
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """解析日期时间字符串，支持带Z后缀的格式和Unix时间戳"""
        try:
            if isinstance(datetime_str, int):
                return datetime.fromtimestamp(datetime_str, timezone.utc)
            
            datetime_str = str(datetime_str)
            
            if datetime_str.isdigit():
                return datetime.fromtimestamp(int(datetime_str), timezone.utc)
            
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(datetime_str)
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)
    
    def _init_exam_config(self):
        """初始化考试系统配置"""
        try:
            config_manager = get_config_manager()
            
            default_exam_configs = [
                ('EXAM_DEFAULT_DURATION', '60', 'integer', '默认考试时长(分钟)', 'exam'),
                ('EXAM_DEFAULT_QUESTION_COUNT', '20', 'integer', '默认题目数量', 'exam'),
                ('EXAM_DEFAULT_TOTAL_POINTS', '100', 'integer', '默认总分', 'exam'),
                ('EXAM_DEFAULT_PASSING_SCORE', '60', 'integer', '默认及格分数', 'exam'),
                ('EXAM_ALLOW_RETAKE', 'false', 'boolean', '允许重新考试', 'exam'),
                ('EXAM_MAX_RETAKES', '3', 'integer', '最大重考次数', 'exam'),
                ('EXAM_SHUFFLE_QUESTIONS', 'true', 'boolean', '随机打乱题目', 'exam'),
                ('EXAM_SHUFFLE_OPTIONS', 'true', 'boolean', '随机打乱选项', 'exam'),
                ('EXAM_AUTO_SUBMIT_TIMEOUT', 'true', 'boolean', '超时自动提交', 'exam'),
                ('EXAM_AUDIO_REQUIRED', 'true', 'boolean', '听力题必须有音频', 'exam'),
                ('EXAM_JAPANESE_ACCENT_DEFAULT', 'kanto', 'string', '日语默认口音', 'exam'),
                ('EXAM_ENGLISH_ACCENT_DEFAULT', 'us', 'string', '英语默认口音', 'exam'),
                ('EXAM_DEFAULT_VOICE', 'female', 'string', '默认音色', 'exam'),
                ('EXAM_STUDENT_MAX_EXAMS', '50', 'integer', '学生最大考试数', 'limits'),
                ('EXAM_QUESTION_LIMIT_PER_EXAM', '100', 'integer', '单场考试最大题目数', 'limits')
            ]
            
            for key, value, config_type, description, category in default_exam_configs:
                if config_manager.get(key) is None:
                    config_manager.set(key, value, config_type, description, category)
            
            logger.info("考试系统配置初始化完成")
        except Exception as e:
            logger.warning(f"初始化考试配置失败: {str(e)}")

    def _init_tables(self):
        """初始化数据库表"""
        try:
            # 创建考试表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    language TEXT NOT NULL DEFAULT 'zh',
                    level TEXT NOT NULL DEFAULT 'intermediate',
                    duration INTEGER NOT NULL DEFAULT 60,
                    question_count INTEGER NOT NULL DEFAULT 20,
                    total_points REAL NOT NULL DEFAULT 100.0,
                    passing_score REAL NOT NULL DEFAULT 60.0,
                    status TEXT NOT NULL DEFAULT 'draft',
                    shuffle_questions INTEGER NOT NULL DEFAULT 1,
                    shuffle_options INTEGER NOT NULL DEFAULT 1,
                    allow_retake INTEGER NOT NULL DEFAULT 0,
                    max_retakes INTEGER NOT NULL DEFAULT 3,
                    time_between_retakes INTEGER NOT NULL DEFAULT 0,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 创建题目表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    exam_id TEXT,
                    type TEXT NOT NULL DEFAULT 'single_choice',
                    content TEXT NOT NULL,
                    options TEXT NOT NULL DEFAULT '[]',
                    correct_answer TEXT NOT NULL DEFAULT '',
                    difficulty INTEGER NOT NULL DEFAULT 1,
                    points REAL NOT NULL DEFAULT 1.0,
                    audio_url TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    explanation TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """)

            # 创建试卷表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_papers (
                    id TEXT PRIMARY KEY,
                    exam_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    questions TEXT NOT NULL DEFAULT '[]',
                    scores TEXT NOT NULL DEFAULT '{}',
                    answers TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'not_started',
                    start_time TEXT,
                    end_time TEXT,
                    submitted_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """)

            # 创建考试结果表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_results (
                    id TEXT PRIMARY KEY,
                    exam_paper_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    total_score REAL NOT NULL DEFAULT 0.0,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    total_count INTEGER NOT NULL DEFAULT 0,
                    accuracy REAL NOT NULL DEFAULT 0.0,
                    time_taken INTEGER NOT NULL DEFAULT 0,
                    passed INTEGER NOT NULL DEFAULT 0,
                    analysis TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (exam_paper_id) REFERENCES exam_papers(id)
                )
            """)

            # 创建题目分析表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS question_analysis (
                    id TEXT PRIMARY KEY,
                    question_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    is_correct INTEGER NOT NULL DEFAULT 0,
                    time_spent INTEGER NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 1,
                    selected_answer TEXT,
                    correct_answer TEXT,
                    difficulty INTEGER NOT NULL DEFAULT 1,
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
            """)

            # 创建用户考试进度表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS user_exam_progress (
                    user_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    current_question INTEGER NOT NULL DEFAULT 0,
                    answers TEXT NOT NULL DEFAULT '{}',
                    time_spent INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, exam_id)
                )
            """)

            # 创建考试模板表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    language TEXT NOT NULL DEFAULT 'zh',
                    level TEXT NOT NULL DEFAULT 'intermediate',
                    duration INTEGER NOT NULL DEFAULT 60,
                    question_count INTEGER NOT NULL DEFAULT 20,
                    question_types TEXT NOT NULL DEFAULT '[]',
                    difficulty_distribution TEXT NOT NULL DEFAULT '{}',
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            logger.info("考试系统表结构创建完成")
        except Exception as e:
            logger.error(f"创建考试系统表结构失败: {str(e)}")

    def _init_indexes(self):
        """初始化索引"""
        try:
            # 为考试表创建索引
            index_manager.create_index('exams', ['status'])
            index_manager.create_index('exams', ['created_by'])
            index_manager.create_index('exams', ['language', 'level'])

            # 为题目表创建索引
            index_manager.create_index('questions', ['exam_id'])
            index_manager.create_index('questions', ['type'])
            index_manager.create_index('questions', ['difficulty'])
            index_manager.create_index('questions', ['tags'])

            # 为试卷表创建索引
            index_manager.create_index('exam_papers', ['exam_id'])
            index_manager.create_index('exam_papers', ['user_id'])
            index_manager.create_index('exam_papers', ['status'])

            # 为考试结果表创建索引
            index_manager.create_index('exam_results', ['exam_id'])
            index_manager.create_index('exam_results', ['user_id'])

            # 为题目分析表创建索引
            index_manager.create_index('question_analysis', ['question_id'])
            index_manager.create_index('question_analysis', ['user_id'])
            index_manager.create_index('question_analysis', ['exam_id'])

            # 为用户考试进度表创建索引
            index_manager.create_index('user_exam_progress', ['user_id'])
            index_manager.create_index('user_exam_progress', ['exam_id'])

            logger.info("考试系统索引创建完成")
        except Exception as e:
            logger.warning(f"创建索引失败: {str(e)}")

    @synchronized(resource='exam_create', lock_type=LockType.WRITE)
    def create_exam(self, exam_data: Dict) -> Optional[str]:
        """创建考试"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            exam = Exam(
                id=str(uuid4()),
                title=exam_data.get('title', ''),
                description=exam_data.get('description', ''),
                language=exam_data.get('language', 'zh'),
                level=exam_data.get('level', 'intermediate'),
                duration=exam_data.get('duration', 60),
                question_count=exam_data.get('question_count', 20),
                total_points=exam_data.get('total_points', 100.0),
                passing_score=exam_data.get('passing_score', 60.0),
                status=ExamStatus(exam_data.get('status', 'draft')),
                shuffle_questions=exam_data.get('shuffle_questions', True),
                shuffle_options=exam_data.get('shuffle_options', True),
                allow_retake=exam_data.get('allow_retake', False),
                max_retakes=exam_data.get('max_retakes', 3),
                time_between_retakes=exam_data.get('time_between_retakes', 0),
                created_by=exam_data.get('created_by'),
                created_at=self._parse_datetime(now),
                updated_at=self._parse_datetime(now)
            )

            exam_type = exam_data.get('exam_type', 'simulation')
            
            query = """INSERT INTO exams 
                      (id, title, description, language, level, duration, question_count,
                       total_points, passing_score, status, shuffle_questions, shuffle_options,
                       allow_retake, max_retakes, time_between_retakes, created_by, created_at, updated_at, exam_type)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                exam.id, exam.title, exam.description, exam.language, exam.level,
                exam.duration, exam.question_count, exam.total_points, exam.passing_score,
                exam.status.value, 1 if exam.shuffle_questions else 0,
                1 if exam.shuffle_options else 0, 1 if exam.allow_retake else 0,
                exam.max_retakes, exam.time_between_retakes, exam.created_by,
                exam.created_at.isoformat(), exam.updated_at.isoformat(),
                exam_type
            ))

            db_sync_manager.track_change('exams', exam.id, ChangeType.INSERT, new_data=exam.to_dict())
            logger.info(f"创建考试成功: {exam.id}")
            return exam.id
        except Exception as e:
            logger.error(f"创建考试失败: {str(e)}")
            return None

    def get_exam(self, exam_id: str) -> Optional[Exam]:
        """获取考试"""
        try:
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')
            db_path = os.path.abspath(db_path)
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
                result = cursor.fetchone()
            
            if not result:
                return None

            if isinstance(result, dict):
                return Exam(
                    id=result['id'],
                    title=result['title'],
                    description=result.get('description', ''),
                    language=result.get('language', 'zh'),
                    level=result.get('level', 'intermediate'),
                    duration=result.get('duration', 60),
                    question_count=result.get('question_count', 20),
                    total_points=result.get('total_points', 100.0),
                    passing_score=result.get('passing_score', 60.0),
                    status=ExamStatus(result.get('status', 'draft')),
                    shuffle_questions=bool(result.get('shuffle_questions', 1)),
                    shuffle_options=bool(result.get('shuffle_options', 1)),
                    allow_retake=bool(result.get('allow_retake', 0)),
                    max_retakes=result.get('max_retakes', 3),
                    time_between_retakes=result.get('time_between_retakes', 0),
                    created_by=result.get('created_by'),
                    created_at=self._parse_datetime(result['created_at']),
                    updated_at=self._parse_datetime(result['updated_at'])
                )
            else:
                return Exam(
                    id=result[0],
                    title=result[1],
                    description=result[2] if result[2] else '',
                    language=result[3] if result[3] else 'zh',
                    level=result[4] if result[4] else 'intermediate',
                    duration=result[5] if result[5] else 60,
                    question_count=result[6] if result[6] else 20,
                    total_points=result[7] if result[7] else 100.0,
                    passing_score=result[8] if result[8] else 60.0,
                    status=ExamStatus(result[9] if result[9] else 'draft'),
                    shuffle_questions=bool(result[10] if result[10] else 1),
                    shuffle_options=bool(result[11] if result[11] else 1),
                    allow_retake=bool(result[12] if result[12] else 0),
                    max_retakes=result[13] if result[13] else 3,
                    time_between_retakes=result[14] if result[14] else 0,
                    created_by=result[15],
                    created_at=self._parse_datetime(result[16]),
                    updated_at=self._parse_datetime(result[17])
                )
        except Exception as e:
            logger.error(f"获取考试失败: {str(e)}")
            return None

    def get_exam_list(self) -> List[Dict]:
        """获取考试列表"""
        try:
            query = "SELECT * FROM exams ORDER BY created_at DESC"
            results = db_manager.fetch_all(query)
            exams = []
            for result in results:
                if isinstance(result, dict):
                    exam_type = result.get('exam_type', 'simulation')
                    exams.append({
                        'id': result['id'],
                        'title': result['title'],
                        'description': result.get('description', ''),
                        'language': result.get('language', 'zh'),
                        'level': result.get('level', 'intermediate'),
                        'duration': result.get('duration', 60),
                        'question_count': result.get('question_count', 20),
                        'total_points': result.get('total_points', 100.0),
                        'passing_score': result.get('passing_score', 60.0),
                        'status': result.get('status', 'draft'),
                        'exam_type': exam_type,
                        'exam_type_label': '历年真题' if exam_type == 'real' else '拟真试题',
                        'created_by': result.get('created_by'),
                        'created_at': result.get('created_at'),
                        'updated_at': result.get('updated_at')
                    })
                else:
                    exam_type = result[18] if len(result) > 18 else 'simulation'
                    exams.append({
                        'id': result[0],
                        'title': result[1],
                        'description': result[2] if result[2] else '',
                        'language': result[3] if result[3] else 'zh',
                        'level': result[4] if result[4] else 'intermediate',
                        'duration': result[5] if result[5] else 60,
                        'question_count': result[6] if result[6] else 20,
                        'total_points': result[7] if result[7] else 100.0,
                        'passing_score': result[8] if result[8] else 60.0,
                        'status': result[9] if result[9] else 'draft',
                        'exam_type': exam_type,
                        'exam_type_label': '历年真题' if exam_type == 'real' else '拟真试题',
                        'created_by': result[15],
                        'created_at': result[16],
                        'updated_at': result[17]
                    })
            return exams
        except Exception as e:
            logger.error(f"获取考试列表失败: {str(e)}")
            return []

    def get_status(self) -> Dict:
        """获取服务状态"""
        try:
            query = "SELECT COUNT(*) FROM exams"
            exam_count = db_manager.fetch_one(query)
            exam_count = exam_count[0] if isinstance(exam_count, (tuple, list)) else 0
            
            query = "SELECT COUNT(*) FROM questions"
            question_count = db_manager.fetch_one(query)
            question_count = question_count[0] if isinstance(question_count, (tuple, list)) else 0
            
            return {
                'status': 'healthy',
                'exams_count': exam_count,
                'questions_count': question_count
            }
        except Exception as e:
            logger.error(f"获取服务状态失败: {str(e)}")
            return {
                'status': 'error',
                'exams_count': 0,
                'questions_count': 0
            }

    def get_questions(self, exam_id: Optional[str] = None) -> List[Dict]:
        """获取题目列表"""
        try:
            if exam_id:
                query = "SELECT * FROM questions WHERE exam_id = ? ORDER BY id"
                results = db_manager.fetch_all(query, (exam_id,))
                logger.info(f"[get_questions] exam_id={exam_id}, 查询到 {len(results)} 条题目")
            else:
                query = "SELECT * FROM questions ORDER BY id LIMIT 50"
                results = db_manager.fetch_all(query)
            
            questions = []
            for result in results:
                if isinstance(result, dict):
                    questions.append({
                        'id': result['id'],
                        'exam_id': result.get('exam_id'),
                        'type': result.get('type', 'single_choice'),
                        'content': result.get('content', ''),
                        'options': json.loads(result.get('options', '[]')),
                        'correct_answer': result.get('correct_answer', ''),
                        'difficulty': result.get('difficulty', 1),
                        'points': result.get('points', 1.0),
                        'audio_url': result.get('audio_url'),
                        'tags': json.loads(result.get('tags', '[]')),
                        'explanation': result.get('explanation', ''),
                        'created_at': result.get('created_at'),
                        'updated_at': result.get('updated_at')
                    })
                else:
                    questions.append({
                        'id': result[0],
                        'exam_id': result[1],
                        'type': result[2] if result[2] else 'single_choice',
                        'content': result[3] if result[3] else '',
                        'options': json.loads(result[4] if result[4] else '[]'),
                        'correct_answer': result[5] if result[5] else '',
                        'difficulty': result[6] if result[6] else 1,
                        'points': result[7] if result[7] else 1.0,
                        'audio_url': result[8],
                        'tags': json.loads(result[9] if result[9] else '[]'),
                        'explanation': result[10] if result[10] else '',
                        'created_at': result[11],
                        'updated_at': result[12]
                    })
            
            if exam_id and len(questions) == 0:
                logger.info(f"[get_questions] 考试 {exam_id} 数据库中没有题目，触发AI自动生成...")
                questions = self._auto_generate_questions(exam_id)
                logger.info(f"[get_questions] AI自动生成完成，生成了 {len(questions)} 道题目")
            elif exam_id:
                logger.info(f"[get_questions] 考试 {exam_id} 数据库中有 {len(questions)} 道题目，跳过AI自动生成")
            
            logger.info(f"[get_questions] 返回 {len(questions)} 道题目")
            return questions
        except Exception as e:
            logger.error(f"[get_questions] 获取题目列表失败: {str(e)}")
            if exam_id:
                return self._auto_generate_questions(exam_id)
            return []
    
    def _auto_generate_questions(self, exam_id: str) -> List[Dict]:
        """自动生成题目"""
        try:
            from app.services.ai_question_filter_service import get_ai_question_filter_service
            
            logger.info(f"[_auto_generate_questions] 开始为考试 {exam_id} 生成题目...")
            
            exam = self.get_exam(exam_id)
            logger.info(f"[_auto_generate_questions] get_exam 返回: {exam}")
            
            if not exam:
                logger.error(f"找不到考试: {exam_id}")
                return []
            
            exam_data = exam.to_dict() if hasattr(exam, 'to_dict') else {}
            logger.info(f"[_auto_generate_questions] exam_data: {json.dumps(exam_data, ensure_ascii=False)[:200]}...")
            
            ai_filter = get_ai_question_filter_service()
            logger.info(f"[_auto_generate_questions] AI筛选服务初始化成功")
            
            questions = ai_filter.filter_and_generate_questions(exam_id, exam_data)
            logger.info(f"[_auto_generate_questions] filter_and_generate_questions 返回 {len(questions)} 道题目")
            
            ai_filter.save_questions_to_exam(exam_id, questions, db_manager)
            
            logger.info(f"为考试 {exam_id} 自动生成并保存了 {len(questions)} 道题目")
            return questions
            
        except Exception as e:
            logger.error(f"自动生成题目失败: {str(e)}")
            return self._generate_default_questions(exam_id)
    
    def _generate_default_questions(self, exam_id: str) -> List[Dict]:
        """生成默认题目"""
        questions = []
        default_content = [
            "以下哪个选项是正确的？",
            "关于本题知识点，说法正确的是？",
            "请选择最合适的答案：",
            "下列描述中，错误的是？",
            "本题考查的核心概念是？"
        ]
        
        for i in range(10):
            correct_key = random.choice(['A', 'B', 'C', 'D'])
            question = {
                'id': f"D_{exam_id[:8]}_{i+1}",
                'exam_id': exam_id,
                'type': 'single_choice',
                'content': default_content[i % len(default_content)],
                'options': [
                    {'key': 'A', 'text': '选项A：正确答案', 'is_correct': (correct_key == 'A'), 'is_distractor': (correct_key != 'A')},
                    {'key': 'B', 'text': '选项B：混淆选项1', 'is_correct': (correct_key == 'B'), 'is_distractor': (correct_key != 'B')},
                    {'key': 'C', 'text': '选项C：混淆选项2', 'is_correct': (correct_key == 'C'), 'is_distractor': (correct_key != 'C')},
                    {'key': 'D', 'text': '选项D：混淆选项3', 'is_correct': (correct_key == 'D'), 'is_distractor': (correct_key != 'D')}
                ],
                'correct_answer': correct_key,
                'difficulty': 3,
                'points': 5,
                'tags': ['default'],
                'explanation': '本题为系统默认生成的测试题目。',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            questions.append(question)
        
        return questions

    @synchronized(resource='exam_update', lock_type=LockType.WRITE)
    def update_exam(self, exam_id: str, exam_data: Dict) -> bool:
        """更新考试"""
        try:
            exam = self.get_exam(exam_id)
            if not exam:
                return False

            old_data = exam.to_dict()

            if 'title' in exam_data:
                exam.title = exam_data['title']
            if 'description' in exam_data:
                exam.description = exam_data['description']
            if 'language' in exam_data:
                exam.language = exam_data['language']
            if 'level' in exam_data:
                exam.level = exam_data['level']
            if 'duration' in exam_data:
                exam.duration = exam_data['duration']
            if 'question_count' in exam_data:
                exam.question_count = exam_data['question_count']
            if 'total_points' in exam_data:
                exam.total_points = exam_data['total_points']
            if 'passing_score' in exam_data:
                exam.passing_score = exam_data['passing_score']
            if 'status' in exam_data:
                exam.status = ExamStatus(exam_data['status'])
            if 'shuffle_questions' in exam_data:
                exam.shuffle_questions = exam_data['shuffle_questions']
            if 'shuffle_options' in exam_data:
                exam.shuffle_options = exam_data['shuffle_options']
            if 'allow_retake' in exam_data:
                exam.allow_retake = exam_data['allow_retake']
            if 'max_retakes' in exam_data:
                exam.max_retakes = exam_data['max_retakes']
            if 'time_between_retakes' in exam_data:
                exam.time_between_retakes = exam_data['time_between_retakes']

            exam.updated_at = datetime.now(timezone.utc)

            query = """UPDATE exams SET
                      title = ?, description = ?, language = ?, level = ?, duration = ?,
                      question_count = ?, total_points = ?, passing_score = ?, status = ?,
                      shuffle_questions = ?, shuffle_options = ?, allow_retake = ?,
                      max_retakes = ?, time_between_retakes = ?, updated_at = ?
                      WHERE id = ?"""

            db_manager.execute(query, (
                exam.title, exam.description, exam.language, exam.level, exam.duration,
                exam.question_count, exam.total_points, exam.passing_score, exam.status.value,
                1 if exam.shuffle_questions else 0, 1 if exam.shuffle_options else 0,
                1 if exam.allow_retake else 0, exam.max_retakes, exam.time_between_retakes,
                exam.updated_at.isoformat(), exam.id
            ))

            db_sync_manager.track_change('exams', exam.id, ChangeType.UPDATE, old_data=old_data, new_data=exam.to_dict())
            logger.info(f"更新考试成功: {exam.id}")
            return True
        except Exception as e:
            logger.error(f"更新考试失败: {str(e)}")
            return False

    @synchronized(resource='exam_delete', lock_type=LockType.WRITE)
    def delete_exam(self, exam_id: str) -> bool:
        """删除考试"""
        try:
            exam = self.get_exam(exam_id)
            if not exam:
                return False

            old_data = exam.to_dict()

            db_manager.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            db_manager.execute("DELETE FROM questions WHERE exam_id = ?", (exam_id,))
            db_manager.execute("DELETE FROM exam_papers WHERE exam_id = ?", (exam_id,))
            db_manager.execute("DELETE FROM exam_results WHERE exam_id = ?", (exam_id,))
            db_manager.execute("DELETE FROM question_analysis WHERE exam_id = ?", (exam_id,))

            db_sync_manager.track_change('exams', exam_id, ChangeType.DELETE, old_data=old_data)
            logger.info(f"删除考试成功: {exam_id}")
            return True
        except Exception as e:
            logger.error(f"删除考试失败: {str(e)}")
            return False

    def list_exams(self, filters: Optional[Dict] = None, page: int = 1, page_size: int = 20) -> Dict:
        """列出考试"""
        try:
            conditions = []
            params = []

            if filters:
                if 'status' in filters:
                    conditions.append("status = ?")
                    params.append(filters['status'])
                if 'language' in filters:
                    conditions.append("language = ?")
                    params.append(filters['language'])
                if 'level' in filters:
                    conditions.append("level = ?")
                    params.append(filters['level'])
                if 'created_by' in filters:
                    conditions.append("created_by = ?")
                    params.append(filters['created_by'])

            where_str = " AND ".join(conditions) if conditions else "1=1"

            count_query = f"SELECT COUNT(*) FROM exams WHERE {where_str}"
            total = db_manager.fetch_scalar(count_query, tuple(params)) or 0

            offset = (page - 1) * page_size
            query = f"SELECT * FROM exams WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            rows = db_manager.fetch_all(query, tuple(params))
            exams = []

            for row in rows:
                if isinstance(row, dict):
                    exams.append(Exam(
                        id=row['id'],
                        title=row['title'],
                        description=row.get('description', ''),
                        language=row.get('language', 'zh'),
                        level=row.get('level', 'intermediate'),
                        duration=row.get('duration', 60),
                        question_count=row.get('question_count', 20),
                        total_points=row.get('total_points', 100.0),
                        passing_score=row.get('passing_score', 60.0),
                        status=ExamStatus(row.get('status', 'draft')),
                        shuffle_questions=bool(row.get('shuffle_questions', 1)),
                        shuffle_options=bool(row.get('shuffle_options', 1)),
                        allow_retake=bool(row.get('allow_retake', 0)),
                        max_retakes=row.get('max_retakes', 3),
                        time_between_retakes=row.get('time_between_retakes', 0),
                        exam_type=row.get('exam_type', 'simulation'),
                        created_by=row.get('created_by'),
                        created_at=self._parse_datetime(row['created_at']),
                        updated_at=self._parse_datetime(row['updated_at'])
                    ).to_dict())
                else:
                    exams.append(Exam(
                        id=row[0],
                        title=row[1],
                        description=row[2] if row[2] else '',
                        language=row[3] if row[3] else 'zh',
                        level=row[4] if row[4] else 'intermediate',
                        duration=row[5] if row[5] else 60,
                        question_count=row[6] if row[6] else 20,
                        total_points=row[7] if row[7] else 100.0,
                        passing_score=row[8] if row[8] else 60.0,
                        status=ExamStatus(row[9] if row[9] else 'draft'),
                        shuffle_questions=bool(row[10] if row[10] else 1),
                        shuffle_options=bool(row[11] if row[11] else 1),
                        allow_retake=bool(row[12] if row[12] else 0),
                        max_retakes=row[13] if row[13] else 3,
                        time_between_retakes=row[14] if row[14] else 0,
                        exam_type=row[18] if len(row) > 18 else 'simulation',
                        created_by=row[15],
                        created_at=self._parse_datetime(row[16]),
                        updated_at=self._parse_datetime(row[17])
                    ).to_dict())

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'exams': exams
            }
        except Exception as e:
            logger.error(f"列出考试失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'exams': []}

    @synchronized(resource='question_create', lock_type=LockType.WRITE)
    def create_question(self, exam_id: str, question_data: Dict) -> Optional[str]:
        """创建题目"""
        try:
            now = datetime.now(timezone.utc)
            question = Question(
                id=str(uuid4()),
                exam_id=exam_id,
                type=QuestionType(question_data.get('type', 'single_choice')),
                content=question_data.get('content', ''),
                options=question_data.get('options', []),
                correct_answer=question_data.get('correct_answer', ''),
                difficulty=question_data.get('difficulty', 1),
                points=question_data.get('points', 1.0),
                audio_url=question_data.get('audio_url'),
                tags=question_data.get('tags', []),
                explanation=question_data.get('explanation', ''),
                created_at=now,
                updated_at=now
            )

            query = """INSERT INTO questions 
                      (id, exam_id, type, content, options, correct_answer, difficulty,
                       points, audio_url, tags, explanation, created_at, updated_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                question.id, question.exam_id, question.type.value,
                question.content, json.dumps(question.options),
                json.dumps(question.correct_answer) if isinstance(question.correct_answer, list) else question.correct_answer,
                question.difficulty, question.points, question.audio_url,
                json.dumps(question.tags), question.explanation,
                question.created_at.isoformat(), question.updated_at.isoformat()
            ))

            db_sync_manager.track_change('questions', question.id, ChangeType.INSERT, new_data=question.to_dict())
            logger.info(f"创建题目成功: {question.id}")
            return question.id
        except Exception as e:
            logger.error(f"创建题目失败: {str(e)}")
            return None

    def get_question(self, question_id: str) -> Optional[Question]:
        """获取题目"""
        try:
            query = "SELECT * FROM questions WHERE id = ?"
            result = db_manager.fetch_one(query, (question_id,))
            if not result:
                return None

            if isinstance(result, dict):
                return Question(
                    id=result['id'],
                    exam_id=result.get('exam_id'),
                    type=QuestionType(result.get('type', 'single_choice')),
                    content=result['content'],
                    options=json.loads(result.get('options', '[]')),
                    correct_answer=json.loads(result.get('correct_answer', '')) if result.get('correct_answer', '').startswith('[') else result.get('correct_answer', ''),
                    difficulty=result.get('difficulty', 1),
                    points=result.get('points', 1.0),
                    audio_url=result.get('audio_url'),
                    tags=json.loads(result.get('tags', '[]')),
                    explanation=result.get('explanation', ''),
                    created_at=self._parse_datetime(result['created_at']),
                    updated_at=self._parse_datetime(result['updated_at'])
                )
            else:
                return Question(
                    id=result[0],
                    exam_id=result[1] if result[1] else None,
                    type=QuestionType(result[2] if result[2] else 'single_choice'),
                    content=result[3],
                    options=json.loads(result[4] if result[4] else '[]'),
                    correct_answer=json.loads(result[5]) if (result[5] and result[5].startswith('[')) else (result[5] if result[5] else ''),
                    difficulty=result[6] if result[6] else 1,
                    points=result[7] if result[7] else 1.0,
                    audio_url=result[8] if result[8] else None,
                    tags=json.loads(result[9] if result[9] else '[]'),
                    explanation=result[10] if result[10] else '',
                    created_at=self._parse_datetime(result[11]),
                    updated_at=self._parse_datetime(result[12])
                )
        except Exception as e:
            logger.error(f"获取题目失败: {str(e)}")
            return None

    def list_questions(self, exam_id: Optional[str] = None, filters: Optional[Dict] = None, 
                       page: int = 1, page_size: int = 50) -> Dict:
        """列出题目"""
        try:
            conditions = []
            params = []

            if exam_id:
                conditions.append("exam_id = ?")
                params.append(exam_id)

            if filters:
                if 'type' in filters:
                    conditions.append("type = ?")
                    params.append(filters['type'])
                if 'difficulty' in filters:
                    conditions.append("difficulty = ?")
                    params.append(filters['difficulty'])

            where_str = " AND ".join(conditions) if conditions else "1=1"

            count_query = f"SELECT COUNT(*) FROM questions WHERE {where_str}"
            total = db_manager.fetch_scalar(count_query, tuple(params)) or 0

            offset = (page - 1) * page_size
            query = f"SELECT * FROM questions WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            rows = db_manager.fetch_all(query, tuple(params))
            questions = []

            for row in rows:
                if isinstance(row, dict):
                    questions.append(Question(
                        id=row['id'],
                        exam_id=row.get('exam_id'),
                        type=QuestionType(row.get('type', 'single_choice')),
                        content=row['content'],
                        options=json.loads(row.get('options', '[]')),
                        correct_answer=json.loads(row.get('correct_answer', '')) if row.get('correct_answer', '').startswith('[') else row.get('correct_answer', ''),
                        difficulty=row.get('difficulty', 1),
                        points=row.get('points', 1.0),
                        audio_url=row.get('audio_url'),
                        tags=json.loads(row.get('tags', '[]')),
                        explanation=row.get('explanation', ''),
                        created_at=self._parse_datetime(row['created_at']),
                        updated_at=self._parse_datetime(row['updated_at'])
                    ).to_dict())
                else:
                    questions.append(Question(
                        id=row[0],
                        exam_id=row[1] if row[1] else None,
                        type=QuestionType(row[2] if row[2] else 'single_choice'),
                        content=row[3],
                        options=json.loads(row[4] if row[4] else '[]'),
                        correct_answer=json.loads(row[5]) if (row[5] and row[5].startswith('[')) else (row[5] if row[5] else ''),
                        difficulty=row[6] if row[6] else 1,
                        points=row[7] if row[7] else 1.0,
                        audio_url=row[8] if row[8] else None,
                        tags=json.loads(row[9] if row[9] else '[]'),
                        explanation=row[10] if row[10] else '',
                        created_at=self._parse_datetime(row[11]),
                        updated_at=self._parse_datetime(row[12])
                    ).to_dict())

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'questions': questions
            }
        except Exception as e:
            logger.error(f"列出题目失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'questions': []}

    @synchronized(resource='exam_paper_create', lock_type=LockType.WRITE)
    def create_exam_paper(self, exam_id: str, user_id: str) -> Optional[str]:
        """创建试卷"""
        try:
            exam = self.get_exam(exam_id)
            if not exam:
                return None

            # 获取题目
            questions = self.list_questions(exam_id=exam_id)
            question_ids = [q['id'] for q in questions.get('questions', [])]

            # 如果需要打乱题目顺序
            if exam.shuffle_questions:
                random.shuffle(question_ids)

            # 限制题目数量
            if exam.question_count > 0 and len(question_ids) > exam.question_count:
                question_ids = question_ids[:exam.question_count]

            now = datetime.now(timezone.utc)
            paper = ExamPaper(
                id=str(uuid4()),
                exam_id=exam_id,
                user_id=user_id,
                questions=question_ids,
                scores={},
                answers={},
                status=ExamPaperStatus.NOT_STARTED,
                created_at=now,
                updated_at=now
            )

            query = """INSERT INTO exam_papers 
                      (id, exam_id, user_id, questions, scores, answers, status,
                       created_at, updated_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                paper.id, paper.exam_id, paper.user_id,
                json.dumps(paper.questions),
                json.dumps(paper.scores),
                json.dumps(paper.answers),
                paper.status.value,
                paper.created_at.isoformat(),
                paper.updated_at.isoformat()
            ))

            db_sync_manager.track_change('exam_papers', paper.id, ChangeType.INSERT, new_data=paper.to_dict())
            logger.info(f"创建试卷成功: {paper.id}")
            return paper.id
        except Exception as e:
            logger.error(f"创建试卷失败: {str(e)}")
            return None

    def get_exam_paper(self, paper_id: str) -> Optional[ExamPaper]:
        """获取试卷"""
        try:
            query = "SELECT * FROM exam_papers WHERE id = ?"
            result = db_manager.fetch_one(query, (paper_id,))
            if not result:
                return None

            if isinstance(result, dict):
                return ExamPaper(
                    id=result['id'],
                    exam_id=result['exam_id'],
                    user_id=result['user_id'],
                    questions=json.loads(result.get('questions', '[]')),
                    scores=json.loads(result.get('scores', '{}')),
                    answers=json.loads(result.get('answers', '{}')),
                    status=ExamPaperStatus(result.get('status', 'not_started')),
                    start_time=self._parse_datetime(result['start_time']) if result.get('start_time') else None,
                    end_time=self._parse_datetime(result['end_time']) if result.get('end_time') else None,
                    submitted_at=self._parse_datetime(result['submitted_at']) if result.get('submitted_at') else None,
                    created_at=self._parse_datetime(result['created_at']),
                    updated_at=self._parse_datetime(result['updated_at'])
                )
            else:
                return ExamPaper(
                    id=result[0],
                    exam_id=result[1],
                    user_id=result[2],
                    questions=json.loads(result[3] if result[3] else '[]'),
                    scores=json.loads(result[4] if result[4] else '{}'),
                    answers=json.loads(result[5] if result[5] else '{}'),
                    status=ExamPaperStatus(result[6] if result[6] else 'not_started'),
                    start_time=self._parse_datetime(result[7]) if result[7] else None,
                    end_time=self._parse_datetime(result[8]) if result[8] else None,
                    submitted_at=self._parse_datetime(result[9]) if result[9] else None,
                    created_at=self._parse_datetime(result[10]),
                    updated_at=self._parse_datetime(result[11])
                )
        except Exception as e:
            logger.error(f"获取试卷失败: {str(e)}")
            return None

    @synchronized(resource='exam_paper_update', lock_type=LockType.WRITE)
    def start_exam(self, paper_id: str) -> bool:
        """开始考试"""
        try:
            paper = self.get_exam_paper(paper_id)
            if not paper:
                return False

            if paper.status != ExamPaperStatus.NOT_STARTED:
                return False

            paper.status = ExamPaperStatus.IN_PROGRESS
            paper.start_time = datetime.now(timezone.utc)
            paper.updated_at = datetime.now(timezone.utc)

            query = """UPDATE exam_papers SET 
                      status = ?, start_time = ?, updated_at = ?
                      WHERE id = ?"""

            db_manager.execute(query, (
                paper.status.value,
                paper.start_time.isoformat(),
                paper.updated_at.isoformat(),
                paper.id
            ))

            db_sync_manager.track_change('exam_papers', paper.id, ChangeType.UPDATE, new_data=paper.to_dict())
            logger.info(f"开始考试: {paper_id}")
            return True
        except Exception as e:
            logger.error(f"开始考试失败: {str(e)}")
            return False

    @synchronized(resource='exam_paper_update', lock_type=LockType.WRITE)
    def save_answer(self, paper_id: str, question_id: str, answer: Any, time_spent: int = 0) -> bool:
        """保存答案"""
        try:
            paper = self.get_exam_paper(paper_id)
            if not paper:
                return False

            if paper.status != ExamPaperStatus.IN_PROGRESS:
                return False

            paper.answers[question_id] = answer
            paper.updated_at = datetime.now(timezone.utc)

            query = """UPDATE exam_papers SET 
                      answers = ?, updated_at = ?
                      WHERE id = ?"""

            db_manager.execute(query, (
                json.dumps(paper.answers),
                paper.updated_at.isoformat(),
                paper.id
            ))

            db_sync_manager.track_change('exam_papers', paper.id, ChangeType.UPDATE, new_data=paper.to_dict())
            return True
        except Exception as e:
            logger.error(f"保存答案失败: {str(e)}")
            return False

    @synchronized(resource='exam_paper_submit', lock_type=LockType.WRITE)
    def submit_exam(self, paper_id: str) -> Optional[str]:
        """提交考试"""
        try:
            paper = self.get_exam_paper(paper_id)
            if not paper:
                return None

            if paper.status != ExamPaperStatus.IN_PROGRESS:
                return None

            exam = self.get_exam(paper.exam_id)
            if not exam:
                return None

            # 计算成绩
            total_score = 0.0
            correct_count = 0
            analyses = []

            for question_id in paper.questions:
                question = self.get_question(question_id)
                if not question:
                    continue

                user_answer = paper.answers.get(question_id)
                is_correct = self._check_answer(question, user_answer)

                if is_correct:
                    total_score += question.points
                    correct_count += 1

                analyses.append({
                    'question_id': question_id,
                    'is_correct': is_correct,
                    'user_answer': user_answer,
                    'correct_answer': question.correct_answer,
                    'points': question.points,
                    'difficulty': question.difficulty,
                    'tags': question.tags
                })

            # 计算正确率
            accuracy = correct_count / len(paper.questions) if paper.questions else 0.0
            passed = total_score >= exam.passing_score

            # 计算用时
            time_taken = 0
            if paper.start_time:
                end_time = datetime.now(timezone.utc)
                time_taken = int((end_time - paper.start_time).total_seconds())

            # 更新试卷状态
            paper.status = ExamPaperStatus.COMPLETED
            paper.end_time = datetime.now(timezone.utc)
            paper.submitted_at = datetime.now(timezone.utc)
            paper.updated_at = datetime.now(timezone.utc)

            query = """UPDATE exam_papers SET 
                      status = ?, end_time = ?, submitted_at = ?, updated_at = ?
                      WHERE id = ?"""

            db_manager.execute(query, (
                paper.status.value,
                paper.end_time.isoformat(),
                paper.submitted_at.isoformat(),
                paper.updated_at.isoformat(),
                paper.id
            ))

            # 创建考试结果
            result = ExamResult(
                id=str(uuid4()),
                exam_paper_id=paper.id,
                exam_id=exam.id,
                user_id=paper.user_id,
                total_score=total_score,
                correct_count=correct_count,
                total_count=len(paper.questions),
                accuracy=accuracy,
                time_taken=time_taken,
                passed=passed,
                analysis={
                    'question_analyses': analyses,
                    'difficulty_distribution': self._get_difficulty_distribution(analyses),
                    'tag_analysis': self._get_tag_analysis(analyses)
                },
                created_at=datetime.now(timezone.utc)
            )

            query = """INSERT INTO exam_results 
                      (id, exam_paper_id, exam_id, user_id, total_score, correct_count,
                       total_count, accuracy, time_taken, passed, analysis, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                result.id, result.exam_paper_id, result.exam_id, result.user_id,
                result.total_score, result.correct_count, result.total_count,
                result.accuracy, result.time_taken, 1 if result.passed else 0,
                json.dumps(result.analysis),
                result.created_at.isoformat()
            ))

            # 记录每道题的分析
            for analysis in analyses:
                question_analysis = QuestionAnalysis(
                    id=str(uuid4()),
                    question_id=analysis['question_id'],
                    user_id=paper.user_id,
                    exam_id=exam.id,
                    is_correct=analysis['is_correct'],
                    time_spent=0,
                    attempts=1,
                    selected_answer=analysis['user_answer'],
                    correct_answer=analysis['correct_answer'],
                    difficulty=analysis['difficulty'],
                    tags=analysis['tags'],
                    created_at=datetime.now(timezone.utc)
                )

                query = """INSERT INTO question_analysis 
                          (id, question_id, user_id, exam_id, is_correct, time_spent,
                           attempts, selected_answer, correct_answer, difficulty, tags, created_at)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

                db_manager.execute(query, (
                    question_analysis.id, question_analysis.question_id,
                    question_analysis.user_id, question_analysis.exam_id,
                    1 if question_analysis.is_correct else 0,
                    question_analysis.time_spent, question_analysis.attempts,
                    json.dumps(question_analysis.selected_answer) if isinstance(question_analysis.selected_answer, list) else str(question_analysis.selected_answer),
                    json.dumps(question_analysis.correct_answer) if isinstance(question_analysis.correct_answer, list) else str(question_analysis.correct_answer),
                    question_analysis.difficulty,
                    json.dumps(question_analysis.tags),
                    question_analysis.created_at.isoformat()
                ))

            db_sync_manager.track_change('exam_results', result.id, ChangeType.INSERT, new_data=result.to_dict())
            logger.info(f"提交考试成功: {paper_id}, 得分: {total_score}")
            return result.id
        except Exception as e:
            logger.error(f"提交考试失败: {str(e)}")
            return None

    def _check_answer(self, question: Question, user_answer: Any) -> bool:
        """检查答案是否正确"""
        if user_answer is None:
            return False

        correct = question.correct_answer

        if isinstance(correct, list):
            if isinstance(user_answer, list):
                return sorted(correct) == sorted(user_answer)
            else:
                return user_answer in correct
        else:
            return str(user_answer) == str(correct)

    def _get_difficulty_distribution(self, analyses: List[Dict]) -> Dict:
        """获取难度分布"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_by_difficulty = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for analysis in analyses:
            difficulty = analysis['difficulty']
            if difficulty in distribution:
                total_by_difficulty[difficulty] += 1
                if analysis['is_correct']:
                    distribution[difficulty] += 1

        result = {}
        for diff in range(1, 6):
            if total_by_difficulty[diff] > 0:
                result[diff] = {
                    'correct': distribution[diff],
                    'total': total_by_difficulty[diff],
                    'accuracy': distribution[diff] / total_by_difficulty[diff]
                }
            else:
                result[diff] = {'correct': 0, 'total': 0, 'accuracy': 0}

        return result

    def _get_tag_analysis(self, analyses: List[Dict]) -> Dict:
        """获取标签分析"""
        tag_stats = {}

        for analysis in analyses:
            tags = analysis.get('tags', [])
            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {'correct': 0, 'total': 0}
                tag_stats[tag]['total'] += 1
                if analysis['is_correct']:
                    tag_stats[tag]['correct'] += 1

        result = {}
        for tag, stats in tag_stats.items():
            result[tag] = {
                'correct': stats['correct'],
                'total': stats['total'],
                'accuracy': stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            }

        return result

    def get_exam_result(self, result_id: str) -> Optional[ExamResult]:
        """获取考试结果"""
        try:
            query = "SELECT * FROM exam_results WHERE id = ?"
            result = db_manager.fetch_one(query, (result_id,))
            if not result:
                return None

            if isinstance(result, dict):
                return ExamResult(
                    id=result['id'],
                    exam_paper_id=result['exam_paper_id'],
                    exam_id=result['exam_id'],
                    user_id=result['user_id'],
                    total_score=result.get('total_score', 0.0),
                    correct_count=result.get('correct_count', 0),
                    total_count=result.get('total_count', 0),
                    accuracy=result.get('accuracy', 0.0),
                    time_taken=result.get('time_taken', 0),
                    passed=bool(result.get('passed', 0)),
                    analysis=json.loads(result.get('analysis', '{}')),
                    created_at=self._parse_datetime(result['created_at'])
                )
            else:
                return ExamResult(
                    id=result[0],
                    exam_paper_id=result[1],
                    exam_id=result[2],
                    user_id=result[3],
                    total_score=result[4] if result[4] else 0.0,
                    correct_count=result[5] if result[5] else 0,
                    total_count=result[6] if result[6] else 0,
                    accuracy=result[7] if result[7] else 0.0,
                    time_taken=result[8] if result[8] else 0,
                    passed=bool(result[9] if result[9] else 0),
                    analysis=json.loads(result[10] if result[10] else '{}'),
                    created_at=self._parse_datetime(result[11])
                )
        except Exception as e:
            logger.error(f"获取考试结果失败: {str(e)}")
            return None

    def get_user_exam_results(self, user_id: str, exam_id: Optional[str] = None, 
                             page: int = 1, page_size: int = 20) -> Dict:
        """获取用户考试结果"""
        try:
            conditions = ["user_id = ?"]
            params = [user_id]

            if exam_id:
                conditions.append("exam_id = ?")
                params.append(exam_id)

            where_str = " AND ".join(conditions)

            count_query = f"SELECT COUNT(*) FROM exam_results WHERE {where_str}"
            total = db_manager.fetch_scalar(count_query, tuple(params)) or 0

            offset = (page - 1) * page_size
            query = f"SELECT * FROM exam_results WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            rows = db_manager.fetch_all(query, tuple(params))
            results = []

            for row in rows:
                if isinstance(row, dict):
                    results.append(ExamResult(
                        id=row['id'],
                        exam_paper_id=row['exam_paper_id'],
                        exam_id=row['exam_id'],
                        user_id=row['user_id'],
                        total_score=row.get('total_score', 0.0),
                        correct_count=row.get('correct_count', 0),
                        total_count=row.get('total_count', 0),
                        accuracy=row.get('accuracy', 0.0),
                        time_taken=row.get('time_taken', 0),
                        passed=bool(row.get('passed', 0)),
                        analysis=json.loads(row.get('analysis', '{}')),
                        created_at=self._parse_datetime(row['created_at'])
                    ).to_dict())
                else:
                    results.append(ExamResult(
                        id=row[0],
                        exam_paper_id=row[1],
                        exam_id=row[2],
                        user_id=row[3],
                        total_score=row[4] if row[4] else 0.0,
                        correct_count=row[5] if row[5] else 0,
                        total_count=row[6] if row[6] else 0,
                        accuracy=row[7] if row[7] else 0.0,
                        time_taken=row[8] if row[8] else 0,
                        passed=bool(row[9] if row[9] else 0),
                        analysis=json.loads(row[10] if row[10] else '{}'),
                        created_at=self._parse_datetime(row[11])
                    ).to_dict())

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'results': results
            }
        except Exception as e:
            logger.error(f"获取用户考试结果失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'results': []}

    def get_exam_statistics(self, exam_id: str) -> Dict:
        """获取考试统计信息"""
        try:
            # 获取考试信息
            exam = self.get_exam(exam_id)
            if not exam:
                return {'error': '考试不存在'}

            # 获取考试结果统计
            query = """SELECT COUNT(*), AVG(total_score), AVG(accuracy), AVG(time_taken),
                          SUM(CASE WHEN passed THEN 1 ELSE 0 END)
                       FROM exam_results WHERE exam_id = ?"""
            result = db_manager.fetch_one(query, (exam_id,))

            if result:
                if isinstance(result, dict):
                    total_takers = result[0] if result[0] else 0
                    avg_score = result[1] if result[1] else 0.0
                    avg_accuracy = result[2] if result[2] else 0.0
                    avg_time = result[3] if result[3] else 0
                    pass_count = result[4] if result[4] else 0
                else:
                    total_takers = result[0] if result[0] else 0
                    avg_score = result[1] if result[1] else 0.0
                    avg_accuracy = result[2] if result[2] else 0.0
                    avg_time = result[3] if result[3] else 0
                    pass_count = result[4] if result[4] else 0
            else:
                total_takers = 0
                avg_score = 0.0
                avg_accuracy = 0.0
                avg_time = 0
                pass_count = 0

            pass_rate = pass_count / total_takers if total_takers > 0 else 0.0

            # 获取题目数量
            question_count = self.list_questions(exam_id=exam_id).get('total', 0)

            return {
                'exam_id': exam_id,
                'title': exam.title,
                'total_takers': total_takers,
                'avg_score': avg_score,
                'avg_accuracy': avg_accuracy,
                'avg_time_taken': avg_time,
                'pass_count': pass_count,
                'pass_rate': pass_rate,
                'question_count': question_count,
                'duration': exam.duration,
                'passing_score': exam.passing_score
            }
        except Exception as e:
            logger.error(f"获取考试统计失败: {str(e)}")
            return {'error': str(e)}

    def get_user_statistics(self, user_id: str) -> Dict:
        """获取用户统计信息"""
        try:
            # 获取用户考试次数
            query = """SELECT COUNT(*), AVG(total_score), AVG(accuracy), 
                          SUM(CASE WHEN passed THEN 1 ELSE 0 END)
                       FROM exam_results WHERE user_id = ?"""
            result = db_manager.fetch_one(query, (user_id,))

            if result:
                if isinstance(result, dict):
                    total_exams = result[0] if result[0] else 0
                    avg_score = result[1] if result[1] else 0.0
                    avg_accuracy = result[2] if result[2] else 0.0
                    pass_count = result[3] if result[3] else 0
                else:
                    total_exams = result[0] if result[0] else 0
                    avg_score = result[1] if result[1] else 0.0
                    avg_accuracy = result[2] if result[2] else 0.0
                    pass_count = result[3] if result[3] else 0
            else:
                total_exams = 0
                avg_score = 0.0
                avg_accuracy = 0.0
                pass_count = 0

            pass_rate = pass_count / total_exams if total_exams > 0 else 0.0

            # 获取用户的错题统计
            query = """SELECT COUNT(*) FROM question_analysis WHERE user_id = ? AND is_correct = 0"""
            wrong_count = db_manager.fetch_scalar(query, (user_id,)) or 0

            # 获取用户已完成的题目数
            query = """SELECT COUNT(*) FROM question_analysis WHERE user_id = ?"""
            total_questions = db_manager.fetch_scalar(query, (user_id,)) or 0

            # 获取薄弱知识点
            query = """SELECT tags, COUNT(*) as count 
                       FROM question_analysis 
                       WHERE user_id = ? AND is_correct = 0
                       GROUP BY tags
                       ORDER BY count DESC LIMIT 5"""
            weak_tags = db_manager.fetch_all(query, (user_id,))

            weak_topics = []
            for row in weak_tags:
                if isinstance(row, dict):
                    tags = json.loads(row.get('tags', '[]'))
                    weak_topics.extend(tags)
                else:
                    tags = json.loads(row[0] if row[0] else '[]')
                    weak_topics.extend(tags)

            return {
                'user_id': user_id,
                'total_exams': total_exams,
                'avg_score': avg_score,
                'avg_accuracy': avg_accuracy,
                'pass_count': pass_count,
                'pass_rate': pass_rate,
                'total_questions_answered': total_questions,
                'wrong_questions': wrong_count,
                'weak_topics': list(set(weak_topics))[:5]
            }
        except Exception as e:
            logger.error(f"获取用户统计失败: {str(e)}")
            return {'error': str(e)}


    def get_exams(self, status: Optional[str] = None, language: Optional[str] = None, 
                 level: Optional[str] = None) -> List[Dict]:
        """获取考试列表（带筛选条件）"""
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            if language:
                conditions.append("language = ?")
                params.append(language)
            if level:
                conditions.append("level = ?")
                params.append(level)
            
            where_str = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM exams WHERE {where_str} ORDER BY created_at DESC"
            
            results = db_manager.fetch_all(query, tuple(params))
            exams = []
            for result in results:
                if isinstance(result, dict):
                    exams.append({
                        'id': result['id'],
                        'title': result['title'],
                        'description': result.get('description', ''),
                        'language': result.get('language', 'zh'),
                        'level': result.get('level', 'intermediate'),
                        'duration': result.get('duration', 60),
                        'question_count': result.get('question_count', 20),
                        'total_points': result.get('total_points', 100.0),
                        'passing_score': result.get('passing_score', 60.0),
                        'status': result.get('status', 'draft'),
                        'shuffle_questions': bool(result.get('shuffle_questions', 1)),
                        'shuffle_options': bool(result.get('shuffle_options', 1)),
                        'allow_retake': bool(result.get('allow_retake', 0)),
                        'max_retakes': result.get('max_retakes', 3),
                        'created_by': result.get('created_by'),
                        'created_at': result.get('created_at'),
                        'updated_at': result.get('updated_at')
                    })
                else:
                    exams.append({
                        'id': result[0],
                        'title': result[1],
                        'description': result[2] if result[2] else '',
                        'language': result[3] if result[3] else 'zh',
                        'level': result[4] if result[4] else 'intermediate',
                        'duration': result[5] if result[5] else 60,
                        'question_count': result[6] if result[6] else 20,
                        'total_points': result[7] if result[7] else 100.0,
                        'passing_score': result[8] if result[8] else 60.0,
                        'status': result[9] if result[9] else 'draft',
                        'shuffle_questions': bool(result[10] if result[10] else 1),
                        'shuffle_options': bool(result[11] if result[11] else 1),
                        'allow_retake': bool(result[12] if result[12] else 0),
                        'max_retakes': result[13] if result[13] else 3,
                        'created_by': result[15],
                        'created_at': result[16],
                        'updated_at': result[17]
                    })
            return exams
        except Exception as e:
            logger.error(f"获取考试列表失败: {str(e)}")
            return []
    
    def add_question(self, exam_id: str, question_data: Dict) -> Optional[str]:
        """添加题目（兼容API调用）"""
        return self.create_question(exam_id, question_data)
    
    @synchronized(resource='question_update', lock_type=LockType.WRITE)
    def update_question(self, question_id: str, question_data: Dict) -> bool:
        """更新题目"""
        try:
            question = self.get_question(question_id)
            if not question:
                return False
            
            old_data = question.to_dict()
            
            if 'type' in question_data:
                question.type = QuestionType(question_data['type'])
            if 'content' in question_data:
                question.content = question_data['content']
            if 'options' in question_data:
                question.options = question_data['options']
            if 'correct_answer' in question_data:
                question.correct_answer = question_data['correct_answer']
            if 'difficulty' in question_data:
                question.difficulty = question_data['difficulty']
            if 'points' in question_data:
                question.points = question_data['points']
            if 'audio_url' in question_data:
                question.audio_url = question_data['audio_url']
            if 'tags' in question_data:
                question.tags = question_data['tags']
            if 'explanation' in question_data:
                question.explanation = question_data['explanation']
            
            question.updated_at = datetime.now(timezone.utc)
            
            query = """UPDATE questions SET
                      type = ?, content = ?, options = ?, correct_answer = ?, difficulty = ?,
                      points = ?, audio_url = ?, tags = ?, explanation = ?, updated_at = ?
                      WHERE id = ?"""
            
            db_manager.execute(query, (
                question.type.value, question.content, json.dumps(question.options),
                json.dumps(question.correct_answer) if isinstance(question.correct_answer, list) else question.correct_answer,
                question.difficulty, question.points, question.audio_url,
                json.dumps(question.tags), question.explanation,
                question.updated_at.isoformat(), question.id
            ))
            
            db_sync_manager.track_change('questions', question.id, ChangeType.UPDATE, old_data=old_data, new_data=question.to_dict())
            logger.info(f"更新题目成功: {question.id}")
            return True
        except Exception as e:
            logger.error(f"更新题目失败: {str(e)}")
            return False
    
    @synchronized(resource='question_delete', lock_type=LockType.WRITE)
    def delete_question(self, question_id: str) -> bool:
        """删除题目"""
        try:
            question = self.get_question(question_id)
            if not question:
                return False
            
            old_data = question.to_dict()
            
            db_manager.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            db_manager.execute("DELETE FROM question_analysis WHERE question_id = ?", (question_id,))
            
            db_sync_manager.track_change('questions', question_id, ChangeType.DELETE, old_data=old_data)
            logger.info(f"删除题目成功: {question_id}")
            return True
        except Exception as e:
            logger.error(f"删除题目失败: {str(e)}")
            return False
    
    def create_paper(self, exam_id: str, user_id: str) -> Optional[str]:
        """创建试卷（兼容API调用）"""
        return self.create_exam_paper(exam_id, user_id)
    
    def get_paper(self, paper_id: str) -> Optional[Dict]:
        """获取试卷详情（兼容API调用）"""
        paper = self.get_exam_paper(paper_id)
        if paper:
            return paper.to_dict()
        return None
    
    def submit_answer(self, paper_id: str, question_id: str, answer: Any) -> bool:
        """提交答案（兼容API调用）"""
        return self.save_answer(paper_id, question_id, answer)
    
    def submit_paper(self, paper_id: str) -> Optional[Dict]:
        """提交试卷（兼容API调用）"""
        result_id = self.submit_exam(paper_id)
        if result_id:
            result = self.get_exam_result(result_id)
            if result:
                return result.to_dict()
        return None
    
    def get_result(self, paper_id: str) -> Optional[Dict]:
        """获取考试结果（兼容API调用）"""
        query = "SELECT * FROM exam_results WHERE exam_paper_id = ?"
        result = db_manager.fetch_one(query, (paper_id,))
        if result:
            if isinstance(result, dict):
                return {
                    'id': result['id'],
                    'exam_paper_id': result['exam_paper_id'],
                    'exam_id': result['exam_id'],
                    'user_id': result['user_id'],
                    'total_score': result.get('total_score', 0.0),
                    'correct_count': result.get('correct_count', 0),
                    'total_count': result.get('total_count', 0),
                    'accuracy': result.get('accuracy', 0.0),
                    'time_taken': result.get('time_taken', 0),
                    'passed': bool(result.get('passed', 0)),
                    'analysis': json.loads(result.get('analysis', '{}')),
                    'created_at': result.get('created_at')
                }
            else:
                return {
                    'id': result[0],
                    'exam_paper_id': result[1],
                    'exam_id': result[2],
                    'user_id': result[3],
                    'total_score': result[4] if result[4] else 0.0,
                    'correct_count': result[5] if result[5] else 0,
                    'total_count': result[6] if result[6] else 0,
                    'accuracy': result[7] if result[7] else 0.0,
                    'time_taken': result[8] if result[8] else 0,
                    'passed': bool(result[9] if result[9] else 0),
                    'analysis': json.loads(result[10] if result[10] else '{}'),
                    'created_at': result[11]
                }
        return None
    
    def get_user_results(self, user_id: str) -> List[Dict]:
        """获取用户考试记录（兼容API调用）"""
        query = "SELECT * FROM exam_results WHERE user_id = ? ORDER BY created_at DESC"
        results = db_manager.fetch_all(query, (user_id,))
        user_results = []
        for result in results:
            if isinstance(result, dict):
                user_results.append({
                    'id': result['id'],
                    'exam_paper_id': result['exam_paper_id'],
                    'exam_id': result['exam_id'],
                    'user_id': result['user_id'],
                    'total_score': result.get('total_score', 0.0),
                    'correct_count': result.get('correct_count', 0),
                    'total_count': result.get('total_count', 0),
                    'accuracy': result.get('accuracy', 0.0),
                    'time_taken': result.get('time_taken', 0),
                    'passed': bool(result.get('passed', 0)),
                    'created_at': result.get('created_at')
                })
            else:
                user_results.append({
                    'id': result[0],
                    'exam_paper_id': result[1],
                    'exam_id': result[2],
                    'user_id': result[3],
                    'total_score': result[4] if result[4] else 0.0,
                    'correct_count': result[5] if result[5] else 0,
                    'total_count': result[6] if result[6] else 0,
                    'accuracy': result[7] if result[7] else 0.0,
                    'time_taken': result[8] if result[8] else 0,
                    'passed': bool(result[9] if result[9] else 0),
                    'created_at': result[11]
                })
        return user_results
    
    def get_exam_stats(self, exam_id: str) -> Dict:
        """获取考试统计（兼容API调用）"""
        return self.get_exam_statistics(exam_id)
    
    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计（兼容API调用）"""
        return self.get_user_statistics(user_id)
    
    def get_exam_config(self) -> Dict[str, Any]:
        """获取考试系统配置"""
        try:
            config_manager = get_config_manager()
            return config_manager.get_by_category('exam')
        except Exception as e:
            logger.error(f"获取考试配置失败: {str(e)}")
            return {}
    
    def get_exam_limit_config(self) -> Dict[str, Any]:
        """获取考试限制配置"""
        try:
            config_manager = get_config_manager()
            return config_manager.get_by_category('limits')
        except Exception as e:
            logger.error(f"获取考试限制配置失败: {str(e)}")
            return {}
    
    def get_default_exam_settings(self) -> Dict[str, Any]:
        """获取默认考试设置"""
        try:
            return {
                'duration': get_config('EXAM_DEFAULT_DURATION', 60),
                'question_count': get_config('EXAM_DEFAULT_QUESTION_COUNT', 20),
                'total_points': get_config('EXAM_DEFAULT_TOTAL_POINTS', 100),
                'passing_score': get_config('EXAM_DEFAULT_PASSING_SCORE', 60),
                'shuffle_questions': get_config('EXAM_SHUFFLE_QUESTIONS', True),
                'shuffle_options': get_config('EXAM_SHUFFLE_OPTIONS', True),
                'allow_retake': get_config('EXAM_ALLOW_RETAKE', False),
                'max_retakes': get_config('EXAM_MAX_RETAKES', 3)
            }
        except Exception as e:
            logger.error(f"获取默认考试设置失败: {str(e)}")
            return {
                'duration': 60,
                'question_count': 20,
                'total_points': 100,
                'passing_score': 60,
                'shuffle_questions': True,
                'shuffle_options': True,
                'allow_retake': False,
                'max_retakes': 3
            }
    
    def get_audio_settings(self) -> Dict[str, Any]:
        """获取音频设置"""
        try:
            return {
                'japanese_accent_default': get_config('EXAM_JAPANESE_ACCENT_DEFAULT', 'kanto'),
                'english_accent_default': get_config('EXAM_ENGLISH_ACCENT_DEFAULT', 'us'),
                'default_voice': get_config('EXAM_DEFAULT_VOICE', 'female'),
                'audio_required': get_config('EXAM_AUDIO_REQUIRED', True)
            }
        except Exception as e:
            logger.error(f"获取音频设置失败: {str(e)}")
            return {
                'japanese_accent_default': 'kanto',
                'english_accent_default': 'us',
                'default_voice': 'female',
                'audio_required': True
            }
    
    def update_exam_config(self, config_key: str, value: Any, config_type: str = 'string', 
                          description: str = '') -> bool:
        """更新考试配置"""
        try:
            return get_config_manager().set(config_key, value, config_type, description, 'exam')
        except Exception as e:
            logger.error(f"更新考试配置失败: {str(e)}")
            return False
    
    def get_system_wide_stats(self) -> Dict[str, Any]:
        """获取系统级考试统计"""
        try:
            stats = {}
            
            query = "SELECT COUNT(*) FROM exams"
            stats['total_exams'] = db_manager.fetch_scalar(query) or 0
            
            query = "SELECT COUNT(*) FROM questions"
            stats['total_questions'] = db_manager.fetch_scalar(query) or 0
            
            query = "SELECT COUNT(*) FROM exam_papers"
            stats['total_papers'] = db_manager.fetch_scalar(query) or 0
            
            query = "SELECT COUNT(*) FROM exam_results"
            stats['total_results'] = db_manager.fetch_scalar(query) or 0
            
            query = "SELECT AVG(total_score) FROM exam_results"
            avg_score = db_manager.fetch_scalar(query)
            stats['average_score'] = avg_score if avg_score else 0.0
            
            query = "SELECT COUNT(*) FROM exam_results WHERE passed = 1"
            passed_count = db_manager.fetch_scalar(query) or 0
            stats['pass_rate'] = passed_count / stats['total_results'] if stats['total_results'] > 0 else 0.0
            
            query = "SELECT COUNT(*) FROM exams WHERE status = 'active'"
            stats['active_exams'] = db_manager.fetch_scalar(query) or 0
            
            query = "SELECT COUNT(*) FROM questions WHERE type = 'listening'"
            stats['listening_questions'] = db_manager.fetch_scalar(query) or 0
            
            query = "SELECT language, COUNT(*) FROM exams GROUP BY language"
            lang_stats = db_manager.fetch_all(query)
            stats['language_distribution'] = {}
            for row in lang_stats:
                if isinstance(row, dict):
                    stats['language_distribution'][row['language']] = row['COUNT(*)']
                else:
                    stats['language_distribution'][row[0]] = row[1]
            
            query = "SELECT level, COUNT(*) FROM exams GROUP BY level"
            level_stats = db_manager.fetch_all(query)
            stats['level_distribution'] = {}
            for row in level_stats:
                if isinstance(row, dict):
                    stats['level_distribution'][row['level']] = row['COUNT(*)']
                else:
                    stats['level_distribution'][row[0]] = row[1]
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            query = "SELECT COUNT(*) FROM exam_results WHERE created_at LIKE ?"
            stats['today_exams'] = db_manager.fetch_scalar(query, (f"{today}%",)) or 0
            
            return stats
        except Exception as e:
            logger.error(f"获取系统统计失败: {str(e)}")
            return {'error': str(e)}
    
    def get_recent_exam_activity(self, days: int = 7) -> List[Dict]:
        """获取最近的考试活动"""
        try:
            query = """
                SELECT er.created_at, e.title, u.username, er.total_score, er.passed
                FROM exam_results er
                JOIN exams e ON er.exam_id = e.id
                JOIN users u ON er.user_id = u.id
                ORDER BY er.created_at DESC
                LIMIT 20
            """
            results = db_manager.fetch_all(query)
            
            activities = []
            for row in results:
                if isinstance(row, dict):
                    activities.append({
                        'timestamp': row['created_at'],
                        'exam_title': row['title'],
                        'username': row['username'],
                        'score': row['total_score'],
                        'passed': bool(row['passed'])
                    })
                else:
                    activities.append({
                        'timestamp': row[0],
                        'exam_title': row[1],
                        'username': row[2],
                        'score': row[3],
                        'passed': bool(row[4])
                    })
            
            return activities
        except Exception as e:
            logger.error(f"获取考试活动失败: {str(e)}")
            return []


    # ==================== 智能组卷增强方法 ====================
    
    def generate_intelligent_paper(
        self,
        total_questions: int = 20,
        total_points: float = 100.0,
        type_ratio: Optional[Dict] = None,
        difficulty_distribution: Optional[Dict] = None,
        required_knowledge_points: Optional[List[str]] = None,
        min_knowledge_coverage: float = 80.0,
        exam_id: Optional[str] = None
    ) -> Dict:
        """
        智能组卷方法
        
        根据难度分布、知识点覆盖率、题型比例自动生成试卷
        
        Args:
            total_questions: 题目总数
            total_points: 总分
            type_ratio: 题型比例配置
            difficulty_distribution: 难度分布配置
            required_knowledge_points: 必须覆盖的知识点列表
            min_knowledge_coverage: 最小知识点覆盖率
            exam_id: 考试ID（用于指定题目池）
        
        Returns:
            生成的试卷信息
        """
        try:
            from app.services.intelligent_paper_generator import (
                get_intelligent_paper_generator, PaperGenerationConfig
            )
            
            generator = get_intelligent_paper_generator(db_manager)
            
            # 默认配置
            default_type_ratio = {
                'single_choice': 0.5,
                'multiple_choice': 0.2,
                'true_false': 0.1,
                'fill_blank': 0.1,
                'short_answer': 0.1
            }
            
            default_difficulty_distribution = {
                1: 0.15, 2: 0.25, 3: 0.35, 4: 0.20, 5: 0.05
            }
            
            config = PaperGenerationConfig(
                total_questions=total_questions,
                total_points=total_points,
                type_ratio=type_ratio or default_type_ratio,
                difficulty_distribution=difficulty_distribution or default_difficulty_distribution,
                required_knowledge_points=required_knowledge_points or [],
                min_knowledge_coverage=min_knowledge_coverage,
                shuffle_questions=True,
                shuffle_options=True
            )
            
            paper = generator.generate_paper(config, exam_id)
            
            logger.info(f"智能组卷完成: {paper.get('paper_id', 'N/A')}")
            return paper
            
        except Exception as e:
            logger.error(f"智能组卷失败: {str(e)}")
            return {'error': str(e), 'questions': []}
    
    def generate_paper_from_template(self, template_id: str, exam_id: Optional[str] = None) -> Dict:
        """
        从模板生成试卷
        
        Args:
            template_id: 模板ID
            exam_id: 考试ID
        
        Returns:
            生成的试卷信息
        """
        try:
            # 获取模板数据
            query = "SELECT * FROM exam_templates WHERE id = ?"
            template = db_manager.fetch_one(query, (template_id,))
            
            if not template:
                logger.error(f"模板不存在: {template_id}")
                return {'error': '模板不存在'}
            
            # 解析模板数据
            if isinstance(template, dict):
                template_data = {
                    'question_count': template.get('question_count', 20),
                    'total_points': 100.0,
                    'type_ratio': json.loads(template.get('question_types', '{}')),
                    'difficulty_distribution': json.loads(template.get('difficulty_distribution', '{}')),
                    'shuffle_questions': True,
                    'shuffle_options': True
                }
            else:
                template_data = {
                    'question_count': template[5] if len(template) > 5 else 20,
                    'total_points': 100.0,
                    'type_ratio': json.loads(template[6]) if len(template) > 6 and template[6] else {},
                    'difficulty_distribution': json.loads(template[7]) if len(template) > 7 and template[7] else {},
                    'shuffle_questions': True,
                    'shuffle_options': True
                }
            
            from app.services.intelligent_paper_generator import get_intelligent_paper_generator
            generator = get_intelligent_paper_generator(db_manager)
            
            paper = generator.generate_paper_from_template(template_data, exam_id)
            
            logger.info(f"从模板生成试卷完成: {template_id}")
            return paper
            
        except Exception as e:
            logger.error(f"从模板生成试卷失败: {str(e)}")
            return {'error': str(e)}
    
    def validate_paper_quality(self, paper: Dict) -> Dict:
        """
        验证试卷质量
        
        Args:
            paper: 试卷数据
        
        Returns:
            验证结果
        """
        try:
            from app.services.intelligent_paper_generator import get_intelligent_paper_generator
            generator = get_intelligent_paper_generator()
            
            validation = generator.validate_paper_quality(paper)
            
            logger.info(f"试卷质量验证完成: 得分 {validation['score']}")
            return validation
            
        except Exception as e:
            logger.error(f"试卷质量验证失败: {str(e)}")
            return {'error': str(e), 'is_valid': False, 'score': 0}
    
    # ==================== 数据分析方法 ====================
    
    def analyze_exam_score_distribution(self, exam_id: str) -> Dict:
        """
        分析考试成绩分布
        
        Args:
            exam_id: 考试ID
        
        Returns:
            成绩分布数据
        """
        try:
            from app.services.exam_data_analysis_service import get_exam_data_analysis_service
            service = get_exam_data_analysis_service()
            
            distribution = service.analyze_score_distribution(exam_id)
            
            result = {
                'score_ranges': distribution.score_ranges,
                'mean': distribution.mean,
                'median': distribution.median,
                'std_dev': distribution.std_dev,
                'min_score': distribution.min_score,
                'max_score': distribution.max_score,
                'mode': distribution.mode,
                'percentile_25': distribution.percentile_25,
                'percentile_75': distribution.percentile_75
            }
            
            logger.info(f"成绩分布分析完成: 平均分 {distribution.mean:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"成绩分布分析失败: {str(e)}")
            return {'error': str(e)}
    
    def analyze_question_difficulty(self, exam_id: str) -> List[Dict]:
        """
        分析题目难度
        
        Args:
            exam_id: 考试ID
        
        Returns:
            题目难度分析列表
        """
        try:
            from app.services.exam_data_analysis_service import get_exam_data_analysis_service
            service = get_exam_data_analysis_service()
            
            analyses = service.analyze_question_difficulty(exam_id)
            
            result = [{
                'question_id': qa.question_id,
                'difficulty_level': qa.difficulty_level,
                'correct_rate': qa.correct_rate,
                'avg_time_spent': qa.avg_time_spent,
                'discrimination_index': qa.discrimination_index,
                'difficulty_index': qa.difficulty_index,
                'analysis_result': qa.analysis_result
            } for qa in analyses]
            
            logger.info(f"题目难度分析完成: 分析了 {len(result)} 道题目")
            return result
            
        except Exception as e:
            logger.error(f"题目难度分析失败: {str(e)}")
            return []
    
    def analyze_knowledge_mastery(
        self,
        exam_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """
        分析知识点掌握度
        
        Args:
            exam_id: 考试ID
            user_id: 用户ID（可选，如果不提供则分析整体）
        
        Returns:
            知识点掌握度列表
        """
        try:
            from app.services.exam_data_analysis_service import get_exam_data_analysis_service
            service = get_exam_data_analysis_service()
            
            mastery_list = service.analyze_knowledge_mastery(exam_id, user_id)
            
            result = [{
                'knowledge_point': km.knowledge_point,
                'total_questions': km.total_questions,
                'correct_count': km.correct_count,
                'mastery_rate': km.mastery_rate,
                'avg_time': km.avg_time,
                'difficulty_avg': km.difficulty_avg,
                'mastery_level': km.mastery_level
            } for km in mastery_list]
            
            logger.info(f"知识点掌握度分析完成: 分析了 {len(result)} 个知识点")
            return result
            
        except Exception as e:
            logger.error(f"知识点掌握度分析失败: {str(e)}")
            return []
    
    def generate_exam_analysis_report(self, exam_id: str) -> Dict:
        """
        生成考试分析报告
        
        Args:
            exam_id: 考试ID
        
        Returns:
            考试分析报告
        """
        try:
            from app.services.exam_data_analysis_service import get_exam_data_analysis_service
            service = get_exam_data_analysis_service()
            
            report = service.generate_exam_analysis_report(exam_id)
            
            result = {
                'exam_id': report.exam_id,
                'total_participants': report.total_participants,
                'score_distribution': {
                    'score_ranges': report.score_distribution.score_ranges,
                    'mean': report.score_distribution.mean,
                    'median': report.score_distribution.median,
                    'std_dev': report.score_distribution.std_dev
                },
                'question_analyses': [{
                    'question_id': qa.question_id,
                    'correct_rate': qa.correct_rate,
                    'analysis_result': qa.analysis_result
                } for qa in report.question_analyses],
                'knowledge_mastery': [{
                    'knowledge_point': km.knowledge_point,
                    'mastery_rate': km.mastery_rate,
                    'mastery_level': km.mastery_level
                } for km in report.knowledge_mastery],
                'overall_statistics': report.overall_statistics,
                'recommendations': report.recommendations,
                'generated_at': report.generated_at.isoformat()
            }
            
            logger.info(f"考试分析报告生成完成: {exam_id}")
            return result
            
        except Exception as e:
            logger.error(f"生成考试分析报告失败: {str(e)}")
            return {'error': str(e)}
    
    def analyze_user_performance_history(self, user_id: str, limit: int = 20) -> Dict:
        """
        分析用户考试历史
        
        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
        
        Returns:
            用户考试历史分析
        """
        try:
            from app.services.exam_data_analysis_service import get_exam_data_analysis_service
            service = get_exam_data_analysis_service()
            
            history = service.analyze_user_exam_history(user_id, limit)
            
            logger.info(f"用户考试历史分析完成: 用户 {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"用户考试历史分析失败: {str(e)}")
            return {'error': str(e)}
    
    # ==================== 防作弊检测方法 ====================
    
    def perform_cheating_detection(
        self,
        session_id: str,
        user_id: str,
        exam_id: str
    ) -> Dict:
        """
        执行作弊检测
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            exam_id: 考试ID
        
        Returns:
            作弊检测结果
        """
        try:
            from app.services.anti_cheating_service import get_anti_cheating_service
            service = get_anti_cheating_service()
            
            result = service.perform_comprehensive_detection(session_id, user_id, exam_id)
            
            detection_result = {
                'is_cheating': result.is_cheating,
                'cheating_type': result.cheating_type,
                'confidence': result.confidence,
                'risk_level': result.risk_level,
                'evidence': result.evidence,
                'recommendation': result.recommendation
            }
            
            logger.info(f"作弊检测完成: 风险等级 {result.risk_level}")
            return detection_result
            
        except Exception as e:
            logger.error(f"作弊检测失败: {str(e)}")
            return {'error': str(e)}
    
    def get_cheating_report(self, session_id: str) -> Dict:
        """
        获取作弊报告
        
        Args:
            session_id: 会话ID
        
        Returns:
            作弊报告
        """
        try:
            from app.services.anti_cheating_service import get_anti_cheating_service
            service = get_anti_cheating_service()
            
            report = service.get_session_cheating_report(session_id)
            
            logger.info(f"作弊报告获取完成: {session_id}")
            return report
            
        except Exception as e:
            logger.error(f"获取作弊报告失败: {str(e)}")
            return {'error': str(e)}
    
    def record_exam_behavior(
        self,
        session_id: str,
        user_id: str,
        exam_id: str,
        event_type: str,
        question_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict:
        """
        记录考试行为
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            exam_id: 考试ID
            event_type: 事件类型
            question_id: 相关题目ID
            details: 事件详情
        
        Returns:
            记录结果
        """
        try:
            from app.services.anti_cheating_service import get_anti_cheating_service
            service = get_anti_cheating_service()
            
            result = service.record_behavior_event(
                session_id, user_id, exam_id, event_type, question_id, details
            )
            
            logger.info(f"行为记录完成: {event_type}")
            return result
            
        except Exception as e:
            logger.error(f"行为记录失败: {str(e)}")
            return {'error': str(e)}
    
    # ==================== 考试模板管理方法 ====================
    
    def create_exam_template(
        self,
        name: str,
        question_count: int,
        description: str = '',
        language: str = 'zh',
        level: str = 'intermediate',
        duration: int = 60,
        type_ratio: Optional[Dict] = None,
        difficulty_distribution: Optional[Dict] = None,
        knowledge_points: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> Optional[str]:
        """
        创建考试模板
        
        Args:
            name: 模板名称
            question_count: 题目数量
            description: 模板描述
            language: 语言
            level: 等级
            duration: 考试时长
            type_ratio: 题型比例
            difficulty_distribution: 难度分布
            knowledge_points: 知识点列表
            created_by: 创建者
        
        Returns:
            模板ID
        """
        try:
            from uuid import uuid4
            
            template_id = str(uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            query = """INSERT INTO exam_templates 
                      (id, name, description, language, level, duration, question_count,
                       question_types, difficulty_distribution, tags, created_by, created_at, updated_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            
            db_manager.execute(query, (
                template_id, name, description, language, level, duration, question_count,
                json.dumps(type_ratio or {}),
                json.dumps(difficulty_distribution or {}),
                json.dumps(knowledge_points or []),
                created_by, now, now
            ))
            
            logger.info(f"创建考试模板成功: {template_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"创建考试模板失败: {str(e)}")
            return None
    
    def get_exam_templates(self) -> List[Dict]:
        """
        获取考试模板列表
        
        Returns:
            模板列表
        """
        try:
            query = "SELECT * FROM exam_templates ORDER BY created_at DESC"
            results = db_manager.fetch_all(query)
            
            templates = []
            for result in results:
                if isinstance(result, dict):
                    templates.append({
                        'id': result['id'],
                        'name': result['name'],
                        'description': result.get('description', ''),
                        'language': result.get('language', 'zh'),
                        'level': result.get('level', 'intermediate'),
                        'duration': result.get('duration', 60),
                        'question_count': result.get('question_count', 20),
                        'question_types': json.loads(result.get('question_types', '{}')),
                        'difficulty_distribution': json.loads(result.get('difficulty_distribution', '{}')),
                        'tags': json.loads(result.get('tags', '[]')),
                        'created_by': result.get('created_by'),
                        'created_at': result.get('created_at'),
                        'updated_at': result.get('updated_at')
                    })
                else:
                    templates.append({
                        'id': result[0],
                        'name': result[1],
                        'description': result[2] if result[2] else '',
                        'language': result[3] if result[3] else 'zh',
                        'level': result[4] if result[4] else 'intermediate',
                        'duration': result[5] if result[5] else 60,
                        'question_count': result[6] if result[6] else 20,
                        'question_types': json.loads(result[7]) if result[7] else {},
                        'difficulty_distribution': json.loads(result[8]) if result[8] else {},
                        'tags': json.loads(result[9]) if result[9] else [],
                        'created_by': result[10],
                        'created_at': result[11],
                        'updated_at': result[12]
                    })
            
            return templates
            
        except Exception as e:
            logger.error(f"获取考试模板列表失败: {str(e)}")
            return []


# 创建全局实例
exam_service = ExamService()
