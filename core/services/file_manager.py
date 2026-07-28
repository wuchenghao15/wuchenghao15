#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS文件管理服务 提供文件上传、下载、管理功能 """

import os
import sys
import json
import time
import shutil
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class FileInfo:
    """文件信息"""
    
    def __init__(self, file_id: str, filename: str, filepath: str, 
                 file_size: int, file_type: str, uploader_id: str = None,
                 upload_time: str = None, description: str = '', 
                 is_public: bool = True):
        self.file_id = file_id
        self.filename = filename
        self.filepath = filepath
        self.file_size = file_size
        self.file_type = file_type
        self.uploader_id = uploader_id
        self.upload_time = upload_time or datetime.now().isoformat()
        self.description = description
        self.is_public = is_public
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'file_id': self.file_id,
            'filename': self.filename,
            'filepath': self.filepath,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploader_id': self.uploader_id,
            'upload_time': self.upload_time,
            'description': self.description,
            'is_public': self.is_public
        }

class FileManager:
    """文件管理器"""
    
    def __init__(self):
        self.files: Dict[str, FileInfo] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._init_storage_dir()
        self._load_files()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'file_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'storage_dir': 'uploads',
            'max_file_size': 10485760,
            'allowed_extensions': ['txt', 'json', 'md', 'csv', 'xlsx', 'pdf', 'png', 'jpg', 'jpeg', 'gif'],
            'auto_cleanup_enabled': True,
            'cleanup_interval': 86400,
            'retention_days': 30,
            'max_files': 1000
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'file_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS files ( id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT NOT NULL UNIQUE, filename TEXT NOT NULL, filepath TEXT NOT NULL, file_size INTEGER NOT NULL, file_type TEXT, uploader_id TEXT, upload_time TEXT DEFAULT CURRENT_TIMESTAMP, description TEXT, is_public INTEGER DEFAULT 1, download_count INTEGER DEFAULT 0, last_download TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_files_id ON files(file_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[文件] 初始化数据库失败: {e}")
    
    def _init_storage_dir(self):
        """初始化存储目录"""
        os.makedirs(self.config['storage_dir'], exist_ok=True)
        os.makedirs(os.path.join(self.config['storage_dir'], 'public'), exist_ok=True)
        os.makedirs(os.path.join(self.config['storage_dir'], 'private'), exist_ok=True)
    
    def _load_files(self):
        """加载文件"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT file_id, filename, filepath, file_size, file_type, uploader_id, upload_time, description, is_public FROM files')
            
            for row in cursor.fetchall():
                file_id, filename, filepath, file_size, file_type, uploader_id, upload_time, description,
                is_public = row
                
                file_info = FileInfo(
                    file_id=file_id,
                    filename=filename,
                    filepath=filepath,
                    file_size=file_size,
                    file_type=file_type,
                    uploader_id=uploader_id,
                    upload_time=upload_time,
                    description=description,
                    is_public=bool(is_public)
                )
                
                self.files[file_id] = file_info
            
            conn.close()
            logger(f"[文件] 加载了 {len(self.files)} 个文件")
        except Exception as e:
            logger(f"[文件] 加载文件失败: {e}")
    
    def _generate_file_id(self) -> str:
        """生成文件ID"""
        return f"file_{int(time.time())}_{hash(os.urandom(16))}"
    
    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        return ext
    
    def _is_extension_allowed(self, filename: str) -> bool:
        """检查扩展名是否允许"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return ext in self.config['allowed_extensions']
    
    def upload_file(self, file_data: bytes, filename: str, 
                    uploader_id: str = None, description: str = '',
                    is_public: bool = True) -> Optional[str]:
        """上传文件"""
        if len(file_data) > self.config['max_file_size']:
            logger(f"[文件] 文件大小超过限制")
            return None
        
        if not self._is_extension_allowed(filename):
            logger(f"[文件] 文件类型不允许: {filename}")
            return None
        
        if len(self.files) >= self.config['max_files']:
            logger(f"[文件] 达到最大文件数量限制")
            return None
        
        file_id = self._generate_file_id()
        file_type = self._get_file_type(filename)
        file_size = len(file_data)
        
        storage_dir = 'public' if is_public else 'private'
        filepath = os.path.join(self.config['storage_dir'], storage_dir, f"{file_id}_{filename}")
        
        try:
            with open(filepath, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            logger(f"[文件] 保存文件失败: {e}")
            return None
        
        file_info = FileInfo(
            file_id=file_id,
            filename=filename,
            filepath=filepath,
            file_size=file_size,
            file_type=file_type,
            uploader_id=uploader_id,
            description=description,
            is_public=is_public
        )
        
        with self.lock:
            self.files[file_id] = file_info
        
        self._save_file_to_db(file_info)
        
        logger(f"[文件] 文件上传成功: {filename}")
        return file_id
    
    def _save_file_to_db(self, file_info: FileInfo):
        """保存文件信息到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO files (file_id, filename, filepath, file_size, file_type, uploader_id, upload_time, description, is_public) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                file_info.file_id, file_info.filename, file_info.filepath,
                file_info.file_size, file_info.file_type, file_info.uploader_id,
                file_info.upload_time, file_info.description,
                1 if file_info.is_public else 0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[文件] 保存文件信息失败: {e}")
    
    def download_file(self, file_id: str) -> Optional[bytes]:
        """下载文件"""
        with self.lock:
            if file_id not in self.files:
                logger(f"[文件] 文件不存在: {file_id}")
                return None
            
            file_info = self.files[file_id]
            
            if not file_info.is_public:
                logger(f"[文件] 文件未公开: {file_id}")
                return None
        
        try:
            with open(file_info.filepath, 'rb') as f:
                data = f.read()
            
            self._record_download(file_id)
            logger(f"[文件] 文件下载成功: {file_info.filename}")
            
            return data
        except Exception as e:
            logger(f"[文件] 读取文件失败: {e}")
            return None
    
    def _record_download(self, file_id: str):
        """记录下载"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' UPDATE files SET download_count = download_count + 1, last_download = ? WHERE file_id = ? ''', (datetime.now().isoformat(), file_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[文件] 记录下载失败: {e}")
    
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        with self.lock:
            if file_id not in self.files:
                logger(f"[文件] 文件不存在: {file_id}")
                return False
            
            file_info = self.files[file_id]
            del self.files[file_id]
        
        try:
            if os.path.exists(file_info.filepath):
                os.remove(file_info.filepath)
        except Exception as e:
            logger(f"[文件] 删除文件失败: {e}")
        
        self._delete_file_from_db(file_id)
        
        logger(f"[文件] 文件删除成功: {file_info.filename}")
        return True
    
    def _delete_file_from_db(self, file_id: str):
        """从数据库删除文件"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM files WHERE file_id = ?', (file_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[文件] 从数据库删除失败: {e}")
    
    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        return self.files.get(file_id)
    
    def get_files(self, file_type: str = None, uploader_id: str = None, 
                  is_public: bool = None, limit: int = 100) -> List[FileInfo]:
        """获取文件列表"""
        result = []
        
        with self.lock:
            for file_info in self.files.values():
                if file_type and file_info.file_type != file_type:
                    continue
                if uploader_id and file_info.uploader_id != uploader_id:
                    continue
                if is_public is not None and file_info.is_public != is_public:
                    continue
                result.append(file_info)
        
        result.sort(key=lambda x: x.upload_time, reverse=True)
        return result[:limit]
    
    def get_file_types(self) -> List[str]:
        """获取所有文件类型"""
        types = set()
        
        with self.lock:
            for file_info in self.files.values():
                types.add(file_info.file_type)
        
        return sorted(list(types))
    
    def update_file_info(self, file_id: str, **kwargs) -> bool:
        """更新文件信息"""
        with self.lock:
            if file_id not in self.files:
                logger(f"[文件] 文件不存在: {file_id}")
                return False
            
            file_info = self.files[file_id]
            
            if 'description' in kwargs:
                file_info.description = kwargs['description']
            if 'is_public' in kwargs:
                old_public = file_info.is_public
                file_info.is_public = kwargs['is_public']
                
                if old_public != file_info.is_public:
                    old_dir = 'public' if old_public else 'private'
                    new_dir = 'public' if file_info.is_public else 'private'
                    old_path = file_info.filepath
                    new_path = old_path.replace(f'{self.config["storage_dir"]}/{old_dir}', 
                                               f'{self.config["storage_dir"]}/{new_dir}')
                    
                    try:
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        shutil.move(old_path, new_path)
                        file_info.filepath = new_path
                    except Exception as e:
                        logger(f"[文件] 移动文件失败: {e}")
                        return False
        
        self._update_file_in_db(file_id, kwargs)
        
        logger(f"[文件] 更新文件信息成功: {file_id}")
        return True
    
    def _update_file_in_db(self, file_id: str, updates: Dict[str, Any]):
        """更新数据库中的文件信息"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key == 'is_public':
                    set_clause.append(f"{key} = ?")
                    params.append(1 if value else 0)
                else:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(file_id)
            
            cursor.execute(f'UPDATE files SET {", ".join(set_clause)} WHERE file_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[文件] 更新数据库失败: {e}")
    
    def _cleanup_expired_files(self):
        """清理过期文件"""
        retention_days = self.config['retention_days']
        cutoff_time = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        expired_file_ids = []
        
        with self.lock:
            for file_id, file_info in self.files.items():
                if file_info.upload_time < cutoff_time:
                    expired_file_ids.append(file_id)
        
        for file_id in expired_file_ids:
            self.delete_file(file_id)
        
        if expired_file_ids:
            logger(f"[文件] 清理过期文件: {len(expired_file_ids)}个")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取文件统计"""
        with self.lock:
            total_size = sum(file.file_size for file in self.files.values())
            public_count = sum(1 for file in self.files.values() if file.is_public)
            private_count = len(self.files) - public_count
            
            return {
                'total_files': len(self.files),
                'total_size': total_size,
                'public_files': public_count,
                'private_files': private_count,
                'max_files': self.config['max_files'],
                'max_file_size': self.config['max_file_size'],
                'storage_dir': self.config['storage_dir']
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running',
            'auto_cleanup_enabled': self.config['auto_cleanup_enabled'],
            'cleanup_interval': self.config['cleanup_interval'],
            'retention_days': self.config['retention_days'],
            'stats': self.get_stats()
        }

file_manager = FileManager()
