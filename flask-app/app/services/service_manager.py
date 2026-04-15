#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台服务管理模块，用于管理系统中的各种服务
"""

import os
import sys
import time
import logging
import threading
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ServiceManager:
    """后台服务管理模块"""
    
    def __init__(self):
        """初始化服务管理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("服务管理器已初始化")
        
        # 服务配置
        self.services = {}
        
        # 监控线程
        self.monitor_thread = None
        self.running = False
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        # 配置信息
        self.config = {
            'monitor_interval': 10,  # 监控间隔（秒）
            'auto_restart': True,    # 自动重启开关
            'max_restart_count': 5,  # 最大重启次数
            'restart_interval': 30,  # 重启间隔（秒）
        }
        
        # 加载配置
        self._load_config()
        
    def _load_config(self):
        """加载服务配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'services_config.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载服务配置
                if 'services' in config_data:
                    for service_name, service_config in config_data['services'].items():
                        # 构建完整的工作目录路径
                        working_dir = service_config.get('working_dir', '.')
                        if working_dir == '.':
                            working_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        
                        self.services[service_name] = {
                            'name': service_config.get('name', service_name),
                            'command': service_config.get('command', ''),
                            'working_dir': working_dir,
                            'status': 'stopped',
                            'process': None,
                            'start_time': None,
                            'pid': None,
                            'restart_count': 0,
                            'auto_start': service_config.get('auto_start', False),
                            'auto_restart': service_config.get('auto_restart', True),
                            'max_restart_count': service_config.get('max_restart_count', 5),
                            'restart_interval': service_config.get('restart_interval', 30)
                        }
                
                # 加载监控配置
                if 'monitoring' in config_data:
                    self.config['monitor_interval'] = config_data['monitoring'].get('interval', 10)
                
                self.logger.info(f"成功加载配置文件: {config_path}")
                self.logger.info(f"加载了 {len(self.services)} 个服务配置")
                
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {str(e)}")
                # 使用默认配置
                self._load_default_config()
        else:
            self.logger.warning(f"配置文件不存在: {config_path}")
            # 使用默认配置
            self._load_default_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.services = {
            'flask_app': {
                'name': 'Flask应用服务',
                'command': 'python3 app.py',
                'working_dir': base_dir,
                'status': 'stopped',
                'process': None,
                'start_time': None,
                'pid': None,
                'restart_count': 0,
                'auto_start': True,
                'auto_restart': True,
                'max_restart_count': 5,
                'restart_interval': 30
            },
            'ai_engine': {
                'name': 'AI引擎服务',
                'command': 'python3 -m app.ai.ai_engine_integrator',
                'working_dir': base_dir,
                'status': 'stopped',
                'process': None,
                'start_time': None,
                'pid': None,
                'restart_count': 0,
                'auto_start': True,
                'auto_restart': True,
                'max_restart_count': 5,
                'restart_interval': 30
            },
            'thread_manager': {
                'name': '线程管理服务',
                'command': 'python3 -m app.ai.thread_process_manager',
                'working_dir': base_dir,
                'status': 'stopped',
                'process': None,
                'start_time': None,
                'pid': None,
                'restart_count': 0,
                'auto_start': True,
                'auto_restart': True,
                'max_restart_count': 5,
                'restart_interval': 30
            }
        }
        self.logger.info("使用默认服务配置")
    
    def start(self):
        """启动服务管理器"""
        if self.running:
            self.logger.warning("服务管理器已经在运行中")
            return
        
        self.logger.info("正在启动服务管理器...")
        self.running = True
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("服务监控线程已启动")
        
        # 自动启动服务
        self._auto_start_services()
        
        self.logger.info("服务管理器启动成功")
    
    def _auto_start_services(self):
        """自动启动配置为auto_start的服务"""
        self.logger.info("开始自动启动服务...")
        success_count = 0
        total_count = 0
        
        for service_name, service in self.services.items():
            if service.get('auto_start', False):
                total_count += 1
                if self.start_service(service_name):
                    success_count += 1
                # 避免同时启动所有服务导致系统负载过高
                time.sleep(1)
        
        self.logger.info(f"自动启动服务完成，成功: {success_count}/{total_count}")
    
    def stop(self):
        """停止服务管理器"""
        if not self.running:
            self.logger.warning("服务管理器已经停止")
            return
        
        self.logger.info("正在停止服务管理器...")
        self.running = False
        
        # 停止所有服务
        for service_name in self.services:
            self.stop_service(service_name)
        
        # 等待监控线程结束
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.logger.info("服务监控线程已停止")
        
        self.logger.info("服务管理器已停止")
    
    def start_service(self, service_name: str):
        """启动指定服务"""
        with self.lock:
            if service_name not in self.services:
                self.logger.error(f"未知服务: {service_name}")
                return False
            
            service = self.services[service_name]
            if service['status'] == 'running':
                self.logger.warning(f"服务 {service['name']} 已经在运行中")
                return True
            
            try:
                self.logger.info(f"正在启动服务: {service['name']}")
                
                # 启动服务进程
                process = subprocess.Popen(
                    service['command'],
                    shell=True,
                    cwd=service['working_dir'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 更新服务状态
                service['process'] = process
                service['status'] = 'running'
                service['start_time'] = datetime.now().isoformat()
                service['pid'] = process.pid
                service['restart_count'] = 0
                
                self.logger.info(f"服务 {service['name']} 启动成功，PID: {process.pid}")
                return True
            except Exception as e:
                self.logger.error(f"启动服务 {service['name']} 失败: {str(e)}")
                service['status'] = 'error'
                return False
    
    def stop_service(self, service_name: str):
        """停止指定服务"""
        with self.lock:
            if service_name not in self.services:
                self.logger.error(f"未知服务: {service_name}")
                return False
            
            service = self.services[service_name]
            if service['status'] == 'stopped':
                self.logger.warning(f"服务 {service['name']} 已经停止")
                return True
            
            try:
                self.logger.info(f"正在停止服务: {service['name']}")
                
                # 终止进程
                if service['process']:
                    service['process'].terminate()
                    try:
                        service['process'].wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        service['process'].kill()
                
                # 更新服务状态
                service['process'] = None
                service['status'] = 'stopped'
                service['start_time'] = None
                service['pid'] = None
                
                self.logger.info(f"服务 {service['name']} 停止成功")
                return True
            except Exception as e:
                self.logger.error(f"停止服务 {service['name']} 失败: {str(e)}")
                service['status'] = 'error'
                return False
    
    def restart_service(self, service_name: str):
        """重启指定服务"""
        with self.lock:
            if service_name not in self.services:
                self.logger.error(f"未知服务: {service_name}")
                return False
            
            self.logger.info(f"正在重启服务: {self.services[service_name]['name']}")
            
            # 停止服务
            if not self.stop_service(service_name):
                return False
            
            # 等待一段时间
            time.sleep(2)
            
            # 启动服务
            if not self.start_service(service_name):
                return False
            
            # 更新重启计数
            self.services[service_name]['restart_count'] += 1
            self.logger.info(f"服务 {self.services[service_name]['name']} 重启成功，重启次数: {self.services[service_name]['restart_count']}")
            return True
    
    def start_all_services(self):
        """启动所有服务"""
        self.logger.info("正在启动所有服务...")
        success_count = 0
        total_count = len(self.services)
        
        for service_name in self.services:
            if self.start_service(service_name):
                success_count += 1
            # 避免同时启动所有服务导致系统负载过高
            time.sleep(1)
        
        self.logger.info(f"启动服务完成，成功: {success_count}/{total_count}")
        return success_count == total_count
    
    def stop_all_services(self):
        """停止所有服务"""
        self.logger.info("正在停止所有服务...")
        success_count = 0
        total_count = len(self.services)
        
        for service_name in self.services:
            if self.stop_service(service_name):
                success_count += 1
        
        self.logger.info(f"停止服务完成，成功: {success_count}/{total_count}")
        return success_count == total_count
    
    def restart_all_services(self):
        """重启所有服务"""
        self.logger.info("正在重启所有服务...")
        success_count = 0
        total_count = len(self.services)
        
        for service_name in self.services:
            if self.restart_service(service_name):
                success_count += 1
            # 避免同时重启所有服务导致系统负载过高
            time.sleep(2)
        
        self.logger.info(f"重启服务完成，成功: {success_count}/{total_count}")
        return success_count == total_count
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            self._check_services()
            time.sleep(self.config['monitor_interval'])
    
    def _check_services(self):
        """检查所有服务状态"""
        with self.lock:
            for service_name, service in self.services.items():
                if service['status'] == 'running':
                    # 检查进程是否还在运行
                    if service['process']:
                        returncode = service['process'].poll()
                        if returncode is not None:
                            # 进程已经退出
                            self.logger.warning(f"服务 {service['name']} 异常退出，返回码: {returncode}")
                            service['status'] = 'stopped'
                            service['process'] = None
                            service['pid'] = None
                            
                            # 检查是否需要自动重启（使用服务级别的配置）
                            auto_restart = service.get('auto_restart', True)
                            max_restart_count = service.get('max_restart_count', 5)
                            restart_interval = service.get('restart_interval', 30)
                            
                            if auto_restart and service['restart_count'] < max_restart_count:
                                self.logger.info(f"尝试自动重启服务: {service['name']}")
                                time.sleep(restart_interval)
                                self.start_service(service_name)
                
                # 记录服务状态
                self.logger.debug(f"服务状态: {service['name']} - {service['status']}")
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取指定服务的状态"""
        with self.lock:
            if service_name not in self.services:
                return {'error': '未知服务'}
            return self.services[service_name].copy()
    
    def get_all_service_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务的状态"""
        with self.lock:
            return {name: service.copy() for name, service in self.services.items()}
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        with self.lock:
            self.logger.info(f"更新服务管理器配置: {new_config}")
            self.config.update(new_config)
    
    def add_service(self, service_name: str, service_config: Dict[str, Any]):
        """添加新服务"""
        with self.lock:
            if service_name in self.services:
                self.logger.warning(f"服务 {service_name} 已存在")
                return False
            
            # 验证服务配置
            required_fields = ['name', 'command', 'working_dir']
            for field in required_fields:
                if field not in service_config:
                    self.logger.error(f"服务配置缺少必要字段: {field}")
                    return False
            
            # 添加服务
            self.services[service_name] = {
                'name': service_config['name'],
                'command': service_config['command'],
                'working_dir': service_config['working_dir'],
                'status': 'stopped',
                'process': None,
                'start_time': None,
                'pid': None,
                'restart_count': 0
            }
            
            self.logger.info(f"添加服务成功: {service_config['name']}")
            return True
    
    def remove_service(self, service_name: str):
        """移除服务"""
        with self.lock:
            if service_name not in self.services:
                self.logger.error(f"未知服务: {service_name}")
                return False
            
            # 停止服务
            self.stop_service(service_name)
            
            # 移除服务
            del self.services[service_name]
            self.logger.info(f"移除服务成功: {service_name}")
            return True

# 初始化服务管理器实例
service_manager = ServiceManager()