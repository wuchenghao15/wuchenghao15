# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的JSON数据上传脚本
用于将本地JSON文件上传到数据库
"""

import os
# JSON import removed - using database
import sqlite3
from contextlib import contextmanager
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def create_table_if_not_exists():
    """创建表(如果不存在)"""
    with sqlite3.connect(DB_PATH) as conn:
        conn_cursor = conn.cursor()
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS local_data_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT NOT NULL,
        file_path TEXT,
        content TEXT,
        status TEXT DEFAULT "pending",
        processed_by TEXT,
        process_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
    logger.info("local_data_uploads表已准备就绪")

def upload_json_file(file_path, data_type):
    """上传单个JSON文件到数据库"""
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)

        # 连接数据库
        with sqlite3.connect(DB_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            # 插入数据
            cursor.execute('''INSERT INTO local_data_uploads (data_type, file_path, content, status) VALUES (?, ?, ?, "pending")''', (data_type, file_path, str(content)))
            conn.commit()

        logger.info(f"成功上传文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"上传文件失败 {file_path}: {str(e)}")
        return False

def find_json_files(directory):
    """查找目录下所有JSON文件"""
    json_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

def main():
    """主函数"""
    logger.info("开始上传本地JSON数据到数据库")

    # 创建表(如果不存在)
    create_table_if_not_exists()

    # 查找所有JSON文件
    project_root = os.path.dirname(os.path.abspath(__file__))
    json_files = find_json_files(project_root)

    logger.info(f"找到 {len(json_files)} 个JSON文件")

    # 上传所有JSON文件
    success_count = 0
    failed_count = 0

    for file_path in json_files:
        # 确定数据类型(根据文件路径)
        if 'config' in file_path.lower():
            data_type = 'config'
        elif 'rule' in file_path.lower():
            data_type = 'rule'
        elif 'log' in file_path.lower():
            data_type = 'log'
        elif 'feature' in file_path.lower():
            data_type = 'feature'
        elif 'ai' in file_path.lower():
            data_type = 'ai'
        else:
            data_type = 'other'

        # 上传文件
        if upload_json_file(file_path, data_type):
            success_count += 1
        else:
            failed_count += 1

    logger.info(f"上传完成: 成功 {success_count} 个,失败 {failed_count} 个")
    logger.info("本地JSON数据上传任务完成")

if __name__ == "__main__":
    main()

