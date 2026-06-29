#!/usr/bin/env python3
"""
错题管理模型
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption


class ErrorQuestionManager:
    """错题管理器"""

    def __init__(self):
        """初始化错题管理器"""
        self._create_tables()

    def _create_tables(self):
        """创建必要的表"""
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            error_tags_table = table_encryption.encrypt_table_name('error_tags')
            error_question_tags_table = table_encryption.encrypt_table_name('error_question_tags')
            review_plans_table = table_encryption.encrypt_table_name('review_plans')
            teacher_ai_transfer_table = table_encryption.encrypt_table_name('teacher_ai_transfer')
            error_statistics_table = table_encryption.encrypt_table_name('error_statistics')
            user_table = table_encryption.encrypt_table_name('user')
            questions_table = table_encryption.encrypt_table_name('questions')
            exam_records_table = table_encryption.encrypt_table_name('exam_records')

            # 创建错题表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_questions_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    exam_record_id INTEGER NOT NULL,
                    user_answer TEXT,
                    correct_answer TEXT,
                    error_reason TEXT,
                    error_type TEXT,
                    knowledge_point TEXT,
                    difficulty_level INTEGER,
                    mastery_level INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    last_review_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id),
                    FOREIGN KEY (question_id) REFERENCES {questions_table}(id),
                    FOREIGN KEY (exam_record_id) REFERENCES {exam_records_table}(id)
                )
            ''')

            # 创建错题标签表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_tags_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建错题-标签关联表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_question_tags_table} (
                    error_question_id INTEGER,
                    tag_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (error_question_id, tag_id),
                    FOREIGN KEY (error_question_id) REFERENCES {error_questions_table}(id),
                    FOREIGN KEY (tag_id) REFERENCES {error_tags_table}(id)
                )
            ''')

            # 创建错题复习计划表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {review_plans_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_question_id INTEGER NOT NULL,
                    review_time TIMESTAMP,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id),
                    FOREIGN KEY (error_question_id) REFERENCES {error_questions_table}(id)
                )
            ''')

            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {teacher_ai_transfer_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_question_id INTEGER NOT NULL,
                    transfer_reason TEXT,
                    teacher_feedback TEXT,
                    follow_up_actions TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id),
                    FOREIGN KEY (error_question_id) REFERENCES {error_questions_table}(id)
                )
            ''')

            # 创建错题统计数据表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_statistics_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_errors INTEGER DEFAULT 0,
                    resolved_errors INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            logger.info("错题管理表结构创建完成")
        except Exception as e:
            logger.error(f"创建错题管理表失败: {e}")

    def add_error_question(self, user_id: int, question_id: int, exam_record_id: int,
                           user_answer: str, correct_answer: str, error_reason: str = None,
                           error_type: str = None, knowledge_point: str = None,
                           difficulty_level: int = None) -> int:
        """
        添加错题

        Args:
            user_id: 用户ID
            question_id: 题目ID
            exam_record_id: 考试记录ID
            user_answer: 用户答案
            correct_answer: 正确答案
            error_reason: 错误原因
            error_type: 错误类型
            knowledge_point: 知识点
            difficulty_level: 难度等级

        Returns:
            错题ID
        """
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            error_question_tags_table = table_encryption.encrypt_table_name('error_question_tags')

            existing = db_manager.fetch_one(
                f"SELECT * FROM {error_questions_table} WHERE user_id = ? AND question_id = ?",
                (user_id, question_id)
            )

            if existing:
                # 更新现有错题
                error_id = existing['id'] if isinstance(existing, dict) else existing[0]
                db_manager.execute(
                    f'''
                    UPDATE {error_questions_table}
                    SET user_answer = ?, correct_answer = ?, error_reason = ?,
                        error_type = ?, knowledge_point = ?, difficulty_level = ?,
                        review_count = review_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (user_answer, correct_answer, error_reason, error_type, knowledge_point,
                     difficulty_level, error_id)
                )
            else:
                # 创建新错题
                db_manager.execute(
                    f'''
                    INSERT INTO {error_questions_table} (user_id, question_id, exam_record_id,
                                                user_answer, correct_answer, error_reason,
                                                error_type, knowledge_point, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (user_id, question_id, exam_record_id, user_answer, correct_answer,
                     error_reason, error_type, knowledge_point, difficulty_level)
                )

                # 获取最后插入的ID
                result = db_manager.fetch_one('SELECT last_insert_rowid()')
                if result:
                    error_id = result['last_insert_rowid()'] if isinstance(result, dict) else result[0]
                else:
                    error_id = -1
            return error_id
        except Exception as e:
            logger.error(f"添加错题失败: {e}")
            return -1

    def _generate_review_plan(self, user_id: int, error_question_id: int, difficulty_level: int):
        """
        自动生成复习计划

        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            difficulty_level: 难度等级
        """
        try:
            import datetime

            # 获取加密后的表名
            review_plans_table = table_encryption.encrypt_table_name('review_plans')

            if difficulty_level == 5:
                intervals = [1, 2, 4, 7, 15]
                priority = 5
            elif difficulty_level == 4:
                intervals = [1, 3, 7, 14]
                priority = 4
            elif difficulty_level == 3:
                intervals = [1, 3, 7]
                priority = 3
            elif difficulty_level == 2:
                intervals = [1, 3]
                priority = 2
            else:
                intervals = [1]
                priority = 1

            # 生成复习计划
            for i, interval in enumerate(intervals):
                review_time = datetime.now() + timedelta(days=interval)
                db_manager.execute(
                    f'''
                    INSERT INTO {review_plans_table} (user_id, error_question_id, review_time, priority)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (user_id, error_question_id, review_time.timestamp(), priority)
                )
        except Exception as e:
            logger.error(f"生成复习计划失败: {e}")


# 创建全局错题管理器实例
error_question_manager = ErrorQuestionManager()
