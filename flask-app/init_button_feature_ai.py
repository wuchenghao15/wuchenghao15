#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化按钮功能扩展专家 AI 员工
"""

import sqlite3
import json
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


def init_button_feature_ai():
    """初始化按钮功能扩展专家 AI 员工"""
    print("开始初始化按钮功能扩展专家 AI 员工...")
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 检查 ai_employees 表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_employees'")
            if not cursor.fetchone():
                print("ai_employees 表不存在，正在创建...")
                create_ai_tables(conn)
            
            # 检查按钮功能扩展专家是否已存在
            cursor.execute("SELECT id FROM ai_employees WHERE employee_code = ?", 
                          ('AI_BUTTON_EXTENDER_001',))
            existing = cursor.fetchone()
            
            if existing:
                print(f"按钮功能扩展专家已存在（ID: {existing[0]}），跳过创建")
            else:
                # 插入新的 AI 员工
                now = datetime.utcnow().isoformat()
                capabilities = json.dumps([
                    "按钮UI设计和优化",
                    "按钮交互逻辑开发",
                    "按钮状态管理",
                    "按钮动画和视觉效果",
                    "按钮事件绑定和处理",
                    "按钮权限控制",
                    "按钮组和工具栏",
                    "按钮响应式设计",
                    "按钮无障碍支持",
                    "按钮性能优化"
                ], ensure_ascii=False)
                specialties = json.dumps([
                    "按钮设计",
                    "UI交互",
                    "前端开发",
                    "事件处理",
                    "用户体验",
                    "功能扩展",
                    "组件开发"
                ], ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO ai_employees 
                    (name, employee_code, description, capabilities, specialties, status, 
                     accuracy, total_tasks, successful_fixes, failed_fixes, 
                     learning_rate, knowledge_base_size, model_version, is_enabled, 
                     priority, max_concurrent_tasks, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    '按钮功能扩展专家',
                    'AI_BUTTON_EXTENDER_001',
                    '专门负责各类按钮功能扩展和优化的AI员工',
                    capabilities,
                    specialties,
                    'active',
                    98.5,
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
                print(f"成功创建按钮功能扩展专家（ID: {new_id}）")
            
            # 检查功能类型表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feature_types'")
            if not cursor.fetchone():
                print("feature_types 表不存在，正在创建...")
                create_feature_types_table(conn)
            
            # 添加按钮功能扩展类型
            cursor.execute("SELECT id FROM feature_types WHERE code = ?", ('BUTTON_EXTEND',))
            feature_type = cursor.fetchone()
            
            if not feature_type:
                now = datetime.utcnow().isoformat()
                keywords = json.dumps([
                    '按钮', 'button', '按钮功能', '按钮扩展', 
                    '按钮组', '工具栏', 'toolbar', '交互按钮',
                    '提交按钮', '保存按钮', '删除按钮', '编辑按钮'
                ], ensure_ascii=False)
                patterns = json.dumps([
                    r'button',
                    r'按钮',
                    r'onclick',
                    r'addEventListener',
                    r'btn-',
                    r'toolbar',
                    r'button-group'
                ], ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO feature_types 
                    (name, code, category, complexity, description, 
                     keywords, patterns, auto_detect, auto_extend, 
                     requires_approval, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    '按钮功能扩展',
                    'BUTTON_EXTEND',
                    'ui_feature',
                    'medium',
                    '按钮和工具栏的功能扩展需求',
                    keywords,
                    patterns,
                    True,
                    True,
                    False,
                    True,
                    now,
                    now
                ))
                print("成功创建 按钮功能扩展 类型")
            
            # 检查按钮功能类型表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='button_feature_types'")
            if not cursor.fetchone():
                print("button_feature_types 表不存在，正在创建...")
                create_button_feature_types_table(conn)
            
            # 添加按钮功能类型
            button_types = [
                ('ACTION_BUTTON', '操作按钮', '执行具体操作的按钮，如提交、保存、删除', 'basic'),
                ('NAV_BUTTON', '导航按钮', '用于页面导航和路由跳转的按钮', 'basic'),
                ('TOGGLE_BUTTON', '切换按钮', '切换状态的开关按钮', 'intermediate'),
                ('DROP_BUTTON', '下拉按钮', '带有下拉菜单的按钮', 'intermediate'),
                ('SPLIT_BUTTON', '分割按钮', '主按钮加下拉选项的组合按钮', 'advanced'),
                ('ICON_BUTTON', '图标按钮', '仅显示图标的按钮', 'basic'),
                ('FAB_BUTTON', '浮动操作按钮', '悬浮在页面上的操作按钮', 'intermediate'),
                ('GROUP_BUTTON', '按钮组', '多个相关按钮的组合', 'intermediate'),
                ('LOADING_BUTTON', '加载按钮', '显示加载状态的按钮', 'intermediate'),
                ('CONFIRM_BUTTON', '确认按钮', '需要二次确认的按钮', 'advanced'),
            ]
            
            for btn_type in button_types:
                try:
                    cursor.execute('''
                        INSERT INTO button_feature_types 
                        (code, name, description, complexity)
                        VALUES (?, ?, ?, ?)
                    ''', btn_type)
                except sqlite3.IntegrityError:
                    pass
            
            print(f"成功添加 {len(button_types)} 种按钮功能类型")
            
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


def create_button_feature_types_table(conn):
    """创建按钮功能类型表（如果不存在）"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS button_feature_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            complexity TEXT DEFAULT 'basic',
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    print("button_feature_types 表创建/检查完成！")


def create_feature_types_table(conn):
    """创建功能类型表（如果不存在）"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            complexity TEXT DEFAULT 'medium',
            description TEXT,
            keywords TEXT,
            patterns TEXT,
            auto_detect BOOLEAN DEFAULT 1,
            auto_extend BOOLEAN DEFAULT 0,
            requires_approval BOOLEAN DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    print("feature_types 表创建/检查完成！")


def create_ai_tables(conn):
    """创建 AI 员工相关表（如果不存在）"""
    cursor = conn.cursor()
    
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
    
    conn.commit()


if __name__ == '__main__':
    success = init_button_feature_ai()
    exit(0 if success else 1)