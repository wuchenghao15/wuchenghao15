#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统权限优先判定法则 - Permission Priority Rules
MTSCOS AI Project v3.1
实现权限优先级判定、冲突解决和动态权限调整机制
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('permission_priority.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('permission_priority')

class PriorityLevel(Enum):
    """权限优先级级别"""
    DENY = 0           # 拒绝（最高优先级 - 显式拒绝）
    ADMIN_OVERRIDE = 1 # 管理员覆盖
    EXPLICIT_ALLOW = 2 # 显式允许
    ROLE_BASED = 3     # 角色基础权限
    GROUP_BASED = 4    # 组基础权限
    INHERITED = 5      # 继承权限
    IMPLICIT = 6       # 隐式权限
    DEFAULT = 7        # 默认权限（最低优先级）

class PermissionType(Enum):
    """权限类型"""
    GLOBAL = "global"           # 全局权限
    MODULE = "module"           # 模块权限
    RESOURCE = "resource"       # 资源权限
    OBJECT = "object"           # 对象权限
    ATTRIBUTE = "attribute"     # 属性权限

class DecisionStrategy(Enum):
    """决策策略"""
    STRICT_DENY = "strict_deny"           # 严格拒绝（任一拒绝则拒绝）
    ALLOW_OVERRIDE = "allow_override"     # 允许覆盖（允许优先于拒绝）
    PRIORITY_BASED = "priority_based"     # 优先级优先
    CONSENSUS = "consensus"               # 共识模式（大多数允许则允许）
    HIERARCHICAL = "hierarchical"         # 层级继承

class ConflictResolution(Enum):
    """冲突解决策略"""
    LAST_WIN = "last_win"                 # 最后应用者获胜
    HIGHEST_PRIORITY = "highest_priority" # 最高优先级获胜
    MOST_SPECIFIC = "most_specific"       # 最具体者获胜
    ADMIN_DECISION = "admin_decision"     # 管理员决策

@dataclass
class PriorityRule:
    """优先级规则"""
    rule_id: str
    name: str
    description: str
    priority: PriorityLevel
    permission_type: PermissionType
    resource_pattern: str = "*"
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: str = None
    is_active: bool = True
    created_at: str = None

@dataclass
class PermissionClaim:
    """权限声明"""
    claim_id: str
    user_id: str
    resource_type: str
    resource_id: str
    action: str
    priority: PriorityLevel
    source: str  # role, group, direct, inherited
    granted_by: str = None
    timestamp: str = None

@dataclass
class ResolutionResult:
    """权限判定结果"""
    allowed: bool
    effective_priority: PriorityLevel
    winning_claim: Optional[PermissionClaim] = None
    conflicting_claims: List[PermissionClaim] = field(default_factory=list)
    resolution_strategy: str = ""
    explanation: str = ""

@dataclass
class PriorityOverride:
    """优先级覆盖规则"""
    override_id: str
    user_id: str
    resource_type: str
    resource_id: str
    action: str
    priority: PriorityLevel
    reason: str = ""
    expires_at: str = None
    created_by: str = ""
    created_at: str = None

class PermissionPriorityEngine:
    """权限优先级判定引擎"""
    
    def __init__(self, db_path: str = "permission_priority.db"):
        self.db_path = db_path
        self._init_database()
        self._init_default_rules()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS priority_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                priority INTEGER NOT NULL,
                permission_type TEXT NOT NULL,
                resource_pattern TEXT DEFAULT '*',
                conditions TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permission_claims (
                claim_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                action TEXT NOT NULL,
                priority INTEGER NOT NULL,
                source TEXT NOT NULL,
                granted_by TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS priority_overrides (
                override_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                action TEXT NOT NULL,
                priority INTEGER NOT NULL,
                reason TEXT,
                expires_at TEXT,
                created_by TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                action TEXT NOT NULL,
                allowed INTEGER NOT NULL,
                effective_priority INTEGER,
                strategy TEXT,
                explanation TEXT,
                timestamp TEXT,
                conflicting_claims TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hierarchy_rules (
                hierarchy_id TEXT PRIMARY KEY,
                parent_resource TEXT,
                child_resource TEXT,
                inherit_permissions INTEGER DEFAULT 1,
                priority_adjustment INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"权限优先级数据库初始化完成: {self.db_path}")
    
    def _init_default_rules(self):
        """初始化默认优先级规则"""
        default_rules = [
            {
                'rule_id': 'PR-001',
                'name': '显式拒绝规则',
                'description': '显式拒绝的权限具有最高优先级',
                'priority': PriorityLevel.DENY.value,
                'permission_type': PermissionType.GLOBAL.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-002',
                'name': '管理员覆盖规则',
                'description': '管理员可以覆盖普通权限',
                'priority': PriorityLevel.ADMIN_OVERRIDE.value,
                'permission_type': PermissionType.GLOBAL.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-003',
                'name': '显式允许规则',
                'description': '显式授予的权限优先于继承权限',
                'priority': PriorityLevel.EXPLICIT_ALLOW.value,
                'permission_type': PermissionType.OBJECT.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-004',
                'name': '角色基础规则',
                'description': '角色权限优先于组权限',
                'priority': PriorityLevel.ROLE_BASED.value,
                'permission_type': PermissionType.MODULE.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-005',
                'name': '组基础规则',
                'description': '组权限优先于继承权限',
                'priority': PriorityLevel.GROUP_BASED.value,
                'permission_type': PermissionType.MODULE.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-006',
                'name': '继承规则',
                'description': '继承的权限优先级较低',
                'priority': PriorityLevel.INHERITED.value,
                'permission_type': PermissionType.RESOURCE.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-007',
                'name': '隐式规则',
                'description': '隐式权限优先级较低',
                'priority': PriorityLevel.IMPLICIT.value,
                'permission_type': PermissionType.MODULE.value,
                'resource_pattern': '*'
            },
            {
                'rule_id': 'PR-008',
                'name': '默认规则',
                'description': '默认权限优先级最低',
                'priority': PriorityLevel.DEFAULT.value,
                'permission_type': PermissionType.GLOBAL.value,
                'resource_pattern': '*'
            }
        ]
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        for rule in default_rules:
            cursor.execute("SELECT rule_id FROM priority_rules WHERE rule_id = ?", (rule['rule_id'],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO priority_rules
                    (rule_id, name, description, priority, permission_type, 
                     resource_pattern, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule['rule_id'], rule['name'], rule['description'],
                    rule['priority'], rule['permission_type'],
                    rule['resource_pattern'], datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
    
    def register_priority_rule(self, name: str, description: str, priority: PriorityLevel,
                              permission_type: PermissionType, resource_pattern: str = "*",
                              conditions: Dict = None) -> str:
        """注册优先级规则"""
        rule_id = f"PR-{int(time.time())}-{secrets.token_hex(3)}"
        
        rule = PriorityRule(
            rule_id=rule_id,
            name=name,
            description=description,
            priority=priority,
            permission_type=permission_type,
            resource_pattern=resource_pattern,
            conditions=conditions or {},
            created_at=datetime.now().isoformat()
        )
        
        self._save_priority_rule(rule)
        logger.info(f"优先级规则已注册: {rule_id} - {name}")
        return rule_id
    
    def _save_priority_rule(self, rule: PriorityRule):
        """保存优先级规则"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO priority_rules
            (rule_id, name, description, priority, permission_type, 
             resource_pattern, conditions, expires_at, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule.rule_id, rule.name, rule.description, rule.priority.value,
            rule.permission_type.value, rule.resource_pattern,
            json.dumps(rule.conditions), rule.expires_at,
            int(rule.is_active), rule.created_at
        ))
        conn.commit()
        conn.close()
    
    def add_permission_claim(self, user_id: str, resource_type: str, resource_id: str,
                            action: str, priority: PriorityLevel, source: str,
                            granted_by: str = None) -> str:
        """添加权限声明"""
        claim_id = f"CLM-{int(time.time())}-{secrets.token_hex(3)}"
        
        claim = PermissionClaim(
            claim_id=claim_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            priority=priority,
            source=source,
            granted_by=granted_by,
            timestamp=datetime.now().isoformat()
        )
        
        self._save_permission_claim(claim)
        logger.info(f"权限声明已添加: {claim_id} - {user_id} -> {action}")
        return claim_id
    
    def _save_permission_claim(self, claim: PermissionClaim):
        """保存权限声明"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO permission_claims
            (claim_id, user_id, resource_type, resource_id, action, 
             priority, source, granted_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim.claim_id, claim.user_id, claim.resource_type,
            claim.resource_id, claim.action, claim.priority.value,
            claim.source, claim.granted_by, claim.timestamp
        ))
        conn.commit()
        conn.close()
    
    def get_user_claims(self, user_id: str, resource_type: str = None,
                       action: str = None) -> List[PermissionClaim]:
        """获取用户的权限声明"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        query = "SELECT * FROM permission_claims WHERE user_id = ?"
        params = [user_id]
        
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['claim_id', 'user_id', 'resource_type', 'resource_id', 'action',
                   'priority', 'source', 'granted_by', 'timestamp']
        
        claims = []
        for row in rows:
            data = dict(zip(columns, row))
            claims.append(PermissionClaim(
                claim_id=data['claim_id'],
                user_id=data['user_id'],
                resource_type=data['resource_type'],
                resource_id=data['resource_id'],
                action=data['action'],
                priority=PriorityLevel(data['priority']),
                source=data['source'],
                granted_by=data['granted_by'],
                timestamp=data['timestamp']
            ))
        
        return claims
    
    def resolve_permission(self, user_id: str, resource_type: str, resource_id: str,
                          action: str, strategy: DecisionStrategy = DecisionStrategy.PRIORITY_BASED,
                          resolution: ConflictResolution = ConflictResolution.HIGHEST_PRIORITY) -> ResolutionResult:
        """解析权限优先级并做出决策"""
        claims = self.get_user_claims(user_id, resource_type, action)
        
        if not claims:
            return self._handle_no_claims(user_id, resource_type, resource_id, action)
        
        allowed_claims = []
        denied_claims = []
        
        for claim in claims:
            if self._is_claim_allowed(claim):
                allowed_claims.append(claim)
            else:
                denied_claims.append(claim)
        
        return self._apply_decision_strategy(
            user_id, resource_type, resource_id, action,
            allowed_claims, denied_claims, strategy, resolution
        )
    
    def _is_claim_allowed(self, claim: PermissionClaim) -> bool:
        """判断声明是否允许"""
        if claim.priority == PriorityLevel.DENY:
            return False
        return True
    
    def _handle_no_claims(self, user_id: str, resource_type: str, 
                         resource_id: str, action: str) -> ResolutionResult:
        """处理无权限声明的情况"""
        return ResolutionResult(
            allowed=False,
            effective_priority=PriorityLevel.DEFAULT,
            explanation="无匹配的权限声明，默认拒绝"
        )
    
    def _apply_decision_strategy(self, user_id: str, resource_type: str, resource_id: str,
                                action: str, allowed_claims: List[PermissionClaim],
                                denied_claims: List[PermissionClaim],
                                strategy: DecisionStrategy,
                                resolution: ConflictResolution) -> ResolutionResult:
        """应用决策策略"""
        log_id = f"LOG-{int(time.time())}-{secrets.token_hex(3)}"
        
        if strategy == DecisionStrategy.STRICT_DENY:
            if denied_claims:
                result = ResolutionResult(
                    allowed=False,
                    effective_priority=PriorityLevel.DENY,
                    winning_claim=denied_claims[0],
                    conflicting_claims=allowed_claims,
                    resolution_strategy=strategy.value,
                    explanation="严格拒绝模式：存在拒绝声明"
                )
                self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
                return result
            else:
                return self._resolve_allowed(user_id, resource_type, resource_id, action,
                                           allowed_claims, resolution)
        
        elif strategy == DecisionStrategy.ALLOW_OVERRIDE:
            if allowed_claims:
                return self._resolve_allowed(user_id, resource_type, resource_id, action,
                                           allowed_claims, resolution)
            else:
                result = ResolutionResult(
                    allowed=False,
                    effective_priority=PriorityLevel.DEFAULT,
                    explanation="允许覆盖模式：无允许声明"
                )
                self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
                return result
        
        elif strategy == DecisionStrategy.PRIORITY_BASED:
            return self._resolve_by_priority(user_id, resource_type, resource_id, action,
                                           allowed_claims, denied_claims, resolution)
        
        elif strategy == DecisionStrategy.CONSENSUS:
            total = len(allowed_claims) + len(denied_claims)
            if total == 0:
                allowed = False
            else:
                allowed = len(allowed_claims) > total / 2
            
            result = ResolutionResult(
                allowed=allowed,
                effective_priority=PriorityLevel.DEFAULT,
                resolution_strategy=strategy.value,
                explanation=f"共识模式：{len(allowed_claims)}/{total} 允许"
            )
            self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
            return result
        
        elif strategy == DecisionStrategy.HIERARCHICAL:
            return self._resolve_hierarchical(user_id, resource_type, resource_id, action,
                                             allowed_claims, denied_claims)
        
        return ResolutionResult(
            allowed=False,
            effective_priority=PriorityLevel.DEFAULT,
            explanation="未知决策策略"
        )
    
    def _resolve_allowed(self, user_id: str, resource_type: str, resource_id: str,
                        action: str, allowed_claims: List[PermissionClaim],
                        resolution: ConflictResolution) -> ResolutionResult:
        """解析允许的声明"""
        log_id = f"LOG-{int(time.time())}-{secrets.token_hex(3)}"
        
        if len(allowed_claims) == 1:
            result = ResolutionResult(
                allowed=True,
                effective_priority=allowed_claims[0].priority,
                winning_claim=allowed_claims[0],
                resolution_strategy=resolution.value,
                explanation="单一声明直接允许"
            )
            self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
            return result
        
        if resolution == ConflictResolution.HIGHEST_PRIORITY:
            winner = min(allowed_claims, key=lambda c: c.priority.value)
        elif resolution == ConflictResolution.LAST_WIN:
            winner = max(allowed_claims, key=lambda c: c.timestamp)
        elif resolution == ConflictResolution.MOST_SPECIFIC:
            winner = max(allowed_claims, key=lambda c: len(c.resource_id or ""))
        else:
            winner = allowed_claims[0]
        
        result = ResolutionResult(
            allowed=True,
            effective_priority=winner.priority,
            winning_claim=winner,
            conflicting_claims=[c for c in allowed_claims if c != winner],
            resolution_strategy=resolution.value,
            explanation=f"通过{resolution.value}策略解决冲突"
        )
        
        self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
        return result
    
    def _resolve_by_priority(self, user_id: str, resource_type: str, resource_id: str,
                            action: str, allowed_claims: List[PermissionClaim],
                            denied_claims: List[PermissionClaim],
                            resolution: ConflictResolution) -> ResolutionResult:
        """按优先级解析"""
        log_id = f"LOG-{int(time.time())}-{secrets.token_hex(3)}"
        
        all_claims = allowed_claims + denied_claims
        
        if resolution == ConflictResolution.HIGHEST_PRIORITY:
            winner = min(all_claims, key=lambda c: c.priority.value)
        elif resolution == ConflictResolution.LAST_WIN:
            winner = max(all_claims, key=lambda c: c.timestamp)
        else:
            winner = min(all_claims, key=lambda c: c.priority.value)
        
        allowed = self._is_claim_allowed(winner)
        
        result = ResolutionResult(
            allowed=allowed,
            effective_priority=winner.priority,
            winning_claim=winner,
            conflicting_claims=[c for c in all_claims if c != winner],
            resolution_strategy=resolution.value,
            explanation=f"优先级判定：{winner.priority.name} 获胜"
        )
        
        self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
        return result
    
    def _resolve_hierarchical(self, user_id: str, resource_type: str, resource_id: str,
                             action: str, allowed_claims: List[PermissionClaim],
                             denied_claims: List[PermissionClaim]) -> ResolutionResult:
        """层级解析"""
        log_id = f"LOG-{int(time.time())}-{secrets.token_hex(3)}"
        
        explicit_denies = [c for c in denied_claims if c.priority == PriorityLevel.DENY]
        if explicit_denies:
            result = ResolutionResult(
                allowed=False,
                effective_priority=PriorityLevel.DENY,
                winning_claim=explicit_denies[0],
                resolution_strategy=DecisionStrategy.HIERARCHICAL.value,
                explanation="层级模式：显式拒绝优先"
            )
            self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
            return result
        
        explicit_allows = [c for c in allowed_claims if c.priority == PriorityLevel.EXPLICIT_ALLOW]
        if explicit_allows:
            winner = min(explicit_allows, key=lambda c: c.priority.value)
            result = ResolutionResult(
                allowed=True,
                effective_priority=winner.priority,
                winning_claim=winner,
                resolution_strategy=DecisionStrategy.HIERARCHICAL.value,
                explanation="层级模式：显式允许"
            )
            self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
            return result
        
        result = ResolutionResult(
            allowed=False,
            effective_priority=PriorityLevel.DEFAULT,
            resolution_strategy=DecisionStrategy.HIERARCHICAL.value,
            explanation="层级模式：无显式声明，默认拒绝"
        )
        self._log_decision(log_id, user_id, resource_type, resource_id, action, result)
        return result
    
    def _log_decision(self, log_id: str, user_id: str, resource_type: str,
                     resource_id: str, action: str, result: ResolutionResult):
        """记录决策日志"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO decision_logs
            (log_id, user_id, resource_type, resource_id, action, allowed,
             effective_priority, strategy, explanation, timestamp, conflicting_claims)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id, user_id, resource_type, resource_id, action,
            int(result.allowed), result.effective_priority.value,
            result.resolution_strategy, result.explanation,
            datetime.now().isoformat(),
            json.dumps([c.claim_id for c in result.conflicting_claims])
        ))
        conn.commit()
        conn.close()
    
    def create_priority_override(self, user_id: str, resource_type: str, resource_id: str,
                                action: str, priority: PriorityLevel, reason: str = "",
                                expires_at: datetime = None, created_by: str = "") -> str:
        """创建优先级覆盖规则"""
        override_id = f"OVR-{int(time.time())}-{secrets.token_hex(3)}"
        
        override = PriorityOverride(
            override_id=override_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            priority=priority,
            reason=reason,
            expires_at=expires_at.isoformat() if expires_at else None,
            created_by=created_by,
            created_at=datetime.now().isoformat()
        )
        
        self._save_priority_override(override)
        logger.info(f"优先级覆盖已创建: {override_id}")
        return override_id
    
    def _save_priority_override(self, override: PriorityOverride):
        """保存优先级覆盖"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO priority_overrides
            (override_id, user_id, resource_type, resource_id, action, priority,
             reason, expires_at, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            override.override_id, override.user_id, override.resource_type,
            override.resource_id, override.action, override.priority.value,
            override.reason, override.expires_at, override.created_by,
            override.created_at
        ))
        conn.commit()
        conn.close()
    
    def add_hierarchy_rule(self, parent_resource: str, child_resource: str,
                          inherit_permissions: bool = True, priority_adjustment: int = 0) -> str:
        """添加层级继承规则"""
        hierarchy_id = f"HRC-{int(time.time())}-{secrets.token_hex(3)}"
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hierarchy_rules
            (hierarchy_id, parent_resource, child_resource, inherit_permissions,
             priority_adjustment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            hierarchy_id, parent_resource, child_resource,
            int(inherit_permissions), priority_adjustment,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"层级规则已添加: {hierarchy_id}")
        return hierarchy_id
    
    def get_effective_permissions(self, user_id: str) -> Dict[str, Dict[str, Set[str]]]:
        """获取用户的有效权限"""
        claims = self.get_user_claims(user_id)
        
        permissions = {}
        for claim in claims:
            if claim.resource_type not in permissions:
                permissions[claim.resource_type] = {}
            
            resource_key = claim.resource_id or "*"
            if resource_key not in permissions[claim.resource_type]:
                permissions[claim.resource_type][resource_key] = set()
            
            permissions[claim.resource_type][resource_key].add(claim.action)
        
        return permissions
    
    def get_decision_history(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """获取决策历史"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        query = "SELECT * FROM decision_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['log_id', 'user_id', 'resource_type', 'resource_id', 'action',
                   'allowed', 'effective_priority', 'strategy', 'explanation',
                   'timestamp', 'conflicting_claims']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_priority_stats(self) -> Dict[str, Any]:
        """获取优先级统计"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM priority_rules WHERE is_active = 1")
        active_rules = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM permission_claims")
        total_claims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM priority_overrides")
        total_overrides = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM decision_logs")
        total_decisions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT allowed, COUNT(*) FROM decision_logs GROUP BY allowed
        """)
        decision_dist = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT priority, COUNT(*) FROM permission_claims GROUP BY priority
        """)
        priority_dist = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'active_rules': active_rules,
            'total_claims': total_claims,
            'total_overrides': total_overrides,
            'total_decisions': total_decisions,
            'decision_distribution': {
                'allowed': decision_dist.get(1, 0),
                'denied': decision_dist.get(0, 0)
            },
            'priority_distribution': {PriorityLevel(k).name: v for k, v in priority_dist.items()}
        }

def main():
    """测试主函数"""
    print("\n🔐 系统权限优先判定法则测试")
    print("=" * 60)
    
    engine = PermissionPriorityEngine()
    
    print("\n📊 初始统计:")
    stats = engine.get_priority_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🧪 测试添加权限声明:")
    claim1 = engine.add_permission_claim(
        user_id="user001",
        resource_type="exam",
        resource_id="exam-001",
        action="read",
        priority=PriorityLevel.ROLE_BASED,
        source="role",
        granted_by="admin"
    )
    print(f"  声明1: {claim1}")
    
    claim2 = engine.add_permission_claim(
        user_id="user001",
        resource_type="exam",
        resource_id="exam-001",
        action="write",
        priority=PriorityLevel.EXPLICIT_ALLOW,
        source="direct",
        granted_by="admin"
    )
    print(f"  声明2: {claim2}")
    
    claim3 = engine.add_permission_claim(
        user_id="user001",
        resource_type="exam",
        resource_id="exam-001",
        action="delete",
        priority=PriorityLevel.DENY,
        source="role",
        granted_by="admin"
    )
    print(f"  声明3: {claim3}")
    
    print("\n🧪 测试权限解析(严格拒绝模式):")
    result = engine.resolve_permission(
        user_id="user001",
        resource_type="exam",
        resource_id="exam-001",
        action="delete",
        strategy=DecisionStrategy.STRICT_DENY
    )
    print(f"  允许: {result.allowed}")
    print(f"  优先级: {result.effective_priority.name}")
    print(f"  解释: {result.explanation}")
    
    print("\n🧪 测试权限解析(优先级模式):")
    result = engine.resolve_permission(
        user_id="user001",
        resource_type="exam",
        resource_id="exam-001",
        action="write",
        strategy=DecisionStrategy.PRIORITY_BASED
    )
    print(f"  允许: {result.allowed}")
    print(f"  优先级: {result.effective_priority.name}")
    
    print("\n🧪 测试创建优先级覆盖:")
    override = engine.create_priority_override(
        user_id="user001",
        resource_type="exam",
        resource_id="exam-001",
        action="delete",
        priority=PriorityLevel.ADMIN_OVERRIDE,
        reason="特殊需求",
        created_by="super_admin"
    )
    print(f"  覆盖ID: {override}")
    
    print("\n🧪 测试获取有效权限:")
    perms = engine.get_effective_permissions("user001")
    print(f"  有效权限: {perms}")
    
    print("\n🧪 测试获取决策历史:")
    history = engine.get_decision_history("user001")
    print(f"  决策记录数: {len(history)}")
    
    print("\n📊 更新后统计:")
    stats = engine.get_priority_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ 系统权限优先判定法则测试完成")

if __name__ == '__main__':
    main()