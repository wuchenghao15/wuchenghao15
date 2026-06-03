# -*- coding: utf-8 -*-
from contextlib import contextmanager
#!/usr/bin/env python3
"""
启动服务器并保存配置到数据库

import os
import sys
import logging
import signal
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.config import load_config

def save_config_to_db():
    将配置保存到数据库
    try:
        import sqlite3
        # JSON import removed - using database
# 加载配置
        config = load_config()

        # 连接数据库
        with sqlite3.connect(sqlite3.connect('app.db')) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            # 创建system_config表(如果不存在)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 保存配置项
            total = 0
            updated = 0
            
            for key, value in config.items():
            # 将复杂类型转换为JSON字符串
            if isinstance(value, (dict, list)):
            value_str = str(value)
            else:
            value_str = str(value)
            
            # 检查配置是否已存在
            cursor.execute('SELECT id FROM system_config WHERE config_key = ?', (key,))
            existing = cursor.fetchone()
            
            if existing:
            # 更新现有配置
            cursor.execute('''
            UPDATE system_config
            SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            ''', (value_str, key))
            updated += 1
            else:
            # 插入新配置
            cursor.execute('''
            INSERT INTO system_config (config_key, config_value, is_active)
            VALUES (?, ?, 1)
            total += 1
            
            conn.commit()
            logger.info(f"[配置管理] 保存配置到数据库成功: 新增 {total} 项, 更新 {updated} 项")
            
            # 关闭连接

        return True
    except Exception as e:
        logger.error(f"[配置管理] 保存配置到数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def start_server():
    启动服务器
    try:
        # 加载配置
        config = load_config()

        # 从配置获取服务器参数
        port = config.get('SERVER_PORT', 8888)
        protocol = config.get('PROTOCOL', 'http')

        logger.info(f"[服务器] 启动 MTSCOS AI Integrated Server v{version}...")
        logger.info(f"[服务器] 服务器将运行在 {protocol}://{host}:{port}")
        logger.info(f"[服务器] 环境: {config.get('ENV', 'development')}")

        # 导入应用
        from app import app

        # 启动服务器
        app.run(host=host, port=port, debug=debug, use_reloader=False)

        return True
    except Exception as e:
        logger.error(f"[服务器] 启动服务器失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    主函数
    logger.info("[系统] MTSCOS AI 服务器启动流程开始...")
    # 1. 保存配置到数据库
        logger.error("[系统] 保存配置到数据库失败,服务器启动流程中止")
        return 1
    # 2. 启动服务器

        logger.info("[系统] 服务器启动成功")
        return 0
    else:
        logger.error("[系统] 服务器启动失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())

"""