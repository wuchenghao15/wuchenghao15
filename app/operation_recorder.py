#!/usr/bin/env python3
"""
操作记录服务
记录操作到数据库和日志文件
"""

import os
import sqlite3
import logging
import json
import time
import shutil
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class OperationRecorder:
    """操作记录服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.to_database = self.config.get('to_database', True)
        self.to_file = self.config.get('to_file', True)
        self.log_level = self.config.get('log_level', 'INFO')
        self.retention_days = self.config.get('retention_days', 30)
        self.max_size = self.config.get('max_size', 104857600)
        
        self._log_file = None
        self._setup_logging()
        self._init_database()
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file_path = os.path.join(log_dir, 'operations.log')
        
        handler = logging.FileHandler(log_file_path, encoding='utf-8')
        handler.setLevel(self.log_level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(self.log_level)
        
        self._log_file = log_file_path
    
    def _init_database(self):
        """初始化数据库表"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                user_id TEXT,
                user_name TEXT,
                module TEXT,
                action TEXT,
                details TEXT,
                result TEXT DEFAULT "success",
                error_message TEXT,
                ip_address TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _cleanup_old_logs(self):
        """清理旧日志"""
        cutoff_time = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM operation_logs WHERE timestamp < ?', (cutoff_time,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"清理了 {deleted_count} 条旧操作记录")
        
        if self._log_file and os.path.exists(self._log_file):
            file_size = os.path.getsize(self._log_file)
            if file_size >= self.max_size:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = self._log_file + f'.{timestamp}'
                shutil.copy2(self._log_file, backup_file)
                with open(self._log_file, 'w') as f:
                    f.write('')
                logger.info(f"日志文件已备份并重置: {backup_file}")
    
    def record(self, operation_type: str, user_id: str = '', user_name: str = '', 
               module: str = '', action: str = '', details: str = '', 
               result: str = 'success', error_message: str = '', ip_address: str = ''):
        """记录操作"""
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        if self.to_file:
            log_message = f"[{operation_type}] 用户:{user_name}({user_id}) 模块:{module} 操作:{action} 结果:{result}"
            if details:
                log_message += f" 详情:{details}"
            if error_message:
                log_message += f" 错误:{error_message}"
            
            if result == 'success':
                logger.info(log_message)
            else:
                logger.error(log_message)
        
        if self.to_database:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO operation_logs 
                (operation_type, user_id, user_name, module, action, details, result, error_message, ip_address,
                timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (operation_type, user_id, user_name, module, action, details, result, error_message, ip_address,
            timestamp))
            
            conn.commit()
            conn.close()
    
    def record_login(self, user_id: str, user_name: str, ip_address: str = '', success: bool = True):
        """记录登录操作"""
        self.record(
            operation_type='login',
            user_id=user_id,
            user_name=user_name,
            module='auth',
            action='login',
            result='success' if success else 'failed',
            ip_address=ip_address
        )
    
    def record_logout(self, user_id: str, user_name: str):
        """记录登出操作"""
        self.record(
            operation_type='logout',
            user_id=user_id,
            user_name=user_name,
            module='auth',
            action='logout'
        )
    
    def record_create(self, user_id: str, user_name: str, module: str, details: str = ''):
        """记录创建操作"""
        self.record(
            operation_type='create',
            user_id=user_id,
            user_name=user_name,
            module=module,
            action='create',
            details=details
        )
    
    def record_update(self, user_id: str, user_name: str, module: str, details: str = ''):
        """记录更新操作"""
        self.record(
            operation_type='update',
            user_id=user_id,
            user_name=user_name,
            module=module,
            action='update',
            details=details
        )
    
    def record_delete(self, user_id: str, user_name: str, module: str, details: str = ''):
        """记录删除操作"""
        self.record(
            operation_type='delete',
            user_id=user_id,
            user_name=user_name,
            module=module,
            action='delete',
            details=details
        )
    
    def record_error(self, user_id: str, user_name: str, module: str, error_message: str = ''):
        """记录错误操作"""
        self.record(
            operation_type='error',
            user_id=user_id,
            user_name=user_name,
            module=module,
            action='error',
            result='failed',
            error_message=error_message
        )
    
    def get_records(self, operation_type: str = None, user_id: str = None, 
                    module: str = None, start_time: str = None, end_time: str = None,
                    limit: int = 100, offset: int = 0) -> List[Dict]:
        """查询操作记录"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM operation_logs WHERE 1=1'
        params = []
        
        if operation_type:
            query += ' AND operation_type = ?'
            params.append(operation_type)
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        if module:
            query += ' AND module = ?'
            params.append(module)
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)
        
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'operation_type': row[1],
            'user_id': row[2],
            'user_name': row[3],
            'module': row[4],
            'action': row[5],
            'details': row[6],
            'result': row[7],
            'error_message': row[8],
            'ip_address': row[9],
            'timestamp': row[10]
        } for row in rows]

operation_recorder = OperationRecorder()