#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS JSON 数据同步数据库系统 (JsonDbSync)
============================================
功能：
  - JSON→数据库导入（Schema自动推断 + 批量插入）
  - 数据库→JSON导出（表数据→JSON文件）
  - 双向同步（文件变更检测 + 增量同步）
  - SSOT 持久化（同步注册表 + 同步日志）

遵循：
  - SSOT 原则（数据库为权威源）
  - 双库双写
  - 审计日志

版本: v1.0.0
"""

import os
import sys
import json
import time
import uuid
import hashlib
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('json_db_sync')


# ============================================================================
# 枚举定义
# ============================================================================

class SyncDirection(Enum):
    """同步方向"""
    JSON_TO_DB = "json_to_db"    # JSON → 数据库
    DB_TO_JSON = "db_to_json"    # 数据库 → JSON
    BIDIRECTIONAL = "bidirectional"  # 双向


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"
    SKIPPED = "skipped"


class ConflictStrategy(Enum):
    """冲突处理策略"""
    DB_PRIORITY = "db_priority"      # 数据库优先（SSOT）
    JSON_PRIORITY = "json_priority"  # JSON优先
    LATEST_WINS = "latest_wins"      # 最新时间戳优先
    MANUAL = "manual"                # 手动处理


# ============================================================================
# Schema 推断器
# ============================================================================

class SchemaInferrer:
    """JSON Schema 推断器 — 从JSON结构推断数据库表结构"""

    # JSON类型到SQLite类型映射
    TYPE_MAP = {
        'int': 'INTEGER',
        'float': 'REAL',
        'str': 'TEXT',
        'bool': 'INTEGER',  # SQLite无BOOL
        'null': 'TEXT',
        'list': 'TEXT',     # JSON序列化
        'dict': 'TEXT',     # JSON序列化
    }

    @staticmethod
    def infer_type(value: Any) -> str:
        """推断单个值的类型"""
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'bool'
        if isinstance(value, int):
            return 'int'
        if isinstance(value, float):
            return 'float'
        if isinstance(value, str):
            return 'str'
        if isinstance(value, list):
            return 'list'
        if isinstance(value, dict):
            return 'dict'
        return 'str'

    @staticmethod
    def infer_widest_type(types: Set[str]) -> str:
        """从多个类型中取最宽类型"""
        if not types:
            return 'TEXT'
        if len(types) == 1:
            return SchemaInferrer.TYPE_MAP.get(types.pop(), 'TEXT')
        # 类型优先级：str > float > int > bool > null
        if 'str' in types:
            return 'TEXT'
        if 'float' in types:
            return 'REAL'
        if 'int' in types:
            return 'INTEGER'
        if 'bool' in types:
            return 'INTEGER'
        return 'TEXT'

    @staticmethod
    def infer_schema(data: Union[Dict, List]) -> Dict[str, str]:
        """
        从JSON数据推断表结构

        Args:
            data: JSON数据（对象或对象数组）

        Returns:
            {字段名: SQLite类型}
        """
        if isinstance(data, dict):
            records = [data]
        elif isinstance(data, list):
            records = [r for r in data if isinstance(r, dict)]
        else:
            return {}

        if not records:
            return {}

        # 收集所有字段及其类型
        field_types: Dict[str, set] = {}
        for record in records:
            for key, value in record.items():
                t = SchemaInferrer.infer_type(value)
                if key not in field_types:
                    field_types[key] = set()
                field_types[key].add(t)

        # 推断最宽类型
        schema = {}
        for field, types in field_types.items():
            schema[field] = SchemaInferrer.infer_widest_type(types)

        return schema

    @staticmethod
    def generate_table_name(json_filepath: str) -> str:
        """从JSON文件路径生成表名"""
        basename = os.path.basename(json_filepath)
        name = os.path.splitext(basename)[0]
        # 清理特殊字符
        name = ''.join(c if c.isalnum() else '_' for c in name)
        return f'json_{name}'

    @staticmethod
    def serialize_value(value: Any) -> Any:
        """序列化值用于数据库存储"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, bool):
            return 1 if value else 0
        if value is None:
            return None
        return value

    @staticmethod
    def deserialize_value(value: Any, target_type: str) -> Any:
        """从数据库反序列化值"""
        if value is None:
            return None
        if target_type in ('list', 'dict'):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        if target_type == 'bool':
            try:
                return bool(int(value))
            except (ValueError, TypeError):
                return value
        if target_type == 'int':
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        if target_type == 'float':
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        return value


# 导入Set类型
from typing import Set


# ============================================================================
# JSON 导入器
# ============================================================================

class JsonImporter:
    """JSON → 数据库导入器"""

    def __init__(self, db_path: str = None, dual_db=None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.stats = {
            'total_imports': 0,
            'total_records': 0,
            'total_tables_created': 0,
            'failed_imports': 0,
        }

    def _get_connection(self):
        """获取数据库连接"""
        if self.dual_db:
            return None  # 使用 dual_db 的方法
        return sqlite3.connect(self.db_path, timeout=10)

    def import_json_file(self, filepath: str, table_name: str = None,
                         mode: str = 'replace') -> Dict[str, Any]:
        """
        导入JSON文件到数据库

        Args:
            filepath: JSON文件路径
            table_name: 目标表名（默认自动生成）
            mode: 导入模式 (replace/append/upsert)

        Returns:
            导入结果
        """
        result = {
            'filepath': filepath,
            'table_name': table_name or SchemaInferrer.generate_table_name(filepath),
            'mode': mode,
            'success': False,
            'records_imported': 0,
            'schema': {},
            'error': None,
        }

        try:
            # 读取JSON文件
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 标准化为记录列表
            if isinstance(data, dict):
                records = [data]
            elif isinstance(data, list):
                records = [r for r in data if isinstance(r, dict)]
            else:
                result['error'] = f'不支持的JSON类型: {type(data).__name__}'
                return result

            if not records:
                result['error'] = '无有效记录'
                return result

            # 推断Schema
            schema = SchemaInferrer.infer_schema(data)
            result['schema'] = schema

            # 创建/更新表
            self._create_table(result['table_name'], schema)

            # 导入数据
            count = self._insert_records(result['table_name'], schema, records, mode)

            result['success'] = True
            result['records_imported'] = count
            self.stats['total_imports'] += 1
            self.stats['total_records'] += count

            logger.info(f"JSON导入成功: {filepath} → {result['table_name']} ({count}条)")

        except json.JSONDecodeError as e:
            result['error'] = f'JSON解析失败: {e}'
            self.stats['failed_imports'] += 1
        except Exception as e:
            result['error'] = str(e)
            self.stats['failed_imports'] += 1
            logger.error(f"JSON导入失败 {filepath}: {e}")

        return result

    def _create_table(self, table_name: str, schema: Dict[str, str]):
        """创建或更新表"""
        if not schema:
            return

        # 如果JSON已有id字段，使用它作为主键，否则自增
        if 'id' in schema:
            columns = [f'"id" {schema["id"]} PRIMARY KEY']
            for field, sql_type in schema.items():
                if field == 'id':
                    continue
                safe_field = field.replace("'", "''")
                columns.append(f'"{safe_field}" {sql_type}')
        else:
            columns = ['_rowid INTEGER PRIMARY KEY AUTOINCREMENT']
            for field, sql_type in schema.items():
                safe_field = field.replace("'", "''")
                columns.append(f'"{safe_field}" {sql_type}')

        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)})'

        if self.dual_db:
            self.dual_db.execute_write(create_sql, ())
        else:
            conn = self._get_connection()
            conn.execute(create_sql)
            conn.commit()
            conn.close()

        self.stats['total_tables_created'] += 1

    def _insert_records(self, table_name: str, schema: Dict[str, str],
                        records: List[Dict], mode: str) -> int:
        """插入记录"""
        if not records or not schema:
            return 0

        fields = list(schema.keys())
        placeholders = ', '.join(['?'] * len(fields))
        safe_fields = ', '.join([f'"{f.replace(chr(39), chr(39)+chr(39))}"' for f in fields])

        if mode == 'replace':
            # 先清空再插入
            delete_sql = f'DELETE FROM "{table_name}"'
            if self.dual_db:
                self.dual_db.execute_write(delete_sql, ())
            else:
                conn = self._get_connection()
                conn.execute(delete_sql)
                conn.commit()
                conn.close()

        # 准备数据
        values = []
        for record in records:
            row = []
            for field in fields:
                val = record.get(field)
                row.append(SchemaInferrer.serialize_value(val))
            values.append(tuple(row))

        insert_sql = f'INSERT INTO "{table_name}" ({safe_fields}) VALUES ({placeholders})'

        if self.dual_db:
            # 双库批量插入
            for val_tuple in values:
                self.dual_db.execute_write(insert_sql, val_tuple)
        else:
            conn = self._get_connection()
            conn.executemany(insert_sql, values)
            conn.commit()
            conn.close()

        return len(values)

    def import_directory(self, dir_path: str, pattern: str = '*.json') -> List[Dict[str, Any]]:
        """批量导入目录中的JSON文件"""
        import glob
        results = []
        json_files = glob.glob(os.path.join(dir_path, pattern))

        for filepath in json_files:
            result = self.import_json_file(filepath)
            results.append(result)

        return results


# ============================================================================
# 数据库导出器
# ============================================================================

class DbExporter:
    """数据库 → JSON 导出器"""

    def __init__(self, db_path: str = None, dual_db=None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.stats = {
            'total_exports': 0,
            'total_records': 0,
            'failed_exports': 0,
        }

    def export_table_to_json(self, table_name: str, output_path: str = None,
                             as_array: bool = True) -> Dict[str, Any]:
        """
        将数据库表导出为JSON文件

        Args:
            table_name: 表名
            output_path: 输出路径（默认 table_name.json）
            as_array: True=数组, False=单对象（仅1条记录时）

        Returns:
            导出结果
        """
        if output_path is None:
            output_path = f'{table_name}.json'

        result = {
            'table_name': table_name,
            'output_path': output_path,
            'success': False,
            'records_exported': 0,
            'error': None,
        }

        try:
            # 查询数据
            if self.dual_db:
                rows = self.dual_db.execute_query(f'SELECT * FROM "{table_name}"', ())
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = [dict(row) for row in cursor.fetchall()]
                conn.close()

            # 移除内部字段 (id/_rowid)
            records = []
            for row in rows:
                record = {k: v for k, v in row.items() if k not in ('id', '_rowid')}
                records.append(record)

            # 写入JSON文件
            if as_array or len(records) > 1:
                output_data = records
            elif len(records) == 1:
                output_data = records[0]
            else:
                output_data = []

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            result['success'] = True
            result['records_exported'] = len(records)
            self.stats['total_exports'] += 1
            self.stats['total_records'] += len(records)

            logger.info(f"数据库导出成功: {table_name} → {output_path} ({len(records)}条)")

        except Exception as e:
            result['error'] = str(e)
            self.stats['failed_exports'] += 1
            logger.error(f"导出失败 {table_name}: {e}")

        return result


# ============================================================================
# 同步管理器
# ============================================================================

class SyncManager:
    """双向同步管理器 — JSON ↔ 数据库"""

    def __init__(self, project_dir: str, db_path: str = None, dual_db=None):
        self.project_dir = project_dir
        self.db_path = db_path
        self.dual_db = dual_db
        self.importer = JsonImporter(db_path, dual_db)
        self.exporter = DbExporter(db_path, dual_db)

        # 同步注册表: {filepath: {table_name, sha256, mtime, last_sync}}
        self.sync_registry: Dict[str, Dict[str, Any]] = {}

        # 配置
        self.conflict_strategy = ConflictStrategy.DB_PRIORITY
        self.auto_sync = True

        # 统计
        self.stats = {
            'total_syncs': 0,
            'json_to_db_syncs': 0,
            'db_to_json_syncs': 0,
            'conflicts': 0,
            'skipped': 0,
        }

        self._ensure_tables()
        self._load_registry()

    def _ensure_tables(self):
        """创建同步注册表和日志表"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_json_sync_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE NOT NULL,
                    table_name TEXT NOT NULL,
                    direction TEXT DEFAULT 'json_to_db',
                    sha256 TEXT,
                    file_mtime TEXT,
                    last_sync_at TEXT,
                    last_sync_status TEXT DEFAULT 'pending',
                    record_count INTEGER DEFAULT 0,
                    auto_sync INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_json_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_id TEXT UNIQUE NOT NULL,
                    filepath TEXT,
                    table_name TEXT,
                    direction TEXT,
                    status TEXT,
                    records_affected INTEGER DEFAULT 0,
                    error_message TEXT,
                    synced_at TEXT DEFAULT (datetime('now', 'localtime')),
                    operator TEXT DEFAULT 'system'
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"创建同步表失败: {e}")

    def _load_registry(self):
        """加载同步注册表"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mt_json_sync_registry")
            for row in cursor.fetchall():
                self.sync_registry[row['filepath']] = {
                    'table_name': row['table_name'],
                    'direction': row['direction'],
                    'sha256': row['sha256'],
                    'mtime': row['file_mtime'],
                    'last_sync': row['last_sync_at'],
                    'status': row['last_sync_status'],
                    'record_count': row['record_count'],
                }
            conn.close()
            logger.info(f"加载同步注册表: {len(self.sync_registry)} 个文件")
        except Exception as e:
            logger.error(f"加载注册表失败: {e}")

    def _compute_sha256(self, filepath: str) -> str:
        """计算文件SHA256"""
        h = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def register_sync(self, filepath: str, table_name: str = None,
                      direction: str = 'json_to_db', auto_sync: bool = True) -> Dict[str, Any]:
        """
        注册文件同步

        Args:
            filepath: JSON文件路径
            table_name: 目标表名
            direction: 同步方向
            auto_sync: 是否自动同步

        Returns:
            注册结果
        """
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.project_dir, filepath)

        table_name = table_name or SchemaInferrer.generate_table_name(filepath)
        sha256 = self._compute_sha256(filepath) if os.path.exists(filepath) else ""
        mtime = str(os.path.getmtime(filepath)) if os.path.exists(filepath) else ""

        self.sync_registry[filepath] = {
            'table_name': table_name,
            'direction': direction,
            'sha256': sha256,
            'mtime': mtime,
            'last_sync': None,
            'status': 'pending',
            'record_count': 0,
        }

        # 落库
        self._save_registry(filepath, table_name, direction, sha256, mtime, auto_sync)

        return {
            'success': True,
            'filepath': filepath,
            'table_name': table_name,
            'direction': direction,
        }

    def _save_registry(self, filepath: str, table_name: str, direction: str,
                       sha256: str, mtime: str, auto_sync: bool):
        """保存注册到数据库"""
        if not self.db_path:
            return
        try:
            if self.dual_db:
                self.dual_db.execute_write(
                    """INSERT OR REPLACE INTO mt_json_sync_registry
                    (filepath, table_name, direction, sha256, file_mtime, last_sync_at, last_sync_status, auto_sync)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (filepath, table_name, direction, sha256, mtime,
                     datetime.now().isoformat(), 1 if auto_sync else 0)
                )
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO mt_json_sync_registry
                    (filepath, table_name, direction, sha256, file_mtime, last_sync_at, last_sync_status, auto_sync)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (filepath, table_name, direction, sha256, mtime,
                     datetime.now().isoformat(), 1 if auto_sync else 0)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"保存注册失败: {e}")

    def _log_sync(self, filepath: str, table_name: str, direction: str,
                  status: str, records: int, error: str = None, operator: str = 'system'):
        """记录同步日志"""
        sync_id = f"SYNC_{int(time.time()*1000)}_{direction}_{uuid.uuid4().hex[:8]}"
        if not self.db_path:
            return
        try:
            if self.dual_db:
                self.dual_db.execute_write(
                    """INSERT INTO mt_json_sync_log
                    (sync_id, filepath, table_name, direction, status, records_affected, error_message, operator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sync_id, filepath, table_name, direction, status, records, error, operator)
                )
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO mt_json_sync_log
                    (sync_id, filepath, table_name, direction, status, records_affected, error_message, operator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sync_id, filepath, table_name, direction, status, records, error, operator)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"日志写入失败: {e}")

    def sync_json_to_db(self, filepath: str, table_name: str = None,
                        mode: str = 'replace') -> Dict[str, Any]:
        """JSON → 数据库同步"""
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.project_dir, filepath)

        if not os.path.exists(filepath):
            return {'success': False, 'error': '文件不存在'}

        result = self.importer.import_json_file(filepath, table_name, mode)
        self.stats['total_syncs'] += 1
        self.stats['json_to_db_syncs'] += 1

        self._log_sync(filepath, result['table_name'], 'json_to_db',
                       'success' if result['success'] else 'failed',
                       result['records_imported'],
                       result.get('error'))

        # 更新注册表
        if result['success']:
            sha256 = self._compute_sha256(filepath)
            mtime = str(os.path.getmtime(filepath))
            self.sync_registry[filepath] = {
                'table_name': result['table_name'],
                'sha256': sha256,
                'mtime': mtime,
                'last_sync': datetime.now().isoformat(),
                'status': 'success',
                'record_count': result['records_imported'],
            }

        return result

    def sync_db_to_json(self, table_name: str, output_path: str = None) -> Dict[str, Any]:
        """数据库 → JSON 同步"""
        result = self.exporter.export_table_to_json(table_name, output_path)
        self.stats['total_syncs'] += 1
        self.stats['db_to_json_syncs'] += 1

        self._log_sync(output_path or f'{table_name}.json', table_name, 'db_to_json',
                       'success' if result['success'] else 'failed',
                       result['records_exported'],
                       result.get('error'))

        return result

    def check_and_sync(self) -> List[Dict[str, Any]]:
        """检查所有注册文件，执行增量同步"""
        results = []
        for filepath, info in list(self.sync_registry.items()):
            if not os.path.exists(filepath):
                continue

            current_sha = self._compute_sha256(filepath)
            current_mtime = str(os.path.getmtime(filepath))

            # 检查是否变更
            if current_sha != info.get('sha256'):
                # 文件已变更，需要同步
                direction = info.get('direction', 'json_to_db')
                if direction in ('json_to_db', 'bidirectional'):
                    result = self.sync_json_to_db(filepath, info['table_name'])
                    results.append(result)
                self.stats['total_syncs'] += 1
            else:
                self.stats['skipped'] += 1

        return results

    def get_status(self) -> Dict[str, Any]:
        """获取同步管理器状态"""
        return {
            'total_registered': len(self.sync_registry),
            'stats': self.stats.copy(),
            'importer_stats': self.importer.stats,
            'exporter_stats': self.exporter.stats,
            'conflict_strategy': self.conflict_strategy.value,
        }

    def get_sync_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取同步日志"""
        if not self.db_path:
            return []
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM mt_json_sync_log ORDER BY synced_at DESC LIMIT ?",
                (limit,)
            )
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"获取日志失败: {e}")
            return []


# ============================================================================
# JSON数据同步数据库系统（主类）
# ============================================================================

class JsonDbSync:
    """
    MTSCOS JSON 数据同步数据库系统

    使用方式：
        sync = JsonDbSync(project_dir='.', db_path='app.db')
        sync.import_json('config.json')           # JSON→DB
        sync.export_json('json_config')           # DB→JSON
        sync.register('config.json', 'config')    # 注册自动同步
        sync.sync_all()                           # 同步所有注册文件
    """

    VERSION = 'v1.0.0'
    SYSTEM_ID = 'json_db_sync_001'
    SYSTEM_NAME = 'MTSCOS JSON数据同步系统'

    def __init__(self, project_dir: str = None, db_path: str = None, dual_db=None):
        self.project_dir = project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path
        self.dual_db = dual_db

        self.sync_manager = SyncManager(self.project_dir, db_path, dual_db)

        logger.info(f"{self.SYSTEM_NAME} 已初始化 (v{self.VERSION})")

    def import_json(self, filepath: str, table_name: str = None,
                    mode: str = 'replace') -> Dict[str, Any]:
        """导入JSON文件到数据库"""
        return self.sync_manager.sync_json_to_db(filepath, table_name, mode)

    def export_json(self, table_name: str, output_path: str = None) -> Dict[str, Any]:
        """导出数据库表到JSON文件"""
        return self.sync_manager.sync_db_to_json(table_name, output_path)

    def register(self, filepath: str, table_name: str = None,
                 direction: str = 'json_to_db') -> Dict[str, Any]:
        """注册文件自动同步"""
        return self.sync_manager.register_sync(filepath, table_name, direction)

    def sync_all(self) -> List[Dict[str, Any]]:
        """同步所有注册文件"""
        return self.sync_manager.check_and_sync()

    def import_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """批量导入目录"""
        return self.sync_manager.importer.import_directory(dir_path)

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'system_id': self.SYSTEM_ID,
            'system_name': self.SYSTEM_NAME,
            'version': self.VERSION,
            'sync_manager': self.sync_manager.get_status(),
        }

    def get_sync_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取同步日志"""
        return self.sync_manager.get_sync_log(limit)


# ============================================================================
# 单例管理
# ============================================================================

_sync_instance: Optional[JsonDbSync] = None
_sync_lock = threading.Lock()


def get_json_db_sync(project_dir: str = None, db_path: str = None,
                     dual_db=None) -> JsonDbSync:
    """获取JSON数据同步系统单例"""
    global _sync_instance
    if _sync_instance is None:
        with _sync_lock:
            if _sync_instance is None:
                _sync_instance = JsonDbSync(
                    project_dir=project_dir,
                    db_path=db_path,
                    dual_db=dual_db,
                )
    return _sync_instance
