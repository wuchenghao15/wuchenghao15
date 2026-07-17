# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
加强版AI员工数据模型
"""

import time
from app.models.base_model import BaseModel
from app.services import get_system_version_service, get_javascript_optimization_service
from app.utils.logging import logger
import logging
import sys


class EnhancedAIEmployee(BaseModel):
    """加强版AI员工模型"""

    table_name = 'enhanced_ai_employees'
    primary_key = 'employee_id'
    columns = {
        'employee_id': 'TEXT PRIMARY KEY',
        'name': 'TEXT NOT NULL',
        'ai_type': 'TEXT NOT NULL',
        'description': 'TEXT NOT NULL',
        'capabilities': 'TEXT',
        'status': 'TEXT NOT NULL DEFAULT "inactive"',
        'config': 'TEXT',
        'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'brain_integration': 'BOOLEAN DEFAULT TRUE',
        'self_learning': 'BOOLEAN DEFAULT TRUE',
        'system_access': 'BOOLEAN DEFAULT TRUE',
        'adaptation_level': 'INTEGER DEFAULT 0'
    }

    def __init__(self, **kwargs):
        """初始化加强版AI员工"""
        if 'capabilities' in kwargs and isinstance(kwargs['capabilities'], list):
            kwargs['capabilities'] = str(kwargs['capabilities'])
        if 'config' in kwargs and isinstance(kwargs['config'], dict):
            kwargs['config'] = str(kwargs['config'])

        super().__init__(**kwargs)

    def __getattr__(self, name):
        """获取属性值,处理JSON类型字段"""
        if name in self._data:
            value = self._data[name]
            if name in ['capabilities', 'config'] and isinstance(value, str):
                try:
                    return eval(value)
                except Exception:
                    return value
            return value
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """设置属性值,处理JSON类型字段"""
        if name in ['_data', '_dirty']:
            super().__setattr__(name, value)
        elif name in self.columns:
            if name in ['capabilities', 'config'] and isinstance(value, (list, dict)):
                value = str(value)

            if self._data.get(name) != value:
                self._data[name] = value
                self._dirty.add(name)
        else:
            super().__setattr__(name, value)

    def to_dict(self):
        """转换为字典"""
        result = {}
        for key, value in self._data.items():
            if key in ['capabilities', 'config'] and value:
                if isinstance(value, str):
                    try:
                        result[key] = eval(value)
                    except Exception:
                        result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def update_adaptation_level(self, new_level):
        """更新适应等级"""
        self.adaptation_level = new_level
        self.save()

    def activate(self):
        """激活AI员工"""
        self.status = 'active'
        self.save()

    def deactivate(self):
        """停用AI员工"""
        self.status = 'inactive'
        self.save()

    def upgrade(self):
        """升级AI员工"""
        self.adaptation_level += 1
        self.save()

    def add_capability(self, capability):
        """添加能力"""
        capabilities = self.capabilities or []
        if capability not in capabilities:
            capabilities.append(capability)
            self.capabilities = capabilities

    def remove_capability(self, capability):
        """移除能力"""
        capabilities = self.capabilities or []
        if capability in capabilities:
            capabilities.remove(capability)
            self.capabilities = capabilities

    def upgrade_system_version(self):
        """
        升级系统版本

        Returns:
            dict: 升级结果
        """
        if not self.system_access:
            return {
                'success': False,
                'message': "AI员工没有系统访问权限"
            }

        logger.info(f"AI员工 {self.name} 正在执行系统版本升级...")
        result = get_system_version_service().upgrade_system_version()

        if result['success']:
            logger.info(f"AI员工 {self.name} 成功升级系统版本!")
        else:
            logger.error(f"AI员工 {self.name} 系统版本升级失败!")

        return result

    def optimize_javascript(self, js_code, filename=None, config=None):
        """
        优化JavaScript代码

        Args:
            js_code: JavaScript代码字符串
            filename: 文件名(可选)
            config: 优化配置(可选)

        Returns:
            dict: 优化结果
        """
        if 'javascript_optimization' not in (self.capabilities or []):
            logger.error(f"AI员工 {self.name} 没有JavaScript优化能力")
            return {'success': False, 'message': '没有JavaScript优化能力'}

        logger.info(f"AI员工 {self.name} 正在优化JavaScript代码...")
        result = get_javascript_optimization_service().optimize(js_code, filename, config)
        return result

    def optimize_javascript_files(self, file_paths, config=None):
        """
        批量优化JavaScript文件

        Args:
            file_paths: JavaScript文件路径列表
            config: 优化配置(可选)

        Returns:
            list: 优化结果列表
        """
        if 'javascript_optimization' not in (self.capabilities or []):
            return [{'success': False, 'message': '没有JavaScript优化能力'} for _ in file_paths]

        results = []
        for file_path in file_paths:
            result = get_javascript_optimization_service().optimize_file(file_path, config)
            results.append(result)
        return results

    def optimize_javascript_directory(self, directory_path, recursive=True, config=None):
        """
        优化目录中的所有JavaScript文件

        Args:
            directory_path: 目录路径
            recursive: 是否递归优化子目录
            config: 优化配置(可选)

        Returns:
            list: 优化结果列表
        """
        if 'javascript_optimization' not in (self.capabilities or []):
            return [{'success': False, 'message': '没有JavaScript优化能力'}]

        logger.info(f"AI员工 {self.name} 正在优化目录 {directory_path} 中的JavaScript文件...")
        result = get_javascript_optimization_service().optimize_directory(directory_path, recursive, config)
        return result

    def initialize_system(self):
        """
        初始化系统,集成初始化脚本功能

        Returns:
            dict: 初始化结果
        """
        if not self.system_access:
            return {'success': False, 'message': '没有系统访问权限'}

        logger.info(f"AI员工 {self.name} 正在初始化系统...")
        return {'success': True, 'message': '系统初始化完成'}

    def get_system_status(self):
        """
        获取系统状态

        Returns:
            dict: 系统状态信息
        """
        if not self.system_access:
            return {}

        logger.info(f"AI员工 {self.name} 正在获取系统状态...")
        return {
            'status': 'running',
            'adaptation_level': self.adaptation_level,
            'capabilities': self.capabilities
        }
