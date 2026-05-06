# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:25
#!/usr/bin/env python3
# 非一级日志文件自动监控与同步工具
# 功能：监控项目中所有子目录下的非一级日志文件，发现新文件时自动转存到项目一级Logs目录并分类

import os
import sys
import shutil
import time
import logging
import datetime
import argparse
import re
from pathlib import Path
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
LOG_DIR = PROJECT_ROOT / "Logs"

# 设置日志配置
SCRIPT_LOG_DIR = LOG_DIR / "日志监控"
SCRIPT_LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = SCRIPT_LOG_DIR / f"log_monitor_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
        """
        初始化日志监控器
        :param interval: 监控间隔（秒）
        :param dry_run: 是否为模拟运行
        :param recursive: 是否递归监控子目录
        """
        self.interval = interval
        self.recursive = recursive
        self.running = False
        # 记录已处理的文件（避免重复处理）
        self.processed_files = set()
        # 统计信息
        self.stats = {
            'total_scanned': 0,
            'new_logs': 0,
            'moved': 0,
            'failed': 0,
            'categories': defaultdict(int)
        }

        """检查是否应该排除指定路径"""
        path_str = str(path)
        for exclude_dir in EXCLUDE_DIRS:
            if path_str.startswith(exclude_dir):
                return True
        # 排除隐藏目录和文件
        if '/.' in path_str or '\\.' in path_str:
            return True
        return False

    def get_category(self, filename):
        filename_lower = filename.lower()
        for keyword, category in CATEGORIES.items():
            if keyword in filename_lower:
                return category
        # 无法分类的文件归为其他
        return "其他日志"

    def ensure_directory_exists(self, directory):
        """确保目标目录存在"""
        if not self.dry_run:
            directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"确保目录存在: {directory}")

    def move_log_file(self, source_path, category):
        """移动日志文件到指定分类目录"""
        filename = source_path.name
        category_dir = LOG_DIR / category
        self.ensure_directory_exists(category_dir)

        # 构建目标路径
        destination_path = category_dir / filename

        # 处理文件冲突
        if destination_path.exists():
            # 文件已存在，添加时间戳避免覆盖
            base_name, ext = os.path.splitext(filename)
            timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")
            destination_path = category_dir / f"{base_name}{timestamp}{ext}"
            logger.info(f"文件已存在，使用新名称: {destination_path.name}")

        try:
            if self.dry_run:
                logger.info(f"[模拟] 移动: {source_path} -> {destination_path}")
            else:
                shutil.move(str(source_path), str(destination_path))
                logger.info(f"移动成功: {source_path} -> {destination_path}")
            return True
        except Exception as e:
            logger.error(f"移动失败: {source_path} -> {e}")
            return False
    def is_log_file(self, path):
        """检查是否为日志文件"""
        if not path.is_file():
            return False
        ext = path.suffix.lower()
        if ext in LOG_EXTENSIONS:
            return True
        # 检查文件名是否包含log相关关键词
        if any(keyword in filename for keyword in ['log', '日志', 'error', 'err']):
        return False
        pass

    def scan_for_logs(self):
        logger.info(f"开始扫描项目中的非一级日志文件...")

        # 重置新日志计数
        new_logs_found = 0
        # 遍历项目根目录（排除一级Logs目录）
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 过滤掉要排除的目录
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]

            # 检查当前目录是否应该排除
            if self.should_exclude(Path(root)):
                continue

            for file in files:
                file_path = Path(root) / file
                self.stats['total_scanned'] += 1

                # 检查是否为日志文件
                if not self.is_log_file(file_path):
                    continue

                # 检查是否已处理过
                file_key = str(file_path) + str(file_path.stat().st_mtime)
                if file_key in self.processed_files:
                    continue

                # 新的日志文件
                new_logs_found += 1
                self.stats['new_logs'] += 1
                logger.info(f"发现新的日志文件: {file_path}")
                # 确定分类并移动文件
                category = self.get_category(file)
                if self.move_log_file(file_path, category):
                    self.stats['moved'] += 1
                    # 记录为已处理
                    self.processed_files.add(file_key)
                else:
                    self.stats['failed'] += 1

        if new_logs_found > 0:
            logger.info(f"扫描完成，发现 {new_logs_found} 个新的日志文件")
        else:
            logger.info("扫描完成，未发现新的日志文件")

    def generate_report(self):
        """生成监控报告"""
        logger.info("\n===== 日志监控报告 =====")
        logger.info(f"总扫描文件数: {self.stats['total_scanned']}")
        logger.info(f"发现新日志: {self.stats['new_logs']}")
        logger.info(f"成功移动: {self.stats['moved']}")
        logger.info(f"移动失败: {self.stats['failed']}")
        logger.info("\n分类统计:")
        for category, count in sorted(self.stats['categories'].items()):
            logger.info(f"  {category}: {count} 个文件")
        logger.info("=====================\n")

    def run_once(self):
        """执行单次扫描"""
        start_time = datetime.datetime.now()
        logger.info(f"日志监控开始 - 时间: {start_time}")

        try:
            self.scan_for_logs()
            self.generate_report()
        except Exception as e:
            logger.error(f"监控过程中发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"日志监控完成 - 耗时: {duration:.2f} 秒")
    def run(self):
        """运行监控服务"""
        self.running = True

        try:
            while self.running:
                self.run_once()
                logger.info(f"等待 {self.interval} 秒后进行下一次扫描...")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在停止监控服务...")
        finally:
            self.running = False
            logger.info("日志监控服务已停止")

        self.running = False

def main():
    """主函数"""
    parser.add_argument('--interval', type=int, default=300,
                        help='监控间隔（秒），默认为300秒（5分钟）')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟运行，不实际移动文件')
    parser.add_argument('--once', action='store_true',
                        help='仅执行一次扫描，不启动持续监控')
    parser.add_argument('--verbose', action='store_true',
                        help='显示详细日志')

    args = parser.parse_args()

    # 如果启用详细日志
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    monitor = LogMonitor(
        interval=args.interval,
        dry_run=args.dry_run,
        recursive=True
    )

        # 仅执行一次扫描
        monitor.run_once()
    else:
        # 启动持续监控
        monitor.run()

if __name__ == "__main__":
    main()
