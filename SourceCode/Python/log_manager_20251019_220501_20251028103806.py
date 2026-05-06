# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:19
#!/usr/bin/env python3

"""
日志管理工具 - 统一管理一级日志文件夹
功能：
1. 扫描项目中的日志文件
2. 将日志文件统一归类到一级Logs目录下
3. 实现自动归类整理功能
4. 支持单次扫描模式
"""
import os
import re
import time
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(PROJECT_ROOT, "Logs")
MONITOR_LOG_DIR = os.path.join(LOG_DIR, "日志监控")

# 确保日志目录存在
os.makedirs(MONITOR_LOG_DIR, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(MONITOR_LOG_DIR, "log_manager.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 一级日志分类规则 - 仅使用一级分类
LOG_CATEGORIES = {
    "JavaScript监控": [
        r'monitor.*\.js', r'js.*monitor', r'javascript.*monitor',
        r'\.js$', r'node_modules', r'\.json$', r'package\.json',
        r'\.log$', r'log.*\.js', r'JS监控', r'js_monitor'
    ],
    "备份工具": [
        r'backup', r'备份', r'auto_sync', r'deploy', r'update',
        r'sync', r'bak_', r'backup_', r'restore', r'archive',
        r'compress', r'tar\.', r'zip$', r'rar$', r'7z$',
        r'backup_tool', r'备份工具', r'数据备份'
    ],
    "错误日志": [
        r'warning', r'warn', r'error_', r'\.error$', r'错误日志'
    ],
    "Python脚本": [
        r'\.pyc$', r'Python脚本', r'python_', r'py_', r'Py_'
    ],
    "系统监控": [
        r'系统监控', r'service', r'服务', r'status', r'check'
    ],
    "其他日志": []  # 默认分类

# 需要排除的目录 - 确保只处理一级目录
EXCLUDE_DIRS = [
    LOG_DIR,  # 排除Logs目录本身，避免递归扫描
    '.git',
    '__pycache__',
    'node_modules',
    'venv',
    '.venv',
    '.vscode',
    '.idea',
    'dist',
    'build',
    'output',
    'target',
    'out',
    'bin',
    'obj'
]

    """
    """
    return dir_name in EXCLUDE_DIRS

def classify_log_file(file_path: str) -> str:
    """
    """
    file_path_lower = file_path.lower()

    for category, patterns in LOG_CATEGORIES.items():
        if category == "其他日志":
            continue  # 最后再考虑默认分类
        for pattern in patterns:
            if re.search(pattern, file_name) or re.search(pattern, file_path_lower):
                return category

    return "其他日志"  # 默认分类

def get_unique_filename(dest_dir: str, filename: str) -> str:
    """
    """
        return filename

    name, ext = os.path.splitext(filename)
    counter = 1

    while os.path.exists(os.path.join(dest_dir, f"{name}_{counter}{ext}")):
        counter += 1

    return f"{name}_{counter}{ext}"

def move_log_file(file_path: str, category: str) -> bool:
    """
    """
        # 确保目标分类目录存在（仅一级目录）
        dest_dir = os.path.join(LOG_DIR, category)
        os.makedirs(dest_dir, exist_ok=True)

        # 获取唯一的目标文件名
        filename = os.path.basename(file_path)
        unique_filename = get_unique_filename(dest_dir, filename)
        dest_path = os.path.join(dest_dir, unique_filename)

        # 复制文件（保留原文件）
        shutil.copy2(file_path, dest_path)
        logger.info(f"已将文件移动到: {dest_path}")

        return True
    except Exception as e:
        logger.error(f"移动文件失败 {file_path}: {str(e)}")
        return False

def scan_and_organize_logs() -> Dict[str, int]:
    """
    """
    moved_count = 0
    total_scanned = 0

    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    logger.info(f"日志目录: {LOG_DIR}")
    logger.info("开始扫描项目中的日志文件...")

    try:
        # 遍历项目目录
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 过滤需要排除的目录
            dirs[:] = [d for d in dirs if not should_exclude_dir(os.path.join(root, d))]

            for file in files:
                # 跳过自身文件
                if file == 'log_manager.py':
                    continue

                file_path = os.path.join(root, file)
                total_scanned += 1

                # 分类文件
                category = classify_log_file(file_path)

                if move_log_file(file_path, category):
                    moved_count += 1
                    stats[category] += 1

    except Exception as e:
        logger.error(f"扫描过程中发生错误: {str(e)}")

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"扫描完成。总扫描文件: {total_scanned}, 成功移动: {moved_count}")
    logger.info(f"耗时: {duration:.5f} 秒")
    logger.info("分类统计:")

    for category, count in stats.items():
        if count > 0:
            logger.info(f"  {category}: {count}")

    logger.info("=" * 60)
    return stats

def main():
    """
    scan_and_organize_logs()

if __name__ == "__main__":
    main()
