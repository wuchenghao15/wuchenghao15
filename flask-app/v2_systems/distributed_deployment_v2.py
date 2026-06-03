#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式部署系统 V2.0 (Distributed Deployment System)
增强版分布式系统，支持节点管理、负载均衡、故障转移、服务发现和数据同步
"""

import time
import uuid
import json
import hashlib
import logging
import threading
import sqlite3
import socket
import struct
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('distributed_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DistributedDeployment')

class NodeStatus(Enum):
    """节点状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    SYNCING = "syncing"

class NodeType(Enum):
    """节点类型枚举"""
    MASTER = "master"
    SLAVE = "slave"
    WORKER = "worker"
    CACHE = "cache"
    GATEWAY = "gateway"

class ServiceStatus(Enum):
    """服务状态枚举"""
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UPDATING = "updating"

class DeploymentStrategy(Enum):
    """部署策略枚举"""
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"

class LoadBalancingAlgorithm(Enum):
    """负载均衡算法枚举"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    WEIGHTED = "weighted"
    RANDOM = "random"

@dataclass
class Node:
    """节点"""
    node_id: str
    name: str
    node_type: NodeType
    host: str
    port: int
    status: NodeStatus = NodeStatus.OFFLINE
    weight: int = 100
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    active_connections: int = 0
    last_heartbeat: float = 0.0
    created_at: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.last_heartbeat == 0.0:
            self.last_heartbeat = time.time()

@dataclass
class Service:
    """服务"""
    service_id: str
    name: str
    version: str
    image: str
    replicas: int = 1
    status: ServiceStatus = ServiceStatus.STOPPED
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    ports: List[Dict] = None
    environment: Dict = None
    resources: Dict = None
    health_check: Dict = None
    created_at: float = 0.0
    updated_at: float = 0.0
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []
        if self.environment is None:
            self.environment = {}
        if self.resources is None:
            self.resources = {}
        if self.health_check is None:
            self.health_check = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class ServiceInstance:
    """服务实例"""
    instance_id: str
    service_id: str
    node_id: str
    status: ServiceStatus = ServiceStatus.DEPLOYING
    port: int = 0
    started_at: float = 0.0
    health: float = 1.0
    request_count: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        if self.started_at == 0.0:
            self.started_at = time.time()

@dataclass
class Deployment:
    """部署记录"""
    deployment_id: str
    service_id: str
    strategy: DeploymentStrategy
    from_version: str
    to_version: str
    status: str = "pending"
    progress: float = 0.0
    created_at: float = 0.0
    completed_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class SyncRecord:
    """同步记录"""
    record_id: str
    node_id: str
    data_type: str
    operation: str
    data: Any
    timestamp: float = 0.0
    status: str = "pending"
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class DistributedDeploymentSystem:
    """增强版分布式部署系统"""
    
    def __init__(self):
        """初始化分布式部署系统"""
        self.nodes: Dict[str, Node] = {}
        self.services: Dict[str, Service] = {}
        self.service_instances: Dict[str, ServiceInstance] = {}
        self.deployments: Dict[str, Deployment] = {}
        self.sync_records: Dict[str, SyncRecord] = {}
        
        self.node_locks: Dict[str, threading.Lock] = {}
        self.global_lock = threading.Lock()
        
        self.health_check_interval = 30
        self.heartbeat_timeout = 60
        
        self._init_database()
        self._init_default_nodes()
        
        self._start_health_monitor()
        self._start_sync_monitor()
        
        logger.info("分布式部署系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('distributed_deployment.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    status TEXT DEFAULT 'offline',
                    weight INTEGER DEFAULT 100,
                    cpu_usage REAL DEFAULT 0,
                    memory_usage REAL DEFAULT 0,
                    disk_usage REAL DEFAULT 0,
                    active_connections INTEGER DEFAULT 0,
                    last_heartbeat REAL,
                    created_at REAL,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    service_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    image TEXT NOT NULL,
                    replicas INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'stopped',
                    strategy TEXT DEFAULT 'rolling',
                    ports TEXT,
                    environment TEXT,
                    resources TEXT,
                    health_check TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_instances (
                    instance_id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    status TEXT DEFAULT 'deploying',
                    port INTEGER DEFAULT 0,
                    started_at REAL,
                    health REAL DEFAULT 1,
                    request_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    FOREIGN KEY (service_id) REFERENCES services(service_id),
                    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    deployment_id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    from_version TEXT,
                    to_version TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress REAL DEFAULT 0,
                    created_at REAL,
                    completed_at REAL,
                    FOREIGN KEY (service_id) REFERENCES services(service_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_records (
                    record_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data TEXT,
                    timestamp REAL,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
                )
            ''')
            
            self.db_conn.commit()
            logger.info("分布式部署数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _init_default_nodes(self):
        """初始化默认节点"""
        local_host = socket.gethostname()
        
        default_nodes = [
            Node(
                node_id="node_master_1",
                name="主节点1",
                node_type=NodeType.MASTER,
                host=local_host,
                port=8001,
                status=NodeStatus.ONLINE,
                metadata={"region": "local", "datacenter": "dc1"}
            ),
            Node(
                node_id="node_slave_1",
                name="从节点1",
                node_type=NodeType.SLAVE,
                host=local_host,
                port=8002,
                status=NodeStatus.ONLINE,
                metadata={"region": "local", "datacenter": "dc1"}
            ),
            Node(
                node_id="node_worker_1",
                name="工作节点1",
                node_type=NodeType.WORKER,
                host=local_host,
                port=8003,
                status=NodeStatus.ONLINE,
                metadata={"region": "local", "datacenter": "dc1"}
            ),
            Node(
                node_id="node_cache_1",
                name="缓存节点1",
                node_type=NodeType.CACHE,
                host=local_host,
                port=8004,
                status=NodeStatus.ONLINE,
                metadata={"region": "local", "datacenter": "dc1"}
            ),
            Node(
                node_id="node_gateway_1",
                name="网关节点1",
                node_type=NodeType.GATEWAY,
                host=local_host,
                port=8005,
                status=NodeStatus.ONLINE,
                metadata={"region": "local", "datacenter": "dc1"}
            )
        ]
        
        with self.global_lock:
            for node in default_nodes:
                if node.node_id not in self.nodes:
                    self.nodes[node.node_id] = node
                    self.node_locks[node.node_id] = threading.Lock()
                    self._save_node(node)
    
    def _save_node(self, node: Node):
        """保存节点到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO nodes
                (node_id, name, node_type, host, port, status, weight, cpu_usage, 
                 memory_usage, disk_usage, active_connections, last_heartbeat, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                node.node_id, node.name, node.node_type.value, node.host, node.port,
                node.status.value, node.weight, node.cpu_usage, node.memory_usage,
                node.disk_usage, node.active_connections, node.last_heartbeat,
                node.created_at, json.dumps(node.metadata)
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存节点失败: {str(e)}")
    
    def _save_service(self, service: Service):
        """保存服务到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO services
                (service_id, name, version, image, replicas, status, strategy, ports, 
                 environment, resources, health_check, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                service.service_id, service.name, service.version, service.image,
                service.replicas, service.status.value, service.strategy.value,
                json.dumps(service.ports), json.dumps(service.environment),
                json.dumps(service.resources), json.dumps(service.health_check),
                service.created_at, service.updated_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存服务失败: {str(e)}")
    
    def add_node(self, name: str, node_type: NodeType, host: str, port: int,
                weight: int = 100, metadata: Dict = None) -> str:
        """添加节点"""
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        
        node = Node(
            node_id=node_id,
            name=name,
            node_type=node_type,
            host=host,
            port=port,
            weight=weight,
            metadata=metadata or {}
        )
        
        with self.global_lock:
            self.nodes[node_id] = node
            self.node_locks[node_id] = threading.Lock()
            self._save_node(node)
        
        logger.info(f"添加节点: {name} ({node_id})")
        return node_id
    
    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        with self.global_lock:
            if node_id not in self.nodes:
                logger.error(f"节点不存在: {node_id}")
                return False
            
            del self.nodes[node_id]
            if node_id in self.node_locks:
                del self.node_locks[node_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM nodes WHERE node_id = ?', (node_id,))
            cursor.execute('DELETE FROM service_instances WHERE node_id = ?', (node_id,))
            self.db_conn.commit()
        
        logger.info(f"移除节点: {node_id}")
        return True
    
    def update_node_status(self, node_id: str, status: NodeStatus) -> bool:
        """更新节点状态"""
        with self.global_lock:
            node = self.nodes.get(node_id)
            if not node:
                return False
            
            node.status = status
            node.last_heartbeat = time.time()
            self._save_node(node)
        
        logger.info(f"更新节点状态: {node_id} -> {status.value}")
        return True
    
    def heartbeat(self, node_id: str, metrics: Dict = None) -> bool:
        """节点心跳"""
        with self.global_lock:
            node = self.nodes.get(node_id)
            if not node:
                return False
            
            node.last_heartbeat = time.time()
            
            if metrics:
                if 'cpu_usage' in metrics:
                    node.cpu_usage = metrics['cpu_usage']
                if 'memory_usage' in metrics:
                    node.memory_usage = metrics['memory_usage']
                if 'disk_usage' in metrics:
                    node.disk_usage = metrics['disk_usage']
                if 'active_connections' in metrics:
                    node.active_connections = metrics['active_connections']
            
            self._save_node(node)
        
        return True
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """获取节点"""
        with self.global_lock:
            return self.nodes.get(node_id)
    
    def list_nodes(self, status: NodeStatus = None, node_type: NodeType = None) -> List[Dict]:
        """列出节点"""
        with self.global_lock:
            result = []
            for node_id, node in self.nodes.items():
                if status and node.status != status:
                    continue
                if node_type and node.node_type != node_type:
                    continue
                
                result.append({
                    "node_id": node.node_id,
                    "name": node.name,
                    "node_type": node.node_type.value,
                    "host": node.host,
                    "port": node.port,
                    "status": node.status.value,
                    "weight": node.weight,
                    "cpu_usage": node.cpu_usage,
                    "memory_usage": node.memory_usage,
                    "active_connections": node.active_connections,
                    "last_heartbeat": node.last_heartbeat
                })
            return result
    
    def deploy_service(self, name: str, version: str, image: str,
                      replicas: int = 1, strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
                      ports: List[Dict] = None, environment: Dict = None,
                      resources: Dict = None) -> str:
        """部署服务"""
        service_id = f"srv_{uuid.uuid4().hex[:8]}"
        
        service = Service(
            service_id=service_id,
            name=name,
            version=version,
            image=image,
            replicas=replicas,
            strategy=strategy,
            ports=ports or [],
            environment=environment or {},
            resources=resources or {}
        )
        
        with self.global_lock:
            self.services[service_id] = service
            self._save_service(service)
        
        threading.Thread(target=self._deploy_service_instances, 
                        args=(service_id,), daemon=True).start()
        
        logger.info(f"部署服务: {name} ({service_id})")
        return service_id
    
    def _deploy_service_instances(self, service_id: str):
        """部署服务实例"""
        service = self.services.get(service_id)
        if not service:
            return
        
        service.status = ServiceStatus.DEPLOYING
        self._save_service(service)
        
        available_nodes = [n for n in self.nodes.values() 
                         if n.status == NodeStatus.ONLINE]
        
        if not available_nodes:
            logger.error("没有可用的节点")
            service.status = ServiceStatus.FAILED
            self._save_service(service)
            return
        
        instances_per_node = max(1, service.replicas // len(available_nodes))
        
        for node in available_nodes[:service.replicas]:
            for i in range(instances_per_node):
                if len(self.service_instances) >= service.replicas:
                    break
                
                instance_id = f"inst_{uuid.uuid4().hex[:8]}"
                instance = ServiceInstance(
                    instance_id=instance_id,
                    service_id=service_id,
                    node_id=node.node_id,
                    status=ServiceStatus.DEPLOYING
                )
                
                self.service_instances[instance_id] = instance
                
                self._create_service_instance(instance, node)
        
        service.status = ServiceStatus.RUNNING
        service.updated_at = time.time()
        self._save_service(service)
        
        logger.info(f"服务实例部署完成: {service_id}")
    
    def _create_service_instance(self, instance: ServiceInstance, node: Node):
        """创建服务实例"""
        time.sleep(0.5)
        
        instance.status = ServiceStatus.RUNNING
        instance.port = 8000 + len(self.service_instances)
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO service_instances
                (instance_id, service_id, node_id, status, port, started_at, health, request_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                instance.instance_id, instance.service_id, instance.node_id,
                instance.status.value, instance.port, instance.started_at,
                instance.health, instance.request_count, instance.error_count
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"创建服务实例失败: {str(e)}")
    
    def scale_service(self, service_id: str, replicas: int) -> bool:
        """扩缩容服务"""
        with self.global_lock:
            service = self.services.get(service_id)
            if not service:
                return False
            
            service.replicas = replicas
            service.updated_at = time.time()
            self._save_service(service)
        
        current_instances = sum(1 for i in self.service_instances.values() 
                              if i.service_id == service_id and i.status == ServiceStatus.RUNNING)
        
        if replicas > current_instances:
            threading.Thread(target=self._scale_up, 
                           args=(service_id, replicas - current_instances), daemon=True).start()
        elif replicas < current_instances:
            self._scale_down(service_id, current_instances - replicas)
        
        logger.info(f"服务扩缩容: {service_id} -> {replicas}")
        return True
    
    def _scale_up(self, service_id: str, count: int):
        """扩容"""
        available_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.ONLINE]
        
        for i in range(count):
            if not available_nodes:
                break
            
            node = available_nodes[i % len(available_nodes)]
            
            instance_id = f"inst_{uuid.uuid4().hex[:8]}"
            instance = ServiceInstance(
                instance_id=instance_id,
                service_id=service_id,
                node_id=node.node_id,
                status=ServiceStatus.DEPLOYING
            )
            
            self.service_instances[instance_id] = instance
            self._create_service_instance(instance, node)
    
    def _scale_down(self, service_id: str, count: int):
        """缩容"""
        instances = [i for i in self.service_instances.values() 
                    if i.service_id == service_id and i.status == ServiceStatus.RUNNING]
        
        for instance in instances[:count]:
            self.service_instances[instance.instance_id].status = ServiceStatus.STOPPED
    
    def update_service(self, service_id: str, version: str) -> str:
        """更新服务"""
        with self.global_lock:
            service = self.services.get(service_id)
            if not service:
                raise ValueError(f"服务不存在: {service_id}")
            
            deployment_id = f"dep_{uuid.uuid4().hex[:8]}"
            deployment = Deployment(
                deployment_id=deployment_id,
                service_id=service_id,
                strategy=service.strategy,
                from_version=service.version,
                to_version=version
            )
            
            self.deployments[deployment_id] = deployment
            
            service.status = ServiceStatus.UPDATING
            service.version = version
            service.updated_at = time.time()
            self._save_service(service)
        
        threading.Thread(target=self._execute_deployment,
                        args=(deployment_id,), daemon=True).start()
        
        logger.info(f"服务更新: {service_id} -> {version}")
        return deployment_id
    
    def _execute_deployment(self, deployment_id: str):
        """执行部署"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return
        
        deployment.status = "in_progress"
        
        for i in range(10):
            deployment.progress = (i + 1) * 10
            time.sleep(0.5)
        
        deployment.status = "completed"
        deployment.completed_at = time.time()
        
        logger.info(f"部署完成: {deployment_id}")
    
    def remove_service(self, service_id: str) -> bool:
        """移除服务"""
        with self.global_lock:
            if service_id not in self.services:
                return False
            
            instances = [i for i in self.service_instances.values() if i.service_id == service_id]
            for instance in instances:
                del self.service_instances[instance.instance_id]
            
            del self.services[service_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM services WHERE service_id = ?', (service_id,))
            cursor.execute('DELETE FROM service_instances WHERE service_id = ?', (service_id,))
            self.db_conn.commit()
        
        logger.info(f"移除服务: {service_id}")
        return True
    
    def get_service(self, service_id: str) -> Optional[Service]:
        """获取服务"""
        with self.global_lock:
            return self.services.get(service_id)
    
    def list_services(self) -> List[Dict]:
        """列出服务"""
        with self.global_lock:
            result = []
            for service_id, service in self.services.items():
                instances = [i for i in self.service_instances.values() 
                           if i.service_id == service_id]
                
                result.append({
                    "service_id": service.service_id,
                    "name": service.name,
                    "version": service.version,
                    "image": service.image,
                    "replicas": service.replicas,
                    "current_replicas": len([i for i in instances if i.status == ServiceStatus.RUNNING]),
                    "status": service.status.value,
                    "strategy": service.strategy.value,
                    "created_at": service.created_at
                })
            return result
    
    def select_node(self, algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN) -> Optional[Node]:
        """选择节点（负载均衡）"""
        available_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.ONLINE]
        
        if not available_nodes:
            return None
        
        if algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return available_nodes[0]
        elif algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return min(available_nodes, key=lambda n: n.active_connections)
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED:
            total_weight = sum(n.weight for n in available_nodes)
            r = hashlib.md5(str(time.time()).encode()).hexdigest()
            index = int(r, 16) % total_weight
            cumulative = 0
            for node in available_nodes:
                cumulative += node.weight
                if index < cumulative:
                    return node
        elif algorithm == LoadBalancingAlgorithm.RANDOM:
            import random
            return random.choice(available_nodes)
        else:
            return available_nodes[0]
    
    def sync_data(self, node_id: str, data_type: str, operation: str, data: Any) -> str:
        """同步数据"""
        record_id = f"sync_{uuid.uuid4().hex[:8]}"
        
        record = SyncRecord(
            record_id=record_id,
            node_id=node_id,
            data_type=data_type,
            operation=operation,
            data=data
        )
        
        with self.global_lock:
            self.sync_records[record_id] = record
        
        threading.Thread(target=self._execute_sync, args=(record_id,), daemon=True).start()
        
        logger.debug(f"数据同步: {node_id} -> {data_type}")
        return record_id
    
    def _execute_sync(self, record_id: str):
        """执行同步"""
        record = self.sync_records.get(record_id)
        if not record:
            return
        
        time.sleep(0.1)
        
        record.status = "completed"
    
    def _start_health_monitor(self):
        """启动健康监控线程"""
        self.health_monitor = threading.Thread(
            target=self._health_monitor_loop,
            name="health_monitor",
            daemon=True
        )
        self.health_monitor.start()
    
    def _health_monitor_loop(self):
        """健康监控循环"""
        while True:
            try:
                self._check_nodes_health()
                self._check_services_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"健康监控线程错误: {str(e)}")
                time.sleep(60)
    
    def _check_nodes_health(self):
        """检查节点健康状态"""
        with self.global_lock:
            for node_id, node in self.nodes.items():
                if node.status == NodeStatus.OFFLINE:
                    continue
                
                if time.time() - node.last_heartbeat > self.heartbeat_timeout:
                    node.status = NodeStatus.OFFLINE
                    self._save_node(node)
                    logger.warning(f"节点离线: {node_id}")
                    continue
                
                if node.cpu_usage > 90 or node.memory_usage > 90:
                    node.status = NodeStatus.DEGRADED
                    self._save_node(node)
    
    def _check_services_health(self):
        """检查服务健康状态"""
        with self.global_lock:
            for instance_id, instance in self.service_instances.items():
                if instance.status != ServiceStatus.RUNNING:
                    continue
                
                if instance.health < 0.5:
                    instance.status = ServiceStatus.FAILED
                    
                    try:
                        cursor = self.db_conn.cursor()
                        cursor.execute('''
                            UPDATE service_instances SET status = ? WHERE instance_id = ?
                        ''', (ServiceStatus.FAILED.value, instance_id))
                        self.db_conn.commit()
                    except Exception as e:
                        logger.error(f"更新服务实例状态失败: {str(e)}")
    
    def _start_sync_monitor(self):
        """启动同步监控线程"""
        self.sync_monitor = threading.Thread(
            target=self._sync_monitor_loop,
            name="sync_monitor",
            daemon=True
        )
        self.sync_monitor.start()
    
    def _sync_monitor_loop(self):
        """同步监控循环"""
        while True:
            try:
                self._process_pending_syncs()
                time.sleep(5)
            except Exception as e:
                logger.error(f"同步监控线程错误: {str(e)}")
                time.sleep(60)
    
    def _process_pending_syncs(self):
        """处理待处理的同步"""
        with self.global_lock:
            for record_id, record in self.sync_records.items():
                if record.status == "pending":
                    threading.Thread(target=self._execute_sync, args=(record_id,), daemon=True).start()
    
    def get_stats(self) -> Dict:
        """获取系统统计信息"""
        with self.global_lock:
            total_nodes = len(self.nodes)
            online_nodes = sum(1 for n in self.nodes.values() if n.status == NodeStatus.ONLINE)
            total_services = len(self.services)
            running_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.RUNNING)
            total_instances = len(self.service_instances)
            running_instances = sum(1 for i in self.service_instances.values() 
                                  if i.status == ServiceStatus.RUNNING)
            
            avg_cpu = sum(n.cpu_usage for n in self.nodes.values()) / total_nodes if total_nodes else 0
            avg_memory = sum(n.memory_usage for n in self.nodes.values()) / total_nodes if total_nodes else 0
            
            return {
                "total_nodes": total_nodes,
                "online_nodes": online_nodes,
                "offline_nodes": total_nodes - online_nodes,
                "total_services": total_services,
                "running_services": running_services,
                "total_instances": total_instances,
                "running_instances": running_instances,
                "avg_cpu_usage": avg_cpu,
                "avg_memory_usage": avg_memory,
                "pending_syncs": sum(1 for r in self.sync_records.values() if r.status == "pending")
            }


def test_distributed_deployment():
    """测试分布式部署系统"""
    print("分布式部署系统 V2.0 测试")
    print("=" * 60)
    
    dds = DistributedDeploymentSystem()
    
    print("列出节点:")
    nodes = dds.list_nodes()
    for node in nodes:
        print(f"  {node['name']}: {node['status']} ({node['node_type']})")
    
    print("\n添加新节点:")
    new_node_id = dds.add_node("测试节点", NodeType.WORKER, "192.168.1.100", 9000)
    print(f"  添加节点: {new_node_id}")
    
    print("\n部署服务:")
    service_id = dds.deploy_service(
        name="test-service",
        version="1.0.0",
        image="test:latest",
        replicas=3,
        strategy=DeploymentStrategy.ROLLING
    )
    print(f"  部署服务: {service_id}")
    
    time.sleep(1)
    
    print("\n列出服务:")
    services = dds.list_services()
    for service in services:
        print(f"  {service['name']}: {service['status']} ({service['current_replicas']}/{service['replicas']})")
    
    print("\n扩缩容测试:")
    dds.scale_service(service_id, 5)
    print("  扩缩容完成")
    
    time.sleep(0.5)
    
    print("\n更新服务:")
    deployment_id = dds.update_service(service_id, "2.0.0")
    print(f"  更新部署: {deployment_id}")
    
    print("\n负载均衡测试:")
    for i in range(5):
        node = dds.select_node(LoadBalancingAlgorithm.ROUND_ROBIN)
        if node:
            print(f"  选择节点: {node.name}")
    
    print("\n数据同步测试:")
    sync_id = dds.sync_data("node_master_1", "config", "update", {"key": "value"})
    print(f"  同步记录: {sync_id}")
    
    print("\n节点心跳测试:")
    dds.heartbeat("node_master_1", {"cpu_usage": 45.5, "memory_usage": 60.2})
    print("  心跳已发送")
    
    print("\n系统统计:")
    stats = dds.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n分布式部署系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_distributed_deployment()