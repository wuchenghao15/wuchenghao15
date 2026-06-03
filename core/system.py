# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System management module - Enhanced Version 2.0
"""

import os
import sys
import subprocess
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from collections import deque
from .config import config
from .logging import logger
import logging

class PerformanceMonitor:
    """Performance metrics collector and monitor"""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.timestamps = deque(maxlen=history_size)
        self._lock = threading.Lock()
    
    def record_metrics(self) -> None:
        """Record current metrics"""
        with self._lock:
            self.cpu_history.append(psutil.cpu_percent())
            self.memory_history.append(psutil.virtual_memory().percent)
            self.disk_history.append(psutil.disk_usage('/').percent)
            self.timestamps.append(datetime.now().isoformat())
    
    def get_metrics_history(self) -> Dict[str, Any]:
        """Get historical metrics"""
        with self._lock:
            return {
                "cpu": list(self.cpu_history),
                "memory": list(self.memory_history),
                "disk": list(self.disk_history),
                "timestamps": list(self.timestamps)
            }
    
    def get_averages(self) -> Dict[str, float]:
        """Get average metrics from history"""
        with self._lock:
            return {
                "cpu_avg": sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
                "memory_avg": sum(self.memory_history) / len(self.memory_history) if self.memory_history else 0,
                "disk_avg": sum(self.disk_history) / len(self.disk_history) if self.disk_history else 0
            }
    
    def get_peaks(self) -> Dict[str, float]:
        """Get peak metrics from history"""
        with self._lock:
            return {
                "cpu_peak": max(self.cpu_history) if self.cpu_history else 0,
                "memory_peak": max(self.memory_history) if self.memory_history else 0,
                "disk_peak": max(self.disk_history) if self.disk_history else 0
            }

class SystemManager:
    """Enhanced system management and monitoring"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.version = "3.2.0"
        self.performance_monitor = PerformanceMonitor()
        self._health_check_callbacks: List[Callable[[], Dict[str, Any]]] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self.performance_monitoring_enabled = config.get("system.performance_monitoring_enabled", True)
        
        if self.performance_monitoring_enabled:
            self._start_monitoring()
    
    def _start_monitoring(self) -> None:
        """Start background monitoring thread"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        def monitor_loop():
            interval = config.get("system.health_check_interval_seconds", 30)
            while self._monitoring_active:
                try:
                    self.performance_monitor.record_metrics()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
        
        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        cpu_freq = psutil.cpu_freq()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
        
        return {
            "version": self.version,
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu": {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(),
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
                "load_average": load_avg
            },
            "memory": {
                "total": self._format_bytes(psutil.virtual_memory().total),
                "available": self._format_bytes(psutil.virtual_memory().available),
                "used": self._format_bytes(psutil.virtual_memory().used),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": self._format_bytes(psutil.disk_usage('/').total),
                "used": self._format_bytes(psutil.disk_usage('/').used),
                "free": self._format_bytes(psutil.disk_usage('/').free),
                "percent": psutil.disk_usage('/').percent
            },
            "uptime": self.get_uptime(),
            "process_count": len(psutil.pids()),
            "network_io": self.get_network_io(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable string"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 ** 2:
            return f"{bytes_value / 1024:.2f} KB"
        elif bytes_value < 1024 ** 3:
            return f"{bytes_value / (1024 ** 2):.2f} MB"
        else:
            return f"{bytes_value / (1024 ** 3):.2f} GB"
    
    def get_uptime(self) -> str:
        """Get system uptime"""
        delta = datetime.now() - self.start_time
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        return f"{delta.days}d {hours}h {minutes}m {seconds}s"
    
    def get_network_io(self) -> Dict[str, Any]:
        """Get network I/O statistics"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": self._format_bytes(net_io.bytes_sent),
            "bytes_recv": self._format_bytes(net_io.bytes_recv),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout
        }
    
    def get_network_interfaces(self) -> Dict[str, Any]:
        """Get network interfaces information"""
        interfaces = {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for name, addr_list in addrs.items():
            interfaces[name] = {
                "addresses": [],
                "is_up": stats[name].isup if name in stats else False,
                "mtu": stats[name].mtu if name in stats else None,
                "speed": stats[name].speed if name in stats else None
            }
            for addr in addr_list:
                interfaces[name]["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
        
        return interfaces
    
    def get_disk_partitions(self) -> List[Dict[str, Any]]:
        """Get disk partitions information"""
        partitions = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total": self._format_bytes(usage.total),
                    "used": self._format_bytes(usage.used),
                    "free": self._format_bytes(usage.free),
                    "percent": usage.percent
                })
            except (PermissionError, FileNotFoundError):
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "error": "Access denied"
                })
        return partitions
    
    def get_process_info(self, pid: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get detailed process information"""
        if pid is None:
            pid = os.getpid()
        
        try:
            process = psutil.Process(pid)
            with process.oneshot():
                return {
                    "pid": pid,
                    "ppid": process.ppid(),
                    "name": process.name(),
                    "status": process.status(),
                    "cpu_percent": process.cpu_percent(),
                    "cpu_times": {
                        "user": process.cpu_times().user,
                        "system": process.cpu_times().system
                    },
                    "memory_percent": process.memory_percent(),
                    "memory_rss": self._format_bytes(process.memory_info().rss),
                    "memory_vms": self._format_bytes(process.memory_info().vms),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                    "username": process.username(),
                    "num_threads": process.num_threads(),
                    "open_files": len(process.open_files()) if hasattr(process, 'open_files') else None,
                    "cmdline": ' '.join(process.cmdline())
                }
        except psutil.NoSuchProcess:
            return None
    
    def get_all_processes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of processes sorted by CPU usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "memory_percent": proc.info['memory_percent'],
                    "status": proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:limit]
    
    def run_command(self, command: str, timeout: int = 30, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run shell command with enhanced options"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "stdout": "",
                "stderr": "Command timed out",
                "return_code": -1,
                "success": False
            }
        except Exception as e:
            return {
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "success": False
            }
    
    def check_service_status(self, service_name: str) -> str:
        """Check service status"""
        if sys.platform == "darwin":
            result = self.run_command(f"brew services list | grep {service_name}")
        elif sys.platform == "linux":
            result = self.run_command(f"systemctl is-active {service_name}")
        else:
            return "Unknown platform"
        
        if result["return_code"] == 0:
            return "running"
        return "stopped"
    
    def restart_service(self, service_name: str) -> bool:
        """Restart service"""
        if sys.platform == "darwin":
            result = self.run_command(f"brew services restart {service_name}")
        elif sys.platform == "linux":
            result = self.run_command(f"sudo systemctl restart {service_name}")
        else:
            return False
        
        return result["return_code"] == 0
    
    def register_health_check(self, callback: Callable[[], Dict[str, Any]]) -> None:
        """Register custom health check callback"""
        self._health_check_callbacks.append(callback)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        return {
            "current": self.get_system_info(),
            "history": self.performance_monitor.get_metrics_history(),
            "averages": self.performance_monitor.get_averages(),
            "peaks": self.performance_monitor.get_peaks()
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        info = self.get_system_info()
        checks = []
        
        # CPU check
        cpu_ok = info["cpu"]["percent"] < 90
        checks.append({
            "name": "CPU",
            "status": "healthy" if cpu_ok else "warning",
            "value": f"{info['cpu']['percent']}%",
            "threshold": "90%"
        })
        
        # Memory check
        memory_ok = info["memory"]["percent"] < 90
        checks.append({
            "name": "Memory",
            "status": "healthy" if memory_ok else "warning",
            "value": f"{info['memory']['percent']}%",
            "threshold": "90%"
        })
        
        # Disk check
        disk_ok = info["disk"]["percent"] < 90
        disk_status = "healthy" if disk_ok else ("critical" if info["disk"]["percent"] > 95 else "warning")
        checks.append({
            "name": "Disk",
            "status": disk_status,
            "value": f"{info['disk']['percent']}%",
            "threshold": "90%"
        })
        
        # Custom checks
        custom_results = {}
        for callback in self._health_check_callbacks:
            try:
                result = callback()
                custom_results.update(result)
            except Exception as e:
                logger.error(f"Health check callback failed: {e}")
        
        # Overall status
        status = "healthy"
        if any(check["status"] == "warning" for check in checks):
            status = "warning"
        if any(check["status"] == "critical" for check in checks):
            status = "critical"
        
        return {
            "status": status,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_uptime(),
            "checks": checks,
            "custom_checks": custom_results,
            "system_info": info
        }
    
    def log_system_status(self):
        """Log current system status"""
        info = self.get_system_info()
        logger.info(f"System Status: CPU={info['cpu']['percent']}%, Memory={info['memory']['percent']}%, Disk={info['disk']['percent']}%")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "version": self.version,
            "uptime": self.get_uptime(),
            "monitoring_active": self._monitoring_active,
            "performance_monitoring": self.performance_monitoring_enabled,
            "health_report": self.get_health_report()
        }

# Global system manager instance
system = SystemManager()
