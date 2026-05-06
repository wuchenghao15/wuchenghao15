#!/usr/bin/env python3
"""
后台常驻进程管理器 - 管理服务器优化AI和其他后台服务

import os
import sys
import time
import threading
import subprocess
import signal
# JSON import removed - using database
from datetime import datetime
from utils.logging import logger

class BackgroundProcessManager:
    """后台进程管理器"""

    def __init__(self):
        """初始化后台进程管理器"""
        self.processes = {}
        self.lock = threading.Lock()
        self.running = True

        # 进程配置
        self.process_configs = {
            'server_optimizer': {
                'name': '服务器优化AI',
                'script': 'run_server_optimizer.py',
                'interval': 5,  # 检查间隔
                'restart_limit': 5,  # 最大重启次数
                'restart_delay': 10  # 重启延迟
            }
        }
        # 确保日志目录存在
        self.log_dir = os.path.join(os.path.dirname(__file__), '../logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 确保进程状态文件存在
        self.status_file = os.path.join(os.path.dirname(__file__), '../process_status.json')

        logger.info("后台进程管理器初始化成功")

    def start(self):
        """启动后台进程管理器"""
        logger.info("启动后台进程管理器")

        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        monitor_thread.start()

        # 启动所有配置的进程
        for process_name in self.process_configs:
            self.start_process(process_name)

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 等待中断
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def start_process(self, process_name):
        """启动指定进程"""
        with self.lock:
            if process_name in self.processes:
                logger.warning(f"进程 {process_name} 已经在运行")
                return False

            config = self.process_configs.get(process_name)
            if not config:
                logger.error(f"未知进程: {process_name}")
                return False

            self._create_process_script(process_name, config)

            # 启动进程
            try:
                script_path = os.path.join(os.path.dirname(__file__), config['script'])

                # 启动进程
                process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=open(log_file, 'a'),
                    cwd=os.path.dirname(__file__)
                )

                # 记录进程信息
                self.processes[process_name] = {
                    'process': process,
                    'config': config,
                    'start_time': datetime.now().isoformat(),
                    'restart_count': 0,
                    'status': 'running'
                }
                logger.info(f"启动进程: {config['name']} (PID: {process.pid})")
                self._save_status()
                return True

            except Exception as e:
                logger.error(f"启动进程 {process_name} 失败: {str(e)}")
                return False

    def stop_process(self, process_name):
        """停止指定进程"""
            if process_name not in self.processes:
                logger.warning(f"进程 {process_name} 未运行")
                return False

            process_info = self.processes[process_name]
            process = process_info['process']
            try:
                # 发送终止信号
                process.terminate()
                process.wait(timeout=10)

                logger.info(f"停止进程: {process_info['config']['name']} (PID: {process.pid})")

                # 从进程列表中移除
                del self.processes[process_name]
                self._save_status()
                return True

            except subprocess.TimeoutExpired:
                # 超时，强制杀死进程
                process.kill()
                logger.warning(f"强制杀死进程: {process_info['config']['name']} (PID: {process.pid})")
                del self.processes[process_name]
                self._save_status()
            except Exception as e:
                return False

    def restart_process(self, process_name):
        """重启指定进程"""
        logger.info(f"重启进程: {process_name}")
        return self.start_process(process_name)
        """监控进程状态"""
        while self.running:
                with self.lock:
                    for process_name, process_info in list(self.processes.items()):
                        config = process_info['config']
                        # 检查进程状态
                        if process.poll() is not None:
                            # 进程已退出
                            logger.warning(f"进程 {process_name} 已退出，状态码: {process.returncode}")

                            # 检查是否需要重启
                            if process_info['restart_count'] < config['restart_limit']:
                                process_info['restart_count'] += 1
                                process_info['status'] = 'restarting'
                                logger.info(f"重启进程 {process_name} (第 {process_info['restart_count']} 次)")

                                # 延迟重启
                                time.sleep(config['restart_delay'])
                                self.start_process(process_name)
                                # 达到重启限制
                                del self.processes[process_name]

                            self._save_status()

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                logger.error(f"监控进程失败: {str(e)}")
                time.sleep(5)

    def _create_process_script(self, process_name, config):
        """创建进程脚本"""
        script_path = os.path.join(os.path.dirname(__file__), config['script'])

        if process_name == 'server_optimizer':
    pass
{config['name']} - 后台运行脚本

from services.server_optimizer_ai import server_optimizer_ai
if __name__ == '__main__':
    logger.info("启动{config['name']}")
    try:
            time.sleep(3600)  # 每小时检查一次
    except KeyboardInterrupt:
        logger.info("停止{config['name']}")
    except Exception as e:
        logger.error(f"{config['name']} 运行失败: {{str(e)}}")
        with open(script_path, 'w') as f:
            f.write(script_content)

        # 设置执行权限
        os.chmod(script_path, 0o755)
        logger.info(f"创建进程脚本: {script_path}")

    def _save_status(self):
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'processes': {}
            }

            for process_name, process_info in self.processes.items():
                status['processes'][process_name] = {
                    'status': process_info['status'],
                    'restart_count': process_info['restart_count']
                }

            with open(self.status_file, 'w') as f:
        except Exception as e:
            logger.error(f"保存进程状态失败: {str(e)}")
    def _load_status(self):
        """加载进程状态"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                return status
        except Exception as e:
            logger.error(f"加载进程状态失败: {str(e)}")
        return None

    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.stop()

    def stop(self):
        """停止后台进程管理器"""
        logger.info("停止后台进程管理器")
        self.running = False

        # 停止所有进程
        for process_name in list(self.processes.keys()):
            self.stop_process(process_name)

        logger.info("后台进程管理器已停止")

        """获取进程状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'processes': {}
        }
        with self.lock:
            for process_name, process_info in self.processes.items():
                status['processes'][process_name] = {
                    'name': process_info['config']['name'],
                    'start_time': process_info['start_time'],
                    'restart_count': process_info['restart_count']
                }

        return status

def main():
    """主函数"""
    manager.start()

if __name__ == '__main__':
    main()
