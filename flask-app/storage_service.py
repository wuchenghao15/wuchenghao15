#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS对象存储服务
提供统一的文件存储抽象（本地/S3兼容）
"""

import os
import sys
import json
import time
import shutil
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, BinaryIO

logger = print


class StorageObject:
    """存储对象"""

    def __init__(self, object_id: str, bucket: str, key: str,
                 size: int = 0, content_type: str = '',
                 etag: str = '', metadata: Dict[str, str] = None,
                 storage_class: str = 'standard',
                 created_at: str = None, last_modified: str = None):
        self.object_id = object_id
        self.bucket = bucket
        self.key = key
        self.size = size
        self.content_type = content_type
        self.etag = etag
        self.metadata = metadata or {}
        self.storage_class = storage_class
        self.created_at = created_at or datetime.now().isoformat()
        self.last_modified = last_modified or self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            'object_id': self.object_id,
            'bucket': self.bucket,
            'key': self.key,
            'size': self.size,
            'content_type': self.content_type,
            'etag': self.etag,
            'metadata': self.metadata,
            'storage_class': self.storage_class,
            'created_at': self.created_at,
            'last_modified': self.last_modified
        }


class StorageBucket:
    """存储桶"""

    def __init__(self, bucket_name: str, description: str = '',
                 max_size: int = 0, created_at: str = None):
        self.bucket_name = bucket_name
        self.description = description
        self.max_size = max_size
        self.used_size = 0
        self.object_count = 0
        self.created_at = created_at or datetime.now().isoformat()
        self.is_public = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'bucket_name': self.bucket_name,
            'description': self.description,
            'max_size': self.max_size,
            'used_size': self.used_size,
            'object_count': self.object_count,
            'created_at': self.created_at,
            'is_public': self.is_public
        }


class StorageService:
    """对象存储服务"""

    def __init__(self, storage_root: str = None):
        self.storage_root = storage_root or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'storage'
        )
        self.buckets: Dict[str, StorageBucket] = {}
        self.is_running = False
        self.lock = threading.Lock()

        os.makedirs(self.storage_root, exist_ok=True)

        self._init_database()
        self._register_default_buckets()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS storage_buckets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bucket_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    max_size INTEGER DEFAULT 0,
                    used_size INTEGER DEFAULT 0,
                    object_count INTEGER DEFAULT 0,
                    is_public INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS storage_objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id TEXT NOT NULL UNIQUE,
                    bucket TEXT NOT NULL,
                    key TEXT NOT NULL,
                    file_path TEXT,
                    size INTEGER DEFAULT 0,
                    content_type TEXT,
                    etag TEXT,
                    metadata TEXT,
                    storage_class TEXT DEFAULT 'standard',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_modified TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS storage_access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id TEXT,
                    bucket TEXT,
                    key TEXT,
                    action TEXT,
                    accessor TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_storage_objects_bucket ON storage_objects(bucket)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_storage_objects_key ON storage_objects(bucket, key)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[存储] 初始化数据库失败: {e}")

    def _register_default_buckets(self):
        """注册默认存储桶"""
        defaults = [
            ('uploads', '用户上传文件', 1024 * 1024 * 1024),
            ('backups', '系统备份文件', 5 * 1024 * 1024 * 1024),
            ('reports', '报表文件', 1024 * 1024 * 1024),
            ('temp', '临时文件', 500 * 1024 * 1024),
            ('avatars', '用户头像', 100 * 1024 * 1024),
            ('documents', '文档文件', 2 * 1024 * 1024 * 1024),
        ]

        for name, desc, max_size in defaults:
            self.create_bucket(name, desc, max_size)

    def create_bucket(self, bucket_name: str, description: str = '',
                      max_size: int = 0) -> bool:
        """创建存储桶"""
        with self.lock:
            if bucket_name in self.buckets:
                return False

            bucket = StorageBucket(bucket_name, description, max_size)
            self.buckets[bucket_name] = bucket

        bucket_path = os.path.join(self.storage_root, bucket_name)
        os.makedirs(bucket_path, exist_ok=True)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO storage_buckets
                (bucket_name, description, max_size)
                VALUES (?, ?, ?)
            ''', (bucket_name, description, max_size))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[存储] 保存桶信息失败: {e}")

        logger(f"[存储] 创建存储桶: {bucket_name}")
        return True

    def _generate_object_id(self) -> str:
        import uuid
        return f"obj_{uuid.uuid4().hex[:16]}"

    def _get_file_path(self, bucket: str, key: str) -> str:
        """获取文件路径"""
        key_path = key.replace('/', os.sep)
        return os.path.join(self.storage_root, bucket, key_path)

    def put_object(self, bucket: str, key: str, data: bytes,
                   content_type: str = '', metadata: Dict[str, str] = None,
                   storage_class: str = 'standard') -> Optional[str]:
        """上传对象"""
        with self.lock:
            if bucket not in self.buckets:
                logger(f"[存储] 存储桶不存在: {bucket}")
                return None

            bkt = self.buckets[bucket]

            if bkt.max_size > 0 and bkt.used_size + len(data) > bkt.max_size:
                logger(f"[存储] 存储桶空间不足: {bucket}")
                return None

        object_id = self._generate_object_id()
        file_path = self._get_file_path(bucket, key)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            logger(f"[存储] 写入文件失败: {e}")
            return None

        etag = hashlib.md5(data).hexdigest()

        obj = StorageObject(
            object_id=object_id,
            bucket=bucket,
            key=key,
            size=len(data),
            content_type=content_type or 'application/octet-stream',
            etag=etag,
            metadata=metadata or {},
            storage_class=storage_class
        )

        self._save_object_to_db(obj)

        with self.lock:
            bkt.used_size += len(data)
            bkt.object_count += 1

        self._update_bucket_stats(bkt)
        self._log_access(object_id, bucket, key, 'put')

        logger(f"[存储] 上传对象: {bucket}/{key} ({len(data)} bytes)")
        return object_id

    def _save_object_to_db(self, obj: StorageObject):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO storage_objects
                (object_id, bucket, key, file_path, size, content_type,
                 etag, metadata, storage_class, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                obj.object_id, obj.bucket, obj.key,
                self._get_file_path(obj.bucket, obj.key),
                obj.size, obj.content_type, obj.etag,
                json.dumps(obj.metadata), obj.storage_class,
                obj.last_modified
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[存储] 保存对象失败: {e}")

    def get_object(self, bucket: str, key: str) -> Optional[bytes]:
        """下载对象"""
        file_path = self._get_file_path(bucket, key)

        if not os.path.exists(file_path):
            logger(f"[存储] 对象不存在: {bucket}/{key}")
            return None

        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            self._log_access(None, bucket, key, 'get')
            return data
        except Exception as e:
            logger(f"[存储] 读取文件失败: {e}")
            return None

    def delete_object(self, bucket: str, key: str) -> bool:
        """删除对象"""
        file_path = self._get_file_path(bucket, key)

        size = 0
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            os.remove(file_path)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM storage_objects WHERE bucket = ? AND key = ?
            ''', (bucket, key))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[存储] 删除对象记录失败: {e}")

        with self.lock:
            bkt = self.buckets.get(bucket)
            if bkt:
                bkt.used_size = max(0, bkt.used_size - size)
                bkt.object_count = max(0, bkt.object_count - 1)

        if bucket in self.buckets:
            self._update_bucket_stats(self.buckets[bucket])

        self._log_access(None, bucket, key, 'delete')
        logger(f"[存储] 删除对象: {bucket}/{key}")
        return True

    def list_objects(self, bucket: str, prefix: str = '',
                     limit: int = 100) -> List[Dict[str, Any]]:
        """列出对象"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            if prefix:
                cursor.execute('''
                    SELECT * FROM storage_objects
                    WHERE bucket = ? AND key LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (bucket, f"{prefix}%", limit))
            else:
                cursor.execute('''
                    SELECT * FROM storage_objects
                    WHERE bucket = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (bucket, limit))

            columns = [desc[0] for desc in cursor.description]
            objects = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return objects
        except Exception as e:
            logger(f"[存储] 列出对象失败: {e}")
            return []

    def copy_object(self, src_bucket: str, src_key: str,
                    dst_bucket: str, dst_key: str) -> Optional[str]:
        """复制对象"""
        data = self.get_object(src_bucket, src_key)
        if data is None:
            return None

        return self.put_object(dst_bucket, dst_key, data)

    def get_object_info(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """获取对象信息"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM storage_objects WHERE bucket = ? AND key = ?
            ''', (bucket, key))

            row = cursor.fetchone()
            if not row:
                conn.close()
                return None

            columns = [desc[0] for desc in cursor.description]
            conn.close()

            return dict(zip(columns, row))
        except Exception as e:
            logger(f"[存储] 获取对象信息失败: {e}")
            return None

    def _update_bucket_stats(self, bucket: StorageBucket):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE storage_buckets
                SET used_size = ?, object_count = ?
                WHERE bucket_name = ?
            ''', (bucket.used_size, bucket.object_count, bucket.bucket_name))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[存储] 更新桶统计失败: {e}")

    def _log_access(self, object_id: str, bucket: str, key: str,
                    action: str, accessor: str = ''):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO storage_access_logs
                (object_id, bucket, key, action, accessor)
                VALUES (?, ?, ?, ?, ?)
            ''', (object_id, bucket, key, action, accessor))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[存储] 记录访问失败: {e}")

    def get_buckets(self) -> List[StorageBucket]:
        return list(self.buckets.values())

    def get_bucket_info(self, bucket_name: str) -> Optional[StorageBucket]:
        return self.buckets.get(bucket_name)

    def get_access_logs(self, bucket: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM storage_access_logs WHERE 1=1'
            params = []

            if bucket:
                query += ' AND bucket = ?'
                params.append(bucket)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except Exception as e:
            logger(f"[存储] 获取访问日志失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        total_size = sum(b.used_size for b in self.buckets.values())
        total_objects = sum(b.object_count for b in self.buckets.values())

        return {
            'status': 'running' if self.is_running else 'stopped',
            'storage_root': self.storage_root,
            'total_buckets': len(self.buckets),
            'total_objects': total_objects,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[存储] 对象存储服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[存储] 对象存储服务已停止")


storage_service = StorageService()
