# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务中枢 - 企业级AI服务管理平台
提供统一的服务注册、发现、编排、监控和故障转移
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Dict
from datetime import datetime
from collections import defaultdict, deque
from enum import Enum
import json
import sys

logger = logging.getLogger('ai_service_hub')


class ServiceStatus(Enum):
    """服务状态枚举"""
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"


class EventType(Enum):
    """事件类型枚举"""
    SERVICE_REGISTERED = "service.registered"
    SERVICE_UNREGISTERED = "service.unregistered"
    SERVICE_HEALTHY = "service.healthy"
    SERVICE_FAILED = "service.failed"
    SERVICE_DEPENDENCY_MET = "service.dependency_met"
    COMMAND_EXECUTED = "command.executed"
    ERROR_OCCURRED = "error.occurred"


class Event:
    """事件对象"""
    def __init__(self, event_type: EventType, source: str, data: Any):
        self.event_type = event_type
        self.source = source
        self.data = data
        self.timestamp = datetime.now().isoformat()
        self.id = f"{event_type.value}_{time.time()}"

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.event_type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp
        }


class EventBus:
    """事件总线 - 服务间通信"""

    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_history = deque(maxlen=1000)
        self.lock = threading.Lock()

    def subscribe(self, event_type: EventType, callback: Callable):
        """订阅事件"""
        with self.lock:
            self.subscribers[event_type.value].append(callback)
            logger.info(f"订阅事件: {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """取消订阅"""
        with self.lock:
            if event_type.value in self.subscribers:
                self.subscribers[event_type.value].remove(callback)

    def publish(self, event: Event):
        """发布事件"""
        with self.lock:
            self.event_history.append(event)

        callbacks = self.subscribers.get(event.event_type.value, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {str(e)}")

    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取事件历史"""
        events = list(self.event_history)[-limit:]
        return [e.to_dict() for e in events]


class ServiceInfo:
    """服务信息"""
    def __init__(self, name: str, service: Any, dependencies: List[str] = None):
        self.name = name
        self.service = service
        self.dependencies = dependencies or []
        self.status = ServiceStatus.INITIALIZING
        self.health_score = 100
        self.last_health_check = time.time()
        self.consecutive_failures = 0
        self.total_requests = 0
        self.failed_requests = 0
        self.registered_at = datetime.now().isoformat()
        self.metadata = {}

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'health_score': self.health_score,
            'dependencies': self.dependencies,
            'last_health_check': self.last_health_check,
            'registered_at': self.registered_at,
            'metrics': {
                'total_requests': self.total_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (self.total_requests - self.failed_requests) / max(self.total_requests, 1) * 100
            },
            'metadata': self.metadata
        }

    def record_request(self, success: bool):
        """记录请求"""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1


class AIServiceHub:
    """AI服务中枢 - 企业级AI服务管理平台"""

    def __init__(self):
        """初始化AI服务中枢"""
        self.services = {}
        self.service_metadata = {}
        self.event_bus = EventBus()
        self.dependency_graph = defaultdict(list)
        self.command_cache = {}
        self.cache_ttl = 300
        self.lock = threading.Lock()

        self.config = {
            'health_check_interval': 30,
            'max_consecutive_failures': 3,
            'auto_restart_enabled': True,
            'dependency_check_enabled': True,
            'cache_enabled': True,
            'event_history_enabled': True
        }

        self.health_check_thread = None
        self.running = False

        self._initialize_services()
        self._start_health_check()

        logger.info("AI服务中枢初始化完成")

    def _initialize_services(self):
        """初始化所有AI服务"""
        service_configs = [
            {
                'name': 'management',
                'module': 'app.ai.ai_management_system',
                'instance': 'ai_management_system',
                'dependencies': []
            },
            {
                'name': 'learning',
                'module': 'app.ai.self_learning_system',
                'instance': 'ai_self_learning_system',
                'dependencies': ['management']
            },
            {
                'name': 'monitoring',
                'module': 'app.ai.monitoring',
                'instance': 'ai_monitor',
                'dependencies': ['management']
            },
            {
                'name': 'engineer',
                'module': 'app.ai.engineer_ai',
                'instance': 'engineer_ai_instance',
                'dependencies': ['monitoring']
            }
        ]

        for config in service_configs:
            try:
                module = __import__(config['module'], fromlist=[config['instance']])
                service_instance = getattr(module, config['instance'])

                self.register_service(
                    name=config['name'],
                    service=service_instance,
                    dependencies=config['dependencies'],
                    metadata={'config': config}
                )

                logger.info(f"服务 {config['name']} 初始化成功")
            except Exception as e:
                logger.error(f"初始化服务 {config['name']} 失败: {str(e)}")

    def register_service(self, name: str, service: Any, dependencies: List[str] = None, metadata: Dict = None):
        """注册服务"""
        with self.lock:
            if name in self.services:
                logger.warning(f"服务 {name} 已存在,将被替换")

            service_info = ServiceInfo(name, service, dependencies or [])
            if metadata:
                service_info.metadata.update(metadata)

            self.services[name] = service_info
            self.service_metadata[name] = metadata or {}

            if dependencies:
                for dep in dependencies:
                    self.dependency_graph[dep].append(name)

            self.event_bus.publish(Event(
                EventType.SERVICE_REGISTERED,
                name,
                {'dependencies': dependencies, 'metadata': metadata}
            ))

            logger.info(f"服务 {name} 注册成功,依赖: {dependencies}")

    def unregister_service(self, name: str):
        """注销服务"""
        with self.lock:
            if name not in self.services:
                logger.warning(f"服务 {name} 不存在")
                return False

            del self.services[name]
            if name in self.service_metadata:
                del self.service_metadata[name]

            for dependents in self.dependency_graph.values():
                if name in dependents:
                    dependents.remove(name)

            self.event_bus.publish(Event(
                EventType.SERVICE_UNREGISTERED,
                name,
                {}
            ))

            logger.info(f"服务 {name} 已注销")
            return True

    def get_service(self, service_name: str, auto_create: bool = False) -> Optional[Any]:
        """获取服务实例"""
        if service_name not in self.services:
            if auto_create:
                return self._create_service_instance(service_name)
            return None

        service_info = self.services[service_name]
        if service_info.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
            return service_info.service

        return None

    def _create_service_instance(self, service_name: str) -> Optional[Any]:
        """创建服务实例"""
        logger.info(f"尝试动态创建服务: {service_name}")
        return None

    def list_services(self, status: ServiceStatus = None) -> List[Dict]:
        """列出所有服务"""
        with self.lock:
            services = []
            for name, info in self.services.items():
                if status is None or info.status == status:
                    services.append(info.to_dict())
            return services

    def get_service_status(self, service_name: str) -> Optional[Dict]:
        """获取服务状态"""
        if service_name not in self.services:
            return None
        return self.services[service_name].to_dict()

    def get_all_status(self) -> Dict[str, Any]:
        """获取所有服务状态"""
        status = {
            'hub': {
                'status': 'running',
                'services_count': len(self.services),
                'timestamp': datetime.now().isoformat()
            },
            'services': {},
            'summary': {
                'healthy': 0,
                'degraded': 0,
                'failed': 0,
                'total': len(self.services)
            }
        }

        for name, info in self.services.items():
            service_status = info.to_dict()
            status['services'][name] = service_status

            if info.status == ServiceStatus.HEALTHY:
                status['summary']['healthy'] += 1
            elif info.status == ServiceStatus.DEGRADED:
                status['summary']['degraded'] += 1
            elif info.status == ServiceStatus.FAILED:
                status['summary']['failed'] += 1

        return status

    def check_dependencies(self, service_name: str) -> Dict[str, Any]:
        """检查服务依赖"""
        if service_name not in self.services:
            return {'error': f'服务 {service_name} 不存在'}

        info = self.services[service_name]
        dependency_status = {}

        for dep in info.dependencies:
            if dep in self.services:
                dep_info = self.services[dep]
                dependency_status[dep] = {
                    'status': dep_info.status.value,
                    'healthy': dep_info.status == ServiceStatus.HEALTHY
                }
            else:
                dependency_status[dep] = {
                    'status': 'missing',
                    'healthy': False
                }

        all_healthy = all(d['healthy'] for d in dependency_status.values())

        return {
            'service': service_name,
            'dependencies': dependency_status,
            'all_dependencies_met': all_healthy
        }

    def execute_command(self, service_name: str, command: str, **kwargs) -> Any:
        """执行服务命令(带缓存和监控)"""
        cache_key = f"{service_name}:{command}:{json.dumps(kwargs, sort_keys=True)}"

        if self.config['cache_enabled'] and cache_key in self.command_cache:
            cached_item = self.command_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                logger.debug(f"从缓存返回: {cache_key}")
                return cached_item['result']

        service = self.get_service(service_name)
        if not service:
            return {'error': f'服务 {service_name} 不可用或未注册'}

        try:
            if hasattr(service, command):
                method = getattr(service, command)
                result = method(**kwargs)

                self.command_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }

                if service_name in self.services:
                    self.services[service_name].record_request(True)

                self.event_bus.publish(Event(
                    EventType.COMMAND_EXECUTED,
                    service_name,
                    {'command': command, 'success': True}
                ))

                return result
            else:
                return {'error': f'服务 {service_name} 没有命令 {command}'}

        except Exception as e:
            if service_name in self.services:
                self.services[service_name].record_request(False)

            self.event_bus.publish(Event(
                EventType.ERROR_OCCURRED,
                service_name,
                {'command': command, 'error': str(e)}
            ))

            logger.error(f"执行命令失败: {service_name}.{command} - {str(e)}")
            return {'error': str(e)}

    def execute_workflow(self, workflow: List[Dict]) -> Dict[str, Any]:
        """执行服务工作流"""
        results = {}
        for step in workflow:
            service_name = step.get('service')
            command = step.get('command')
            params = step.get('params', {})

            result = self.execute_command(service_name, command, **params)
            results[f"{service_name}.{command}"] = result

            if 'error' in result and step.get('required', True):
                return {
                    'success': False,
                    'failed_at': f"{service_name}.{command}",
                    'error': result['error'],
                    'partial_results': results
                }

        return {
            'success': True,
            'results': results
        }

    def _health_check(self):
        """健康检查"""
        with self.lock:
            for name, info in self.services.items():
                try:
                    has_get_status = hasattr(info.service, 'get_status')
                    has_get_metrics = hasattr(info.service, 'get_metrics')
                    has_get_system_status = hasattr(info.service, 'get_system_status')

                    is_healthy = has_get_status or has_get_metrics or has_get_system_status

                    if is_healthy:
                        if info.consecutive_failures > 0:
                            info.consecutive_failures = 0
                        info.status = ServiceStatus.HEALTHY
                        info.health_score = min(100, info.health_score + 10)

                        self.event_bus.publish(Event(
                            EventType.SERVICE_HEALTHY,
                            name,
                            {'health_score': info.health_score}
                        ))
                    else:
                        info.consecutive_failures += 1
                        if info.consecutive_failures >= self.config['max_consecutive_failures']:
                            info.status = ServiceStatus.FAILED
                            info.health_score = max(0, info.health_score - 20)

                            self.event_bus.publish(Event(
                                EventType.SERVICE_FAILED,
                                name,
                                {'failures': info.consecutive_failures}
                            ))

                    info.last_health_check = time.time()

                except Exception as e:
                    logger.error(f"健康检查失败 {name}: {str(e)}")
                    info.consecutive_failures += 1
                    if info.consecutive_failures >= self.config['max_consecutive_failures']:
                        info.status = ServiceStatus.FAILED

    def _start_health_check(self):
        """启动健康检查线程"""
        if self.running:
            return

        self.running = True

        def health_check_loop():
            while self.running:
                try:
                    self._health_check()
                    time.sleep(self.config['health_check_interval'])
                except Exception as e:
                    logger.error(f"健康检查线程错误: {str(e)}")

        self.health_check_thread = threading.Thread(
            target=health_check_loop,
            daemon=True,
            name="AI-Hub-HealthCheck"
        )
        self.health_check_thread.start()
        logger.info("健康检查线程已启动")

    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        if service_name not in self.services:
            logger.error(f"服务 {service_name} 不存在")
            return False

        try:
            info = self.services[service_name]
            info.status = ServiceStatus.INITIALIZING

            if hasattr(info.service, 'initialize'):
                info.service.initialize()
            elif hasattr(info.service, 'start'):
                info.service.start()

            info.consecutive_failures = 0
            info.status = ServiceStatus.HEALTHY

            logger.info(f"服务 {service_name} 重启成功")
            return True

        except Exception as e:
            logger.error(f"重启服务 {service_name} 失败: {str(e)}")
            return False

    def subscribe_to_events(self, event_type: EventType, callback: Callable):
        """订阅事件"""
        self.event_bus.subscribe(event_type, callback)

    def unsubscribe_from_events(self, event_type: EventType, callback: Callable):
        """取消订阅事件"""
        self.event_bus.unsubscribe(event_type, callback)

    def get_event_history(self, limit: int = 100) -> List[Dict]:
        """获取事件历史"""
        return self.event_bus.get_history(limit)

    def update_config(self, config: Dict):
        """更新配置"""
        self.config.update(config)
        logger.info(f"AI服务中枢配置已更新: {config}")

    def clear_cache(self):
        """清除命令缓存"""
        self.command_cache.clear()
        logger.info("命令缓存已清除")

    def get_dashboard(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'hub_status': {
                'running': self.running,
                'services_count': len(self.services),
                'config': self.config
            },
            'services': self.list_services(),
            'status': self.get_all_status(),
            'recent_events': self.get_event_history(20)
        }

    def shutdown(self):
        """关闭AI服务中枢"""
        logger.info("正在关闭AI服务中枢...")
        self.running = False

        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)

        for name in list(self.services.keys()):
            self.unregister_service(name)

        self.clear_cache()
        logger.info("AI服务中枢已关闭")


ai_service_hub = AIServiceHub()
