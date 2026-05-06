#!/usr/bin/env python3
"""
版本号管理服务 - 确保数据库记录系统最高版本号，防止版本号错乱
"""

import sqlite3
import re
from datetime import datetime
from app.utils.logging import logger

class VersionManager:
    """版本号管理服务"""
    
    _instance = None
    _lock = __import__('threading').RLock()
    
    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(VersionManager, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化版本管理器"""
        self.db_path = 'flask-app/app.db'
        self._create_version_table()
        self._current_version = self._get_highest_version()
        logger.info(f"版本管理器初始化完成，当前版本: {self._current_version}")
    
    def _create_version_table(self):
        """创建版本管理表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                major INTEGER NOT NULL,
                minor INTEGER NOT NULL,
                patch INTEGER NOT NULL,
                build INTEGER DEFAULT 0,
                release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_version_control_version ON version_control(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_version_control_active ON version_control(is_active)')
        
        conn.commit()
        conn.close()
    
    def _get_highest_version(self):
        """获取数据库中最高版本号"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version FROM version_control 
            ORDER BY major DESC, minor DESC, patch DESC, build DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        return "1.0.0"
    
    def parse_version(self, version_str):
        """解析版本号字符串"""
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?$'
        match = re.match(pattern, version_str)
        
        if match:
            return {
                'major': int(match.group(1)),
                'minor': int(match.group(2)),
                'patch': int(match.group(3)),
                'build': int(match.group(4)) if match.group(4) else 0
            }
        return None
    
    def compare_versions(self, v1, v2):
        """比较两个版本号，返回 -1, 0, 1"""
        v1_parts = self.parse_version(v1)
        v2_parts = self.parse_version(v2)
        
        if not v1_parts or not v2_parts:
            raise ValueError("无效的版本号格式")
        
        for key in ['major', 'minor', 'patch', 'build']:
            if v1_parts[key] < v2_parts[key]:
                return -1
            elif v1_parts[key] > v2_parts[key]:
                return 1
        
        return 0
    
    def validate_version(self, version_str):
        """验证版本号格式是否正确"""
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?$'
        if not re.match(pattern, version_str):
            raise ValueError(f"无效的版本号格式: {version_str}")
        return True
    
    def get_current_version(self):
        """获取当前版本号"""
        return self._current_version
    
    def upgrade_version(self, level='patch', description=None):
        """升级版本号
        
        Args:
            level: 'major', 'minor', 'patch', 'build'
            description: 版本更新描述
        
        Returns:
            str: 新版本号
        """
        with self._lock:
            current = self._current_version
            parts = self.parse_version(current)
            
            if level == 'major':
                parts['major'] += 1
                parts['minor'] = 0
                parts['patch'] = 0
                parts['build'] = 0
            elif level == 'minor':
                parts['minor'] += 1
                parts['patch'] = 0
                parts['build'] = 0
            elif level == 'patch':
                parts['patch'] += 1
                parts['build'] = 0
            elif level == 'build':
                parts['build'] += 1
            else:
                raise ValueError("无效的升级级别: major, minor, patch, build")
            
            new_version = f"{parts['major']}.{parts['minor']}.{parts['patch']}"
            if parts['build'] > 0:
                new_version += f".{parts['build']}"
            
            # 检查新版本是否已存在
            if self._version_exists(new_version):
                # 如果存在，自动增加build号
                parts['build'] += 1
                new_version = f"{parts['major']}.{parts['minor']}.{parts['patch']}.{parts['build']}"
            
            # 记录新版本到数据库
            self._record_version(new_version, description)
            
            # 更新当前版本
            self._current_version = new_version
            
            logger.info(f"版本升级完成: {current} -> {new_version}")
            return new_version
    
    def _version_exists(self, version):
        """检查版本号是否已存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM version_control WHERE version = ?', (version,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists
    
    def _record_version(self, version, description=None):
        """记录新版本到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        parts = self.parse_version(version)
        
        cursor.execute('''
            INSERT INTO version_control 
            (version, major, minor, patch, build, description, release_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (version, parts['major'], parts['minor'], parts['patch'], parts['build'], description, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def set_version(self, version, description=None):
        """手动设置版本号（谨慎使用）"""
        with self._lock:
            self.validate_version(version)
            
            # 检查是否比当前版本高
            if self.compare_versions(version, self._current_version) <= 0:
                raise ValueError(f"新版本必须高于当前版本 {self._current_version}")
            
            # 检查是否已存在
            if self._version_exists(version):
                raise ValueError(f"版本 {version} 已存在")
            
            # 记录新版本
            self._record_version(version, description)
            self._current_version = version
            
            logger.info(f"版本手动设置完成: {version}")
            return version
    
    def get_version_history(self, limit=10):
        """获取版本历史记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, release_date, description, is_active 
            FROM version_control 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'version': row[0],
                'release_date': row[1],
                'description': row[2],
                'is_active': bool(row[3])
            })
        
        conn.close()
        return history
    
    def validate_version_order(self):
        """验证版本号顺序是否正确，防止错乱"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, major, minor, patch, build 
            FROM version_control 
            ORDER BY id ASC
        ''')
        
        versions = cursor.fetchall()
        conn.close()
        
        if len(versions) < 2:
            return True, "版本数量不足，无需验证"
        
        for i in range(1, len(versions)):
            prev = versions[i-1]
            curr = versions[i]
            
            # 验证数值顺序
            prev_num = (prev[1], prev[2], prev[3], prev[4])
            curr_num = (curr[1], curr[2], curr[3], curr[4])
            
            if curr_num <= prev_num:
                return False, f"版本顺序错乱: {prev[0]} -> {curr[0]}"
        
        return True, "版本顺序验证通过"
    
    def get_next_version(self, level='patch'):
        """获取下一个版本号（不实际升级）"""
        current = self._current_version
        parts = self.parse_version(current)
        
        if level == 'major':
            return f"{parts['major'] + 1}.0.0"
        elif level == 'minor':
            return f"{parts['major']}.{parts['minor'] + 1}.0"
        elif level == 'patch':
            return f"{parts['major']}.{parts['minor']}.{parts['patch'] + 1}"
        elif level == 'build':
            return f"{parts['major']}.{parts['minor']}.{parts['patch']}.{parts['build'] + 1}"
        else:
            raise ValueError("无效的升级级别")
    
    def lock_version(self, version):
        """锁定版本号，防止被覆盖"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE version_control SET is_active = 0 WHERE version = ?', (version,))
        conn.commit()
        conn.close()
        
        logger.info(f"版本已锁定: {version}")
    
    def get_version_info(self, version):
        """获取版本详细信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, major, minor, patch, build, release_date, description, is_active, created_at 
            FROM version_control 
            WHERE version = ?
        ''', (version,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'version': row[0],
                'major': row[1],
                'minor': row[2],
                'patch': row[3],
                'build': row[4],
                'release_date': row[5],
                'description': row[6],
                'is_active': bool(row[7]),
                'created_at': row[8]
            }
        return None

# 创建单例实例
version_manager = VersionManager()