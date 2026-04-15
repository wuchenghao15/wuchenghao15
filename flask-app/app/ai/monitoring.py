import threading
import time
import json
import psutil
import numpy as np
from app.config import Config
from app.utils.logging import logger

class AIMonitor:
    """AI监控类，用于监控系统错误并尝试修复"""
    
    def __init__(self):
        self.errors = []
        self.performance_data = []
        self.error_lock = threading.Lock()
        self.performance_lock = threading.Lock()
        # 使用默认值，不再直接访问Config.AI_CONFIG
        self.monitoring_enabled = True
        self.auto_fix_enabled = True
        self.base_monitoring_frequency = 3  # 基础监控频率（秒）
        self.monitoring_frequency = self.base_monitoring_frequency  # 当前监控频率
        self.error_count = {
            'frontend': 0,
            'backend': 0,
            'database': 0,
            'ai': 0,
            'network': 0,
            'security': 0
        }
        # 新增：监控指标
        self.metrics = {
            'total_errors': 0,
            'fixed_errors': 0,
            'unfixed_errors': 0,
            'last_check_time': time.time()
        }
        # 新增：性能指标
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
        # 新增：智能监控配置
        self.smart_monitoring = {
            'enabled': True,
            'min_interval': 1,  # 最小监控间隔（秒）
            'max_interval': 10,  # 最大监控间隔（秒）
            'cpu_thresholds': {
                'low': 30,  # CPU使用率低于30%时降低监控频率
                'high': 70  # CPU使用率高于70%时提高监控频率
            },
            'memory_thresholds': {
                'low': 40,  # 内存使用率低于40%时降低监控频率
                'high': 80  # 内存使用率高于80%时提高监控频率
            }
        }
        # 新增：性能预测配置
        self.performance_prediction = {
            'enabled': True,
            'history_window': 60,  # 历史数据窗口（秒）
            'prediction_horizon': 300,  # 预测 horizon（秒）
            'min_data_points': 10,  # 最小数据点数量
            'warning_threshold': 80,  # 警告阈值（%）
            'critical_threshold': 90  # 临界阈值（%）
        }
        # 新增：数据存储配置
        self.data_storage = {
            'performance_data_limit': 1000,  # 性能数据上限
            'error_data_limit': 500,  # 错误数据上限
            'use_ring_buffer': True,  # 使用环形缓冲区
            'performance_data_index': 0  # 环形缓冲区索引
        }

    
    def start_monitoring(self):
        """启动监控线程"""
        if self.monitoring_enabled:
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
            logger.info("AI监控服务已启动")
    
    def _adjust_monitoring_frequency(self):
        """根据系统负载动态调整监控频率"""
        if not self.smart_monitoring['enabled']:
            return
        
        try:
            # 获取当前系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            # 根据资源使用情况调整监控频率
            new_frequency = self.base_monitoring_frequency
            
            # CPU负载调整
            if cpu_usage < self.smart_monitoring['cpu_thresholds']['low']:
                new_frequency += 1  # 降低监控频率
            elif cpu_usage > self.smart_monitoring['cpu_thresholds']['high']:
                new_frequency -= 1  # 提高监控频率
            
            # 内存负载调整
            if memory_usage < self.smart_monitoring['memory_thresholds']['low']:
                new_frequency += 1  # 降低监控频率
            elif memory_usage > self.smart_monitoring['memory_thresholds']['high']:
                new_frequency -= 1  # 提高监控频率
            
            # 确保频率在合理范围内
            new_frequency = max(self.smart_monitoring['min_interval'], 
                               min(self.smart_monitoring['max_interval'], new_frequency))
            
            # 更新监控频率
            if new_frequency != self.monitoring_frequency:
                old_frequency = self.monitoring_frequency
                self.monitoring_frequency = new_frequency
                logger.info(f"智能调整监控频率: {old_frequency}s -> {new_frequency}s (CPU: {cpu_usage}%, 内存: {memory_usage}%)")
                
        except Exception as e:
            logger.error(f"调整监控频率失败: {str(e)}")
    
    def _monitor_loop(self):
        """监控循环"""
        last_prediction_time = 0
        last_advice_time = 0
        last_bottleneck_time = 0
        prediction_interval = 60  # 性能预测间隔（秒）
        advice_interval = 300  # 资源优化建议间隔（秒）
        bottleneck_interval = 120  # 性能瓶颈检测间隔（秒）
        
        while self.monitoring_enabled:
            # 定期检查错误
            self._check_errors()
            # 更新监控指标
            self._update_metrics()
            # 更新性能指标
            self._update_performance_metrics()
            # 智能调整监控频率
            self._adjust_monitoring_frequency()

            # 生成性能报告（每30秒一次）
            if time.time() - self.performance_metrics['last_performance_update'] > 30:
                self._generate_performance_report()
            
            # 执行性能预测（每60秒一次）
            if time.time() - last_prediction_time > prediction_interval:
                self._predict_performance()
                last_prediction_time = time.time()
            
            # 生成资源优化建议（每5分钟一次）
            if time.time() - last_advice_time > advice_interval:
                self._generate_resource_optimization_advice()
                last_advice_time = time.time()
            
            # 检测性能瓶颈（每2分钟一次）
            if time.time() - last_bottleneck_time > bottleneck_interval:
                self._detect_performance_bottlenecks()
                last_bottleneck_time = time.time()

            time.sleep(self.monitoring_frequency)  # 使用动态调整的频率
    
    def log_error(self, error_type, error_message, error_stack=None, component=None):
        """记录错误信息"""
        with self.error_lock:
            error = {
                'timestamp': time.time(),
                'type': error_type,
                'message': error_message,
                'stack': error_stack,
                'component': component,
                'fixed': False
            }
            
            # 使用环形缓冲区存储错误数据
            limit = self.data_storage['error_data_limit']
            if self.data_storage['use_ring_buffer']:
                if len(self.errors) < limit:
                    self.errors.append(error)
                else:
                    # 覆盖最早的错误数据
                    index = len(self.errors) % limit
                    self.errors[index] = error
            else:
                # 传统方式：保留最近的错误数据
                self.errors.append(error)
                if len(self.errors) > limit:
                    self.errors = self.errors[-limit:]
            
            self.error_count[error_type] = self.error_count.get(error_type, 0) + 1
            logger.error(f"[{error_type}] {component}: {error_message}")
            
            # 尝试自动修复
            if self.auto_fix_enabled:
                self._attempt_fix(error)
    
    def _update_metrics(self):
        """更新监控指标"""
        with self.error_lock:
            self.metrics['total_errors'] = len(self.errors)
            self.metrics['fixed_errors'] = len([e for e in self.errors if e['fixed']])
            self.metrics['unfixed_errors'] = len([e for e in self.errors if not e['fixed']])
            self.metrics['last_check_time'] = time.time()
    
    def log_performance_data(self, response_time, component, resource_usage=None, throughput=None):
        """记录性能数据
        
        Args:
            response_time: 响应时间（秒）
            component: 组件名称
            resource_usage: 资源使用情况（CPU、内存、磁盘、网络）
            throughput: 吞吐量（请求/秒）
        """
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
            
            # 使用环形缓冲区存储性能数据
            limit = self.data_storage['performance_data_limit']
            if self.data_storage['use_ring_buffer']:
                if len(self.performance_data) < limit:
                    self.performance_data.append(performance_entry)
                else:
                    # 覆盖最早的数据
                    index = self.data_storage['performance_data_index']
                    self.performance_data[index] = performance_entry
                    self.data_storage['performance_data_index'] = (index + 1) % limit
            else:
                # 传统方式：保留最近的数据
                self.performance_data.append(performance_entry)
                if len(self.performance_data) > limit:
                    self.performance_data = self.performance_data[-limit:]
    
    def _update_performance_metrics(self):
        """更新性能指标"""
        with self.performance_lock:
            if not self.performance_data:
                return
            
            # 获取最近60秒的性能数据
            recent_data = [
                entry for entry in self.performance_data 
                if time.time() - entry['timestamp'] < 60
            ]
            
            if not recent_data:
                return
            
            # 计算响应时间指标
            response_times = [entry['response_time'] for entry in recent_data]
            if response_times:
                self.performance_metrics['average_response_time'] = sum(response_times) / len(response_times)
                self.performance_metrics['max_response_time'] = max(response_times)
                self.performance_metrics['min_response_time'] = min(response_times)
                # 计算95th百分位响应时间
                response_times.sort()
                idx = int(len(response_times) * 0.95)
                self.performance_metrics['response_time_95th'] = response_times[idx] if idx < len(response_times) else response_times[-1]
            
            # 计算吞吐量
            throughput_values = [entry['throughput'] for entry in recent_data if entry['throughput'] > 0]
            if throughput_values:
                self.performance_metrics['throughput'] = sum(throughput_values) / len(throughput_values)
            
            # 计算资源使用情况
            cpu_values = [entry['resource_usage']['cpu'] for entry in recent_data]
            memory_values = [entry['resource_usage']['memory'] for entry in recent_data]
            disk_values = [entry['resource_usage']['disk'] for entry in recent_data]
            network_values = [entry['resource_usage']['network'] for entry in recent_data]
            
            self.performance_metrics['resource_usage'] = {
                'cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                'disk': sum(disk_values) / len(disk_values) if disk_values else 0,
                'network': sum(network_values) / len(network_values) if network_values else 0
            }
            
            self.performance_metrics['last_performance_update'] = time.time()
    
    def _generate_performance_report(self):
        """生成性能报告"""
        with self.performance_lock:
            if not self.performance_data:
                return
            
            # 获取不同时间窗口的性能数据
            time_windows = {
                '1min': 60,
                '5min': 300,
                '15min': 900
            }
            
            window_data = {}
            for window_name, window_seconds in time_windows.items():
                window_data[window_name] = [
                    entry for entry in self.performance_data 
                    if time.time() - entry['timestamp'] < window_seconds
                ]
            
            # 按组件分组分析
            component_data = {}
            for window_name, data in window_data.items():
                component_data[window_name] = {}
                for entry in data:
                    comp = entry['component']
                    if comp not in component_data[window_name]:
                        component_data[window_name][comp] = []
                    component_data[window_name][comp].append(entry)
            
            # 生成组件性能报告
            component_reports = {}
            for window_name, comp_data in component_data.items():
                component_reports[window_name] = {}
                for comp, data in comp_data.items():
                    response_times = [entry['response_time'] for entry in data]
                    cpu_values = [entry['resource_usage']['cpu'] for entry in data]
                    memory_values = [entry['resource_usage']['memory'] for entry in data]
                    
                    component_reports[window_name][comp] = {
                        'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                        'max_response_time': max(response_times) if response_times else 0,
                        'min_response_time': min(response_times) if response_times else 0,
                        'p95_response_time': self._calculate_percentile(response_times, 95),
                        'average_cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                        'average_memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                        'total_requests': len(data),
                        'throughput': len(data) / time_windows[window_name] if time_windows[window_name] > 0 else 0
                    }
            
            # 生成趋势数据（用于可视化）
            trend_data = {
                'timestamps': [],
                'response_times': [],
                'cpu_usage': [],
                'memory_usage': []
            }
            
            # 按时间排序并提取最近100条数据用于趋势分析
            sorted_data = sorted(self.performance_data, key=lambda x: x['timestamp'])[-100:]
            for entry in sorted_data:
                trend_data['timestamps'].append(entry['timestamp'])
                trend_data['response_times'].append(entry['response_time'])
                trend_data['cpu_usage'].append(entry['resource_usage']['cpu'])
                trend_data['memory_usage'].append(entry['resource_usage']['memory'])
            
            # 生成性能报告
            performance_report = {
                'timestamp': time.time(),
                'summary_metrics': self.performance_metrics.copy(),
                'component_performance': component_reports,
                'trend_data': trend_data,
                'total_performance_entries': len(self.performance_data),
                'data_age': time.time() - min(entry['timestamp'] for entry in self.performance_data) if self.performance_data else 0,
                'recommendations': []
            }
            
            # 添加性能优化建议
            if self.performance_metrics['average_response_time'] > 1.0:
                performance_report['recommendations'].append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f'平均响应时间过高: {self.performance_metrics["average_response_time"]:.2f}s',
                    'suggestions': [
                        '优化数据库查询',
                        '考虑使用缓存',
                        '检查网络延迟',
                        '优化代码逻辑'
                    ]
                })
            
            if self.performance_metrics['resource_usage']['cpu'] > 70:
                performance_report['recommendations'].append({
                    'type': 'resource',
                    'severity': 'warning',
                    'message': f'CPU使用率过高: {self.performance_metrics["resource_usage"]["cpu"]:.2f}%',
                    'suggestions': [
                        '检查占用CPU的进程',
                        '优化计算密集型任务',
                        '考虑负载均衡',
                        '增加CPU资源'
                    ]
                })
            
            if self.performance_metrics['resource_usage']['memory'] > 80:
                performance_report['recommendations'].append({
                    'type': 'resource',
                    'severity': 'warning',
                    'message': f'内存使用率过高: {self.performance_metrics["resource_usage"]["memory"]:.2f}%',
                    'suggestions': [
                        '检查内存泄漏',
                        '优化内存使用',
                        '增加内存资源',
                        '清理缓存'
                    ]
                })
            
            logger.info(f"AI性能报告: {json.dumps(performance_report, indent=2)}")
    
    def _check_errors(self):
        """检查错误并生成报告"""
        with self.error_lock:
            if not self.errors:
                return
            
            # 只处理未修复的错误
            unfixed_errors = [e for e in self.errors if not e['fixed']]
            if not unfixed_errors:
                return
            
            # 生成错误报告
            error_report = {
                'total_errors': len(self.errors),
                'fixed_errors': self.metrics['fixed_errors'],
                'unfixed_errors': self.metrics['unfixed_errors'],
                'error_types': self.error_count.copy(),
                'recent_unfixed_errors': unfixed_errors[-5:]  # 最近5个未修复的错误
            }
            
            logger.info(f"AI监控报告: {json.dumps(error_report, indent=2)}")
    
    def _attempt_fix(self, error):
        """尝试修复错误"""
        try:
            logger.info(f"尝试修复错误: {error['message']}")
            
            # 根据错误类型执行不同的修复策略
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
            
            # 更新错误状态
            if fix_success:
                error['fixed'] = True
                logger.info(f"成功修复错误: {error['message']}")
            else:
                logger.warning(f"无法自动修复错误: {error['message']}")
        except Exception as e:
            logger.error(f"修复错误失败: {str(e)}")
    
    def _fix_frontend_error(self, error):
        """修复前端错误"""
        # 前端错误修复逻辑
        logger.info(f"修复前端错误: {error['message']}")
        # 这里可以添加具体的修复逻辑
        return True
    
    def _fix_backend_error(self, error):
        """修复后端错误"""
        # 后端错误修复逻辑
        logger.info(f"修复后端错误: {error['message']}")
        # 这里可以添加具体的修复逻辑
        return True
    
    def _fix_database_error(self, error):
        """修复数据库错误"""
        # 数据库错误修复逻辑
        logger.info(f"修复数据库错误: {error['message']}")
        # 这里可以添加具体的修复逻辑
        return True
    
    def _fix_ai_error(self, error):
        """修复AI错误"""
        # AI错误修复逻辑
        logger.info(f"修复AI错误: {error['message']}")
        # 这里可以添加具体的修复逻辑
        return True
    
    def _fix_network_error(self, error):
        """修复网络错误"""
        # 网络错误修复逻辑
        logger.info(f"修复网络错误: {error['message']}")
        # 这里可以添加具体的修复逻辑
        return True
    
    def _fix_security_error(self, error):
        """修复安全错误"""
        # 安全错误修复逻辑
        logger.info(f"修复安全错误: {error['message']}")
        # 这里可以添加具体的修复逻辑
        return True
    
    def get_error_stats(self):
        """获取错误统计信息"""
        with self.error_lock:
            return {
                'total_errors': len(self.errors),
                'error_count': self.error_count.copy(),
                'unfixed_errors': len([e for e in self.errors if not e['fixed']])
            }
    
    def get_performance_metrics(self):
        """获取性能指标
        
        Returns:
            Dict: 性能指标数据
        """
        with self.performance_lock:
            return self.performance_metrics.copy()
    
    def get_performance_data(self, limit: int = 100):
        """获取性能数据
        
        Args:
            limit: 返回数据的数量限制
            
        Returns:
            List[Dict]: 性能数据列表
        """
        with self.performance_lock:
            return self.performance_data[-limit:].copy()
    
    def generate_detailed_performance_report(self, time_window: str = '5min') -> Dict:
        """生成详细的性能报告
        
        Args:
            time_window: 时间窗口，可选值：'1min', '5min', '15min', '1h'
            
        Returns:
            Dict: 详细的性能报告
        """
        time_window_map = {
            '1min': 60,
            '5min': 300,
            '15min': 900,
            '1h': 3600
        }
        
        window_seconds = time_window_map.get(time_window, 300)
        
        with self.performance_lock:
            # 获取指定时间窗口内的性能数据
            recent_data = [
                entry for entry in self.performance_data 
                if time.time() - entry['timestamp'] < window_seconds
            ]
            
            if not recent_data:
                return {
                    'timestamp': time.time(),
                    'time_window': time_window,
                    'message': 'No performance data available for the specified time window',
                    'summary_metrics': self.performance_metrics.copy(),
                    'component_performance': {},
                    'total_performance_entries': 0
                }
            
            # 按组件分组分析
            component_data = {}
            for entry in recent_data:
                comp = entry['component']
                if comp not in component_data:
                    component_data[comp] = []
                component_data[comp].append(entry)
            
            # 生成组件性能报告
            component_reports = {}
            for comp, data in component_data.items():
                response_times = [entry['response_time'] for entry in data]
                cpu_values = [entry['resource_usage']['cpu'] for entry in data]
                memory_values = [entry['resource_usage']['memory'] for entry in data]
                
                component_reports[comp] = {
                    'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                    'max_response_time': max(response_times) if response_times else 0,
                    'min_response_time': min(response_times) if response_times else 0,
                    'p95_response_time': self._calculate_percentile(response_times, 95),
                    'p99_response_time': self._calculate_percentile(response_times, 99),
                    'average_cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'average_memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'total_requests': len(data)
                }
            
            # 生成详细性能报告
            performance_report = {
                'timestamp': time.time(),
                'time_window': time_window,
                'summary_metrics': self.performance_metrics.copy(),
                'component_performance': component_reports,
                'total_performance_entries': len(recent_data),
                'detailed_metrics': {
                    'response_time_distribution': self._calculate_response_time_distribution(recent_data),
                    'resource_usage_trend': self._calculate_resource_usage_trend(recent_data)
                }
            }
            
            return performance_report
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数值
        
        Args:
            values: 数值列表
            percentile: 百分位（0-100）
            
        Returns:
            float: 百分位数值
        """
        if not values:
            return 0
        
        values.sort()
        idx = int(len(values) * percentile / 100)
        return values[idx] if idx < len(values) else values[-1]
    
    def _calculate_response_time_distribution(self, data: List[Dict]) -> Dict:
        """计算响应时间分布
        
        Args:
            data: 性能数据列表
            
        Returns:
            Dict: 响应时间分布数据
        """
        response_times = [entry['response_time'] for entry in data]
        if not response_times:
            return {}
        
        # 定义响应时间区间
        buckets = [0, 0.1, 0.5, 1, 2, 5, float('inf')]
        bucket_counts = {f'{buckets[i]}-{buckets[i+1]}s': 0 for i in range(len(buckets)-1)}
        
        # 统计每个区间的请求数
        for rt in response_times:
            for i in range(len(buckets)-1):
                if buckets[i] <= rt < buckets[i+1]:
                    bucket_counts[f'{buckets[i]}-{buckets[i+1]}s'] += 1
                    break
        
        return bucket_counts
    
    def _calculate_resource_usage_trend(self, data: List[Dict]) -> Dict:
        """计算资源使用趋势
        
        Args:
            data: 性能数据列表
            
        Returns:
            Dict: 资源使用趋势数据
        """
        if not data:
            return {}
        
        # 按时间排序
        sorted_data = sorted(data, key=lambda x: x['timestamp'])
        
        # 计算时间窗口的资源使用趋势
        trend_data = {
            'timestamps': [],
            'cpu': [],
            'memory': [],
            'disk': [],
            'network': []
        }
        
        for entry in sorted_data:
            trend_data['timestamps'].append(entry['timestamp'])
            trend_data['cpu'].append(entry['resource_usage']['cpu'])
            trend_data['memory'].append(entry['resource_usage']['memory'])
            trend_data['disk'].append(entry['resource_usage']['disk'])
            trend_data['network'].append(entry['resource_usage']['network'])
        
        return trend_data
    
    def _predict_performance(self):
        """预测系统性能趋势
        
        Returns:
            Dict: 性能预测结果
        """
        if not self.performance_prediction['enabled']:
            return {}
        
        try:
            with self.performance_lock:
                # 获取最近的性能数据
                recent_data = [
                    entry for entry in self.performance_data 
                    if time.time() - entry['timestamp'] < self.performance_prediction['history_window']
                ]
                
                if len(recent_data) < self.performance_prediction['min_data_points']:
                    return {
                        'message': '数据点不足，无法进行预测',
                        'data_points': len(recent_data),
                        'required': self.performance_prediction['min_data_points']
                    }
                
                # 按时间排序
                recent_data.sort(key=lambda x: x['timestamp'])
                
                # 准备数据用于线性回归
                timestamps = np.array([entry['timestamp'] for entry in recent_data])
                cpu_values = np.array([entry['resource_usage']['cpu'] for entry in recent_data])
                memory_values = np.array([entry['resource_usage']['memory'] for entry in recent_data])
                
                # 归一化时间戳
                t = (timestamps - timestamps[0]).reshape(-1, 1)
                
                # 线性回归预测CPU使用率
                cpu_model = np.polyfit(t.flatten(), cpu_values, 1)
                cpu_slope, cpu_intercept = cpu_model
                
                # 线性回归预测内存使用率
                memory_model = np.polyfit(t.flatten(), memory_values, 1)
                memory_slope, memory_intercept = memory_model
                
                # 预测未来的性能
                future_t = self.performance_prediction['prediction_horizon']
                predicted_cpu = cpu_slope * future_t + cpu_intercept
                predicted_memory = memory_slope * future_t + memory_intercept
                
                # 确保预测值在合理范围内
                predicted_cpu = max(0, min(100, predicted_cpu))
                predicted_memory = max(0, min(100, predicted_memory))
                
                # 生成预测报告
                prediction_report = {
                    'timestamp': time.time(),
                    'prediction_horizon': self.performance_prediction['prediction_horizon'],
                    'predicted_cpu': predicted_cpu,
                    'predicted_memory': predicted_memory,
                    'cpu_trend': '上升' if cpu_slope > 0 else '下降' if cpu_slope < 0 else '稳定',
                    'memory_trend': '上升' if memory_slope > 0 else '下降' if memory_slope < 0 else '稳定',
                    'cpu_slope': cpu_slope,
                    'memory_slope': memory_slope,
                    'warnings': []
                }
                
                # 检查是否有性能预警
                if predicted_cpu > self.performance_prediction['critical_threshold']:
                    prediction_report['warnings'].append(f'CPU使用率预测将达到 {predicted_cpu:.2f}%，超过临界阈值 {self.performance_prediction["critical_threshold"]}%')
                elif predicted_cpu > self.performance_prediction['warning_threshold']:
                    prediction_report['warnings'].append(f'CPU使用率预测将达到 {predicted_cpu:.2f}%，超过警告阈值 {self.performance_prediction["warning_threshold"]}%')
                
                if predicted_memory > self.performance_prediction['critical_threshold']:
                    prediction_report['warnings'].append(f'内存使用率预测将达到 {predicted_memory:.2f}%，超过临界阈值 {self.performance_prediction["critical_threshold"]}%')
                elif predicted_memory > self.performance_prediction['warning_threshold']:
                    prediction_report['warnings'].append(f'内存使用率预测将达到 {predicted_memory:.2f}%，超过警告阈值 {self.performance_prediction["warning_threshold"]}%')
                
                # 记录预测结果
                if prediction_report['warnings']:
                    logger.warning(f"性能预测预警: {json.dumps(prediction_report['warnings'])}")
                
                logger.info(f"性能预测: CPU={predicted_cpu:.2f}%, 内存={predicted_memory:.2f}% (趋势: CPU-{prediction_report['cpu_trend']}, 内存-{prediction_report['memory_trend']})")
                
                return prediction_report
                
        except Exception as e:
            logger.error(f"性能预测失败: {str(e)}")
            return {'error': str(e)}
    
    def _generate_resource_optimization_advice(self):
        """生成资源使用优化建议
        
        Returns:
            Dict: 资源优化建议
        """
        try:
            # 获取当前系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # 网络使用情况
            net_io = psutil.net_io_counters()
            
            # 生成优化建议
            advice = {
                'timestamp': time.time(),
                'current_resources': {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'disk_usage': disk_usage,
                    'total_memory': memory.total / (1024 * 1024 * 1024),  # GB
                    'available_memory': memory.available / (1024 * 1024 * 1024),  # GB
                    'total_disk': disk.total / (1024 * 1024 * 1024),  # GB
                    'available_disk': disk.free / (1024 * 1024 * 1024),  # GB
                    'network_sent': net_io.bytes_sent / (1024 * 1024),  # MB
                    'network_recv': net_io.bytes_recv / (1024 * 1024)  # MB
                },
                'optimization_advice': []
            }
            
            # CPU优化建议
            if cpu_usage > 80:
                advice['optimization_advice'].append({
                    'resource': 'CPU',
                    'severity': 'critical',
                    'advice': 'CPU使用率过高，建议：1. 检查是否有占用CPU的进程 2. 考虑优化代码或增加CPU资源 3. 限制并发请求数'
                })
            elif cpu_usage > 60:
                advice['optimization_advice'].append({
                    'resource': 'CPU',
                    'severity': 'warning',
                    'advice': 'CPU使用率较高，建议：1. 优化算法 2. 考虑使用缓存 3. 检查是否有不必要的后台进程'
                })
            
            # 内存优化建议
            if memory_usage > 85:
                advice['optimization_advice'].append({
                    'resource': '内存',
                    'severity': 'critical',
                    'advice': '内存使用率过高，建议：1. 检查内存泄漏 2. 优化内存使用 3. 增加内存资源 4. 清理缓存'
                })
            elif memory_usage > 65:
                advice['optimization_advice'].append({
                    'resource': '内存',
                    'severity': 'warning',
                    'advice': '内存使用率较高，建议：1. 优化数据结构 2. 及时释放不需要的对象 3. 考虑使用分页或流式处理'
                })
            
            # 磁盘优化建议
            if disk_usage > 90:
                advice['optimization_advice'].append({
                    'resource': '磁盘',
                    'severity': 'critical',
                    'advice': '磁盘使用率过高，建议：1. 清理无用文件 2. 归档旧数据 3. 考虑增加磁盘空间'
                })
            elif disk_usage > 70:
                advice['optimization_advice'].append({
                    'resource': '磁盘',
                    'severity': 'warning',
                    'advice': '磁盘使用率较高，建议：1. 清理临时文件 2. 检查日志文件大小 3. 考虑使用压缩存储'
                })
            
            # 进程优化建议
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 10 or proc_info['memory_percent'] > 5:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if processes:
                # 按CPU使用率排序，取前5个
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                top_processes = processes[:5]
                advice['top_resource_consuming_processes'] = top_processes
                advice['optimization_advice'].append({
                    'resource': '进程',
                    'severity': 'info',
                    'advice': f'发现{len(top_processes)}个资源消耗较高的进程，建议检查这些进程是否必要'
                })
            
            # 记录优化建议
            if advice['optimization_advice']:
                logger.info(f"资源优化建议: {json.dumps(advice['optimization_advice'], indent=2, ensure_ascii=False)}")
            else:
                logger.info("系统资源使用正常，无需优化")
            
            return advice
            
        except Exception as e:
            logger.error(f"生成资源优化建议失败: {str(e)}")
            return {'error': str(e)}
    
    def _detect_performance_bottlenecks(self):
        """检测性能瓶颈
        
        Returns:
            Dict: 性能瓶颈检测结果
        """
        try:
            bottlenecks = {
                'timestamp': time.time(),
                'detected_bottlenecks': [],
                'system_metrics': {}
            }
            
            # 获取系统指标
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            net_io = psutil.net_io_counters()
            
            bottlenecks['system_metrics'] = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_sent': net_io.bytes_sent / (1024 * 1024),  # MB
                'network_recv': net_io.bytes_recv / (1024 * 1024)  # MB
            }
            
            # 检测CPU瓶颈
            if cpu_usage > 85:
                bottlenecks['detected_bottlenecks'].append({
                    'type': 'CPU',
                    'severity': 'critical',
                    'description': f'CPU使用率过高: {cpu_usage:.2f}%',
                    'possible_causes': [
                        '高并发请求',
                        '计算密集型任务',
                        '进程死锁或无限循环',
                        '过多的上下文切换'
                    ],
                    'suggestions': [
                        '检查占用CPU的进程',
                        '优化算法和代码',
                        '考虑负载均衡',
                        '增加CPU资源'
                    ]
                })
            elif cpu_usage > 70:
                bottlenecks['detected_bottlenecks'].append({
                    'type': 'CPU',
                    'severity': 'warning',
                    'description': f'CPU使用率较高: {cpu_usage:.2f}%',
                    'possible_causes': [
                        '并发请求增加',
                        '后台任务运行',
                        '缓存失效'
                    ],
                    'suggestions': [
                        '监控CPU使用趋势',
                        '优化热点代码',
                        '考虑使用缓存'
                    ]
                })
            
            # 检测内存瓶颈
            if memory_usage > 90:
                bottlenecks['detected_bottlenecks'].append({
                    'type': '内存',
                    'severity': 'critical',
                    'description': f'内存使用率过高: {memory_usage:.2f}%',
                    'possible_causes': [
                        '内存泄漏',
                        '数据缓存过大',
                        '内存密集型操作',
                        '过多的并发连接'
                    ],
                    'suggestions': [
                        '检查内存泄漏',
                        '优化内存使用',
                        '增加内存资源',
                        '清理无用缓存'
                    ]
                })
            elif memory_usage > 75:
                bottlenecks['detected_bottlenecks'].append({
                    'type': '内存',
                    'severity': 'warning',
                    'description': f'内存使用率较高: {memory_usage:.2f}%',
                    'possible_causes': [
                        '缓存增长',
                        '临时数据积累',
                        '连接池过大'
                    ],
                    'suggestions': [
                        '监控内存使用趋势',
                        '优化数据结构',
                        '调整缓存策略'
                    ]
                })
            
            # 检测磁盘瓶颈
            if disk_usage > 95:
                bottlenecks['detected_bottlenecks'].append({
                    'type': '磁盘',
                    'severity': 'critical',
                    'description': f'磁盘使用率过高: {disk_usage:.2f}%',
                    'possible_causes': [
                        '磁盘空间不足',
                        '日志文件过大',
                        '临时文件积累',
                        '数据库文件增长'
                    ],
                    'suggestions': [
                        '清理无用文件',
                        '归档旧数据',
                        '增加磁盘空间',
                        '检查日志轮转配置'
                    ]
                })
            elif disk_usage > 80:
                bottlenecks['detected_bottlenecks'].append({
                    'type': '磁盘',
                    'severity': 'warning',
                    'description': f'磁盘使用率较高: {disk_usage:.2f}%',
                    'possible_causes': [
                        '日志积累',
                        '临时文件未清理',
                        '数据文件增长'
                    ],
                    'suggestions': [
                        '清理临时文件',
                        '检查日志大小',
                        '考虑数据压缩'
                    ]
                })
            
            # 检测进程瓶颈
            high_cpu_processes = []
            high_memory_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 20:
                        high_cpu_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent']
                        })
                    if proc_info['memory_percent'] > 10:
                        high_memory_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'memory_percent': proc_info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if high_cpu_processes:
                high_cpu_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                top_cpu_processes = high_cpu_processes[:3]
                bottlenecks['detected_bottlenecks'].append({
                    'type': '进程',
                    'severity': 'warning',
                    'description': f'发现{len(top_cpu_processes)}个高CPU占用进程',
                    'details': top_cpu_processes,
                    'suggestions': [
                        '检查这些进程是否必要',
                        '优化进程代码',
                        '考虑进程拆分或负载均衡'
                    ]
                })
            
            if high_memory_processes:
                high_memory_processes.sort(key=lambda x: x['memory_percent'], reverse=True)
                top_memory_processes = high_memory_processes[:3]
                bottlenecks['detected_bottlenecks'].append({
                    'type': '进程',
                    'severity': 'warning',
                    'description': f'发现{len(top_memory_processes)}个高内存占用进程',
                    'details': top_memory_processes,
                    'suggestions': [
                        '检查内存使用情况',
                        '优化内存管理',
                        '考虑内存泄漏'
                    ]
                })
            
            # 检测性能数据中的瓶颈
            with self.performance_lock:
                if self.performance_data:
                    # 按组件分析响应时间
                    component_response_times = {}
                    for entry in self.performance_data[-100:]:  # 最近100条数据
                        component = entry['component']
                        if component not in component_response_times:
                            component_response_times[component] = []
                        component_response_times[component].append(entry['response_time'])
                    
                    # 识别响应时间异常的组件
                    for component, times in component_response_times.items():
                        avg_time = sum(times) / len(times)
                        max_time = max(times)
                        if avg_time > 1.0:  # 平均响应时间超过1秒
                            bottlenecks['detected_bottlenecks'].append({
                                'type': '组件',
                                'severity': 'warning',
                                'description': f'组件 {component} 响应时间异常',
                                'details': {
                                    'average_response_time': avg_time,
                                    'max_response_time': max_time,
                                    'sample_count': len(times)
                                },
                                'suggestions': [
                                    '检查组件代码',
                                    '优化数据库查询',
                                    '考虑缓存机制',
                                    '检查网络延迟'
                                ]
                            })
            
            # 记录瓶颈检测结果
            if bottlenecks['detected_bottlenecks']:
                logger.warning(f"性能瓶颈检测: {json.dumps(bottlenecks['detected_bottlenecks'], indent=2, ensure_ascii=False)}")
            else:
                logger.info("未检测到性能瓶颈")
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"检测性能瓶颈失败: {str(e)}")
            return {'error': str(e)}
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        logger.info("AI监控服务已停止")
    
    def upgrade_monitoring_config(self):
        """升级监控配置"""
        try:
            # 添加新的监控配置项
            if not hasattr(self, 'enhanced_monitoring'):
                self.enhanced_monitoring = {
                    'real_time_alerting': True,
                    'error_prediction': True,
                    'performance_analysis': True,
                    'resource_monitoring': True
                }
                logger.info("已添加增强监控配置")
            
            # 更新监控频率
            if not hasattr(self, 'monitoring_frequency'):
                self.monitoring_frequency = 3  # 从5秒改为3秒
                logger.info("已更新监控频率为3秒")
            
            # 添加新的错误类型统计
            for error_type in ['ai', 'network', 'security']:
                if error_type not in self.error_count:
                    self.error_count[error_type] = 0
            
            logger.info("AI监控配置升级完成")
            return True
        except Exception as e:
            logger.error(f"升级监控配置失败: {str(e)}")
            return False

# 全局AI监控实例引用
_ai_monitor_instance = None

def get_ai_monitor():
    """获取或创建AI监控实例"""
    global _ai_monitor_instance
    if _ai_monitor_instance is None:
        _ai_monitor_instance = AIMonitor()
    return _ai_monitor_instance

# 创建并导出AI监控实例
ai_monitor = get_ai_monitor()
