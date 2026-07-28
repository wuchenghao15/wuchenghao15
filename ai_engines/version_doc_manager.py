# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
版本文档管理器
自动管理系统版本、变更说明、历史档案，并写入规则
"""

import os
import json
import uuid
import sqlite3
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

VERSION_LEVELS = ['major', 'minor', 'patch']

class VersionDocManager:
    """版本文档管理器"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'version_manager.db')
        self._create_tables()
        self.current_version = self._load_current_version()
        self.changelog_entries = []

    def _create_tables(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id TEXT UNIQUE,
                    version_number TEXT,
                    version_level TEXT,
                    changes TEXT,
                    changelog TEXT,
                    release_notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    git_commit TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT UNIQUE,
                    rule_name TEXT,
                    rule_type TEXT,
                    description TEXT,
                    action TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("[VersionDocManager] 数据库表创建完成")

    def _load_current_version(self) -> str:
        """加载当前版本"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT version_number FROM version_history ORDER BY id DESC LIMIT 1')
                result = cursor.fetchone()
                if result:
                    return result[0]
        except Exception as e:
            logger.error(f"[VersionDocManager] 加载版本失败: {e}")
        
        return '1.0.0'

    def bump_version(self, level: str = 'patch', changes: List[str] = None) -> Dict[str, Any]:
        """升级版本"""
        if level not in VERSION_LEVELS:
            level = 'patch'
        
        major, minor, patch = map(int, self.current_version.split('.'))
        
        if level == 'major':
            major += 1
            minor = 0
            patch = 0
        elif level == 'minor':
            minor += 1
            patch = 0
        else:
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        version_id = f"v{new_version.replace('.', '_')}"
        
        changelog = self._generate_changelog(new_version, changes or [])
        
        version_info = {
            'version_id': version_id,
            'version_number': new_version,
            'version_level': level,
            'changes': json.dumps(changes or [], ensure_ascii=False),
            'changelog': changelog,
            'release_notes': self._generate_release_notes(new_version, changes or []),
            'created_at': datetime.now().isoformat(),
            'git_commit': self._get_git_commit()
        }
        
        self._save_version(version_info)
        self.current_version = new_version
        self.changelog_entries.append(version_info)
        
        self._write_rules()
        
        logger.info(f"[VersionDocManager] 版本升级: {self.current_version} -> {new_version}")
        return version_info

    def _generate_changelog(self, version: str, changes: List[str]) -> str:
        """生成变更日志"""
        changelog = f"## {version} ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        
        if changes:
            for change in changes:
                changelog += f"- {change}\n"
        else:
            changelog += "- 系统自动更新\n"
        
        changelog += "\n"
        return changelog

    def _generate_release_notes(self, version: str, changes: List[str]) -> str:
        """生成发布说明"""
        notes = f"MTSCOS AI系统 v{version}\n"
        notes += "=" * (len(notes) - 1) + "\n\n"
        notes += f"发布日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        notes += "变更内容:\n"
        
        if changes:
            for i, change in enumerate(changes, 1):
                notes += f"{i}. {change}\n"
        else:
            notes += "暂无具体变更说明\n"
        
        notes += "\n系统版本历史记录\n"
        notes += "-" * 30 + "\n"
        
        return notes

    def _get_git_commit(self) -> str:
        """获取当前Git提交"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            return result.stdout.strip()[:8]
        except Exception:
            return 'unknown'

    def _save_version(self, version: Dict):
        """保存版本信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO version_history 
                    (version_id, version_number, version_level, changes, changelog, release_notes, git_commit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version['version_id'],
                    version['version_number'],
                    version['version_level'],
                    version['changes'],
                    version['changelog'],
                    version['release_notes'],
                    version['git_commit']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[VersionDocManager] 保存版本失败: {e}")

    def _write_rules(self):
        """写入规则到系统规则表"""
        rules = [
            {
                'rule_id': 'version_rule_001',
                'rule_name': '版本升级规则',
                'rule_type': 'versioning',
                'description': '每次系统修复或功能更新后必须更新版本号',
                'action': 'enforce'
            },
            {
                'rule_id': 'version_rule_002',
                'rule_name': '变更日志规则',
                'rule_type': 'documentation',
                'description': '每次版本升级必须生成详细的变更日志',
                'action': 'enforce'
            },
            {
                'rule_id': 'version_rule_003',
                'rule_name': '回滚测试规则',
                'rule_type': 'testing',
                'description': '每次版本升级前必须执行回滚测试',
                'action': 'enforce'
            },
            {
                'rule_id': 'version_rule_004',
                'rule_name': 'Git提交规则',
                'rule_type': 'version_control',
                'description': '每次版本升级必须提交到Git并推送',
                'action': 'enforce'
            },
            {
                'rule_id': 'version_rule_005',
                'rule_name': '历史记录规则',
                'rule_type': 'archiving',
                'description': '所有版本变更必须保存到历史档案库',
                'action': 'enforce'
            },
            {
                'rule_id': 'version_rule_006',
                'rule_name': '自动提交规则',
                'rule_type': 'automation',
                'description': '系统自动执行Git提交和推送，防止人工重复提交',
                'action': 'auto'
            }
        ]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for rule in rules:
                    cursor.execute('''
                        INSERT OR REPLACE INTO system_rules 
                        (rule_id, rule_name, rule_type, description, action)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        rule['rule_id'],
                        rule['rule_name'],
                        rule['rule_type'],
                        rule['description'],
                        rule['action']
                    ))
                conn.commit()
            
            logger.info("[VersionDocManager] 版本管理规则已写入")
        except Exception as e:
            logger.error(f"[VersionDocManager] 写入规则失败: {e}")

    def auto_git_commit(self, message: str = None) -> Dict[str, Any]:
        """自动Git提交"""
        if not message:
            message = f"chore: 自动提交 - 版本 {self.current_version}"
        
        try:
            subprocess.run(['git', 'add', '.'], capture_output=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                capture_output=True, text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            if result.returncode != 0 and 'nothing to commit' not in result.stderr:
                return {'success': False, 'error': result.stderr}
            
            subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            
            logger.info(f"[VersionDocManager] Git提交完成: {message}")
            return {'success': True, 'message': message, 'commit': self._get_git_commit()}
        except Exception as e:
            logger.error(f"[VersionDocManager] Git提交失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_version_history(self) -> List[Dict]:
        """获取版本历史"""
        history = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM version_history ORDER BY id DESC')
                for row in cursor.fetchall():
                    history.append({
                        'version_id': row[1],
                        'version_number': row[2],
                        'version_level': row[3],
                        'changes': json.loads(row[4]) if row[4] else [],
                        'changelog': row[5],
                        'release_notes': row[6],
                        'created_at': row[7],
                        'git_commit': row[8]
                    })
        except Exception as e:
            logger.error(f"[VersionDocManager] 获取版本历史失败: {e}")
        return history

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.current_version

    def get_changelog(self) -> str:
        """获取变更日志"""
        history = self.get_version_history()
        changelog = "# MTSCOS AI系统变更日志\n\n"
        for version in history:
            changelog += version.get('changelog', '')
        return changelog

    def get_rules(self) -> List[Dict]:
        """获取版本管理规则"""
        rules = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM system_rules WHERE enabled = 1')
                for row in cursor.fetchall():
                    rules.append({
                        'rule_id': row[1],
                        'rule_name': row[2],
                        'rule_type': row[3],
                        'description': row[4],
                        'action': row[5],
                        'enabled': row[6]
                    })
        except Exception as e:
            logger.error(f"[VersionDocManager] 获取规则失败: {e}")
        return rules