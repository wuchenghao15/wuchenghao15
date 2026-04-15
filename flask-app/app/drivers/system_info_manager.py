#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统信息数据管理器
负责系统信息数据的收集、存储、分析和报告
"""

import os
import sys
import time
import json
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
        logger.info(f"系统信息管理器初始化完成，系统: {self.system_type}, 版本: {self.manager_version}")
    
    def collect_system_info(self) -> Dict:
        """收集系统信息
        
        Returns:
            Dict: 系统信息
        """
        try:
            logger.info("开始收集系统信息...")
            
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
                        'frequency': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None,
                        'usage': psutil.cpu_percent(interval=1)
                    },
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'used': psutil.virtual_memory().used,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': []
                },
                'network': {
                    'interfaces': [],
                    'connections': len(psutil.net_connections())
                }
            }
            
            # 收集磁盘信息
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
                except:
                    pass
            
            # 收集网络接口信息
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
            return {
                "success": True,
                "info": system_info
            }
            
        except Exception as e:
            logger.error(f"收集系统信息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_system_info(self, system_info: Dict) -> Dict:
        """分析系统信息
        
        Args:
            system_info: 系统信息
            
        Returns:
            Dict: 分析结果
        """
        try:
            logger.info("开始分析系统信息...")
            
            analysis = {
                'timestamp': time.time(),
                'cpu_analysis': {},
                'memory_analysis': {},
                'disk_analysis': {},
                'network_analysis': {},
                'recommendations': []
            }
            
            # 分析CPU使用情况
            cpu_usage = system_info.get('hardware', {}).get('cpu', {}).get('usage', 0)
            if cpu_usage > 80:
                analysis['cpu_analysis']['status'] = 'high'
                analysis['recommendations'].append("CPU使用率过高，建议检查运行中的进程")
            elif cpu_usage > 50:
                analysis['cpu_analysis']['status'] = 'medium'
            else:
                analysis['cpu_analysis']['status'] = 'normal'
            
            # 分析内存使用情况
            memory_percent = system_info.get('hardware', {}).get('memory', {}).get('percent', 0)
            if memory_percent > 80:
                analysis['memory_analysis']['status'] = 'high'
                analysis['recommendations'].append("内存使用率过高，建议关闭不必要的应用程序")
            elif memory_percent > 50:
                analysis['memory_analysis']['status'] = 'medium'
            else:
                analysis['memory_analysis']['status'] = 'normal'
            
            # 分析磁盘使用情况
            disks = system_info.get('hardware', {}).get('disk', [])
            for disk in disks:
                disk_percent = disk.get('percent', 0)
                if disk_percent > 90:
                    analysis['disk_analysis']['status'] = 'high'
                    analysis['recommendations'].append(f"磁盘 {disk.get('mountpoint', 'unknown')} 空间不足，建议清理文件")
                    break
            
            if 'status' not in analysis['disk_analysis']:
                analysis['disk_analysis']['status'] = 'normal'
            
            # 分析网络连接数
            connections = system_info.get('network', {}).get('connections', 0)
            if connections > 100:
                analysis['network_analysis']['status'] = 'high'
                analysis['recommendations'].append("网络连接数过多，建议检查网络连接")
            else:
                analysis['network_analysis']['status'] = 'normal'
            
            logger.info("系统信息分析完成")
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"分析系统信息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_report(self, system_info: Dict, analysis: Dict) -> Dict:
        """生成系统信息报告
        
        Args:
            system_info: 系统信息
            analysis: 分析结果
            
        Returns:
            Dict: 报告
        """
        try:
            logger.info("生成系统信息报告...")
            
            report = {
                'timestamp': time.time(),
                'report_id': f"report_{int(time.time())}",
                'system': system_info.get('system', {}),
                'hardware_summary': {
                    'cpu': system_info.get('hardware', {}).get('cpu', {}),
                    'memory': system_info.get('hardware', {}).get('memory', {}),
                    'disk': system_info.get('hardware', {}).get('disk', [])
                },
                'network_summary': system_info.get('network', {}),
                'analysis': analysis.get('analysis', {}),
                'recommendations': analysis.get('analysis', {}).get('recommendations', []),
                'generated_by': 'SystemInfoManager'
            }
            
            # 保存报告到文件
            report_dir = 'reports/system_info'
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            report_file = os.path.join(report_dir, f"system_info_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"系统信息报告生成完成，保存至: {report_file}")
            return {
                "success": True,
                "report": report,
                "file": report_file
            }
            
        except Exception as e:
            logger.error(f"生成系统信息报告失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def monitor_system(self, interval: int = 60) -> Dict:
        """监控系统状态
        
        Args:
            interval: 监控间隔（秒）
            
        Returns:
            Dict: 监控结果
        """
        try:
            logger.info(f"开始监控系统状态，间隔: {interval}秒...")
            
            # 收集初始数据
            initial_info = self.collect_system_info()
            if not initial_info.get('success'):
                return initial_info
            
            # 等待指定间隔
            time.sleep(interval)
            
            # 收集结束数据
            final_info = self.collect_system_info()
            if not final_info.get('success'):
                return final_info
            
            # 分析变化
            cpu_diff = final_info['info']['hardware']['cpu']['usage'] - initial_info['info']['hardware']['cpu']['usage']
            memory_diff = final_info['info']['hardware']['memory']['percent'] - initial_info['info']['hardware']['memory']['percent']
            
            monitor_result = {
                'initial_info': initial_info['info'],
                'final_info': final_info['info'],
                'changes': {
                    'cpu_usage_diff': cpu_diff,
                    'memory_percent_diff': memory_diff,
                    'duration': interval
                }
            }
            
            logger.info("系统状态监控完成")
            return {
                "success": True,
                "result": monitor_result
            }
            
        except Exception as e:
            logger.error(f"监控系统状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 全局系统信息管理器实例
system_info_manager = SystemInfoManager()

def get_system_info_manager() -> SystemInfoManager:
    """获取系统信息管理器实例
    
    Returns:
        SystemInfoManager: 系统信息管理器实例
    """
    return system_info_manager
