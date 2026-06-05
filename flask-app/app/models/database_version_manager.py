#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库版本管理系统
提供数据库版本控制、优化和变更追踪功能
"""

import sqlite3
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from app.utils.logging import logger


class DatabaseVersionManager:
    """数据库版本管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        self.db_path = db_path
        self._init_version_table()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_version_table(self):
        """初始化版本记录表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建数据库版本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL UNIQUE,
                    major_version INTEGER DEFAULT 1,
                    minor_version INTEGER DEFAULT 0,
                    patch_version INTEGER DEFAULT 0,
                    description TEXT,
                    changes TEXT,
                    schema_hash TEXT,
                    data_hash TEXT,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    applied_at TEXT,
                    status TEXT DEFAULT 'pending',
                    rollback_available INTEGER DEFAULT 0,
                    backup_data BLOB
                )
            ''')
            
            # 创建数据库变更记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    table_name TEXT,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    sql_statement TEXT,
                    affected_rows INTEGER DEFAULT 0,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    rollback_sql TEXT,
                    rollback_status TEXT DEFAULT 'not_applied'
                )
            ''')
            
            # 创建数据库优化记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_optimization_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    optimization_type TEXT NOT NULL,
                    description TEXT,
                    tables_affected TEXT,
                    space_saved INTEGER DEFAULT 0,
                    performance_gain REAL DEFAULT 0.0,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    executed_by TEXT DEFAULT 'system',
                    status TEXT DEFAULT 'success'
                )
            ''')
            
            # 创建数据库索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_indexes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    index_name TEXT NOT NULL UNIQUE,
                    columns TEXT NOT NULL,
                    is_unique INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TEXT,
                    efficiency_score REAL DEFAULT 0.0
                )
            ''')
            
            logger.info("数据库版本控制表初始化完成")
    
    def _calculate_schema_hash(self) -> str:
        """计算数据库模式哈希"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_str = ""
            for table in tables:
                if table.startswith('sqlite_'):
                    continue
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
                row = cursor.fetchone()
                if row:
                    schema_str += row[0]
            
            return hashlib.sha256(schema_str.encode()).hexdigest()
    
    def _calculate_data_hash(self) -> str:
        """计算数据哈希"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            data_parts = []
            for table in tables:
                if table.startswith('sqlite_'):
                    continue
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                data_parts.append(f"{table}:{count}")
            
            return hashlib.sha256(",".join(data_parts).encode()).hexdigest()
    
    def create_version(self, version: str, description: str, changes: List[str], 
                      created_by: str = 'system') -> bool:
        """创建新版本记录"""
        try:
            version_parts = version.split('.')
            major = int(version_parts[0]) if len(version_parts) > 0 else 1
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2]) if len(version_parts) > 2 else 0
            
            schema_hash = self._calculate_schema_hash()
            data_hash = self._calculate_data_hash()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO db_version_history 
                    (version, major_version, minor_version, patch_version, description, 
                     changes, schema_hash, data_hash, created_by, applied_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version, major, minor, patch, description,
                    json.dumps(changes, ensure_ascii=False), schema_hash, data_hash,
                    created_by, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'applied'
                ))
                
                logger.info(f"数据库版本记录已创建: {version}")
                return True
        except Exception as e:
            logger.error(f"创建版本记录失败: {e}")
            return False
    
    def record_change(self, version: str, change_type: str, table_name: str = None,
                     field_name: str = None, old_value: Any = None, new_value: Any = None,
                     sql_statement: str = None, affected_rows: int = 0,
                     created_by: str = 'system', rollback_sql: str = None) -> bool:
        """记录数据库变更"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO db_change_log 
                    (version, change_type, table_name, field_name, old_value, new_value,
                     sql_statement, affected_rows, created_by, rollback_sql)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version, change_type, table_name, field_name,
                    str(old_value) if old_value is not None else None,
                    str(new_value) if new_value is not None else None,
                    sql_statement, affected_rows, created_by, rollback_sql
                ))
                
                logger.info(f"数据库变更已记录: {change_type} on {table_name}")
                return True
        except Exception as e:
            logger.error(f"记录变更失败: {e}")
            return False
    
    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """获取版本信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM db_version_history WHERE version = ?", (version,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_versions(self) -> List[Dict[str, Any]]:
        """获取所有版本"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM db_version_history ORDER BY major_version DESC, minor_version DESC, patch_version DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_changes_by_version(self, version: str) -> List[Dict[str, Any]]:
        """获取指定版本的变更"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM db_change_log WHERE version = ? ORDER BY id", (version,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取优化历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM db_optimization_log ORDER BY id DESC LIMIT {limit}")
            return [dict(row) for row in cursor.fetchall()]
    
    def optimize_database(self, optimization_type: str = 'vacuum') -> Dict[str, Any]:
        """优化数据库"""
        start_time = time.time()
        result = {
            'success': False,
            'optimization_type': optimization_type,
            'tables_affected': [],
            'space_saved': 0,
            'performance_gain': 0.0,
            'execution_time': 0.0
        }
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取优化前的数据库大小
                cursor.execute("PRAGMA page_count")
                page_count_before = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                size_before = page_count_before * page_size
                
                # 执行优化
                if optimization_type == 'vacuum':
                    conn.execute("VACUUM")
                elif optimization_type == 'analyze':
                    conn.execute("ANALYZE")
                elif optimization_type == 'reindex':
                    # 重新索引所有表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
                    indexes = [row[0] for row in cursor.fetchall()]
                    for index_name in indexes:
                        if not index_name.startswith('sqlite_'):
                            conn.execute(f"REINDEX {index_name}")
                    result['tables_affected'] = indexes
                
                # 获取优化后的数据库大小
                cursor.execute("PRAGMA page_count")
                page_count_after = cursor.fetchone()[0]
                size_after = page_count_after * page_size
                
                result['space_saved'] = max(0, size_before - size_after)
                result['execution_time'] = time.time() - start_time
                result['success'] = True
                
                # 记录优化操作
                self._log_optimization(
                    optimization_type=optimization_type,
                    description=f"数据库{optimization_type}优化完成",
                    tables_affected=json.dumps(result['tables_affected']),
                    space_saved=result['space_saved'],
                    performance_gain=result['performance_gain']
                )
                
                logger.info(f"数据库优化完成: {optimization_type}, 节省空间: {result['space_saved']} bytes")
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
            result['error'] = str(e)
        
        return result
    
    def _log_optimization(self, optimization_type: str, description: str,
                        tables_affected: str, space_saved: int, 
                        performance_gain: float, executed_by: str = 'system') -> bool:
        """记录优化操作"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO db_optimization_log 
                    (optimization_type, description, tables_affected, space_saved, 
                     performance_gain, executed_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (optimization_type, description, tables_affected, 
                     space_saved, performance_gain, executed_by))
                return True
        except Exception as e:
            logger.error(f"记录优化失败: {e}")
            return False
    
    def analyze_indexes(self) -> List[Dict[str, Any]]:
        """分析数据库索引"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取所有索引
            cursor.execute('''
                SELECT name, tbl_name, sql FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL
            ''')
            
            indexes = []
            for row in cursor.fetchall():
                index_name, table_name, sql = row
                if not index_name.startswith('sqlite_'):
                    # 分析索引使用情况
                    cursor.execute(f"EXPLAIN QUERY PLAN SELECT * FROM {table_name} WHERE rowid=1")
                    
                    indexes.append({
                        'index_name': index_name,
                        'table_name': table_name,
                        'sql': sql,
                        'is_unique': 'UNIQUE' in sql.upper(),
                        'created_at': datetime.now().isoformat(),
                        'efficiency_score': 0.0  # 可以基于查询分析计算
                    })
            
            return indexes
    
    def create_index(self, table_name: str, column_name: str, 
                    index_name: str = None, unique: bool = False) -> bool:
        """创建索引"""
        try:
            if index_name is None:
                index_name = f"idx_{table_name}_{column_name}"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查索引是否已存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
                if cursor.fetchone():
                    logger.info(f"索引已存在: {index_name}")
                    return False
                
                # 创建索引
                unique_str = "UNIQUE" if unique else ""
                cursor.execute(f"CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
                
                # 记录索引创建
                self._record_index(table_name, index_name, column_name, unique)
                
                logger.info(f"索引创建成功: {index_name}")
                return True
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def _record_index(self, table_name: str, index_name: str, columns: str, 
                     is_unique: bool = 0) -> bool:
        """记录索引创建"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO db_indexes 
                    (table_name, index_name, columns, is_unique)
                    VALUES (?, ?, ?, ?)
                ''', (table_name, index_name, columns, is_unique))
                return True
        except Exception as e:
            logger.error(f"记录索引失败: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = []
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"PRAGMA table_info({table})")
                columns = len(cursor.fetchall())
                
                table_stats.append({
                    'table_name': table,
                    'row_count': count,
                    'column_count': columns
                })
            
            # 获取数据库大小
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            total_size = page_count * page_size
            
            # 获取索引数量
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            index_count = cursor.fetchone()[0]
            
            return {
                'total_tables': len(tables),
                'total_indexes': index_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'table_stats': table_stats,
                'version_count': self._get_version_count()
            }
    
    def _get_version_count(self) -> int:
        """获取版本数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM db_version_history")
            return cursor.fetchone()[0]
    
    def generate_version_report(self, version: str = None) -> Dict[str, Any]:
        """生成版本报告"""
        if version:
            version_info = self.get_version_info(version)
            changes = self.get_changes_by_version(version)
            return {
                'version': version_info,
                'changes': changes,
                'change_count': len(changes)
            }
        else:
            all_versions = self.get_all_versions()
            return {
                'versions': all_versions,
                'total_versions': len(all_versions),
                'database_stats': self.get_database_stats()
            }
    
    def export_version_history(self, filepath: str, format: str = 'json') -> bool:
        """导出版本历史"""
        try:
            data = {
                'exported_at': datetime.now().isoformat(),
                'database_path': self.db_path,
                'versions': self.get_all_versions(),
                'database_stats': self.get_database_stats(),
                'optimization_history': self.get_optimization_history(50)
            }
            
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == 'markdown':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self._generate_markdown_report(data))
            
            logger.info(f"版本历史已导出: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出版本历史失败: {e}")
            return False
    
    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """生成Markdown报告"""
        md = "# 数据库版本报告\n\n"
        md += f"**导出时间**: {data['exported_at']}\n\n"
        md += f"**数据库路径**: {data['database_path']}\n\n"
        
        stats = data['database_stats']
        md += "## 数据库统计\n\n"
        md += f"- 表数量: {stats['total_tables']}\n"
        md += f"- 索引数量: {stats['total_indexes']}\n"
        md += f"- 数据库大小: {stats['total_size_mb']} MB\n"
        md += f"- 版本数量: {stats['version_count']}\n\n"
        
        md += "## 版本历史\n\n"
        for version in data['versions']:
            md += f"### v{version['version']}\n\n"
            md += f"**日期**: {version['created_at']}\n\n"
            md += f"**描述**: {version['description']}\n\n"
            if version.get('changes'):
                changes = json.loads(version['changes'])
                md += "**变更**:\n"
                for change in changes:
                    md += f"- {change}\n"
            md += "\n---\n\n"
        
        return md


# 创建全局实例
db_version_manager = DatabaseVersionManager()
