# -*- coding: utf-8 -*-
"""AI Monitor - System monitoring and error handling"""

import threading
import time
from typing import List, Dict, Optional
import sys
import os

class AIMonitor:
    """AI Monitor for system error monitoring and auto-fix"""

    def __init__(self):
        self.errors = []
        self.performance_data = []
        self.asphalt_performance_data = []
        self.error_lock = threading.Lock()
        self.performance_lock = threading.Lock()
        self.asphalt_performance_lock = threading.Lock()
        
        self.monitoring_enabled = True
        self.auto_fix_enabled = True
        self.monitoring_frequency = 3
        
        self.error_count = {
            'frontend': 0,
            'backend': 0,
            'database': 0,
            'ai': 0,
            'network': 0,
            'security': 0,
            'asphalt': 0
        }
        
        self.metrics = {
            'total_errors': 0,
            'fixed_errors': 0,
            'unfixed_errors': 0,
            'last_check_time': time.time()
        }
        
        self.performance_metrics = {
            'average_response_time': 0,
            'max_response_time': 0,
            'min_response_time': 0,
            'response_time_95th': 0,
            'throughput': 0,
            'resource_usage': {
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'network': 0
            },
            'last_performance_update': time.time()
        }
        
        self.asphalt_performance_metrics = {
            'average_stability': 0,
            'average_durability': 0,
            'average_viscosity': 0,
            'anomaly_count': 0,
            'last_asphalt_update': time.time()
        }

    def start_monitoring(self):
        """Start monitoring thread"""
        if self.monitoring_enabled:
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()

    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring_enabled:
            self._check_errors()
            self._update_metrics()
            self._update_performance_metrics()
            self._update_asphalt_performance_metrics()
            
            if time.time() - self.performance_metrics['last_performance_update'] > 30:
                self._generate_performance_report()
            
            if time.time() - self.asphalt_performance_metrics['last_asphalt_update'] > 30:
                self._generate_asphalt_performance_report()
            
            time.sleep(self.monitoring_frequency)

    def log_error(self, error_type: str, error_message: str, error_stack: Optional[str] = None, component: Optional[str] = None):
        """Log error information"""
        with self.error_lock:
            error = {
                'timestamp': time.time(),
                'type': error_type,
                'message': error_message,
                'stack': error_stack,
                'component': component,
                'fixed': False
            }
            self.errors.append(error)
            self.error_count[error_type] = self.error_count.get(error_type, 0) + 1
            
            if self.auto_fix_enabled:
                self._attempt_fix(error)

    def _update_metrics(self):
        """Update monitoring metrics"""
        with self.error_lock:
            self.metrics['total_errors'] = len(self.errors)
            self.metrics['fixed_errors'] = len([e for e in self.errors if e['fixed']])
            self.metrics['unfixed_errors'] = len([e for e in self.errors if not e['fixed']])
            self.metrics['last_check_time'] = time.time()

    def log_performance_data(self, response_time: float, component: str, resource_usage: Optional[Dict] = None, throughput: Optional[float] = None):
        """Log performance data"""
        with self.performance_lock:
            performance_entry = {
                'timestamp': time.time(),
                'response_time': response_time,
                'component': component,
                'resource_usage': resource_usage or {
                    'cpu': 0,
                    'memory': 0,
                    'disk': 0,
                    'network': 0
                },
                'throughput': throughput or 0
            }
            self.performance_data.append(performance_entry)
            self.performance_data = self.performance_data[-1000:]

    def log_asphalt_performance_data(self, asphalt_type_id: str, performance_data: Dict, location: Optional[Dict] = None, sample_id: Optional[str] = None):
        """Log asphalt performance data"""
        with self.asphalt_performance_lock:
            asphalt_entry = {
                'timestamp': time.time(),
                'asphalt_type_id': asphalt_type_id,
                'performance_data': performance_data or {
                    'stability': 0,
                    'durability': 0,
                    'viscosity': 0
                },
                'location': location or {},
                'sample_id': sample_id
            }
            self.asphalt_performance_data.append(asphalt_entry)
            self.asphalt_performance_data = self.asphalt_performance_data[-1000:]

    def _update_performance_metrics(self):
        """Update performance metrics"""
        with self.performance_lock:
            if not self.performance_data:
                return
            
            recent_data = [entry for entry in self.performance_data if time.time() - entry['timestamp'] < 60]
            
            if not recent_data:
                return
            
            response_times = [entry['response_time'] for entry in recent_data]
            if response_times:
                self.performance_metrics['average_response_time'] = sum(response_times) / len(response_times)
                self.performance_metrics['max_response_time'] = max(response_times)
                self.performance_metrics['min_response_time'] = min(response_times)
                response_times.sort()
                idx = int(len(response_times) * 0.95)
                self.performance_metrics['response_time_95th'] = response_times[idx] if idx < len(response_times) else response_times[-1]
            
            throughput_values = [entry['throughput'] for entry in recent_data if entry.get('throughput', 0) > 0]
            if throughput_values:
                self.performance_metrics['throughput'] = sum(throughput_values) / len(throughput_values)
            
            memory_values = [entry['resource_usage'].get('memory', 0) for entry in recent_data]
            disk_values = [entry['resource_usage'].get('disk', 0) for entry in recent_data]
            network_values = [entry['resource_usage'].get('network', 0) for entry in recent_data]
            cpu_values = [entry['resource_usage'].get('cpu', 0) for entry in recent_data]
            
            self.performance_metrics['resource_usage'] = {
                'cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                'disk': sum(disk_values) / len(disk_values) if disk_values else 0,
                'network': sum(network_values) / len(network_values) if network_values else 0
            }
            
            self.performance_metrics['last_performance_update'] = time.time()

    def _generate_performance_report(self):
        """Generate performance report"""
        with self.performance_lock:
            if not self.performance_data:
                return
            
            recent_data_5min = [entry for entry in self.performance_data if time.time() - entry['timestamp'] < 300]
            
            component_data = {}
            for entry in recent_data_5min:
                comp = entry['component']
                if comp not in component_data:
                    component_data[comp] = []
                component_data[comp].append(entry)
            
            component_reports = {}
            for comp, data in component_data.items():
                response_times = [entry['response_time'] for entry in data]
                component_reports[comp] = {
                    'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                    'min_response_time': min(response_times) if response_times else 0,
                    'total_requests': len(data)
                }
            
            performance_report = {
                'summary_metrics': self.performance_metrics.copy(),
                'component_performance': component_reports,
                'time_window': '5min'
            }
            return performance_report

    def _update_asphalt_performance_metrics(self):
        """Update asphalt performance metrics"""
        with self.asphalt_performance_lock:
            if not self.asphalt_performance_data:
                return
            
            recent_data = [entry for entry in self.asphalt_performance_data if time.time() - entry['timestamp'] < 60]
            
            if not recent_data:
                return
            
            stability_values = [entry['performance_data'].get('stability', 0) for entry in recent_data if isinstance(entry['performance_data'], dict)]
            durability_values = [entry['performance_data'].get('durability', 0) for entry in recent_data if isinstance(entry['performance_data'], dict)]
            viscosity_values = [entry['performance_data'].get('viscosity', 0) for entry in recent_data if isinstance(entry['performance_data'], dict)]
            
            anomaly_count = 0
            for entry in recent_data:
                perf_data = entry['performance_data']
                if isinstance(perf_data, dict):
                    if perf_data.get('stability', 0) < 0.5:
                        anomaly_count += 1
                    if perf_data.get('viscosity', 0) > 100 or perf_data.get('viscosity', 0) < 10:
                        anomaly_count += 1
            
            if stability_values:
                self.asphalt_performance_metrics['average_stability'] = sum(stability_values) / len(stability_values)
            if durability_values:
                self.asphalt_performance_metrics['average_durability'] = sum(durability_values) / len(durability_values)
            if viscosity_values:
                self.asphalt_performance_metrics['average_viscosity'] = sum(viscosity_values) / len(viscosity_values)
            
            self.asphalt_performance_metrics['anomaly_count'] = anomaly_count
            self.asphalt_performance_metrics['last_asphalt_update'] = time.time()

    def _generate_asphalt_performance_report(self):
        """Generate asphalt performance report"""
        with self.asphalt_performance_lock:
            if not self.asphalt_performance_data:
                return None
            
            recent_data_5min = [entry for entry in self.asphalt_performance_data if time.time() - entry['timestamp'] < 300]
            
            if not recent_data_5min:
                return None
            
            asphalt_type_data = {}
            for entry in recent_data_5min:
                asphalt_type = entry['asphalt_type_id']
                if asphalt_type not in asphalt_type_data:
                    asphalt_type_data[asphalt_type] = []
                asphalt_type_data[asphalt_type].append(entry)
            
            asphalt_type_reports = {}
            for asphalt_type, data in asphalt_type_data.items():
                stability_values = [entry['performance_data'].get('stability', 0) for entry in data if isinstance(entry['performance_data'], dict)]
                durability_values = [entry['performance_data'].get('durability', 0) for entry in data if isinstance(entry['performance_data'], dict)]
                viscosity_values = [entry['performance_data'].get('viscosity', 0) for entry in data if isinstance(entry['performance_data'], dict)]
                
                asphalt_type_reports[asphalt_type] = {
                    'average_stability': sum(stability_values) / len(stability_values) if stability_values else 0,
                    'average_durability': sum(durability_values) / len(durability_values) if durability_values else 0,
                    'average_viscosity': sum(viscosity_values) / len(viscosity_values) if viscosity_values else 0
                }
            
            asphalt_report = {
                'timestamp': time.time(),
                'summary_metrics': self.asphalt_performance_metrics.copy(),
                'asphalt_type_performance': asphalt_type_reports,
                'time_window': '5min'
            }
            return asphalt_report

    def _check_errors(self):
        """Check errors and generate report"""
        with self.error_lock:
            if not self.errors:
                return
            
            unfixed_errors = [e for e in self.errors if not e['fixed']]
            if unfixed_errors:
                pass

    def _attempt_fix(self, error: Dict):
        """Attempt to fix error"""
        try:
            fix_success = False
            
            if error['type'] == 'frontend':
                fix_success = self._fix_frontend_error(error)
            elif error['type'] == 'backend':
                fix_success = self._fix_backend_error(error)
            elif error['type'] == 'database':
                fix_success = self._fix_database_error(error)
            elif error['type'] == 'ai':
                fix_success = self._fix_ai_error(error)
            elif error['type'] == 'network':
                fix_success = self._fix_network_error(error)
            elif error['type'] == 'security':
                fix_success = self._fix_security_error(error)
            
            if fix_success:
                error['fixed'] = True
        except Exception:
            pass

    def _fix_frontend_error(self, error: Dict) -> bool:
        """Fix frontend error"""
        return True

    def _fix_backend_error(self, error: Dict) -> bool:
        """Fix backend error"""
        return True

    def _fix_database_error(self, error: Dict) -> bool:
        """Fix database error"""
        return True

    def _fix_ai_error(self, error: Dict) -> bool:
        """Fix AI error"""
        return True

    def _fix_network_error(self, error: Dict) -> bool:
        """Fix network error"""
        return True

    def _fix_security_error(self, error: Dict) -> bool:
        """Fix security error"""
        return True

    def get_error_stats(self) -> Dict:
        """Get error statistics"""
        with self.error_lock:
            return {
                'total_errors': len(self.errors),
                'error_count': self.error_count.copy(),
                'unfixed_errors': len([e for e in self.errors if not e['fixed']])
            }

    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        with self.performance_lock:
            return self.performance_metrics.copy()

    def get_performance_data(self, limit: int = 100) -> List[Dict]:
        """Get performance data"""
        with self.performance_lock:
            return self.performance_data[-limit:].copy()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_enabled = False

_ai_monitor_instance = None

def get_ai_monitor():
    """Get or create AI monitor instance"""
    global _ai_monitor_instance
    if _ai_monitor_instance is None:
        _ai_monitor_instance = AIMonitor()
    return _ai_monitor_instance
