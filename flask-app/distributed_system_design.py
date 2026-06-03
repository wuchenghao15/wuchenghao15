# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式AI系统设计
实现分布式节点管理、通信机制、任务分配和容错处理
"""
import time
import uuid
import logging
import threading
import json
from enum import Enum
from collections import defaultdict
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('distributed_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DistributedSystem')

class NodeType(Enum):
    """节点类型枚举"""
    MASTER = "master"
    WORKER = "worker"
    MONITOR = "monitor"
    GATEWAY = "gateway"

class NodeStatus(Enum):
    """节点状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class DistributedSystem:
    """分布式AI系统"""

    def __init__(self, node_id, node_type=NodeType.WORKER, master_address=None):
        """初始化分布式系统节点"""
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.node_type = node_type
        self.master_address = master_address
        self.status = NodeStatus.INITIALIZING
        self.heartbeat_interval = 5
        self.nodes = {}
        self.tasks = {}
        self.task_queue = []
        self.lock = threading.Lock()
        self.is_running = False

        self.start()

    def start(self):
        """启动分布式系统节点"""
        if self.is_running:
            logger.warning(f"节点 {self.node_id} 已在运行")
            return

        self.is_running = True
        self.status = NodeStatus.RUNNING

        logger.info(f"启动分布式系统节点: {self.node_id} (类型: {self.node_type.value})")

        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        if self.node_type == NodeType.MASTER:
            self._start_master_services()
        elif self.node_type == NodeType.WORKER:
            self._start_worker_services()
        elif self.node_type == NodeType.MONITOR:
            self._start_monitor_services()
        elif self.node_type == NodeType.GATEWAY:
            self._start_gateway_services()

    def stop(self):
        """停止分布式系统节点"""
        if not self.is_running:
            logger.warning(f"节点 {self.node_id} 未在运行")
            return
        self.status = NodeStatus.SHUTTING_DOWN
        logger.info(f"停止分布式系统节点: {self.node_id}")

        self.is_running = False
        self.heartbeat_thread.join(timeout=5)

        self.status = NodeStatus.SHUTDOWN
        logger.info(f"节点 {self.node_id} 已停止")

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_running:
            try:
                if self.node_type == NodeType.MASTER:
                    self._send_heartbeat_to_workers()
                else:
                    self._send_heartbeat_to_master()
            except Exception as e:
                logger.error(f"心跳发送失败: {str(e)}")

            time.sleep(self.heartbeat_interval)

    def _send_heartbeat_to_master(self):
        """向主节点发送心跳"""
        if not self.master_address:
            return

        logger.debug(f"节点 {self.node_id} 向主节点发送心跳")

        time.sleep(0.1)

    def _send_heartbeat_to_workers(self):
        """向所有工作节点发送心跳"""
        with self.lock:
            for node_id, node in self.nodes.items():
                if node["type"] == NodeType.WORKER.value:
                    logger.debug(f"主节点向工作节点 {node_id} 发送心跳")

    def _start_master_services(self):
        """启动主节点服务"""
        logger.info("启动主节点服务...")

        self.node_manager_thread = threading.Thread(target=self._node_manager)
        self.node_manager_thread.daemon = True
        self.node_manager_thread.start()

        self.task_scheduler_thread = threading.Thread(target=self._task_scheduler)
        self.task_scheduler_thread.daemon = True
        self.task_scheduler_thread.start()

        self.fault_detector_thread = threading.Thread(target=self._fault_detector)
        self.fault_detector_thread.daemon = True
        self.fault_detector_thread.start()

    def _start_worker_services(self):
        """启动工作节点服务"""
        logger.info("启动工作节点服务...")

        self.task_executor_thread = threading.Thread(target=self._task_executor)
        self.task_executor_thread.daemon = True
        self.task_executor_thread.start()

    def _start_monitor_services(self):
        """启动监控节点服务"""
        logger.info("启动监控节点服务...")

        self.system_monitor_thread = threading.Thread(target=self._system_monitor)
        self.system_monitor_thread.daemon = True
        self.system_monitor_thread.start()

    def _start_gateway_services(self):
        """启动网关节点服务"""
        logger.info("启动网关节点服务...")

        self.request_router_thread = threading.Thread(target=self._request_router)
        self.request_router_thread.daemon = True
        self.request_router_thread.start()

    def register_node(self, node_info):
        """注册节点"""
        with self.lock:
            node_id = node_info["node_id"]
            if node_id in self.nodes:
                logger.warning(f"节点已存在: {node_id}")
                return False
            self.nodes[node_id] = {
                **node_info,
                "last_heartbeat": time.time(),
                "status": NodeStatus.RUNNING.value
            }

            logger.info(f"节点已注册: {node_id} (类型: {node_info['type']})")
            return True

    def unregister_node(self, node_id):
        """注销节点"""
        with self.lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                logger.info(f"节点已注销: {node_id}")
                return True
            return False

    def create_task(self, task_info):
        """创建任务"""
        with self.lock:
            task_id = task_info.get("task_id", f"task_{uuid.uuid4().hex[:8]}")

            task = {
                **task_info,
                "task_id": task_id,
                "status": TaskStatus.PENDING.value,
                "assigned_to": None,
                "created_at": time.time(),
                "started_at": None,
                "result": None,
                "error": None,
                "retry_count": 0
            }

            self.tasks[task_id] = task
            self.task_queue.append(task_id)

            self._sort_task_queue()

            logger.info(f"任务已创建: {task_id} - {task_info['name']}")
            return task_id

    def _sort_task_queue(self):
        """按优先级排序任务队列"""
        priority_order = {
            "urgent": 0,
            "high": 1,
            "medium": 2,
            "low": 3
        }

        self.task_queue.sort(key=lambda task_id: priority_order.get(
            self.tasks[task_id].get("priority", "medium"), 2
        ))

    def _node_manager(self):
        """节点管理器"""
        while self.is_running:
            with self.lock:
                current_time = time.time()
                for node_id, node in list(self.nodes.items()):
                    if current_time - node["last_heartbeat"] > 30:
                        logger.warning(f"节点 {node_id} 心跳超时,标记为故障")
                        node["status"] = NodeStatus.FAILED.value
            time.sleep(10)

    def _task_scheduler(self):
        """任务调度器"""
        while self.is_running:
            with self.lock:
                for task_id in list(self.task_queue):
                    if self.tasks[task_id]["status"] != TaskStatus.PENDING.value:
                        continue

                    worker_node = self._find_suitable_worker(task_id)
                    if worker_node:
                        self._assign_task(task_id, worker_node["node_id"])
                        self.task_queue.remove(task_id)

            time.sleep(1)

    def _find_suitable_worker(self, task_id):
        """寻找合适的工作节点"""
        task = self.tasks[task_id]
        required_skills = task.get("required_skills", [])

        with self.lock:
            available_workers = [
                node for node in self.nodes.values()
                if node["type"] == NodeType.WORKER.value and
                node["status"] == NodeStatus.RUNNING.value and
                all(skill in node.get("skills", []) for skill in required_skills)
            ]

            if not available_workers:
                return None

            available_workers.sort(key=lambda node: node.get("workload", 0))
            return available_workers[0]

    def _assign_task(self, task_id, node_id):
        """分配任务给工作节点"""
        with self.lock:
            task = self.tasks[task_id]
            task["status"] = TaskStatus.ASSIGNED.value
            task["assigned_to"] = node_id

            if node_id in self.nodes:
                self.nodes[node_id]["workload"] = self.nodes[node_id].get("workload", 0) + 1
            logger.info(f"任务已分配: {task_id} -> {node_id}")

    def _task_executor(self):
        """任务执行器"""
        while self.is_running:
            with self.lock:
                assigned_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task["assigned_to"] == self.node_id and
                    task["status"] == TaskStatus.ASSIGNED.value
                ]
            for task_id in assigned_tasks:
                self._execute_task(task_id)
            time.sleep(1)

    def _execute_task(self, task_id):
        """执行任务"""
        with self.lock:
            task = self.tasks[task_id]
            task["status"] = TaskStatus.RUNNING.value
            task["started_at"] = time.time()

        try:
            logger.info(f"开始执行任务: {task_id} - {task['name']}")

            time.sleep(2)
            with self.lock:
                task["status"] = TaskStatus.COMPLETED.value
                task["completed_at"] = time.time()

                if task["assigned_to"] in self.nodes:
                    self.nodes[task["assigned_to"]]["workload"] -= 1

            logger.info(f"任务执行完成: {task_id}")
        except Exception as e:
            with self.lock:
                task["status"] = TaskStatus.FAILED.value
                task["completed_at"] = time.time()
                task["error"] = str(e)
                task["retry_count"] += 1
                if task["assigned_to"] in self.nodes:
                    self.nodes[task["assigned_to"]]["workload"] -= 1

                if task["retry_count"] < task.get("max_retries", 3):
                    task["assigned_to"] = None
                    self.task_queue.append(task_id)
                    logger.info(f"任务 {task_id} 执行失败,将重试 (重试次数: {task['retry_count']})")
                else:
                    logger.error(f"任务 {task_id} 执行失败,已达到最大重试次数")

    def _fault_detector(self):
        """故障检测器"""
        while self.is_running:
            with self.lock:
                for node_id, node in list(self.nodes.items()):
                    if node["status"] == NodeStatus.FAILED.value:
                        logger.warning(f"检测到故障节点: {node_id}")
                        for task_id, task in self.tasks.items():
                            if task["assigned_to"] == node_id and task["status"] in [TaskStatus.RUNNING.value, TaskStatus.ASSIGNED.value]:
                                logger.info(f"重新分配故障节点 {node_id} 的任务: {task_id}")
                                task["status"] = TaskStatus.PENDING.value
                                task["assigned_to"] = None
                                self.task_queue.append(task_id)

                        del self.nodes[node_id]
            time.sleep(15)

    def _system_monitor(self):
        """系统监控器"""
        while self.is_running:
            with self.lock:
                monitor_result = {
                    "timestamp": time.time(),
                    "worker_count": len([n for n in self.nodes.values() if n["type"] == NodeType.WORKER.value]),
                    "pending_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.PENDING.value]),
                    "running_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.RUNNING.value]),
                    "completed_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.COMPLETED.value]),
                    "failed_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.FAILED.value])
                }
            time.sleep(10)

    def _request_router(self):
        """请求路由器"""
        while self.is_running:
            logger.debug("网关节点处理外部请求")
            time.sleep(5)

    def get_system_status(self):
        """获取系统状态"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "status": self.status.value,
            "is_running": self.is_running,
            "node_count": len(self.nodes),
            "task_count": len(self.tasks),
            "timestamp": time.time()
        }

    def list_nodes(self, status=None):
        """列出节点"""
        with self.lock:
            if status:
                return [n for n in self.nodes.values() if n["status"] == status]
            return list(self.nodes.values())

    def list_tasks(self, status=None):
        """列出任务"""
        with self.lock:
            if status:
                return [t for t in self.tasks.values() if t["status"] == status]
            return list(self.tasks.values())

def test_distributed_system():
    """测试分布式系统"""
    print("=" * 60)
    print("分布式AI系统测试")
    print("=" * 60)

    master_node = DistributedSystem("master_node", NodeType.MASTER)

    worker_nodes = []
    for i in range(3):
        worker = DistributedSystem(f"worker_{i}", NodeType.WORKER, "master_node")
        worker_nodes.append(worker)

        master_node.register_node({
            "node_id": worker.node_id,
            "type": NodeType.WORKER.value,
            "status": NodeStatus.RUNNING.value,
            "skills": ["code_development", "bug_fixing", "test_execution"],
            "workload": 0,
            "last_heartbeat": time.time()
        })

    monitor_node = DistributedSystem("monitor_node", NodeType.MONITOR, "master_node")
    master_node.register_node({
        "node_id": monitor_node.node_id,
        "type": NodeType.MONITOR.value,
        "status": NodeStatus.RUNNING.value,
        "last_heartbeat": time.time()
    })

    print("\n节点列表:")
    nodes = master_node.list_nodes()
    for node in nodes:
        print(f"  {node['node_id']} - {node['type']} ({node['status']}) - 技能: {node.get('skills', [])}")

    print("\n创建测试任务...")

    for i in range(5):
        task_name = f"测试任务_{i+1}"
        task_priority = ["low", "medium", "high", "urgent", "medium"][i]
        master_node.create_task({
            "name": task_name,
            "description": f"{task_name} 描述",
            "priority": task_priority
        })

    print("\n任务列表:")
    tasks = master_node.list_tasks()
    for task in tasks:
        print(f"  {task['task_id']} - {task['name']} (优先级: {task['priority']}) - 状态: {task['status']}")

    print("\n等待任务执行 (10秒)...")
    time.sleep(10)

    print("\n任务执行状态:")
    tasks = master_node.list_tasks()
    for task in tasks:
        print(f"  {task['task_id']} - {task['name']} - 状态: {task['status']}")
        if task['status'] == TaskStatus.COMPLETED.value:
            print(f"    执行结果: {task['result']}")
        elif task['status'] == TaskStatus.FAILED.value:
            print(f"    错误信息: {task['error']}")

    system_status = master_node.get_system_status()
    print(f"\n系统状态: {json.dumps(system_status, indent=2)}")

    for worker in worker_nodes:
        worker.stop()

    monitor_node.stop()
    master_node.stop()
    print("\n" + "=" * 60)
    print("分布式AI系统测试完成")
    print("=" * 60)

def generate_architecture_design():
    """生成分布式系统架构设计文档"""
    design = {
        "系统名称": "分布式AI员工系统",
        "架构类型": "主从架构",
        "设计原则": [
            "高可用性",
            "可扩展性",
            "容错性",
            "负载均衡",
            "易于管理"
        ],
        "节点类型": [
            {
                "类型": "主节点 (Master)",
                "职责": [
                    "节点管理",
                    "任务调度",
                    "故障检测",
                    "系统监控"
                ],
                "数量": "1个(可配置主备)"
            },
            {
                "类型": "工作节点 (Worker)",
                "职责": [
                    "执行具体任务",
                    "向主节点报告状态",
                    "处理本地任务"
                ],
                "数量": "可动态扩展"
            },
            {
                "类型": "监控节点 (Monitor)",
                "职责": [
                    "系统状态监控",
                    "性能指标收集",
                    "告警处理"
                ],
                "数量": "1个或多个"
            },
            {
                "类型": "网关节点 (Gateway)",
                "职责": [
                    "外部请求路由",
                    "负载均衡",
                    "安全认证"
                ],
                "数量": "1个或多个"
            }
        ],
        "通信机制": [
            "心跳机制: 节点间定期发送心跳,检测节点状态",
            "状态同步: 节点间同步系统状态和配置信息",
            "故障通知: 故障节点检测和通知"
        ],
        "任务分配策略": [
            "基于技能匹配: 根据任务要求的技能匹配合适的工作节点",
            "基于负载均衡: 将任务分配给负载最低的节点",
            "基于优先级: 高优先级任务优先分配",
            "基于地理位置: 优先分配给地理位置相近的节点"
        ],
        "容错机制": [
            "节点故障检测: 通过心跳机制检测节点故障",
            "任务重试: 故障节点的任务自动重试",
            "任务转移: 故障节点的任务转移到其他健康节点",
            "主节点故障: 支持主备切换或选举机制"
        ],
        "监控和管理": [
            "系统状态监控",
            "性能指标收集",
            "日志管理",
            "告警机制",
            "节点管理界面"
        ],
        "部署方案": [
            "容器化部署: 使用Docker和Kubernetes管理节点",
            "云原生支持: 支持公有云、私有云和混合云部署",
            "自动化部署: 支持自动化部署和扩缩容",
            "配置管理: 集中式配置管理"
        ]
    }

    with open("distributed_system_architecture.json", "w", encoding="utf-8") as f:
        json.dump(design, f, ensure_ascii=False, indent=2)

    print("\n分布式系统架构设计文档已生成: distributed_system_architecture.json")

    return design

if __name__ == "__main__":
    generate_architecture_design()
    test_distributed_system()
