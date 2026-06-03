# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库迁移脚本 - 统一考试系统表结构
确保各模块使用一致的主键类型和表结构
"""

import os
import sys
import sqlite3
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def log(message: str, symbol: str = '📋'):
    """日志记录"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


def backup_database():
    """备份数据库"""
    backup_path = f"{DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(DATABASE_PATH, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
        log(f"数据库备份成功: {backup_path}", '✅')
        return True
    except Exception as e:
        log(f"数据库备份失败: {str(e)}", '❌')
        return False


def migrate_exam_sessions():
    """迁移考试会话表"""
    log('迁移考试会话表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查现有表结构
        cursor.execute("PRAGMA table_info(exam_sessions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if columns and columns[0][2].upper() == 'INTEGER':
            log('检测到exam_sessions表id字段为INTEGER类型,需要迁移...', '⚠️')
            
            # 创建临时表
            cursor.execute('''
                CREATE TABLE exam_sessions_new (
                    id TEXT PRIMARY KEY,
                    exam_id TEXT,
                    user_id INTEGER,
                    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    end_time TEXT,
                    duration INTEGER,
                    score REAL,
                    status TEXT DEFAULT 'in_progress',
                    ip_address TEXT,
                    device_info TEXT,
                    proctor_log TEXT,
                    ai_analysis TEXT,
                    metadata TEXT,
                    total_questions INTEGER DEFAULT 0,
                    correct_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 迁移数据
            cursor.execute('SELECT * FROM exam_sessions')
            rows = cursor.fetchall()
            
            for row in rows:
                old_id = row[0]
                new_id = f"SES_{uuid.uuid4().hex[:12]}"
                
                # 构建INSERT语句
                if len(row) >= 16:
                    cursor.execute('''
                        INSERT INTO exam_sessions_new 
                        (id, exam_id, user_id, start_time, end_time, duration, score, status,
                         ip_address, device_info, proctor_log, ai_analysis, metadata, 
                         total_questions, correct_count, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (new_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                          row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15]))
                elif len(row) >= 9:
                    cursor.execute('''
                        INSERT INTO exam_sessions_new 
                        (id, exam_id, user_id, start_time, end_time, status, score, 
                         ai_analysis, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (new_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))
            
            # 删除旧表并重命名新表
            cursor.execute('DROP TABLE exam_sessions')
            cursor.execute('ALTER TABLE exam_sessions_new RENAME TO exam_sessions')
            
            log('exam_sessions表迁移完成', '✅')
        else:
            log('exam_sessions表结构已正确', '✅')
            
        conn.commit()
    except Exception as e:
        log(f'exam_sessions表迁移失败: {str(e)}', '❌')
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate_exam_answers():
    """迁移考试答案表"""
    log('迁移考试答案表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(exam_answers)")
        columns = cursor.fetchall()
        
        if columns and columns[0][2].upper() == 'INTEGER':
            log('检测到exam_answers表id字段为INTEGER类型,需要迁移...', '⚠️')
            
            cursor.execute('''
                CREATE TABLE exam_answers_new (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    question_id TEXT,
                    user_answer TEXT,
                    correct_answer TEXT,
                    is_correct BOOLEAN,
                    answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    time_spent INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES exam_sessions(id)
                )
            ''')
            
            cursor.execute('SELECT * FROM exam_answers')
            rows = cursor.fetchall()
            
            for row in rows:
                new_id = f"ANS_{uuid.uuid4().hex[:12]}"
                cursor.execute('''
                    INSERT INTO exam_answers_new 
                    (id, session_id, question_id, user_answer, correct_answer, is_correct, answered_at, time_spent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (new_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
            
            cursor.execute('DROP TABLE exam_answers')
            cursor.execute('ALTER TABLE exam_answers_new RENAME TO exam_answers')
            
            log('exam_answers表迁移完成', '✅')
        else:
            log('exam_answers表结构已正确', '✅')
            
        conn.commit()
    except Exception as e:
        log(f'exam_answers表迁移失败: {str(e)}', '❌')
        conn.rollback()
        raise
    finally:
        conn.close()


def create_exam_papers_table():
    """创建试卷表(如果不存在)"""
    log('创建/更新试卷表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES exams(id)
            )
        ''')
        
        log('exam_papers表创建/更新完成', '✅')
        conn.commit()
    except Exception as e:
        log(f'exam_papers表创建失败: {str(e)}', '❌')
        raise
    finally:
        conn.close()


def create_exam_results_table():
    """创建考试结果表(如果不存在)"""
    log('创建/更新考试结果表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_paper_id) REFERENCES exam_papers(id)
            )
        ''')
        
        log('exam_results表创建/更新完成', '✅')
        conn.commit()
    except Exception as e:
        log(f'exam_results表创建失败: {str(e)}', '❌')
        raise
    finally:
        conn.close()


def create_question_analysis_table():
    """创建题目分析表(如果不存在)"""
    log('创建/更新题目分析表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        log('question_analysis表创建/更新完成', '✅')
        conn.commit()
    except Exception as e:
        log(f'question_analysis表创建失败: {str(e)}', '❌')
        raise
    finally:
        conn.close()


def create_user_exam_progress_table():
    """创建用户考试进度表(如果不存在)"""
    log('创建/更新用户考试进度表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_exam_progress (
                user_id TEXT NOT NULL,
                exam_id TEXT NOT NULL,
                current_question INTEGER NOT NULL DEFAULT 0,
                answers TEXT NOT NULL DEFAULT '{}',
                time_spent INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, exam_id)
            )
        ''')
        
        log('user_exam_progress表创建/更新完成', '✅')
        conn.commit()
    except Exception as e:
        log(f'user_exam_progress表创建失败: {str(e)}', '❌')
        raise
    finally:
        conn.close()


def create_ai_generated_questions_table():
    """创建AI生成题目表(如果不存在)"""
    log('创建/更新AI生成题目表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_generated_questions (
                id TEXT PRIMARY KEY,
                exam_id TEXT,
                question_type TEXT,
                language TEXT,
                difficulty TEXT,
                content TEXT,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                generated_by TEXT,
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                used_count INTEGER DEFAULT 0
            )
        ''')
        
        log('ai_generated_questions表创建/更新完成', '✅')
        conn.commit()
    except Exception as e:
        log(f'ai_generated_questions表创建失败: {str(e)}', '❌')
        raise
    finally:
        conn.close()


def create_indexes():
    """创建索引"""
    log('创建索引...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    indexes = [
        ('idx_exam_sessions_user_id', 'exam_sessions', ['user_id']),
        ('idx_exam_sessions_exam_id', 'exam_sessions', ['exam_id']),
        ('idx_exam_sessions_status', 'exam_sessions', ['status']),
        ('idx_exam_answers_session_id', 'exam_answers', ['session_id']),
        ('idx_exam_papers_exam_id', 'exam_papers', ['exam_id']),
        ('idx_exam_papers_user_id', 'exam_papers', ['user_id']),
        ('idx_exam_papers_status', 'exam_papers', ['status']),
        ('idx_exam_results_exam_id', 'exam_results', ['exam_id']),
        ('idx_exam_results_user_id', 'exam_results', ['user_id']),
        ('idx_question_analysis_question_id', 'question_analysis', ['question_id']),
        ('idx_question_analysis_user_id', 'question_analysis', ['user_id']),
        ('idx_user_exam_progress_user_id', 'user_exam_progress', ['user_id']),
        ('idx_user_exam_progress_exam_id', 'user_exam_progress', ['exam_id']),
        ('idx_ai_generated_questions_exam_id', 'ai_generated_questions', ['exam_id']),
    ]
    
    try:
        for idx_name, table_name, columns in indexes:
            columns_str = ', '.join(columns)
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({columns_str})')
                log(f'  ✅ 创建索引 {idx_name}', '✅')
            except Exception as e:
                log(f'  ⚠️ 索引 {idx_name} 创建失败(可能已存在): {str(e)}', '⚠️')
        
        conn.commit()
        log('索引创建完成', '✅')
    except Exception as e:
        log(f'创建索引失败: {str(e)}', '❌')
        raise
    finally:
        conn.close()


def verify_tables():
    """验证表结构"""
    log('验证表结构...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    tables = ['exam_sessions', 'exam_answers', 'exam_papers', 
              'exam_results', 'question_analysis', 'user_exam_progress', 'ai_generated_questions']
    
    try:
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            if columns:
                id_type = columns[0][2].upper()
                log(f'  ✅ {table}: id字段类型 = {id_type}', '✅')
                if id_type != 'TEXT':
                    log(f'  ⚠️ {table}: id字段类型应为TEXT,当前为{id_type}', '⚠️')
            else:
                log(f'  ❌ {table}: 表不存在', '❌')
        
        conn.close()
        log('表结构验证完成', '✅')
    except Exception as e:
        log(f'验证表结构失败: {str(e)}', '❌')
        raise


def main():
    """主函数"""
    print('\n' + '='*60)
    print('📝 数据库迁移 - 统一考试系统表结构')
    print('='*60 + '\n')
    
    # 1. 备份数据库
    if not backup_database():
        print('数据库备份失败,终止迁移')
        return
    
    # 2. 迁移表结构
    try:
        migrate_exam_sessions()
        migrate_exam_answers()
        create_exam_papers_table()
        create_exam_results_table()
        create_question_analysis_table()
        create_user_exam_progress_table()
        create_ai_generated_questions_table()
        
        # 3. 创建索引
        create_indexes()
        
        # 4. 验证表结构
        verify_tables()
        
        print('\n' + '='*60)
        log('数据库迁移完成!', '✅')
        print('='*60 + '\n')
        
    except Exception as e:
        print(f'\n❌ 数据库迁移失败: {str(e)}')
        print('建议从备份恢复数据库')


if __name__ == '__main__':
    main()
