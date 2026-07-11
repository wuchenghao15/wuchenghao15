import psutil
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

class HealthCheckService:
    """系统健康检查服务"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """获取系统信息"""
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        system_release = 'Unknown'
        try:
            if sys.platform == 'darwin':
                system_release = os.uname().release
            elif sys.platform == 'linux':
                system_release = os.uname().release
            elif sys.platform == 'win32':
                system_release = os.environ.get('OS', 'Windows')
        except Exception:
            system_release = 'Unknown'
        
        return {
            'platform': os.name,
            'system': sys.platform,
            'release': system_release,
            'version': psutil.__version__,
            'boot_time': datetime.fromtimestamp(boot_time).isoformat(),
            'uptime': {
                'seconds': int(uptime),
                'hours': int(uptime // 3600),
                'days': int(uptime // 86400)
            }
        }
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """获取CPU信息"""
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count() or 0
        logical_cpu_count = psutil.cpu_count() or 0
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_times = psutil.cpu_times()
        
        return {
            'physical_cores': cpu_count,
            'logical_cores': logical_cpu_count,
            'usage_percent': cpu_percent,
            'times': {
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle
            },
            'status': 'healthy' if cpu_percent < 90 else 'warning' if cpu_percent < 98 else 'critical'
        }
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """获取内存信息"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'used_percent': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent,
            'status': 'healthy' if mem.percent < 85 else 'warning' if mem.percent < 95 else 'critical'
        }
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """获取磁盘信息"""
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            'total': disk_usage.total,
            'used': disk_usage.used,
            'free': disk_usage.free,
            'used_percent': disk_usage.percent,
            'io_read_count': disk_io.read_count if disk_io else 0,
            'io_write_count': disk_io.write_count if disk_io else 0,
            'io_read_bytes': disk_io.read_bytes if disk_io else 0,
            'io_write_bytes': disk_io.write_bytes if disk_io else 0,
            'status': 'healthy' if disk_usage.percent < 85 else 'warning' if disk_usage.percent < 95 else 'critical'
        }
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """获取网络信息"""
        net_io = psutil.net_io_counters()
        
        return {
            'bytes_sent': net_io.bytes_sent if net_io else 0,
            'bytes_recv': net_io.bytes_recv if net_io else 0,
            'packets_sent': net_io.packets_sent if net_io else 0,
            'packets_recv': net_io.packets_recv if net_io else 0
        }
    
    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """获取进程信息"""
        process_count = len(psutil.pids())
        current_process = psutil.Process()
        
        return {
            'total_processes': process_count,
            'current_process': {
                'pid': current_process.pid,
                'name': current_process.name(),
                'cpu_percent': current_process.cpu_percent(interval=0.1),
                'memory_percent': current_process.memory_percent(),
                'memory_info': current_process.memory_info()._asdict(),
                'status': current_process.status(),
                'created_at': datetime.fromtimestamp(current_process.create_time()).isoformat()
            }
        }
    
    @staticmethod
    def get_database_status() -> Dict[str, Any]:
        """获取数据库状态"""
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return {'status': 'healthy', 'message': '数据库连接正常'}
        except Exception as e:
            return {'status': 'critical', 'message': f'数据库连接失败: {str(e)}'}
    
    @staticmethod
    def get_health_summary() -> Dict[str, Any]:
        """获取健康检查摘要"""
        cpu = HealthCheckService.get_cpu_info()
        memory = HealthCheckService.get_memory_info()
        disk = HealthCheckService.get_disk_info()
        database = HealthCheckService.get_database_status()
        
        checks = [cpu['status'], memory['status'], disk['status'], database['status']]
        
        if 'critical' in checks:
            overall_status = 'critical'
        elif 'warning' in checks:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'components': {
                'cpu': cpu['status'],
                'memory': memory['status'],
                'disk': disk['status'],
                'database': database['status']
            },
            'details': {
                'cpu': cpu,
                'memory': memory,
                'disk': disk,
                'database': database
            }
        }
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """获取所有监控指标"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': HealthCheckService.get_system_info(),
            'cpu': HealthCheckService.get_cpu_info(),
            'memory': HealthCheckService.get_memory_info(),
            'disk': HealthCheckService.get_disk_info(),
            'network': HealthCheckService.get_network_info(),
            'process': HealthCheckService.get_process_info(),
            'database': HealthCheckService.get_database_status()
        }