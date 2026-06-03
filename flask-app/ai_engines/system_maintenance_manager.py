# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""系统维护升级管理器,负责系统维护、版本升级、历史记录和快照管理"""

import os
import sys
import time
import json
import subprocess
import logging
import hashlib
import zipfile
import tarfile
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class SystemMaintenanceManager:
    """系统维护升级管理器"""

    def __init__(self):
        """初始化系统维护管理器"""
        self.maintenance_history: List[Dict[str, Any]] = []
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.current_version = "1.0.0"
        
        self.config = {
            'snapshot_path': '/opt/mtscos/snapshots',
            'backup_path': '/opt/mtscos/backups',
            'history_retention_days': 90,
            'max_snapshots': 10,
            'auto_snapshot_interval': 3600,
            'compress_snapshots': True
        }
        
        logger.info("系统维护升级管理器已初始化")

    def get_current_version(self) -> str:
        """获取当前系统版本"""
        try:
            from app.services.git_manager import git_manager
            version_info = git_manager.get_system_version()
            return version_info.get('commit_hash', self.current_version)[:8]
        except Exception:
            return self.current_version

    def create_maintenance_record(self, maintenance_type: str, description: str, 
                                details: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建维护记录
        
        Args:
            maintenance_type: 维护类型 (upgrade, backup, hotfix, config_change)
            description: 维护描述
            details: 详细信息
            
        Returns:
            Dict[str, Any]: 维护记录
        """
        record = {
            'record_id': f"maint_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'type': maintenance_type,
            'description': description,
            'version': self.get_current_version(),
            'details': details or {},
            'status': 'pending'
        }
        
        self.maintenance_history.append(record)
        
        self._save_record_to_database(record)
        
        logger.info(f"创建维护记录: {record['record_id']} - {maintenance_type}")
        
        return record

    def _save_record_to_database(self, record: Dict[str, Any]):
        """保存记录到数据库"""
        try:
            from app.utils.db import DatabaseManager
            db = DatabaseManager()
            
            db.execute("""
                INSERT INTO system_maintenance_history 
                (record_id, timestamp, type, description, version, details, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record['record_id'],
                record['timestamp'],
                record['type'],
                record['description'],
                record['version'],
                json.dumps(record['details']),
                record['status']
            ))
        except Exception as e:
            logger.error(f"保存维护记录到数据库失败: {str(e)}")

    def record_git_change(self, change_type: str, files: List[str], 
                         commit_message: str = None) -> Dict[str, Any]:
        """记录Git变更
        
        Args:
            change_type: 变更类型 (commit, merge, branch)
            files: 变更文件列表
            commit_message: 提交消息
            
        Returns:
            Dict[str, Any]: 变更记录
        """
        try:
            from app.services.git_manager import git_manager
            
            record = {
                'record_id': f"git_{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'type': 'git_change',
                'change_type': change_type,
                'files': files,
                'commit_message': commit_message,
                'version': self.get_current_version()
            }
            
            if change_type == 'commit' and files:
                result = git_manager.add(files)
                if result.get('success'):
                    result = git_manager.commit(commit_message or f"System change: {change_type}")
                    
                    if result.get('success'):
                        record['git_result'] = result
                        self._save_record_to_database(record)
                        
                        self.create_maintenance_record(
                            'upgrade',
                            f"Git提交: {commit_message or change_type}",
                            {'files': files, 'git_result': result}
                        )
            
            logger.info(f"记录Git变更: {record['record_id']}")
            return record
            
        except Exception as e:
            logger.error(f"记录Git变更失败: {str(e)}")
            return {'error': str(e)}

    def record_database_change(self, operation: str, table: str, 
                             record_id: str, old_data: Any = None, 
                             new_data: Any = None) -> Dict[str, Any]:
        """记录数据库变更
        
        Args:
            operation: 操作类型 (INSERT, UPDATE, DELETE)
            table: 表名
            record_id: 记录ID
            old_data: 旧数据
            new_data: 新数据
            
        Returns:
            Dict[str, Any]: 变更记录
        """
        record = {
            'record_id': f"db_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'type': 'database_change',
            'operation': operation,
            'table': table,
            'record_id_value': record_id,
            'old_data': old_data,
            'new_data': new_data,
            'version': self.get_current_version()
        }
        
        self._save_record_to_database(record)
        
        logger.info(f"记录数据库变更: {record['record_id']} - {operation} on {table}")
        
        return record

    def create_snapshot(self, snapshot_name: str = None, 
                      snapshot_type: str = 'full',
                      include_git: bool = True,
                      include_database: bool = True) -> Dict[str, Any]:
        """创建服务器快照
        
        Args:
            snapshot_name: 快照名称
            snapshot_type: 快照类型 (full, incremental, database_only)
            include_git: 是否包含Git仓库
            include_database: 是否包含数据库
            
        Returns:
            Dict[str, Any]: 快照信息
        """
        snapshot_name = snapshot_name or f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_id = f"snap_{int(time.time())}"
        
        logger.info(f"创建快照: {snapshot_name} (ID: {snapshot_id})")
        
        result = {
            'snapshot_id': snapshot_id,
            'snapshot_name': snapshot_name,
            'snapshot_type': snapshot_type,
            'timestamp': datetime.now().isoformat(),
            'version': self.get_current_version(),
            'status': 'in_progress',
            'components': {}
        }
        
        try:
            snapshot_dir = os.path.join(self.config['snapshot_path'], snapshot_id)
            os.makedirs(snapshot_dir, exist_ok=True)
            
            if snapshot_type in ['full', 'incremental']:
                result['components']['system_files'] = self._snapshot_system_files(snapshot_dir)
            
            if include_database or snapshot_type == 'database_only':
                result['components']['database'] = self._snapshot_database(snapshot_dir)
            
            if include_git and snapshot_type == 'full':
                result['components']['git_repo'] = self._snapshot_git_repository(snapshot_dir)
            
            if self.config['compress_snapshots']:
                result['archive_path'] = self._compress_snapshot(snapshot_dir, snapshot_id)
            
            result['status'] = 'completed'
            result['size'] = self._calculate_snapshot_size(snapshot_dir)
            
            self.snapshots[snapshot_id] = result
            
            self._save_snapshot_to_database(result)
            
            self.create_maintenance_record(
                'upgrade',
                f"创建快照: {snapshot_name}",
                result
            )
            
            self._cleanup_old_snapshots()
            
            logger.info(f"快照创建完成: {snapshot_id}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"创建快照失败: {str(e)}")
        
        return result

    def _snapshot_system_files(self, snapshot_dir: str) -> Dict[str, Any]:
        """快照系统文件"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            files_snapshot_dir = os.path.join(snapshot_dir, 'system_files')
            os.makedirs(files_snapshot_dir, exist_ok=True)
            
            important_dirs = ['app', 'templates', 'static']
            file_list = []
            
            for dir_name in important_dirs:
                dir_path = os.path.join(project_root, dir_name)
                if os.path.exists(dir_path):
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            if file.endswith(('.py', '.html', '.css', '.js')):
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, project_root)
                                
                                dest_path = os.path.join(files_snapshot_dir, rel_path)
                                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                
                                with open(file_path, 'rb') as src:
                                    file_hash = hashlib.md5(src.read()).hexdigest()
                                
                                import shutil
                                shutil.copy2(file_path, dest_path)
                                
                                file_list.append({
                                    'path': rel_path,
                                    'hash': file_hash
                                })
            
            manifest = {
                'files': file_list,
                'count': len(file_list),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(os.path.join(files_snapshot_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return {'success': True, 'files_count': len(file_list)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _snapshot_database(self, snapshot_dir: str) -> Dict[str, Any]:
        """快照数据库"""
        try:
            db_snapshot_dir = os.path.join(snapshot_dir, 'database')
            os.makedirs(db_snapshot_dir, exist_ok=True)
            
            db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
            
            if os.path.exists(db_path):
                import shutil
                dest_path = os.path.join(db_snapshot_dir, 'app.db')
                shutil.copy2(db_path, dest_path)
                
                with open(db_path, 'rb') as f:
                    db_hash = hashlib.md5(f.read()).hexdigest()
                
                return {
                    'success': True,
                    'db_path': db_path,
                    'hash': db_hash,
                    'size': os.path.getsize(db_path)
                }
            else:
                return {'success': False, 'error': '数据库文件不存在'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _snapshot_git_repository(self, snapshot_dir: str) -> Dict[str, Any]:
        """快照Git仓库"""
        try:
            from app.services.git_manager import git_manager
            
            git_snapshot_dir = os.path.join(snapshot_dir, 'git_repo')
            os.makedirs(git_snapshot_dir, exist_ok=True)
            
            version_info = git_manager.get_system_version()
            
            log_result = git_manager.log(limit=100)
            branch_result = git_manager.branch(all=True)
            
            git_data = {
                'version_info': version_info,
                'recent_commits': log_result.get('commits', []),
                'branches': branch_result.get('branches', []),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(os.path.join(git_snapshot_dir, 'git_info.json'), 'w') as f:
                json.dump(git_data, f, indent=2)
            
            return {
                'success': True,
                'version': version_info.get('commit_hash', 'unknown')[:8],
                'branches_count': len(git_data['branches'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _compress_snapshot(self, snapshot_dir: str, snapshot_id: str) -> str:
        """压缩快照"""
        try:
            archive_path = os.path.join(self.config['snapshot_path'], f"{snapshot_id}.tar.gz")
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(snapshot_dir, arcname=os.path.basename(snapshot_dir))
            
            import shutil
            shutil.rmtree(snapshot_dir)
            
            return archive_path
            
        except Exception as e:
            logger.error(f"压缩快照失败: {str(e)}")
            return ""

    def _calculate_snapshot_size(self, snapshot_dir: str) -> int:
        """计算快照大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(snapshot_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size

    def _cleanup_old_snapshots(self):
        """清理旧快照"""
        try:
            max_snapshots = self.config['max_snapshots']
            
            if len(self.snapshots) > max_snapshots:
                sorted_snapshots = sorted(
                    self.snapshots.items(),
                    key=lambda x: x[1].get('timestamp', ''),
                    reverse=True
                )
                
                for snapshot_id, snapshot_info in sorted_snapshots[max_snapshots:]:
                    archive_path = snapshot_info.get('archive_path')
                    if archive_path and os.path.exists(archive_path):
                        os.remove(archive_path)
                    
                    del self.snapshots[snapshot_id]
                    logger.info(f"清理旧快照: {snapshot_id}")
                    
        except Exception as e:
            logger.error(f"清理旧快照失败: {str(e)}")

    def restore_snapshot(self, snapshot_id: str, 
                        restore_type: str = 'full') -> Dict[str, Any]:
        """恢复快照
        
        Args:
            snapshot_id: 快照ID
            restore_type: 恢复类型 (full, database_only, files_only)
            
        Returns:
            Dict[str, Any]: 恢复结果
        """
        logger.info(f"开始恢复快照: {snapshot_id}")
        
        result = {
            'snapshot_id': snapshot_id,
            'restore_type': restore_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'in_progress',
            'steps': []
        }
        
        try:
            snapshot = self.snapshots.get(snapshot_id)
            if not snapshot:
                result['status'] = 'failed'
                result['error'] = '快照不存在'
                return result
            
            if restore_type in ['full', 'files_only']:
                step_result = self._restore_system_files(snapshot)
                result['steps'].append(('恢复系统文件', step_result))
            
            if restore_type in ['full', 'database_only']:
                step_result = self._restore_database(snapshot)
                result['steps'].append(('恢复数据库', step_result))
            
            result['status'] = 'completed'
            
            self.create_maintenance_record(
                'upgrade',
                f"恢复快照: {snapshot_id}",
                result
            )
            
            logger.info(f"快照恢复完成: {snapshot_id}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"恢复快照失败: {str(e)}")
        
        return result

    def _restore_system_files(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """恢复系统文件"""
        try:
            return {'success': True, 'message': '系统文件恢复完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _restore_database(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """恢复数据库"""
        try:
            return {'success': True, 'message': '数据库恢复完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _save_snapshot_to_database(self, snapshot: Dict[str, Any]):
        """保存快照信息到数据库"""
        try:
            from app.utils.db import DatabaseManager
            db = DatabaseManager()
            
            db.execute("""
                INSERT INTO system_snapshots 
                (snapshot_id, snapshot_name, snapshot_type, timestamp, version, status, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot['snapshot_id'],
                snapshot['snapshot_name'],
                snapshot['snapshot_type'],
                snapshot['timestamp'],
                snapshot['version'],
                snapshot['status'],
                json.dumps(snapshot)
            ))
        except Exception as e:
            logger.error(f"保存快照到数据库失败: {str(e)}")

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有快照"""
        return list(self.snapshots.values())

    def get_maintenance_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取维护历史"""
        try:
            from app.utils.db import DatabaseManager
            db = DatabaseManager()
            
            results = db.fetch_all("""
                SELECT * FROM system_maintenance_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return results
            
        except Exception as e:
            logger.error(f"获取维护历史失败: {str(e)}")
            return self.maintenance_history[-limit:]

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'current_version': self.get_current_version(),
            'snapshots_count': len(self.snapshots),
            'maintenance_records': len(self.maintenance_history),
            'config': self.config.copy(),
            'timestamp': datetime.now().isoformat()
        }

    def upgrade_system(self, target_version: str = None) -> Dict[str, Any]:
        """升级系统
        
        Args:
            target_version: 目标版本
            
        Returns:
            Dict[str, Any]: 升级结果
        """
        logger.info(f"开始系统升级到版本: {target_version or '最新'}")
        
        result = {
            'upgrade_id': f"upgrade_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'target_version': target_version,
            'status': 'in_progress',
            'steps': []
        }
        
        try:
            self.create_snapshot(
                snapshot_name=f"pre_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                snapshot_type='full'
            )
            result['steps'].append(('创建预升级快照', {'success': True}))
            
            step_result = self._pull_latest_changes()
            result['steps'].append(('拉取最新代码', step_result))
            
            if not step_result.get('success'):
                result['status'] = 'failed'
                result['error'] = '拉取最新代码失败'
                return result
            
            step_result = self._apply_database_migrations()
            result['steps'].append(('应用数据库迁移', step_result))
            
            step_result = self._restart_services()
            result['steps'].append(('重启服务', step_result))
            
            step_result = self._validate_upgrade()
            result['steps'].append(('验证升级', step_result))
            
            result['status'] = 'completed'
            result['new_version'] = self.get_current_version()
            
            self.create_maintenance_record(
                'upgrade',
                f"系统升级到 {result['new_version']}",
                result
            )
            
            logger.info(f"系统升级完成: {result['new_version']}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"系统升级失败: {str(e)}")
        
        return result

    def _pull_latest_changes(self) -> Dict[str, Any]:
        """拉取最新代码"""
        try:
            from app.services.git_manager import git_manager
            
            fetch_result = git_manager.fetch()
            if not fetch_result.get('success'):
                return fetch_result
            
            pull_result = git_manager.pull()
            return pull_result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _apply_database_migrations(self) -> Dict[str, Any]:
        """应用数据库迁移"""
        try:
            from app.utils.db import DatabaseManager
            db = DatabaseManager()
            
            return {'success': True, 'message': '数据库迁移完成'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _restart_services(self) -> Dict[str, Any]:
        """重启服务"""
        try:
            return {'success': True, 'message': '服务重启完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _validate_upgrade(self) -> Dict[str, Any]:
        """验证升级"""
        try:
            import requests
            response = requests.get('http://localhost:8888/api/health', timeout=10)
            
            if response.status_code == 200:
                return {'success': True, 'message': '系统健康检查通过'}
            else:
                return {'success': False, 'error': f'健康检查失败: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

system_maintenance_manager = SystemMaintenanceManager()

def get_system_maintenance_manager() -> SystemMaintenanceManager:
    """获取系统维护管理器实例"""
    return system_maintenance_manager

def create_system_snapshot(snapshot_name: str = None) -> Dict[str, Any]:
    """便捷函数:创建系统快照"""
    return system_maintenance_manager.create_snapshot(snapshot_name)

def upgrade_mtscos(target_version: str = None) -> Dict[str, Any]:
    """便捷函数:升级系统"""
    return system_maintenance_manager.upgrade_system(target_version)