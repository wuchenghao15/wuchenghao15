import psutil
import os
import sys
import time
import socket
import threading
from datetime import datetime
from typing import Dict, Any, Optional

class HealthCheckService:
    """系统健康检查服务"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._health_history = []
        self._component_status_cache = {}
        self._last_check_time = None

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
            },
            'python_version': sys.version,
            'cpu_architecture': os.uname().machine if hasattr(os, 'uname') else 'Unknown'
        }

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """获取CPU信息"""
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count() or 0
        logical_cpu_count = psutil.cpu_count() or 0
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_times = psutil.cpu_times()
        cpu_freq = psutil.cpu_freq()

        return {
            'physical_cores': cpu_count,
            'logical_cores': logical_cpu_count,
            'usage_percent': cpu_percent,
            'frequency': {
                'current': cpu_freq.current if cpu_freq else None,
                'min': cpu_freq.min if cpu_freq else None,
                'max': cpu_freq.max if cpu_freq else None
            },
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

        disk_partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except Exception:
                pass

        return {
            'total': disk_usage.total,
            'used': disk_usage.used,
            'free': disk_usage.free,
            'used_percent': disk_usage.percent,
            'io_read_count': disk_io.read_count if disk_io else 0,
            'io_write_count': disk_io.write_count if disk_io else 0,
            'io_read_bytes': disk_io.read_bytes if disk_io else 0,
            'io_write_bytes': disk_io.write_bytes if disk_io else 0,
            'partitions': disk_partitions,
            'status': 'healthy' if disk_usage.percent < 85 else 'warning' if disk_usage.percent < 95 else 'critical'
        }

    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """获取网络信息"""
        net_io = psutil.net_io_counters()
        net_connections = psutil.net_connections()

        interfaces = []
        for iface, addrs in psutil.net_if_addrs().items():
            interface_info = {'name': iface, 'addresses': []}
            for addr in addrs:
                interface_info['addresses'].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
            interfaces.append(interface_info)

        return {
            'bytes_sent': net_io.bytes_sent if net_io else 0,
            'bytes_recv': net_io.bytes_recv if net_io else 0,
            'packets_sent': net_io.packets_sent if net_io else 0,
            'packets_recv': net_io.packets_recv if net_io else 0,
            'connections_count': len(net_connections),
            'interfaces': interfaces
        }

    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """获取进程信息"""
        process_count = len(psutil.pids())
        current_process = psutil.Process()

        child_processes = []
        try:
            for child in current_process.children(recursive=True):
                try:
                    child_processes.append({
                        'pid': child.pid,
                        'name': child.name(),
                        'cpu_percent': child.cpu_percent(interval=0.01),
                        'memory_percent': child.memory_percent()
                    })
                except Exception:
                    pass
        except Exception:
            pass

        return {
            'total_processes': process_count,
            'current_process': {
                'pid': current_process.pid,
                'name': current_process.name(),
                'cpu_percent': current_process.cpu_percent(interval=0.1),
                'memory_percent': current_process.memory_percent(),
                'memory_info': current_process.memory_info()._asdict(),
                'status': current_process.status(),
                'created_at': datetime.fromtimestamp(current_process.create_time()).isoformat(),
                'threads': current_process.num_threads(),
                'children_count': len(child_processes)
            },
            'child_processes': child_processes
        }

    @staticmethod
    def get_database_status() -> Dict[str, Any]:
        """获取数据库状态"""
        databases = []
        db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'split_databases')

        if os.path.exists(db_dir):
            for db_file in os.listdir(db_dir):
                if db_file.endswith('.db'):
                    db_path = os.path.join(db_dir, db_file)
                    status = 'healthy'
                    message = '数据库连接正常'
                    size = os.path.getsize(db_path)

                    try:
                        import sqlite3
                        conn = sqlite3.connect(db_path, timeout=5)
                        cursor = conn.cursor()
                        cursor.execute('SELECT 1')
                        conn.close()
                    except Exception as e:
                        status = 'critical'
                        message = f'数据库连接失败: {str(e)}'

                    databases.append({
                        'name': db_file,
                        'path': db_path,
                        'size': size,
                        'status': status,
                        'message': message
                    })

        main_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')
        main_status = 'healthy'
        main_message = '数据库连接正常'
        main_size = os.path.getsize(main_db_path) if os.path.exists(main_db_path) else 0

        try:
            import sqlite3
            conn = sqlite3.connect(main_db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
        except Exception as e:
            main_status = 'critical'
            main_message = f'数据库连接失败: {str(e)}'

        databases.append({
            'name': 'app.db',
            'path': main_db_path,
            'size': main_size,
            'status': main_status,
            'message': main_message
        })

        overall_status = 'healthy'
        for db in databases:
            if db['status'] == 'critical':
                overall_status = 'critical'
                break
            elif db['status'] == 'warning':
                overall_status = 'warning'

        return {
            'status': overall_status,
            'message': main_message,
            'databases': databases,
            'total_databases': len(databases)
        }

    @staticmethod
    def get_redis_status() -> Dict[str, Any]:
        """获取Redis状态"""
        try:
            from app.services.redis_manager import redis_manager
            if redis_manager.is_connected():
                info = redis_manager.info() if hasattr(redis_manager, 'info') else {}
                return {
                    'status': 'healthy',
                    'connected': True,
                    'using_memory_fallback': False,
                    'info': info
                }
            elif hasattr(redis_manager, '_use_memory_fallback') and redis_manager._use_memory_fallback:
                return {
                    'status': 'warning',
                    'connected': False,
                    'using_memory_fallback': True,
                    'message': 'Redis连接失败，已切换到内存缓存模式'
                }
            else:
                return {
                    'status': 'critical',
                    'connected': False,
                    'using_memory_fallback': False,
                    'message': 'Redis连接失败'
                }
        except ImportError:
            return {
                'status': 'warning',
                'connected': False,
                'message': 'Redis模块未安装'
            }
        except Exception as e:
            return {
                'status': 'critical',
                'connected': False,
                'message': f'Redis检查失败: {str(e)}'
            }

    def get_component_status(self) -> Dict[str, Any]:
        """获取组件状态"""
        components = {
            'database': self.get_database_status(),
            'redis': self.get_redis_status(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info()
        }

        overall_status = 'healthy'
        for name, status in components.items():
            component_status = status.get('status', 'unknown')
            if component_status == 'critical':
                overall_status = 'critical'
                break
            elif component_status == 'warning':
                overall_status = 'warning'

        self._component_status_cache = components
        self._last_check_time = datetime.now()

        return {
            'overall_status': overall_status,
            'components': components,
            'checked_at': self._last_check_time.isoformat()
        }

    @staticmethod
    def check_service_availability() -> Dict[str, Any]:
        """检查服务可用性"""
        services = []

        try:
            socket.setdefaulttimeout(2)
            localhost = socket.gethostbyname('localhost')

            for port in [5000, 6379]:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        result = sock.connect_ex((localhost, port))
                        services.append({
                            'service': 'HTTP' if port == 5000 else 'Redis',
                            'port': port,
                            'status': 'healthy' if result == 0 else 'critical',
                            'message': '服务可用' if result == 0 else '服务不可用'
                        })
                except Exception as e:
                    services.append({
                        'service': 'HTTP' if port == 5000 else 'Redis',
                        'port': port,
                        'status': 'critical',
                        'message': f'检查失败: {str(e)}'
                    })
        except Exception as e:
            services.append({
                'service': 'Network',
                'status': 'critical',
                'message': f'网络检查失败: {str(e)}'
            })

        return {'services': services}

    @staticmethod
    def check_log_files() -> Dict[str, Any]:
        """检查日志文件"""
        log_dirs = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        ]

        log_files = []
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(log_dir, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            log_files.append({
                                'name': file,
                                'path': file_path,
                                'size': file_size,
                                'modified_time': modified_time.isoformat(),
                                'size_status': 'healthy' if file_size < 100 * 1024 * 1024 else 'warning'
                            })
                        except Exception:
                            pass

        return {'log_files': log_files, 'total_logs': len(log_files)}

    @staticmethod
    def check_environment() -> Dict[str, Any]:
        """检查环境变量"""
        required_vars = ['SECRET_KEY', 'MODEL_PATH']
        optional_vars = ['REDIS_URL', 'DATABASE_URL']

        env_check = {
            'required': [],
            'optional': []
        }

        for var in required_vars:
            value = os.environ.get(var)
            env_check['required'].append({
                'name': var,
                'exists': value is not None,
                'value': '***' if var == 'SECRET_KEY' else value,
                'status': 'healthy' if value is not None else 'critical'
            })

        for var in optional_vars:
            value = os.environ.get(var)
            env_check['optional'].append({
                'name': var,
                'exists': value is not None,
                'value': value,
                'status': 'healthy' if value is not None else 'warning'
            })

        return env_check

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康检查摘要"""
        cpu = self.get_cpu_info()
        memory = self.get_memory_info()
        disk = self.get_disk_info()
        database = self.get_database_status()
        redis = self.get_redis_status()
        services = self.check_service_availability()
        environment = self.check_environment()

        checks = [cpu['status'], memory['status'], disk['status'], database['status'], redis['status']]
        for service in services.get('services', []):
            checks.append(service['status'])

        if 'critical' in checks:
            overall_status = 'critical'
        elif 'warning' in checks:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'

        health_record = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'components': {
                'cpu': cpu['status'],
                'memory': memory['status'],
                'disk': disk['status'],
                'database': database['status'],
                'redis': redis['status']
            },
            'details': {
                'cpu': cpu,
                'memory': memory,
                'disk': disk,
                'database': database,
                'redis': redis,
                'services': services,
                'environment': environment
            }
        }

        self._health_history.append(health_record)
        if len(self._health_history) > 100:
            self._health_history = self._health_history[-100:]

        return health_record

    def get_health_history(self, limit: int = 20) -> list:
        """获取健康检查历史"""
        return self._health_history[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有监控指标"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'process': self.get_process_info(),
            'database': self.get_database_status(),
            'redis': self.get_redis_status(),
            'services': self.check_service_availability(),
            'environment': self.check_environment(),
            'logs': self.check_log_files()
        }


health_check_service = HealthCheckService()