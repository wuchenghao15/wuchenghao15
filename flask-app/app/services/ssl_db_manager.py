import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
SSL与数据库绑定服务
将SSL证书信息存储到数据库,实现证书的持久化管理
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional

class SSLDBManager:
    """SSL数据库管理器"""
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化SSL相关数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # SSL证书配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ssl_certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cert_name TEXT UNIQUE NOT NULL,
                    cert_type TEXT DEFAULT 'self_signed',
                    cert_pem TEXT,
                    key_pem TEXT,
                    ca_cert_pem TEXT,
                    common_name TEXT,
                    issuer TEXT,
                    not_before TEXT,
                    not_after TEXT,
                    days_remaining INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # SSL配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ssl_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # SSL日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ssl_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT,
                    cert_name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_certificate(self, cert_name: str, cert_pem: str, key_pem: str, 
                        common_name: str = "localhost", issuer: str = "",
                        not_before: str = "", not_after: str = "", days_remaining: int = 0) -> bool:
        """保存证书到数据库"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ssl_certificates 
                    (cert_name, cert_type, cert_pem, key_pem, common_name, issuer, 
                     not_before, not_after, days_remaining, is_active, updated_at)
                    VALUES (?, 'self_signed', ?, ?, ?, ?, ?, ?, ?, TRUE, ?)
                ''', (cert_name, cert_pem, key_pem, common_name, issuer, 
                      not_before, not_after, days_remaining, datetime.now()))
                
                conn.commit()
                
                self.log('INFO', f"证书 '{cert_name}' 已保存到数据库")
                return True
        except Exception as e:
            self.log('ERROR', f"保存证书失败: {str(e)}")
            return False
    
    def load_certificate(self, cert_name: str) -> Optional[Dict]:
        """从数据库加载证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT cert_pem, key_pem, common_name, issuer, not_before, 
                           not_after, days_remaining, is_active, created_at
                    FROM ssl_certificates WHERE cert_name = ? AND is_active = TRUE
                ''', (cert_name,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'cert_pem': row[0],
                        'key_pem': row[1],
                        'common_name': row[2],
                        'issuer': row[3],
                        'not_before': row[4],
                        'not_after': row[5],
                        'days_remaining': row[6],
                        'is_active': bool(row[7]),
                        'created_at': row[8]
                    }
                return None
        except Exception as e:
            self.log('ERROR', f"加载证书失败: {str(e)}")
            return None
    
    def delete_certificate(self, cert_name: str) -> bool:
        """删除证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE ssl_certificates SET is_active = FALSE, updated_at = ? 
                    WHERE cert_name = ?
                ''', (datetime.now(), cert_name))
                
                conn.commit()
                
                self.log('INFO', f"证书 '{cert_name}' 已标记为禁用")
                return cursor.rowcount > 0
        except Exception as e:
            self.log('ERROR', f"删除证书失败: {str(e)}")
            return False
    
    def list_certificates(self) -> list:
        """列出所有证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT cert_name, cert_type, common_name, not_after, days_remaining, is_active
                    FROM ssl_certificates ORDER BY created_at DESC
                ''')
                
                return [{
                    'cert_name': row[0],
                    'cert_type': row[1],
                    'common_name': row[2],
                    'not_after': row[3],
                    'days_remaining': row[4],
                    'is_active': bool(row[5])
                } for row in cursor.fetchall()]
        except Exception as e:
            self.log('ERROR', f"列出证书失败: {str(e)}")
            return []
    
    def save_setting(self, key: str, value, description: str = "") -> bool:
        """保存SSL配置"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ssl_settings 
                    (setting_key, setting_value, description, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (key, value_str, description, datetime.now()))
                
                conn.commit()
                return True
        except Exception as e:
            self.log('ERROR', f"保存配置失败: {str(e)}")
            return False
    
    def load_setting(self, key: str, default=None):
        """加载SSL配置"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT setting_value FROM ssl_settings WHERE setting_key = ?', (key,))
                
                row = cursor.fetchone()
                if row:
                    try:
                        return json.loads(row[0])
                    except ValueError:
                        return row[0]
                return default
        except Exception as e:
            self.log('ERROR', f"加载配置失败: {str(e)}")
            return default
    
    def log(self, level: str, message: str, cert_name: str = ""):
        """记录SSL日志"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ssl_logs (level, message, cert_name, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (level, message, cert_name, datetime.now()))
                
                conn.commit()
        except Exception as e:
            print(f"记录SSL日志失败: {e}")
    
    def get_logs(self, limit: int = 50) -> list:
        """获取SSL日志"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT level, message, cert_name, created_at 
                    FROM ssl_logs ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                
                return [{
                    'level': row[0],
                    'message': row[1],
                    'cert_name': row[2],
                    'created_at': row[3]
                } for row in cursor.fetchall()]
        except Exception as e:
            return []
    
    def export_certificate(self, cert_name: str, export_dir: str = "ssl") -> bool:
        """从数据库导出证书到文件"""
        cert = self.load_certificate(cert_name)
        if not cert:
            return False
        
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            cert_path = os.path.join(export_dir, f"{cert_name}.pem")
            key_path = os.path.join(export_dir, f"{cert_name}_key.pem")
            
            with open(cert_path, "w") as f:
                f.write(cert['cert_pem'])
            
            with open(key_path, "w") as f:
                f.write(cert['key_pem'])
            
            os.chmod(cert_path, 0o644)
            os.chmod(key_path, 0o600)
            
            self.log('INFO', f"证书 '{cert_name}' 已导出到 {export_dir}")
            return True
        except Exception as e:
            self.log('ERROR', f"导出证书失败: {str(e)}")
            return False
    
    def import_certificate_from_db(self, cert_name: str, ssl_dir: str = "ssl") -> bool:
        """从数据库导入证书到文件系统"""
        return self.export_certificate(cert_name, ssl_dir)
    
    def sync_certificates(self):
        """同步文件系统和数据库中的证书"""
        try:
            ssl_dir = "ssl"
            if os.path.exists(ssl_dir):
                cert_path = os.path.join(ssl_dir, "cert.pem")
                key_path = os.path.join(ssl_dir, "key.pem")
                
                if os.path.exists(cert_path) and os.path.exists(key_path):
                    with open(cert_path, "r") as f:
                        cert_pem = f.read()
                    
                    with open(key_path, "r") as f:
                        key_pem = f.read()
                    
                    self.save_certificate("default", cert_pem, key_pem)
                    self.log('INFO', "已从文件系统同步证书: default")
            
            self.log('INFO', "证书同步完成")
            return True
        except Exception as e:
            self.log('ERROR', f"同步证书失败: {str(e)}")
            return False

# 全局实例
ssl_db_manager = None

def get_ssl_db_manager():
    """获取SSL数据库管理器实例"""
    global ssl_db_manager
    if ssl_db_manager is None:
        ssl_db_manager = SSLDBManager()
    return ssl_db_manager

if __name__ == "__main__":
    manager = SSLDBManager()
    
    # 同步证书
    manager.sync_certificates()
    
    # 列出所有证书
    certs = manager.list_certificates()
    print("数据库中的证书:")
    for cert in certs:
        print(f"  - {cert['cert_name']}: {cert['common_name']} (有效期剩余: {cert['days_remaining']}天)")
    
    # 获取日志
    logs = manager.get_logs(10)
    print("\n最近的SSL日志:")
    for log in logs:
        logger.info(f"  [{log['level']}] {log['message']}")
