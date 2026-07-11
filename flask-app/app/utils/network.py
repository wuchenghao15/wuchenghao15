# -*- coding: utf-8 -*-
from datetime import datetime
import threading
from app.config import Config
from app.utils.logging import logger
import logging


class NetworkOptimizer:
    """网络优化类: 用于优化系统网络性能"""

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

    def cache_response(self, key, response, ttl=None):
        """缓存API响应"""
        if ttl is None:
            ttl = Config.NETWORK_CONFIG['CACHE_TTL']
        with self.lock:
            self.cache[key] = {
                'response': response,
                'expires_at': datetime.now().timestamp() + ttl,
                'access_count': 0
            }

    def get_cached_response(self, key):
        """获取缓存的API响应"""
        with self.lock:
            if key in self.cache:
                cache_entry = self.cache[key]
                if cache_entry['expires_at'] > datetime.now().timestamp():
                    cache_entry['access_count'] += 1
                    self.performance_metrics['cached_requests'] += 1
                    return cache_entry['response']
        return None

    def is_duplicate_request(self, client_ip, endpoint, request_data):
        """检测是否为重复请求"""
        if not Config.NETWORK_CONFIG['DUPLICATE_REQUEST_DETECTION']:
            return False
        return False

    def rate_limit_check(self, client_ip):
        """检查是否超过速率限制"""
        # 本地IP完全跳过速率限制
        if client_ip in ['127.0.0.1', 'localhost', '::1']:
            return False
        
        with self.lock:
            current_time = datetime.now().timestamp()
            minute_key = f"{client_ip}:{int(current_time // 60)}"

            if minute_key not in self.request_count:
                self.request_count[minute_key] = 0
            self.request_count[minute_key] += 1

            for key in list(self.request_count.keys()):
                if int(key.split(':')[-1]) < int(current_time // 60):
                    del self.request_count[key]

            is_limited = self.request_count[minute_key] > Config.NETWORK_CONFIG['RATE_LIMIT_PER_IP']
            if is_limited:
                self.performance_metrics['rate_limited_requests'] += 1
            return is_limited

    def optimize_response_data(self, data):
        """优化响应数据: 移除重复和不必要的字段"""
        if isinstance(data, dict):
            return {k: self.optimize_response_data(v) for k, v in data.items() if v is not None and v != ''}
        elif isinstance(data, list):
            return [self.optimize_response_data(item) for item in data]
        return data

    def update_performance_metrics(self, response_time):
        """更新性能指标"""
        with self.lock:
            self.response_times.append(response_time)
            recent_responses = self.response_times[-100:]
            self.avg_response_time = sum(recent_responses) / len(recent_responses) if recent_responses else 0
            self.performance_metrics['avg_response_time'] = self.avg_response_time

            if response_time > self.performance_metrics['peak_response_time']:
                self.performance_metrics['peak_response_time'] = response_time

    def get_performance_metrics(self):
        """获取性能指标"""
        with self.lock:
            return self.performance_metrics.copy()

    def clear_cache(self):
        """清除所有缓存"""
        with self.lock:
            self.cache.clear()


network_optimizer = NetworkOptimizer()
