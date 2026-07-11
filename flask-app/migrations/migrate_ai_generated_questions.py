# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - AI生成题目元数据表
添加ai_generated_questions表，记录AI生成题目的元数据信息
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       'split_databases/question.db')


def migrate():
    """执行数据库迁移"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(ai_generated_questions)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            if 'question_id' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN question_id INTEGER")
                logger.info("[数据库迁移] 添加question_id字段")
            
            if 'generation_source' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN generation_source TEXT")
                logger.info("[数据库迁移] 添加generation_source字段")
            
            if 'confidence_score' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN confidence_score REAL DEFAULT 0.0")
                logger.info("[数据库迁移] 添加confidence_score字段")
            
            if 'review_status' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN review_status TEXT DEFAULT 'pending'")
                logger.info("[数据库迁移] 添加review_status字段")
            
            if 'generation_time' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN generation_time TEXT")
                logger.info("[数据库迁移] 添加generation_time字段")
            
            if 'generator_model' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN generator_model TEXT")
                logger.info("[数据库迁移] 添加generator_model字段")
            
            if 'source_text' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN source_text TEXT")
                logger.info("[数据库迁移] 添加source_text字段")
            
            if 'created_at' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
                logger.info("[数据库迁移] 添加created_at字段")
            
            if 'updated_at' not in existing_columns:
                cursor.execute("ALTER TABLE ai_generated_questions ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP")
                logger.info("[数据库迁移] 添加updated_at字段")
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ai_generated_question_id 
                    ON ai_generated_questions(question_id)
                """)
                logger.info("[数据库迁移] 创建idx_ai_generated_question_id索引")
            except Exception:
                pass
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ai_generated_subject 
                    ON ai_generated_questions(subject)
                """)
                logger.info("[数据库迁移] 创建idx_ai_generated_subject索引")
            except Exception:
                pass
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ai_generated_review_status 
                    ON ai_generated_questions(review_status)
                """)
                logger.info("[数据库迁移] 创建idx_ai_generated_review_status索引")
            except Exception:
                pass
            
            conn.commit()
            logger.info("[数据库迁移] ai_generated_questions表迁移完成")
            
            cursor.execute("SELECT COUNT(*) FROM ai_generated_questions")
            count = cursor.fetchone()[0]
            logger.info(f"[数据库迁移] 当前ai_generated_questions表记录数: {count}")
            
            return True
    except Exception as e:
        logger.error(f"[数据库迁移] ai_generated_questions表迁移失败: {e}")
        return False


def verify_migration():
    """验证迁移结果"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='ai_generated_questions'
            """)
            result = cursor.fetchone()
            
            if result:
                logger.info("[迁移验证] ai_generated_questions表已存在")
                
                cursor.execute("PRAGMA table_info(ai_generated_questions)")
                columns = cursor.fetchall()
                logger.info(f"[迁移验证] 表结构: {[col[1] for col in columns]}")
                
                return True
            else:
                logger.error("[迁移验证] ai_generated_questions表不存在")
                return False
    except Exception as e:
        logger.error(f"[迁移验证] 验证失败: {e}")
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("开始执行数据库迁移...")
    
    if migrate():
        print("迁移执行成功")
        
        if verify_migration():
            print("迁移验证成功")
        else:
            print("迁移验证失败")
    else:
        print("迁移执行失败")