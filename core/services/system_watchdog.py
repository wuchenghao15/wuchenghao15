#!/usr/bin/env python3
"""
系统守护进程管理器 - System Watchdog
自动监控和管理系统服务，防止意外终止，支持自动重启
"""

import os
import sys
import json
import time
import signal
import subprocess
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_DIR, 'config', 'services_config.json')
PID_DIR = os.path.join(PROJECT_DIR, 'pids')
WATCHDOG_PID_FILE = os.path.join(PID_DIR, 'watchdog.pid')

MAX_RESTART_ATTEMPTS = 5
RESTART_DELAY = 5
CHECK_INTERVAL = 10
MIN_UPTIME_BEFORE_RESTART = 30


class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.processes: Dict[str, psutil.Process] = {}
        self.restart_counts: Dict[str, int] = {}
        self.last_start_time: Dict[str, float] = {}
        self._load_config()
        self._ensure_pid_dir()
        self._running = True

    def _ensure_pid_dir(self):
        os.makedirs(PID_DIR, exist_ok=True)

    def _load_config(self):
        """加载服务配置"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.services = json.load(f)
            logger.info(f"已加载 {len(self.services)} 个服务配置")
        except FileNotFoundError:
            logger.warning(f"配置文件未找到: {CONFIG_FILE}")
            self.services = self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件解析错误: {e}")
            self.services = self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认服务配置"""
        return {
            'flask_app': {
                'name': 'Flask应用',
                'command': ['python3', 'server_real_db.py'],
                'cwd': PROJECT_DIR,
                'env': {},
                'log_file': 'flask_app.log',
                'check_port': 8888,
                'auto_start': True,
                'auto_restart': True
            },
            'ai_agent_service': {
                'name': 'AI Agent服务',
                'command': ['python3', '-m', 'ai_engines.ai_service'],
                'cwd': PROJECT_DIR,
                'env': {},
                'log_file': 'ai_agent_service.log',
                'check_port': None,
                'auto_start': True,
                'auto_restart': True
            },
            'auto_scheduler': {
                'name': '自动调度器',
                'command': ['python3', '-m', 'ai_engines.auto_scheduler'],
                'cwd': PROJECT_DIR,
                'env': {},
                'log_file': 'auto_scheduler.log',
                'check_port': None,
                'auto_start': True,
                'auto_restart': True
            }
        }

    def _get_pid_file(self, service_name: str) -> str:
        return os.path.join(PID_DIR, f"{service_name}.pid")

    def _save_pid(self, service_name: str, pid: int):
        with open(self._get_pid_file(service_name), 'w') as f:
            f.write(str(pid))

    def _load_pid(self, service_name: str) -> Optional[int]:
        pid_file = self._get_pid_file(service_name)
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return None
        return None

    def _remove_pid(self, service_name: str):
        pid_file = self._get_pid_file(service_name)
        if os.path.exists(pid_file):
            os.remove(pid_file)

    def is_process_running(self, pid: int) -> bool:
        """检查进程是否运行"""
        try:
            return psutil.pid_exists(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return False

    def start_service(self, service_name: str) -> bool:
        """启动服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False

        config = self.services[service_name]
        
        if not config.get('auto_start', True):
            logger.info(f"服务 {service_name} 已禁用自动启动")
            return False

        existing_pid = self._load_pid(service_name)
        if existing_pid and self.is_process_running(existing_pid):
            logger.info(f"服务 {service_name} 已在运行 (PID: {existing_pid})")
            self.processes[service_name] = psutil.Process(existing_pid)
            return True

        logger.info(f"启动服务: {config['name']}")
        
        try:
            env = os.environ.copy()
            env.update(config.get('env', {}))
            
            log_path = os.path.join(PROJECT_DIR, config.get('log_file', f"{service_name}.log"))
            log_file = open(log_path, 'a')
            
            process = subprocess.Popen(
                config['command'],
                cwd=config.get('cwd', PROJECT_DIR),
                env=env,
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid
            )
            
            self.processes[service_name] = process
            self._save_pid(service_name, process.pid)
            self.last_start_time[service_name] = time.time()
            self.restart_counts[service_name] = 0
            
            logger.info(f"服务 {service_name} 启动成功 (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"启动服务 {service_name} 失败: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False

        existing_pid = self._load_pid(service_name)
        if existing_pid and self.is_process_running(existing_pid):
            try:
                os.killpg(os.getpgid(existing_pid), signal.SIGTERM)
                time.sleep(2)
                
                if self.is_process_running(existing_pid):
                    os.killpg(os.getpgid(existing_pid), signal.SIGKILL)
                    time.sleep(1)
                
                logger.info(f"服务 {service_name} 已停止")
            except Exception as e:
                logger.error(f"停止服务 {service_name} 失败: {e}")
        
        self._remove_pid(service_name)
        if service_name in self.processes:
            del self.processes[service_name]
        
        return True

    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        logger.info(f"重启服务: {service_name}")
        self.stop_service(service_name)
        time.sleep(2)
        return self.start_service(service_name)

    def check_service(self, service_name: str) -> bool:
        """检查服务状态"""
        config = self.services[service_name]
        pid = self._load_pid(service_name)
        
        if not pid:
            logger.warning(f"服务 {service_name} 没有PID文件")
            return False

        if not self.is_process_running(pid):
            logger.warning(f"服务 {service_name} 进程已停止 (PID: {pid})")
            return False

        check_port = config.get('check_port')
        if check_port:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', check_port))
                sock.close()
                
                if result != 0:
                    logger.warning(f"服务 {service_name} 端口 {check_port} 未响应")
                    return False
            except Exception as e:
                logger.error(f"检查端口 {check_port} 失败: {e}")
        
        return True

    def monitor_services(self):
        """监控所有服务"""
        logger.info("开始监控服务...")
        
        for service_name in self.services:
            if self.services[service_name].get('auto_start', True):
                self.start_service(service_name)
        
        while self._running:
            try:
                for service_name, config in self.services.items():
                    if not config.get('auto_restart', True):
                        continue
                    
                    is_running = self.check_service(service_name)
                    
                    if not is_running:
                        restart_count = self.restart_counts.get(service_name, 0)
                        
                        if restart_count >= MAX_RESTART_ATTEMPTS:
                            logger.error(f"服务 {service_name} 重启次数已达上限 ({MAX_RESTART_ATTEMPTS})，停止重启")
                            continue
                        
                        uptime = time.time() - self.last_start_time.get(service_name, 0)
                        if uptime < MIN_UPTIME_BEFORE_RESTART and restart_count > 0:
                            logger.warning(f"服务 {service_name} 启动后很快停止，等待 {RESTART_DELAY} 秒后重试")
                            time.sleep(RESTART_DELAY)
                        
                        logger.info(f"尝试重启服务 {service_name} (第 {restart_count + 1} 次)")
                        success = self.restart_service(service_name)
                        
                        if success:
                            self.restart_counts[service_name] = restart_count + 1
                            logger.info(f"服务 {service_name} 重启成功")
                        else:
                            logger.error(f"服务 {service_name} 重启失败")
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(CHECK_INTERVAL)

    def start_all(self):
        """启动所有服务"""
        logger.info("启动所有服务...")
        for service_name in self.services:
            self.start_service(service_name)

    def stop_all(self):
        """停止所有服务"""
        logger.info("停止所有服务...")
        for service_name in self.services:
            self.stop_service(service_name)

    def get_status(self) -> Dict:
        """获取所有服务状态"""
        status = {}
        for service_name, config in self.services.items():
            pid = self._load_pid(service_name)
            is_running = self.is_process_running(pid) if pid else False
            
            status[service_name] = {
                'name': config['name'],
                'pid': pid,
                'running': is_running,
                'restart_count': self.restart_counts.get(service_name, 0),
                'auto_restart': config.get('auto_restart', True),
                'log_file': config.get('log_file')
            }
        
        return status

    def shutdown(self):
        """关闭守护进程"""
        logger.info("正在关闭系统守护进程...")
        self._running = False
        self.stop_all()
        self._remove_pid('watchdog')


def is_watchdog_running() -> bool:
    """检查守护进程是否已运行"""
    if os.path.exists(WATCHDOG_PID_FILE):
        try:
            with open(WATCHDOG_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            return psutil.pid_exists(pid)
        except (ValueError, IOError):
            return False
    return False


def save_watchdog_pid():
    """保存守护进程PID"""
    os.makedirs(PID_DIR, exist_ok=True)
    with open(WATCHDOG_PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def remove_watchdog_pid():
    """删除守护进程PID文件"""
    if os.path.exists(WATCHDOG_PID_FILE):
        os.remove(WATCHDOG_PID_FILE)


def signal_handler(signum, frame):
    """信号处理"""
    logger.info(f"收到信号 {signum}，正在退出...")
    global watchdog
    if watchdog:
        watchdog.shutdown()
    remove_watchdog_pid()
    sys.exit(0)


def main():
    global watchdog
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        watchdog = ServiceManager()
        
        if command == 'start':
            if is_watchdog_running():
                logger.error("系统守护进程已在运行")
                sys.exit(1)
            
            save_watchdog_pid()
            logger.info("启动系统守护进程...")
            watchdog.start_all()
            watchdog.monitor_services()
        
        elif command == 'stop':
            watchdog.stop_all()
            remove_watchdog_pid()
            logger.info("系统守护进程已停止")
        
        elif command == 'restart':
            watchdog.stop_all()
            time.sleep(2)
            watchdog.start_all()
            logger.info("所有服务已重启")
        
        elif command == 'status':
            status = watchdog.get_status()
            print("=" * 50)
            print("MTSCOS AI System - 服务状态")
            print("=" * 50)
            for service_name, info in status.items():
                status_icon = "✓" if info['running'] else "✗"
                print(f"  {status_icon} {info['name']}")
                print(f"     PID: {info['pid'] or '未运行'}")
                print(f"     重启次数: {info['restart_count']}")
                print(f"     自动重启: {'开启' if info['auto_restart'] else '关闭'}")
                print(f"     日志文件: {info['log_file']}")
                print()
            print("=" * 50)
        
        elif command == 'start-service':
            if len(sys.argv) > 2:
                service_name = sys.argv[2]
                watchdog.start_service(service_name)
            else:
                print("用法: python3 system_watchdog.py start-service <服务名>")
        
        elif command == 'stop-service':
            if len(sys.argv) > 2:
                service_name = sys.argv[2]
                watchdog.stop_service(service_name)
            else:
                print("用法: python3 system_watchdog.py stop-service <服务名>")
        
        elif command == 'restart-service':
            if len(sys.argv) > 2:
                service_name = sys.argv[2]
                watchdog.restart_service(service_name)
            else:
                print("用法: python3 system_watchdog.py restart-service <服务名>")
        
        else:
            print("未知命令")
            print("可用命令: start, stop, restart, status, start-service, stop-service, restart-service")
    
    else:
        print("系统守护进程管理器")
        print("用法: python3 system_watchdog.py <命令>")
        print()
        print("命令列表:")
        print("  start              - 启动守护进程和所有服务")
        print("  stop               - 停止守护进程和所有服务")
        print("  restart            - 重启所有服务")
        print("  status             - 查看服务状态")
        print("  start-service <name>   - 启动指定服务")
        print("  stop-service <name>    - 停止指定服务")
        print("  restart-service <name> - 重启指定服务")


if __name__ == '__main__':
    watchdog = None
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    
    main()
