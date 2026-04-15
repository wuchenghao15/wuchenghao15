#!/usr/bin/env python3
"""
AI Master-Slave Server Manager
"""

import threading
import time
import json
from collections import deque
from typing import List, Dict, Any, Optional

class AIServerNode:
    """AI服务器节点基类"""
    def __init__(self, node_id: str, name: str, ip: str, port: int):
        self.node_id = node_id
        self.name = name
        self.ip = ip
        self.port = port
        self.status = "active"  # active, inactive, maintenance, error
        self.last_heartbeat = time.time()
        self.load = 0.0  # 0.0 to 1.0
        self.resources = {
            "cpu": 0.0,
            "memory": 0.0,
            "disk": 0.0
        }
        self.task_queue = deque()
        self.executed_tasks = []
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()
    
    def update_status(self, status: str):
        """更新节点状态"""
        self.status = status
    
    def update_resources(self, resources: Dict[str, float]):
        """更新资源使用情况"""
        self.resources.update(resources)
        # 计算总体负载
        self.load = sum(resources.values()) / 3.0
    
    def add_task(self, task: Dict[str, Any]):
        """添加任务到队列"""
        self.task_queue.append(task)
    
    def execute_next_task(self):
        """执行下一个任务"""
        if self.task_queue:
            task = self.task_queue.popleft()
            # 这里应该是实际执行任务的逻辑
            task["status"] = "completed"
            task["completed_time"] = time.time()
            self.executed_tasks.append(task)
            return task
        return None
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取节点健康状态"""
        current_time = time.time()
        is_alive = (current_time - self.last_heartbeat) < 30  # 30秒无心跳视为死亡
        
        return {
            "node_id": self.node_id,
            "name": self.name,
            "status": self.status,
            "is_alive": is_alive,
            "load": self.load,
            "resources": self.resources,
            "last_heartbeat": self.last_heartbeat,
            "pending_tasks": len(self.task_queue),
            "executed_tasks": len(self.executed_tasks)
        }

class AIMasterServer(AIServerNode):
    """AI主服务器"""
    def __init__(self, node_id: str, name: str, ip: str, port: int):
        super().__init__(node_id, name, ip, port)
        self.slave_servers = {}  # slave_id -> AISlaveServer
        self.task_distribution_strategy = "round-robin"  # round-robin, load-based
    
    def add_slave_server(self, slave_server):
        """添加从服务器"""
        self.slave_servers[slave_server.node_id] = slave_server
    
    def remove_slave_server(self, slave_id: str):
        """移除从服务器"""
        if slave_id in self.slave_servers:
            del self.slave_servers[slave_id]
    
    def distribute_task(self, task: Dict[str, Any]):
        """分发任务到从服务器"""
        if not self.slave_servers:
            # 没有从服务器，自己执行
            self.add_task(task)
            return None
        
        if self.task_distribution_strategy == "round-robin":
            # 轮询策略
            slave_ids = list(self.slave_servers.keys())
            if not slave_ids:
                return None
            
            # 找到下一个应该接收任务的从服务器
            # 基于已执行任务数量
            min_tasks = min([len(slave.executed_tasks) for slave in self.slave_servers.values()])
            next_slave = None
            for slave_id, slave in self.slave_servers.items():
                if len(slave.executed_tasks) == min_tasks:
                    next_slave = slave
                    break
        elif self.task_distribution_strategy == "load-based":
            # 基于负载的策略
            # 找到负载最低的从服务器
            min_load = min([slave.load for slave in self.slave_servers.values()])
            next_slave = None
            for slave_id, slave in self.slave_servers.items():
                if slave.load == min_load and slave.status == "active":
                    next_slave = slave
                    break
        else:
            # 默认轮询
            next_slave = list(self.slave_servers.values())[0]
        
        if next_slave:
            next_slave.add_task(task)
            return next_slave.node_id
        return None
    
    def get_all_slaves_health(self) -> List[Dict[str, Any]]:
        """获取所有从服务器的健康状态"""
        return [slave.get_health_status() for slave in self.slave_servers.values()]
    
    def update_slave_heartbeat(self, slave_id: str):
        """更新从服务器心跳"""
        if slave_id in self.slave_servers:
            self.slave_servers[slave_id].update_heartbeat()
    
    def update_slave_resources(self, slave_id: str, resources: Dict[str, float]):
        """更新从服务器资源使用情况"""
        if slave_id in self.slave_servers:
            self.slave_servers[slave_id].update_resources(resources)

class AISlaveServer(AIServerNode):
    """AI从服务器"""
    def __init__(self, node_id: str, name: str, ip: str, port: int, master_id: str):
        super().__init__(node_id, name, ip, port)
        self.master_id = master_id
        self.registration_time = time.time()
        self.ai_employees = []  # 该服务器上的AI员工列表
    
    def register_ai_employee(self, employee_id: str):
        """注册AI员工到服务器"""
        if employee_id not in self.ai_employees:
            self.ai_employees.append(employee_id)
    
    def unregister_ai_employee(self, employee_id: str):
        """从服务器注销AI员工"""
        if employee_id in self.ai_employees:
            self.ai_employees.remove(employee_id)
    
    def get_ai_employees(self) -> List[str]:
        """获取服务器上的AI员工列表"""
        return self.ai_employees.copy()

class AIServerClusterManager:
    """AI服务器集群管理器"""
    def __init__(self):
        self.master_servers = {}  # master_id -> AIMasterServer
        self.slave_servers = {}  # slave_id -> AISlaveServer
        self.node_id_counter = 1
    
    def create_master_server(self, name: str, ip: str, port: int) -> str:
        """创建主服务器"""
        node_id = f"master_{self.node_id_counter}"
        self.node_id_counter += 1
        master = AIMasterServer(node_id, name, ip, port)
        self.master_servers[node_id] = master
        return node_id
    
    def create_slave_server(self, name: str, ip: str, port: int, master_id: str) -> str:
        """创建从服务器"""
        if master_id not in self.master_servers:
            return None
        
        node_id = f"slave_{self.node_id_counter}"
        self.node_id_counter += 1
        slave = AISlaveServer(node_id, name, ip, port, master_id)
        self.slave_servers[node_id] = slave
        self.master_servers[master_id].add_slave_server(slave)
        return node_id
    
    def get_master_server(self, master_id: str) -> Optional[AIMasterServer]:
        """获取主服务器"""
        return self.master_servers.get(master_id)
    
    def get_slave_server(self, slave_id: str) -> Optional[AISlaveServer]:
        """获取从服务器"""
        return self.slave_servers.get(slave_id)
    
    def get_all_master_servers(self) -> Dict[str, AIMasterServer]:
        """获取所有主服务器"""
        return self.master_servers
    
    def get_all_slave_servers(self) -> Dict[str, AISlaveServer]:
        """获取所有从服务器"""
        return self.slave_servers
    
    def remove_server(self, node_id: str):
        """移除服务器"""
        if node_id in self.master_servers:
            # 移除主服务器及其所有从服务器
            master = self.master_servers[node_id]
            for slave_id in list(master.slave_servers.keys()):
                if slave_id in self.slave_servers:
                    del self.slave_servers[slave_id]
            del self.master_servers[node_id]
        elif node_id in self.slave_servers:
            # 从相应的主服务器中移除该从服务器
            slave = self.slave_servers[node_id]
            if slave.master_id in self.master_servers:
                self.master_servers[slave.master_id].remove_slave_server(node_id)
            del self.slave_servers[node_id]
    
    def distribute_task_to_cluster(self, task: Dict[str, Any]) -> Optional[str]:
        """将任务分发到集群"""
        if not self.master_servers:
            return None
        
        # 简单策略：选择第一个主服务器
        master_id = list(self.master_servers.keys())[0]
        return self.master_servers[master_id].distribute_task(task)
    
    def get_cluster_health_report(self) -> Dict[str, Any]:
        """获取集群健康报告"""
        report = {
            "timestamp": time.time(),
            "master_count": len(self.master_servers),
            "slave_count": len(self.slave_servers),
            "masters": {},
            "slaves": {}
        }
        
        # 获取所有主服务器状态
        for master_id, master in self.master_servers.items():
            report["masters"][master_id] = master.get_health_status()
            report["masters"][master_id]["slave_count"] = len(master.slave_servers)
        
        # 获取所有从服务器状态
        for slave_id, slave in self.slave_servers.items():
            report["slaves"][slave_id] = slave.get_health_status()
            report["slaves"][slave_id]["ai_employee_count"] = len(slave.ai_employees)
        
        return report
    
    def monitor_cluster(self):
        """监控集群状态（应该在后台线程中运行）"""
        while True:
            # 检查所有节点的心跳
            current_time = time.time()
            for slave_id, slave in self.slave_servers.items():
                if (current_time - slave.last_heartbeat) > 30:
                    slave.update_status("inactive")
                    print(f"[WARNING] Slave server {slave_id} is inactive")
            
            # 可以添加更多监控逻辑，如资源使用阈值检查等
            time.sleep(10)  # 每10秒检查一次

# 创建全局AI服务器集群管理器实例
ai_server_cluster_manager = AIServerClusterManager()

# 启动集群监控线程
monitor_thread = threading.Thread(target=ai_server_cluster_manager.monitor_cluster, daemon=True)
monitor_thread.start()
