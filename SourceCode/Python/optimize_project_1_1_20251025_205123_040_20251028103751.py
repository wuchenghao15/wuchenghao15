# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:24
#!/usr/bin/env python3
"""
MTSCOS项目优化脚本
用于整理文件结构、删除冗余文件、更新版本信息并启动服务
"""
import os
import shutil
import time
import subprocess
import datetime
import logging
import re
from pathlib import Path

# 配置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs', 'optimization')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'optimization_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MTSCOS_Optimizer')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 部署目录
DEPLOY_DIR = os.path.join(PROJECT_ROOT, 'Deployment', 'deploy_site')

# 需要删除的冗余文件和目录
REDUNDANT_ITEMS = [
    # 测试文件和目录
    os.path.join(PROJECT_ROOT, 'SourceCode', 'TestChanges'),
    os.path.join(PROJECT_ROOT, 'Backups', 'MyBackup'),

    # 测试脚本
    os.path.join(PROJECT_ROOT, 'test_complete_sync_logs.sh'),
    os.path.join(PROJECT_ROOT, 'test_logs.sh'),
    os.path.join(PROJECT_ROOT, 'test_sync_logs.sh'),

    # 旧版本文件
    os.path.join(DEPLOY_DIR, 'VERSION.old'),

    # 部署目录下的空文件夹
    os.path.join(DEPLOY_DIR, 'MyTools'),
]

LOG_DIRS_TO_CLEAN = [
    os.path.join(PROJECT_ROOT, 'Logs', '报告文件'),
    os.path.join(PROJECT_ROOT, 'Logs', '日志分类器'),
    os.path.join(PROJECT_ROOT, 'Logs', '自动备份'),
    os.path.join(PROJECT_ROOT, 'Logs', '自动同步'),
]

SERVICES_TO_START = [
    {
        'name': 'error_log_handler',
        'script': os.path.join(DEPLOY_DIR, 'error_log_handler.py'),
        'command': f'python3 {os.path.join(DEPLOY_DIR, "error_log_handler.py")}',
        'cwd': DEPLOY_DIR,
        'description': '错误日志处理服务'
    },
    {
        'name': 'service_monitor',
        'script': os.path.join(DEPLOY_DIR, 'service_monitor.py'),
        'command': f'python3 {os.path.join(DEPLOY_DIR, "service_monitor.py")}',
        'description': '服务监控脚本'
    },
    {
        'name': 'auto_backup_js',
        'command': f'python3 {os.path.join(PROJECT_ROOT, "Scripts", "auto_backup_js_files.py")} --auto-run',
        'description': 'JavaScript自动备份服务'
]

    """记录操作日志"""
    logger.info(f"[{action}] {details}")

def delete_redundant_items():
    log_action("开始", "删除冗余文件和目录")

    for item in REDUNDANT_ITEMS:
        if os.path.exists(item):
            try:
                if os.path.isfile(item) or os.path.islink(item):
                    os.remove(item)
                    log_action("删除文件", item)
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    log_action("删除目录", item)
            except Exception as e:
                logger.error(f"删除 {item} 失败: {str(e)}")

    log_action("完成", "删除冗余文件和目录")

def clean_old_logs(days_to_keep=7):
    """清理旧日志文件"""
    log_action("开始", f"清理{days_to_keep}天前的日志文件")

    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

    for log_dir in LOG_DIRS_TO_CLEAN:
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                file_path = os.path.join(log_dir, filename)
                if os.path.isfile(file_path):
                    # 检查文件修改时间
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            log_action("删除旧日志", file_path)
                        except Exception as e:
                            logger.error(f"删除旧日志 {file_path} 失败: {str(e)}")

    log_action("完成", "清理旧日志文件")

def update_version():
    """更新版本信息"""

    # 生成新版本号
    now = datetime.datetime.now()
    version_date = now.strftime("%m%d")
    version_time = now.strftime("%H%M")

    # 读取当前版本
    version_file = os.path.join(DEPLOY_DIR, 'VERSION')
    current_version = "测试版本 6.6.00000000"
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            current_version = f.read().strip()

    # 解析版本号并更新
    version_match = re.search(r'测试版本 (\d+)\.(\d+)\.(\d{8})', current_version)
    if version_match:
        major, minor = version_match.group(1), version_match.group(2)
        new_version = f"测试版本 {major}.{minor}.{version_date}{version_time}"
    else:
        new_version = f"测试版本 6.6.{version_date}{version_time}"

    # 保存新版本
    try:
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(new_version)
        log_action("更新版本", f"新版本: {new_version}")

        # 更新README.md中的版本信息
        update_readme_version(new_version)
    except Exception as e:
        logger.error(f"更新版本信息失败: {str(e)}")

    return new_version

def update_readme_version(new_version):
    """更新README.md中的版本信息"""
    readme_file = os.path.join(DEPLOY_DIR, 'README.md')
    if os.path.exists(readme_file):
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换版本号
            if re.search(r'版本: [^\n]+', content):
                content = re.sub(r'版本: [^\n]+', f'版本: {new_version}', content)
            else:
                # 如果没有版本信息，添加到开头
                content = f"版本: {new_version}\n\n" + content
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(content)
            log_action("更新README", f"更新README中的版本信息为: {new_version}")
        except Exception as e:
            logger.error(f"更新README失败: {str(e)}")

def start_service(service):
    """启动指定的服务"""
    log_action("开始", f"启动服务: {service['name']} ({service['description']})")
    try:
        # 检查服务是否已经在运行
        check_cmd = f'pgrep -f "{os.path.basename(service["script"])}"'
        result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            # 服务已经在运行，先停止它
            pids = result.stdout.decode().strip().split()
            for pid in pids:
                log_action("停止服务", f"停止已运行的 {service['name']} (PID: {pid})")
                time.sleep(1)

        # 启动新的服务实例
        log_action("执行命令", f"在 {service['cwd']} 中执行: {service['command']}")

        # 使用nohup启动服务，使其在后台运行
        nohup_cmd = f'nohup {service["command"]} > /dev/null 2>&1 &'
        subprocess.run(nohup_cmd, shell=True, cwd=service['cwd'])

        # 等待服务启动
        time.sleep(2)

        # 验证服务是否启动成功
        result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE)
        if result.returncode == 0:
            pids = result.stdout.decode().strip().split()
            log_action("启动成功", f"服务 {service['name']} 已启动 (PID: {pids[0]})")
            return True
        else:
            log_action("启动失败", f"服务 {service['name']} 启动失败")
            return False
    except Exception as e:
        logger.error(f"启动服务 {service['name']} 时出错: {str(e)}")
        return False

def start_all_services():
    """启动所有需要的服务"""
    log_action("开始", "启动所有服务")

    for service in SERVICES_TO_START:

    log_action("完成", f"服务启动完成，成功启动 {success_count}/{len(SERVICES_TO_START)} 个服务")

def check_service_status():
    """检查所有服务的运行状态"""
    log_action("开始", "检查服务状态")

    for service in SERVICES_TO_START:
        result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE)

        if result.returncode == 0:
            pids = result.stdout.decode().strip().split()
            log_action("服务状态", f"{service['name']}: 运行中 (PID: {pids[0]})")
        else:
            log_action("服务状态", f"{service['name']}: 未运行")

    log_action("完成", "检查服务状态")

def main():
    """主函数"""
    start_time = time.time()
    log_action("优化开始", "MTSCOS项目优化开始执行")

        # 1. 删除冗余文件和目录
        delete_redundant_items()
        # 3. 更新版本信息

        start_all_services()

        # 5. 检查服务状态
        check_service_status()

        # 6. 生成优化报告
        end_time = time.time()
        log_action("优化完成", f"MTSCOS项目优化完成，耗时: {end_time - start_time:.2f}秒")
        log_action("优化报告", f"项目版本已更新至: {new_version}")
        log_action("优化报告", f"日志已保存至: {LOG_FILE}")

        print(f"\n优化完成！版本: {new_version}")
        print(f"详细日志: {LOG_FILE}")

    except Exception as e:
        logger.error(f"优化过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()
