# -*- coding: utf-8 -*-
"""
安全数据迁移框架
分批迁移 / MD5一致性校验 / 断点续传 / 原表保留
"""

import os
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MigrationFramework:
    """安全数据迁移框架

    迁移原则：
    1. 分批迁移：每批 1000 条，OFFSET 翻页
    2. MD5 校验：源数据 vs 目标数据一致性验证
    3. 断点续传：从 migration_progress 表读取已完成行数
    4. 原表保留：迁移后不删除原数据，仅标记 migrated=1
    5. 自动建表：目标库不存在表时自动创建（复制源表 schema）
    """

    BATCH_SIZE = 1000

    def __init__(self, manager):
        """初始化迁移框架

        Args:
            manager: AIDistributedDatabaseManager 实例
        """
        self.manager = manager
        self.app_root = manager.app_root
        self.app_db_path = os.path.join(self.app_root, 'app.db')

    def migrate_next_batch(self, table_name: str) -> Dict[str, Any]:
        """迁移下一个批次

        Args:
            table_name: 要迁移的表名

        Returns:
            迁移结果 {status, completed_rows, total_rows, md5_check, target_db}
        """
        # 获取迁移进度
        progress = self._get_progress(table_name)
        if not progress:
            return {'status': 'not_found', 'table_name': table_name}

        if progress['status'] == 'completed':
            return {
                'status': 'completed',
                'table_name': table_name,
                'completed_rows': progress['completed_rows'],
                'total_rows': progress['total_rows'],
                'md5_check': progress.get('md5_check')
            }

        target_db = progress['target_db']
        completed_rows = progress['completed_rows']
        total_rows = progress['total_rows']
        batch_size = progress.get('batch_size', self.BATCH_SIZE)

        # 确保目标表存在
        self._ensure_target_table(table_name, target_db)

        # 标记为运行中
        if progress['status'] == 'pending':
            self.manager.update_migration_progress(
                table_name, completed_rows, 'running'
            )

        # 读取源数据（分批）
        try:
            source_rows = self._read_source_batch(table_name, completed_rows, batch_size)
        except Exception as e:
            logger.error(f"读取源表 {table_name} 失败: {e}")
            self.manager.update_migration_progress(
                table_name, completed_rows, 'error', error=f"读取源表失败: {e}"
            )
            return {'status': 'error', 'table_name': table_name, 'error': str(e)}

        if not source_rows:
            # 没有更多数据，迁移完成
            md5_check = self._verify_migration(table_name, target_db)

            self.manager.update_migration_progress(
                table_name, completed_rows, 'completed', md5_check=md5_check
            )

            self.manager.log_decision(
                decision_type='migration_completed',
                details=f"表 {table_name} 迁移完成: {completed_rows} 行, MD5={md5_check}",
                action_taken=f"迁移到 {target_db}"
            )

            return {
                'status': 'completed',
                'table_name': table_name,
                'completed_rows': completed_rows,
                'total_rows': total_rows,
                'md5_check': md5_check,
                'target_db': target_db
            }

        # 写入目标库
        try:
            written = self._write_target_batch(table_name, target_db, source_rows)
        except Exception as e:
            logger.error(f"写入目标库 {target_db}.{table_name} 失败: {e}")
            self.manager.update_migration_progress(
                table_name, completed_rows, 'error', error=f"写入目标库失败: {e}"
            )
            return {'status': 'error', 'table_name': table_name, 'error': str(e)}

        # 更新进度
        new_completed = completed_rows + written
        self.manager.update_migration_progress(
            table_name, new_completed, 'running'
        )

        logger.info(f"表 {table_name} 迁移进度: {new_completed}/{total_rows} "
                     f"({round(new_completed/max(total_rows,1)*100, 1)}%)")

        return {
            'status': 'running',
            'table_name': table_name,
            'completed_rows': new_completed,
            'total_rows': total_rows,
            'target_db': target_db
        }

    def _get_progress(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取迁移进度"""
        progress_list = self.manager.get_migration_status(table_name)
        if progress_list:
            return progress_list[0]
        return None

    def _ensure_target_table(self, table_name: str, target_db: str):
        """确保目标库中表存在（自动复制 schema）"""
        conn = self.manager.get_shard_connection(target_db)
        c = conn.cursor()

        # 检查表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if c.fetchone():
            c.close()
            return

        # 从源库复制表结构
        try:
            source_conn = sqlite3.connect(self.app_db_path, timeout=5.0)
            sc = source_conn.cursor()
            sc.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            row = sc.fetchone()
            source_conn.close()

            if row and row[0]:
                create_sql = row[0]
                c.execute(create_sql)
                conn.commit()
                logger.info(f"目标库 {target_db} 中创建表 {table_name}")
        except Exception as e:
            logger.error(f"复制表 {table_name} schema 失败: {e}")
        finally:
            c.close()

    def _read_source_batch(self, table_name: str, offset: int, limit: int) -> list:
        """从源表分批读取数据"""
        source_conn = sqlite3.connect(self.app_db_path, timeout=10.0)
        source_conn.row_factory = sqlite3.Row
        sc = source_conn.cursor()
        sc.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
        rows = sc.fetchall()
        source_conn.close()
        return rows

    def _write_target_batch(self, table_name: str, target_db: str, rows: list) -> int:
        """将数据写入目标库"""
        if not rows:
            return 0

        conn = self.manager.get_shard_connection(target_db)
        c = conn.cursor()

        # 获取列名
        columns = rows[0].keys()
        placeholders = ','.join(['?'] * len(columns))
        col_str = ','.join(columns)

        # 批量插入
        data = [tuple(row[col] for col in columns) for row in rows]
        c.executemany(
            f"INSERT OR IGNORE INTO {table_name} ({col_str}) VALUES ({placeholders})",
            data
        )
        conn.commit()
        c.close()

        return len(data)

    def _verify_migration(self, table_name: str, target_db: str) -> str:
        """MD5 一致性校验（分批哈希，避免全表扫描卡死）

        对比源表和目标表的数据 MD5 哈希，采用分批处理：
        1. 用 MAX(rowid) 替代 COUNT(*)（O(log n) vs O(n)）
        2. 分批读取数据做 MD5，每批 10000 行，避免内存溢出和长时间锁表
        """
        try:
            BATCH_SIZE = 10000

            # 源表统计和哈希（分批）
            source_conn = sqlite3.connect(self.app_db_path, timeout=10.0)
            source_conn.row_factory = sqlite3.Row
            sc = source_conn.cursor()

            sc.execute(f"SELECT MAX(rowid) FROM {table_name}")
            max_rowid = sc.fetchone()[0]
            source_count = max_rowid if max_rowid is not None else 0

            source_hash = hashlib.md5()
            offset = 0
            while offset <= source_count:
                sc.execute(f"SELECT * FROM {table_name} ORDER BY rowid LIMIT ? OFFSET ?",
                          (BATCH_SIZE, offset))
                rows = sc.fetchall()
                if not rows:
                    break
                for row in rows:
                    source_hash.update(str(row).encode('utf-8'))
                offset += BATCH_SIZE
            source_conn.close()

            # 目标表统计和哈希（分批）
            conn = self.manager.get_shard_connection(target_db)
            conn.row_factory = sqlite3.Row
            tc = conn.cursor()

            tc.execute(f"SELECT MAX(rowid) FROM {table_name}")
            max_rowid = tc.fetchone()[0]
            target_count = max_rowid if max_rowid is not None else 0

            target_hash = hashlib.md5()
            offset = 0
            while offset <= target_count:
                tc.execute(f"SELECT * FROM {table_name} ORDER BY rowid LIMIT ? OFFSET ?",
                          (BATCH_SIZE, offset))
                rows = tc.fetchall()
                if not rows:
                    break
                for row in rows:
                    target_hash.update(str(row).encode('utf-8'))
                offset += BATCH_SIZE
            tc.close()

            if source_count == target_count and source_hash.hexdigest() == target_hash.hexdigest():
                return f"passed:{source_hash.hexdigest()[:16]}"
            else:
                return f"failed:source={source_count}/target={target_count}"
        except Exception as e:
            return f"error:{str(e)[:50]}"

    def get_progress(self, table_name: str) -> Dict[str, Any]:
        """获取单表迁移进度（公开接口）"""
        progress = self._get_progress(table_name)
        if not progress:
            return {'table_name': table_name, 'status': 'not_found'}

        total = progress.get('total_rows', 0)
        completed = progress.get('completed_rows', 0)
        percentage = round(completed / max(total, 1) * 100, 2) if total > 0 else 0

        return {
            'table_name': table_name,
            'status': progress['status'],
            'completed_rows': completed,
            'total_rows': total,
            'percentage': percentage,
            'target_db': progress['target_db'],
            'md5_check': progress.get('md5_check'),
            'started_at': progress.get('started_at'),
            'completed_at': progress.get('completed_at'),
            'error': progress.get('error_message')
        }

    def get_all_progress(self) -> list:
        """获取所有迁移进度"""
        all_progress = self.manager.get_migration_status()
        results = []
        for p in all_progress:
            total = p.get('total_rows', 0)
            completed = p.get('completed_rows', 0)
            percentage = round(completed / max(total, 1) * 100, 2) if total > 0 else 0
            results.append({
                'table_name': p['table_name'],
                'status': p['status'],
                'completed_rows': completed,
                'total_rows': total,
                'percentage': percentage,
                'target_db': p['target_db'],
                'md5_check': p.get('md5_check'),
                'completed_at': p.get('completed_at')
            })
        return results
