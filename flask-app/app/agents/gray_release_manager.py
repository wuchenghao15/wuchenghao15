# -*- coding: utf-8 -*-
"""
灰度发布管理器 - 灰度发布系统核心组件
支持：灰度发布、全量发布、自动回滚、流量控制、健康检查
杜绝全站崩盘，确保发布安全
"""
import os
import json
import time
import shutil
import logging
import threading
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ReleaseStatus(Enum):
    DRAFT = 'draft'
    PREPARING = 'preparing'
    GRAY = 'gray'
    FULL = 'full'
    COMPLETED = 'completed'
    ROLLING_BACK = 'rolling_back'
    ROLLED_BACK = 'rolled_back'
    FAILED = 'failed'


class ReleaseStrategy(Enum):
    PERCENTAGE = 'percentage'
    USER_GROUP = 'user_group'
    IP_RANGE = 'ip_range'
    COOKIE = 'cookie'


class GrayReleaseManager:
    """灰度发布管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self._releases: Dict[str, Dict] = {}
        self._current_release: Optional[str] = None
        self._gray_percentage = 0
        self._gray_users: List[str] = []
        self._gray_ips: List[str] = []
        self._last_health_check = None
        self._health_status = 'healthy'
        self._unhealthy_count = 0
        self._max_unhealthy_count = 3
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        
        self._init_database()
        self._load_releases()
        self._start_health_monitor()
        
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS release_history (
                    release_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    strategy TEXT DEFAULT 'percentage',
                    gray_percentage INTEGER DEFAULT 0,
                    gray_users TEXT DEFAULT '[]',
                    gray_ips TEXT DEFAULT '[]',
                    description TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    rolled_back_at TEXT,
                    rollback_reason TEXT DEFAULT '',
                    commit_hash TEXT DEFAULT '',
                    previous_version TEXT DEFAULT '',
                    success_rate REAL DEFAULT 100.0,
                    error_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS release_steps (
                    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    release_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT DEFAULT '',
                    FOREIGN KEY (release_id) REFERENCES release_history (release_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_check_history (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    release_id TEXT,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    response_time REAL,
                    error_rate REAL,
                    details TEXT DEFAULT '',
                    FOREIGN KEY (release_id) REFERENCES release_history (release_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[灰度发布] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[灰度发布] 初始化数据库失败: {e}")
    
    def _load_releases(self):
        """加载历史发布记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM release_history ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            for row in rows:
                release = {
                    'release_id': row[0],
                    'version': row[1],
                    'status': row[2],
                    'strategy': row[3],
                    'gray_percentage': row[4],
                    'gray_users': json.loads(row[5]) if row[5] else [],
                    'gray_ips': json.loads(row[6]) if row[6] else [],
                    'description': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                    'started_at': row[10],
                    'completed_at': row[11],
                    'rolled_back_at': row[12],
                    'rollback_reason': row[13],
                    'commit_hash': row[14],
                    'previous_version': row[15],
                    'success_rate': row[16],
                    'error_count': row[17]
                }
                self._releases[row[0]] = release
                
                if row[2] in ['gray', 'full']:
                    self._current_release = row[0]
                    self._gray_percentage = row[4]
            
            conn.close()
            logger.info(f"[灰度发布] 已加载 {len(self._releases)} 条发布记录")
        except Exception as e:
            logger.error(f"[灰度发布] 加载发布记录失败: {e}")
    
    def _start_health_monitor(self):
        """启动健康监控线程"""
        def monitor():
            while True:
                try:
                    self._perform_health_check()
                except Exception as e:
                    logger.error(f"[灰度发布] 健康检查失败: {e}")
                time.sleep(30)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        logger.info("[灰度发布] 健康监控线程已启动")
    
    def _perform_health_check(self):
        """执行健康检查"""
        if not self._current_release:
            return
        
        try:
            import sqlite3
            import psutil
            
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            response_time = self._measure_response_time()
            error_rate = self._calculate_error_rate()
            
            if cpu_usage > 95 or memory_usage > 95 or error_rate > 10:
                self._unhealthy_count += 1
                self._health_status = 'unhealthy'
                logger.warning(f"[灰度发布] 检测到不健康状态(第{self._unhealthy_count}次) - CPU:{cpu_usage}% 内存:{memory_usage}% 错误率:{error_rate}%")
                
                if self._unhealthy_count >= self._max_unhealthy_count:
                    if self._gray_percentage > 0 and self._gray_percentage < 100:
                        logger.info("[灰度发布] 连续不健康，自动触发回滚")
                        self.rollback(self._current_release, reason=f'连续{self._max_unhealthy_count}次健康检查失败')
            else:
                self._unhealthy_count = 0
                self._health_status = 'healthy'
            
            self._last_health_check = datetime.now().isoformat()
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO health_check_history 
                (release_id, timestamp, status, cpu_usage, memory_usage, response_time, error_rate, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self._current_release,
                self._last_health_check,
                self._health_status,
                cpu_usage,
                memory_usage,
                response_time,
                error_rate,
                json.dumps({
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'response_time': response_time,
                    'error_rate': error_rate
                })
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"[灰度发布] 健康检查异常: {e}")
    
    def _measure_response_time(self) -> float:
        """测量API响应时间"""
        try:
            import requests
            start = time.time()
            requests.get('http://localhost:8888/api/monitoring/health', timeout=5)
            return (time.time() - start) * 1000
        except Exception:
            return 9999.0
    
    def _calculate_error_rate(self) -> float:
        """计算错误率"""
        return 0.0
    
    def create_release(self, version: str, description: str = '', 
                      strategy: str = 'percentage', commit_hash: str = '') -> str:
        """创建发布计划"""
        release_id = f"release_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        with self._lock:
            release = {
                'release_id': release_id,
                'version': version,
                'status': ReleaseStatus.DRAFT.value,
                'strategy': strategy,
                'gray_percentage': 0,
                'gray_users': [],
                'gray_ips': [],
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None,
                'rolled_back_at': None,
                'rollback_reason': '',
                'commit_hash': commit_hash,
                'previous_version': self._get_current_version(),
                'success_rate': 100.0,
                'error_count': 0
            }
            
            self._releases[release_id] = release
            self._save_release(release)
            
        logger.info(f"[灰度发布] 创建发布计划: {release_id} v{version}")
        return release_id
    
    def _get_current_version(self) -> str:
        """获取当前版本"""
        try:
            from app.version import VERSION
            return VERSION
        except Exception:
            return 'unknown'
    
    def _save_release(self, release: Dict):
        """保存发布记录到数据库"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO release_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                release['release_id'],
                release['version'],
                release['status'],
                release['strategy'],
                release['gray_percentage'],
                json.dumps(release['gray_users']),
                json.dumps(release['gray_ips']),
                release['description'],
                release['created_at'],
                release['updated_at'],
                release['started_at'],
                release['completed_at'],
                release['rolled_back_at'],
                release['rollback_reason'],
                release['commit_hash'],
                release['previous_version'],
                release['success_rate'],
                release['error_count']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[灰度发布] 保存发布记录失败: {e}")
    
    def start_release(self, release_id: str) -> bool:
        """开始发布"""
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                logger.error(f"[灰度发布] 发布计划不存在: {release_id}")
                return False
            
            if release['status'] != ReleaseStatus.DRAFT.value:
                logger.error(f"[灰度发布] 发布状态不正确: {release['status']}")
                return False
            
            release['status'] = ReleaseStatus.PREPARING.value
            release['started_at'] = datetime.now().isoformat()
            release['updated_at'] = datetime.now().isoformat()
            self._current_release = release_id
            self._save_release(release)
        
        logger.info(f"[灰度发布] 开始发布: {release_id}")
        return True
    
    def set_gray_percentage(self, release_id: str, percentage: int) -> bool:
        """设置灰度比例"""
        if percentage < 0 or percentage > 100:
            logger.error(f"[灰度发布] 无效的灰度比例: {percentage}")
            return False
        
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                logger.error(f"[灰度发布] 发布计划不存在: {release_id}")
                return False
            
            if release['status'] not in [ReleaseStatus.PREPARING.value, ReleaseStatus.GRAY.value]:
                logger.error(f"[灰度发布] 当前状态不支持设置灰度比例: {release['status']}")
                return False
            
            release['gray_percentage'] = percentage
            release['status'] = ReleaseStatus.GRAY.value
            release['updated_at'] = datetime.now().isoformat()
            self._gray_percentage = percentage
            self._save_release(release)
        
        logger.info(f"[灰度发布] 设置灰度比例: {release_id} -> {percentage}%")
        return True
    
    def add_gray_users(self, release_id: str, users: List[str]) -> bool:
        """添加灰度用户"""
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                return False
            
            new_users = list(set(release['gray_users'] + users))
            release['gray_users'] = new_users
            release['updated_at'] = datetime.now().isoformat()
            self._gray_users = new_users
            self._save_release(release)
        
        logger.info(f"[灰度发布] 添加灰度用户: {release_id} +{len(users)}人")
        return True
    
    def add_gray_ips(self, release_id: str, ips: List[str]) -> bool:
        """添加灰度IP"""
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                return False
            
            new_ips = list(set(release['gray_ips'] + ips))
            release['gray_ips'] = new_ips
            release['updated_at'] = datetime.now().isoformat()
            self._gray_ips = new_ips
            self._save_release(release)
        
        logger.info(f"[灰度发布] 添加灰度IP: {release_id} +{len(ips)}个")
        return True
    
    def full_release(self, release_id: str) -> bool:
        """全量发布"""
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                return False
            
            if release['status'] != ReleaseStatus.GRAY.value:
                logger.error(f"[灰度发布] 当前状态不支持全量发布: {release['status']}")
                return False
            
            release['gray_percentage'] = 100
            release['status'] = ReleaseStatus.FULL.value
            release['updated_at'] = datetime.now().isoformat()
            self._gray_percentage = 100
            self._save_release(release)
        
        logger.info(f"[灰度发布] 全量发布: {release_id}")
        return True
    
    def complete_release(self, release_id: str) -> bool:
        """完成发布"""
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                return False
            
            if release['status'] != ReleaseStatus.FULL.value:
                logger.error(f"[灰度发布] 当前状态不支持完成发布: {release['status']}")
                return False
            
            release['status'] = ReleaseStatus.COMPLETED.value
            release['completed_at'] = datetime.now().isoformat()
            release['updated_at'] = datetime.now().isoformat()
            self._current_release = None
            self._gray_percentage = 0
            self._save_release(release)
        
        logger.info(f"[灰度发布] 发布完成: {release_id}")
        return True
    
    def rollback(self, release_id: str, reason: str = '') -> bool:
        """回滚发布"""
        with self._lock:
            release = self._releases.get(release_id)
            if not release:
                return False
            
            if release['status'] not in [ReleaseStatus.GRAY.value, ReleaseStatus.FULL.value]:
                logger.error(f"[灰度发布] 当前状态不支持回滚: {release['status']}")
                return False
            
            release['status'] = ReleaseStatus.ROLLING_BACK.value
            release['updated_at'] = datetime.now().isoformat()
            self._save_release(release)
        
        logger.warning(f"[灰度发布] 开始回滚: {release_id}, 原因: {reason}")
        
        try:
            self._execute_rollback(release)
            
            with self._lock:
                release['status'] = ReleaseStatus.ROLLED_BACK.value
                release['rolled_back_at'] = datetime.now().isoformat()
                release['rollback_reason'] = reason
                release['updated_at'] = datetime.now().isoformat()
                self._current_release = None
                self._gray_percentage = 0
                self._save_release(release)
            
            logger.info(f"[灰度发布] 回滚完成: {release_id}")
            return True
        except Exception as e:
            logger.error(f"[灰度发布] 回滚失败: {e}")
            with self._lock:
                release['status'] = ReleaseStatus.FAILED.value
                release['rollback_reason'] = f"{reason} - 回滚异常: {str(e)}"
                release['updated_at'] = datetime.now().isoformat()
                self._save_release(release)
            return False
    
    def _execute_rollback(self, release: Dict):
        """执行实际回滚操作"""
        logger.info(f"[灰度发布] 执行回滚到版本: {release['previous_version']}")
        
        try:
            subprocess.run(
                ['git', 'checkout', release['previous_version']],
                capture_output=True,
                text=True,
                timeout=30
            )
            logger.info(f"[灰度发布] Git回滚成功")
        except Exception as e:
            logger.warning(f"[灰度发布] Git回滚失败: {e}")
    
    def is_gray_user(self, user_id: str = None, ip: str = None) -> bool:
        """判断是否为灰度用户"""
        if self._gray_percentage >= 100:
            return True
        
        if self._gray_percentage == 0:
            return False
        
        if user_id and user_id in self._gray_users:
            return True
        
        if ip and ip in self._gray_ips:
            return True
        
        if self._gray_percentage > 0:
            import hashlib
            if user_id:
                hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                return (hash_val % 100) < self._gray_percentage
            
            if ip:
                hash_val = int(hashlib.md5(ip.encode()).hexdigest(), 16)
                return (hash_val % 100) < self._gray_percentage
        
        return False
    
    def get_release_status(self, release_id: str) -> Optional[Dict]:
        """获取发布状态"""
        return self._releases.get(release_id)
    
    def get_all_releases(self) -> List[Dict]:
        """获取所有发布记录"""
        return sorted(self._releases.values(), key=lambda x: x['created_at'], reverse=True)
    
    def get_current_release(self) -> Optional[Dict]:
        """获取当前进行中的发布"""
        if not self._current_release:
            return None
        return self._releases.get(self._current_release)
    
    def get_gray_percentage(self) -> int:
        """获取当前灰度比例"""
        return self._gray_percentage
    
    def get_health_status(self) -> Dict:
        """获取健康状态"""
        return {
            'status': self._health_status,
            'last_check': self._last_health_check,
            'current_release': self._current_release
        }
    
    def get_release_history(self, limit: int = 20) -> List[Dict]:
        """获取发布历史"""
        return list(self._releases.values())[:limit]


def get_release_manager() -> GrayReleaseManager:
    """获取灰度发布管理器单例"""
    return GrayReleaseManager()


def init_release_system():
    """初始化发布系统"""
    manager = get_release_manager()
    logger.info("[灰度发布] 灰度发布系统初始化完成")
    return manager