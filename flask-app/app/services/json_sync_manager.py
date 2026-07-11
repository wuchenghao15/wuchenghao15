import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
JSON加密同步管理器
实现JSON数据加密和自动同步到数据库
"""

import os
import json
import sqlite3
import hashlib
import time
import threading
from datetime import datetime
from typing import Dict, Optional, Any

class JSONSyncManager:
    """JSON加密同步管理器"""
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.json_files = {}
        self.last_sync_times = {}
        self.sync_interval = 5
        self.is_running = False
        self.sync_thread = None
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化JSON同步相关的数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT UNIQUE NOT NULL,
                    encrypted_content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    sync_time TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    sync_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def _encrypt_content(self, content: str) -> str:
        """加密JSON内容"""
        import hashlib
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        import base64
        
        password = b'MTSCOS_JSON_ENCRYPTION_KEY_2024'
        salt = b'MTSCOS_JSON_SALT'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        fernet = Fernet(key)
        
        return fernet.encrypt(content.encode()).decode()
    
    def _decrypt_content(self, encrypted_content: str) -> str:
        """解密JSON内容"""
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        import base64
        
        password = b'MTSCOS_JSON_ENCRYPTION_KEY_2024'
        salt = b'MTSCOS_JSON_SALT'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        fernet = Fernet(key)
        
        try:
            return fernet.decrypt(encrypted_content.encode()).decode()
        except Exception:
            return encrypted_content
    
    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希值"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def add_json_file(self, file_path: str) -> bool:
        """添加需要监控的JSON文件"""
        if not os.path.exists(file_path):
            self.log_sync(file_path, 'ADD', 'FAILED', '文件不存在')
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            file_name = os.path.basename(file_path)
            self.json_files[file_path] = {
                'name': file_name,
                'current_hash': self._calculate_hash(content),
                'last_modified': os.path.getmtime(file_path)
            }
            
            self.log_sync(file_path, 'ADD', 'SUCCESS', '文件已添加监控')
            return True
        except Exception as e:
            self.log_sync(file_path, 'ADD', 'FAILED', str(e))
            return False
    
    def remove_json_file(self, file_path: str) -> bool:
        """移除监控的JSON文件"""
        if file_path in self.json_files:
            del self.json_files[file_path]
            self.log_sync(file_path, 'REMOVE', 'SUCCESS', '文件已移除监控')
            return True
        return False
    
    def sync_single_file(self, file_path: str) -> bool:
        """同步单个JSON文件到数据库"""
        if file_path not in self.json_files:
            return False
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.log_sync(file_path, 'SYNC', 'FAILED', '文件不存在')
                return False
            
            # 读取文件内容
            with open(file_path, 'r') as f:
                content = f.read()
            
            # 解析JSON确保格式正确
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.log_sync(file_path, 'SYNC', 'FAILED', f'JSON格式错误: {e}')
                return False
            
            # 计算哈希值
            content_hash = self._calculate_hash(content)
            last_modified = os.path.getmtime(file_path)
            
            # 检查是否有变化
            if content_hash == self.json_files[file_path]['current_hash']:
                return True
            
            # 加密内容
            encrypted_content = self._encrypt_content(content)
            
            # 获取当前版本
            file_name = os.path.basename(file_path)
            current_version = self._get_current_version(file_name)
            
            # 保存到数据库
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO json_data 
                    (file_name, encrypted_content, content_hash, last_modified, 
                     sync_time, version, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (file_name, encrypted_content, content_hash, 
                      last_modified, datetime.now(), current_version + 1, datetime.now()))
                
                conn.commit()
            
            # 更新缓存
            self.json_files[file_path]['current_hash'] = content_hash
            self.json_files[file_path]['last_modified'] = last_modified
            self.last_sync_times[file_path] = time.time()
            
            self.log_sync(file_path, 'SYNC', 'SUCCESS', f'同步成功,版本: {current_version + 1}')
            return True
        
        except Exception as e:
            self.log_sync(file_path, 'SYNC', 'FAILED', str(e))
            return False
    
    def _get_current_version(self, file_name: str) -> int:
        """获取当前版本号"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version FROM json_data WHERE file_name = ?', (file_name,))
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def sync_all_files(self) -> int:
        """同步所有监控的JSON文件"""
        success_count = 0
        for file_path in self.json_files.keys():
            if self.sync_single_file(file_path):
                success_count += 1
        return success_count
    
    def log_sync(self, file_path: str, action: str, status: str, message: str = ""):
        """记录同步日志"""
        file_name = os.path.basename(file_path) if file_path else ""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO json_sync_logs (file_name, action, status, message, sync_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (file_name, action, status, message, datetime.now()))
                conn.commit()
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def start_monitoring(self):
        """开始监控JSON文件变化"""
        self.is_running = True
        
        def monitor_loop():
            while self.is_running:
                try:
                    self.sync_all_files()
                except Exception as e:
                    print(f"监控循环错误: {e}")
                time.sleep(self.sync_interval)
        
        self.sync_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.sync_thread.start()
        
        self.log_sync('', 'MONITOR', 'STARTED', 'JSON监控服务已启动')
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join()
        self.log_sync('', 'MONITOR', 'STOPPED', 'JSON监控服务已停止')
    
    def get_stored_json(self, file_name: str) -> Optional[Dict]:
        """从数据库获取解密后的JSON数据"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT encrypted_content FROM json_data WHERE file_name = ?', (file_name,))
                row = cursor.fetchone()
                
                if row:
                    decrypted = self._decrypt_content(row[0])
                    return json.loads(decrypted)
                return None
        except Exception as e:
            print(f"获取JSON数据失败: {e}")
            return None
    
    def list_stored_files(self) -> list:
        """列出数据库中存储的所有JSON文件"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT file_name, version, sync_time FROM json_data ORDER BY sync_time DESC')
                
                return [{
                    'file_name': row[0],
                    'version': row[1],
                    'last_sync': row[2]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"列出文件失败: {e}")
            return []
    
    def get_sync_logs(self, limit: int = 50) -> list:
        """获取同步日志"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT file_name, action, status, message, sync_time 
                    FROM json_sync_logs ORDER BY sync_time DESC LIMIT ?
                ''', (limit,))
                
                return [{
                    'file_name': row[0],
                    'action': row[1],
                    'status': row[2],
                    'message': row[3],
                    'sync_time': row[4]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取日志失败: {e}")
            return []

# 全局实例
json_sync_manager = None

def get_json_sync_manager():
    """获取JSON同步管理器实例"""
    global json_sync_manager
    if json_sync_manager is None:
        json_sync_manager = JSONSyncManager()
    return json_sync_manager

if __name__ == "__main__":
    manager = JSONSyncManager()
    
    print("=== JSON加密同步测试 ===")
    
    # 创建测试JSON文件
    test_json = {
        'name': '测试数据',
        'version': 1,
        'data': [1, 2, 3],
        'timestamp': datetime.now().isoformat()
    }
    
    test_file = 'test_data.json'
    with open(test_file, 'w') as f:
        json.dump(test_json, f, ensure_ascii=False, indent=2)
    
    # 添加监控
    manager.add_json_file(test_file)
    print(f"已添加监控文件: {test_file}")
    
    # 同步到数据库
    manager.sync_single_file(test_file)
    print("已同步到数据库")
    
    # 从数据库读取
    stored_data = manager.get_stored_json(test_file)
    print(f"从数据库读取: {stored_data}")
    
    # 更新JSON文件
    test_json['version'] = 2
    test_json['timestamp'] = datetime.now().isoformat()
    with open(test_file, 'w') as f:
        json.dump(test_json, f, ensure_ascii=False, indent=2)
    
    # 再次同步
    manager.sync_single_file(test_file)
    print("更新后再次同步")
    
    # 检查版本
    stored_data = manager.get_stored_json(test_file)
    print(f"更新后的版本: {stored_data}")
    
    # 列出存储的文件
    files = manager.list_stored_files()
    print(f"\n数据库中的JSON文件:")
    for f in files:
        print(f"  - {f['file_name']} (版本: {f['version']})")
    
    # 获取日志
    logs = manager.get_sync_logs(5)
    print(f"\n最近的同步日志:")
    for log in logs:
        print(f"  [{log['sync_time']}] {log['action']} {log['file_name']}: {log['status']}")
    
    # 清理测试文件
    os.remove(test_file)
    
    logger.info("\n == 测试完成 ===")
