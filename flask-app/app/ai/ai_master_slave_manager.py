#!/usr/bin/env python3
"""
AI子母服务器管理器
负责管理AI母服务器和子服务器的通信、任务分配和资源调度

import logging
import time
# JSON import removed - using database
import threading
from datetime import datetime
import requests

# 配置日志
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
            node_type: 节点类型（master/slave）
            host: 节点主机地址
            port: 节点端口
        self.node_id = node_id
        self.node_type = node_type
        self.host = host
        self.port = port
        self.status = "online"  # online, offline, upgrading, maintenance
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
        self.logger.info(f"✓ AI服务器节点 {node_id} 已初始化，类型: {node_type}")

    def get_status(self):
        """获取节点状态"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_updated_at": self.last_updated_at.isoformat(),
            "performance_metrics": self.performance_metrics,
            "ai_employees_count": len(self.ai_employees),
            "ai_collections_count": len(self.ai_collections)
        }

    def update_performance(self, metrics):
        """更新性能指标

        Args:
            metrics: 性能指标数据
        self.last_updated_at = datetime.now()

    def update_status(self, status):
        """更新节点状态
        Args:
            status: 新的状态
        self.status = status
        self.logger.info(f"节点状态已更新: {status}")

class AIMasterServer(AIServerNode):
    """AI母服务器，负责管理子服务器和AI员工"""

        """初始化AI母服务器

        Args:
            host: 母服务器主机地址
            port: 母服务器端口
        super().__init__("master_001", "master", host, port)
        self.task_queue = []
        self.task_counter = 0

        # 启动监控和调度线程
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        self.scheduling_thread = threading.Thread(target=self._scheduling_loop)
        self.scheduling_thread.daemon = True
        self.scheduling_thread.start()

        self.logger.info("✓ AI母服务器初始化完成")

    def _monitoring_loop(self):
        """监控循环，定期检查子服务器状态"""
        while True:
            time.sleep(10)
            self._monitor_slave_servers()

    def _scheduling_loop(self):
        """调度循环，定期分配任务"""
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
                    # 更新性能指标
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

        self.logger.info(f"开始分配任务，队列中有 {len(self.task_queue)} 个任务")

        # 按负载选择最佳子服务器
        online_slaves = [slave for slave in self.slave_servers.values() if slave.status == "online"]
        if not online_slaves:
            self.logger.warning("没有可用的子服务器")
            return

        # 简单的负载均衡策略：选择CPU使用率最低的子服务器
        best_slave = min(online_slaves, key=lambda x: x.performance_metrics["cpu_usage"])

        # 取出一个任务
        task = self.task_queue.pop(0)

        try:
            # 发送任务给子服务器
            response = requests.post(
                json=task,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info(f"任务 {task['task_id']} 已分配给子服务器 {best_slave.node_id}")
            else:
                self.task_queue.insert(0, task)
        except Exception as e:
            self.logger.error(f"发送任务失败: {str(e)}")
            # 将任务重新放回队列
            self.task_queue.insert(0, task)

    def register_slave_server(self, slave_info):
        """注册子服务器
        Args:
            slave_info: 子服务器信息
        Returns:
            注册结果
        slave_id = slave_info.get("node_id")
            # 生成唯一ID

        # 创建子服务器实例
        slave_server = AIServerNode(
            "slave",
            slave_info.get("port")
        )

        # 添加到子服务器列表
        self.slave_servers[slave_id] = slave_server
        self.logger.info(f"✓ 子服务器 {slave_id} 已注册")

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
            del self.slave_servers[slave_id]
            self.logger.info(f"✓ 子服务器 {slave_id} 已注销")
        else:
            self.logger.error(f"未找到子服务器: {slave_id}")
            return {"success": False, "message": "未找到子服务器"}

    def list_slave_servers(self):
        """列出所有子服务器

        Returns:
            子服务器列表
        return [slave.get_status() for slave in self.slave_servers.values()]

    def submit_task(self, task_data):
        """提交任务到任务队列

        Args:
            task_data: 任务数据

        Returns:
            提交结果
        # 生成任务ID
        task_id = f"task_{self.task_counter:06d}"

        # 创建任务对象
            "task_id": task_id,
            "task_data": task_data,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        # 添加到任务队列
        self.task_queue.append(task)
        self.logger.info(f"✓ 任务 {task_id} 已提交到队列")

        return {
            "success": True,
            "message": "任务提交成功",
            "task_id": task_id
        }

    def get_system_status(self):
        """获取系统状态

        Returns:
            系统状态信息
        return {
            "master_server": self.get_status(),
            "slave_servers": self.list_slave_servers(),
            "task_queue_size": len(self.task_queue),
            "total_slave_servers": len(self.slave_servers),
            "online_slave_servers": sum(1 for slave in self.slave_servers.values() if slave.status == "online")
        }

    """AI子服务器，负责执行具体的AI任务"""

    def __init__(self, host, port, master_host, master_port):
        """初始化AI子服务器

        Args:
            host: 子服务器主机地址
            port: 子服务器端口
            master_host: 母服务器主机地址
            master_port: 母服务器端口
        super().__init__(f"slave_{int(time.time() * 1000)}", "slave", host, port)
        self.registered_with_master = False

        # 启动注册和心跳线程
        self.registration_thread = threading.Thread(target=self._registration_loop)
        self.registration_thread.start()

        self.logger.info("✓ AI子服务器初始化完成")

    def _registration_loop(self):
        """注册和心跳循环"""
        while True:
            if not self.registered_with_master:
                self._register_with_master()
            else:
                self._send_heartbeat()
            # 每30秒执行一次
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
                self.logger.info(f"✓ 成功注册到母服务器")
            else:
        except Exception as e:
            self.logger.error(f"注册到母服务器失败: {str(e)}")

    def _send_heartbeat(self):
        try:
            response = requests.post(
                json={
                    "node_id": self.node_id,
                    "status": self.status,
                    "performance_metrics": self.performance_metrics
                timeout=5

                self.logger.error(f"发送心跳失败: {response.text}")
        except Exception as e:
            self.logger.error(f"发送心跳失败: {str(e)}")
            self.registered_with_master = False

    def execute_task(self, task_data):

            task_data: 任务数据

            任务执行结果
        self.logger.info(f"执行任务: {task_data.get('type')}")

        # 从task_data中提取具体的任务信息
        task_content = task_data.get("content", {})

            # 调用AI服务生成文本
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            return result
            # 执行数据库查询
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            ai_manager = get_ai_employee_manager()
            result = ai_manager.execute_task_by_role("database_service", task_content)
            return result
        elif task_type == "file_operation":
            # 执行文件操作
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            result = ai_manager.execute_task_by_role("filesystem_service", task_content)
            return result
        else:
            return {"success": False, "message": f"未知的任务类型: {task_type}"}

class AIServerClusterManager:

        """初始化AI服务器集群管理器"""
        self.master_server = None
        self.slave_servers = []
        self.logger.info("✓ AI服务器集群管理器已初始化")
    def create_master_server(self, host="0.0.0.0", port=8888):
        """创建母服务器

        Args:
            port: 母服务器端口

        Returns:
            母服务器实例
        if self.master_server:
            return self.master_server

        self.master_server = AIMasterServer(host, port)
        self.logger.info(f"✓ 母服务器已创建，地址: http://{host}:{port}")
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
        self.slave_servers.append(slave_server)
        self.logger.info(f"✓ 子服务器已创建，地址: http://{host}:{port}")
        return slave_server

    def get_cluster_status(self):
        """获取集群状态

        Returns:
            "master_server": self.master_server.get_status() if self.master_server else None,
            "online_servers": sum(1 for slave in self.slave_servers if slave.status == "online") + \
                             (1 if self.master_server and self.master_server.status == "online" else 0)

# 全局AI服务器集群管理器实例

def get_cluster_manager():
    """获取全局AI服务器集群管理器实例
    Returns:
        全局AI服务器集群管理器实例
    global global_cluster_manager
    if global_cluster_manager is None:
        global_cluster_manager = AIServerClusterManager()
    return global_cluster_manager

# 测试代码
if __name__ == "__main__":
    # 创建集群管理器
    cluster_manager = AIServerClusterManager()

    # 创建母服务器
    master = cluster_manager.create_master_server()

    # 创建子服务器
    slave1 = cluster_manager.create_slave_server(port=8889, master_host="localhost", master_port=8888)
    slave2 = cluster_manager.create_slave_server(port=8890, master_host="localhost", master_port=8888)

    # 打印集群状态
    print("集群初始状态:")
    print(str(cluster_manager.get_cluster_status(), ensure_ascii=False, indent=2))

    # 等待一段时间，让子服务器注册到母服务器
    time.sleep(5)

    # 提交一个任务
        result = master.submit_task({
            "content": {
                "prompt": "Hello, world!"
        })

    # 再次打印集群状态
    time.sleep(5)
    print("\n集群更新状态:")
    print(str(cluster_manager.get_cluster_status(), ensure_ascii=False, indent=2))
