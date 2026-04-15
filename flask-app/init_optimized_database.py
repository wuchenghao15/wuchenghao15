#!/usr/bin/env python3
"""
初始化优化后的数据库表结构
"""

import os
import sys
import json
from app.utils.db import db_manager
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption


def init_optimized_database():
    """初始化优化后的数据库表结构"""
    logger.info("开始初始化优化后的数据库表结构...")
    
    try:
        # 获取加密后的表名
        error_questions_table = table_encryption.encrypt_table_name('error_questions')
        error_tags_table = table_encryption.encrypt_table_name('error_tags')
        error_question_tags_table = table_encryption.encrypt_table_name('error_question_tags')
        review_plans_table = table_encryption.encrypt_table_name('review_plans')
        teacher_ai_transfer_table = table_encryption.encrypt_table_name('teacher_ai_transfer')
        error_statistics_table = table_encryption.encrypt_table_name('error_statistics')
        learning_analyses_table = table_encryption.encrypt_table_name('learning_analyses')
        learning_interests_table = table_encryption.encrypt_table_name('learning_interests')
        learning_directions_table = table_encryption.encrypt_table_name('learning_directions')
        learning_activities_table = table_encryption.encrypt_table_name('learning_activities')
        questions_table = table_encryption.encrypt_table_name('questions')
        user_table = table_encryption.encrypt_table_name('user')
        exam_records_table = table_encryption.encrypt_table_name('exam_records')
        
        logger.info(f"使用加密表名: {error_questions_table}, {error_tags_table}, {error_statistics_table}")
        
        # 1. 更新错题表结构
        logger.info("更新错题表结构...")
        try:
            # 添加新字段
            db_manager.execute(f'''
                ALTER TABLE {error_questions_table}
                ADD COLUMN knowledge_point TEXT
            ''')
            logger.info("添加 knowledge_point 字段成功")
        except Exception as e:
            logger.warning(f"添加 knowledge_point 字段失败: {str(e)}")
        
        try:
            db_manager.execute(f'''
                ALTER TABLE {error_questions_table}
                ADD COLUMN difficulty_level INTEGER
            ''')
            logger.info("添加 difficulty_level 字段成功")
        except Exception as e:
            logger.warning(f"添加 difficulty_level 字段失败: {str(e)}")
        
        # 2. 更新错题标签表结构
        logger.info("更新错题标签表结构...")
        try:
            db_manager.execute(f'''
                ALTER TABLE {error_tags_table}
                ADD COLUMN category TEXT
            ''')
            logger.info("添加 category 字段成功")
        except Exception as e:
            logger.warning(f"添加 category 字段失败: {str(e)}")
        
        # 3. 更新复习计划表结构
        logger.info("更新复习计划表结构...")
        try:
            db_manager.execute(f'''
                ALTER TABLE {review_plans_table}
                ADD COLUMN review_interval INTEGER
            ''')
            logger.info("添加 review_interval 字段成功")
        except Exception as e:
            logger.warning(f"添加 review_interval 字段失败: {str(e)}")
        
        try:
            db_manager.execute(f'''
                ALTER TABLE {review_plans_table}
                ADD COLUMN priority INTEGER DEFAULT 1
            ''')
            logger.info("添加 priority 字段成功")
        except Exception as e:
            logger.warning(f"添加 priority 字段失败: {str(e)}")
        
        # 4. 更新老师AI交接表结构
        logger.info("更新老师AI交接表结构...")
        try:
            db_manager.execute(f'''
                ALTER TABLE {teacher_ai_transfer_table}
                ADD COLUMN follow_up_actions TEXT
            ''')
            logger.info("添加 follow_up_actions 字段成功")
        except Exception as e:
            logger.warning(f"添加 follow_up_actions 字段失败: {str(e)}")
        
        # 5. 创建错题统计数据表
        logger.info("创建错题统计数据表...")
        try:
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_statistics_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE,
                    total_errors INTEGER DEFAULT 0,
                    resolved_errors INTEGER DEFAULT 0,
                    error_types TEXT,
                    knowledge_points TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            logger.info("创建错题统计数据表成功")
        except Exception as e:
            logger.error(f"创建错题统计数据表失败: {str(e)}")
        
        # 6. 确保学习分析相关表存在
        logger.info("确保学习分析相关表存在...")
        try:
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_analyses_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            logger.info("创建学习分析表成功")
        except Exception as e:
            logger.error(f"创建学习分析表失败: {str(e)}")
        
        try:
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_interests_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    interest_level INTEGER NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            logger.info("创建学习兴趣表成功")
        except Exception as e:
            logger.error(f"创建学习兴趣表失败: {str(e)}")
        
        try:
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_directions_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            logger.info("创建学习方向表成功")
        except Exception as e:
            logger.error(f"创建学习方向表失败: {str(e)}")
        
        try:
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_activities_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT NOT NULL,
                    duration INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            logger.info("创建学习活动表成功")
        except Exception as e:
            logger.error(f"创建学习活动表失败: {str(e)}")
        
        # 7. 确保题目表有必要的字段
        logger.info("确保题目表有必要的字段...")
        fields = [
            ('answer', 'TEXT'),
            ('explanation', 'TEXT'),
            ('category_id', 'INTEGER'),
            ('language_id', 'INTEGER'),
            ('level_id', 'INTEGER'),
            ('question_type', 'TEXT'),
            ('difficulty_score', 'REAL'),
            ('discrimination_index', 'REAL'),
            ('usage_count', 'INTEGER'),
            ('correct_rate', 'REAL'),
            ('audio_url', 'TEXT'),
            ('image_url', 'TEXT'),
            ('video_url', 'TEXT'),
            ('time_limit', 'INTEGER'),
            ('score', 'INTEGER'),
            ('created_at', 'TIMESTAMP'),
            ('updated_at', 'TIMESTAMP'),
            ('type', 'TEXT'),
            ('options', 'TEXT'),
            ('tags', 'TEXT')
        ]
        
        for field_name, field_type in fields:
            try:
                db_manager.execute(f'''
                    ALTER TABLE {questions_table}
                    ADD COLUMN {field_name} {field_type}
                ''')
                logger.info(f"添加 {field_name} 字段成功")
            except Exception as e:
                logger.warning(f"添加 {field_name} 字段失败: {str(e)}")
        
        logger.info("数据库表结构初始化完成！")
        return True
        
    except Exception as e:
        logger.error(f"初始化数据库表结构失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("初始化优化后的数据库表结构...")
    success = init_optimized_database()
    if success:
        logger.info("数据库表结构初始化成功！")
    else:
        logger.error("数据库表结构初始化失败！")
