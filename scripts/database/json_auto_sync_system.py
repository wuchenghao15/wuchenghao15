#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS JSON自动同步系统
监控和同步所有JSON文件到数据库
"""

import os
import json
import time
import threading
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class JSONFileHandler(FileSystemEventHandler):
    """JSON文件变化处理器"""
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and event.src_path.endswith('.json'):
            print(f"检测到文件变化: {event.src_path}")
            self.sync_manager.on_file_changed(event.src_path)
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and event.src_path.endswith('.json'):
            print(f"检测到新文件: {event.src_path}")
            self.sync_manager.on_file_created(event.src_path)

class EnhancedJSONSyncManager:
    """增强的JSON同步管理器"""
    
    def __init__(self, db_path: str = "json_sync.db", project_root: str = None):
        self.db_path = db_path
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.json_files = {}
        self.last_sync_times = {}
        self.sync_interval = 10
        self.is_running = False
        self.sync_thread = None
        self.observer = None
        self.event_handler = None
        self._init_tables()
        
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_sync_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    directory TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    sync_enabled BOOLEAN DEFAULT 1,
                    last_sync TEXT,
                    last_modified REAL,
                    content_hash TEXT,
                    version INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_sync_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    sync_time TEXT NOT NULL,
                    version INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    sync_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希值"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def scan_directory(self, directory: str = None, recursive: bool = True):
        """扫描目录中的JSON文件"""
        scan_dir = directory or self.project_root
        print(f"正在扫描目录: {scan_dir}")
        
        found_count = 0
        for root, dirs, files in os.walk(scan_dir):
            # 跳过某些目录
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    self.register_json_file(file_path)
                    found_count += 1
        
        print(f"扫描完成，发现 {found_count} 个JSON文件")
        return found_count
    
    def register_json_file(self, file_path: str):
        """注册JSON文件到数据库"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_name = os.path.basename(file_path)
            directory = os.path.dirname(file_path)
            content_hash = self._calculate_hash(content)
            last_modified = os.path.getmtime(file_path)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO json_sync_config 
                    (file_path, file_name, directory, content_hash, last_modified, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_path, file_name, directory, content_hash, last_modified, datetime.now().isoformat()))
                conn.commit()
            
            self.json_files[file_path] = {
                'file_name': file_name,
                'file_path': file_path,
                'content_hash': content_hash,
                'last_modified': last_modified
            }
            
            self.log_sync(file_path, 'REGISTER', 'SUCCESS', '文件已注册')
            return True
        except Exception as e:
            print(f"注册JSON文件失败: {e}")
            self.log_sync(file_path, 'REGISTER', 'FAILED', str(e))
            return False
    
    def on_file_changed(self, file_path: str):
        """文件变化回调"""
        self.sync_file(file_path)
    
    def on_file_created(self, file_path: str):
        """文件创建回调"""
        self.register_json_file(file_path)
        self.sync_file(file_path)
    
    def sync_file(self, file_path: str) -> bool:
        """同步单个文件到数据库"""
        try:
            if not os.path.exists(file_path):
                self.log_sync(file_path, 'SYNC', 'FAILED', '文件不存在')
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.log_sync(file_path, 'SYNC', 'FAILED', f'JSON格式错误: {e}')
                return False
            
            content_hash = self._calculate_hash(content)
            last_modified = os.path.getmtime(file_path)
            
            current_version = self._get_current_version(file_path)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO json_sync_data 
                    (file_path, file_name, content, content_hash, version, sync_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_path, os.path.basename(file_path), 
                      content, content_hash, current_version + 1, datetime.now().isoformat()))
                
                cursor.execute('''
                    UPDATE json_sync_config 
                    SET last_sync = ?, content_hash = ?, last_modified = ?, version = ?, updated_at = ?
                    WHERE file_path = ?
                ''', (datetime.now().isoformat(), content_hash, last_modified, current_version + 1, datetime.now().isoformat(), file_path))
                
                conn.commit()
            
            self.log_sync(file_path, 'SYNC', 'SUCCESS', f'同步成功,版本: {current_version + 1}')
            return True
        
        except Exception as e:
            self.log_sync(file_path, 'SYNC', 'FAILED', str(e))
            return False
    
    def _get_current_version(self, file_path: str) -> int:
        """获取当前版本号"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version FROM json_sync_config WHERE file_path = ?', (file_path,))
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def sync_all_files(self) -> int:
        """同步所有注册的文件"""
        success_count = 0
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT file_path FROM json_sync_config WHERE sync_enabled = 1')
                files = cursor.fetchall()
                
                for (file_path,) in files:
                    if self.sync_file(file_path):
                        success_count += 1
        except Exception as e:
            print(f"批量同步失败: {e}")
        
        return success_count
    
    def start_file_monitoring(self, directories: List[str] = None):
        """启动文件监控"""
        self.is_running = True
        self.event_handler = JSONFileHandler(self)
        self.observer = Observer()
        
        monitor_dirs = directories or [self.project_root]
        
        for dir_path in monitor_dirs:
            if os.path.exists(dir_path):
                self.observer.schedule(self.event_handler, dir_path, recursive=True)
                print(f"开始监控目录: {dir_path}")
        
        self.observer.start()
        self.log_sync('', 'MONITOR', 'STARTED', '文件监控已启动')
    
    def stop_file_monitoring(self):
        """停止文件监控"""
        self.is_running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.log_sync('', 'MONITOR', 'STOPPED', '文件监控已停止')
    
    def start_periodic_sync(self):
        """启动定期同步"""
        self.is_running = True
        
        def sync_loop():
            while self.is_running:
                try:
                    self.sync_all_files()
                except Exception as e:
                    print(f"定期同步错误: {e}")
                time.sleep(self.sync_interval)
        
        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        print(f"定期同步已启动，间隔: {self.sync_interval}秒")
    
    def stop_periodic_sync(self):
        """停止定期同步"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join()
    
    def log_sync(self, file_path: str, action: str, status: str, message: str = ""):
        """记录同步日志"""
        try:
            file_name = os.path.basename(file_path) if file_path else ""
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO json_sync_logs (file_path, file_name, action, status, message, sync_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_path, file_name, action, status, message, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def get_sync_logs(self, limit: int = 100) -> List[Dict]:
        """获取同步日志"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT file_path, file_name, action, status, message, sync_time 
                    FROM json_sync_logs ORDER BY sync_time DESC LIMIT ?
                ''', (limit,))
                
                return [{
                    'file_path': row[0],
                    'file_name': row[1],
                    'action': row[2],
                    'status': row[3],
                    'message': row[4],
                    'sync_time': row[5]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取日志失败: {e}")
            return []
    
    def get_registered_files(self) -> List[Dict]:
        """获取已注册的文件列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT file_path, file_name, directory, last_sync, version 
                    FROM json_sync_config ORDER BY updated_at DESC
                ''')
                
                return [{
                    'file_path': row[0],
                    'file_name': row[1],
                    'directory': row[2],
                    'last_sync': row[3],
                    'version': row[4]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取文件列表失败: {e}")
            return []
    
    def get_json_content(self, file_path: str, version: int = None) -> Optional[Dict]:
        """从数据库获取JSON内容"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if version:
                    cursor.execute('''
                        SELECT content FROM json_sync_data WHERE file_path = ? AND version = ?
                    ''', (file_path, version))
                else:
                    cursor.execute('''
                        SELECT content FROM json_sync_data 
                        WHERE file_path = ? ORDER BY version DESC LIMIT 1
                    ''', (file_path,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
        except Exception as e:
            print(f"获取JSON内容失败: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """获取同步统计信息"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM json_sync_config')
                total_files = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM json_sync_config WHERE last_sync IS NOT NULL')
                synced_files = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM json_sync_data')
                total_versions = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM json_sync_logs WHERE status = 'SUCCESS'
                ''')
                success_count = cursor.fetchone()[0]
                
                return {
                    'total_files': total_files,
                    'synced_files': synced_files,
                    'total_versions': total_versions,
                    'success_count': success_count
                }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}

class JSONSyncAPI:
    """JSON同步API集成"""
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
    
    def register_flask_routes(self, app):
        """注册Flask路由"""
        from flask import jsonify, request
        
        @app.route('/api/json-sync/status', methods=['GET'])
        def get_sync_status():
            stats = self.sync_manager.get_statistics()
            return jsonify({'success': True, 'data': stats})
        
        @app.route('/api/json-sync/files', methods=['GET'])
        def list_files():
            files = self.sync_manager.get_registered_files()
            return jsonify({'success': True, 'data': files})
        
        @app.route('/api/json-sync/logs', methods=['GET'])
        def get_logs():
            limit = request.args.get('limit', 50, type=int)
            logs = self.sync_manager.get_sync_logs(limit)
            return jsonify({'success': True, 'data': logs})
        
        @app.route('/api/json-sync/sync', methods=['POST'])
        def trigger_sync():
            count = self.sync_manager.sync_all_files()
            return jsonify({'success': True, 'synced_files': count})
        
        @app.route('/api/json-sync/scan', methods=['POST'])
        def scan_files():
            count = self.sync_manager.scan_directory()
            return jsonify({'success': True, 'found_files': count})
        
        @app.route('/api/json-sync/file/<path:file_path>', methods=['GET'])
        def get_file_content(file_path):
            version = request.args.get('version', type=int)
            content = self.sync_manager.get_json_content(file_path, version)
            if content:
                return jsonify({'success': True, 'data': content})
            return jsonify({'success': False, 'error': '文件不存在'}), 404

def main():
    """主函数"""
    print("=" * 60)
    print("MTSCOS JSON自动同步系统")
    print("=" * 60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    sync_manager = EnhancedJSONSyncManager(db_path="mtcos_json_sync.db", project_root=project_root)
    
    # 扫描目录
    print("\n正在扫描JSON文件...")
    found_count = sync_manager.scan_directory()
    
    if found_count > 0:
        print(f"发现 {found_count} 个JSON文件")
        
        # 初始同步
        print("\n正在执行初始同步...")
        synced_count = sync_manager.sync_all_files()
        print(f"同步完成: {synced_count} 个文件")
    
    # 显示统计
    stats = sync_manager.get_statistics()
    print("\n同步统计:")
    print(f"  - 总文件: {stats.get('total_files', 0)}")
    print(f"  - 已同步: {stats.get('synced_files', 0)}")
    print(f"  - 版本总数: {stats.get('total_versions', 0)}")
    print(f"  - 成功次数: {stats.get('success_count', 0)}")
    
    # 启动监控
    print("\n启动文件监控...")
    sync_manager.start_file_monitoring()
    
    print("\n启动定期同步...")
    sync_manager.start_periodic_sync()
    
    print("\n" + "=" * 60)
    print("JSON同步系统已启动!")
    print("按 Ctrl+C 停止")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        sync_manager.stop_file_monitoring()
        sync_manager.stop_periodic_sync()
        print("已停止")

if __name__ == "__main__":
    main()
