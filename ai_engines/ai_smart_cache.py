# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI智能缓存中间件
根据请求频率和响应时间自动调整缓存策略
"""

import time
import hashlib
import logging
import threading
from typing import Dict, Optional

from app.utils.logging import logger
from flask import request, make_response
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Smart Cache - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_smart_cache.log'),
        logging.StreamHandler()
    ])

class AISmartCache:
    """AI智能缓存类"""

    def __init__(self):
        self.cache = {}
        self.cache_stats = {}
        self.request_history = {}
        self.response_times = {}

        self.config = {
            'default_ttl': 300,
            'max_ttl': 3600,
            'min_ttl': 60,
            'cleanup_interval': 3600,
            'popular_threshold': 10,
            'slow_threshold': 0.5,
            'cacheable_status_codes': [200, 304],
            'cacheable_methods': ['GET', 'HEAD']
        }

        self._start_cleanup_thread()

        logger.info("AI智能缓存初始化完成")

    def _start_cleanup_thread(self):
        """启动缓存清理线程"""
        def cleanup_cache():
            while True:
                time.sleep(self.config['cleanup_interval'])
                self._cleanup_expired_cache()

        cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for key, cache_entry in self.cache.items():
            if current_time - cache_entry['timestamp'] > cache_entry['ttl']:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")

    def _generate_cache_key(self):
        """生成缓存键"""
        key_parts = [
            request.method,
            request.path,
            str(sorted(request.args.to_dict().items())),
            str(sorted(request.form.to_dict().items()))
        ]
        if request.is_json:
            try:
                json_data = request.get_json()
                if json_data:
                    key_parts.append(str(sorted(json_data.items()) if isinstance(json_data, dict) else str(json_data)))
            except Exception as e:
                logger.debug(f"无法解析JSON请求体: {str(e)}")

        cache_key = hashlib.md5('|'.join(key_parts).encode('utf-8')).hexdigest()
        return cache_key

    def _update_cache_stats(self, cache_key: str, is_hit: bool, processing_time: float):
        """更新缓存统计信息"""
        if cache_key not in self.request_history:
            self.request_history[cache_key] = []
        self.request_history[cache_key].append(time.time())

        if len(self.request_history[cache_key]) > 100:
            self.request_history[cache_key] = self.request_history[cache_key][-100:]

        if cache_key not in self.response_times:
            self.response_times[cache_key] = []
        self.response_times[cache_key].append(processing_time)

        if len(self.response_times[cache_key]) > 100:
            self.response_times[cache_key] = self.response_times[cache_key][-100:]

        if cache_key not in self.cache_stats:
            self.cache_stats[cache_key] = {
                'hit_count': 0,
                'miss_count': 0,
            }

        if is_hit:
            self.cache_stats[cache_key]['hit_count'] += 1
        else:
            self.cache_stats[cache_key]['miss_count'] += 1

        total_processing_time = sum(self.response_times[cache_key])
        self.cache_stats[cache_key]['avg_processing_time'] = total_processing_time / len(self.response_times[cache_key])

    def smart_cache_middleware(self, app):
        """智能缓存中间件"""
        @app.before_request
        def before_request():
            if request.method not in self.config['cacheable_methods']:
                return

            cache_key = self._generate_cache_key()
            request.cache_key = cache_key
            request.cache_hit = False
            request.processing_start_time = time.time()

            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                current_time = time.time()

                if current_time - cache_entry['timestamp'] <= cache_entry['ttl']:
                    logger.debug(f"缓存命中: {cache_key}")
                    request.cache_hit = True

                    processing_time = time.time() - request.processing_start_time
                    self._update_cache_stats(cache_key, True, processing_time)

                    response = make_response(cache_entry['data']['body'])
                    response.status_code = cache_entry['data']['status_code']
                    response.headers['X-Cache'] = 'HIT'
                    response.headers['X-Cache-TTL'] = str(int(cache_entry['ttl'] - (current_time - cache_entry['timestamp'])))
                    return response

        @app.after_request
        def after_request(response):
            if request.method not in self.config['cacheable_methods']:
                return response

            cache_key = getattr(request, 'cache_key', None)
            if cache_key and not getattr(request, 'cache_hit', False):
                processing_time = time.time() - getattr(request, 'processing_start_time', time.time())
                self._update_cache_stats(cache_key, False, processing_time)

            return response

        logger.info("AI智能缓存中间件注册完成")
        return app

    def clear_cache(self, cache_key: Optional[str] = None):
        """清除缓存

        Args:
            cache_key: 可选,指定要清除的缓存键,不指定则清除所有缓存
        """
        if cache_key:
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.info(f"清除缓存: {cache_key}")
        else:
            self.cache.clear()


ai_smart_cache = AISmartCache()


def ai_smart_cache_middleware(app):
    """AI智能缓存中间件入口"""
    return ai_smart_cache.smart_cache_middleware(app)
