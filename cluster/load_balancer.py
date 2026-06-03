# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
负载均衡器 - 支持多种算法、健康检查、故障转移和性能监控
"""

import os
import json
import time
import threading
import socket
import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancingAlgorithm(Enum):
    """负载均衡算法枚举"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    RANDOM = "random"

class NodeStatus(Enum):
    """节点状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class LoadBalancer:
    """负载均衡器核心类"""
    
    def __init__(self, config_path: str = "cluster/config/load_balancer.json"):
        self.config = self._load_config(config_path)
        self.nodes = self._init_nodes()
        self.algorithm = LoadBalancingAlgorithm(self.config.get("algorithm", "round_robin"))
        self.running = False
        self.lock = threading.RLock()
        
        # 算法状态
        self.round_robin_index = 0
        self.connections: Dict[str, int] = {node['id']: 0 for node in self.nodes}
        
        # 健康检查配置
        self.health_check_enabled = self.config.get("health_check", {}).get("enabled", True)
        self.health_check_interval = self.config.get("health_check", {}).get("interval", 10)
        self.health_check_timeout = self.config.get("health_check", {}).get("timeout", 5)
        self.health_check_path = self.config.get("health_check", {}).get("path", "/health")
        
        # 性能指标
        self.metrics = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'start_time': datetime.now().isoformat()
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'listen_address': '0.0.0.0',
            'listen_port': 8080,
            'algorithm': 'round_robin',
            'nodes': [
                {'host': '127.0.0.1', 'port': 8443, 'weight': 1, 'id': 'node-master'},
                {'host': '127.0.0.1', 'port': 8444, 'weight': 1, 'id': 'node-worker-1'},
                {'host': '127.0.0.1', 'port': 8445, 'weight': 1, 'id': 'node-worker-2'}
            ],
            'health_check': {'enabled': True, 'interval': 10, 'timeout': 5, 'path': '/health'},
            'max_connections': 1000,
            'connection_timeout': 30
        }
    
    def _init_nodes(self) -> List[Dict]:
        """初始化节点列表"""
        nodes = []
        for i, node in enumerate(self.config['nodes']):
            nodes.append({
                'id': node.get('id', f'node-{i}'),
                'host': node['host'],
                'port': node['port'],
                'weight': node.get('weight', 1),
                'status': NodeStatus.HEALTHY.value,
                'connections': 0,
                'last_health_check': None,
                'health_score': 100
            })
        return nodes
    
    def start(self):
        """启动负载均衡器"""
        self.running = True
        logger.info("负载均衡器启动")
        
        if self.health_check_enabled:
            self._start_health_check()
        
        logger.info(f"负载均衡算法: {self.algorithm.value}")
        logger.info(f"节点数量: {len(self.nodes)}")
    
    def _start_health_check(self):
        """启动健康检查线程"""
        def check_health():
            while self.running:
                self._perform_health_check()
                time.sleep(self.health_check_interval)
        
        thread = threading.Thread(target=check_health, daemon=True)
        thread.start()
        logger.info("健康检查线程已启动")
    
    def _perform_health_check(self):
        """执行健康检查"""
        for node in self.nodes:
            try:
                # 简化的健康检查
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.health_check_timeout)
                result = sock.connect_ex((node['host'], node['port']))
                
                if result == 0:
                    node['status'] = NodeStatus.HEALTHY.value
                    node['health_score'] = 100
                    sock.close()
                else:
                    node['health_score'] = max(0, node['health_score'] - 20)
                    if node['health_score'] <= 0:
                        node['status'] = NodeStatus.UNHEALTHY.value
                    else:
                        node['status'] = NodeStatus.DEGRADED.value
            except Exception as e:
                node['status'] = NodeStatus.UNHEALTHY.value
                logger.error(f"节点 {node['id']} 健康检查失败: {e}")
            
            node['last_health_check'] = datetime.now().isoformat()
    
    def _get_healthy_nodes(self) -> List[Dict]:
        """获取健康节点列表"""
        return [node for node in self.nodes if node['status'] != NodeStatus.UNHEALTHY.value]
    
    def select_node(self, client_ip: str = None) -> Optional[Dict]:
        """选择节点"""
        healthy_nodes = self._get_healthy_nodes()
        
        if not healthy_nodes:
            logger.error("没有可用的健康节点")
            return None
        
        with self.lock:
            if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return self._round_robin(healthy_nodes)
            elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return self._least_connections(healthy_nodes)
            elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin(healthy_nodes)
            elif self.algorithm == LoadBalancingAlgorithm.IP_HASH:
                return self._ip_hash(healthy_nodes, client_ip)
            elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
                return self._random(healthy_nodes)
        
        return healthy_nodes[0]
    
    def _round_robin(self, nodes: List[Dict]) -> Dict:
        """轮询算法"""
        node = nodes[self.round_robin_index % len(nodes)]
        self.round_robin_index += 1
        return node
    
    def _least_connections(self, nodes: List[Dict]) -> Dict:
        """最小连接数算法"""
        return min(nodes, key=lambda n: n['connections'])
    
    def _weighted_round_robin(self, nodes: List[Dict]) -> Dict:
        """加权轮询算法"""
        total_weight = sum(node['weight'] for node in nodes)
        index = self.round_robin_index % total_weight
        
        cumulative = 0
        for node in nodes:
            cumulative += node['weight']
            if index < cumulative:
                self.round_robin_index += 1
                return node
        
        self.round_robin_index += 1
        return nodes[0]
    
    def _ip_hash(self, nodes: List[Dict], client_ip: str) -> Dict:
        """IP哈希算法"""
        if not client_ip:
            return nodes[0]
        
        hash_value = hash(client_ip)
        return nodes[hash_value % len(nodes)]
    
    def _random(self, nodes: List[Dict]) -> Dict:
        """随机算法"""
        import random
        return random.choice(nodes)
    
    def record_connection(self, node_id: str, connected: bool = True):
        """记录连接数"""
        with self.lock:
            if connected:
                self.connections[node_id] = self.connections.get(node_id, 0) + 1
            else:
                self.connections[node_id] = max(0, self.connections.get(node_id, 0) - 1)
    
    def record_request(self, success: bool, response_time: float = 0):
        """记录请求统计"""
        with self.lock:
            self.metrics['total_requests'] += 1
            if success:
                self.metrics['success_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            if response_time > 0:
                self.metrics['response_times'].append(response_time)
                if len(self.metrics['response_times']) > 1000:
                    self.metrics['response_times'].pop(0)
    
    def get_status(self) -> Dict:
        """获取负载均衡器状态"""
        avg_response_time = 0
        if self.metrics['response_times']:
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        
        return {
            'algorithm': self.algorithm.value,
            'status': 'running' if self.running else 'stopped',
            'nodes': self.nodes,
            'metrics': {
                'total_requests': self.metrics['total_requests'],
                'success_rate': self.metrics['success_requests'] / max(1, self.metrics['total_requests']) * 100,
                'avg_response_time_ms': avg_response_time * 1000,
                'uptime': self._calculate_uptime()
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_uptime(self) -> str:
        """计算运行时间"""
        start = datetime.fromisoformat(self.metrics['start_time'])
        delta = datetime.now() - start
        return str(delta).split('.')[0]
    
    def add_node(self, node_config: Dict):
        """添加节点"""
        with self.lock:
            self.nodes.append({
                'id': node_config.get('id', f'node-{len(self.nodes)}'),
                'host': node_config['host'],
                'port': node_config['port'],
                'weight': node_config.get('weight', 1),
                'status': NodeStatus.HEALTHY.value,
                'connections': 0,
                'last_health_check': None,
                'health_score': 100
            })
            self.connections[node_config.get('id', f'node-{len(self.nodes)-1}')] = 0
        logger.info(f"节点已添加: {node_config.get('id')}")
    
    def remove_node(self, node_id: str):
        """移除节点"""
        with self.lock:
            self.nodes = [node for node in self.nodes if node['id'] != node_id]
            if node_id in self.connections:
                del self.connections[node_id]
        logger.info(f"节点已移除: {node_id}")
    
    def set_algorithm(self, algorithm: str):
        """设置负载均衡算法"""
        try:
            self.algorithm = LoadBalancingAlgorithm(algorithm)
            logger.info(f"算法已切换为: {algorithm}")
            return True
        except ValueError:
            logger.error(f"无效的算法: {algorithm}")
            return False
    
    def stop(self):
        """停止负载均衡器"""
        self.running = False
        logger.info("负载均衡器已停止")

def get_load_balancer() -> LoadBalancer:
    """获取负载均衡器实例"""
    return LoadBalancer()

if __name__ == '__main__':
    lb = get_load_balancer()
    lb.start()
    
    print("负载均衡器已启动")
    print(f"算法: {lb.algorithm.value}")
    print(f"节点数: {len(lb.nodes)}")
    
    # 测试选择节点
    for i in range(10):
        node = lb.select_node(f'192.168.1.{i}')
        if node:
            print(f"请求 {i+1}: 分配到 {node['id']} ({node['host']}:{node['port']})")
        time.sleep(0.5)
    
    print("\n负载均衡器状态:")
    status = lb.get_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
