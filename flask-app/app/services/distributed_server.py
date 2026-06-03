#!/usr/bin/env python3
"""分布式服务器管理模块,用于管理客户端的子服务器,减轻主服务器负载"""

import time
import threading
import socket
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)

class DistributedServerManager:
    """分布式服务器管理器类"""

    def __init__(self):
        """初始化分布式服务器管理器"""
        self.is_running = False
        self.monitor_thread = None
        self.load_balancer_thread = None
        
        self.child_servers: Dict[str, Dict[str, Any]] = {}
        self.child_servers_lock = threading.RLock()
        
        self.heartbeat_interval = 30
        self.server_timeout = 60
        self.max_child_servers = 100
        
        self.config = {
            'heartbeat_interval': 30,
            'server_timeout': 60,
            'max_child_servers': 100,
            'load_balancing_strategy': 'round_robin',
            'health_check_interval': 10,
            'auto_retry_count': 3,
            'failover_threshold': 3
        }
        
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'active_connections': 0
        }
        
        self.health_checks = {}
        self.request_history = []
        self.algorithm_state = {
            'round_robin_index': 0
        }
        
        logger.info("分布式服务器管理器已初始化")

    def start(self):
        """启动分布式服务器管理器"""
        if self.is_running:
            logger.warning("分布式服务器管理器已经在运行中")
            return
        
        self.is_running = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("分布式服务器监控线程已启动")
        
        self.load_balancer_thread = threading.Thread(target=self._load_balancer_loop, daemon=True)
        self.load_balancer_thread.start()
        logger.info("分布式服务器负载均衡线程已启动")
        
        logger.info("分布式服务器管理器已启动")

    def stop(self):
        """停止分布式服务器管理器"""
        if not self.is_running:
            logger.warning("分布式服务器管理器已经停止")
            return
        
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            logger.info("分布式服务器监控线程已停止")
        
        if self.load_balancer_thread:
            self.load_balancer_thread.join(timeout=5)
            logger.info("分布式服务器负载均衡线程已停止")
        
        logger.info("分布式服务器管理器已停止")

    def _monitor_loop(self):
        """监控循环,定期检查服务器健康状态"""
        while self.is_running:
            try:
                self._check_server_health()
                self._cleanup_timeout_servers()
                time.sleep(self.config['health_check_interval'])
            except Exception as e:
                logger.error(f"分布式服务器监控循环异常: {str(e)}")

    def _load_balancer_loop(self):
        """负载均衡循环,定期更新服务器负载信息"""
        while self.is_running:
            try:
                self._update_server_load()
                time.sleep(5)
            except Exception as e:
                logger.error(f"负载均衡循环异常: {str(e)}")

    def _check_server_health(self):
        """检查所有服务器的健康状态"""
        with self.child_servers_lock:
            for server_id, server_info in list(self.child_servers.items()):
                if server_info['status'] == 'active':
                    health = self._perform_health_check(server_id)
                    server_info['last_health_check'] = time.time()
                    server_info['health_status'] = health
                    
                    if health != 'healthy':
                        server_info['health_fail_count'] = server_info.get('health_fail_count', 0) + 1
                        if server_info['health_fail_count'] >= self.config['failover_threshold']:
                            logger.warning(f"服务器 {server_id} 健康检查失败次数超过阈值,标记为不可用")
                            server_info['status'] = 'unavailable'
                            server_info['failover_time'] = time.time()
                elif server_info['status'] == 'unavailable':
                    if time.time() - server_info.get('failover_time', 0) > 120:
                        self._attempt_recovery(server_id)

    def _perform_health_check(self, server_id: str) -> str:
        """执行服务器健康检查"""
        server_info = self.child_servers.get(server_id)
        if not server_info:
            return 'unknown'
        
        host = server_info.get('host', '')
        port = server_info.get('port', 0)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return 'healthy'
            else:
                return 'unhealthy'
        except Exception as e:
            logger.debug(f"健康检查失败 {server_id}: {str(e)}")
            return 'unhealthy'

    def _cleanup_timeout_servers(self):
        """清理超时的服务器"""
        current_time = time.time()
        with self.child_servers_lock:
            timeout_servers = []
            for server_id, server_info in self.child_servers.items():
                last_heartbeat = server_info.get('last_heartbeat', 0)
                if current_time - last_heartbeat > self.config['server_timeout']:
                    timeout_servers.append(server_id)
            
            for server_id in timeout_servers:
                logger.warning(f"服务器 {server_id} 心跳超时,自动注销")
                self.unregister_server(server_id)

    def _update_server_load(self):
        """更新服务器负载信息"""
        with self.child_servers_lock:
            for server_id, server_info in self.child_servers.items():
                if server_info['status'] == 'active':
                    server_info['current_load'] = self._calculate_server_load(server_info)

    def _calculate_server_load(self, server_info: Dict[str, Any]) -> float:
        """计算服务器负载"""
        cpu_usage = server_info.get('cpu_usage', 0)
        memory_usage = server_info.get('memory_usage', 0)
        active_requests = server_info.get('active_requests', 0)
        max_requests = server_info.get('max_requests', 100)
        
        cpu_weight = 0.4
        memory_weight = 0.3
        request_weight = 0.3
        
        normalized_request_load = min(active_requests / max_requests, 1.0) if max_requests > 0 else 0
        
        return (cpu_weight * cpu_usage + 
                memory_weight * memory_usage + 
                request_weight * normalized_request_load * 100)

    def _attempt_recovery(self, server_id: str):
        """尝试恢复故障服务器"""
        server_info = self.child_servers.get(server_id)
        if not server_info:
            return
        
        health = self._perform_health_check(server_id)
        if health == 'healthy':
            logger.info(f"服务器 {server_id} 恢复健康,重新激活")
            server_info['status'] = 'active'
            server_info['health_fail_count'] = 0
            server_info['last_heartbeat'] = time.time()

    def register_server(self, server_id: str, server_info: Dict[str, Any]):
        """注册子服务器"""
        with self.child_servers_lock:
            if len(self.child_servers) >= self.config['max_child_servers']:
                logger.error(f"无法注册服务器 {server_id}: 已达到最大服务器数量限制")
                return False
            
            self.child_servers[server_id] = {
                **server_info,
                'server_id': server_id,
                'last_heartbeat': time.time(),
                'status': 'active',
                'health_status': 'healthy',
                'health_fail_count': 0,
                'current_load': 0.0,
                'active_requests': 0,
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0.0,
                'registered_at': datetime.now().isoformat()
            }
        
        logger.info(f"子服务器 {server_id} 已注册")
        return True

    def unregister_server(self, server_id: str):
        """注销子服务器"""
        with self.child_servers_lock:
            if server_id in self.child_servers:
                del self.child_servers[server_id]
        
        logger.info(f"子服务器 {server_id} 已注销")

    def update_heartbeat(self, server_id: str):
        """更新服务器心跳"""
        with self.child_servers_lock:
            if server_id in self.child_servers:
                self.child_servers[server_id]['last_heartbeat'] = time.time()
                self.child_servers[server_id]['status'] = 'active'
                self.child_servers[server_id]['health_fail_count'] = 0
                return True
        return False

    def get_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """获取服务器状态"""
        with self.child_servers_lock:
            return self.child_servers.get(server_id)

    def get_all_servers(self) -> Dict[str, Any]:
        """获取所有服务器"""
        with self.child_servers_lock:
            return self.child_servers.copy()

    def get_active_servers(self) -> List[Dict[str, Any]]:
        """获取所有活跃服务器"""
        with self.child_servers_lock:
            return [info for info in self.child_servers.values() 
                    if info['status'] == 'active' and info['health_status'] == 'healthy']

    def select_server(self, strategy: str = None) -> Optional[str]:
        """根据负载均衡策略选择服务器"""
        strategy = strategy or self.config['load_balancing_strategy']
        active_servers = self.get_active_servers()
        
        if not active_servers:
            logger.warning("没有可用的活跃服务器")
            return None
        
        if strategy == 'round_robin':
            return self._select_round_robin(active_servers)
        elif strategy == 'least_load':
            return self._select_least_load(active_servers)
        elif strategy == 'random':
            return self._select_random(active_servers)
        elif strategy == 'ip_hash':
            return self._select_ip_hash(active_servers)
        else:
            return self._select_round_robin(active_servers)

    def _select_round_robin(self, servers: List[Dict[str, Any]]) -> str:
        """轮询策略选择服务器"""
        server_ids = [s['server_id'] for s in servers]
        index = self.algorithm_state['round_robin_index'] % len(server_ids)
        self.algorithm_state['round_robin_index'] += 1
        return server_ids[index]

    def _select_least_load(self, servers: List[Dict[str, Any]]) -> str:
        """最小负载策略选择服务器"""
        min_load = float('inf')
        selected_server = None
        
        for server in servers:
            load = server.get('current_load', float('inf'))
            if load < min_load:
                min_load = load
                selected_server = server['server_id']
        
        return selected_server

    def _select_random(self, servers: List[Dict[str, Any]]) -> str:
        """随机策略选择服务器"""
        import random
        server_ids = [s['server_id'] for s in servers]
        return random.choice(server_ids)

    def _select_ip_hash(self, servers: List[Dict[str, Any]]) -> str:
        """IP哈希策略选择服务器"""
        import hashlib
        
        client_ip = self._get_client_ip()
        server_ids = sorted([s['server_id'] for s in servers])
        
        if client_ip:
            hash_val = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
            index = hash_val % len(server_ids)
            return server_ids[index]
        
        return self._select_round_robin(servers)

    def _get_client_ip(self) -> Optional[str]:
        """获取客户端IP(需要在Web请求上下文中使用)"""
        return None

    def distribute_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """分发请求到子服务器"""
        server_id = self.select_server()
        
        if not server_id:
            return {
                'success': False,
                'error': '没有可用的服务器',
                'timestamp': datetime.now().isoformat()
            }
        
        server_info = self.get_server_status(server_id)
        if not server_info:
            return {
                'success': False,
                'error': '服务器信息不存在',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            with self.child_servers_lock:
                if server_id in self.child_servers:
                    self.child_servers[server_id]['active_requests'] += 1
                    self.child_servers[server_id]['total_requests'] += 1
            
            response = self._forward_request(server_id, server_info, request_data)
            
            with self.child_servers_lock:
                if server_id in self.child_servers:
                    self.child_servers[server_id]['active_requests'] -= 1
                    if response.get('success', False):
                        self.child_servers[server_id]['successful_requests'] += 1
                    else:
                        self.child_servers[server_id]['failed_requests'] += 1
            
            self.stats['total_requests'] += 1
            if response.get('success', False):
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
            
            return response
        except Exception as e:
            logger.error(f"请求分发失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'server_id': server_id,
                'timestamp': datetime.now().isoformat()
            }

    def _forward_request(self, server_id: str, server_info: Dict[str, Any], 
                        request_data: Dict[str, Any]) -> Dict[str, Any]:
        """转发请求到子服务器"""
        host = server_info.get('host', '')
        port = server_info.get('port', 0)
        
        try:
            import requests
            
            url = f"http://{host}:{port}/api/handle_request"
            response = requests.post(url, json=request_data, timeout=30)
            
            return {
                'success': True,
                'server_id': server_id,
                'response': response.json(),
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'server_id': server_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_server_stats(self, server_id: str = None) -> Dict[str, Any]:
        """获取服务器统计信息"""
        if server_id:
            server_info = self.get_server_status(server_id)
            if server_info:
                return {
                    'server_id': server_id,
                    'status': server_info.get('status'),
                    'health_status': server_info.get('health_status'),
                    'current_load': server_info.get('current_load'),
                    'total_requests': server_info.get('total_requests'),
                    'successful_requests': server_info.get('successful_requests'),
                    'failed_requests': server_info.get('failed_requests'),
                    'avg_response_time': server_info.get('avg_response_time'),
                    'registered_at': server_info.get('registered_at')
                }
            return {'error': '服务器不存在'}
        
        return self.stats

    def set_load_balancing_strategy(self, strategy: str):
        """设置负载均衡策略"""
        valid_strategies = ['round_robin', 'least_load', 'random', 'ip_hash']
        if strategy in valid_strategies:
            self.config['load_balancing_strategy'] = strategy
            logger.info(f"负载均衡策略已更改为: {strategy}")
            return True
        return False

    def get_load_balancing_strategy(self) -> str:
        """获取当前负载均衡策略"""
        return self.config['load_balancing_strategy']

    def set_config(self, config: Dict[str, Any]):
        """更新配置"""
        with self.child_servers_lock:
            self.config.update(config)
            logger.info(f"分布式服务器配置已更新: {config}")

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()

    def get_system_status(self) -> Dict[str, Any]:
        """获取分布式系统状态"""
        active_count = len(self.get_active_servers())
        total_count = len(self.get_all_servers())
        
        return {
            'is_running': self.is_running,
            'total_servers': total_count,
            'active_servers': active_count,
            'config': self.get_config(),
            'stats': self.stats.copy(),
            'load_balancing_strategy': self.get_load_balancing_strategy(),
            'timestamp': datetime.now().isoformat()
        }

    def scale_up(self, count: int = 1):
        """增加服务器数量(预留接口)"""
        logger.info(f"请求扩展 {count} 台服务器")
        return {'success': True, 'message': f"已请求扩展 {count} 台服务器"}

    def scale_down(self, count: int = 1):
        """减少服务器数量(预留接口)"""
        logger.info(f"请求缩减 {count} 台服务器")
        return {'success': True, 'message': f"已请求缩减 {count} 台服务器"}

    def __str__(self):
        return f"DistributedServerManager(is_running={self.is_running}, servers={len(self.child_servers)})"

    def __repr__(self):
        return self.__str__()

distributed_server_manager = DistributedServerManager()

def get_distributed_server_manager() -> DistributedServerManager:
    """获取分布式服务器管理器实例"""
    return distributed_server_manager