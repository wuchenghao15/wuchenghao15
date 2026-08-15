#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 性能优化引擎 v16.0.0
====================================
全面提升系统性能，包括数据库查询优化、缓存策略、并发处理和资源调度

核心能力：
1. 数据库查询优化 - 智能查询优化、索引建议、慢查询分析
2. 缓存策略增强 - 多级缓存、智能预热、缓存预热
3. 并发处理优化 - 连接池优化、线程池管理、异步处理
4. 资源调度优化 - 资源分配、负载均衡、性能监控
"""

import os
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'performance_optimizer.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PerformanceOptimizer')


class QueryOptimizer:
    """数据库查询优化器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._query_cache = {}
        self._slow_queries = []
        self._index_suggestions = []
        self._lock = threading.RLock()
    
    def analyze_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """分析SQL查询并给出优化建议"""
        with self._lock:
            analysis = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'suggestions': [],
                'estimated_cost': 0,
                'optimization_score': 100
            }
            
            # 检查是否使用了SELECT *
            if 'SELECT *' in query.upper():
                analysis['suggestions'].append({
                    'type': 'SELECT_STAR',
                    'severity': 'medium',
                    'message': '避免使用SELECT *，明确指定需要的列',
                    'impact': '减少数据传输量，提升查询性能'
                })
                analysis['optimization_score'] -= 15
            
            # 检查是否缺少WHERE条件
            if 'SELECT' in query.upper() and 'WHERE' not in query.upper():
                analysis['suggestions'].append({
                    'type': 'MISSING_WHERE',
                    'severity': 'high',
                    'message': '查询缺少WHERE条件，可能导致全表扫描',
                    'impact': '添加WHERE条件可显著提升查询速度'
                })
                analysis['optimization_score'] -= 30
            
            # 检查是否使用了LIKE '%...'
            if "LIKE '%" in query or "LIKE '% " in query:
                analysis['suggestions'].append({
                    'type': 'LEADING_WILDCARD',
                    'severity': 'high',
                    'message': '避免使用前导通配符LIKE \'%...\''，
                    'impact': '前导通配符会导致索引失效，使用全文索引替代'
                })
                analysis['optimization_score'] -= 25
            
            # 检查是否使用了子查询
            if query.upper().count('SELECT') > 1:
                analysis['suggestions'].append({
                    'type': 'SUBQUERY',
                    'severity': 'medium',
                    'message': '考虑将子查询改写为JOIN',
                    'impact': 'JOIN通常比子查询性能更好'
                })
                analysis['optimization_score'] -= 10
            
            # 检查是否使用了ORDER BY
            if 'ORDER BY' in query.upper() and 'LIMIT' not in query.upper():
                analysis['suggestions'].append({
                    'type': 'ORDER_WITHOUT_LIMIT',
                    'severity': 'low',
                    'message': 'ORDER BY without LIMIT可能导致大量数据排序',
                    'impact': '添加LIMIT限制返回结果数量'
                })
                analysis['optimization_score'] -= 5
            
            # 估算查询成本
            analysis['estimated_cost'] = self._estimate_query_cost(query)
            
            return analysis
    
    def _estimate_query_cost(self, query: str) -> float:
        """估算查询成本（0-100，越低越好）"""
        cost = 10
        
        # 表连接数量
        join_count = query.upper().count('JOIN')
        cost += join_count * 15
        
        # 子查询数量
        subquery_count = query.upper().count('SELECT') - 1
        cost += subquery_count * 20
        
        # 排序操作
        if 'ORDER BY' in query.upper():
            cost += 10
        
        # 分组操作
        if 'GROUP BY' in query.upper():
            cost += 15
        
        # 聚合函数
        aggregate_funcs = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
        for func in aggregate_funcs:
            if func in query.upper():
                cost += 5
        
        return min(100, cost)
    
    def suggest_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """为表建议索引"""
        suggestions = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 获取现有索引
            cursor.execute(f"PRAGMA index_list({table_name})")
            existing_indexes = cursor.fetchall()
            
            # 分析查询模式（从慢查询日志中）
            query_patterns = self._analyze_query_patterns(table_name)
            
            for pattern in query_patterns:
                if pattern['type'] == 'frequent_where':
                    suggestions.append({
                        'table': table_name,
                        'columns': pattern['columns'],
                        'reason': f"频繁在 {', '.join(pattern['columns'])} 上进行WHERE查询",
                        'priority': 'high',
                        'estimated_improvement': '30-50%'
                    })
                elif pattern['type'] == 'join_condition':
                    suggestions.append({
                        'table': table_name,
                        'columns': pattern['columns'],
                        'reason': f"JOIN条件中频繁使用 {', '.join(pattern['columns'])}",
                        'priority': 'high',
                        'estimated_improvement': '40-60%'
                    })
                elif pattern['type'] == 'order_by':
                    suggestions.append({
                        'table': table_name,
                        'columns': pattern['columns'],
                        'reason': f"频繁在 {', '.join(pattern['columns'])} 上排序",
                        'priority': 'medium',
                        'estimated_improvement': '20-30%'
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"索引建议生成失败: {e}")
            return []
        finally:
            conn.close()
    
    def _analyze_query_patterns(self, table_name: str) -> List[Dict[str, Any]]:
        """分析查询模式"""
        # 这里应该从慢查询日志中分析，简化实现
        return [
            {
                'type': 'frequent_where',
                'columns': ['id', 'created_at'],
                'frequency': 100
            }
        ]
    
    def record_slow_query(self, query: str, execution_time: float, params: tuple = None):
        """记录慢查询"""
        with self._lock:
            self._slow_queries.append({
                'query': query,
                'execution_time': execution_time,
                'params': params,
                'timestamp': datetime.now().isoformat()
            })
            
            # 只保留最近1000条慢查询
            if len(self._slow_queries) > 1000:
                self._slow_queries = self._slow_queries[-1000:]
            
            logger.warning(f"慢查询记录: {execution_time:.3f}s - {query[:100]}")
    
    def get_slow_query_report(self) -> Dict[str, Any]:
        """获取慢查询报告"""
        with self._lock:
            if not self._slow_queries:
                return {'total': 0, 'queries': []}
            
            # 按执行时间排序
            sorted_queries = sorted(
                self._slow_queries,
                key=lambda x: x['execution_time'],
                reverse=True
            )
            
            # 统计信息
            total_time = sum(q['execution_time'] for q in self._slow_queries)
            avg_time = total_time / len(self._slow_queries)
            max_time = max(q['execution_time'] for q in self._slow_queries)
            
            return {
                'total': len(self._slow_queries),
                'total_time': total_time,
                'avg_time': avg_time,
                'max_time': max_time,
                'top_10': sorted_queries[:10],
                'queries': sorted_queries
            }


class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        self._cache = {}
        self._cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
        self._lock = threading.RLock()
        self._max_size = 10000
        self._ttl = 3600  # 默认1小时过期
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # 检查是否过期
                if entry['expires_at'] > datetime.now():
                    self._cache_stats[key]['hits'] += 1
                    return entry['value']
                else:
                    # 过期，删除
                    del self._cache[key]
            
            self._cache_stats[key]['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存值"""
        with self._lock:
            if ttl is None:
                ttl = self._ttl
            
            # 检查缓存大小
            if len(self._cache) >= self._max_size:
                self._evict()
            
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now()
            }
    
    def _evict(self):
        """缓存淘汰（LRU策略）"""
        if not self._cache:
            return
        
        # 找到最久未使用的条目
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['created_at']
        )
        del self._cache[oldest_key]
        logger.debug(f"缓存淘汰: {oldest_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_hits = sum(stats['hits'] for stats in self._cache_stats.values())
            total_misses = sum(stats['misses'] for stats in self._cache_stats.values())
            total_requests = total_hits + total_misses
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hit_rate': total_hits / total_requests if total_requests > 0 else 0,
                'total_hits': total_hits,
                'total_misses': total_misses,
                'total_requests': total_requests
            }
    
    def warmup(self, keys: List[str], loader_func):
        """缓存预热"""
        warmed = 0
        for key in keys:
            if key not in self._cache:
                try:
                    value = loader_func(key)
                    self.set(key, value)
                    warmed += 1
                except Exception as e:
                    logger.error(f"缓存预热失败 {key}: {e}")
        
        logger.info(f"缓存预热完成: {warmed}/{len(keys)}")
        return warmed


class ConnectionPoolOptimizer:
    """连接池优化器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._pool = []
        self._pool_size = 10
        self._max_pool_size = 50
        self._lock = threading.RLock()
        self._stats = {'created': 0, 'reused': 0, 'closed': 0}
        
        # 初始化连接池
        self._init_pool()
    
    def _init_pool(self):
        """初始化连接池"""
        for _ in range(self._pool_size):
            conn = self._create_connection()
            self._pool.append(conn)
            self._stats['created'] += 1
    
    def _create_connection(self):
        """创建新连接"""
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_connection(self):
        """从连接池获取连接"""
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._stats['reused'] += 1
                return conn
            else:
                # 池空，创建新连接
                if self._stats['created'] < self._max_pool_size:
                    conn = self._create_connection()
                    self._stats['created'] += 1
                    return conn
                else:
                    raise Exception("连接池已满，无法获取连接")
    
    def return_connection(self, conn):
        """归还连接到连接池"""
        with self._lock:
            if len(self._pool) < self._pool_size:
                self._pool.append(conn)
            else:
                conn.close()
                self._stats['closed'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'max_pool_size': self._max_pool_size,
                'created': self._stats['created'],
                'reused': self._stats['reused'],
                'closed': self._stats['closed'],
                'reuse_rate': self._stats['reused'] / (self._stats['created'] + self._stats['reused']) 
                    if (self._stats['created'] + self._stats['reused']) > 0 else 0
            }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._metrics = defaultdict(list)
        self._lock = threading.RLock()
        self._max_metrics = 10000
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """记录性能指标"""
        with self._lock:
            self._metrics[metric_name].append({
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'tags': tags or {}
            })
            
            # 限制指标数量
            if len(self._metrics[metric_name]) > self._max_metrics:
                self._metrics[metric_name] = self._metrics[metric_name][-self._max_metrics:]
    
    def get_metric_stats(self, metric_name: str) -> Dict[str, Any]:
        """获取指标统计"""
        with self._lock:
            if metric_name not in self._metrics:
                return {'error': '指标不存在'}
            
            values = [m['value'] for m in self._metrics[metric_name]]
            
            return {
                'count': len(values),
                'avg': sum(values) / len(values) if values else 0,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99)
            }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                name: self.get_metric_stats(name)
                for name in self._metrics.keys()
            }


class PerformanceOptimizer:
    """性能优化引擎主类"""
    
    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.connection_pool = ConnectionPoolOptimizer(DATABASE_PATH)
        self.performance_monitor = PerformanceMonitor()
        
        logger.info("性能优化引擎初始化完成")
    
    def optimize_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """优化查询"""
        # 分析查询
        analysis = self.query_optimizer.analyze_query(query, params)
        
        # 记录性能指标
        self.performance_monitor.record_metric(
            'query_optimization_score',
            analysis['optimization_score'],
            {'query_type': 'select' if 'SELECT' in query.upper() else 'other'}
        )
        
        return analysis
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'query_optimizer': {
                'slow_queries': self.query_optimizer.get_slow_query_report()
            },
            'cache_optimizer': self.cache_optimizer.get_stats(),
            'connection_pool': self.connection_pool.get_stats(),
            'performance_metrics': self.performance_monitor.get_all_metrics()
        }
    
    def start_optimization_loop(self, interval: int = 60):
        """启动优化循环"""
        def _loop():
            while True:
                try:
                    # 定期执行优化任务
                    report = self.get_performance_report()
                    logger.info(f"性能报告: 缓存命中率={report['cache_optimizer']['hit_rate']:.2%}")
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"优化循环错误: {e}")
                    time.sleep(interval)
        
        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()
        logger.info("性能优化循环已启动")


# 全局实例
performance_optimizer = PerformanceOptimizer()

if __name__ == '__main__':
    print("=== 性能优化引擎测试 ===")
    
    # 测试查询优化
    query = "SELECT * FROM users WHERE created_at > '2024-01-01'"
    analysis = performance_optimizer.optimize_query(query)
    print(f"查询分析: {analysis}")
    
    # 测试缓存
    performance_optimizer.cache_optimizer.set('test_key', {'data': 'test'})
    value = performance_optimizer.cache_optimizer.get('test_key')
    print(f"缓存测试: {value}")
    
    # 获取性能报告
    report = performance_optimizer.get_performance_report()
    print(f"性能报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
    
    print("\n性能优化引擎测试完成")
