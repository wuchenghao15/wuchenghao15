#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时服务器监控系统
实时监控服务器状态,一旦检测到异常,及时实例化针对性AI进行修复,并上报数据库和日志
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
# JSON import removed - using database
import time
import threading
import uuid
import psutil
import socket
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.utils.logging import logger
from app.utils.db import db_manager
from ai_monitor_server import ai_monitor_server
from ai_employee_manager import AIEmployeeManager

class RealTimeServerMonitor:
    """实时服务器监控系统"""

    def __init__(self):
        self.is_running = False
        self.thread_lock = threading.RLock()
        self.monitor_thread = None
        self.check_interval = 5  # 检查间隔(秒)

        # 服务器状态指标
        self.server_status = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": {},
            "network_stats": {},
            "process_count": 0,
            "thread_count": 0,
            "uptime": 0,
            "load_average": [0.0, 0.0, 0.0],
            "open_files": 0,
            "connections": 0,
            "running_services": [],
            "system_temperature": {}
        }

        # 异常阈值配置
        self.thresholds = {
            "cpu_usage": 80.0,  # CPU使用率阈值(%)
            "memory_usage": 85.0,  # 内存使用率阈值(%)
            "disk_usage": 90.0,  # 磁盘使用率阈值(%)
            "load_average": 5.0,  # 1分钟负载平均值阈值
            "connections": 1000,  # 并发连接数阈值
            "temperature": 80.0  # 系统温度阈值(°C)
        }
        # 异常历史记录
        self.exception_history = []

        # 暂时注释掉AI员工管理器初始化,避免启动问题
        # self.ai_employee_manager = AIEmployeeManager()
        self.ai_employee_manager = None

        logger.info("实时服务器监控系统初始化完成")

    def start(self):
        """启动实时服务器监控"""
        with self.thread_lock:
            if self.is_running:
                logger.warning("实时服务器监控系统已在运行中")
                return False

            self.is_running = True

            # 暂时注释掉AI监控服务器启动,避免启动问题
            # ai_monitor_server.start()

            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

            logger.info("实时服务器监控系统已启动")
            return True

    def stop(self):
        """停止实时服务器监控"""
        with self.thread_lock:
            if not self.is_running:
                return False

            self.is_running = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
                logger.info("监控线程已停止")

            # 停止AI监控服务器
            ai_monitor_server.stop()

            logger.info("实时服务器监控系统已停止")
            return True

    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 收集服务器状态
                server_stats = self._collect_server_stats()

                # 检查异常
                exceptions = self._detect_exceptions(server_stats)

                # 如果有异常,处理异常(暂时简化,不使用AI员工管理器)
                if exceptions:
                    for exception in exceptions:
                        logger.warning(f"检测到异常: {exception['description']}")

                # 更新全局服务器状态
                self.server_status.update(server_stats)

            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}")

            time.sleep(self.check_interval)

    def _collect_server_stats(self):
        """收集服务器状态信息"""
        stats = {}

        # CPU使用率
        stats["cpu_usage"] = psutil.cpu_percent(interval=0.1)

        # 内存使用率
        memory = psutil.virtual_memory()
        stats["memory_usage"] = memory.percent

        # 磁盘使用率
        disk_usage = {}
        for partition in psutil.disk_partitions():
            if partition.mountpoint in ["/", "/boot", "/home"]:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = usage.percent
                except:
                    continue
        stats["disk_usage"] = disk_usage
        # 负载平均值
        stats["load_average"] = list(os.getloadavg())

        # 网络统计
        net_io = psutil.net_io_counters()
        stats["network_stats"] = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout
        }

        stats["process_count"] = len(psutil.pids())
        stats["thread_count"] = sum(p.num_threads() for p in psutil.process_iter(['num_threads']))

        # 系统运行时间
        stats["uptime"] = time.time() - psutil.boot_time()

        # 打开文件数量
        stats["open_files"] = len(psutil.open_files())

        # 网络连接数量
        stats["connections"] = len(psutil.net_connections())

        # 运行中的服务(简化版,只检查关键服务)
        running_services = []
        critical_processes = ["python", "nginx", "mysql", "redis"]
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'] in critical_processes and p.info['name'] not in running_services:
                    running_services.append(p.info['name'])
            except:
                continue
        stats["running_services"] = running_services

        system_temperature = {}
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    for entry in entries:
                        system_temperature[name] = entry.current
        except:
            pass
        stats["system_temperature"] = system_temperature

        return stats

    def _detect_exceptions(self, stats):
        """检测异常"""
        exceptions = []

        if stats["cpu_usage"] > self.thresholds["cpu_usage"]:
            exceptions.append({
                "type": "high_cpu_usage",
                "level": "warning",
                "description": f"CPU使用率过高: {stats['cpu_usage']:.2f}%",
                "value": stats["cpu_usage"],
                "threshold": self.thresholds["cpu_usage"]
            })

        # 检查内存使用率
        if stats["memory_usage"] > self.thresholds["memory_usage"]:
            exceptions.append({
                "type": "high_memory_usage",
                "level": "warning",
                "description": f"内存使用率过高: {stats['memory_usage']:.2f}%",
                "value": stats["memory_usage"],
                "threshold": self.thresholds["memory_usage"]
            })

        # 检查磁盘使用率
        for mountpoint, usage in stats["disk_usage"].items():
            if usage > self.thresholds["disk_usage"]:
                exceptions.append({
                    "type": "high_disk_usage",
                    "description": f"磁盘 {mountpoint} 使用率过高: {usage:.2f}%",
                    "value": usage,
                    "details": {"mountpoint": mountpoint}
                })

        # 检查负载平均值
            exceptions.append({
                "type": "high_load_average",
                "description": f"系统负载过高: {stats['load_average'][0]:.2f}",
                "value": stats["load_average"][0],
                "threshold": self.thresholds["load_average"]
            })

        # 检查网络连接数量
        if stats["connections"] > self.thresholds["connections"]:
            exceptions.append({
                "type": "high_connections_count",
                "value": stats["connections"],
                "threshold": self.thresholds["connections"]
            })

        for sensor, temp in stats["system_temperature"].items():
            if temp > self.thresholds["temperature"]:
                exceptions.append({
                    "type": "high_temperature",
                    "description": f"系统温度过高 ({sensor}): {temp:.2f}°C",
                    "threshold": self.thresholds["temperature"],
                    "details": {"sensor": sensor}
                })
        # 检查关键服务是否运行
        critical_services = ["python"]  # 根据实际情况调整
        for service in critical_services:
            if service not in stats["running_services"]:
                exceptions.append({
                    "type": "service_down",
                    "level": "critical",
                    "details": {"service": service}
                })


    def _handle_exceptions(self, exceptions, server_stats):
        """处理异常"""
        for exception in exceptions:
            try:

                # 生成异常ID
                exception_id = f"exception_{uuid.uuid4().hex[:12]}"
                exception["timestamp"] = datetime.now().isoformat()

                # 记录异常到历史
                self.exception_history.append(exception)

                # 根据异常类型调用相应的AI进行修复
                repair_result = self._repair_exception(exception)

                # 上报到数据库和日志
                self._report_exception(exception, repair_result)

            except Exception as e:
                logger.error(f"处理异常失败: {str(e)}")

    def _repair_exception(self, exception):
        repair_result = {
            "success": False,
            "message": "AI员工管理器未初始化,无法执行修复",
            "action": "none",
            "details": {}
        }
        return repair_result
    def _get_ai_requirements(self, exception_type):
        return None

    def _create_specialized_ai(self, exception):
        """动态创建专门的AI员工进行修复"""
        repair_result = {
            "success": False,
            "message": "AI员工管理器未初始化,无法创建专门AI员工",
            "action": "create_specialized_ai",
            "details": {}
        }
        return repair_result
    def _report_exception(self, exception, repair_result):
        """上报异常和修复结果"""
        try:
            # 只记录到日志,不进行数据库操作
            logger.warning(f"检测到异常: {exception['description']}")
            logger.info(f"异常类型: {exception['type']}, 级别: {exception['level']}")
        except Exception as e:
            logger.error(f"上报异常时出错: {str(e)}")

    def get_status(self):
        """获取监控系统状态"""
        if self.ai_employee_manager:
            ai_employee_count = len(self.ai_employee_manager.get_all_employees())

        # 检查ai_monitor_server是否可用
        ai_monitor_status = {"is_running": False, "message": "AI监控服务器未初始化"}
        try:
            ai_monitor_status = ai_monitor_server.get_status()
        except Exception as e:
            logger.warning(f"获取AI监控状态失败: {str(e)}")

        return {
            "check_interval": self.check_interval,
            "server_status": self.server_status,
            "exception_history": self.exception_history[-20:],  # 返回最近20条异常记录
            "ai_monitor_status": ai_monitor_status,
            "ai_employee_count": ai_employee_count
        }

        if interval > 0:
            logger.info(f"检查间隔已设置为 {interval} 秒")
            return True
        return False
    def update_thresholds(self, thresholds):
        """更新异常阈值"""
        logger.info(f"异常阈值已更新: {thresholds}")


if __name__ == "__main__":
    # 启动实时服务器监控
    real_time_server_monitor.start()

    # 保持运行
    try:
        print("实时服务器监控系统已启动,按Ctrl+C停止...")
        while True:
            # 每分钟打印一次状态
            time.sleep(60)
            status = real_time_server_monitor.get_status()
            print(f"\n=== 服务器监控状态 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
            print(f"CPU使用率: {status['server_status']['cpu_usage']:.2f}%")
            print(f"内存使用率: {status['server_status']['memory_usage']:.2f}%")
            print(f"磁盘使用率: {status['server_status']['disk_usage']}")
            print(f"系统负载: {status['server_status']['load_average']}")
            print(f"网络连接数: {status['server_status']['connections']}")
            print(f"最近异常数: {len(status['exception_history'])}")
    except KeyboardInterrupt:
        real_time_server_monitor.stop()
        print("实时服务器监控系统已停止")
