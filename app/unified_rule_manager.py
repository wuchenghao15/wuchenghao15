#!/usr/bin/env python3
"""
统一规则管理服务
整合系统所有规则的管理、执行、监控功能
"""

import sqlite3
import os
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

class UnifiedRuleManager:
    """统一规则管理服务"""
    
    RULE_CATEGORIES = {
        'architecture': '架构层规则',
        'data': '数据层规则',
        'security': '安全层规则',
        'operations': '运维层规则',
        'git': 'Git同步规则',
        'github': 'GitHub同步规则',
        'backup': '备份规则',
        'high_availability': '高可用规则',
        'recovery': '恢复规则',
        'audit': '审计规则',
        'release': '发布规则',
        'update': '更新规则',
        'learning': '学习规则',
        'auto_upgrade': '自动升级规则',
        'data_governance': '数据治理规则',
        'maintenance': '维护规则',
        'system': '系统核心规则'
    }
    
    RULE_PRIORITIES = ['critical', 'high', 'medium', 'low']
    
    def __init__(self):
        self._rules_cache = {}
        self._rule_listeners = {}
        self._is_running = False
        self._sync_thread = None
        self._init_database()
        self._load_rules()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                rule_value TEXT,
                rule_type TEXT DEFAULT "system",
                description TEXT,
                is_active INTEGER DEFAULT 1,
                priority TEXT DEFAULT "medium",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                effective_from TEXT,
                expires_at TEXT,
                rule_group TEXT,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT NOT NULL,
                execution_time TEXT DEFAULT CURRENT_TIMESTAMP,
                result TEXT DEFAULT "success",
                error_message TEXT,
                executed_by TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_rules(self):
        """加载所有规则到缓存"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT rule_code, rule_value FROM system_rules WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        
        self._rules_cache = {row[0]: row[1] for row in rows}
        logger.info(f"✓ 已加载 {len(self._rules_cache)} 条规则到缓存")
    
    def _sync_cache(self):
        """同步缓存"""
        while self._is_running:
            try:
                self._load_rules()
            except Exception as e:
                logger.error(f"缓存同步失败: {e}")
            time.sleep(300)
    
    def start(self):
        """启动规则管理服务"""
        self._is_running = True
        self._sync_thread = threading.Thread(target=self._sync_cache, daemon=True)
        self._sync_thread.start()
        logger.info("✓ 统一规则管理服务已启动")
    
    def stop(self):
        """停止规则管理服务"""
        self._is_running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("✓ 统一规则管理服务已停止")
    
    def get_rule(self, rule_code: str, default: Any = None) -> Any:
        """获取规则值"""
        return self._rules_cache.get(rule_code, default)
    
    def get_rule_int(self, rule_code: str, default: int = 0) -> int:
        """获取整数类型规则值"""
        value = self.get_rule(rule_code)
        return int(value) if value else default
    
    def get_rule_bool(self, rule_code: str, default: bool = False) -> bool:
        """获取布尔类型规则值"""
        value = self.get_rule(rule_code)
        return value == '1' if value is not None else default
    
    def get_rule_float(self, rule_code: str, default: float = 0.0) -> float:
        """获取浮点类型规则值"""
        value = self.get_rule(rule_code)
        return float(value) if value else default
    
    def set_rule(self, rule_code: str, value: str, description: str = '') -> bool:
        """设置规则值"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_rules WHERE rule_code = ?', (rule_code,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            cursor.execute('''
                UPDATE system_rules SET rule_value = ?, description = ?, updated_at = ? WHERE rule_code = ?
            ''', (value, description, datetime.now().isoformat(), rule_code))
        else:
            cursor.execute('''
                INSERT INTO system_rules (rule_code, rule_name, rule_value, description)
                VALUES (?, ?, ?, ?)
            ''', (rule_code, rule_code, value, description))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            self._rules_cache[rule_code] = value
            self._notify_listeners(rule_code, value)
        
        return success
    
    def add_rule(self, rule_code: str, rule_name: str, rule_value: str, 
                 rule_type: str = 'system', description: str = '', 
                 priority: str = 'medium') -> bool:
        """添加新规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO system_rules 
                (rule_code, rule_name, rule_value, rule_type, description, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (rule_code, rule_name, rule_value, rule_type, description, priority))
            
            conn.commit()
            self._rules_cache[rule_code] = rule_value
            logger.info(f"✓ 添加规则: {rule_code}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"✗ 规则已存在: {rule_code}")
            return False
        finally:
            conn.close()
    
    def delete_rule(self, rule_code: str) -> bool:
        """删除规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM system_rules WHERE rule_code = ?', (rule_code,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if success:
            self._rules_cache.pop(rule_code, None)
            logger.info(f"✓ 删除规则: {rule_code}")
        
        return success
    
    def get_rules_by_type(self, rule_type: str) -> List[Dict]:
        """按类型获取规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_rules WHERE rule_type = ? AND is_active = 1', (rule_type,))
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_dicts(rows)
    
    def get_rules_by_category(self, category: str) -> List[Dict]:
        """按类别获取规则"""
        return self.get_rules_by_type(category)
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_rules WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_dicts(rows)
    
    def get_rules_summary(self) -> Dict:
        """获取规则汇总"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT rule_type, COUNT(*) FROM system_rules WHERE is_active = 1 GROUP BY rule_type')
        type_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT priority, COUNT(*) FROM system_rules WHERE is_active = 1 GROUP BY priority')
        priority_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_rules': sum(type_counts.values()),
            'rules_by_type': type_counts,
            'rules_by_priority': priority_counts,
            'categories': self.RULE_CATEGORIES
        }
    
    def _rows_to_dicts(self, rows: List) -> List[Dict]:
        """将数据库行转换为字典"""
        return [{
            'id': row[0],
            'rule_code': row[1],
            'rule_name': row[2],
            'rule_value': row[3],
            'rule_type': row[4],
            'description': row[5],
            'is_active': row[6],
            'priority': row[7],
            'created_at': row[8],
            'updated_at': row[9],
            'effective_from': row[10],
            'expires_at': row[11],
            'rule_group': row[12],
            'metadata': json.loads(row[13]) if row[13] else {}
        } for row in rows]
    
    def register_listener(self, rule_code: str, callback):
        """注册规则变更监听器"""
        if rule_code not in self._rule_listeners:
            self._rule_listeners[rule_code] = []
        self._rule_listeners[rule_code].append(callback)
    
    def _notify_listeners(self, rule_code: str, value: str):
        """通知规则变更"""
        if rule_code in self._rule_listeners:
            for callback in self._rule_listeners[rule_code]:
                try:
                    callback(rule_code, value)
                except Exception as e:
                    logger.error(f"通知监听器失败: {callback}, 错误: {e}")
    
    def execute_rule(self, rule_code: str, context: Dict = None) -> Dict:
        """执行规则"""
        result = {
            'success': True,
            'rule_code': rule_code,
            'execution_time': datetime.now().isoformat(),
            'result': 'success'
        }
        
        try:
            rule = self.get_rule(rule_code)
            if rule is None:
                result['success'] = False
                result['error_message'] = f"规则不存在: {rule_code}"
                result['result'] = 'failed'
                return result
            
            self._log_execution(rule_code, 'success')
            logger.info(f"✓ 执行规则: {rule_code}")
            
        except Exception as e:
            result['success'] = False
            result['error_message'] = str(e)
            result['result'] = 'failed'
            self._log_execution(rule_code, 'failed', str(e))
            logger.error(f"✗ 执行规则失败: {rule_code}, 错误: {e}")
        
        return result
    
    def _log_execution(self, rule_code: str, result: str, error_message: str = ''):
        """记录规则执行日志"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rule_execution_logs (rule_code, result, error_message)
            VALUES (?, ?, ?)
        ''', (rule_code, result, error_message))
        
        conn.commit()
        conn.close()
    
    def get_execution_logs(self, rule_code: str = None, limit: int = 100) -> List[Dict]:
        """获取规则执行日志"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if rule_code:
            cursor.execute('SELECT * FROM rule_execution_logs WHERE rule_code = ? ORDER BY execution_time DESC LIMIT ?', 
                          (rule_code, limit))
        else:
            cursor.execute('SELECT * FROM rule_execution_logs ORDER BY execution_time DESC LIMIT ?', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'rule_code': row[1],
            'execution_time': row[2],
            'result': row[3],
            'error_message': row[4],
            'executed_by': row[5],
            'metadata': json.loads(row[6]) if row[6] else {}
        } for row in rows]
    
    def validate_rule_code(self, rule_code: str) -> bool:
        """验证规则代码格式"""
        import re
        pattern = r'^[A-Z][A-Z0-9_]*[A-Z0-9]$'
        return bool(re.match(pattern, rule_code))
    
    def validate_rule_value(self, rule_code: str, value: str) -> bool:
        """验证规则值"""
        value_types = {
            'ENABLED': value in ('0', '1'),
            'INTERVAL': value.isdigit(),
            'COUNT': value.isdigit(),
            'PATH': True,
            'PERCENTAGE': value.isdigit() and 0 <= int(value) <= 100,
        }
        
        for key, validator in value_types.items():
            if key in rule_code:
                return validator
        
        return True

unified_rule_manager = UnifiedRuleManager()