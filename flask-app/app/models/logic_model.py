# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逻辑模型 - 系统核心业务逻辑处理
包含业务规则引擎、工作流管理、状态机等核心逻辑组件
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

business_logic_engine = None
decision_engine = None


class BusinessLogicEngine:
    """业务逻辑引擎"""

    def __init__(self):
        self.rules = {}
        self.workflows = {}
        self.state_machines = {}
        logger.info("业务逻辑引擎初始化完成")

    def register_rule(self, rule_id: str, rule_logic):
        """注册业务规则"""
        self.rules[rule_id] = rule_logic
        logger.info(f"注册业务规则: {rule_id}")

    def execute_rule(self, rule_id: str, data: Dict[str, Any]) -> Any:
        """执行业务规则"""
        if rule_id in self.rules:
            try:
                result = self.rules[rule_id](data)
                logger.info(f"执行规则 {rule_id} 成功")
                return result
            except Exception as e:
                logger.error(f"执行规则 {rule_id} 失败: {str(e)}")
                return None
        else:
            logger.warning(f"规则 {rule_id} 不存在")
            return None

    def register_workflow(self, workflow_id: str, steps: List):
        """注册工作流"""
        self.workflows[workflow_id] = steps
        logger.info(f"注册工作流: {workflow_id}, 包含 {len(steps)} 个步骤")

    def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 不存在")

        steps = self.workflows[workflow_id]
        results = {}

        for i, step in enumerate(steps):
            step_name = step.get('name', f'step_{i}')
            try:
                handler = step.get('handler')
                result = handler(context) if handler else None
                results[step_name] = {'success': True, 'result': result}
                logger.info(f"工作流 {workflow_id} 步骤 {step_name} 完成")

                if step.get('terminate_on_success') and result:
                    break
                if step.get('terminate_on_failure') and not result:
                    results[step_name]['success'] = False
                    break
            except Exception as e:
                results[step_name] = {'success': False, 'error': str(e)}
                logger.error(f"工作流 {workflow_id} 步骤 {step_name} 失败: {str(e)}")
                if not step.get('continue_on_error'):
                    break

        return results


class StateMachine:
    """状态机"""

    def __init__(self, states: List[str], transitions: Dict[str, List[str]]):
        self.states = states
        self.transitions = transitions
        self.current_state = None
        self.state_history = []
        logger.info(f"状态机初始化, 状态: {states}")

    def start(self, initial_state: str):
        """启动状态机"""
        if initial_state not in self.states:
            raise ValueError(f"初始状态 {initial_state} 不存在")
        self.current_state = initial_state
        self.state_history.append({'state': initial_state, 'timestamp': datetime.now()})
        logger.info(f"状态机启动, 初始状态: {initial_state}")

    def transition(self, new_state: str):
        """状态转换"""
        if new_state not in self.states:
            raise ValueError(f"状态 {new_state} 不存在")

        if self.current_state not in self.transitions or new_state not in self.transitions[self.current_state]:
            raise ValueError(f"无法从 {self.current_state} 转换到 {new_state}")

        self.current_state = new_state
        self.state_history.append({'state': new_state, 'timestamp': datetime.now()})
        logger.info(f"状态转换: {self.current_state}")

    def get_state(self) -> str:
        """获取当前状态"""
        return self.current_state


class DecisionEngine:
    """决策引擎"""

    def __init__(self):
        self.strategies = {}
        logger.info("决策引擎初始化完成")

    def register_strategy(self, strategy_id: str, strategy):
        """注册决策策略"""
        self.strategies[strategy_id] = strategy
        logger.info(f"注册决策策略: {strategy_id}")

    def decide(self, strategy_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行决策"""
        if strategy_id not in self.strategies:
            raise ValueError(f"策略 {strategy_id} 不存在")

        try:
            result = self.strategies[strategy_id](context)
            return result
        except Exception as e:
            logger.error(f"执行决策策略 {strategy_id} 失败: {str(e)}")
            return {'error': str(e)}


def init_logic_model():
    """初始化逻辑模型"""
    global business_logic_engine, decision_engine

    logger.info("初始化逻辑模型...")

    business_logic_engine = BusinessLogicEngine()
    decision_engine = DecisionEngine()

    business_logic_engine.register_rule(
        'user_registration_validation',
        lambda data: all([data.get('username'), data.get('email'), data.get('password')])
    )

    business_logic_engine.register_rule(
        'order_processing',
        lambda data: {'status': 'processed', 'timestamp': datetime.now().isoformat()}
    )

    business_logic_engine.register_workflow('user_onboarding', [
        {'name': 'validate_input', 'handler': lambda c: True},
        {'name': 'create_user', 'handler': lambda c: {'user_id': '123'}},
        {'name': 'send_welcome_email', 'handler': lambda c: {'email_sent': True}},
    ])

    decision_engine.register_strategy(
        'risk_assessment',
        lambda context: {'risk_level': 'low', 'score': 0.2}
    )

    decision_engine.register_strategy(
        'resource_allocation',
        lambda context: {'allocated': True, 'resources': {'cpu': 1, 'memory': 512}}
    )

    logger.info("逻辑模型初始化完成")


if __name__ == "__main__":
    init_logic_model()
