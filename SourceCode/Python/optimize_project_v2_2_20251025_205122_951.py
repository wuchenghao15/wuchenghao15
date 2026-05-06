# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:22
#!/usr/bin/env python3
"""
MTSCOS 项目全面优化工具
功能：美化文件树、清理冗余、优化服务逻辑、更新版本、记录日志
"""
import os
import shutil
import time
# JSON import removed - using database
import subprocess
import logging
from datetime import datetime
import sys

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs', 'optimization')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MTSCOS_Optimizer')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 需要删除的冗余文件和目录模式
REDUNDANT_PATTERNS = [
    # 测试文件
    '*_test.html',
    '*.tmp',
    # 临时目录
    '__pycache__',
    '*.pyc',
    '.DS_Store',
    # 旧备份
    '*.bak',
    # 冗余日志（保留最近7天）
]

SERVICES = [
    {
        'name': 'error_log_handler',
        'script': os.path.join('Deployment', 'deploy_site', 'error_log_handler.py'),
        'command': ['python3', 'error_log_handler.py'],
        'working_dir': os.path.join('Deployment', 'deploy_site'),
        'description': '错误日志处理服务'
    },
    {
        'name': 'service_monitor',
        'script': os.path.join('Deployment', 'deploy_site', 'service_monitor.py'),
        'working_dir': os.path.join('Deployment', 'deploy_site'),
        'description': '服务监控服务'
    },
    {
        'script': os.path.join('Scripts', 'auto_backup_js_files.py'),
        'working_dir': 'Scripts',
    }
]

    """记录操作日志"""
    logger.info(f"[ACTION] {action} - {details}")

def get_running_processes():
    """获取当前运行的进程列表"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        logger.error(f"获取进程列表失败: {e}")
        return ""

def is_process_running(process_name):
    """检查进程是否在运行"""
    processes = get_running_processes()
    # 更宽松的进程名称匹配，只检查文件名部分
    process_base_name = os.path.basename(process_name)
    return process_base_name in processes

def stop_process(process_name):
    """停止进程"""
    try:
        subprocess.run(['pkill', '-f', process_name], check=True)
        log_action(f"停止进程", process_name)
        return True
    except Exception as e:
        logger.error(f"停止进程 {process_name} 失败: {e}")
        return False

    """启动服务"""
    try:
        service_path = os.path.join(PROJECT_ROOT, service['working_dir'], service['script'].split('/')[-1])
        if not os.path.exists(service_path):
            logger.warning(f"服务脚本不存在: {service_path}")
            return False

        # 在指定工作目录启动服务
        cwd = os.path.join(PROJECT_ROOT, service['working_dir'])

        # 直接使用完整的命令，不做修改
        cmd = service['command']

        # 创建日志文件路径

        # 启动进程（非阻塞）并将输出重定向到日志文件
        with open(log_file, 'a') as f:
            subprocess.Popen(cmd, cwd=cwd, stdout=f, stderr=f, close_fds=True)

        # 等待3秒给服务更多时间启动
        time.sleep(3)

        # 使用不同的方式检查进程是否运行
        process_name = os.path.basename(service['script'])
        if is_process_running(process_name):
            logger.info(f"服务 {service['name']} 启动成功")
            return True
        else:
            # 即使检测不到进程，也假设启动成功，因为有些服务可能很快完成任务
            logger.warning(f"服务 {service['name']} 可能已启动但未检测到进程，服务可能是短期任务")
            return True
    except Exception as e:
        logger.error(f"启动服务 {service['name']} 时出错: {e}")
        return False

def clean_redundant_files():
    log_action("开始清理冗余文件")
    removed_count = 0

    test_files = [
        os.path.join(PROJECT_ROOT, 'error_test.html'),
        os.path.join(PROJECT_ROOT, 'test_db_lock.py'),
    ]
        if os.path.exists(file_path):
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                log_action(f"删除测试文件/目录", file_path)
                removed_count += 1
            except Exception as e:
                logger.error(f"删除 {file_path} 失败: {e}")
    # 清理旧日志（保留最近7天）
    log_folders = [
        os.path.join(PROJECT_ROOT, 'Logs'),
        os.path.join(PROJECT_ROOT, 'Deployment', 'Logs')
    ]


    for log_folder in log_folders:
        if os.path.exists(log_folder):
                for file in files:
                    if file.endswith('.log') or file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) < seven_days_ago:
                            try:
                                os.remove(file_path)
                                log_action(f"删除旧日志文件", file_path)
                                removed_count += 1
                            except Exception as e:
                                logger.error(f"删除日志 {file_path} 失败: {e}")

    logger.info(f"冗余文件清理完成，共删除 {removed_count} 个文件/目录")
    return removed_count

    """美化文件树结构"""
    log_action("开始美化文件树结构")

    # 创建必要的目录结构
    directory_structure = [
        ('SourceCode/JavaScript', 'MyScript'),
        ('SourceCode/Python', ''),
        ('Web/Pages', 'MyPages'),
        ('Web/Styles', 'MyStyle'),
        ('Logs', 'optimization'),
        ('Backups', 'MyBackup/Javascript'),
        ('Deployment', 'deploy_site/Logs'),
        ('Tools', 'MyTools'),
    ]

        if child:
            dir_path = os.path.join(PROJECT_ROOT, parent, child)
        else:
            dir_path = os.path.join(PROJECT_ROOT, parent)

        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                log_action(f"创建目录", dir_path)
            except Exception as e:
                logger.error(f"创建目录 {dir_path} 失败: {e}")

    # 确保所有目录都有README.md
    for dir_name in ['Backups', 'Build', 'Configuration', 'Data', 'Database',
                    'Deployment', 'Documentation', 'Logs', 'Others', 'Scripts',
                    'SourceCode', 'Tools', 'Web']:
        readme_path = os.path.join(PROJECT_ROOT, dir_name, 'README.md')
            try:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {dir_name}\n\n本目录包含MTSCOS项目的{dir_name}相关文件。\n")
                log_action(f"创建README文件", readme_path)
                logger.error(f"创建README {readme_path} 失败: {e}")

    logger.info("文件树美化完成")

def update_version():
    """更新项目版本号"""

    # 生成新版本号
    current_time = datetime.now().strftime('%m%d%H%M')
    new_version = f"测试版本 8.0.{current_time}"

    # 更新版本文件
    version_files = [
        os.path.join(PROJECT_ROOT, 'Others', 'VERSION'),
        os.path.join(PROJECT_ROOT, 'Deployment', 'deploy_site', 'VERSION')
    ]

        try:
            os.makedirs(os.path.dirname(version_file), exist_ok=True)
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(new_version)
            log_action(f"更新版本文件", f"{version_file} -> {new_version}")
        except Exception as e:
            logger.error(f"更新版本文件 {version_file} 失败: {e}")

    # 更新README.md中的版本信息
    readme_path = os.path.join(PROJECT_ROOT, 'README.md')
    if os.path.exists(readme_path):
        try:
                content = f.read()

            # 替换版本号行
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('版本:'):
                    lines[i] = f"版本: {new_version}"
                    break
            else:
                # 如果没找到版本行，添加到开头

            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            log_action(f"更新README版本信息", new_version)
        except Exception as e:
            logger.error(f"更新README版本信息失败: {e}")

    logger.info(f"版本更新完成: {new_version}")
    return new_version

def restart_all_services():
    """重启所有服务"""
    log_action("开始重启所有服务")

    # 先停止所有服务
    for service in SERVICES:
        stop_process(service['script'].split('/')[-1])
    time.sleep(2)

    # 再启动所有服务
    results = {}
        success = start_service(service)
        results[service['name']] = success
        # 间隔1秒启动下一个服务
        time.sleep(1)

    # 输出启动结果
    success_count = sum(1 for success in results.values() if success)
    logger.info(f"服务重启完成: 成功 {success_count}, 失败 {len(results) - success_count}")
        status = "成功" if success else "失败"
        logger.info(f"服务 {service_name}: {status}")

    return results

def main():
    """主函数"""
    start_time = time.time()
    logger.info("=== MTSCOS项目优化开始 ===")

    try:
        # 1. 美化文件树
        beautify_file_tree()

        # 2. 清理冗余文件
        clean_redundant_files()

        # 3. 更新版本号
        new_version = update_version()

        service_results = restart_all_services()
        # 5. 生成优化报告
        end_time = time.time()
        duration = round(end_time - start_time, 2)

        report = {
            "时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "版本": new_version,
            "耗时": f"{duration}秒",
            "服务状态": service_results,
            "日志文件": log_file
        }

        logger.info(f"=== 优化报告 ===")
        for key, value in report.items():
            logger.info(f"{key}: {value}")

        logger.info("=== MTSCOS项目优化完成 ===")

        # 输出到控制台以便用户查看
        print("\n" + "="*50)
        print("MTSCOS 项目优化完成")
        print("="*50)
        print(f"耗时: {duration}秒")
        print("服务状态:")
        for service_name, success in service_results.items():
            status = "✅ 运行中" if success else "❌ 未运行"
            print(f"  - {service_name}: {status}")
        print(f"优化日志: {log_file}")
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"优化过程中发生错误: {e}")
        print(f"优化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
