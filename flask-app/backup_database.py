# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份脚本
"""

import os
import shutil
import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

# 数据库文件路径
DB_FILE = 'app.db'
# 备份目录
BACKUP_DIR = 'database_backups'


def backup_database():
    """备份数据库"""
    # 检查数据库文件是否存在
    if not os.path.exists(DB_FILE):
        logging.error(f"数据库文件 {DB_FILE} 不存在")
        return False

    # 创建备份目录
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logging.info(f"创建备份目录: {BACKUP_DIR}")

    # 生成备份文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'app.db.backup_{timestamp}')

    try:
        # 复制数据库文件
        shutil.copy2(DB_FILE, backup_file)
        logging.info(f"数据库备份成功: {backup_file}")

        # 检查备份文件是否存在
        if os.path.exists(backup_file):
            logging.info(f"备份文件大小: {os.path.getsize(backup_file) / 1024 / 1024:.2f} MB")
            return True
        else:
            logging.error("备份文件创建失败")
            return False
    except Exception as e:
        logging.error(f"备份过程中出现错误: {str(e)}")
        return False

def clean_old_backups(max_backups=10):
    """清理旧备份文件,保留最新的max_backups个"""
    if not os.path.exists(BACKUP_DIR):
        return

    backup_files = []
    for file in os.listdir(BACKUP_DIR):
        if file.startswith('app.db.backup_'):
            file_path = os.path.join(BACKUP_DIR, file)
            if os.path.isfile(file_path):
                backup_files.append((file_path, os.path.getmtime(file_path)))

    # 按修改时间排序,最新的在前
    backup_files.sort(key=lambda x: x[1], reverse=True)

    # 删除多余的备份
    if len(backup_files) > max_backups:
        for file_path, _ in backup_files[max_backups:]:
            try:
                os.remove(file_path)
                logging.info(f"删除旧备份文件: {file_path}")
            except Exception as e:
                logging.error(f"删除备份文件失败: {file_path}, 错误: {str(e)}")


if __name__ == '__main__':
    success = backup_database()
    if success:
        logging.info("数据库备份完成")
        # 清理旧备份
        clean_old_backups()
    else:
        logging.error("数据库备份失败")
