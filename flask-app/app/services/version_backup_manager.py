# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""版本历史备份系统
提供版本快照、备份、恢复和对比功能
"""

import os
import json
import shutil
import time
import sqlite3
import hashlib
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading


class VersionBackupManager:
    """版本历史备份管理器"""
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.project_history')
        
        self.base_dir = base_dir
        self.versions_dir = os.path.join(base_dir, 'versions')
        self.backups_dir = os.path.join(base_dir, 'backups')
        self.db_path = os.path.join(base_dir, 'version_history.db')
        
        self.lock = threading.Lock()
        
        self._init_directories()
        self._init_database()
    
    def _init_directories(self):
        """初始化目录结构"""
        for d in [self.base_dir, self.versions_dir, self.backups_dir]:
            os.makedirs(d, exist_ok=True)
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                snapshot_name TEXT NOT NULL,
                snapshot_path TEXT NOT NULL,
                description TEXT,
                file_count INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                checksum TEXT,
                created_at REAL,
                created_by TEXT DEFAULT 'system',
                is_archived INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_name TEXT NOT NULL,
                backup_type TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                from_version TEXT,
                to_version TEXT,
                description TEXT,
                file_count INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                checksum TEXT,
                created_at REAL,
                status TEXT DEFAULT 'completed'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restore_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER,
                restore_path TEXT NOT NULL,
                restored_at REAL,
                restored_by TEXT DEFAULT 'system',
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (backup_id) REFERENCES backup_records(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_version ON version_snapshots(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_backups_type ON backup_records(backup_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_backups_version ON backup_records(from_version)')
        
        conn.commit()
        conn.close()
    
    def create_snapshot(self, version: str, source_dir: str, 
                       description: str = None, snapshot_name: str = None) -> str:
        """创建版本快照"""
        with self.lock:
            if snapshot_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                snapshot_name = f"v{version}_{timestamp}"
            
            snapshot_path = os.path.join(self.versions_dir, snapshot_name)
            
            if os.path.exists(snapshot_path):
                raise ValueError(f"快照已存在: {snapshot_name}")
            
            os.makedirs(snapshot_path, exist_ok=True)
            
            file_count = 0
            total_size = 0
            
            if os.path.exists(source_dir):
                for root, dirs, files in os.walk(source_dir):
                    for f in files:
                        src_path = os.path.join(root, f)
                        rel_path = os.path.relpath(src_path, source_dir)
                        dst_path = os.path.join(snapshot_path, rel_path)
                        
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        try:
                            shutil.copy2(src_path, dst_path)
                            file_count += 1
                            total_size += os.path.getsize(src_path)
                        except Exception:
                            pass
            
            version_info_path = os.path.join(snapshot_path, 'VERSION')
            with open(version_info_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': version,
                    'snapshot_name': snapshot_name,
                    'created_at': time.time(),
                    'description': description or '',
                    'file_count': file_count,
                    'total_size': total_size
                }, f, ensure_ascii=False, indent=2)
            
            checksum = self._calculate_checksum(snapshot_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO version_snapshots 
                (version, snapshot_name, snapshot_path, description, file_count, total_size, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (version, snapshot_name, snapshot_path, description, file_count, total_size, checksum, time.time()))
            conn.commit()
            conn.close()
            
            return snapshot_name
    
    def _calculate_checksum(self, path: str) -> str:
        """计算目录的校验和"""
        md5 = hashlib.md5()
        
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in sorted(files):
                    file_path = os.path.join(root, f)
                    try:
                        with open(file_path, 'rb') as fp:
                            while True:
                                chunk = fp.read(8192)
                                if not chunk:
                                    break
                                md5.update(chunk)
                    except Exception:
                        pass
        elif os.path.isfile(path):
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    md5.update(chunk)
        
        return md5.hexdigest()
    
    def list_snapshots(self, version: str = None, limit: int = 20) -> List[Dict]:
        """列出版本快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT version, snapshot_name, description, file_count, total_size, created_at, is_archived FROM version_snapshots'
        params = []
        
        if version:
            query += ' WHERE version = ?'
            params.append(version)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'version': row[0],
            'snapshot_name': row[1],
            'description': row[2],
            'file_count': row[3],
            'total_size': row[4],
            'created_at': row[5],
            'is_archived': bool(row[6])
        } for row in rows]
    
    def get_snapshot(self, snapshot_name: str) -> Optional[Dict]:
        """获取快照信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT version, snapshot_name, snapshot_path, description, 
                   file_count, total_size, checksum, created_at, is_archived
            FROM version_snapshots WHERE snapshot_name = ?
        ''', (snapshot_name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'version': row[0],
                'snapshot_name': row[1],
                'snapshot_path': row[2],
                'description': row[3],
                'file_count': row[4],
                'total_size': row[5],
                'checksum': row[6],
                'created_at': row[7],
                'is_archived': bool(row[8])
            }
        return None
    
    def create_backup(self, backup_name: str = None, backup_type: str = 'full',
                     source_dir: str = None, description: str = None,
                     from_version: str = None, to_version: str = None) -> str:
        """创建备份"""
        with self.lock:
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{backup_type}_{timestamp}"
            
            backup_path = os.path.join(self.backups_dir, f"{backup_name}.zip")
            
            if os.path.exists(backup_path):
                raise ValueError(f"备份已存在: {backup_name}")
            
            file_count = 0
            total_size = 0
            
            if source_dir and os.path.exists(source_dir):
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(source_dir):
                        for f in files:
                            file_path = os.path.join(root, f)
                            arcname = os.path.relpath(file_path, source_dir)
                            zipf.write(file_path, arcname)
                            file_count += 1
                            total_size += os.path.getsize(file_path)
            
            checksum = self._calculate_checksum(backup_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backup_records 
                (backup_name, backup_type, backup_path, from_version, to_version, 
                 description, file_count, total_size, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (backup_name, backup_type, backup_path, from_version, to_version,
                  description, file_count, total_size, checksum, time.time()))
            conn.commit()
            conn.close()
            
            return backup_name
    
    def list_backups(self, backup_type: str = None, limit: int = 20) -> List[Dict]:
        """列出备份"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT backup_name, backup_type, from_version, to_version, description, file_count, total_size, created_at, status FROM backup_records'
        params = []
        
        if backup_type:
            query += ' WHERE backup_type = ?'
            params.append(backup_type)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'backup_name': row[0],
            'backup_type': row[1],
            'from_version': row[2],
            'to_version': row[3],
            'description': row[4],
            'file_count': row[5],
            'total_size': row[6],
            'created_at': row[7],
            'status': row[8]
        } for row in rows]
    
    def restore_backup(self, backup_name: str, restore_path: str) -> bool:
        """恢复备份"""
        backup_path = os.path.join(self.backups_dir, f"{backup_name}.zip")
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"备份不存在: {backup_name}")
        
        os.makedirs(restore_path, exist_ok=True)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(restore_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM backup_records WHERE backup_name = ?', (backup_name,))
        backup_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO restore_records (backup_id, restore_path, restored_at)
            VALUES (?, ?, ?)
        ''', (backup_id, restore_path, time.time()))
        conn.commit()
        conn.close()
        
        return True
    
    def delete_snapshot(self, snapshot_name: str) -> bool:
        """删除快照"""
        with self.lock:
            snapshot = self.get_snapshot(snapshot_name)
            if not snapshot:
                return False
            
            snapshot_path = snapshot['snapshot_path']
            if os.path.exists(snapshot_path):
                shutil.rmtree(snapshot_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM version_snapshots WHERE snapshot_name = ?', (snapshot_name,))
            conn.commit()
            conn.close()
            
            return True
    
    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        with self.lock:
            backup_path = os.path.join(self.backups_dir, f"{backup_name}.zip")
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM backup_records WHERE backup_name = ?', (backup_name,))
            conn.commit()
            conn.close()
            
            return True
    
    def get_backup_stats(self) -> Dict:
        """获取备份统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM version_snapshots')
        total_snapshots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM backup_records')
        total_backups = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT version) FROM version_snapshots')
        version_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_size) FROM version_snapshots')
        total_snapshot_size = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(total_size) FROM backup_records')
        total_backup_size = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT backup_type, COUNT(*) 
            FROM backup_records 
            GROUP BY backup_type
        ''')
        backup_types = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_snapshots': total_snapshots,
            'total_backups': total_backups,
            'version_count': version_count,
            'total_snapshot_size': total_snapshot_size,
            'total_backup_size': total_backup_size,
            'total_size': total_snapshot_size + total_backup_size,
            'backup_types': backup_types
        }
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_min_snapshots: int = 5) -> int:
        """清理旧备份"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = time.time() - (keep_days * 86400)
            
            cursor.execute('''
                SELECT snapshot_name FROM version_snapshots 
                WHERE created_at < ? AND is_archived = 0
                ORDER BY created_at DESC
            ''', (cutoff,))
            
            old_snapshots = cursor.fetchall()
            
            deleted_count = 0
            
            if len(old_snapshots) > keep_min_snapshots:
                to_delete = old_snapshots[keep_min_snapshots:]
                for (snapshot_name,) in to_delete:
                    self.delete_snapshot(snapshot_name)
                    deleted_count += 1
            
            cursor.execute('''
                SELECT backup_name FROM backup_records 
                WHERE created_at < ? AND status = 'completed'
                ORDER BY created_at DESC
            ''', (cutoff,))
            
            old_backups = cursor.fetchall()
            
            if len(old_backups) > keep_min_snapshots:
                to_delete = old_backups[keep_min_snapshots:]
                for (backup_name,) in to_delete:
                    self.delete_backup(backup_name)
                    deleted_count += 1
            
            conn.close()
            
            return deleted_count
    
    def archive_snapshot(self, snapshot_name: str) -> bool:
        """归档快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE version_snapshots SET is_archived = 1 WHERE snapshot_name = ?', (snapshot_name,))
        conn.commit()
        conn.close()
        return True
    
    def unarchive_snapshot(self, snapshot_name: str) -> bool:
        """取消归档快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE version_snapshots SET is_archived = 0 WHERE snapshot_name = ?', (snapshot_name,))
        conn.commit()
        conn.close()
        return True


version_backup_manager = VersionBackupManager()
