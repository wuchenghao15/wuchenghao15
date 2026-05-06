#!/usr/bin/env python3
"""
创建用户管家AI
负责用户管理和自动填充拓展功能

import os
import sys
import sqlite3
# JSON import removed - using database
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_user_manager_ai():
    """创建用户管家AI"""
    db_path = "app.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建用户管家AI
        user_manager_ai = {
            "ai_name": "user_manager_ai",
            "instance_id": "user_manager_ai",
            "collection_id": "main_ai_ensemble",
            "ai_type": "user_manager",
            "name": "用户管家AI",
            "description": "负责用户管理、个人信息管理和自动填充拓展功能，提供智能用户服务",
            "functions": str([
                "user_management",
                "profile_management",
                "auto_fill",
                "preferences_management",
                "user_analytics",
                "personalization",
                "data_synchronization",
                "security_management"
            ]),
            "responsibilities": str([
                "用户账户管理",
                "个人信息管理",
                "自动填充功能",
                "用户偏好设置",
                "用户行为分析",
                "个性化服务",
                "数据同步",
                "用户安全管理"
            ]),
            "config": str({
                "auto_fill": {
                    "enabled": True,
                    "fields": ["name", "email", "phone", "address", "company", "job_title"],
                    "sync_with_browser": True,
                    "auto_save": True
                },
                "personalization": {
                    "enabled": True,
                    "learning_rate": 0.1,
                },
                "security": {
                    "data_encryption": True,
                    "data_retention": 365
                }
            }),
            "bound_user": "admin"
        }

        # 插入用户管家AI
        sql = """
        (ai_name, instance_id, collection_id, ai_type, name, description,
         functions, responsibilities, status, config, bound_user, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)

        params = (
            user_manager_ai["ai_name"],
            user_manager_ai["instance_id"],
            user_manager_ai["collection_id"],
            user_manager_ai["ai_type"],
            user_manager_ai["name"],
            user_manager_ai["description"],
            user_manager_ai["functions"],
            user_manager_ai["responsibilities"],
            user_manager_ai["status"],
            user_manager_ai["config"],
            user_manager_ai["bound_user"]
        )

        cursor.execute(sql, params)
        conn.commit()

        print("用户管家AI创建成功！")
        print(f"AI名称: {user_manager_ai['name']}")
        print(f"类型: {user_manager_ai['ai_type']}")
        print(f"状态: {user_manager_ai['status']}")

        # 创建用户相关的表
        create_user_tables(cursor)

        conn.close()
        return True

    except Exception as e:
        print(f"创建用户管家AI失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_user_tables(cursor):
    """创建用户相关的表"""
    # 用户个人信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        company TEXT,
        job_title TEXT,
        birthday DATE,
        avatar TEXT,
        preferences TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 用户自动填充数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auto_fill_data (
        user_id INTEGER NOT NULL,
        field_name TEXT NOT NULL,
        field_value TEXT NOT NULL,
        usage_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    )
    ''')

    # 用户偏好设置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        preference_key TEXT NOT NULL,
        category TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, preference_key)
    )

    # 用户行为数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_behavior (
        user_id INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
    )
    ''')

    print("用户相关表创建成功！")
if __name__ == "__main__":
