# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统业务拆分 + 分布式架构管理器 - 支持微服务拆分、服务发现、分布式协调
"""

import os
import time
import json
import hashlib
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('distributed_business')

class ServiceType(Enum):
    """服务类型"""
    API_GATEWAY = "api_gateway"          # API网关
    USER_SERVICE = "user_service"        # 用户服务
    EXAM_SERVICE = "exam_service"        # 考试服务
    QUESTION_SERVICE = "question_service" # 题库服务
    SEARCH_SERVICE = "search_service"    # 搜索服务
    CACHE_SERVICE = "cache_service"      # 缓存服务
    DATABASE_SERVICE = "database_service" # 数据库服务
    MESSAGE_SERVICE = "message_service"  # 消息服务
    SCHEDULE_SERVICE = "schedule_service" # 定时任务服务

class ServiceStatus(Enum):
    """服务状态"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    FAULTY = "faulty"

class BusinessModule:
    """业务模块"""
    
    def __init__(self, name: str, service_type: ServiceType, config: Dict = None):
        self.name = name
        self.service_type = service_type
        self.config = config or {}
        self.status = ServiceStatus.STOPPED
        self.instances = []
        self.dependencies = []
        
    def add_instance(self, instance: Dict):
        """添加服务实例"""
        self.instances.append(instance)
    
    def add_dependency(self, module_name: str):
        """添加依赖"""
        self.dependencies.append(module_name)
    
    def start(self):
        """启动模块"""
        self.status = ServiceStatus.STARTING
        # 模拟启动
        time.sleep(0.1)
        self.status = ServiceStatus.RUNNING
        logger.info(f"模块启动: {self.name}")
    
    def stop(self):
        """停止模块"""
        self.status = ServiceStatus.STOPPING
        time.sleep(0.1)
        self.status = ServiceStatus.STOPPED
        logger.info(f"模块停止: {self.name}")

class ServiceDiscovery:
    """服务发现"""
    
    def __init__(self):
        self.services = {}
        self.service_instances = {}
        self.heartbeat_interval = 30
    
    def register_service(self, service_name: str, instances: List[Dict]):
        """注册服务"""
        self.services[service_name] = {
            'registered_at': time.time(),
            'instances': instances
        }
        self.service_instances[service_name] = instances
        logger.info(f"服务注册: {service_name}, 实例数: {len(instances)}")
    
    def discover_service(self, service_name: str) -> Optional[List[Dict]]:
        """发现服务"""
        if service_name in self.service_instances:
            # 过滤健康实例
            return [inst for inst in self.service_instances[service_name] if inst.get('healthy', True)]
        return None
    
    def get_healthy_instances(self, service_name: str) -> List[Dict]:
        """获取健康实例"""
        instances = self.discover_service(service_name)
        if instances:
            return [inst for inst in instances if inst.get('status') == 'healthy']
        return []
    
    def update_instance_status(self, service_name: str, instance_id: str, status: str):
        """更新实例状态"""
        if service_name in self.service_instances:
            for inst in self.service_instances[service_name]:
                if inst.get('id') == instance_id:
                    inst['status'] = status
                    inst['last_heartbeat'] = time.time()
    
    def heartbeat(self, service_name: str, instance_id: str):
        """心跳上报"""
        self.update_instance_status(service_name, instance_id, 'healthy')

class APIGateway:
    """API网关"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.routes = {}
        self.service_discovery = ServiceDiscovery()
        self.middlewares = []
        
    def add_route(self, path: str, service_name: str, method: str = 'GET'):
        """添加路由"""
        key = f"{method}:{path}"
        self.routes[key] = service_name
        logger.info(f"添加路由: {method} {path} -> {service_name}")
    
    def route_request(self, method: str, path: str) -> Optional[str]:
        """路由请求"""
        key = f"{method}:{path}"
        if key in self.routes:
            return self.routes[key]
        
        # 尝试前缀匹配
        for route_key, service_name in self.routes.items():
            route_method, route_path = route_key.split(':', 1)
            if method == route_method and path.startswith(route_path):
                return service_name
        
        return None
    
    def forward_request(self, method: str, path: str, headers: Dict = None, body: bytes = None):
        """转发请求"""
        service_name = self.route_request(method, path)
        
        if not service_name:
            return 404, {}, b"Not Found"
        
        instances = self.service_discovery.get_healthy_instances(service_name)
        
        if not instances:
            return 503, {}, b"Service Unavailable"
        
        # 简单轮询选择
        instance = instances[0]
        
        try:
            import http.client
            conn = http.client.HTTPConnection(instance['host'], instance['port'])
            conn.request(method, path, body, headers or {})
            response = conn.getresponse()
            status = response.status
            response_headers = dict(response.getheaders())
            response_body = response.read()
            conn.close()
            
            return status, response_headers, response_body
        except Exception as e:
            logger.error(f"请求转发失败: {e}")
            return 500, {}, str(e).encode()

class DistributedBusinessManager:
    """分布式业务管理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        
        # 业务模块
        self.modules = self._init_modules()
        
        # API网关
        self.api_gateway = APIGateway()
        self._init_gateway_routes()
        
        # 服务发现
        self.service_discovery = self.api_gateway.service_discovery
        
        # 分布式协调
        self.coordination = DistributedCoordination()
        
        # 统计信息
        self.stats = {
            'services_started': 0,
            'services_stopped': 0,
            'requests_processed': 0,
            'errors': 0
        }
        
        logger.info("分布式业务管理器初始化完成")
    
    def _default_config(self) -> Dict:
        return {
            'environment': 'development',
            'service_discovery': {
                'enabled': True,
                'heartbeat_interval': 30
            },
            'api_gateway': {
                'host': 'localhost',
                'port': 8080
            },
            'modules': {
                'user_service': {'enabled': True, 'instances': 2},
                'exam_service': {'enabled': True, 'instances': 2},
                'question_service': {'enabled': True, 'instances': 1},
                'search_service': {'enabled': True, 'instances': 1},
                'cache_service': {'enabled': True, 'instances': 1},
                'database_service': {'enabled': True, 'instances': 1}
            }
        }
    
    def _init_modules(self) -> Dict[str, BusinessModule]:
        """初始化业务模块"""
        modules = {}
        
        # 用户服务
        modules['user_service'] = BusinessModule('user_service', ServiceType.USER_SERVICE, {
            'description': '用户管理服务',
            'port': 8001,
            'dependencies': ['database_service', 'cache_service']
        })
        modules['user_service'].add_instance({'id': 'user-1', 'host': 'localhost', 'port': 8001, 'status': 'healthy'})
        modules['user_service'].add_instance({'id': 'user-2', 'host': 'localhost', 'port': 8002, 'status': 'healthy'})
        
        # 考试服务
        modules['exam_service'] = BusinessModule('exam_service', ServiceType.EXAM_SERVICE, {
            'description': '考试管理服务',
            'port': 8003,
            'dependencies': ['database_service', 'question_service', 'cache_service']
        })
        modules['exam_service'].add_instance({'id': 'exam-1', 'host': 'localhost', 'port': 8003, 'status': 'healthy'})
        modules['exam_service'].add_instance({'id': 'exam-2', 'host': 'localhost', 'port': 8004, 'status': 'healthy'})
        
        # 题库服务
        modules['question_service'] = BusinessModule('question_service', ServiceType.QUESTION_SERVICE, {
            'description': '题库管理服务',
            'port': 8005,
            'dependencies': ['database_service', 'search_service']
        })
        modules['question_service'].add_instance({'id': 'question-1', 'host': 'localhost', 'port': 8005, 'status': 'healthy'})
        
        # 搜索服务
        modules['search_service'] = BusinessModule('search_service', ServiceType.SEARCH_SERVICE, {
            'description': '全文搜索服务',
            'port': 8006,
            'dependencies': []
        })
        modules['search_service'].add_instance({'id': 'search-1', 'host': 'localhost', 'port': 8006, 'status': 'healthy'})
        
        # 缓存服务
        modules['cache_service'] = BusinessModule('cache_service', ServiceType.CACHE_SERVICE, {
            'description': '分布式缓存服务',
            'port': 8007,
            'dependencies': []
        })
        modules['cache_service'].add_instance({'id': 'cache-1', 'host': 'localhost', 'port': 8007, 'status': 'healthy'})
        
        # 数据库服务
        modules['database_service'] = BusinessModule('database_service', ServiceType.DATABASE_SERVICE, {
            'description': '数据库服务',
            'port': 8008,
            'dependencies': []
        })
        modules['database_service'].add_instance({'id': 'db-1', 'host': 'localhost', 'port': 8008, 'status': 'healthy'})
        
        return modules
    
    def _init_gateway_routes(self):
        """初始化网关路由"""
        routes = [
            ('GET', '/api/users', 'user_service'),
            ('POST', '/api/users', 'user_service'),
            ('GET', '/api/users/<id>', 'user_service'),
            ('PUT', '/api/users/<id>', 'user_service'),
            ('DELETE', '/api/users/<id>', 'user_service'),
            
            ('GET', '/api/exams', 'exam_service'),
            ('POST', '/api/exams', 'exam_service'),
            ('GET', '/api/exams/<id>', 'exam_service'),
            ('PUT', '/api/exams/<id>', 'exam_service'),
            ('DELETE', '/api/exams/<id>', 'exam_service'),
            
            ('GET', '/api/questions', 'question_service'),
            ('POST', '/api/questions', 'question_service'),
            ('GET', '/api/questions/<id>', 'question_service'),
            ('PUT', '/api/questions/<id>', 'question_service'),
            ('DELETE', '/api/questions/<id>', 'question_service'),
            
            ('GET', '/api/search', 'search_service'),
            ('POST', '/api/search', 'search_service'),
            
            ('GET', '/api/cache', 'cache_service'),
            ('POST', '/api/cache', 'cache_service'),
            ('DELETE', '/api/cache/<key>', 'cache_service'),
            
            ('GET', '/api/health', 'database_service')
        ]
        
        for method, path, service in routes:
            self.api_gateway.add_route(path, service, method)
    
    def start_all(self):
        """启动所有服务"""
        for name, module in self.modules.items():
            module.start()
            # 注册服务到服务发现
            self.service_discovery.register_service(name, module.instances)
            self.stats['services_started'] += 1
        
        logger.info(f"已启动 {self.stats['services_started']} 个服务")
    
    def stop_all(self):
        """停止所有服务"""
        for name, module in self.modules.items():
            module.stop()
            self.stats['services_stopped'] += 1
        
        logger.info(f"已停止 {self.stats['services_stopped']} 个服务")
    
    def get_service_status(self, service_name: str) -> Optional[Dict]:
        """获取服务状态"""
        if service_name in self.modules:
            module = self.modules[service_name]
            return {
                'name': module.name,
                'type': module.service_type.value,
                'status': module.status.value,
                'instances': module.instances,
                'dependencies': module.dependencies
            }
        return None
    
    def get_all_services(self) -> Dict:
        """获取所有服务状态"""
        result = {}
        for name, module in self.modules.items():
            result[name] = {
                'name': module.name,
                'type': module.service_type.value,
                'status': module.status.value,
                'instance_count': len(module.instances),
                'dependencies': module.dependencies
            }
        return result
    
    def process_request(self, method: str, path: str, headers: Dict = None, body: bytes = None):
        """处理请求"""
        return self.api_gateway.forward_request(method, path, headers, body)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'services': {
                'started': self.stats['services_started'],
                'stopped': self.stats['services_stopped'],
                'total': len(self.modules)
            },
            'requests': {
                'processed': self.stats['requests_processed'],
                'errors': self.stats['errors']
            }
        }

class DistributedCoordination:
    """分布式协调"""
    
    def __init__(self):
        self.locks = {}
        self.leader = None
        self.election_in_progress = False
    
    def acquire_lock(self, resource: str, owner: str, timeout: int = 30) -> bool:
        """获取分布式锁"""
        if resource in self.locks:
            if time.time() - self.locks[resource]['acquired_at'] > timeout:
                # 锁已过期
                del self.locks[resource]
            else:
                return False
        
        self.locks[resource] = {
            'owner': owner,
            'acquired_at': time.time()
        }
        return True
    
    def release_lock(self, resource: str, owner: str) -> bool:
        """释放分布式锁"""
        if resource in self.locks and self.locks[resource]['owner'] == owner:
            del self.locks[resource]
            return True
        return False
    
    def elect_leader(self, candidates: List[str]) -> str:
        """选举领导者"""
        if self.election_in_progress:
            return self.leader or candidates[0]
        
        self.election_in_progress = True
        
        # 简单选举:选择第一个可用的
        self.leader = candidates[0] if candidates else None
        
        self.election_in_progress = False
        return self.leader

# 全局实例
distributed_manager = DistributedBusinessManager()

def get_distributed_manager() -> DistributedBusinessManager:
    """获取分布式业务管理器实例"""
    return distributed_manager

def start_all_services():
    """启动所有服务"""
    distributed_manager.start_all()

def stop_all_services():
    """停止所有服务"""
    distributed_manager.stop_all()

if __name__ == '__main__':
    print("🚀 分布式业务架构测试")
    print("=" * 70)
    
    manager = DistributedBusinessManager()
    
    print("\n📝 业务模块列表")
    services = manager.get_all_services()
    for name, info in services.items():
        status = "✅" if info['status'] == 'running' else "🔹"
        print(f"  {status} {name}: {info['type']}, 实例数: {info['instance_count']}")
    
    print("\n📝 启动所有服务")
    manager.start_all()
    
    services = manager.get_all_services()
    for name, info in services.items():
        status = "✅" if info['status'] == 'running' else "❌"
        print(f"  {status} {name}: {info['status']}")
    
    print("\n📝 服务路由")
    for route, service in manager.api_gateway.routes.items():
        method, path = route.split(':', 1)
        print(f"  {method:6s} {path} -> {service}")
    
    print("\n📝 服务发现测试")
    user_instances = manager.service_discovery.discover_service('user_service')
    print(f"  用户服务实例: {len(user_instances)}")
    
    print("\n📊 统计信息")
    stats = manager.get_stats()
    print(f"  启动服务: {stats['services']['started']}")
    print(f"  总服务数: {stats['services']['total']}")
    
    print("\n🎉 测试完成!")
