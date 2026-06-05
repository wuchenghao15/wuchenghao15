#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学内容管理模型
包含教学大纲、教学备课、教案管理功能
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from app.utils.logging import logger


class TeachingSyllabus:
    """教学大纲模型"""
    
    table_name = 'teaching_syllabus'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key in ['id', 'grade', 'subject', 'semester', 'title', 'description', 'content', 
                    'objectives', 'knowledge_points', 'teaching_hours', 'difficulty_level',
                    'prerequisites', 'teaching_methods', 'assessment_methods', 
                    'reference_materials', 'created_by', 'updated_by', 'status', 
                    'version', 'created_at', 'updated_at']:
            if hasattr(self, key):
                value = getattr(self, key)
                if key in ['objectives', 'knowledge_points', 'prerequisites', 
                          'teaching_methods', 'assessment_methods', 'reference_materials']:
                    if isinstance(value, str):
                        try:
                            result[key] = json.loads(value)
                        except Exception:
                            result[key] = []
                    else:
                        result[key] = value
                else:
                    result[key] = value
        return result


class TeachingPreparation:
    """教学备课模型"""
    
    table_name = 'teaching_preparation'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key in ['id', 'syllabus_id', 'grade', 'subject', 'lesson_title', 
                    'lesson_number', 'teaching_hours', 'teaching_date', 'objectives',
                    'key_points', 'difficult_points', 'teaching_aids', 'teaching_process',
                    'time_allocation', 'homework', 'reflection', 'teaching_resources',
                    'created_by', 'updated_by', 'status', 'version', 'created_at', 'updated_at']:
            if hasattr(self, key):
                value = getattr(self, key)
                if key in ['objectives', 'key_points', 'difficult_points', 
                          'teaching_aids', 'time_allocation', 'teaching_resources']:
                    if isinstance(value, str):
                        try:
                            result[key] = json.loads(value)
                        except Exception:
                            result[key] = []
                    else:
                        result[key] = value
                else:
                    result[key] = value
        return result


class TeachingPlan:
    """教案模型"""
    
    table_name = 'teaching_plan'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key in ['id', 'syllabus_id', 'preparation_id', 'grade', 'subject', 
                    'lesson_title', 'lesson_type', 'class_duration', 'students_count',
                    'teaching_objectives', 'knowledge_skills', 'emotional_attitudes',
                    'key_points', 'difficult_points', 'teaching_methods', 'teaching_aids',
                    'teaching_process', 'board_design', 'activity_design', 
                    'question_design', 'assessment_design', 'homework_design',
                    'after_class_reflection', 'teaching_notes', 'attachments',
                    'created_by', 'updated_by', 'status', 'version', 'created_at', 'updated_at']:
            if hasattr(self, key):
                value = getattr(self, key)
                if key in ['teaching_objectives', 'knowledge_skills', 'emotional_attitudes',
                          'key_points', 'difficult_points', 'teaching_methods', 
                          'teaching_aids', 'activity_design', 'question_design', 'attachments']:
                    if isinstance(value, str):
                        try:
                            result[key] = json.loads(value)
                        except Exception:
                            result[key] = []
                    else:
                        result[key] = value
                else:
                    result[key] = value
        return result


class TeachingContentManager:
    """教学内容管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用项目的app.db
            import os
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建教学大纲表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teaching_syllabus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grade TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    semester TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT NOT NULL,
                    objectives TEXT DEFAULT '[]',
                    knowledge_points TEXT DEFAULT '[]',
                    teaching_hours INTEGER DEFAULT 0,
                    difficulty_level TEXT DEFAULT 'medium',
                    prerequisites TEXT DEFAULT '[]',
                    teaching_methods TEXT DEFAULT '[]',
                    assessment_methods TEXT DEFAULT '[]',
                    reference_materials TEXT DEFAULT '[]',
                    created_by TEXT DEFAULT 'system',
                    updated_by TEXT,
                    status TEXT DEFAULT 'active',
                    version INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建教学备课表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teaching_preparation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    syllabus_id INTEGER,
                    grade TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    lesson_title TEXT NOT NULL,
                    lesson_number INTEGER DEFAULT 0,
                    teaching_hours INTEGER DEFAULT 1,
                    teaching_date TEXT,
                    objectives TEXT DEFAULT '[]',
                    key_points TEXT DEFAULT '[]',
                    difficult_points TEXT DEFAULT '[]',
                    teaching_aids TEXT DEFAULT '[]',
                    teaching_process TEXT NOT NULL,
                    time_allocation TEXT DEFAULT '[]',
                    homework TEXT,
                    reflection TEXT,
                    teaching_resources TEXT DEFAULT '[]',
                    created_by TEXT DEFAULT 'system',
                    updated_by TEXT,
                    status TEXT DEFAULT 'draft',
                    version INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建教案表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teaching_plan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    syllabus_id INTEGER,
                    preparation_id INTEGER,
                    grade TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    lesson_title TEXT NOT NULL,
                    lesson_type TEXT DEFAULT 'new',
                    class_duration INTEGER DEFAULT 40,
                    students_count INTEGER DEFAULT 45,
                    teaching_objectives TEXT DEFAULT '[]',
                    knowledge_skills TEXT DEFAULT '[]',
                    emotional_attitudes TEXT DEFAULT '[]',
                    key_points TEXT DEFAULT '[]',
                    difficult_points TEXT DEFAULT '[]',
                    teaching_methods TEXT DEFAULT '[]',
                    teaching_aids TEXT DEFAULT '[]',
                    teaching_process TEXT NOT NULL,
                    board_design TEXT,
                    activity_design TEXT DEFAULT '[]',
                    question_design TEXT DEFAULT '[]',
                    assessment_design TEXT,
                    homework_design TEXT,
                    after_class_reflection TEXT,
                    teaching_notes TEXT,
                    attachments TEXT DEFAULT '[]',
                    created_by TEXT DEFAULT 'system',
                    updated_by TEXT,
                    status TEXT DEFAULT 'draft',
                    version INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("教学内容数据库初始化完成")
    
    def create_syllabus(self, data: Dict[str, Any]) -> int:
        """创建教学大纲"""
        # 序列化JSON字段
        data_copy = data.copy()
        for field in ['objectives', 'knowledge_points', 'prerequisites', 
                     'teaching_methods', 'assessment_methods', 'reference_materials']:
            if field in data_copy and isinstance(data_copy[field], list):
                data_copy[field] = json.dumps(data_copy[field], ensure_ascii=False)
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_copy['created_at'] = now
        data_copy['updated_at'] = now
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ', '.join(['?' for _ in data_copy])
            columns = ', '.join(data_copy.keys())
            values = tuple(data_copy.values())
            
            cursor.execute(f'INSERT INTO teaching_syllabus ({columns}) VALUES ({placeholders})', values)
            return cursor.lastrowid
    
    def create_preparation(self, data: Dict[str, Any]) -> int:
        """创建教学备课"""
        data_copy = data.copy()
        for field in ['objectives', 'key_points', 'difficult_points', 
                     'teaching_aids', 'time_allocation', 'teaching_resources']:
            if field in data_copy and isinstance(data_copy[field], list):
                data_copy[field] = json.dumps(data_copy[field], ensure_ascii=False)
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_copy['created_at'] = now
        data_copy['updated_at'] = now
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ', '.join(['?' for _ in data_copy])
            columns = ', '.join(data_copy.keys())
            values = tuple(data_copy.values())
            
            cursor.execute(f'INSERT INTO teaching_preparation ({columns}) VALUES ({placeholders})', values)
            return cursor.lastrowid
    
    def create_plan(self, data: Dict[str, Any]) -> int:
        """创建教案"""
        data_copy = data.copy()
        for field in ['teaching_objectives', 'knowledge_skills', 'emotional_attitudes',
                     'key_points', 'difficult_points', 'teaching_methods', 
                     'teaching_aids', 'activity_design', 'question_design', 'attachments']:
            if field in data_copy and isinstance(data_copy[field], list):
                data_copy[field] = json.dumps(data_copy[field], ensure_ascii=False)
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_copy['created_at'] = now
        data_copy['updated_at'] = now
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ', '.join(['?' for _ in data_copy])
            columns = ', '.join(data_copy.keys())
            values = tuple(data_copy.values())
            
            cursor.execute(f'INSERT INTO teaching_plan ({columns}) VALUES ({placeholders})', values)
            return cursor.lastrowid
    
    def get_syllabus_count(self) -> int:
        """获取教学大纲数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teaching_syllabus WHERE status = 'active'")
            return cursor.fetchone()[0]
    
    def get_preparation_count(self) -> int:
        """获取教学备课数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teaching_preparation")
            return cursor.fetchone()[0]
    
    def get_plan_count(self) -> int:
        """获取教案数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teaching_plan")
            return cursor.fetchone()[0]
    
    def get_published_preparation_count(self) -> int:
        """获取已发布的教学备课数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teaching_preparation WHERE status = 'published'")
            return cursor.fetchone()[0]
    
    def get_published_plan_count(self) -> int:
        """获取已发布的教案数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teaching_plan WHERE status = 'published'")
            return cursor.fetchone()[0]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取教学内容统计"""
        return {
            'syllabus_count': self.get_syllabus_count(),
            'preparation_count': self.get_preparation_count(),
            'plan_count': self.get_plan_count(),
            'published_preparation_count': self.get_published_preparation_count(),
            'published_plan_count': self.get_published_plan_count()
        }


# 创建全局实例
try:
    teaching_content_manager = TeachingContentManager()
except Exception as e:
    logger.warning(f"教学内容管理器初始化失败: {e}")
    teaching_content_manager = None

