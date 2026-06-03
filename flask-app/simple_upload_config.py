# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
简单配置上传脚本,不加载完整应用上下文
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import json
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')

default_configs = {
    'APP_NAME': ('MTSCOS AI System', 'string'),
    'SECRET_KEY': ('dev-secret-key', 'string'),
    'PORT': (8888, 'integer'),

    'SESSION_COOKIE_HTTPONLY': (True, 'boolean'),
    'SESSION_COOKIE_SAMESITE': ('Lax', 'string'),

    'DATABASE_PATH': ('app.db', 'string'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': (False, 'boolean'),

    'HASH_ITERATIONS': (100000, 'integer'),
    'HASH_ALGORITHM': ('sha256', 'string'),

    'ENCRYPTION_KEY_FILE': ('encryption.key', 'string'),

    'LOG_FORMAT': ('%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s', 'string'),
    'LOG_SIZE_FILE': ('system_size.log', 'string'),
    'LOG_TIME_FILE': ('system_time.log', 'string'),
    'LOG_MAX_BYTES': (10*1024*1024, 'integer'),
    'LOG_BACKUP_COUNT': (10, 'integer'),
    'LOG_ROTATE_WHEN': ('midnight', 'string'),
    'LOG_ROTATE_INTERVAL': (1, 'integer'),
    'LOG_ROTATE_BACKUP_COUNT': (30, 'integer'),

    'LOG_LEVEL': ('INFO', 'string'),

    'NETWORK_CONFIG': ({
        'CACHE_ENABLED': True,
        'CACHE_TTL': 3600,
        'CACHE_TYPE': 'redis',
        'MAX_CONCURRENT_REQUESTS': 200,
        'RATE_LIMIT_PER_IP': 120,
        'DATA_COMPRESSION': True,
        'COMPRESSION_LEVEL': 6,
        'DUPLICATE_REQUEST_DETECTION': True,
        'REQUEST_TIMEOUT': 30,
        'KEEP_ALIVE_ENABLED': True,
        'KEEP_ALIVE_TIMEOUT': 120,
        'TCP_NODELAY': True,
        'BACKLOG_SIZE': 200,
        'CONNECTION_POOL_SIZE': 50,
        'CONNECTION_POOL_TIMEOUT': 60
    }, 'json'),

    'AI_CONFIG': ({
        'MONITORING_ENABLED': True,
        'LEARNING_ENABLED': True,
        'SELF_OPTIMIZATION': True,
        'AUTO_UPGRADE': True,
        'MODEL_PATH': 'data/ai_models',
        'TRAINING_DATA_PATH': 'data/training_data',
        'UPDATE_INTERVAL': 1800,
        'OPTIMIZATION_INTERVAL': 3600,
        'MODEL_OPTIMIZATION_ENABLED': True,
        'AI_COORDINATION_ENABLED': True,
        'DYNAMIC_RESOURCE_ALLOCATION': True,
        'AI_PERFORMANCE_MONITORING': True
    }, 'json'),

    'SECURITY_CONFIG': ({
        'ALLOW_GUEST_LOGIN': True,
        'MAX_LOGIN_ATTEMPTS': 5,
        'LOCKOUT_DURATION': 1800,
        'TWO_FACTOR_ENABLED': False,
        'IP_WHITELIST': [],
        'DISABLE_API': False
    }, 'json')
}


def convert_to_string(value, config_type):
    """将值转换为字符串"""
    if config_type == "json":
        return json.dumps(value, ensure_ascii=False)
    elif config_type == "boolean":
        return "true" if value else "false"
    else:
        return str(value)


def upload_config():
    """上传配置到数据库"""
    print(f"连接数据库: {DB_PATH}")
    print("=" * 60)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT NOT NULL,
            config_type TEXT NOT NULL DEFAULT 'string',
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            
            print("系统配置表已存在或创建成功")
            
            uploaded = 0
            updated = 0
            
            for config_key, (value, config_type) in default_configs.items():
                str_value = convert_to_string(value, config_type)
                
                cursor.execute("SELECT id FROM system_config WHERE config_key = ?", (config_key,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                    UPDATE system_config
                    SET config_value = ?, config_type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE config_key = ?
                    ''', (str_value, config_type, config_key))
                    updated += 1
                    print(f"更新配置: {config_key}")
                else:
                    cursor.execute('''
                    INSERT INTO system_config (config_key, config_value, config_type, description, is_active)
                    VALUES (?, ?, ?, '', 1)
                    ''', (config_key, str_value, config_type))
                    uploaded += 1
                    print(f"上传配置: {config_key}")
            
            conn.commit()

        print(f"\n配置上传完成!")
        print(f"结果: 新增 {uploaded} 个,更新 {updated} 个")

    except Exception as e:
        print(f"上传失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    upload_config()
