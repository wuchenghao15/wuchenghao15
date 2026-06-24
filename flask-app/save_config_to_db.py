# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
保存配置到数据库 - 确保所有配置项都被正确写入数据库

import os
import sys
import logging
# JSON import removed - using database
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.config import load_config

def create_system_config_table(conn: sqlite3.Connection):
    创建系统配置表
    cursor = conn.cursor()

    # 创建system_config表
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

    conn.commit()
    logger.info("[配置管理] system_config表创建成功")

def save_config_to_db(config: Dict[str, Any]):
    将配置保存到数据库
    try:
        # 连接数据库
        with sqlite3.connect('app.db') as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            # 创建表(如果不存在)
            create_system_config_table(conn)
            
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
            WHERE config_key = ?
            ''', (value_str, key))
            updated += 1
            # 插入新配置
            cursor.execute('''
            INSERT INTO system_config (config_key, config_value, is_active)
            VALUES (?, ?, 1)
            ''', (key, value_str))
            total += 1
            
            logger.info(f"[配置管理] 保存配置到数据库成功: 新增 {total} 项, 更新 {updated} 项")
            
            # 关闭连接

        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def verify_config_in_db():
    验证配置是否已正确保存到数据库
    try:
        # 连接数据库
        with sqlite3.connect('app.db') as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            # 查询配置项数量
            cursor.execute('SELECT COUNT(*) FROM system_config')
            count = cursor.fetchone()[0]
            
            # 查询部分配置项
            sample_configs = cursor.fetchall()
        logger.info(f"[配置管理] 数据库中配置项数量: {count}")

        return count > 0
    except Exception as e:
        logger.error(f"[配置管理] 验证配置失败: {str(e)}")
        return False

def main():
    主函数
    logger.info("开始保存配置到数据库...")

    # 加载所有配置
    logger.info(f"加载了 {len(config)} 个配置项")

    # 保存配置到数据库
    if save_config_to_db(config):
        logger.info("配置保存成功!")

        if verify_config_in_db():
            logger.info("配置验证成功!")
        else:
            logger.error("配置验证失败!")
            return 1
    else:
        logger.error("配置保存失败!")
        return 1

if __name__ == '__main__':
    sys.exit(main())

"""