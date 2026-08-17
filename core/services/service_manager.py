#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MTSCOS统一服务管理器管理所有服务的启动、停止、监控和协调"""

import os
import sys
import json
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class ServiceInfo:
    """服务信息"""
    
    def __init__(self, name: str, module_name: str, instance_name: str,
                 description: str = '', dependencies: List[str] = None,
                 auto_start: bool = True):
        self.name = name
        self.module_name = module_name
        self.instance_name = instance_name
        self.description = description
        self.dependencies = dependencies or []
        self.auto_start = auto_start
        self.status = 'stopped'
        self.start_time = None
        self.stop_time = None
        self.error_count = 0
        self.last_error = None
        self.process = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'module_name': self.module_name,
            'instance_name': self.instance_name,
            'description': self.description,
            'dependencies': self.dependencies,
            'auto_start': self.auto_start,
            'status': self.status,
            'start_time': self.start_time,
            'stop_time': self.stop_time,
            'error_count': self.error_count,
            'last_error': self.last_error
        }

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.service_instances: Dict[str, Any] = {}
        self.is_running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._register_default_services()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'service_manager_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'monitor_interval': 30,
            'auto_restart_enabled': True,
            'max_restart_attempts': 3,
            'restart_delay': 5,
            'health_check_enabled': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'service_manager_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _register_default_services(self):
        """注册默认服务"""
        services = [
            ServiceInfo('auth', 'auth_manager', 'auth_manager', 
                       '用户认证服务', [], True),
            ServiceInfo('config', 'config_manager', 'config_manager',
                       '配置管理服务', [], True),
            ServiceInfo('cache', 'cache_manager', 'cache_manager',
                       '数据缓存服务', ['config'], True),
            ServiceInfo('log', 'activity_log_service', 'activity_log_service',
                       '活动日志服务', [], True),
            ServiceInfo('error', 'error_monitor', 'error_monitor',
                       '错误监控服务', ['log'], True),
            ServiceInfo('email', 'email_service', 'email_service',
                       '邮件服务', ['config'], True),
            ServiceInfo('sms', 'sms_service', 'sms_service',
                       '短信服务', ['config'], True),
            ServiceInfo('message', 'message_system', 'message_system',
                       '实时消息系统', [], True),
            ServiceInfo('monitor', 'system_monitor', 'system_monitor',
                       '系统监控服务', [], True),
            ServiceInfo('export', 'data_export_service', 'data_export_service',
                       '数据导出服务', ['config'], True),
            ServiceInfo('scheduler', 'task_scheduler', 'task_scheduler',
                       '定时任务调度服务', [], True),
            ServiceInfo('skill', 'skill_manager', 'skill_manager',
                       '技能管理服务', ['config'], True),
            ServiceInfo('file', 'file_manager', 'file_manager',
                       '文件管理服务', ['config'], True),
            ServiceInfo('backup', 'backup_manager', 'backup_manager',
                       '系统备份服务', [], True),
            ServiceInfo('api', 'api_gateway', 'api_gateway',
                       'API网关服务', ['auth', 'log'], True)
        ]
        
        for service in services:
            self.services[service.name] = service
    
    def register_service(self, service_info: ServiceInfo):
        """注册服务"""
        with self.lock:
            self.services[service_info.name] = service_info
        logger(f"[服务] 注册服务: {service_info.name}")
    
    def unregister_service(self, service_name: str):
        """注销服务"""
        with self.lock:
            if service_name in self.services:
                del self.services[service_name]
                if service_name in self.service_instances:
                    del self.service_instances[service_name]
        logger(f"[服务] 注销服务: {service_name}")
    
    def _check_dependencies(self, service_name: str) -> bool:
        """检查依赖是否已启动"""
        service = self.services.get(service_name)
        if not service:
            return False
        
        for dep in service.dependencies:
            dep_service = self.services.get(dep)
            if dep_service and dep_service.status != 'running':
                logger(f"[服务] 依赖服务未启动: {dep}")
                return False
        
        return True
    
    def start_service(self, service_name: str) -> bool:
        """启动服务"""
        service = self.services.get(service_name)
        if not service:
            logger(f"[服务] 服务不存在: {service_name}")
            return False
        
        if service.status == 'running':
            logger(f"[服务] 服务已运行: {service_name}")
            return True
        
        if not self._check_dependencies(service_name):
            logger(f"[服务] 依赖检查失败: {service_name}")
            return False
        
        try:
            module = __import__(service.module_name, fromlist=[service.instance_name])
            instance = getattr(module, service.instance_name)
            
            if hasattr(instance, 'start'):
                instance.start()
            
            self.service_instances[service_name] = instance
            
            service.status = 'running'
            service.start_time = datetime.now().isoformat()
            service.stop_time = None
            
            logger(f"[服务] ✓ 启动成功: {service_name}")
            return True
        except Exception as e:
            service.status = 'error'
            service.error_count += 1
            service.last_error = str(e)
            logger(f"[服务] ✗ 启动失败: {service_name} - {e}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        service = self.services.get(service_name)
        if not service:
            logger(f"[服务] 服务不存在: {service_name}")
            return False
        
        if service.status != 'running':
            logger(f"[服务] 服务未运行: {service_name}")
            return True
        
        try:
            instance = self.service_instances.get(service_name)
            
            if instance and hasattr(instance, 'stop'):
                instance.stop()
            
            service.status = 'stopped'
            service.stop_time = datetime.now().isoformat()
            
            logger(f"[服务] ✓ 停止成功: {service_name}")
            return True
        except Exception as e:
            service.error_count += 1
            service.last_error = str(e)
            logger(f"[服务] ✗ 停止失败: {service_name} - {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        self.stop_service(service_name)
        time.sleep(1)
        return self.start_service(service_name)
    
    def start_all(self):
        """启动所有服务"""
        logger(f"[服务] 开始启动所有服务...")
        
        for service_name in self.services:
            service = self.services[service_name]
            if service.auto_start:
                self.start_service(service_name)
        
        logger(f"[服务] 所有服务启动完成")
    
    def stop_all(self):
        """停止所有服务"""
        logger(f"[服务] 开始停止所有服务...")
        
        for service_name in reversed(list(self.services.keys())):
            self.stop_service(service_name)
        
        logger(f"[服务] 所有服务停止完成")
    
    def _health_check(self):
        """健康检查"""
        for service_name, service in self.services.items():
            if service.status == 'running':
                instance = self.service_instances.get(service_name)
                
                if instance and hasattr(instance, 'get_status'):
                    try:
                        status = instance.get_status()
                        
                        if status.get('status') == 'error':
                            logger(f"[服务] 健康检查失败: {service_name}")
                            
                            if self.config['auto_restart_enabled'] and service.error_count < self.config['max_restart_attempts']:
                                logger(f"[服务] 自动重启服务: {service_name}")
                                time.sleep(self.config['restart_delay'])
                                self.restart_service(service_name)
                    except Exception as e:
                        service.error_count += 1
                        service.last_error = str(e)
                        logger(f"[服务] 健康检查异常: {service_name} - {e}")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                time.sleep(self.config['monitor_interval'])
                
                if self.config['health_check_enabled']:
                    self._health_check()
            except Exception as e:
                logger(f"[服务] 监控循环错误: {e}")
    
    def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        return self.services.get(service_name)
    
    def get_services(self, status: str = None) -> List[ServiceInfo]:
        """获取服务列表"""
        result = []
        
        with self.lock:
            for service in self.services.values():
                if status and service.status != status:
                    continue
                result.append(service)
        
        return result
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取服务状态详情"""
        service = self.services.get(service_name)
        if not service:
            return {'error': '服务不存在'}
        
        instance = self.service_instances.get(service_name)
        
        status_info = service.to_dict()
        
        if instance and hasattr(instance, 'get_status'):
            try:
                status_info['details'] = instance.get_status()
            except Exception as e:
                status_info['details'] = {'error': str(e)}
        
        return status_info
    
    def get_overall_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        with self.lock:
            running_count = sum(1 for s in self.services.values() if s.status == 'running')
            stopped_count = sum(1 for s in self.services.values() if s.status == 'stopped')
            error_count = sum(1 for s in self.services.values() if s.status == 'error')
            total_errors = sum(s.error_count for s in self.services.values())
            
            return {
                'total_services': len(self.services),
                'running_services': running_count,
                'stopped_services': stopped_count,
                'error_services': error_count,
                'total_errors': total_errors,
                'auto_restart_enabled': self.config['auto_restart_enabled'],
                'monitor_interval': self.config['monitor_interval']
            }
    
    def get_service_instance(self, service_name: str) -> Optional[Any]:
        """获取服务实例"""
        return self.service_instances.get(service_name)
    
    def start(self):
        """启动服务管理器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger(f"[服务] 统一服务管理器已启动")
        
        self.start_all()
    
    def stop(self):
        """停止服务管理器"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        self.stop_all()
        logger(f"[服务] 统一服务管理器已停止")

service_manager = ServiceManager()
