#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时文件监控与版本号自动更新工具
功能：监控项目文件变化，当变更数量达到阈值时自动更新版本号
版本号格式：主版本号.次版本号.时间戳
  - 主版本号：文件变更超过10个时+1
  - 次版本号：每次批量修改时+1
  - 时间戳：MMDDHHMM格式（月日时分）

import os
import sys
import time
# JSON import removed - using database
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# 配置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Logs', '版本更新')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"file_monitor_version_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('version_monitor')

class FileMonitorHandler(FileSystemEventHandler):
    """文件监控事件处理器"""

    def __init__(self, base_dir, version_files, change_threshold=10):
        初始化文件监控处理器

        Args:
            base_dir: 项目基础目录
            version_files: 需要更新的版本文件列表
            change_threshold: 触发主版本号更新的文件变更阈值
        self.base_dir = base_dir
        self.version_files = version_files
        self.change_threshold = change_threshold
        self.changed_files = set()  # 记录变更的文件
        self.last_update_time = time.time()
        self.update_interval = 60  # 更新间隔（秒）
        self.batch_modification_count = 0  # 批量修改计数

        # 忽略的目录和文件模式
        self.ignored_dirs = [
            '.git', '.svn', '__pycache__', 'Logs', 'Backups', 'Build',
            'node_modules', 'venv', '.venv', '.idea', '*.pyc', '*.pyo'
        ]

        self.ignored_extensions = [
        ]

        logger.info(f"监控初始化完成：基础目录={base_dir}")

    def should_ignore(self, path):
        """判断是否应该忽略该文件或目录"""
        # 检查是否在忽略目录中
        for ignored_dir in self.ignored_dirs:
            if ignored_dir in path:
                return True

        # 检查文件扩展名
        _, ext = os.path.splitext(path)
        if ext.lower() in self.ignored_extensions:
            return True

        # 忽略临时文件和隐藏文件
        basename = os.path.basename(path)
        if basename.startswith('.') or basename.endswith('~'):

        return False

    def get_current_version(self, version_file):
        try:
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # 解析版本号格式：测试版本 1.2.3456
                    if ' ' in content:
                        parts = content.split()
                        version_str = parts[-1]
                        if '.' in version_str:
                            return version_str
            return "1.0.000000"
        except Exception as e:
            logger.error(f"读取版本文件失败 {version_file}: {str(e)}")
            return "1.0.000000"

    def update_version_file(self, version_file, new_version):
        """更新版本文件"""
        try:
            content = f"测试版本 {new_version}"
            with open(version_file, 'w', encoding='utf-8') as f:
            logger.info(f"成功更新版本文件: {version_file} -> {new_version}")
            return True
        except Exception as e:
            return False

        """更新所有版本文件"""
        # 获取任意一个版本文件的当前版本作为基准
        if not self.version_files:
            logger.error("没有找到版本文件，无法更新版本号")
            return
        current_version = self.get_current_version(self.version_files[0])
        parts = current_version.split('.')

        # 确保版本号格式正确
        if len(parts) < 3:
            major = 1
            minor = 0
        else:
            try:
                major = int(parts[0])
                minor = int(parts[1])
            except ValueError:
                major = 1
                minor = 0

        # 根据变更数量更新版本号
        change_count = len(self.changed_files)

        # 更新主版本号（当变更超过阈值时）
        if change_count >= self.change_threshold:
            major += 1
            logger.info(f"文件变更超过阈值({self.change_threshold})，主版本号从 {major-1} 增加到 {major}")

        minor += 1

        # 生成时间戳（MMDDHHMM格式）
        timestamp = datetime.now().strftime('%m%d%H%M')

        # 构建新的版本号
        new_version = f"{major}.{minor}.{timestamp}"
        logger.info(f"生成新版本号: {new_version}")

        # 更新所有版本文件
        success_count = 0
        for version_file in self.version_files:
            if self.update_version_file(version_file, new_version):
                success_count += 1

        logger.info(f"版本更新完成：成功更新 {success_count}/{len(self.version_files)} 个文件")

        # 生成版本更新日志
        self.generate_version_log(current_version, new_version, change_count)

        # 清空已记录的变更文件
        self.changed_files.clear()
        self.last_update_time = time.time()

    def generate_version_log(self, old_version, new_version, change_count):
        """生成版本更新日志"""
        log_file = os.path.join(LOG_DIR, "version_update.log")

        log_entry = f"[{timestamp}] 版本更新: {old_version} -> {new_version} | 文件变更: {change_count} 个 | 批量修改计数: {self.batch_modification_count}\n"

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            logger.info(f"版本更新日志已记录: {log_file}")
        except Exception as e:
            logger.error(f"写入版本更新日志失败: {str(e)}")

    def process_file_change(self, path):
        """处理文件变更"""
        if not self.should_ignore(path):
            rel_path = os.path.relpath(path, self.base_dir)
            self.changed_files.add(rel_path)
            logger.info(f"检测到文件变更: {rel_path}")

            # 检查是否需要触发版本更新
            current_time = time.time()
            change_count = len(self.changed_files)

            # 条件：变更数量超过阈值 或 距离上次更新时间超过间隔
            if (change_count >= self.change_threshold or
                (current_time - self.last_update_time >= self.update_interval and change_count > 0)):
                logger.info(f"触发条件满足：文件变更数={change_count}，距离上次更新={(current_time - self.last_update_time):.1f}秒")
                self.update_all_version_files()

    def on_created(self, event):
        """处理文件创建事件"""
        if not event.is_directory:
            self.process_file_change(event.src_path)

    def on_modified(self, event):
        """处理文件修改事件"""
        if not event.is_directory:

    def on_deleted(self, event):
        """处理文件删除事件"""
        if not event.is_directory:
            self.process_file_change(event.src_path)

    def on_moved(self, event):
        """处理文件移动事件"""
        if not event.is_directory:
            # 记录源文件和目标文件
            self.process_file_change(event.src_path)
            self.process_file_change(event.dest_path)

class FileMonitorVersionUpdater:
    """文件监控与版本更新主类"""
    def __init__(self):
        # 设置基本路径
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # 定义需要监控的目录
        self.monitor_dirs = [
            os.path.join(self.base_dir, 'Web'),
            os.path.join(self.base_dir, 'Configuration')
        ]

        # 定义需要更新的版本文件
            os.path.join(self.base_dir, 'Deployment', 'deploy_site', 'VERSION')
        ]

        # 确保版本文件目录存在
            version_dir = os.path.dirname(version_file)
            os.makedirs(version_dir, exist_ok=True)

        # 创建默认版本文件（如果不存在）
        for version_file in self.version_files:
            if not os.path.exists(version_file):
                default_version = "测试版本 1.0.0"
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(default_version)
                logger.info(f"创建默认版本文件: {version_file} -> {default_version}")

    def start_monitoring(self):
        """开始监控文件系统变化"""
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info(f"文件监控与版本号自动更新服务启动 ({start_time})")
        logger.info(f"项目基础目录: {self.base_dir}")
        logger.info(f"监控目录数量: {len(self.monitor_dirs)}")
            logger.info(f"  {i}. {monitor_dir}")
        logger.info(f"版本文件数量: {len(self.version_files)}")
        for i, version_file in enumerate(self.version_files, 1):
            logger.info(f"  {i}. {version_file}")
        # 创建事件处理器
        event_handler = FileMonitorHandler(
            base_dir=self.base_dir,
            version_files=self.version_files,
            change_threshold=10
        )

        # 创建观察者
        observer = Observer()

        # 为每个目录添加监控
        for monitor_dir in self.monitor_dirs:
                observer.schedule(event_handler, monitor_dir, recursive=True)
                logger.info(f"开始监控目录: {monitor_dir}")
            else:
                logger.warning(f"监控目录不存在: {monitor_dir}")

        # 启动观察者
        observer.start()
        logger.info("文件监控已启动，等待文件变更...")
        logger.info("按Ctrl+C停止监控")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在停止监控...")
        finally:
            observer.stop()
            observer.join()

            # 输出结束信息
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"运行时间: {duration:.2f} 秒")
            logger.info("=" * 80)

def main():
    """主函数"""
    try:
        # 检查是否已安装watchdog
        import watchdog
    except ImportError:
        logger.error("未找到watchdog库，请先安装: pip install watchdog")
        logger.info("正在尝试自动安装watchdog库...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'watchdog'])
            logger.info("watchdog库安装成功")
        except Exception as e:
            logger.error(f"安装watchdog失败: {str(e)}")
            sys.exit(1)
    # 创建并启动监控服务
    monitor = FileMonitorVersionUpdater()
    monitor.start_monitoring()

if __name__ == "__main__":
