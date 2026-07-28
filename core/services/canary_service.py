#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS灰度发布服务
提供版本控制和灰度发布功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class Release:
    """版本发布"""
    
    def __init__(self, release_id: str, version: str, title: str,
                 description: str = '', release_type: str = 'patch',
                 status: str = 'draft', rollout_percentage: float = 0.0,
                 created_at: str = None):
        self.release_id = release_id
        self.version = version
        self.title = title
        self.description = description
        self.release_type = release_type
        self.status = status
        self.rollout_percentage = rollout_percentage
        self.created_at = created_at or datetime.now().isoformat()
        self.deployed_at = None
        self.rollback_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'release_id': self.release_id,
            'version': self.version,
            'title': self.title,
            'description': self.description,
            'release_type': self.release_type,
            'status': self.status,
            'rollout_percentage': self.rollout_percentage,
            'created_at': self.created_at,
            'deployed_at': self.deployed_at,
            'rollback_at': self.rollback_at
        }

class CanaryRule:
    """灰度规则"""
    
    def __init__(self, rule_id: str, release_id: str, name: str,
                 rule_type: str = 'percentage', value: Any = 0.0,
                 conditions: Dict[str, Any] = None, enabled: bool = True,
                 created_at: str = None):
        self.rule_id = rule_id
        self.release_id = release_id
        self.name = name
        self.rule_type = rule_type
        self.value = value
        self.conditions = conditions or {}
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'release_id': self.release_id,
            'name': self.name,
            'rule_type': self.rule_type,
            'value': self.value,
            'conditions': self.conditions,
            'enabled': self.enabled,
            'created_at': self.created_at
        }

class CanaryService:
    """灰度发布服务"""
    
    def __init__(self):
        self.releases: Dict[str, Release] = {}
        self.rules: Dict[str, CanaryRule] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'canary_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'default_rollout_steps': [10, 25, 50, 75, 100],
            'rollout_step_delay': 300,
            'auto_promote_enabled': True,
            'monitoring_thresholds': {
                'error_rate': 0.05,
                'latency_p95': 500,
                'cpu_usage': 80
            },
            'max_concurrent_releases': 5
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'canary_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS releases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    release_id TEXT NOT NULL UNIQUE,
                    version TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    release_type TEXT DEFAULT 'patch',
                    status TEXT DEFAULT 'draft',
                    rollout_percentage REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    deployed_at TEXT,
                    rollback_at TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS canary_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    release_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    rule_type TEXT DEFAULT 'percentage',
                    value TEXT,
                    conditions TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS release_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    release_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rollout_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    release_id TEXT NOT NULL,
                    percentage REAL,
                    status TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_releases_id ON releases(release_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_canary_rules_release ON canary_rules(release_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[灰度] 初始化数据库失败: {e}")
    
    def _generate_release_id(self) -> str:
        """生成发布ID"""
        return f"release_{int(time.time())}_{hash(os.urandom(16))}"
    
    def create_release(self, version: str, title: str, description: str = '',
                      release_type: str = 'patch') -> str:
        """创建版本发布"""
        release_id = self._generate_release_id()
        
        release = Release(
            release_id=release_id,
            version=version,
            title=title,
            description=description,
            release_type=release_type
        )
        
        with self.lock:
            self.releases[release_id] = release
        
        self._save_release_to_db(release)
        logger(f"[灰度] 创建版本发布: {version} - {title}")
        
        return release_id
    
    def _save_release_to_db(self, release: Release):
        """保存发布到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO releases 
                (release_id, version, title, description, release_type, status, rollout_percentage, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                release.release_id, release.version, release.title,
                release.description, release.release_type,
                release.status, release.rollout_percentage,
                release.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[灰度] 保存发布失败: {e}")
    
    def update_release(self, release_id: str, **kwargs) -> bool:
        """更新版本发布"""
        with self.lock:
            if release_id not in self.releases:
                logger(f"[灰度] 发布不存在: {release_id}")
                return False
            
            release = self.releases[release_id]
            
            if 'title' in kwargs:
                release.title = kwargs['title']
            if 'description' in kwargs:
                release.description = kwargs['description']
            if 'status' in kwargs:
                release.status = kwargs['status']
            if 'rollout_percentage' in kwargs:
                release.rollout_percentage = kwargs['rollout_percentage']
        
        self._update_release_in_db(release_id, kwargs)
        logger(f"[灰度] 更新版本发布: {release_id}")
        
        return True
    
    def _update_release_in_db(self, release_id: str, updates: Dict[str, Any]):
        """更新数据库中的发布"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                set_clause.append(f"{key} = ?")
                params.append(value)
            
            params.append(release_id)
            
            cursor.execute(f'UPDATE releases SET {", ".join(set_clause)} WHERE release_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[灰度] 更新发布失败: {e}")
    
    def delete_release(self, release_id: str) -> bool:
        """删除版本发布"""
        with self.lock:
            if release_id not in self.releases:
                logger(f"[灰度] 发布不存在: {release_id}")
                return False
            
            del self.releases[release_id]
        
        self._delete_release_from_db(release_id)
        logger(f"[灰度] 删除版本发布: {release_id}")
        
        return True
    
    def _delete_release_from_db(self, release_id: str):
        """从数据库删除发布"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM releases WHERE release_id = ?', (release_id,))
            cursor.execute('DELETE FROM canary_rules WHERE release_id = ?', (release_id,))
            cursor.execute('DELETE FROM release_metrics WHERE release_id = ?', (release_id,))
            cursor.execute('DELETE FROM rollout_history WHERE release_id = ?', (release_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[灰度] 删除发布失败: {e}")
    
    def deploy_release(self, release_id: str) -> bool:
        """部署版本发布"""
        with self.lock:
            if release_id not in self.releases:
                logger(f"[灰度] 发布不存在: {release_id}")
                return False
            
            release = self.releases[release_id]
            
            if release.status != 'draft':
                logger(f"[灰度] 发布状态不允许部署: {release.status}")
                return False
            
            release.status = 'deployed'
            release.deployed_at = datetime.now().isoformat()
        
        self._update_release_in_db(release_id, {'status': 'deployed', 'deployed_at': release.deployed_at})
        self._start_rollout(release_id)
        
        logger(f"[灰度] 部署版本发布: {release.version}")
        return True
    
    def _start_rollout(self, release_id: str):
        """开始灰度发布"""
        def rollout():
            try:
                steps = self.config['default_rollout_steps']
                
                for percentage in steps:
                    time.sleep(self.config['rollout_step_delay'])
                    
                    if not self._check_health(release_id):
                        logger(f"[灰度] 健康检查失败，停止灰度发布: {release_id}")
                        self.rollback_release(release_id)
                        return
                    
                    self.update_release(release_id, rollout_percentage=percentage)
                    self._log_rollout(release_id, percentage, 'completed')
                    
                    logger(f"[灰度] 灰度发布进度: {percentage}%")
                
                self.update_release(release_id, status='completed', rollout_percentage=100.0)
                logger(f"[灰度] 灰度发布完成: {release_id}")
            except Exception as e:
                logger(f"[灰度] 灰度发布失败: {release_id} - {e}")
        
        thread = threading.Thread(target=rollout, daemon=True)
        thread.start()
    
    def _check_health(self, release_id: str) -> bool:
        """健康检查"""
        try:
            from system_monitor import system_monitor
            
            metrics = system_monitor.get_system_metrics()
            
            if metrics.get('cpu_percent', 0) > self.config['monitoring_thresholds']['cpu_usage']:
                return False
            
            return True
        except:
            return True
    
    def rollback_release(self, release_id: str) -> bool:
        """回滚版本发布"""
        with self.lock:
            if release_id not in self.releases:
                logger(f"[灰度] 发布不存在: {release_id}")
                return False
            
            release = self.releases[release_id]
            
            release.status = 'rolled_back'
            release.rollback_at = datetime.now().isoformat()
            release.rollout_percentage = 0.0
        
        self._update_release_in_db(release_id, {
            'status': 'rolled_back',
            'rollback_at': datetime.now().isoformat(),
            'rollout_percentage': 0.0
        })
        
        logger(f"[灰度] 回滚版本发布: {release.version}")
        return True
    
    def _log_rollout(self, release_id: str, percentage: float, status: str):
        """记录灰度发布历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO rollout_history (release_id, percentage, status, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (release_id, percentage, status, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[灰度] 记录灰度历史失败: {e}")
    
    def add_canary_rule(self, release_id: str, name: str, rule_type: str = 'percentage',
                       value: Any = 0.0, conditions: Dict[str, Any] = None) -> str:
        """添加灰度规则"""
        rule_id = f"rule_{int(time.time())}_{hash(os.urandom(16))}"
        
        rule = CanaryRule(
            rule_id=rule_id,
            release_id=release_id,
            name=name,
            rule_type=rule_type,
            value=value,
            conditions=conditions or {}
        )
        
        with self.lock:
            self.rules[rule_id] = rule
        
        self._save_rule_to_db(rule)
        logger(f"[灰度] 添加灰度规则: {name}")
        
        return rule_id
    
    def _save_rule_to_db(self, rule: CanaryRule):
        """保存规则到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO canary_rules 
                (rule_id, release_id, name, rule_type, value, conditions, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.rule_id, rule.release_id, rule.name,
                rule.rule_type, str(rule.value),
                json.dumps(rule.conditions),
                1 if rule.enabled else 0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[灰度] 保存规则失败: {e}")
    
    def evaluate_canary(self, user_id: str = None, user_ip: str = None,
                       request: Dict[str, Any] = None) -> Optional[str]:
        """评估灰度规则"""
        active_releases = [r for r in self.releases.values() 
                          if r.status == 'deployed' and r.rollout_percentage > 0]
        
        for release in active_releases:
            release_rules = [r for r in self.rules.values() 
                            if r.release_id == release.release_id and r.enabled]
            
            if not release_rules:
                if self._check_percentage(release.rollout_percentage):
                    return release.version
            
            for rule in release_rules:
                if self._evaluate_rule(rule, user_id, user_ip, request):
                    return release.version
        
        return None
    
    def _check_percentage(self, percentage: float) -> bool:
        """检查百分比规则"""
        import random
        return random.random() * 100 <= percentage
    
    def _evaluate_rule(self, rule: CanaryRule, user_id: str = None,
                       user_ip: str = None, request: Dict[str, Any] = None) -> bool:
        """评估规则"""
        if rule.rule_type == 'percentage':
            return self._check_percentage(float(rule.value))
        
        if rule.rule_type == 'user_id':
            if user_id and user_id in (rule.value.split(',') if isinstance(rule.value, str) else []):
                return True
        
        if rule.rule_type == 'ip_range':
            if user_ip:
                for ip_range in rule.value.split(','):
                    if self._ip_in_range(user_ip, ip_range.strip()):
                        return True
        
        if rule.rule_type == 'custom':
            condition = rule.conditions.get('expression', '')
            try:
                # 安全修复：使用受限的eval环境，仅允许基本比较运算
                import ast as _ast
                # 仅允许简单条件表达式，禁止函数调用和属性访问
                tree = _ast.parse(condition, mode='eval')
                allowed_nodes = (_ast.Expression, _ast.BoolOp, _ast.Compare, _ast.Num,
                                 _ast.Str, _ast.Name, _ast.Load, _ast.And, _ast.Or,
                                 _ast.Eq, _ast.NotEq, _ast.Lt, _ast.LtE, _ast.Gt, _ast.GtE,
                                 _ast.Constant, _ast.Tuple, _ast.List)
                for node in _ast.walk(tree):
                    if not isinstance(node, allowed_nodes):
                        return False
                return eval(condition, {'__builtins__': {}}, {'user_id': user_id, 'user_ip': user_ip})
            except:
                return False
        
        return False
    
    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """检查IP是否在范围内"""
        try:
            import ipaddress
            ip_addr = ipaddress.ip_address(ip)
            
            if '-' in ip_range:
                start_ip, end_ip = ip_range.split('-')
                return ipaddress.ip_address(start_ip.strip()) <= ip_addr <= ipaddress.ip_address(end_ip.strip())
            
            if '/' in ip_range:
                return ip_addr in ipaddress.ip_network(ip_range, strict=False)
            
            return ip == ip_range
        except:
            return False
    
    def get_release(self, release_id: str) -> Optional[Release]:
        """获取版本发布"""
        return self.releases.get(release_id)
    
    def get_releases(self, status: str = None) -> List[Release]:
        """获取版本发布列表"""
        with self.lock:
            if status:
                return [r for r in self.releases.values() if r.status == status]
            return list(self.releases.values())
    
    def get_rollout_history(self, release_id: str = None) -> List[Dict[str, Any]]:
        """获取灰度发布历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM rollout_history WHERE 1=1'
            params = []
            
            if release_id:
                query += ' AND release_id = ?'
                params.append(release_id)
            
            query += ' ORDER BY started_at DESC'
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                history.append(dict(zip(columns, row)))
            
            conn.close()
            return history
        except Exception as e:
            logger(f"[灰度] 获取灰度历史失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            deployed_count = sum(1 for r in self.releases.values() if r.status == 'deployed')
            active_count = sum(1 for r in self.releases.values() if r.status in ['deployed', 'completed'])
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_releases': len(self.releases),
                'deployed_releases': deployed_count,
                'active_releases': active_count,
                'total_rules': len(self.rules),
                'auto_promote_enabled': self.config['auto_promote_enabled'],
                'default_rollout_steps': self.config['default_rollout_steps']
            }
    
    def start(self):
        """启动灰度发布服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[灰度] 灰度发布服务已启动")
    
    def stop(self):
        """停止灰度发布服务"""
        self.is_running = False
        logger(f"[灰度] 灰度发布服务已停止")

canary_service = CanaryService()
