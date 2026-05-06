# -*- coding: utf-8 -*-
from datetime import datetime
import threading
# JSON import removed - using database
from app.config import Config
from app.utils.logging import logger

class NetworkOptimizer:
    """网络优化类，用于优化系统网络性能"""

    def __init__(self):
        self.cache = {}
        self.request_count = {}
        self.request_history = {}
        self.lock = threading.Lock()
        self.response_times = []
        self.avg_response_time = 0
        self.request_queue = []
        self.max_queue_size = 100
        self.performance_metrics = {
            'total_requests': 0,
            'cached_requests': 0,
            'rate_limited_requests': 0,
            'duplicate_requests': 0,
            'avg_response_time': 0,
            'peak_response_time': 0
        }

    def cache_response(self, key, response, ttl=Config.NETWORK_CONFIG['CACHE_TTL']):
        """缓存API响应"""
        with self.lock:
            self.cache[key] = {
                'response': response,
                'expires_at': datetime.now().timestamp() + ttl,
                'access_count': 0

    def get_cached_response(self, key):
        """获取缓存的API响应"""
        with self.lock:
                cache_entry = self.cache[key]
                if cache_entry['expires_at'] > datetime.now().timestamp():
                    # 更新访问计数
                    cache_entry['access_count'] += 1
                    # 更新性能指标
                    self.performance_metrics['cached_requests'] += 1
                    return cache_entry['response']
                else:
                    # 缓存过期，删除
                    del self.cache[key]
            return None

    def is_duplicate_request(self, client_ip, endpoint, request_data):
        """检测是否为重复请求"""
        if not Config.NETWORK_CONFIG['DUPLICATE_REQUEST_DETECTION']:
            return False

        with self.lock:
            current_time = datetime.now().timestamp()

            if request_key in self.request_history:
                # 检查请求是否在短时间内重复
                if current_time - self.request_history[request_key] < 2:  # 2秒内的重复请求
                    self.performance_metrics['duplicate_requests'] += 1
                    return True

            # 更新请求历史，只保留最近1000个请求
            self.request_history[request_key] = current_time
            if len(self.request_history) > 1000:
                # 删除最旧的请求记录
                oldest_key = next(iter(self.request_history))
                del self.request_history[oldest_key]

            return False

    def rate_limit_check(self, client_ip):
        with self.lock:
            minute_key = f"{client_ip}:{int(current_time // 60)}"

            if minute_key not in self.request_count:
                self.request_count[minute_key] = 0
            self.request_count[minute_key] += 1

            # 清理旧的请求计数
            for key in list(self.request_count.keys()):
                if int(key.split(':')[-1]) < int(current_time // 60):
                    del self.request_count[key]

            is_limited = self.request_count[minute_key] > Config.NETWORK_CONFIG['RATE_LIMIT_PER_IP']
            if is_limited:
                self.performance_metrics['rate_limited_requests'] += 1
            return is_limited

    def optimize_response_data(self, data):
        """优化响应数据，移除重复和不必要的字段"""
        if isinstance(data, dict):
            # 移除空值和重复键
            return {k: self.optimize_response_data(v) for k, v in data.items() if v is not None and v != ''}
        elif isinstance(data, list):
            # 移除重复项
            seen = []
            result = []
            for item in data:
                item_str = str(item, sort_keys=True)
                if item_str not in seen:
                    seen.append(item_str)
                    result.append(self.optimize_response_data(item))
            return result
        return data

    def update_performance_metrics(self, response_time):
        """更新性能指标"""
        with self.lock:
            self.response_times.append(response_time)

            # 计算平均响应时间（最近100个请求）
            recent_responses = self.response_times[-100:]
            self.avg_response_time = sum(recent_responses) / len(recent_responses) if recent_responses else 0
            self.performance_metrics['avg_response_time'] = self.avg_response_time

            # 更新峰值响应时间
            if response_time > self.performance_metrics['peak_response_time']:
                self.performance_metrics['peak_response_time'] = response_time

    def get_performance_metrics(self):
        """获取性能指标"""
        with self.lock:

    def clear_cache(self):
        """清除所有缓存"""
        with self.lock:

# 初始化网络优化器
network_optimizer = NetworkOptimizer()
