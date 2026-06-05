#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接记录版本信息到数据库
"""

import sqlite3
import json
from datetime import datetime
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


def connect_db():
    """连接数据库"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def record_version():
    """记录1.6.0版本到数据库"""
    
    version = "1.6.0"
    description = "硬件管理系统UI增强版 - 完善侧边栏和主内容区功能"
    changes = [
        "完善侧边栏功能 - 添加系统状态指示器、导航折叠、多级菜单、快捷操作面板",
        "拓展主内容区顶部栏 - 添加全局搜索增强、通知下拉面板、用户菜单、快捷操作按钮",
        "优化仪表盘主内容 - 添加实时数据图表、设备状态热力图、AI分析面板增强",
        "添加响应式设计和移动端适配",
        "修复模板路径配置问题 - 确保硬件管理系统模板正确加载",
        "完善所有硬件管理页面 - 仪表盘、设备管理、系统设置、性能监控、系统日志、API密钥管理",
        "增强用户体验 - 添加实时性能监控和智能分析功能"
    ]
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 检查版本表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version_history'")
        if not cursor.fetchone():
            print("版本表不存在，先创建表...")
            # 创建版本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL UNIQUE,
                    major_version INTEGER DEFAULT 1,
                    minor_version INTEGER DEFAULT 0,
                    patch_version INTEGER DEFAULT 0,
                    description TEXT,
                    changes TEXT,
                    schema_hash TEXT,
                    data_hash TEXT,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    applied_at TEXT,
                    status TEXT DEFAULT 'pending',
                    rollback_available INTEGER DEFAULT 0,
                    backup_data BLOB
                )
            ''')
        
        # 插入版本记录
        version_parts = version.split('.')
        major = int(version_parts[0]) if len(version_parts) > 0 else 1
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        patch = int(version_parts[2]) if len(version_parts) > 2 else 0
        
        cursor.execute('''
            INSERT OR REPLACE INTO db_version_history 
            (version, major_version, minor_version, patch_version, description, 
             changes, created_by, applied_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version, major, minor, patch, description,
            json.dumps(changes, ensure_ascii=False),
            'System AI', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'applied'
        ))
        
        # 同时创建变更日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                change_type TEXT NOT NULL,
                table_name TEXT,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                sql_statement TEXT,
                affected_rows INTEGER DEFAULT 0,
                created_by TEXT DEFAULT 'system',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                rollback_sql TEXT,
                rollback_status TEXT DEFAULT 'not_applied'
            )
        ''')
        
        # 记录变更
        cursor.execute('''
            INSERT INTO db_change_log 
            (version, change_type, table_name, field_name, old_value, new_value,
             sql_statement, affected_rows, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version, 'ui_enhancement', 'templates', 'hardware_ui',
            '1.5.0', '1.6.0', 'Update hardware management templates',
            6, 'System AI'
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 成功记录版本 {version} 到数据库")
        return True
        
    except Exception as e:
        print(f"❌ 记录失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_versions():
    """显示所有版本"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM db_version_history ORDER BY major_version DESC, minor_version DESC, patch_version DESC")
        versions = cursor.fetchall()
        
        print("\n📋 数据库版本记录:")
        for v in versions:
            print(f"  - v{v['version']}: {v['description']} ({v['created_at']})")
        
        conn.close()
    except Exception as e:
        print(f"获取版本列表失败: {e}")


if __name__ == "__main__":
    print("🚀 正在记录硬件管理系统UI增强版更新...")
    success = record_version()
    
    if success:
        show_versions()
        print("\n✅ 完成！")
