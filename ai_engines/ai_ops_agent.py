#!/usr/bin/env python3
"""AI智能运维Agent"""

import os
import re
import logging
import json
import subprocess
import psutil
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIOpsAgent(AIEmployee):
    """AI智能运维Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI智能运维专家"):
        super().__init__(employee_id, name, 'ops_agent', 9)
        self.skills = [
            '系统监控', '资源管理', '进程管理',
            '服务监控', '日志分析', '告警管理',
            '性能监控', '容量规划', '自动化运维'
        ]
        self.monitor_history = []
        self.total_monitors = 0
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        info = {
            'platform': os.name,
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_total': round(psutil.virtual_memory().total / (1024 ** 3), 2),
            'memory_available': round(psutil.virtual_memory().available / (1024 ** 3), 2),
            'memory_used': round(psutil.virtual_memory().used / (1024 ** 3), 2),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_total': round(psutil.disk_usage('/').total / (1024 ** 3), 2),
            'disk_used': round(psutil.disk_usage('/').used / (1024 ** 3), 2),
            'disk_free': round(psutil.disk_usage('/').free / (1024 ** 3), 2),
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': self._get_network_io(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.total_monitors += 1
        self.monitor_history.append({'type': 'system', 'summary': info})
        
        return info
    
    def _get_network_io(self) -> Dict:
        """获取网络IO"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': round(net_io.bytes_sent / (1024 ** 2), 2),
                'bytes_recv': round(net_io.bytes_recv / (1024 ** 2), 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception:
            return {}
    
    def get_process_info(self) -> List[Dict]:
        """获取进程信息"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent'],
                    'status': proc.info['status']
                })
        except Exception:
            pass
        
        return processes[:20]
    
    def get_top_processes(self, limit: int = 10) -> List[Dict]:
        """获取资源占用最高的进程"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
            
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        except Exception:
            pass
        
        return processes[:limit]
    
    def monitor_health(self) -> Dict[str, Any]:
        """监控系统健康状态"""
        system_info = self.get_system_info()
        
        alerts = []
        
        if system_info['cpu_percent'] > 80:
            alerts.append(f"CPU使用率过高: {system_info['cpu_percent']}%")
        
        if system_info['memory_percent'] > 85:
            alerts.append(f"内存使用率过高: {system_info['memory_percent']}%")
        
        if system_info['disk_percent'] > 90:
            alerts.append(f"磁盘使用率过高: {system_info['disk_percent']}%")
        
        return {
            'health': 'healthy' if not alerts else 'warning',
            'alerts': alerts,
            'system_info': system_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def check_service(self, service_name: str) -> Dict[str, Any]:
        """检查服务状态"""
        try:
            result = subprocess.run(
                ['ps', 'aux', '|', 'grep', service_name],
                capture_output=True,
                text=True,
                shell=True
            )
            
            is_running = len(result.stdout.strip()) > 0
            
            return {
                'service_name': service_name,
                'is_running': is_running,
                'result': result.stdout[:500],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service_name': service_name,
                'is_running': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def kill_process(self, pid: int) -> bool:
        """终止进程"""
        try:
            proc = psutil.Process(pid)
            proc.kill()
            return True
        except Exception:
            return False
    
    def analyze_logs(self, log_path: str, lines: int = 100) -> Dict[str, Any]:
        """分析日志"""
        if not os.path.exists(log_path):
            return {'error': '日志文件不存在'}
        
        try:
            with open(log_path, 'r') as f:
                log_content = f.readlines()[-lines:]
            
            error_patterns = [
                (r'ERROR', '错误'),
                (r'WARN', '警告'),
                (r'EXCEPTION', '异常'),
                (r'FATAL', '致命'),
                (r'Traceback', '堆栈')
            ]
            
            found_patterns = {}
            for pattern, label in error_patterns:
                count = sum(1 for line in log_content if re.search(pattern, line))
                if count > 0:
                    found_patterns[label] = count
            
            return {
                'log_path': log_path,
                'total_lines': len(log_content),
                'patterns_found': found_patterns,
                'recent_lines': ''.join(log_content[-10:]),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_report(self) -> str:
        """生成运维报告"""
        system_info = self.get_system_info()
        health = self.monitor_health()
        
        report_lines = []
        report_lines.append("# 系统运维报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("## 系统状态")
        report_lines.append(f"- 健康状态: {health['health']}")
        report_lines.append(f"- CPU: {system_info['cpu_percent']}%")
        report_lines.append(f"- 内存: {system_info['memory_percent']}%")
        report_lines.append(f"- 磁盘: {system_info['disk_percent']}%")
        report_lines.append("")
        
        if health['alerts']:
            report_lines.append("## 告警信息")
            for alert in health['alerts']:
                report_lines.append(f"- {alert}")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取运维统计"""
        return {
            'total_monitors': self.total_monitors,
            'recent_monitors': self.monitor_history[-5:]
        }

ops_agent = AIOpsAgent('ai_ops_agent_001')
