#!/usr/bin/env python3
"""
AI子母服务器管理器
负责管理AI母服务器和子服务器的通信, 任务分配和资源调度
"""
import logging
import time
import threading
from datetime import datetime
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ai_master_slave_manager')

class AIServerNode:
    """AI服务器节点基类"""

    def __init__(self, node_id, node_type, host, port):
        """初始化AI服务器节点

        Args:
            node_id: 节点ID
            node_type: 节点类型(master/slave)
            host: 节点主机地址
            port: 节点端口
        """
        self.node_id = node_id
        self.node_type = node_type
        self.host = host
        self.port = port
        self.status = "online"
        self.created_at = datetime.now()
        self.last_updated_at = datetime.now()
        self.performance_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "tasks_processed": 0,
            "response_time": 0.0,
            "error_rate": 0.0
        }
        self.ai_employees = []
        self.ai_collections = []

        self.logger = logging.getLogger(f"ai_server_{node_id}")
        self.logger.info(f"AI服务器节点 {node_id} 已初始化,类型: {node_type}")

    def get_status(self):
        """获取节点状态"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "performance_metrics": self.performance_metrics,
            "ai_employees_count": len(self.ai_employees),
            "ai_collections_count": len(self.ai_collections)
        }

    def update_performance(self, metrics):
        """更新性能指标

        Args:
            metrics: 性能指标数据
        """
        self.performance_metrics.update(metrics)
        self.last_updated_at = datetime.now()

    def update_status(self, status):
        """更新节点状态

        Args:
            status: 新的状态
        """
        self.status = status
        self.logger.info(f"节点状态已更新: {status}")


class AIMasterServer(AIServerNode):
    """AI母服务器: 负责管理子服务器和AI员工"""

    def __init__(self, host, port):
        """初始化AI母服务器

        Args:
            host: 母服务器主机地址
            port: 母服务器端口
        """
        super().__init__("master_001", "master", host, port)
        self.slave_servers = {}
        self.task_queue = []
        self.task_counter = 0

        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        self.scheduling_thread = threading.Thread(target=self._scheduling_loop)
        self.scheduling_thread.daemon = True
        self.scheduling_thread.start()

        self.logger.info("AI母服务器初始化完成")

    def _monitoring_loop(self):
        """监控循环: 定期检查子服务器状态"""
        while True:
            time.sleep(10)
            self._monitor_slave_servers()

    def _scheduling_loop(self):
        """调度循环: 定期分配任务"""
        while True:
            time.sleep(5)
            self._schedule_tasks()

    def _monitor_slave_servers(self):
        """监控子服务器状态"""
        self.logger.info("执行子服务器监控...")

        for slave_id, slave_server in self.slave_servers.items():
            try:
                response = requests.get(f"http://{slave_server.host}:{slave_server.port}/api/health", timeout=5)
                if response.status_code == 200:
                    slave_server.update_status("online")
                    metrics = response.json().get("performance_metrics", {})
                    slave_server.update_performance(metrics)
                else:
                    slave_server.update_status("degraded")
            except Exception as e:
                self.logger.error(f"子服务器 {slave_id} 健康检查失败: {str(e)}")
                slave_server.update_status("offline")

    def _schedule_tasks(self):
        """分配任务给子服务器"""
        if not self.task_queue:
            return

        self.logger.info(f"开始分配任务, 队列中有 {len(self.task_queue)} 个任务")

        online_slaves = [slave for slave in self.slave_servers.values() if slave.status == "online"]
        if not online_slaves:
            self.logger.warning("没有可用的子服务器")
            return

        best_slave = min(online_slaves, key=lambda x: x.performance_metrics["cpu_usage"])
        task = self.task_queue.pop(0)

        try:
            response = requests.post(
                f"http://{best_slave.host}:{best_slave.port}/api/execute_task",
                json=task,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info(f"任务 {task['task_id']} 已分配给子服务器 {best_slave.node_id}")
            else:
                self.task_queue.insert(0, task)
        except Exception as e:
            self.logger.error(f"发送任务失败: {str(e)}")
            self.task_queue.insert(0, task)

    def register_slave_server(self, slave_info):
        """注册子服务器

        Args:
            slave_info: 子服务器信息

        Returns:
            注册结果
        """
        slave_id = slave_info.get("node_id")
        if not slave_id:
            slave_id = f"slave_{int(time.time() * 1000)}"

        slave_server = AIServerNode(
            slave_id,
            "slave",
            slave_info.get("host"),
            slave_info.get("port")
        )

        self.slave_servers[slave_id] = slave_server
        self.logger.info(f"子服务器 {slave_id} 已注册")

        return {
            "success": True,
            "message": "子服务器注册成功",
            "slave_id": slave_id
        }

    def unregister_slave_server(self, slave_id):
        """注销子服务器

        Args:
            slave_id: 子服务器ID

        Returns:
            注销结果
        """
        if slave_id in self.slave_servers:
            del self.slave_servers[slave_id]
            self.logger.info(f"子服务器 {slave_id} 已注销")
            return {"success": True, "message": "子服务器已注销"}
        else:
            self.logger.error(f"未找到子服务器: {slave_id}")
            return {"success": False, "message": "未找到子服务器"}

    def list_slave_servers(self):
        """列出所有子服务器

        Returns:
            子服务器列表
        """
        return [slave.get_status() for slave in self.slave_servers.values()]

    def submit_task(self, task_data):
        """提交任务到任务队列

        Args:
            task_data: 任务数据

        Returns:
            提交结果
        """
        task_id = f"task_{self.task_counter:06d}"
        self.task_counter += 1

        task = {
            "task_id": task_id,
            "task_data": task_data,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        self.task_queue.append(task)
        self.logger.info(f"任务 {task_id} 已提交到队列")

        return {
            "success": True,
            "task_id": task_id,
            "message": "任务已提交"
        }

    def get_system_status(self):
        """获取系统状态

        Returns:
            系统状态信息
        """
        return {
            "master_status": self.get_status(),
            "slave_count": len(self.slave_servers),
            "online_slaves": len([s for s in self.slave_servers.values() if s.status == "online"]),
            "task_queue_size": len(self.task_queue)
        }


class AISlaveServer(AIServerNode):
    """AI子服务器: 负责执行母服务器分配的任务"""

    def __init__(self, host, port, master_host, master_port):
        """初始化AI子服务器

        Args:
            host: 子服务器主机地址
            port: 子服务器端口
            master_host: 母服务器主机地址
            master_port: 母服务器端口
        """
        super().__init__(f"slave_{int(time.time() * 1000)}", "slave", host, port)
        self.master_host = master_host
        self.master_port = master_port
        self.registered_with_master = False

        self.registration_thread = threading.Thread(target=self._registration_loop)
        self.registration_thread.start()

        self.logger.info("AI子服务器初始化完成")

    def _registration_loop(self):
        """注册和心跳循环"""
        while True:
            if not self.registered_with_master:
                self._register_with_master()
            else:
                self._send_heartbeat()
            time.sleep(30)

    def _register_with_master(self):
        """注册到母服务器"""
        try:
            response = requests.post(
                f"http://{self.master_host}:{self.master_port}/api/register_slave",
                json={
                    "host": self.host,
                    "port": self.port,
                    "node_id": self.node_id
                },
                timeout=5
            )

            if response.status_code == 200:
                self.registered_with_master = True
                self.logger.info("成功注册到母服务器")
            else:
                self.logger.error(f"注册失败: {response.text}")
        except Exception as e:
            self.logger.error(f"注册到母服务器失败: {str(e)}")

    def _send_heartbeat(self):
        """发送心跳"""
        try:
            response = requests.post(
                f"http://{self.master_host}:{self.master_port}/api/heartbeat",
                json={
                    "node_id": self.node_id,
                    "status": self.status,
                    "performance_metrics": self.performance_metrics
                },
                timeout=5
            )

            if response.status_code != 200:
                self.logger.error(f"发送心跳失败: {response.text}")
        except Exception as e:
            self.logger.error(f"发送心跳失败: {str(e)}")
            self.registered_with_master = False

    def execute_task(self, task_data):
        """执行任务

        Args:
            task_data: 任务数据

        Returns:
            任务执行结果
        """
        self.logger.info(f"执行任务: {task_data.get('type')}")

        task_content = task_data.get("content", {})

        try:
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            manager = get_ai_employee_manager()
            result = manager.execute_task_by_role("ai_service", task_content)
            return result
        except Exception as e:
            self.logger.error(f"执行任务失败: {str(e)}")
            return {"success": False, "message": str(e)}


class AIServerClusterManager:
    """AI服务器集群管理器"""

    def __init__(self):
        self.master_server = None
        self.slave_servers = []
        self.logger = logging.getLogger('ai_server_cluster_manager')
        self.logger.info("AI服务器集群管理器初始化完成")

    def create_master_server(self, host="0.0.0.0", port=8888):
        """创建母服务器

        Args:
            host: 母服务器主机地址
            port: 母服务器端口

        Returns:
            母服务器实例
        """
        if self.master_server:
            return self.master_server

        self.master_server = AIMasterServer(host, port)
        self.logger.info(f"母服务器已创建,地址: http://{host}:{port}")
        return self.master_server

    def create_slave_server(self, host="0.0.0.0", port=8889, master_host="localhost", master_port=8888):
        """创建子服务器

        Args:
            host: 子服务器主机地址
            port: 子服务器端口
            master_host: 母服务器主机地址
            master_port: 母服务器端口

        Returns:
            子服务器实例
        """
        slave_server = AISlaveServer(host, port, master_host, master_port)
        self.slave_servers.append(slave_server)
        self.logger.info(f"子服务器已创建,地址: http://{host}:{port}")
        return slave_server

    def get_cluster_status(self):
        """获取集群状态

        Returns:
            集群状态信息
        """
        return {
            "master_server": self.master_server.get_status() if self.master_server else None,
            "slave_servers": [slave.get_status() for slave in self.slave_servers],
            "online_servers": sum(1 for slave in self.slave_servers if slave.status == "online") +
                              (1 if self.master_server and self.master_server.status == "online" else 0)
        }


global_cluster_manager = None


def get_cluster_manager():
    """获取全局AI服务器集群管理器实例

    Returns:
        全局AI服务器集群管理器实例
    """
    global global_cluster_manager
    if global_cluster_manager is None:
        global_cluster_manager = AIServerClusterManager()
    return global_cluster_manager
