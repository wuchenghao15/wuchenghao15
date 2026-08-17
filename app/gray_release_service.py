#!/usr/bin/env python3
"""
灰度发布服务
实现灰度发布、渐进式发布、自动回滚等功能
"""

import os
import sqlite3
import logging
import time
import json
from datetime import datetime
from typing import Dict, Optional, List, Set

logger = logging.getLogger(__name__)

class GrayReleaseService:
    """灰度发布服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.percentage = self.config.get('percentage', 10)
        self.user_list = self.config.get('user_list', '')
        self.rollback_on_error = self.config.get('rollback_on_error', True)
        self.error_threshold = self.config.get('error_threshold', 5)
        self.gradual_enabled = self.config.get('gradual_enabled', True)
        self.gradual_steps = self.config.get('gradual_steps', 5)
        self.gradual_interval = self.config.get('gradual_interval', 3600)
        self.monitor_enabled = self.config.get('monitor_enabled', True)
        
        self._current_step = 0
        self._current_percentage = 0
        self._release_active = False
        self._error_count = 0
        self._total_requests = 0
        self._gray_users: Set[str] = set()
        
        self._init_gray_users()
        self._init_database()
    
    def _init_gray_users(self):
        """初始化灰度用户列表"""
        if self.user_list:
            self._gray_users = set(self.user_list.split(','))
    
    def _init_database(self):
        """初始化数据库表"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gray_release_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                release_version TEXT NOT NULL,
                release_status TEXT DEFAULT "pending",
                current_step INTEGER DEFAULT 0,
                current_percentage INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                gray_users TEXT,
                start_time TEXT,
                end_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _calculate_percentage(self, step: int) -> int:
        """计算当前步骤的灰度比例"""
        if step >= self.gradual_steps:
            return 100
        return min(100, int((step + 1) * (100 / self.gradual_steps)))
    
    def _should_rollback(self) -> bool:
        """判断是否需要回滚"""
        if not self.rollback_on_error:
            return False
        
        if self._total_requests == 0:
            return False
        
        error_rate = (self._error_count / self._total_requests) * 100
        return error_rate >= self.error_threshold
    
    def start_release(self, version: str, user_ids: Optional[List[str]] = None):
        """开始灰度发布"""
        if not self.enabled:
            logger.info("灰度发布未启用")
            return
        
        logger.info(f"开始灰度发布，版本: {version}")
        
        if user_ids:
            self._gray_users = set(user_ids)
        
        self._release_active = True
        self._current_step = 0
        self._current_percentage = self.percentage
        self._error_count = 0
        self._total_requests = 0
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO gray_release_records 
            (release_version, release_status, current_step, current_percentage, 
             gray_users, start_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (version, 'active', 0, self._current_percentage, 
              json.dumps(list(self._gray_users)), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"灰度发布已启动，当前比例: {self._current_percentage}%")
    
    def advance_step(self):
        """推进到下一步"""
        if not self._release_active or not self.gradual_enabled:
            return
        
        if self._current_step >= self.gradual_steps:
            logger.info("已达到最大步骤，发布完成")
            self._release_active = False
            return
        
        self._current_step += 1
        self._current_percentage = self._calculate_percentage(self._current_step)
        
        logger.info(f"推进到步骤 {self._current_step}/{self.gradual_steps}，比例: {self._current_percentage}%")
        
        if self._current_percentage >= 100:
            self.complete_release()
    
    def rollback(self):
        """回滚发布"""
        logger.warning("执行灰度发布回滚")
        
        self._release_active = False
        self._current_percentage = 0
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE gray_release_records 
            SET release_status = 'rolled_back', end_time = ? 
            WHERE release_status = 'active'
        ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
        
        logger.info("灰度发布已回滚")
    
    def complete_release(self):
        """完成发布"""
        logger.info("完成灰度发布")
        
        self._release_active = False
        self._current_percentage = 100
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE gray_release_records 
            SET release_status = 'completed', end_time = ?, current_percentage = 100 
            WHERE release_status = 'active'
        ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
        
        logger.info("灰度发布已完成，全量上线")
    
    def is_gray_user(self, user_id: str) -> bool:
        """判断用户是否为灰度用户"""
        if not self.enabled or not self._release_active:
            return False
        
        if self._current_percentage >= 100:
            return True
        
        if self._gray_users and user_id in self._gray_users:
            return True
        
        user_hash = hash(user_id)
        threshold = int((self._current_percentage / 100) * 1000000)
        return (user_hash % 1000000) < threshold
    
    def record_request(self, user_id: str, success: bool):
        """记录请求"""
        if not self.enabled or not self._release_active:
            return
        
        self._total_requests += 1
        if not success:
            self._error_count += 1
        
        if self.monitor_enabled:
            error_rate = (self._error_count / self._total_requests) * 100
            logger.info(f"灰度发布监控 - 请求数: {self._total_requests}, 错误数: {self._error_count}, 错误率: {error_rate:.2f}%")
        
        if self._should_rollback():
            logger.warning(f"错误率 {error_rate:.2f}% 超过阈值 {self.error_threshold}%，触发自动回滚")
            self.rollback()
    
    def get_release_status(self) -> Dict:
        """获取发布状态"""
        return {
            'enabled': self.enabled,
            'release_active': self._release_active,
            'current_step': self._current_step,
            'current_percentage': self._current_percentage,
            'error_count': self._error_count,
            'total_requests': self._total_requests,
            'gradual_steps': self.gradual_steps,
            'gradual_interval': self.gradual_interval
        }

gray_release_service = GrayReleaseService()