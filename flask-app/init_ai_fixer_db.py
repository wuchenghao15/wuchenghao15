#!/usr/bin/env python3
"""
初始化AI员工修复报告数据库表
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def init_ai_fixer_db():
    """初始化AI员工修复报告数据库表"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建AI员工修复报告表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_fix_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            specialty TEXT,
            issue_type TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            fix_method TEXT,
            fixed BOOLEAN DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            additional_info TEXT
        )
        ''')
        
        # 创建AI员工统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL UNIQUE,
            employee_name TEXT NOT NULL,
            specialty TEXT,
            fix_count INTEGER DEFAULT 0,
            report_count INTEGER DEFAULT 0,
            last_fix_time TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
        ''')
        
        # 插入初始AI员工数据
        employees = [
            ('template_fixer_001', '模板修复专家', '模板依赖修复、静态文件缺失检测、路径配置优化'),
            ('route_fixer_001', '路由修复专家', '路由冲突检测、权限配置修复、404错误处理'),
        ]
        
        for emp_id, emp_name, specialty in employees:
            cursor.execute('''
            INSERT OR IGNORE INTO ai_employee_stats (employee_id, employee_name, specialty)
            VALUES (?, ?, ?)
            ''', (emp_id, emp_name, specialty))
        
        conn.commit()
        logger.info("AI员工修复报告数据库表初始化成功")
        
        # 显示表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='ai_employee_fix_reports'")
        table_sql = cursor.fetchone()
        logger.info(f"修复报告表结构:\n{table_sql[0]}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"初始化AI员工修复报告数据库失败: {e}")
        raise

if __name__ == '__main__':
    init_ai_fixer_db()
    print("✅ AI员工修复报告数据库表已创建")
    print("✅ AI员工初始数据已插入")