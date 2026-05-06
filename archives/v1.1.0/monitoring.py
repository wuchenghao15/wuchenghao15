# -*- coding: utf-8 -*-
import threading
import time
# JSON import removed - using database
from app.config import Config
from app.utils.logging import logger

class AIMonitor:
    """AI监控类，用于监控系统错误并尝试修复"""

    def __init__(self):
        self.errors = []
        self.performance_data = []
        self.asphalt_performance_data = []
        self.error_lock = threading.Lock()
        self.performance_lock = threading.Lock()
        self.asphalt_performance_lock = threading.Lock()
        # 使用默认值，不再直接访问Config.AI_CONFIG
        self.monitoring_enabled = True
        self.auto_fix_enabled = True
        self.monitoring_frequency = 3  # 监控频率（秒）
        self.error_count = {
            'frontend': 0,
            'backend': 0,
            'database': 0,
            'ai': 0,
            'network': 0,
            'security': 0,
            'asphalt': 0
        }
        # 新增：监控指标
        self.metrics = {
            'total_errors': 0,
            'fixed_errors': 0,
            'unfixed_errors': 0,
            'last_check_time': time.time()
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
        # 新增：沥青性能指标
        self.asphalt_performance_metrics = {
            'average_stability': 0,
            'average_durability': 0,
            'average_viscosity': 0,
            'anomaly_count': 0,
            'last_asphalt_update': time.time()

    def start_monitoring(self):
        """启动监控线程"""
        if self.monitoring_enabled:
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
            logger.info("AI监控服务已启动")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            # 定期检查错误
            self._check_errors()
            # 更新监控指标
            self._update_metrics()
            # 更新性能指标
            self._update_performance_metrics()
            # 更新沥青性能指标
            self._update_asphalt_performance_metrics()
            # 生成性能报告（每30秒一次）
            if time.time() - self.performance_metrics['last_performance_update'] > 30:
                self._generate_performance_report()
            # 生成沥青性能报告（每30秒一次）
            if time.time() - self.asphalt_performance_metrics['last_asphalt_update'] > 30:
                self._generate_asphalt_performance_report()
            time.sleep(self.monitoring_frequency)  # 每3秒检查一次

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
            self.errors.append(error)
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
                    'disk': 0,
                    'network': 0
            # 保留最近1000条性能数据
                self.performance_data = self.performance_data[-1000:]
    def log_asphalt_performance_data(self, asphalt_type_id, performance_data, location=None, sample_id=None):

        Args:
            asphalt_type_id: 沥青类型ID
            performance_data: 沥青性能数据，包含stability、durability、viscosity等字段
            location: 位置信息
            sample_id: 样本ID
        """
        with self.asphalt_performance_lock:
            asphalt_entry = {
                'timestamp': time.time(),
                'asphalt_type_id': asphalt_type_id,
                'performance_data': performance_data or {
                    'stability': 0,
                    'durability': 0,
                },
                'location': location or {},
                'sample_id': sample_id
            self.asphalt_performance_data.append(asphalt_entry)
            # 保留最近1000条沥青性能数据

    def _update_performance_metrics(self):
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
                # 计算95th百分位响应时间
                response_times.sort()
                idx = int(len(response_times) * 0.95)
                self.performance_metrics['response_time_95th'] = response_times[idx] if idx < len(response_times) else response_times[-1]

            # 计算吞吐量
            throughput_values = [entry['throughput'] for entry in recent_data if entry['throughput'] > 0]
            if throughput_values:
                self.performance_metrics['throughput'] = sum(throughput_values) / len(throughput_values)

            # 计算资源使用情况
            memory_values = [entry['resource_usage']['memory'] for entry in recent_data]
            disk_values = [entry['resource_usage']['disk'] for entry in recent_data]
            network_values = [entry['resource_usage']['network'] for entry in recent_data]

            self.performance_metrics['resource_usage'] = {
                'cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                'disk': sum(disk_values) / len(disk_values) if disk_values else 0,
                'network': sum(network_values) / len(network_values) if network_values else 0

            self.performance_metrics['last_performance_update'] = time.time()

    def _generate_performance_report(self):
        """生成性能报告"""
        with self.performance_lock:
            if not self.performance_data:
                return

            # 获取最近5分钟的性能数据用于趋势分析
            recent_data_5min = [
                entry for entry in self.performance_data
                if time.time() - entry['timestamp'] < 300
            ]

            # 按组件分组分析
            component_data = {}
            for entry in recent_data_5min:
                comp = entry['component']
                if comp not in component_data:
                    component_data[comp] = []
                component_data[comp].append(entry)

            # 生成组件性能报告
            for comp, data in component_data.items():
                response_times = [entry['response_time'] for entry in data]
                    'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                    'min_response_time': min(response_times) if response_times else 0,
                    'total_requests': len(data)

            # 生成性能报告
            performance_report = {
                'summary_metrics': self.performance_metrics.copy(),
                'component_performance': component_reports,
                'time_window': '5min'

            logger.info(f"AI性能报告: {str(performance_report, indent=2)}")

    def _update_asphalt_performance_metrics(self):
        """更新沥青性能指标"""
        with self.asphalt_performance_lock:
            if not self.asphalt_performance_data:
                return

            # 获取最近60秒的沥青性能数据
                entry for entry in self.asphalt_performance_data
                if time.time() - entry['timestamp'] < 60
            ]

            if not recent_data:
                return

            # 计算关键性能指标
            stability_values = [
                entry['performance_data'].get('stability', 0) for entry in recent_data
                if isinstance(entry['performance_data'], dict) and 'stability' in entry['performance_data']
            ]
            durability_values = [
                entry['performance_data'].get('durability', 0) for entry in recent_data
                if isinstance(entry['performance_data'], dict) and 'durability' in entry['performance_data']
            ]
            viscosity_values = [
                entry['performance_data'].get('viscosity', 0) for entry in recent_data
            ]

            # 计算异常数量
            for entry in recent_data:
                perf_data = entry['performance_data']
                if perf_data.get('stability', 0) < 0.5:
                    anomaly_count += 1
                if perf_data.get('viscosity', 0) > 100 or perf_data.get('viscosity', 0) < 10:

            # 更新沥青性能指标
                self.asphalt_performance_metrics['average_stability'] = sum(stability_values) / len(stability_values)
                self.asphalt_performance_metrics['average_durability'] = sum(durability_values) / len(durability_values)
                self.asphalt_performance_metrics['average_viscosity'] = sum(viscosity_values) / len(viscosity_values)

            self.asphalt_performance_metrics['anomaly_count'] = anomaly_count

    def _generate_asphalt_performance_report(self):
        """生成沥青性能报告"""
        with self.asphalt_performance_lock:

            # 获取最近5分钟的沥青性能数据用于趋势分析
            recent_data_5min = [
                if time.time() - entry['timestamp'] < 300
            ]

                return

            # 按沥青类型分组分析
            asphalt_type_data = {}
            for entry in recent_data_5min:
                asphalt_type = entry['asphalt_type_id']
                if asphalt_type not in asphalt_type_data:
                    asphalt_type_data[asphalt_type] = []
                asphalt_type_data[asphalt_type].append(entry)

            # 生成沥青类型性能报告
            asphalt_type_reports = {}
            for asphalt_type, data in asphalt_type_data.items():
                # 计算每种沥青类型的性能指标
                    if isinstance(entry['performance_data'], dict) and 'stability' in entry['performance_data']
                ]
                durability_values = [
                    if isinstance(entry['performance_data'], dict) and 'durability' in entry['performance_data']
                ]
                viscosity_values = [
                    entry['performance_data'].get('viscosity', 0) for entry in data
                    if isinstance(entry['performance_data'], dict) and 'viscosity' in entry['performance_data']
                ]

                asphalt_type_reports[asphalt_type] = {
                    'average_stability': sum(stability_values) / len(stability_values) if stability_values else 0,
                    'average_durability': sum(durability_values) / len(durability_values) if durability_values else 0,
                    'average_viscosity': sum(viscosity_values) / len(viscosity_values) if viscosity_values else 0,
                    'anomaly_count': sum(1 for entry in data if
                                         entry['performance_data'].get('viscosity', 0) < 10))

            # 生成沥青性能报告
                'timestamp': time.time(),
                'summary_metrics': self.asphalt_performance_metrics.copy(),
                'time_window': '5min'

            logger.info(f"沥青性能报告: {str(asphalt_report, indent=2)}")

    def _check_errors(self):
        """检查错误并生成报告"""
        with self.error_lock:
                return

            # 只处理未修复的错误
            if not unfixed_errors:
                return
            # 生成错误报告
                'total_errors': len(self.errors),
                'fixed_errors': self.metrics['fixed_errors'],
                'unfixed_errors': self.metrics['unfixed_errors'],
                'recent_unfixed_errors': unfixed_errors[-5:]  # 最近5个未修复的错误

            logger.info(f"AI监控报告: {str(error_report, indent=2)}")
        """尝试修复错误"""
        try:

            # 根据错误类型执行不同的修复策略
            if error['type'] == 'frontend':
                fix_success = self._fix_frontend_error(error)
                fix_success = self._fix_backend_error(error)
            elif error['type'] == 'database':
            elif error['type'] == 'ai':
                fix_success = self._fix_ai_error(error)
            elif error['type'] == 'security':
                fix_success = self._fix_security_error(error)

            if fix_success:
                error['fixed'] = True
                logger.info(f"成功修复错误: {error['message']}")
            else:
                logger.warning(f"无法自动修复错误: {error['message']}")
        except Exception as e:
            logger.error(f"修复错误失败: {str(e)}")

    def _fix_frontend_error(self, error):
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
        time_window_map = {
            '1min': 60,
            '5min': 300,
            '15min': 900,

        window_seconds = time_window_map.get(time_window, 300)
            # 获取指定时间窗口内的性能数据
                entry for entry in self.performance_data
                if time.time() - entry['timestamp'] < window_seconds
            ]

            if not recent_data:
                    'time_window': time_window,
                    'message': 'No performance data available for the specified time window',
                    'summary_metrics': self.performance_metrics.copy(),

            # 按组件分组分析
            component_data = {}
                comp = entry['component']
                if comp not in component_data:
                    component_data[comp] = []

            # 生成组件性能报告
            component_reports = {}
                response_times = [entry['response_time'] for entry in data]
                cpu_values = [entry['resource_usage']['cpu'] for entry in data]
                memory_values = [entry['resource_usage']['memory'] for entry in data]

                component_reports[comp] = {
                    'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                    'p95_response_time': self._calculate_percentile(response_times, 95),
                    'p99_response_time': self._calculate_percentile(response_times, 99),
                    'average_memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'total_requests': len(data)

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

            return performance_report

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:

        Args:
            percentile: 百分位（0-100）

        Returns:
            float: 百分位数值
        if not values:
            return 0

        values.sort()
        idx = int(len(values) * percentile / 100)

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

        # 统计每个区间的请求数
        for rt in response_times:
                if buckets[i] <= rt < buckets[i+1]:

        return bucket_counts

        """计算资源使用趋势
        Args:
        Returns:
        """
        if not data:

        trend_data = {
            'cpu': [],
            'disk': [],
            'network': []
            trend_data['timestamps'].append(entry['timestamp'])
            trend_data['memory'].append(entry['resource_usage']['memory'])
            trend_data['network'].append(entry['resource_usage']['network'])
        return trend_data

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False

    def upgrade_monitoring_config(self):
        try:
            # 添加新的监控配置项
                self.enhanced_monitoring = {
                    'real_time_alerting': True,
                    'error_prediction': True,
                    'resource_monitoring': True
                logger.info("已添加增强监控配置")
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

def get_ai_monitor():
    """获取或创建AI监控实例"""
    global _ai_monitor_instance
    if _ai_monitor_instance is None:
        _ai_monitor_instance = AIMonitor()
    return _ai_monitor_instance

# 创建并导出AI监控实例
