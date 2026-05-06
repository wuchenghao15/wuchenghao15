#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则模型 - 系统规则引擎和策略管理
包含规则定义、策略引擎、动态规则更新等功能

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)

class RuleModel:
    """规则模型核心类"""

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.policy_manager = PolicyManager()
        self.dynamic_rule_updater = DynamicRuleUpdater()
        logger.info("规则模型初始化完成")

    def add_rule(self, rule):
        """添加规则"""
        self.rule_engine.add_rule(rule)

    def evaluate_rules(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估规则"""
        return self.rule_engine.evaluate(context)

    def add_policy(self, policy):
        """添加策略"""
        self.policy_manager.add_policy(policy)

    def apply_policy(self, policy_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """应用策略"""
        return self.policy_manager.apply_policy(policy_id, context)

    def update_rule(self, rule_id: str, new_rule):
        """更新规则"""
        self.dynamic_rule_updater.update_rule(rule_id, new_rule)

class RuleEngine:
    """规则引擎"""

    def __init__(self):
        logger.info("规则引擎初始化完成")

    def add_rule(self, rule):
        """添加规则"""
        logger.info(f"添加规则: {rule.id}")
    def remove_rule(self, rule_id: str):
        """移除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"移除规则: {rule_id}")

    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估所有规则"""
        results = []

        for rule_id, rule in self.rules.items():
            try:
                result = rule.evaluate(context)
                results.append({
                    'rule_id': rule_id,
                    'matched': result,
                    'priority': rule.priority,
                    'action': rule.action if result else None
                })
            except Exception as e:
                results.append({
                    'rule_id': rule_id,
                    'matched': False,
                    'error': str(e)
                logger.error(f"规则评估失败 {rule_id}: {str(e)}")
        # 按优先级排序
        results.sort(key=lambda x: x.get('priority', 0), reverse=True)


class Rule:
    """规则类"""

    def __init__(self, rule_id: str, condition: Callable, action=None, priority: int = 1):
        self.id = rule_id
        self.condition = condition
        self.action = action
        self.priority = priority
        self.created_at = datetime.now()
        self.enabled = True

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """评估规则"""
        if not self.enabled:
            return False
        return self.condition(context)
    def execute(self, context: Dict[str, Any]) -> Any:
        """执行规则动作"""
        if self.action:
            return self.action(context)
        return None

class PolicyManager:
    """策略管理器"""

    def __init__(self):
        logger.info("策略管理器初始化完成")

    def add_policy(self, policy):
        """添加策略"""
        self.policies[policy.id] = policy
        logger.info(f"添加策略: {policy.id}")

    def remove_policy(self, policy_id: str):
        if policy_id in self.policies:
            logger.info(f"移除策略: {policy_id}")

    def apply_policy(self, policy_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """应用策略"""
        if policy_id not in self.policies:
            raise ValueError(f"策略 {policy_id} 不存在")

        policy = self.policies[policy_id]
        return policy.apply(context)

    """策略类"""
    def __init__(self, policy_id: str, rules: List[Rule], default_action=None):
        self.id = policy_id
        self.rules = rules
        self.default_action = default_action
        self.created_at = datetime.now()

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """应用策略"""
        results = []
        matched_rules = []

        for rule in self.rules:
            try:
                if rule.evaluate(context):
                    matched_rules.append(rule.id)
                    if rule.action:
                        results.append({'rule_id': rule.id, 'result': result})

        # 如果有默认动作且没有匹配的规则
        if self.default_action and not matched_rules:
            results.append({'rule_id': 'default', 'result': self.default_action(context)})
        return {
            'policy_id': self.id,
            'matched_rules': matched_rules,
            'results': results,
            'applied_at': datetime.now().isoformat()
        }

class DynamicRuleUpdater:
    """动态规则更新器"""
    def __init__(self):
        logger.info("动态规则更新器初始化完成")

    def update_rule(self, rule_id: str, new_rule):
        """更新规则"""
        from flask_app.app.models.rule_model import rule_model

        if rule_id in rule_model.rule_engine.rules:
            old_rule = rule_model.rule_engine.rules[rule_id]
            rule_model.rule_engine.rules[rule_id] = new_rule

            self.update_history.append({
                'rule_id': rule_id,
                'old_rule': {'id': old_rule.id, 'priority': old_rule.priority},
                'new_rule': {'id': new_rule.id, 'priority': new_rule.priority},
            })
            logger.info(f"更新规则: {rule_id}")
        else:
            raise ValueError(f"规则 {rule_id} 不存在")

    def rollback_update(self, update_index: int):
        """回滚更新"""
        if update_index < 0 or update_index >= len(self.update_history):
            raise ValueError("无效的更新索引")

        update = self.update_history[update_index]
        rule_id = update['rule_id']
        from flask_app.app.models.rule_model import rule_model

        # 恢复旧规则
        old_rule_data = update['old_rule']
        restored_rule = Rule(
            condition=lambda c: True,
            priority=old_rule_data['priority']
        )
        rule_model.rule_engine.rules[rule_id] = restored_rule

        logger.info(f"回滚规则更新: {rule_id}")

    def get_update_history(self) -> List[Dict[str, Any]]:
        """获取更新历史"""
        return self.update_history

# 全局实例
rule_model = RuleModel()

def init_rule_model():
    """初始化规则模型"""
    logger.info("初始化规则模型...")
    # 创建示例规则
    rules = [
        Rule(
            rule_id='access_control_rule',
            condition=lambda c: c.get('user_role') == 'admin',
            action=lambda c: {'access_granted': True, 'level': 'full'},
            priority=10
        ),
        Rule(
            rule_id='rate_limit_rule',
            condition=lambda c: c.get('request_count', 0) > 100,
            action=lambda c: {'action': 'throttle', 'message': '请求过于频繁'},
            priority=8
        ),
        Rule(
            rule_id='content_filter_rule',
            condition=lambda c: 'spam' in c.get('content', '').lower(),
            action=lambda c: {'action': 'block', 'reason': '垃圾内容'},
            priority=7
        ),
        Rule(
            rule_id='security_rule',
            condition=lambda c: c.get('risk_score', 0) > 0.8,
            action=lambda c: {'action': 'block', 'reason': '高风险'},
            priority=9
        )
    ]

    for rule in rules:
        rule_model.add_rule(rule)

    # 创建示例策略
    policy = Policy(
        policy_id='access_policy',
        rules=rules[:2],  # access_control_rule 和 rate_limit_rule
        default_action=lambda c: {'access_granted': False, 'reason': '默认拒绝'}
    )
    rule_model.add_policy(policy)

    logger.info("规则模型初始化完成")

if __name__ == "__main__":
    init_rule_model()
