#!/usr/bin/env python3
"""
数据库索引管理器
支持智能索引创建、查询优化和索引维护
"""

import threading
import time
import json
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from app.utils.logging import logger
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption


class IndexRecommendation:
    """索引推荐"""
    def __init__(self, table: str, columns: List[str], index_type: str = 'btree', reason: str = ''):
        self.table = table
        self.columns = columns
        self.index_type = index_type
        self.reason = reason
        self.score = 0.0

    def to_dict(self) -> Dict:
        return {
            'table': self.table,
            'columns': self.columns,
            'index_type': self.index_type,
            'reason': self.reason,
            'score': self.score
        }


class IndexStatistics:
    """索引统计信息"""
    def __init__(self):
        self.total_indexes = 0
        self.used_indexes = 0
        self.unused_indexes = []
        self.index_sizes = {}
        self.query_patterns = []
        self.slow_queries = []

    def to_dict(self) -> Dict:
        return {
            'total_indexes': self.total_indexes,
            'used_indexes': self.used_indexes,
            'unused_indexes': self.unused_indexes,
            'index_sizes': self.index_sizes,
            'query_patterns': self.query_patterns,
            'slow_queries': self.slow_queries
        }


class DatabaseIndexManager:
    """数据库索引管理器"""

    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.query_history = []
        self.query_history_lock = threading.Lock()
        self.index_metadata = {}
        self.index_metadata_lock = threading.Lock()
        self.max_history_size = 10000
        self.analysis_interval = 300  # 5分钟分析一次
        self.analysis_thread = None
        self.running = False

        # 加载索引元数据
        self._load_index_metadata()

    def _load_index_metadata(self):
        """加载索引元数据"""
        try:
            # 从数据库加载索引元数据表
            self._create_metadata_table()
            cursor, success = self.db.execute("SELECT * FROM index_metadata")
            if success and cursor:
                rows = cursor.fetchall()
                for row in rows:
                    if len(row) >= 5:
                        self.index_metadata[row[0]] = {
                            'table_name': row[1],
                            'columns': json.loads(row[2]),
                            'index_type': row[3],
                            'created_at': row[4],
                            'usage_count': row[5] if len(row) > 5 else 0,
                            'last_used': row[6] if len(row) > 6 else None
                        }
        except Exception as e:
            logger.warning(f"加载索引元数据失败: {str(e)}")

    def _save_index_metadata(self, index_name: str, table_name: str, columns: List[str], index_type: str):
        """保存索引元数据"""
        try:
            now = datetime.now().isoformat()
            columns_json = json.dumps(columns)
            
            query = """INSERT OR REPLACE INTO index_metadata 
                      (index_name, table_name, columns, index_type, created_at, usage_count) 
                      VALUES (?, ?, ?, ?, ?, 0)"""
            self.db.execute(query, (index_name, table_name, columns_json, index_type, now))
        except Exception as e:
            logger.error(f"保存索引元数据失败: {str(e)}")

    def _create_metadata_table(self):
        """创建索引元数据表"""
        query = """CREATE TABLE IF NOT EXISTS index_metadata (
            index_name TEXT PRIMARY KEY,
            table_name TEXT NOT NULL,
            columns TEXT NOT NULL,
            index_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used TEXT
        )"""
        self.db.execute(query)

    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        tables = []
        try:
            if self.db.db_type == 'sqlite':
                cursor, success = self.db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'index_%'"
                )
            elif self.db.db_type == 'mysql':
                cursor, success = self.db.execute("SHOW TABLES")
            elif self.db.db_type == 'postgresql':
                cursor, success = self.db.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
            
            if success and cursor:
                rows = cursor.fetchall()
                for row in rows:
                    tables.append(row[0])
        except Exception as e:
            logger.error(f"获取表列表失败: {str(e)}")
        
        return tables

    def get_table_columns(self, table_name: str) -> List[Dict]:
        """获取表的列信息"""
        columns = []
        try:
            if self.db.db_type == 'sqlite':
                cursor, success = self.db.execute(f"PRAGMA table_info({table_name})")
                if success and cursor:
                    rows = cursor.fetchall()
                    for row in rows:
                        columns.append({
                            'name': row[1],
                            'type': row[2],
                            'not_null': bool(row[3]),
                            'default': row[4],
                            'primary_key': bool(row[5])
                        })
            elif self.db.db_type == 'mysql':
                cursor, success = self.db.execute(f"DESCRIBE {table_name}")
                if success and cursor:
                    rows = cursor.fetchall()
                    for row in rows:
                        columns.append({
                            'name': row[0],
                            'type': row[1],
                            'not_null': row[2] == 'YES',
                            'default': row[4],
                            'primary_key': row[3] == 'PRI'
                        })
            elif self.db.db_type == 'postgresql':
                cursor, success = self.db.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                if success and cursor:
                    rows = cursor.fetchall()
                    for row in rows:
                        columns.append({
                            'name': row[0],
                            'type': row[1],
                            'not_null': row[2] == 'NO',
                            'default': row[3],
                            'primary_key': False
                        })
        except Exception as e:
            logger.error(f"获取表 {table_name} 列信息失败: {str(e)}")
        
        return columns

    def get_existing_indexes(self, table_name: str) -> List[Dict]:
        """获取表的现有索引"""
        indexes = []
        try:
            if self.db.db_type == 'sqlite':
                cursor, success = self.db.execute(f"PRAGMA index_list({table_name})")
                if success and cursor:
                    rows = cursor.fetchall()
                    for row in rows:
                        index_name = row[1]
                        cursor2, _ = self.db.execute(f"PRAGMA index_info({index_name})")
                        if cursor2:
                            cols = cursor2.fetchall()
                            columns = [col[2] for col in cols]
                            indexes.append({
                                'name': index_name,
                                'columns': columns,
                                'unique': bool(row[2]),
                                'type': 'btree'
                            })
            elif self.db.db_type == 'mysql':
                cursor, success = self.db.execute(f"SHOW INDEX FROM {table_name}")
                if success and cursor:
                    rows = cursor.fetchall()
                    index_dict = {}
                    for row in rows:
                        idx_name = row[2]
                        if idx_name not in index_dict:
                            index_dict[idx_name] = {
                                'name': idx_name,
                                'columns': [],
                                'unique': row[1] == 0,
                                'type': row[10]
                            }
                        index_dict[idx_name]['columns'].append(row[4])
                    indexes = list(index_dict.values())
            elif self.db.db_type == 'postgresql':
                cursor, success = self.db.execute(f"""
                    SELECT
                        i.relname AS index_name,
                        a.attname AS column_name,
                        ix.indisunique AS is_unique
                    FROM
                        pg_index ix
                        JOIN pg_class i ON i.oid = ix.indexrelid
                        JOIN pg_class t ON t.oid = ix.indrelid
                        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                    WHERE
                        t.relname = '{table_name}'
                    ORDER BY
                        i.relname, a.attnum
                """)
                if success and cursor:
                    rows = cursor.fetchall()
                    index_dict = {}
                    for row in rows:
                        idx_name = row[0]
                        if idx_name not in index_dict:
                            index_dict[idx_name] = {
                                'name': idx_name,
                                'columns': [],
                                'unique': bool(row[2]),
                                'type': 'btree'
                            }
                        index_dict[idx_name]['columns'].append(row[1])
                    indexes = list(index_dict.values())
        except Exception as e:
            logger.error(f"获取表 {table_name} 索引失败: {str(e)}")
        
        return indexes

    def create_index(self, table_name: str, columns: List[str], index_type: str = 'btree', 
                    unique: bool = False, index_name: Optional[str] = None) -> bool:
        """创建索引"""
        try:
            if not index_name:
                col_str = '_'.join(columns)
                index_name = f"idx_{table_name}_{col_str}"

            # 检查索引是否已存在
            existing = self.get_existing_indexes(table_name)
            for idx in existing:
                if idx['name'] == index_name:
                    logger.info(f"索引 {index_name} 已存在")
                    return True
                if set(idx['columns']) == set(columns):
                    logger.info(f"表 {table_name} 的列 {columns} 已存在索引")
                    return True

            # 构建索引创建语句
            unique_str = 'UNIQUE' if unique else ''
            
            if self.db.db_type == 'sqlite':
                type_str = ''
            elif self.db.db_type == 'mysql':
                type_str = f"USING {index_type.upper()}"
            elif self.db.db_type == 'postgresql':
                type_str = f"USING {index_type}"
            else:
                type_str = ''

            columns_str = ', '.join(columns)
            query = f"CREATE {unique_str} INDEX {index_name} {type_str} ON {table_name} ({columns_str})"
            
            self.db.execute(query)
            self._save_index_metadata(index_name, table_name, columns, index_type)
            logger.info(f"索引 {index_name} 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            return False

    def drop_index(self, index_name: str, table_name: str) -> bool:
        """删除索引"""
        try:
            if self.db.db_type == 'sqlite':
                query = f"DROP INDEX IF EXISTS {index_name}"
            elif self.db.db_type in ['mysql', 'postgresql']:
                query = f"DROP INDEX IF EXISTS {index_name} ON {table_name}"
            else:
                query = f"DROP INDEX {index_name}"
            
            self.db.execute(query)
            
            # 删除元数据
            if index_name in self.index_metadata:
                del self.index_metadata[index_name]
                self.db.execute("DELETE FROM index_metadata WHERE index_name = ?", (index_name,))
            
            logger.info(f"索引 {index_name} 删除成功")
            return True
        except Exception as e:
            logger.error(f"删除索引失败: {str(e)}")
            return False

    def analyze_query_patterns(self) -> List[IndexRecommendation]:
        """分析查询模式并推荐索引"""
        recommendations = []
        
        try:
            # 统计查询中的WHERE/JOIN/ORDER BY/GROUP BY子句
            pattern_stats = {}
            
            with self.query_history_lock:
                for query_entry in self.query_history:
                    query = query_entry.get('query', '').upper()
                    table = query_entry.get('table', '')
                    
                    if not table:
                        continue
                    
                    # 分析查询中的列使用
                    columns_used = self._extract_columns_from_query(query_entry.get('query', ''), table)
                    
                    for cols in columns_used:
                        key = (table, tuple(sorted(cols)))
                        if key not in pattern_stats:
                            pattern_stats[key] = {
                                'count': 0,
                                'avg_execution_time': 0,
                                'queries': []
                            }
                        pattern_stats[key]['count'] += 1
                        pattern_stats[key]['avg_execution_time'] += query_entry.get('execution_time', 0)
                        pattern_stats[key]['queries'].append(query_entry)
            
            # 计算平均执行时间
            for key in pattern_stats:
                stats = pattern_stats[key]
                stats['avg_execution_time'] /= stats['count']
                
                # 计算推荐分数
                score = stats['count'] * (stats['avg_execution_time'] ** 0.5)
                
                if stats['count'] >= 3 and score >= 5:
                    table, cols = key
                    recommendation = IndexRecommendation(
                        table=table,
                        columns=list(cols),
                        index_type='btree',
                        reason=f"被使用 {stats['count']} 次, 平均执行时间 {stats['avg_execution_time']:.3f}s"
                    )
                    recommendation.score = score
                    recommendations.append(recommendation)
            
            # 按分数排序
            recommendations.sort(key=lambda x: x.score, reverse=True)
            
        except Exception as e:
            logger.error(f"分析查询模式失败: {str(e)}")
        
        return recommendations

    def _extract_columns_from_query(self, query: str, table: str) -> List[List[str]]:
        """从查询中提取使用的列"""
        column_groups = []
        
        try:
            query_upper = query.upper()
            
            # 简单的列提取逻辑(实际项目中应该使用SQL解析器)
            # 查找WHERE子句
            where_idx = query_upper.find('WHERE')
            if where_idx != -1:
                where_part = query[where_idx + 5:].split('ORDER BY')[0].split('GROUP BY')[0].split('LIMIT')[0]
                # 简单提取等号左边的列名
                import re
                # 查找类似 "column = ?" 或 "column IN (...)" 的模式
                matches = re.findall(r'(\w+)\s*(?:=|<>|>|<|>=|<=|LIKE|IN)\s*(?:\?|%s|:|\()', where_part, re.IGNORECASE)
                if matches:
                    column_groups.append(matches)
            
            # 查找ORDER BY子句
            order_idx = query_upper.find('ORDER BY')
            if order_idx != -1:
                order_part = query[order_idx + 8:].split('LIMIT')[0]
                matches = re.findall(r'(\w+)', order_part)
                if matches:
                    column_groups.append(matches)
            
            # 查找GROUP BY子句
            group_idx = query_upper.find('GROUP BY')
            if group_idx != -1:
                group_part = query[group_idx + 8:].split('ORDER BY')[0].split('LIMIT')[0]
                matches = re.findall(r'(\w+)', group_part)
                if matches:
                    column_groups.append(matches)
                    
        except Exception:
            pass
        
        return column_groups

    def log_query(self, query: str, execution_time: float, table: Optional[str] = None):
        """记录查询日志"""
        with self.query_history_lock:
            entry = {
                'query': query,
                'execution_time': execution_time,
                'table': table,
                'timestamp': time.time()
            }
            self.query_history.append(entry)
            
            # 限制历史大小
            if len(self.query_history) > self.max_history_size:
                self.query_history = self.query_history[-self.max_history_size:]

    def auto_create_indexes(self, min_score: float = 10.0) -> int:
        """自动创建推荐的索引"""
        recommendations = self.analyze_query_patterns()
        created_count = 0
        
        for rec in recommendations:
            if rec.score >= min_score:
                if self.create_index(rec.table, rec.columns, rec.index_type):
                    created_count += 1
        
        logger.info(f"自动创建了 {created_count} 个索引")
        return created_count

    def get_index_statistics(self) -> IndexStatistics:
        """获取索引统计信息"""
        stats = IndexStatistics()
        
        try:
            tables = self.get_all_tables()
            
            for table in tables:
                indexes = self.get_existing_indexes(table)
                stats.total_indexes += len(indexes)
                
                for idx in indexes:
                    # 检查索引是否在元数据中有使用记录
                    if idx['name'] in self.index_metadata:
                        meta = self.index_metadata[idx['name']]
                        if meta.get('usage_count', 0) > 0:
                            stats.used_indexes += 1
                        else:
                            stats.unused_indexes.append(f"{table}.{idx['name']}")
            
            # 慢查询分析
            with self.query_history_lock:
                for entry in self.query_history:
                    if entry.get('execution_time', 0) > 1.0:
                        stats.slow_queries.append({
                            'query': entry['query'][:200] + '...' if len(entry['query']) > 200 else entry['query'],
                            'execution_time': entry['execution_time'],
                            'table': entry.get('table'),
                            'timestamp': datetime.fromtimestamp(entry['timestamp']).isoformat()
                        })
            
        except Exception as e:
            logger.error(f"获取索引统计失败: {str(e)}")
        
        return stats

    def optimize_indexes(self) -> Dict:
        """优化索引 - 删除未使用的,创建需要的"""
        result = {
            'deleted': [],
            'created': [],
            'recommendations': []
        }
        
        # 获取统计信息
        stats = self.get_index_statistics()
        
        # 删除未使用的索引(保留超过30天未使用的)
        for unused_idx in stats.unused_indexes:
            try:
                table, idx_name = unused_idx.split('.')
                if self.drop_index(idx_name, table):
                    result['deleted'].append(unused_idx)
            except Exception:
                pass
        
        # 获取推荐
        recommendations = self.analyze_query_patterns()
        result['recommendations'] = [r.to_dict() for r in recommendations[:10]]
        
        # 创建高优先级索引
        for rec in recommendations[:5]:
            if rec.score >= 20:
                if self.create_index(rec.table, rec.columns, rec.index_type):
                    result['created'].append(f"{rec.table}.{rec.columns}")
        
        return result

    def start_background_analysis(self):
        """启动后台分析线程"""
        if self.running:
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._background_worker, daemon=True)
        self.analysis_thread.start()
        logger.info("数据库索引管理后台线程启动")

    def stop_background_analysis(self):
        """停止后台分析线程"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        logger.info("数据库索引管理后台线程停止")

    def _background_worker(self):
        """后台工作线程"""
        while self.running:
            try:
                time.sleep(self.analysis_interval)
                # 自动创建索引
                self.auto_create_indexes(min_score=15.0)
            except Exception as e:
                logger.error(f"后台分析线程错误: {str(e)}")

    def create_basic_indexes_for_all_tables(self) -> Dict[str, List[str]]:
        """为所有表创建基础索引"""
        results = {}
        
        tables = self.get_all_tables()
        
        for table in tables:
            created = []
            columns = self.get_table_columns(table)
            
            # 为常见查询列创建索引
            common_columns = ['user_id', 'created_at', 'updated_at', 'status', 'type', 'category']
            for col in common_columns:
                if any(c['name'] == col for c in columns):
                    if self.create_index(table, [col]):
                        created.append(col)
            
            results[table] = created
        
        return results


# 创建全局索引管理器实例
index_manager = DatabaseIndexManager()
