#!/usr/bin/env python3
"""
AI数据库排序检索Agent - 增强数据库查询排序和检索功能
提供智能排序、全文检索、分页查询、复杂条件查询等能力
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import re
import sqlite3
import time
import hashlib
import threading
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engines.ai_employee_system import AIEmployee
from ai_engines.db_schema_registry import TABLE_REGISTRY

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')


class AIDatabaseSortSearchAgent(AIEmployee):
    """AI数据库排序检索Agent - 智能排序和检索"""

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "db_sort_search", level)
        self.type = "db_sort_search"
        self._lock = threading.RLock()
        self._cache = OrderedDict()
        self._cache_max_size = 500
        self._cache_ttl = 300
        self._query_history = []
        self._query_history_max = 1000
        self._db_connections = {}
        self._schema_cache = {}
        self._sort_history = {}

    def start(self):
        self.status = "active"
        logger.info(f"[排序检索Agent] {self.name} 已启动")

    def stop(self):
        self.status = "inactive"
        self._close_connections()
        logger.info(f"[排序检索Agent] {self.name} 已停止")

    def _get_db_connection(self, db_name: str) -> sqlite3.Connection:
        with self._lock:
            if db_name in self._db_connections:
                return self._db_connections[db_name]
            
            db_path = os.path.join(DB_DIR, f"{db_name}.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._db_connections[db_name] = conn
                return conn
            return None

    def _close_connections(self):
        with self._lock:
            for conn in self._db_connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            self._db_connections.clear()

    def _find_table_in_databases(self, table_name: str) -> Optional[str]:
        for db_name in os.listdir(DB_DIR):
            if db_name.endswith('.db'):
                db_path = os.path.join(DB_DIR, db_name)
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                    if cursor.fetchone():
                        conn.close()
                        return db_name[:-3]
                    conn.close()
                except Exception:
                    continue
        return None

    def _get_cache_key(self, sql: str, params: Tuple = ()) -> str:
        key_data = f"{sql}:{params}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry['timestamp'] < self._cache_ttl:
                    entry['hits'] += 1
                    self._cache.move_to_end(key)
                    return entry['data']
                else:
                    del self._cache[key]
        return None

    def _set_to_cache(self, key: str, data: Any):
        with self._lock:
            if len(self._cache) >= self._cache_max_size:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'hits': 1
            }

    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        if table_name in self._schema_cache:
            return self._schema_cache[table_name]
        
        for db_name in os.listdir(DB_DIR):
            if db_name.endswith('.db'):
                db_path = os.path.join(DB_DIR, db_name)
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    if columns:
                        schema = {
                            'table': table_name,
                            'database': db_name[:-3],
                            'columns': [{'name': col[1], 'type': col[2]} for col in columns]
                        }
                        self._schema_cache[table_name] = schema
                        conn.close()
                        return schema
                    conn.close()
                except Exception:
                    continue
        return None

    def _execute_sql(self, db_name: str, sql: str, params: Tuple = ()) -> Dict:
        try:
            conn = self._get_db_connection(db_name)
            if conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    return {'success': True, 'data': [dict(row) for row in rows]}
                else:
                    conn.commit()
                    return {'success': True, 'affected_rows': cursor.rowcount}
            return {'success': False, 'error': f"无法连接数据库: {db_name}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def smart_sort_query(self, table: str, columns: List[str] = None, 
                        conditions: Dict = None, sort_by: str = None, 
                        sort_order: str = 'ASC', page: int = 1, 
                        page_size: int = 20) -> Dict:
        """智能排序查询"""
        db_name = self._find_table_in_databases(table)
        if not db_name:
            return {'success': False, 'error': f"未找到表: {table}"}

        schema = self.get_table_schema(table)
        if not schema:
            return {'success': False, 'error': f"无法获取表结构: {table}"}

        if columns:
            select_clause = ', '.join(columns)
        else:
            select_clause = '*'

        where_clauses = []
        params = []
        if conditions:
            for key, value in conditions.items():
                if isinstance(value, str):
                    if '%' in value:
                        where_clauses.append(f"{key} LIKE ?")
                    else:
                        where_clauses.append(f"{key} = ?")
                else:
                    where_clauses.append(f"{key} = ?")
                params.append(value)

        where_clause = ''
        if where_clauses:
            where_clause = ' WHERE ' + ' AND '.join(where_clauses)

        if sort_by:
            sort_columns = [col['name'] for col in schema['columns']]
            if sort_by in sort_columns:
                sort_clause = f" ORDER BY {sort_by} {sort_order.upper()}"
            else:
                sort_clause = f" ORDER BY {sort_columns[0]} {sort_order.upper()}"
        else:
            sort_clause = self._infer_sort_clause(table, schema)

        offset = (page - 1) * page_size
        limit_clause = f" LIMIT {page_size} OFFSET {offset}"

        sql = f"SELECT {select_clause} FROM {table}{where_clause}{sort_clause}{limit_clause}"
        
        cache_key = self._get_cache_key(sql, tuple(params))
        cached = self._get_from_cache(cache_key)
        if cached:
            return {'success': True, 'data': cached, 'from_cache': True}

        result = self._execute_sql(db_name, sql, tuple(params))
        
        if result['success']:
            total_sql = f"SELECT COUNT(*) FROM {table}{where_clause}"
            total_result = self._execute_sql(db_name, total_sql, tuple(params))
            total = total_result['data'][0]['COUNT(*)'] if total_result['success'] else len(result['data'])
            
            self._set_to_cache(cache_key, result['data'])
            
            return {
                'success': True,
                'data': result['data'],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'from_cache': False,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        
        return result

    def _infer_sort_clause(self, table: str, schema: Dict) -> str:
        """智能推断排序字段"""
        common_sort_fields = ['created_at', 'updated_at', 'id', 'timestamp', 'date', 'time']
        
        for field in common_sort_fields:
            if field in [col['name'] for col in schema['columns']]:
                return f" ORDER BY {field} DESC"
        
        return " ORDER BY id DESC"

    def full_text_search(self, table: str, search_query: str, 
                        search_fields: List[str] = None, 
                        sort_by: str = None, page: int = 1, 
                        page_size: int = 20) -> Dict:
        """全文检索"""
        db_name = self._find_table_in_databases(table)
        if not db_name:
            return {'success': False, 'error': f"未找到表: {table}"}

        schema = self.get_table_schema(table)
        if not schema:
            return {'success': False, 'error': f"无法获取表结构: {table}"}

        all_columns = [col['name'] for col in schema['columns']]
        
        if search_fields:
            text_columns = [f for f in search_fields if f in all_columns]
        else:
            text_columns = [col['name'] for col in schema['columns'] 
                          if col['type'] in ['TEXT', 'VARCHAR', 'CHAR']]

        if not text_columns:
            return {'success': False, 'error': "没有可搜索的文本字段"}

        search_terms = search_query.split()
        
        where_clauses = []
        params = []
        
        for term in search_terms:
            field_clauses = []
            for field in text_columns:
                field_clauses.append(f"{field} LIKE ?")
                params.append(f"%{term}%")
            if field_clauses:
                where_clauses.append('(' + ' OR '.join(field_clauses) + ')')

        where_clause = ''
        if where_clauses:
            where_clause = ' WHERE ' + ' AND '.join(where_clauses)

        if sort_by and sort_by in all_columns:
            sort_clause = f" ORDER BY {sort_by} DESC"
        else:
            sort_clause = self._infer_sort_clause(table, schema)

        offset = (page - 1) * page_size
        limit_clause = f" LIMIT {page_size} OFFSET {offset}"

        sql = f"SELECT * FROM {table}{where_clause}{sort_clause}{limit_clause}"
        
        cache_key = self._get_cache_key(sql, tuple(params))
        cached = self._get_from_cache(cache_key)
        if cached:
            return {'success': True, 'data': cached, 'from_cache': True}

        result = self._execute_sql(db_name, sql, tuple(params))
        
        if result['success']:
            total_sql = f"SELECT COUNT(*) FROM {table}{where_clause}"
            total_result = self._execute_sql(db_name, total_sql, tuple(params))
            total = total_result['data'][0]['COUNT(*)'] if total_result['success'] else len(result['data'])
            
            self._set_to_cache(cache_key, result['data'])
            
            return {
                'success': True,
                'data': result['data'],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'from_cache': False,
                'search_fields': text_columns,
                'search_query': search_query
            }
        
        return result

    def advanced_query(self, table: str, query_spec: Dict) -> Dict:
        """高级查询接口"""
        db_name = self._find_table_in_databases(table)
        if not db_name:
            return {'success': False, 'error': f"未找到表: {table}"}

        schema = self.get_table_schema(table)
        if not schema:
            return {'success': False, 'error': f"无法获取表结构: {table}"}

        columns = query_spec.get('columns', ['*'])
        conditions = query_spec.get('conditions', {})
        sort_by = query_spec.get('sort_by')
        sort_order = query_spec.get('sort_order', 'ASC')
        page = query_spec.get('page', 1)
        page_size = query_spec.get('page_size', 20)
        group_by = query_spec.get('group_by')
        having = query_spec.get('having')

        select_clause = ', '.join(columns)

        where_clauses = []
        params = []
        if conditions:
            for key, value in conditions.items():
                if isinstance(value, dict):
                    op = value.get('op', '=')
                    val = value.get('value')
                    if op.upper() == 'IN':
                        if isinstance(val, (list, tuple)):
                            placeholders = ', '.join(['?'] * len(val))
                            where_clauses.append(f"{key} IN ({placeholders})")
                            params.extend(val)
                        else:
                            where_clauses.append(f"{key} IN {val}")
                    else:
                        where_clauses.append(f"{key} {op} ?")
                        params.append(val)
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)

        where_clause = ''
        if where_clauses:
            where_clause = ' WHERE ' + ' AND '.join(where_clauses)

        group_clause = ''
        if group_by:
            group_clause = f" GROUP BY {group_by}"
            if having:
                group_clause += f" HAVING {having}"

        if sort_by:
            sort_clause = f" ORDER BY {sort_by} {sort_order.upper()}"
        else:
            sort_clause = self._infer_sort_clause(table, schema)

        offset = (page - 1) * page_size
        limit_clause = f" LIMIT {page_size} OFFSET {offset}"

        sql = f"SELECT {select_clause} FROM {table}{where_clause}{group_clause}{sort_clause}{limit_clause}"
        
        cache_key = self._get_cache_key(sql, tuple(params))
        cached = self._get_from_cache(cache_key)
        if cached:
            return {'success': True, 'data': cached, 'from_cache': True}

        result = self._execute_sql(db_name, sql, tuple(params))
        
        if result['success']:
            total_sql = f"SELECT COUNT(*) FROM {table}{where_clause}"
            total_result = self._execute_sql(db_name, total_sql, tuple(params))
            total = total_result['data'][0]['COUNT(*)'] if total_result['success'] else len(result['data'])
            
            self._set_to_cache(cache_key, result['data'])
            
            return {
                'success': True,
                'data': result['data'],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'from_cache': False
            }
        
        return result

    def natural_language_search(self, query: str) -> Dict:
        """自然语言搜索"""
        patterns = {
            r'.*查找.*用户.*(用户名|姓名).*(?P<keyword>.+)': {
                'table': 'users',
                'search_fields': ['username', 'email'],
                'sort_by': 'created_at'
            },
            r'.*搜索.*管理员': {
                'table': 'users',
                'conditions': {'role': 'admin'},
                'sort_by': 'created_at'
            },
            r'.*搜索.*学生': {
                'table': 'users',
                'conditions': {'role': 'student'},
                'sort_by': 'created_at'
            },
            r'.*(最新|最近).*(日志|记录)': {
                'table': 'error_logs',
                'sort_by': 'timestamp',
                'page_size': 10
            },
            r'.*(错误|问题).*统计': {
                'table': 'error_logs',
                'columns': ['error_type', 'COUNT(*) as count'],
                'group_by': 'error_type'
            },
            r'.*(修复|修复记录)': {
                'table': 'repair_history',
                'sort_by': 'fix_time',
                'page_size': 10
            },
        }

        for pattern, config in patterns.items():
            match = re.match(pattern, query, re.IGNORECASE)
            if match:
                keyword = match.group('keyword') if 'keyword' in match.groupdict() else None
                
                if keyword:
                    return self.full_text_search(
                        table=config['table'],
                        search_query=keyword,
                        search_fields=config.get('search_fields'),
                        sort_by=config.get('sort_by'),
                        page_size=config.get('page_size', 20)
                    )
                else:
                    return self.smart_sort_query(
                        table=config['table'],
                        columns=config.get('columns'),
                        conditions=config.get('conditions'),
                        sort_by=config.get('sort_by'),
                        page_size=config.get('page_size', 20)
                    )

        return {'success': False, 'error': f"无法理解查询: {query}"}

    def multi_table_search(self, tables: List[str], 
                          join_conditions: List[str],
                          search_query: str,
                          select_fields: List[str] = None,
                          sort_by: str = None,
                          page: int = 1,
                          page_size: int = 20) -> Dict:
        """多表联合搜索"""
        if not tables:
            return {'success': False, 'error': '至少需要一个表'}

        main_db = self._find_table_in_databases(tables[0])
        if not main_db:
            return {'success': False, 'error': f"未找到表: {tables[0]}"}

        if select_fields:
            select_clause = ', '.join(select_fields)
        else:
            select_clause = '*'

        from_clause = tables[0]
        for i in range(1, len(tables)):
            if join_conditions[i-1]:
                from_clause += f" JOIN {tables[i]} ON {join_conditions[i-1]}"

        search_terms = search_query.split()
        where_clauses = []
        params = []

        for term in search_terms:
            where_clauses.append(f"({tables[0]}.username LIKE ? OR {tables[0]}.email LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])

        where_clause = ''
        if where_clauses:
            where_clause = ' WHERE ' + ' AND '.join(where_clauses)

        if sort_by:
            sort_clause = f" ORDER BY {sort_by} DESC"
        else:
            sort_clause = " ORDER BY id DESC"

        offset = (page - 1) * page_size
        limit_clause = f" LIMIT {page_size} OFFSET {offset}"

        sql = f"SELECT {select_clause} FROM {from_clause}{where_clause}{sort_clause}{limit_clause}"
        
        cache_key = self._get_cache_key(sql, tuple(params))
        cached = self._get_from_cache(cache_key)
        if cached:
            return {'success': True, 'data': cached, 'from_cache': True}

        result = self._execute_sql(main_db, sql, tuple(params))
        
        if result['success']:
            total_sql = f"SELECT COUNT(*) FROM {from_clause}{where_clause}"
            total_result = self._execute_sql(main_db, total_sql, tuple(params))
            total = total_result['data'][0]['COUNT(*)'] if total_result['success'] else len(result['data'])
            
            self._set_to_cache(cache_key, result['data'])
            
            return {
                'success': True,
                'data': result['data'],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'from_cache': False
            }
        
        return result

    def get_search_suggestions(self, table: str, prefix: str) -> List[str]:
        """获取搜索建议"""
        db_name = self._find_table_in_databases(table)
        if not db_name:
            return []

        schema = self.get_table_schema(table)
        if not schema:
            return []

        text_columns = [col['name'] for col in schema['columns'] 
                      if col['type'] in ['TEXT', 'VARCHAR', 'CHAR']]
        
        suggestions = set()
        for col in text_columns:
            sql = f"SELECT DISTINCT {col} FROM {table} WHERE {col} LIKE ? LIMIT 10"
            result = self._execute_sql(db_name, sql, (f"{prefix}%",))
            if result['success']:
                for row in result['data']:
                    suggestions.add(row[col])
        
        return list(suggestions)[:10]

    def get_cache_stats(self) -> Dict:
        with self._lock:
            total_hits = sum(entry['hits'] for entry in self._cache.values())
            return {
                'cache_size': len(self._cache),
                'max_size': self._cache_max_size,
                'total_hits': total_hits,
                'cache_ttl': self._cache_ttl
            }

    def clear_cache(self):
        with self._lock:
            self._cache.clear()
        logger.info("[排序检索Agent] 缓存已清空")
