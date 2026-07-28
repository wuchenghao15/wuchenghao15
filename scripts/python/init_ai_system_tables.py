#!/usr/bin/env python3
"""
AI系统数据库表初始化脚本
根据AI系统操作规范创建所需的数据库表
"""

import sqlite3
import os
import json
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def init_ai_employees_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            employee_type TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            capabilities TEXT DEFAULT '[]',
            personality TEXT DEFAULT '{}',
            learning_progress REAL DEFAULT 0.0,
            empowerment_enabled INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_employees 表已创建/验证")

def init_ai_engine_config_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_engine_config (
            engine_type TEXT PRIMARY KEY,
            config TEXT DEFAULT '{}',
            version TEXT DEFAULT '1.0',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_engine_config 表已创建/验证")

def init_ai_cluster_config_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_cluster_config (
            cluster_id TEXT PRIMARY KEY,
            cluster_type TEXT NOT NULL,
            config TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_cluster_config 表已创建/验证")

def init_ai_employee_config_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_config (
            employee_id TEXT PRIMARY KEY,
            employee_type TEXT NOT NULL,
            capabilities TEXT DEFAULT '[]',
            config TEXT DEFAULT '{}',
            assigned_cluster TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_employee_config 表已创建/验证")

def init_ai_cluster_employee_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_cluster_employee (
            cluster_id TEXT,
            employee_id TEXT,
            FOREIGN KEY (cluster_id) REFERENCES ai_cluster_config(cluster_id),
            FOREIGN KEY (employee_id) REFERENCES ai_employee_config(employee_id),
            PRIMARY KEY (cluster_id, employee_id)
        )
    ''')
    logger.info("  ✅ ai_cluster_employee 表已创建/验证")

def init_ai_brain_knowledge_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
            knowledge_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            knowledge_type TEXT DEFAULT 'domain',
            source TEXT DEFAULT 'system',
            tags TEXT DEFAULT '[]',
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_brain_knowledge 表已创建/验证")

def init_ai_brain_activity_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_brain_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id TEXT,
            activity_type TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (knowledge_id) REFERENCES ai_brain_knowledge(knowledge_id)
        )
    ''')
    logger.info("  ✅ ai_brain_activity 表已创建/验证")

def init_ai_operation_logs_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            target TEXT NOT NULL,
            operator TEXT,
            details TEXT DEFAULT '{}',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_operation_logs 表已创建/验证")

def init_ai_engine_logs_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_engine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engine_type TEXT NOT NULL,
            prompt_hash TEXT,
            response_status INTEGER,
            latency REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✅ ai_engine_logs 表已创建/验证")

def init_ai_task_logs_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            employee_id TEXT,
            task_type TEXT,
            status TEXT DEFAULT 'running',
            result TEXT DEFAULT '{}',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (employee_id) REFERENCES ai_employees(employee_id)
        )
    ''')
    logger.info("  ✅ ai_task_logs 表已创建/验证")

def init_ai_employee_empowerment_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_empowerment (
            employee_id TEXT PRIMARY KEY,
            personality_type TEXT DEFAULT 'analytical',
            traits TEXT DEFAULT '{}',
            emotion_state TEXT DEFAULT 'neutral',
            learning_domain TEXT DEFAULT 'general_programming',
            knowledge_points INTEGER DEFAULT 0,
            learning_resources TEXT DEFAULT '[]',
            empowerment_level INTEGER DEFAULT 1,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES ai_employees(employee_id)
        )
    ''')
    logger.info("  ✅ ai_employee_empowerment 表已创建/验证")

def init_ai_employee_learning_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            learning_entry TEXT DEFAULT '{}',
            proficiency_gain REAL DEFAULT 0.0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES ai_employees(employee_id)
        )
    ''')
    logger.info("  ✅ ai_employee_learning 表已创建/验证")

def init_all_tables():
    logger.info("=== AI系统数据库表初始化 ===")
    logger.info(f"时间: {datetime.now()}")
    logger.info(f"数据库: {DATABASE_PATH}")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        logger.info("\n1. 初始化AI员工相关表...")
        init_ai_employees_table(conn)
        init_ai_employee_config_table(conn)
        init_ai_employee_empowerment_table(conn)
        init_ai_employee_learning_table(conn)
        
        logger.info("\n2. 初始化AI引擎相关表...")
        init_ai_engine_config_table(conn)
        init_ai_engine_logs_table(conn)
        
        logger.info("\n3. 初始化AI集群相关表...")
        init_ai_cluster_config_table(conn)
        init_ai_cluster_employee_table(conn)
        
        logger.info("\n4. 初始化AI脑库相关表...")
        init_ai_brain_knowledge_table(conn)
        init_ai_brain_activity_table(conn)
        
        logger.info("\n5. 初始化AI操作日志相关表...")
        init_ai_operation_logs_table(conn)
        init_ai_task_logs_table(conn)
        
        conn.commit()
        conn.close()
        
        logger.info("\n=== 所有AI系统表初始化完成 ===")
        
        # 验证表创建结果
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ai_%'")
        tables = cursor.fetchall()
        conn.close()
        
        logger.info(f"\n已创建的AI相关表 ({len(tables)} 张):")
        for table in sorted(tables):
            logger.info(f"  - {table[0]}")
            
    except Exception as e:
        logger.info(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_all_tables()