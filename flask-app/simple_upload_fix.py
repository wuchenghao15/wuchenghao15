#!/usr/bin/env python3
"""
简化的JSON上传脚本，修复了语法错误，只处理特定目录

import os
# JSON import removed - using database
import sqlite3
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

# 只处理特定目录
target_dirs = ['src', 'config']

# 已上传的文件计数
total_processed = 0
success_count = 0
failed_count = 0

def main():
    """主函数"""
    logger.info("开始简化版JSON上传...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 遍历目标目录
    project_root = os.path.dirname(os.path.abspath(__file__))

    for target_dir in target_dirs:
        target_path = os.path.join(project_root, target_dir)
        if not os.path.exists(target_path):
            logger.warning(f"目录不存在: {target_path}")
            continue

        logger.info(f"处理目录: {target_path}")

        # 递归查找JSON文件
        for root, dirs, files in os.walk(target_path):
            # 跳过__pycache__目录
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    process_file(file_path, cursor)

    conn.commit()
    conn.close()

    logger.info(f"\n上传完成:")
    logger.info(f"✅ 成功: {success_count} 个")
    logger.info(f"❌ 失败: {failed_count} 个")
    logger.info(f"📊 总计: {total_processed} 个")
    logger.info("简化版JSON上传任务完成")

def process_file(file_path, cursor):
    """处理单个JSON文件"""
    global total_processed, success_count, failed_count

    total_processed += 1

    try:
        # 检查文件大小
        if os.path.getsize(file_path) == 0:
            logger.warning(f"跳过空文件: {file_path}")
            return

        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)

        # 确定数据类型
        file_path_lower = file_path.lower()
        if 'rule' in file_path_lower or 'permission' in file_path_lower:
            data_type = 'rule'
        elif 'config' in file_path_lower:
            data_type = 'config'
        else:
            data_type = 'other'

        # 插入数据
        cursor.execute('''
        INSERT OR IGNORE INTO local_data_uploads (data_type, file_path, content, status)
        VALUES (?, ?, ?, "pending")
        ''', (data_type, file_path, str(content)))

        logger.info(f"✅ 成功上传: {file_path}")
        success_count += 1

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON格式错误 {file_path}: {str(e)}")
        failed_count += 1
    except Exception as e:
        logger.error(f"❌ 处理失败 {file_path}: {str(e)}")
        failed_count += 1
if __name__ == "__main__":
    main()
