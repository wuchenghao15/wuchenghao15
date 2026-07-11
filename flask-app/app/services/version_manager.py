# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
版本号管理服务 - 确保数据库记录系统最高版本号,防止版本号错乱
"""
from flask import Blueprint, jsonify, request
import sqlite3
from contextlib import contextmanager
import re
from datetime import datetime
from app.utils.logging import logger
import logging
import json

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
        import os
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')
        self._create_version_table()
        self._current_version = self._get_highest_version()
        logger.info(f"版本管理器初始化完成,当前版本: {self._current_version}")
    
    def _create_version_table(self):
        """创建版本管理表"""
        with sqlite3.connect(self.db_path) as conn:
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
            
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_version_control_version ON version_control(version)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_version_control_active ON version_control(is_active)')
            
            conn.commit()
    
    def _get_highest_version(self):
        """获取数据库中最高版本号"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT version FROM version_control 
            ORDER BY major DESC, minor DESC, patch DESC, build DESC
            LIMIT 1
            ''')
            result = cursor.fetchone()
            
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
        """比较两个版本号: 返回 -1, 0, 1"""
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
            
            if self._version_exists(new_version):
                parts['build'] += 1
                new_version = f"{parts['major']}.{parts['minor']}.{parts['patch']}.{parts['build']}"
            
            self._record_version(new_version, description)
            self._current_version = new_version
            
            logger.info(f"版本升级完成: {current} -> {new_version}")
            return new_version
    
    def _version_exists(self, version):
        """检查版本号是否已存在"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM version_control WHERE version = ?', (version,))
            exists = cursor.fetchone()[0] > 0
        return exists
    
    def _record_version(self, version, description=None):
        """记录新版本到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            parts = self.parse_version(version)
            
            cursor.execute('''
            INSERT INTO version_control 
            (version, major, minor, patch, build, description, release_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (version, parts['major'], parts['minor'], parts['patch'], parts['build'], description, datetime.now().isoformat()))
            
            conn.commit()
    
    def set_version(self, version, description=None):
        """手动设置版本号(谨慎使用)"""
        with self._lock:
            self.validate_version(version)
            
            if self.compare_versions(version, self._current_version) <= 0:
                raise ValueError(f"新版本必须高于当前版本 {self._current_version}")
            
            if self._version_exists(version):
                raise ValueError(f"版本 {version} 已存在")
            
            self._record_version(version, description)
            self._current_version = version
            
            logger.info(f"版本手动设置完成: {version}")
            return version
    
    def get_version_history(self, limit=10):
        """获取版本历史记录"""
        with sqlite3.connect(self.db_path) as conn:
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
            
        return history
    
    def validate_version_order(self):
        """验证版本号顺序是否正确,防止错乱"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT version, major, minor, patch, build 
            FROM version_control 
            ORDER BY id ASC
            ''')
            
            versions = cursor.fetchall()
        
        if len(versions) < 2:
            return True, "版本数量不足,无需验证"
        
        for i in range(1, len(versions)):
            prev = versions[i-1]
            curr = versions[i]
            
            prev_ver = f"{prev[1]}.{prev[2]}.{prev[3]}.{prev[4]}"
            curr_ver = f"{curr[1]}.{curr[2]}.{curr[3]}.{curr[4]}"
            
            if self.compare_versions(curr_ver, prev_ver) < 0:
                return False, f"版本顺序错误: {prev[0]} -> {curr[0]}"
        
        return True, "版本顺序正确"
    
    def get_next_version(self, level='patch'):
        """获取下一个版本号(不实际升级)"""
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
        
        return current
    
    def lock_version(self, version):
        """锁定版本号,防止被覆盖"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE version_control SET is_active = 0 WHERE version = ?', (version,))
            conn.commit()
        
        logger.info(f"版本已锁定: {version}")
    
    def get_version_info(self, version):
        """获取版本详细信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT version, major, minor, patch, build, release_date, description, is_active, created_at 
            FROM version_control 
            WHERE version = ?
            ''', (version,))
            
            row = cursor.fetchone()
        
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

    def compare_versions_detail(self, v1, v2):
        """详细比较两个版本的差异"""
        v1_info = self.get_version_info(v1)
        v2_info = self.get_version_info(v2)
        
        if not v1_info or not v2_info:
            return {'error': '版本不存在'}
        
        comparison = {
            'version1': v1,
            'version2': v2,
            'comparison_result': self.compare_versions(v1, v2),
            'is_newer': self.compare_versions(v2, v1) > 0,
            'version_bump': self._detect_version_bump(v1, v2),
            'details': {
                'major_diff': v2_info['major'] - v1_info['major'],
                'minor_diff': v2_info['minor'] - v1_info['minor'],
                'patch_diff': v2_info['patch'] - v1_info['patch'],
                'build_diff': v2_info['build'] - v1_info['build']
            }
        }
        
        return comparison

    def _detect_version_bump(self, v1, v2):
        """检测版本升级类型"""
        v1_parts = self.parse_version(v1)
        v2_parts = self.parse_version(v2)
        
        if not v1_parts or not v2_parts:
            return 'unknown'
        
        if v2_parts['major'] > v1_parts['major']:
            return 'major'
        elif v2_parts['minor'] > v1_parts['minor']:
            return 'minor'
        elif v2_parts['patch'] > v1_parts['patch']:
            return 'patch'
        elif v2_parts['build'] > v1_parts['build']:
            return 'build'
        else:
            return 'none'

    def get_version_tree(self):
        """获取版本树结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT version, major, minor, patch, build, release_date, description 
            FROM version_control 
            ORDER BY major DESC, minor DESC, patch DESC, build DESC
            ''')
            versions = cursor.fetchall()
        
        tree = {}
        for ver in versions:
            major = str(ver[1])
            minor = str(ver[2])
            
            if major not in tree:
                tree[major] = {
                    'major_version': major,
                    'minor_versions': {},
                    'total_versions': 0
                }
            
            if minor not in tree[major]['minor_versions']:
                tree[major]['minor_versions'][minor] = {
                    'minor_version': minor,
                    'patch_versions': [],
                    'total_patches': 0
                }
            
            tree[major]['minor_versions'][minor]['patch_versions'].append({
                'version': ver[0],
                'patch': ver[3],
                'build': ver[4],
                'release_date': ver[5],
                'description': ver[6]
            })
            tree[major]['minor_versions'][minor]['total_patches'] += 1
            tree[major]['total_versions'] += 1
        
        return tree

    def export_version_history(self, filepath, format='json'):
        """导出版本历史"""
        history = self.get_version_history(limit=1000)
        
        try:
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        'export_date': datetime.now().isoformat(),
                        'total_versions': len(history),
                        'current_version': self._current_version,
                        'versions': history
                    }, f, ensure_ascii=False, indent=2)
            elif format == 'markdown':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('# 版本历史记录\n\n')
                    f.write(f'- 导出版本: {self._current_version}\n')
                    f.write(f'- 导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                    f.write(f'- 版本数量: {len(history)}\n\n')
                    f.write('## 版本列表\n\n')
                    f.write('| 版本号 | 发布日期 | 描述 | 状态 |\n')
                    f.write('|--------|----------|------|------|\n')
                    for ver in history:
                        status = '✅ 激活' if ver['is_active'] else '🔒 锁定'
                        f.write(f"| {ver['version']} | {ver['release_date']} | {ver.get('description', '-')} | {status} |\n")
            else:
                return False
            
            logger.info(f"版本历史已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出版本历史失败: {e}")
            return False

    def get_version_statistics(self):
        """获取版本统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM version_control')
            total_versions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM version_control WHERE is_active = 1')
            active_versions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT major) FROM version_control')
            major_versions = cursor.fetchone()[0]
            
            cursor.execute('SELECT MIN(release_date), MAX(release_date) FROM version_control')
            date_range = cursor.fetchone()
            
            cursor.execute('''
            SELECT major, COUNT(*) as count 
            FROM version_control 
            GROUP BY major 
            ORDER BY count DESC
            ''')
            version_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_versions': total_versions,
            'active_versions': active_versions,
            'locked_versions': total_versions - active_versions,
            'major_versions': major_versions,
            'current_version': self._current_version,
            'first_release_date': date_range[0],
            'latest_release_date': date_range[1],
            'version_distribution': version_distribution
        }

    def cleanup_old_versions(self, keep_major=3, keep_minor=5):
        """清理旧版本,保留指定数量的主要版本和次要版本"""
        with self._lock:
            tree = self.get_version_tree()
            majors = sorted(tree.keys(), key=lambda x: int(x), reverse=True)
            keep_versions = set()
            
            for major in majors[:keep_major]:
                minors = sorted(tree[major]['minor_versions'].keys(), key=lambda x: int(x), reverse=True)
                for minor in minors[:keep_minor]:
                    for patch in tree[major]['minor_versions'][minor]['patch_versions']:
                        keep_versions.add(patch['version'])
            
            if self._current_version not in keep_versions:
                keep_versions.add(self._current_version)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT version FROM version_control')
                all_versions = {row[0] for row in cursor.fetchall()}
                
                to_delete = all_versions - keep_versions
                
                for ver in to_delete:
                    cursor.execute('DELETE FROM version_control WHERE version = ?', (ver,))
                
                conn.commit()
            
            logger.info(f"清理了 {len(to_delete)} 个旧版本，保留 {len(keep_versions)} 个版本")
            return len(to_delete)

    def initialize_from_changelog(self):
        """从changelog初始化版本历史"""
        try:
            from app.version import CHANGELOG
            
            with self._lock:
                for entry in reversed(CHANGELOG):
                    version = entry['version']
                    if not self._version_exists(version):
                        description = f"{entry['title']}: {'; '.join(entry['changes'][:3])}..."
                        self._record_version(version, description)
                
                if hasattr(self, '_current_version'):
                    latest = CHANGELOG[0]['version']
                    if self.compare_versions(latest, self._current_version) > 0:
                        self._current_version = latest
            
            logger.info("从changelog初始化版本历史完成")
            return True
        except Exception as e:
            logger.error(f"从changelog初始化失败: {e}")
            return False

    def get_version_diff(self, v1, v2):
        """获取两个版本之间的差异列表"""
        try:
            from app.version import get_version_range
            
            versions = get_version_range(v2, v1)
            all_changes = []
            
            for ver in versions:
                for change in ver.get('changes', []):
                    all_changes.append({
                        'version': ver['version'],
                        'date': ver['date'],
                        'change': change
                    })
            
            return {
                'from_version': v2,
                'to_version': v1,
                'version_count': len(versions),
                'total_changes': len(all_changes),
                'changes': all_changes
            }
        except Exception as e:
            return {'error': str(e)}

version_manager = VersionManager()
