# -*- coding: utf-8 -*-
"""
题库数据模型
包括题目、分类、语种和等级的数据库模型定义
"""

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
        self.id = id
        self.name = name
        self.code = code
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or datetime.now(UTC).isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class QuestionLevel:
    """题库等级模型"""
    
    def __init__(self, id: int = None, name: str = None, level: int = None, description: str = None,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.name = name
        self.level = level
        self.description = description
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or datetime.now(UTC).isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Question:
    """题目模型"""
    
    def __init__(self, id: int = None, content: str = None, answer: str = None, explanation: str = None,
                 category_id: int = None, language_id: int = None, level_id: int = None,
                 question_type: str = "single_choice", options: list = None,
                 tags: list = None, difficulty_score: float = None,
                 discrimination_index: float = None, usage_count: int = 0,
                 correct_rate: float = None, audio_url: str = None, image_url: str = None,
                 video_url: str = None, time_limit: int = None, score: int = None,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.content = content
        self.answer = answer
        self.explanation = explanation
        self.category_id = category_id
        self.language_id = language_id
        self.level_id = level_id
        self.question_type = question_type  # single_choice, multiple_choice, true_false, fill_blank, short_answer, listening, case_analysis, comprehensive, translation, essay, matching, ordering, image_based, drag_drop, gap_filling, speaking, reading, debate_topic, presentation_topic
        self.options = options or []  # 选择题选项列表
        self.tags = tags or []  # 题目标签
        self.difficulty_score = difficulty_score  # 难度分数(0-10)
        self.discrimination_index = discrimination_index  # 区分度(0-1)
        self.usage_count = usage_count  # 使用次数
        self.correct_rate = correct_rate  # 正确率(0-1)
        self.audio_url = audio_url  # 听力题音频URL
        self.image_url = image_url  # 图片题图片URL
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
            'category_id': self.category_id,
            'language_id': self.language_id,
            'level_id': self.level_id,
            'question_type': self.question_type,
            'options': self.options,
            'tags': self.tags,
            'difficulty_score': self.difficulty_score,
            'discrimination_index': self.discrimination_index,
            'usage_count': self.usage_count,
            'correct_rate': self.correct_rate,
            'audio_url': self.audio_url,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'time_limit': self.time_limit,
            'score': self.score,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    # 静态方法，转发到question_manager实例
    @staticmethod
    def get_by_id(question_id):
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
        language_id_map = {'japanese': 1, 'english': 2}
        language_id = language_id_map.get(subject)
        
        questions = question_manager.get_questions(language_id=language_id, limit=1000)
        return len(questions)
    
    @staticmethod
    def update_question_usage(question_id, accuracy):
        """更新题目使用情况"""
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
            # 保存更新
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
        return False
    
    @staticmethod
    def create_table():
        """创建题目表"""
        # 这个方法实际上不需要实现，因为表结构已经在QuestionManager中处理
        pass
    
    @staticmethod
    def get_questions_by_filters(**kwargs):
        """根据过滤条件获取题目"""
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


class QuestionManager:
    """题库管理器"""
    
    def __init__(self):
        # 使用数据库管理器，不再需要直接管理数据库连接
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表结构"""
        try:
            logger.info("开始创建数据库表结构...")
            
            # 创建题目分类表
            logger.info("创建题目分类表...")
            create_category_table_sql = '''
            CREATE TABLE IF NOT EXISTS question_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            '''
            logger.debug(f"执行SQL: {create_category_table_sql}")
            db_manager.execute(create_category_table_sql)
            logger.info("题目分类表创建成功")
            
            # 创建题目语种表
            logger.info("创建题目语种表...")
            create_language_table_sql = '''
            CREATE TABLE IF NOT EXISTS question_languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            '''
            logger.debug(f"执行SQL: {create_language_table_sql}")
            db_manager.execute(create_language_table_sql)
            logger.info("题目语种表创建成功")
            
            # 创建题目等级表
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
            )
            '''
            logger.debug(f"执行SQL: {create_question_table_sql}")
            db_manager.execute(create_question_table_sql)
            logger.info("题目表创建成功")
            
            # 插入默认数据
            logger.info("插入默认数据...")
            self._insert_default_data()
            
            logger.info("数据库表结构创建成功")
        except Exception as e:
            logger.error(f"创建数据库表结构失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _insert_default_data(self):
        """插入默认数据"""
        try:
            # 检查是否已有数据
            categories = self.get_all_categories()
            if not categories:
                # 插入默认分类
                self.create_category('默认分类', '默认题目分类')
            
            languages = self.get_all_languages()
            if not languages:
                # 插入默认语种
                self.create_language('日语', 'ja')
                self.create_language('英语', 'en')
                self.create_language('中文', 'zh')
            
            levels = self.get_all_levels()
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
            'description': description,
            'created_at': now,
            'updated_at': now
        }
        
        category_id = db_manager.insert('question_categories', data)
        
        if category_id:
            return QuestionCategory(id=category_id, name=name, description=description, created_at=now, updated_at=now)
        return None
    
    def get_category(self, category_id: int) -> Optional[QuestionCategory]:
        """获取分类"""
        query = 'SELECT id, name, description, created_at, updated_at FROM question_categories WHERE id = ?'
        row = db_manager.fetch_one(query, (category_id,))
        
        if row:
            # 确保返回的是元组格式
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
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            else:
                categories.append(QuestionCategory(*row))
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
                    code=row['code'],
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
            'name': name,
            'level': level,
            'description': description,
            'created_at': now,
            'updated_at': now
        }
        
        level_id = db_manager.insert('question_levels', data)
        
        if level_id:
            return QuestionLevel(id=level_id, name=name, level=level, description=description, created_at=now, updated_at=now)
        return None
    
    def get_level(self, level_id: int) -> Optional[QuestionLevel]:
        """获取等级"""
        query = 'SELECT id, name, level, description, created_at, updated_at FROM question_levels WHERE id = ?'
        row = db_manager.fetch_one(query, (level_id,))
        
        if row:
            # 确保返回的是元组格式
            if isinstance(row, dict):
                return QuestionLevel(
                    id=row['id'],
                    name=row['name'],
                    level=row['level'],
                    description=row['description'],
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
                levels.append(QuestionLevel(
                    id=row['id'],
                    name=row['name'],
                    level=row['level'],
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            else:
                levels.append(QuestionLevel(*row))
        return levels
    
    # 题目管理
    def create_question(self, content: str, answer: str, explanation: str = None,
                       category_id: int = None, language_id: int = None, level_id: int = None,
                       question_type: str = "single_choice", options: list = None, tags: list = None,
                       difficulty_score: float = None, discrimination_index: float = None,
                       usage_count: int = 0, correct_rate: float = None, audio_url: str = None,
                       image_url: str = None, video_url: str = None, time_limit: int = None, score: int = None) -> Question:
        """创建题目"""
        now = datetime.now(UTC).isoformat()
        
        # 构建数据字典
        data = {
            'content': content,
            'answer': answer,
            'explanation': explanation,
            'category_id': category_id,
            'language_id': language_id,
            'level_id': level_id,
            'type': question_type,
            'question_type': question_type,
            'difficulty_score': difficulty_score,
            'discrimination_index': discrimination_index,
            'usage_count': usage_count,
            'correct_rate': correct_rate,
            'audio_url': audio_url,
            'image_url': image_url,
            'video_url': video_url,
            'time_limit': time_limit,
            'score': score,
            'created_at': now,
            'updated_at': now
        }
        
        # 插入数据
        question_id = db_manager.insert('questions', data)
        
        if question_id:
            # 处理选项
            if options:
                for index, option_text in enumerate(options):
                    db_manager.execute(
                        'INSERT INTO question_options (question_id, option_text, option_index) VALUES (?, ?, ?)',
                        (question_id, option_text, index)
                    )
            
            # 处理标签
            if tags:
                for tag_name in tags:
                    # 查找或创建标签
                    tag = db_manager.fetch_one('SELECT id FROM question_tags WHERE tag_name = ?', (tag_name,))
                    if not tag:
                        db_manager.execute('INSERT INTO question_tags (tag_name) VALUES (?)', (tag_name,))
                        tag = db_manager.fetch_one('SELECT last_insert_rowid()')
                        tag_id = tag['last_insert_rowid()'] if isinstance(tag, dict) else tag[0]
                    else:
                        tag_id = tag['id'] if isinstance(tag, dict) else tag[0]
                    
                    # 关联标签
                    db_manager.execute(
                        'INSERT OR IGNORE INTO question_tag_relations (question_id, tag_id) VALUES (?, ?)',
                        (question_id, tag_id)
                    )
            
            return Question(id=question_id, content=content, answer=answer, explanation=explanation,
                           category_id=category_id, language_id=language_id, level_id=level_id,
                           question_type=question_type, options=options or [], tags=tags or [],
                           difficulty_score=difficulty_score, discrimination_index=discrimination_index,
                           usage_count=usage_count, correct_rate=correct_rate, audio_url=audio_url,
                           image_url=image_url, video_url=video_url, time_limit=time_limit, score=score,
                           created_at=now, updated_at=now)
        return None
    
    def get_question(self, question_id: int) -> Optional[Question]:
        """获取题目"""
        # 构建查询语句，包含所有可能的字段
        query = '''
        SELECT id, content, answer, explanation, category_id, language_id, level_id, 
               question_type, difficulty_score, discrimination_index, 
               usage_count, correct_rate, audio_url, image_url, video_url, time_limit, score, 
               created_at, updated_at 
        FROM questions WHERE id = ?
        '''
        
        row = db_manager.fetch_one(query, (question_id,))
        
        if row:
            # 解析字段
            if isinstance(row, dict):
                question_data = {
                    'id': row['id'],
                    'content': row['content'],
                    'answer': row['answer'],
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
                (question_id,)
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
                (question_id,)
            )
            question_data['tags'] = [tag['tag_name'] if isinstance(tag, dict) else tag[0] for tag in tags]
            
            return Question(**question_data)
        return None
    
    def check_question_duplicate(self, content: str, language_id: int, level_id: int,
                                threshold: float = 0.9) -> bool:
        """
        检查题目是否重复
        
        Args:
            content: 题目内容
            language_id: 语种ID
            level_id: 等级ID
            threshold: 相似度阈值
            
        Returns:
            bool: 是否重复
        """
        # 首先检查完全相同的内容
        query = '''
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
                return True
        
        return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            float: 相似度 (0-1)
        """
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
        FROM questions WHERE 1=1
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
            params.append(difficulty_max)
        if correct_rate_min is not None:
            query += ' AND correct_rate >= ?'
            params.append(correct_rate_min)
        if correct_rate_max is not None:
            query += ' AND correct_rate <= ?'
            params.append(correct_rate_max)
        
        # 标签过滤
        if tags:
            for tag in tags:
                query += " AND id IN (SELECT question_id FROM question_tag_relations qtr JOIN question_tags qt ON qtr.tag_id = qt.id WHERE qt.tag_name = ?)"
                params.append(tag)
        
        query += ' ORDER BY id LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        rows = db_manager.fetch_all(query, params)
        
        questions = []
        for row in rows:
            # 解析字段
            if isinstance(row, dict):
                question_data = {
                    'id': row['id'],
                    'content': row['content'],
                    'answer': row['answer'],
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
        data = {
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
            'video_url': question.video_url,
            'time_limit': question.time_limit,
            'score': question.score,
            'updated_at': question.updated_at
        }
        
        # 执行更新
        success = db_manager.update('questions', data, 'id = ?', (question_id,))
        
        if success:
            # 更新选项
            if 'options' in kwargs:
                # 删除旧选项
                db_manager.execute('DELETE FROM question_options WHERE question_id = ?', (question_id,))
                # 添加新选项
                if kwargs['options']:
                    for index, option_text in enumerate(kwargs['options']):
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
                        db_manager.execute(
                            'INSERT OR IGNORE INTO question_tag_relations (question_id, tag_id) VALUES (?, ?)',
                            (question_id, tag_id)
                        )
            
            return question
        return None
    
    def delete_question(self, question_id: int) -> bool:
        """删除题目"""
        success = db_manager.delete('questions', 'id = ?', (question_id,))
        return success
    
    def batch_delete_questions(self, question_ids: List[int]) -> bool:
        """
        批量删除题目
        
        Args:
            question_ids: 要删除的题目ID列表
            
        Returns:
            是否删除成功
        """
        if not question_ids:
            return True
        
        # 构建删除语句
        placeholders = ','.join(['?'] * len(question_ids))
        query = f'DELETE FROM questions WHERE id IN ({placeholders})'
        
        # 执行删除
        cursor, success = db_manager.execute(query, question_ids)
        if success and cursor:
            # 对于批量删除，需要获取影响的行数
            # 注意：这里的cursor可能是模拟的，需要检查
            if hasattr(cursor, 'rowcount'):
                affected_rows = cursor.rowcount
            else:
                # 如果无法获取rowcount，假设成功
                affected_rows = len(question_ids)
            logger.info(f"批量删除了 {affected_rows} 道题目")
            return affected_rows > 0
        return False
    
    def batch_update_questions(self, updates: List[dict]) -> int:
        """
        批量更新题目
        
        Args:
            updates: 更新数据列表，每个元素包含id和要更新的字段
            
        Returns:
            更新成功的题目数量
        """
        if not updates:
            return 0
        
        success_count = 0
        
        for update in updates:
            try:
                question_id = update.pop('id')
                
                # 执行更新
                success = db_manager.update('questions', update, 'id = ?', (question_id,))
                if success:
                    success_count += 1
            except Exception as e:
                logger.error(f"更新题目 {update.get('id')} 失败: {str(e)}")
        
        logger.info(f"批量更新了 {success_count} 道题目")
        return success_count
    

    
    def analyze_question_difficulty(self, question_id: int) -> float:
        """
        分析题目难度
        
        Args:
            question_id: 题目ID
            
        Returns:
            难度分数(0-10)
        """
        # 这里实现题目难度分析逻辑
        # 实际项目中应基于题目使用情况、正确率等数据计算
        import random
        return round(random.uniform(1.0, 10.0), 2)
    
    def analyze_question_discrimination(self, question_id: int) -> float:
        """
        分析题目区分度
        
        Args:
            question_id: 题目ID
            
        Returns:
            区分度(0-1)
        """
        # 这里实现题目区分度分析逻辑
        # 实际项目中应基于高分组和低分组的正确率差异计算
        import random
        return round(random.uniform(0.0, 1.0), 3)
    
    def generate_question_bank_report(self) -> dict:
        """
        生成题库报告
        
        Returns:
            题库报告数据
        """
        # 统计总题目数
        total_questions = db_manager.fetch_scalar('SELECT COUNT(*) FROM questions')
        
        # 按题型统计
        rows = db_manager.fetch_all('SELECT question_type, COUNT(*) FROM questions GROUP BY question_type')
        questions_by_type = {row[0]: row[1] for row in rows}
        
        # 按难度统计
        rows = db_manager.fetch_all('SELECT level_id, COUNT(*) FROM questions GROUP BY level_id')
        questions_by_level = {row[0]: row[1] for row in rows}
        
        # 按分类统计
        rows = db_manager.fetch_all('SELECT category_id, COUNT(*) FROM questions GROUP BY category_id')
        questions_by_category = {row[0]: row[1] for row in rows}
        
        # 按语种统计
        rows = db_manager.fetch_all('SELECT language_id, COUNT(*) FROM questions GROUP BY language_id')
        questions_by_language = {row[0]: row[1] for row in rows}
        
        return {
            'total_questions': total_questions,
            'questions_by_type': questions_by_type,
            'questions_by_level': questions_by_level,
            'questions_by_category': questions_by_category,
            'questions_by_language': questions_by_language,
            'generated_at': datetime.now(UTC).isoformat()
        }
    
    def search_questions(self, keyword: str, category_id: int = None, language_id: int = None, 
                        level_id: int = None, question_type: str = None) -> List[Question]:
        """
        搜索题目
        
        Args:
            keyword: 搜索关键词
            category_id: 分类ID
            language_id: 语种ID
            level_id: 等级ID
            question_type: 题目类型
            
        Returns:
            匹配的题目列表
        """
        # 构建查询语句，包含所有可能的字段
        query = '''
        SELECT id, content, answer, explanation, category_id, language_id, level_id, 
               question_type, difficulty_score, discrimination_index, 
               usage_count, correct_rate, audio_url, image_url, video_url, time_limit, score, 
               created_at, updated_at 
        FROM questions 
        WHERE content LIKE ? OR answer LIKE ? OR explanation LIKE ?
        '''
        params = [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']
        
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
        
        rows = db_manager.fetch_all(query, params)
        
        questions = []
        for row in rows:
            # 解析字段
            if isinstance(row, dict):
                question_data = {
                    'id': row['id'],
                    'content': row['content'],
                    'answer': row['answer'],
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
        """
        获取热门标签
        
        Args:
            limit: 返回数量限制
            
        Returns:
            热门标签列表
        """
        # 从关联表中获取标签统计
        query = '''
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
        """
        评估题目质量
        
        Args:
            question_id: 题目ID
            
        Returns:
            题目质量评估结果
        """
        question = self.get_question(question_id)
        if not question:
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
        
        # 2. 基于区分度评估
        if question.discrimination_index is not None:
            if question.discrimination_index >= 0.3:
                # 区分度良好
                quality_score += 3
            else:
                # 区分度不佳
                quality_score += 1
                feedback.append("题目区分度不佳")
        else:
            # 没有区分度数据
            quality_score += 1
            feedback.append("缺少区分度数据")
        
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
            feedback.append("题目使用次数不足")
        
        # 4. 基于难度分数评估
        if question.difficulty_score is not None:
            if 3 <= question.difficulty_score <= 7:
                # 难度适中
                quality_score += 2
            elif question.difficulty_score < 3:
                # 难度偏低
                quality_score += 1
                feedback.append("题目难度分数偏低")
            else:
                # 难度偏高
                quality_score += 1
                feedback.append("题目难度分数偏高")
        else:
            # 没有难度分数
            quality_score += 1
            feedback.append("缺少难度分数")
        
        # 生成质量等级
        if quality_score >= 12:
            quality_level = "优秀"
        elif quality_score >= 8:
            quality_level = "良好"
        elif quality_score >= 5:
            quality_level = "一般"
        else:
            quality_level = "较差"
        
        return {
            "question_id": question_id,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "feedback": feedback,
            "metrics": {
                "correct_rate": question.correct_rate,
                "discrimination_index": question.discrimination_index,
                "usage_count": question.usage_count,
                "difficulty_score": question.difficulty_score
            }
        }
    
    def optimize_question_quality(self, question_id: int) -> bool:
        """
        优化题目质量
        
        Args:
            question_id: 题目ID
            
        Returns:
            是否优化成功
        """
        try:
            question = self.get_question(question_id)
            if not question:
                return False
            
            # 获取质量评估结果
            quality_eval = self.evaluate_question_quality(question_id)
            
            # 根据评估结果进行优化
            updates = {}
            
            # 优化难度分数
            if "题目难度过高" in quality_eval["feedback"] and question.difficulty_score:
                updates["difficulty_score"] = max(1.0, question.difficulty_score - 1.5)
            elif "题目难度过低" in quality_eval["feedback"] and question.difficulty_score:
                updates["difficulty_score"] = min(10.0, question.difficulty_score + 1.5)
            
            # 如果缺少数据，增加使用次数（通过调整权重）
            if "缺少足够的答题数据" in quality_eval["feedback"]:
                # 可以在这里添加逻辑，例如调整题目在生成试卷时的权重
                pass
            
            # 如果有更新，保存到数据库
            if updates:
                self.update_question(question_id, **updates)
            
            logger.info(f"优化题目 {question_id} 质量，评估结果: {quality_eval['quality_level']}")
            return True
        except Exception as e:
            logger.error(f"优化题目 {question_id} 质量失败: {str(e)}")
            return False
    
    def batch_optimize_questions(self, limit: int = 100) -> dict:
        """
        批量优化题目质量
        
        Args:
            limit: 优化题目数量限制
            
        Returns:
            优化结果
        """
        try:
            # 获取所有题目
            questions = self.get_questions(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for question in questions:
                if self.optimize_question_quality(question.id):
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"批量优化完成，成功: {success_count}，失败: {failed_count}")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total_questions": len(questions)
            }
        except Exception as e:
            logger.error(f"批量优化题目质量失败: {str(e)}")
            return {
                "success_count": 0,
                "failed_count": 0,
                "total_questions": 0,
                "error": str(e)
            }
    
    def batch_import_questions(self, questions_data: List[dict]) -> dict:
        """
        批量导入题目
        
        Args:
            questions_data: 题目数据列表
            
        Returns:
            导入结果
        """
        logger.info(f"开始批量导入 {len(questions_data)} 道题目")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for question_data in questions_data:
            try:
                # 验证题目数据
                if not self._validate_question_data(question_data):
                    error_count += 1
                    errors.append(f"题目数据验证失败: {json.dumps(question_data, ensure_ascii=False)[:100]}...")
                    continue
                
                # 创建题目
                self.create_question(
                    content=question_data["content"],
                    answer=question_data["answer"],
                    explanation=question_data.get("explanation"),
                    category_id=question_data.get("category_id"),
                    language_id=question_data.get("language_id"),
                    level_id=question_data.get("level_id"),
                    question_type=question_data.get("question_type", "single_choice"),
                    options=question_data.get("options", [])
                )
                
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"导入题目失败: {str(e)}")
        
        logger.info(f"批量导入完成，成功: {success_count}，失败: {error_count}")
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    
    def _validate_question_data(self, question_data: dict) -> bool:
        """
        验证题目数据
        
        Args:
            question_data: 题目数据
            
        Returns:
            是否验证通过
        """
        # 检查必填字段
        required_fields = ["content", "answer"]
        for field in required_fields:
            if not question_data.get(field):
                return False
        
        # 验证题目类型
        valid_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer", "listening"]
        if question_data.get("question_type") and question_data.get("question_type") not in valid_types:
            return False
        
        # 验证选择题必须有选项
        question_type = question_data.get("question_type", "single_choice")
        if question_type in ["single_choice", "multiple_choice"]:
            if not question_data.get("options") or len(question_data.get("options")) < 2:
                return False
        
        # 验证听力题必须有音频URL
        if question_type == "listening":
            if not question_data.get("audio_url"):
                return False
        
        return True
    
    def generate_questions(self, count: int = 5, category_id: int = None, 
                         language_id: int = None, level_id: int = None, 
                         question_type: str = None) -> List[Question]:
        """
        自动生成题目
        利用AI生成新的题目，提高题库的规模和多样性，支持多种题目类型
        
        Args:
            count: 生成题目的数量
            category_id: 分类ID
            language_id: 语种ID
            level_id: 等级ID
            question_type: 题目类型 (single_choice, multiple_choice, true_false, fill_blank, short_answer, listening)
            
        Returns:
            生成的题目列表
        """
        logger.info(f"开始自动生成 {count} 道题目...")
        
        generated_questions = []
        
        # 获取分类、语种和等级信息
        categories = self.get_all_categories()
        languages = self.get_all_languages()
        levels = self.get_all_levels()
        
        # 选择目标分类、语种和等级
        target_category = None
        if category_id:
            target_category = self.get_category(category_id)
        elif categories:
            import random
            target_category = random.choice(categories)
        
        target_language = None
        if language_id:
            target_language = self.get_language(language_id)
        elif languages:
            import random
            target_language = random.choice(languages)
        
        target_level = None
        if level_id:
            target_level = self.get_level(level_id)
        elif levels:
            import random
            target_level = random.choice(levels)
        
        # 如果没有找到合适的分类、语种或等级，使用默认值
        if not target_category:
            target_category = QuestionCategory(name="数学", description="数学题目分类")
            target_category = self.create_category(target_category.name, target_category.description)
        
        if not target_language:
            target_language = QuestionLanguage(name="中文", code="zh")
            target_language = self.create_language(target_language.name, target_language.code)
        
        if not target_level:
            target_level = QuestionLevel(name="初级", level=1, description="适合初学者")
            target_level = self.create_level(target_level.name, target_level.level, target_level.description)
        
        # 扩展可用的题目类型
        available_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer", "case_analysis", "comprehensive"]
        
        # 扩展题目分类和内容库
        category_content_libraries = {
            "数学": {
                "初级": {
                    "topics": ["基础算术", "简单几何", "时间计算", "单位换算", "数字认知"],
                    "question_templates": {
                        "single_choice": [
                            "{num1} + {num2} = ?",
                            "{num1} - {num2} = ?",
                            "{num1} × {num2} = ?",
                            "{num1} ÷ {num2} = ?",
                            "以下哪个是偶数？",
                            "以下哪个是奇数？"
                        ],
                        "multiple_choice": [
                            "以下哪些是质数？",
                            "以下哪些是偶数？",
                            "以下哪些是3的倍数？"
                        ],
                        "true_false": [
                            "{num1} + {num2} = {sum}",
                            "{num1}是偶数",
                            "{num1}是质数"
                        ],
                        "fill_blank": [
                            "{num1} + {num2} = ____",
                            "{num1} × {num2} = ____",
                            "1小时 = ____分钟"
                        ],
                        "short_answer": [
                            "请计算：{num1} + {num2} + {num3}",
                            "请计算：{num1} × {num2} ÷ {num3}",
                            "请写出3个偶数"
                        ]
                    }
                },
                "中级": {
                    "topics": ["代数基础", "几何图形", "分数运算", "小数运算", "应用题"],
                    "question_templates": {
                        "single_choice": [
                            "{num1} × {num2} + {num3} = ?",
                            "解方程：{coeff}x + {const} = {result}",
                            "半径为{radius}的圆的面积是多少？",
                            "{fraction1} + {fraction2} = ?"
                        ],
                        "multiple_choice": [
                            "以下哪些是直角三角形的判定条件？",
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
                            "矩阵[[1,2],[3,4]]的行列式是多少？"
                        ],
                        "multiple_choice": [
                            "以下哪些是奇函数？",
                            "以下哪些是可导函数？"
                        ],
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
                            "Which one is a fruit?",
                            "Which one is a color?"
                        ],
                        "multiple_choice": [
                            "Which of the following are fruits?",
                            "Which of the following are colors?"
                        ],
                        "true_false": [
                            "'Apple' means '{chinese_word}' in Chinese",
                            "'Red' is a color"
                        ],
                        "fill_blank": [
                            "The English word for '{chinese_word}' is ____",
                            "I ____ a student (be动词填空)"
                        ],
                        "short_answer": [
                            "What is the English word for '{chinese_word}'?",
                            "How do you say '{chinese_word}' in English?"
                        ]
                    }
                },
                "中级": {
                    "topics": ["动词时态", "句型结构", "阅读理解", "词汇辨析", "写作基础"],
                    "question_templates": {
                        "single_choice": [
                            "What is the past tense of '{verb}'?",
                            "Which one is correct?",
                            "Choose the right preposition: I go ____ school by bus"
                        ],
                        "multiple_choice": [
                            "Which of the following are irregular verbs?",
                            "Which of the following sentences are correct?"
                        ],
                        "true_false": [
                            "The past tense of 'write' is 'writed'",
                            "'I am go to school' is correct"
                        ],
                        "fill_blank": [
                            "She ____ to the park yesterday (go的正确形式)",
                            "I ____ English for 3 years (learn的正确形式)"
                        ],
                        "short_answer": [
                            "What is the difference between 'say' and 'tell'?",
                            "How do you form the present perfect tense?"
                        ]
                    }
                },
                "高级": {
                    "topics": ["高级语法", "文学赏析", "商务英语", "学术写作", "翻译技巧"],
                    "question_templates": {
                        "single_choice": [
                            "Which one is a complex sentence?",
                            "Choose the correct passive voice: The book ____ by him",
                            "Which one uses correct subject-verb agreement?"
                        ],
                        "multiple_choice": [
                            "Which of the following are complex sentences?",
                            "Which of the following use correct parallel structure?"
                        ],
                        "true_false": [
                            "'Had + past participle' is used for past perfect tense",
                            "Passive voice is always better than active voice"
                        ],
                        "fill_blank": [
                            "The experiment ____ by the scientists last year (conduct的正确形式)",
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
                            "以下哪些是褒义词？",
                            "以下哪些是量词？"
                        ],
                        "true_false": [
                            "'苹果'是一个名词",
                            "逗号用于分隔句子中的并列成分"
                        ],
                        "fill_blank": [
                            "床前明月光，疑是____霜",
                            "我有一____书（量词填空）"
                        ],
                        "short_answer": [
                            "请写出'大'的反义词",
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
                },
                "中级": {
                    "topics": ["阅读理解", "作文写作", "语法知识", "修辞手法", "文学常识"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是比喻句？",
                            "'春风又绿江南岸'中的'绿'是什么词性？",
                            "以下哪个成语使用正确？"
                        ],
                        "multiple_choice": [
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
                },
                "高级": {
                    "topics": ["文学赏析", "文言文阅读", "高级写作", "修辞技巧", "文化常识"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是文言虚词？",
                            "'落霞与孤鹜齐飞，秋水共长天一色'出自哪篇文章？",
                            "以下哪个是通假字？"
                        ],
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
                "初级": {
                    "topics": ["基础物理概念", "力学基础", "热学初步", "光学现象", "声学知识"],
                    "question_templates": {
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
                            "案例分析：小明推桌子，桌子没有动。\n\n问题：1. 为什么桌子没有动？\n2. 此时桌子受到了哪些力的作用？",
                            "案例分析：在寒冷的冬天，窗户玻璃上会出现冰花。\n\n问题：1. 冰花出现在窗户的内侧还是外侧？\n2. 这种现象属于什么物态变化？"
                        ],
                        "comprehensive": [
                            "请完成以下任务：\n1. 简述力的三要素\n2. 举例说明力的作用效果\n3. 解释为什么在太空中人会漂浮"
                        ]
                    }
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
                            "以下哪些现象属于电磁感应？"
                        ],
                        "true_false": [
                            "摩擦力总是阻碍物体的运动",
                            "动能定理适用于所有力做功的情况",
                            "电场力做功与路径无关"
                        ],
                        "fill_blank": [
                            "功的公式是W = ____",
                            "欧姆定律的表达式是I = ____",
                            "动能的公式是Ek = ____"
                        ],
                        "short_answer": [
                            "请推导动能定理",
                            "请解释楞次定律的内容",
                            "请说明热力学第一定律的含义"
                        ],
                        "case_analysis": [
                            "案例分析：一辆汽车以10m/s的速度行驶，突然刹车，经过5s后停止。\n\n问题：1. 汽车的加速度是多少？\n2. 刹车过程中汽车行驶的距离是多少？\n3. 请用牛顿运动定律解释刹车过程",
                            "案例分析：一个小球从10m高处自由下落，忽略空气阻力。\n\n问题：1. 小球下落的时间是多少？\n2. 小球落地时的速度是多少？\n3. 请计算小球下落过程中重力做的功"
                        ],
                        "comprehensive": [
                            "请完成以下关于牛顿运动定律的任务：\n1. 简述牛顿三大定律的内容\n2. 举例说明牛顿第二定律的应用\n3. 解释为什么汽车启动时乘客会向后仰"
                        ]
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
                        ],
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
                            "请完成以下任务：\n1. 简述原子的结构\n2. 解释什么是元素周期表\n3. 举例说明常见的化学变化和物理变化"
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
                            "请完成以下关于电化学的任务：\n1. 简述原电池的工作原理\n2. 解释电解池与原电池的区别\n3. 举例说明电化学在日常生活中的应用"
                        ]
                    }
                },
                "高级": {
                    "topics": ["有机化学", "物理化学", "分析化学", "结构化学", "化学热力学"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是烷烃的通式？",
                            "吉布斯自由能变ΔG与反应自发性的关系是什么？",
                            "以下哪个是分光光度法的基本原理？"
                        ],
                        "multiple_choice": [
                            "以下哪些是有机化合物的官能团？",
                            "以下哪些是热力学状态函数？"
                        ],
                        "true_false": [
                            "有机化合物都含有碳元素",
                            "熵增加的反应一定是自发反应",
                            "质谱法可以确定化合物的分子量"
                        ],
                        "fill_blank": [
                            "烷烃的通式是____",
                            "热力学第一定律的数学表达式是____",
                            "pH的定义是____"
                        ],
                        "short_answer": [
                            "请解释什么是同系物",
                            "请推导范特霍夫方程",
                            "请说明红外光谱的基本原理"
                        ],
                        "case_analysis": [
                            "案例分析：某有机化合物的分子式为C4H10O，红外光谱显示在3300cm-1处有强宽峰，1H-NMR谱显示有4组峰，面积比为3:3:2:2。\n\n问题：1. 推测该化合物的结构\n2. 解释红外光谱和核磁共振谱的特征峰\n3. 写出该化合物的可能同分异构体",
                            "案例分析：已知反应A + B → C的速率方程为v = k[A][B]2，当[A]和[B]都增加到原来的2倍时，反应速率如何变化？\n\n问题：1. 确定该反应的级数\n2. 计算速率常数k的单位\n3. 解释反应物浓度对反应速率的影响"
                        ],
                        "comprehensive": [
                            "请完成以下关于有机化学的综合任务：\n1. 简述有机物的分类方法\n2. 解释什么是官能团\n3. 说明有机合成的基本策略"
                        ]
                    }
                }
            },
            "历史": {
                "初级": {
                    "topics": ["中国古代史概述", "世界古代史初步", "历史人物简介", "重大历史事件", "历史文化常识"],
                    "question_templates": {
                        "single_choice": [
                            "秦始皇统一中国的时间是哪一年？",
                            "以下哪个是中国古代四大发明之一？",
                            "第一次世界大战爆发于哪一年？"
                        ],
                        "multiple_choice": [
                            "以下哪些是中国古代的朝代？",
                            "以下哪些是第二次世界大战的主要参战国？"
                        ],
                        "true_false": [
                            "唐太宗是唐朝的第二位皇帝",
                            "哥伦布发现美洲新大陆是在15世纪",
                            "辛亥革命发生于1911年"
                        ],
                        "fill_blank": [
                            "中国历史上第一个统一的中央集权国家是____",
                            "四大发明包括造纸术、印刷术、火药和____",
                            "抗日战争胜利于____年"
                        ],
                        "short_answer": [
                            "请简述秦始皇的主要功绩",
                            "请解释什么是文艺复兴",
                            "请说明鸦片战争的影响"
                        ],
                        "case_analysis": [
                            "案例分析：阅读以下材料，回答问题。\n\n材料：秦始皇统一六国后，实行了一系列改革措施，包括统一文字、货币、度量衡，修建长城，建立郡县制等。\n\n问题：1. 秦始皇的这些改革措施有什么作用？\n2. 你如何评价秦始皇的历史地位？",
                            "案例分析：阅读以下材料，回答问题。\n\n材料：14世纪，文艺复兴运动在意大利兴起，强调人文主义，反对封建神学，提倡以人为中心而不是以神为中心。\n\n问题：1. 文艺复兴运动的核心思想是什么？\n2. 文艺复兴运动对欧洲历史产生了什么影响？"
                        ],
                        "comprehensive": [
                            "请完成以下关于中国古代史的任务：\n1. 简述中国古代的四大发明\n2. 说明丝绸之路的历史意义\n3. 列举中国古代的三个重要朝代及其主要成就"
                        ]
                    }
                },
                "中级": {
                    "topics": ["中国古代政治制度", "世界近代史", "中国近代史", "历史事件分析", "历史人物评价"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个是科举制度创立的朝代？",
                            "工业革命最早开始于哪个国家？",
                            "以下哪个事件标志着中国新民主主义革命的开端？"
                        ],
                        "multiple_choice": [
                            "以下哪些是启蒙运动的代表人物？",
                            "以下哪些事件与第二次工业革命有关？"
                        ],
                        "true_false": [
                            "辛亥革命推翻了清朝统治，结束了中国两千多年的封建帝制",
                            "美国独立战争爆发的原因是英国的殖民压迫",
                            "法国大革命的导火索是三级会议的召开"
                        ],
                        "fill_blank": [
                            "中国古代的三省六部制创立于____朝",
                            "工业革命的标志是____的改良",
                            "五四运动的口号包括'外争主权，____'"
                        ],
                        "short_answer": [
                            "请分析科举制度的影响",
                            "请简述工业革命的历史意义",
                            "请评价孙中山的历史地位"
                        ],
                        "case_analysis": [
                            "案例分析：阅读以下材料，回答问题。\n\n材料：19世纪中期，英国率先完成工业革命，成为世界上第一个工业国家。工业革命带来了生产力的巨大飞跃，但也导致了环境污染、工人生活恶化等问题。\n\n问题：1. 工业革命的主要发明有哪些？\n2. 工业革命对英国社会产生了什么影响？\n3. 你如何评价工业革命的历史地位？",
                            "案例分析：阅读以下材料，回答问题。\n\n材料：1911年，辛亥革命爆发，推翻了清朝统治，结束了中国两千多年的封建帝制，建立了中华民国。\n\n问题：1. 辛亥革命的历史背景是什么？\n2. 辛亥革命的主要成果有哪些？\n3. 为什么说辛亥革命是中国近代史上的一次伟大的资产阶级民主革命？"
                        ],
                        "comprehensive": [
                            "请完成以下关于世界近代史的任务：\n1. 简述法国大革命的主要过程\n2. 说明第一次工业革命的影响\n3. 分析近代西方国家殖民扩张的双重作用"
                        ]
                    }
                },
                "高级": {
                    "topics": ["中国现代史", "世界现代史", "历史理论与方法", "历史专题研究", "比较历史分析"],
                    "question_templates": {
                        "single_choice": [
                            "以下哪个事件标志着冷战的开始？",
                            "中国改革开放的总设计师是谁？",
                            "以下哪个是全球化的主要特征？"
                        ],
                        "multiple_choice": [
                            "以下哪些是冷战时期的国际组织？",
                            "以下哪些因素推动了全球化进程？"
                        ],
                        "true_false": [
                            "冷战的结束标志着世界格局进入多极化时代",
                            "中国加入世界贸易组织是在2001年",
                            "经济全球化只带来了积极影响"
                        ],
                        "fill_blank": [
                            "冷战开始的标志是____的发表",
                            "中国改革开放始于____年",
                            "联合国成立于____年"
                        ],
                        "short_answer": [
                            "请分析冷战结束的原因",
                            "请评价中国改革开放的历史意义",
                            "请论述全球化对世界历史发展的影响"
                        ],
                        "case_analysis": [
                            "案例分析：阅读以下材料，回答问题。\n\n材料：1947年，杜鲁门主义出台，标志着冷战的开始。1991年，苏联解体，冷战结束。冷战期间，美苏两国进行了长期的军备竞赛，同时也在科技、文化等领域展开了竞争。\n\n问题：1. 冷战的主要原因是什么？\n2. 冷战对世界历史产生了什么影响？\n3. 冷战结束后，世界格局发生了怎样的变化？",
                            "案例分析：阅读以下材料，回答问题。\n\n材料：1978年，中国开始实行改革开放政策，经济快速发展，综合国力不断增强。40多年来，中国的GDP从世界第11位上升到第2位，成为世界第二大经济体。\n\n问题：1. 中国改革开放的主要内容有哪些？\n2. 改革开放对中国社会产生了什么影响？\n3. 中国改革开放的成功经验对其他国家有何启示？"
                        ],
                        "comprehensive": [
                            "请完成以下关于20世纪世界史的任务：\n1. 分析两次世界大战的异同\n2. 说明冷战的影响\n3. 论述全球化的利弊"
                        ]
                    }
                }
            }
        }
        
        # 扩展内容库数据
        chinese_words = ["苹果", "香蕉", "橙子", "葡萄", "西瓜", "猫", "狗", "鸟", "鱼", "花", 
                        "太阳", "月亮", "星星", "天空", "大地", "海洋", "河流", "山脉", "森林", "草原",
                        "美丽", "快乐", "聪明", "高大", "红色", "跑", "吃", "写", "读", "唱"]
        english_words = ["apple", "banana", "orange", "grape", "watermelon", "cat", "dog", "bird", "fish", "flower",
                        "sun", "moon", "star", "sky", "earth", "ocean", "river", "mountain", "forest", "grassland",
                        "beautiful", "happy", "smart", "tall", "red", "run", "eat", "write", "read", "sing"]
        verbs = ["go", "eat", "run", "write", "read", "speak", "listen", "watch", "play", "study",
                "work", "sleep", "walk", "jump", "sing", "dance", "draw", "paint", "cook", "clean"]
        irregular_verbs = {"go": "went", "eat": "ate", "run": "ran", "write": "wrote", "read": "read",
                          "speak": "spoke", "break": "broke", "make": "made", "take": "took", "see": "saw",
                          "drive": "drove", "ride": "rode", "swim": "swam", "give": "gave", "bring": "brought"}
        
        # 新增物理、化学、历史内容库数据
        physics_data = {
            "units": ["米", "千克", "秒", "安培", "开尔文", "摩尔", "坎德拉"],
            "fundamental_laws": ["牛顿运动定律", "热力学定律", "电磁学定律", "相对论", "量子力学"],
            "famous_scientists": ["牛顿", "爱因斯坦", "麦克斯韦", "玻尔", "伽利略"],
            "physical_quantities": ["长度", "质量", "时间", "电流", "温度", "物质的量", "发光强度"]
        }
        
        chemistry_data = {
            "elements": ["氢", "氦", "锂", "铍", "硼", "碳", "氮", "氧", "氟", "氖"],
            "compounds": ["水", "二氧化碳", "氧气", "氮气", "氯化钠", "硫酸", "盐酸", "氢氧化钠"],
            "chemical_reactions": ["化合反应", "分解反应", "置换反应", "复分解反应", "氧化还原反应"],
            "famous_chemists": ["门捷列夫", "拉瓦锡", "道尔顿", "阿伏伽德罗", "居里夫人"]
        }
        
        history_data = {
            "chinese_dynasties": ["夏", "商", "周", "秦", "汉", "唐", "宋", "元", "明", "清"],
            "world_events": ["第一次世界大战", "第二次世界大战", "工业革命", "法国大革命", "美国独立战争"],
            "historical_figures": ["秦始皇", "唐太宗", "成吉思汗", "拿破仑", "华盛顿"],
            "ancient_civilizations": ["古埃及", "古希腊", "古罗马", "古印度", "古代中国"]
        }
        
        # 生成题目
        for i in range(count):
            import random
            
            # 确定题目类型
            current_type = question_type or random.choice(available_types)
            
            # 获取分类和难度信息
            category_name = target_category.name
            level_name = target_level.name
            level_value = target_level.level
            
            # 获取对应分类和难度的内容库
            category_lib = category_content_libraries.get(category_name, category_content_libraries["数学"])
            level_lib = category_lib.get(level_name, category_lib["初级"])
            
            # 生成题目内容
            content = ""
            answer = ""
            explanation = ""
            options = []
            tags = []
            
            # 优化难度评分机制
            # 基础难度分数（基于等级）
            base_difficulty = random.uniform(1, 10) if not level_value else level_value * 2.5
            
            # 根据题目类型调整难度
            type_adjustment = {
                "single_choice": 0.0,
                "multiple_choice": 1.0,
                "true_false": -1.0,
                "fill_blank": 1.5,
                "short_answer": 2.0,
                "case_analysis": 3.0,
                "comprehensive": 3.5
            }
            
            # 根据学科调整难度
            subject_adjustment = {
                "数学": 0.0,
                "英语": -0.5,
                "语文": -0.3,
                "物理": 1.0,
                "化学": 0.8,
                "历史": -0.2
            }
            
            # 计算最终难度分数
            difficulty_score = base_difficulty + type_adjustment.get(current_type, 0.0) + subject_adjustment.get(category_name, 0.0)
            
            # 确保难度分数在1-10之间
            difficulty_score = max(1.0, min(10.0, difficulty_score))
            
            # 根据分类、难度和题型生成具体题目
            # 处理案例分析题和综合题
            if current_type == "case_analysis" or current_type == "comprehensive":
                # 生成案例分析题或综合题
                template = random.choice(level_lib["question_templates"][current_type])
                content = template
                answer = "根据分析回答"
                explanation = f"这是一道{level_name}难度的{category_name}{current_type.replace('_', ' ')}题"
                options = []
            elif category_name == "数学":
                # 生成随机数字
                num1 = random.randint(1, 20) if level_value <= 2 else random.randint(10, 100)
                num2 = random.randint(1, 20) if level_value <= 2 else random.randint(10, 100)
                num3 = random.randint(1, 10) if level_value <= 2 else random.randint(5, 50)
                
                # 确保除法有整数结果
                if num2 == 0:
                    num2 = 1
                if num1 % num2 != 0:
                    num1 = num2 * random.randint(1, 10)
                
                if current_type == "single_choice":
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["single_choice"])
                    
                    # 填充模板
                    if "{num1} + {num2}" in template:
                        correct_answer = num1 + num2
                        options = [
                            str(correct_answer),
                            str(correct_answer + random.randint(1, 5)),
                            str(correct_answer - random.randint(1, 5)),
                            str(num1 * num2)
                        ]
                        content = template.format(num1=num1, num2=num2)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"
                    elif "{num1} - {num2}" in template:
                        correct_answer = num1 - num2
                        options = [
                            str(correct_answer),
                            str(correct_answer + random.randint(1, 5)),
                            str(correct_answer - random.randint(1, 5)),
                            str(num1 + num2)
                        ]
                        content = template.format(num1=num1, num2=num2)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}减{num2}等于{correct_answer}"
                    elif "{num1} × {num2}" in template:
                        correct_answer = num1 * num2
                        options = [
                            str(correct_answer),
                            str(correct_answer + random.randint(1, 10)),
                            str(correct_answer - random.randint(1, 10)),
                            str(num1 + num2)
                        ]
                        content = template.format(num1=num1, num2=num2)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}乘{num2}等于{correct_answer}"
                    elif "{num1} ÷ {num2}" in template:
                        correct_answer = num1 // num2
                        options = [
                            str(correct_answer),
                            str(correct_answer + random.randint(1, 5)),
                            str(correct_answer - random.randint(1, 5)),
                            str(num1 * num2)
                        ]
                        content = template.format(num1=num1, num2=num2)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}除以{num2}等于{correct_answer}"
                    elif "偶数" in template:
                        even_num = random.randint(2, 20) * 2
                        options = [
                            str(even_num),
                            str(even_num + 1),
                            str(even_num + 3),
                            str(even_num + 5)
                        ]
                        content = template
                        answer = str(even_num)
                        explanation = f"这是一道{level_lib['topics'][0]}题，能被2整除的数是偶数，{even_num}是偶数"
                    elif "奇数" in template:
                        odd_num = random.randint(1, 10) * 2 + 1
                        options = [
                            str(odd_num),
                            str(odd_num + 1),
                            str(odd_num + 2),
                            str(odd_num + 4)
                        ]
                        content = template
                        answer = str(odd_num)
                        explanation = f"这是一道{level_lib['topics'][0]}题，不能被2整除的数是奇数，{odd_num}是奇数"
                    else:
                        # 默认生成加法题
                        correct_answer = num1 + num2
                        options = [
                            str(correct_answer),
                            str(correct_answer + 1),
                            str(correct_answer - 1),
                            str(num1 * num2)
                        ]
                        content = f"{num1} + {num2} = ?"
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"
                    
                    # 随机打乱选项
                    random.shuffle(options)
                    answer = str(correct_answer)
                
                elif current_type == "multiple_choice":
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["multiple_choice"])
                    
                    # 生成质数题
                    if "质数" in template:
                        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
                        non_primes = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18]
                        
                        # 选择3个质数和3个非质数
                        selected_primes = random.sample(primes, 3)
                        selected_non_primes = random.sample(non_primes, 3)
                        options = [str(p) for p in selected_primes + selected_non_primes]
                        answer = ",".join([str(p) for p in selected_primes])
                        content = template
                        explanation = f"这是一道{level_lib['topics'][0]}题，质数是大于1的自然数，除了1和它本身没有其他因数。{answer}都是质数"
                    # 生成偶数题
                    elif "偶数" in template:
                        evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
                        odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
                        
                        selected_evens = random.sample(evens, 3)
                        selected_odds = random.sample(odds, 3)
                        options = [str(e) for e in selected_evens + selected_odds]
                        answer = ",".join([str(e) for e in selected_evens])
                        content = template
                        explanation = f"这是一道{level_lib['topics'][0]}题，能被2整除的数是偶数。{answer}都是偶数"
                    # 生成倍数题
                    else:
                        base = 3
                        multiples = [base * i for i in range(1, 11)]
                        non_multiples = [i for i in range(1, 31) if i % base != 0]
                        
                        selected_multiples = random.sample(multiples, 3)
                        selected_non_multiples = random.sample(non_multiples, 3)
                        options = [str(m) for m in selected_multiples + selected_non_multiples]
                        answer = ",".join([str(m) for m in selected_multiples])
                        content = template.format(num=base)
                        explanation = f"这是一道{level_lib['topics'][0]}题，能被{base}整除的数是{base}的倍数。{answer}都是{base}的倍数"
                    
                    # 随机打乱选项
                    random.shuffle(options)
                
                elif current_type == "true_false":
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["true_false"])
                    
                    # 生成判断题
                    sum_val = num1 + num2
                    is_true = random.choice([True, False])
                    
                    if "{num1} + {num2} = {sum}" in template:
                        if is_true:
                            content = template.format(num1=num1, num2=num2, sum=sum_val)
                            answer = "true"
                            explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}确实等于{sum_val}"
                        else:
                            wrong_sum = sum_val + random.randint(1, 10)
                            content = template.format(num1=num1, num2=num2, sum=wrong_sum)
                            answer = "false"
                            explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{sum_val}，而不是{wrong_sum}"
                    elif "{num1}是偶数" in template:
                        if num1 % 2 == 0:
                            content = template.format(num1=num1)
                            answer = "true"
                            explanation = f"这是一道{level_lib['topics'][0]}题，{num1}能被2整除，是偶数"
                        else:
                            content = template.format(num1=num1)
                            answer = "false"
                            explanation = f"这是一道{level_lib['topics'][0]}题，{num1}不能被2整除，不是偶数"
                    else:  # {num1}是质数
                        is_prime = num1 > 1 and all(num1 % i != 0 for i in range(2, int(num1**0.5) + 1))
                        content = template.format(num1=num1)
                        answer = "true" if is_prime else "false"
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}是{'质数' if is_prime else '合数'}"
                
                elif current_type == "fill_blank":
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["fill_blank"])
                    
                    if "{num1} + {num2}" in template:
                        correct_answer = num1 + num2
                        content = template.format(num1=num1, num2=num2)
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"
                    elif "{num1} × {num2}" in template:
                        correct_answer = num1 * num2
                        content = template.format(num1=num1, num2=num2)
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}乘{num2}等于{correct_answer}"
                    elif "1小时 = ____分钟" in template:
                        content = template
                        answer = "60"
                        explanation = f"这是一道{level_lib['topics'][0]}题，1小时等于60分钟"
                    else:
                        correct_answer = num1 + num2
                        content = f"{num1} + {num2} = ____"
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"
                
                else:  # short_answer
                    # 随机选择模板
                    template = random.choice(level_lib["question_templates"]["short_answer"])
                    
                    if "请计算：{num1} + {num2} + {num3}" in template:
                        correct_answer = num1 + num2 + num3
                        content = template.format(num1=num1, num2=num2, num3=num3)
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{num1+num2}，再加{num3}等于{correct_answer}"
                    elif "请计算：{num1} × {num2} ÷ {num3}" in template:
                        correct_answer = num1 * num2 // num3
                        content = template.format(num1=num1, num2=num2, num3=num3)
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}乘{num2}等于{num1*num2}，再除以{num3}等于{correct_answer}"
                    elif "请写出3个偶数" in template:
                        content = template
                        even_nums = [str(random.randint(2, 20) * 2) for _ in range(3)]
                        answer = ", ".join(even_nums)
                        explanation = f"这是一道{level_lib['topics'][0]}题，偶数是能被2整除的数，{answer}都是偶数"
                    else:
                        content = f"请计算：{num1} + {num2}"
                        correct_answer = num1 + num2
                        answer = str(correct_answer)
                        explanation = f"这是一道{level_lib['topics'][0]}题，{num1}加{num2}等于{correct_answer}"
            
            elif category_name == "英语":
                # 生成英语题目
                if level_value <= 2:  # 初级
                    if current_type == "single_choice":
                        # 生成词汇题
                        word_index = random.randint(0, len(chinese_words)-1)
                        chinese_word = chinese_words[word_index]
                        correct_answer = english_words[word_index]
                        
                        # 生成干扰选项
                        distractors = random.sample([w for w in english_words if w != correct_answer], 3)
                        options = [correct_answer] + distractors
                        random.shuffle(options)
                        
                        content = f"What is the English word for '{chinese_word}'?"
                        answer = correct_answer
                        explanation = f"{chinese_word}的英语单词是{correct_answer}"
                    
                    elif current_type == "multiple_choice":
                        # 生成词汇分类题
                        categories = ["水果", "动物", "自然"]
                        selected_category = random.choice(categories)
                        
                        if selected_category == "水果":
                            fruits = chinese_words[:5]
                            fruit_answers = english_words[:5]
                            non_fruits = chinese_words[5:10]
                            non_fruit_answers = english_words[5:10]
                        elif selected_category == "动物":
                            fruits = chinese_words[5:10]
                            fruit_answers = english_words[5:10]
                            non_fruits = chinese_words[:5]
                            non_fruit_answers = english_words[:5]
                        else:  # 自然
                            fruits = chinese_words[10:15]
                            fruit_answers = english_words[10:15]
                            non_fruits = chinese_words[:5]
                            non_fruit_answers = english_words[:5]
                        
                        # 选择3个正确答案和3个干扰选项
                        selected_fruits = random.sample(fruits, 3)
                        selected_fruit_answers = [english_words[chinese_words.index(f)] for f in selected_fruits]
                        selected_non_fruits = random.sample(non_fruits, 3)
                        selected_non_fruit_answers = [english_words[chinese_words.index(nf)] for nf in selected_non_fruits]
                        
                        options = selected_fruit_answers + selected_non_fruit_answers
                        random.shuffle(options)
                        answer = ",".join(selected_fruit_answers)
                        content = f"Which of the following are {selected_category}?"
                        explanation = f"这是一道词汇分类题，{selected_category}包括{', '.join(selected_fruit_answers)}"
                    
                    elif current_type == "true_false":
                        word_index = random.randint(0, len(chinese_words)-1)
                        chinese_word = chinese_words[word_index]
                        english_word = english_words[word_index]
                        
                        is_true = random.choice([True, False])
                        if is_true:
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
                        correct_answer = english_words[word_index]
                        
                        content = f"The English word for '{chinese_word}' is ____"
                        answer = correct_answer
                        explanation = f"'{chinese_word}'的英语单词是{correct_answer}"
                    
                    else:  # short_answer
                        # 生成词汇简答题
                        word_index = random.randint(0, len(chinese_words)-1)
                        chinese_word = chinese_words[word_index]
                        
                        content = f"What is the English word for '{chinese_word}'?"
                        answer = english_words[word_index]
                        explanation = f"{chinese_word}的英语单词是{answer}"
                
                else:  # 中级或高级
                    if current_type == "single_choice":
                        # 生成动词时态题
                        verb = random.choice(list(irregular_verbs.keys()))
                        correct_answer = irregular_verbs[verb]
                        
                        options = [
                            correct_answer,
                            f"{verb}ed",
                            f"{verb}s",
                            f"{verb}ing"
                        ]
                        random.shuffle(options)
                        
                        content = f"What is the past tense of '{verb}'?"
                        answer = correct_answer
                        explanation = f"'{verb}'的过去式是不规则变化，正确形式是{correct_answer}"
                    
                    elif current_type == "multiple_choice":
                        # 生成不规则动词多选题
                        correct_verbs = random.sample(list(irregular_verbs.keys()), 3)
                        regular_verbs = [v for v in verbs if v not in irregular_verbs]
                        wrong_verbs = random.sample(regular_verbs, 3)
                        
                        options = correct_verbs + wrong_verbs
                        random.shuffle(options)
                        answer = ",".join(correct_verbs)
                        
                        content = "Which of the following are irregular verbs?"
                        explanation = f"不规则动词的过去式不遵循一般规则，{', '.join(correct_verbs)}都是不规则动词"
                    
                    elif current_type == "true_false":
                        # 生成动词时态判断题
                        verb = random.choice(list(irregular_verbs.keys()))
                        correct_past = irregular_verbs[verb]
                        
                        is_true = random.choice([True, False])
                        if is_true:
                            content = f"The past tense of '{verb}' is '{correct_past}'"
                            answer = "true"
                            explanation = f"'{verb}'的过去式确实是'{correct_past}'，是不规则变化"
                        else:
                            content = f"The past tense of '{verb}' is '{verb}ed'"
                            answer = "false"
                            explanation = f"'{verb}'的过去式是不规则变化，应该是'{correct_past}'，而不是'{verb}ed'"
                    
                    elif current_type == "fill_blank":
                        # 生成动词时态填空题
                        verb = random.choice(list(irregular_verbs.keys()))
                        correct_past = irregular_verbs[verb]
                        
                        content = f"She ____ to the park yesterday ({verb}的正确形式)"
                        answer = correct_past
                        explanation = f"yesterday表示过去时间，应该使用过去式，'{verb}'的过去式是不规则变化，正确形式是{correct_past}"
                    
                    else:  # short_answer
                        # 生成动词时态简答题
                        verb = random.choice(list(irregular_verbs.keys()))
                        
                        content = f"What is the past tense of '{verb}'?"
                        answer = irregular_verbs[verb]
                        explanation = f"'{verb}'的过去式是不规则变化，正确形式是{answer}"
            
            elif category_name == "语文":
                # 生成语文题目
                if level_value <= 2:  # 初级
                    if current_type == "single_choice":
                        # 生成近义词题
                        synonyms = {
                            "美丽": ["漂亮", "好看", "绚丽", "丑陋"],
                            "快乐": ["开心", "高兴", "愉快", "悲伤"],
                            "大": ["巨大", "庞大", "宏大", "小"],
                            "小": ["微小", "渺小", "细小", "大"],
                            "聪明": ["聪慧", "伶俐", "睿智", "愚蠢"]
                        }
                        
                        base_word = random.choice(list(synonyms.keys()))
                        correct_answer = synonyms[base_word][0]
                        options = synonyms[base_word]
                        random.shuffle(options)
                        
                        content = f"'{base_word}'的近义词是？"
                        answer = correct_answer
                        explanation = f"'{base_word}'和'{correct_answer}'意思相近，是近义词"
                    
                    elif current_type == "multiple_choice":
                        # 生成词性分类题
                        nouns = ["苹果", "猫", "书", "学校", "太阳"]
                        verbs = ["跑", "吃", "写", "读", "唱"]
                        adjectives = ["美丽", "快乐", "聪明", "高大", "红色"]
                        
                        word_type = random.choice(["名词", "动词", "形容词"])
                        if word_type == "名词":
                            correct_words = nouns
                            wrong_words = verbs + adjectives
                        elif word_type == "动词":
                            correct_words = verbs
                            wrong_words = nouns + adjectives
                        else:
                            correct_words = adjectives
                            wrong_words = nouns + verbs
                        
                        selected_correct = random.sample(correct_words, 3)
                        selected_wrong = random.sample(wrong_words, 3)
                        options = selected_correct + selected_wrong
                        random.shuffle(options)
                        answer = ",".join(selected_correct)
                        
                        content = f"以下哪些是{word_type}？"
                        explanation = f"{word_type}是表示{word_type}的词，{', '.join(selected_correct)}都是{word_type}"
                    
                    elif current_type == "fill_blank":
                        # 生成古诗词填空题
                        poems = {
                            "床前明月光，疑是____上霜。": "地",
                            "举头望明月，____头思故乡。": "低",
                            "春眠不觉晓，处处闻____鸟。": "啼",
                            "夜来风雨声，花落知____少。": "多",
                            "锄禾日当午，汗滴____下土。": "禾"
                        }
                        
                        poem_line, correct_char = random.choice(list(poems.items()))
                        content = poem_line.replace(correct_char, "____")
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
                            answer = "true"
                            explanation = f"'{word}'表示事物名称，是名词"
                        else:
                            word = random.choice(verbs)
                            content = f"'{word}'是一个名词"
                            answer = "false"
                            explanation = f"'{word}'表示动作，是动词，不是名词"
                
                else:  # 中级或高级
                    if current_type == "single_choice":
                        # 生成修辞手法题
                        metaphor_sentences = [
                            "叶子出水很高，像亭亭的舞女的裙。",
                            "月亮像一个大银盘挂在天空。",
                            "他的眼睛像星星一样明亮。"
                        ]
                        non_metaphor_sentences = [
                            "叶子出水很高。",
                            "月亮挂在天空。",
                            "他的眼睛很明亮。"
                        ]
                        
                        is_metaphor = random.choice([True, False])
                        if is_metaphor:
                            content = random.choice(metaphor_sentences)
                            options = ["比喻", "拟人", "夸张", "排比"]
                            answer = "比喻"
                            explanation = f"这句话使用了比喻的修辞手法，将{content.split('像')[0].strip()}比作{content.split('像')[1].strip()}"
                        else:
                            content = random.choice(non_metaphor_sentences)
                            options = ["比喻", "拟人", "夸张", "没有使用修辞手法"]
                            answer = "没有使用修辞手法"
                            explanation = f"这句话是普通陈述句，没有使用修辞手法"
                    
                    elif current_type == "multiple_choice":
                        # 生成文学常识题
                        authors = {
                            "鲁迅": ["《狂人日记》", "《阿Q正传》", "《孔乙己》"],
                            "老舍": ["《骆驼祥子》", "《茶馆》", "《四世同堂》"],
                            "曹雪芹": ["《红楼梦》", "《石头记》", "《金陵十二钗》"]
                        }
                        
                        author = random.choice(list(authors.keys()))
                        correct_works = authors[author]
                        wrong_works = []
                        for other_author, works in authors.items():
                            if other_author != author:
                                wrong_works.extend(works)
                        
                        selected_wrong = random.sample(wrong_works, 3)
                        options = correct_works + selected_wrong
                        random.shuffle(options)
                        answer = ",".join(correct_works)
                        
                        content = f"以下哪些是{author}的作品？"
                        explanation = f"{author}是中国著名作家，代表作包括{', '.join(correct_works)}"
                    
                    elif current_type == "fill_blank":
                        # 生成古诗词填空题（高级）
                        advanced_poems = {
                            "欲穷千里目，更上一____楼。": "层",
                            "天生我材必有用，千金散尽____复来。": "还",
                            "人生自古谁无死，留取丹心照____青。": "汗",
                            "不识庐山真面目，只缘身在此____中。": "山",
                            "问渠那得清如许，为有源头活____来。": "水"
                        }
                        
                        poem_line, correct_char = random.choice(list(advanced_poems.items()))
                        content = poem_line.replace(correct_char, "____")
                        answer = correct_char
                        explanation = f"这是经典古诗词中的诗句，正确填空是'{correct_char}'"
                    
                    else:  # true_false 或 short_answer
                        # 生成成语解释题
                        idioms = {
                            "画龙点睛": "比喻说话或写文章时，在关键处用几句话点明实质，使内容生动有力",
                            "井底之蛙": "比喻见识短浅的人",
                            "守株待兔": "比喻不主动努力，而存万一的侥幸心理，希望得到意外的收获",
                            "亡羊补牢": "比喻出了问题以后想办法补救，可以防止继续受损失",
                            "掩耳盗铃": "比喻自己欺骗自己，明明掩盖不住的事情偏要想法子掩盖"
                        }
                        
                        idiom, meaning = random.choice(list(idioms.items()))
                        content = f"请解释成语'{idiom}'的意思"
                        answer = meaning
                        explanation = f"这是一个常见成语，正确解释是{meaning}"
            
            elif category_name in ["物理", "化学", "历史"]:
                # 生成物理、化学、历史题目
                if category_name == "物理":
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
                            answer = "牛顿"
                            explanation = "力的国际单位是牛顿，符号为N"
                        elif "光在真空中的传播速度约为多少？" in template:
                            content = template
                            options = ["3×10^5 km/s", "3×10^8 km/s", "3×10^5 m/s", "3×10^8 m/s"]
                            answer = "3×10^8 m/s"
                            explanation = "光在真空中的传播速度约为3×10^8 m/s，相当于3×10^5 km/s"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.choice(options)
                            explanation = f"这是一道{level_name}难度的物理单选题"
                    
                    elif current_type == "multiple_choice":
                        # 生成物理多选题
                        template = random.choice(level_lib["question_templates"]["multiple_choice"])
                        if "以下哪些是基本物理量？" in template:
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
                        if "力是维持物体运动的原因" in template:
                            content = template
                            answer = "false"
                            explanation = "力是改变物体运动状态的原因，不是维持物体运动的原因"
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
                            explanation = f"这是一道{level_name}难度的物理判断题"
                    
                    elif current_type == "fill_blank":
                        # 生成物理填空题
                        template = random.choice(level_lib["question_templates"]["fill_blank"])
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
                        template = random.choice(level_lib["question_templates"]["single_choice"])
                        if "秦始皇统一中国的时间是哪一年？" in template:
                            content = template
                            options = ["公元前221年", "公元前206年", "公元221年", "公元206年"]
                            answer = "公元前221年"
                            explanation = "秦始皇于公元前221年统一六国，建立了中国历史上第一个统一的中央集权国家"
                        elif "以下哪个是中国古代四大发明之一？" in template:
                            content = template
                            options = ["造纸术", "火药", "印刷术", "以上都是"]
                            answer = "以上都是"
                            explanation = "中国古代四大发明包括造纸术、火药、印刷术和指南针"
                        elif "第一次世界大战爆发于哪一年？" in template:
                            content = template
                            options = ["1914年", "1918年", "1939年", "1945年"]
                            answer = "1914年"
                            explanation = "第一次世界大战爆发于1914年，结束于1918年"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.choice(options)
                            explanation = f"这是一道{level_name}难度的历史单选题"
                    
                    elif current_type == "multiple_choice":
                        # 生成历史多选题
                        template = random.choice(level_lib["question_templates"]["multiple_choice"])
                        if "以下哪些是中国古代的朝代？" in template:
                            content = template
                            options = ["夏", "商", "周", "秦"]
                            answer = "夏,商,周,秦"
                            explanation = "夏、商、周、秦都是中国古代的朝代"
                        elif "以下哪些是第二次世界大战的主要参战国？" in template:
                            content = template
                            options = ["美国", "德国", "日本", "意大利"]
                            answer = "美国,德国,日本,意大利"
                            explanation = "第二次世界大战的主要参战国包括同盟国（如美国、英国、苏联等）和轴心国（如德国、日本、意大利等）"
                        else:
                            content = template
                            options = ["选项A", "选项B", "选项C", "选项D"]
                            answer = random.sample(options, 2)
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
                            explanation = "哥伦布于1492年（15世纪）发现了美洲新大陆"
                        elif "辛亥革命发生于1911年" in template:
                            content = template
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
                            answer = "秦"
                            explanation = "秦始皇统一六国后，建立了中国历史上第一个统一的中央集权国家——秦朝"
                        elif "四大发明包括造纸术、印刷术、火药和____" in template:
                            content = template
                            answer = "指南针"
                            explanation = "中国古代四大发明包括造纸术、印刷术、火药和指南针"
                        elif "抗日战争胜利于____年" in template:
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
                    answer = "选项A"
                    options = ["选项A", "选项B", "选项C", "选项D"]
                    explanation = f"这是一道{level_name}难度的{category_name}单选题"
                elif current_type == "multiple_choice":
                    content = f"{category_name}相关问题：以下哪些选项是正确的？"
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
                tags=tags,
                difficulty_score=difficulty_score,
                usage_count=0,
                correct_rate=None
            )
            
            generated_questions.append(question)
        
        logger.info(f"成功生成 {len(generated_questions)} 道题目")
        return generated_questions
    
    def generate_question_by_ai(self, prompt: str = None, category_name: str = None, 
                              level_name: str = None, question_type: str = None) -> Optional[Question]:
        """
        使用AI生成单个题目
        
        Args:
            prompt: 生成题目的提示词
            category_name: 题目分类名称
            level_name: 题目难度名称
            question_type: 题目类型
            
        Returns:
            生成的题目，如果失败则返回None
        """
        try:
            logger.info("使用AI生成题目...")
            
            # 获取分类、语种和等级信息
            categories = self.get_all_categories()
            category_id = categories[0].id if categories else 1
            if category_name:
                # 查找对应分类
                for cat in categories:
                    if cat.name == category_name:
                        category_id = cat.id
                        break
            
            languages = self.get_all_languages()
            language_id = languages[0].id if languages else 1
            
            levels = self.get_all_levels()
            level_id = levels[0].id if levels else 1
            level_value = 1
            if level_name:
                # 查找对应等级
                for lvl in levels:
                    if lvl.name == level_name:
                        level_id = lvl.id
                        level_value = lvl.level
                        break
            
            # 生成更智能的提示词
            if not prompt:
                # 根据分类、难度和题型生成提示词
                prompt = f"生成一道{level_name if level_name else '中级'}难度的{category_name if category_name else '数学'}题目，"
                prompt += f"题目类型为{question_type if question_type else '单选题'}，"
                prompt += "包含题目内容、答案和详细解析。题目内容要清晰明确，答案要准确，解析要详细易懂。"
                prompt += "确保题目具有一定的挑战性和教育价值。"
            
            # 这里可以集成实际的AI模型，如OpenAI API或本地模型
            # 目前使用增强的模拟数据，生成更真实的题目
            import random
            
            # 生成更智能的题目
            if category_name == "数学" or not category_name:
                # 生成数学题目
                if level_value <= 2:
                    # 初级或中级数学题
                    num1 = random.randint(1, 50)
                    num2 = random.randint(1, 50)
                    operation = random.choice(["+", "-", "×", "÷"])
                    
                    if operation == "+":
                        result = num1 + num2
                        question_content = f"计算：{num1} + {num2} = ?"
                        question_answer = str(result)
                        question_explanation = f"这是一道简单的加法题，{num1}加上{num2}等于{result}"
                    elif operation == "-":
                        result = num1 - num2
                        question_content = f"计算：{num1} - {num2} = ?"
                        question_answer = str(result)
                        question_explanation = f"这是一道简单的减法题，{num1}减去{num2}等于{result}"
                    elif operation == "×":
                        result = num1 * num2
                        question_content = f"计算：{num1} × {num2} = ?"
                        question_answer = str(result)
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
                    tenses = [
                        ("present perfect", "I ____ (study) English for 5 years.", "have studied"),
                        ("past perfect", "He ____ (finish) his homework before he went out.", "had finished"),
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
                        "井底之蛙": "比喻见识短浅的人",
                        "守株待兔": "比喻不主动努力，而存万一的侥幸心理，希望得到意外的收获"
                    }
                    idiom, meaning = random.choice(list(idioms.items()))
                    question_content = f"解释成语'画龙点睛'的意思"
                    question_answer = meaning
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
                question_content = f"{category_name}相关问题：{random.choice(['什么是', '请解释', '简述'])}{random.choice(['基本概念', '主要原理', '重要应用'])}"
                question_answer = f"{category_name}相关答案"
                question_explanation = f"这是一道关于{category_name}的题目，答案是{question_answer}"
            
            # 生成题目选项（如果是选择题）
            options = []
            if question_type in ["single_choice", "multiple_choice"]:
                # 生成选项
                options = [question_answer]
                # 生成干扰选项
                for _ in range(3):
                    if category_name == "数学" or not category_name:
                        # 数学题干扰选项
                        if level_value <= 2:
                            distractor = str(int(question_answer) + random.randint(-10, 10))
                        else:
                            distractor = f"{float(question_answer.split(',')[0].split('=')[1]) + random.uniform(-5, 5):.2f}"
                    else:
                        # 其他学科干扰选项
                        distractor = f"干扰选项{random.randint(1, 100)}"
                    options.append(distractor)
                # 随机打乱选项
                random.shuffle(options)
            
            # 确定题目类型
            final_question_type = question_type if question_type else "short_answer"
            
            # 生成标签
            tags = [category_name if category_name else "数学", 
                   level_name if level_name else "中级", 
                   final_question_type]
            
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
            return question
        except Exception as e:
            logger.error(f"AI生成题目失败: {str(e)}")
            return None
    
    def generate_questions_by_ai(self, count: int = 5, category_name: str = None, 
                                level_name: str = None, question_type: str = None) -> List[Question]:
        """
        使用AI批量生成题目
        
        Args:
            count: 生成题目的数量
            category_name: 题目分类名称
            level_name: 题目难度名称
            question_type: 题目类型
            
        Returns:
            生成的题目列表
        """
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
