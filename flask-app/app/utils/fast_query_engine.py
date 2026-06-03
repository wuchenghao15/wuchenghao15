# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
快速查询检索引擎
支持全文搜索、多维度查询、缓存加速和智能查询优化
"""

import threading
import time
import re
import json
import hashlib
from typing import List, Dict, Tuple, Optional, Any, Union
from datetime import datetime
from functools import lru_cache
from collections import defaultdict
from app.utils.logging import logger
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption
import logging


class SearchResult:
    """搜索结果"""
    def __init__(self):
        self.results = []
        self.total = 0
        self.page = 1
        self.page_size = 20
        self.execution_time = 0.0
        self.highlighted = {}

    def to_dict(self) -> Dict:
        return {
            'results': self.results,
            'total': self.total,
            'page': self.page,
            'page_size': self.page_size,
            'execution_time': self.execution_time,
            'highlighted': self.highlighted
        }


class QueryCache:
    """查询缓存"""
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if time.time() - entry['timestamp'] > self.ttl:
                del self.cache[key]
                del self.access_times[key]
                return None
            
            self.access_times[key] = time.time()
            return entry['data']

    def set(self, key: str, data: Any):
        with self.lock:
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[key] = {
                'data': data,
                'timestamp': time.time()
            }
            self.access_times[key] = time.time()

    def _evict_oldest(self):
        """淘汰最旧的缓存"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        if oldest_key in self.cache:
            del self.cache[oldest_key]
        if oldest_key in self.access_times:
            del self.access_times[oldest_key]

    def clear(self, pattern: Optional[str] = None):
        """清除缓存"""
        with self.lock:
            if pattern:
                keys_to_delete = [k for k in self.cache.keys() if pattern in k]
                for k in keys_to_delete:
                    del self.cache[k]
                    if k in self.access_times:
                        del self.access_times[k]
            else:
                self.cache.clear()
                self.access_times.clear()


class InvertedIndex:
    """倒排索引 - 用于全文搜索"""
    def __init__(self):
        self.index = defaultdict(set)
        self.documents = {}
        self.lock = threading.RLock()

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """添加文档到索引"""
        with self.lock:
            self.documents[doc_id] = {
                'text': text,
                'metadata': metadata or {},
                'timestamp': time.time()
            }
            
            # 分词并建立索引
            words = self._tokenize(text)
            for word in words:
                self.index[word.lower()].add(doc_id)

    def remove_document(self, doc_id: str):
        """移除文档"""
        with self.lock:
            if doc_id in self.documents:
                del self.documents[doc_id]
            
            # 从索引中移除
            for word in list(self.index.keys()):
                if doc_id in self.index[word]:
                    self.index[word].remove(doc_id)
                    if not self.index[word]:
                        del self.index[word]

    def search(self, query: str, limit: int = 100) -> List[Dict]:
        """搜索"""
        with self.lock:
            query_words = self._tokenize(query)
            if not query_words:
                return []
            
            # 找到包含所有查询词的文档
            doc_scores = defaultdict(float)
            
            for word in query_words:
                word_lower = word.lower()
                if word_lower in self.index:
                    for doc_id in self.index[word_lower]:
                        doc_scores[doc_id] += 1.0
            
            # 按分数排序
            sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
            
            # 返回结果
            results = []
            for doc_id, score in sorted_docs[:limit]:
                if doc_id in self.documents:
                    doc = self.documents[doc_id]
                    results.append({
                        'id': doc_id,
                        'score': score,
                        'text': doc['text'],
                        'metadata': doc['metadata']
                    })
            
            return results

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 移除标点符号并分割
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        # 简单的n-gram处理
        ngrams = []
        for word in words:
            if len(word) > 2:
                for i in range(len(word) - 1):
                    ngrams.append(word[i:i+2])
        return words + ngrams


class FastQueryEngine:
    """快速查询引擎"""

    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.cache = QueryCache(max_size=2000, ttl=300)
        self.inverted_index = InvertedIndex()
        self.query_stats = defaultdict(int)
        self.stats_lock = threading.Lock()
        
        # 预加载配置
        self._init_search_tables()

    def _init_search_tables(self):
        """初始化搜索表"""
        try:
            # 创建全文搜索元数据表
            query = """CREATE TABLE IF NOT EXISTS search_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                primary_key TEXT NOT NULL,
                search_columns TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_indexed TEXT
            )"""
            self.db.execute(query)
            
            # 创建搜索缓存表
            query = """CREATE TABLE IF NOT EXISTS search_cache (
                cache_key TEXT PRIMARY KEY,
                result_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )"""
            self.db.execute(query)
        except Exception as e:
            logger.warning(f"初始化搜索表失败: {str(e)}")

    def _generate_cache_key(self, query_type: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = {'type': query_type, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def register_search_table(self, table_name: str, primary_key: str, search_columns: List[str]):
        """注册可搜索的表"""
        try:
            now = datetime.now().isoformat()
            columns_json = json.dumps(search_columns)
            
            query = """INSERT OR REPLACE INTO search_metadata 
                      (table_name, primary_key, search_columns, created_at) 
                      VALUES (?, ?, ?, ?)"""
            self.db.execute(query, (table_name, primary_key, columns_json, now))
            
            logger.info(f"表 {table_name} 已注册为搜索表")
        except Exception as e:
            logger.error(f"注册搜索表失败: {str(e)}")

    def fulltext_search(self, table_name: str, query: str, 
                       columns: Optional[List[str]] = None,
                       filters: Optional[Dict] = None,
                       page: int = 1,
                       page_size: int = 20,
                       use_cache: bool = True) -> SearchResult:
        """全文搜索"""
        start_time = time.time()
        result = SearchResult()
        result.page = page
        result.page_size = page_size
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(
                'fulltext', 
                table=table_name, 
                query=query, 
                columns=columns,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    result.results = cached
                    result.execution_time = time.time() - start_time
                    result.total = len(cached)
                    return result
            
            # 获取搜索列
            if not columns:
                columns = self._get_search_columns(table_name)
            
            if not columns:
                logger.warning(f"表 {table_name} 没有配置搜索列")
                return result
            
            # 构建搜索查询
            where_clauses = []
            params = []
            
            # 全文搜索条件
            search_conditions = []
            for col in columns:
                search_conditions.append(f"{col} LIKE ?")
                params.append(f"%{query}%")
            
            if search_conditions:
                where_clauses.append(f"({' OR '.join(search_conditions)})")
            
            # 过滤条件
            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
            
            # 构建查询
            where_str = ' AND '.join(where_clauses) if where_clauses else '1=1'
            
            # 计数查询
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_str}"
            total = self.db.fetch_scalar(count_query, tuple(params)) or 0
            result.total = total
            
            # 数据查询
            offset = (page - 1) * page_size
            data_query = f"SELECT * FROM {table_name} WHERE {where_str} LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            
            rows = self.db.fetch_all(data_query, tuple(params))
            result.results = rows
            
            # 高亮
            result.highlighted = self._highlight_results(rows, query, columns)
            
            # 缓存结果
            if use_cache:
                self.cache.set(cache_key, rows)
            
            # 更新统计
            with self.stats_lock:
                self.query_stats[f'fulltext:{table_name}'] += 1
            
        except Exception as e:
            logger.error(f"全文搜索失败: {str(e)}")
        
        result.execution_time = time.time() - start_time
        return result

    def _get_search_columns(self, table_name: str) -> List[str]:
        """获取表的搜索列"""
        try:
            query = "SELECT search_columns FROM search_metadata WHERE table_name = ?"
            result = self.db.fetch_one(query, (table_name,))
            if result:
                if isinstance(result, dict):
                    return json.loads(result.get('search_columns', '[]'))
                else:
                    return json.loads(result[0])
        except Exception:
            pass
        return []

    def _highlight_results(self, results: List[Dict], query: str, columns: List[str]) -> Dict[str, str]:
        """高亮搜索结果"""
        highlighted = {}
        
        for i, row in enumerate(results):
            row_dict = row if isinstance(row, dict) else {}
            for col in columns:
                if col in row_dict:
                    text = str(row_dict[col])
                    if query.lower() in text.lower():
                        # 简单的高亮
                        highlighted_text = text.replace(
                            query, 
                            f"<mark>{query}</mark>"
                        )
                        highlighted[f"{i}:{col}"] = highlighted_text
        
        return highlighted

    def multidimensional_query(self, table_name: str, 
                             conditions: Dict[str, Any],
                             order_by: Optional[List[Tuple[str, str]]] = None,
                             page: int = 1,
                             page_size: int = 20,
                             use_cache: bool = True) -> SearchResult:
        """多维度查询"""
        start_time = time.time()
        result = SearchResult()
        result.page = page
        result.page_size = page_size
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(
                'multidim',
                table=table_name,
                conditions=conditions,
                order_by=order_by,
                page=page,
                page_size=page_size
            )
            
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    result.results = cached
                    result.execution_time = time.time() - start_time
                    result.total = len(cached)
                    return result
            
            # 构建查询
            where_clauses = []
            params = []
            
            for key, value in conditions.items():
                if isinstance(value, dict):
                    # 高级条件: { 'gt': 100, 'lt': 200 }
                    for op, val in value.items():
                        if op == 'eq':
                            where_clauses.append(f"{key} = ?")
                            params.append(val)
                        elif op == 'ne':
                            where_clauses.append(f"{key} != ?")
                            params.append(val)
                        elif op == 'gt':
                            where_clauses.append(f"{key} > ?")
                            params.append(val)
                        elif op == 'lt':
                            where_clauses.append(f"{key} < ?")
                            params.append(val)
                        elif op == 'gte':
                            where_clauses.append(f"{key} >= ?")
                            params.append(val)
                        elif op == 'lte':
                            where_clauses.append(f"{key} <= ?")
                            params.append(val)
                        elif op == 'in':
                            placeholders = ','.join(['?'] * len(val))
                            where_clauses.append(f"{key} IN ({placeholders})")
                            params.extend(val)
                        elif op == 'like':
                            where_clauses.append(f"{key} LIKE ?")
                            params.append(val)
                elif isinstance(value, list):
                    placeholders = ','.join(['?'] * len(value))
                    where_clauses.append(f"{key} IN ({placeholders})")
                    params.extend(value)
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
            
            where_str = ' AND '.join(where_clauses) if where_clauses else '1=1'
            
            # ORDER BY
            order_str = ''
            if order_by:
                order_parts = []
                for col, direction in order_by:
                    order_parts.append(f"{col} {direction.upper()}")
                order_str = ' ORDER BY ' + ', '.join(order_parts)
            
            # 计数查询
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_str}"
            total = self.db.fetch_scalar(count_query, tuple(params)) or 0
            result.total = total
            
            # 数据查询
            offset = (page - 1) * page_size
            data_query = f"SELECT * FROM {table_name} WHERE {where_str}{order_str} LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            
            rows = self.db.fetch_all(data_query, tuple(params))
            result.results = rows
            
            # 缓存结果
            if use_cache:
                self.cache.set(cache_key, rows)
            
            # 更新统计
            with self.stats_lock:
                self.query_stats[f'multidim:{table_name}'] += 1
            
        except Exception as e:
            logger.error(f"多维度查询失败: {str(e)}")
        
        result.execution_time = time.time() - start_time
        return result

    def aggregate_query(self, table_name: str, 
                       group_by: List[str],
                       aggregations: Dict[str, str],
                       filters: Optional[Dict] = None,
                       use_cache: bool = True) -> List[Dict]:
        """聚合查询"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(
                'aggregate',
                table=table_name,
                group_by=group_by,
                aggregations=aggregations,
                filters=filters
            )
            
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    return cached
            
            # 构建查询
            select_parts = group_by.copy()
            for alias, agg in aggregations.items():
                select_parts.append(f"{agg} AS {alias}")
            
            where_clauses = []
            params = []
            
            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
            
            where_str = ' AND '.join(where_clauses) if where_clauses else '1=1'
            group_str = ', '.join(group_by)
            
            query = f"SELECT {', '.join(select_parts)} FROM {table_name} WHERE {where_str} GROUP BY {group_str}"
            
            results = self.db.fetch_all(query, tuple(params))
            
            # 缓存结果
            if use_cache:
                self.cache.set(cache_key, results)
            
            # 更新统计
            with self.stats_lock:
                self.query_stats[f'aggregate:{table_name}'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"聚合查询失败: {str(e)}")
            return []

    def batch_get(self, table_name: str, ids: List[Any], 
                 id_column: str = 'id',
                 use_cache: bool = True) -> Dict[Any, Dict]:
        """批量获取"""
        if not ids:
            return {}
        
        start_time = time.time()
        results = {}
        
        try:
            # 尝试从缓存获取
            cached_results = {}
            missing_ids = []
            
            if use_cache:
                for id_val in ids:
                    cache_key = self._generate_cache_key('get', table=table_name, id=id_val)
                    cached = self.cache.get(cache_key)
                    if cached:
                        cached_results[id_val] = cached
                    else:
                        missing_ids.append(id_val)
            else:
                missing_ids = ids
            
            # 获取缺失的数据
            if missing_ids:
                placeholders = ','.join(['?'] * len(missing_ids))
                query = f"SELECT * FROM {table_name} WHERE {id_column} IN ({placeholders})"
                rows = self.db.fetch_all(query, tuple(missing_ids))
                
                for row in rows:
                    row_dict = row if isinstance(row, dict) else {}
                    id_val = row_dict.get(id_column, row[0] if row else None)
                    if id_val is not None:
                        results[id_val] = row_dict
                        if use_cache:
                            cache_key = self._generate_cache_key('get', table=table_name, id=id_val)
                            self.cache.set(cache_key, row_dict)
            
            # 合并结果
            results.update(cached_results)
            
            # 更新统计
            with self.stats_lock:
                self.query_stats['batch_get'] += 1
            
        except Exception as e:
            logger.error(f"批量获取失败: {str(e)}")
        
        return results

    def invalidate_table_cache(self, table_name: str):
        """清除表相关缓存"""
        self.cache.clear(table_name)
        logger.info(f"表 {table_name} 缓存已清除")

    def get_query_stats(self) -> Dict:
        """获取查询统计"""
        with self.stats_lock:
            return dict(self.query_stats)

    def clear_all_cache(self):
        """清除所有缓存"""
        self.cache.clear()
        logger.info("所有缓存已清除")

    def build_in_memory_index(self, table_name: str, text_column: str, id_column: str = 'id'):
        """构建内存倒排索引"""
        try:
            query = f"SELECT {id_column}, {text_column} FROM {table_name}"
            rows = self.db.fetch_all(query)
            
            for row in rows:
                row_dict = row if isinstance(row, dict) else {}
                doc_id = str(row_dict.get(id_column, row[0] if row else ''))
                text = str(row_dict.get(text_column, ''))
                self.inverted_index.add_document(doc_id, text, {'table': table_name})
            
            logger.info(f"表 {table_name} 内存索引构建完成")
        except Exception as e:
            logger.error(f"构建内存索引失败: {str(e)}")

    def search_in_memory(self, query: str, limit: int = 100) -> List[Dict]:
        """内存搜索"""
        return self.inverted_index.search(query, limit)


# 创建全局快速查询引擎实例
fast_query = FastQueryEngine()
