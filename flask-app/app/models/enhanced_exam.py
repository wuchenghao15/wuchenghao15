# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强的考试系统模型
"""

import time
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger
import logging


class EnhancedExam:
    """增强的考试模型"""

    def __init__(self):
        """初始化考试模型"""
        self._create_tables()

    def _create_tables(self):
        """创建必要的表"""
        try:
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    duration INTEGER,
                    total_questions INTEGER,
                    passing_score REAL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    content TEXT NOT NULL,
                    options TEXT,
                    correct_answer TEXT,
                    difficulty INTEGER DEFAULT 1,
                    points REAL DEFAULT 1.0,
                    audio_url TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')

            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS exam_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    user_id INTEGER,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    answers TEXT,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')

            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS answer_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_record_id INTEGER,
                    question_id INTEGER,
                    user_answer TEXT,
                    is_correct INTEGER,
                    points_earned REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exam_record_id) REFERENCES exam_records(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')

            logger.info("考试系统表结构创建完成")

        except Exception as e:
            logger.error(f"创建考试系统表结构失败: {str(e)}")

    def create_exam(self, name: str, description: str, duration: int, total_questions: int, passing_score: float) -> int:
        """
        创建新考试

        Args:
            name: 考试名称
            description: 考试描述
            duration: 考试时长(分钟)
            total_questions: 题目总数
            passing_score: 及格分数

        Returns:
            考试ID
        """
        try:
            db_manager.execute(
                '''
                INSERT INTO exams (name, description, duration, total_questions, passing_score)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (name, description, duration, total_questions, passing_score)
            )

            result = db_manager.fetch_one('SELECT last_insert_rowid()')
            if result:
                if isinstance(result, dict):
                    return result['last_insert_rowid()']
                return result[0]
            return None
        except Exception as e:
            logger.error(f"创建考试失败: {str(e)}")
            return None
