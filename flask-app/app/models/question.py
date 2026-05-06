# -*- coding: utf-8 -*-
"""
题库数据模型
包括题目、分类、语种和等级的数据库模型定义

import sqlite3
import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional

from app.config import load_config
from app.utils.db import db_manager

# 初始化日志记录器
logger = logging.getLogger(__name__)


class QuestionCategory:
    """题库分类模型"""

    def __init__(self, id: int = None, name: str = None, description: str = None,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class QuestionLanguage:
    """题库语种模型"""

    def __init__(self, id: int = None, name: str = None, code: str = None,
                 created_at: str = None, updated_at: str = None):
        self.name = name
        self.created_at = created_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'code': self.code,
            'updated_at': self.updated_at

class QuestionLevel:

                 created_at: str = None, updated_at: str = None):
        self.name = name
        self.created_at = created_at or datetime.now(UTC).isoformat()
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
        }


    """题目模型"""

                 category_id: int = None, language_id: int = None, level_id: int = None,
                 question_type: str = "single_choice", options: list = None,
                 discrimination_index: float = None, usage_count: int = 0,
                 correct_rate: float = None, audio_url: str = None, image_url: str = None,
                 created_at: str = None, updated_at: str = None):
        self.content = content
        self.explanation = explanation
        self.language_id = language_id
        self.level_id = level_id
        self.options = options or []  # 选择题选项列表
        self.difficulty_score = difficulty_score  # 难度分数(0-10)
        self.discrimination_index = discrimination_index  # 区分度(0-1)
        self.correct_rate = correct_rate  # 正确率(0-1)
        self.audio_url = audio_url  # 听力题音频URL
        self.video_url = video_url  # 视频题视频URL
        self.time_limit = time_limit  # 题目时间限制（秒）
        self.score = score  # 题目分值
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'answer': self.answer,
            'explanation': self.explanation,
            'language_id': self.language_id,
            'level_id': self.level_id,
            'question_type': self.question_type,
            'tags': self.tags,
            'difficulty_score': self.difficulty_score,
            'discrimination_index': self.discrimination_index,
            'usage_count': self.usage_count,
            'audio_url': self.audio_url,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'score': self.score,
            'created_at': self.created_at,
            'updated_at': self.updated_at

    # 静态方法，转发到question_manager实例
    @staticmethod
        """根据ID获取题目"""
        return question_manager.get_question(question_id)

    @staticmethod
    def get_questions(subject=None, difficulty=None, question_type=None, limit=100):
        """获取题目列表"""
        # 转换参数映射
        language_id_map = {'japanese': 1, 'english': 2}
        language_id = language_id_map.get(subject)

        level_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
        level_id = level_map.get(difficulty)

        return question_manager.get_questions(
            language_id=language_id,
            level_id=level_id,
            question_type=question_type,
            limit=limit
        )

    @staticmethod
    def get_question_count(subject=None):
        """获取题目数量"""
        # 转换参数映射
        language_id = language_id_map.get(subject)

        questions = question_manager.get_questions(language_id=language_id, limit=1000)

    @staticmethod
    def update_question_usage(question_id, accuracy):
        question = question_manager.get_question(question_id)
        if question:
            # 更新使用次数
            question.usage_count += 1
            # 更新正确率
            if question.correct_rate is None:
                question.correct_rate = accuracy
            else:
                # 平滑更新正确率
                question.correct_rate = (question.correct_rate * (question.usage_count - 1) + accuracy) / question.usage_count
            question_manager.update_question(question.id,
                                           usage_count=question.usage_count,
                                           correct_rate=question.correct_rate)

    @staticmethod
    def is_duplicate_question(content, language, category):
        """检查题目是否重复"""
        # 转换参数映射
        language_id_map = {'japanese': 1, 'english': 2}
        language_id = language_id_map.get(language)

        # 简单实现：检查内容是否相似
        questions = question_manager.get_questions(language_id=language_id, limit=100)
        for question in questions:
            if content in question.content or question.content in content:
                return True

    @staticmethod
    def create_table():
        """创建题目表"""
        pass
    @staticmethod
        # 转换参数映射
        language_id_map = {'japanese': 1, 'english': 2}
        if 'language' in kwargs:
            kwargs['language_id'] = language_id_map.get(kwargs.pop('language'))

        level_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
        if 'difficulty' in kwargs:
            kwargs['level_id'] = level_map.get(kwargs.pop('difficulty'))

        return question_manager.get_questions(**kwargs)

    @staticmethod
    def _connect_db():
        """获取数据库连接"""
        return question_manager._get_connection()


    """题库管理器"""

    def __init__(self):
        # 使用数据库管理器，不再需要直接管理数据库连接
        self._create_tables()

        """创建数据库表结构"""
        try:

            # 创建题目分类表
            logger.info("创建题目分类表...")
            CREATE TABLE IF NOT EXISTS question_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
            )
            '''
            logger.debug(f"执行SQL: {create_category_table_sql}")
            db_manager.execute(create_category_table_sql)
            logger.info("题目分类表创建成功")

            # 创建题目语种表
            logger.info("创建题目语种表...")
            CREATE TABLE IF NOT EXISTS question_languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                updated_at TEXT
            )
            '''
            logger.debug(f"执行SQL: {create_language_table_sql}")
            db_manager.execute(create_language_table_sql)
            logger.info("题目语种表创建成功")

            logger.info("创建题目等级表...")
            create_level_table_sql = '''
            CREATE TABLE IF NOT EXISTS question_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            '''
            logger.debug(f"执行SQL: {create_level_table_sql}")
            db_manager.execute(create_level_table_sql)
            logger.info("题目等级表创建成功")

            # 创建题目表，包含新添加的字段
            logger.info("创建题目表...")
            create_question_table_sql = '''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                answer TEXT NOT NULL,
                explanation TEXT,
                category_id INTEGER,
                language_id INTEGER,
                level_id INTEGER,
                question_type TEXT DEFAULT 'single_choice',
                options TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                difficulty_score REAL,
                discrimination_index REAL,
                usage_count INTEGER DEFAULT 0,
                correct_rate REAL,
                audio_url TEXT,
                image_url TEXT,
                video_url TEXT,
                time_limit INTEGER,
                score INTEGER,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (category_id) REFERENCES question_categories (id),
                FOREIGN KEY (language_id) REFERENCES question_languages (id),
                FOREIGN KEY (level_id) REFERENCES question_levels (id)
            '''
            db_manager.execute(create_question_table_sql)
            logger.info("题目表创建成功")
            # 插入默认数据
            self._insert_default_data()

        except Exception as e:
            logger.error(f"创建数据库表结构失败: {str(e)}")
            import traceback
            traceback.print_exc()
    def _insert_default_data(self):
        """插入默认数据"""
            # 检查是否已有数据
            categories = self.get_all_categories()
            if not categories:
                self.create_category('默认分类', '默认题目分类')
            languages = self.get_all_languages()
            if not languages:
                self.create_language('日语', 'ja')
                self.create_language('英语', 'en')
                self.create_language('中文', 'zh')
            if not levels:
                # 插入默认等级
                self.create_level('初级', 1, '初级难度')
                self.create_level('中级', 2, '中级难度')
                self.create_level('高级', 3, '高级难度')
                self.create_level('专家', 4, '专家难度')

            logger.info("默认数据插入成功")
        except Exception as e:
            logger.error(f"插入默认数据失败: {str(e)}")

    def _get_connection(self):
        """获取数据库连接"""
        # 此方法不再需要，使用db_manager替代
        return None

    # 分类管理
    def create_category(self, name: str, description: str = None) -> QuestionCategory:
        """创建分类"""
        now = datetime.now(UTC).isoformat()

        data = {
            'name': name,
            'created_at': now,
            'updated_at': now
        }

        category_id = db_manager.insert('question_categories', data)

        if category_id:
            return QuestionCategory(id=category_id, name=name, description=description, created_at=now, updated_at=now)
        return None

        """获取分类"""
        query = 'SELECT id, name, description, created_at, updated_at FROM question_categories WHERE id = ?'
        row = db_manager.fetch_one(query, (category_id,))

        if row:
            if isinstance(row, dict):
                return QuestionCategory(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return QuestionCategory(*row)
        return None

    def get_all_categories(self) -> List[QuestionCategory]:
        """获取所有分类"""
        query = 'SELECT id, name, description, created_at, updated_at FROM question_categories ORDER BY id'
        rows = db_manager.fetch_all(query)

        categories = []
        for row in rows:
            if isinstance(row, dict):
                categories.append(QuestionCategory(
                    id=row['id'],
                    name=row['name'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            else:
        return categories

    # 语种管理
    def create_language(self, name: str, code: str) -> QuestionLanguage:
        """创建语种"""
        now = datetime.now(UTC).isoformat()

        data = {
            'name': name,
            'code': code,
            'created_at': now,
            'updated_at': now
        }

        language_id = db_manager.insert('question_languages', data)

        if language_id:
            return QuestionLanguage(id=language_id, name=name, code=code, created_at=now, updated_at=now)
        return None

    def get_language(self, language_id: int) -> Optional[QuestionLanguage]:
        """获取语种"""
        query = 'SELECT id, name, code, created_at, updated_at FROM question_languages WHERE id = ?'
        row = db_manager.fetch_one(query, (language_id,))

        if row:
            # 确保返回的是元组格式
            if isinstance(row, dict):
                return QuestionLanguage(
                    id=row['id'],
                    name=row['name'],
                    code=row['code'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return QuestionLanguage(*row)
        return None

    def get_all_languages(self) -> List[QuestionLanguage]:
        """获取所有语种"""
        query = 'SELECT id, name, code, created_at, updated_at FROM question_languages ORDER BY id'
        rows = db_manager.fetch_all(query)

        languages = []
        for row in rows:
            if isinstance(row, dict):
                languages.append(QuestionLanguage(
                    id=row['id'],
                    name=row['name'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            else:
                languages.append(QuestionLanguage(*row))
        return languages

    # 等级管理
    def create_level(self, name: str, level: int, description: str = None) -> QuestionLevel:
        """创建等级"""
        now = datetime.now(UTC).isoformat()

        data = {
            'level': level,
            'description': description,
            'updated_at': now


            return QuestionLevel(id=level_id, name=name, level=level, description=description, created_at=now, updated_at=now)

    def get_level(self, level_id: int) -> Optional[QuestionLevel]:
        """获取等级"""
        row = db_manager.fetch_one(query, (level_id,))

            # 确保返回的是元组格式
                return QuestionLevel(
                    id=row['id'],
                    level=row['level'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return QuestionLevel(*row)
        return None

    def get_all_levels(self) -> List[QuestionLevel]:
        """获取所有等级"""
        query = 'SELECT id, name, level, description, created_at, updated_at FROM question_levels ORDER BY level'
        rows = db_manager.fetch_all(query)

        levels = []
        for row in rows:
            if isinstance(row, dict):
                    id=row['id'],
                    description=row['description'],
                    updated_at=row['updated_at']
                ))
            else:
        return levels

    def create_question(self, content: str, answer: str, explanation: str = None,
                       category_id: int = None, language_id: int = None, level_id: int = None,
                       question_type: str = "single_choice", options: list = None, tags: list = None,
                       difficulty_score: float = None, discrimination_index: float = None,
                       image_url: str = None, video_url: str = None, time_limit: int = None, score: int = None) -> Question:
        """创建题目"""

        # 构建数据字典
            'content': content,
            'answer': answer,
            'explanation': explanation,
            'category_id': category_id,
            'level_id': level_id,
            'type': question_type,
            'difficulty_score': difficulty_score,
            'audio_url': audio_url,
            'image_url': image_url,
            'time_limit': time_limit,
        }
        # 插入数据
        question_id = db_manager.insert('questions', data)
            # 处理选项
            if options:
                    db_manager.execute(
                        'INSERT INTO question_options (question_id, option_text, option_index) VALUES (?, ?, ?)',
                    )

            if tags:
                for tag_name in tags:
                    # 查找或创建标签
                    tag = db_manager.fetch_one('SELECT id FROM question_tags WHERE tag_name = ?', (tag_name,))
                    if not tag:
                        db_manager.execute('INSERT INTO question_tags (tag_name) VALUES (?)', (tag_name,))
                        tag_id = tag['last_insert_rowid()'] if isinstance(tag, dict) else tag[0]
                    else:

                    # 关联标签
                        'INSERT OR IGNORE INTO question_tag_relations (question_id, tag_id) VALUES (?, ?)',
                        (question_id, tag_id)
                    )

            return Question(id=question_id, content=content, answer=answer, explanation=explanation,
                           question_type=question_type, options=options or [], tags=tags or [],
                           difficulty_score=difficulty_score, discrimination_index=discrimination_index,
                           usage_count=usage_count, correct_rate=correct_rate, audio_url=audio_url,
                           created_at=now, updated_at=now)

    def get_question(self, question_id: int) -> Optional[Question]:
        """获取题目"""
        # 构建查询语句，包含所有可能的字段
        query = '''
               question_type, difficulty_score, discrimination_index,
               created_at, updated_at
        '''

        row = db_manager.fetch_one(query, (question_id,))
        if row:
                question_data = {
                    'id': row['id'],
                    'answer': row['answer'],
                    'explanation': row['explanation'],
                    'language_id': row['language_id'],
                    'level_id': row['level_id'],
                    'question_type': row.get('question_type', 'single_choice'),
                    'options': [],
                    'tags': [],
                    'difficulty_score': row.get('difficulty_score'),
                    'usage_count': row.get('usage_count', 0),
                    'audio_url': row.get('audio_url'),
                    'video_url': row.get('video_url'),
                    'time_limit': row.get('time_limit'),
                    'score': row.get('score'),
                    'updated_at': row.get('updated_at')
            else:
                # 元组格式
                question_data = {
                    'content': row[1],
                    'answer': row[2],
                    'explanation': row[3],
                    'language_id': row[5],
                    'question_type': row[7] if len(row) > 7 else 'single_choice',
                    'tags': [],
                    'difficulty_score': row[8] if len(row) > 8 else None,
                    'discrimination_index': row[9] if len(row) > 9 else None,
                    'usage_count': row[10] if len(row) > 10 else 0,
                    'correct_rate': row[11] if len(row) > 11 else None,
                    'audio_url': row[12] if len(row) > 12 else None,
                    'image_url': row[13] if len(row) > 13 else None,
                    'video_url': row[14] if len(row) > 14 else None,
                    'time_limit': row[15] if len(row) > 15 else None,
                    'score': row[16] if len(row) > 16 else None,
                    'created_at': row[17] if len(row) > 17 else None,
                    'updated_at': row[18] if len(row) > 18 else None
                }

            # 获取选项
            options = db_manager.fetch_all(
                'SELECT option_text FROM question_options WHERE question_id = ? ORDER BY option_index',
                (question_id,)
            )
            question_data['options'] = [opt['option_text'] if isinstance(opt, dict) else opt[0] for opt in options]

            # 获取标签
            tags = db_manager.fetch_all(
                '''
                FROM question_tag_relations qtr
                JOIN question_tags qt ON qtr.tag_id = qt.id
                WHERE qtr.question_id = ?
                ''',
                (question_id,)
            )
            question_data['tags'] = [tag['tag_name'] if isinstance(tag, dict) else tag[0] for tag in tags]
            return Question(**question_data)
        return None

    def check_question_duplicate(self, content: str, language_id: int, level_id: int,
                                threshold: float = 0.9) -> bool:
        检查题目是否重复

        Args:
            content: 题目内容
            language_id: 语种ID
            level_id: 等级ID
            threshold: 相似度阈值

        Returns:
            bool: 是否重复
        # 首先检查完全相同的内容
        SELECT COUNT(*) FROM questions
        WHERE content = ? AND language_id = ? AND level_id = ?
        '''
        count = db_manager.fetch_scalar(query, (content, language_id, level_id))
        if count and count > 0:
            return True
        # 检查相似度高的题目（使用简单的字符串相似度检查）
        query = '''
        SELECT content FROM questions
        WHERE language_id = ? AND level_id = ?
        '''
        existing_contents = db_manager.fetch_all(query, (language_id, level_id))
        for row in existing_contents:
            if isinstance(row, dict):
                existing_content = row['content']
            else:
                existing_content = row[0]
            similarity = self._calculate_similarity(content, existing_content)
            if similarity >= threshold:

        return False

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        计算两个字符串的相似度

        Args:
            str1: 第一个字符串
            str2: 第二个字符串

        Returns:
            float: 相似度 (0-1)
        import difflib
        return difflib.SequenceMatcher(None, str1, str2).ratio()

    def get_questions(self, category_id: int = None, language_id: int = None, level_id: int = None,
                     question_type: str = None, tags: list = None, difficulty_min: float = None,
                     difficulty_max: float = None, correct_rate_min: float = None,
                     correct_rate_max: float = None, limit: int = 100, offset: int = 0) -> List[Question]:
        """获取题目列表，支持按分类、语种、等级、题目类型、标签、难度、正确率过滤"""
        # 构建查询语句，包含所有可能的字段
        query = '''
        SELECT id, content, answer, explanation, category_id, language_id, level_id,
               question_type, difficulty_score, discrimination_index,
               usage_count, correct_rate, audio_url, image_url, video_url, time_limit, score,
               created_at, updated_at
        '''
        params = []

        if category_id:
            query += ' AND category_id = ?'
            params.append(category_id)
        if language_id:
            query += ' AND language_id = ?'
            params.append(language_id)
        if level_id:
            query += ' AND level_id = ?'
            params.append(level_id)
        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type)
        if difficulty_min is not None:
            query += ' AND difficulty_score >= ?'
            params.append(difficulty_min)
        if difficulty_max is not None:
            query += ' AND difficulty_score <= ?'
        if correct_rate_min is not None:
            query += ' AND correct_rate >= ?'
            params.append(correct_rate_min)
        if correct_rate_max is not None:
            query += ' AND correct_rate <= ?'
            params.append(correct_rate_max)

        # 标签过滤
        if tags:
                params.append(tag)

        query += ' ORDER BY id LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        rows = db_manager.fetch_all(query, params)

        questions = []
            # 解析字段
                question_data = {
                    'content': row['content'],
                    'explanation': row['explanation'],
                    'category_id': row['category_id'],
                    'language_id': row['language_id'],
                    'level_id': row['level_id'],
                    'question_type': row.get('question_type', 'single_choice'),
                    'options': [],
                    'tags': [],
                    'difficulty_score': row.get('difficulty_score'),
                    'discrimination_index': row.get('discrimination_index'),
                    'usage_count': row.get('usage_count', 0),
                    'correct_rate': row.get('correct_rate'),
                    'audio_url': row.get('audio_url'),
                    'image_url': row.get('image_url'),
                    'video_url': row.get('video_url'),
                    'time_limit': row.get('time_limit'),
                    'score': row.get('score'),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at')
                }
            else:
                # 元组格式
                question_data = {
                    'id': row[0],
                    'content': row[1],
                    'answer': row[2],
                    'explanation': row[3],
                    'language_id': row[5],
                    'level_id': row[6],
                    'question_type': row[7] if len(row) > 7 else 'single_choice',
                    'tags': [],
                    'difficulty_score': row[8] if len(row) > 8 else None,
                    'discrimination_index': row[9] if len(row) > 9 else None,
                    'usage_count': row[10] if len(row) > 10 else 0,
                    'audio_url': row[12] if len(row) > 12 else None,
                    'image_url': row[13] if len(row) > 13 else None,
                    'video_url': row[14] if len(row) > 14 else None,
                    'time_limit': row[15] if len(row) > 15 else None,
                    'score': row[16] if len(row) > 16 else None,
                    'created_at': row[17] if len(row) > 17 else None,
                    'updated_at': row[18] if len(row) > 18 else None
                }

            # 获取选项
            options = db_manager.fetch_all(
                'SELECT option_text FROM question_options WHERE question_id = ? ORDER BY option_index',
                (question_data['id'],)
            )

            # 获取标签
            tags = db_manager.fetch_all(
                '''
                SELECT qt.tag_name
                FROM question_tag_relations qtr
                JOIN question_tags qt ON qtr.tag_id = qt.id
                WHERE qtr.question_id = ?
            )

            questions.append(Question(**question_data))

        return questions

    def update_question(self, question_id: int, **kwargs) -> Optional[Question]:
        """更新题目"""
        # 获取现有题目
        question = self.get_question(question_id)
        if not question:
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(question, key):
                setattr(question, key, value)

        # 更新updated_at
        question.updated_at = datetime.now(UTC).isoformat()

        # 构建更新数据
            'content': question.content,
            'answer': question.answer,
            'explanation': question.explanation,
            'category_id': question.category_id,
            'language_id': question.language_id,
            'level_id': question.level_id,
            'question_type': question.question_type,
            'difficulty_score': question.difficulty_score,
            'discrimination_index': question.discrimination_index,
            'usage_count': question.usage_count,
            'correct_rate': question.correct_rate,
            'audio_url': question.audio_url,
            'image_url': question.image_url,
            'time_limit': question.time_limit,
            'updated_at': question.updated_at
        }

        success = db_manager.update('questions', data, 'id = ?', (question_id,))
        if success:
                db_manager.execute('DELETE FROM question_options WHERE question_id = ?', (question_id,))
                if kwargs['options']:
                        db_manager.execute(
                            'INSERT INTO question_options (question_id, option_text, option_index) VALUES (?, ?, ?)',
                            (question_id, option_text, index)
                        )

            # 更新标签
            if 'tags' in kwargs:
                # 删除旧标签关联
                db_manager.execute('DELETE FROM question_tag_relations WHERE question_id = ?', (question_id,))
                # 添加新标签
                if kwargs['tags']:
                    for tag_name in kwargs['tags']:
                        # 查找或创建标签
                        tag = db_manager.fetch_one('SELECT id FROM question_tags WHERE tag_name = ?', (tag_name,))
                        if not tag:
                            db_manager.execute('INSERT INTO question_tags (tag_name) VALUES (?)', (tag_name,))
                            tag = db_manager.fetch_one('SELECT last_insert_rowid()')
                            tag_id = tag['last_insert_rowid()'] if isinstance(tag, dict) else tag[0]
                        else:
                            tag_id = tag['id'] if isinstance(tag, dict) else tag[0]

                        # 关联标签
                            (question_id, tag_id)

            return question

    def delete_question(self, question_id: int) -> bool:
        """删除题目"""
        success = db_manager.delete('questions', 'id = ?', (question_id,))
        return success

    def batch_delete_questions(self, question_ids: List[int]) -> bool:
        批量删除题目

        Args:
            question_ids: 要删除的题目ID列表

        Returns:
            是否删除成功
        if not question_ids:
            return True

        placeholders = ','.join(['?'] * len(question_ids))
        query = f'DELETE FROM questions WHERE id IN ({placeholders})'
        # 执行删除
        cursor, success = db_manager.execute(query, question_ids)
            # 对于批量删除，需要获取影响的行数
            if hasattr(cursor, 'rowcount'):
            else:
                affected_rows = len(question_ids)
            return affected_rows > 0

        批量更新题目
            updates: 更新数据列表，每个元素包含id和要更新的字段
        Returns:
            更新成功的题目数量
            return 0

        for update in updates:
                question_id = update.pop('id')
                # 执行更新
                if success:
            except Exception as e:

        return success_count

    def analyze_question_difficulty(self, question_id: int) -> float:
        Args:

            难度分数(0-10)
        # 这里实现题目难度分析逻辑
        import random
        return round(random.uniform(1.0, 10.0), 2)
    def analyze_question_discrimination(self, question_id: int) -> float:

            question_id: 题目ID
        Returns:
        # 这里实现题目区分度分析逻辑
        return round(random.uniform(0.0, 1.0), 3)
    def generate_question_bank_report(self) -> dict:

        Returns:
            题库报告数据
        total_questions = db_manager.fetch_scalar('SELECT COUNT(*) FROM questions')
        # 按题型统计
        questions_by_type = {row[0]: row[1] for row in rows}
        # 按难度统计
        questions_by_level = {row[0]: row[1] for row in rows}
        # 按分类统计

        rows = db_manager.fetch_all('SELECT language_id, COUNT(*) FROM questions GROUP BY language_id')

            'total_questions': total_questions,
            'questions_by_level': questions_by_level,
            'questions_by_category': questions_by_category,
            'questions_by_language': questions_by_language,
        }
    def search_questions(self, keyword: str, category_id: int = None, language_id: int = None,
        搜索题目

        Args:
            category_id: 分类ID
            level_id: 等级ID

        # 构建查询语句，包含所有可能的字段
               question_type, difficulty_score, discrimination_index,
               usage_count, correct_rate, audio_url, image_url, video_url, time_limit, score,
        FROM questions
        '''

            query += ' AND category_id = ?'
        if level_id:
            params.append(question_type)
        questions = []
        for row in rows:
            if isinstance(row, dict):
                question_data = {
                    'content': row['content'],
                    'answer': row['answer'],
                    'category_id': row['category_id'],
                    'question_type': row.get('question_type', 'single_choice'),
                    'options': [],
                    'tags': [],
                    'difficulty_score': row.get('difficulty_score'),
                    'discrimination_index': row.get('discrimination_index'),
                    'usage_count': row.get('usage_count', 0),
                    'correct_rate': row.get('correct_rate'),
                    'audio_url': row.get('audio_url'),
                    'image_url': row.get('image_url'),
                    'video_url': row.get('video_url'),
                    'time_limit': row.get('time_limit'),
                    'score': row.get('score'),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at')
                }
            else:
                # 元组格式
                question_data = {
                    'id': row[0],
                    'content': row[1],
                    'answer': row[2],
                    'explanation': row[3],
                    'category_id': row[4],
                    'language_id': row[5],
                    'level_id': row[6],
                    'question_type': row[7] if len(row) > 7 else 'single_choice',
                    'options': [],
                    'tags': [],
                    'difficulty_score': row[8] if len(row) > 8 else None,
                    'discrimination_index': row[9] if len(row) > 9 else None,
                    'usage_count': row[10] if len(row) > 10 else 0,
                    'correct_rate': row[11] if len(row) > 11 else None,
                    'audio_url': row[12] if len(row) > 12 else None,
                    'image_url': row[13] if len(row) > 13 else None,
                    'video_url': row[14] if len(row) > 14 else None,
                    'time_limit': row[15] if len(row) > 15 else None,
                    'score': row[16] if len(row) > 16 else None,
                    'created_at': row[17] if len(row) > 17 else None,
                    'updated_at': row[18] if len(row) > 18 else None
                }

            # 获取选项
            options = db_manager.fetch_all(
                'SELECT option_text FROM question_options WHERE question_id = ? ORDER BY option_index',
                (question_data['id'],)
            )
            question_data['options'] = [opt['option_text'] if isinstance(opt, dict) else opt[0] for opt in options]

            # 获取标签
            tags = db_manager.fetch_all(
                '''
                SELECT qt.tag_name
                FROM question_tag_relations qtr
                JOIN question_tags qt ON qtr.tag_id = qt.id
                WHERE qtr.question_id = ?
                ''',
                (question_data['id'],)
            )
            question_data['tags'] = [tag['tag_name'] if isinstance(tag, dict) else tag[0] for tag in tags]

            questions.append(Question(**question_data))

        return questions

    def get_popular_tags(self, limit: int = 20) -> List[dict]:
        获取热门标签

        Args:

        Returns:
            热门标签列表
        # 从关联表中获取标签统计
        SELECT qt.tag_name, COUNT(*) as count
        FROM question_tag_relations qtr
        JOIN question_tags qt ON qtr.tag_id = qt.id
        GROUP BY qt.tag_name
        ORDER BY count DESC
        LIMIT ?
        '''

        rows = db_manager.fetch_all(query, (limit,))

        # 构建结果
        popular_tags = []
        for row in rows:
            if isinstance(row, dict):
                popular_tags.append({'tag': row['tag_name'], 'count': row['count']})
            else:
                popular_tags.append({'tag': row[0], 'count': row[1]})

        return popular_tags
    def evaluate_question_quality(self, question_id: int) -> dict:
        评估题目质量

        Args:
            question_id: 题目ID

        Returns:
            题目质量评估结果
        question = self.get_question(question_id)
            return {}

        # 计算质量评分
        quality_score = 0
        feedback = []

        # 1. 基于正确率评估
        if question.correct_rate is not None:
            if 0.3 <= question.correct_rate <= 0.8:
                # 正确率在合理范围内
                quality_score += 4
            elif question.correct_rate < 0.3:
                # 题目太难
                quality_score += 1
                feedback.append("题目难度过高")
            else:
                # 题目太简单
                quality_score += 1
                feedback.append("题目难度过低")
        else:
            # 没有足够的数据
            quality_score += 2
            feedback.append("缺少足够的答题数据")

        if question.discrimination_index is not None:
            if question.discrimination_index >= 0.3:
                # 区分度良好
                quality_score += 3
            else:
                # 区分度不佳
                quality_score += 1
                feedback.append("题目区分度不佳")
            # 没有区分度数据
            quality_score += 1

        # 3. 基于使用次数评估
        if question.usage_count >= 50:
            # 使用次数足够
            quality_score += 3
        elif question.usage_count >= 10:
            # 使用次数一般
            quality_score += 2
        else:
            # 使用次数太少
            quality_score += 1

        if question.difficulty_score is not None:
            if 3 <= question.difficulty_score <= 7:
                # 难度适中
                quality_score += 2
                # 难度偏低
            else:
                # 难度偏高
                feedback.append("题目难度分数偏高")
        else:
            # 没有难度分数
            quality_score += 1

        # 生成质量等级
            quality_level = "优秀"
        elif quality_score >= 8:
        elif quality_score >= 5:
            quality_level = "一般"
            quality_level = "较差"
        return {
            "question_id": question_id,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "metrics": {
                "correct_rate": question.correct_rate,
                "discrimination_index": question.discrimination_index,
                "usage_count": question.usage_count,
                "difficulty_score": question.difficulty_score
            }
        }

    def optimize_question_quality(self, question_id: int) -> bool:
        优化题目质量

        Args:
            question_id: 题目ID

        Returns:
            是否优化成功
        try:
            question = self.get_question(question_id)
                return False

            # 获取质量评估结果

            # 根据评估结果进行优化
            updates = {}

            if "题目难度过高" in quality_eval["feedback"] and question.difficulty_score:
                updates["difficulty_score"] = max(1.0, question.difficulty_score - 1.5)
                updates["difficulty_score"] = min(10.0, question.difficulty_score + 1.5)

            if "缺少足够的答题数据" in quality_eval["feedback"]:
                # 可以在这里添加逻辑，例如调整题目在生成试卷时的权重
            # 如果有更新，保存到数据库
            if updates:

            return True
            logger.error(f"优化题目 {question_id} 质量失败: {str(e)}")
            return False
    def batch_optimize_questions(self, limit: int = 100) -> dict:

            limit: 优化题目数量限制

            优化结果
        try:
            # 获取所有题目
            questions = self.get_questions(limit=limit)
            failed_count = 0
            for question in questions:
                    failed_count += 1

            return {
                "success_count": success_count,
                "total_questions": len(questions)
            }
            logger.error(f"批量优化题目质量失败: {str(e)}")
            return {
                "total_questions": 0,
                "error": str(e)
    def batch_import_questions(self, questions_data: List[dict]) -> dict:
        批量导入题目
        Args:

            导入结果
        logger.info(f"开始批量导入 {len(questions_data)} 道题目")
        success_count = 0
        for question_data in questions_data:
                if not self._validate_question_data(question_data):
                    error_count += 1
                    continue
                self.create_question(
                    content=question_data["content"],
                    category_id=question_data.get("category_id"),
                    question_type=question_data.get("question_type", "single_choice"),
                error_count += 1
        return {
            "errors": errors


        Args:
        Returns:
            是否验证通过
            if not question_data.get(field):

        # 验证题目类型
        if question_data.get("question_type") and question_data.get("question_type") not in valid_types:
        # 验证选择题必须有选项
        if question_type in ["single_choice", "multiple_choice"]:
            if not question_data.get("options") or len(question_data.get("options")) < 2:

        # 验证听力题必须有音频URL
            if not question_data.get("audio_url"):
                return False
        return True

                         question_type: str = None) -> List[Question]:
        自动生成题目
        Args:
            count: 生成题目的数量
            language_id: 语种ID
            question_type: 题目类型 (single_choice, multiple_choice, true_false, fill_blank, short_answer, listening)
        Returns:
            生成的题目列表

        generated_questions = []

        # 获取分类、语种和等级信息
        languages = self.get_all_languages()
        levels = self.get_all_levels()
        # 选择目标分类、语种和等级
        target_category = None
            target_category = self.get_category(category_id)
        elif categories:
            import random
            target_category = random.choice(categories)

        if language_id:
        elif languages:
            import random

        target_level = None
            target_level = self.get_level(level_id)
        elif levels:
            import random

        # 如果没有找到合适的分类、语种或等级，使用默认值
            target_category = QuestionCategory(name="数学", description="数学题目分类")
            target_category = self.create_category(target_category.name, target_category.description)
        if not target_language:
            target_language = self.create_language(target_language.name, target_language.code)
        if not target_level:
            target_level = QuestionLevel(name="初级", level=1, description="适合初学者")

        # 扩展可用的题目类型
        available_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer", "case_analysis", "comprehensive"]

            "数学": {
                "初级": {
                    "topics": ["基础算术", "简单几何", "时间计算", "单位换算", "数字认知"],
                    "question_templates": {
                        "single_choice": [
                            "{num1} + {num2} = ?",
                            "{num1} - {num2} = ?",
                            "{num1} × {num2} = ?",
                            "{num1} ÷ {num2} = ?",
                            "以下哪个是奇数？"
                        ],
                            "以下哪些是偶数？",
                            "以下哪些是3的倍数？"
                        ],
                        "true_false": [
                            "{num1} + {num2} = {sum}",
                            "{num1}是偶数",
                        ],
                        "fill_blank": [
                            "{num1} × {num2} = ____",
                            "1小时 = ____分钟"
                        ],
                            "请计算：{num1} + {num2} + {num3}",
                            "请计算：{num1} × {num2} ÷ {num3}",
                            "请写出3个偶数"
                        ]
                },
                "中级": {
                    "topics": ["代数基础", "几何图形", "分数运算", "小数运算", "应用题"],
                    "question_templates": {
                        "single_choice": [
                            "解方程：{coeff}x + {const} = {result}",
                            "半径为{radius}的圆的面积是多少？",
                        ],
                        "multiple_choice": [
                            "以下哪些是方程{coeff}x + {const} = {result}的解？"
                        ],
                        "true_false": [
                            "所有偶数都是合数",
                            "三角形内角和为180度",
                            "圆的周长公式是πr²"
                        ],
                        "fill_blank": [
                            "解方程：2x + {num} = {result}，x = ____",
                            "{fraction} = ____（小数）",
                            "长方形的面积公式是 ____ × 宽"
                        ],
                        "short_answer": [
                            "请简述勾股定理的内容",
                            "请计算半径为{radius}的圆的周长",
                            "解方程：{coeff}x² + {const} = {result}"
                        ]
                    }
                },
                "高级": {
                    "topics": ["三角函数", "微积分基础", "线性代数", "概率统计", "复杂方程"],
                    "question_templates": {
                        "single_choice": [
                            "sin(π/2) = ?",
                            "lim(x→0) sin(x)/x = ?",
                        ],
                        "multiple_choice": [
                            "以下哪些是可导函数？"
                        "true_false": [
                            "导数为零的点一定是极值点",
                            "奇函数的图像关于原点对称"
                        ],
                        "fill_blank": [
                            "d/dx (x²) = ____",
                            "∫x dx = ____ + C"
                        ],
                        "short_answer": [
                            "请计算∫₀¹ x² dx",
                            "请求解微分方程 y' + y = 0",
                            "请计算正态分布N(0,1)的均值和方差"
                        ]
                    }
                }
            },
            "英语": {
                "初级": {
                    "topics": ["基础词汇", "简单语法", "日常对话", "数字表达", "时间表达"],
                    "question_templates": {
                        "single_choice": [
                            "What is the English word for '{chinese_word}'?",
                            "Which one is a color?"
                        ],
                        "multiple_choice": [
                            "Which of the following are fruits?",
                            "Which of the following are colors?"
                        "true_false": [
                            "'Apple' means '{chinese_word}' in Chinese",
                            "'Red' is a color"
                        ],
                            "The English word for '{chinese_word}' is ____",
                        ],
                            "What is the English word for '{chinese_word}'?",
                            "How do you say '{chinese_word}' in English?"
                    }
                },
                "中级": {
                    "question_templates": {
                        "single_choice": [
                            "What is the past tense of '{verb}'?",
                            "Which one is correct?",
                            "Choose the right preposition: I go ____ school by bus"
                        ],
                        "multiple_choice": [
                            "Which of the following are irregular verbs?",
                        ],
                        "true_false": [
                            "She ____ to the park yesterday (go的正确形式)",
                            "I ____ English for 3 years (learn的正确形式)"
                        ],
                        "short_answer": [
                            "What is the difference between 'say' and 'tell'?",
                            "How do you form the present perfect tense?"
                        ]
                    }
                "高级": {
                    "question_templates": {
                            "Which one is a complex sentence?",
                            "Choose the correct passive voice: The book ____ by him",
                            "Which one uses correct subject-verb agreement?"
                        "multiple_choice": [
                            "Which of the following are complex sentences?",
                            "Which of the following use correct parallel structure?"
                        ],
                        "true_false": [
                            "'Had + past participle' is used for past perfect tense",
                            "Passive voice is always better than active voice"
                        ],
                            "____ the weather is bad, we will go out (连词填空)"
                        ],
                        "short_answer": [
                            "Please explain the difference between present perfect and simple past",
                            "Please translate the sentence into English: '{chinese_sentence}'",
                            "Please write a paragraph about '{topic}'"
                        ]
                    }
                }
            },
            "语文": {
                "初级": {
                    "topics": ["汉字认知", "词语理解", "句子结构", "标点符号", "古诗词背诵"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是正确的汉字？",
                            "'美丽'的近义词是？",
                            "以下哪个标点符号使用正确？"
                        ],
                        "multiple_choice": [
                            "以下哪些是量词？"
                        "true_false": [
                            "'苹果'是一个名词",
                        "fill_blank": [
                            "床前明月光，疑是____霜",
                            "我有一____书（量词填空）"
                        ],
                        "short_answer": [
                            "请用'快乐'造句"
                        ],
                        "case_analysis": [
                            "阅读下面的短文，回答问题：\n\n春天来了，万物复苏。花园里的花开了，有红色的、黄色的、紫色的，非常美丽。小鸟在树上唱歌，蝴蝶在花丛中飞舞。\n\n问题：短文描述的是什么季节？",
                            "阅读下面的句子，回答问题：\n\n小明是一个聪明的孩子，他学习很努力，经常帮助同学。\n\n问题：小明是一个什么样的孩子？"
                        ],
                        "comprehensive": [
                            "请完成以下任务：\n1. 写出'春'的反义词\n2. 用'春天'造句\n3. 写出两个描写春天的成语"
                        ]
                    }
                "中级": {
                    "topics": ["阅读理解", "作文写作", "语法知识", "修辞手法", "文学常识"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是比喻句？",
                            "'春风又绿江南岸'中的'绿'是什么词性？",
                            "以下哪个成语使用正确？"
                        ],
                            "以下哪些是修辞手法？",
                            "以下哪些是鲁迅的作品？"
                        ],
                        "true_false": [
                            "比喻是一种修辞手法",
                            "《红楼梦》的作者是施耐庵"
                        ],
                        "fill_blank": [
                            "____，淡妆浓抹总相宜",
                            "他跑得像____一样快（比喻填空）"
                        ],
                        "short_answer": [
                            "请解释成语'画龙点睛'的意思",
                            "请分析这句话的修辞手法：'叶子出水很高，像亭亭的舞女的裙'",
                            "请简述《三国演义》的主要内容"
                        ],
                        "case_analysis": [
                            "阅读下面的段落，回答问题：\n\n月光如流水一般，静静地泻在这一片叶子和花上。薄薄的青雾浮起在荷塘里。叶子和花仿佛在牛乳中洗过一样；又像笼着轻纱的梦。\n\n问题：1. 这段话使用了什么修辞手法？\n2. 作者通过这段描写表达了怎样的情感？",
                            "阅读下面的句子，分析其语法结构：\n\n他昨天在图书馆认真地读了一本关于中国历史的书。\n\n问题：1. 这句话的主语是什么？\n2. 这句话的状语有哪些？"
                        ],
                        "comprehensive": [
                            "请完成以下任务：\n1. 分析'春风又绿江南岸'中'绿'字的用法\n2. 写出两个含有'绿'字的成语\n3. 用'绿'字写一个比喻句"
                        ]
                    }
                "高级": {
                        "single_choice": [
                            "以下哪个是文言虚词？",
                            "'落霞与孤鹜齐飞，秋水共长天一色'出自哪篇文章？",
                            "以下哪个是通假字？"
                        "multiple_choice": [
                            "以下哪些是唐宋八大家？",
                            "以下哪些是词牌名？"
                        ],
                        "true_false": [
                            "'之乎者也'是文言虚词",
                            "《诗经》是我国第一部诗歌总集"
                        ],
                        "fill_blank": [
                            "天生我材必有用，____千金散尽还复来",
                            "____，必有我师焉"
                        ],
                        "short_answer": [
                            "请赏析杜甫《登高》的艺术特色",
                            "请翻译文言文：'学而时习之，不亦说乎'",
                            "请论述《红楼梦》的主题思想"
                        ],
                        "case_analysis": [
                            "阅读下面的文言文，回答问题：\n\n学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？\n\n问题：1. 解释文中'说'和'愠'的意思\n2. 这段话表达了孔子怎样的教育思想？\n3. 请将这段话翻译成现代汉语",
                            "阅读下面的诗歌，回答问题：\n\n登高\n杜甫\n风急天高猿啸哀，渚清沙白鸟飞回。\n无边落木萧萧下，不尽长江滚滚来。\n万里悲秋常作客，百年多病独登台。\n艰难苦恨繁霜鬓，潦倒新停浊酒杯。\n\n问题：1. 分析这首诗的意象和意境\n2. 这首诗表达了诗人怎样的思想感情？"
                        ],
                        "comprehensive": [
                            "请完成以下关于《红楼梦》的综合任务：\n1. 简述《红楼梦》的主要情节\n2. 分析贾宝玉的人物形象\n3. 谈谈《红楼梦》的艺术特色"
                        ]
                    }
                }
            },
            "物理": {
                    "topics": ["基础物理概念", "力学基础", "热学初步", "光学现象", "声学知识"],
                        "single_choice": [
                            "声音在以下哪种介质中传播速度最快？",
                            "以下哪个是力的单位？",
                            "光在真空中的传播速度约为多少？"
                        ],
                        "multiple_choice": [
                            "以下哪些是基本物理量？",
                            "以下哪些是力的作用效果？"
                        ],
                        "true_false": [
                            "力是维持物体运动的原因",
                            "声音的传播需要介质",
                            "光沿直线传播"
                        ],
                        "fill_blank": [
                            "牛顿第一定律又称____定律",
                            "声音的三要素是音调、响度和____",
                            "质量的国际单位是____"
                        ],
                        "short_answer": [
                            "请简述牛顿第一定律的内容",
                            "请解释什么是惯性",
                            "请说明声音是如何产生的"
                        ],
                        "case_analysis": [
                            "案例分析：在寒冷的冬天，窗户玻璃上会出现冰花。\n\n问题：1. 冰花出现在窗户的内侧还是外侧？\n2. 这种现象属于什么物态变化？"
                        ],
                        "comprehensive": [
                            "请完成以下任务：\n1. 简述力的三要素\n2. 举例说明力的作用效果\n3. 解释为什么在太空中人会漂浮"
                        ]
                },
                "中级": {
                    "topics": ["牛顿运动定律", "功和能", "电磁学基础", "机械波", "热力学定律"],
                    "question_templates": {
                        "single_choice": [
                            "物体在力F的作用下移动了距离s，力F对物体做功为多少？",
                            "以下哪个是欧姆定律的表达式？",
                            "机械能守恒的条件是什么？"
                        ],
                        "multiple_choice": [
                            "以下哪些是矢量？",
                        ],
                        "true_false": [
                            "摩擦力总是阻碍物体的运动",
                            "动能定理适用于所有力做功的情况",
                        ],
                        "fill_blank": [
                            "功的公式是W = ____",
                            "欧姆定律的表达式是I = ____",
                            "动能的公式是Ek = ____"
                        ],
                        "short_answer": [
                            "请解释楞次定律的内容",
                            "请说明热力学第一定律的含义"
                        "case_analysis": [
                            "案例分析：一辆汽车以10m/s的速度行驶，突然刹车，经过5s后停止。\n\n问题：1. 汽车的加速度是多少？\n2. 刹车过程中汽车行驶的距离是多少？\n3. 请用牛顿运动定律解释刹车过程",
                            "案例分析：一个小球从10m高处自由下落，忽略空气阻力。\n\n问题：1. 小球下落的时间是多少？\n2. 小球落地时的速度是多少？\n3. 请计算小球下落过程中重力做的功"
                        ],
                        "comprehensive": [
                    }
                },
                "高级": {
                    "topics": ["相对论基础", "量子物理初步", "电磁学进阶", "流体力学", "热力学统计"],
                    "question_templates": {
                        "single_choice": [
                            "爱因斯坦相对论的基本假设是什么？",
                            "以下哪个是量子力学的基本方程？",
                            "麦克斯韦方程组描述了什么？"
                        ],
                        "multiple_choice": [
                            "以下哪些现象属于量子效应？",
                            "以下哪些是相对论效应？"
                        ],
                        "true_false": [
                            "光速在所有参考系中都是恒定的",
                            "量子力学中粒子的位置和动量可以同时精确测量",
                            "热力学第二定律指出了熵增加的方向"
                        ],
                        "fill_blank": [
                            "狭义相对论的质能方程是E = ____",
                            "德布罗意波长公式是λ = ____",
                            "热力学第二定律的数学表达式是____"
                        "short_answer": [
                            "请简述狭义相对论的时间膨胀效应",
                            "请解释波粒二象性",
                            "请推导麦克斯韦方程组的微分形式"
                        ],
                        "case_analysis": [
                            "案例分析：考虑相对论效应，一艘飞船以0.8c的速度相对于地球飞行。\n\n问题：1. 飞船上的时钟相对于地球变慢了多少？\n2. 飞船的长度相对于地球收缩了多少？\n3. 请解释相对论中的时间膨胀和长度收缩现象",
                            "案例分析：光电效应实验中，当用频率为ν的光照射金属表面时，产生的光电子最大初动能为Ek。\n\n问题：1. 请用爱因斯坦的光电效应方程解释实验结果\n2. 若增大光的强度，光电子的最大初动能会如何变化？\n3. 若增大光的频率，光电子的最大初动能会如何变化？"
                        ],
                        "comprehensive": [
                            "请完成以下关于电磁学的综合任务：\n1. 简述麦克斯韦方程组的物理意义\n2. 解释电磁波的产生和传播机制\n3. 说明电磁感应现象在日常生活中的应用"
                        ]
                }
            },
            "化学": {
                "初级": {
                    "topics": ["化学基本概念", "元素与化合物", "化学反应", "溶液基础", "常见物质"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是水的化学式？",
                            "氧气的化学符号是什么？",
                            "以下哪个是金属元素？"
                        ],
                        "multiple_choice": [
                            "以下哪些是元素周期表中的碱金属？",
                            "以下哪些是化学反应的基本类型？"
                        ],
                        "true_false": [
                            "原子是化学变化中的最小粒子",
                            "催化剂可以改变反应速率",
                            "所有物质都是由分子构成的"
                        ],
                        "fill_blank": [
                            "水的化学式是____",
                            "氧气的化学符号是____",
                            "元素周期表中共有____个周期"
                        ],
                        "short_answer": [
                            "请简述分子的定义",
                            "请解释什么是化学反应",
                            "请说明元素和化合物的区别"
                        ],
                        "case_analysis": [
                            "案例分析：将一块锌片放入硫酸铜溶液中，观察到锌片表面有红色物质析出，溶液颜色由蓝色变为无色。\n\n问题：1. 这个反应属于什么类型的化学反应？\n2. 写出该反应的化学方程式",
                            "案例分析：将二氧化碳通入澄清石灰水中，观察到石灰水变浑浊。\n\n问题：1. 写出该反应的化学方程式\n2. 若继续通入二氧化碳，浑浊会消失，为什么？"
                        ],
                        "comprehensive": [
                        ]
                    }
                },
                "中级": {
                    "topics": ["化学反应原理", "物质结构", "元素周期律", "化学平衡", "电化学基础"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是酸碱中和反应的产物？",
                            "化学平衡常数K的大小与什么有关？",
                            "原电池的正极发生什么反应？"
                        ],
                        "multiple_choice": [
                            "以下哪些是氧化还原反应？",
                            "以下哪些因素会影响化学平衡？"
                        ],
                        "true_false": [
                            "pH=7的溶液一定是中性溶液",
                            "升高温度会加快所有化学反应的速率",
                            "强电解质在水中完全电离"
                        ],
                        "fill_blank": [
                            "酸碱中和反应的本质是____结合生成水",
                            "化学平衡的特征是____相等",
                            "氧化还原反应的本质是____的转移"
                        ],
                        "short_answer": [
                            "请简述勒夏特列原理",
                            "请解释什么是电解质",
                            "请说明化学平衡常数的意义"
                        ],
                        "case_analysis": [
                            "案例分析：工业合成氨的反应为N2(g) + 3H2(g) ⇌ 2NH3(g) ΔH < 0。\n\n问题：1. 简述影响该反应平衡的因素\n2. 工业上如何选择合适的温度和压强条件？\n3. 催化剂对平衡有何影响？",
                            "案例分析：将等体积的0.1mol/L盐酸和0.1mol/L氢氧化钠溶液混合，测定混合溶液的pH。\n\n问题：1. 混合溶液的pH是多少？\n2. 写出该反应的离子方程式\n3. 若改用等体积的0.1mol/L醋酸和0.1mol/L氢氧化钠溶液混合，pH会有何变化？"
                        ],
                        "comprehensive": [
                    }
                },
                "高级": {
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是烷烃的通式？",
                            "吉布斯自由能变ΔG与反应自发性的关系是什么？",
                        ],
                        "multiple_choice": [
                            "以下哪些是有机化合物的官能团？",
                            "以下哪些是热力学状态函数？"
                        "true_false": [
                            "有机化合物都含有碳元素",
                            "熵增加的反应一定是自发反应",
                            "质谱法可以确定化合物的分子量"
                        ],
                        "fill_blank": [
                            "烷烃的通式是____",
                            "热力学第一定律的数学表达式是____",
                            "pH的定义是____"
                        "short_answer": [
                            "请推导范特霍夫方程",
                            "请说明红外光谱的基本原理"
                        ],
                        "case_analysis": [
                            "案例分析：某有机化合物的分子式为C4H10O，红外光谱显示在3300cm-1处有强宽峰，1H-NMR谱显示有4组峰，面积比为3:3:2:2。\n\n问题：1. 推测该化合物的结构\n2. 解释红外光谱和核磁共振谱的特征峰\n3. 写出该化合物的可能同分异构体",
                        ],
                        "comprehensive": [
                            "请完成以下关于有机化学的综合任务：\n1. 简述有机物的分类方法\n2. 解释什么是官能团\n3. 说明有机合成的基本策略"
                }
            "历史": {
                "初级": {
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是中国古代四大发明之一？",
                        ],
                        "multiple_choice": [
                            "以下哪些是中国古代的朝代？",
                            "以下哪些是第二次世界大战的主要参战国？"
                        "true_false": [
                            "唐太宗是唐朝的第二位皇帝",
                            "辛亥革命发生于1911年"
                        ],
                            "中国历史上第一个统一的中央集权国家是____",
                            "抗日战争胜利于____年"
                        ],
                        "short_answer": [
                            "请解释什么是文艺复兴",
                            "请说明鸦片战争的影响"
                        ],
                            "案例分析：阅读以下材料，回答问题。\n\n材料：14世纪，文艺复兴运动在意大利兴起，强调人文主义，反对封建神学，提倡以人为中心而不是以神为中心。\n\n问题：1. 文艺复兴运动的核心思想是什么？\n2. 文艺复兴运动对欧洲历史产生了什么影响？"
                        ],
                        ]
                    }
                    "topics": ["中国古代政治制度", "世界近代史", "中国近代史", "历史事件分析", "历史人物评价"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是科举制度创立的朝代？",
                            "工业革命最早开始于哪个国家？",
                        "multiple_choice": [
                            "以下哪些事件与第二次工业革命有关？"
                        ],
                        "true_false": [
                            "美国独立战争爆发的原因是英国的殖民压迫",
                        ],
                        "fill_blank": [
                            "中国古代的三省六部制创立于____朝",
                            "工业革命的标志是____的改良",
                        ],
                            "请分析科举制度的影响",
                            "请评价孙中山的历史地位"
                        ],
                        "case_analysis": [
                            "案例分析：阅读以下材料，回答问题。\n\n材料：1911年，辛亥革命爆发，推翻了清朝统治，结束了中国两千多年的封建帝制，建立了中华民国。\n\n问题：1. 辛亥革命的历史背景是什么？\n2. 辛亥革命的主要成果有哪些？\n3. 为什么说辛亥革命是中国近代史上的一次伟大的资产阶级民主革命？"
                        ],
                        "comprehensive": [
                },
                    "question_templates": {
                            "以下哪个事件标志着冷战的开始？",
                            "中国改革开放的总设计师是谁？",
                        ],
                        "multiple_choice": [
                            "以下哪些是冷战时期的国际组织？",
                            "以下哪些因素推动了全球化进程？"
                        "true_false": [
                            "冷战的结束标志着世界格局进入多极化时代",
                            "经济全球化只带来了积极影响"
                        ],
                        "fill_blank": [
                            "中国改革开放始于____年",
                        ],
                            "请分析冷战结束的原因",
                            "请评价中国改革开放的历史意义",
                            "请论述全球化对世界历史发展的影响"
                            "案例分析：阅读以下材料，回答问题。\n\n材料：1947年，杜鲁门主义出台，标志着冷战的开始。1991年，苏联解体，冷战结束。冷战期间，美苏两国进行了长期的军备竞赛，同时也在科技、文化等领域展开了竞争。\n\n问题：1. 冷战的主要原因是什么？\n2. 冷战对世界历史产生了什么影响？\n3. 冷战结束后，世界格局发生了怎样的变化？",
                            "案例分析：阅读以下材料，回答问题。\n\n材料：1978年，中国开始实行改革开放政策，经济快速发展，综合国力不断增强。40多年来，中国的GDP从世界第11位上升到第2位，成为世界第二大经济体。\n\n问题：1. 中国改革开放的主要内容有哪些？\n2. 改革开放对中国社会产生了什么影响？\n3. 中国改革开放的成功经验对其他国家有何启示？"
                        "comprehensive": [
                            "请完成以下关于20世纪世界史的任务：\n1. 分析两次世界大战的异同\n2. 说明冷战的影响\n3. 论述全球化的利弊"
                }
            }

        chinese_words = ["苹果", "香蕉", "橙子", "葡萄", "西瓜", "猫", "狗", "鸟", "鱼", "花",
                        "美丽", "快乐", "聪明", "高大", "红色", "跑", "吃", "写", "读", "唱"]
                        "sun", "moon", "star", "sky", "earth", "ocean", "river", "mountain", "forest", "grassland",
                        "beautiful", "happy", "smart", "tall", "red", "run", "eat", "write", "read", "sing"]
                          "speak": "spoke", "break": "broke", "make": "made", "take": "took", "see": "saw",
                          "drive": "drove", "ride": "rode", "swim": "swam", "give": "gave", "bring": "brought"}
        # 新增物理、化学、历史内容库数据
        physics_data = {
            "fundamental_laws": ["牛顿运动定律", "热力学定律", "电磁学定律", "相对论", "量子力学"],
            "physical_quantities": ["长度", "质量", "时间", "电流", "温度", "物质的量", "发光强度"]
        chemistry_data = {
            "elements": ["氢", "氦", "锂", "铍", "硼", "碳", "氮", "氧", "氟", "氖"],
            "compounds": ["水", "二氧化碳", "氧气", "氮气", "氯化钠", "硫酸", "盐酸", "氢氧化钠"],
            "chemical_reactions": ["化合反应", "分解反应", "置换反应", "复分解反应", "氧化还原反应"],
            "famous_chemists": ["门捷列夫", "拉瓦锡", "道尔顿", "阿伏伽德罗", "居里夫人"]

        history_data = {
            "world_events": ["第一次世界大战", "第二次世界大战", "工业革命", "法国大革命", "美国独立战争"],
        }

        # 生成题目
        for i in range(count):

            # 确定题目类型
            current_type = question_type or random.choice(available_types)
            level_name = target_level.name

            # 获取对应分类和难度的内容库
            category_lib = category_content_libraries.get(category_name, category_content_libraries["数学"])

            content = ""
            options = []

            # 基础难度分数（基于等级）
            base_difficulty = random.uniform(1, 10) if not level_value else level_value * 2.5
            # 根据题目类型调整难度
            type_adjustment = {
                "single_choice": 0.0,
                "multiple_choice": 1.0,
                "true_false": -1.0,

            subject_adjustment = {
                "数学": 0.0,
                "语文": -0.3,
                "物理": 1.0,
                "化学": 0.8,
            }

            # 计算最终难度分数

            difficulty_score = max(1.0, min(10.0, difficulty_score))
            # 处理案例分析题和综合题
                template = random.choice(level_lib["question_templates"][current_type])
                content = template
                explanation = f"这是一道{level_name}难度的{category_name}{current_type.replace('_', ' ')}题"
                options = []
                # 生成随机数字
                num2 = random.randint(1, 20) if level_value <= 2 else random.randint(10, 100)
                # 确保除法有整数结果
                    num2 = 1
                if num1 % num2 != 0:
                    num1 = num2 * random.randint(1, 10)

                if current_type == "single_choice":
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["single_choice"])

                        correct_answer = num1 + num2
                        options = [
                            str(correct_answer - random.randint(1, 5)),
                            str(num1 * num2)
                        ]
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"
                    elif "{num1} - {num2}" in template:
                        options = [
                            str(correct_answer + random.randint(1, 5)),
                            str(correct_answer - random.randint(1, 5)),
                        ]
                        content = template.format(num1=num1, num2=num2)
                        correct_answer = num1 * num2
                        options = [
                            str(correct_answer + random.randint(1, 10)),
                            str(correct_answer - random.randint(1, 10)),
                        ]
                    elif "{num1} ÷ {num2}" in template:
                        correct_answer = num1 // num2
                        options = [
                            str(correct_answer),
                            str(correct_answer - random.randint(1, 5)),
                            str(num1 * num2)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}除以{num2}等于{correct_answer}"
                    elif "偶数" in template:
                        options = [
                            str(even_num),
                            str(even_num + 1),
                            str(even_num + 5)
                        ]
                    elif "奇数" in template:
                        odd_num = random.randint(1, 10) * 2 + 1
                        options = [
                            str(odd_num + 1),
                            str(odd_num + 4)
                        ]
                        content = template
                        answer = str(odd_num)
                    else:
                        # 默认生成加法题
                        correct_answer = num1 + num2
                            str(correct_answer - 1),
                            str(num1 * num2)
                        ]
                        content = f"{num1} + {num2} = ?"
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"

                    # 随机打乱选项
                    random.shuffle(options)

                elif current_type == "multiple_choice":
                    # 生成质数题
                        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
                        non_primes = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18]

                        selected_non_primes = random.sample(non_primes, 3)
                        content = template
                        explanation = f"这是一道{level_lib['topics'][0]}题，质数是大于1的自然数，除了1和它本身没有其他因数。{answer}都是质数"
                    elif "偶数" in template:

                        selected_odds = random.sample(odds, 3)
                        options = [str(e) for e in selected_evens + selected_odds]
                        content = template
                    # 生成倍数题
                    else:
                        base = 3
                        multiples = [base * i for i in range(1, 11)]
                        non_multiples = [i for i in range(1, 31) if i % base != 0]

                        selected_multiples = random.sample(multiples, 3)
                        options = [str(m) for m in selected_multiples + selected_non_multiples]
                        answer = ",".join([str(m) for m in selected_multiples])
                        content = template.format(num=base)
                        explanation = f"这是一道{level_lib['topics'][0]}题，能被{base}整除的数是{base}的倍数。{answer}都是{base}的倍数"
                    # 随机打乱选项
                    random.shuffle(options)

                    # 随机选择模板

                    # 生成判断题

                        if is_true:
                            answer = "true"
                            wrong_sum = sum_val + random.randint(1, 10)
                            content = template.format(num1=num1, num2=num2, sum=wrong_sum)
                            answer = "false"
                    elif "{num1}是偶数" in template:
                        if num1 % 2 == 0:
                            content = template.format(num1=num1)
                            answer = "false"
                            explanation = f"这是一道{level_lib['topics'][0]}题，{num1}不能被2整除，不是偶数"
                    else:  # {num1}是质数
                        is_prime = num1 > 1 and all(num1 % i != 0 for i in range(2, int(num1**0.5) + 1))
                        answer = "true" if is_prime else "false"
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}是{'质数' if is_prime else '合数'}"

                elif current_type == "fill_blank":
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["fill_blank"])

                        content = template.format(num1=num1, num2=num2)
                        answer = str(correct_answer)
                    elif "{num1} × {num2}" in template:
                        correct_answer = num1 * num2
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}乘{num2}等于{correct_answer}"
                        content = template
                        answer = "60"
                        explanation = f"这是一道{level_lib['topics'][0]}题，1小时等于60分钟"
                    else:
                        content = f"{num1} + {num2} = ____"
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"

                    if "请计算：{num1} + {num2} + {num3}" in template:
                        content = template.format(num1=num1, num2=num2, num3=num3)
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{num1+num2}，再加{num3}等于{correct_answer}"
                    elif "请计算：{num1} × {num2} ÷ {num3}" in template:
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}乘{num2}等于{num1*num2}，再除以{num3}等于{correct_answer}"
                    elif "请写出3个偶数" in template:
                        even_nums = [str(random.randint(2, 20) * 2) for _ in range(3)]
                        answer = ", ".join(even_nums)
                    else:

            elif category_name == "英语":
                # 生成英语题目
                if level_value <= 2:  # 初级
                        word_index = random.randint(0, len(chinese_words)-1)
                        chinese_word = chinese_words[word_index]
                        correct_answer = english_words[word_index]
                        # 生成干扰选项
                        distractors = random.sample([w for w in english_words if w != correct_answer], 3)
                        options = [correct_answer] + distractors
                        random.shuffle(options)
                        answer = correct_answer
                        explanation = f"{chinese_word}的英语单词是{correct_answer}"

                        # 生成词汇分类题
                        categories = ["水果", "动物", "自然"]
                        selected_category = random.choice(categories)

                        if selected_category == "水果":
                            fruit_answers = english_words[:5]
                            non_fruits = chinese_words[5:10]
                        elif selected_category == "动物":
                            fruits = chinese_words[5:10]
                            non_fruits = chinese_words[:5]
                            fruits = chinese_words[10:15]
                            fruit_answers = english_words[10:15]

                        # 选择3个正确答案和3个干扰选项
                        selected_fruit_answers = [english_words[chinese_words.index(f)] for f in selected_fruits]
                        selected_non_fruit_answers = [english_words[chinese_words.index(nf)] for nf in selected_non_fruits]

                        options = selected_fruit_answers + selected_non_fruit_answers
                        content = f"Which of the following are {selected_category}?"

                    elif current_type == "true_false":
                        is_true = random.choice([True, False])
                            content = f"'{english_word}' means '{chinese_word}' in Chinese"
                            answer = "true"
                            explanation = f"'{english_word}'的中文意思确实是'{chinese_word}'"
                        else:
                            wrong_index = (word_index + 5) % len(chinese_words)
                            wrong_chinese = chinese_words[wrong_index]
                            content = f"'{english_word}' means '{wrong_chinese}' in Chinese"
                            answer = "false"
                            explanation = f"'{english_word}'的中文意思是'{chinese_word}'，而不是'{wrong_chinese}'"

                    elif current_type == "fill_blank":
                        # 生成词汇填空题
                        word_index = random.randint(0, len(chinese_words)-1)
                        chinese_word = chinese_words[word_index]
                        content = f"The English word for '{chinese_word}' is ____"
                        explanation = f"'{chinese_word}'的英语单词是{correct_answer}"
                    else:  # short_answer
                        word_index = random.randint(0, len(chinese_words)-1)
                        content = f"What is the English word for '{chinese_word}'?"
                        answer = english_words[word_index]
                        explanation = f"{chinese_word}的英语单词是{answer}"

                    if current_type == "single_choice":
                        # 生成动词时态题
                        correct_answer = irregular_verbs[verb]

                            f"{verb}ed",
                            f"{verb}s",
                        ]

                        answer = correct_answer
                        explanation = f"'{verb}'的过去式是不规则变化，正确形式是{correct_answer}"

                    elif current_type == "multiple_choice":
                        correct_verbs = random.sample(list(irregular_verbs.keys()), 3)
                        regular_verbs = [v for v in verbs if v not in irregular_verbs]

                        random.shuffle(options)
                        answer = ",".join(correct_verbs)

                        explanation = f"不规则动词的过去式不遵循一般规则，{', '.join(correct_verbs)}都是不规则动词"

                    elif current_type == "true_false":
                        # 生成动词时态判断题
                        correct_past = irregular_verbs[verb]

                            answer = "true"
                        else:
                            content = f"The past tense of '{verb}' is '{verb}ed'"
                            answer = "false"

                    elif current_type == "fill_blank":
                        correct_past = irregular_verbs[verb]

                        content = f"She ____ to the park yesterday ({verb}的正确形式)"
                        answer = correct_past
                        explanation = f"yesterday表示过去时间，应该使用过去式，'{verb}'的过去式是不规则变化，正确形式是{correct_past}"

                    else:  # short_answer
                        # 生成动词时态简答题
                        verb = random.choice(list(irregular_verbs.keys()))

            elif category_name == "语文":
                    if current_type == "single_choice":
                        # 生成近义词题
                        synonyms = {
                            "美丽": ["漂亮", "好看", "绚丽", "丑陋"],
                            "大": ["巨大", "庞大", "宏大", "小"],
                            "小": ["微小", "渺小", "细小", "大"],
                            "聪明": ["聪慧", "伶俐", "睿智", "愚蠢"]
                        }
                        correct_answer = synonyms[base_word][0]
                        options = synonyms[base_word]
                        random.shuffle(options)
                        content = f"'{base_word}'的近义词是？"
                        answer = correct_answer
                        # 生成词性分类题
                        nouns = ["苹果", "猫", "书", "学校", "太阳"]
                        verbs = ["跑", "吃", "写", "读", "唱"]
                        adjectives = ["美丽", "快乐", "聪明", "高大", "红色"]

                        word_type = random.choice(["名词", "动词", "形容词"])
                        if word_type == "名词":
                            correct_words = nouns
                        elif word_type == "动词":
                            correct_words = verbs
                            wrong_words = nouns + adjectives
                        else:
                            correct_words = adjectives
                            wrong_words = nouns + verbs

                        selected_correct = random.sample(correct_words, 3)
                        selected_wrong = random.sample(wrong_words, 3)
                        answer = ",".join(selected_correct)

                        content = f"以下哪些是{word_type}？"

                    elif current_type == "fill_blank":
                        # 生成古诗词填空题
                        poems = {
                            "举头望明月，____头思故乡。": "低",
                            "春眠不觉晓，处处闻____鸟。": "啼",
                            "夜来风雨声，花落知____少。": "多",
                            "锄禾日当午，汗滴____下土。": "禾"
                        }

                        answer = correct_char
                        explanation = f"这是经典古诗词中的诗句，正确填空是'{correct_char}'"
                    else:  # true_false 或 short_answer
                        # 生成词语词性题
                        nouns = ["苹果", "猫", "书", "学校", "太阳"]
                        verbs = ["跑", "吃", "写", "读", "唱"]

                        is_noun = random.choice([True, False])
                        if is_noun:
                            word = random.choice(nouns)
                            content = f"'{word}'是一个名词"
                            explanation = f"'{word}'表示事物名称，是名词"
                        else:
                            word = random.choice(verbs)
                            content = f"'{word}'是一个名词"
                            answer = "false"

                else:  # 中级或高级
                    if current_type == "single_choice":
                        # 生成修辞手法题
                            "月亮像一个大银盘挂在天空。",
                            "他的眼睛像星星一样明亮。"
                        ]
                        non_metaphor_sentences = [
                            "月亮挂在天空。",
                            "他的眼睛很明亮。"
                        ]

                        is_metaphor = random.choice([True, False])
                            content = random.choice(metaphor_sentences)
                            options = ["比喻", "拟人", "夸张", "排比"]
                            answer = "比喻"
                            explanation = f"这句话使用了比喻的修辞手法，将{content.split('像')[0].strip()}比作{content.split('像')[1].strip()}"
                        else:
                            options = ["比喻", "拟人", "夸张", "没有使用修辞手法"]
                            explanation = f"这句话是普通陈述句，没有使用修辞手法"

                    elif current_type == "multiple_choice":
                        # 生成文学常识题
                        authors = {
                            "鲁迅": ["《狂人日记》", "《阿Q正传》", "《孔乙己》"],
                            "老舍": ["《骆驼祥子》", "《茶馆》", "《四世同堂》"],
                            "曹雪芹": ["《红楼梦》", "《石头记》", "《金陵十二钗》"]
                        }

                        correct_works = authors[author]
                        for other_author, works in authors.items():
                            if other_author != author:
                                wrong_works.extend(works)

                        selected_wrong = random.sample(wrong_works, 3)
                        options = correct_works + selected_wrong
                        answer = ",".join(correct_works)

                        content = f"以下哪些是{author}的作品？"
                        explanation = f"{author}是中国著名作家，代表作包括{', '.join(correct_works)}"
                    elif current_type == "fill_blank":
                        # 生成古诗词填空题（高级）
                        advanced_poems = {
                            "欲穷千里目，更上一____楼。": "层",
                            "不识庐山真面目，只缘身在此____中。": "山",
                            "问渠那得清如许，为有源头活____来。": "水"
                        }

                        content = poem_line.replace(correct_char, "____")
                        answer = correct_char
                        explanation = f"这是经典古诗词中的诗句，正确填空是'{correct_char}'"

                    else:  # true_false 或 short_answer
                        # 生成成语解释题
                        idioms = {
                            "画龙点睛": "比喻说话或写文章时，在关键处用几句话点明实质，使内容生动有力",
                            "守株待兔": "比喻不主动努力，而存万一的侥幸心理，希望得到意外的收获",
                            "亡羊补牢": "比喻出了问题以后想办法补救，可以防止继续受损失",
                            "掩耳盗铃": "比喻自己欺骗自己，明明掩盖不住的事情偏要想法子掩盖"
                        }

                        content = f"请解释成语'{idiom}'的意思"
                        answer = meaning
                        explanation = f"这是一个常见成语，正确解释是{meaning}"

            elif category_name in ["物理", "化学", "历史"]:
                # 生成物理、化学、历史题目
                    if current_type == "single_choice":
                        # 生成物理单选题
                        template = random.choice(level_lib["question_templates"]["single_choice"])
                        if "声音在以下哪种介质中传播速度最快？" in template:
                            content = template
                            options = ["空气", "水", "钢铁", "真空"]
                            answer = "钢铁"
                            explanation = "声音在固体中传播速度最快，钢铁是固体，所以声音在钢铁中传播速度最快"
                        elif "以下哪个是力的单位？" in template:
                            content = template
                            options = ["焦耳", "牛顿", "瓦特", "帕斯卡"]
                            explanation = "力的国际单位是牛顿，符号为N"
                        elif "光在真空中的传播速度约为多少？" in template:
                            content = template
                            answer = "3×10^8 m/s"
                            explanation = "光在真空中的传播速度约为3×10^8 m/s，相当于3×10^5 km/s"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.choice(options)

                    elif current_type == "multiple_choice":
                        # 生成物理多选题
                        template = random.choice(level_lib["question_templates"]["multiple_choice"])
                            content = template
                            options = ["长度", "质量", "时间", "速度"]
                            answer = "长度,质量,时间"
                            explanation = "基本物理量包括长度、质量、时间、电流、温度、物质的量和发光强度"
                        elif "以下哪些是力的作用效果？" in template:
                            content = template
                            options = ["改变物体的形状", "改变物体的运动状态", "改变物体的质量", "改变物体的密度"]
                            answer = "改变物体的形状,改变物体的运动状态"
                            explanation = "力的作用效果包括改变物体的形状和改变物体的运动状态"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.sample(options, 2)
                            answer = ",".join(answer)
                            explanation = f"这是一道{level_name}难度的物理多选题"

                    elif current_type == "true_false":
                        # 生成物理判断题
                        template = random.choice(level_lib["question_templates"]["true_false"])
                            content = template
                            answer = "false"
                        elif "声音的传播需要介质" in template:
                            content = template
                            answer = "true"
                            explanation = "声音的传播需要介质，不能在真空中传播"
                        elif "光沿直线传播" in template:
                            content = template
                            answer = "true"
                            explanation = "在均匀介质中，光沿直线传播"
                        else:
                            content = template
                            answer = random.choice(["true", "false"])

                    elif current_type == "fill_blank":
                        # 生成物理填空题
                        if "牛顿第一定律又称____定律" in template:
                            content = template
                            answer = "惯性"
                            explanation = "牛顿第一定律又称惯性定律，描述了物体保持其运动状态的性质"
                        elif "声音的三要素是音调、响度和____" in template:
                            content = template
                            answer = "音色"
                            explanation = "声音的三要素包括音调、响度和音色"
                        elif "质量的国际单位是____" in template:
                            content = template
                            answer = "千克"
                            explanation = "质量的国际单位是千克，符号为kg"
                        else:
                            content = template
                            answer = "物理量"
                            explanation = f"这是一道{level_name}难度的物理填空题"

                    else:  # short_answer
                        # 生成物理简答题
                        template = random.choice(level_lib["question_templates"]["short_answer"])
                        if "请简述牛顿第一定律的内容" in template:
                            content = template
                            answer = "一切物体在没有受到力的作用时，总保持静止状态或匀速直线运动状态"
                            explanation = "牛顿第一定律又称惯性定律，是经典力学的基本定律之一"
                        elif "请解释什么是惯性" in template:
                            content = template
                            answer = "物体保持静止状态或匀速直线运动状态的性质叫做惯性"
                            explanation = "惯性是物体的固有属性，一切物体都有惯性"
                        elif "请说明声音是如何产生的" in template:
                            content = template
                            answer = "声音是由物体的振动产生的"
                            explanation = "当物体振动时，会引起周围介质的振动，从而产生声波，传播到我们的耳朵中，我们就听到了声音"
                        else:
                            content = template
                            answer = "这是一个物理简答题"
                            explanation = f"这是一道{level_name}难度的物理简答题"

                elif category_name == "化学":
                    if current_type == "single_choice":
                        # 生成化学单选题
                        template = random.choice(level_lib["question_templates"]["single_choice"])
                        if "以下哪个是水的化学式？" in template:
                            content = template
                            options = ["H2O", "CO2", "O2", "NaCl"]
                            answer = "H2O"
                            explanation = "水的化学式是H2O，表示一个水分子由两个氢原子和一个氧原子组成"
                        elif "氧气的化学符号是什么？" in template:
                            content = template
                            options = ["O", "O2", "CO2", "H2O"]
                            answer = "O2"
                            explanation = "氧气是由氧分子组成的，每个氧分子由两个氧原子组成，所以氧气的化学符号是O2"
                        elif "以下哪个是金属元素？" in template:
                            content = template
                            options = ["H", "O", "Fe", "Cl"]
                            answer = "Fe"
                            explanation = "Fe是铁的化学符号，铁是一种金属元素"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.choice(options)
                            explanation = f"这是一道{level_name}难度的化学单选题"

                    elif current_type == "multiple_choice":
                        # 生成化学多选题
                        template = random.choice(level_lib["question_templates"]["multiple_choice"])
                        if "以下哪些是元素周期表中的碱金属？" in template:
                            content = template
                            options = ["Li", "Na", "K", "Ca"]
                            answer = "Li,Na,K"
                            explanation = "碱金属位于元素周期表的第ⅠA族，包括Li（锂）、Na（钠）、K（钾）等"
                        elif "以下哪些是化学反应的基本类型？" in template:
                            content = template
                            options = ["化合反应", "分解反应", "置换反应", "氧化反应"]
                            answer = "化合反应,分解反应,置换反应"
                            explanation = "化学反应的基本类型包括化合反应、分解反应、置换反应和复分解反应"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.sample(options, 2)
                            answer = ",".join(answer)
                            explanation = f"这是一道{level_name}难度的化学多选题"

                    elif current_type == "true_false":
                        # 生成化学判断题
                        template = random.choice(level_lib["question_templates"]["true_false"])
                        if "原子是化学变化中的最小粒子" in template:
                            content = template
                            answer = "true"
                            explanation = "在化学变化中，原子是不可再分的最小粒子"
                        elif "催化剂可以改变反应速率" in template:
                            content = template
                            answer = "true"
                            explanation = "催化剂可以改变反应速率，而本身的质量和化学性质在反应前后不变"
                        elif "所有物质都是由分子构成的" in template:
                            content = template
                            answer = "false"
                            explanation = "物质可以由分子、原子或离子构成"
                        else:
                            content = template
                            answer = random.choice(["true", "false"])
                            explanation = f"这是一道{level_name}难度的化学判断题"

                    elif current_type == "fill_blank":
                        # 生成化学填空题
                        template = random.choice(level_lib["question_templates"]["fill_blank"])
                        if "水的化学式是____" in template:
                            content = template
                            answer = "H2O"
                            explanation = "水的化学式是H2O，表示一个水分子由两个氢原子和一个氧原子组成"
                        elif "氧气的化学符号是____" in template:
                            content = template
                            answer = "O2"
                            explanation = "氧气的化学符号是O2，表示一个氧分子由两个氧原子组成"
                        elif "元素周期表中共有____个周期" in template:
                            content = template
                            answer = "7"
                            explanation = "元素周期表中共有7个周期，横行表示周期"
                        else:
                            content = template
                            answer = "化学物质"
                            explanation = f"这是一道{level_name}难度的化学填空题"

                    else:  # short_answer
                        # 生成化学简答题
                        template = random.choice(level_lib["question_templates"]["short_answer"])
                        if "请简述分子的定义" in template:
                            content = template
                            answer = "分子是保持物质化学性质的最小粒子"
                            explanation = "分子是构成物质的一种基本粒子，同种物质的分子化学性质相同"
                        elif "请解释什么是化学反应" in template:
                            content = template
                            answer = "化学反应是指物质发生变化时生成新物质的过程"
                            explanation = "化学反应的本质是原子的重新组合，生成新的分子或物质"
                        elif "请说明元素和化合物的区别" in template:
                            content = template
                            answer = "元素是具有相同质子数的一类原子的总称，化合物是由不同种元素组成的纯净物"
                            explanation = "元素是纯净物的基本组成单位，化合物是由两种或两种以上元素组成的纯净物"
                        else:
                            content = template
                            answer = "这是一个化学简答题"
                            explanation = f"这是一道{level_name}难度的化学简答题"

                elif category_name == "历史":
                    if current_type == "single_choice":
                        # 生成历史单选题
                        if "秦始皇统一中国的时间是哪一年？" in template:
                            options = ["公元前221年", "公元前206年", "公元221年", "公元206年"]
                            explanation = "秦始皇于公元前221年统一六国，建立了中国历史上第一个统一的中央集权国家"
                            content = template
                            options = ["造纸术", "火药", "印刷术", "以上都是"]
                            answer = "以上都是"
                            content = template
                            answer = "1914年"
                            explanation = "第一次世界大战爆发于1914年，结束于1918年"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.choice(options)

                        if "以下哪些是中国古代的朝代？" in template:
                            content = template
                            options = ["夏", "商", "周", "秦"]
                            explanation = "夏、商、周、秦都是中国古代的朝代"
                            content = template
                            answer = "美国,德国,日本,意大利"
                            explanation = "第二次世界大战的主要参战国包括同盟国（如美国、英国、苏联等）和轴心国（如德国、日本、意大利等）"
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = ",".join(answer)
                            explanation = f"这是一道{level_name}难度的历史多选题"
                    elif current_type == "true_false":
                        # 生成历史判断题
                        template = random.choice(level_lib["question_templates"]["true_false"])
                        if "唐太宗是唐朝的第二位皇帝" in template:
                            content = template
                            answer = "true"
                            explanation = "唐太宗李世民是唐朝的第二位皇帝，开创了贞观之治"
                        elif "哥伦布发现美洲新大陆是在15世纪" in template:
                            content = template
                            answer = "true"
                        elif "辛亥革命发生于1911年" in template:
                            answer = "true"
                            explanation = "辛亥革命发生于1911年，推翻了清朝统治，结束了中国两千多年的封建帝制"
                        else:
                            content = template
                            answer = random.choice(["true", "false"])
                            explanation = f"这是一道{level_name}难度的历史判断题"
                    elif current_type == "fill_blank":
                        # 生成历史填空题
                        template = random.choice(level_lib["question_templates"]["fill_blank"])
                        if "中国历史上第一个统一的中央集权国家是____" in template:
                            content = template
                            explanation = "秦始皇统一六国后，建立了中国历史上第一个统一的中央集权国家——秦朝"
                        elif "四大发明包括造纸术、印刷术、火药和____" in template:
                            content = template
                            answer = "指南针"
                            explanation = "中国古代四大发明包括造纸术、印刷术、火药和指南针"
                            content = template
                            answer = "1945"
                            explanation = "中国人民抗日战争胜利于1945年，日本宣布无条件投降"
                        else:
                            content = template
                            answer = "历史事件"
                            explanation = f"这是一道{level_name}难度的历史填空题"
                    else:  # short_answer
                        # 生成历史简答题
                        template = random.choice(level_lib["question_templates"]["short_answer"])
                        if "请简述秦始皇的主要功绩" in template:
                            content = template
                            answer = "秦始皇统一六国，建立了中国历史上第一个统一的中央集权国家，统一文字、货币、度量衡，修建长城等"
                            explanation = "秦始皇是中国历史上的重要人物，其统一措施对中国历史产生了深远影响"
                        elif "请解释什么是文艺复兴" in template:
                            content = template
                            answer = "文艺复兴是14-16世纪起源于意大利的一场思想文化运动，强调人文主义，反对封建神学，促进了欧洲文化的繁荣"
                            explanation = "文艺复兴是欧洲近代史上的重要转折点，推动了欧洲从中世纪向近代社会的过渡"
                        elif "请说明鸦片战争的影响" in template:
                            content = template
                            answer = "鸦片战争是中国近代史的开端，中国开始沦为半殖民地半封建社会，被迫签订了不平等条约，中国的社会性质发生了根本变化"
                            explanation = "鸦片战争打破了中国闭关锁国的局面，开启了中国近代百年屈辱史"
                        else:
                            content = template
                            answer = "这是一个历史简答题"
                            explanation = f"这是一道{level_name}难度的历史简答题"

            else:  # 其他分类
                # 生成通用题目
                if current_type == "single_choice":
                    content = f"{category_name}相关问题：以下哪个选项是正确的？"
                    options = ["选项A", "选项B", "选项C", "选项D"]
                    explanation = f"这是一道{level_name}难度的{category_name}单选题"
                elif current_type == "multiple_choice":
                    answer = "选项A,选项B"
                    options = ["选项A", "选项B", "选项C", "选项D"]
                    explanation = f"这是一道{level_name}难度的{category_name}多选题"
                elif current_type == "true_false":
                    content = f"{category_name}相关陈述：这是一个正确的陈述"
                    answer = "true"
                    explanation = f"这是一道{level_name}难度的{category_name}判断题"
                elif current_type == "fill_blank":
                    content = f"{category_name}相关问题：____是这个领域的重要概念"
                    answer = "关键概念"
                    explanation = f"这是一道{level_name}难度的{category_name}填空题"
                else:
                    content = f"{category_name}相关问题：请简述{level_name}难度的相关内容"
                    answer = "相关内容的简述"
                    explanation = f"这是一道{level_name}难度的{category_name}简答题"

            # 添加标签
            tags.append(category_name)
            tags.append(level_name)
            tags.append(current_type)
            tags.append(level_lib['topics'][0])  # 添加主题标签

            # 创建题目对象
            question = self.create_question(
                content=content,
                answer=answer,
                explanation=explanation,
                category_id=target_category.id,
                language_id=target_language.id,
                level_id=target_level.id,
                question_type=current_type,
                options=options,
                difficulty_score=difficulty_score,
                usage_count=0,
                correct_rate=None
            )


        return generated_questions

    def generate_question_by_ai(self, prompt: str = None, category_name: str = None,
                              level_name: str = None, question_type: str = None) -> Optional[Question]:
        使用AI生成单个题目

        Args:
            prompt: 生成题目的提示词
            category_name: 题目分类名称
            question_type: 题目类型

        Returns:
        try:
            # 获取分类、语种和等级信息
            categories = self.get_all_categories()
            category_id = categories[0].id if categories else 1
                # 查找对应分类
                for cat in categories:
                    if cat.name == category_name:
                        category_id = cat.id

            language_id = languages[0].id if languages else 1

            level_value = 1
                # 查找对应等级
                for lvl in levels:
                    if lvl.name == level_name:
                        break
            # 生成更智能的提示词
                # 根据分类、难度和题型生成提示词
                prompt = f"生成一道{level_name if level_name else '中级'}难度的{category_name if category_name else '数学'}题目，"
                prompt += f"题目类型为{question_type if question_type else '单选题'}，"
                prompt += "包含题目内容、答案和详细解析。题目内容要清晰明确，答案要准确，解析要详细易懂。"
                prompt += "确保题目具有一定的挑战性和教育价值。"

            # 目前使用增强的模拟数据，生成更真实的题目
            import random

            # 生成更智能的题目
            if category_name == "数学" or not category_name:
                # 生成数学题目
                if level_value <= 2:
                    # 初级或中级数学题
                    num1 = random.randint(1, 50)
                    operation = random.choice(["+", "-", "×", "÷"])

                    if operation == "+":
                        result = num1 + num2
                        question_answer = str(result)
                        question_explanation = f"这是一道简单的加法题，{num1}加上{num2}等于{result}"
                        result = num1 - num2
                        question_content = f"计算：{num1} - {num2} = ?"
                        question_answer = str(result)
                    elif operation == "×":
                        result = num1 * num2
                        question_content = f"计算：{num1} × {num2} = ?"
                        question_explanation = f"这是一道简单的乘法题，{num1}乘以{num2}等于{result}"
                    else:  # ÷
                        # 确保能整除
                        num2 = random.randint(1, 10)
                        num1 = num2 * random.randint(1, 20)
                        result = num1 // num2
                        question_content = f"计算：{num1} ÷ {num2} = ?"
                        question_answer = str(result)
                        question_explanation = f"这是一道简单的除法题，{num1}除以{num2}等于{result}"
                else:
                    # 高级数学题
                    a = random.randint(1, 10)
                    b = random.randint(1, 10)
                    c = random.randint(1, 10)
                    question_content = f"求解二次方程：{a}x² + {b}x + {c} = 0"
                    # 计算判别式
                    delta = b**2 - 4*a*c
                    if delta > 0:
                        x1 = (-b + delta**0.5) / (2*a)
                        x2 = (-b - delta**0.5) / (2*a)
                        question_answer = f"x1={x1:.2f}, x2={x2:.2f}"
                        question_explanation = f"这是一道二次方程求解题。判别式Δ={delta} > 0，所以有两个不同的实数根：x1=(-b+√Δ)/(2a)={x1:.2f}，x2=(-b-√Δ)/(2a)={x2:.2f}"
                    elif delta == 0:
                        x = -b / (2*a)
                        question_answer = f"x={x:.2f}"
                        question_explanation = f"这是一道二次方程求解题。判别式Δ={delta} = 0，所以有一个重根：x=-b/(2a)={x:.2f}"
                    else:
                        question_answer = "无实数根"
                        question_explanation = f"这是一道二次方程求解题。判别式Δ={delta} < 0，所以该方程无实数根"

            elif category_name == "英语":
                # 生成英语题目
                if level_value <= 2:
                    # 初级英语题
                    words = {
                        "apple": "苹果",
                        "banana": "香蕉",
                        "cat": "猫",
                        "dog": "狗",
                        "book": "书"
                    }
                    word, chinese_meaning = random.choice(list(words.items()))
                    question_content = f"What is the Chinese meaning of '{word}'?"
                    question_answer = chinese_meaning
                    question_explanation = f"'word'的中文意思是'{chinese_meaning}'"
                else:
                    # 高级英语题
                        ("present perfect", "I ____ (study) English for 5 years.", "have studied"),
                        ("future perfect", "By next year, I ____ (live) here for 10 years.", "will have lived")
                    ]
                    tense_name, sentence, correct_answer = random.choice(tenses)
                    question_content = f"Fill in the blank with the correct form of the verb in brackets (using {tense_name} tense): {sentence}"
                    question_answer = correct_answer
                    question_explanation = f"这是一道关于{tense_name}时态的题目。{tense_name}的结构是'{tense_name}结构'，所以正确答案是'{correct_answer}'"

            elif category_name == "语文":
                # 生成语文题目
                if level_value <= 2:
                    # 初级语文题
                    idioms = {
                        "画龙点睛": "比喻在关键地方简明扼要地点明要旨，使内容生动传神",
                    idiom, meaning = random.choice(list(idioms.items()))
                    question_explanation = f"'画龙点睛'是一个常用成语，意思是{meaning}"
                else:
                    # 高级语文题
                    poems = {
                        "床前明月光，疑是地上霜。": "李白《静夜思》",
                        "春眠不觉晓，处处闻啼鸟。": "孟浩然《春晓》",
                        "举头望明月，低头思故乡。": "李白《静夜思》"
                    }
                    poem_line, author = random.choice(list(poems.items()))
                    question_content = f"请说出诗句'{poem_line}'的作者和出处"
                    question_answer = author
                    question_explanation = f"这句诗出自{author}，是中国古代文学中的经典诗句"

            else:
                # 其他学科
                question_answer = f"{category_name}相关答案"
                question_explanation = f"这是一道关于{category_name}的题目，答案是{question_answer}"
            # 生成题目选项（如果是选择题）
            options = []
                # 生成选项
                options = [question_answer]
                # 生成干扰选项
                    if category_name == "数学" or not category_name:
                        # 数学题干扰选项
                        if level_value <= 2:
                        else:
                    else:
                        # 其他学科干扰选项
                        distractor = f"干扰选项{random.randint(1, 100)}"
                    options.append(distractor)
                random.shuffle(options)

            # 确定题目类型
            final_question_type = question_type if question_type else "short_answer"

            # 生成标签
            tags = [category_name if category_name else "数学",
                   level_name if level_name else "中级",

            # 生成难度分数
            difficulty_score = level_value * 2.5 if level_value else 5.0

            # 创建题目
            question = self.create_question(
                content=question_content,
                answer=question_answer,
                explanation=question_explanation,
                category_id=category_id,
                language_id=language_id,
                level_id=level_id,
                question_type=final_question_type,
                options=options,
                tags=tags,
                difficulty_score=difficulty_score
            )

            logger.info("AI生成题目成功")
            logger.error(f"AI生成题目失败: {str(e)}")
            return None
                                level_name: str = None, question_type: str = None) -> List[Question]:
        使用AI批量生成题目

        Args:
            count: 生成题目的数量
            category_name: 题目分类名称
            question_type: 题目类型

        Returns:
        generated_questions = []
        for _ in range(count):
            question = self.generate_question_by_ai(
                category_name=category_name,
                level_name=level_name,
                question_type=question_type
            )
            if question:
                generated_questions.append(question)

        logger.info(f"使用AI批量生成了 {len(generated_questions)} 道题目")
        return generated_questions


# 创建全局题库管理器实例
question_manager = QuestionManager()
