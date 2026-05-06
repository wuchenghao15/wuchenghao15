#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JavaScript 文件自动监控与加密工具
用于监控 MyScript 目录下的新 JavaScript 文件创建事件，并自动进行加密处理

import os
import time
import argparse
# JSON import removed - using database
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

# 导入现有的加密功能
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from encrypt_js import JSEncryptor

class JSMonitorHandler(FileSystemEventHandler):
    """文件系统事件处理器，用于监控新的JS文件创建"""

    def __init__(self, encryptor):
        初始化事件处理器

        Args:
            encryptor: JSEncryptor实例，用于执行加密操作
        self.encryptor = encryptor
        self.processed_files = set()
        self.last_process_time = {}
        self.min_interval = 2  # 最小处理间隔(秒)，避免频繁处理

    def on_created(self, event):
        """处理文件创建事件"""
        if not event.is_directory and event.src_path.endswith('.js'):
            self._process_file(event.src_path)

    def on_modified(self, event):
        """处理文件修改事件，可用于处理已存在但被修改的JS文件"""
        if not event.is_directory and event.src_path.endswith('.js'):
            # 检查文件是否已经被加密（通过文件内容判断）
            if not self._is_already_encrypted(event.src_path):

    def _is_already_encrypted(self, file_path):
        """检查文件是否已经被加密"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查是否包含加密标记
                return 'MTSCOS - Protected Script' in content
        except Exception:
            return False

    def _process_file(self, file_path, is_modified=False):
        """处理JS文件加密"""
        # 避免频繁处理同一文件
        current_time = time.time()
        if file_path in self.last_process_time:
            if current_time - self.last_process_time[file_path] < self.min_interval:
                return

        self.last_process_time[file_path] = current_time

        # 等待文件写入完成
        time.sleep(0.5)

        # 记录操作类型
        action = "修改" if is_modified else "创建"

        try:
            # 检查文件大小是否合理，避免处理空文件
            if os.path.getsize(file_path) == 0:
                self.encryptor.log(f"跳过空文件: {file_path}")

            # 使用JSEncryptor处理文件
            self.encryptor.log(f"检测到新{action}的JS文件: {file_path}")
            result = self.encryptor.process_file(file_path)
            if result:
                self.processed_files.add(file_path)
                self.encryptor.log(f"成功加密{action}的文件: {file_path}")
            else:
                self.encryptor.log(f"加密{action}的文件失败: {file_path}")

        except Exception as e:
            self.encryptor.log(f"处理{action}的文件时出错: {file_path} - {str(e)}")

class JSMonitor:
    """JavaScript文件监控器"""

    def __init__(self, watch_dir, output_dir=None, backup=True, verbose=False, log_file=None):
        初始化监控器

        Args:
            watch_dir: 监控目录路径
            output_dir: 输出目录路径
            backup: 是否备份原文件
            log_file: 日志文件路径
        self.watch_dir = watch_dir
        self.encryptor = JSEncryptor(
            input_dir=watch_dir,
            output_dir=output_dir,
            backup=backup,
            verbose=verbose
        )
        self.handler = JSMonitorHandler(self.encryptor)
        self.observer = Observer()
        self.running = False
        self.log_file = log_file
        self.monitor_logs = []

    def log(self, message):
        """记录监控日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [MONITOR] {message}"
        print(log_message)
        self.monitor_logs.append(log_message)

        # 保存到日志文件
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_message + '\n')
            except Exception as e:
                print(f"写入日志文件失败: {str(e)}")

    def start(self):
        try:
            # 检查监控目录是否存在
            if not os.path.isdir(self.watch_dir):
                self.log(f"错误: 监控目录 '{self.watch_dir}' 不存在")
                return False
            # 注册监控事件

            # 启动监控
            self.observer.start()
            self.running = True

            self.log(f"开始监控目录: {self.watch_dir}")
            self.log(f"按 Ctrl+C 停止监控")

            # 初始扫描，加密未被加密的现有JS文件
            self._initial_scan()

            return True

        except Exception as e:
            self.log(f"启动监控失败: {str(e)}")
            return False

    def _initial_scan(self):
        """初始扫描目录中的JS文件，加密未被加密的文件"""
        self.log("开始初始扫描目录中的JS文件...")

        unencrypted_count = 0
        for root, dirs, files in os.walk(self.watch_dir):
            for file in files:
                if file.endswith('.js'):
                        self.handler._process_file(file_path, is_modified=True)
                        unencrypted_count += 1

        if unencrypted_count > 0:
            self.log(f"初始扫描完成，共发现 {unencrypted_count} 个未加密的JS文件并尝试加密")
        else:
            self.log("初始扫描完成，所有JS文件已加密")

    def stop(self):
        """停止监控器"""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            self.log("监控已停止")

    def run_forever(self):
        """持续运行监控器"""
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.log("检测到中断信号，正在停止监控...")
            finally:
                self.stop()
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='JavaScript文件自动监控与加密工具')
        '--watch', '-w',
        default='./MyScript',
        help='监控目录路径，默认为 ./MyScript'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='输出目录路径，默认为直接替换原文件'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不备份原文件'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    parser.add_argument(
        '--log-file',
        help='指定日志文件路径'

    args = parser.parse_args()

    # 创建监控器并启动
        watch_dir=args.watch,
        output_dir=args.output,
        backup=not args.no_backup,
        verbose=args.verbose,
    )

    monitor.run_forever()

