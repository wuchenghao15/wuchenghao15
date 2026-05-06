# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:26
#!/usr/bin/env python3

"""
日志管理工具
功能：
1. 扫描项目中的日志文件
2. 将日志文件统一归类到一级Logs目录下
3. 实现自动归类整理功能
4. 提供持续监控模式
"""
import os
import re
import time
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# 一级日志分类规则
LOG_CATEGORIES = {
    "JavaScript监控": [
        r'monitor.*\.js', r'js.*monitor', r'javascript.*monitor',
        r'\.js$', r'node_modules', r'\.json$', r'package\.json',
        r'\.log$', r'log.*\.js', r'JS监控', r'js_monitor', r'\.bak$'
    ],
    "备份工具": [
        r'backup', r'备份', r'auto_sync', r'deploy', r'update',
        r'sync', r'bak_', r'\.bak$', r'backup_', r'restore',
        r'backup_', r'archive', r'compress', r'tar\.', r'zip$',
        r'rar$', r'7z$', r'backup_tool', r'备份工具', r'数据备份'
    ],
    "错误日志": [
        r'warning', r'warn', r'error_', r'\.error$', r'error\.',
        r'fail_', r'crash_', r'warning_', r'warn_', r'错误日志'
    ],
    "Python脚本": [
        r'\.pyc$', r'\.pyo$', r'\.pyd$', r'Python脚本', r'python_',
        r'py_', r'Py_', r'\.egg$', r'\.whl$', r'pip', r'requirements\.txt'
    ],
    "系统监控": [
        r'系统监控', r'service', r'服务', r'status', r'check',
        r'system_', r'service_', r'monitor_', r'health_', r'status_',
        r'check_', r'系统_', r'服务_', r'监控_', r'健康_'
    ],
    "版本控制": [
        r'release', r'发布', r'version_', r'release_', r'版本_',
        r'发布_', r'version_control', r'版本控制', r'git', r'commit',
        r'tag', r'branch', r'git_', r'commit_', r'tag_', r'branch_'
    ],
    "安装部署": [
        r'install_', r'setup_', r'deploy_', r'安装_', r'部署_',
        r'setup\.py', r'requirements\.txt', r'pip', r'conda', r'virtualenv',
        r'venv', r'venv/', r'virtualenv/', r'pipenv', r'poetry'
    ],
    "配置文件": [
        r'\.cfg$', r'\.ini$', r'\.yaml$', r'\.yml$', r'\.json$',
        r'config_', r'setting_', r'配置_', r'设置_', r'config\.',
        r'setting\.', r'配置\.', r'设置\.'
    ],
    "文档文件": [
        r'\.txt$', r'\.doc$', r'\.docx$', r'\.pdf$', r'\.html$',
        r'\.htm$', r'doc', r'DOC', r'document', r'DOCUMENT',
        r'说明文档', r'使用说明', r'用户手册', r'开发文档'
    ],
    "其他日志": []  # 默认分类

# 需要排除的目录
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
    'obj',
    'test-results',
    'coverage',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    '.nox',
    '.env',
    '.gitignore',
    '.dockerignore',
    '.gitmodules',
    '.hgignore',
    '.svn',
    '.DS_Store',
    'Thumbs.db'
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
        # 确保目标分类目录存在
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

                # 移动文件
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

    return stats

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    logger.info(f"日志目录: {LOG_DIR}")
    logger.info("开始执行日志整理任务...")
    # 执行扫描和整理
    scan_and_organize_logs()

    logger.info("日志整理任务完成。")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
