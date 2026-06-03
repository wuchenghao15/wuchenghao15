# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
基于用户等级的出题服务
负责根据用户等级生成合适难度的题目,实现向上兼容的出题逻辑
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LevelBasedQuestionGenerator:
    """基于用户等级的题目生成器"""

    def __init__(self, db_path="app.db"):
        """初始化题目生成器"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        self.difficulty_distribution = {
            'user_level': 0.7,
            'user_level_plus_1': 0.2,
            'user_level_plus_2': 0.1
        }

        self.level_map = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }

        self.reverse_level_map = {
            1: 'beginner',
            2: 'intermediate',
            3: 'advanced',
            4: 'expert'
        }

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_user_level(self, user_id):
        """
        获取用户等级

        Args:
            user_id: 用户ID

        Returns:
            用户等级(数字),默认为1(beginner)
        """
        if not self.connect():
            return 1

        try:
            self.cursor.execute(
                'SELECT level FROM users WHERE id = ?',
                (user_id,)
            )
            result = self.cursor.fetchone()

            if result:
                level_name = result[0]
                return self.level_map.get(level_name, 1)
            return 1
        except Exception as e:
            logger.error(f"获取用户等级失败: {str(e)}")
            return 1
        finally:
            self.close()

    def _get_questions_by_level(self, level, count, language):
        """
        根据难度等级获取题目

        Args:
            level: 难度等级(数字)
            count: 需要的题目数量
            language: 语言

        Returns:
            题目列表
        """
        if not self.connect():
            return []

        try:
            self.cursor.execute(
                'SELECT * FROM questions WHERE level_id = ? AND language = ? ORDER BY RANDOM() LIMIT ?',
                (level, language, count)
            )
            questions = self.cursor.fetchall()
            return questions
        except Exception as e:
            logger.error(f"获取题目失败: {str(e)}")
            return []
        finally:
            self.close()

    def generate_questions_for_user(self, user_id, total_count=20, language='zh'):
        """
        为用户生成题目

        Args:
            user_id: 用户ID
            total_count: 总题目数量
            language: 语言

        Returns:
            题目列表
        """
        user_level = self.get_user_level(user_id)

        level_1_count = int(total_count * self.difficulty_distribution['user_level'])
        level_2_count = int(total_count * self.difficulty_distribution['user_level_plus_1'])
        level_3_count = total_count - level_1_count - level_2_count

        questions = []

        level_1_questions = self._get_questions_by_level(user_level, level_1_count, language)
        questions.extend(level_1_questions)

        if user_level < 4:
            level_2_questions = self._get_questions_by_level(user_level + 1, level_2_count, language)
            questions.extend(level_2_questions)

        if user_level < 3:
            level_3_questions = self._get_questions_by_level(user_level + 2, level_3_count, language)
            questions.extend(level_3_questions)

        random.shuffle(questions)

        return questions

    def get_level_name(self, level):
        """获取等级名称"""
        return self.reverse_level_map.get(level, 'beginner')

    def get_level_number(self, level_name):
        """获取等级数字"""
        return self.level_map.get(level_name, 1)


level_based_generator = None


def get_level_based_generator():
    """获取题目生成器实例"""
    global level_based_generator
    if level_based_generator is None:
        level_based_generator = LevelBasedQuestionGenerator()
    return level_based_generator
