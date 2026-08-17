#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS系统备份服务
提供数据库备份、文件备份和恢复功能
"""

import os
import sys
import json
import time
import zipfile
import shutil
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self.is_running = False
        self.backup_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'backup_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'backup_dir': 'backups',
            'auto_backup_enabled': True,
            'auto_backup_interval': 3600,
            'backup_retention_days': 7,
            'max_backups': 30,
            'compress_backups': True,
            'include_database': True,
            'include_files': True,
            'include_config': True,
            'backup_time': '02:00'
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'backup_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        os.makedirs(self.config['backup_dir'], exist_ok=True)
    
    def _generate_backup_name(self) -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"backup_{timestamp}"
    
    def _backup_database(self, backup_path: str):
        """备份数据库"""
        db_path = 'app.db'
        
        if not os.path.exists(db_path):
            return
        
        try:
            conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(os.path.join(backup_path, 'app.db'))
            
            with backup_conn:
                conn.backup(backup_conn)
            
            conn.close()
            backup_conn.close()
            
            logger(f"[备份] 数据库备份完成")
        except Exception as e:
            logger(f"[备份] 数据库备份失败: {e}")
    
    def _backup_files(self, backup_path: str):
        """备份文件"""
        files_to_backup = [
            ('app.db', 'database/'),
            ('config', 'config/'),
            ('docs', 'docs/'),
            ('VERSION', 'root/'),
            ('requirements.txt', 'root/')
        ]
        
        for src, dest in files_to_backup:
            src_path = os.path.join(os.path.dirname(__file__), '..', src)
            dest_path = os.path.join(backup_path, dest)
            
            if os.path.exists(src_path):
                os.makedirs(dest_path, exist_ok=True)
                
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, os.path.join(dest_path, os.path.basename(src)), 
                                   dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dest_path)
        
        logger(f"[备份] 文件备份完成")
    
    def _backup_config(self, backup_path: str):
        """备份配置文件"""
        config_dir = os.path.dirname(__file__)
        config_files = [f for f in os.listdir(config_dir) if f.endswith('_config.json')]
        
        config_path = os.path.join(backup_path, 'config')
        os.makedirs(config_path, exist_ok=True)
        
        for config_file in config_files:
            src = os.path.join(config_dir, config_file)
            dest = os.path.join(config_path, config_file)
            
            if os.path.exists(src):
                shutil.copy2(src, dest)
        
        logger(f"[备份] 配置文件备份完成")
    
    def _compress_backup(self, backup_path: str) -> str:
        """压缩备份"""
        zip_path = f"{backup_path}.zip"
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            shutil.rmtree(backup_path)
            logger(f"[备份] 压缩完成: {zip_path}")
            
            return zip_path
        except Exception as e:
            logger(f"[备份] 压缩失败: {e}")
            return backup_path
    
    def create_backup(self, description: str = None) -> str:
        """创建备份"""
        self._ensure_backup_dir()
        
        backup_name = self._generate_backup_name()
        backup_path = os.path.join(self.config['backup_dir'], backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        logger(f"[备份] 开始创建备份: {backup_name}")
        
        if self.config['include_database']:
            self._backup_database(backup_path)
        
        if self.config['include_files']:
            self._backup_files(backup_path)
        
        if self.config['include_config']:
            self._backup_config(backup_path)
        
        backup_info = {
            'backup_name': backup_name,
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'size': 0,
            'compressed': False
        }
        
        if self.config['compress_backups']:
            backup_path = self._compress_backup(backup_path)
            backup_info['compressed'] = True
        
        backup_info['size'] = os.path.getsize(backup_path)
        
        info_file = f"{backup_path}.info"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        self._cleanup_old_backups()
        
        logger(f"[备份] 备份完成: {backup_path}")
        return backup_path
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        backup_dir = self.config['backup_dir']
        
        if not os.path.exists(backup_dir):
            return
        
        backup_files = []
        
        for f in os.listdir(backup_dir):
            if f.startswith('backup_'):
                filepath = os.path.join(backup_dir, f)
                mtime = os.path.getmtime(filepath)
                backup_files.append((filepath, mtime))
        
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        if len(backup_files) > self.config['max_backups']:
            for filepath, _ in backup_files[self.config['max_backups']:]:
                try:
                    if os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                    else:
                        os.remove(filepath)
                    
                    info_file = f"{filepath}.info"
                    if os.path.exists(info_file):
                        os.remove(info_file)
                except Exception as e:
                    logger(f"[备份] 清理备份失败: {e}")
        
        retention_days = self.config['backup_retention_days']
        cutoff_time = time.time() - retention_days * 24 * 3600
        
        for filepath, mtime in backup_files:
            if mtime < cutoff_time:
                try:
                    if os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                    else:
                        os.remove(filepath)
                    
                    info_file = f"{filepath}.info"
                    if os.path.exists(info_file):
                        os.remove(info_file)
                except Exception as e:
                    logger(f"[备份] 清理过期备份失败: {e}")
    
    def _auto_backup_loop(self):
        """自动备份循环"""
        while self.is_running:
            try:
                now = datetime.now()
                backup_time = self.config['backup_time']
                
                if now.hour == int(backup_time.split(':')[0]) and now.minute == int(backup_time.split(':')[1]):
                    self.create_backup(description="自动备份")
                
                time.sleep(self.config['auto_backup_interval'])
            except Exception as e:
                logger(f"[备份] 自动备份循环错误: {e}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """恢复备份"""
        logger(f"[备份] 开始恢复备份: {backup_path}")
        
        try:
            if backup_path.endswith('.zip'):
                extract_path = backup_path[:-4]
                
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                
                backup_path = extract_path
            
            db_src = os.path.join(backup_path, 'app.db')
            if os.path.exists(db_src):
                shutil.copy2(db_src, 'app.db')
                logger(f"[备份] 数据库恢复完成")
            
            config_src = os.path.join(backup_path, 'config')
            if os.path.exists(config_src):
                for f in os.listdir(config_src):
                    shutil.copy2(os.path.join(config_src, f), 
                                os.path.join(os.path.dirname(__file__), f))
                logger(f"[备份] 配置恢复完成")
            
            if backup_path.endswith('_extracted'):
                shutil.rmtree(backup_path)
            
            logger(f"[备份] 恢复完成")
            return True
        except Exception as e:
            logger(f"[备份] 恢复失败: {e}")
            return False
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """获取备份列表"""
        backup_dir = self.config['backup_dir']
        
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        
        for f in os.listdir(backup_dir):
            if f.startswith('backup_') and not f.endswith('.info'):
                filepath = os.path.join(backup_dir, f)
                info_file = f"{filepath}.info"
                
                info = {
                    'name': f,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'mtime': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                    'compressed': f.endswith('.zip')
                }
                
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f:
                        try:
                            info_data = json.load(f)
                            info.update(info_data)
                        except:
                            pass
                
                backups.append(info)
        
        backups.sort(key=lambda x: x['mtime'], reverse=True)
        return backups
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """获取备份信息"""
        backup_dir = self.config['backup_dir']
        
        for ext in ['', '.zip']:
            filepath = os.path.join(backup_dir, f"{backup_name}{ext}")
            info_file = f"{filepath}.info"
            
            if os.path.exists(filepath):
                info = {
                    'name': backup_name,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'mtime': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                    'compressed': bool(ext)
                }
                
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f:
                        try:
                            info_data = json.load(f)
                            info.update(info_data)
                        except:
                            pass
                
                return info
        
        return None
    
    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        backup_dir = self.config['backup_dir']
        
        for ext in ['', '.zip']:
            filepath = os.path.join(backup_dir, f"{backup_name}{ext}")
            
            if os.path.exists(filepath):
                try:
                    if os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                    else:
                        os.remove(filepath)
                    
                    info_file = f"{filepath}.info"
                    if os.path.exists(info_file):
                        os.remove(info_file)
                    
                    logger(f"[备份] 删除备份: {backup_name}")
                    return True
                except Exception as e:
                    logger(f"[备份] 删除备份失败: {e}")
        
        return False
    
    def start(self):
        """启动备份服务"""
        if self.is_running:
            return
        
        self.is_running = True
        
        if self.config['auto_backup_enabled']:
            self.backup_thread = threading.Thread(target=self._auto_backup_loop, daemon=True)
            self.backup_thread.start()
        
        logger(f"[备份] 系统备份服务已启动")
    
    def stop(self):
        """停止备份服务"""
        self.is_running = False
        if self.backup_thread:
            self.backup_thread.join()
        
        logger(f"[备份] 系统备份服务已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        backups = self.get_backups()
        
        return {
            'status': 'running' if self.is_running else 'stopped',
            'auto_backup_enabled': self.config['auto_backup_enabled'],
            'auto_backup_interval': self.config['auto_backup_interval'],
            'backup_time': self.config['backup_time'],
            'backup_retention_days': self.config['backup_retention_days'],
            'max_backups': self.config['max_backups'],
            'compress_backups': self.config['compress_backups'],
            'total_backups': len(backups),
            'last_backup': backups[0]['mtime'] if backups else None
        }

backup_manager = BackupManager()
