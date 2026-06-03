# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户快照模型
用于处理用户状态快照的记录和查询
"""

import time
import gzip
import base64
import zlib
import lzma
from app.utils.db import db_manager
from app.utils.logging import logger
import logging
import json


class UserSnapshot:
    """用户状态快照数据模型"""

    def __init__(self, snapshot_id=None, user_id=None, session_id=None, timestamp=None,
                 snapshot_type=None, version='1.0', size=0, compressed=0,
                 compression_algorithm=None, checksum=None, status='active',
                 metadata=None, data=None):
        self.snapshot_id = snapshot_id
        self.user_id = user_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.snapshot_type = snapshot_type
        self.version = version
        self.size = size
        self.compressed = compressed
        self.compression_algorithm = compression_algorithm
        self.checksum = checksum
        self.status = status
        self.metadata = metadata or {}
        self.data = data or {}

    @staticmethod
    def create_table():
        """创建用户快照表"""
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS user_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                snapshot_type TEXT NOT NULL,
                version TEXT DEFAULT '1.0',
                size INTEGER DEFAULT 0,
                compressed INTEGER DEFAULT 0,
                compression_algorithm TEXT DEFAULT NULL,
                checksum TEXT DEFAULT NULL,
                status TEXT DEFAULT 'active',
                metadata TEXT NOT NULL DEFAULT '{}',
                data TEXT NOT NULL DEFAULT '{}'
            )
        '''
        db_manager.execute(create_table_sql)

        try:
            db_manager.execute('SELECT compression_algorithm FROM user_snapshots LIMIT 1')
        except Exception:
            db_manager.execute('ALTER TABLE user_snapshots ADD COLUMN compression_algorithm TEXT DEFAULT NULL')

        try:
            db_manager.execute('SELECT checksum FROM user_snapshots LIMIT 1')
        except Exception:
            db_manager.execute('ALTER TABLE user_snapshots ADD COLUMN checksum TEXT DEFAULT NULL')

        index_queries = [
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_user_id ON user_snapshots(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_session_id ON user_snapshots(session_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_timestamp ON user_snapshots(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_type ON user_snapshots(snapshot_type)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_status ON user_snapshots(status)'
        ]

        for query in index_queries:
            db_manager.execute(query)

        logger.info("用户快照表创建成功")

    @staticmethod
    def _compress_data(data_str: str, algorithm: str = 'gzip') -> str:
        """使用指定算法压缩数据"""
        data_bytes = data_str.encode('utf-8')

        if algorithm == 'gzip':
            compressed = gzip.compress(data_bytes, compresslevel=9)
        elif algorithm == 'zlib':
            compressed = zlib.compress(data_bytes, level=9)
        elif algorithm == 'lzma':
            compressed = lzma.compress(data_bytes, preset=9)
        else:
            raise ValueError(f"不支持的压缩算法: {algorithm}")

        return base64.b64encode(compressed).decode('utf-8')

    @staticmethod
    def _select_best_compression_algorithm(data_str: str) -> str:
        """选择最佳压缩算法"""
        algorithms = ['gzip', 'zlib', 'lzma']
        best_algorithm = None
        best_ratio = 0

        original_size = len(data_str.encode('utf-8'))

        for algorithm in algorithms:
            try:
                compressed = UserSnapshot._compress_data(data_str, algorithm)
                compressed_size = len(compressed.encode('utf-8'))
                ratio = (original_size - compressed_size) / original_size

                if ratio > best_ratio and ratio > 0.1:
                    best_ratio = ratio
                    best_algorithm = algorithm
            except Exception:
                continue

        return best_algorithm

    def save(self, should_compress=True):
        """保存用户快照"""
        data = self.data or {}
        metadata = self.metadata or {}
        data_json = str(data)
        metadata_json = str(metadata)

        original_size = len(data_json.encode('utf-8'))

        final_compressed = self.compressed
        final_data = data_json
        final_size = original_size
        final_compression_algorithm = self.compression_algorithm

        if should_compress and original_size > 512:
            best_algorithm = UserSnapshot._select_best_compression_algorithm(data_json)
            if best_algorithm:
                compressed_data = UserSnapshot._compress_data(data_json, best_algorithm)
                compressed_size = len(compressed_data.encode('utf-8'))

                if compressed_size < original_size:
                    final_data = compressed_data
                    final_size = compressed_size
                    final_compressed = 1
                    final_compression_algorithm = best_algorithm
                else:
                    final_compressed = 0
                    final_compression_algorithm = None
            else:
                final_compressed = 0
                final_compression_algorithm = None

        self.compressed = final_compressed
        self.compression_algorithm = final_compression_algorithm

        if self.snapshot_id:
            update_sql = '''
                UPDATE user_snapshots SET user_id=?, session_id=?, timestamp=?, snapshot_type=?, version=?,
                size=?, compressed=?, compression_algorithm=?, checksum=?, status=?, metadata=?, data=?
                WHERE snapshot_id=?
            '''
            params = (self.user_id, self.session_id, self.timestamp, self.snapshot_type,
                      self.version, final_size, final_compressed, final_compression_algorithm,
                      self.checksum, self.status, metadata_json, final_data, self.snapshot_id)
            db_manager.execute(update_sql, params)
        else:
            self.snapshot_id = f"snapshot_{int(time.time() * 1000)}_{self.user_id}_{self.session_id[:8] if self.session_id else 'unknown'}"
            insert_sql = '''
                INSERT INTO user_snapshots (snapshot_id, user_id, session_id, timestamp, snapshot_type, version,
                size, compressed, compression_algorithm, checksum, status, metadata, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.snapshot_id, self.user_id, self.session_id, self.timestamp,
                      self.snapshot_type, self.version, final_size, final_compressed,
                      final_compression_algorithm, self.checksum, self.status, metadata_json, final_data)
            db_manager.execute(insert_sql, params)

        logger.debug(f"保存用户快照成功: {self.snapshot_id}, 原始大小: {original_size}字节, 存储大小: {final_size}字节, 压缩: {'是' if final_compressed else '否'}, 算法: {final_compression_algorithm}")

    def restore(self):
        """恢复用户快照"""
        if not self.snapshot_id:
            return False

        row = db_manager.fetch_one(
            'SELECT * FROM user_snapshots WHERE snapshot_id=?',
            (self.snapshot_id,)
        )

        if row:
            self.user_id = row[1]
            self.session_id = row[2]
            self.timestamp = row[3]
            self.snapshot_type = row[4]
            self.version = row[5]
            self.size = row[6]
            self.compressed = row[7]
            self.compression_algorithm = row[8]
            self.checksum = row[9]
            self.status = row[10]
            self.metadata = eval(row[11]) if row[11] else {}
            self.data = eval(row[12]) if row[12] else {}
            return True
        return False

    def archive(self):
        """归档用户快照"""
        if not self.snapshot_id:
            return False

        self.status = 'archived'
        db_manager.execute(
            'UPDATE user_snapshots SET status=? WHERE snapshot_id=?',
            ('archived', self.snapshot_id)
        )
        return True

    def delete(self):
        """删除用户快照"""
        if not self.snapshot_id:
            return False

        db_manager.execute(
            'DELETE FROM user_snapshots WHERE snapshot_id=?',
            (self.snapshot_id,)
        )
        return True
