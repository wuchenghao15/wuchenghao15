# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI数据库中间件,用于优化数据库与前端的交互
"""

import time
import threading
import hashlib
from functools import wraps
from app.utils.logging import logger
from app.ai.automation import ai_automation_manager
import logging


class AIDatabaseMiddleware:
    """AI数据库中间件类"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.query_history = []
        self.query_history_lock = threading.Lock()
        self.cache_ttl = 300
        self.max_cache_size = 1000

    def _generate_cache_key(self, func_name, *args, **kwargs):
        """生成缓存键"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        return hashlib.md5(str(key_data).encode()).hexdigest()

    def _get_from_cache(self, key):
        """从缓存中获取数据"""
        with self.cache_lock:
            if key in self.cache:
                cache_entry = self.cache[key]
                if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                    cache_entry['hits'] += 1
                    logger.debug(f"缓存命中: {key}, 命中次数: {cache_entry['hits']}")
                    return cache_entry['data']
        return None

    def _set_to_cache(self, key, data):
        """将数据存入缓存"""
        with self.cache_lock:
            if len(self.cache) >= self.max_cache_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
                logger.debug(f"缓存已满,删除最旧缓存: {oldest_key}")

            self.cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'hits': 0
            }

    def _log_query(self, func_name, args, kwargs, result, execution_time):
        """记录查询历史"""
        with self.query_history_lock:
            query_entry = {
                'func_name': func_name,
                'args': args,
                'kwargs': kwargs,
                'result': result,
                'execution_time': execution_time,
                'timestamp': time.time()
            }

            self.query_history.append(query_entry)
            if len(self.query_history) > 1000:
                self.query_history.pop(0)

    def with_cache(self, func):
        """缓存装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = self._generate_cache_key(func.__name__, *args, **kwargs)

            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data

            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            self._set_to_cache(cache_key, result)
            self._log_query(func.__name__, args, kwargs, result, execution_time)

            return result
        return wrapper

    def fetch_one(self, query, params=None):
        """智能查询:返回单行结果"""
        return self.with_cache(self.db_manager.fetch_one)(query, params)

    def fetch_all(self, query, params=None):
        """智能查询:返回所有结果"""
        return self.with_cache(self.db_manager.fetch_all)(query, params)

    def fetch_scalar(self, query, params=None):
        """智能查询:返回单个值"""
        return self.with_cache(self.db_manager.fetch_scalar)(query, params)

    def execute(self, query, params=None):
        """智能执行SQL查询"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if any(kw in query.upper() for kw in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']):
                    cache_keys_to_delete.append(cache_key)
                    break

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(f"执行写操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.execute(query, params)
        execution_time = time.time() - start_time

        self._log_query('execute', (query, params), {}, result, execution_time)
        return result

    def insert(self, table, data):
        """智能插入数据"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if table in str(cache_key):
                    cache_keys_to_delete.append(cache_key)

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(f"执行插入操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.insert(table, data)
        execution_time = time.time() - start_time

        self._log_query('insert', (table, data), {}, result, execution_time)
        return result

    def update(self, table, data, where_clause, where_params=None):
        """智能更新数据"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if table in str(cache_key):
                    cache_keys_to_delete.append(cache_key)

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(f"执行更新操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.update(table, data, where_clause, where_params)
        execution_time = time.time() - start_time

        self._log_query('update', (table, data, where_clause, where_params), {}, result, execution_time)
        return result

    def delete(self, table, where_clause, where_params=None):
        """智能删除数据"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if table in str(cache_key):
                    cache_keys_to_delete.append(cache_key)

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(f"执行删除操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.delete(table, where_clause, where_params)
        execution_time = time.time() - start_time

        self._log_query('delete', (table, where_clause, where_params), {}, result, execution_time)
        return result

    def optimize_query(self, query):
        """优化查询语句"""
        logger.info(f"优化查询: {query}")
        return query

    def get_query_analysis(self):
        """获取查询分析"""
        analysis = {
            'total_queries': len(self.query_history),
            'slow_queries': [],
            'cache_hit_rate': 0,
            'frequent_queries': []
        }

        total_hits = 0
        total_cache_accesses = 0
        with self.cache_lock:
            for cache_entry in self.cache.values():
                total_hits += cache_entry['hits']
                total_cache_accesses += cache_entry['hits'] + 1

        if total_cache_accesses > 0:
            analysis['cache_hit_rate'] = total_hits / total_cache_accesses

        with self.query_history_lock:
            for query_entry in self.query_history:
                if query_entry['execution_time'] > 1.0:
                    slow_query = {
                        'func_name': query_entry['func_name'],
                        'args': query_entry['args'],
                        'execution_time': query_entry['execution_time'],
                        'timestamp': query_entry['timestamp']
                    }
                    analysis['slow_queries'].append(slow_query)

            query_counts = {}
            for query_entry in self.query_history:
                query_key = f"{query_entry['func_name']}:{str(query_entry['args'])}"
                query_counts[query_key] = query_counts.get(query_key, 0) + 1

            for query_key, count in query_counts.items():
                if count > 5:
                    analysis['frequent_queries'].append({
                        'query_key': query_key,
                        'count': count
                    })

        return analysis

    def clear_cache(self):
        """清空缓存"""
        with self.cache_lock:
            cache_size = len(self.cache)
            self.cache.clear()
            logger.info(f"清空缓存,共删除 {cache_size} 个缓存项")

    def get_cache_stats(self):
        """获取缓存统计"""
        with self.cache_lock:
            total_entries = len(self.cache)
            total_hits = sum(entry['hits'] for entry in self.cache.values())

            current_time = time.time()
            if total_entries > 0:
                avg_age = sum(current_time - entry['timestamp'] for entry in self.cache.values()) / total_entries
            else:
                avg_age = 0

        return {
            'total_entries': total_entries,
            'total_hits': total_hits,
            'average_age': avg_age,
            'max_cache_size': self.max_cache_size,
            'cache_ttl': self.cache_ttl
        }
