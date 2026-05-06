# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:21
#!/usr/bin/env python3
"""
服务监控与自动修复脚本
功能：监控系统中各种自动执行的脚本和服务依赖项，检测启动和加载状态，自动修复错误
"""
import os
import sys
import time
import subprocess
# JSON import removed - using database
import logging
import psutil
import signal
import datetime
from pathlib import Path

# 配置日志
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "Logs", "服务监控")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"service_monitor_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# 定义需要监控的服务配置
SERVICES_CONFIG = {
    "js_monitor": {
        "name": "JavaScript文件监控服务",
        "start_script": os.path.join(SCRIPT_DIR, "start_js_monitor.sh"),
        "stop_script": None,  # 通过start脚本的stop参数停止或使用auto_start_all_monitors.sh
        "pid_file": os.path.join(SCRIPT_DIR, ".js_monitor.pid"),
        "monitor_script": os.path.join(SCRIPT_DIR, "../SourceCode/Python/monitor_js_files.py"),
        "log_dir": os.path.join(SCRIPT_DIR, "../Logs/JavaScript监控"),
        "dependencies": ["python3"]
    },
    "version_monitor": {
        "name": "版本监控服务",
        "start_script": os.path.join(SCRIPT_DIR, "start_version_monitor.sh"),
        "stop_script": None,  # 通过start脚本的stop参数停止
        "pid_file": os.path.join(SCRIPT_DIR, ".version_monitor.pid"),
        "monitor_script": os.path.join(SCRIPT_DIR, "../SourceCode/Python/update_version.py"),
        "log_dir": os.path.join(SCRIPT_DIR, "../Logs/版本更新"),
        "dependencies": ["python3"]
    },
        "name": "备份服务",
        "stop_script": None,
        "pid_file": os.path.join(SCRIPT_DIR, ".bak_backup_service.pid"),
        "monitor_script": os.path.join(SCRIPT_DIR, "../SourceCode/Python/real_time_bak_backup.py"),
        "log_dir": os.path.join(SCRIPT_DIR, "../Logs/备份工具"),
        "dependencies": ["python3"]
    },
        "name": "错误日志处理服务",
        "start_script": os.path.join(SCRIPT_DIR, "start_error_log_processor.sh"),
        "pid_file": os.path.join(SCRIPT_DIR, "../Logs/error_log_processor.pid"),
        "monitor_script": os.path.join(SCRIPT_DIR, "../SourceCode/Python/error_log_processor.py"),
        "log_dir": os.path.join(SCRIPT_DIR, "../Logs/错误日志"),
        "dependencies": ["python3"]
    }
# 系统依赖项
SYSTEM_DEPENDENCIES = [
    "python3",
    "bash",
    "node"
]
    def __init__(self, check_interval=60, auto_fix=True):
        self.check_interval = check_interval
        self.auto_fix = auto_fix
        self.running = False
        self.service_status = {}

    def check_system_dependencies(self):
        """检查系统依赖项是否安装"""
        logging.info("检查系统依赖项...")
        missing_deps = []

        for dep in SYSTEM_DEPENDENCIES:
            try:
                subprocess.run(["which", dep], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info(f"依赖项 '{dep}' 已安装")
            except subprocess.CalledProcessError:
                missing_deps.append(dep)
                logging.warning(f"依赖项 '{dep}' 未安装")

        if missing_deps and self.auto_fix:
            logging.info("尝试安装缺失的依赖项...")
            # 根据操作系统类型安装依赖项
            try:
                if sys.platform == "darwin":  # macOS
                    for dep in missing_deps:
                        if dep == "node":
                            logging.info("建议使用 Homebrew 安装 Node.js: brew install node")
                        elif dep == "python3":
                            logging.info("macOS 已预装 Python3，可能需要更新或重新安装")
                elif sys.platform.startswith("linux"):
                    # 尝试使用 apt-get (Debian/Ubuntu)
                    if subprocess.run(["which", "apt-get"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                        subprocess.run(cmd)

                        install_cmd = ["sudo", "apt-get", "install", "-y"]
                        if "python3" in missing_deps:
                            install_cmd.append("python3")
                        if "node" in missing_deps:
                            install_cmd.append("nodejs")
                        if len(install_cmd) > 3:
                            subprocess.run(install_cmd)
            except Exception as e:
                logging.error(f"安装依赖项失败: {str(e)}")

        return len(missing_deps) == 0

    def check_service_script_exists(self, service_config):
        """检查服务脚本是否存在"""
        if not os.path.exists(service_config["start_script"]):
            logging.error(f"服务启动脚本不存在: {service_config['start_script']}")
            return False

        if service_config["stop_script"] and not os.path.exists(service_config["stop_script"]):
            logging.warning(f"服务停止脚本不存在: {service_config['stop_script']}")

        return True

    def check_pid_file(self, pid_file):
        """检查PID文件是否有效"""
        if not os.path.exists(pid_file):
            return False, None

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # 检查进程是否存在
            if psutil.pid_exists(pid):
                return True, pid
            else:
                # PID文件存在但进程不存在，删除无效的PID文件
                os.remove(pid_file)
                return False, None
        except Exception as e:
            logging.error(f"读取PID文件失败: {pid_file}, {str(e)}")
            return False, None

    def is_service_running(self, service_id):
        """检查服务是否正在运行"""
        service_config = SERVICES_CONFIG[service_id]
        is_running, pid = self.check_pid_file(service_config["pid_file"])

        if is_running:
            try:
                cmdline = ' '.join(process.cmdline())
                monitor_script = os.path.basename(service_config["monitor_script"])
                    logging.info(f"服务 '{service_config['name']}' 正在运行 (PID: {pid})")
                    return True, pid
                else:
                    # 进程存在但不是我们期望的服务
                    os.remove(service_config["pid_file"])
                    return False, None
            except Exception as e:
                logging.error(f"检查进程信息失败: {str(e)}")
                return False, None

        return False, None

    def start_service(self, service_id):
        """启动服务"""
        service_config = SERVICES_CONFIG[service_id]
        logging.info(f"尝试启动服务: {service_config['name']}")
        # 确保日志目录存在
        os.makedirs(service_config["log_dir"], exist_ok=True)
        if not self.check_service_script_exists(service_config):
            return False
        # 确保脚本有执行权限
            logging.info(f"为启动脚本添加执行权限: {service_config['start_script']}")
            try:
                subprocess.run(["chmod", "+x", service_config["start_script"]], check=True)
            except subprocess.CalledProcessError:
                logging.error(f"添加执行权限失败: {service_config['start_script']}")
                return False

        # 启动服务
        try:
            if service_id == "version_monitor":
            else:
                cmd = ["bash", service_config["start_script"]]

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 等待一段时间让服务启动
            time.sleep(3)

            # 验证服务是否成功启动
            if is_running:
                logging.info(f"服务启动成功: {service_config['name']}")
                return True
            else:
                logging.error(f"服务启动失败: {service_config['name']}")
                return False
        except subprocess.CalledProcessError as e:
            stderr_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "无错误输出"
            logging.error(f"启动服务失败: {service_config['name']}, 错误: {stderr_output}")
            return False
        except Exception as e:
            logging.error(f"启动服务时发生异常: {service_config['name']}, {str(e)}")
            return False

    def stop_service(self, service_id):
        """停止服务"""
        service_config = SERVICES_CONFIG[service_id]
        logging.info(f"尝试停止服务: {service_config['name']}")

        # 首先检查PID文件并尝试优雅停止
        is_running, pid = self.check_pid_file(service_config["pid_file"])
        if is_running and pid:
                os.kill(pid, signal.SIGTERM)
                logging.info(f"向进程 {pid} 发送 SIGTERM 信号")
                # 等待进程终止
                start_time = time.time()
                while psutil.pid_exists(pid) and time.time() - start_time < timeout:
                    # 如果进程仍然存在，发送SIGKILL
                    os.kill(pid, signal.SIGKILL)
                    logging.warning(f"向进程 {pid} 发送 SIGKILL 信号")

                # 删除PID文件
                if os.path.exists(service_config["pid_file"]):
                    os.remove(service_config["pid_file"])
                    logging.info(f"已删除PID文件: {service_config['pid_file']}")

                return True
            except Exception as e:
                logging.error(f"停止进程失败: {pid}, {str(e)}")

        # 尝试使用停止脚本
            try:
                subprocess.run(["bash", service_config["stop_script"]], check=True)
                logging.info(f"使用停止脚本停止服务: {service_config['stop_script']}")
                return True
            except subprocess.CalledProcessError as e:
        elif service_id == "version_monitor":
            # 特殊处理版本监控服务
            try:
                subprocess.run(["bash", service_config["start_script"], "stop"], check=True)
                return True
            except subprocess.CalledProcessError as e:

        return False

        logging.info(f"重启服务: {SERVICES_CONFIG[service_id]['name']}")

        # 停止服务

        # 等待一段时间
        time.sleep(2)

        # 启动服务
        return self.start_service(service_id)

    def check_and_fix_service(self, service_id):
        service_config = SERVICES_CONFIG[service_id]

        # 检查服务是否正在运行
        is_running, pid = self.is_service_running(service_id)

            logging.warning(f"服务未运行: {service_config['name']}")
            if self.auto_fix:
                # 尝试启动服务
                success = self.start_service(service_id)
                if success:
                    self.service_status[service_id] = {"status": "running", "last_check": datetime.datetime.now().isoformat()}
                else:
                    # 尝试重启服务
                    logging.warning(f"首次启动失败，尝试重启服务: {service_config['name']}")
                    if success:
                        self.service_status[service_id] = {"status": "running", "last_check": datetime.datetime.now().isoformat()}
                    else:
                        self.service_status[service_id] = {"status": "failed", "last_check": datetime.datetime.now().isoformat(), "error": "无法启动服务"}
            else:
                self.service_status[service_id] = {"status": "stopped", "last_check": datetime.datetime.now().isoformat()}
        else:
            try:
                process = psutil.Process(pid)
                status = process.status()

                if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                    logging.warning(f"服务进程异常: {service_config['name']}, 状态: {status}")
                    if self.auto_fix:
                        self.restart_service(service_id)
                        self.service_status[service_id] = {"status": "restarted", "last_check": datetime.datetime.now().isoformat()}
                else:
            except Exception as e:
                logging.error(f"检查服务健康状态失败: {service_config['name']}, {str(e)}")
                self.service_status[service_id] = {"status": "unknown", "last_check": datetime.datetime.now().isoformat(), "error": str(e)}

    def check_all_services(self):
        """检查所有服务"""
        logging.info("开始检查所有服务...")

        # 首先检查系统依赖项
        self.check_system_dependencies()

        # 检查每个服务
        results = {}
        for service_id in SERVICES_CONFIG:
            try:
                results[service_id] = self.check_and_fix_service(service_id)
            except Exception as e:
                logging.error(f"检查服务时发生异常: {service_id}, {str(e)}")

        # 保存状态报告
        self.save_status_report()

        return results
    def save_status_report(self):
        """保存服务状态报告"""
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "services": self.service_status,
            "total_services": len(SERVICES_CONFIG),
        }
        report_file = os.path.join(LOG_DIR, f"status_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            logging.info(f"状态报告已保存: {report_file}")
        except Exception as e:
            logging.error(f"保存状态报告失败: {str(e)}")
    def run_monitor(self):
        """运行监控主循环"""
        logging.info("服务监控启动")
        self.running = True
        try:
            # 首次检查所有服务

            # 定期检查
            while self.running:
                time.sleep(self.check_interval)
                self.check_all_services()
        except KeyboardInterrupt:
            logging.info("监控被用户中断")
        except Exception as e:
        finally:
            self.running = False
            logging.info("服务监控停止")

        """停止监控"""
        logging.info("停止服务监控...")
        self.running = False

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='服务监控与自动修复脚本')
    parser.add_argument('--interval', type=int, default=60, help='检查间隔（秒）')
    parser.add_argument('--auto-fix', action='store_true', default=True, help='自动修复发现的问题')
    parser.add_argument('--check-once', action='store_true', help='只检查一次并退出')
    parser.add_argument('--service', help='指定要检查的服务ID')
    parser.add_argument('--stop', help='停止指定服务')
    parser.add_argument('--restart', help='重启指定服务')
    parser.add_argument('--status', action='store_true', help='显示所有服务状态')

    args = parser.parse_args()
    monitor = ServiceMonitor(check_interval=args.interval, auto_fix=args.auto_fix)

    if args.service:
        # 检查指定服务
        if args.service not in SERVICES_CONFIG:
            print(f"错误: 未知的服务ID: {args.service}")
            print(f"可用的服务: {', '.join(SERVICES_CONFIG.keys())}")
            return
        monitor.check_and_fix_service(args.service)
    elif args.start:
        # 启动指定服务
        if args.start not in SERVICES_CONFIG:
            print(f"错误: 未知的服务ID: {args.start}")
            return
        monitor.start_service(args.start)
    elif args.stop:
        # 停止指定服务
        if args.stop not in SERVICES_CONFIG:
            print(f"错误: 未知的服务ID: {args.stop}")
            return
        monitor.stop_service(args.stop)
    elif args.restart:
        # 重启指定服务
        if args.restart not in SERVICES_CONFIG:
            print(f"错误: 未知的服务ID: {args.restart}")
            return
        monitor.restart_service(args.restart)
    elif args.status:
        # 显示服务状态
        monitor.check_all_services()
        print(str(monitor.service_status, ensure_ascii=False, indent=2))
    elif args.check_once:
        # 只检查一次
        monitor.check_all_services()
        # 运行监控
        monitor.run_monitor()

if __name__ == "__main__":
    main()
