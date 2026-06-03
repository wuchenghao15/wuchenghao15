# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微服务架构管理器 - 支持服务注册发现、RPC通信、配置中心、服务监控
"""

import os
import time
import json
import hashlib
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('microservices')

class ServiceStatus(Enum):
    """服务状态"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    FAULTY = "faulty"

class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        self.services = {}
        self.service_instances = {}
        self.heartbeat_timeout = 60
    
    def register(self, service_name: str, instance: Dict):
        """注册服务实例"""
        if service_name not in self.services:
            self.services[service_name] = {
                'registered_at': time.time(),
                'version': instance.get('version', '1.0.0')
            }
            self.service_instances[service_name] = []
        
        instance['last_heartbeat'] = time.time()
        instance['status'] = 'healthy'
        
        # 检查是否已存在
        existing = next((i for i in self.service_instances[service_name] 
                        if i['id'] == instance['id']), None)
        if existing:
            existing.update(instance)
        else:
            self.service_instances[service_name].append(instance)
        
        logger.info(f"服务注册: {service_name} - {instance['id']}")
    
    def deregister(self, service_name: str, instance_id: str):
        """注销服务实例"""
        if service_name in self.service_instances:
            self.service_instances[service_name] = [
                i for i in self.service_instances[service_name] 
                if i['id'] != instance_id
            ]
            logger.info(f"服务注销: {service_name} - {instance_id}")
    
    def discover(self, service_name: str) -> List[Dict]:
        """发现服务实例"""
        if service_name not in self.service_instances:
            return []
        
        # 过滤不健康实例
        now = time.time()
        healthy_instances = []
        
        for instance in self.service_instances[service_name]:
            if now - instance.get('last_heartbeat', 0) < self.heartbeat_timeout:
                healthy_instances.append(instance)
            else:
                instance['status'] = 'unhealthy'
        
        return healthy_instances
    
    def heartbeat(self, service_name: str, instance_id: str):
        """心跳上报"""
        if service_name in self.service_instances:
            for instance in self.service_instances[service_name]:
                if instance['id'] == instance_id:
                    instance['last_heartbeat'] = time.time()
                    instance['status'] = 'healthy'
    
    def get_all_services(self) -> List[str]:
        """获取所有服务名称"""
        return list(self.services.keys())

class RPCFramework:
    """RPC框架"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self.timeout = 30
    
    def call(self, service_name: str, method: str, params: Dict = None) -> Any:
        """调用远程服务方法"""
        instances = self.registry.discover(service_name)
        
        if not instances:
            raise Exception(f"服务不可用: {service_name}")
        
        # 简单轮询
        instance = instances[0]
        
        try:
            import http.client
            conn = http.client.HTTPConnection(instance['host'], instance['port'], timeout=self.timeout)
            
            request_data = json.dumps({
                'method': method,
                'params': params or {}
            })
            
            conn.request('POST', '/rpc', request_data, {'Content-Type': 'application/json'})
            response = conn.getresponse()
            
            if response.status == 200:
                result = json.loads(response.read().decode())
                conn.close()
                return result.get('result')
            else:
                conn.close()
                raise Exception(f"RPC调用失败: {response.status}")
        
        except Exception as e:
            logger.error(f"RPC调用失败 [{service_name}]: {e}")
            raise
    
    def register_service(self, service_name: str, host: str, port: int, version: str = '1.0.0'):
        """注册RPC服务"""
        instance = {
            'id': f"{service_name}_{host}:{port}",
            'host': host,
            'port': port,
            'version': version,
            'last_heartbeat': time.time(),
            'status': 'healthy'
        }
        self.registry.register(service_name, instance)
    
    def start_heartbeat(self, service_name: str, instance_id: str, interval: int = 30):
        """启动心跳线程"""
        def heartbeat_loop():
            while True:
                self.registry.heartbeat(service_name, instance_id)
                time.sleep(interval)
        
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()

class ConfigCenter:
    """配置中心"""
    
    def __init__(self):
        self.configs = {}
        self.watchers = {}
    
    def set_config(self, key: str, value: Any, namespace: str = 'default'):
        """设置配置"""
        if namespace not in self.configs:
            self.configs[namespace] = {}
        
        old_value = self.configs[namespace].get(key)
        self.configs[namespace][key] = value
        
        # 通知监听器
        self._notify_watchers(namespace, key, value, old_value)
        
        logger.info(f"配置更新: {namespace}/{key}")
    
    def get_config(self, key: str, namespace: str = 'default', default=None) -> Any:
        """获取配置"""
        return self.configs.get(namespace, {}).get(key, default)
    
    def get_namespace_configs(self, namespace: str) -> Dict:
        """获取命名空间所有配置"""
        return self.configs.get(namespace, {})
    
    def watch(self, key: str, callback: Callable, namespace: str = 'default'):
        """监听配置变化"""
        if namespace not in self.watchers:
            self.watchers[namespace] = {}
        
        if key not in self.watchers[namespace]:
            self.watchers[namespace][key] = []
        
        self.watchers[namespace][key].append(callback)
    
    def _notify_watchers(self, namespace: str, key: str, new_value, old_value):
        """通知配置监听器"""
        if namespace in self.watchers and key in self.watchers[namespace]:
            for callback in self.watchers[namespace][key]:
                try:
                    callback(key, new_value, old_value)
                except Exception as e:
                    logger.error(f"配置监听器执行失败: {e}")

class ServiceMonitor:
    """服务监控"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def record_metric(self, service_name: str, metric_name: str, value: float):
        """记录指标"""
        if service_name not in self.metrics:
            self.metrics[service_name] = {}
        
        if metric_name not in self.metrics[service_name]:
            self.metrics[service_name][metric_name] = []
        
        self.metrics[service_name][metric_name].append({
            'timestamp': time.time(),
            'value': value
        })
        
        # 保留最近100条记录
        if len(self.metrics[service_name][metric_name]) > 100:
            self.metrics[service_name][metric_name].pop(0)
    
    def get_metrics(self, service_name: str) -> Dict:
        """获取服务指标"""
        return self.metrics.get(service_name, {})
    
    def check_alert(self, service_name: str, metric_name: str, threshold: float, operator: str = '>'):
        """检查告警条件"""
        if service_name not in self.metrics or metric_name not in self.metrics[service_name]:
            return False
        
        latest = self.metrics[service_name][metric_name][-1]['value']
        
        if operator == '>' and latest > threshold:
            alert = {
                'timestamp': time.time(),
                'service': service_name,
                'metric': metric_name,
                'value': latest,
                'threshold': threshold,
                'operator': operator,
                'message': f"{service_name} {metric_name} {operator} {threshold}"
            }
            self.alerts.append(alert)
            return True
        
        return False
    
    def get_alerts(self) -> List[Dict]:
        """获取所有告警"""
        return self.alerts
    
    def clear_alerts(self):
        """清除告警"""
        self.alerts.clear()

class MicroservicesManager:
    """微服务架构管理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        
        # 核心组件
        self.registry = ServiceRegistry()
        self.rpc = RPCFramework()
        self.config_center = ConfigCenter()
        self.monitor = ServiceMonitor()
        
        # 微服务列表
        self.services = self._init_services()
        
        # 初始化配置
        self._init_default_configs()
        
        logger.info("微服务架构管理器初始化完成")
    
    def _default_config(self) -> Dict:
        return {
            'environment': 'development',
            'registry': {
                'heartbeat_timeout': 60,
                'cleanup_interval': 300
            },
            'rpc': {
                'timeout': 30,
                'retries': 3
            },
            'config_center': {
                'watch_enabled': True
            },
            'monitor': {
                'enabled': True,
                'alert_thresholds': {
                    'response_time': 500,
                    'error_rate': 0.1,
                    'cpu_usage': 80
                }
            }
        }
    
    def _init_services(self) -> Dict:
        """初始化微服务"""
        services = {}
        
        # 用户服务
        services['user-service'] = {
            'name': 'user-service',
            'description': '用户管理服务',
            'host': 'localhost',
            'port': 9001,
            'version': '1.0.0',
            'status': ServiceStatus.STOPPED,
            'methods': ['get_user', 'create_user', 'update_user', 'delete_user']
        }
        
        # 考试服务
        services['exam-service'] = {
            'name': 'exam-service',
            'description': '考试管理服务',
            'host': 'localhost',
            'port': 9002,
            'version': '1.0.0',
            'status': ServiceStatus.STOPPED,
            'methods': ['create_exam', 'start_exam', 'submit_exam', 'get_result']
        }
        
        # 题库服务
        services['question-service'] = {
            'name': 'question-service',
            'description': '题库管理服务',
            'host': 'localhost',
            'port': 9003,
            'version': '1.0.0',
            'status': ServiceStatus.STOPPED,
            'methods': ['get_question', 'search_questions', 'create_question']
        }
        
        # 搜索服务
        services['search-service'] = {
            'name': 'search-service',
            'description': '搜索服务',
            'host': 'localhost',
            'port': 9004,
            'version': '1.0.0',
            'status': ServiceStatus.STOPPED,
            'methods': ['search', 'index_document']
        }
        
        # 通知服务
        services['notification-service'] = {
            'name': 'notification-service',
            'description': '通知服务',
            'host': 'localhost',
            'port': 9005,
            'version': '1.0.0',
            'status': ServiceStatus.STOPPED,
            'methods': ['send_email', 'send_sms', 'send_push']
        }
        
        return services
    
    def _init_default_configs(self):
        """初始化默认配置"""
        # 服务配置
        self.config_center.set_config('user-service.port', 9001)
        self.config_center.set_config('exam-service.port', 9002)
        self.config_center.set_config('question-service.port', 9003)
        
        # 数据库配置
        self.config_center.set_config('database.host', 'localhost')
        self.config_center.set_config('database.port', 5432)
        self.config_center.set_config('database.name', 'mtscos')
        
        # 缓存配置
        self.config_center.set_config('cache.enabled', True)
        self.config_center.set_config('cache.ttl', 3600)
        
        # 日志配置
        self.config_center.set_config('log.level', 'INFO')
        self.config_center.set_config('log.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    def start_service(self, service_name: str):
        """启动服务"""
        if service_name not in self.services:
            logger.error(f"服务不存在: {service_name}")
            return False
        
        service = self.services[service_name]
        
        # 标记为启动中
        service['status'] = ServiceStatus.STARTING
        
        # 注册服务
        self.rpc.register_service(
            service_name,
            service['host'],
            service['port'],
            service['version']
        )
        
        # 启动心跳
        instance_id = f"{service_name}_{service['host']}:{service['port']}"
        self.rpc.start_heartbeat(service_name, instance_id)
        
        # 标记为运行中
        service['status'] = ServiceStatus.RUNNING
        
        logger.info(f"服务启动: {service_name}")
        return True
    
    def stop_service(self, service_name: str):
        """停止服务"""
        if service_name not in self.services:
            logger.error(f"服务不存在: {service_name}")
            return False
        
        service = self.services[service_name]
        service['status'] = ServiceStatus.STOPPING
        
        # 注销服务
        instance_id = f"{service_name}_{service['host']}:{service['port']}"
        self.registry.deregister(service_name, instance_id)
        
        service['status'] = ServiceStatus.STOPPED
        
        logger.info(f"服务停止: {service_name}")
        return True
    
    def start_all(self):
        """启动所有服务"""
        for service_name in self.services:
            self.start_service(service_name)
        logger.info(f"已启动 {len(self.services)} 个服务")
    
    def stop_all(self):
        """停止所有服务"""
        for service_name in self.services:
            self.stop_service(service_name)
        logger.info(f"已停止 {len(self.services)} 个服务")
    
    def call_service(self, service_name: str, method: str, params: Dict = None) -> Any:
        """调用服务方法"""
        return self.rpc.call(service_name, method, params)
    
    def get_service_status(self, service_name: str) -> Optional[Dict]:
        """获取服务状态"""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        instances = self.registry.discover(service_name)
        
        return {
            'name': service['name'],
            'description': service['description'],
            'host': service['host'],
            'port': service['port'],
            'version': service['version'],
            'status': service['status'].value,
            'instances': len(instances),
            'methods': service['methods']
        }
    
    def get_all_services(self) -> Dict:
        """获取所有服务状态"""
        result = {}
        for service_name in self.services:
            result[service_name] = self.get_service_status(service_name)
        return result
    
    def get_config(self, key: str, namespace: str = 'default') -> Any:
        """获取配置"""
        return self.config_center.get_config(key, namespace)
    
    def set_config(self, key: str, value: Any, namespace: str = 'default'):
        """设置配置"""
        self.config_center.set_config(key, value, namespace)
    
    def record_metric(self, service_name: str, metric_name: str, value: float):
        """记录指标"""
        self.monitor.record_metric(service_name, metric_name, value)
    
    def get_metrics(self, service_name: str) -> Dict:
        """获取服务指标"""
        return self.monitor.get_metrics(service_name)
    
    def get_alerts(self) -> List[Dict]:
        """获取告警"""
        return self.monitor.get_alerts()

# 全局实例
microservices_manager = MicroservicesManager()

def get_microservices_manager() -> MicroservicesManager:
    """获取微服务管理器实例"""
    return microservices_manager

def start_all_services():
    """启动所有服务"""
    microservices_manager.start_all()

def stop_all_services():
    """停止所有服务"""
    microservices_manager.stop_all()

if __name__ == '__main__':
    print("🚀 微服务架构测试")
    print("=" * 70)
    
    manager = MicroservicesManager()
    
    print("\n📝 服务列表")
    services = manager.get_all_services()
    for name, info in services.items():
        print(f"  🔹 {name}: {info['description']}, 端口: {info['port']}")
    
    print("\n📝 启动所有服务")
    manager.start_all()
    
    services = manager.get_all_services()
    for name, info in services.items():
        status = "✅" if info['status'] == 'running' else "❌"
        print(f"  {status} {name}: {info['status']}")
    
    print("\n📝 服务注册")
    registered = manager.registry.get_all_services()
    print(f"  已注册服务: {registered}")
    
    print("\n📝 配置中心")
    db_host = manager.get_config('database.host')
    print(f"  数据库主机: {db_host}")
    
    print("\n📝 记录指标")
    manager.record_metric('user-service', 'response_time', 15.5)
    manager.record_metric('user-service', 'request_count', 100)
    metrics = manager.get_metrics('user-service')
    print(f"  指标数量: {len(metrics)}")
    
    print("\n🎉 测试完成!")
