#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据层服务 - 实现数据与应用分离
提供独立的数据访问接口和数据管理功能
"""

import json
import os
import shutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from app.utils.logging import logger
from app.utils.db import db_manager
from app.utils.lock_sync_manager import lock_sync_manager, LockType, synchronized


class DataLayerService:
    """数据层服务类"""

    def __init__(self):
        self._data_dir = os.environ.get('DATA_DIR', '/app/data')
        self._backup_dir = os.environ.get('BACKUP_DIR', '/app/backups')
        self._ensure_directories()
        logger.info("数据层服务初始化完成")

    def _ensure_directories(self):
        """确保数据目录存在"""
        os.makedirs(self._data_dir, exist_ok=True)
        os.makedirs(self._backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self._data_dir, 'uploads'), exist_ok=True)
        os.makedirs(os.path.join(self._data_dir, 'exports'), exist_ok=True)
        os.makedirs(os.path.join(self._data_dir, 'temp'), exist_ok=True)

    @synchronized(resource='data_backup', lock_type=LockType.WRITE)
    def create_backup(self, backup_name: Optional[str] = None) -> Optional[str]:
        """创建数据库备份"""
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f"backup_{timestamp}"
            backup_path = os.path.join(self._backup_dir, f"{backup_name}.db")

            # SQLite备份
            if db_manager.db_type == 'sqlite':
                db_path = getattr(db_manager, 'db_path', 'app.db')
                if os.path.exists(db_path):
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"数据库备份成功: {backup_path}")
                    return backup_path

            logger.error("不支持的数据库类型")
            return None
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return None

    @synchronized(resource='data_restore', lock_type=LockType.WRITE)
    def restore_backup(self, backup_path: str) -> bool:
        """从备份恢复数据库"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"备份文件不存在: {backup_path}")
                return False

            if db_manager.db_type == 'sqlite':
                db_path = getattr(db_manager, 'db_path', 'app.db')
                shutil.copy2(backup_path, db_path)
                logger.info(f"数据库恢复成功: {backup_path}")
                return True

            logger.error("不支持的数据库类型")
            return False
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            return False

    def list_backups(self) -> List[Dict]:
        """列出所有备份文件"""
        backups = []
        try:
            for filename in os.listdir(self._backup_dir):
                if filename.endswith('.db'):
                    filepath = os.path.join(self._backup_dir, filename)
                    stats = os.stat(filepath)
                    backups.append({
                        'name': filename,
                        'path': filepath,
                        'size': stats.st_size,
                        'created_at': datetime.fromtimestamp(stats.st_ctime).isoformat()
                    })
            backups.sort(key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            logger.error(f"列出备份失败: {str(e)}")
        return backups

    @synchronized(resource='data_export', lock_type=LockType.WRITE)
    def export_table(self, table_name: str, format_type: str = 'json') -> Optional[str]:
        """导出数据表"""
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            export_path = os.path.join(self._data_dir, 'exports', f"{table_name}_{timestamp}.{format_type}")

            # 查询表数据
            query = f"SELECT * FROM {table_name}"
            rows = db_manager.fetch_all(query)

            if format_type == 'json':
                data = []
                for row in rows:
                    if isinstance(row, dict):
                        data.append(row)
                    else:
                        # 获取列名
                        cursor, _ = db_manager.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()] if cursor else []
                        data.append(dict(zip(columns, row)))

                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format_type == 'csv':
                import csv
                with open(export_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    if rows:
                        # 获取列名
                        cursor, _ = db_manager.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()] if cursor else []
                        writer.writerow(columns)
                        for row in rows:
                            if isinstance(row, dict):
                                writer.writerow([row.get(col, '') for col in columns])
                            else:
                                writer.writerow(row)

            logger.info(f"表 {table_name} 导出成功: {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"导出表失败: {str(e)}")
            return None

    @synchronized(resource='data_import', lock_type=LockType.WRITE)
    def import_table(self, table_name: str, file_path: str) -> bool:
        """导入数据表"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"导入文件不存在: {file_path}")
                return False

            _, ext = os.path.splitext(file_path)

            if ext.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data:
                    columns = list(data[0].keys())
                    placeholders = ','.join(['?' for _ in columns])
                    columns_str = ','.join(columns)

                    # 清空表
                    db_manager.execute(f"DELETE FROM {table_name}")

                    # 批量插入
                    for row in data:
                        values = [row.get(col) for col in columns]
                        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        db_manager.execute(query, tuple(values))

            elif ext.lower() == '.csv':
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    columns = reader.fieldnames or []
                    placeholders = ','.join(['?' for _ in columns])
                    columns_str = ','.join(columns)

                    db_manager.execute(f"DELETE FROM {table_name}")

                    for row in reader:
                        values = [row.get(col) for col in columns]
                        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        db_manager.execute(query, tuple(values))

            logger.info(f"表 {table_name} 导入成功")
            return True
        except Exception as e:
            logger.error(f"导入表失败: {str(e)}")
            return False

    def get_table_info(self) -> List[Dict]:
        """获取所有表信息"""
        tables = []
        try:
            if db_manager.db_type == 'sqlite':
                cursor, _ = db_manager.execute("SELECT name FROM sqlite_master WHERE type='table'")
                if cursor:
                    for row in cursor.fetchall():
                        table_name = row[0]
                        # 获取列信息
                        cursor2, _ = db_manager.execute(f"PRAGMA table_info({table_name})")
                        columns = []
                        if cursor2:
                            for col in cursor2.fetchall():
                                columns.append({
                                    'name': col[1],
                                    'type': col[2],
                                    'not_null': bool(col[3]),
                                    'primary_key': bool(col[5])
                                })
                        # 获取行数
                        count = db_manager.fetch_scalar(f"SELECT COUNT(*) FROM {table_name}") or 0
                        tables.append({
                            'name': table_name,
                            'columns': columns,
                            'row_count': count
                        })
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}")
        return tables

    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        stats = {
            'tables': [],
            'total_rows': 0,
            'database_type': db_manager.db_type,
            'backup_count': len(self.list_backups())
        }

        try:
            tables = self.get_table_info()
            stats['tables'] = tables
            stats['total_rows'] = sum(t['row_count'] for t in tables)
        except Exception as e:
            logger.error(f"获取数据库统计失败: {str(e)}")

        return stats

    @synchronized(resource='data_cleanup', lock_type=LockType.WRITE)
    def cleanup_temp_files(self, days_to_keep: int = 7) -> int:
        """清理临时文件"""
        deleted_count = 0
        try:
            temp_dir = os.path.join(self._data_dir, 'temp')
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                if os.path.isfile(filepath):
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff:
                        os.remove(filepath)
                        deleted_count += 1

            logger.info(f"清理了 {deleted_count} 个临时文件")
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")

        return deleted_count

    @synchronized(resource='data_migrate', lock_type=LockType.WRITE)
    def migrate_data(self, source_db_uri: str, target_tables: Optional[List[str]] = None) -> Dict:
        """迁移数据"""
        result = {
            'success': True,
            'migrated_tables': [],
            'failed_tables': [],
            'row_counts': {}
        }

        try:
            # 获取所有表
            all_tables = [t['name'] for t in self.get_table_info()]
            tables_to_migrate = target_tables or all_tables

            for table in tables_to_migrate:
                if table not in all_tables:
                    result['failed_tables'].append(table)
                    continue

                try:
                    # 导出数据
                    export_path = self.export_table(table, 'json')
                    if export_path:
                        # 如果需要迁移到其他数据库,可以在这里实现
                        result['migrated_tables'].append(table)
                        result['row_counts'][table] = self._count_rows(table)
                    else:
                        result['failed_tables'].append(table)
                except Exception as e:
                    logger.error(f"迁移表 {table} 失败: {str(e)}")
                    result['failed_tables'].append(table)

        except Exception as e:
            logger.error(f"数据迁移失败: {str(e)}")
            result['success'] = False

        return result

    def _count_rows(self, table_name: str) -> int:
        """获取表行数"""
        try:
            return db_manager.fetch_scalar(f"SELECT COUNT(*) FROM {table_name}") or 0
        except Exception:
            return 0


# 创建全局实例
data_layer_service = DataLayerService()
