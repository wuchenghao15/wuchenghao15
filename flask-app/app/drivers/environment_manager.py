#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统环境管理器
负责系统环境的监控、优化和管理
"""

import os
import sys
import time
import json
import logging
import platform
import psutil
import subprocess
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('environment_manager')

class EnvironmentManager:
    """系统环境管理器"""
    
    def __init__(self):
        """初始化环境管理器"""
        self.system_type = platform.system()
        self.system_version = platform.version()
        self.python_version = platform.python_version()
        self.manager_version = "1.0.0"
        logger.info(f"环境管理器初始化完成，系统: {self.system_type}, 版本: {self.manager_version}")
    
    def monitor_system(self) -> Dict:
        """监控系统状态
        
        Returns:
            Dict: 系统状态信息
        """
        try:
            logger.info("开始监控系统状态...")
            
            system_status = {
                'cpu': {
                    'count': psutil.cpu_count(),
                    'usage': psutil.cpu_percent(interval=1),
                    'frequency': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'used': psutil.virtual_memory().used,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                },
                'network': {
                    'interfaces': list(psutil.net_if_addrs().keys()),
                    'connections': len(psutil.net_connections())
                },
                'system': {
                    'type': self.system_type,
                    'version': self.system_version,
                    'python_version': self.python_version
                },
                'timestamp': time.time()
            }
            
            logger.info("系统状态监控完成")
            return {
                "success": True,
                "status": system_status
            }
            
        except Exception as e:
            logger.error(f"监控系统状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def optimize_environment(self) -> Dict:
        """优化系统环境
        
        Returns:
            Dict: 优化结果
        """
        try:
            logger.info("开始优化系统环境...")
            
            optimizations = []
            
            # 1. 检查并优化内存使用
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 80:
                optimizations.append("内存使用率过高，建议关闭不必要的应用程序")
            
            # 2. 检查并优化磁盘空间
            disk_percent = psutil.disk_usage('/').percent
            if disk_percent > 90:
                optimizations.append("磁盘空间不足，建议清理临时文件")
            
            # 3. 检查并优化CPU使用
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 90:
                optimizations.append("CPU使用率过高，建议检查运行中的进程")
            
            logger.info("系统环境优化完成")
            return {
                "success": True,
                "optimizations": optimizations,
                "system_status": {
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "cpu_usage": cpu_usage
                }
            }
            
        except Exception as e:
            logger.error(f"优化系统环境失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_system(self) -> Dict:
        """清理系统
        
        Returns:
            Dict: 清理结果
        """
        try:
            logger.info("开始清理系统...")
            
            cleanup_tasks = []
            
            # 1. 清理临时文件
            try:
                temp_dir = os.path.join(os.path.expanduser('~'), 'tmp')
                if os.path.exists(temp_dir):
                    files = os.listdir(temp_dir)
                    if files:
                        cleanup_tasks.append(f"清理临时目录: {temp_dir} ({len(files)} 个文件)")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
            
            # 2. 清理Python缓存
            try:
                import glob
                pycache_dirs = glob.glob('**/__pycache__', recursive=True)
                if pycache_dirs:
                    cleanup_tasks.append(f"清理Python缓存: {len(pycache_dirs)} 个目录")
            except Exception as e:
                logger.warning(f"清理Python缓存失败: {str(e)}")
            
            logger.info("系统清理完成")
            return {
                "success": True,
                "tasks": cleanup_tasks
            }
            
        except Exception as e:
            logger.error(f"清理系统失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_environment_report(self) -> Dict:
        """获取环境报告
        
        Returns:
            Dict: 环境报告
        """
        try:
            logger.info("生成环境报告...")
            
            report = {
                'system': {
                    'type': self.system_type,
                    'version': self.system_version,
                    'python_version': self.python_version
                },
                'resources': {
                    'cpu': {
                        'count': psutil.cpu_count(),
                        'usage': psutil.cpu_percent(interval=1),
                        'frequency': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None
                    },
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'used': psutil.virtual_memory().used,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'used': psutil.disk_usage('/').used,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    }
                },
                'environment_variables': {
                    'PATH': os.environ.get('PATH', 'N/A')[:500],  # 截断长路径
                    'HOME': os.environ.get('HOME', 'N/A'),
                    'USER': os.environ.get('USER', 'N/A')
                },
                'timestamp': time.time()
            }
            
            logger.info("环境报告生成完成")
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"生成环境报告失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 全局环境管理器实例
environment_manager = EnvironmentManager()

def get_environment_manager() -> EnvironmentManager:
    """获取环境管理器实例
    
    Returns:
        EnvironmentManager: 环境管理器实例
    """
    return environment_manager
