#!/usr/bin/env python3
"""
创建项目参数表并初始化项目参数
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库连接函数
from app import get_db_connection

def create_project_params_table():
    """创建项目参数表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 创建项目参数表
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
    
    # 项目参数列表
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
            'param_value': 'True',
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
            'param_value': 'True',
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
            cursor.execute(
                '''INSERT OR REPLACE INTO project_params 
                (param_name, param_value, param_type, description, is_active, updated_at) 
                VALUES (?, ?, ?, ?, ?, datetime('now'))''',
                (param['param_name'], param['param_value'], param['param_type'], 
                 param['description'], param['is_active'])
            )
        
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
        cursor.execute("SELECT param_name, param_value, param_type, description FROM project_params WHERE is_active = 1")
        params = cursor.fetchall()
        
        # 转换为字典格式
        param_dict = {}
        for param in params:
            param_name = param[0]
            param_value = param[1]
            param_type = param[2]
            
            # 根据类型转换值
            if param_type == 'integer':
                param_dict[param_name] = int(param_value)
            elif param_type == 'boolean':
                param_dict[param_name] = param_value.lower() in ('true', '1', 'yes')
            elif param_type == 'json':
                param_dict[param_name] = json.loads(param_value)
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
        # AI自动优化的参数调整
        # 这里可以添加更复杂的AI逻辑，比如根据系统资源自动调整参数
        ai_optimized_params = [
            {
                'param_name': 'max_ai_workers',
                'param_value': '15',  # AI建议调整为15
                'description': 'AI自动优化: 增加AI工作进程数以提高性能'
            },
            {
                'param_name': 'session_timeout',
                'param_value': '7200',  # AI建议延长会话超时时间
                'description': 'AI自动优化: 延长会话超时时间以提高用户体验'
            }
        ]
        
        for param in ai_optimized_params:
            cursor.execute(
                '''UPDATE project_params 
                SET param_value = ?, description = ?, updated_at = datetime('now') 
                WHERE param_name = ? AND ai_auto_config = 1''',
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
    # 创建项目参数表
    create_project_params()
    
    # 写入项目参数
    write_project_params()
    
    # AI自动配置参数
    ai_auto_configure_params()
    
    # 获取并打印项目参数
    params = get_project_params()
    print("\n[INFO] 当前项目参数:")
    for name, value in params.items():
        print(f"  {name}: {value}")
