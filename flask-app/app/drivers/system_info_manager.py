# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统信息数据管理器
负责系统信息数据的收集、存储、分析和报告
"""

import os
import sys
import time
import logging
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('system_info_manager')


class SystemInfoManager:
    """系统信息数据管理器"""

    def __init__(self):
        """初始化系统信息管理器"""
        self.system_type = platform.system()
        self.manager_version = "1.0.0"
        logger.info(f"系统信息管理器初始化完成,系统: {self.system_type}, 版本: {self.manager_version}")

    def collect_system_info(self) -> Dict:
        """
        收集系统信息

        Returns:
            Dict: 系统信息
        """
        try:
            logger.info("开始收集系统信息...")

            cpu_freq = psutil.cpu_freq()
            system_info = {
                'timestamp': time.time(),
                'system': {
                    'type': platform.system(),
                    'version': platform.version(),
                    'hostname': platform.node(),
                    'architecture': platform.architecture(),
                    'processor': platform.processor()
                },
                'hardware': {
                    'cpu': {
                        'count': psutil.cpu_count(),
                        'cores': psutil.cpu_count(logical=False),
                        'frequency': cpu_freq.current if cpu_freq else None,
                        'usage': psutil.cpu_percent(interval=1)
                    },
                    'memory': {
                        'available': psutil.virtual_memory().available,
                        'used': psutil.virtual_memory().used,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': []
                },
                'network': {
                    'connections': len(psutil.net_connections()),
                    'interfaces': []
                }
            }

            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    system_info['hardware']['disk'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'opts': partition.opts,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except Exception:
                    pass

            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'name': interface,
                    'addresses': []
                }
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                system_info['network']['interfaces'].append(interface_info)

            logger.info("系统信息收集完成")
            return system_info
        except Exception as e:
            logger.error(f"收集系统信息失败: {e}")
            return {}
