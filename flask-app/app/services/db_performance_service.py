# -*- coding: utf-8 -*-
"""
数据库性能优化服务
提供数据库索引优化、查询性能监控、分片管理等功能
"""

import os
import sqlite3
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DatabasePerformanceService:
    """数据库性能优化服务"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._db_connections = {}
        self._query_stats = {}
        self._slow_query_threshold = 1.0
        self._initialized = True
        
        logger.info("[数据库性能服务] 初始化完成")
    
    def get_db_connection(self, db_name: str):
        """获取数据库连接"""
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'split_databases')
        
        db_paths = {
            'auth': os.path.join(db_dir, 'auth.db'),
            'exam': os.path.join(db_dir, 'exam.db'),
            'question': os.path.join(db_dir, 'question.db'),
            'learning': os.path.join(db_dir, 'learning.db'),
            'system': os.path.join(db_dir, 'system.db'),
            'ai': os.path.join(db_dir, 'ai.db'),
            'physics': os.path.join(db_dir, 'physics.db'),
            'math': os.path.join(db_dir, 'math.db'),
            'admin': os.path.join(db_dir, 'admin.db'),
            'proctor': os.path.join(db_dir, 'proctor.db'),
            'user': os.path.join(db_dir, 'user.db'),
            'log': os.path.join(db_dir, 'log.db'),
            'other': os.path.join(db_dir, 'other.db'),
            'api_management': os.path.join(db_dir, 'api_management.db'),
            'routes_management': os.path.join(db_dir, 'routes_management.db'),
            'search_models': os.path.join(db_dir, 'search_models.db'),
            'mtscos': os.path.join(db_dir, 'mtscos.db'),
        }
        
        db_path = db_paths.get(db_name)
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        
        if db_name not in self._db_connections:
            conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
            conn.row_factory = sqlite3.Row
            self._db_connections[db_name] = conn
        
        return self._db_connections[db_name]
    
    def execute_with_timing(self, db_name: str, sql: str, params: tuple = ()):
        """执行SQL并记录执行时间"""
        start_time = time.time()
        conn = self.get_db_connection(db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, params)
            conn.commit()
            rows = cursor.fetchall() if sql.strip().upper().startswith('SELECT') else []
            execution_time = time.time() - start_time
            
            self._record_query_stats(db_name, sql, execution_time)
            
            if execution_time > self._slow_query_threshold:
                logger.warning(f"[慢查询] 数据库: {db_name}, 耗时: {execution_time:.2f}s, SQL: {sql[:100]}")
            
            return rows, execution_time
        except Exception as e:
            conn.rollback()
            logger.error(f"[SQL执行失败] 数据库: {db_name}, SQL: {sql[:100]}, 错误: {e}")
            return [], 0
    
    def _record_query_stats(self, db_name: str, sql: str, execution_time: float):
        """记录查询统计"""
        if db_name not in self._query_stats:
            self._query_stats[db_name] = {
                'total_queries': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'slow_queries': 0,
                'query_patterns': {}
            }
        
        stats = self._query_stats[db_name]
        stats['total_queries'] += 1
        stats['total_time'] += execution_time
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        
        if execution_time > self._slow_query_threshold:
            stats['slow_queries'] += 1
        
        pattern = sql.strip().split()[0].upper()
        if pattern not in stats['query_patterns']:
            stats['query_patterns'][pattern] = {'count': 0, 'total_time': 0}
        stats['query_patterns'][pattern]['count'] += 1
        stats['query_patterns'][pattern]['total_time'] += execution_time
    
    def get_query_stats(self, db_name: str = None):
        """获取查询统计"""
        if db_name:
            return self._query_stats.get(db_name, {})
        return self._query_stats
    
    def analyze_table(self, db_name: str, table_name: str):
        """分析表结构和索引"""
        conn = self.get_db_connection(db_name)
        cursor = conn.cursor()
        
        result = {
            'table_name': table_name,
            'columns': [],
            'indexes': [],
            'row_count': 0,
            'size_bytes': 0,
            'recommendations': []
        }
        
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            result['columns'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            result['row_count'] = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            for idx in indexes:
                cursor.execute(f"PRAGMA index_info({idx[1]})")
                columns = [col[2] for col in cursor.fetchall()]
                result['indexes'].append({
                    'name': idx[1],
                    'unique': idx[2],
                    'columns': columns
                })
            
            cursor.execute(f"PRAGMA table_size({table_name})")
            result['size_bytes'] = cursor.fetchone()[0]
            
            self._generate_index_recommendations(result)
            
        except Exception as e:
            logger.error(f"[表分析失败] {db_name}.{table_name}: {e}")
        
        return result
    
    def _generate_index_recommendations(self, table_info: Dict):
        """生成索引建议"""
        recommendations = []
        columns = table_info['columns']
        index_columns = set()
        
        for idx in table_info['indexes']:
            index_columns.update(idx['columns'])
        
        foreign_key_cols = []
        for col in columns:
            if col.get('pk', 0) == 1:
                continue
            
            if col['name'] in ['id', 'created_at', 'updated_at']:
                if col['name'] not in index_columns:
                    recommendations.append({
                        'type': 'INDEX',
                        'column': col['name'],
                        'reason': f"建议为 {col['name']} 添加索引，常用于查询条件或排序"
                    })
            
            if 'id' in col['name'] and col['name'] != 'id':
                foreign_key_cols.append(col['name'])
        
        if foreign_key_cols and not any(set(fk.split('_')[:-1]).intersection(index_columns) for fk in foreign_key_cols):
            recommendations.append({
                'type': 'INDEX',
                'column': ', '.join(foreign_key_cols),
                'reason': f"建议为外键列 {', '.join(foreign_key_cols)} 添加索引，优化关联查询"
            })
        
        table_info['recommendations'] = recommendations
    
    def optimize_database(self, db_name: str):
        """优化数据库"""
        conn = self.get_db_connection(db_name)
        cursor = conn.cursor()
        
        results = {
            'db_name': db_name,
            'optimizations': []
        }
        
        try:
            cursor.execute("VACUUM")
            results['optimizations'].append({
                'type': 'VACUUM',
                'status': 'success',
                'message': '数据库压缩完成'
            })
            
            cursor.execute("PRAGMA optimize")
            results['optimizations'].append({
                'type': 'OPTIMIZE',
                'status': 'success',
                'message': '数据库优化完成'
            })
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"ANALYZE {table}")
            
            results['optimizations'].append({
                'type': 'ANALYZE',
                'status': 'success',
                'message': f'分析了 {len(tables)} 个表'
            })
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"[数据库优化失败] {db_name}: {e}")
            results['optimizations'].append({
                'type': 'ERROR',
                'status': 'failed',
                'message': str(e)
            })
        
        return results
    
    def get_database_status(self):
        """获取所有数据库状态"""
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'split_databases')
        status = []
        
        for db_name in ['auth', 'exam', 'question', 'learning', 'system', 'ai', 
                       'physics', 'math', 'admin', 'proctor', 'user', 'log', 'other',
                       'api_management', 'routes_management', 'search_models', 'mtscos']:
            db_path = os.path.join(db_dir, f'{db_name}.db')
            db_status = {
                'db_name': db_name,
                'exists': os.path.exists(db_path),
                'size_bytes': 0,
                'table_count': 0,
                'total_rows': 0,
                'last_modified': None
            }
            
            if os.path.exists(db_path):
                db_status['size_bytes'] = os.path.getsize(db_path)
                db_status['last_modified'] = datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat()
                
                try:
                    conn = sqlite3.connect(db_path, check_same_thread=False)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    db_status['table_count'] = len(tables)
                    
                    total_rows = 0
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            total_rows += cursor.fetchone()[0]
                        except:
                            pass
                    db_status['total_rows'] = total_rows
                    
                    conn.close()
                except Exception as e:
                    logger.error(f"[数据库状态查询失败] {db_name}: {e}")
            
            status.append(db_status)
        
        return status
    
    def create_index(self, db_name: str, table_name: str, columns: List[str], index_name: str = None):
        """创建索引"""
        conn = self.get_db_connection(db_name)
        cursor = conn.cursor()
        
        if not index_name:
            index_name = f"idx_{table_name}_{'_'.join(columns)}"
        
        column_list = ', '.join(columns)
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_list})"
        
        try:
            cursor.execute(sql)
            conn.commit()
            return {
                'success': True,
                'message': f"索引 {index_name} 创建成功"
            }
        except Exception as e:
            logger.error(f"[索引创建失败] {db_name}.{table_name}: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def drop_index(self, db_name: str, index_name: str):
        """删除索引"""
        conn = self.get_db_connection(db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
            conn.commit()
            return {
                'success': True,
                'message': f"索引 {index_name} 删除成功"
            }
        except Exception as e:
            logger.error(f"[索引删除失败] {db_name}: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_slow_queries(self, db_name: str = None, limit: int = 20):
        """获取慢查询列表"""
        slow_queries = []
        
        for name, stats in self._query_stats.items():
            if db_name and name != db_name:
                continue
            
            for pattern, pattern_stats in stats.get('query_patterns', {}).items():
                avg_time = pattern_stats['total_time'] / pattern_stats['count']
                if avg_time > self._slow_query_threshold:
                    slow_queries.append({
                        'db_name': name,
                        'pattern': pattern,
                        'count': pattern_stats['count'],
                        'avg_time': avg_time,
                        'total_time': pattern_stats['total_time']
                    })
        
        slow_queries.sort(key=lambda x: x['avg_time'], reverse=True)
        return slow_queries[:limit]
    
    def reset_stats(self):
        """重置统计数据"""
        self._query_stats = {}
        logger.info("[数据库性能服务] 统计数据已重置")


db_performance_service = DatabasePerformanceService()
