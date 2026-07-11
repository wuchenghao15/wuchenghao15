# -*- coding: utf-8 -*-
"""
数据校验与并发控制系统
- 数据合法性校验
- 数据唯一性约束
- 数据互锁与并发控制
- 数据监控与审计
"""

import re
import json
import hashlib
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# 校验规则枚举
# ============================================================================

class ValidationRuleType(Enum):
    """校验规则类型"""
    REQUIRED = "required"
    TYPE = "type"
    FORMAT = "format"
    RANGE = "range"
    LENGTH = "length"
    UNIQUE = "unique"
    PATTERN = "pattern"
    ENUM = "enum"
    CUSTOM = "custom"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    SQL_SAFE = "sql_safe"
    XSS_SAFE = "xss_safe"


class LockType(Enum):
    """锁类型"""
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


class LockLevel(Enum):
    """锁级别"""
    ROW = "row"
    TABLE = "table"
    DATABASE = "database"


# ============================================================================
# 数据校验器
# ============================================================================

class DataValidator:
    """数据合法性校验器"""

    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    PHONE_PATTERNS = {
        'cn': re.compile(r'^1[3-9]\d{9}$'),
        'us': re.compile(r'^\+?1?\d{10}$'),
        'intl': re.compile(r'^\+?\d{7,15}$')
    }

    URL_PATTERN = re.compile(
        r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
        r'[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
    )

    SQL_INJECTION_PATTERNS = [
        re.compile(r"['\"].*?(OR|AND|UNION|SELECT|INSERT|UPDATE|DELETE|DROP|EXEC|EXECUTE).*?['\"]", re.IGNORECASE),
        re.compile(r"(--|\/\*|\*\/|;|\\)", re.IGNORECASE),
        re.compile(r"(xp_|sp_)\w+", re.IGNORECASE),
    ]

    XSS_PATTERNS = [
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe.*?>", re.IGNORECASE),
        re.compile(r"eval\s*\(", re.IGNORECASE),
    ]

    @classmethod
    def validate(cls, data: Dict[str, Any], rules: Dict[str, List[Dict]]) -> Tuple[bool, Dict[str, List[str]]]:
        """
        校验数据
        
        Args:
            data: 待校验的数据字典
            rules: 校验规则字典 {字段名: [规则列表]}
            
        Returns:
            (是否通过, 错误信息字典)
        """
        errors = defaultdict(list)
        
        for field, field_rules in rules.items():
            value = data.get(field)
            
            for rule in field_rules:
                rule_type = rule.get('type')
                try:
                    passed, error_msg = cls._apply_rule(field, value, rule, data)
                    if not passed:
                        errors[field].append(error_msg)
                except Exception as e:
                    errors[field].append(f"校验规则执行异常: {str(e)}")
        
        is_valid = len(errors) == 0
        return is_valid, dict(errors)

    @classmethod
    def _apply_rule(cls, field: str, value: Any, rule: Dict, all_data: Dict) -> Tuple[bool, str]:
        """应用单个校验规则"""
        rule_type = rule.get('type')
        message = rule.get('message', '')

        if rule_type == ValidationRuleType.REQUIRED.value:
            if value is None or value == '' or (isinstance(value, list) and len(value) == 0):
                return False, message or f"{field} 不能为空"
            return True, ""

        if value is None:
            return True, ""

        if rule_type == ValidationRuleType.TYPE.value:
            expected_type = rule.get('value')
            type_map = {
                'string': str,
                'int': int,
                'float': (int, float),
                'bool': bool,
                'list': list,
                'dict': dict,
                'date': str,
            }
            expected = type_map.get(expected_type)
            if expected and not isinstance(value, expected):
                return False, message or f"{field} 类型错误，应为 {expected_type}"
            return True, ""

        if rule_type == ValidationRuleType.LENGTH.value:
            min_len = rule.get('min', 0)
            max_len = rule.get('max', float('inf'))
            length = len(str(value))
            if length < min_len:
                return False, message or f"{field} 长度不能小于 {min_len}"
            if length > max_len:
                return False, message or f"{field} 长度不能大于 {max_len}"
            return True, ""

        if rule_type == ValidationRuleType.RANGE.value:
            min_val = rule.get('min')
            max_val = rule.get('max')
            try:
                num_value = float(value)
                if min_val is not None and num_value < min_val:
                    return False, message or f"{field} 不能小于 {min_val}"
                if max_val is not None and num_value > max_val:
                    return False, message or f"{field} 不能大于 {max_val}"
            except (ValueError, TypeError):
                return False, message or f"{field} 数值格式错误"
            return True, ""

        if rule_type == ValidationRuleType.PATTERN.value:
            pattern = rule.get('value')
            if isinstance(pattern, str):
                pattern = re.compile(pattern)
            if not pattern.match(str(value)):
                return False, message or f"{field} 格式不正确"
            return True, ""

        if rule_type == ValidationRuleType.ENUM.value:
            allowed = rule.get('value', [])
            if value not in allowed:
                return False, message or f"{field} 必须是 {allowed} 之一"
            return True, ""

        if rule_type == ValidationRuleType.EMAIL.value:
            if not cls.EMAIL_PATTERN.match(str(value)):
                return False, message or f"{field} 邮箱格式不正确"
            return True, ""

        if rule_type == ValidationRuleType.PHONE.value:
            region = rule.get('region', 'cn')
            pattern = cls.PHONE_PATTERNS.get(region, cls.PHONE_PATTERNS['intl'])
            if not pattern.match(str(value)):
                return False, message or f"{field} 手机号格式不正确"
            return True, ""

        if rule_type == ValidationRuleType.URL.value:
            if not cls.URL_PATTERN.match(str(value)):
                return False, message or f"{field} URL格式不正确"
            return True, ""

        if rule_type == ValidationRuleType.SQL_SAFE.value:
            for pattern in cls.SQL_INJECTION_PATTERNS:
                if pattern.search(str(value)):
                    return False, message or f"{field} 包含不安全的SQL内容"
            return True, ""

        if rule_type == ValidationRuleType.XSS_SAFE.value:
            for pattern in cls.XSS_PATTERNS:
                if pattern.search(str(value)):
                    return False, message or f"{field} 包含不安全的脚本内容"
            return True, ""

        if rule_type == ValidationRuleType.CUSTOM.value:
            validator_func = rule.get('validator')
            if callable(validator_func):
                result = validator_func(value, all_data)
                if isinstance(result, tuple):
                    return result
                return result, "" if result else (message or f"{field} 校验失败")
            return True, ""

        return True, ""

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """清理字符串，移除危险字符"""
        if not isinstance(value, str):
            return str(value)
        
        value = value.strip()
        
        for pattern in cls.XSS_PATTERNS:
            value = pattern.sub('', value)
        
        if len(value) > max_length:
            value = value[:max_length]
        
        return value

    @classmethod
    def sanitize_sql_identifier(cls, value: str) -> str:
        """安全化SQL标识符"""
        if not isinstance(value, str):
            return ''
        return re.sub(r'[^a-zA-Z0-9_]', '', value)


# ============================================================================
# 唯一性约束管理器
# ============================================================================

class UniqueConstraintManager:
    """数据唯一性约束管理器"""

    def __init__(self):
        self._constraints: Dict[str, Dict] = {}
        self._cache: Dict[str, set] = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 300

    def register_constraint(self, table_name: str, fields: List[str], 
                          constraint_name: Optional[str] = None) -> str:
        """
        注册唯一性约束
        
        Args:
            table_name: 表名
            fields: 字段列表
            constraint_name: 约束名称
            
        Returns:
            约束ID
        """
        if not constraint_name:
            constraint_name = f"uk_{table_name}_{'_'.join(fields)}"
        
        constraint_id = hashlib.md5(f"{table_name}:{','.join(sorted(fields))}".encode()).hexdigest()
        
        self._constraints[constraint_id] = {
            'table_name': table_name,
            'fields': fields,
            'constraint_name': constraint_name,
            'created_at': datetime.now()
        }
        
        logger.info(f"注册唯一性约束: {constraint_name} on {table_name}({', '.join(fields)})")
        return constraint_id

    def check_uniqueness(self, table_name: str, fields: Dict[str, Any],
                        exclude_id: Optional[str] = None,
                        db_connection = None) -> Tuple[bool, str]:
        """
        检查数据唯一性
        
        Args:
            table_name: 表名
            fields: 字段数据 {字段名: 值}
            exclude_id: 排除的记录ID
            db_connection: 数据库连接
            
        Returns:
            (是否唯一, 错误信息)
        """
        constraint_id = hashlib.md5(
            f"{table_name}:{','.join(sorted(fields.keys()))}".encode()
        ).hexdigest()
        
        if constraint_id not in self._constraints:
            self.register_constraint(table_name, list(fields.keys()))
        
        cache_key = f"{table_name}:{constraint_id}"
        
        with self._cache_lock:
            if cache_key in self._cache:
                value_tuple = tuple(sorted(fields.items()))
                if value_tuple in self._cache[cache_key]:
                    if not exclude_id or self._check_not_excluded(table_name, fields, exclude_id, db_connection):
                        return False, f"数据已存在: {', '.join(f'{k}={v}' for k, v in fields.items())}"
        
        if db_connection:
            return self._check_in_db(table_name, fields, exclude_id, db_connection)
        
        return True, ""

    def _check_in_db(self, table_name: str, fields: Dict[str, Any],
                    exclude_id: Optional[str], db_connection) -> Tuple[bool, str]:
        """在数据库中检查唯一性"""
        try:
            cursor = db_connection.cursor()
            
            where_clauses = []
            params = []
            
            for field, value in fields.items():
                safe_field = re.sub(r'[^a-zA-Z0-9_]', '', field)
                where_clauses.append(f"{safe_field} = ?")
                params.append(value)
            
            if exclude_id:
                where_clauses.append("id != ?")
                params.append(exclude_id)
            
            query = f"SELECT COUNT(*) FROM {table_name} WHERE {' AND '.join(where_clauses)}"
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            if count > 0:
                return False, f"数据已存在: {', '.join(f'{k}={v}' for k, v in fields.items())}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"检查唯一性失败: {e}")
            return True, ""

    def _check_not_excluded(self, table_name: str, fields: Dict[str, Any],
                           exclude_id: str, db_connection) -> bool:
        """检查是否为排除的记录"""
        if not db_connection:
            return True
        is_unique, _ = self._check_in_db(table_name, fields, exclude_id, db_connection)
        return not is_unique

    def update_cache(self, table_name: str, constraint_fields: List[str], 
                    values: Dict[str, Any]):
        """更新唯一性缓存"""
        constraint_id = hashlib.md5(
            f"{table_name}:{','.join(sorted(constraint_fields))}".encode()
        ).hexdigest()
        cache_key = f"{table_name}:{constraint_id}"
        
        with self._cache_lock:
            if cache_key not in self._cache:
                self._cache[cache_key] = set()
            
            value_tuple = tuple(sorted((k, values.get(k)) for k in constraint_fields))
            self._cache[cache_key].add(value_tuple)

    def clear_cache(self, table_name: Optional[str] = None):
        """清除缓存"""
        with self._cache_lock:
            if table_name:
                keys_to_remove = [k for k in self._cache if k.startswith(f"{table_name}:")]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                self._cache.clear()

    def get_constraints(self, table_name: Optional[str] = None) -> Dict:
        """获取所有约束"""
        if table_name:
            return {k: v for k, v in self._constraints.items() 
                   if v['table_name'] == table_name}
        return self._constraints


# ============================================================================
# 分布式锁管理器
# ============================================================================

class DistributedLockManager:
    """分布式锁管理器（支持内存级互锁）"""

    def __init__(self):
        self._locks: Dict[str, threading.RLock] = {}
        self._lock_info: Dict[str, Dict] = {}
        self._creation_lock = threading.Lock()
        self._deadlock_check_interval = 60
        self._last_deadlock_check = time.time()

    def acquire(self, lock_key: str, lock_type: LockType = LockType.EXCLUSIVE,
               timeout: float = 30.0, level: LockLevel = LockLevel.ROW) -> Tuple[bool, Optional[str]]:
        """
        获取锁
        
        Args:
            lock_key: 锁键
            lock_type: 锁类型
            timeout: 超时时间（秒）
            level: 锁级别
            
        Returns:
            (是否成功, 锁ID)
        """
        lock_id = f"{lock_key}_{int(time.time() * 1000)}_{threading.get_ident()}"
        
        with self._creation_lock:
            if lock_key not in self._locks:
                self._locks[lock_key] = threading.RLock()
                self._lock_info[lock_key] = {
                    'type': lock_type.value,
                    'level': level.value,
                    'holders': [],
                    'waiters': 0,
                    'created_at': datetime.now()
                }
        
        lock = self._locks[lock_key]
        acquired = lock.acquire(timeout=timeout)
        
        if acquired:
            with self._creation_lock:
                self._lock_info[lock_key]['holders'].append({
                    'lock_id': lock_id,
                    'thread_id': threading.get_ident(),
                    'acquired_at': datetime.now(),
                    'type': lock_type.value
                })
            logger.debug(f"获取锁成功: {lock_key} (ID: {lock_id})")
            return True, lock_id
        else:
            logger.warning(f"获取锁超时: {lock_key}")
            return False, None

    def release(self, lock_key: str, lock_id: str) -> bool:
        """
        释放锁
        
        Args:
            lock_key: 锁键
            lock_id: 锁ID
            
        Returns:
            是否成功
        """
        if lock_key not in self._locks:
            return False
        
        lock = self._locks[lock_key]
        
        try:
            lock.release()
            
            with self._creation_lock:
                if lock_key in self._lock_info:
                    self._lock_info[lock_key]['holders'] = [
                        h for h in self._lock_info[lock_key]['holders']
                        if h['lock_id'] != lock_id
                    ]
            
            logger.debug(f"释放锁: {lock_key} (ID: {lock_id})")
            return True
        except Exception as e:
            logger.error(f"释放锁失败: {lock_key}, {e}")
            return False

    def is_locked(self, lock_key: str) -> bool:
        """检查是否被锁定"""
        if lock_key not in self._locks:
            return False
        return self._lock_info.get(lock_key, {}).get('holders', []) != []

    def get_lock_info(self, lock_key: Optional[str] = None) -> Dict:
        """获取锁信息"""
        with self._creation_lock:
            if lock_key:
                return dict(self._lock_info.get(lock_key, {}))
            return {k: dict(v) for k, v in self._lock_info.items()}

    def check_deadlocks(self) -> List[Dict]:
        """检查死锁"""
        deadlocks = []
        with self._creation_lock:
            for lock_key, info in self._lock_info.items():
                holders = info.get('holders', [])
                if len(holders) > 1 and info.get('type') == LockType.EXCLUSIVE.value:
                    deadlocks.append({
                        'lock_key': lock_key,
                        'holders': holders,
                        'level': info.get('level')
                    })
        self._last_deadlock_check = time.time()
        return deadlocks

    def force_release(self, lock_key: str) -> bool:
        """强制释放锁（谨慎使用）"""
        if lock_key not in self._locks:
            return False
        
        try:
            lock = self._locks[lock_key]
            while True:
                try:
                    lock.release()
                except Exception:
                    break
            
            with self._creation_lock:
                if lock_key in self._lock_info:
                    self._lock_info[lock_key]['holders'] = []
            
            logger.warning(f"强制释放锁: {lock_key}")
            return True
        except Exception as e:
            logger.error(f"强制释放锁失败: {e}")
            return False

    def cleanup_stale_locks(self, max_age: int = 3600) -> int:
        """清理过期锁"""
        cleaned = 0
        now = datetime.now()
        
        with self._creation_lock:
            keys_to_remove = []
            for lock_key, info in self._lock_info.items():
                holders = info.get('holders', [])
                if holders:
                    oldest = min(h['acquired_at'] for h in holders)
                    if (now - oldest).total_seconds() > max_age:
                        keys_to_remove.append(lock_key)
            
            for key in keys_to_remove:
                del self._locks[key]
                del self._lock_info[key]
                cleaned += 1
        
        logger.info(f"清理过期锁: {cleaned} 个")
        return cleaned


# ============================================================================
# 并发事务控制器
# ============================================================================

class ConcurrencyController:
    """并发事务控制器"""

    def __init__(self):
        self._transaction_locks: Dict[str, List[str]] = {}
        self._lock_manager = DistributedLockManager()
        self._optimistic_locks: Dict[str, int] = {}
        self._transaction_counter = 0
        self._counter_lock = threading.Lock()

    def begin_transaction(self, transaction_id: Optional[str] = None) -> str:
        """
        开始事务
        
        Returns:
            事务ID
        """
        with self._counter_lock:
            self._transaction_counter += 1
            if not transaction_id:
                transaction_id = f"tx_{int(time.time())}_{self._transaction_counter}"
        
        self._transaction_locks[transaction_id] = []
        logger.debug(f"开始事务: {transaction_id}")
        return transaction_id

    def acquire_lock(self, transaction_id: str, resource_key: str,
                    lock_type: LockType = LockType.EXCLUSIVE,
                    timeout: float = 30.0) -> bool:
        """
        事务内获取锁
        
        Args:
            transaction_id: 事务ID
            resource_key: 资源键
            lock_type: 锁类型
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        if transaction_id not in self._transaction_locks:
            return False
        
        success, lock_id = self._lock_manager.acquire(
            resource_key, lock_type, timeout
        )
        
        if success and lock_id:
            self._transaction_locks[transaction_id].append(
                (resource_key, lock_id)
            )
        
        return success

    def commit_transaction(self, transaction_id: str) -> bool:
        """
        提交事务并释放所有锁
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否成功
        """
        if transaction_id not in self._transaction_locks:
            return False
        
        locks = self._transaction_locks.pop(transaction_id, [])
        
        for resource_key, lock_id in reversed(locks):
            self._lock_manager.release(resource_key, lock_id)
        
        logger.debug(f"提交事务: {transaction_id}, 释放 {len(locks)} 个锁")
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        回滚事务并释放所有锁
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否成功
        """
        if transaction_id not in self._transaction_locks:
            return False
        
        locks = self._transaction_locks.pop(transaction_id, [])
        
        for resource_key, lock_id in reversed(locks):
            self._lock_manager.release(resource_key, lock_id)
        
        logger.debug(f"回滚事务: {transaction_id}, 释放 {len(locks)} 个锁")
        return True

    def optimistic_lock_check(self, resource_key: str, expected_version: int) -> bool:
        """
        乐观锁检查
        
        Args:
            resource_key: 资源键
            expected_version: 期望版本号
            
        Returns:
            是否匹配
        """
        current_version = self._optimistic_locks.get(resource_key, 0)
        return current_version == expected_version

    def increment_version(self, resource_key: str) -> int:
        """
        递增版本号
        
        Args:
            resource_key: 资源键
            
        Returns:
            新版本号
        """
        self._optimistic_locks[resource_key] = self._optimistic_locks.get(resource_key, 0) + 1
        return self._optimistic_locks[resource_key]

    def get_lock_manager(self) -> DistributedLockManager:
        """获取锁管理器"""
        return self._lock_manager

    def get_active_transactions(self) -> int:
        """获取活跃事务数"""
        return len(self._transaction_locks)


# ============================================================================
# 数据审计与监控
# ============================================================================

class DataAuditMonitor:
    """数据审计与监控系统"""

    def __init__(self):
        self._audit_log: List[Dict] = []
        self._audit_lock = threading.Lock()
        self._max_log_size = 10000
        self._violation_stats: Dict[str, int] = defaultdict(int)
        self._violation_lock = threading.Lock()
        self._alert_callbacks: List[Callable] = []
        self._alert_threshold = 10

    def log_audit(self, table_name: str, operation: str, 
                 record_id: Optional[str], old_data: Optional[Dict],
                 new_data: Optional[Dict], operator: str,
                 ip: Optional[str] = None, reason: Optional[str] = None):
        """
        记录审计日志
        
        Args:
            table_name: 表名
            operation: 操作类型(INSERT/UPDATE/DELETE)
            record_id: 记录ID
            old_data: 旧数据
            new_data: 新数据
            operator: 操作人
            ip: IP地址
            reason: 原因
        """
        audit_entry = {
            'timestamp': datetime.now(),
            'table_name': table_name,
            'operation': operation,
            'record_id': record_id,
            'old_data': old_data,
            'new_data': new_data,
            'operator': operator,
            'ip': ip,
            'reason': reason,
            'changes': self._compute_changes(old_data, new_data)
        }
        
        with self._audit_lock:
            self._audit_log.append(audit_entry)
            if len(self._audit_log) > self._max_log_size:
                self._audit_log = self._audit_log[-self._max_log_size:]
        
        logger.debug(f"审计日志: {operation} on {table_name} by {operator}")

    def _compute_changes(self, old_data: Optional[Dict], 
                        new_data: Optional[Dict]) -> Dict:
        """计算数据变更"""
        changes = {}
        
        if not old_data and not new_data:
            return changes
        
        old_data = old_data or {}
        new_data = new_data or {}
        
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return changes

    def report_violation(self, violation_type: str, details: Dict):
        """
        报告违规
        
        Args:
            violation_type: 违规类型
            details: 详细信息
        """
        with self._violation_lock:
            self._violation_stats[violation_type] += 1
            count = self._violation_stats[violation_type]
        
        logger.warning(f"数据违规: {violation_type}, count: {count}, details: {details}")
        
        if count >= self._alert_threshold:
            self._trigger_alert(violation_type, count, details)

    def _trigger_alert(self, violation_type: str, count: int, details: Dict):
        """触发告警"""
        for callback in self._alert_callbacks:
            try:
                callback(violation_type, count, details)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")

    def register_alert_callback(self, callback: Callable):
        """注册告警回调"""
        self._alert_callbacks.append(callback)

    def get_audit_log(self, table_name: Optional[str] = None,
                     operation: Optional[str] = None,
                     limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        with self._audit_lock:
            logs = list(self._audit_log)
        
        if table_name:
            logs = [l for l in logs if l['table_name'] == table_name]
        
        if operation:
            logs = [l for l in logs if l['operation'] == operation]
        
        return logs[-limit:]

    def get_violation_stats(self) -> Dict[str, int]:
        """获取违规统计"""
        with self._violation_lock:
            return dict(self._violation_stats)

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self._audit_lock:
            total_audits = len(self._audit_log)
        
        with self._violation_lock:
            total_violations = sum(self._violation_stats.values())
        
        operations = defaultdict(int)
        with self._audit_lock:
            for entry in self._audit_log:
                operations[entry['operation']] += 1
        
        return {
            'total_audits': total_audits,
            'total_violations': total_violations,
            'operations': dict(operations),
            'violation_types': dict(self._violation_stats)
        }

    def clear_logs(self):
        """清除日志"""
        with self._audit_lock:
            self._audit_log.clear()
        
        with self._violation_lock:
            self._violation_stats.clear()


# ============================================================================
# 数据校验与并发控制中心
# ============================================================================

class DataIntegrityCenter:
    """数据完整性中心（统一入口）"""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化"""
        self.validator = DataValidator()
        self.unique_manager = UniqueConstraintManager()
        self.concurrency_controller = ConcurrencyController()
        self.audit_monitor = DataAuditMonitor()
        self._initialized = True
        logger.info("数据完整性中心初始化完成")

    def validate_data(self, data: Dict, rules: Dict) -> Tuple[bool, Dict]:
        """校验数据"""
        return self.validator.validate(data, rules)

    def check_uniqueness(self, table_name: str, fields: Dict,
                        exclude_id: Optional[str] = None,
                        db_connection = None) -> Tuple[bool, str]:
        """检查唯一性"""
        return self.unique_manager.check_uniqueness(
            table_name, fields, exclude_id, db_connection
        )

    def acquire_lock(self, resource_key: str, 
                    lock_type: LockType = LockType.EXCLUSIVE,
                    timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
        """获取锁"""
        return self.concurrency_controller.get_lock_manager().acquire(
            resource_key, lock_type, timeout
        )

    def release_lock(self, resource_key: str, lock_id: str) -> bool:
        """释放锁"""
        return self.concurrency_controller.get_lock_manager().release(
            resource_key, lock_id
        )

    def log_audit(self, table_name: str, operation: str,
                 record_id: Optional[str], old_data: Optional[Dict],
                 new_data: Optional[Dict], operator: str,
                 ip: Optional[str] = None):
        """记录审计"""
        self.audit_monitor.log_audit(
            table_name, operation, record_id, old_data, new_data, operator, ip
        )

    def get_status(self) -> Dict:
        """获取系统状态"""
        lock_manager = self.concurrency_controller.get_lock_manager()
        lock_info = lock_manager.get_lock_info()
        
        active_locks = sum(
            1 for info in lock_info.values() 
            if info.get('holders', [])
        )
        
        return {
            'validator_rules': len(getattr(DataValidator, '__dict__', {})),
            'unique_constraints': len(self.unique_manager.get_constraints()),
            'active_locks': active_locks,
            'total_locks': len(lock_info),
            'active_transactions': self.concurrency_controller.get_active_transactions(),
            'audit_statistics': self.audit_monitor.get_statistics()
        }


# 全局单例
data_integrity_center = DataIntegrityCenter()
