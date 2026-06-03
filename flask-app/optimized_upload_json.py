# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
优化的JSON数据上传脚本
用于将本地JSON文件上传到数据库,增加了重试机制和超时处理
"""

import os
import json
import sqlite3
from contextlib import contextmanager
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

MAX_RETRIES = 3
RETRY_DELAY = 2
BATCH_SIZE = 20
SKIP_EMPTY_FILES = True

SKIP_DIRS = ['backups', '.git', '__pycache__', 'venv', 'env']

SKIP_FILES = [r'^\.', r'~$', r'\.tmp$']

def create_table_if_not_exists():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
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
    logger.info("✅ local_data_uploads表已准备就绪")

def upload_json_file(file_path, data_type):
    for attempt in range(MAX_RETRIES):
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False

            if os.path.getsize(file_path) == 0:
                if SKIP_EMPTY_FILES:
                    logger.warning(f"跳过空文件: {file_path}")
                    return True
                else:
                    logger.error(f"文件为空: {file_path}")
                    return False

            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)

            with sqlite3.connect(DB_PATH, timeout=30) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO local_data_uploads (data_type, file_path, content, status)
                VALUES (?, ?, ?, "pending")
                ''', (data_type, file_path, json.dumps(content, ensure_ascii=False)))
                
                conn.commit()

            logger.info(f"✅ 成功上传文件: {file_path}")
            return True
        except json.JSONDecodeError:
            logger.error(f"JSON解析错误: {file_path}")
            return False
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"⚠️  上传文件失败 (尝试 {attempt+1}/{MAX_RETRIES}) {file_path}: {str(e)}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"上传文件失败: {file_path} - {str(e)}")
                return False
    return False

def find_json_files(directory):
    import re

    json_files = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            if not file.endswith('.json'):
                continue

            skip = False
            for pattern in SKIP_FILES:
                if re.match(pattern, file):
                    skip = True
                    break
            if skip:
                continue

            json_files.append(os.path.join(root, file))

    logger.info(f"共找到 {len(json_files)} 个JSON文件")
    return json_files

def get_data_type(file_path):
    file_path_lower = file_path.lower()

    if 'ai' in file_path_lower:
        return 'ai'
    elif 'config' in file_path_lower or 'setting' in file_path_lower:
        return 'config'
    elif 'feature' in file_path_lower:
        return 'feature'
    elif 'log' in file_path_lower or 'history' in file_path_lower:
        return 'log'
    elif 'rule' in file_path_lower or 'permission' in file_path_lower:
        return 'rule'
    elif 'design' in file_path_lower or 'scheme' in file_path_lower:
        return 'design'
    else:
        return 'other'

def main():
    logger.info("开始上传本地JSON数据到数据库(优化版)")

    create_table_if_not_exists()

    project_root = os.path.dirname(os.path.abspath(__file__))
    json_files = find_json_files(project_root)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i in range(0, len(json_files), BATCH_SIZE):
        batch = json_files[i:i+BATCH_SIZE]
        logger.info(f"处理批次 {i//BATCH_SIZE + 1}/{(len(json_files)+BATCH_SIZE-1)//BATCH_SIZE}: {len(batch)} 个文件")

        for file_path in batch:
            data_type = get_data_type(file_path)

            if upload_json_file(file_path, data_type):
                success_count += 1
            else:
                failed_count += 1

        if i + BATCH_SIZE < len(json_files):
            logger.info(f"批次完成,休息 {RETRY_DELAY} 秒")
            time.sleep(RETRY_DELAY)

    logger.info(f"\n上传完成:")
    logger.info(f"✅ 成功: {success_count} 个")
    logger.info(f"❌ 失败: {failed_count} 个")
    logger.info(f"⚠️  跳过: {skipped_count} 个")
    logger.info(f"📊 总计: {success_count + failed_count + skipped_count} 个")
    logger.info("本地JSON数据上传任务完成")

if __name__ == "__main__":
    main()
