# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建项目参数表并初始化项目参数
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection
import json

def create_project_params_table():
    """创建项目参数表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_params (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                param_name TEXT UNIQUE NOT NULL,
                param_value TEXT NOT NULL,
                param_type TEXT DEFAULT 'string',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        print("[INFO] 项目参数表创建成功")
        return True
    except Exception as e:
        print(f"[ERROR] 创建项目参数表失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def write_project_params():
    """写入项目参数到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    project_params = [
        {
            'param_name': 'app_port',
            'param_value': '8888',
            'param_type': 'integer',
            'description': '应用运行端口',
            'is_active': 1
        },
        {
            'param_name': 'app_mode',
            'param_value': 'development',
            'param_type': 'string',
            'description': '应用运行模式',
            'is_active': 1
        },
        {
            'param_name': 'debug_mode',
            'param_value': 'false',
            'param_type': 'boolean',
            'description': '调试模式开关',
            'is_active': 1
        },
        {
            'param_name': 'default_language',
            'param_value': 'chinese',
            'param_type': 'string',
            'description': '默认语言',
            'is_active': 1
        },
        {
            'param_name': 'session_timeout',
            'param_value': '3600',
            'param_type': 'integer',
            'description': '会话超时时间(秒)',
            'is_active': 1
        },
        {
            'param_name': 'ai_auto_config',
            'param_value': 'true',
            'param_type': 'boolean',
            'description': 'AI自动配置开关',
            'is_active': 1
        },
        {
            'param_name': 'max_ai_workers',
            'param_value': '10',
            'param_type': 'integer',
            'description': '最大AI工作进程数',
            'is_active': 1
        }
    ]
    try:
        for param in project_params:
            cursor.execute('''
                INSERT INTO project_params (param_name, param_value, param_type, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (param['param_name'], param['param_value'], param['param_type'],
                  param['description'], param['is_active']))

        conn.commit()
        print("[INFO] 项目参数写入成功")
        return True
    except Exception as e:
        print(f"[ERROR] 写入项目参数失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_project_params():
    """获取所有项目参数"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT param_name, param_value, param_type FROM project_params WHERE is_active = 1")
        params = cursor.fetchall()

        param_dict = {}
        for param in params:
            param_name = param[0]
            param_value = param[1]
            param_type = param[2]

            if param_type == 'integer':
                param_dict[param_name] = int(param_value)
            elif param_type == 'boolean':
                param_dict[param_name] = param_value.lower() in ('true', '1', 'yes')
            elif param_type == 'json':
                param_dict[param_name] = eval(param_value)
            else:
                param_dict[param_name] = param_value

        return param_dict
    except Exception as e:
        print(f"[ERROR] 获取项目参数失败: {str(e)}")
        return {}
    finally:
        conn.close()

def ai_auto_configure_params():
    """AI自动配置项目参数"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        ai_optimized_params = [
            {
                'param_name': 'max_ai_workers',
                'param_value': '15',
                'description': 'AI自动优化: 增加AI工作进程数以提高性能'
            },
            {
                'param_name': 'session_timeout',
                'param_value': '7200',
                'description': 'AI自动优化: 延长会话超时时间以提高用户体验'
            }
        ]

        for param in ai_optimized_params:
            cursor.execute(
                '''UPDATE project_params
                SET param_value = ?, description = ?, updated_at = datetime('now')
                WHERE param_name = ?''',
                (param['param_value'], param['description'], param['param_name'])
            )

        conn.commit()
        print("[INFO] AI自动配置项目参数成功")
        return True
    except Exception as e:
        print(f"[ERROR] AI自动配置项目参数失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    create_project_params_table()
    write_project_params()
    ai_auto_configure_params()
    params = get_project_params()
    print("\n[INFO] 当前项目参数:")
    for name, value in params.items():
        print(f"  {name}: {value}")
