#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化 CDN 和图标修复专家 AI 员工
"""

import sqlite3
import json
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


def init_ai_employee():
    """初始化新的 AI 员工"""
    print("开始初始化 CDN 和图标修复专家 AI 员工...")
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 检查 ai_employees 表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_employees'")
            if not cursor.fetchone():
                print("ai_employees 表不存在，正在创建...")
                create_ai_tables(conn)
            
            # 检查 CDN 和图标修复专家是否已存在
            cursor.execute("SELECT id FROM ai_employees WHERE employee_code = ?", 
                          ('AI_CDN_ICON_FIXER_001',))
            existing = cursor.fetchone()
            
            if existing:
                print(f"CDN 和图标修复专家已存在（ID: {existing[0]}），跳过创建")
            else:
                # 插入新的 AI 员工
                now = datetime.utcnow().isoformat()
                capabilities = json.dumps([
                    "检测CDN加载失败",
                    "替换外部CDN为本地资源",
                    "使用内联SVG替代字体图标",
                    "优化资源加载策略",
                    "缓存失效处理"
                ], ensure_ascii=False)
                specialties = json.dumps([
                    "Font Awesome",
                    "CDN优化",
                    "图标系统",
                    "前端资源管理",
                    "性能优化"
                ], ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO ai_employees 
                    (name, employee_code, description, capabilities, specialties, status, 
                     accuracy, total_tasks, successful_fixes, failed_fixes, 
                     learning_rate, knowledge_base_size, model_version, is_enabled, 
                     priority, max_concurrent_tasks, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'CDN和图标修复专家',
                    'AI_CDN_ICON_FIXER_001',
                    '专门修复CDN加载失败和图标显示问题的AI员工',
                    capabilities,
                    specialties,
                    'active',
                    99.5,
                    0,
                    0,
                    0,
                    0.001,
                    0,
                    '1.0.0',
                    True,
                    10,
                    10,
                    now,
                    now
                ))
                
                new_id = cursor.lastrowid
                print(f"成功创建 CDN 和图标修复专家（ID: {new_id}）")
            
            # 检查错误类型表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='error_types'")
            if not cursor.fetchone():
                print("error_types 表不存在，正在创建...")
                create_ai_tables(conn)
            
            # 添加 CDN 加载失败错误类型
            cursor.execute("SELECT id FROM error_types WHERE code = ?", ('CDN_LOAD_FAIL',))
            cdn_error = cursor.fetchone()
            
            if not cdn_error:
                now = datetime.utcnow().isoformat()
                keywords = json.dumps([
                    'CDN', 'fontawesome', 'font-awesome', 
                    'cdn.jsdelivr.net', 'cdnjs.cloudflare.com', 
                    '资源加载', '图标显示'
                ], ensure_ascii=False)
                patterns = json.dumps([
                    r'font.*\.css',
                    r'font.*\.js',
                    r'cdn\.',
                    r'ERR_ABORTED',
                    r'net::ERR'
                ], ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO error_types 
                    (name, code, category, severity, description, 
                     keywords, patterns, auto_detect, auto_fix, 
                     requires_approval, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'CDN加载失败',
                    'CDN_LOAD_FAIL',
                    'network_error',
                    'high',
                    '外部CDN资源加载失败，如Font Awesome等',
                    keywords,
                    patterns,
                    True,
                    True,
                    False,
                    True,
                    now,
                    now
                ))
                print("成功创建 CDN加载失败 错误类型")
            
            # 添加图标显示失败错误类型
            cursor.execute("SELECT id FROM error_types WHERE code = ?", ('ICON_SHOW_FAIL',))
            icon_error = cursor.fetchone()
            
            if not icon_error:
                now = datetime.utcnow().isoformat()
                keywords = json.dumps([
                    '图标', 'icon', 'missing icon', 'no icon', '显示失败'
                ], ensure_ascii=False)
                patterns = json.dumps([
                    r'<i.*class.*fa-',
                    r'fa-icon',
                    r'mdi-'
                ], ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO error_types 
                    (name, code, category, severity, description, 
                     keywords, patterns, auto_detect, auto_fix, 
                     requires_approval, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    '图标显示失败',
                    'ICON_SHOW_FAIL',
                    'custom',
                    'medium',
                    '网页图标无法显示失败',
                    keywords,
                    patterns,
                    True,
                    True,
                    False,
                    True,
                    now,
                    now
                ))
                print("成功创建 图标显示失败 错误类型")
            
            conn.commit()
            print("\n✅ AI 员工初始化成功！")
            
            # 列出所有 AI 员工
            print("\n当前所有 AI 员工：")
            cursor.execute("SELECT id, name, employee_code, status, accuracy FROM ai_employees")
            employees = cursor.fetchall()
            for emp in employees:
                print(f"  ID: {emp[0]}, 名称: {emp[1]}, 代码: {emp[2]}, 状态: {emp[3]}, 准确率: {emp[4]}%")
            
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def create_ai_tables(conn):
    """创建 AI 员工相关表（如果不存在）"""
    cursor = conn.cursor()
    
    # 创建 ai_employees 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employee_code TEXT UNIQUE NOT NULL,
            description TEXT,
            capabilities TEXT,
            specialties TEXT,
            status TEXT DEFAULT 'active',
            accuracy REAL DEFAULT 0.0,
            total_tasks INTEGER DEFAULT 0,
            successful_fixes INTEGER DEFAULT 0,
            failed_fixes INTEGER DEFAULT 0,
            learning_rate REAL DEFAULT 0.001,
            knowledge_base_size INTEGER DEFAULT 0,
            last_training TEXT,
            model_version TEXT,
            is_enabled BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 0,
            max_concurrent_tasks INTEGER DEFAULT 5,
            created_by INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 创建 error_types 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            description TEXT,
            keywords TEXT,
            patterns TEXT,
            auto_detect BOOLEAN DEFAULT 1,
            auto_fix BOOLEAN DEFAULT 0,
            requires_approval BOOLEAN DEFAULT 1,
            example_code TEXT,
            correct_code TEXT,
            occurrence_count INTEGER DEFAULT 0,
            fix_success_rate REAL DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 创建 solutions 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            error_type_id INTEGER,
            ai_employee_id INTEGER,
            problem_description TEXT NOT NULL,
            problem_code TEXT,
            error_message TEXT,
            solution_code TEXT NOT NULL,
            explanation TEXT,
            steps TEXT,
            status TEXT DEFAULT 'pending',
            is_verified BOOLEAN DEFAULT 0,
            is_tested BOOLEAN DEFAULT 0,
            test_results TEXT,
            fix_success BOOLEAN DEFAULT 0,
            performance_impact TEXT,
            side_effects TEXT,
            confidence_score REAL DEFAULT 0.0,
            similar_cases_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            created_by INTEGER,
            approved_by INTEGER,
            created_at TEXT,
            updated_at TEXT,
            deployed_at TEXT
        )
    ''')
    
    # 创建 fix_tasks 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fix_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_code TEXT UNIQUE NOT NULL,
            error_type_id INTEGER,
            ai_employee_id INTEGER NOT NULL,
            source_file TEXT,
            source_code TEXT NOT NULL,
            error_line INTEGER,
            error_message TEXT,
            fixed_code TEXT,
            solution_id INTEGER,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            start_time TEXT,
            end_time TEXT,
            execution_time REAL,
            is_successful BOOLEAN DEFAULT 0,
            error_details TEXT,
            warnings TEXT,
            user_feedback TEXT,
            rating INTEGER,
            created_by INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 创建 learning_records 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_employee_id INTEGER NOT NULL,
            solution_id INTEGER,
            fix_task_id INTEGER,
            input_data TEXT,
            output_data TEXT,
            expected_output TEXT,
            is_correct BOOLEAN DEFAULT 0,
            error_type TEXT,
            error_details TEXT,
            loss_value REAL,
            accuracy REAL,
            learning_time REAL,
            model_version_before TEXT,
            model_version_after TEXT,
            learning_type TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    print("AI 员工相关表创建/检查完成！")


if __name__ == '__main__':
    success = init_ai_employee()
    exit(0 if success else 1)
