#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份服务
实现双备份加第三备份（使用不同引擎），自动数据库加密
"""

import os
import sqlite3
import json
import time
import zipfile
import shutil
from datetime import datetime
from typing import Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import tempfile
from app.utils.logging import logger


class BackupService:
    """数据库备份服务"""
    
    BACKUP_DIRS = {
        'primary': 'backups/primary',
        'secondary': 'backups/secondary',
        'tertiary': 'backups/tertiary'
    }
    
    IMAGE_DIR = 'backups/images'
    ENCRYPTION_KEY_FILE = 'backups/encryption_key.key'
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        self.db_path = db_path
        
        self._init_backup_dirs()
        self._init_encryption_key()
        self._init_backup_tables()
    
    def _init_backup_dirs(self):
        """初始化备份目录"""
        for backup_type, dir_path in self.BACKUP_DIRS.items():
            full_path = os.path.join(os.path.dirname(self.db_path), dir_path)
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"备份目录已初始化: {full_path}")
        
        image_path = os.path.join(os.path.dirname(self.db_path), self.IMAGE_DIR)
        os.makedirs(image_path, exist_ok=True)
        logger.info(f"镜像目录已初始化: {image_path}")
    
    def _init_encryption_key(self):
        """初始化加密密钥"""
        key_path = os.path.join(os.path.dirname(self.db_path), self.ENCRYPTION_KEY_FILE)
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(self.encryption_key)
        
        self.fernet = Fernet(self.encryption_key)
        logger.info("加密密钥初始化完成")
    
    def _init_backup_tables(self):
        """初始化备份记录表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_type TEXT NOT NULL,
                    backup_engine TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    checksum TEXT,
                    is_encrypted INTEGER DEFAULT 1,
                    backup_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    description TEXT,
                    source_db TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_type TEXT NOT NULL,
                    interval_minutes INTEGER DEFAULT 60,
                    backup_types TEXT DEFAULT 'primary,secondary,tertiary',
                    is_enabled INTEGER DEFAULT 1,
                    last_run_time TEXT,
                    next_run_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("备份记录表初始化完成")
    
    @staticmethod
    def _get_connection():
        """获取数据库连接"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        sha256_hash = hashes.Hash(hashes.SHA256())
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        return base64.b64encode(sha256_hash.finalize()).decode()
    
    def _encrypt_file(self, input_path: str, output_path: str) -> bool:
        """加密文件"""
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.fernet.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"加密文件失败: {e}")
            return False
    
    def _decrypt_file(self, input_path: str, output_path: str) -> bool:
        """解密文件"""
        try:
            with open(input_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"解密文件失败: {e}")
            return False
    
    def _export_to_csv(self, conn: sqlite3.Connection, output_path: str) -> bool:
        """导出数据库到CSV格式（第三备份引擎）"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    csv_content = ','.join(columns) + '\n'
                    for row in rows:
                        csv_content += ','.join(str(col) for col in row) + '\n'
                    
                    zipf.writestr(f"{table}.csv", csv_content)
            
            return True
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False
    
    def _export_to_json(self, conn: sqlite3.Connection, output_path: str) -> bool:
        """导出数据库到JSON格式（第三备份引擎）"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            data = {}
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                table_data = []
                for row in rows:
                    table_data.append(dict(zip(columns, row)))
                
                data[table] = table_data
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            return False
    
    def create_backup(self, backup_type: str = 'primary') -> Dict[str, Any]:
        """创建备份"""
        result = {
            'success': False,
            'backup_type': backup_type,
            'file_path': '',
            'file_size': 0,
            'checksum': '',
            'is_encrypted': True,
            'error': ''
        }
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.db_path), self.BACKUP_DIRS[backup_type])
            
            if backup_type == 'primary':
                backup_engine = 'sqlite_copy'
                backup_filename = f"backup_{timestamp}_primary.sqlite"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                shutil.copy2(self.db_path, backup_path)
            
            elif backup_type == 'secondary':
                backup_engine = 'sqlite_dump'
                backup_filename = f"backup_{timestamp}_secondary.sql"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                with sqlite3.connect(self.db_path) as conn:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        for line in conn.iterdump():
                            f.write(line + '\n')
            
            elif backup_type == 'tertiary':
                backup_engine = 'csv_json'
                backup_filename = f"backup_{timestamp}_tertiary"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                with sqlite3.connect(self.db_path) as conn:
                    self._export_to_csv(conn, backup_path + '.zip')
                    self._export_to_json(conn, backup_path + '.json')
                
                with zipfile.ZipFile(backup_path + '_combined.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_path + '.zip', os.path.basename(backup_path + '.zip'))
                    zipf.write(backup_path + '.json', os.path.basename(backup_path + '.json'))
                
                backup_path = backup_path + '_combined.zip'
                
                os.remove(backup_path.replace('_combined.zip', '.zip'))
                os.remove(backup_path.replace('_combined.zip', '.json'))
            
            else:
                result['error'] = '未知备份类型'
                return result
            
            encrypted_path = backup_path + '.encrypted'
            if self._encrypt_file(backup_path, encrypted_path):
                os.remove(backup_path)
                backup_path = encrypted_path
            
            result['file_path'] = backup_path
            result['file_size'] = os.path.getsize(backup_path)
            result['checksum'] = self._calculate_checksum(backup_path)
            result['backup_engine'] = backup_engine
            result['success'] = True
            
            logger.info(f"备份创建成功: {backup_type} - {backup_path}")
            
            self._save_backup_record(result)
            
            self.cleanup_excess_backups(keep_count=20)
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"创建备份失败: {e}")
        
        return result
    
    def create_all_backups(self) -> List[Dict[str, Any]]:
        """创建所有备份"""
        results = []
        
        for backup_type in self.BACKUP_DIRS.keys():
            result = self.create_backup(backup_type)
            results.append(result)
        
        return results
    
    def _save_backup_record(self, backup_info: Dict[str, Any]):
        """保存备份记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backup_records 
                (backup_type, backup_engine, file_path, file_size, 
                 checksum, is_encrypted, description, source_db)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backup_info['backup_type'],
                backup_info['backup_engine'],
                backup_info['file_path'],
                backup_info['file_size'],
                backup_info['checksum'],
                backup_info['is_encrypted'],
                f"自动备份 {backup_info['backup_type']}",
                self.db_path
            ))
    
    def get_backup_records(self, backup_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取备份记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if backup_type:
                cursor.execute(f"SELECT * FROM backup_records WHERE backup_type = ? ORDER BY id DESC LIMIT {limit}", (backup_type,))
            else:
                cursor.execute(f"SELECT * FROM backup_records ORDER BY id DESC LIMIT {limit}")
            return [dict(row) for row in cursor.fetchall()]
    
    def restore_backup(self, backup_id: int) -> bool:
        """恢复备份"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM backup_records WHERE id = ?", (backup_id,))
                record = cursor.fetchone()
                
                if not record:
                    logger.error(f"备份记录不存在: {backup_id}")
                    return False
                
                backup_path = record['file_path']
                
                if not os.path.exists(backup_path):
                    logger.error(f"备份文件不存在: {backup_path}")
                    return False
                
                backup_engine = record['backup_engine']
                
                if backup_engine == 'sqlite_copy':
                    shutil.copy2(backup_path, self.db_path)
                
                elif backup_engine == 'sqlite_dump':
                    with sqlite3.connect(self.db_path) as target_conn:
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            sql_script = f.read()
                        target_conn.executescript(sql_script)
                
                elif backup_engine == 'csv_json':
                    logger.warning("CSV/JSON备份恢复需要手动处理")
                    return False
                
                logger.info(f"备份恢复成功: {backup_id}")
                return True
                
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 7) -> int:
        """清理旧备份"""
        cleanup_count = 0
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        
        for backup_type, dir_path in self.BACKUP_DIRS.items():
            full_path = os.path.join(os.path.dirname(self.db_path), dir_path)
            if os.path.exists(full_path):
                for filename in os.listdir(full_path):
                    file_path = os.path.join(full_path, filename)
                    if os.path.isfile(file_path):
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime < cutoff_time:
                            os.remove(file_path)
                            cleanup_count += 1
        
        logger.info(f"已清理 {cleanup_count} 个旧备份文件")
        return cleanup_count
    
    def cleanup_excess_backups(self, keep_count: int = 20) -> int:
        """清理多余备份，保持最近N份"""
        cleanup_count = 0
        
        for backup_type, dir_path in self.BACKUP_DIRS.items():
            full_path = os.path.join(os.path.dirname(self.db_path), dir_path)
            if os.path.exists(full_path):
                files = []
                for filename in os.listdir(full_path):
                    file_path = os.path.join(full_path, filename)
                    if os.path.isfile(file_path):
                        files.append((file_path, os.path.getmtime(file_path)))
                
                files.sort(key=lambda x: x[1], reverse=True)
                
                if len(files) > keep_count:
                    for file_path, _ in files[keep_count:]:
                        os.remove(file_path)
                        cleanup_count += 1
        
        logger.info(f"已清理 {cleanup_count} 个多余备份文件，保持最近 {keep_count} 份")
        return cleanup_count
    
    def create_restore_image(self, version: str = 'latest') -> Dict[str, Any]:
        """创建恢复镜像（保留1.0和最新版本）"""
        result = {
            'success': False,
            'version': version,
            'file_path': '',
            'error': ''
        }
        
        try:
            image_dir = os.path.join(os.path.dirname(self.db_path), self.IMAGE_DIR)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if version == '1.0':
                image_filename = f"restore_image_v1.0_{timestamp}.zip"
            else:
                image_filename = f"restore_image_latest_{timestamp}.zip"
            
            image_path = os.path.join(image_dir, image_filename)
            
            with zipfile.ZipFile(image_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(self.db_path, os.path.basename(self.db_path))
                
                for root, dirs, files in os.walk(os.path.dirname(self.db_path)):
                    for file in files:
                        if file.endswith('.sql') or file.endswith('.json'):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(self.db_path))
                            zipf.write(file_path, arcname)
            
            encrypted_path = image_path + '.encrypted'
            if self._encrypt_file(image_path, encrypted_path):
                os.remove(image_path)
                image_path = encrypted_path
            
            self._cleanup_old_images()
            
            result['success'] = True
            result['file_path'] = image_path
            result['file_size'] = os.path.getsize(image_path)
            
            logger.info(f"恢复镜像创建成功: {version} - {image_path}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"创建恢复镜像失败: {e}")
        
        return result
    
    def _cleanup_old_images(self):
        """清理旧的恢复镜像，只保留1.0和最新版本"""
        image_dir = os.path.join(os.path.dirname(self.db_path), self.IMAGE_DIR)
        if not os.path.exists(image_dir):
            return
        
        v1_files = []
        latest_files = []
        
        for filename in os.listdir(image_dir):
            file_path = os.path.join(image_dir, filename)
            if os.path.isfile(file_path):
                if 'v1.0' in filename:
                    v1_files.append((file_path, os.path.getmtime(file_path)))
                elif 'latest' in filename:
                    latest_files.append((file_path, os.path.getmtime(file_path)))
        
        v1_files.sort(key=lambda x: x[1], reverse=True)
        latest_files.sort(key=lambda x: x[1], reverse=True)
        
        for file_path, _ in v1_files[1:]:
            os.remove(file_path)
        
        for file_path, _ in latest_files[1:]:
            os.remove(file_path)
    
    def verify_backup_integrity(self, backup_id: int) -> bool:
        """验证备份完整性"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM backup_records WHERE id = ?", (backup_id,))
                record = cursor.fetchone()
                
                if not record:
                    return False
                
                backup_path = record['file_path']
                stored_checksum = record['checksum']
                
                if not os.path.exists(backup_path):
                    return False
                
                current_checksum = self._calculate_checksum(backup_path)
                
                return current_checksum == stored_checksum
                
        except Exception as e:
            logger.error(f"验证备份完整性失败: {e}")
            return False
    
    def get_backup_status(self) -> Dict[str, Any]:
        """获取备份状态"""
        records = self.get_backup_records(limit=10)
        
        status = {
            'total_backups': len(records),
            'last_backup_time': None,
            'backups_by_type': {
                'primary': 0,
                'secondary': 0,
                'tertiary': 0
            },
            'encryption_enabled': True,
            'backup_dirs': {}
        }
        
        if records:
            status['last_backup_time'] = records[0]['backup_time']
        
        for record in records:
            status['backups_by_type'][record['backup_type']] += 1
        
        for backup_type, dir_path in self.BACKUP_DIRS.items():
            full_path = os.path.join(os.path.dirname(self.db_path), dir_path)
            status['backup_dirs'][backup_type] = {
                'path': full_path,
                'exists': os.path.exists(full_path)
            }
        
        return status
    
    def schedule_backup(self, schedule_type: str = 'hourly', interval_minutes: int = 60) -> bool:
        """设置备份计划"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO backup_schedule 
                    (schedule_type, interval_minutes, next_run_time)
                    VALUES (?, ?, ?)
                ''', (
                    schedule_type,
                    interval_minutes,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            logger.info(f"备份计划已设置: {schedule_type}，间隔 {interval_minutes} 分钟")
            return True
        except Exception as e:
            logger.error(f"设置备份计划失败: {e}")
            return False


backup_service = BackupService()