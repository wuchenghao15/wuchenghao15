# -*- coding: utf-8 -*-
"""
MonitoringCollector - 监控采集器
统一采集应用底层监控和服务器运维监控数据
支持Prometheus、Telegraf、Loki等多种输出格式
"""
import json
import logging
import os
import time
import psutil
import socket
import threading
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class MonitoringCollector:
    """监控采集器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.metrics = defaultdict(list)
        self.collect_interval = 30
        self.running = False
        self._prometheus_metrics = {}
        self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self):
        """初始化Prometheus指标"""
        try:
            from prometheus_client import Gauge, Counter, Histogram, Summary
            
            self._prometheus_metrics['cpu_usage'] = Gauge(
                'mtscos_cpu_usage_percent', 'CPU usage percentage'
            )
            self._prometheus_metrics['memory_usage'] = Gauge(
                'mtscos_memory_usage_percent', 'Memory usage percentage'
            )
            self._prometheus_metrics['disk_usage'] = Gauge(
                'mtscos_disk_usage_percent', 'Disk usage percentage'
            )
            self._prometheus_metrics['network_bytes_sent'] = Counter(
                'mtscos_network_bytes_sent_total', 'Network bytes sent'
            )
            self._prometheus_metrics['network_bytes_recv'] = Counter(
                'mtscos_network_bytes_recv_total', 'Network bytes received'
            )
            self._prometheus_metrics['active_connections'] = Gauge(
                'mtscos_active_connections', 'Active connections'
            )
            self._prometheus_metrics['request_count'] = Counter(
                'mtscos_requests_total', 'Total requests', ['endpoint', 'method', 'status']
            )
            self._prometheus_metrics['request_duration'] = Histogram(
                'mtscos_request_duration_seconds', 'Request duration', ['endpoint']
            )
            self._prometheus_metrics['error_count'] = Counter(
                'mtscos_errors_total', 'Total errors', ['type']
            )
            
            logger.info("[监控采集器] Prometheus指标初始化完成")
        except ImportError:
            logger.warning("[监控采集器] prometheus_client未安装，跳过指标初始化")
    
    def collect_system_metrics(self) -> Dict:
        """采集系统指标"""
        metrics = {}
        
        metrics['timestamp'] = datetime.now().isoformat()
        metrics['host'] = socket.gethostname()
        
        metrics['cpu'] = {
            'usage_percent': psutil.cpu_percent(interval=0.5),
            'count': psutil.cpu_count(),
            'load_avg': list(os.getloadavg()),
            'times': {
                'user': psutil.cpu_times().user,
                'system': psutil.cpu_times().system,
                'idle': psutil.cpu_times().idle
            }
        }
        
        memory = psutil.virtual_memory()
        metrics['memory'] = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'used_percent': memory.percent,
            'cached_gb': round(memory.cached / (1024**3), 2) if hasattr(memory, 'cached') else 0
        }
        
        swap = psutil.swap_memory()
        metrics['swap'] = {
            'total_gb': round(swap.total / (1024**3), 2),
            'used_gb': round(swap.used / (1024**3), 2),
            'used_percent': swap.percent
        }
        
        disk_usage = psutil.disk_usage('/')
        metrics['disk'] = {
            'total_gb': round(disk_usage.total / (1024**3), 2),
            'used_gb': round(disk_usage.used / (1024**3), 2),
            'free_gb': round(disk_usage.free / (1024**3), 2),
            'used_percent': disk_usage.percent
        }
        
        disk_io = psutil.disk_io_counters()
        metrics['disk_io'] = {
            'read_count': disk_io.read_count,
            'write_count': disk_io.write_count,
            'read_bytes': disk_io.read_bytes,
            'write_bytes': disk_io.write_bytes
        }
        
        net_io = psutil.net_io_counters()
        metrics['network'] = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'err_in': net_io.errin,
            'err_out': net_io.errout,
            'drop_in': net_io.dropin,
            'drop_out': net_io.dropout
        }
        
        metrics['network_interfaces'] = []
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    metrics['network_interfaces'].append({
                        'interface': iface,
                        'ip': addr.address,
                        'netmask': addr.netmask
                    })
        
        metrics['processes'] = {
            'total': len(psutil.pids()),
            'running': len([p for p in psutil.process_iter(['status']) if p.info.get('status') == 'running'])
        }
        
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        metrics['uptime'] = {
            'boot_time': boot_time.isoformat(),
            'days': uptime.days,
            'hours': uptime.seconds // 3600,
            'minutes': (uptime.seconds % 3600) // 60
        }
        
        self._update_prometheus_metrics(metrics)
        
        return metrics
    
    def _update_prometheus_metrics(self, metrics: Dict):
        """更新Prometheus指标"""
        try:
            self._prometheus_metrics['cpu_usage'].set(metrics['cpu']['usage_percent'])
            self._prometheus_metrics['memory_usage'].set(metrics['memory']['used_percent'])
            self._prometheus_metrics['disk_usage'].set(metrics['disk']['used_percent'])
            self._prometheus_metrics['network_bytes_sent'].inc(metrics['network']['bytes_sent'])
            self._prometheus_metrics['network_bytes_recv'].inc(metrics['network']['bytes_recv'])
        except Exception:
            pass
    
    def collect_app_metrics(self) -> Dict:
        """采集应用指标"""
        metrics = {}
        
        metrics['timestamp'] = datetime.now().isoformat()
        metrics['python'] = {
            'version': os.sys.version.split()[0],
            'pid': os.getpid(),
            'ppid': os.getppid()
        }
        
        try:
            process = psutil.Process(os.getpid())
            metrics['process'] = {
                'memory_mb': round(process.memory_info().rss / (1024**2), 2),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
        except Exception as e:
            metrics['process'] = {'error': str(e)}
        
        return metrics
    
    def collect_logs(self, lines: int = 50) -> Dict:
        """采集日志"""
        logs = {}
        
        try:
            log_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/logs'
            if os.path.exists(log_dir):
                log_files = sorted(os.listdir(log_dir))
                
                for log_file in log_files[-5:]:
                    file_path = os.path.join(log_dir, log_file)
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.readlines()[-lines:]
                                logs[log_file] = {
                                    'lines': content,
                                    'count': len(content)
                                }
                        except Exception:
                            pass
        except Exception as e:
            logs['error'] = str(e)
        
        return logs
    
    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式指标"""
        try:
            from prometheus_client import generate_latest
            return generate_latest().decode('utf-8')
        except ImportError:
            return "# HELP mtscos_cpu_usage_percent CPU usage percentage\n# TYPE mtscos_cpu_usage_percent gauge\nmtscos_cpu_usage_percent 0\n"
    
    def format_telegraf(self, metrics: Dict) -> str:
        """格式化为Telegraf格式"""
        lines = []
        timestamp = int(time.time() * 10**9)
        
        cpu = metrics.get('cpu', {})
        lines.append(f"cpu,host={socket.gethostname()} usage_percent={cpu.get('usage_percent', 0)},count={cpu.get('count', 0)} {timestamp}")
        
        memory = metrics.get('memory', {})
        lines.append(f"memory,host={socket.gethostname()} used_percent={memory.get('used_percent', 0)},used_gb={memory.get('used_gb', 0)} {timestamp}")
        
        disk = metrics.get('disk', {})
        lines.append(f"disk,host={socket.gethostname()} used_percent={disk.get('used_percent', 0)},used_gb={disk.get('used_gb', 0)},free_gb={disk.get('free_gb', 0)} {timestamp}")
        
        network = metrics.get('network', {})
        lines.append(f"network,host={socket.gethostname()} bytes_sent={network.get('bytes_sent', 0)},bytes_recv={network.get('bytes_recv', 0)} {timestamp}")
        
        return '\n'.join(lines)
    
    def format_loki(self, metrics: Dict) -> Dict:
        """格式化为Loki格式"""
        streams = []
        
        labels = {
            'app': 'mtscos',
            'host': socket.gethostname(),
            'type': 'metrics'
        }
        
        entries = []
        
        cpu_msg = f"CPU: {metrics.get('cpu', {}).get('usage_percent', 0)}% | Memory: {metrics.get('memory', {}).get('used_percent', 0)}% | Disk: {metrics.get('disk', {}).get('used_percent', 0)}%"
        entries.append({
            'ts': datetime.now().isoformat() + 'Z',
            'line': cpu_msg
        })
        
        streams.append({
            'stream': labels,
            'values': [[str(int(time.time() * 10**9)), cpu_msg]]
        })
        
        return {'streams': streams}
    
    def push_to_loki(self, metrics: Dict, loki_url: str = None):
        """推送数据到Loki"""
        try:
            import requests
            
            loki_url = loki_url or os.environ.get('LOKI_URL', 'http://localhost:3100/loki/api/v1/push')
            
            payload = self.format_loki(metrics)
            
            response = requests.post(
                loki_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 204:
                logger.info("[监控采集器] 数据已推送到Loki")
                return True
            else:
                logger.warning(f"[监控采集器] 推送Loki失败: {response.status_code}")
                return False
        
        except Exception as e:
            logger.warning(f"[监控采集器] 推送Loki异常: {e}")
            return False
    
    def start_collection(self):
        """启动采集线程"""
        if self.running:
            return
        
        self.running = True
        
        def collect_loop():
            while self.running:
                try:
                    system_metrics = self.collect_system_metrics()
                    app_metrics = self.collect_app_metrics()
                    
                    combined = {**system_metrics, **app_metrics}
                    self.metrics['system'].append(combined)
                    
                    if len(self.metrics['system']) > 100:
                        self.metrics['system'] = self.metrics['system'][-100:]
                    
                    self.push_to_loki(combined)
                    
                except Exception as e:
                    logger.error(f"[监控采集器] 采集循环异常: {e}")
                
                time.sleep(self.collect_interval)
        
        threading.Thread(target=collect_loop, daemon=True).start()
        logger.info("[监控采集器] 采集线程已启动")
    
    def stop_collection(self):
        """停止采集"""
        self.running = False
        logger.info("[监控采集器] 采集线程已停止")


def get_monitoring_collector() -> MonitoringCollector:
    """获取监控采集器实例"""
    return MonitoringCollector()


def init_monitoring():
    """初始化监控采集"""
    collector = get_monitoring_collector()
    collector.start_collection()
    return collector
