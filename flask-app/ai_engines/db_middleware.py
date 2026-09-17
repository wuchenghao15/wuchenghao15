# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI数据库中间件,用于优化数据库与前端的交互
r"""

import time
import threading
import hashlib
from functools import wraps
from app.utils.logging import logger
from app.ai.automation import ai_automation_manager
import logging

logger = logging.getLogger(__name__)


class AIDatabaseMiddleware:
    r"""AI数据库中间件类r"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.query_history = []
        self.query_history_lock = threading.Lock()
        self.cache_ttl = 300
        self.max_cache_size = 1000

    def _generate_cache_key(self, func_name, *args, **kwargs):
        r"""生成缓存键r"""
        key_data = {
            r'func': func_name,
            r'args': args,
            r'kwargs': kwargs
        }
        return hashlib.sha256(str(key_data).encode()).hexdigest()

    def _get_from_cache(self, key):
        r"""从缓存中获取数据r"""
        with self.cache_lock:
            if key in self.cache:
                cache_entry = self.cache[key]
                if time.time() - cache_entry[r'timestamp'] < self.cache_ttl:
                    cache_entry[r'hits'] += 1
                    logger.debug(f"缓存命中: {key}, 命中次数: {cache_entry[r'hits']}")
                    return cache_entry[r'data']
        return None

    def _set_to_cache(self, key, data):
        r"""将数据存入缓存r"""
        with self.cache_lock:
            if len(self.cache) >= self.max_cache_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][r'timestamp'])
                del self.cache[oldest_key]
                logger.debug(fr"缓存已满,删除最旧缓存: {oldest_key}")

            self.cache[key] = {
                r'data': data,
                r'timestamp': time.time(),
                r'hits': 0
            }

    def _log_query(self, func_name, args, kwargs, result, execution_time):
        r"""记录查询历史r"""
        with self.query_history_lock:
            query_entry = {
                r'func_name': func_name,
                r'args': args,
                r'kwargs': kwargs,
                r'result': result,
                r'execution_time': execution_time,
                r'timestamp': time.time()
            }

            self.query_history.append(query_entry)
            if len(self.query_history) > 1000:
                self.query_history.pop(0)

    def with_cache(self, func):
        r"""缓存装饰器r"""
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
        r"""智能查询:返回单行结果r"""
        return self.with_cache(self.db_manager.fetch_one)(query, params)

    def fetch_all(self, query, params=None):
        r"""智能查询:返回所有结果r"""
        return self.with_cache(self.db_manager.fetch_all)(query, params)

    def fetch_scalar(self, query, params=None):
        r"""智能查询:返回单个值r"""
        return self.with_cache(self.db_manager.fetch_scalar)(query, params)

    def execute(self, query, params=None):
        r"""智能执行SQL查询r"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if any(kw in query.upper() for kw in [r'INSERT', r'UPDATE', r'DELETE', r'DROP', r'ALTER']):
                    cache_keys_to_delete.append(cache_key)
                    break

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(fr"执行写操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.execute(query, params)
        execution_time = time.time() - start_time

        self._log_query(r'execute', (query, params), {}, result, execution_time)
        return result

    def insert(self, table, data):
        r"""智能插入数据r"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if table in str(cache_key):
                    cache_keys_to_delete.append(cache_key)

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(fr"执行插入操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.insert(table, data)
        execution_time = time.time() - start_time

        self._log_query(r'insert', (table, data), {}, result, execution_time)
        return result

    def update(self, table, data, where_clause, where_params=None):
        r"""智能更新数据r"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if table in str(cache_key):
                    cache_keys_to_delete.append(cache_key)

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(fr"执行更新操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.update(table, data, where_clause, where_params)
        execution_time = time.time() - start_time

        self._log_query(r'update', (table, data, where_clause, where_params), {}, result, execution_time)
        return result

    def delete(self, table, where_clause, where_params=None):
        r"""智能删除数据r"""
        cache_keys_to_delete = []
        with self.cache_lock:
            for cache_key in self.cache:
                if table in str(cache_key):
                    cache_keys_to_delete.append(cache_key)

            for cache_key in cache_keys_to_delete:
                del self.cache[cache_key]

            if cache_keys_to_delete:
                logger.debug(fr"执行删除操作,清空 {len(cache_keys_to_delete)} 个缓存项")

        start_time = time.time()
        result = self.db_manager.delete(table, where_clause, where_params)
        execution_time = time.time() - start_time

        self._log_query(r'delete', (table, where_clause, where_params), {}, result, execution_time)
        return result

    def optimize_query(self, query):
        r"""优化查询语句r"""
        logger.info(fr"优化查询: {query}")
        return query

    def get_query_analysis(self):
        r"""获取查询分析r"""
        analysis = {
            r'total_queries': len(self.query_history),
            r'slow_queries': [],
            r'cache_hit_rate': 0,
            r'frequent_queries': []
        }

        total_hits = 0
        total_cache_accesses = 0
        with self.cache_lock:
            for cache_entry in self.cache.values():
                total_hits += cache_entry[r'hits']
                total_cache_accesses += cache_entry[r'hits'] + 1

        if total_cache_accesses > 0:
            analysis[r'cache_hit_rate'] = total_hits / total_cache_accesses

        with self.query_history_lock:
            for query_entry in self.query_history:
                if query_entry[r'execution_time'] > 1.0:
                    slow_query = {
                        r'func_name': query_entry[r'func_name'],
                        r'args': query_entry[r'args'],
                        r'execution_time': query_entry[r'execution_time'],
                        r'timestamp': query_entry[r'timestamp']
                    }
                    analysis[r'slow_queries'].append(slow_query)

            query_counts = {}
            for query_entry in self.query_history:
                query_key = f"{query_entry[r'func_name']}:{str(query_entry[r'args'])}"
                query_counts[query_key] = query_counts.get(query_key, 0) + 1

            for query_key, count in query_counts.items():
                if count > 5:
                    analysis[r'frequent_queries'].append({
                        r'query_key': query_key,
                        r'count': count
                    })

        return analysis

    def clear_cache(self):
        r"""清空缓存r"""
        with self.cache_lock:
            cache_size = len(self.cache)
            self.cache.clear()
            logger.info(fr"清空缓存,共删除 {cache_size} 个缓存项")

    def get_cache_stats(self):
        r"""获取缓存统计r"""
        with self.cache_lock:
            total_entries = len(self.cache)
            total_hits = sum(entry[r'hits'] for entry in self.cache.values())

            current_time = time.time()
            if total_entries > 0:
                avg_age = sum(current_time - entry[r'timestamp'] for entry in self.cache.values()) / total_entries
            else:
                avg_age = 0

        return {
            r'total_entries': total_entries,
            r'total_hits': total_hits,
            r'average_age': avg_age,
            r'max_cache_size': self.max_cache_size,
            r'cache_ttl': self.cache_ttl
        }
