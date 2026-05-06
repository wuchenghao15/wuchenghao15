# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:17
#!/usr/bin/env python3
"""
日志管理与监控脚本
功能：
1. 删除非一级Logs文件夹的源码
2. 统一修改路径到一级Logs文件夹
3. 自动归类整理日志文件
4. 持续监控新项目日志生成
"""
import os
import shutil
import time
import logging
import datetime
from pathlib import Path
from collections import defaultdict
import signal
import sys

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "Logs"

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "日志监控" / "log_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# 确保日志监控目录存在
os.makedirs(LOG_DIR / "日志监控", exist_ok=True)

# 日志分类规则
CATEGORIES = {
    'backup': '备份工具',
    'backup_': '备份工具',
    '错误': '错误日志',
    'error': '错误日志',
    'monitor': 'JavaScript监控',
    'js_': 'JavaScript监控',
    'log': '其他日志',
    'report': '其他日志',
    '统计': '其他日志',
    '登录': '登录系统',
    'login': '登录系统',
    'register': '登录系统',
    '系统管理': '系统管理',
    'system': '系统管理',
    '优化': '优化日志',
    'optimization': '优化日志',
    '自动同步': '自动同步',
    'sync': '自动同步',
    '构建': '构建系统',
    'build': '构建系统',
    '版本': '版本更新',
    'version': '版本更新',
    '数据库': '数据库',
    'db_': '数据库',
    'mssql': '数据库'
}

# 排除的目录
EXCLUDE_DIRS = ['Logs', 'Build', 'Backups', '.git', 'node_modules', '__pycache__', 'Deployment']

# 有效的日志文件扩展名
LOG_EXTENSIONS = ['.log', '.txt', '.pid', '.json', '.sh', '.md']

def clean_non_first_level_logs():
    """删除非一级Logs文件夹下的源码文件"""
    logger.info("开始清理非一级Logs文件夹中的源码...")

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 跳过一级Logs目录
        if str(root) == str(LOG_DIR):
            continue

        # 检查是否是Logs子目录
        if 'Logs' in root.split(os.sep):
            for file in files:
                # 清理Python、JavaScript等源码文件
                if file.endswith(('.py', '.js', '.css', '.html')):
                    file_path = Path(root) / file
                    try:
                        os.remove(file_path)
                        logger.info(f"已删除非一级Logs目录源码: {file_path}")
                    except Exception as e:
                        logger.error(f"删除失败: {file_path} - {e}")

    logger.info("清理完成")

def organize_log_file(file_path, stats):
    """整理单个日志文件到一级Logs目录"""
    file_name = file_path.name.lower()

    # 确定文件分类
    category = '其他日志'
    for keyword, cat_name in CATEGORIES.items():
        if keyword in file_name:
            category = cat_name
            break

    # 确保目标目录存在
    target_dir = LOG_DIR / category
    os.makedirs(target_dir, exist_ok=True)

    # 处理文件名冲突
    target_path = target_dir / file_path.name
    if target_path.exists():
        # 如果是相同文件，不移动
        if os.path.getsize(file_path) == os.path.getsize(target_path):
            try:
                with open(file_path, 'rb') as f1, open(target_path, 'rb') as f2:
                        logger.debug(f"文件相同，跳过: {file_path}")
                        return
            except Exception as e:
                logger.debug(f"文件比较失败: {e}")

        # 文件名冲突，添加时间戳
        base_name, ext = os.path.splitext(file_path.name)
        timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
        target_path = target_dir / (base_name + timestamp + ext)

    # 移动文件
    try:
        shutil.move(str(file_path), str(target_path))
        stats[category] += 1
    except Exception as e:
        logger.error(f"移动失败: {file_path} - {e}")
        stats['错误'] += 1

def scan_and_organize_logs():
    """扫描并整理项目中的所有日志文件"""
    logger.info("开始扫描和整理日志文件...")
    stats = defaultdict(int)
    processed_files = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 过滤排除目录

        # 跳过一级Logs目录
        if str(root) == str(LOG_DIR):
            continue
        for file in files:
            file_path = Path(root) / file

            # 检查是否为日志相关文件
                any(file_lower.endswith(ext) for ext in LOG_EXTENSIONS) or
                any(keyword in file_lower for keyword in ['log', '日志', 'error', 'backup', 'report', 'pid'])

                organize_log_file(file_path, stats)
                processed_files += 1

    # 输出统计信息
    logger.info(f"\n扫描完成！共处理 {processed_files} 个文件")
    logger.info("分类统计:")
    for cat, count in sorted(stats.items()):
        logger.info(f"  {cat}: {count}个文件")

def continuous_monitoring():
    """持续监控新的日志文件"""
    logger.info("开始持续监控日志文件...")
    logger.info("按 Ctrl+C 停止监控")

    # 注册信号处理
    def signal_handler(sig, frame):
        logger.info("接收到停止信号，正在停止监控...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 记录已处理的文件
    processed_files = set()

    while True:
        try:
            stats = defaultdict(int)
            new_files = 0

            for root, dirs, files in os.walk(PROJECT_ROOT):
                # 过滤排除目录
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                    continue

                    file_path = Path(root) / file
                    file_lower = file.lower()
                    # 判断是否为日志文件且未处理过
                        any(keyword in file_lower for keyword in ['log', '日志', 'error', 'backup', 'report', 'pid'])
                    )

                        processed_files.add(str(file_path))
            if new_files > 0:

            # 定期清理已处理文件记录，避免内存占用过大
            if len(processed_files) > 10000:
                # 只保留最近处理的5000个文件
                processed_files = set(list(processed_files)[-5000:])

            time.sleep(300)

        except Exception as e:
            # 短暂暂停后继续

    """主函数"""
    logger.info("=" * 60)
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    logger.info(f"日志目录: {LOG_DIR}")
