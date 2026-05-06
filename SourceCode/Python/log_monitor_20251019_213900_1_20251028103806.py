# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:19
#!/usr/bin/env python3
# 非一级日志文件自动监控与同步工具

import os
import sys
import shutil
import time
import logging
import datetime
import argparse
from pathlib import Path
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = PROJECT_ROOT / "Logs"

# 设置日志配置
SCRIPT_LOG_DIR = LOG_DIR / "日志监控"
SCRIPT_LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = SCRIPT_LOG_DIR / ("log_monitor_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("LogMonitor")

# 定义日志文件扩展名
LOG_EXTENSIONS = ['.log', '.txt', '.json']

# 定义排除的目录
EXCLUDE_DIRS = [
    str(LOG_DIR),
    str(PROJECT_ROOT / "Build"),
    str(PROJECT_ROOT / "Backups"),
    str(PROJECT_ROOT / ".git"),
    str(PROJECT_ROOT / "node_modules"),
    str(PROJECT_ROOT / "__pycache__")
]
# 定义分类规则：关键词 -> 目标目录
CATEGORIES = {
    'auto_sync': '自动同步',
    'logs_sorter': '日志分类器',
    'logs_sorting_report': '报告文件',
    'test': '其他',
    'backup': '备份工具',
    'performance': '性能优化',
    'clean': '冗余清理',
    'organizer': '文件夹整理',
    'root_organizer': '根目录整理',
    'error_log': '错误日志',
    'error': '错误日志',
    'build': '构建系统',
    'encrypt': 'JavaScript加密',
    'monitor': 'JavaScript监控',
    'anti_hotlink': '防盗链脚本',
    'version': '版本更新',
    'login': '登录系统',
    'register': '注册系统',
    'verifycode': '验证码系统',
    'arduino': 'Arduino模块',
    'mssql': '数据库配置',
    'database': '数据库配置',
    'service': '服务监控',
    'js_monitor': 'JavaScript监控',
    'bak_backup': '备份工具'
}

class LogMonitor:
    def __init__(self, interval=300, dry_run=False, recursive=True):
        self.interval = interval
        self.dry_run = dry_run
        self.recursive = recursive
        self.running = False
        self.processed_files = set()
        self.stats = {
            'total_scanned': 0,
            'new_logs': 0,
            'moved': 0,
            'failed': 0,
            'categories': defaultdict(int)
        }

        path_str = str(path)
        for exclude_dir in EXCLUDE_DIRS:
            if path_str.startswith(exclude_dir):
                return True
        if '/.' in path_str or '\\.' in path_str:
            return True
        return False

        filename_lower = filename.lower()
        for keyword, category in CATEGORIES.items():
            if keyword in filename_lower:
                return category
        return '其他日志'

    def ensure_directory_exists(self, directory):
        if not self.dry_run:
            directory.mkdir(parents=True, exist_ok=True)
        logger.debug('确保目录存在: ' + str(directory))

    def move_log_file(self, source_path, category):
        filename = source_path.name
        category_dir = LOG_DIR / category
        self.ensure_directory_exists(category_dir)

        destination_path = category_dir / filename

        if destination_path.exists():
            base_name, ext = os.path.splitext(filename)
            timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
            destination_path = category_dir / (base_name + timestamp + ext)
            logger.info('文件已存在，使用新名称: ' + destination_path.name)

        try:
            if self.dry_run:
                logger.info('[模拟] 移动: ' + str(source_path) + ' -> ' + str(destination_path))
            else:
                shutil.move(str(source_path), str(destination_path))
                logger.info('移动成功: ' + str(source_path) + ' -> ' + str(destination_path))
            return True
        except Exception as e:
            logger.error('移动失败: ' + str(source_path) + ' -> ' + str(e))

    def is_log_file(self, path):
        if not path.is_file():
            return False
        if ext in LOG_EXTENSIONS:
            return True
        filename = path.name.lower()
        return False

        logger.info('开始扫描项目中的非一级日志文件...')
        new_logs_found = 0

        for root, dirs, files in os.walk(PROJECT_ROOT):

            if self.should_exclude(Path(root)):
                continue

            for file in files:
                file_path = Path(root) / file
                self.stats['total_scanned'] += 1

                if not self.is_log_file(file_path):
                    continue

                file_key = str(file_path) + str(file_path.stat().st_mtime)
                if file_key in self.processed_files:
                    continue

                new_logs_found += 1
                self.stats['new_logs'] += 1
                logger.info('发现新的日志文件: ' + str(file_path))

                if self.move_log_file(file_path, category):
                    self.stats['moved'] += 1
                    self.stats['categories'][category] += 1
                else:
                    self.stats['failed'] += 1

        if new_logs_found > 0:
            logger.info('扫描完成，发现 ' + str(new_logs_found) + ' 个新的日志文件')
        else:
            logger.info('扫描完成，未发现新的日志文件')

    def generate_report(self):
        logger.info('\n===== 日志监控报告 =====')
        logger.info('总扫描文件数: ' + str(self.stats['total_scanned']))
        logger.info('发现新日志: ' + str(self.stats['new_logs']))
        logger.info('成功移动: ' + str(self.stats['moved']))
        logger.info('移动失败: ' + str(self.stats['failed']))
        logger.info('\n分类统计:')
        for category, count in sorted(self.stats['categories'].items()):
            logger.info('  ' + category + ': ' + str(count) + ' 个文件')
        logger.info('=====================\n')

    def run_once(self):
        start_time = datetime.datetime.now()
        logger.info('日志监控开始 - 时间: ' + str(start_time))

        try:
            self.scan_for_logs()
            self.generate_report()
        except Exception as e:
            logger.error('监控过程中发生错误: ' + str(e))
            import traceback
            logger.error(traceback.format_exc())

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()

    def run(self):
        self.running = True

        try:
            while self.running:
                self.run_once()
                logger.info('等待 ' + str(self.interval) + ' 秒后进行下一次扫描...')
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info('收到停止信号，正在停止监控服务...')
        finally:
            self.running = False
            logger.info('日志监控服务已停止')
        self.running = False

def main():
    parser.add_argument('--interval', type=int, default=300,
                        help='监控间隔（秒），默认为300秒（5分钟）')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟运行，不实际移动文件')
    parser.add_argument('--once', action='store_true',
                        help='仅执行一次扫描，不启动持续监控')
    parser.add_argument('--verbose', action='store_true',
                        help='显示详细日志')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    monitor = LogMonitor(
        interval=args.interval,
        dry_run=args.dry_run,
        recursive=True
    )

        monitor.run_once()
    else:
        monitor.run()

if __name__ == "__main__":
    main()
