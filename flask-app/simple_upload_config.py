#!/usr/bin/env python3
"""
简单配置上传脚本，不加载完整应用上下文
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# 直接指定数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')

# 默认配置（从ConfigBase提取的关键配置）
default_configs = {
    # 应用基本配置
    'APP_NAME': ('MTSCOS AI System', 'string'),
    'SECRET_KEY': ('dev-secret-key', 'string'),
    'PORT': (8888, 'integer'),
    
    # 会话安全配置
    'SESSION_COOKIE_HTTPONLY': (True, 'boolean'),
    'SESSION_COOKIE_SAMESITE': ('Lax', 'string'),
    
    # 数据库配置
    'DATABASE_PATH': ('app.db', 'string'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': (False, 'boolean'),
    
    # 密码哈希相关配置
    'HASH_ITERATIONS': (100000, 'integer'),
    'HASH_ALGORITHM': ('sha256', 'string'),
    
    # 加密密钥文件配置
    'ENCRYPTION_KEY_FILE': ('encryption.key', 'string'),
    
    # 日志配置
    'LOG_FORMAT': ('%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s', 'string'),
    'LOG_SIZE_FILE': ('system_size.log', 'string'),
    'LOG_TIME_FILE': ('system_time.log', 'string'),
    'LOG_MAX_BYTES': (10*1024*1024, 'integer'),
    'LOG_BACKUP_COUNT': (10, 'integer'),
    'LOG_ROTATE_WHEN': ('midnight', 'string'),
    'LOG_ROTATE_INTERVAL': (1, 'integer'),
    'LOG_ROTATE_BACKUP_COUNT': (30, 'integer'),
    
    # 日志级别（不同环境有不同值，这里使用默认值）
    'LOG_LEVEL': ('INFO', 'string'),
    
    # 网络优化配置
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
    
    # AI配置
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
    
    # 安全配置
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
        return json.dumps(value, ensure_ascii=False, indent=None)
    elif config_type == "boolean":
        return "true" if value else "false"
    else:
        return str(value)


def upload_config():
    """上传配置到数据库"""
    print(f"连接数据库: {DB_PATH}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 确保系统配置表存在
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
        
        print("✅ 系统配置表已存在或创建成功")
        
        # 上传每个配置
        uploaded = 0
        updated = 0
        
        for config_key, (value, config_type) in default_configs.items():
            str_value = convert_to_string(value, config_type)
            
            # 检查配置是否已存在
            cursor.execute("SELECT id FROM system_config WHERE config_key = ?", (config_key,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新配置
                cursor.execute('''
                    UPDATE system_config 
                    SET config_value = ?, config_type = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE config_key = ?
                ''', (str_value, config_type, config_key))
                updated += 1
                print(f"✏️  更新配置: {config_key}")
            else:
                # 插入新配置
                cursor.execute('''
                    INSERT INTO system_config (config_key, config_value, config_type, description, is_active) 
                    VALUES (?, ?, ?, ?, 1)
                ''', (config_key, str_value, config_type, f"自动上传的配置: {config_key}"))
                uploaded += 1
                print(f"📤 上传配置: {config_key}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 配置上传完成！")
        print(f"📊 结果: 新增 {uploaded} 个，更新 {updated} 个")
        return True
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    upload_config()
