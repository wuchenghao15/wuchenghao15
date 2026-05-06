#!/usr/bin/env python3
"""
系统启动脚本 - 启动所有服务并监控状态

import os
import time
import subprocess
from utils.logging import logger
from services.system_ai import system_ai

class SystemStarter:
    """系统启动器"""

    def __init__(self):
        """初始化系统启动器"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.services = {
            'web_server': {
                'command': 'python3 app.py',
                'port': 8888,
                'status': False
            }
        }
    def start_all_services(self):
        """启动所有服务"""
        logger.info("开始启动所有服务")

        # 清理之前的进程
        self._cleanup_processes()

        # 启动Web服务器
        self._start_web_server()

        # 启动系统AI服务
        self._start_system_ai()

        # 监控服务状态
        self._monitor_startup()

    def _cleanup_processes(self):
        """清理之前的进程"""
        logger.info("清理之前的进程")

        # 清理占用8888端口的进程
        try:
            subprocess.run(
                ['lsof', '-i', ':8888', '|', 'grep', 'LISTEN', '|', 'awk', '{print $2}', '|', 'xargs', 'kill', '-9'],
                shell=True
            )
            logger.info("清理端口8888成功")
        except Exception as e:
            logger.error(f"清理进程失败: {str(e)}")

    def _start_web_server(self):
        """启动Web服务器"""
        logger.info("启动Web服务器")

        try:
            # 在后台启动Web服务器
                ['nohup', 'python3', 'app.py', '>', 'server.log', '2>&1', '&'],
                cwd=self.base_dir
            logger.info("Web服务器启动命令已执行")
        except Exception as e:
            logger.error(f"启动Web服务器失败: {str(e)}")
    def _start_system_ai(self):
        """启动系统AI服务"""
        # 系统AI服务会在导入时自动启动
        logger.info("系统AI服务已启动")

    def _monitor_startup(self):
        """监控启动过程"""
        logger.info("监控服务启动状态")

        start_time = time.time()
        timeout = 30  # 30秒超时

        while time.time() - start_time < timeout:
            # 检查Web服务器状态
            web_server_status = self._check_web_server()

            if web_server_status:
                logger.info("Web服务器启动成功")
                self.services['web_server']['status'] = True
                break

            logger.info("等待Web服务器启动...")
            time.sleep(2)

        if not web_server_status:
            logger.error("Web服务器启动超时")
            # 尝试修复
            system_ai.restart_all_services()

        # 报告启动结果
        self._report_startup_result()

    def _check_web_server(self):
        """检查Web服务器状态

        Returns:
            bool: Web服务器是否运行
        try:
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:8888/'],
                timeout=5
            )
            return result.returncode == 0 and result.stdout.decode().strip() in ['200', '302']
        except:
            return False

    def _report_startup_result(self):
        logger.info("=== 系统启动报告 ===")

        for service_name, service_info in self.services.items():
            status = "运行中" if service_info['status'] else "未运行"
            logger.info(f"{service_name}: {status}")

        # 报告系统AI状态
        ai_status = system_ai.get_service_status()
        logger.info("系统AI服务状态:")
        for service, status in ai_status.items():
            logger.info(f"  {service}: {'运行中' if status else '未运行'}")

        logger.info("=== 启动完成 ===")

    def get_status(self):
        """获取系统状态

        Returns:
            dict: 系统状态
        status = {
            'services': self.services,
            'system_ai': system_ai.get_service_status(),
            'problems': system_ai.get_problems(),
            'solutions': system_ai.get_solutions(),
            'learning_data': system_ai.get_learning_data()
        }

    starter = SystemStarter()
    starter.start_all_services()

    # 显示最终状态
    status = starter.get_status()
    logger.info(f"最终系统状态: {status}")
