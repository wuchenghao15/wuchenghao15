#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群管理服务 - 实现应用集群和负载均衡
"""

import json
import time
import requests
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4

from app.utils.logging import logger
from app.utils.lock_sync_manager import lock_sync_manager, LockType, synchronized


class NodeRole(Enum):
    """节点角色"""
    MASTER = "master"
    SLAVE = "slave"
    STANDBY = "standby"


class NodeStatus(Enum):
    """节点状态"""
    ACTIVE = "active"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DOWN = "down"
    MAINTENANCE = "maintenance"


@dataclass
class ClusterNode:
    """集群节点"""
    id: str
    name: str
    host: str
    port: int
    role: NodeRole
    status: NodeStatus
    weight: int = 1
    connections: int = 0
    last_heartbeat: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'role': self.role.value,
            'status': self.status.value,
            'weight': self.weight,
            'connections': self.connections,
            'last_heartbeat': self.last_heartbeat,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"


class ClusterService:
    """集群管理服务"""

    def __init__(self):
        self._nodes: Dict[str, ClusterNode] = {}
        self._nodes_lock = threading.RLock()
        self._strategy = LoadBalanceStrategy.ROUND_ROBIN
        self._round_robin_index = 0
        self._health_check_interval = 10  # 健康检查间隔(秒)
        self._heartbeat_timeout = 30  # 心跳超时(秒)
        self._running = False
        self._health_thread = None
        self._local_node_id = self._generate_node_id()
        self._init_default_nodes()
        logger.info("集群管理服务初始化完成")

    def _generate_node_id(self) -> str:
        """生成节点ID"""
        import socket
        hostname = socket.gethostname()
        return f"node-{hostname}-{uuid4().hex[:8]}"

    def _init_default_nodes(self):
        """初始化默认节点"""
        import os
        node_count = int(os.environ.get('CLUSTER_NODE_COUNT', 1))
        
        for i in range(node_count):
            node_id = f"node-{i+1}"
            host = f"mtscos-app-{i+1}" if node_count > 1 else "mtscos-app"
            role = NodeRole.MASTER if i == 0 else NodeRole.SLAVE
            
            node = ClusterNode(
                id=node_id,
                name=f"MTSCOS Node {i+1}",
                host=host,
                port=8888,
                role=role,
                status=NodeStatus.ACTIVE,
                weight=1,
                last_heartbeat=time.time()
            )
            self._nodes[node_id] = node

    def add_node(self, node_data: Dict) -> bool:
        """添加节点"""
        try:
            node = ClusterNode(
                id=node_data.get('id', str(uuid4())),
                name=node_data.get('name', 'Unknown Node'),
                host=node_data.get('host', 'localhost'),
                port=node_data.get('port', 8888),
                role=NodeRole(node_data.get('role', 'slave')),
                status=NodeStatus.ACTIVE,
                weight=node_data.get('weight', 1),
                last_heartbeat=time.time()
            )

            with self._nodes_lock:
                self._nodes[node.id] = node

            logger.info(f"节点添加成功: {node.id}")
            return True
        except Exception as e:
            logger.error(f"添加节点失败: {str(e)}")
            return False

    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        try:
            with self._nodes_lock:
                if node_id in self._nodes:
                    del self._nodes[node_id]
                    logger.info(f"节点移除成功: {node_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"移除节点失败: {str(e)}")
            return False

    def get_node(self, node_id: str) -> Optional[ClusterNode]:
        """获取节点"""
        with self._nodes_lock:
            return self._nodes.get(node_id)

    def list_nodes(self, status_filter: Optional[str] = None) -> List[ClusterNode]:
        """列出节点"""
        with self._nodes_lock:
            nodes = list(self._nodes.values())
            if status_filter:
                nodes = [n for n in nodes if n.status.value == status_filter]
            return nodes

    def update_node_status(self, node_id: str, status: NodeStatus):
        """更新节点状态"""
        with self._nodes_lock:
            if node_id in self._nodes:
                self._nodes[node_id].status = status
                logger.info(f"节点状态更新: {node_id} -> {status.value}")

    def update_node_connections(self, node_id: str, delta: int):
        """更新节点连接数"""
        with self._nodes_lock:
            if node_id in self._nodes:
                self._nodes[node_id].connections += delta

    def record_heartbeat(self, node_id: str):
        """记录心跳"""
        with self._nodes_lock:
            if node_id in self._nodes:
                self._nodes[node_id].last_heartbeat = time.time()
                self._nodes[node_id].status = NodeStatus.HEALTHY

    def start_health_check(self):
        """启动健康检查"""
        if self._running:
            return
        
        self._running = True
        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()
        logger.info("集群健康检查已启动")

    def stop_health_check(self):
        """停止健康检查"""
        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=5)
        logger.info("集群健康检查已停止")

    def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                self._perform_health_check()
                time.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"健康检查错误: {str(e)}")
                time.sleep(5)

    def _perform_health_check(self):
        """执行健康检查"""
        with self._nodes_lock:
            for node_id, node in list(self._nodes.items()):
                try:
                    # 检查心跳超时
                    if time.time() - node.last_heartbeat > self._heartbeat_timeout:
                        node.status = NodeStatus.UNHEALTHY
                        logger.warning(f"节点心跳超时: {node_id}")
                        continue

                    # HTTP健康检查
                    try:
                        response = requests.get(
                            f"http://{node.host}:{node.port}/health",
                            timeout=5
                        )
                        if response.status_code == 200:
                            node.status = NodeStatus.HEALTHY
                        else:
                            node.status = NodeStatus.UNHEALTHY
                    except requests.exceptions.RequestException:
                        node.status = NodeStatus.DOWN
                        logger.warning(f"节点不可达: {node_id}")

                except Exception as e:
                    logger.error(f"检查节点 {node_id} 失败: {str(e)}")

    def set_load_balance_strategy(self, strategy: LoadBalanceStrategy):
        """设置负载均衡策略"""
        self._strategy = strategy
        logger.info(f"负载均衡策略已设置为: {strategy.value}")

    def get_load_balance_strategy(self) -> LoadBalanceStrategy:
        """获取负载均衡策略"""
        return self._strategy

    @synchronized(resource='load_balancing', lock_type=LockType.READ)
    def select_node(self, client_ip: Optional[str] = None) -> Optional[ClusterNode]:
        """选择节点"""
        with self._nodes_lock:
            # 获取可用节点
            healthy_nodes = [n for n in self._nodes.values() 
                           if n.status in [NodeStatus.ACTIVE, NodeStatus.HEALTHY]]
            
            if not healthy_nodes:
                logger.warning("没有可用的健康节点")
                return None

            # 根据策略选择节点
            if self._strategy == LoadBalanceStrategy.ROUND_ROBIN:
                return self._select_round_robin(healthy_nodes)
            elif self._strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
                return self._select_least_connections(healthy_nodes)
            elif self._strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
                return self._select_weighted_round_robin(healthy_nodes)
            elif self._strategy == LoadBalanceStrategy.IP_HASH:
                return self._select_ip_hash(healthy_nodes, client_ip)
            else:
                return self._select_round_robin(healthy_nodes)

    def _select_round_robin(self, nodes: List[ClusterNode]) -> ClusterNode:
        """轮询策略"""
        node = nodes[self._round_robin_index % len(nodes)]
        self._round_robin_index += 1
        return node

    def _select_least_connections(self, nodes: List[ClusterNode]) -> ClusterNode:
        """最小连接数策略"""
        return min(nodes, key=lambda n: n.connections)

    def _select_weighted_round_robin(self, nodes: List[ClusterNode]) -> ClusterNode:
        """加权轮询策略"""
        total_weight = sum(n.weight for n in nodes)
        random_val = self._round_robin_index % total_weight
        self._round_robin_index += 1

        current = 0
        for node in nodes:
            current += node.weight
            if random_val < current:
                return node

        return nodes[0]

    def _select_ip_hash(self, nodes: List[ClusterNode], client_ip: str) -> ClusterNode:
        """IP哈希策略"""
        if not client_ip:
            return nodes[0]
        
        # 简单的IP哈希
        hash_val = sum(int(octet) for octet in client_ip.split('.') if octet.isdigit())
        return nodes[hash_val % len(nodes)]

    def get_cluster_stats(self) -> Dict:
        """获取集群统计"""
        with self._nodes_lock:
            total = len(self._nodes)
            active = sum(1 for n in self._nodes.values() 
                       if n.status in [NodeStatus.ACTIVE, NodeStatus.HEALTHY])
            unhealthy = sum(1 for n in self._nodes.values() if n.status == NodeStatus.UNHEALTHY)
            down = sum(1 for n in self._nodes.values() if n.status == NodeStatus.DOWN)
            total_connections = sum(n.connections for n in self._nodes.values())

            return {
                'total_nodes': total,
                'active_nodes': active,
                'unhealthy_nodes': unhealthy,
                'down_nodes': down,
                'total_connections': total_connections,
                'strategy': self._strategy.value,
                'nodes': [n.to_dict() for n in self._nodes.values()]
            }

    def promote_to_master(self, node_id: str) -> bool:
        """提升为主节点"""
        try:
            with self._nodes_lock:
                if node_id not in self._nodes:
                    return False

                # 将当前主节点降级
                for n in self._nodes.values():
                    if n.role == NodeRole.MASTER:
                        n.role = NodeRole.STANDBY
                        break

                # 提升指定节点
                self._nodes[node_id].role = NodeRole.MASTER
                self._nodes[node_id].status = NodeStatus.ACTIVE

            logger.info(f"节点 {node_id} 已提升为主节点")
            return True
        except Exception as e:
            logger.error(f"提升主节点失败: {str(e)}")
            return False

    def get_master_node(self) -> Optional[ClusterNode]:
        """获取主节点"""
        with self._nodes_lock:
            for node in self._nodes.values():
                if node.role == NodeRole.MASTER:
                    return node
            return None

    def replicate_to_slaves(self, data: Dict) -> Dict:
        """复制数据到从节点"""
        results = {}
        
        with self._nodes_lock:
            slaves = [n for n in self._nodes.values() if n.role == NodeRole.SLAVE]

        for slave in slaves:
            try:
                response = requests.post(
                    f"http://{slave.host}:{slave.port}/api/internal/replicate",
                    json=data,
                    timeout=10
                )
                results[slave.id] = {
                    'success': response.status_code == 200,
                    'status_code': response.status_code
                }
            except Exception as e:
                results[slave.id] = {
                    'success': False,
                    'error': str(e)
                }

        return results


# 创建全局实例
cluster_service = ClusterService()
