# -*- coding: utf-8 -*-
"""
AI监控模块
用于监控系统运行状态、性能指标和错误信息,并提供自动修复功能
"""

import threading
import time
import psutil
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import sys

logger = logging.getLogger('ai_monitor')


class AIMonitor:
    """AI监控类:用于监控系统状态、性能指标和错误"""

    def __init__(self):
        """初始化AI监控"""
        self.errors = deque(maxlen=1000)
        self.performance_data = deque(maxlen=500)
        self.error_lock = threading.Lock()
        self.performance_lock = threading.Lock()
        self.monitoring_enabled = True
        self.auto_fix_enabled = True
        self.monitoring_frequency = 3
        self.monitoring_thread = None

        self.error_count = {
            'frontend': 0,
            'backend': 0,
            'database': 0,
            'ai': 0,
            'network': 0,
            'security': 0,
            'vikey': 0,
            'layout': 0,
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
            }
        }

        self.alert_thresholds = {
            'cpu': 80,
            'memory': 85,
            'disk': 90,
            'response_time': 1000,
            'error_rate': 0.05,
            'error_rate_vikey': 0.01,
            'layout_violation_rate': 0.1,
        }

        self.idle_thresholds = {
            'warn': 300,
            'hibernate': 900,
            'reclaim': 1800,
        }

        self.alerts = deque(maxlen=100)
        self.vikey_status = {
            'vikey_present': None,
            'vikey_bound': None,
            'last_probe_time': None,
            'serial': None,
            'consecutive_anomalies': 0,
        }
        self.memorial_theme_state = {
            'current_theme': 'standard',
            'today_date': None,
            'ribbon_text': '',
            'grayscale_enabled': False,
        }
        self.start_monitoring()

        logger.info("AI监控初始化完成")

    def log_error(self, error_type: str, error_message: str, **kwargs):
        """记录错误"""
        with self.error_lock:
            error_entry = {
                'time': time.time(),
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'message': error_message,
                'details': kwargs
            }
            self.errors.append(error_entry)
            self.metrics['total_errors'] += 1

            if error_type in self.error_count:
                self.error_count[error_type] += 1

            logger.info(f"记录错误: [{error_type}] {error_message}")

            if self.auto_fix_enabled:
                self._attempt_auto_fix(error_type, error_message, kwargs)

    def _attempt_auto_fix(self, error_type: str, error_message: str, details: Dict):
        """尝试自动修复错误"""
        try:
            if error_type == 'database':
                self._fix_database_error(details)
            elif error_type == 'network':
                self._fix_network_error(details)
            elif error_type == 'ai':
                self._fix_ai_error(details)

            self.metrics['fixed_errors'] += 1
        except Exception as e:
            logger.error(f"自动修复失败: {str(e)}")
            self.metrics['unfixed_errors'] += 1

    def _fix_database_error(self, details: Dict):
        """修复数据库错误"""
        logger.info("尝试修复数据库错误...")

    def _fix_network_error(self, details: Dict):
        """修复网络错误"""
        logger.info("尝试修复网络错误...")

    def _fix_ai_error(self, details: Dict):
        """修复AI错误"""
        logger.info("尝试修复AI错误...")

    def log_performance(self, response_time: float = None, throughput: float = None, **kwargs):
        """记录性能数据"""
        with self.performance_lock:
            perf_entry = {
                'time': time.time(),
                'timestamp': datetime.now().isoformat()
            }

            if response_time is not None:
                perf_entry['response_time'] = response_time
            if throughput is not None:
                perf_entry['throughput'] = throughput

            perf_entry.update(kwargs)

            self.performance_data.append(perf_entry)
            self._update_performance_metrics()

    def _update_performance_metrics(self):
        """更新性能指标"""
        if not self.performance_data:
            return

        response_times = [p.get('response_time', 0) for p in self.performance_data if 'response_time' in p]
        if response_times:
            self.performance_metrics['average_response_time'] = sum(response_times) / len(response_times)
            self.performance_metrics['max_response_time'] = max(response_times)
            self.performance_metrics['min_response_time'] = min(response_times)

            sorted_times = sorted(response_times)
            idx_95 = int(len(sorted_times) * 0.95)
            self.performance_metrics['response_time_95th'] = sorted_times[idx_95] if sorted_times else 0

        throughputs = [p.get('throughput', 0) for p in self.performance_data if 'throughput' in p]
        if throughputs:
            self.performance_metrics['throughput'] = sum(throughputs) / len(throughputs)

    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            self.performance_metrics['resource_usage'] = {
                'cpu': psutil.cpu_percent(interval=1),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent,
                'network': psutil.net_io_counters()._asdict()
            }

            self._check_alerts()

            self._check_vikey_health()
            self._check_memorial_theme()

        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")

    def _check_alerts(self):
        """检查是否触发告警"""
        usage = self.performance_metrics['resource_usage']

        if usage['cpu'] > self.alert_thresholds['cpu']:
            self._create_alert('cpu', 'HIGH', f"CPU使用率: {usage['cpu']:.1f}%")

        if usage['memory'] > self.alert_thresholds['memory']:
            self._create_alert('memory', 'HIGH', f"内存使用率: {usage['memory']:.1f}%")

        if usage['disk'] > self.alert_thresholds['disk']:
            self._create_alert('disk', 'HIGH', f"磁盘使用率: {usage['disk']:.1f}%")

        if self.performance_metrics['average_response_time'] > self.alert_thresholds['response_time']:
            self._create_alert(
                'response_time',
                'HIGH',
                f"平均响应时间: {self.performance_metrics['average_response_time']:.1f}ms"
            )

    def _check_vikey_health(self):
        """VIKEY硬件密钥健康检测（MTS架构v2.0新增）"""
        try:
            present = False
            bound = False
            serial = None
            try:
                from core.services.vikey_driver import get_vikey_manager
                mgr = get_vikey_manager()
                det = mgr.detect()
                if isinstance(det, dict):
                    devices = det.get('devices') or []
                    for d in devices:
                        if not isinstance(d, dict):
                            continue
                        is_present = bool(d.get('is_present', d.get('present', True)))
                        if is_present:
                            present = True
                            serial = d.get('serial') or d.get('device_serial')
                            binding = d.get('binding') if isinstance(d.get('binding'), dict) else {}
                            b_user = binding.get('username') or d.get('username')
                            b_status = binding.get('binding_status') or binding.get('status') or d.get('binding_status') or ''
                            bound = bool(b_user) or b_status == 'bound'
                            if present and bound:
                                break
            except ImportError:
                try:
                    import urllib.request, json
                    with urllib.request.urlopen('http://127.0.0.1:8888/api/vikey/detect', timeout=2) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        d = data.get('data', data)
                        present = (d.get('present_count') or 0) > 0
                        if present and d.get('devices'):
                            for dev in d['devices']:
                                if dev.get('present') and dev.get('binding_status') == 'bound':
                                    bound = True
                                    serial = dev.get('serial')
                                    break
                except Exception:
                    pass
            except Exception:
                pass
            now = time.time()
            self.vikey_status['vikey_present'] = present
            self.vikey_status['vikey_bound'] = bound
            self.vikey_status['last_probe_time'] = now
            self.vikey_status['serial'] = serial
            abnormal = (present is False or bound is False)
            if abnormal:
                self.vikey_status['consecutive_anomalies'] += 1
                if self.vikey_status['consecutive_anomalies'] >= 3:
                    self._create_alert(
                        'vikey',
                        'CRITICAL',
                        f"VIKEY硬件密钥异常: present={present}, bound={bound}, serial={serial}, 连续异常={self.vikey_status['consecutive_anomalies']}次"
                    )
                    with self.error_lock:
                        self.error_count['vikey'] += 1
                        self.metrics['total_errors'] += 1
            else:
                if self.vikey_status['consecutive_anomalies'] > 0:
                    self.vikey_status['consecutive_anomalies'] = 0
                    logger.info("VIKEY硬件密钥恢复正常")
        except Exception as e:
            logger.error(f"VIKEY健康检测失败: {str(e)}")

    def _check_memorial_theme(self):
        """公祭日主题自动检测（MTS架构v2.0新增）"""
        try:
            today = datetime.now().strftime('%m-%d')
            self.memorial_theme_state['today_date'] = today
            memorial_map = {
                '09-18': '九一八事变纪念日',
                '09-30': '烈士纪念日',
                '12-13': '南京大屠杀死难者国家公祭日',
            }
            if today in memorial_map:
                name = memorial_map[today]
                if self.memorial_theme_state['current_theme'] != 'memorial':
                    self.memorial_theme_state['current_theme'] = 'memorial'
                    self.memorial_theme_state['grayscale_enabled'] = True
                    self.memorial_theme_state['ribbon_text'] = f"国家公祭日·{name}·追思主题"
                    logger.info(f"检测到今日为国家公祭日 [{name}]，自动切换黑灰追思主题")
            else:
                if self.memorial_theme_state['current_theme'] != 'standard':
                    self.memorial_theme_state['current_theme'] = 'standard'
                    self.memorial_theme_state['grayscale_enabled'] = False
                    self.memorial_theme_state['ribbon_text'] = ''
                    logger.info("非公祭日，恢复标准深紫色渐变主题")
        except Exception as e:
            logger.error(f"公祭日主题检测失败: {str(e)}")

    def _create_alert(self, alert_type: str, severity: str, message: str):
        """创建告警"""
        alert = {
            'time': time.time(),
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'severity': severity,
            'message': message
        }
        self.alerts.append(alert)
        logger.warning(f"告警触发: [{severity}] {alert_type} - {message}")

    def start_monitoring(self):
        """启动监控"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("AI监控已在运行中")
            return

        def monitoring_loop():
            while self.monitoring_enabled:
                try:
                    self._collect_system_metrics()
                    time.sleep(self.monitoring_frequency)
                except Exception as e:
                    logger.error(f"监控线程错误: {str(e)}")
                    time.sleep(self.monitoring_frequency)

        self.monitoring_thread = threading.Thread(
            target=monitoring_loop,
            daemon=True,
            name="AI-Monitoring"
        )
        self.monitoring_thread.start()
        logger.info("AI监控启动")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("AI监控停止")

    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        return {
            'metrics': self.metrics,
            'performance': self.performance_metrics,
            'error_count': self.error_count,
            'recent_alerts': list(self.alerts)[-10:]
        }

    def get_errors(self, limit: int = 50, error_type: str = None) -> List[Dict]:
        """获取错误列表"""
        with self.error_lock:
            errors = list(self.errors)

        if error_type:
            errors = [e for e in errors if e.get('error_type') == error_type]

        return errors[-limit:]

    def get_performance_data(self, limit: int = 100) -> List[Dict]:
        """获取性能数据"""
        with self.performance_lock:
            return list(self.performance_data)[-limit:]

    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """获取告警列表"""
        return list(self.alerts)[-limit:]

    def clear_errors(self):
        """清除错误记录"""
        with self.error_lock:
            self.errors.clear()
            self.error_count = {k: 0 for k in self.error_count}
            self.metrics['total_errors'] = 0
            self.metrics['fixed_errors'] = 0
            self.metrics['unfixed_errors'] = 0
        logger.info("错误记录已清除")

    def clear_performance_data(self):
        """清除性能数据"""
        with self.performance_lock:
            self.performance_data.clear()
        logger.info("性能数据已清除")

    def update_thresholds(self, thresholds: Dict):
        """更新告警阈值"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"告警阈值已更新: {thresholds}")

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        usage = self.performance_metrics['resource_usage']

        health_score = 100
        issues = []

        if usage['cpu'] > 80:
            health_score -= 20
            issues.append('CPU使用率过高')
        if usage['memory'] > 85:
            health_score -= 20
            issues.append('内存使用率过高')
        if usage['disk'] > 90:
            health_score -= 20
            issues.append('磁盘使用率过高')

        if self.metrics['total_errors'] > 100:
            health_score -= 20
            issues.append('错误数量过多')

        status = 'healthy'
        if health_score < 60:
            status = 'critical'
        elif health_score < 80:
            status = 'warning'

        return {
            'status': status,
            'health_score': health_score,
            'issues': issues,
            'metrics': self.metrics,
            'resource_usage': usage,
            'vikey': self.vikey_status,
            'memorial_theme': self.memorial_theme_state,
            'architecture': 'MTS v2.0',
        }

    def monitor_employee_idle(self, employee_manager):
        """监控AI员工空闲状态并应用3级空闲策略"""
        if not employee_manager:
            return {'success': False, 'error': 'employee_manager为空'}

        idle_stats = {
            'total': 0,
            'active': 0,
            'idle': 0,
            'hibernated': 0,
            'reclaimed': 0,
            'actions_taken': [],
            'warnings': [],
        }

        for emp_id, employee in employee_manager.employees.items():
            idle_stats['total'] += 1
            
            status = getattr(employee, 'status', 'unknown')
            
            if status == 'active':
                idle_stats['active'] += 1
                
                try:
                    idle_duration = employee.get_idle_duration() if hasattr(employee, 'get_idle_duration') else 0
                except Exception:
                    idle_duration = 0
                
                if idle_duration > self.idle_thresholds['reclaim']:
                    result = employee.reclaim()
                    idle_stats['reclaimed'] += 1
                    idle_stats['actions_taken'].append({
                        'employee_id': emp_id,
                        'name': getattr(employee, 'name', emp_id),
                        'action': 'reclaim',
                        'duration': f"{idle_duration:.1f}s",
                        'message': result.get('message', '')
                    })
                    self._create_alert('employee_idle', 'CRITICAL', f"AI员工 {getattr(employee, 'name', emp_id)} 空闲超30分钟，已回收")
                
                elif idle_duration > self.idle_thresholds['hibernate']:
                    result = employee.hibernate()
                    idle_stats['hibernated'] += 1
                    idle_stats['active'] -= 1
                    idle_stats['actions_taken'].append({
                        'employee_id': emp_id,
                        'name': getattr(employee, 'name', emp_id),
                        'action': 'hibernate',
                        'duration': f"{idle_duration:.1f}s",
                        'message': result.get('message', '')
                    })
                    self._create_alert('employee_idle', 'WARNING', f"AI员工 {getattr(employee, 'name', emp_id)} 空闲超15分钟，已休眠")
                
                elif idle_duration > self.idle_thresholds['warn']:
                    idle_stats['idle'] += 1
                    idle_stats['warnings'].append({
                        'employee_id': emp_id,
                        'name': getattr(employee, 'name', emp_id),
                        'idle_duration': f"{idle_duration:.1f}s"
                    })
            
            elif status == 'hibernated':
                idle_stats['hibernated'] += 1
            
            elif status == 'reclaimed':
                idle_stats['reclaimed'] += 1

        if idle_stats['actions_taken']:
            logger.info(f"AI员工空闲监控: 执行了 {len(idle_stats['actions_taken'])} 个操作")

        return idle_stats


ai_monitor = AIMonitor()
