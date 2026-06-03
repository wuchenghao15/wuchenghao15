# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MTSCOS AI Project Container - 用于管理全局实例和依赖
"""


class AppContainer:
    """应用容器 - 管理全局实例和依赖"""

    def __init__(self):
        self.services = {}
        self.config = {}

    def register(self, name, service):
        """注册服务"""
        self.services[name] = service

    def get(self, name):
        """获取服务"""
        if name not in self.services:
            raise ValueError(f"Service {name} not registered")
        return self.services[name]

    def has(self, name):
        """检查服务是否已注册"""
        return name in self.services

    def remove(self, name):
        """移除服务"""
        if name in self.services:
            del self.services[name]

    def clear(self):
        """清空所有服务"""
        self.services.clear()

    def load_config(self, config):
        """加载配置"""
        self.config.update(config)

    def get_config(self, key, default=None):
        """获取配置"""
        return self.config.get(key, default)
