# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Backup Manager for MTSCOS AI System
实时双备份管理模块
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Dict, List, Optional
from flask import session


class BackupManager:
    """备份管理器 - 实时双备份"""

    def __init__(self, db_path: str, backup_dir: str = None, auto_backup_interval: int = 300):
        self.db_path = db_path
        self.backup_dir = backup_dir or os.path.join(os.path.dirname(db_path), 'backups')
        self.auto_backup_interval = auto_backup_interval
        self.is_running = False
        self.lock = Lock()

        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'primary'), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'secondary'), exist_ok=True)

        self._init_db()
        self._start_auto_backup()

    def _init_db(self):
        """初始化备份数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_type TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            backup_size INTEGER,
            checksum TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'success'
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()

    def _start_auto_backup(self):
        """启动自动备份线程"""
        self.is_running = True

        def backup_loop():
            while self.is_running:
                import time
                time.sleep(self.auto_backup_interval)
                self.perform_auto_backup()

        self.backup_thread = Thread(target=backup_loop, daemon=True)
        self.backup_thread.start()

    def stop_auto_backup(self):
        """停止自动备份"""
        self.is_running = False

    def perform_auto_backup(self):
        """执行自动备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            primary_path = os.path.join(self.backup_dir, 'primary', f'backup_{timestamp}.db')
            secondary_path = os.path.join(self.backup_dir, 'secondary', f'backup_{timestamp}.db')

            self._backup_file(self.db_path, primary_path)
            self._backup_file(self.db_path, secondary_path)

            self._record_backup('auto', primary_path)
            self._record_backup('auto', secondary_path)

            self._cleanup_old_backups()

            return True, '自动备份成功'
        except Exception as e:
            return False, f'自动备份失败: {str(e)}'

    def _backup_file(self, source: str, destination: str):
        """备份文件"""
        shutil.copy2(source, destination)

        checksum = self._calculate_checksum(destination)

        return destination, checksum

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _record_backup(self, backup_type: str, backup_path: str):
        """记录备份历史"""
        try:
            backup_size = os.path.getsize(backup_path)
            checksum = self._calculate_checksum(backup_path)

            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO backup_history (backup_type, backup_path, backup_size, checksum)
                VALUES (?, ?, ?, ?)
                ''', (backup_type, backup_path, backup_size, checksum))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record backup: {e}")

    def _cleanup_old_backups(self, keep_count: int = 10):
        """清理旧备份"""
        try:
            primary_dir = os.path.join(self.backup_dir, 'primary')

            files = sorted([f for f in os.listdir(primary_dir) if f.endswith('.db')],
                          key=lambda x: os.path.getmtime(os.path.join(primary_dir, x)),
                          reverse=True)

            for f in files[keep_count:]:
                try:
                    os.remove(os.path.join(primary_dir, f))
                    secondary_file = os.path.join(self.backup_dir, 'secondary', f)
                    if os.path.exists(secondary_file):
                        os.remove(secondary_file)
                except Exception as e:
                    logger.error(f"Failed to remove old backup {f}: {e}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def manual_backup(self, backup_name: str = None) -> bool:
        """手动备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = backup_name or f'manual_{timestamp}'

            primary_path = os.path.join(self.backup_dir, 'primary', f'{name}.db')
            secondary_path = os.path.join(self.backup_dir, 'secondary', f'{name}.db')

            self._backup_file(self.db_path, primary_path)
            self._backup_file(self.db_path, secondary_path)

            self._record_backup('manual', primary_path)
            self._record_backup('manual', secondary_path)

            return True
        except Exception as e:
            print(f"Manual backup failed: {e}")
            return False

    def restore_backup(self, backup_path: str) -> bool:
        """恢复备份"""
        try:
            if not os.path.exists(backup_path):
                return False

            checksum = self._calculate_checksum(backup_path)

            temp_path = self.db_path + '.temp'
            shutil.copy2(backup_path, temp_path)

            with sqlite3.connect(temp_path) as conn:
                
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM sqlite_master')

            os.replace(temp_path, self.db_path)

            return True
        except Exception as e:
            print(f"Restore backup failed: {e}")
            return False

    def get_backup_list(self, limit: int = 50) -> List[Dict]:
        """获取备份列表"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, backup_type, backup_path, backup_size, checksum, created_at, status
            FROM backup_history
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
            
            columns = ['id', 'backup_type', 'backup_path', 'backup_size', 'checksum', 'created_at', 'status']
            backups = []
            for row in cursor.fetchall():
                backups.append(dict(zip(columns, row)))
            
        return backups

    def verify_backup(self, backup_path: str) -> bool:
        """验证备份完整性"""
        try:
            if not os.path.exists(backup_path):
                return False

            with sqlite3.connect(backup_path) as conn:
                
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM sqlite_master')

            return True
        except Exception:
            return False

    def get_backup_status(self) -> Dict:
        """获取备份状态"""
        primary_dir = os.path.join(self.backup_dir, 'primary')

        latest_backup = None
        backup_count = 0

        try:
            files = [f for f in os.listdir(primary_dir) if f.endswith('.db')]
            backup_count = len(files)

            if files:
                latest = max(files, key=lambda x: os.path.getmtime(os.path.join(primary_dir, x)))
                latest_path = os.path.join(primary_dir, latest)
                latest_backup = {
                    'filename': latest,
                    'path': latest_path,
                    'size': os.path.getsize(latest_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(latest_path)).isoformat(),
                    'valid': self.verify_backup(latest_path)
                }
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")

        return {
            'backup_dir': self.backup_dir,
            'backup_count': backup_count,
            'latest_backup': latest_backup,
            'auto_backup_enabled': self.is_running,
            'primary_backup_dir': primary_dir,
            'secondary_backup_dir': os.path.join(self.backup_dir, 'secondary')
        }

    def sync_backups(self) -> bool:
        """同步主备备份"""
        try:
            primary_dir = os.path.join(self.backup_dir, 'primary')
            secondary_dir = os.path.join(self.backup_dir, 'secondary')

            primary_files = set(os.listdir(primary_dir))
            secondary_files = set(os.listdir(secondary_dir))

            to_sync = primary_files - secondary_files

            for f in to_sync:
                src = os.path.join(primary_dir, f)
                dst = os.path.join(secondary_dir, f)
                shutil.copy2(src, dst)

            return True
        except Exception as e:
            logger.error(f"Failed to sync backups: {e}")
            return False


backup_manager: Optional[BackupManager] = None


def init_backup_manager(db_path: str, backup_dir: str = None, auto_backup_interval: int = 300):
    """初始化备份管理器"""
    global backup_manager
    backup_manager = BackupManager(db_path, backup_dir, auto_backup_interval)
    return backup_manager


def get_backup_manager() -> BackupManager:
    """获取备份管理器实例"""
    global backup_manager
    if backup_manager is None:
        backup_manager = BackupManager('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
    return backup_manager


def perform_backup() -> tuple:
    """执行备份"""
    return get_backup_manager().perform_auto_backup()


def restore_from_backup(backup_path: str) -> bool:
    """从备份恢复"""
    return get_backup_manager().restore_backup(backup_path)


def get_backup_status() -> Dict:
    """获取备份状态"""
    return get_backup_manager().get_backup_status()
