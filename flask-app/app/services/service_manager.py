#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台服务管理模块，用于管理系统中的各种服务"""

import os
import sys
import time
import logging
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ServiceManager:
    """后台服务管理模块"""

    def __init__(self):
        """初始化服务管理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("服务管理器已初始化")

        self.services = {}
        self.service_threads = {}

    def register_service(self, service_name: str, service_func, **kwargs):
        """注册服务"""
        self.services[service_name] = {
            'func': service_func,
            'kwargs': kwargs,
            'status': 'registered',
            'thread': None
        }

    def start_service(self, service_name: str):
        """启动服务"""
        if service_name in self.services:
            self.services[service_name]['status'] = 'running'
            self.logger.info(f"服务 {service_name} 已启动")

    def stop_service(self, service_name: str):
        """停止服务"""
        if service_name in self.services:
            self.services[service_name]['status'] = 'stopped'
            self.logger.info(f"服务 {service_name} 已停止")

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务状态"""
        return self.services.get(service_name)

    def get_all_status(self) -> Dict[str, Any]:
        """获取所有服务状态"""
        return self.services

    def start(self):
        """启动服务管理器"""
        self.logger.info("服务管理器启动")
        for service_name in self.services:
            self.start_service(service_name)

    def start_all_services(self):
        """启动所有服务"""
        self.start()

service_manager = ServiceManager()