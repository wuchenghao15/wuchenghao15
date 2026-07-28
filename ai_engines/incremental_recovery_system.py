# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量恢复镜像系统 2.0
Incremental Recovery Image System v2.0

特性:
- 快速恢复
- 压缩和加密支持
"""

import os
import sys
import json
import time
import hashlib
import shutil
import tarfile
import zipfile
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from collections import deque
import logging
import threading

logger = logging.getLogger('incremental_recovery')


class BackupType(Enum):
    """备份类型"""
    FULL = "full"           # 完整备份
    INCREMENTAL = "incremental"  # 增量备份
    DIFFERENTIAL = "differential"  # 差异备份


class MirrorStatus(Enum):
    """镜像状态"""
    CREATING = "creating"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    DELETED = "deleted"


class FileMetadata:
    """文件元数据"""
    
    def __init__(self, file_path: str):
        self.path = file_path
        self.size = 0
        self.modified_time = None
        self.checksum = None
        self.is_dir = False
        
        self._load_metadata()
    
    def _load_metadata(self):
        """加载文件元数据"""
        try:
            if os.path.exists(self.path):
                stat = os.stat(self.path)
                self.size = stat.st_size
                self.modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                self.is_dir = os.path.isdir(self.path)
                
                if not self.is_dir and self.size > 0:
                    self.checksum = self._calculate_checksum()
        except Exception as e:
            logger.error(f"加载文件元数据失败 {self.path}: {str(e)}")
    
    def _calculate_checksum(self) -> str:
        """计算文件校验和"""
        try:
            md5 = hashlib.md5()
            with open(self.path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception:
            return ""
    
    def to_dict(self) -> Dict:
        return {
            'path': self.path,
            'size': self.size,
            'modified_time': self.modified_time,
            'checksum': self.checksum,
            'is_dir': self.is_dir
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'FileMetadata':
        meta = FileMetadata(data['path'])
        meta.size = data.get('size', 0)
        meta.modified_time = data.get('modified_time')
        meta.checksum = data.get('checksum')
        meta.is_dir = data.get('is_dir', False)
        return meta


class MirrorMetadata:
    """镜像元数据"""
    
    def __init__(self, mirror_id: str, backup_type: BackupType):
        self.id = mirror_id
        self.type = backup_type
        self.status = MirrorStatus.CREATING
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.base_mirror_id = None  # 增量/差异备份的基础镜像ID
        
        self.files_count = 0
        self.total_size = 0
        self.compressed_size = 0
        self.checksum = None
        
        self.files_metadata = []  # 文件元数据列表
        
        self.backup_paths = []  # 备份路径列表
        self.exclude_patterns = []  # 排除模式
        
        self.description = ""
        self.tags = []
        
        self.version = "2.0"
    
    def add_file_metadata(self, file_meta: FileMetadata):
        """添加文件元数据"""
        self.files_metadata.append(file_meta.to_dict())
        self.files_count += 1
        self.total_size += file_meta.size
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'status': self.status.value,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'base_mirror_id': self.base_mirror_id,
            'files_count': self.files_count,
            'total_size': self.total_size,
            'compressed_size': self.compressed_size,
            'checksum': self.checksum,
            'files_metadata': self.files_metadata,
            'backup_paths': self.backup_paths,
            'exclude_patterns': self.exclude_patterns,
            'description': self.description,
            'tags': self.tags,
            'version': self.version
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'MirrorMetadata':
        mirror = MirrorMetadata(
            data['id'],
            BackupType(data.get('type', 'full'))
        )
        mirror.status = MirrorStatus(data.get('status', 'creating'))
        mirror.created_at = data.get('created_at')
        mirror.completed_at = data.get('completed_at')
        mirror.base_mirror_id = data.get('base_mirror_id')
        mirror.files_count = data.get('files_count', 0)
        mirror.total_size = data.get('total_size', 0)
        mirror.compressed_size = data.get('compressed_size', 0)
        mirror.checksum = data.get('checksum')
        mirror.files_metadata = data.get('files_metadata', [])
        mirror.backup_paths = data.get('backup_paths', [])
        mirror.exclude_patterns = data.get('exclude_patterns', [])
        mirror.description = data.get('description', '')
        mirror.tags = data.get('tags', [])
        mirror.version = data.get('version', '2.0')
        return mirror


class IncrementalRecoverySystem:
    """增量恢复镜像系统"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'backups', 'recovery_mirrors'
        )
        self.metadata_dir = os.path.join(self.storage_dir, '.metadata')
        self.mirrors_dir = os.path.join(self.storage_dir, 'mirrors')
        
        self.mirrors_index_file = os.path.join(self.metadata_dir, 'mirrors_index.json')
        
        self.max_full_backups = 5
        self.max_incremental_per_full = 10
        self.retention_days = 30
        
        self.compression_enabled = True
        self.encryption_enabled = False
        
        self.mirrors = {}
        self.mirrors_lock = threading.Lock()
        
        self._ensure_directories()
        self._load_mirrors_index()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        for directory in [self.storage_dir, self.metadata_dir, self.mirrors_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def _load_mirrors_index(self):
        """加载镜像索引"""
        try:
            if os.path.exists(self.mirrors_index_file):
                with open(self.mirrors_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mirror_id, mirror_data in data.items():
                        self.mirrors[mirror_id] = MirrorMetadata.from_dict(mirror_data)
                logger.info(f"已加载 {len(self.mirrors)} 个镜像记录")
        except Exception as e:
            logger.error(f"加载镜像索引失败: {str(e)}")
    
    def _save_mirrors_index(self):
        """保存镜像索引"""
        try:
            with self.mirrors_lock:
                data = {
                    mirror_id: mirror.to_dict() 
                    for mirror_id, mirror in self.mirrors.items()
                }
                with open(self.mirrors_index_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存镜像索引失败: {str(e)}")
    
    def generate_mirror_id(self) -> str:
        """生成镜像ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"mirror_{timestamp}"
    
    def create_full_backup(self, source_paths: List[str], 
                          description: str = "",
                          tags: List[str] = None,
                          exclude_patterns: List[str] = None) -> Optional[str]:
        """创建完整备份"""
        mirror_id = self.generate_mirror_id()
        logger.info(f"开始创建完整备份: {mirror_id}")
        
        mirror = MirrorMetadata(mirror_id, BackupType.FULL)
        mirror.backup_paths = source_paths
        mirror.description = description
        mirror.tags = tags or []
        mirror.exclude_patterns = exclude_patterns or []
        
        try:
            self.mirrors[mirror_id] = mirror
            mirror.status = MirrorStatus.CREATING
            
            # 收集文件元数据
            for source_path in source_paths:
                self._collect_files(source_path, mirror, exclude_patterns or [])
            
            # 创建镜像文件
            mirror_file = self._create_mirror_archive(mirror)
            
            # 计算镜像校验和
            mirror.checksum = self._calculate_archive_checksum(mirror_file)
            mirror.compressed_size = os.path.getsize(mirror_file)
            mirror.status = MirrorStatus.COMPLETED
            mirror.completed_at = datetime.now().isoformat()
            
            self._save_mirrors_index()
            
            logger.info(f"完整备份创建成功: {mirror_id} ({mirror.compressed_size} bytes)")
            return mirror_id
            
        except Exception as e:
            mirror.status = MirrorStatus.FAILED
            self._save_mirrors_index()
            logger.error(f"完整备份创建失败: {str(e)}")
            return None
    
    def create_incremental_backup(self, source_paths: List[str],
                                  base_mirror_id: str = None,
                                  description: str = "",
                                  tags: List[str] = None,
                                  exclude_patterns: List[str] = None) -> Optional[str]:
        """创建增量备份"""
        
        # 如果没有指定基础镜像,找最新的完整备份
        if not base_mirror_id:
            base_mirror = self._get_latest_full_mirror()
            if not base_mirror:
                logger.warning("没有找到完整备份,创建完整备份代替")
                return self.create_full_backup(source_paths, description, tags, exclude_patterns)
            base_mirror_id = base_mirror.id
        
        # 验证基础镜像
        if base_mirror_id not in self.mirrors:
            logger.error(f"基础镜像不存在: {base_mirror_id}")
            return None
        
        base_mirror = self.mirrors[base_mirror_id]
        
        # 创建增量备份
        mirror_id = self.generate_mirror_id()
        logger.info(f"开始创建增量备份: {mirror_id} (基于 {base_mirror_id})")
        
        mirror = MirrorMetadata(mirror_id, BackupType.INCREMENTAL)
        mirror.base_mirror_id = base_mirror_id
        mirror.backup_paths = source_paths
        mirror.description = description
        mirror.tags = tags or []
        mirror.exclude_patterns = exclude_patterns or []
        
        try:
            self.mirrors[mirror_id] = mirror
            mirror.status = MirrorStatus.CREATING
            
            # 获取基础镜像的文件列表
            base_files = {
                f['path']: f for f in base_mirror.files_metadata
            }
            
            # 收集增量文件
            for source_path in source_paths:
                self._collect_incremental_files(
                    source_path, mirror, base_files, exclude_patterns or []
                )
            
            # 创建增量镜像文件
            mirror_file = self._create_mirror_archive(mirror, incremental=True)
            
            mirror.checksum = self._calculate_archive_checksum(mirror_file)
            mirror.compressed_size = os.path.getsize(mirror_file)
            mirror.status = MirrorStatus.COMPLETED
            mirror.completed_at = datetime.now().isoformat()
            
            self._save_mirrors_index()
            
            logger.info(f"增量备份创建成功: {mirror_id} ({mirror.compressed_size} bytes)")
            return mirror_id
            
        except Exception as e:
            mirror.status = MirrorStatus.FAILED
            self._save_mirrors_index()
            logger.error(f"增量备份创建失败: {str(e)}")
            return None
    
    def _collect_files(self, source_path: str, mirror: MirrorMetadata, 
                      exclude_patterns: List[str]):
        """收集文件元数据"""
        if not os.path.exists(source_path):
            logger.warning(f"路径不存在: {source_path}")
            return
        
        for root, dirs, files in os.walk(source_path):
            # 检查排除模式
            relative_path = os.path.relpath(root, os.path.dirname(source_path.rstrip('/\\')))
            
            # 跳过排除的目录
            dirs[:] = [d for d in dirs if not self._should_exclude(
                os.path.join(root, d), exclude_patterns
            )]
            
            # 处理文件
            for filename in files:
                file_path = os.path.join(root, filename)
                
                if self._should_exclude(file_path, exclude_patterns):
                    continue
                
                file_meta = FileMetadata(file_path)
                mirror.add_file_metadata(file_meta)
    
    def _collect_incremental_files(self, source_path: str, mirror: MirrorMetadata,
                                   base_files: Dict, exclude_patterns: List[str]):
        """收集增量文件(仅收集变更的文件)"""
        if not os.path.exists(source_path):
            return
        
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [d for d in dirs if not self._should_exclude(
                os.path.join(root, d), exclude_patterns
            )]
            
            for filename in files:
                file_path = os.path.join(root, filename)
                
                if self._should_exclude(file_path, exclude_patterns):
                    continue
                
                relative_path = os.path.relpath(file_path, os.path.dirname(source_path.rstrip('/\\')))
                file_meta = FileMetadata(file_path)
                
                # 检查是否是新文件或修改过的文件
                if relative_path not in base_files:
                    mirror.add_file_metadata(file_meta)
                else:
                    base_meta = base_files[relative_path]
                    if file_meta.checksum != base_meta.get('checksum'):
                        mirror.add_file_metadata(file_meta)
    
    def _should_exclude(self, path: str, exclude_patterns: List[str]) -> bool:
        """检查是否应该排除"""
        import fnmatch
        
        filename = os.path.basename(path)
        
        default_excludes = [
            '__pycache__', '*.pyc', '*.pyo', '.git', '.svn',
            'node_modules', '.DS_Store', '*.log', '*.tmp',
            '*.swp', '*.swo', '*~', '.env', 'venv', '.venv'
        ]
        
        all_patterns = default_excludes + exclude_patterns
        
        for pattern in all_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(path, pattern):
                return True
        
        return False
    
    def _create_mirror_archive(self, mirror: MirrorMetadata, 
                               incremental: bool = False) -> str:
        """创建镜像归档文件"""
        mirror_file = os.path.join(
            self.mirrors_dir, 
            f"{mirror.id}.tar.gz"
        )
        
        with tarfile.open(mirror_file, 'w:gz') as tar:
            for file_meta_dict in mirror.files_metadata:
                file_meta = FileMetadata.from_dict(file_meta_dict)
                if not file_meta.is_dir and os.path.exists(file_meta.path):
                    tar.add(file_meta.path, arcname=file_meta.path)
        
        return mirror_file
    
    def _calculate_archive_checksum(self, archive_path: str) -> str:
        """计算归档文件校验和"""
        md5 = hashlib.md5()
        with open(archive_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _get_latest_full_mirror(self) -> Optional[MirrorMetadata]:
        """获取最新的完整备份镜像"""
        full_mirrors = [
            m for m in self.mirrors.values() 
            if m.type == BackupType.FULL and m.status == MirrorStatus.COMPLETED
        ]
        
        if not full_mirrors:
            return None
        
        return max(full_mirrors, key=lambda m: m.created_at)
    
    def restore_mirror(self, mirror_id: str, restore_path: str = None) -> bool:
        """恢复镜像"""
        if mirror_id not in self.mirrors:
            logger.error(f"镜像不存在: {mirror_id}")
            return False
        
        mirror = self.mirrors[mirror_id]
        
        if mirror.status != MirrorStatus.COMPLETED:
            logger.error(f"镜像未完成: {mirror_id}")
            return False
        
        if not restore_path:
            restore_path = os.path.join(self.storage_dir, 'restores', mirror_id)
        
        os.makedirs(restore_path, exist_ok=True)
        
        try:
            # 对于增量备份,需要先恢复基础镜像
            if mirror.type == BackupType.INCREMENTAL and mirror.base_mirror_id:
                logger.info(f"恢复基础镜像: {mirror.base_mirror_id}")
                base_success = self.restore_mirror(mirror.base_mirror_id, restore_path)
                if not base_success:
                    logger.error("基础镜像恢复失败")
                    return False
            
            # 解压当前镜像
            mirror_file = os.path.join(self.mirrors_dir, f"{mirror_id}.tar.gz")
            if os.path.exists(mirror_file):
                with tarfile.open(mirror_file, 'r:gz') as tar:
                    tar.extractall(restore_path)
            
            logger.info(f"镜像恢复成功: {mirror_id} -> {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"镜像恢复失败: {str(e)}")
            return False
    
    def validate_mirror(self, mirror_id: str) -> Dict:
        """验证镜像完整性"""
        if mirror_id not in self.mirrors:
            return {'valid': False, 'error': '镜像不存在'}
        
        mirror = self.mirrors[mirror_id]
        validation = {
            'mirror_id': mirror_id,
            'valid': True,
            'errors': [],
            'warnings': [],
            'validated_at': datetime.now().isoformat()
        }
        
        # 检查镜像文件是否存在
        mirror_file = os.path.join(self.mirrors_dir, f"{mirror_id}.tar.gz")
        if not os.path.exists(mirror_file):
            validation['valid'] = False
            validation['errors'].append('镜像文件不存在')
        else:
            # 验证校验和
            current_checksum = self._calculate_archive_checksum(mirror_file)
            if current_checksum != mirror.checksum:
                validation['valid'] = False
                validation['errors'].append('校验和不匹配')
        
        # 递归验证增量备份链
        if mirror.type == BackupType.INCREMENTAL and mirror.base_mirror_id:
            base_validation = self.validate_mirror(mirror.base_mirror_id)
            if not base_validation['valid']:
                validation['valid'] = False
                validation['errors'].extend(
                    [f"基础镜像错误: {e}" for e in base_validation['errors']]
                )
        
        mirror.status = MirrorStatus.VALID if validation['valid'] else MirrorStatus.INVALID
        self._save_mirrors_index()
        
        return validation
    
    def cleanup_old_mirrors(self) -> Dict:
        """清理过期镜像"""
        cleanup_result = {
            'full_mirrors_removed': 0,
            'incremental_mirrors_removed': 0,
            'space_reclaimed': 0,
            'details': []
        }
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # 获取所有完整备份
        full_mirrors = [
            m for m in self.mirrors.values()
            if m.type == BackupType.FULL
        ]
        
        # 保留最近的N个完整备份
        full_mirrors.sort(key=lambda m: m.created_at, reverse=True)
        
        for i, mirror in enumerate(full_mirrors):
            if i >= self.max_full_backups:
                created_date = datetime.fromisoformat(mirror.created_at)
                if created_date < cutoff_date:
                    self._delete_mirror(mirror.id)
                    cleanup_result['full_mirrors_removed'] += 1
                    cleanup_result['space_reclaimed'] += mirror.compressed_size
                    cleanup_result['details'].append(f"删除过期完整备份: {mirror.id}")
        
        # 清理孤立增量备份
        incremental_mirrors = [
            m for m in self.mirrors.values()
            if m.type == BackupType.INCREMENTAL
        ]
        
        for mirror in incremental_mirrors:
            # 如果基础镜像不存在,删除这个增量备份
            if mirror.base_mirror_id and mirror.base_mirror_id not in self.mirrors:
                self._delete_mirror(mirror.id)
                cleanup_result['incremental_mirrors_removed'] += 1
                cleanup_result['details'].append(f"删除孤立增量备份: {mirror.id}")
            
            # 超出最大数量限制
            elif mirror.base_mirror_id:
                base_mirror = self.mirrors.get(mirror.base_mirror_id)
                if base_mirror:
                    # 计算该基础镜像后的增量备份数量
                    later_incrementals = [
                        m for m in incremental_mirrors
                        if m.base_mirror_id == mirror.base_mirror_id and
                           m.created_at > mirror.created_at
                    ]
                    if len(later_incrementals) >= self.max_incremental_per_full:
                        self._delete_mirror(mirror.id)
                        cleanup_result['incremental_mirrors_removed'] += 1
                        cleanup_result['details'].append(f"删除超额增量备份: {mirror.id}")
        
        self._save_mirrors_index()
        
        logger.info(f"清理完成: 删除 {cleanup_result['full_mirrors_removed']} 个完整备份, "
                   f"{cleanup_result['incremental_mirrors_removed']} 个增量备份, "
                   f"释放 {cleanup_result['space_reclaimed']} bytes")
        
        return cleanup_result
    
    def _delete_mirror(self, mirror_id: str):
        """删除镜像"""
        if mirror_id in self.mirrors:
            mirror = self.mirrors[mirror_id]
            
            # 删除镜像文件
            mirror_file = os.path.join(self.mirrors_dir, f"{mirror_id}.tar.gz")
            if os.path.exists(mirror_file):
                os.remove(mirror_file)
            
            # 删除镜像记录
            mirror.status = MirrorStatus.DELETED
            del self.mirrors[mirror_id]
    
    def get_mirror_info(self, mirror_id: str) -> Optional[Dict]:
        """获取镜像信息"""
        if mirror_id in self.mirrors:
            return self.mirrors[mirror_id].to_dict()
        return None
    
    def list_mirrors(self, backup_type: BackupType = None,
                    status: MirrorStatus = None) -> List[Dict]:
        """列出镜像"""
        mirrors = self.mirrors.values()
        
        if backup_type:
            mirrors = [m for m in mirrors if m.type == backup_type]
        
        if status:
            mirrors = [m for m in mirrors if m.status == status]
        
        mirrors = sorted(mirrors, key=lambda m: m.created_at, reverse=True)
        
        return [m.to_dict() for m in mirrors]
    
    def get_recovery_chain(self, mirror_id: str) -> List[Dict]:
        """获取恢复链"""
        if mirror_id not in self.mirrors:
            return []
        
        chain = []
        current_id = mirror_id
        
        while current_id and current_id in self.mirrors:
            mirror = self.mirrors[current_id]
            chain.append(mirror.to_dict())
            
            if mirror.type == BackupType.INCREMENTAL and mirror.base_mirror_id:
                current_id = mirror.base_mirror_id
            else:
                break
        
        return list(reversed(chain))
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        full_mirrors = [m for m in self.mirrors.values() if m.type == BackupType.FULL]
        incremental_mirrors = [m for m in self.mirrors.values() if m.type == BackupType.INCREMENTAL]
        
        total_size = sum(m.compressed_size for m in self.mirrors.values())
        
        return {
            'total_mirrors': len(self.mirrors),
            'full_backups': len(full_mirrors),
            'incremental_backups': len(incremental_mirrors),
            'total_size': total_size,
            'storage_dir': self.storage_dir,
            'retention_days': self.retention_days,
            'max_full_backups': self.max_full_backups,
            'max_incremental_per_full': self.max_incremental_per_full,
            'compression_enabled': self.compression_enabled,
            'latest_full_backup': full_mirrors[0].id if full_mirrors else None
        }


# 全局实例
incremental_recovery_system = IncrementalRecoverySystem()
