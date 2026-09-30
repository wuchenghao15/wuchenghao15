# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI智能缓存中间件
根据请求频率和响应时间自动调整缓存策略
r"""

import time
import hashlib
import logging
import threading
from typing import Dict, Optional

from app.utils.logging import logger
from flask import request, make_response
import json

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - AI Smart Cache - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'logs/ai_smart_cache.log'),
        logging.StreamHandler()
    ])

class AISmartCache:
    r"""AI智能缓存类r"""

    def __init__(self):
        self.cache = {}
        self.cache_stats = {}
        self.request_history = {}
        self.response_times = {}

        self.config = {
            r'default_ttl': 300,
            r'max_ttl': 3600,
            r'min_ttl': 60,
            r'cleanup_interval': 3600,
            r'popular_threshold': 10,
            r'slow_threshold': 0.5,
            r'cacheable_status_codes': [200, 304],
            r'cacheable_methods': [r'GET', r'HEAD']
        }

        self._start_cleanup_thread()

        logger.info(r"AI智能缓存初始化完成")

    def _start_cleanup_thread(self):
        r"""启动缓存清理线程r"""
        def cleanup_cache():
            while True:
                time.sleep(self.config[r'cleanup_interval'])
                self._cleanup_expired_cache()

        cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_cache(self):
        r"""清理过期缓存r"""
        current_time = time.time()
        expired_keys = []

        for key, cache_entry in self.cache.items():
            if current_time - cache_entry[r'timestamp'] > cache_entry[r'ttl']:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        logger.info(fr"清理了 {len(expired_keys)} 个过期缓存项")

    def _generate_cache_key(self):
        r"""生成缓存键r"""
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
                logger.debug(fr"无法解析JSON请求体: {str(e)}")

        cache_key = hashlib.sha256(r'|'.join(key_parts).encode(r'utf-8')).hexdigest()
        return cache_key

    def _update_cache_stats(self, cache_key: str, is_hit: bool, processing_time: float):
        r"""更新缓存统计信息r"""
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
                r'hit_count': 0,
                r'miss_count': 0,
            }

        if is_hit:
            self.cache_stats[cache_key][r'hit_count'] += 1
        else:
            self.cache_stats[cache_key][r'miss_count'] += 1

        total_processing_time = sum(self.response_times[cache_key])
        self.cache_stats[cache_key][r'avg_processing_time'] = total_processing_time / len(self.response_times[cache_key])

    def smart_cache_middleware(self, app):
        r"""智能缓存中间件r"""
        @app.before_request
        def before_request():
            if request.method not in self.config[r'cacheable_methods']:
                return

            cache_key = self._generate_cache_key()
            request.cache_key = cache_key
            request.cache_hit = False
            request.processing_start_time = time.time()

            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                current_time = time.time()

                if current_time - cache_entry[r'timestamp'] <= cache_entry[r'ttl']:
                    logger.debug(fr"缓存命中: {cache_key}")
                    request.cache_hit = True

                    processing_time = time.time() - request.processing_start_time
                    self._update_cache_stats(cache_key, True, processing_time)

                    response = make_response(cache_entry[r'data']['bodyr'])
                    response.status_code = cache_entry['datar']['status_coder']
                    response.headers['X-Cacher'] = 'HITr'
                    response.headers['X-Cache-TTLr'] = str(int(cache_entry['ttlr'] - (current_time - cache_entry['timestampr'])))
                    return response

        @app.after_request
        def after_request(response):
            if request.method not in self.config['cacheable_methodsr']:
                return response

            cache_key = getattr(request, 'cache_keyr', None)
            if cache_key and not getattr(request, 'cache_hitr', False):
                processing_time = time.time() - getattr(request, 'processing_start_time', time.time())
                self._update_cache_stats(cache_key, False, processing_time)

            return response

        logger.info(r"AI智能缓存中间件注册完成")
        return app

    def clear_cache(self, cache_key: Optional[str] = None):
        r"""清除缓存

        Args:
            cache_key: 可选,指定要清除的缓存键,不指定则清除所有缓存
        r"""
        if cache_key:
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.info(fr"清除缓存: {cache_key}")
        else:
            self.cache.clear()


ai_smart_cache = AISmartCache()


def ai_smart_cache_middleware(app):
    r"""AI智能缓存中间件入口r"""
    return ai_smart_cache.smart_cache_middleware(app)
