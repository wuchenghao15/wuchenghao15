#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI自动化系统数据库初始化"""

import sqlite3
import os
from datetime import datetime

def init_ai_automation_tables(db_path='app.db'):
    """初始化AI自动化系统所需的数据库表"""
    print("初始化AI自动化系统数据库表...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS ai_learning_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learning_cycle INTEGER,
            knowledge_points INTEGER,
            patterns_learned INTEGER,
            timestamp TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_usage REAL,
            memory_usage REAL,
            disk_usage REAL,
            active_tasks INTEGER
        )''',
        
        '''CREATE TABLE IF NOT EXISTS system_status (
            status_id TEXT PRIMARY KEY,
            status TEXT,
            last_update TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT,
            message TEXT,
            timestamp TEXT,
            status TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS automation_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            schedule_type TEXT,
            command TEXT,
            last_run TEXT,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1
        )''',
        
        '''CREATE TABLE IF NOT EXISTS optimization_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            optimization_type TEXT,
            details TEXT,
            timestamp TEXT
        )'''
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    cursor.execute('INSERT OR REPLACE INTO system_status (status_id, status, last_update) VALUES (?, ?, ?)',
                  ('main', 'running', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    print("✓ AI自动化系统数据库表初始化完成")

if __name__ == "__main__":
    init_ai_automation_tables()