# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:08
#!/usr/bin/env python3

"""
日志统一管理工具
功能：
1. 将项目中所有log文件夹和log文件转存到一级Logs目录
2. 删除非一级Logs文件夹和其中的文件
3. 实现文件冲突处理和日志分类
"""
import os
import re
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional

# 设置项目根目录和一级Logs目录
PROJECT_ROOT = os.path.abspath('.')
MAIN_LOG_DIR = os.path.join(PROJECT_ROOT, 'Logs')

# 确保一级Logs目录存在
os.makedirs(MAIN_LOG_DIR, exist_ok=True)

# 配置日志记录
LOG_FILE = os.path.join(MAIN_LOG_DIR, '日志管理', 'unify_logs.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 日志分类规则
LOG_CATEGORIES = {
    "JavaScript监控": [r'js', r'javascript', r'node', r'\.js$', r'\.json$'],
    "备份工具": [r'backup', r'备份', r'bak', r'sync', r'deploy', r'update'],
    "错误日志": [r'error', r'错误', r'fail', r'crash', r'warning', r'warn', r'exception'],
    "Python脚本": [r'python', r'\.py$', r'py_'],
    "系统监控": [r'system', r'系统', r'monitor', r'监控', r'service', r'服务'],
    "版本控制": [r'version', r'版本', r'release', r'发布', r'git', r'tag', r'commit'],
    "配置文件": [r'config', r'配置', r'setting', r'设置', r'\.conf$', r'\.ini$', r'\.yaml$', r'\.yml$'],
    "文档文件": [r'readme', r'说明', r'文档', r'\.md$', r'\.txt$', r'\.doc$', r'\.pdf$'],
    "日志监控": [r'log', r'日志', r'monitor'],
    "其他日志": []  # 默认分类
}

# 需要排除的目录
EXCLUDE_DIRS = {
    MAIN_LOG_DIR,  # 排除主Logs目录本身
    '.git', '__pycache__', 'node_modules', 'venv', '.venv',
    '.vscode', '.idea', 'dist', 'build', 'output', 'target'
}

EXCLUDE_FILES = {
    'unify_logs.py',  # 排除自身
    '.DS_Store', 'Thumbs.db', '.gitignore', '.dockerignore'
}

    """
    """
    # 检查是否包含log相关关键词
    log_keywords = ['log', '日志', 'backup', '备份', 'error', '错误', 'warning', '警告']
    for keyword in log_keywords:
        if keyword in path_lower:
            return True
    # 检查文件扩展名
    log_extensions = ['.log', '.txt', '.md', '.bak', '.backup']
    for ext in log_extensions:
        if path_lower.endswith(ext):
            return True
    # 检查是否是日志文件夹
    if 'log' in path_lower or '日志' in path_lower:
        return True
    return False

    """
    """
    for category, patterns in LOG_CATEGORIES.items():
        if category == "其他日志":
            continue  # 最后再考虑默认分类
        for pattern in patterns:
            if re.search(pattern, file_name, re.IGNORECASE):
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

def move_to_main_logs(source_path: str, is_directory: bool = False) -> bool:
    """
    """
        # 获取目标分类
        if is_directory:
            category = classify_file(source_path)
        else:
            category = classify_file(source_path)

        # 创建分类目录
        dest_category_dir = os.path.join(MAIN_LOG_DIR, category)
        os.makedirs(dest_category_dir, exist_ok=True)

        # 生成目标路径
        base_name = os.path.basename(source_path)
        unique_name = get_unique_filename(dest_category_dir, base_name)
        dest_path = os.path.join(dest_category_dir, unique_name)

        # 移动文件或目录
        if is_directory:
            shutil.move(source_path, dest_path)
        else:
            shutil.move(source_path, dest_path)
            logger.info(f"已移动文件: {source_path} -> {dest_path}")

        return True
    except Exception as e:
        logger.error(f"移动失败 {source_path}: {str(e)}")
        return False

def scan_and_unify_logs():
    """
    logger.info(f"开始统一管理项目日志文件")
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    logger.info(f"一级Logs目录: {MAIN_LOG_DIR}")

    # 存储已经处理过的文件路径，避免重复处理

    # 首先扫描所有日志相关的文件夹和文件
        # 检查当前目录是否需要排除
        if any(exclude_dir in root for exclude_dir in EXCLUDE_DIRS):
            continue

        # 检查当前目录是否是日志相关目录
        if is_log_related(root) and root != MAIN_LOG_DIR and not root.startswith(MAIN_LOG_DIR):
            logs_dirs_to_delete.add(root)

            # 处理目录中的所有文件
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                file_path = os.path.join(root, file)
                if file_path not in processed_files:
                    if move_to_main_logs(file_path):
                        processed_files.add(file_path)
        else:
            # 处理非日志目录中的日志文件
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                file_path = os.path.join(root, file)
                if is_log_related(file) and file_path not in processed_files:
                    if move_to_main_logs(file_path):
                        processed_files.add(file_path)

    # 删除非一级日志文件夹
    logger.info(f"\n开始删除非一级日志文件夹...")
    for log_dir in sorted(logs_dirs_to_delete, reverse=True):  # 逆序删除，先删除深层目录
        if os.path.exists(log_dir) and not log_dir.startswith(MAIN_LOG_DIR):
            try:
                # 确保目录为空（因为文件已经移动）
                shutil.rmtree(log_dir)
            except Exception as e:
                logger.error(f"删除文件夹失败 {log_dir}: {str(e)}")
    logger.info("\n日志统一管理完成！")
    logger.info(f"共处理 {len(processed_files)} 个文件")
    logger.info(f"删除 {len(logs_dirs_to_delete)} 个非一级日志文件夹")
    logger.info("=" * 80)

    """
if __name__ == "__main__":
    main()
