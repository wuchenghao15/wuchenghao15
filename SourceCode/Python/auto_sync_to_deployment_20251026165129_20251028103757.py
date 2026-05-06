# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:30
#!/usr/bin/env python3

"""
自动同步脚本 - 监控本地项目文件变化并自动同步到Deployment目录
使用Python的watchdog库实现文件监控功能，包含详细的日志记录和统计功能
"""
import os
import sys
import time
import shutil
import logging
import hashlib
from datetime import datetime
from logging.handlers import RotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent, FileMovedEvent

# 配置路径
SOURCE_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
DEPLOY_DIR = os.path.join(SOURCE_DIR, "Deployment/deploy_site")
LOG_DIR = os.path.join(SOURCE_DIR, "Logs")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 生成带时间戳的日志文件名，与shell脚本保持一致
LOG_TIMESTAMP = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"auto_sync_{LOG_TIMESTAMP}.log")
STATS_LOG = os.path.join(LOG_DIR, f"auto_sync_stats_{LOG_TIMESTAMP}.log")

# 配置日志（带轮转功能）

# 创建logger实例
logger = logging.getLogger("sync_logger")
logger.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 清除现有的处理器
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# 创建RotatingFileHandler进行日志轮转
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=10,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 定义颜色输出（用于终端显示）
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def log_with_color(message, color=None):
    """输出带颜色的日志信息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if color and sys.stdout.isatty():
        print(f"{color}{timestamp} - {message}{Colors.NC}")
    else:
        print(f"{timestamp} - {message}")
    # 记录到日志时不包含颜色代码
    logger.info(message)

def get_file_hash(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希值失败 {file_path}: {str(e)}")
        return None

def sync_file(src_file, dst_dir, relative_path=None, stats=None):
    """同步单个文件，支持统计信息收集"""
    try:
        # 初始化统计信息（如果未提供）
            stats = {
                'total_files': 0,
                'synced_files': 0,
                'failed_files': 0,
                'updated_files': 0,
                'created_files': 0,
                'deleted_files': 0,
                'total_size_bytes': 0,
                'synced_size_bytes': 0
            }

        # 确保目标目录存在
            os.makedirs(dst_dir, exist_ok=True)

        # 构建目标文件路径
        if relative_path:
            dst_file = os.path.join(dst_dir, relative_path)
            # 确保目标文件的父目录存在
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        else:
            dst_file = os.path.join(dst_dir, os.path.basename(src_file))
        # 获取源文件大小
        file_size = os.path.getsize(src_file)
        stats['total_size_bytes'] += file_size

        # 检查是否需要同步
        file_action = "新建"
        if os.path.exists(dst_file):
            # 检查文件是否相同（基于修改时间和大小）
            src_mtime = os.stat(src_file).st_mtime
            dst_mtime = os.stat(dst_file).st_mtime
            src_size = os.stat(src_file).st_size
            dst_size = os.stat(dst_file).st_size

            if src_mtime == dst_mtime and src_size == dst_size:
                stats['total_files'] += 1
                return True
            else:
                file_action = "更新"
        else:
            stats['created_files'] += 1
        # 复制文件
        shutil.copy2(src_file, dst_file)
        stats['synced_files'] += 1
        stats['total_files'] += 1
        stats['synced_size_bytes'] += file_size

        # 如果是脚本文件，添加执行权限
        if dst_file.endswith(('.sh', '.py', '.js')):
            os.chmod(dst_file, os.stat(dst_file).st_mode | 0o111)
        logger.info(f"[{file_action}] {src_file} -> {dst_file} ({file_size/1024:.2f} KB)")
        log_with_color(f"[{file_action}] {os.path.basename(src_file)} ({file_size/1024:.2f} KB)", Colors.GREEN)

        return True
    except Exception as e:
        stats['failed_files'] += 1
        stats['total_files'] += 1
        logger.error(f"同步文件失败 {src_file}: {str(e)}")
        log_with_color(f"同步文件失败 {os.path.basename(src_file)}: {str(e)}", Colors.RED)
        return False
def sync_directory(src_dir, dst_dir):
    stats = {
        'total_files': 0,
        'synced_files': 0,
        'failed_files': 0,
        'updated_files': 0,
        'created_files': 0,
        'total_size_bytes': 0,
    }
    try:
        start_time = time.time()
        # 如果目标目录不存在，创建它
        # 使用rsync风格的同步
        deleted_count = 0
            # 计算对应的源目录路径
            if relative_path != '.':
            else:
                src_root = src_dir
            # 删除不在源目录中的文件
            for file in files:
                src_file = os.path.join(src_root, file)
                dst_file = os.path.join(root, file)
                if not os.path.exists(src_file):
                        os.remove(dst_file)
                        deleted_count += 1
                        stats['deleted_files'] += 1
                        logger.info(f"[删除] {dst_file}")
                        log_with_color(f"[删除] {os.path.basename(dst_file)}", Colors.YELLOW)
                        logger.error(f"删除文件失败 {dst_file}: {str(e)}")

        # 复制源目录中的所有文件
        for root, dirs, files in os.walk(src_dir):
            # 计算相对路径
            relative_path = os.path.relpath(root, src_dir)
            if relative_path != '.':
                current_dst_dir = os.path.join(dst_dir, relative_path)
            else:
                current_dst_dir = dst_dir
            # 创建目标子目录
            for dir_name in dirs:
                os.makedirs(os.path.join(current_dst_dir, dir_name), exist_ok=True)

            # 复制文件
            for file in files:
                src_file = os.path.join(root, file)
                relative_file_path = os.path.relpath(src_file, src_dir)
                sync_file(src_file, dst_dir, relative_file_path, stats)

        # 计算耗时
        elapsed_time = time.time() - start_time

        # 记录目录同步统计信息
        logger.info(f"目录同步完成: {src_dir} -> {dst_dir}")
        logger.info(f"同步统计 - 文件总数: {stats['total_files']}, 成功: {stats['synced_files']}, 失败: {stats['failed_files']}, 删除: {stats['deleted_files']}")
        logger.info(f"同步统计 - 新建: {stats['created_files']}, 更新: {stats['updated_files']}")
        logger.info(f"同步统计 - 数据量: {stats['synced_size_bytes']/1024/1024:.2f} MB, 耗时: {elapsed_time:.2f} 秒")

        log_with_color(f"同步统计 - 成功: {stats['synced_files']}, 失败: {stats['failed_files']}, 删除: {stats['deleted_files']}", Colors.YELLOW)
        log_with_color(f"同步统计 - 数据量: {stats['synced_size_bytes']/1024/1024:.2f} MB, 耗时: {elapsed_time:.2f} 秒", Colors.YELLOW)

        return True, stats
    except Exception as e:
        logger.error(f"目录同步失败 {src_dir}: {str(e)}")
        log_with_color(f"目录同步失败 {src_dir}: {str(e)}", Colors.RED)
        return False, stats
def sync_project():
    """同步整个项目，返回详细的统计信息"""
    sync_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = time.time()

    # 初始化全局统计信息
    global_stats = {
        'sync_id': sync_id,
        'total_files': 0,
        'synced_files': 0,
        'failed_files': 0,
        'updated_files': 0,
        'created_files': 0,
        'deleted_files': 0,
        'total_size_bytes': 0,
        'synced_size_bytes': 0,
        'sync_time_seconds': 0,
        'sync_success': True
    }
    logger.info(f"===== 开始同步项目文件到Deployment目录 (ID: {sync_id}) =====")
    log_with_color(f"===== 开始同步项目文件到Deployment目录 (ID: {sync_id}) =====", Colors.GREEN)
    try:
        # 同步版本文件
        deploy_version = "未知版本"
        if os.path.exists(version_file):
                'total_files': 0,
                'failed_files': 0,
                'created_files': 0,
                'synced_size_bytes': 0
            }

            # 合并统计信息
                if key in global_stats:
                    global_stats[key] += value

            try:
                    deploy_version = f.read().strip()
                log_with_color(f"当前部署版本: {deploy_version}", Colors.GREEN)
            except Exception as e:
                logger.error(f"读取版本文件失败: {str(e)}")
        # 同步各目录并收集统计信息
        sync_tasks = [
            ("Web/Pages/MyPages", "MyPages", "页面文件"),
            ("SourceCode/JavaScript/MyScript", "MyScript", "JavaScript文件"),
            ("Tools/MyTools", "MyTools", "工具文件"),
            ("Data/MyData", "MyData", "数据文件")

        for src_path, dst_path, description in sync_tasks:
            web_pages_dir = os.path.join(SOURCE_DIR, src_path)
            if os.path.exists(web_pages_dir):
                logger.info(f"开始同步{description}: {web_pages_dir} -> {deploy_pages_dir}")
                success, stats = sync_directory(web_pages_dir, deploy_pages_dir)
                # 合并统计信息
                for key, value in stats.items():
                        global_stats[key] += value

                if not success:
                    global_stats['sync_success'] = False
            else:
                logger.warning(f"跳过同步{description}，源目录不存在: {web_pages_dir}")
        # 同步关键Python脚本
        python_dir = os.path.join(SOURCE_DIR, "SourceCode/Python")
        deploy_python_dir = os.path.join(DEPLOY_DIR, "MyPages")
        python_scripts = ["login.py", "register.py", "CheckCode.py"]

        if os.path.exists(python_dir):
            for script in python_scripts:
                script_path = os.path.join(python_dir, script)
                if os.path.exists(script_path):
                    sync_file(script_path, deploy_python_dir, stats=global_stats)

        # 复制主HTML文件
        source_index_html = os.path.join(os.path.join(DEPLOY_DIR, "MyPages"), "index.html")
        if os.path.exists(source_index_html):
            sync_file(source_index_html, DEPLOY_DIR, stats=global_stats)

        # 同步日志收集器相关文件
        logs_dir = os.path.join(SOURCE_DIR, "Logs")
        deploy_logs_dir = os.path.join(DEPLOY_DIR, "Logs")
        log_files = ["log_collector.py", "start_log_collector.sh"]

        if os.path.exists(logs_dir):
            for log_file in log_files:
                log_file_path = os.path.join(logs_dir, log_file)
                if os.path.exists(log_file_path):
                    sync_file(log_file_path, deploy_logs_dir, stats=global_stats)

        # 更新日志收集器端口配置
        config_changed = False
        log_manager_js = os.path.join(DEPLOY_DIR, "MyScript/log_manager.js")
        if os.path.exists(log_manager_js):
            try:
                with open(log_manager_js, 'r') as f:
                    content = f.read()

                # 更新端口配置
                new_content = content.replace(
                    'server_log_endpoint = "http://localhost:9000/Logs/save_log"',
                    'server_log_endpoint = "http://localhost:9999/Logs/save_log"',
                    'server_log_endpoint = "http://localhost:8002/Logs/save_log"'

                    with open(log_manager_js, 'w') as f:
                        f.write(new_content)
                    config_changed = True
                    logger.info(f"已更新日志收集器配置: {log_manager_js}")
                    log_with_color(f"已更新日志收集器配置", Colors.GREEN)
            except Exception as e:
                global_stats['sync_success'] = False
                logger.error(f"更新日志收集器配置失败: {str(e)}")
                log_with_color(f"更新日志收集器配置失败: {str(e)}", Colors.RED)

        # 计算总耗时
        global_stats['sync_time_seconds'] = time.time() - start_time

        # 记录最终同步统计信息
        logger.info(f"===== 项目同步完成 (ID: {sync_id}) =====")
        logger.info(f"同步结果: {'成功' if global_stats['sync_success'] else '部分失败'}")
        logger.info(f"部署版本: {deploy_version}")
        logger.info(f"文件统计: 总数={global_stats['total_files']}, 成功={global_stats['synced_files']}, 失败={global_stats['failed_files']}")
        logger.info(f"操作统计: 新建={global_stats['created_files']}, 更新={global_stats['updated_files']}, 删除={global_stats['deleted_files']}")
        logger.info(f"数据统计: 同步大小={global_stats['synced_size_bytes']/1024/1024:.2f} MB, 总大小={global_stats['total_size_bytes']/1024/1024:.2f} MB")
        logger.info(f"时间统计: 总耗时={global_stats['sync_time_seconds']:.2f} 秒, 速度={global_stats['synced_size_bytes']/1024/1024/global_stats['sync_time_seconds']:.2f} MB/秒")
        if config_changed:
            logger.info("配置更新: 日志收集器配置已更新")

        # 输出彩色统计信息到终端
        log_with_color(f"===== 项目同步完成 (ID: {sync_id}) =====", Colors.GREEN)
        log_with_color(f"同步结果: {'成功' if global_stats['sync_success'] else '部分失败'}",
                     Colors.GREEN if global_stats['sync_success'] else Colors.YELLOW)
        log_with_color(f"部署版本: {deploy_version}", Colors.GREEN)
        log_with_color(f"文件统计: 总数={global_stats['total_files']}, 成功={global_stats['synced_files']}, 失败={global_stats['failed_files']}", Colors.YELLOW)
        log_with_color(f"操作统计: 新建={global_stats['created_files']}, 更新={global_stats['updated_files']}, 删除={global_stats['deleted_files']}", Colors.YELLOW)
        log_with_color(f"数据统计: {global_stats['synced_size_bytes']/1024/1024:.2f} MB, 耗时: {global_stats['sync_time_seconds']:.2f} 秒", Colors.YELLOW)

        # 将同步统计信息保存到单独的统计日志文件，与shell脚本格式一致
        with open(STATS_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ID:{sync_id} 结果:{global_stats['sync_success']} 版本:{deploy_version} "
                    f"文件:总数={global_stats['total_files']},成功={global_stats['synced_files']},失败={global_stats['failed_files']} "
                    f"操作:新建={global_stats['created_files']},更新={global_stats['updated_files']},删除={global_stats['deleted_files']} "
                    f"数据:{global_stats['synced_size_bytes']/1024/1024:.2f}MB 时间:{global_stats['sync_time_seconds']:.2f}s\n")

    except Exception as e:
        global_stats['sync_success'] = False
        global_stats['sync_time_seconds'] = time.time() - start_time
        logger.error(f"项目同步过程中发生错误: {str(e)}")
        log_with_color(f"项目同步过程中发生错误: {str(e)}", Colors.RED)

    return global_stats

    """处理文件系统事件的处理器"""

    def __init__(self):
        self.last_sync_time = 0
        self.sync_delay = 1  # 同步延迟时间（秒）

    def on_any_event(self, event):
        """处理任何文件系统事件"""
        # 忽略临时文件和目录事件
        if event.is_directory or \
            return

        # 限制同步频率
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_delay:
            return

        # 记录事件
        event_type = "修改" if isinstance(event, FileModifiedEvent) else \
                    "创建" if isinstance(event, FileCreatedEvent) else \
                    "删除" if isinstance(event, FileDeletedEvent) else \
                    "移动" if isinstance(event, FileMovedEvent) else "未知"

        log_with_color(f"检测到文件{event_type}: {event.src_path}", Colors.YELLOW)

        # 执行同步
        self.last_sync_time = current_time
        sync_project()

def main():
    """主函数"""
    try:
        # 检查是否安装了watchdog
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            log_with_color("未安装watchdog库，尝试安装...", Colors.YELLOW)
            import subprocess
            log_with_color("watchdog库安装成功", Colors.GREEN)
        # 执行初始同步
        sync_project()

        monitor_dirs = [
            os.path.join(SOURCE_DIR, "Web/Pages/MyPages"),
            os.path.join(SOURCE_DIR, "Web/Styles/MyStyle"),
            os.path.join(SOURCE_DIR, "Tools/MyTools"),
            os.path.join(SOURCE_DIR, "Data/MyData"),
            os.path.join(SOURCE_DIR, "SourceCode/Python"),
            os.path.join(SOURCE_DIR, "Others"),
            os.path.join(SOURCE_DIR, "Logs")
        ]

        # 过滤掉不存在的目录
        valid_monitor_dirs = []
        for dir_path in monitor_dirs:
            if os.path.exists(dir_path):
                valid_monitor_dirs.append(dir_path)
                log_with_color(f"添加监控目录: {dir_path}", Colors.GREEN)
            else:
                log_with_color(f"监控目录不存在，跳过: {dir_path}", Colors.YELLOW)

        # 检查是否有有效的监控目录
            log_with_color("没有找到有效的监控目录，脚本退出", Colors.RED)
            sys.exit(1)

        # 创建观察者和事件处理器
        event_handler = FileChangeHandler()
        observer = Observer()
        # 为每个目录添加监控
        for dir_path in valid_monitor_dirs:
            observer.schedule(event_handler, dir_path, recursive=True)

        # 启动观察者
        observer.start()
        log_with_color("开始监控文件变化，按 Ctrl+C 停止...", Colors.GREEN)

        # 保持脚本运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log_with_color("接收到中断信号，停止监控...", Colors.YELLOW)
        finally:
            observer.stop()
            observer.join()
            log_with_color("监控已停止", Colors.YELLOW)

    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
