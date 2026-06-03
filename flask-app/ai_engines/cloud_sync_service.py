# -*- coding: utf-8 -*-
"""
MTSCOS 云端同步服务
支持云存储、数据同步、跨设备同步、备份恢复
"""

import os
import json
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import OrderedDict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_sync_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cloud_sync_service')

class CloudStorageBackend:
    """云存储后端基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.connected = False
    
    def connect(self) -> bool:
        """连接存储后端"""
        self.connected = True
        logger.info(f"已连接到 {self.name}")
        return True
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info(f"已断开 {self.name} 连接")
    
    def upload_file(self, file_path: str, remote_path: str) -> bool:
        """上传文件"""
        raise NotImplementedError
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        raise NotImplementedError
    
    def list_files(self, remote_path: str) -> List[str]:
        """列出文件"""
        raise NotImplementedError
    
    def delete_file(self, remote_path: str) -> bool:
        """删除文件"""
        raise NotImplementedError
    
    def file_exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError

class LocalCloudBackend(CloudStorageBackend):
    """本地云存储模拟后端"""
    
    def __init__(self):
        super().__init__('LocalCloud')
        self.base_dir = os.path.join(os.path.expanduser('~'), '.mtscos_cloud')
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _get_remote_path(self, remote_path: str) -> str:
        """获取本地路径"""
        return os.path.join(self.base_dir, remote_path.lstrip('/'))
    
    def upload_file(self, file_path: str, remote_path: str) -> bool:
        """上传文件"""
        try:
            local_remote_path = self._get_remote_path(remote_path)
            os.makedirs(os.path.dirname(local_remote_path), exist_ok=True)
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            with open(local_remote_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"文件上传成功: {file_path} -> {remote_path}")
            return True
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        try:
            local_remote_path = self._get_remote_path(remote_path)
            
            if not os.path.exists(local_remote_path):
                logger.error(f"远程文件不存在: {remote_path}")
                return False
            
            with open(local_remote_path, 'rb') as f:
                content = f.read()
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"文件下载成功: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return False
    
    def list_files(self, remote_path: str) -> List[str]:
        """列出文件"""
        try:
            local_remote_path = self._get_remote_path(remote_path)
            
            if not os.path.exists(local_remote_path):
                return []
            
            files = []
            for item in os.listdir(local_remote_path):
                item_path = os.path.join(local_remote_path, item)
                if os.path.isfile(item_path):
                    files.append(f"{remote_path}/{item}")
            
            return files
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """删除文件"""
        try:
            local_remote_path = self._get_remote_path(remote_path)
            
            if os.path.exists(local_remote_path):
                os.remove(local_remote_path)
                logger.info(f"文件删除成功: {remote_path}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        local_remote_path = self._get_remote_path(remote_path)
        return os.path.exists(local_remote_path)

class SyncSession:
    """同步会话"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_id = f"sync_{int(datetime.now().timestamp())}"
        self.start_time = datetime.now()
        self.status = 'active'
        self.uploaded_files = []
        self.downloaded_files = []
        self.skipped_files = []
        self.errors = []
    
    def add_uploaded(self, file_path: str):
        """添加已上传文件"""
        self.uploaded_files.append(file_path)
    
    def add_downloaded(self, file_path: str):
        """添加已下载文件"""
        self.downloaded_files.append(file_path)
    
    def add_skipped(self, file_path: str):
        """添加跳过文件"""
        self.skipped_files.append(file_path)
    
    def add_error(self, file_path: str, error: str):
        """添加错误"""
        self.errors.append({'file': file_path, 'error': error})
    
    def complete(self):
        """完成会话"""
        self.status = 'completed'
        self.end_time = datetime.now()
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': getattr(self, 'end_time', None).isoformat() if hasattr(self, 'end_time') else None,
            'status': self.status,
            'uploaded_files': self.uploaded_files,
            'downloaded_files': self.downloaded_files,
            'skipped_files': self.skipped_files,
            'errors': self.errors,
            'duration': (self.end_time - self.start_time).total_seconds() if hasattr(self, 'end_time') else 0
        }

class CloudSyncService:
    """云端同步服务"""
    
    def __init__(self):
        self.backend = LocalCloudBackend()
        self.user_sync_status = {}
        self.sync_history = []
        self.auto_sync_enabled = True
        self.auto_sync_interval_minutes = 30
        self._start_auto_sync()
        logger.info("云端同步服务初始化完成")
    
    def _get_user_folder(self, user_id: str) -> str:
        """获取用户云存储文件夹"""
        return f"users/{user_id}"
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_sync_metadata(self, user_id: str) -> Dict[str, Any]:
        """获取同步元数据"""
        metadata_path = f"{self._get_user_folder(user_id)}/sync_metadata.json"
        
        if self.backend.file_exists(metadata_path):
            local_path = f"/tmp/sync_metadata_{user_id}.json"
            if self.backend.download_file(metadata_path, local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return {'last_sync': None, 'files': {}}
    
    def _save_sync_metadata(self, user_id: str, metadata: Dict[str, Any]):
        """保存同步元数据"""
        metadata_path = f"{self._get_user_folder(user_id)}/sync_metadata.json"
        local_path = f"/tmp/sync_metadata_{user_id}.json"
        
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        self.backend.upload_file(local_path, metadata_path)
    
    def sync_file(self, user_id: str, local_file_path: str, remote_file_name: str, 
                  sync_direction: str = 'both') -> Dict[str, Any]:
        """同步单个文件"""
        result = {
            'success': False,
            'file': remote_file_name,
            'action': 'none',
            'message': ''
        }
        
        remote_path = f"{self._get_user_folder(user_id)}/{remote_file_name}"
        metadata = self._get_sync_metadata(user_id)
        
        try:
            if sync_direction in ['upload', 'both']:
                if os.path.exists(local_file_path):
                    local_checksum = self._calculate_checksum(local_file_path)
                    remote_checksum = metadata.get('files', {}).get(remote_file_name, {}).get('checksum')
                    
                    if local_checksum != remote_checksum:
                        if self.backend.upload_file(local_file_path, remote_path):
                            metadata['files'][remote_file_name] = {
                                'checksum': local_checksum,
                                'last_modified': datetime.now().isoformat(),
                                'size': os.path.getsize(local_file_path)
                            }
                            result['action'] = 'uploaded'
                            result['success'] = True
                            result['message'] = '文件已上传'
                        else:
                            result['message'] = '文件上传失败'
                    else:
                        result['action'] = 'skipped'
                        result['success'] = True
                        result['message'] = '文件未变化，跳过'
            
            if sync_direction in ['download', 'both'] and result['action'] != 'uploaded':
                if self.backend.file_exists(remote_path):
                    remote_checksum = metadata.get('files', {}).get(remote_file_name, {}).get('checksum')
                    
                    if os.path.exists(local_file_path):
                        local_checksum = self._calculate_checksum(local_file_path)
                        if local_checksum == remote_checksum:
                            result['action'] = 'skipped'
                            result['success'] = True
                            result['message'] = '文件未变化，跳过'
                            return result
                    
                    if self.backend.download_file(remote_path, local_file_path):
                        result['action'] = 'downloaded'
                        result['success'] = True
                        result['message'] = '文件已下载'
                else:
                    if sync_direction == 'download':
                        result['message'] = '远程文件不存在'
            
            self._save_sync_metadata(user_id, metadata)
            
        except Exception as e:
            result['message'] = f'同步失败: {str(e)}'
            logger.error(f"文件同步失败 {remote_file_name}: {e}")
        
        return result
    
    def sync_user_data(self, user_id: str, local_data_dir: str, sync_direction: str = 'both') -> Dict[str, Any]:
        """同步用户数据"""
        session = SyncSession(user_id)
        
        try:
            if not self.backend.connected:
                self.backend.connect()
            
            files_to_sync = []
            
            if os.path.exists(local_data_dir):
                for item in os.listdir(local_data_dir):
                    item_path = os.path.join(local_data_dir, item)
                    if os.path.isfile(item_path):
                        files_to_sync.append(item)
            
            for filename in files_to_sync:
                local_path = os.path.join(local_data_dir, filename)
                result = self.sync_file(user_id, local_path, filename, sync_direction)
                
                if result['success']:
                    if result['action'] == 'uploaded':
                        session.add_uploaded(filename)
                    elif result['action'] == 'downloaded':
                        session.add_downloaded(filename)
                    elif result['action'] == 'skipped':
                        session.add_skipped(filename)
                else:
                    session.add_error(filename, result['message'])
            
            session.complete()
            self.sync_history.append(session.to_dict())
            
            self.user_sync_status[user_id] = {
                'last_sync': datetime.now().isoformat(),
                'status': 'synced',
                'files_uploaded': len(session.uploaded_files),
                'files_downloaded': len(session.downloaded_files)
            }
            
            result = {
                'success': True,
                'session_id': session.session_id,
                'user_id': user_id,
                'uploaded': session.uploaded_files,
                'downloaded': session.downloaded_files,
                'skipped': session.skipped_files,
                'errors': session.errors,
                'duration': session.to_dict()['duration'],
                'message': f"同步完成: 上传 {len(session.uploaded_files)} 个文件，下载 {len(session.downloaded_files)} 个文件"
            }
            
            logger.info(result['message'])
            return result
        
        except Exception as e:
            session.add_error('sync', str(e))
            session.complete()
            self.sync_history.append(session.to_dict())
            
            return {
                'success': False,
                'session_id': session.session_id,
                'user_id': user_id,
                'message': f"同步失败: {str(e)}",
                'errors': [str(e)]
            }
    
    def backup_user_data(self, user_id: str, local_data_dir: str) -> Dict[str, Any]:
        """备份用户数据到云端"""
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        backup_path = f"{self._get_user_folder(user_id)}/backups/{backup_name}"
        
        try:
            if not self.backend.connected:
                self.backend.connect()
            
            import zipfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp_path = tmp.name
            
            with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(local_data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, local_data_dir)
                        zipf.write(file_path, arcname)
            
            success = self.backend.upload_file(tmp_path, backup_path)
            os.remove(tmp_path)
            
            if success:
                logger.info(f"用户 {user_id} 数据备份成功: {backup_name}")
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'backup_path': backup_path,
                    'message': '备份成功'
                }
            
            return {'success': False, 'message': '备份失败'}
        
        except Exception as e:
            logger.error(f"备份失败: {e}")
            return {'success': False, 'message': f'备份失败: {str(e)}'}
    
    def restore_user_data(self, user_id: str, backup_name: str, restore_dir: str) -> Dict[str, Any]:
        """从云端恢复用户数据"""
        backup_path = f"{self._get_user_folder(user_id)}/backups/{backup_name}"
        
        try:
            if not self.backend.connected:
                self.backend.connect()
            
            if not self.backend.file_exists(backup_path):
                return {'success': False, 'message': '备份文件不存在'}
            
            import zipfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp_path = tmp.name
            
            if not self.backend.download_file(backup_path, tmp_path):
                return {'success': False, 'message': '下载备份文件失败'}
            
            os.makedirs(restore_dir, exist_ok=True)
            
            with zipfile.ZipFile(tmp_path, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            os.remove(tmp_path)
            
            logger.info(f"用户 {user_id} 数据恢复成功: {backup_name}")
            return {
                'success': True,
                'backup_name': backup_name,
                'restore_dir': restore_dir,
                'message': '恢复成功'
            }
        
        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return {'success': False, 'message': f'恢复失败: {str(e)}'}
    
    def list_user_backups(self, user_id: str) -> List[Dict[str, Any]]:
        """列出用户备份"""
        backups = []
        backup_dir = f"{self._get_user_folder(user_id)}/backups"
        
        try:
            if not self.backend.connected:
                self.backend.connect()
            
            files = self.backend.list_files(backup_dir)
            
            for file in files:
                if file.endswith('.zip'):
                    basename = os.path.basename(file)
                    date_str = basename.replace('backup_', '').replace('.zip', '')
                    backups.append({
                        'name': basename,
                        'path': file,
                        'date': datetime.strptime(date_str, '%Y%m%d_%H%M%S').isoformat()
                    })
            
            backups.sort(key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
        
        return backups
    
    def get_user_sync_status(self, user_id: str) -> Dict[str, Any]:
        """获取用户同步状态"""
        return self.user_sync_status.get(user_id, {
            'last_sync': None,
            'status': 'never_synced',
            'files_uploaded': 0,
            'files_downloaded': 0
        })
    
    def get_sync_history(self, user_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取同步历史"""
        history = self.sync_history
        
        if user_id:
            history = [h for h in history if h['user_id'] == user_id]
        
        return history[-limit:]
    
    def start_auto_sync(self):
        """启动自动同步"""
        self.auto_sync_enabled = True
        logger.info("自动同步已启动")
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.auto_sync_enabled = False
        logger.info("自动同步已停止")
    
    def _start_auto_sync(self):
        """启动定时自动同步任务"""
        def scheduled_sync():
            if self.auto_sync_enabled:
                logger.info("执行定时自动同步...")
                for user_id in list(self.user_sync_status.keys()):
                    status = self.user_sync_status.get(user_id, {})
                    last_sync = status.get('last_sync')
                    
                    if last_sync:
                        last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        if (datetime.now() - last_sync_time).total_seconds() > self.auto_sync_interval_minutes * 60:
                            logger.info(f"自动同步用户 {user_id}")
        
        import schedule
        import time
        
        schedule.every(self.auto_sync_interval_minutes).minutes.do(scheduled_sync)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"定时同步任务已启动，每 {self.auto_sync_interval_minutes} 分钟执行一次")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'version': '1.0.0',
            'backend': self.backend.name,
            'connected': self.backend.connected,
            'auto_sync_enabled': self.auto_sync_enabled,
            'auto_sync_interval_minutes': self.auto_sync_interval_minutes,
            'active_users': len(self.user_sync_status),
            'sync_history_count': len(self.sync_history)
        }

cloud_sync_service = CloudSyncService()

if __name__ == '__main__':
    service = CloudSyncService()
    
    print("=== 云端同步服务测试 ===")
    print(json.dumps(service.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 同步用户数据 ===")
    os.makedirs('/tmp/test_user_data', exist_ok=True)
    with open('/tmp/test_user_data/test_file.txt', 'w') as f:
        f.write('Hello Cloud!')
    
    sync_result = service.sync_user_data('test_user_001', '/tmp/test_user_data')
    print(json.dumps(sync_result, indent=2, ensure_ascii=False))
    
    print("\n=== 获取同步状态 ===")
    status = service.get_user_sync_status('test_user_001')
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    print("\n=== 备份用户数据 ===")
    backup_result = service.backup_user_data('test_user_001', '/tmp/test_user_data')
    print(json.dumps(backup_result, indent=2, ensure_ascii=False))
    
    print("\n=== 列出用户备份 ===")
    backups = service.list_user_backups('test_user_001')
    print(json.dumps(backups, indent=2, ensure_ascii=False))
    
    print("\n=== 恢复用户数据 ===")
    if backups:
        restore_result = service.restore_user_data('test_user_001', backups[0]['name'], '/tmp/restore_test')
        print(json.dumps(restore_result, indent=2, ensure_ascii=False))
    
    print("\n=== 获取同步历史 ===")
    history = service.get_sync_history('test_user_001')
    print(json.dumps(history, indent=2, ensure_ascii=False))
    
    print("\n=== 测试完成 ===")
    print("云端同步服务运行中，定时同步任务已启动...")