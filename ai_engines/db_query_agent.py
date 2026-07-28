#!/usr/bin/env python3
"""
AI数据库查询Agent - 增强数据库查询功能
提供自然语言转SQL、查询优化、智能缓存、多库路由等能力
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
from ai_engines.db_schema_registry import TABLE_REGISTRY, TableCategory, FeatureModule, DataHeat

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')


class AIDatabaseQueryAgent(AIEmployee):
    """AI数据库查询Agent - 智能数据库查询与优化"""

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "db_query", level)
        self.type = "db_query"
        self._lock = threading.RLock()
        self._cache = OrderedDict()
        self._cache_max_size = 500
        self._cache_ttl = 300
        self._query_history = []
        self._query_history_max = 1000
        self._db_connections = {}
        self._schema_cache = {}

    def start(self):
        """启动Agent"""
        self.status = "active"
        logger.info(f"[DB查询Agent] {self.name} 已启动")

    def stop(self):
        """停止Agent"""
        self.status = "inactive"
        self._close_connections()
        logger.info(f"[DB查询Agent] {self.name} 已停止")

    def _get_db_connection(self, db_name: str) -> sqlite3.Connection:
        """获取数据库连接（带连接池）"""
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
        """关闭所有数据库连接"""
        with self._lock:
            for conn in self._db_connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            self._db_connections.clear()

    def _get_cache_key(self, sql: str, params: Tuple = ()) -> str:
        """生成缓存键"""
        key_data = f"{sql}:{params}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
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
        """存入缓存"""
        with self._lock:
            if len(self._cache) >= self._cache_max_size:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            
            self._cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'hits': 1
            }

    def _log_query(self, sql: str, params: Tuple, result: Any, execution_time: float):
        """记录查询历史"""
        with self._lock:
            entry = {
                'sql': sql,
                'params': params,
                'result_count': len(result) if isinstance(result, list) else 1,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            self._query_history.append(entry)
            if len(self._query_history) > self._query_history_max:
                self._query_history.pop(0)

    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """获取表结构信息"""
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

    def execute_query(self, sql: str, params: Tuple = (), use_cache: bool = True) -> Dict:
        """执行SQL查询"""
        start_time = time.time()
        
        cache_key = self._get_cache_key(sql, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                execution_time = time.time() - start_time
                self._log_query(sql, params, cached_data, execution_time)
                return {
                    'success': True,
                    'data': cached_data,
                    'execution_time': execution_time,
                    'from_cache': True
                }
        
        try:
            db_name = self._infer_database_from_sql(sql)
            conn = self._get_db_connection(db_name)
            
            if conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    data = [dict(row) for row in rows]
                else:
                    conn.commit()
                    data = {'affected_rows': cursor.rowcount}
                
                execution_time = time.time() - start_time
                
                if use_cache and sql.strip().upper().startswith('SELECT'):
                    self._set_to_cache(cache_key, data)
                
                self._log_query(sql, params, data, execution_time)
                
                return {
                    'success': True,
                    'data': data,
                    'execution_time': execution_time,
                    'from_cache': False
                }
            else:
                return {'success': False, 'error': f"无法连接数据库: {db_name}"}
        
        except Exception as e:
            execution_time = time.time() - start_time
            return {'success': False, 'error': str(e), 'execution_time': execution_time}

    def _infer_database_from_sql(self, sql: str) -> str:
        """从SQL推断目标数据库"""
        tables_in_sql = re.findall(r'\bFROM\s+(\w+)\b|\bJOIN\s+(\w+)\b', sql, re.IGNORECASE)
        tables = [t[0] or t[1] for t in tables_in_sql]
        
        for table in tables:
            db_name = self._find_table_in_databases(table)
            if db_name:
                return db_name
        
        for table in tables:
            if table in TABLE_REGISTRY:
                shard_db = TABLE_REGISTRY[table].get('shard_db', 'other')
                if shard_db.endswith('.db'):
                    shard_db = shard_db[:-3]
                return shard_db
        
        return 'other'
    
    def _find_table_in_databases(self, table_name: str) -> Optional[str]:
        """在所有数据库中查找表"""
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

    def optimize_query(self, sql: str) -> str:
        """优化SQL查询"""
        optimized = sql
        
        optimized = re.sub(r'\bSELECT\s+\*\b', 'SELECT', optimized, flags=re.IGNORECASE)
        
        optimized = re.sub(r'\bORDER\s+BY\s+\*\b', '', optimized, flags=re.IGNORECASE)
        
        if 'LIMIT' not in optimized.upper() and ('SELECT' in optimized.upper() or 'QUERY' in optimized.upper()):
            if optimized.strip().endswith(';'):
                optimized = optimized[:-1] + ' LIMIT 1000;'
            else:
                optimized += ' LIMIT 1000'
        
        return optimized

    def natural_to_sql(self, natural_query: str) -> str:
        """自然语言转SQL"""
        query = natural_query.lower().strip()
        
        mappings = {
            r'.*所有.*用户': 'SELECT * FROM users',
            r'.*用户数量': 'SELECT COUNT(*) as count FROM users',
            r'.*最近.*登录': 'SELECT * FROM users ORDER BY last_login DESC LIMIT 10',
            r'.*活跃.*用户': 'SELECT * FROM users WHERE status = "active"',
            r'.*管理员': 'SELECT * FROM users WHERE role = "admin"',
            r'.*学生': 'SELECT * FROM users WHERE role = "student"',
            r'.*题目.*总数': 'SELECT COUNT(*) as count FROM questions',
            r'.*最新.*题目': 'SELECT * FROM questions ORDER BY created_at DESC LIMIT 10',
            r'.*考试.*记录': 'SELECT * FROM exam_records ORDER BY exam_date DESC LIMIT 10',
            r'.*错误.*日志': 'SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 10',
            r'.*修复.*记录': 'SELECT * FROM repair_history ORDER BY fix_time DESC LIMIT 10',
        }
        
        for pattern, sql_template in mappings.items():
            if re.match(pattern, query):
                return sql_template
        
        return f"-- 无法自动转换: {natural_query}"

    def analyze_query_performance(self, top_n: int = 10) -> List[Dict]:
        """分析查询性能"""
        slow_queries = sorted(
            self._query_history,
            key=lambda x: x['execution_time'],
            reverse=True
        )[:top_n]
        
        return [{
            'sql': q['sql'][:100] + '...' if len(q['sql']) > 100 else q['sql'],
            'execution_time': round(q['execution_time'], 4),
            'result_count': q['result_count'],
            'timestamp': q['timestamp']
        } for q in slow_queries]

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        with self._lock:
            total_hits = sum(entry['hits'] for entry in self._cache.values())
            return {
                'cache_size': len(self._cache),
                'max_size': self._cache_max_size,
                'total_hits': total_hits,
                'cache_ttl': self._cache_ttl
            }

    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
        logger.info("[DB查询Agent] 缓存已清空")

    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        stats = {}
        for db_name in os.listdir(DB_DIR):
            if db_name.endswith('.db'):
                db_path = os.path.join(DB_DIR, db_name)
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [t[0] for t in cursor.fetchall()]
                    
                    table_counts = {}
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            table_counts[table] = cursor.fetchone()[0]
                        except Exception:
                            table_counts[table] = 'N/A'
                    
                    stats[db_name[:-3]] = {
                        'tables': tables,
                        'table_counts': table_counts,
                        'total_tables': len(tables)
                    }
                    conn.close()
                except Exception as e:
                    stats[db_name[:-3]] = {'error': str(e)}
        
        return stats

    def smart_query(self, query: str, params: Tuple = (), optimize: bool = True) -> Dict:
        """智能查询入口"""
        if not query.strip():
            return {'success': False, 'error': '查询语句为空'}
        
        if query.strip().startswith('--'):
            sql = self.natural_to_sql(query[2:].strip())
        else:
            sql = query
        
        if optimize:
            sql = self.optimize_query(sql)
        
        logger.info(f"[DB查询Agent] 执行查询: {sql[:100]}...")
        return self.execute_query(sql, params)

    def batch_query(self, queries: List[str]) -> List[Dict]:
        """批量执行查询"""
        results = []
        for query in queries:
            results.append(self.smart_query(query))
        return results

    def join_query(self, tables: List[str], conditions: List[str], select_fields: List[str] = None) -> Dict:
        """多表联合查询"""
        if not tables:
            return {'success': False, 'error': '至少需要一个表'}
        
        if select_fields:
            select_clause = ', '.join(select_fields)
        else:
            select_clause = '*'
        
        from_clause = ' JOIN '.join(tables)
        
        if conditions:
            where_clause = ' WHERE ' + ' AND '.join(conditions)
        else:
            where_clause = ''
        
        sql = f"SELECT {select_clause} FROM {from_clause}{where_clause} LIMIT 1000"
        
        return self.execute_query(sql)

    def aggregate_query(self, table: str, group_by: str, aggregations: Dict) -> Dict:
        """聚合查询"""
        agg_clauses = []
        for func, field in aggregations.items():
            agg_clauses.append(f"{func.upper()}({field}) as {func}_{field}")
        
        sql = f"SELECT {group_by}, {', '.join(agg_clauses)} FROM {table} GROUP BY {group_by} LIMIT 1000"
        
        return self.execute_query(sql)
